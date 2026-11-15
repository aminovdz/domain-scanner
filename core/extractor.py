"""
Domain Extractor & URL Protocol Formatter
Extracts domains from arbitrary text/HTML/logs and adds or strips protocols (http, https, ftp, www).
"""

import re
from typing import List, Set
from urllib.parse import urlparse
import tldextract

URL_PATTERN = re.compile(
    r'(?:https?|ftp|sftp)://[^\s/$.?#].[^\s]*|'  # Full URLs
    r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b',  # Bare domain patterns
    re.IGNORECASE
)

extractor = tldextract.TLDExtract(cache_dir="/tmp/.tld_cache")

def extract_domains_from_text(text: str, apex_only: bool = True) -> List[str]:
    """
    Extract all unique domains from unstructured text, markdown, HTML, or logs.
    """
    if not text:
        return []

    found = URL_PATTERN.findall(text)
    domains: Set[str] = set()

    for item in found:
        item = item.strip().lower()
        if not item:
            continue

        # If it has a protocol, parse netloc
        if "://" in item:
            parsed = urlparse(item)
            host = parsed.netloc or parsed.path
        else:
            host = item.split("/")[0]

        # Strip port
        host = host.split(":")[0].strip(".-")

        ext = extractor(host)
        if not ext.domain or not ext.suffix:
            continue

        if apex_only:
            root_domain = f"{ext.domain}.{ext.suffix}".lower()
            domains.add(root_domain)
        else:
            sub = f"{ext.subdomain}." if ext.subdomain else ""
            full_domain = f"{sub}{ext.domain}.{ext.suffix}".lower()
            domains.add(full_domain)

    return sorted(domains)

def format_domain_urls(
    domains: List[str],
    protocol: str = "none",
    www_mode: str = "keep"
) -> List[str]:
    """
    Format domain list:
    - protocol: 'none', 'https', 'http', 'ftp', 'sftp'
    - www_mode: 'keep', 'add', 'remove'
    """
    formatted: List[str] = []

    for d in domains:
        d = d.strip()
        if not d:
            continue

        # Strip existing protocol if present
        if "://" in d:
            d = d.split("://", 1)[1]

        # Clean trailing slash or path
        d = d.split("/")[0].strip()

        # Handle WWW
        has_www = d.lower().startswith("www.")
        if www_mode == "add" and not has_www:
            d = "www." + d
        elif www_mode == "remove" and has_www:
            d = d[4:]

        # Apply protocol
        if protocol and protocol.lower() != "none":
            proto = protocol.lower().rstrip(":/")
            d = f"{proto}://{d}"

        formatted.append(d)

    return formatted
