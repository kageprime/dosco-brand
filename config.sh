#!/usr/bin/env bash
# Dosco Agent Network — branding configuration.
# Edit these values to match your organization. They are consumed by apply.sh
# and build-frontend.sh.

# Email that every kortix.com contact/support address is repointed to.
export DOSCO_SUPPORT_EMAIL="${DOSCO_SUPPORT_EMAIL:-support@dosco.live}"

# Canonical origin used in SEO metadata / canonical URLs.
export DOSCO_CANONICAL="${DOSCO_CANONICAL:-https://dosco.example.com}"

# Product naming.
export DOSCO_PRODUCT_NAME="Dosco Agent Network"
export DOSCO_SHORT_NAME="Dosco"

# Locations.
export SUNA_REPO="/home/ubuntu/suna"
export BRAND_DIR="/home/ubuntu/dosco-brand"

# Path to the running self-host .env (used only to bake sane NEXT_PUBLIC_*
# fallback values into the build; runtime KORTIX_PUBLIC_* env overrides these).
export KORTIX_ENV="/home/ubuntu/.config/kortix/self-host/default/.env"
