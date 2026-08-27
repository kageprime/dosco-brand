# Dosco Agent Network — Frontend Reskin Overlay

This directory holds the **branding layer** that turns the upstream Suna/Kortix
frontend into the private "Dosco Agent Network" product. It is kept *outside*
the Suna source tree on purpose: the Suna repo (`/home/ubuntu/suna`) never
stores your changes, so pulling upstream never causes merge conflicts.

## Files
- `config.sh`        — branding variables (edit `DOSCO_SUPPORT_EMAIL`, `DOSCO_CANONICAL`, names).
- `stamp-assets.py`  — stamps real brand artwork (light/dark/icon) onto `apps/web/public`,
                       generating exact-size favicons/tiles and SVG wrappers for `.svg` slots.
- `transform-en.py`  — rewrites `apps/web/translations/en.json` (Kortix→Dosco,
                       strips "open source"/"self-host", neutralizes URLs, repoints emails).
- `apply.sh`         — stamps branding onto a CLEAN checkout (assets, en.json, metadata,
                       manifest, removes external Kortix/GitHub/social links).
- `build-frontend.sh`— host Next.js standalone build + `docker buildx` → `kortix/kortix-frontend:local`.
- `assets/`          — real brand files: `doscologo-dark.png` (dark artwork, light bg),
                       `doscologo-light.png` (light artwork, dark bg), `doscologoIcon.png`
                       (icon → favicons/avatars). `assets/derived/` is generated, gitignored.

## Update workflow (pull upstream, keep reskin)
```sh
cd /home/ubuntu/suna
git fetch upstream
git reset --hard upstream/main          # or a specific tag, e.g. v0.13.6
cd /home/ubuntu/dosco-brand
bash apply.sh                           # re-stamp Dosco branding
bash build-frontend.sh                  # rebuild kortix/kortix-frontend:local
cd /home/ubuntu/.config/kortix/self-host/default
docker compose -p kortix-default -f docker-compose.yml up -d --no-deps frontend
```
`apply.sh` runs `git checkout -- apps/web` first, so re-application is idempotent.

## Notes
- API + LLM gateway keep running the upstream `:0.13.5` images (not rebuilt).
- Updater is stopped and `KORTIX_AUTO_UPDATE=false` / `KORTIX_IMAGE_PULL=never`
  prevent the self-host stack from overwriting the local frontend image.
- After `git reset --hard`, re-verify: upstream may rename a logo file or move a
  nav link, which would make an asset copy or link removal silently miss.
- Set `DOSCO_SUPPORT_EMAIL` / `DOSCO_CANONICAL` to your real values, then rebuild.
