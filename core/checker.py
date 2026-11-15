"""
Domain Checker Core Engine
Performs multi-tiered asynchronous checks:
1. Fast Async DNS resolution (A, AAAA, NS, MX, SOA with authoritative NXDOMAIN detection)
2. Authoritative ICANN RDAP query
3. WHOIS fallback
4. Direct registrar purchase links & monetization upsells
"""

import asyncio
import re
import ssl
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional
from urllib.parse import quote, urlparse

import aiohttp
import certifi
import dns.asyncresolver
import dns.resolver

try:
    from config import AFFILIATE_LINKS
except ImportError:
    AFFILIATE_LINKS = {}

class DomainStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    TAKEN = "TAKEN"
    UNKNOWN = "UNKNOWN"
    INVALID = "INVALID"

@dataclass
class CheckResult:
    domain: str
    status: DomainStatus
    reason: str
    stage: str
    duration: float
    buy_links: Dict[str, str] = field(default_factory=dict)

    def is_available(self) -> bool:
        return self.status == DomainStatus.AVAILABLE

def generate_buy_links(domain: str) -> Dict[str, str]:
    """
    Generate 1-click links for:
    - Domain Registrars (Porkbun, Namecheap, GoDaddy, Papaki for .gr)
    - Web Hosting Upsell (Hostinger)
    - Website Builders (Shopify, Wix) & Logo (Looka)
    """
    q_domain = quote(domain)
    sld = domain.split(".")[0]

    links = {}

    # Check if custom affiliate links are in config
    if AFFILIATE_LINKS:
        for k, v in AFFILIATE_LINKS.items():
            links[k] = v.format(domain=q_domain, domain_name=sld)
    else:
        # Defaults
        links["Porkbun"] = f"https://porkbun.com/checkout/search?q={q_domain}"
        links["Namecheap"] = f"https://www.namecheap.com/domains/registration/results/?domain={q_domain}"
        links["GoDaddy"] = f"https://www.godaddy.com/domainsearch/find?checkAvail=1&domainToCheck={q_domain}"
        links["Hostinger"] = f"https://www.hostinger.com/web-hosting?domain={q_domain}"
        links["Shopify"] = f"https://www.shopify.com/free-trial?ref=domain-scanner&domain={q_domain}"
        links["Wix"] = f"https://www.wix.com/?domain={q_domain}"
        links["Looka"] = f"https://looka.com/logo-maker/?company_name={sld}"

    # For .gr Greek domains, ensure Papaki is available
    if domain.endswith(".gr"):
        links["Papaki"] = f"https://www.papaki.com/en/domain-names-search.htm?domain={q_domain}"

    return links

def clean_domain(raw: str) -> Optional[str]:
    """Clean and normalize domain input."""
    if not raw or not isinstance(raw, str):
        return None
    d = raw.strip().lower()
    if "://" in d:
        parsed = urlparse(d)
        d = parsed.netloc or parsed.path
    d = d.split("/")[0].split("?")[0].split("#")[0].strip()
    d = d.split(":")[0].strip(".-")

    domain_regex = r"^([a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$"
    if not re.match(domain_regex, d):
        return None
    return d

WHOIS_AVAILABLE_INDICATORS = [
    "no match",
    "not found",
    "is free",
    "status: free",
    "available",
    "no data found",
    "no entries found",
    "domain not found",
    "nothing found",
    "not registered",
    "object does not exist",
    "no such domain",
    "domain unknown",
    "nothing found",
    "no information available",
]

class DomainChecker:
    def __init__(
        self,
        dns_concurrency: int = 30,
        rdap_concurrency: int = 5,
        timeout: float = 4.0,
    ):
        self.dns_concurrency = dns_concurrency
        self.rdap_concurrency = rdap_concurrency
        self.timeout = timeout
        self.dns_semaphore = asyncio.Semaphore(dns_concurrency)
        self.rdap_semaphore = asyncio.Semaphore(rdap_concurrency)

        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/rdap+json, application/json, text/plain, */*",
        }

    async def _check_dns(self, domain: str) -> tuple[Optional[bool], str]:
        """
        Check DNS records across standard and ccTLD extensions (.gr, .de, .com, etc.).
        Returns:
            (True, reason) -> TAKEN (active DNS found)
            (False, "NXDOMAIN") -> Non-existent domain at TLD level (High confidence AVAILABLE)
            (False, reason) -> No active A/MX records
        """
        async with self.dns_semaphore:
            resolver = dns.asyncresolver.Resolver()
            resolver.timeout = self.timeout
            resolver.lifetime = self.timeout

            for rtype in ["A", "AAAA", "NS", "MX", "CNAME"]:
                try:
                    answers = await resolver.resolve(domain, rtype)
                    if answers:
                        return True, f"Active DNS ({rtype}: {str(answers[0])})"
                except (dns.resolver.NoAnswer, dns.resolver.NoNameservers):
                    continue
                except dns.resolver.NXDOMAIN:
                    return False, "NXDOMAIN"
                except Exception:
                    continue

            # Query SOA to test TLD zone delegation (especially effective for ccTLDs like .gr)
            try:
                answers = await resolver.resolve(domain, "SOA")
                if answers:
                    return True, "Active Registry SOA"
            except dns.resolver.NXDOMAIN:
                return False, "NXDOMAIN"
            except Exception:
                pass

            return False, "No active DNS records found"

    async def _check_rdap(self, session: aiohttp.ClientSession, domain: str) -> tuple[Optional[DomainStatus], str]:
        """Query ICANN RDAP service."""
        async with self.rdap_semaphore:
            url = f"https://rdap.org/domain/{domain}"
            try:
                async with session.get(
                    url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    allow_redirects=True,
                ) as resp:
                    if resp.status == 404:
                        return DomainStatus.AVAILABLE, "RDAP: 404 Not Found (Available)"
                    elif resp.status == 200:
                        data = await resp.json()
                        handle = data.get("handle") or data.get("ldhName") or "Registered"
                        return DomainStatus.TAKEN, f"RDAP: Registered ({handle})"
                    elif resp.status == 429:
                        return None, "RDAP: Rate limited (429)"
                    else:
                        return None, f"RDAP HTTP status {resp.status}"
            except Exception as e:
                return None, f"RDAP lookup failed: {type(e).__name__}"

    async def _check_whois(self, domain: str) -> tuple[DomainStatus, str]:
        """Fallback WHOIS check."""
        loop = asyncio.get_running_loop()
        try:
            def run_whois():
                return subprocess.run(
                    ["whois", domain],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout + 2.0,
                )

            res = await loop.run_in_executor(None, run_whois)
            out = res.stdout.lower()

            for indicator in WHOIS_AVAILABLE_INDICATORS:
                if indicator in out:
                    return DomainStatus.AVAILABLE, f"WHOIS: '{indicator}' matched"

            if any(k in out for k in ["registrar:", "creation date:", "registry domain id:", "domain status:"]):
                return DomainStatus.TAKEN, "WHOIS: Registration record found"

            if not out.strip():
                return DomainStatus.UNKNOWN, "WHOIS: Empty response"

            return DomainStatus.UNKNOWN, "WHOIS: Ambiguous response"
        except subprocess.TimeoutExpired:
            return DomainStatus.UNKNOWN, "WHOIS: Timeout"
        except FileNotFoundError:
            try:
                import whois
                w = await loop.run_in_executor(None, lambda: whois.whois(domain))
                if w and w.domain_name:
                    return DomainStatus.TAKEN, "WHOIS: Registration record found"
                return DomainStatus.AVAILABLE, "WHOIS: Domain not found (Available)"
            except Exception as pe:
                err_str = str(pe).lower()
                if any(ind in err_str for ind in ["no match", "not found", "not registered"]):
                    return DomainStatus.AVAILABLE, "WHOIS: Not registered (Available)"
                return DomainStatus.UNKNOWN, f"WHOIS unavailable: {type(pe).__name__}"
        except Exception as e:
            return DomainStatus.UNKNOWN, f"WHOIS error: {str(e)}"

    async def check_single(self, session: aiohttp.ClientSession, raw_domain: str) -> CheckResult:
        """Check domain across DNS -> RDAP -> WHOIS pipeline."""
        start_t = time.perf_counter()
        domain = clean_domain(raw_domain)

        if not domain:
            return CheckResult(
                domain=raw_domain.strip(),
                status=DomainStatus.INVALID,
                reason="Invalid domain format (e.g. example.com or example.gr)",
                stage="Validation",
                duration=time.perf_counter() - start_t,
            )

        # 1. DNS Resolution (Handles active domains & ccTLD NXDOMAIN like .gr)
        dns_taken, dns_reason = await self._check_dns(domain)
        if dns_taken:
            return CheckResult(
                domain=domain,
                status=DomainStatus.TAKEN,
                reason=dns_reason,
                stage="DNS",
                duration=time.perf_counter() - start_t,
                buy_links=generate_buy_links(domain),
            )

        # If NXDOMAIN detected on ccTLD (like .gr, .de) where RDAP is not supported
        if dns_reason == "NXDOMAIN":
            # Quick verification: ccTLDs with no RDAP are confirmed available
            tld = domain.split(".")[-1]
            if tld in ["gr", "al", "cy", "bg"]:
                return CheckResult(
                    domain=domain,
                    status=DomainStatus.AVAILABLE,
                    reason="DNS: NXDOMAIN at TLD registry (Available to register)",
                    stage="DNS",
                    duration=time.perf_counter() - start_t,
                    buy_links=generate_buy_links(domain),
                )

        # 2. RDAP Query
        rdap_status, rdap_reason = await self._check_rdap(session, domain)
        if rdap_status is not None:
            return CheckResult(
                domain=domain,
                status=rdap_status,
                reason=rdap_reason,
                stage="RDAP",
                duration=time.perf_counter() - start_t,
                buy_links=generate_buy_links(domain),
            )

        # 3. WHOIS Fallback
        whois_status, whois_reason = await self._check_whois(domain)
        if whois_status != DomainStatus.UNKNOWN:
            return CheckResult(
                domain=domain,
                status=whois_status,
                reason=whois_reason,
                stage="WHOIS",
                duration=time.perf_counter() - start_t,
                buy_links=generate_buy_links(domain),
            )

        # If WHOIS was ambiguous but DNS gave NXDOMAIN
        if dns_reason == "NXDOMAIN":
            return CheckResult(
                domain=domain,
                status=DomainStatus.AVAILABLE,
                reason="DNS: NXDOMAIN (Unregistered in TLD Zone)",
                stage="DNS",
                duration=time.perf_counter() - start_t,
                buy_links=generate_buy_links(domain),
            )

        return CheckResult(
            domain=domain,
            status=DomainStatus.UNKNOWN,
            reason=f"{whois_reason} ({rdap_reason})",
            stage="Verification",
            duration=time.perf_counter() - start_t,
            buy_links=generate_buy_links(domain),
        )

    async def check_all(
        self,
        domain_list: List[str],
        on_progress: Optional[Callable[[CheckResult, int, int], None]] = None,
    ) -> List[CheckResult]:
        """Check a list of domains concurrently."""
        connector = aiohttp.TCPConnector(ssl=self.ssl_context, limit=self.dns_concurrency)
        async with aiohttp.ClientSession(connector=connector) as session:
            total = len(domain_list)
            completed = 0

            async def wrapped_check(d: str) -> CheckResult:
                nonlocal completed
                res = await self.check_single(session, d)
                completed += 1
                if on_progress:
                    on_progress(res, completed, total)
                return res

            tasks = [asyncio.create_task(wrapped_check(d)) for d in domain_list]
            return await asyncio.gather(*tasks)
