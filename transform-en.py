#!/usr/bin/env python3
"""Transform apps/web/translations/en.json for the Dosco Agent Network reskin.

Branding is applied to a CLEAN checkout (apply.sh runs `git checkout` first),
so this script can safely rewrite every string value:
  * Kortix / Suna  -> Dosco (product) ; "Kortix Computer" -> "Dosco Agent"
  * remove "open source" / "self-host" / "MIT-licensed" phrasing
  * neutralize GitHub / kortix.com external URLs
  * repoint *@kortix.com emails to the Dosco support address
Keys are preserved (only string values are touched) so references never break.
"""
import json
import re
import sys

PATH = sys.argv[1]
EMAIL = sys.argv[2] if len(sys.argv) > 2 else "support@dosco.example.com"
CANON = sys.argv[3] if len(sys.argv) > 3 else "https://dosco.example.com"


def transform(s: str) -> str:
    if not isinstance(s, str):
        return s

    # --- product naming ---
    s = s.replace("Kortix Computer", "Dosco Agent")
    s = s.replace("Kortix", "Dosco")
    s = s.replace("Suna", "Dosco")  # old product name, fully rebrand

    # --- tagline: "open-source AI Management System" -> "Dosco Agent Terminal" ---
    s = s.replace("open-source AI Management System", "Dosco Agent Terminal")
    s = s.replace("open-source AI management system", "Dosco Agent Terminal")
    s = s.replace("open source AI Management System", "Dosco Agent Terminal")

    # --- remove open-source / self-host phrasing (adjectives) ---
    s = re.sub(r"open[\s-]?source", "", s, flags=re.IGNORECASE)
    s = re.sub(r"self[\s-]?host(?:able)?", "", s, flags=re.IGNORECASE)
    s = re.sub(r"MIT[\s-]?licensed", "", s, flags=re.IGNORECASE)

    # --- github / open-source button labels ---
    s = s.replace("Star on GitHub", "Star")
    s = s.replace("View on GitHub", "View project")
    s = s.replace("stars on GitHub", "stars")

    # --- self-host install snippet ---
    s = s.replace(
        "curl -fsSL kortix.com/install",
        "Contact your administrator for access",
    )

    # --- emails ---
    s = re.sub(r"[\w.+-]+@kortix\.com", EMAIL, s)

    # --- external URLs -> neutralize / repoint ---
    s = s.replace("https://github.com/kortix-ai/suna", "#")
    s = s.replace("https://github.com/kortix-ai", "#")
    s = s.replace("https://status.kortix.com", "#")
    s = s.replace("https://x.com/kortix", "#")
    s = s.replace("https://linkedin.com/company/kortix", "#")
    s = s.replace("https://kortix.com", CANON)
    s = s.replace("kortix.com/install", "#")
    s = s.replace("kortix.com", CANON)

    # --- clean up artifacts left by removals ---
    s = re.sub(r"\s{2,}", " ", s)
    s = s.replace(" ,", ",").replace(" .", ".").replace(" :", ":")
    s = s.replace("( ", "(").replace(" )", ")")
    s = re.sub(r"\s*[-–—]\s*$", "", s)
    s = s.replace(" - ", " ").replace(" – ", " ").replace(" — ", " ")
    s = s.strip()
    s = s.strip(" ,.-")
    return s


def walk(o):
    if isinstance(o, dict):
        return {k: walk(v) for k, v in o.items()}
    if isinstance(o, list):
        return [walk(v) for v in o]
    if isinstance(o, str):
        return transform(o)
    return o


with open(PATH, encoding="utf-8") as f:
    data = json.load(f)

data = walk(data)

with open(PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")

print(f"[transform-en] rewrote {PATH}")
