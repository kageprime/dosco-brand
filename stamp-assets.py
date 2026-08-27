#!/usr/bin/env python3
"""Stamp Dosco brand assets onto a Suna checkout's apps/web/public tree.

Real-brand light/dark/icon mapping (replaces the placeholder stamping):

  assets/doscologo-dark.png   dark artwork   -> LIGHT backgrounds (logo_black,
                                               brandkit "Black", og banners)
  assets/doscologo-light.png  light artwork  -> DARK backgrounds (logomark-white,
                                               brandkit "White", dark posters)
  assets/doscologoIcon.png    square icon    -> favicons, avatars, provider marks

.svg target slots receive SVG wrappers with the PNG embedded as base64, so the
app's hardcoded .svg paths keep rendering. Idempotent over a clean checkout.
"""
import base64
import io
import os
import shutil
import sys

from PIL import Image

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
DERIVED = os.path.join(ASSETS, "derived")
DARK = os.path.join(ASSETS, "doscologo-dark.png")      # dark artwork, light bg
LIGHT = os.path.join(ASSETS, "doscologo-light.png")    # light artwork, dark bg
ICON = os.path.join(ASSETS, "doscologoIcon.png")       # square-ish icon


def _load(path: str) -> Image.Image:
    if not os.path.isfile(path):
        sys.exit(f"[stamp] ERROR: missing brand asset {path}")
    return Image.open(path).convert("RGBA")


def center_square(im: Image.Image) -> Image.Image:
    w, h = im.size
    side = min(w, h)
    left, top = (w - side) // 2, (h - side) // 2
    return im.crop((left, top, left + side, top + side))


def resized(im: Image.Image, size: int) -> Image.Image:
    return im.resize((size, size), Image.LANCZOS)


def resized_width(im: Image.Image, width: int) -> Image.Image:
    w, h = im.size
    return im.resize((width, round(h * width / w)), Image.LANCZOS)


def save_svg_wrapper(im: Image.Image, path: str, max_width: int = 1200) -> None:
    """Wrap a raster in a minimal SVG so hardcoded .svg paths keep rendering."""
    w, h = im.size
    if w > max_width:
        im = resized_width(im, max_width)
        w, h = im.size
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            '<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {w} {h}" preserveAspectRatio="xMidYMid meet" '
            f'width="{w}" height="{h}">'
            f'<image width="{w}" height="{h}" '
            f'href="data:image/png;base64,{b64}"/></svg>\n'
        )


def build_derived() -> dict:
    """Generate exact-size variants + SVG wrappers on disk; return path map."""
    dark, light, icon = _load(DARK), _load(LIGHT), _load(ICON)

    icon_sq = center_square(icon)                     # 1024x1024
    favicon32 = resized(icon_sq, 32)
    icon512 = resized(icon_sq, 512)
    # Maskable icons need a safe zone: content at ~80% on a transparent canvas.
    logo512 = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    content = resized(icon_sq, 410)
    logo512.paste(content, (51, 51), content)

    os.makedirs(DERIVED, exist_ok=True)
    favicon32_path = os.path.join(DERIVED, "favicon-32.png")
    icon512_path = os.path.join(DERIVED, "icon-512.png")
    logo512_path = os.path.join(DERIVED, "logo-512.png")
    favicon32.save(favicon32_path, "PNG", optimize=True)
    icon512.save(icon512_path, "PNG", optimize=True)
    logo512.save(logo512_path, "PNG", optimize=True)

    mark_dark_svg = os.path.join(DERIVED, "_dosco-mark-dark.svg")   # for dark bg
    mark_light_svg = os.path.join(DERIVED, "_dosco-mark-light.svg") # for light bg
    icon_svg = os.path.join(DERIVED, "_dosco-icon.svg")

    save_svg_wrapper(light, mark_dark_svg)
    save_svg_wrapper(dark, mark_light_svg)
    save_svg_wrapper(icon512, icon_svg)

    return {
        "favicon32": favicon32_path,
        "logo512": logo512_path,
        "icon512": icon512_path,
        "mark_dark_svg": mark_dark_svg,
        "mark_light_svg": mark_light_svg,
        "icon_svg": icon_svg,
        "light_wordmark": LIGHT,
        "dark_wordmark": DARK,
    }


def copy_raster(src_image, dest: str) -> None:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copyfile(src_image, dest)


def stamp(web_public: str) -> None:
    a = build_derived()
    p = lambda *parts: os.path.join(web_public, *parts)

    # ── Exact-name slots ────────────────────────────────────────────────
    exact = {
        # icon (square) slots
        "favicon.png": ("raster", a["favicon32"]),
        "favicon-light.png": ("raster", a["favicon32"]),
        "logo_black.png": ("raster", a["logo512"]),          # 512 maskable
        "marko.png": ("raster", a["icon512"]),
        "banner.png": ("raster", a["light_wordmark"]),       # og banner
        # svg slots
        "kortix-symbol.svg": ("svg", a["icon_svg"]),         # avatars/marks
        "brand/chrome.svg": ("svg", a["icon_svg"]),
        "logomark-white.svg": ("svg", a["mark_dark_svg"]),   # dark surfaces
        "kortix-logomark-white.svg": ("svg", a["mark_dark_svg"]),
        "kortix-brandmark-bg.svg": ("svg", a["mark_dark_svg"]),
    }
    for rel, (kind, src) in exact.items():
        dest = p(*rel.split("/"))
        if not os.path.isfile(dest):
            continue
        if kind == "svg":
            if src.endswith(".svg"):
                shutil.copyfile(src, dest)
            else:
                save_svg_wrapper(src, dest)
        else:
            copy_raster(src, dest)
        print(f"[stamp] {rel}")

    # ── brandkit: Black = dark artwork (light bg); White = for dark bg ──
    brandkit = p("brandkit")
    if os.path.isdir(brandkit):
        for root, _dirs, files in os.walk(brandkit):
            for name in sorted(files):
                if not name.lower().endswith((".png", ".svg")):
                    continue
                dest = os.path.join(root, name)
                if "avatar" in name.lower() or "profile" in root.lower():
                    src = a["icon_svg"] if name.endswith(".svg") else a["icon512"]
                elif "black" in name.lower():
                    src = a["mark_light_svg"] if name.endswith(".svg") else a["dark_wordmark"]
                else:  # White
                    src = a["mark_dark_svg"] if name.endswith(".svg") else a["light_wordmark"]
                if src.endswith(".svg"):
                    shutil.copyfile(src, dest)
                else:
                    copy_raster(src, dest)
                print(f"[stamp] brandkit: {os.path.relpath(dest, web_public)}")

    # ── Bulk: every remaining *kortix* raster — no Kortix artwork served ──
    count = 0
    for root, _dirs, files in os.walk(web_public):
        for name in sorted(files):
            if "kortix" not in name.lower():
                continue
            if not name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif")):
                continue
            dest = os.path.join(root, name)
            if dest.endswith(".svg"):
                shutil.copyfile(a["icon_svg"], dest)
            else:
                w, h = Image.open(dest).size
                src = a["light_wordmark"] if (h and w / h > 1.4) else a["icon512"]
                copy_raster(src, dest)
            count += 1
    print(f"[stamp] bulk *kortix* assets replaced: {count}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: stamp-assets.py <path-to-apps/web/public>")
    stamp(sys.argv[1])
    print("[stamp] done.")