"""
DomainSuite Pro - Secure Configuration File
Loads secrets from environment variables or Streamlit secrets, keeping credentials safe.
Never commit passwords or private API keys directly into public repositories.
"""

import os
from typing import Dict

# Helper to safely retrieve secrets from Streamlit secrets, Environment variables, or defaults
def get_secret(key: str, default: str = "") -> str:
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.environ.get(key, default)

# ==========================================
# 1. GOOGLE ADSENSE & BANNER ADVERTISING
# ==========================================
ENABLE_ADS = os.environ.get("ENABLE_ADS", "true").lower() in ("true", "1", "yes")

# Top Leaderboard Ad HTML (Placed right under the header)
TOP_BANNER_AD_HTML = os.environ.get(
    "TOP_BANNER_AD_HTML",
    """
<div style="background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%); border: 1px solid #334155; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between;">
    <div>
        <span style="font-size: 10px; color: #94a3b8; text-transform: uppercase; border: 1px solid #475569; padding: 2px 5px; border-radius: 3px; margin-right: 8px;">Sponsored</span>
        <strong style="color: #f8fafc; font-size: 13px;">🚀 Hostinger: 75% Off Web Hosting + Free Domain + SSL ($2.99/mo)</strong>
        <span style="color: #94a3b8; font-size: 12px; margin-left: 8px;">Launch your website on your new domain in minutes.</span>
    </div>
    <a href="https://hostinger.com" target="_blank" style="background: #6366f1; color: #fff; padding: 6px 14px; border-radius: 5px; font-size: 12px; font-weight: bold; text-decoration: none;">Claim Deal ➔</a>
</div>
"""
)

# Sidebar Ad HTML
SIDEBAR_AD_HTML = os.environ.get(
    "SIDEBAR_AD_HTML",
    """
<div style="background:#1e293b; padding:12px; border-radius:6px; border:1px solid #334155; margin-top:10px;">
    <div style="font-size:10px; color:#94a3b8; text-transform:uppercase;">Sponsored Partner</div>
    <div style="font-weight:bold; font-size:13px; color:#fff; margin-top:2px;">Launch Store on Shopify</div>
    <p style="font-size:11px; color:#cbd5e1; margin:4px 0 8px 0;">Build an ecommerce business on your new domain for $1/month.</p>
    <a href="https://shopify.com" target="_blank" style="background:#059669; color:#fff; padding:4px 8px; border-radius:4px; font-size:11px; text-decoration:none; font-weight:bold;">Start Free Trial ➔</a>
</div>
"""
)

# ==========================================
# 2. AFFILIATE LINKS & MONETIZATION
# ==========================================
# You can customize these via Environment variables or directly here:
AFFILIATE_LINKS: Dict[str, str] = {
    "Porkbun": os.environ.get("AFFILIATE_PORKBUN", "https://porkbun.com/checkout/search?q={domain}"),
    "Namecheap": os.environ.get("AFFILIATE_NAMECHEAP", "https://www.namecheap.com/domains/registration/results/?domain={domain}"),
    "GoDaddy": os.environ.get("AFFILIATE_GODADDY", "https://www.godaddy.com/domainsearch/find?checkAvail=1&domainToCheck={domain}"),
    "Papaki": os.environ.get("AFFILIATE_PAPAKI", "https://www.papaki.com/en/domain-names-search.htm?domain={domain}"),
    "Hostinger": os.environ.get("AFFILIATE_HOSTINGER", "https://www.hostinger.com/web-hosting?domain={domain}"),
    "Shopify": os.environ.get("AFFILIATE_SHOPIFY", "https://www.shopify.com/free-trial?domain={domain}"),
    "Wix": os.environ.get("AFFILIATE_WIX", "https://www.wix.com/?domain={domain}"),
    "Looka": os.environ.get("AFFILIATE_LOOKA", "https://looka.com/logo-maker/?company_name={domain_name}"),
}

# ==========================================
# 3. DONATIONS & SUPPORT
# ==========================================
BUY_ME_A_COFFEE_URL = os.environ.get("BUY_ME_A_COFFEE_URL", "https://buymeacoffee.com")
PAYPAL_DONATION_URL = os.environ.get("PAYPAL_DONATION_URL", "")

# ==========================================
# 4. SECURE SMTP SETTINGS (For Drop Watcher)
# ==========================================
# Loaded securely from Environment Variables or Streamlit Secrets
SMTP_CONFIG = {
    "ENABLED": os.environ.get("SMTP_ENABLED", "false").lower() in ("true", "1", "yes"),
    "SMTP_SERVER": get_secret("SMTP_SERVER", "smtp.gmail.com"),
    "SMTP_PORT": int(get_secret("SMTP_PORT", "587")),
    "SENDER_EMAIL": get_secret("SMTP_SENDER_EMAIL", ""),
    "SENDER_PASSWORD": get_secret("SMTP_SENDER_PASSWORD", ""),  # App password, never committed
    "FROM_NAME": os.environ.get("SMTP_FROM_NAME", "Domain Drop Alert"),
}

# ==========================================
# 5. SECURITY & ABUSE LIMITS
# ==========================================
MAX_BULK_SCAN_DOMAINS = int(os.environ.get("MAX_BULK_SCAN_DOMAINS", "500"))
MAX_WATCH_LIST_PER_IP = int(os.environ.get("MAX_WATCH_LIST_PER_IP", "15"))

# ==========================================
# 6. SEO & SEARCH ENGINE CONFIGURATION
# ==========================================
SITE_URL = os.environ.get("SITE_URL", "https://yourdomain.com").rstrip("/")
META_TITLE = os.environ.get(
    "META_TITLE",
    "Bulk Domain Availability Checker & Greek .GR Scanner | DomainSuite"
)
META_DESCRIPTION = os.environ.get(
    "META_DESCRIPTION",
    "Free high-speed bulk domain checker for .com, .gr, .ai, .io, and 50+ extensions. Fast multi-tier DNS & WHOIS search with instant 1-click registration links."
)
GOOGLE_SITE_VERIFICATION = os.environ.get("GOOGLE_SITE_VERIFICATION", "")
OG_IMAGE_URL = os.environ.get("OG_IMAGE_URL", f"{SITE_URL}/og-preview.png")
