#!/usr/bin/env python3
"""Dosco hero visual: remove the product/chat frame, render a deliverable row.

Replaces `<HeroSurfaces />` (the animated Web/CLI/Slack/Teams surfaces under the
headline) with a restrained row of finished-work artifacts, keeping the hero
pure-typographic per the "Built to work, not to talk." refresh.

Run AFTER apply.sh's global Kortix->Dosco + patch-copy.py, so `old` strings are
the post-rebrand upstream originals. Idempotent.
"""
import os
import sys
import re

WEB = sys.argv[1]


def patch_hero_tsx():
    p = f"{WEB}/src/features/marketing/hero.tsx"
    s = open(p, encoding="utf-8").read()
    # Whitespace-tolerant: match the demo frame block regardless of indent.
    pattern = re.compile(
        r'\n[ \t]*<div\s*\n[ \t]*id="demo"[^>]*>\s*\n[ \t]*<HeroSurfaces\s*/>\s*\n[ \t]*</div>\s*\n'
    )
    replacement = (
        '\n        <div\n'
        '          id="demo"\n'
        '          className="kx-hero-frame relative z-10 mx-auto mt-12 max-w-4xl scroll-mt-24 px-6 [--kx-enter:290ms] sm:mt-14 lg:mt-10"\n'
        '        >\n'
        '          <DeliverableRow />\n'
        '        </div>\n'
    )
    new_s, n = pattern.subn(replacement, s, count=1)
    if n:
        s = new_s
        print("[patch] OK: hero.tsx (frame -> DeliverableRow)")
    else:
        print("[patch] SKIP: hero.tsx frame block not matched")
    # swap the HeroSurfaces import for the deliverable component import
    s = s.replace(
        "import { HeroSurfaces } from '@/features/marketing/hero-surfaces';",
        "import { DeliverableRow } from '@/features/marketing/hero-deliverables';",
    )
    open(p, "w", encoding="utf-8").write(s)


def patch_content_ts():
    """Insert heroDeliverables into content.ts (idempotent via marker)."""
    p = f"{WEB}/src/features/marketing/landing/content.ts"
    s = open(p, encoding="utf-8").read()
    if "heroDeliverables" in s:
        print("[patch] content.ts (heroDeliverables already present)")
        return
    marker = "} as const;\n"
    # insert right after the heroEyebrow export block (its trailing `}; as const;`)
    # We locate the heroEyebrow block end: the second occurrence of "} as const;"
    # after "heroEyebrow".
    idx = s.index("export const heroEyebrow =")
    end = s.find("} as const;", idx)
    end = s.find("\n", end) + 1  # end of that line
    insert = (
        "\n/** Deliverable-row artifacts shown under the hero — proof the agent\n"
        " *  ships finished work, not chat. Rendered by the Hero component in\n"
        " *  lieu of the product/chat surfaces frame. */\n"
        "export const heroDeliverables = [\n"
        "  { id: 'frontend', role: 'Frontend', artifact: 'Design handoff', note: 'FINAL' },\n"
        "  { id: 'backend', role: 'Backend', artifact: 'API shipped', note: 'FINAL' },\n"
        "  { id: 'pm', role: 'Product', artifact: 'Roadmap locked', note: 'FINAL' },\n"
        "] as const;\n"
    )
    s = s[:end] + insert + s[end:]
    open(p, "w", encoding="utf-8").write(s)
    print("[hero] content.ts (heroDeliverables inserted)")


def append_component():
    # Create the DeliverableRow component file if not present.
    comp = f"{WEB}/src/features/marketing/hero-deliverables.tsx"
    if os.path.exists(comp):
        return
    body = """'use client';

import { heroDeliverables } from '@/features/marketing/landing/content';

/** A light "finished work" strip under the hero — one artifact per role, all
 *  stamped FINAL, replacing the old chat/product-surface frame. Keeps the hero
 *  pure-typographic while still showing the deliverable, not a chat bubble. */
export function DeliverableRow() {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {heroDeliverables.map((d) => (
        <div
          key={d.id}
          className="flex flex-col items-center justify-center rounded-xl border border-border/60 bg-background/40 px-4 py-6 text-center backdrop-blur-sm"
        >
          <span className="text-muted-foreground text-xs uppercase tracking-[0.18em]">
            {d.role}
          </span>
          <span className="text-foreground mt-1 text-sm font-medium">
            {d.artifact}
          </span>
          <span className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-[10px] font-semibold tracking-wide text-emerald-600">
            <span className="size-1.5 rounded-full bg-emerald-500" />
            {d.note} · 100%
          </span>
        </div>
      ))}
    </div>
  );
}
"""
    open(comp, "w", encoding="utf-8").write(body.lstrip())
    print(f"[patch] create: {comp}")


if __name__ == "__main__":
    patch_content_ts()
    patch_hero_tsx()
    append_component()
    print("[patch] hero done.")