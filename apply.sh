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

# 2) Copy Dosco logo / favicon assets over upstream public filenames.
echo "[apply] copying assets..."
for f in \
  kortix-symbol.svg \
  kortix-logomark-white.svg \
  logomark-white.svg \
  kortix-brandmark-bg.svg \
  favicon.png \
  favicon-light.png \
  brand/chrome.svg ; do
  if [ -f "$DIR/assets/$f" ]; then
    mkdir -p "$(dirname "$WEB/public/$f")"
    cp "$DIR/assets/$f" "$WEB/public/$f"
  else
    echo "[apply] WARNING: missing asset $f (skipped)" >&2
  fi
done

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
# strip any remaining open-source / self-host phrasing in this file
import re
s = re.sub(r"open[\s-]?source", "", s, flags=re.IGNORECASE)
s = re.sub(r"self[\s-]?host(?:able)?", "", s, flags=re.IGNORECASE)
s = re.sub(r"\s{2,}", " ", s)
open(p, "w", encoding="utf-8").write(s)
PY

# 5) Patch manifest.json.
echo "[apply] patching manifest.json..."
python3 - <<'PY'
import json
p = "apps/web/public/manifest.json"
d = json.load(open(p, encoding="utf-8"))
d["name"] = "Dosco Agent Network"
d["short_name"] = "Dosco"
d["description"] = (
    d.get("description", "")
    .replace("Kortix", "Dosco")
    .replace("open-source", "")
    .replace("open source", "")
)
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

echo "[apply] done. Branding stamped. Next: build-frontend.sh"
