#!/usr/bin/env python3
"""Dosco brand pass over apps/api/src (and its tests).

Run manually after an upstream sync — NOT from apply.sh (which stamps
apps/web per build). Idempotent: every rule maps upstream wording to Dosco
wording; re-runs are no-ops once applied.

Rules mirror transform-en.py's spirit for backend copy:
  * whole-word `Kortix` -> `Dosco` (`Kortix Computer` -> `Dosco Agent` first)
  * kortix.* hosts -> dosco.live equivalents (ordered, longest first)
  * *@kortix.com/ai -> same local-part @dosco.live (noreply stays noreply)
Kept verbatim: real CLI invocations, X-Kortix-* wire headers, lowercase
ids/paths/packages/bins, kortix-appd, test-fixture domains (*.test etc.),
CORS entries are REWRITTEN (self-host serves dosco.live origins).
"""
import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "apps/api/src"

PH = "\x00HDR\x00"

URLS = [
    ("gateway-dev.kortix.com", "gateway-dev.dosco.live"),
    ("dev-api.kortix.com", "dev-api.dosco.live"),
    ("api.kortix.com", "api.dosco.live"),
    ("new-dev.kortix.com", "new-dev.dosco.live"),
    ("dev-new.kortix.com", "dev-new.dosco.live"),
    ("dev.kortix.com", "dev.dosco.live"),
    ("staging.kortix.com", "staging.dosco.live"),
    ("new.kortix.com", "new.dosco.live"),
    ("preview.kortix.com", "preview.dosco.live"),
    ("docs.kortix.com", "dosco.live/docs"),
    ("apps.kortix.com", "apps.dosco.live"),
    ("www.kortix.cloud", "www.dosco.live"),
    ("kortix.cloud", "dosco.live"),
    ("essentia.kortix.cloud", "essentia.dosco.live"),
    ("www.kortix.com", "dosco.live"),
    ("kortix.com", "dosco.live"),
    ("kortix.ai", "dosco.live"),
]

# Fixture domains used by tests — renaming them buys nothing and churns
# fixtures. Matched before the generic rules so they survive.
FIXTURE_RE = re.compile(r"[A-Za-z0-9.-]*kortix(?:\.test|\.example|ssotest)[A-Za-z0-9.-]*", re.IGNORECASE)


def transform(s: str) -> str:
    # protect wire-protocol headers (clients send them verbatim)
    hdrs = re.findall(r"X-Kortix[A-Za-z-]*", s)
    s = re.sub(r"X-Kortix[A-Za-z-]*", PH, s)
    s = s.replace("Kortix Computer", "Dosco Agent")
    s = re.sub(r"\bKortix\b", "Dosco", s)
    # protect fixture domains before host swaps
    fixt = FIXTURE_RE.findall(s)
    s = FIXTURE_RE.sub("\x00FIX\x00", s)
    for a, b in URLS:
        s = s.replace(a, b)
    for f in fixt:
        s = s.replace("\x00FIX\x00", f, 1)
    s = s.replace("noreply@kortix.ai", "noreply@dosco.live")
    s = s.replace("noreply@kortix.com", "noreply@dosco.live")
    s = re.sub(
        r"[\w.+-]+@kortix\.(?:com|ai)\b",
        lambda m: m.group(0).split("@")[0] + "@dosco.live",
        s,
    )
    # internal default pointed at a nonexistent host; compose serves llm-gateway
    s = s.replace("http://kortix-gateway:8090", "http://llm-gateway:8090")
    for h in hdrs:
        s = s.replace(PH, h, 1)
    assert PH not in s and "\x00FIX\x00" not in s
    return s


def main() -> None:
    nfiles = 0
    for dp, _, fs in os.walk(ROOT):
        for f in sorted(fs):
            if not f.endswith(".ts"):
                continue
            p = os.path.join(dp, f)
            s = open(p, encoding="utf-8").read()
            t = transform(s)
            if t != s:
                open(p, "w", encoding="utf-8").write(t)
                nfiles += 1
    print(f"[patch-api] touched {nfiles} files under {ROOT}")


if __name__ == "__main__":
    main()
