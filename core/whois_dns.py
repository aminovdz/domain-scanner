"""
WHOIS & DNS Record Explorer
Provides detailed WHOIS registration information and live DNS record mapping.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import dns.asyncresolver
import dns.resolver
import whois

@dataclass
class WHOISDetails:
    domain: str
    registrar: Optional[str] = None
    creation_date: Optional[str] = None
    expiration_date: Optional[str] = None
    updated_date: Optional[str] = None
    status: List[str] = field(default_factory=list)
    nameservers: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)
    country: Optional[str] = None
    org: Optional[str] = None
    raw_text: str = ""
    is_registered: bool = False
    error: Optional[str] = None

@dataclass
class DNSRecords:
    domain: str
    records: Dict[str, List[str]] = field(default_factory=dict)
    has_active_dns: bool = False
    error: Optional[str] = None

def _format_date(d: Any) -> Optional[str]:
    """Format single or list of datetime objects into readable string."""
    if not d:
        return None
    if isinstance(d, list):
        d = d[0]
    if isinstance(d, datetime):
        return d.strftime("%Y-%m-%d %H:%M:%S UTC")
    return str(d)

async def lookup_whois(domain: str) -> WHOISDetails:
    """Perform comprehensive WHOIS lookup."""
    loop = asyncio.get_running_loop()

    def _sync_whois():
        try:
            return whois.whois(domain)
        except whois.exceptions.WhoisDomainNotFoundError:
            return None
        except Exception as e:
            return e

    res = await loop.run_in_executor(None, _sync_whois)

    if res is None:
        return WHOISDetails(
            domain=domain,
            is_registered=False,
            raw_text="Domain not found in registry (Available).",
        )
    elif isinstance(res, Exception):
        return WHOISDetails(
            domain=domain,
            is_registered=False,
            error=str(res),
            raw_text=f"Lookup failed: {str(res)}",
        )

    # Process statuses
    statuses = res.status if isinstance(res.status, list) else [res.status] if res.status else []
    nameservers = res.name_servers if isinstance(res.name_servers, list) else [res.name_servers] if res.name_servers else []
    emails = res.emails if isinstance(res.emails, list) else [res.emails] if res.emails else []

    return WHOISDetails(
        domain=domain,
        registrar=str(res.registrar) if res.registrar else None,
        creation_date=_format_date(res.creation_date),
        expiration_date=_format_date(res.expiration_date),
        updated_date=_format_date(res.updated_date),
        status=[str(s).split()[0] for s in statuses if s],
        nameservers=[str(ns).lower() for ns in nameservers if ns],
        emails=[str(em) for em in emails if em],
        country=str(res.country) if res.country else None,
        org=str(res.org) if res.org else None,
        raw_text=str(res.text) if hasattr(res, "text") and res.text else "",
        is_registered=bool(res.domain_name),
    )

async def lookup_dns_records(domain: str, timeout: float = 3.0) -> DNSRecords:
    """Query live DNS records across all major types (A, AAAA, MX, TXT, NS, CNAME, SOA)."""
    resolver = dns.asyncresolver.Resolver()
    resolver.timeout = timeout
    resolver.lifetime = timeout

    record_types = ["A", "AAAA", "MX", "TXT", "NS", "CNAME", "SOA"]
    results: Dict[str, List[str]] = {}
    has_records = False

    async def _query_type(rtype: str):
        nonlocal has_records
        try:
            answers = await resolver.resolve(domain, rtype)
            if answers:
                results[rtype] = [str(r) for r in answers]
                has_records = True
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.resolver.Timeout):
            pass
        except Exception:
            pass

    await asyncio.gather(*[_query_type(t) for t in record_types])

    return DNSRecords(
        domain=domain,
        records=results,
        has_active_dns=has_records,
    )
