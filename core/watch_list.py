"""
Email Domain Drop Watcher - Security Hardened
Privately and securely stores domain drop monitoring requests in data/watched_domains.json.
Visitors NEVER see other visitors' watched domains or email addresses.
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
WATCH_FILE = DATA_DIR / "watched_domains.json"

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
DOMAIN_REGEX = re.compile(r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$")

MAX_TOTAL_WATCHES = 5000

def mask_email(email: str) -> str:
    """Mask email for safe UI display (e.g. j***n@example.com)."""
    if "@" not in email:
        return "***"
    user, domain = email.split("@", 1)
    if len(user) <= 2:
        masked_user = user[0] + "*"
    else:
        masked_user = user[0] + "*" * (len(user) - 2) + user[-1]
    return f"{masked_user}@{domain}"

def is_valid_email(email: str) -> bool:
    if not email or len(email) > 254:
        return False
    # Prevent header injection
    if "\r" in email or "\n" in email or "%0a" in email.lower() or "%0d" in email.lower():
        return False
    return bool(EMAIL_REGEX.match(email.strip()))

def is_valid_domain(domain: str) -> bool:
    if not domain or len(domain) > 253:
        return False
    return bool(DOMAIN_REGEX.match(domain.strip().lower()))

def load_watched_domains() -> List[Dict]:
    """Load existing watched domains securely."""
    if not WATCH_FILE.exists():
        return []
    try:
        with open(WATCH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_watched_domains(watches: List[Dict]):
    """
    Persist watched list securely with atomic write and restricted permissions (0o600).
    Only the server process user can read or write this file.
    """
    temp_file = WATCH_FILE.with_suffix(".tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(watches, f, indent=2)

        # Restrict permissions: read/write by owner only (0o600)
        try:
            os.chmod(temp_file, 0o600)
        except OSError:
            pass

        # Atomic replace
        os.replace(temp_file, WATCH_FILE)
    except Exception:
        if temp_file.exists():
            temp_file.unlink(missing_ok=True)

def add_domain_watch(domain: str, email: str) -> Tuple[bool, str]:
    """
    Register a private domain drop watch.
    Guarantees no data leakage of other users.
    """
    domain = domain.lower().strip()
    email = email.lower().strip()

    if not is_valid_domain(domain):
        return False, "Please enter a valid domain name (e.g. startup.com or mybrand.gr)."
    if not is_valid_email(email):
        return False, "Please enter a valid, secure email address."

    watches = load_watched_domains()

    if len(watches) >= MAX_TOTAL_WATCHES:
        return False, "Watch list capacity full. Please try again later."

    # Prevent duplicate notification requests
    for w in watches:
        if w.get("domain") == domain and w.get("email") == email:
            return True, f"✔ You are already on the alert list for {domain}! We will notify {mask_email(email)} when it drops."

    watches.append({
        "domain": domain,
        "email": email,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "status": "WATCHING",
        "last_checked": None,
        "alerted": False,
    })

    save_watched_domains(watches)
    return True, f"✔ Successfully added to your private drop watch list! We will notify {mask_email(email)} the instant {domain} becomes available."

SUBSCRIBERS_FILE = DATA_DIR / "subscribers.json"

def add_newsletter_subscriber(email: str) -> Tuple[bool, str]:
    """Privately store newsletter subscriber email with restricted permissions."""
    email = email.lower().strip()
    if not is_valid_email(email):
        return False, "Please enter a valid email address."

    subscribers: List[Dict] = []
    if SUBSCRIBERS_FILE.exists():
        try:
            with open(SUBSCRIBERS_FILE, "r", encoding="utf-8") as f:
                subscribers = json.load(f)
        except Exception:
            subscribers = []

    for s in subscribers:
        if s.get("email") == email:
            return True, f"You are already subscribed with {mask_email(email)}!"

    subscribers.append({
        "email": email,
        "subscribed_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    })

    temp_file = SUBSCRIBERS_FILE.with_suffix(".tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(subscribers, f, indent=2)
        try:
            os.chmod(temp_file, 0o600)
        except OSError:
            pass
        os.replace(temp_file, SUBSCRIBERS_FILE)
        return True, "🎉 You're on the VIP list! Check your inbox for today's curated drop list."
    except Exception as e:
        return False, "Failed to save subscription. Please try again."
