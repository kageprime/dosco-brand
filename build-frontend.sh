#!/usr/bin/env bash
# Build ONLY the frontend image (kortix/kortix-frontend:local) with Dosco branding.
# API + gateway stay on the upstream :0.13.5 images — not rebuilt here.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=config.sh
source "$DIR/config.sh"

REPO_ROOT="$SUNA_REPO"
WEB="$REPO_ROOT/apps/web"
TAG="${FRONTEND_TAG:-local}"

# --- Bake sane NEXT_PUBLIC_* fallbacks from the running self-host .env.
#     At container runtime the KORTIX_PUBLIC_* env in the compose file overrides
#     these, so this is only a fallback in case those are ever missing. ---
if [ -f "$KORTIX_ENV" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$KORTIX_ENV"
  set +a
fi

NEXT_PUBLIC_BILLING_ENABLED="${KORTIX_PUBLIC_BILLING_ENABLED:-false}"
NEXT_PUBLIC_DISABLE_LANDING_PAGE="${KORTIX_PUBLIC_DISABLE_LANDING_PAGE:-false}"
NEXT_PUBLIC_RESTRICT_ACCOUNT_CREATION="${KORTIX_PUBLIC_RESTRICT_ACCOUNT_CREATION:-false}"
NEXT_PUBLIC_BACKEND_URL="${API_PUBLIC_URL}/v1"
NEXT_PUBLIC_URL="${PUBLIC_URL}"
NEXT_PUBLIC_SUPABASE_URL="${SUPABASE_PUBLIC_URL}"
NEXT_PUBLIC_SUPABASE_ANON_KEY="${SUPABASE_ANON_KEY}"

echo "[build] NEXT_PUBLIC_URL=$NEXT_PUBLIC_URL"
echo "[build] NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL"

cd "$REPO_ROOT"

# --- Host-side Next.js standalone build ---
echo "[build] running next build (standalone)..."
rm -rf "$WEB/.next"
(
  cd "$WEB"
  NEXT_OUTPUT=standalone \
  NEXT_PUBLIC_BILLING_ENABLED="$NEXT_PUBLIC_BILLING_ENABLED" \
  NEXT_PUBLIC_DISABLE_LANDING_PAGE="$NEXT_PUBLIC_DISABLE_LANDING_PAGE" \
  NEXT_PUBLIC_RESTRICT_ACCOUNT_CREATION="$NEXT_PUBLIC_RESTRICT_ACCOUNT_CREATION" \
  NEXT_PUBLIC_BACKEND_URL="$NEXT_PUBLIC_BACKEND_URL" \
  NEXT_PUBLIC_URL="$NEXT_PUBLIC_URL" \
  NEXT_PUBLIC_SUPABASE_URL="$NEXT_PUBLIC_SUPABASE_URL" \
  NEXT_PUBLIC_SUPABASE_ANON_KEY="$NEXT_PUBLIC_SUPABASE_ANON_KEY" \
  pnpm run build
)

# --- Repair the standalone Next package (pnpm symlink fix from upstream script) ---
echo "[build] repairing standalone Next package..."
(
  cd "$REPO_ROOT"
  STANDALONE_NEXT_PACKAGE=$(find apps/web/.next/standalone/node_modules/.pnpm -path '*/node_modules/next/package.json' -type f | sort | head -n 1)
  [ -n "$STANDALONE_NEXT_PACKAGE" ] || { echo "could not find standalone next package" >&2; exit 1; }
  WORKSPACE_NEXT_PACKAGE=$(node - "$REPO_ROOT/apps/web" <<'JS'
const { createRequire } = require('module');
const requireFromWeb = createRequire(`${process.argv[2]}/package.json`);
console.log(requireFromWeb.resolve('next/package.json'));
JS
  )
  [ -n "$WORKSPACE_NEXT_PACKAGE" ] || { echo "could not resolve workspace next package" >&2; exit 1; }
  STANDALONE_NEXT_DIR=$(dirname "$STANDALONE_NEXT_PACKAGE")
  WORKSPACE_NEXT_DIR=$(dirname "$WORKSPACE_NEXT_PACKAGE")
  cp -R "$WORKSPACE_NEXT_DIR/." "$STANDALONE_NEXT_DIR/"

  node - "$REPO_ROOT" <<'JS'
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

const repoRoot = process.argv[2];
const requireFromWeb = createRequire(`${repoRoot}/apps/web/package.json`);
const pnpmRoot = path.join(repoRoot, 'node_modules/.pnpm');
const standalonePnpmRoot = path.join(repoRoot, 'apps/web/.next/standalone/node_modules/.pnpm');

function packageNameFromPackageJson(packageJsonPath) {
  const marker = `${path.sep}node_modules${path.sep}`;
  const markerIndex = packageJsonPath.lastIndexOf(marker);
  if (markerIndex === -1) return null;
  const packageDir = packageJsonPath.slice(0, markerIndex);
  const relative = path.relative(pnpmRoot, packageDir);
  if (relative.startsWith('..')) return null;
  return relative.split(path.sep)[0];
}

function packageNameFromResolvedPath(resolvedPath) {
  const relative = path.relative(pnpmRoot, resolvedPath);
  if (relative.startsWith('..')) return null;
  return relative.split(path.sep)[0];
}

const queue = [];
const shikiPackage = packageNameFromPackageJson(requireFromWeb.resolve('shiki/package.json'));
if (shikiPackage) queue.push(shikiPackage);

const copied = new Set();
while (queue.length > 0) {
  const packageName = queue.shift();
  if (!packageName || copied.has(packageName)) continue;
  copied.add(packageName);

  const sourceDir = path.join(pnpmRoot, packageName);
  const targetDir = path.join(standalonePnpmRoot, packageName);
  if (!fs.existsSync(sourceDir)) continue;
  fs.rmSync(targetDir, { recursive: true, force: true });
  fs.cpSync(sourceDir, targetDir, {
    recursive: true,
    dereference: false,
    verbatimSymlinks: true,
  });

  const stack = [sourceDir];
  while (stack.length > 0) {
    const current = stack.pop();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const entryPath = path.join(current, entry.name);
      if (entry.isSymbolicLink()) {
        const target = path.resolve(path.dirname(entryPath), fs.readlinkSync(entryPath));
        const dependencyPackage = packageNameFromResolvedPath(target);
        if (dependencyPackage && !copied.has(dependencyPackage)) {
          queue.push(dependencyPackage);
        }
      } else if (entry.isDirectory()) {
        stack.push(entryPath);
      }
    }
  }
}
JS
)

# --- Build the image with buildx ---
echo "[build] docker buildx build -> kortix/kortix-frontend:${TAG}"
docker buildx build --no-cache -f "$REPO_ROOT/apps/web/Dockerfile" -t "kortix/kortix-frontend:${TAG}" "$REPO_ROOT"

echo "[build] done. Image: kortix/kortix-frontend:${TAG}"
