#!/usr/bin/env python3
"""Transform apps/web/translations/en.json for the Dosco Agent Network reskin.

Branding is applied to a CLEAN checkout (apply.sh runs `git checkout` first),
so this script can safely rewrite every string value:
  * Kortix / Suna  -> Dosco (product) ; "Kortix Computer" -> "Dosco Agent"
  * remove "open source" / "self-host" / "MIT-licensed" phrasing
  * neutralize GitHub / kortix.com external URLs
  * repoint *@kortix.com emails to the Dosco support address
Keys are preserved (only string values are touched) so references never break.

Durability rules (learned the hard way):
  * REWRITES below maps exact pre-stamp AND already-mangled values to their
    final copy, so the script repairs HEAD and is idempotent on re-runs.
  * Generic cleanup runs ONLY when a removal actually fired. It never strips
    terminal periods, never eats em-dashes / NBSP / punctuation-only strings
    ('.', '---', mdash, nbsp, middot, '>', quotes).
  * The `kortix self-host ...` CLI invocation is a real command and is kept.
"""
import json
import re
import sys

PATH = sys.argv[1]
EMAIL = sys.argv[2] if len(sys.argv) > 2 else "support@dosco.example.com"
CANON = sys.argv[3] if len(sys.argv) > 3 else "https://dosco.example.com"

# Exact hand rewrites: {input value -> final Dosco copy}.
# Keys cover both the pre-stamp upstream wording and the mangled output of
# the old naive transform, so this repairs an already-stamped file and is a
# no-op once applied. Generated from /tmp/broken.json + /tmp/finals.json.
REWRITES = {
    '"License" refers to the permissions granted to Users to use the Site and Service as outlined in these Terms of Use, or the separate LICENSE file for ing': '"License" refers to the permissions granted to Users to use the Site and Service as outlined in these Terms of Use, or the separate LICENSE file for private deployment.',
    '"License" refers to the permissions granted to Users to use the Site and Service as outlined in these Terms of Use, or the separate LICENSE file for self-hosting.': '"License" refers to the permissions granted to Users to use the Site and Service as outlined in these Terms of Use, or the separate LICENSE file for private deployment.',
    '"Self-Hosting" refers to deployment of the Service on user\'s own infrastructure, subject to the terms of the LICENSE file.': '"Private deployment" refers to deployment of the Service on user\'s own infrastructure, subject to the terms of the LICENSE file.',
    '"ing" refers to deployment of the Service on user\'s own infrastructure, subject to the terms of the LICENSE file': '"Private deployment" refers to deployment of the Service on user\'s own infrastructure, subject to the terms of the LICENSE file.',
    '-- or self-host': '-- or on-prem',
    'A ed instance runs its own gateway for its own model routing. It never sees or routes to Dosco credentials, and there is no platform fee on a ed account': 'A private instance runs its own gateway for its own model routing. It never sees or routes to Dosco credentials, and there is no platform fee on a private account.',
    'A self-hosted instance runs its own gateway for its own model routing. It never sees or routes to Kortix credentials, and there is no platform fee on a self-hosted account.': 'A private instance runs its own gateway for its own model routing. It never sees or routes to Dosco credentials, and there is no platform fee on a private account.',
    'Agents, skills, tools, connectors, schedules all just files in a repo. Edit them in your IDE, run them locally, ship to the cloud with one command.,, yours': 'Agents, skills, tools, connectors, schedules — all just files in a repo. Edit them in your IDE, run them locally, ship to the cloud with one command.',
    'Agents, skills, tools, connectors, schedules — all just files in a repo. Edit them in your IDE, run them locally, ship to the cloud with one command. Open source, self-hostable, yours.': 'Agents, skills, tools, connectors, schedules — all just files in a repo. Edit them in your IDE, run them locally, ship to the cloud with one command.',
    'Available on Enterprise, and on a ed instance with an Enterprise licence. The built-in roles above are free on every plan': 'Available on Enterprise, and on a private instance with an Enterprise licence. The built-in roles above are free on every plan.',
    'Available on Enterprise, and on a self-hosted instance with an Enterprise licence. The built-in roles above are free on every plan.': 'Available on Enterprise, and on a private instance with an Enterprise licence. The built-in roles above are free on every plan.',
    'Connect your first tool and watch it come back with something you can use. Free to start, free to': 'Connect your first tool and watch it come back with something you can use. Free to start, with no lock-in.',
    'Connect your first tool and watch it come back with something you can use. Free to start, free to self-host.': 'Connect your first tool and watch it come back with something you can use. Free to start, with no lock-in.',
    'Connect your tools and hand a Dosco agent a real task. Free to start, free to': 'Connect your tools and hand a Dosco agent a real task. Free to start, with no lock-in.',
    'Connect your tools and hand a Kortix agent a real task. Free to start, free to self-host.': 'Connect your tools and hand a Dosco agent a real task. Free to start, with no lock-in.',
    'Dosco': 'Deploy Dosco',
    "Dosco is the AI operating system where your company's knowledge compounds. Connect your tools, deploy an agent, and start accumulating your own token capital. Free to start, free to": "Dosco is the AI operating system where your company's knowledge compounds. Connect your tools, deploy an agent, and start accumulating your own token capital. Free to start, with no lock-in.",
    'Dosco, AI command center, AI agents, AI workforce, AI platform, ed AI agents, AI automation, agent orchestration, AI-native company, build AI agents, connect 3000 tools, AI operations': 'Dosco, AI command center, AI agents, AI workforce, AI platform, private AI agents, AI automation, agent orchestration, AI-native company, build AI agents, connect 3000 tools, AI operations',
    'Every agent, skill, automation, and policy is a versioned file in a git repo you control. Diff it, review it, roll it back like software. Run it on our cloud or anywhere. No black box, no lock-in': 'Every agent, skill, automation, and policy is a versioned file in a git repo you control. Diff it, review it, roll it back — like software. Run it on our cloud or yours. No black box, no lock-in.',
    'Every agent, skill, automation, and policy is a versioned file in a git repo you control. Diff it, review it, roll it back — like software. Run it on our cloud or self-host anywhere. No black box, no lock-in.': 'Every agent, skill, automation, and policy is a versioned file in a git repo you control. Diff it, review it, roll it back — like software. Run it on our cloud or yours. No black box, no lock-in.',
    'For ed setups or custom-scoped installs': 'For private setups or custom-scoped installs.',
    'For self-hosted setups or custom-scoped installs.': 'For private setups or custom-scoped installs.',
    'Hand a Dosco agent a real task and get a finished result back. Free to start, free to': 'Hand a Dosco agent a real task and get a finished result back. Free to start, with no lock-in.',
    'Hand a Kortix agent a real task and get a finished result back. Free to start, free to self-host.': 'Hand a Dosco agent a real task and get a finished result back. Free to start, with no lock-in.',
    "Kortix is the open-source AI operating system where your company's knowledge compounds. Connect your tools, deploy an agent, and start accumulating your own token capital. Free to start, free to self-host.": "Dosco is the AI operating system where your company's knowledge compounds. Connect your tools, deploy an agent, and start accumulating your own token capital. Free to start, with no lock-in.",
    'Kortix, AI command center, AI agents, AI workforce, open source AI platform, self-hosted AI agents, AI automation, agent orchestration, AI-native company, build AI agents, connect 3000 tools, AI operations': 'Dosco, AI command center, AI agents, AI workforce, AI platform, private AI agents, AI automation, agent orchestration, AI-native company, build AI agents, connect 3000 tools, AI operations',
    'Most tools hand you one layer and rent you the rest. Dosco is all of them,, running wherever you put it': 'Most tools hand you one layer and rent you the rest. Dosco is all of them, running wherever you put it.',
    'Most tools hand you one layer and rent you the rest. Kortix is all of them, open source, running wherever you put it.': 'Most tools hand you one layer and rent you the rest. Dosco is all of them, running wherever you put it.',
    'Open &': 'No lock-in',
    'Open & self-hostable': 'No lock-in',
    'Open Source': 'No lock-in',
    'Open source': 'No lock-in',
    'Open source and self-hostable': 'No lock-in',
    'Open source and self-hostable — Kortix Cloud, your VPC, or on-prem.': 'No lock-in — Dosco Cloud, your VPC, or on-prem.',
    'Open source and self-hostable. Any model, your keys. Kortix Cloud, your own VPC, or fully on-prem.': 'No lock-in. Any model, your keys. Dosco Cloud, your own VPC, or fully on-prem.',
    'Open source and self-hostable. Any model, your keys. Kortix Cloud, your own VPC, or your own on-prem network.': 'No lock-in. Any model, your keys. Dosco Cloud, your own VPC, or your own on-prem network.',
    'Open source and self-hostable. Your data, your models, your infra.': 'No lock-in. Your data, your models, your infra.',
    'Open source by design': 'Yours by design',
    'Open source · Any model, your keys · Self-host, VPC, or on-prem': 'Any model, your keys · VPC or on-prem',
    'Open source · SSO · RBAC · on-prem · no lock-in': 'SSO · RBAC · on-prem · no lock-in',
    'Open source · SSO, RBAC & on-prem · Any model, your keys · No lock-in': 'SSO, RBAC & on-prem · Any model, your keys · No lock-in',
    'Open source · SSO, RBAC & on-prem · No lock-in': 'SSO, RBAC & on-prem · No lock-in',
    'Open source · Self-hostable · MIT-licensed core': 'No lock-in',
    'Open source, so the harness is never the thing you are locked into': 'So the harness is never the thing you are locked into',
    'Open source, with support for any AI model. Use Kortix Cloud or run it on your own systems.': 'With support for any AI model. Use Dosco Cloud or run it on your own systems.',
    'Open source. Self-host it or run it on Kortix cloud — nothing is locked to a vendor.': 'Run it on Dosco cloud — nothing is locked to a vendor.',
    'Open source. Self-host the exact same stack, bring your own keys.': 'Run the exact same stack, bring your own keys.',
    'Open source. Self-host the exact same stack, bring your own runtime and model keys. No black box, no lock-in.': 'Run the exact same stack, bring your own runtime and model keys. No black box, no lock-in.',
    'Open. Self-hostable. Yours down to the metal.': 'Private. Yours down to the metal.',
    'Open.. Yours down to the metal': 'Private. Yours down to the metal.',
    'Point this desktop app at a ed Dosco instance. The window reloads and the choice is saved locally': 'Point this desktop app at a private Dosco instance. The window reloads and the choice is saved locally.',
    'Point this desktop app at a self-hosted Kortix instance. The window reloads and the choice is saved locally.': 'Point this desktop app at a private Dosco instance. The window reloads and the choice is saved locally.',
    'Run on cloud, self-host, or VPC.': 'Run on cloud or VPC.',
    'Run on cloud,, or VPC': 'Run on cloud or VPC.',
    'SAML SSO, SCIM directory sync, custom roles, groups and reading the audit log are Enterprise entitlements. On a ed instance they switch on with an Enterprise licence. The built-in owner, admin, member, manager and editor roles are there on every install, and the audit record is written on every install whether or not you can read it back yet': 'SAML SSO, SCIM directory sync, custom roles, groups and reading the audit log are Enterprise entitlements. On a private instance they switch on with an Enterprise licence. The built-in owner, admin, member, manager and editor roles are there on every install, and the audit record is written on every install whether or not you can read it back yet.',
    'SAML SSO, SCIM directory sync, custom roles, groups and reading the audit log are Enterprise entitlements. On a self-hosted instance they switch on with an Enterprise licence. The built-in owner, admin, member, manager and editor roles are there on every install, and the audit record is written on every install whether or not you can read it back yet.': 'SAML SSO, SCIM directory sync, custom roles, groups and reading the audit log are Enterprise entitlements. On a private instance they switch on with an Enterprise licence. The built-in owner, admin, member, manager and editor roles are there on every install, and the audit record is written on every install whether or not you can read it back yet.',
    'SSO · RBAC · Audit logs · Self-host · Open source': 'SSO · RBAC · Audit logs',
    'SSO · RBAC · Audit logs · ·': 'SSO · RBAC · Audit logs',
    'Same freedom, built for more than one person. Free to start, free to': 'Same freedom, built for more than one person. Free to start, with no lock-in.',
    'Same freedom, built for more than one person. Free to start, free to self-host.': 'Same freedom, built for more than one person. Free to start, with no lock-in.',
    'Self-Hosting Options:': 'Deployment Options:',
    'Self-host': 'On-prem',
    'Self-host Kortix': 'Deploy Dosco',
    'Self-host anywhere': 'Run anywhere',
    'Self-host free': 'Free to deploy',
    'Self-host in minutes, or have us walk you through Cloud and Enterprise in a live demo.': 'Deploy in minutes, or have us walk you through Cloud and Enterprise in a live demo.',
    'Self-host in one line.': 'Deploy in one line.',
    'Self-host on your cloud, VPC, or on-prem': 'Run on your cloud, VPC, or on-prem',
    'Self-host on your cloud, VPC, or on-prem — no lock-in': 'Run on your cloud, VPC, or on-prem — no lock-in',
    'Self-host or managed cloud': 'On-prem or managed cloud',
    'Self-host or single-tenant. Network egress controls. Data never leaves.': 'Single-tenant. Network egress controls. Data never leaves.',
    'Self-host the same stack, anytime.': 'Run the same stack, anytime.',
    'Self-host the whole platform for free. Move to managed cloud per seat, and to enterprise when you need on-prem and advanced controls.': 'Run the whole platform on your infrastructure. Move to managed cloud per seat, and to enterprise when you need on-prem and advanced controls.',
    'Self-host when needed': 'On-prem when needed',
    'Self-host, VPC, on-prem, or air-gapped. SOC 2 Type II in progress.': 'VPC, on-prem, or air-gapped. SOC 2 Type II in progress.',
    'Self-host, VPC, on-prem, or air-gapped. Your data, config, and models stay yours.': 'VPC, on-prem, or air-gapped. Your data, config, and models stay yours.',
    'Self-host, bring your own models, no vendor lock-in.': 'Bring your own models, no vendor lock-in.',
    'Self-hostable': 'On-prem',
    'Self-hostable underneath.': 'Private underneath.',
    'Self-hosted': 'On-prem',
    "Self-hosted setups don't have OAuth wired up — paste a manifest and tokens to finish the install. Stored encrypted in this project's secrets": "Private setups don't have OAuth wired up — paste a manifest and tokens to finish the install. Stored encrypted in this project's secrets",
    'Self-hosted updates run from the host': 'Updates run from the host',
    'Self-hosting is free and always will be. Kortix Cloud is the same product with the box, the upgrades and the sandbox tier taken off your hands.': 'Running it yourself is free and always will be. Dosco Cloud is the same product with the box, the upgrades and the sandbox tier taken off your hands.',
    'Self-hosting is not a smaller Kortix with the interesting parts removed. It is the whole control plane — accounts, projects, repos, secrets, connectors, policies, audit — running inside your network, on storage you back up yourself.': 'The private deployment is not a smaller Dosco with the interesting parts removed. It is the whole control plane — accounts, projects, repos, secrets, connectors, policies, audit — running inside your network, on storage you back up yourself.',
    'Single sign-on is SAML 2.0. Every tool call is written to an audit record with the agent, the person or trigger, the outcome and the approver. Deployment is Dosco Cloud, your own VPC, or your own on-prem network it is, so you can read what you are running. It is not air-gapped: starting a ed stack pulls images over the network. For an isolated topology, talk to us': 'Single sign-on is SAML 2.0. Every tool call is written to an audit record with the agent, the person or trigger, the outcome and the approver. Deployment is Dosco Cloud, your own VPC, or your own on-prem network — and you can read what you are running. It is not air-gapped: starting a private stack pulls images over the network. For an isolated topology, talk to us.',
    'Single sign-on is SAML 2.0. Every tool call is written to an audit record with the agent, the person or trigger, the outcome and the approver. Deployment is Kortix Cloud, your own VPC, or your own on-prem network — it is open source, so you can read what you are running. It is not air-gapped: starting a self-hosted stack pulls images over the network. For an isolated topology, talk to us.': 'Single sign-on is SAML 2.0. Every tool call is written to an audit record with the agent, the person or trigger, the outcome and the approver. Deployment is Dosco Cloud, your own VPC, or your own on-prem network — and you can read what you are running. It is not air-gapped: starting a private stack pulls images over the network. For an isolated topology, talk to us.',
    'Start with one job, connect the tools it needs, and reach it from Slack, the web or the CLI. Free to start, free to': 'Start with one job, connect the tools it needs, and reach it from Slack, the web or the CLI. Free to start, with no lock-in.',
    'Start with one job, connect the tools it needs, and reach it from Slack, the web or the CLI. Free to start, free to self-host.': 'Start with one job, connect the tools it needs, and reach it from Slack, the web or the CLI. Free to start, with no lock-in.',
    'The Service software is available for ing on your own infrastructure, subject to the terms of the LICENSE file in our GitHub repository. ing is governed by the Dosco Public Source License (KPSL), which includes restrictions on network-accessible deployments and commercial use. For network-accessible deployments or commercial use beyond the LICENSE terms, a separate commercial license agreement is required. Please refer to the LICENSE file for complete terms and contact': 'The Service software is available for private deployment on your own infrastructure, subject to the terms of the LICENSE file in our repository. Private deployment is governed by the Dosco Public Source License (DPSL), which includes restrictions on network-accessible deployments and commercial use. For network-accessible deployments or commercial use beyond the LICENSE terms, a separate commercial license agreement is required. Please refer to the LICENSE file for complete terms and contact',
    'The Service software is available for self-hosting on your own infrastructure, subject to the terms of the LICENSE file in our GitHub repository. Self-hosting is governed by the Kortix Public Source License (KPSL), which includes restrictions on network-accessible deployments and commercial use. For network-accessible deployments or commercial use beyond the LICENSE terms, a separate commercial license agreement is required. Please refer to the LICENSE file for complete terms and contact': 'The Service software is available for private deployment on your own infrastructure, subject to the terms of the LICENSE file in our repository. Private deployment is governed by the Dosco Public Source License (DPSL), which includes restrictions on network-accessible deployments and commercial use. For network-accessible deployments or commercial use beyond the LICENSE terms, a separate commercial license agreement is required. Please refer to the LICENSE file for complete terms and contact',
    'VPC, on-prem, or air-gapped. SOC 2 Type II in progress': 'VPC, on-prem, or air-gapped. SOC 2 Type II in progress.',
    'VPC, on-prem, or air-gapped. Your data, config, and models stay yours': 'VPC, on-prem, or air-gapped. Your data, config, and models stay yours.',
    'and': 'No lock-in',
    'and Dosco Cloud, your VPC, or on-prem': 'No lock-in — Dosco Cloud, your VPC, or on-prem.',
    'and. Any model, your keys. Dosco Cloud, your own VPC, or fully on-prem': 'No lock-in. Any model, your keys. Dosco Cloud, your own VPC, or fully on-prem.',
    'and. Any model, your keys. Dosco Cloud, your own VPC, or your own on-prem network': 'No lock-in. Any model, your keys. Dosco Cloud, your own VPC, or your own on-prem network.',
    'and. Your data, your models, your infra': 'No lock-in. Your data, your models, your infra.',
    'anywhere': 'Run anywhere',
    'bring your own models, no vendor lock-in': 'Bring your own models, no vendor lock-in.',
    'by design': 'Yours by design',
    'ed': 'On-prem',
    "ed setups don't have OAuth wired up paste a manifest and tokens to finish the install. Stored encrypted in this project's secrets": "Private setups don't have OAuth wired up — paste a manifest and tokens to finish the install. Stored encrypted in this project's secrets",
    'ed updates run from the host': 'Updates run from the host',
    'free': 'Free to deploy',
    'in minutes, or have us walk you through Cloud and Enterprise in a live demo': 'Deploy in minutes, or have us walk you through Cloud and Enterprise in a live demo.',
    'in one line': 'Deploy in one line.',
    'ing Options:': 'Deployment Options:',
    'ing is free and always will be. Dosco Cloud is the same product with the box, the upgrades and the sandbox tier taken off your hands': 'Running it yourself is free and always will be. Dosco Cloud is the same product with the box, the upgrades and the sandbox tier taken off your hands.',
    'ing is not a smaller Dosco with the interesting parts removed. It is the whole control plane accounts, projects, repos, secrets, connectors, policies, audit running inside your network, on storage you back up yourself': 'The private deployment is not a smaller Dosco with the interesting parts removed. It is the whole control plane — accounts, projects, repos, secrets, connectors, policies, audit — running inside your network, on storage you back up yourself.',
    'it or run it on Dosco cloud nothing is locked to a vendor': 'Run it on Dosco cloud — nothing is locked to a vendor.',
    'on your cloud, VPC, or on-prem': 'Run on your cloud, VPC, or on-prem',
    'on your cloud, VPC, or on-prem no lock-in': 'Run on your cloud, VPC, or on-prem — no lock-in',
    'open &': 'No lock-in',
    'open & self-hostable': 'No lock-in',
    'or': '-- or on-prem',
    'or managed cloud': 'On-prem or managed cloud',
    'or single-tenant. Network egress controls. Data never leaves': 'Single-tenant. Network egress controls. Data never leaves.',
    'self-host': 'on-prem',
    'so the harness is never the thing you are locked into': 'So the harness is never the thing you are locked into',
    'the exact same stack, bring your own keys': 'Run the exact same stack, bring your own keys.',
    'the exact same stack, bring your own runtime and model keys. No black box, no lock-in': 'Run the exact same stack, bring your own runtime and model keys. No black box, no lock-in.',
    'the same stack, anytime': 'Run the same stack, anytime.',
    'the whole platform for free. Move to managed cloud per seat, and to enterprise when you need on-prem and advanced controls': 'Run the whole platform on your infrastructure. Move to managed cloud per seat, and to enterprise when you need on-prem and advanced controls.',
    'underneath': 'Private underneath.',
    'when needed': 'On-prem when needed',
    'with support for any AI model. Use Dosco Cloud or run it on your own systems': 'With support for any AI model. Use Dosco Cloud or run it on your own systems.',
    '· Any model, your keys ·, VPC, or on-prem': 'Any model, your keys · VPC or on-prem',
    '· SSO · RBAC · on-prem · no lock-in': 'SSO · RBAC · on-prem · no lock-in',
    '· SSO, RBAC & on-prem · Any model, your keys · No lock-in': 'SSO, RBAC & on-prem · Any model, your keys · No lock-in',
    '· SSO, RBAC & on-prem · No lock-in': 'SSO, RBAC & on-prem · No lock-in',
    '· · core': 'No lock-in',
}

# Strings the old naive transform blanked entirely (trailing-strip ate '.',
# '---', mdash, NBSP; removals ate pure-claim labels). Keyed by JSON path so
# the ambiguous '' value maps precisely. Applied only when the current value
# is blank -- a legitimate upstream change to real copy is left alone.
PATH_EMPTY_FIX = {
    "support/hub/faqWhatCreditsAnswerAfter": ".",
    "hardcodedUi/appHomePage/openRow1Title": "No lock-in",
    "hardcodedUi/appHomePricingPage/line153JsxTextOpenSource": "No lock-in",
    "hardcodedUi/componentsAdminAdminDashboardSections/line232JsxTextMdash": "\u2014",
    "hardcodedUi/componentsAdminAdminDashboardSections/line234JsxTextMdash": "\u2014",
    "hardcodedUi/componentsHomeCodeWindow/line35JsxTextNbsp": "\u00a0",
    "hardcodedUi/componentsHomeCodeWindow/line39JsxTextNbsp": "\u00a0",
    "hardcodedUi/componentsHomeCodeWindow/line42JsxTextNbsp": "\u00a0",
    "hardcodedUi/componentsHomeCodeWindow/line59JsxTextNbsp": "\u00a0",
    "hardcodedUi/componentsHomeCodeWindow/line74JsxTextNbsp": "\u00a0",
    "hardcodedUi/autoAppPresentationSlidesPlatformJsxAttrTitleOpenSourced5df9dc2": "No lock-in",
    "hardcodedUi/i18nComplete/text37a5d04181b5": "On-prem",
    "hardcodedUi/i18nComplete/text67a0d2e0dab4": "No lock-in",
    "hardcodedUi/i18nComplete/text7859cc3ee2ae": "on-prem",
    "hardcodedUi/i18nComplete/texta2536dee19c6": "On-prem",
    "hardcodedUi/i18nComplete/textcb3f91d54eee": "---",
}

# Real CLI invocation -- must survive ("kortix self-host start" is a command).
CLI_PH = "\x00CLI0\x00"
CLI_RE = re.compile(r"kortix self-host", re.IGNORECASE)

CLAIM_RE = re.compile(
    r"open[\s-]?source|self[\s-]?host(?:able|ed|ing)?|MIT[\s-]?licensed",
    re.IGNORECASE,
)


def tidy(s: str, orig: str) -> str:
    """Clean artifacts left by a removal. Never touches periods, dashes, NBSP."""
    s = re.sub(r" {2,}", " ", s)
    if "\u00b7" in s:
        parts = [p.strip() for p in s.split("\u00b7")]
        if any(p == "" for p in parts):
            parts = [p for p in parts if p]
            s = " \u00b7 ".join(parts)
    s = re.sub(r",\s*,", ",", s)
    s = re.sub(r"^\s*,\s*", "", s)
    s = re.sub(r"\u00b7\s*,\s*", "\u00b7 ", s)
    s = re.sub(r"\s*,\s*([.!?])", r"\1", s)
    s = re.sub(r"\.\s+\.", ".", s)
    s = re.sub(r" {2,}", " ", s)
    s = s.strip(" \t\r\n")
    if s:
        stripped = s.lstrip()
        o = orig.lstrip()
        if (
            o
            and o[0].isupper()
            and stripped[0].isalpha()
            and stripped[0].islower()
            and stripped[0].isascii()
        ):
            idx = s.index(stripped[0])
            s = s[:idx] + stripped[0].upper() + s[idx + 1 :]
    return s


def transform(s: str, path: str = "") -> str:
    if not isinstance(s, str):
        return s
    if s.strip() == "" and path in PATH_EMPTY_FIX:
        return PATH_EMPTY_FIX[path]
    if s in REWRITES:
        return REWRITES[s]

    # --- product naming ---
    s = s.replace("Kortix Computer", "Dosco Agent")
    s = s.replace("Kortix", "Dosco")
    s = s.replace("Suna", "Dosco")  # old product name, fully rebrand

    # --- tagline: "open-source AI Management System" -> "Dosco Agent Terminal" ---
    s = s.replace("open-source AI Management System", "Dosco Agent Terminal")
    s = s.replace("open-source AI management system", "Dosco Agent Terminal")
    s = s.replace("open source AI Management System", "Dosco Agent Terminal")

    # --- remove open-source / self-host phrasing (adjectives) ---
    s = CLI_RE.sub(CLI_PH, s)
    before = s
    s = CLAIM_RE.sub("", s)
    removed = s != before
    s = s.replace(CLI_PH, "kortix self-host")
    if removed:
        # restore original case of the CLI span when it was untouched
        s = tidy(s, before.replace(CLI_PH, "kortix self-host"))

    # --- github / open-source button labels ---
    s = s.replace("Star on GitHub", "Star")
    s = s.replace("View on GitHub", "View project")
    s = s.replace("stars on GitHub", "stars")

    # --- self-host install snippet ---
    s = s.replace(
        "curl -fsSL kortix.com/install",
        "Contact your administrator for access",
    )

    # --- emails ---
    s = re.sub(r"[\w.+-]+@kortix\.com", EMAIL, s)
    # .ai contact twins the .com rule misses (support hub, fault page,
    # region block). Demo/placeholder personas (ada/grace/alan/dom) stay.
    s = re.sub(r"\bsupport@kortix\.ai\b", EMAIL, s)
    sec_domain = EMAIL.split("@", 1)[1] if "@" in EMAIL else "dosco.live"
    s = re.sub(r"\bsecurity@kortix\.ai\b", f"security@{sec_domain}", s)

    # --- external URLs -> neutralize / repoint ---
    s = s.replace("https://github.com/kortix-ai/suna", "#")
    s = s.replace("https://github.com/kortix-ai", "#")
    s = s.replace("https://status.kortix.com", "#")
    s = s.replace("https://x.com/kortix", "#")
    s = s.replace("https://linkedin.com/company/kortix", "#")
    s = s.replace("https://kortix.com", CANON)
    s = s.replace("kortix.com/install", "#")
    s = s.replace("kortix.com", CANON)

    # Strings emptied by the removal above get the surviving benefit label.
    if s.strip() == "":
        return "No lock-in"
    return s


def walk(o, path=""):
    if isinstance(o, dict):
        return {k: walk(v, f"{path}/{k}" if path else k) for k, v in o.items()}
    if isinstance(o, list):
        return [walk(v, f"{path}[{i}]") for i, v in enumerate(o)]
    if isinstance(o, str):
        return transform(o, path)
    return o


with open(PATH, encoding="utf-8") as f:
    data = json.load(f)

data = walk(data)

with open(PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")

print(f"[transform-en] rewrote {PATH}")
