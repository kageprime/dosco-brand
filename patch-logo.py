#!/usr/bin/env python3
"""Patch the upstream logo component to render Dosco artwork.

Upstream `apps/web/src/components/ui/kortix-logo.tsx` draws the Kortix
symbol/wordmark as inline SVG path data — artwork the public/ asset stamp can
never reach (it only swaps files, not bundled code). This script:

  1. derives transparent Dosco wordmark/icon PNGs (dark artwork for light
     backgrounds, light artwork for dark backgrounds) into
     `apps/web/public/brand/` by alpha-recoloring the transparent brand
     sources — so the mark keeps its exact shape in both color schemes;
  2. replaces the two fallback <svg> branches of the component with
     theme-swapped <img> renders of those assets (same class/`dark:` swap
     pattern the component already uses for org-branding images). The
     `useBranding()` override logic above the fallbacks is left untouched.

Idempotent: exits 0 without changes when the patch marker is present.
"""
import os
import sys

from PIL import Image

BRAND_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BRAND_DIR, "assets")
# Transparent sources. doscologo-dark.png is an opaque badge and unusable
# here; the light lockup + icon carry the true artwork shape with alpha.
WORDMARK_SRC = os.path.join(ASSETS, "doscologo-light.png")
ICON_SRC = os.path.join(ASSETS, "doscologoIcon.png")

DARK_ART = (2, 2, 2, 255)        # #020202 — artwork for LIGHT backgrounds
LIGHT_ART = (253, 252, 253, 255)  # #fdfcfd — artwork for DARK backgrounds

MARKER = "/brand/dosco-wordmark-dark.png"


def recolor(src: str, color: tuple, max_w: int) -> Image.Image:
    """Silhouette-recolor: keep the alpha mask, force a solid fill color."""
    im = Image.open(src).convert("RGBA")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    out = Image.new("RGBA", im.size, color)
    out.putalpha(im.getchannel("A"))
    return out


def make_assets(public_brand: str) -> None:
    os.makedirs(public_brand, exist_ok=True)
    jobs = {
        "dosco-wordmark-dark.png": (WORDMARK_SRC, DARK_ART, 1200),
        "dosco-wordmark-light.png": (WORDMARK_SRC, LIGHT_ART, 1200),
        "dosco-icon-dark.png": (ICON_SRC, DARK_ART, 512),
        "dosco-icon-light.png": (ICON_SRC, LIGHT_ART, 512),
    }
    for name, (src, color, max_w) in jobs.items():
        im = recolor(src, color, max_w)
        im = im.crop(im.getchannel("A").getbbox())  # trim transparent padding
        im.save(os.path.join(public_brand, name), "PNG", optimize=True)
        print(f"[logo] {name}  {im.size[0]}x{im.size[1]}")


TAIL = f"""  // Dosco fallback art (stamped by dosco-brand patch-logo.py): upstream drew
  // the Kortix mark inline here. We render transparent Dosco PNGs instead,
  // swapped per color scheme exactly like the org-branding images above.
  const fallbackAlt = branding?.app_name ?? 'Dosco';

  if (variant === 'icon') {{
    const imgStyle = {{ width: `${{size}}px`, height: `${{size}}px`, ...style }};
    const imgProps = props as ComponentPropsWithoutRef<'img'>;
    return (
      <>
        {{/* eslint-disable-next-line @next/next/no-img-element */}}
        <img
          src="/brand/dosco-icon-dark.png"
          alt={{fallbackAlt}}
          draggable={{false}}
          className={{cn('shrink-0 select-none object-contain dark:hidden', className)}}
          style={{imgStyle}}
          {{...imgProps}}
        />
        {{/* eslint-disable-next-line @next/next/no-img-element */}}
        <img
          src="/brand/dosco-icon-light.png"
          alt={{fallbackAlt}}
          draggable={{false}}
          className={{cn('hidden shrink-0 select-none object-contain dark:block', className)}}
          style={{imgStyle}}
          {{...imgProps}}
        />
      </>
    );
  }}

  const imgStyle = {{
    height: `${{size}}px`,
    width: 'auto',
    maxWidth: `${{size * 8}}px`,
    ...style,
  }};
  const imgProps = props as ComponentPropsWithoutRef<'img'>;
  return (
    <>
      {{/* eslint-disable-next-line @next/next/no-img-element */}}
      <img
        src="/brand/dosco-wordmark-dark.png"
        alt={{fallbackAlt}}
        draggable={{false}}
        className={{cn('shrink-0 select-none object-contain dark:hidden', className)}}
        style={{imgStyle}}
        {{...imgProps}}
      />
      {{/* eslint-disable-next-line @next/next/no-img-element */}}
      <img
        src="/brand/dosco-wordmark-light.png"
        alt={{fallbackAlt}}
        draggable={{false}}
        className={{cn('hidden shrink-0 select-none object-contain dark:block', className)}}
        style={{imgStyle}}
        {{...imgProps}}
      />
    </>
  );
}}
"""


def patch_component(web: str) -> None:
    p = os.path.join(web, "src", "components", "ui", "kortix-logo.tsx")
    s = open(p, encoding="utf-8").read()
    if MARKER in s:
        print("[logo] component already patched; skipping")
        return
    anchor = "  if (variant === 'icon') {"
    idx = s.find(anchor)
    if idx == -1:
        sys.exit("[logo] ERROR: could not locate the fallback <svg> branches in kortix-logo.tsx")
    s = s[:idx] + TAIL
    open(p, "w", encoding="utf-8").write(s)
    print("[logo] kortix-logo.tsx: fallback <svg> branches -> Dosco <img> renders")


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: patch-logo.py <path-to-apps/web>")
    web = sys.argv[1]
    make_assets(os.path.join(web, "public", "brand"))
    patch_component(web)


if __name__ == "__main__":
    main()
