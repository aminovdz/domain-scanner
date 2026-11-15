"""
Short & Brandable Domain Generator
Generates pronounceable 4-letter CVCV, 5-letter names, and modern tech startup words.
"""

import itertools
import random
from typing import List, Set

CONSONANTS = "bcdfghjklmnprstvwxz"
VOWELS = "aeiou"

PREMIUM_TECH_SUFFIXES = ["flow", "sync", "byte", "loop", "node", "nest", "core", "cube", "grid", "stack", "lab", "hub", "bot"]
PREMIUM_TECH_PREFIXES = ["omni", "meta", "hyper", "cyber", "open", "neo", "syn", "zen", "flex", "auto", "data"]

def generate_cvcv_domains(tlds: List[str], count: int = 40) -> List[str]:
    """Generate pronounceable 4-letter Consonant-Vowel-Consonant-Vowel domains."""
    names: Set[str] = set()
    tlds = [t.lstrip(".") for t in tlds]

    # Weighted smooth consonants
    smooth_c = "bdfklmnprstv"
    v = "aeiou"

    attempts = 0
    while len(names) < count and attempts < 1000:
        attempts += 1
        c1 = random.choice(smooth_c)
        v1 = random.choice(v)
        c2 = random.choice(smooth_c)
        v2 = random.choice(v)
        word = f"{c1}{v1}{c2}{v2}"
        for tld in tlds:
            names.add(f"{word}.{tld}")

    return sorted(list(names))[:count]

def generate_5letter_brandables(tlds: List[str], count: int = 40) -> List[str]:
    """Generate 5-letter modern pronounceable brandable domains."""
    names: Set[str] = set()
    tlds = [t.lstrip(".") for t in tlds]

    patterns = ["cvcvc", "cvvcv", "vcvcv"]
    c_set = "bcdfgklmnprstvz"
    v_set = "aeiou"

    attempts = 0
    while len(names) < count and attempts < 1500:
        attempts += 1
        pat = random.choice(patterns)
        chars = [random.choice(c_set) if p == "c" else random.choice(v_set) for p in pat]
        word = "".join(chars)
        for tld in tlds:
            names.add(f"{word}.{tld}")

    return sorted(list(names))[:count]

def generate_prefix_suffix_combos(keywords: List[str], tlds: List[str], count: int = 50) -> List[str]:
    """Combine root keywords with tech affixes."""
    names: Set[str] = set()
    tlds = [t.lstrip(".") for t in tlds]

    for kw in keywords:
        kw = kw.strip().lower()
        if not kw:
            continue
        for tld in tlds:
            # Exact
            names.add(f"{kw}.{tld}")
            # Prefixes
            for pfx in PREMIUM_TECH_PREFIXES[:6]:
                names.add(f"{pfx}{kw}.{tld}")
            # Suffixes
            for sfx in PREMIUM_TECH_SUFFIXES[:6]:
                names.add(f"{kw}{sfx}.{tld}")

    return sorted(list(names))[:count]
