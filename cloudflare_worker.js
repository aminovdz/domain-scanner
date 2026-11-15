/**
 * Cloudflare Worker: SEO Pre-Renderer & Proxy for DomainSuite Pro
 * 
 * Features:
 * 1. Delivers complete, pre-rendered semantic HTML to Googlebot, Bingbot, social crawlers.
 * 2. Directly serves /robots.txt and /sitemap.xml with correct headers.
 * 3. Transparently proxies regular users to the live Render app with WebSocket/Streamlit support.
 */

const UPSTREAM_HOST = "domainsuite-pro.onrender.com"; // <-- Replace with your Render.com hostname if different
const CANONICAL_DOMAIN = "https://yourdomain.com"; // <-- Replace with your real domain

const CRAWLER_USER_AGENTS = [
  "googlebot",
  "bingbot",
  "yandex",
  "baiduspider",
  "facebookexternalhit",
  "twitterbot",
  "rogerbot",
  "linkedinbot",
  "embedly",
  "quora link preview",
  "showyoubot",
  "outbrain",
  "pinterest",
  "developers.google.com/+/web/snippet",
  "slackbot",
  "vkshare",
  "w3c_validator",
  "redditbot",
  "applebot",
  "whatsapp",
  "flipboard",
  "tumblr",
  "bitlybot",
  "skypeuripreview",
  "nuzzel",
  "discordbot",
  "google-pageinsight",
  "qwantify",
  "pinterestbot",
  "bitrix link preview",
  "xing-content-gathering"
];

function isBot(userAgent) {
  if (!userAgent) return false;
  const ua = userAgent.toLowerCase();
  return CRAWLER_USER_AGENTS.some(bot => ua.includes(bot));
}

function getCrawlerHTML(origin) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Free Bulk Domain Checker — .com .gr .ai .io & 50+ TLDs | DomainSuite</title>
  <meta name="description" content="Instantly check bulk domain availability across .com, .gr, .ai, .io & 50+ extensions. Free WHOIS lookup, DNS explorer, domain drop watcher & brandable name generator. No signup needed.">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
  <link rel="canonical" href="${origin}/">
  <meta property="og:type" content="website">
  <meta property="og:url" content="${origin}/">
  <meta property="og:title" content="Free Bulk Domain Checker — .com .gr .ai .io & 50+ TLDs | DomainSuite">
  <meta property="og:description" content="Instantly check bulk domain availability across .com, .gr, .ai, .io & 50+ extensions. Free WHOIS lookup, DNS explorer, domain drop watcher & brandable name generator. No signup needed.">
  <meta property="og:image" content="${origin}/og-preview.png">
  <meta property="og:site_name" content="DomainSuite Pro">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Free Bulk Domain Checker — .com .gr .ai .io & 50+ TLDs | DomainSuite">
  <meta name="twitter:description" content="Instantly check bulk domain availability across .com, .gr, .ai, .io & 50+ extensions. Free WHOIS lookup, DNS explorer, domain drop watcher & brandable name generator.">
  <meta name="twitter:image" content="${origin}/og-preview.png">
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "WebApplication",
        "@id": "${origin}/#webapp",
        "name": "DomainSuite Pro",
        "url": "${origin}/",
        "description": "Free high-speed bulk domain availability checker for .com, .gr, .ai, .io, and 50+ extensions.",
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "All",
        "browserRequirements": "Requires JavaScript",
        "offers": {
          "@type": "Offer",
          "price": "0",
          "priceCurrency": "USD"
        }
      },
      {
        "@type": "FAQPage",
        "@id": "${origin}/#faq",
        "mainEntity": [
          {
            "@type": "Question",
            "name": "How does the bulk domain availability checker work?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "DomainSuite uses an asynchronous multi-tier pipeline: first querying active A, AAAA, NS, and MX DNS records in parallel. Unassigned domains are verified against official ICANN RDAP endpoints and registry WHOIS servers."
            }
          },
          {
            "@type": "Question",
            "name": "Can I check Greek (.gr) domain names in bulk?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "Yes! DomainSuite natively resolves Greek (.gr) domains against authoritative ICS-FORTH registry nameservers, accurately identifying NXDOMAIN states with 1-click registration links on Papaki, Namecheap, and GoDaddy."
            }
          },
          {
            "@type": "Question",
            "name": "Is DomainSuite completely free to use?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "Yes, DomainSuite is 100% free with no registration required. You can scan up to 500 domains simultaneously, format URL protocols, lookup WHOIS records, and monitor dropped domains."
            }
          }
        ]
      },
      {
        "@type": "HowTo",
        "@id": "${origin}/#howto",
        "name": "How to Check Domain Availability in Bulk",
        "description": "Step-by-step guide to scanning multiple domain names at once using DomainSuite Pro",
        "step": [
          {
            "@type": "HowToStep",
            "position": 1,
            "name": "Enter domain names",
            "text": "Type or paste your domain names one per line into the text area, or upload a .txt or .csv file."
          },
          {
            "@type": "HowToStep",
            "position": 2,
            "name": "Select extensions to scan",
            "text": "Choose which TLDs to scan: .com, .gr, .ai, .io, or select all supported extensions simultaneously."
          },
          {
            "@type": "HowToStep",
            "position": 3,
            "name": "Run the bulk scan",
            "text": "Click the Scan button. The multi-tier engine checks DNS records, RDAP endpoints, and WHOIS in parallel."
          },
          {
            "@type": "HowToStep",
            "position": 4,
            "name": "Register available domains",
            "text": "Click the registration button next to any available domain to claim it on Namecheap, Porkbun, Papaki (.gr), or GoDaddy."
          }
        ]
      }
    ]
  }
  </script>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 900px; margin: 40px auto; padding: 0 20px; color: #1e293b;">
  <header>
    <h1>⚡ DomainSuite Pro — Bulk Domain Availability Checker & Greek (.GR) Scanner</h1>
    <p>High-speed, multi-tier asynchronous domain scanner supporting .com, .gr, .ai, .io, and 50+ extensions with 1-click registrar links.</p>
  </header>
  <main>
    <section>
      <h2>Supported Tools</h2>
      <ul>
        <li><strong>Bulk Domain Availability Scanner:</strong> Scan up to 500 domains across multiple TLDs at once.</li>
        <li><strong>Native Greek (.GR) TLD Scanner:</strong> Authoritative ICS-FORTH registry NXDOMAIN lookup.</li>
        <li><strong>WHOIS & DNS Record Inspector:</strong> Deep inspection of A, AAAA, MX, TXT, NS, CNAME, SOA records.</li>
        <li><strong>Domain Extractor:</strong> Extract clean domains from raw text and format protocol prefixes.</li>
        <li><strong>Brandable Name Generator:</strong> Generate 4-letter CVCV, 5-letter brandable, and keyword affixes.</li>
        <li><strong>Domain Drop Watcher:</strong> Private automated alerts when monitored domains become available.</li>
      </ul>
    </section>
    <section>
      <h2>Frequently Asked Questions</h2>
      <article>
        <h3>How does the multi-tier verification engine work?</h3>
        <p>DomainSuite combines async DNS queries (<50ms) to filter out 90%+ taken domains without hitting registry limits, authoritative ICANN RDAP REST queries, and authoritative registry checks for ccTLDs like .gr.</p>
      </article>
      <article>
        <h3>How can I register domains found to be available?</h3>
        <p>1-click registration links are generated for Porkbun, Namecheap, Papaki (for Greek .gr domains), and GoDaddy.</p>
      </article>
    </section>
  </main>
  <footer style="margin-top: 40px; border-top: 1px solid #e2e8f0; padding-top: 20px; font-size: 0.9em; color: #64748b;">
    <p>DomainSuite Pro &bull; Free Online Domain Intelligence Suite</p>
  </footer>
</body>
</html>`;
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const origin = url.origin;

    // 1. Robots.txt handler
    if (url.pathname === "/robots.txt") {
      return new Response(
        `User-agent: *\nAllow: /\nDisallow: /data/\n\nSitemap: ${origin}/sitemap.xml\n`,
        {
          headers: {
            "Content-Type": "text/plain; charset=utf-8",
            "Cache-Control": "public, max-age=86400"
          }
        }
      );
    }

    // 2. Sitemap.xml handler
    if (url.pathname === "/sitemap.xml") {
      const today = new Date().toISOString().split("T")[0];
      return new Response(
        `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>${origin}/</loc>
    <lastmod>${today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>`,
        {
          headers: {
            "Content-Type": "application/xml; charset=utf-8",
            "Cache-Control": "public, max-age=86400"
          }
        }
      );
    }

    // 3. Search Engine Crawler & Social Media Pre-render Check
    const userAgent = request.headers.get("User-Agent") || "";
    if (isBot(userAgent) && (url.pathname === "/" || url.pathname === "")) {
      return new Response(getCrawlerHTML(origin), {
        headers: {
          "Content-Type": "text/html; charset=utf-8",
          "Cache-Control": "public, max-age=3600"
        }
      });
    }

    // 4. Proxy all user/browser traffic to the upstream Render application
    url.hostname = UPSTREAM_HOST;
    url.protocol = "https:";
    url.port = "";

    const headers = new Headers(request.headers);
    headers.set("Host", UPSTREAM_HOST);
    headers.set("X-Forwarded-Host", url.hostname);
    headers.set("X-Forwarded-Proto", "https");

    // Support WebSocket upgrade for Streamlit
    return fetch(url.toString(), {
      method: request.method,
      headers: headers,
      body: request.body,
      redirect: "follow"
    });
  }
};
