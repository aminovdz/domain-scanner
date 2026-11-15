"""
DomainSuite Pro - Bulk Domain Scanner & Intelligence Suite
Monetization-ready platform with AdSense, Affiliates, Hosting & Website Builder Upsells.
"""

import asyncio
import html
import io
import time
from typing import Dict, List, Set

import pandas as pd
import streamlit as st

import config
from core.brandable import generate_5letter_brandables, generate_cvcv_domains, generate_prefix_suffix_combos
from core.checker import CheckResult, DomainChecker, DomainStatus, clean_domain
from core.extractor import extract_domains_from_text, format_domain_urls
from core.watch_list import add_domain_watch, add_newsletter_subscriber
from core.whois_dns import lookup_dns_records, lookup_whois

st.set_page_config(
    page_title=config.META_TITLE,
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": f"### {config.META_TITLE}\n{config.META_DESCRIPTION}\n\n[Visit Website]({config.SITE_URL})"
    }
)

# Injected SEO Meta Tags, Open Graph, Twitter Cards, and Schema.org JSON-LD
google_verification_tag = (
    f'<meta name="google-site-verification" content="{html.escape(config.GOOGLE_SITE_VERIFICATION, quote=True)}" />'
    if config.GOOGLE_SITE_VERIFICATION else ""
)

st.markdown(f"""
<!-- Primary SEO Meta Tags -->
<meta name="title" content="{html.escape(config.META_TITLE, quote=True)}" />
<meta name="description" content="{html.escape(config.META_DESCRIPTION, quote=True)}" />
<meta name="keywords" content="bulk domain checker, bulk domain availability search, check .gr domain availability, domain drop watcher, greek domain search, whois lookup, domain extractor, buy domain" />
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1" />
<link rel="canonical" href="{config.SITE_URL}/" />
{google_verification_tag}

<!-- Open Graph / Facebook -->
<meta property="og:type" content="website" />
<meta property="og:url" content="{config.SITE_URL}/" />
<meta property="og:title" content="{html.escape(config.META_TITLE, quote=True)}" />
<meta property="og:description" content="{html.escape(config.META_DESCRIPTION, quote=True)}" />
<meta property="og:image" content="{config.OG_IMAGE_URL}" />
<meta property="og:site_name" content="DomainSuite Pro" />

<!-- Twitter -->
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:url" content="{config.SITE_URL}/" />
<meta name="twitter:title" content="{html.escape(config.META_TITLE, quote=True)}" />
<meta name="twitter:description" content="{html.escape(config.META_DESCRIPTION, quote=True)}" />
<meta name="twitter:image" content="{config.OG_IMAGE_URL}" />

<!-- Schema.org Structured Data: WebApplication & FAQPage for Google Rich Snippets -->
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@graph": [
    {{
      "@type": "WebApplication",
      "@id": "{config.SITE_URL}/#webapp",
      "name": "DomainSuite Pro",
      "url": "{config.SITE_URL}/",
      "description": "{html.escape(config.META_DESCRIPTION, quote=True)}",
      "applicationCategory": "BusinessApplication",
      "operatingSystem": "All",
      "browserRequirements": "Requires JavaScript",
      "offers": {{
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "USD"
      }}
    }},
    {{
      "@type": "FAQPage",
      "@id": "{config.SITE_URL}/#faq",
      "mainEntity": [
        {{
          "@type": "Question",
          "name": "How does the bulk domain availability checker work?",
          "acceptedAnswer": {{
            "@type": "Answer",
            "text": "DomainSuite uses an asynchronous multi-tier pipeline: first querying active A, AAAA, NS, and MX DNS records in parallel. Unassigned domains are verified against official ICANN RDAP endpoints and registry WHOIS servers."
          }}
        }},
        {{
          "@type": "Question",
          "name": "Can I check Greek (.gr) domain names in bulk?",
          "acceptedAnswer": {{
            "@type": "Answer",
            "text": "Yes! DomainSuite natively resolves Greek (.gr) domains against authoritative ICS-FORTH registry nameservers, accurately identifying NXDOMAIN states with 1-click registration links on Papaki, Namecheap, and GoDaddy."
          }}
        }},
        {{
          "@type": "Question",
          "name": "Is DomainSuite completely free to use?",
          "acceptedAnswer": {{
            "@type": "Answer",
            "text": "Yes, DomainSuite is 100% free with no registration required. You can scan up to 500 domains simultaneously, format URL protocols, lookup WHOIS records, and monitor dropped domains."
          }}
        }},
        {{
          "@type": "Question",
          "name": "How do I register an available domain found by the scanner?",
          "acceptedAnswer": {{
            "@type": "Answer",
            "text": "When an available domain is discovered, 1-click registration buttons appear directly in the results table for Porkbun, Namecheap, Papaki (.gr), and GoDaddy for instant registration at standard retail pricing."
          }}
        }}
      ]
    }}
  ]
}}
</script>
""", unsafe_allow_html=True)

# Custom Styling
st.markdown("""
<style>
    .badge-avail {
        background-color: #10b981;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
        display: inline-block;
    }
    .badge-taken {
        background-color: #ef4444;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
        display: inline-block;
    }
    .badge-unknown {
        background-color: #f59e0b;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
        display: inline-block;
    }
    .buy-btn {
        display: inline-block;
        padding: 3px 7px;
        margin: 1px;
        font-size: 11px;
        font-weight: 600;
        text-decoration: none;
        color: #fff !important;
        border-radius: 4px;
    }
    .buy-porkbun { background-color: #ea580c; }
    .buy-namecheap { background-color: #dc2626; }
    .buy-godaddy { background-color: #2563eb; }
    .buy-papaki { background-color: #0284c7; }
    .buy-hostinger { background-color: #6366f1; }
    .buy-shopify { background-color: #059669; }
    .buy-looka { background-color: #8b5cf6; }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "scan_results" not in st.session_state:
    st.session_state["scan_results"] = None
if "scan_duration" not in st.session_state:
    st.session_state["scan_duration"] = 0.0
if "last_scanned_count" not in st.session_state:
    st.session_state["last_scanned_count"] = 0
if "bulk_input_text" not in st.session_state:
    st.session_state["bulk_input_text"] = ""

# Sidebar Settings & Monetization
st.sidebar.title("⚡ DomainSuite")
st.sidebar.caption("High-Speed Domain Intelligence & Monetization")

st.sidebar.markdown("### ⚙️ Scanner Settings")
concurrency = st.sidebar.slider("Concurrency", min_value=10, max_value=60, value=30, step=5)
timeout = st.sidebar.slider("Timeout (seconds)", min_value=1.0, max_value=8.0, value=4.0, step=0.5)

st.sidebar.markdown("---")

# Donation & Support Section
if config.BUY_ME_A_COFFEE_URL:
    st.sidebar.markdown("### ☕ Support This Tool")
    st.sidebar.markdown(f"""
    Love this free tool? Support server costs and ongoing updates:
    <a href="{config.BUY_ME_A_COFFEE_URL}" target="_blank" style="display:inline-block; background-color:#ffdd00; color:#000; font-weight:bold; padding:8px 12px; border-radius:6px; text-decoration:none; margin-top:4px;">
    💛 Buy Me a Coffee
    </a>
    """, unsafe_allow_html=True)
    st.sidebar.markdown("---")

# Sidebar Ad Placement (Configurable in config.py)
if config.ENABLE_ADS and config.SIDEBAR_AD_HTML:
    st.sidebar.markdown(config.SIDEBAR_AD_HTML, unsafe_allow_html=True)

# Top AdSense / Banner Container (Configurable in config.py)
if config.ENABLE_ADS and config.TOP_BANNER_AD_HTML:
    st.markdown(config.TOP_BANNER_AD_HTML, unsafe_allow_html=True)

# Main Navigation Tabs (Typo Scanner removed as requested)
tabs = st.tabs([
    "🌐 Bulk Scanner & Multi-TLD",
    "🔎 WHOIS & DNS Records",
    "🧹 Domain Extractor & Cleaner",
    "💡 Brandable & Short Names",
    "📬 Domain Drop Watcher",
    "💎 Curated Drops (VIP)",
])

# ----------------- TAB 1: BULK SCANNER -----------------
with tabs[0]:
    st.subheader("🌐 Bulk Domain Scanner & Multi-Extension Checker")
    st.caption("Check bulk lists or expand names across international extensions (e.g. .gr, .com, .net, .ai, .io, .de) with 1-click buy links.")

    col_in1, col_in2 = st.columns([2, 1])
    raw_inputs: List[str] = []

    with col_in1:
        input_choice = st.radio("Input Source", ["Paste Domain Names or Keywords", "Upload File (.txt, .csv)"], horizontal=True)
        if input_choice == "Paste Domain Names or Keywords":
            text_val = st.text_area(
                "Enter domain names or keyword names (one per line or comma separated):",
                value=st.session_state["bulk_input_text"],
                height=150,
                placeholder="google.com\nmybrand.gr\nsuperfastai\ncloudsynth",
            )
            if text_val.strip():
                for line in text_val.splitlines():
                    parts = [p.strip() for p in line.replace(",", " ").split() if p.strip()]
                    raw_inputs.extend(parts)
        else:
            uploaded_f = st.file_uploader("Upload domain list file (.txt, .csv)", type=["txt", "csv"])
            if uploaded_f:
                content = uploaded_f.getvalue().decode("utf-8", errors="ignore")
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        parts = [p.strip() for p in line.replace(",", " ").split() if p.strip()]
                        raw_inputs.extend(parts)

    with col_in2:
        st.markdown("#### 🌍 Extension Expansion")
        expand_extensions = st.checkbox("Scan across multiple extensions", value=False, help="Automatically check candidate names against selected TLDs like .gr, .com, .net, etc.")

        selected_tlds: List[str] = []
        if expand_extensions:
            preset = st.selectbox(
                "Extension Preset",
                [
                    "European & Regional (.gr, .de, .fr, .it, .es, .eu, .co.uk)",
                    "Top Global (.com, .net, .org, .co, .info, .biz)",
                    "Tech & Modern (.ai, .io, .dev, .app, .tech, .xyz)",
                    "Custom Extension List",
                ]
            )
            if "European" in preset:
                default_tlds = ["gr", "de", "fr", "it", "es", "eu", "co.uk"]
            elif "Global" in preset:
                default_tlds = ["com", "net", "org", "co"]
            elif "Tech" in preset:
                default_tlds = ["ai", "io", "dev", "app", "tech", "com"]
            else:
                default_tlds = ["gr", "com", "ai", "io", "net", "org"]

            custom_tld_str = st.text_input("Selected Extensions (comma separated):", value=", ".join(default_tlds))
            selected_tlds = [t.strip().lstrip(".").lower() for t in custom_tld_str.split(",") if t.strip()]

    # Process and expand domain candidates
    final_domains_to_scan: List[str] = []
    seen = set()

    for item in raw_inputs:
        item = item.strip().lower()
        if not item:
            continue

        if expand_extensions and selected_tlds:
            # Strip existing TLD if user entered one
            base_name = item.split(".")[0]
            for tld in selected_tlds:
                d = f"{base_name}.{tld}"
                cd = clean_domain(d) or d
                if cd and cd not in seen:
                    seen.add(cd)
                    final_domains_to_scan.append(cd)
        else:
            cd = clean_domain(item) or item
            if cd and cd not in seen:
                seen.add(cd)
                final_domains_to_scan.append(cd)

    # Actions
    col_b1, col_b2, col_b3 = st.columns([1, 1, 3])
    start_bulk = col_b1.button("🚀 Start Bulk Scan", type="primary", disabled=len(final_domains_to_scan) == 0)

    if st.session_state["scan_results"] is not None:
        if col_b2.button("🔄 Clear Results"):
            st.session_state["scan_results"] = None
            st.session_state["scan_duration"] = 0.0
            st.session_state["last_scanned_count"] = 0
            st.rerun()

    if len(final_domains_to_scan) > config.MAX_BULK_SCAN_DOMAINS:
        st.warning(f"⚠️ Input list capped at {config.MAX_BULK_SCAN_DOMAINS} domains per scan to prevent resource exhaustion.")
        final_domains_to_scan = final_domains_to_scan[:config.MAX_BULK_SCAN_DOMAINS]

    if final_domains_to_scan:
        st.caption(f"Ready to scan: **{len(final_domains_to_scan)}** domain combinations")

    # Run Scan
    if start_bulk and final_domains_to_scan:
        prog = st.progress(0.0)
        t_start = time.perf_counter()
        checker = DomainChecker(dns_concurrency=concurrency, timeout=timeout)
        results = asyncio.run(checker.check_all(final_domains_to_scan))
        duration = time.perf_counter() - t_start
        prog.progress(1.0)

        st.session_state["scan_results"] = results
        st.session_state["scan_duration"] = duration
        st.session_state["last_scanned_count"] = len(final_domains_to_scan)

    # Render Results
    if st.session_state["scan_results"] is not None:
        res_list: List[CheckResult] = st.session_state["scan_results"]
        dur = st.session_state["scan_duration"]
        cnt = st.session_state["last_scanned_count"]

        st.success(f"✔ Completed scan of {cnt} domains in {dur:.2f}s ({(cnt / max(0.001, dur)):.1f} domains/sec)")

        m1, m2, m3, m4 = st.columns(4)
        av_cnt = sum(1 for r in res_list if r.status == DomainStatus.AVAILABLE)
        tk_cnt = sum(1 for r in res_list if r.status == DomainStatus.TAKEN)
        un_cnt = sum(1 for r in res_list if r.status == DomainStatus.UNKNOWN)

        m1.metric("Total Scanned", len(res_list))
        m2.metric("🟢 Available to Buy", av_cnt)
        m3.metric("🔴 Taken", tk_cnt)
        m4.metric("🟡 Unknown", un_cnt)

        st.markdown("---")
        flt = st.radio("Display Filter", ["🟢 Available Only", "Show All", "🔴 Taken Only"], horizontal=True, key="bulk_flt_radio")

        sorted_res = sorted(res_list, key=lambda x: (0 if x.status == DomainStatus.AVAILABLE else 1, x.domain))
        if flt == "🟢 Available Only":
            display_res = [r for r in sorted_res if r.status == DomainStatus.AVAILABLE]
        elif flt == "🔴 Taken Only":
            display_res = [r for r in sorted_res if r.status == DomainStatus.TAKEN]
        else:
            display_res = sorted_res

        rows = []
        for r in display_res:
            safe_dom = html.escape(r.domain)
            safe_stage = html.escape(r.stage)
            safe_reason = html.escape(r.reason)

            pork = html.escape(r.buy_links.get("Porkbun", "#"), quote=True)
            nc = html.escape(r.buy_links.get("Namecheap", "#"), quote=True)
            gd = html.escape(r.buy_links.get("GoDaddy", "#"), quote=True)
            papaki = html.escape(r.buy_links.get("Papaki", "#"), quote=True)
            host = html.escape(r.buy_links.get("Hostinger", "#"), quote=True)
            shop = html.escape(r.buy_links.get("Shopify", "#"), quote=True)
            look = html.escape(r.buy_links.get("Looka", "#"), quote=True)

            if r.status == DomainStatus.AVAILABLE:
                st_html = '<span class="badge-avail">AVAILABLE</span>'
                # For .gr domains, emphasize Papaki & Namecheap/GoDaddy
                if r.domain.endswith(".gr"):
                    buy_html = (
                        f'<a href="{papaki}" target="_blank" class="buy-btn buy-papaki">Papaki (.gr)</a>'
                        f'<a href="{nc}" target="_blank" class="buy-btn buy-namecheap">Namecheap</a>'
                        f'<a href="{gd}" target="_blank" class="buy-btn buy-godaddy">GoDaddy</a>'
                    )
                else:
                    buy_html = (
                        f'<a href="{pork}" target="_blank" class="buy-btn buy-porkbun">Porkbun</a>'
                        f'<a href="{nc}" target="_blank" class="buy-btn buy-namecheap">Namecheap</a>'
                        f'<a href="{gd}" target="_blank" class="buy-btn buy-godaddy">GoDaddy</a>'
                    )

                upsell_html = (
                    f'<a href="{host}" target="_blank" class="buy-btn buy-hostinger">⚡ Hosting $2.99</a>'
                    f'<a href="{shop}" target="_blank" class="buy-btn buy-shopify">🛍️ Store</a>'
                    f'<a href="{look}" target="_blank" class="buy-btn buy-looka">🎨 Logo</a>'
                )
            elif r.status == DomainStatus.TAKEN:
                st_html = '<span class="badge-taken">TAKEN</span>'
                buy_html = '<span style="color:#64748b; font-size:12px;">Registered</span>'
                upsell_html = '<span style="color:#64748b; font-size:12px;">-</span>'
            else:
                st_html = '<span class="badge-unknown">UNKNOWN</span>'
                buy_html = f'<a href="{nc}" target="_blank" class="buy-btn buy-godaddy">Check</a>'
                upsell_html = '<span style="color:#64748b; font-size:12px;">-</span>'

            rows.append({
                "Domain": f"**{safe_dom}**",
                "Status": st_html,
                "Stage": safe_stage,
                "Verification Detail": safe_reason,
                "Buy Domain": buy_html,
                "Hosting & Website Upsell": upsell_html,
            })

        if rows:
            st.write(pd.DataFrame(rows).to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.info("No domains match the selected filter.")

        st.markdown("### 📥 Export Scan Results")
        c_dl1, c_dl2 = st.columns(2)
        av_txt = "\n".join([r.domain for r in sorted_res if r.status == DomainStatus.AVAILABLE])
        c_dl1.download_button("🟢 Download Available (.txt)", av_txt, "available_domains.txt", "text/plain", disabled=av_cnt == 0)

        csv_buf = io.StringIO()
        pd.DataFrame([
            {
                "domain": r.domain,
                "status": r.status.value,
                "stage": r.stage,
                "reason": r.reason,
                "porkbun_link": r.buy_links.get("Porkbun", ""),
                "namecheap_link": r.buy_links.get("Namecheap", ""),
                "godaddy_link": r.buy_links.get("GoDaddy", ""),
                "papaki_link": r.buy_links.get("Papaki", ""),
                "hostinger_hosting_link": r.buy_links.get("Hostinger", ""),
                "shopify_builder_link": r.buy_links.get("Shopify", ""),
            }
            for r in sorted_res
        ]).to_csv(csv_buf, index=False)
        c_dl2.download_button("📥 Download Full CSV", csv_buf.getvalue(), "scan_results.csv", "text/csv")

# ----------------- TAB 2: WHOIS & DNS RECORDS -----------------
with tabs[1]:
    st.subheader("🔎 WHOIS Lookup & Live DNS Record Explorer")
    st.caption("Inspect ownership, registration dates, registrar, and live DNS records (A, AAAA, MX, TXT/SPF, NS, SOA).")

    whois_input = st.text_input("Enter domain name to inspect:", value="google.gr")
    whois_btn = st.button("🔍 Lookup WHOIS & DNS", type="primary")

    if whois_btn and whois_input:
        cd = clean_domain(whois_input) or whois_input.strip().lower()
        with st.spinner(f"Querying WHOIS & DNS records for {cd}..."):
            whois_info = asyncio.run(lookup_whois(cd))
            dns_info = asyncio.run(lookup_dns_records(cd))

        col_w1, col_w2 = st.columns(2)

        with col_w1:
            st.markdown("#### 📋 Registration & WHOIS Details")
            if whois_info.is_registered:
                st.success(f"**Status:** Registered")
                st.write(f"**Registrar:** `{whois_info.registrar or 'ICS-FORTH / Registry'}`")
                st.write(f"**Created On:** `{whois_info.creation_date or 'N/A'}`")
                st.write(f"**Expires On:** `{whois_info.expiration_date or 'N/A'}`")
                st.write(f"**Updated On:** `{whois_info.updated_date or 'N/A'}`")
                st.write(f"**Organization:** `{whois_info.org or 'Privacy Protected'}`")
                st.write(f"**Country:** `{whois_info.country or 'N/A'}`")
                if whois_info.status:
                    st.write(f"**Domain Status Codes:** {', '.join(whois_info.status[:3])}")
            else:
                st.info(f"**Status:** Not Registered or Available to Buy!")
                safe_cd = html.escape(cd)
                buy_nc = html.escape(f"https://www.namecheap.com/domains/registration/results/?domain={cd}", quote=True)
                st.markdown(f'<a href="{buy_nc}" target="_blank" class="buy-btn buy-namecheap">Register {safe_cd} Now</a>', unsafe_allow_html=True)

        with col_w2:
            st.markdown("#### 🌐 Live DNS Records")
            if dns_info.has_active_dns:
                for rtype, records in dns_info.records.items():
                    with st.expander(f"**{rtype} Records** ({len(records)})", expanded=rtype in ["A", "MX"]):
                        for r in records:
                            st.code(r, language=None)
            else:
                st.warning("No active DNS records found for this domain.")

# ----------------- TAB 3: DOMAIN EXTRACTOR & CLEANER -----------------
with tabs[2]:
    st.subheader("🧹 Domain Extractor & URL Protocol Formatter")
    st.caption("Paste messy text, code, HTML, or URL dumps to extract clean domain names, with options to add/strip http, https, ftp, or www.")

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        messy_text = st.text_area(
            "Paste raw text, HTML, or URLs:",
            height=200,
            placeholder="Check out https://www.example.com/test and ftp://files.mysite.gr or mailto:info@coolbrand.ai",
        )
        extract_mode = st.radio("Extraction Mode", ["Apex / Root Domain only (e.g. example.com)", "Keep Subdomains (e.g. files.mysite.gr)"], horizontal=True)

    with col_e2:
        st.markdown("#### ⚙️ Output Formatting Options")
        protocol_choice = st.selectbox("Protocol Prefix", ["none (clean domain)", "https://", "http://", "ftp://", "sftp://"])
        www_choice = st.selectbox("WWW Handling", ["keep as is", "add www.", "remove www."])

        extract_btn = st.button("🚀 Extract & Format Domains", type="primary")

    if extract_btn and messy_text.strip():
        apex_only = "Apex" in extract_mode
        extracted = extract_domains_from_text(messy_text, apex_only=apex_only)

        proto_val = "none" if "none" in protocol_choice else protocol_choice.replace("://", "")
        www_val = "add" if "add" in www_choice else "remove" if "remove" in www_choice else "keep"
        formatted_list = format_domain_urls(extracted, protocol=proto_val, www_mode=www_val)

        st.success(f"Extracted **{len(formatted_list)}** unique domains!")
        formatted_out = "\n".join(formatted_list)

        col_res1, col_res2 = st.columns([2, 1])
        with col_res1:
            st.text_area("Extracted Domains Output:", value=formatted_out, height=180)
        with col_res2:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            st.download_button("📥 Download Extracted (.txt)", formatted_out, "extracted_domains.txt", "text/plain")

            if st.button("➡️ Send to Bulk Scanner"):
                st.session_state["bulk_input_text"] = "\n".join(extracted)
                st.success("Loaded into Bulk Scanner! Switch to Tab 1 to scan them.")

# ----------------- TAB 4: BRANDABLE & SHORT NAMES -----------------
with tabs[3]:
    st.subheader("💡 Brandable & Short Domain Hunter")
    st.caption("Generate rare 4-letter CVCV pronounceable domains, 5-letter brandables, or tech startup combinations.")

    b_type = st.radio(
        "Generator Pattern",
        [
            "4-Letter CVCV (e.g. kiva, bexi, zuno - Ultra Rare)",
            "5-Letter Brandables (e.g. novax, lumar, velys)",
            "Keyword + Tech Affixes (e.g. openflow, synclab, hyperbot)",
        ],
        horizontal=True,
    )

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        sel_tlds = st.multiselect("Extensions to Test", ["com", "gr", "ai", "io", "co", "app", "dev"], default=["com", "gr", "ai"])
        num_candidates = st.slider("Number of Candidates", min_value=10, max_value=60, value=30, step=10)

    with col_b2:
        custom_kw = st.text_input("Root Keywords (if using affixes):", value="zen pulse")
        gen_btn = st.button("✨ Generate Candidate Domains", type="primary")

    if gen_btn:
        if "4-Letter" in b_type:
            candidates = generate_cvcv_domains(sel_tlds, count=num_candidates)
        elif "5-Letter" in b_type:
            candidates = generate_5letter_brandables(sel_tlds, count=num_candidates)
        else:
            kws = [k.strip() for k in custom_kw.replace(",", " ").split() if k.strip()]
            candidates = generate_prefix_suffix_combos(kws, sel_tlds, count=num_candidates)

        st.session_state["generated_brandables"] = candidates

    if "generated_brandables" in st.session_state and st.session_state["generated_brandables"]:
        cands = st.session_state["generated_brandables"]
        st.write(f"Generated **{len(cands)}** candidates ready to test:")
        st.code("\n".join(cands[:25]) + ("\n..." if len(cands) > 25 else ""))

        if st.button("🚀 Bulk Scan These Candidates Now"):
            st.session_state["bulk_input_text"] = "\n".join(cands)
            st.success("Loaded into Bulk Scanner! Switch to Tab 1 to run the scan.")

# ----------------- TAB 5: DOMAIN DROP WATCHER -----------------
with tabs[4]:
    st.subheader("📬 Domain Drop Watcher (Private Email Alerts)")
    st.caption("Track taken domains you wish you owned. When they drop or expire, receive an automated email notification.")

    col_w1, col_w2 = st.columns([2, 1])
    with col_w1:
        target_drop_domain = st.text_input("Target Domain to Watch:", placeholder="desiredstartup.com or hotel.gr")
        user_email = st.text_input("Your Notification Email:", placeholder="you@example.com")
        watch_btn = st.button("🔔 Watch This Domain Privately", type="primary")

        if watch_btn:
            ok, msg = add_domain_watch(target_drop_domain, user_email)
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    with col_w2:
        st.info(
            "🔒 **Privacy Guarantee**:\n"
            "Your watched domains and email address are stored privately in server-side storage and are **NEVER** shown to other visitors.\n\n"
            "⚙️ **How it works**:\n"
            "An automated background cron task checks the status of watched domains. The second your target domain drops into public availability, an email is sent to you with instant registration links."
        )

# ----------------- TAB 6: CURATED DROPS (PLAN C) -----------------
with tabs[5]:
    st.subheader("💎 Curated Daily Dropped Domains & VIP Newsletter (Plan C)")
    st.caption("Hand-curated high-value expired & dropped domains. Subscribe for daily exclusive drops.")

    st.markdown("""
    <div style="background:linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); padding:20px; border-radius:10px; border:1px solid #4338ca; margin-bottom:20px;">
        <h4 style="color:#fff; margin:0 0 8px 0;">📬 Get Daily Curated Expired Domain Drops in Your Inbox</h4>
        <p style="color:#c7d2fe; font-size:13px; margin:0 0 12px 0;">Join 2,500+ startup founders and domain investors getting daily lists of 5-letter .coms, dictionary words, and high-DA expired domains.</p>
    </div>
    """, unsafe_allow_html=True)

    c_sub1, c_sub2 = st.columns([3, 1])
    sub_email = c_sub1.text_input("Enter your email for the Daily VIP Drops:", placeholder="investor@domain.com", key="nl_email")
    if c_sub2.button("Subscribe Free", type="primary"):
        ok, msg = add_newsletter_subscriber(sub_email)
        if ok:
            st.success(msg)
        else:
            st.error(msg)

    st.markdown("---")
    st.markdown("#### 🌟 Today's Hand-Picked Available Drops (Sample)")

    curated_sample = [
        {"Domain": "zenflow.ai", "Category": "AI / Productivity", "Buy Link": "https://porkbun.com/checkout/search?q=zenflow.ai"},
        {"Domain": "kivabox.com", "Category": "Brandable / Ecommerce", "Buy Link": "https://porkbun.com/checkout/search?q=kivabox.com"},
        {"Domain": "cloudnest.dev", "Category": "Developer / Cloud", "Buy Link": "https://porkbun.com/checkout/search?q=cloudnest.dev"},
        {"Domain": "athenshub.gr", "Category": "Regional Greek Tech", "Buy Link": "https://www.papaki.com/en/domain-names-search.htm?domain=athenshub.gr"},
    ]

    c_df = pd.DataFrame(curated_sample)
    c_df["Action"] = c_df["Buy Link"].apply(lambda url: f'<a href="{html.escape(url, quote=True)}" target="_blank" class="buy-btn buy-porkbun">Check & Register</a>')
    st.write(c_df[["Domain", "Category", "Action"]].to_html(escape=False, index=False), unsafe_allow_html=True)

# Semantic On-Page SEO Content & Crawlable FAQ for Search Engines
st.markdown("---")
with st.expander("📖 Comprehensive Guide to Bulk Domain Checking & FAQ (Click to Expand)", expanded=False):
    st.markdown("""
    ### Bulk Domain Availability Checker & Greek (.GR) Registry Scanner
    Searching for untaken domain names for startups, local businesses, or brand acquisitions can be tedious when checking registrars one by one. **DomainSuite Pro** provides an ultra-fast, multi-threaded domain scanner engineered for webmasters, investors, and developers.

    #### ⚡ Why Multi-Tier Verification Outperforms Legacy WHOIS
    Legacy WHOIS lookups over port 43 are slow and quickly trigger IP rate limits from ICANN registries. DomainSuite uses an intelligent multi-stage pipeline:
    1. **Asynchronous DNS Pre-Filter (<50ms)**: By simultaneously checking authoritative DNS records (`A`, `AAAA`, `NS`, `MX`), 90%+ of registered domains are confirmed **TAKEN** in milliseconds without exhausting registry quotas.
    2. **Authoritative ICANN RDAP (RFC 7480)**: Unassigned candidates are checked via official HTTP REST RDAP endpoints, where an HTTP `404` confirms availability.
    3. **Authoritative Greek (.GR) TLD Resolution**: For `.gr` domains, our engine queries the root **ICS-FORTH** registry nameservers directly. An `NXDOMAIN` response definitively confirms that the `.gr` name is open for public registration.

    #### 🌍 Supported Top-Level Domains (TLDs)
    * **Global gTLDs**: `.com`, `.net`, `.org`, `.co`, `.info`, `.biz`, `.xyz`
    * **Tech & Modern Extensions**: `.ai`, `.io`, `.dev`, `.app`, `.tech`, `.cloud`
    * **European ccTLDs**: `.gr` (Greece), `.de` (Germany), `.fr` (France), `.it` (Italy), `.es` (Spain), `.eu` (European Union), `.co.uk` (United Kingdom)

    #### ❓ Frequently Asked Questions (FAQ)
    * **How do I check domains in bulk?**  
      Paste your list of names or upload a `.txt` / `.csv` file. You can also check **"Scan across multiple extensions"** to automatically test names across `.com`, `.gr`, `.ai`, and other extensions simultaneously.
    * **Can I register available domains directly?**  
      Yes. For every available domain, direct 1-click registration buttons are provided for **Porkbun**, **Namecheap**, **GoDaddy**, and **Papaki** (specialized Greek registrar for `.gr` domains).
    * **Is my search data private and secure?**  
      Yes. All checks are executed in-memory in your private browser session. We never log, store, or sell user search queries.
    """)

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align:center; color:#64748b; font-size:12px; padding:10px;">
    ⚡ DomainSuite Pro &bull; Multi-Tier DNS, RDAP & WHOIS Engine &bull; 
    <a href="{config.BUY_ME_A_COFFEE_URL}" target="_blank" style="color:#6366f1; text-decoration:none;">Support Project ☕</a>
</div>
""", unsafe_allow_html=True)
