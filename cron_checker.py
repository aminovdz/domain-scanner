#!/usr/bin/env python3
"""
Cron Drop Checker & Email Notification Dispatcher
Run via system crontab (e.g. every 6 hours):
    0 */6 * * * cd /path/to/domain-scanner && python3 cron_checker.py >> data/cron.log 2>&1

Scans watched domains in data/watched_domains.json. When a watched domain drops,
it sends an automated email notification with 1-click registration links.
"""

import asyncio
from datetime import datetime, timezone
import email.message
import smtplib
from pathlib import Path
from core.checker import DomainChecker, DomainStatus
from core.watch_list import load_watched_domains, save_watched_domains

try:
    from config import SMTP_CONFIG
except ImportError:
    SMTP_CONFIG = {"ENABLED": False}

def send_email_alert(to_email: str, domain: str, buy_links: dict):
    """Dispatch email alert via configured SMTP server."""
    if not SMTP_CONFIG.get("ENABLED", False):
        print(f"[SIMULATED EMAIL] Domain {domain} is AVAILABLE! Would notify {to_email}.")
        return True

    msg = email.message.EmailMessage()
    msg["Subject"] = f"🚨 Alert: Watched Domain '{domain}' is now AVAILABLE to Buy!"
    msg["From"] = f"{SMTP_CONFIG.get('FROM_NAME', 'Domain Drop Alert')} <{SMTP_CONFIG.get('SENDER_EMAIL')}>"
    msg["To"] = to_email

    links_text = "\n".join([f"- {name}: {url}" for name, url in buy_links.items() if name in ["Porkbun", "Namecheap", "Papaki", "GoDaddy"]])

    body = f"""Hello,

Great news! The domain you were watching:

    👉 {domain}

has just dropped or expired and is now AVAILABLE for public registration!

Register it now before someone else grabs it:
{links_text}

---
DomainSuite Drop Watcher Alert Service
"""
    msg.set_content(body)

    try:
        server = smtplib.SMTP(SMTP_CONFIG["SMTP_SERVER"], SMTP_CONFIG["SMTP_PORT"])
        server.starttls()
        server.login(SMTP_CONFIG["SENDER_EMAIL"], SMTP_CONFIG["SENDER_PASSWORD"])
        server.send_message(msg)
        server.quit()
        print(f"[EMAIL SENT] Successfully notified {to_email} for {domain}")
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email to {to_email}: {e}")
        return False

async def run_cron():
    print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Running automated domain drop check...")
    watches = load_watched_domains()
    if not watches:
        print("No domains on watch list.")
        return

    active_watches = [w for w in watches if w.get("status") == "WATCHING" and not w.get("alerted", False)]
    if not active_watches:
        print("No active un-alerted domains to check.")
        return

    checker = DomainChecker(dns_concurrency=20, timeout=4.0)
    domains_to_check = list(set([w["domain"] for w in active_watches]))
    print(f"Checking {len(domains_to_check)} unique watched domains...")

    results = await checker.check_all(domains_to_check)
    res_map = {r.domain: r for r in results}

    updated_count = 0
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    for w in watches:
        d = w["domain"]
        if d in res_map:
            r = res_map[d]
            w["last_checked"] = now_str
            if r.status == DomainStatus.AVAILABLE and not w.get("alerted", False):
                print(f"🎉 FOUND AVAILABLE: {d} -> Notifying {w['email']}")
                sent = send_email_alert(w["email"], d, r.buy_links)
                if sent:
                    w["alerted"] = True
                    w["alerted_at"] = now_str
                    w["status"] = "ALERTED"
                updated_count += 1

    save_watched_domains(watches)
    print(f"Done. Processed {len(active_watches)} watches, {updated_count} alerts triggered.\n")

if __name__ == "__main__":
    asyncio.run(run_cron())
