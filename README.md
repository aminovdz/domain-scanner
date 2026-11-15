# ⚡ DomainSuite Pro

A complete, high-performance domain intelligence platform and bulk scanner with integrated monetization (Affiliates, Hosting & Website Builder Upsells, AdSense) and complete **SEO optimization to rank on Google Search**.

---

## 🛠️ Complete Feature Suite

1. **🌐 Bulk Domain Scanner**: Multi-tier async scanning (DNS pre-filter + RDAP + WHOIS) across international extensions (`.com`, `.gr`, `.net`, `.ai`, `.io`, `.de`, etc.) with 1-click purchase links (Porkbun, Namecheap, GoDaddy, Papaki for `.gr`) and upsell integrations (Hostinger, Shopify, Wix, Looka).
2. **🔎 WHOIS & DNS Records Explorer**: Detailed ownership lookup (Registrar, Created, Expiry, Status, Nameservers) and live DNS records (A, AAAA, MX, TXT/SPF, NS, SOA).
3. **🧹 Domain Extractor & Sanitizer**: Extract clean domain names from unstructured text, HTML, or logs, with options to add or strip protocols (`https://`, `http://`, `ftp://`) and `www.`.
4. **💡 Short & Brandable Name Hunter**: Generate rare 4-letter CVCV pronounceable domains, 5-letter brandables, or tech affix combinations.
5. **📬 Domain Drop Watcher (Private Email Alerts)**: Private, secure domain drop monitoring with an automated cron job.
6. **💎 Curated Daily Drops & VIP Newsletter**: Email newsletter lead capture and curated high-value expired domain showcase.

---

## 🚀 Google Search SEO Optimization

DomainSuite Pro is fully optimized out of the box to rank on Google Search:

* **Keyword-Targeted Meta Title & Description**: Configured in `config.py` targeting high-volume searches ("bulk domain availability checker", "greek .gr domain search", "bulk whois lookup").
* **Open Graph & Twitter Cards**: High-converting social share previews for X/Twitter, Facebook, LinkedIn, and Discord.
* **Schema.org Structured Data (JSON-LD)**:
  * `WebApplication`: Declares software category, free pricing, and features.
  * `FAQPage`: Powers **Google Rich Results (expandable dropdown FAQ snippets)** directly in Google SERP results!
* **Semantic On-Page Content**: Crawlable H1/H2 architecture, technical feature explanations, and structured FAQ guide.
* **Search Engine Files**: Ready-to-serve [`static/robots.txt`](file:///Users/Mc/.gemini/antigravity/scratch/domain-scanner/static/robots.txt) and [`static/sitemap.xml`](file:///Users/Mc/.gemini/antigravity/scratch/domain-scanner/static/sitemap.xml).
* **Google Search Console Ready**: Plug in your verification code in `config.py` (`GOOGLE_SITE_VERIFICATION`) to verify ownership in seconds.

---

## 💰 Built-in Monetization Architecture

* **Plan A (Registrars & Hosting)**: Namecheap, Porkbun, GoDaddy, and Papaki affiliate links + Hostinger Web Hosting upsells ($50–$100 commission per signup).
* **Plan C (Curated Newsletter)**: Lead capture for premium daily dropped domain newsletter.
* **Plan D (Website & Logo Builder)**: Direct upsell buttons for Shopify, Wix, and Looka AI Logo Maker.
* **AdSense & Sponsored Banners**: Dedicated banner ad containers at the top and in the sidebar.
* **Donations**: Integrated "Buy Me a Coffee" support buttons.

All links and AdSense codes are cleanly configured in [`config.py`](file:///Users/Mc/.gemini/antigravity/scratch/domain-scanner/config.py).

---

## 🚀 Quick Start

### 1. Launch the Web Dashboard
```bash
cd /Users/Mc/.gemini/antigravity/scratch/domain-scanner
./domain-scanner ui
```
Opens in your browser at: **http://localhost:8505**

### 2. Run Bulk Scanner from Terminal
```bash
cd /Users/Mc/.gemini/antigravity/scratch/domain-scanner
./domain-scanner -d google.com google.gr x7k9q2m9z8p1w3b.gr --only-available
```

---

## 🌐 100% Free Custom Domain Deployment & Google Indexing

Read the complete deployment guide in [`CUSTOM_DOMAIN_SETUP.md`](file:///Users/Mc/.gemini/antigravity/scratch/domain-scanner/CUSTOM_DOMAIN_SETUP.md):
* **Render.com**: Native free custom domain + automated SSL.
* **Streamlit Cloud + Cloudflare Worker**: Free proxy with root `/robots.txt` and `/sitemap.xml`.
* **Google Search Console**: Step-by-step verification and sitemap submission.
