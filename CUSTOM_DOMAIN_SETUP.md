# 🌐 100% Free Custom Domain Deployment Guide

You can connect your own custom domain (e.g., `scanner.yourdomain.com` or `yourdomain.com`) to this application with free SSL without paying any hosting fees.

---

## Method 1: Render.com (Recommended for Native Custom Domains)

Render's free tier provides native custom domain mapping with free automatic Let's Encrypt SSL.

### Step 1: Deploy on Render
1. Push your project to GitHub.
2. Sign up at [Render.com](https://render.com) (free).
3. Click **"New +" ➔ "Web Service"** and connect your GitHub repository.
4. Fill in the settings:
   * **Runtime**: `Python 3`
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
   * **Instance Type**: `Free`
5. Click **"Deploy Web Service"**.

### Step 2: Add Your Custom Domain
1. In your Render service dashboard, click **Settings** ➔ Scroll down to **Custom Domains**.
2. Click **Add Custom Domain** and enter your domain (e.g., `scanner.yourdomain.com` or `yourdomain.com`).
3. Render will give you a target CNAME (e.g. `your-app.onrender.com`).

### Step 3: Configure Your DNS
Go to your domain registrar or DNS manager (Cloudflare, Namecheap, GoDaddy):
* **Record Type**: `CNAME`
* **Host / Name**: `scanner` (or `@` for root domain)
* **Target / Value**: `your-app.onrender.com`
* **TTL**: Auto / 5 minutes

Render will verify the DNS and issue your free SSL certificate automatically within 2–5 minutes.

---

## Method 2: Streamlit Cloud + Cloudflare Worker (Zero Cold Starts)

If you host on **Streamlit Community Cloud** (`https://yourapp.streamlit.app`), you can map your custom domain to it for free using a lightweight Cloudflare Worker.

### Step 1: Deploy on Streamlit Cloud
1. Push to GitHub and deploy on [share.streamlit.io](https://share.streamlit.io).
2. Note your free URL (e.g. `https://my-domain-scanner.streamlit.app`).

### Step 2: Create a Free Cloudflare Worker
1. Log in to [Cloudflare](https://dash.cloudflare.com) (free).
2. Go to **Workers & Pages** ➔ Click **Create Application** ➔ **Create Worker**.
3. Click **Quick Edit** and paste this exact code:

```javascript
export default {
  async fetch(request) {
    const url = new URL(request.url);

    // 1. Direct SEO Robots.txt & Sitemap serving
    if (url.pathname === "/robots.txt") {
      return new Response(
        "User-agent: *\nAllow: /\nDisallow: /data/\n\nSitemap: " + url.origin + "/sitemap.xml",
        { headers: { "Content-Type": "text/plain" } }
      );
    }
    if (url.pathname === "/sitemap.xml") {
      return new Response(
        `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>${url.origin}/</loc>
    <lastmod>${new Date().toISOString().split('T')[0]}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>`,
        { headers: { "Content-Type": "application/xml" } }
      );
    }

    // 2. Proxy all other traffic to Streamlit App
    url.hostname = "my-domain-scanner.streamlit.app"; // <-- Replace with your Streamlit app hostname
    const newRequest = new Request(url.toString(), {
      method: request.method,
      headers: request.headers,
      body: request.body,
      redirect: "follow",
    });
    return fetch(newRequest);
  }
};
```

4. Click **Save and Deploy**.

### Step 3: Route Your Custom Domain to the Worker
1. In Cloudflare, go to **Websites** ➔ Select your domain ➔ **Workers Routes**.
2. Click **Add Route**:
   * **Route**: `scanner.yourdomain.com/*`
   * **Worker**: Select the worker you just created.
3. In Cloudflare DNS, add a dummy `CNAME`:
   * **Name**: `scanner`
   * **Target**: `100::` (or any proxy IP)
   * **Proxy Status**: Proxied (Orange Cloud)

Your custom domain `scanner.yourdomain.com` now serves your Streamlit scanner with full HTTPS, fast global caching, and root `/robots.txt` and `/sitemap.xml`!

---

## 📈 Google Search Console (SEO Indexing Steps)

To rank on Google as quickly as possible:

1. **Verify Ownership**:
   * Go to [Google Search Console](https://search.google.com/search-console).
   * Choose **URL Prefix** (e.g. `https://scanner.yourdomain.com`).
   * Select **HTML Tag** verification. Copy the code (e.g. `google-site-verification=XYZ123`).
   * Open `config.py` and set:
     ```python
     GOOGLE_SITE_VERIFICATION = "XYZ123"
     SITE_URL = "https://scanner.yourdomain.com"
     ```
   * Click **Verify** in Search Console.

2. **Submit Your Sitemap**:
   * In Search Console ➔ **Sitemaps**.
   * Submit: `https://scanner.yourdomain.com/sitemap.xml`.
   * Google will schedule immediate crawling.

3. **Verify Rich Results / FAQ Schema**:
   * Test your live URL at [Google Rich Results Test](https://search.google.com/test/rich-results).
   * Confirm that both **WebApplication** and **FAQPage** structured data are detected. This enables rich dropdown FAQ snippets in Google search results.
