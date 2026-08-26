#!/usr/bin/env python3
"""Apply Dosco rebrand copy/header/footer patches to the checked-out Suna web source.

Run AFTER apply.sh's global Kortix->Dosco pass, so `old` strings are the
upstream (Kortix) originals. Idempotent: every replacement targets a unique
upstream substring.
"""
import re
import sys

WEB = sys.argv[1]

def patch(path, old, new):
    p = f"{WEB}/{path}"
    s = open(p, encoding="utf-8").read()
    if old not in s:
        print(f"[patch] SKIP (not found): {path}  -> {old[:60]!r}")
        return
    s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8").write(s)
    print(f"[patch] OK: {path}")

# ---- landing/content.ts : remove open-source framing + weave core message ----
patch("src/features/marketing/landing/content.ts",
      " * Anchored on the README's opening: \"The open-source AI Management System\".",
      " * Anchored on the product tagline: \"Dosco Agent Terminal\".")

patch("src/features/marketing/landing/content.ts",
      "  title: 'The open-source AI Management System',\n"
      "  sub: 'Your agents, their skills, your company memory and every connector in one platform. Any model, your keys, self-hosted or managed cloud.',\n"
      "  ctaPrimary: 'Get started',\n"
      "  ctaSecondary: 'Request demo',\n"
      "  trust: 'Open source \u00b7 Any model, your keys \u00b7 Self-host, VPC, or on-prem',",
      "  title: 'Dosco Agent Terminal',\n"
      "  sub: \"Dosco is not a chatbot that returns chat text. Dosco delivers deliverables \u2014 actual work that counts. Drop it into a sprint and it works as a teammate; it becomes anything you need, from UI engineer to accountant, every role run at 100% capacity.\",\n"
      "  ctaPrimary: 'Get started',\n"
      "  ctaSecondary: 'Request demo',\n"
      "  trust: 'Any model, your keys \u00b7 Self-host, VPC, or on-prem',")

patch("src/features/marketing/landing/content.ts",
      "  lead: 'The leading open-source alternative to',",
      "  lead: 'The AI command center that replaces',")

patch("src/features/marketing/landing/content.ts",
      "  sub: 'Start with one job and grow from there.',\n"
      "  trust: 'Open source \u00b7 SSO, RBAC & on-prem \u00b7 Any model, your keys \u00b7 No lock-in',",
      "  sub: 'Start with one job and grow from there.',\n"
      "  trust: 'SSO, RBAC & on-prem \u00b7 Any model, your keys \u00b7 No lock-in',")

patch("src/features/marketing/landing/content.ts",
      "      body: 'Dosco Cloud, your own VPC, or your own on-prem network. It is open source, so you can read every line of what you are trusting.',",
      "      body: 'Dosco Cloud, your own VPC, or your own on-prem network \u2014 yours down to the metal.',")

patch("src/features/marketing/landing/content.ts",
      "  sub: 'Most tools hand you one layer and rent you the rest. Dosco is all of them, open source, running wherever you put it.',",
      "  sub: 'Most tools hand you one layer and rent you the rest. Dosco is all of them, running wherever you put it.',")

patch("src/features/marketing/landing/content.ts",
      "    {\n"
      "      id: 'kortix',\n"
      "      name: 'Dosco',\n"
      "      body: 'Every layer above brought together in one platform your team owns, deploys and scales end to end \u2014 from the model to the finished work. That\u2019s Dosco.',\n"
      "      chips: ['Open source', 'Self-hostable', 'Yours down to the metal'],\n"
      "    },",
      "    {\n"
      "      id: 'kortix',\n"
      "      name: '\u706b Dosco Network',\n"
      "      body: 'Every layer above brought together in one platform your team owns, deploys and scales end to end \u2014 from the model to the finished work. That\u2019s \u706b Dosco Network.',\n"
      "      chips: ['\u706b Dosco Network', 'Self-hostable', 'Yours down to the metal'],\n"
      "    },")

# ---- cli-demo.tsx : tagline -> Dosco Agent Terminal ----
patch("src/components/home/cli-demo.tsx",
      "    t('The open-source AI Management System', 'fg'),",
      "    t('Dosco Agent Terminal', 'fg'),")

# ---- footer.tsx : slim to minimal Dosco footer (regex over the whole block) ----
fp = f"{WEB}/src/components/home/footer.tsx"
fs = open(fp, encoding="utf-8").read()
NEW_FOOTER = '''const FOOTER_SECTIONS: FooterSection[] = [
  {
    title: '\u706b Dosco',
    links: [
      { label: 'Dosco', href: '/' },
      { label: 'Privacy', href: '/legal?tab=privacy' },
      { label: 'Terms', href: '/legal/terms' },
    ],
  },
];'''
fs2, n = re.subn(
    r"const FOOTER_SECTIONS: FooterSection\[\] = \[.*?\n\];",
    NEW_FOOTER,
    fs,
    flags=re.DOTALL,
)
if n:
    open(fp, "w", encoding="utf-8").write(fs2)
    print("[patch] OK: src/components/home/footer.tsx (slimmed)")
else:
    print("[patch] SKIP (no change): src/components/home/footer.tsx")

# ---- navbar.tsx : remove GitHub star button + its imports/usage ----
np = f"{WEB}/src/components/home/navbar.tsx"
s = open(np, encoding="utf-8").read()
before = s
s = re.sub(
    r"\n\s*\{/\* `stars`, not `formattedStars`:.*?chip\. \*/\}\n\s*\{stars !== null && !starsLoading && \(.*?\)\}\n\n",
    "\n",
    s,
    flags=re.DOTALL,
)
s = s.replace(
    "  const { stars, formattedStars, loading: starsLoading } = useGitHubStars('kortix-ai', 'kortix');\n",
    "",
)
s = s.replace("import { Github } from '@/features/icon/icons/github';\n", "")
s = s.replace("import { useGitHubStars } from '@/hooks/utils/use-github-stars';\n", "")
# Remove the GitHub logo import and the GitHub drawer/social entry regardless of
# its href (apply.sh step 7 rewrites the URL to '#', so match any href).
s = re.sub(r"\n\s*GithubLogoIcon,", "", s)
s = re.sub(r"\n\s*\{ label: 'GitHub', href: '[^']*', icon: GithubLogoIcon \},", "", s)
if s != before:
    open(np, "w", encoding="utf-8").write(s)
    print("[patch] OK: src/components/home/navbar.tsx (GitHub removed)")
else:
    print("[patch] SKIP (no change): src/components/home/navbar.tsx")

# ---- about / company page : rebrand to 火 Dosco Network + core message ----
patch("src/features/marketing/about/content.ts",
      "export const hero = {\n"
      "  eyebrow: 'About Dosco',\n"
      "  title: 'We are building the open AGI platform.',\n"
      "  lead: 'Every company should own all of it \u2014 every agent, all of their data, every skill, every connector, the memory, the whole configuration.',\n"
      "  ctaPrimary: 'We are hiring',\n"
      "  ctaPrimaryHref: '/careers',\n"
      "  ctaSecondary: 'Read the code',\n"
      "  ctaSecondaryHref: '?',\n"
      "  imageAlt: 'The Dosco team',\n"
      "  starsCaption: 'stars on kortix-ai/suna',\n"
      "} as const;",
      "export const hero = {\n"
      "  eyebrow: 'About \u706b Dosco Network',\n"
      "  title: 'Dosco delivers deliverables \u2014 not just chat.',\n"
      "  lead: 'Dosco is a flexible AI agent that becomes any role \u2014 UI engineer, logo designer, accountant, PR \u2014 at 100% capacity. Hand it a sprint and it drops in and executes. The perfect coworker.',\n"
      "  ctaPrimary: 'Talk to us',\n"
      "  ctaPrimaryHref: '/contact',\n"
      "  ctaSecondary: 'Request a demo',\n"
      "  ctaSecondaryHref: '/contact',\n"
      "  imageAlt: '\u706b Dosco Network team (illustration)',\n"
      "  starsCaption: 'the \u706b Dosco Network',\n"
      "} as const;")

patch("src/features/marketing/about/content.ts",
      "  {\n"
      "    id: 'own',\n"
      "    n: '01',\n"
      "    title: 'You own all of it.',\n"
      "    body: 'On your own infrastructure if you want it there. Dosco does not sit beside the company as one more tool. It becomes the company \u2014 where the work, the context and the operations live.',\n"
      "  },",
      "  {\n"
      "    id: 'own',\n"
      "    n: '01',\n"
      "    title: 'Dosco delivers deliverables, not chat.',\n"
      "    body: 'Dosco is not a chatbot that returns text. It ships actual work that counts \u2014 finished designs, code, reports, filings. The output is the deliverable.',\n"
      "  },")

patch("src/features/marketing/about/content.ts",
      "  {\n"
      "    id: 'closed',\n"
      "    n: '02',\n"
      "    title: 'The closed platforms are becoming AGI operating systems too.',\n"
      "    body: 'Claude Cowork, ChatGPT Work and the rest are heading for full agent management systems an entire company runs on. That is the direction of the industry. The difference is that you will never own those.',\n"
      "  },",
      "  {\n"
      "    id: 'closed',\n"
      "    n: '02',\n"
      "    title: 'One agent, every role at 100% capacity.',\n"
      "    body: '\u706b Dosco Network becomes whatever you need \u2014 UI engineer, logo designer, accountant, PR. Each role runs at full capacity, the moment you need it.',\n"
      "  },")

patch("src/features/marketing/about/content.ts",
      "  {\n"
      "    id: 'shift',\n"
      "    n: '03',\n"
      "    title: 'Autonomy is shifting from humans to agents.',\n"
      "    body: 'Every company is already autonomous. Today people drive that autonomy. Agents will. Dosco is where the shift happens.',\n"
      "  },",
      "  {\n"
      "    id: 'shift',\n"
      "    n: '03',\n"
      "    title: 'The perfect coworker drops into your sprint.',\n"
      "    body: 'Hand Dosco a sprint and it executes \u2014 planning, building, and landing the work end to end. Autonomy shifts from humans to agents, and \u706b Dosco Network is the teammate that does it.',\n"
      "  },")

patch("src/features/marketing/about/content.ts",
      "export const closing = {\n"
      "  title: 'Every lab will have an AGI platform. Ours is the one you own.',\n"
      "  ctaPrimary: 'Come build it',\n"
      "  ctaPrimaryHref: '/careers',\n"
      "  ctaSecondary: 'Read the code',\n"
      "  ctaSecondaryHref: '?',\n"
      "} as const;",
      "export const closing = {\n"
      "  title: 'Every team will run on agents. \u706b Dosco Network is the one you own.',\n"
      "  ctaPrimary: 'Talk to us',\n"
      "  ctaPrimaryHref: '/contact',\n"
      "  ctaSecondary: 'Read the code',\n"
      "  ctaSecondaryHref: '#',\n"
      "} as const;")

# ---- about route metadata : drop open-source framing, weave Dosco Network ----
patch("src/app/(public)/(seo)/about/page.tsx",
      "const DESCRIPTION =\n"
      "  'Dosco is building the open AGI platform. A company owns all of it \u2014 every agent, all of their data, every skill, every connector, the memory, the whole configuration, on their own infrastructure.';",
      "const DESCRIPTION =\n"
      "  'Dosco Network is where work gets done. A flexible AI agent becomes any role \u2014 UI engineer, logo designer, accountant, PR \u2014 at 100% capacity, dropping into your sprint to deliver actual work.';")

patch("src/app/(public)/(seo)/about/page.tsx",
      "  keywords:\n"
      "    'Dosco, about Dosco, open AGI platform, open source AI management system, autonomous companies, AI agents, self-hosted agent platform',",
      "  keywords:\n"
      "    'Dosco, Dosco Network, AI agent, deliverables, AI coworker, autonomous work, AI agents',")

ap = f"{WEB}/src/app/(public)/(seo)/about/page.tsx"
as_ = open(ap, encoding="utf-8").read()
as2, an = re.subn(
    r"title: 'About Dosco \u2013 The open AGI platform',",
    "title: 'About \u706b Dosco Network \u2013 the AI coworker that delivers',",
    as_,
)
if an:
    open(ap, "w", encoding="utf-8").write(as2)
    print(f"[patch] OK: src/app/(public)/(seo)/about/page.tsx (title x{an})")
else:
    print("[patch] SKIP (no change): src/app/(public)/(seo)/about/page.tsx")

# ---- about hero image : replace Kortix team photo with labeled placeholder ----
patch("src/features/marketing/about/about-page.tsx",
      "import Image from 'next/image';\n",
      "")
patch("src/features/marketing/about/about-page.tsx",
      "          <Image\n"
      "            src=\"/images/team.webp\"\n"
      "            alt={hero.imageAlt}\n"
      "            fill\n"
      "            priority\n"
      "            className=\"object-cover object-bottom\"\n"
      "            sizes=\"100vw\"\n"
      "          />",
      "          <div\n"
      "            className=\"absolute inset-0 flex flex-col items-center justify-center gap-3 bg-gradient-to-b from-orange-500/10 to-transparent\"\n"
      "            role=\"img\"\n"
      "            aria-label={hero.imageAlt}\n"
      "          >\n"
      "            <span className=\"text-6xl\" aria-hidden>\u706b</span>\n"
      "            <span className=\"text-muted-foreground px-4 text-center text-sm font-medium\">\n"
      "              \u706b Dosco Network team \u2014 illustration coming soon\n"
      "            </span>\n"
      "          </div>")

# ---- careers : remove the link/entry from every nav, footer list, and config ----
patch("src/lib/site-config.ts",
      "        { name: 'Careers', href: '/careers' },",
      "")
patch("src/lib/seo/public-content.ts",
      "  '/careers',\n",
      "")
patch("src/lib/seo/public-content.ts",
      "  {\n"
      "    kind: 'marketing',\n"
      "    slug: 'careers',\n"
      "    title: 'Careers at Dosco',\n"
      "    description:\n"
      "      'Open positions at Dosco \u2014 Marketing / Content, Sales, FDE / Services, Product / Eng, Product / R&D. Belgrade, Serbia and San Francisco. We hire for prolonged ownership.',\n"
      "    htmlPath: '/careers',\n"
      "  },",
      "")
mp = f"{WEB}/src/middleware.ts"
ms = open(mp, encoding="utf-8").read()
ms2, mn = re.subn(
    r"  '/company-as-code',\n  '/careers',\n  '/blog',",
    "  '/company-as-code',\n  '/blog',",
    ms,
)
ms2, mn2 = re.subn(
    r"  '/careers', // Careers page should be public\n",
    "",
    ms2,
)
if mn or mn2:
    open(mp, "w", encoding="utf-8").write(ms2)
    print(f"[patch] OK: src/middleware.ts (careers removed: {mn + mn2})")
else:
    print("[patch] SKIP (no change): src/middleware.ts")

# ---- blog : empty the post listing but keep the page shell ----
patch("src/app/(public)/(seo)/blog/page.tsx",
      "  const posts = getAllPosts();\n"
      "  const [featured, ...rest] = posts;",
      "  const posts = getAllPosts();\n"
      "  // Dosco authors its own posts \u2014 listing cleared, shell kept.\n"
      "  posts.length = 0;\n"
      "  const [featured, ...rest] = posts;")

# ---- download : swap Kortix desktop links for Coming soon (Win/Mac/Linux) ----
patch("src/features/marketing/download/content.ts",
      "export const DESKTOP_ROWS: Record<DesktopOs, RowCopy> = {\n"
      "  macos: { label: 'macOS', hint: 'Universal', href: '/download/macos' },\n"
      "  windows: { label: 'Windows', hint: '64-bit', href: '/download/windows' },\n"
      "  linux: { label: 'Linux', hint: 'AppImage \u00b7 x86_64', href: '/download/linux' },\n"
      "};",
      "export const DESKTOP_STATUS = 'Coming soon';\n"
      "\n"
      "export const DESKTOP_ROWS: Record<DesktopOs, ComingSoonRowCopy> = {\n"
      "  macos: { label: 'macOS', hint: 'Universal' },\n"
      "  windows: { label: 'Windows', hint: '64-bit' },\n"
      "  linux: { label: 'Linux', hint: 'AppImage \u00b7 x86_64' },\n"
      "};")

patch("src/app/(public)/download/page.tsx",
      "import {\n"
      "  formatSize,\n"
      "  getLatestRelease,\n"
      "  pickDesktopAsset,\n"
      "} from '@/features/marketing/download/releases';\n",
      "")
patch("src/app/(public)/download/page.tsx",
      "  const [headerList, params, release] = await Promise.all([\n"
      "    headers(),\n"
      "    searchParams,\n"
      "    getLatestRelease(),\n"
      "  ]);",
      "  const [headerList, params] = await Promise.all([\n"
      "    headers(),\n"
      "    searchParams,\n"
      "  ]);")
patch("src/app/(public)/download/page.tsx",
      "  const desktopRows: CardRow[] = orderedDesktop(detected).map((os) => {\n"
      "    const size = release ? formatSize(pickDesktopAsset(release.assets, os)?.size ?? 0) : '';\n"
      "    return {\n"
      "      id: os,\n"
      "      label: DESKTOP_ROWS[os].label,\n"
      "      // The size drops out of the join when GitHub is unreachable, leaving just\n"
      "      // the copy. Never a placeholder, never a stale number.\n"
      "      meta: [DESKTOP_ROWS[os].hint, size].filter(Boolean).join(' \u00b7 '),\n"
      "      href: DESKTOP_ROWS[os].href,\n"
      "      Mark: DESKTOP_MARKS[os],\n"
      "    };\n"
      "  });",
      "  const desktopRows: CardRow[] = orderedDesktop(detected).map((os) => ({\n"
      "    id: os,\n"
      "    label: DESKTOP_ROWS[os].label,\n"
      "    meta: DESKTOP_ROWS[os].hint,\n"
      "    status: DESKTOP_STATUS,\n"
      "    Mark: DESKTOP_MARKS[os],\n"
      "  }));")
patch("src/app/(public)/download/page.tsx",
       "  DESKTOP_ROWS,\n  MOBILE_CARD,",
       "  DESKTOP_ROWS,\n  DESKTOP_STATUS,\n  MOBILE_CARD,")

# ---- contact : rebrand, real emails, neutralize kortix refs ----
patch("src/app/(public)/(marketing)/contact/page.tsx",
      "const CONTACT_EMAIL = 'hey@kortix.ai';",
      "const CONTACT_EMAIL = 'support@dosco.live';")
patch("src/app/(public)/(marketing)/contact/page.tsx",
      "// Public demo event (cal.com/team/kortix/demo) + a namespace unique to it.",
      "// Public demo event (cal.com/team/dosco/demo) + a namespace unique to it.")
patch("src/app/(public)/(marketing)/contact/page.tsx",
      "const CAL_LINK = 'team/kortix/demo';",
      "const CAL_LINK = 'team/dosco/demo';")
patch("src/app/(public)/(marketing)/contact/page.tsx",
      "const CAL_NAMESPACE = 'kortix-enterprise-demo';",
      "const CAL_NAMESPACE = 'dosco-enterprise-demo';")

print("[patch] done")
