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

## Update workflow (pull upstream, keep reskin + local commits)

The `local-dev` branch carries **local commits that must survive every pull**
(OAuth login, Zen model catalog, docs rebrand). Use **rebase, never
`reset --hard`** — a reset would delete them:

```sh
cd /home/ubuntu/suna
git fetch upstream main
git rebase upstream/main               # replays local commits onto upstream tip
# resolve conflicts if any (likely: apps/api model catalog, auth page), then:
git rebase --continue

cd /home/ubuntu/dosco-brand
bash apply.sh                           # re-stamp Dosco branding (cleans apps/web first)
bash build-frontend.sh                  # rebuild kortix/kortix-frontend:local
cd /home/ubuntu/.config/kortix/self-host/default
docker compose -p kortix-default --env-file .env up -d --no-deps frontend
# (restart supabase-kong too if supabase-auth was recreated — Kong caches its IP)
```

`apply.sh` runs `git checkout -- apps/web` first — **anything uncommitted in
apps/web is lost**, so always commit local work before rebranding.
The stamped branding (544 files) stays uncommitted; it is regenerated from this
overlay on every apply.

> ⚠️ **API contract caution:** the frontend must not jump far ahead of the API
> image (`dosco/kortix-api:0.13.5-zen.3`). Upstream's session-surface refactor
> (#6987) changed web↔api interplay — after pulling 0.13.6-dev commits, rebuild
> the API image from the same commit before deploying the new frontend.

## Notes
- API + LLM gateway keep running the upstream `:0.13.5` images (not rebuilt).
- Updater is stopped and `KORTIX_AUTO_UPDATE=false` / `KORTIX_IMAGE_PULL=never`
  prevent the self-host stack from overwriting the local frontend image.
- After `git reset --hard`, re-verify: upstream may rename a logo file or move a
  nav link, which would make an asset copy or link removal silently miss.
- Set `DOSCO_SUPPORT_EMAIL` / `DOSCO_CANONICAL` to your real values, then rebuild.
