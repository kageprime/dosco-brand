#!/usr/bin/env bash
# Stamp Dosco Agent Network branding onto a CLEAN Suna checkout.
# Branding lives ONLY here (in dosco-brand/) — the Suna repo never stores it,
# so `git fetch upstream && git reset --hard upstream/main` is always clean.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=config.sh
source "$DIR/config.sh"

REPO="$SUNA_REPO"
WEB="$REPO/apps/web"

echo "[apply] using repo: $REPO"
cd "$REPO"

# 1) Ensure a pristine base so re-application is idempotent & pull-safe.
git checkout -- apps/web 2>/dev/null || true

# 2) Stamp real Dosco brand assets (light/dark/icon mapping + derived sizes).
#    SVG slots get wrappers with the PNG embedded, so hardcoded .svg paths work.
LOGO_DARK="$DIR/assets/doscologo-dark.png"
LOGO_LIGHT="$DIR/assets/doscologo-light.png"
LOGO_ICON="$DIR/assets/doscologoIcon.png"
for f in "$LOGO_DARK" "$LOGO_LIGHT" "$LOGO_ICON"; do
  [ -f "$f" ] || { echo "[apply] ERROR: missing brand asset $f" >&2; exit 1; }
done

echo "[apply] stamping Dosco brand assets (light/dark/icon)..."
python3 "$DIR/stamp-assets.py" "$WEB/public"
echo "[apply] asset replacement done (marketing .mp4/.webm videos left as-is)."

# 3) Rebrand the i18n strings (the bulk of user-facing "Kortix" text).
echo "[apply] transforming en.json..."
python3 "$DIR/transform-en.py" "$WEB/translations/en.json" "$DOSCO_SUPPORT_EMAIL" "$DOSCO_CANONICAL"

# 4) Patch site metadata (page title / SEO).
echo "[apply] patching site-metadata.ts..."
python3 - "$DOSCO_CANONICAL" <<'PY'
import sys
canon = sys.argv[1]
p = "apps/web/src/lib/site-metadata.ts"
s = open(p, encoding="utf-8").read()
s = s.replace(
    "export const CANONICAL_ORIGIN = 'https://kortix.com';",
    f"export const CANONICAL_ORIGIN = '{canon}';",
)
s = s.replace("name: 'Kortix',", "name: 'Dosco Agent Network',")
s = s.replace(
    "title: 'Kortix – The AI Command Center for Your Company',",
    "title: 'Dosco Agent Network – The AI Command Center for Your Company',",
)
s = s.replace(
    "Kortix, AI command center, autonomous company operating system",
    "Dosco Agent Network, the private AI command center for your company",
)
s = s.replace(
    "The open-source AI command center for your company.",
    "The private AI command center for your company.",
)
# strip any remaining open-source / self-host phrasing in this file.
# Grammar-aware (mirrors transform-en.py): consume ed/ing/able forms whole,
# collapse only space/comma debris, never touch periods or dashes. Also
# repairs debris stamped by the old naive pass ('CLI. , any model',
# 'ed AI agents') which is committed to HEAD.
import re
s = s.replace(
    "or the CLI. , any model, your keys.",
    "or the CLI. Any model, your keys.",
)
s = s.replace(
    "AI platform, ed AI agents,",
    "AI platform, private AI agents,",
)
s = re.sub(r"open[\s-]?source", "", s, flags=re.IGNORECASE)
s = re.sub(r"self[\s-]?host(?:able|ed|ing)?", "", s, flags=re.IGNORECASE)
s = re.sub(r"MIT[\s-]?licensed", "", s, flags=re.IGNORECASE)
s = re.sub(r" {2,}", " ", s)
s = re.sub(r",\s*,", ",", s)
s = re.sub(r"\.\s*,\s*", ". ", s)
open(p, "w", encoding="utf-8").write(s)
PY

# 4b) Patch robots policy host + visitor-pixel host + their tests.
# robots.ts gates the Allow-all policy on CANONICAL_HOSTS={'kortix.com',...},
# so dosco.live serves blanket Disallow (de-indexed). layout.tsx gates the
# visitor pixel on the kortix.com host, so it never loads on dosco.live.
# The two robots tests assert on kortix.com hosts and move with the fix.
echo "[apply] patching robots.ts + layout.tsx site host..."
python3 - "$DOSCO_CANONICAL" <<'PY'
import re
import sys

canon = sys.argv[1].rstrip("/")
host = re.sub(r"^https?://", "", canon).split("/")[0]
www = f"www.{host}" if not host.startswith("www.") else host

p = "apps/web/src/lib/seo/robots.ts"
s = open(p, encoding="utf-8").read()
s = re.sub(
    r"const CANONICAL_HOSTS = new Set\(\[.*?\]\)",
    f"const CANONICAL_HOSTS = new Set(['{host}', '{www}'])",
    s,
    flags=re.DOTALL,
)
s = s.replace(".kortix.com", f".{host}").replace("kortix.com", host)
open(p, "w", encoding="utf-8").write(s)
print("[apply] OK: robots.ts canonical hosts ->", host)

lp = "apps/web/src/app/layout.tsx"
s = open(lp, encoding="utf-8").read()
s = s.replace("isKortixSiteHost", "isDoscoSiteHost")
s = s.replace("'kortix.com'", f"'{host}'").replace("'.kortix.com'", f"'.{host}'")
open(lp, "w", encoding="utf-8").write(s)
print("[apply] OK: layout.tsx site host ->", host)

for tp in (
    "apps/web/src/lib/agent-discovery.test.ts",
    "apps/web/src/lib/seo/public-content.test.ts",
):
    try:
        t = open(tp, encoding="utf-8").read()
    except FileNotFoundError:
        continue
    before = t
    t = t.replace("renderRobotsTxt('kortix.com')", f"renderRobotsTxt('{host}')")
    t = t.replace("dev.kortix.com", f"dev.{host}").replace(
        "staging.kortix.com", f"staging.{host}"
    )
    if t != before:
        open(tp, "w", encoding="utf-8").write(t)
        print(f"[apply] OK: {tp} test hosts -> {host}")
PY
# 5) Patch manifest.json.
echo "[apply] patching manifest.json..."
python3 - <<'PY'
import json
import re
p = "apps/web/public/manifest.json"
d = json.load(open(p, encoding="utf-8"))
d["name"] = "Dosco Agent Network"
d["short_name"] = "Dosco"
d["description"] = re.sub(
    r" {2,}",
    " ",
    (
        d.get("description", "")
        .replace("Kortix", "Dosco")
        .replace("open-source", "")
        .replace("open source", "")
    ),
).strip()
# Kortix native-app store listings: Dosco ships no native wrapper, so drop
# the prompt-to-install-Kortix-app entirely (fixes the "the  AI" double
# space left by the old removal too).
d.pop("related_applications", None)
d["prefer_related_applications"] = False
json.dump(d, open(p, "w", encoding="utf-8"), indent=2)
open(p, "a").write("\n")
PY

# 6) Remove external Kortix / GitHub / social links from the nav + footer,
#    and rebrand any remaining "Kortix" text values in site-config.ts.
echo "[apply] neutralizing external links in site-config.ts..."
SC="$WEB/src/lib/site-config.ts"
if [ -f "$SC" ]; then
  # delete whole lines that point at Kortix social / external properties
  sed -i -E "/x\.com\/kortix/d; /linkedin\.com\/company\/kortix/d; /github\.com\/kortix-ai/d; /status\.kortix\.com/d" "$SC"
  # repoint the contact mailto to Dosco
  sed -i "s/hey@kortix\.com/$DOSCO_SUPPORT_EMAIL/g" "$SC"
  # rebrand displayed "Kortix" text (whole-word only; preserves component identifiers)
  sed -i -E "s/\bKortix\b/Dosco/g; s/open AI command center/private AI command center/g" "$SC"
fi

# 7) Global safety pass: neutralize any remaining kortix.com / github URLs in source.
echo "[apply] global URL neutralization pass over apps/web source..."
grep -rl --include=*.ts --include=*.tsx -E "kortix\.com|github\.com/kortix" \
  "$WEB/src" "$WEB/app" "$WEB/components" 2>/dev/null | while read -r f; do
  sed -i -E \
    "s#https://github.com/kortix-ai(/suna)?#?#g; \
     s#https://x.com/kortix#?#g; \
     s#https://linkedin.com/company/kortix#?#g; \
     s#https://status.kortix.com#?#g; \
     s#https://kortix.com#$DOSCO_CANONICAL#g" "$f"
done || true

# 8) Rebrand any remaining whole-word "Kortix" in JSX/TS string literals.
#    Whole-word only, so camelCase identifiers (e.g. KortixProjectScope) and
#    lowercase package paths (@kortix/sdk) are left untouched.
echo "[apply] global Kortix->Dosco word pass over apps/web source..."
grep -rl --include=*.ts --include=*.tsx -E "\bKortix\b" \
  "$WEB/src" "$WEB/app" "$WEB/components" 2>/dev/null | while read -r f; do
  sed -i -E "s/\bKortix\b/Dosco/g" "$f"
done || true

# 9) Patch landing/hero copy, remove the header GitHub link, and slim the footer
#    for the Dosco rebrand. Runs AFTER the global Kortix->Dosco pass, so the
#    `old` strings in patch-copy.py are the post-rename upstream strings.
echo "[apply] patching Dosco landing/header/footer copy..."
python3 "$DIR/patch-copy.py" "$WEB"

# 10) Hero visual: drop the product/chat surface frame, render the deliverable
#     row instead (and insert heroDeliverables copy into content.ts).
echo "[apply] patching Dosco hero visual..."
python3 "$DIR/hero-patch.py" "$WEB"

# 11) Logo component: upstream draws the Kortix mark/wordmark as inline SVG
#     path data inside kortix-logo.tsx — unreachable by the public/ asset
#     stamp. Derive transparent Dosco marks into public/brand/ and swap the
#     fallback <svg> branches to theme-swapped <img> renders. Must run AFTER
#     the global sed passes so this code is not rewritten by them.
echo "[apply] patching Dosco logo component..."
python3 "$DIR/patch-logo.py" "$WEB"

echo "[apply] done. Branding stamped. Next: build-frontend.sh"
