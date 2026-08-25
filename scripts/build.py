#!/usr/bin/env python3
"""
Software Observatory — static site generator.

Reads markdown files with YAML frontmatter from content/, renders HTML
pages using templates, computes backlinks from see_also references, and
writes everything to the site root.

Usage:
    .venv/bin/python build.py
"""

import os
import sys
import re
import html
import glob
import hashlib
import time
import shutil
from pathlib import Path

import yaml
import markdown


SITE_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = SITE_ROOT / "content"
OUTPUT_DIR = SITE_ROOT
CSS_DIR = SITE_ROOT / "css"
JS_DIR = SITE_ROOT / "js"

# Section pages rendered as clean directory URLs: /catalog/ -> catalog/index.html.
# Markdown bodies link these by bare filename (catalog.html#behavioral), and
# fix_link_depths rewrites them using this set.
SECTION_PAGES = {
    "catalog", "atlas", "framework", "glossary", "about",
    "contact", "privacy", "categories",
}

# ── Sensor family metadata ──────────────────────────────────────────────────

FAMILIES = [
    {
        "slug": "structural",
        "num": "01",
        "name": "Structural",
        "icon": "\u25a0",
        "question": "Is this artifact internally coherent?",
        "examples": "Compiler, type checker, linter, formatter, schema validator",
        "stack_levels": ["compilation", "static-analysis"],
    },
    {
        "slug": "behavioral",
        "num": "02",
        "name": "Behavioral",
        "icon": "●",
        "question": "Does it do what we expect?",
        "examples": "Unit, integration, E2E, contract, snapshot tests",
        "stack_levels": ["behavioral-tests", "integration-tests"],
    },
    {
        "slug": "test-effectiveness",
        "num": "03",
        "name": "Test Effectiveness",
        "icon": "▲",
        "question": "Do our tests actually detect failures?",
        "examples": "Coverage, diff coverage, mutation testing",
        "stack_levels": ["mutation-testing"],
    },
    {
        "slug": "invariants",
        "num": "04",
        "name": "Invariants",
        "icon": "◆",
        "question": "What must always be true?",
        "examples": "Balance >= 0, every FK valid, every request has one ID",
        "stack_levels": ["static-analysis", "production-behavior"],
    },
    {
        "slug": "adversarial",
        "num": "05",
        "name": "Adversarial",
        "icon": "✖",
        "question": "Can we make our evidence of correctness fail?",
        "examples": "Fuzzing, fault injection, chaos, metamorphic testing",
        "stack_levels": ["property-metamorphic", "mutation-testing"],
    },
    {
        "slug": "runtime",
        "num": "06",
        "name": "Runtime",
        "icon": "○",
        "question": "What is it actually doing?",
        "examples": "Logs, traces, metrics, profiles, high-cardinality events",
        "stack_levels": ["production-behavior"],
    },
    {
        "slug": "change",
        "num": "07",
        "name": "Change",
        "icon": "→",
        "question": "What did this change actually affect?",
        "examples": "API compatibility, canary, shadow traffic, error budget, A/B testing",
        "stack_levels": ["canary-shadow", "user-outcome"],
    },
    {
        "slug": "architecture",
        "num": "08",
        "name": "Architecture",
        "icon": "▣",
        "question": "Is the system becoming harder to reason about?",
        "examples": "Dependency graphs, coupling, fitness functions, hotspots",
        "stack_levels": ["static-analysis"],
    },
    {
        "slug": "evolution",
        "num": "09",
        "name": "Evolution",
        "icon": "⟳",
        "question": "Does this look like changes that caused trouble before?",
        "examples": "Revert rate, regression rate, churn, incident correlation",
        "stack_levels": ["user-outcome"],
    },
    {
        "slug": "comprehension",
        "num": "10",
        "name": "Human Comprehension",
        "icon": "✔",
        "question": "Can another observer understand and challenge this?",
        "examples": "Review, explainability tests, documentation drift, onboarding",
        "stack_levels": ["static-analysis", "behavioral-tests", "production-behavior", "user-outcome"],
    },
]

FAMILY_BY_SLUG = {f["slug"]: f for f in FAMILIES}

# Confidence stack layers (top to bottom)
STACK_LAYERS = [
    {"slug": "user-outcome",          "label": "User outcome",           "desc": "Does the system produce the intended result for users?"},
    {"slug": "production-behavior",   "label": "Production behavior",   "desc": "What is it actually doing in the real world?"},
    {"slug": "canary-shadow",         "label": "Canary / shadow",       "desc": "Does the new version behave differently from the old?"},
    {"slug": "integration-tests",     "label": "Integration tests",    "desc": "Does it work connected to its real dependencies?"},
    {"slug": "behavioral-tests",      "label": "Behavioral tests",      "desc": "Does it do what we expect for given inputs?"},
    {"slug": "property-metamorphic",  "label": "Property / metamorphic","desc": "Does it obey generalized properties across input spaces?"},
    {"slug": "mutation-testing",      "label": "Mutation testing",      "desc": "Would our tests detect plausible wrong implementations?"},
    {"slug": "static-analysis",      "label": "Static analysis / types","desc": "Is it internally coherent and structurally valid?"},
    {"slug": "compilation",           "label": "Compilation",          "desc": "Is it a valid inhabitant of the language?"},
    {"slug": "source-text",           "label": "Source text",           "desc": "The opaque artifact itself."},
]

# Lifecycle stages for the atlas grid (left to right: when the signal arrives).
# Each stage folds in one or more confidence-stack levels; the stack remains
# the narrative model, this is the operational one.
LIFECYCLE_STAGES = [
    {"slug": "build",      "label": "Build",      "desc": "Signals available before the code runs.",
     "levels": ["source-text", "compilation", "static-analysis"]},
    {"slug": "test",       "label": "Test",       "desc": "Signals from exercising the system with chosen inputs.",
     "levels": ["mutation-testing", "property-metamorphic", "behavioral-tests", "integration-tests"]},
    {"slug": "deploy",     "label": "Deploy",     "desc": "Signals from rolling a change out safely.",
     "levels": ["canary-shadow"]},
    {"slug": "production", "label": "Production", "desc": "Signals from the live system.",
     "levels": ["production-behavior"]},
    {"slug": "outcome",    "label": "Outcome",    "desc": "Signals about real-world results and history.",
     "levels": ["user-outcome"]},
]

STAGE_BY_LEVEL = {}
for _stage in LIFECYCLE_STAGES:
    for _lvl in _stage["levels"]:
        STAGE_BY_LEVEL[_lvl] = _stage["slug"]

# Scatter positions for the homepage latency/efficacy diagram, keyed by
# confidence-stack layer slug. x = feedback latency (0=instant, 100=slow),
# y = efficacy of the signal (0=suggestive, 100=definitive). Hand-tuned;
# "source-text" is not a sensor and is intentionally absent.
STACK_SCATTER = {
    "compilation":          {"x": 4,  "y": 82},
    "static-analysis":      {"x": 14, "y": 64},
    "mutation-testing":     {"x": 46, "y": 78},
    "property-metamorphic": {"x": 42, "y": 62},
    "behavioral-tests":     {"x": 32, "y": 48},
    "integration-tests":    {"x": 56, "y": 58},
    "canary-shadow":        {"x": 66, "y": 50},
    "production-behavior":  {"x": 82, "y": 42},
    "user-outcome":         {"x": 94, "y": 92},
}

# Ordinal scales mapping sensor frontmatter onto the same axes
TIER_LABELS = {
    "I":   "controlled study",
    "II":  "observational study",
    "III": "case study",
    "IV":  "argument",
}

LATENCY_X = {
    "milliseconds": 6,
    "seconds": 20,
    "minutes": 42,
    "minutes-hours": 56,
    "hours": 62,
    "seconds-hours": 68,
    "days": 76,
    "weeks": 90,
    "months": 95,
    "varies": 50,
}
ORACLE_Y = {
    "minimum": 14,
    "low": 30,
    "medium": 50,
    "high": 72,
    "maximum": 92,
}

# ── Oracle strength bar widths ──────────────────────────────────────────────

ORACLE_WIDTHS = {
    "maximum": 100,
    "high": 90,
    "medium": 60,
    "low": 40,
    "minimum": 20,
}

INDEPENDENCE_DOTS = {
    "maximum": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    "minimum": 1,
}

LATENCY_LABELS = {
    "milliseconds": "ms",
    "seconds": "s",
    "minutes": "m",
    "minutes-hours": "m-h",
    "hours": "h",
    "seconds-hours": "s-h",
    "days": "d",
    "weeks": "w",
    "months": "mo",
    "varies": "varies",
}

# Full-word forms for display contexts where the abbreviation alone is opaque
# (card badges, sensor page sidebar). Defaults to the key itself with hyphens
# spelled out as "to"; entries below only exist to reorder compound ranges.
class _LatencyWords(dict):
    def __missing__(self, key):
        return key.replace("-", " to ")

LATENCY_WORDS = _LatencyWords({
    "minutes-hours": "minutes to hours",
    "seconds-hours": "seconds to hours",
})


def latency_badge_html(latency_key):
    """Small latency badge with full-word text and a hover tooltip."""
    word = LATENCY_WORDS[latency_key]
    tip = f"How long it takes to get this feedback: {word}"
    return (f'<span class="latency-badge" title="{html.escape(tip)}">'
            f'<span class="sr-only">Feedback latency: </span>~{html.escape(word)}</span>')


def note_hover_html(note):
    """A small (?) marker whose hover text carries extra color for a property."""
    if not note:
        return ""
    return (f' <span class="prop-note" title="{html.escape(note)}" '
            f'aria-label="{html.escape(note)}">(?)</span>')


def provisional_note_html(note):
    """A visible inline hedge rendered in the sidebar under the scalar it
    qualifies. Used for claims the field has not settled (e.g. model
    correlation effects on second-agent-review independence)."""
    if not note:
        return ""
    return ('\n          <dd class="provisional-note">Provisional — '
            f'{html.escape(note)}</dd>')


# ── Markdown rendering ──────────────────────────────────────────────────────

def render_markdown(text):
    """Render markdown to HTML."""
    md = markdown.Markdown(extensions=["tables", "fenced_code", "smarty"])
    return md.convert(text)


def fix_link_depths(html_str, pages_depth="", sensor_slugs=()):
    """Rewrite relative URLs in rendered markdown HTML to site-absolute URLs.

    Sensor markdown links to sibling sensors by bare filename
    (type-checker.html) and to section pages the same way (catalog.html,
    atlas.html). All pages now live at clean directory URLs
    (/sensors/<slug>/, /catalog/, ...) and every generated link is
    site-absolute, so this rewrites those bare filenames to their absolute
    destinations. pages_depth is accepted for signature compatibility but
    ignored.

    Also adds a class to inline <a> tags so they get link styling.
    """
    import re

    # Add link-body class to <a> tags that don't already have a class
    # This gives them visible link styling
    def add_link_class(match):
        tag = match.group(0)
        if 'class="' in tag:
            return tag  # already has a class
        if 'href="#"' in tag:
            return tag  # placeholder links
        return tag.replace('<a ', '<a class="body-link" ', 1)

    html_str = re.sub(r'<a(?![^>]*class=)[^>]*>', add_link_class, html_str)

    def fix_href(match):
        full = match.group(0)
        url = match.group(1)
        if url.startswith(('http://', 'https://', '#', 'mailto:', '/')):
            return full
        path, _, frag = url.partition("#")
        stem = path.removesuffix(".html")
        if "/" not in path and stem in sensor_slugs:
            dest = f"/sensors/{stem}/"
        elif "/" not in path and stem in SECTION_PAGES:
            dest = f"/{stem}/"
        else:
            return full  # unrecognized; leave for the link checker to flag
        return f'href="{dest}{"#" + frag if frag else ""}"'

    html_str = re.sub(r'href="([^"]+)"', fix_href, html_str)

    return html_str


# ── Frontmatter parsing ─────────────────────────────────────────────────────

def parse_frontmatter(filepath):
    """Parse a markdown file with YAML frontmatter. Returns (meta, body)."""
    with open(filepath, "r") as f:
        content = f.read()

    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2].strip()
    return meta, body


# ── Sensor loading ──────────────────────────────────────────────────────────

def load_sensors():
    """Load all sensor markdown files. Returns list of dicts."""
    sensors = []
    sensor_dir = CONTENT_DIR / "sensors"
    if not sensor_dir.exists():
        return sensors

    sensor_slugs = {p.stem for p in sensor_dir.glob("*.md")}
    for filepath in sorted(sensor_dir.glob("*.md")):
        meta, body = parse_frontmatter(filepath)
        slug = filepath.stem
        meta["slug"] = slug
        meta["body_html"] = fix_link_depths(render_markdown(body), sensor_slugs=sensor_slugs)
        meta["filename"] = str(filepath)
        sensors.append(meta)

    return sensors


def compute_backlinks(sensors):
    """For each sensor, find all other sensors that reference it in see_also."""
    by_id = {s["id"]: s for s in sensors}
    backlinks = {s["id"]: [] for s in sensors}

    for sensor in sensors:
        for ref_id in sensor.get("see_also", []):
            if ref_id in backlinks:
                ref_sensor = by_id.get(ref_id)
                if ref_sensor:
                    backlinks[ref_id].append({
                        "from_id": sensor["id"],
                        "from_title": sensor["title"],
                        "from_slug": sensor["slug"],
                        "from_family": sensor.get("family", ""),
                        "context": f"references this as a related sensor",
                    })

    return backlinks


def resolve_see_also(see_also_ids, sensors_by_id, families_by_slug):
    """Resolve see_also IDs to objects with title, slug, family, url.
    All urls are site-absolute."""
    results = []
    for ref in see_also_ids:
        if ref in sensors_by_id:
            s = sensors_by_id[ref]
            results.append({
                "title": s["title"],
                "family": FAMILY_BY_SLUG.get(s.get("family", ""), {}).get("name", ""),
                "family_slug": s.get("family", ""),
                "url": f"/sensors/{s['slug']}/",
            })
        elif ref in families_by_slug:
            f = families_by_slug[ref]
            results.append({
                "title": f["name"],
                "family": "Family",
                "family_slug": f["slug"],
                "url": f"/catalog/#{f['slug']}",
            })
        elif ref == "atlas":
            results.append({
                "title": "Sensor Atlas",
                "family": "Atlas",
                "family_slug": "atlas",
                "url": "/atlas/",
            })
    return results


def blurb_text(body_html, limit=200):
    """Plain-text blurb from rendered body HTML.

    Strips tags, decodes HTML entities (so callers can html.escape exactly
    once), collapses whitespace to the first paragraph, and truncates at a
    sentence boundary when the paragraph exceeds `limit` chars. Falls back
    to a word boundary + ellipsis if no sentence ends in the window.
    """
    # First paragraph only: rendered markdown wraps each source paragraph in
    # <p> tags, so split on paragraph boundaries rather than raw newlines
    # (source lines are hard-wrapped and would otherwise cut mid-sentence).
    text = re.sub(r"<[^>]+>", "", body_html)
    paragraphs = re.split(r"\n\s*\n", text.strip())
    first = " ".join(html.unescape(paragraphs[0]).split())
    if len(first) <= limit:
        return first
    window = first[:limit]
    ends = [m.end() for m in re.finditer(r"""[.!?]+["')\]]*(?=\s|$)""", window)]
    if ends and ends[-1] >= limit // 2:
        return window[:ends[-1]].rstrip()
    return window.rsplit(" ", 1)[0].rstrip(",;:") + "…"


def add_heading_ids(html_str, used_ids=None):
    """Give <h2>/<h3> elements stable ids (slugified text) so they can be
    deep-linked. Headings that already have an id are left alone.
    `used_ids` tracks collisions across the whole page (a page body may be
    assembled from several fragments, so callers should share one set)."""
    if used_ids is None:
        used_ids = set()

    def slugify(text):
        s = re.sub(r"<[^>]+>", "", text)
        s = html.unescape(s).lower()
        s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
        return s or "section"

    def replace(match):
        tag, attrs, inner = match.group(1), match.group(2), match.group(3)
        if 'id="' in attrs:
            m = re.search(r'id="([^"]+)"', attrs)
            if m:
                used_ids.add(m.group(1))
            return match.group(0)
        base = slugify(inner)
        slug, n = base, 2
        while slug in used_ids:
            slug = f"{base}-{n}"
            n += 1
        used_ids.add(slug)
        return f'<{tag}{attrs} id="{slug}">{inner}</{tag}>'

    return re.sub(r'<(h[23])([^>]*)>(.*?)</h[23]>', replace, html_str, flags=re.S)


def oracle_dots_html(oracle_str):
    """Render the 5-dot oracle meter."""
    filled = {"maximum": 5, "high": 4, "medium": 3, "low": 2, "minimum": 1}.get(oracle_str, 0)
    dots = ""
    for i in range(5):
        cls = "filled" if i < filled else "empty"
        dots += f'<span class="dot {cls}"></span>'
    return dots


def independence_dots_html(ind_str):
    """Render the 5-dot independence meter."""
    filled = INDEPENDENCE_DOTS.get(ind_str, 0)
    dots = ""
    for i in range(5):
        cls = "filled" if i < filled else "empty"
        dots += f'<span class="dot {cls}"></span>'
    return dots


# ── HTML templates ──────────────────────────────────────────────────────────

def html_head(title, canonical="", json_ld=""):
    """canonical is a site-relative path like 'catalog/' ('' for the root)."""
    canonical_link = ""
    if canonical:
        canonical_link = f'\n  <link rel="canonical" href="{SITE_URL}/{canonical}">'
    json_ld_block = ""
    if json_ld:
        json_ld_block = f'\n  <script type="application/ld+json">\n{json_ld}\n  </script>'
    full_title = title if title == "Software Observatory" else f"{title} — Software Observatory"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(full_title)}</title>
  <meta name="description" content="A catalog of epistemic sensors for software correctness — the observable signals that reduce uncertainty about whether a system is correct, maintainable, and behaving as intended.">{canonical_link}
  <meta property="og:type" content="website">
  <meta property="og:title" content="{html.escape(full_title)}">
  <meta property="og:description" content="A catalog of epistemic sensors for software correctness.">
  <meta property="og:url" content="{SITE_URL}/{canonical}">
  <meta property="og:image" content="{SITE_URL}/og.png">
  <meta property="og:site_name" content="Software Observatory">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{html.escape(full_title)}">
  <meta name="twitter:description" content="A catalog of epistemic sensors for software correctness.">
  <meta name="twitter:image" content="{SITE_URL}/og.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=JetBrains+Mono:wght@400;500;600&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/observatory.css">
  <link rel="alternate" type="application/rss+xml" title="Software Observatory" href="{SITE_URL}/rss.xml">{json_ld_block}
  <script data-goatcounter="https://stats.softwareobservatory.com/count"
          async src="https://stats.softwareobservatory.com/count.js"></script>
</head>"""


def html_header():
    """Site header with nav. All links are site-absolute."""
    nav_items = [
        ("/catalog/", "Catalog"),
        ("/atlas/", "Atlas"),
        ("/framework/", "Framework"),
        ("/glossary/", "Glossary"),
        ("/about/", "About"),
    ]
    nav_html = "\n".join(f'      <a href="{href}">{label}</a>' for href, label in nav_items)
    return f"""  <header class="site-header">
    <a href="/" class="logo">
      <span class="logo-mark" aria-hidden="true"><svg viewBox="0 0 32 32" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <!-- brass spyglass on a small tripod, angled up to the right -->
        <g transform="rotate(-30 16 16)">
          <rect x="4" y="13.5" width="7" height="5" rx="1"/>
          <rect x="11" y="12.5" width="8" height="7" rx="1"/>
          <rect x="19" y="11" width="6.5" height="10" rx="1"/>
          <line x1="25.5" y1="12" x2="25.5" y2="20"/>
          <line x1="17" y1="19.5" x2="17" y2="24"/>
          <line x1="17" y1="24" x2="12" y2="28"/>
          <line x1="17" y1="24" x2="22" y2="28"/>
        </g>
      </svg></span>
      <span class="logo-text">Software&nbsp;Observatory</span>
    </a>
    <nav class="primary-nav">
{nav_html}
    </nav>
    <div class="search-box">
      <input type="search" class="search-input" placeholder="Search sensors…" aria-label="Search sensors" autocomplete="off">
      <div class="search-results" hidden></div>
      <noscript><p class="search-noscript"><a href="/catalog/">Browse the catalog</a> or <a href="/categories/">browse by category</a>.</p></noscript>
    </div>
  </header>"""


def html_footer():
    return f"""  <footer class="site-footer">
    <div class="footer-inner">
      <p class="footer-tagline">Software Observatory — a catalog of epistemic sensors for software.</p>
      <p class="footer-copy">© 2026 <a href="https://justin.abrah.ms/">Justin Abrahms</a> · <a href="/about/">About</a> · <a href="/glossary/">Glossary</a> · <span class="license-badge">CC BY-NC-SA 4.0</span></p>
    </div>
  </footer>"""


def html_page(title, body_content, canonical="", json_ld=""):
    """canonical: site-relative URL for the canonical link (e.g. 'about/').
    json_ld: JSON-LD string to inject as a script block in <head>."""
    # Deep-linkable headings get ids before the page is assembled
    body_content = add_heading_ids(body_content)
    return f"""{html_head(title, canonical=canonical, json_ld=json_ld)}
<body>
{html_header()}
{body_content}
{html_footer()}
  <script src="/js/main.js"></script>
</body>
</html>"""


# ── Page generators ─────────────────────────────────────────────────────────

def generate_sensor_page(sensor, backlinks, sensors_by_id, families_by_slug, output_dir):
    """Generate a single sensor detail page."""
    family = FAMILY_BY_SLUG.get(sensor.get("family", ""), {})
    family_name = family.get("name", sensor.get("family", ""))
    family_slug = family.get("slug", "")

    # Resolve see_also (all urls site-absolute)
    see_also_items = resolve_see_also(sensor.get("see_also", []), sensors_by_id, families_by_slug)

    # Resolve backlinks
    backlink_items = []
    for bl in backlinks.get(sensor["id"], []):
        backlink_items.append({
            "title": bl["from_title"],
            "url": f"/sensors/{bl['from_slug']}/",
            "context": bl["context"],
        })

    # Categories
    categories = sensor.get("categories", [])

    # References (structured frontmatter)
    references = sensor.get("references", [])
    refs_html = ""
    if references:
        tools = [r for r in references if r.get("kind") == "tool"]
        papers = [r for r in references if r.get("kind") == "publication"]
        others = [r for r in references if r.get("kind") not in ("tool", "publication")]

        sections = []

        if papers:
            items = ""
            for r in papers:
                parts = []
                if r.get("url"):
                    parts.append(f'<a href="{html.escape(r["url"])}" class="wikilink">{html.escape(r["title"])}</a>')
                else:
                    parts.append(html.escape(r["title"]))
                meta_parts = []
                if r.get("authors"):
                    meta_parts.append(html.escape(r["authors"]))
                if r.get("year"):
                    meta_parts.append(html.escape(str(r["year"])))
                if r.get("tier"):
                    tier_label = TIER_LABELS.get(str(r["tier"]).upper(), str(r["tier"]))
                    meta_parts.append(html.escape(tier_label))
                if r.get("venue"):
                    meta_parts.append(html.escape(r["venue"]))
                if meta_parts:
                    parts.append(f'<span class="ref-meta">{" · ".join(meta_parts)}</span>')
                items += f"          <li>{' — '.join(parts)}</li>\n"
            sections.append(f'        <h3 class="references-subheading">Publications</h3>\n        <ul class="reference-list">\n{items.rstrip()}\n        </ul>')

        if tools:
            items = ""
            for r in tools:
                title = html.escape(r["title"])
                if r.get("url"):
                    title = f'<a href="{html.escape(r["url"])}" class="wikilink">{title}</a>'
                desc = f'<span class="ref-desc">{html.escape(r["description"])}</span>' if r.get("description") else ""
                items += f"          <li><span class=\"ref-title\">{title}</span>{desc}</li>\n"
            sections.append(f'        <h3 class="references-subheading">Tooling</h3>\n        <ul class="reference-list reference-tools">\n{items.rstrip()}\n        </ul>')

        if others:
            items = ""
            for r in others:
                title = html.escape(r["title"])
                if r.get("url"):
                    title = f'<a href="{html.escape(r["url"])}" class="wikilink">{title}</a>'
                meta_parts = []
                if r.get("year"):
                    meta_parts.append(str(r["year"]))
                if meta_parts:
                    title += f' <span class="ref-meta">{html.escape(" · ".join(meta_parts))}</span>'
                items += f"          <li>{title}</li>\n"
            sections.append(f'        <h3 class="references-subheading">Further reading</h3>\n        <ul class="reference-list">\n{items.rstrip()}\n        </ul>')

        refs_html = f'        <h2>References</h2>\n' + "\n".join(sections)

    # See-also grid HTML
    see_also_html = ""
    if see_also_items:
        cards = ""
        for item in see_also_items:
            cards += f"""          <a href="{item['url']}" class="see-also-card">
            <span class="see-also-type">{html.escape(item['family'])}</span>
            <span class="see-also-title">{html.escape(item['title'])}</span>
          </a>\n"""
        see_also_html = f"""        <h2>Related sensors</h2>
        <div class="see-also-grid">
{cards.rstrip()}
        </div>"""

    # Category links
    cat_html = ""
    if categories:
        cat_links = ""
        for cat in categories:
            # Link to family section if it matches a family slug
            fam = FAMILY_BY_SLUG.get(cat.lower().replace(" ", "-"), {})
            if fam:
                cat_links += f'          <a href="/catalog/#{fam["slug"]}" class="cat-link">{html.escape(cat)}</a>\n'
            else:
                cat_slug = re.sub(r"[^a-z0-9]+", "-", cat.lower()).strip("-")
                cat_links += f'          <a href="/categories/#{cat_slug}" class="cat-link">{html.escape(cat)}</a>\n'
        cat_html = f"""        <div class="entry-categories">
          <span class="cat-label">Categories:</span>
{cat_links.rstrip()}
        </div>"""

    # Backlinks sidebar
    backlink_html = ""
    if backlink_items:
        items = ""
        for bl in backlink_items:
            items += f"""          <li><a href="{bl['url']}">{html.escape(bl['title'])}</a>
            <span class="backlink-context">{html.escape(bl['context'])}</span></li>\n"""
        backlink_html = f"""      <div class="sidebar-box">
        <h3 class="sidebar-heading">What links here</h3>
        <ul class="backlink-list">
{items.rstrip()}
        </ul>
      </div>"""

    # Category sidebar
    cat_sidebar_html = ""
    if categories:
        items = ""
        for cat in categories:
            fam = FAMILY_BY_SLUG.get(cat.lower().replace(" ", "-"), {})
            if fam:
                url = f"/catalog/#{fam['slug']}"
            else:
                cat_slug = re.sub(r"[^a-z0-9]+", "-", cat.lower()).strip("-")
                url = f"/categories/#{cat_slug}"
            items += f'          <li><a href="{url}">Category: {html.escape(cat)}</a></li>\n'
        cat_sidebar_html = f"""      <div class="sidebar-box">
        <h3 class="sidebar-heading">Related categories</h3>
        <ul class="sidebar-cat-list">
{items.rstrip()}
        </ul>
      </div>"""

    body = f"""  <div class="wiki-layout">
    <article class="signal-detail">
      <p class="breadcrumb"><a href="/catalog/">Catalog</a> › <a href="/catalog/#{family_slug}">{html.escape(family_name)}</a> › {html.escape(sensor['title'])}</p>

      <header class="signal-detail-header">
        <h1 class="signal-detail-title">{html.escape(sensor['title'])}</h1>
        <div class="signal-detail-meta">
          <span class="tag tag-family">{html.escape(family_name)}</span>
          <span class="tag tag-confidence">{html.escape(sensor.get('oracle', '').title())} oracle</span>
          <span class="tag tag-type">{html.escape(sensor.get('type', '').title())}</span>
        </div>
      </header>

      <div class="signal-detail-body">
        {sensor['body_html']}

        {see_also_html}

{cat_html}

{refs_html}
      </div>
    </article>

    <aside class="wiki-sidebar">
      <div class="sidebar-box">
        <h3 class="sidebar-heading">Sensor properties</h3>
        <dl class="meta-list">
          <dt>Family</dt>           <dd><a href="/catalog/#{family_slug}" class="wikilink">{html.escape(family_name)}</a></dd>
          <dt>Oracle</dt>          <dd>{html.escape(sensor.get('oracle', '').title())}{note_hover_html(sensor.get('oracle_note'))}</dd>
          <dt>Independence</dt>     <dd>{html.escape(sensor.get('independence', '').title())}{note_hover_html(sensor.get('independence_note'))}</dd>{provisional_note_html(sensor.get('provisional'))}
          <dt>Scope</dt>           <dd>{html.escape(sensor.get('scope', '').replace('-', ' ').title())}{note_hover_html(sensor.get('scope_note'))}</dd>
          <dt>Latency</dt>         <dd>{html.escape(LATENCY_WORDS[sensor.get('latency', '')].capitalize())}{note_hover_html(sensor.get('latency_note'))}</dd>
          <dt>Actionability</dt>   <dd>{html.escape(sensor.get('actionability', '').title())}{note_hover_html(sensor.get('actionability_note'))}</dd>
          <dt>Type</dt>             <dd>{html.escape(sensor.get('type', '').title())}{note_hover_html(sensor.get('type_note'))}</dd>
          <dt>Entry ID</dt>        <dd>{html.escape(sensor.get('id', ''))}</dd>
          <dt>Reviewed</dt>        <dd>{html.escape(str(sensor.get('last_reviewed', ''))[:7])}</dd>
        </dl>
      </div>
{backlink_html}
{cat_sidebar_html}
    </aside>
  </div>"""

    page_html = html_page(f"{sensor['title']}", body, canonical=f"sensors/{sensor['slug']}/")
    out_path = output_dir / "sensors" / sensor["slug"] / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)


def generate_catalog_page(sensors, output_dir):
    """Generate the catalog page with all families."""

    # Group sensors by family
    by_family = {}
    for s in sensors:
        fam = s.get("family", "uncategorized")
        by_family.setdefault(fam, []).append(s)

    # Build family sections
    sections_html = ""
    for family in FAMILIES:
        fam_sensors = by_family.get(family["slug"], [])
        if not fam_sensors:
            continue

        cards = ""
        for s in fam_sensors:
            oracle_str = s.get("oracle", "low")
            oracle_d = oracle_dots_html(oracle_str)
            lat = latency_badge_html(s.get("latency", ""))
            title = s["title"]
            slug = s["slug"]

            cards += f"""          <a class="signal-card" href="/sensors/{slug}/">
            <div class="signal-card-meta">
              <span class="tag tag-family">{html.escape(family['name'])}</span>
              <span class="tag tag-type">{html.escape(s.get('type', '').title())}</span>
            </div>
            <h3 class="signal-card-title">{html.escape(title)}</h3>
            <p class="signal-card-blurb">{html.escape(blurb_text(s.get('body_html', ''), 200))}</p>
            <div class="signal-card-footer">
              <span class="oracle-meter">{oracle_d} Oracle</span>
              {lat}
            </div>
          </a>\n"""

        sections_html += f"""      <section class="family-section" id="{family['slug']}" data-family="{family['slug']}">
        <div class="family-header">
          <span class="family-num">{family['num']}</span>
          <div>
            <h2 class="family-title">{html.escape(family['name'])}</h2>
            <p class="family-tagline">"{html.escape(family['question'])}"</p>
          </div>
        </div>
        <div class="signal-grid">
{cards.rstrip()}
        </div>
      </section>

"""

    # Filter sidebar
    filter_families = ""
    for f in FAMILIES:
        count = len(by_family.get(f["slug"], []))
        filter_families += f'          <li><button type="button" data-family="{f["slug"]}" aria-pressed="false">{html.escape(f["name"])} <span class="count">{count}</span></button></li>\n'

    total = len(sensors)

    body = f"""  <section class="page-header">
    <p class="eyebrow">The Catalog</p>
    <h1 class="page-title">Sensor Catalog</h1>
    <p class="page-lede">
      A catalog of <a href="/glossary/#epistemic-sensor" class="wikilink">epistemic sensors</a> — the
      observable signals that increase our confidence that a system is correct,
      maintainable, and behaving as intended. Organized into {len(FAMILIES)} families.
      Each entry documents what the sensor can detect, what it cannot detect,
      how easily it can be gamed, and what evidence it produces.
    </p>
  </section>

  <div class="catalog-layout">
    <aside class="filter-sidebar">
      <div class="filter-group">
        <h3 class="filter-heading">Sensor Family</h3>
        <ul class="filter-list" id="family-filter">
          <li><button type="button" class="active" data-family="all" aria-pressed="true">All Families <span class="count">{total}</span></button></li>
{filter_families.rstrip()}
        </ul>
      </div>
    </aside>

    <div class="catalog-content">
{sections_html.rstrip()}
    </div>
  </div>"""

    page_html = html_page("Sensor Catalog", body, canonical="catalog/")
    out_path = output_dir / "catalog" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)


def generate_atlas_page(sensors, output_dir):
    """Generate the atlas page: a family x lifecycle-stage grid, plus a
    dependency map of how families lean on each other."""

    # Group sensors by family
    by_family = {}
    for s in sensors:
        fam = s.get("family", "uncategorized")
        by_family.setdefault(fam, []).append(s)

    # Grid: rows = families, columns = lifecycle stages
    matrix_rows = ""
    for family in FAMILIES:
        fam_sensors = by_family.get(family["slug"], [])

        matrix_rows += f"""        <div class="matrix-row">
          <div class="matrix-row-label">
            <span class="matrix-fam-num">{family['num']}</span>
            <span class="matrix-fam-icon fam-{family['slug']}" aria-hidden="true">{family['icon']}</span>
            <a href="/catalog/#{family['slug']}" class="matrix-fam-name">{html.escape(family['name'])}</a>
          </div>
"""

        for stage in LIFECYCLE_STAGES:
            cell_sensors = []
            for s in fam_sensors:
                stage_slug = STAGE_BY_LEVEL.get(s.get("stack_level", ""), "")
                if stage_slug == stage["slug"]:
                    cell_sensors.append(s)

            if cell_sensors:
                chips = ""
                for s in cell_sensors:
                    chips += f'<a href="/sensors/{s["slug"]}/" class="matrix-chip">{html.escape(s["title"])}</a>\n'
                matrix_rows += f"""          <div class="matrix-cell has-sensors">
            {chips.rstrip()}
          </div>
"""
            else:
                matrix_rows += '          <div class="matrix-cell empty"></div>\n'

        matrix_rows += "        </div>\n"

    # Column headers (earliest signal first)
    col_headers = ""
    for stage in LIFECYCLE_STAGES:
        col_headers += f"""            <div class="matrix-col-header" title="{html.escape(stage['desc'])}">
              <span class="col-label">{html.escape(stage['label'])}</span>
            </div>
"""

    # Family dependency graph, drawn from see_also references.
    # A reference from a sensor in family A to family B means A leans on B.
    fam_slug_aliases = {}
    for f in FAMILIES:
        fam_slug_aliases[f["slug"]] = f["slug"]
        fam_slug_aliases[f["slug"] + "-family"] = f["slug"]

    sensors_by_id = {s["id"]: s for s in sensors}
    # edge key: (src, tgt); value: list of contributing sensor titles
    edge_sensors = {}
    for s in sensors:
        src = s.get("family", "")
        if not src:
            continue
        for ref in s.get("see_also", []):
            tgt = None
            if ref in fam_slug_aliases:
                tgt = fam_slug_aliases[ref]
            elif ref in sensors_by_id:
                tgt = sensors_by_id[ref].get("family", "")
            if tgt and tgt != src:
                key = (src, tgt)
                edge_sensors.setdefault(key, [])
                if s["title"] not in edge_sensors[key]:
                    edge_sensors[key].append(s["title"])

    # Keep the strongest edges (most contributing sensors), one direction per pair
    pair_best = {}
    for (src, tgt), titles in edge_sensors.items():
        pair = tuple(sorted([src, tgt]))
        if pair not in pair_best or len(titles) > len(pair_best[pair][2]):
            pair_best[pair] = (src, tgt, titles)

    strong_edges = sorted(pair_best.values(), key=lambda e: -len(e[2]))[:14]

    # Compact label for each edge: use the shortest contributing sensor title
    def short_label(titles):
        return min(titles, key=len) if titles else ""

    # Layout: place nodes on a circle
    import math
    n = len(FAMILIES)
    cx, cy, radius = 560, 460, 340
    node_pos = {}
    for i, f in enumerate(FAMILIES):
        angle = (2 * math.pi * i / n) - math.pi / 2
        node_pos[f["slug"]] = (cx + radius * math.cos(angle), cy + radius * math.sin(angle))

    NODE_R = 9

    def edge_geometry(p1, p2, bend=0.18):
        """Trim the line to start/end at the circle rims, return (path_d, tip, tip_angle)."""
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        norm = math.hypot(dx, dy) or 1
        ux, uy = dx / norm, dy / norm
        s = (p1[0] + ux * NODE_R, p1[1] + uy * NODE_R)
        e = (p2[0] - ux * NODE_R, p2[1] - uy * NODE_R)
        mx, my = (s[0] + e[0]) / 2, (s[1] + e[1]) / 2
        edx, edy = e[0] - s[0], e[1] - s[1]
        qx, qy = mx - edy * bend, my + edx * bend
        path_d = f"M {s[0]:.1f} {s[1]:.1f} Q {qx:.1f} {qy:.1f} {e[0]:.1f} {e[1]:.1f}"
        # Tangent at the end of a quadratic bezier: (e - q)
        tip_angle = math.atan2(e[1] - qy, e[0] - qx)
        return path_d, e, tip_angle

    def arrowhead_points(tip, angle, size=8):
        """Triangle pointing along `angle` with apex at `tip`."""
        ax, ay = tip
        perp = angle + math.pi / 2
        b1x = ax - size * math.cos(angle) + (size * 0.5) * math.cos(perp)
        b1y = ay - size * math.sin(angle) + (size * 0.5) * math.sin(perp)
        b2x = ax - size * math.cos(angle) - (size * 0.5) * math.cos(perp)
        b2y = ay - size * math.sin(angle) - (size * 0.5) * math.sin(perp)
        return f"{ax:.1f},{ay:.1f} {b1x:.1f},{b1y:.1f} {b2x:.1f},{b2y:.1f}"

    def edge_label_pos(p1, p2, bend=0.18, t=0.5):
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        qx, qy = mx - dy * bend, my + dx * bend
        x = (1 - t) ** 2 * p1[0] + 2 * (1 - t) * t * qx + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p1[1] + 2 * (1 - t) * t * qy + t ** 2 * p2[1]
        # Nudge perpendicular to the curve so the label floats off the stroke
        norm = math.hypot(dx, dy) or 1
        off = 12
        x += (-dy / norm) * off
        y += (dx / norm) * off
        return x, y

    edges_svg = ""
    labels_svg = ""
    for idx, (src, tgt, titles) in enumerate(strong_edges):
        p1, p2 = node_pos[src], node_pos[tgt]
        # Vary bend direction slightly per edge to reduce overlap
        bend = 0.18 if idx % 2 == 0 else -0.18
        path_d, tip, tip_angle = edge_geometry(p1, p2, bend)
        lx, ly = edge_label_pos(p1, p2, bend)
        why = short_label(titles)
        cls = "dep-edge"
        tip_pts = arrowhead_points(tip, tip_angle)
        edges_svg += f'          <path class="{cls}" data-src="{src}" data-tgt="{tgt}" d="{path_d}"><title>{html.escape(src)} leans on {html.escape(tgt)}</title></path>\n'
        edges_svg += f'          <polygon class="dep-arrowhead" data-src="{src}" data-tgt="{tgt}" points="{tip_pts}" />\n'
        labels_svg += f'          <text class="dep-edge-label" data-src="{src}" data-tgt="{tgt}" x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle"><title>{html.escape(", ".join(titles))}</title>{html.escape(why)}</text>\n'

    nodes_svg = ""
    for f in FAMILIES:
        x, y = node_pos[f["slug"]]
        # Push label anchor outward based on position relative to center
        anchor = "start" if x > cx + 10 else ("end" if x < cx - 10 else "middle")
        lx = x + (16 if anchor == "start" else (-16 if anchor == "end" else 0))
        ly = y + (-18 if y < cy - 10 else (28 if y > cy + 10 else 4))
        nodes_svg += f"""          <a href="/catalog/#{f['slug']}" class="dep-node" data-family="{f['slug']}">
            <circle cx="{x:.1f}" cy="{y:.1f}" r="9" class="dep-node-dot" />
            <text class="dep-node-label" x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}">{html.escape(f['name'])}</text>
          </a>
"""

    dep_graph_svg = f"""      <svg class="dep-graph" viewBox="0 0 1120 920" role="img" aria-label="Family dependency graph: how sensor families lean on each other">
        <title>Family dependency graph</title>
        <desc>Arrows point from the family that leans to the family it leans on. {len(edge_sensors)} edges shown. See the text list below the graph for the full edge set.</desc>
{edges_svg.rstrip()}
{labels_svg.rstrip()}
{nodes_svg.rstrip()}
      </svg>"""

    # Text equivalent of the dependency graph for screen readers
    edge_list = ""
    for (src, tgt), sensor_titles in sorted(edge_sensors.items()):
        src_name = FAMILY_BY_SLUG.get(src, {}).get("name", src)
        tgt_name = FAMILY_BY_SLUG.get(tgt, {}).get("name", tgt)
        edge_list += f'        <li>{html.escape(src_name)} leans on {html.escape(tgt_name)} via: {html.escape(", ".join(sorted(sensor_titles)))}</li>\n'
    edge_list_html = f"""      <details class="sr-only">
        <summary>Family dependency graph (text)</summary>
        <ul>
{edge_list.rstrip()}
        </ul>
      </details>"""

    # Family map
    family_map = ""
    for f in FAMILIES:
        family_map += f"""        <a href="/catalog/#{f['slug']}" class="family-map-card">
          <span class="fam-num">{f['num']}</span>
          <span class="fam-name">{html.escape(f['name'])}</span>
          <span class="fam-q">"{html.escape(f['question'])}"</span>
        </a>
"""

    body = f"""  <div class="atlas-container">
    <section class="page-header">
      <p class="eyebrow">The Atlas</p>
      <h1 class="page-title">Sensor Atlas</h1>
      <p class="page-lede">
        A navigational map of the sensor landscape. Each row is a
        <a href="/catalog/" class="wikilink">sensor family</a> — a question
        you're asking about the system. Each column is a stage of the software
        lifecycle — <em>when</em> the signal becomes available, from authoring
        the code on the left to observing real-world outcomes on the right.
        For the narrative version of how evidence accumulates, see the
        <a href="/#confidence-stack" class="wikilink">confidence stack</a>.
      </p>
    </section>

    <div class="atlas-intro">
      <p style="color:var(--text-soft);max-width:44rem;line-height:1.7;">
        Use the atlas to orient yourself. <em>What question are you
        asking?</em> Find the row. <em>When can you afford to learn the
        answer?</em> Find the column. Empty cells are questions nobody
        instrumented at that stage yet.
      </p>
    </div>

    <!-- Grid -->
    <div class="atlas-matrix-wrapper">
      <div class="atlas-matrix">
        <div class="matrix-header-row">
          <div class="matrix-corner"></div>
{col_headers.rstrip()}
        </div>
{matrix_rows.rstrip()}
      </div>
    </div>

    <!-- Axis labels -->
    <div class="atlas-axes">
      <div class="axis-label-h">← What question are you asking? (sensor families)</div>
      <div class="axis-label-v">← earlier / cheaper &nbsp;&nbsp;|&nbsp;&nbsp; later / closer to reality → <br>Lifecycle stages</div>
    </div>

    <!-- Family map -->
    <div class="family-map-section">
      <h2 class="section-heading">{len(FAMILIES)} families at a glance</h2>
      <div class="family-map-grid">
{family_map.rstrip()}
      </div>
    </div>

    <!-- Dependency graph -->
    <div class="dep-map-section">
      <h2 class="section-heading">How the families lean on each other</h2>
      <p class="dep-map-lede">
        Sensor families are not a stack — evidence from one family routinely
        depends on another family having done its job. Arrows point from the
        family that leans to the family it leans on, labelled with a sensor
        that carries the connection. Hover a node to isolate its
        neighborhood. Drawn from the cross-references inside the catalog
        entries themselves; only the strongest links are shown.
      </p>
      <div class="dep-graph-wrapper">
{dep_graph_svg}
      </div>
{edge_list_html}
    </div>
  </div>"""

    page_html = html_page("Sensor Atlas", body, canonical="atlas/")
    out_path = output_dir / "atlas" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)


def generate_index_page(sensors, output_dir):
    """Generate the homepage."""

    # Featured sensor
    featured = next((s for s in sensors if s["id"] == "SO-003"), sensors[0] if sensors else None)
    featured_family = FAMILY_BY_SLUG.get(featured.get("family", ""), {}) if featured else {}

    # Families grid
    families_grid = ""
    for f in FAMILIES:
        families_grid += f"""        <a href="/catalog/#{f['slug']}" class="family-card">
          <span class="family-num">{f['num']}</span>
          <h3 class="family-name">{html.escape(f['name'])}</h3>
          <p class="family-question">"{html.escape(f['question'])}"</p>
          <p class="family-examples">{html.escape(f['examples'])}</p>
        </a>
"""

    # Featured entries — one per family for the first six families, so the
    # selection is deterministic and spread across the catalog rather than
    # masquerading as "recently reviewed" when all review dates are identical.
    featured_slugs = [
        "type-checker", "mutation-testing", "fuzzing",
        "observability-events", "independent-review", "canary-analysis",
    ]
    sensors_by_slug = {s["slug"]: s for s in sensors}
    recent_sensors = [sensors_by_slug[s] for s in featured_slugs if s in sensors_by_slug]
    recent_html = ""
    for s in recent_sensors:
        fam = FAMILY_BY_SLUG.get(s.get("family", ""), {})
        recent_html += f"""        <li class="entry">
          <span class="entry-family">{html.escape(fam.get('name', ''))}</span>
          <a href="/sensors/{s['slug']}/" class="entry-title wikilink">{html.escape(s['title'])}</a>
          <span class="entry-blurb">{html.escape(blurb_text(s.get('body_html', ''), 140))}</span>
        </li>
"""

    # Confidence scatter: feedback latency (x) against signal efficacy (y).
    # Two datasets — stack layers (hand-positioned) and individual sensors
    # (positioned from latency/oracle frontmatter, jittered to declutter).
    def scatter_layer_points():
        pts = ""
        for layer in STACK_LAYERS:
            pos = STACK_SCATTER.get(layer["slug"])
            if not pos:
                continue
            pts += f"""          <a href="/atlas/" class="scatter-point layer-point" style="left:{pos['x']}%;bottom:{pos['y']}%" data-label="{html.escape(layer['label'])}">
            <span class="scatter-dot"></span>
            <span class="scatter-tag">{html.escape(layer['label'])}</span>
          </a>
"""
        return pts.rstrip()

    def scatter_sensor_points():
        # Group by cell so overlapping sensors fan out deterministically
        cells = {}
        for s in sensors:
            x = LATENCY_X.get(s.get("latency", ""), 50)
            y = ORACLE_Y.get(s.get("oracle", ""), 50)
            cells.setdefault((x, y), []).append(s)
        pts = ""
        for (x, y), members in cells.items():
            n = len(members)
            for i, s in enumerate(members):
                # deterministic fan: hash the slug for a stable pseudo-random
                # offset within a disc that grows with cell population
                import math
                h = int(hashlib.md5(s["slug"].encode()).hexdigest(), 16)
                ang = (h % 360) * math.pi / 180
                rad = 2.2 * math.sqrt(i / max(n - 1, 1)) if n > 1 else 0
                spread = min(7, 1.5 + n * 0.55) if n > 1 else 0
                dx = math.cos(ang) * spread * rad / 2.2
                dy = math.sin(ang) * spread * rad / 2.2
                fam = FAMILY_BY_SLUG.get(s.get("family", ""), {}).get("name", "")
                fam_slug = s.get("family", "")
                fam_icon = FAMILY_BY_SLUG.get(fam_slug, {}).get("icon", "")
                pts += f"""          <a href="/sensors/{s['slug']}/" class="scatter-point sensor-point fam-{html.escape(fam_slug)}" style="left:{x + dx:.1f}%;bottom:{y + dy:.1f}%" data-label="{html.escape(s['title'])}" data-family="{html.escape(fam)}">
            <span class="scatter-dot" aria-hidden="true">{fam_icon}</span>
            <span class="scatter-tag">{html.escape(s['title'])}</span>
          </a>
"""
        return pts.rstrip()

    def scatter_legend():
        keys = ""
        for f in FAMILIES:
            keys += f"""          <span class="legend-key"><span class="legend-dot fam-{f['slug']}" aria-hidden="true">{f['icon']}</span>{html.escape(f['name'])}</span>
"""
        return keys.rstrip()

    scatter_html = f"""      <div class="scatter-toggle" role="group" aria-label="Scatter data">
        <button type="button" class="scatter-toggle-btn active" data-scatter="layers">Layers</button>
        <button type="button" class="scatter-toggle-btn" data-scatter="sensors">Sensors</button>
      </div>
      <div class="scatter-frame" data-scatter-mode="layers">
        <div class="scatter-y-label">efficacy of the signal</div>
        <div class="scatter-body">
          <div class="scatter-y-ticks">
            <span>definitive</span>
            <span>suggestive</span>
          </div>
          <div class="scatter-plot">
{scatter_layer_points()}
{scatter_sensor_points()}
          </div>
        </div>
        <div class="scatter-x-axis">
          <span>instant</span>
          <span>feedback latency →</span>
          <span>slow</span>
        </div>
        <p class="scatter-hint">Hover a point to name it. Click to open the entry.</p>
        <div class="scatter-legend">
{scatter_legend()}
        </div>
      </div>
      <details class="sr-only">
        <summary>Sensor list (latency × efficacy)</summary>
        <table>
          <thead><tr><th>Sensor</th><th>Family</th><th>Feedback latency</th><th>Efficacy (oracle)</th></tr></thead>
          <tbody>
{"".join(f'          <tr><td><a href="/sensors/{s["slug"]}/">{html.escape(s["title"])}</a></td><td>{html.escape(FAMILY_BY_SLUG.get(s.get("family",""),{}).get("name",""))}</td><td>{html.escape(s.get("latency",""))}</td><td>{html.escape(s.get("oracle",""))}</td></tr>\n' for s in sensors)}
          </tbody>
        </table>
      </details>"""

    body = f"""  <main>
    <section class="hero">
      <div class="hero-inner">
        <p class="eyebrow">An industry resource</p>
        <h1 class="hero-title">
          What independent observations<br>
          <em>would cause us to believe</em><br>
          this software is correct?
        </h1>
        <p class="hero-lede">
          Software is increasingly an opaque artifact. We cannot — and often
          do not want to — fully understand every implementation. The Software
          Observatory is a catalog of <a href="/catalog/" class="wikilink">epistemic sensors</a>:
          the observable signals that reduce uncertainty about whether a system
          is correct, maintainable, and behaving as intended. Not "code quality
          metrics." Measurement instruments pointed at different failure modes.
        </p>
        <div class="hero-actions">
          <a href="/catalog/" class="btn btn-primary">Browse the catalog →</a>
          <a href="/atlas/" class="btn btn-ghost">Open the atlas</a>
        </div>
      </div>
      <div class="hero-visual" aria-hidden="true">
        <svg viewBox="0 0 400 400" class="hero-instruments">
          <!-- the opaque artifact -->
          <circle cx="200" cy="200" r="52" class="art-body" />
          <circle cx="200" cy="200" r="52" class="art-rim" />
          <!-- instruments: sight-lines at different depths -->
          <!-- near, penetrating (static analysis) -->
          <line x1="90" y1="90" x2="176" y2="176" class="sight deep" />
          <circle cx="90" cy="90" r="5" class="instr" />
          <!-- near, penetrating (types) -->
          <line x1="310" y1="80" x2="230" y2="172" class="sight deep" />
          <circle cx="310" cy="80" r="5" class="instr" />
          <!-- mid, surface (tests) -->
          <line x1="330" y1="230" x2="252" y2="212" class="sight mid" />
          <circle cx="330" cy="230" r="5" class="instr" />
          <!-- mid, surface (behavioral) -->
          <line x1="70" y1="250" x2="148" y2="222" class="sight mid" />
          <circle cx="70" cy="250" r="5" class="instr" />
          <!-- far, glancing (production) -->
          <line x1="250" y1="355" x2="222" y2="252" class="sight far" />
          <circle cx="250" cy="355" r="5" class="instr far-instr" />
          <!-- very far, glancing (user outcome) -->
          <line x1="60" y1="40" x2="120" y2="120" class="sight farthest" stroke-dasharray="3 5" />
          <circle cx="60" cy="40" r="4" class="instr far-instr" />
          <line x1="360" y1="330" x2="290" y2="285" class="sight farthest" stroke-dasharray="3 5" />
          <circle cx="360" cy="330" r="4" class="instr far-instr" />
        </svg>
      </div>
    </section>

    <section class="core-insight">
      <blockquote class="big-quote">
        <p>
          <a href="/glossary/#no-single-sensor" class="wikilink">No single sensor measures correctness</a>. Coverage measures execution.
          <a href="/sensors/mutation-testing/" class="wikilink">Mutation testing</a> measures
          test sensitivity. <a href="/sensors/type-checker/" class="wikilink">Types</a> measure
          a particular class of structural inconsistency.
          <a href="/sensors/contract-tests/" class="wikilink">Contracts</a> measure boundary
          assumptions. <a href="/sensors/observability-events/" class="wikilink">Observability</a>
          measures what actually happened and preserves enough dimensionality
          to investigate unknown unknowns.
        </p>
        <p>They are all measurement instruments pointed at different failure modes.</p>
      </blockquote>
    </section>

    <section class="families-section">
      <h2 class="section-heading">{len(FAMILIES)} sensor families</h2>
      <p class="section-lede">
        The catalog is organized into {len(FAMILIES)} families, each asking a different
        question about the system. Together, they form a mesh of independent
        evidence — no single sensor is sufficient, but the combination
        constrains uncertainty from multiple directions.
      </p>
      <div class="families-grid">
{families_grid.rstrip()}
      </div>
    </section>

    <section class="stack-preview" id="confidence-stack">
      <h2 class="section-heading">The confidence landscape</h2>
      <p class="section-lede">
        No single sensor is sufficient, so there is no total ordering across
        sensors — no "best" sensor. But each <em>dimension</em> (oracle
        strength, latency, scope) is a partial order, and the atlas's
        left-to-right axis is <em>time</em>, not quality. Each one trades
        <em>feedback latency</em> — how long you wait for the signal —
        against <em>efficacy</em>: how much the signal can actually tell
        you. Compilation is instant and definitive about validity; user
        outcomes are slow and definitive about everything that matters. Most
        sensors live somewhere in between.
      </p>
{scatter_html}
      <div class="stack-cta">
        <a href="/atlas/" class="btn btn-ghost">Open the atlas →</a>
      </div>
    </section>

    <section class="featured-signal">
      <div class="featured-meta">
        <span class="tag tag-family">{html.escape(featured_family.get('name', ''))}</span>
        <span class="tag tag-confidence">High oracle strength</span>
      </div>
      <h2 class="featured-title"><a href="/sensors/{featured['slug']}/" class="wikilink" style="border-bottom:none">{html.escape(featured['title'])}</a></h2>
      <p class="featured-blurb">
        Take <code>if user.is_admin: allow()</code> and mutate it to
        <code>if not user.is_admin: allow()</code>. If all your tests still
        pass, your tests did not actually establish the behavior you thought
        you established. Mutation testing is a sensor of test
        <em>sensitivity</em> rather than test <em>presence</em>.
      </p>
      <div class="featured-cta">
        <a href="/sensors/{featured['slug']}/">Read the full entry →</a>
      </div>
    </section>

    <section class="recent">
      <h2 class="section-heading">Start here</h2>
      <ul class="entry-list">
{recent_html.rstrip()}
      </ul>
    </section>
  </main>"""

    import json as _json
    website_ld = _json.dumps({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "Software Observatory",
        "url": SITE_URL,
        "description": "A catalog of epistemic sensors for software correctness.",
        "author": {
            "@type": "Person",
            "name": "Justin Abrahms",
            "url": "https://justin.abrah.ms",
            "email": "mailto:justin@abrah.ms",
            "sameAs": [
                "https://github.com/justinabrahms",
                "https://bsky.app/profile/justin.abrah.ms",
                "https://www.linkedin.com/in/justinabrahms",
            ],
        },
    }, indent=2)

    page_html = html_page("Software Observatory", body, canonical="", json_ld=website_ld)
    out_path = output_dir / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)


def generate_framework_page(sensors, output_dir):
    """Generate the framework page."""

    body = f"""  <section class="page-header">
    <p class="eyebrow">The Framework</p>
    <h1 class="page-title">Sensor Properties</h1>
    <p class="page-lede">
      We don't rank sensors as "good" or "bad." Every sensor is characterized
      along six dimensions that determine when it is useful, what it can and
      cannot detect, and what evidence it produces for an agent or human.
    </p>
  </section>

  <div class="framework-content">
    <div class="framework-intro">
      <p>
        The important thing is that <a href="/glossary/#no-single-sensor" class="wikilink">no single sensor measures
        <em>correctness</em></a>. Each sensor measures one thing. Coverage
        measures execution. Mutation measures test sensitivity. Types measure
        a particular class of structural inconsistency. Contracts measure
        boundary assumptions. Observability measures what actually happened
        and preserves enough dimensionality to investigate unknown unknowns.
      </p>
      <p>
        The question becomes: <em>what independent observations would cause us
        to update our belief that this software is correct?</em>
      </p>
    </div>

    <section class="property-detail">
      <span class="property-detail-num">01</span>
      <h2 class="property-detail-title">Oracle strength</h2>
      <p class="property-detail-question">How confidently does it know that something is wrong?</p>
      <div class="property-bars">
        <div class="bar-row"><span class="bar-label">compiler error</span><div class="bar-track"><div class="bar-fill" style="width:100%"></div></div><span class="bar-pct">maximum</span></div>
        <div class="bar-row"><span class="bar-label">type error</span><div class="bar-track"><div class="bar-fill" style="width:100%"></div></div><span class="bar-pct">maximum</span></div>
        <div class="bar-row"><span class="bar-label">test assertion</span><div class="bar-track"><div class="bar-fill" style="width:90%"></div></div><span class="bar-pct">high</span></div>
        <div class="bar-row"><span class="bar-label">mutation</span><div class="bar-track"><div class="bar-fill" style="width:90%"></div></div><span class="bar-pct">high</span></div>
        <div class="bar-row"><span class="bar-label">linter</span><div class="bar-track"><div class="bar-fill" style="width:80%"></div></div><span class="bar-pct">medium</span></div>
        <div class="bar-row"><span class="bar-label">coverage</span><div class="bar-track"><div class="bar-fill" style="width:40%"></div></div><span class="bar-pct">low</span></div>
        <div class="bar-row"><span class="bar-label">complexity</span><div class="bar-track"><div class="bar-fill" style="width:20%"></div></div><span class="bar-pct">minimum</span></div>
        <div class="bar-row"><span class="bar-label">code review</span><div class="bar-track"><div class="bar-fill" style="width:60%"></div></div><span class="bar-pct">medium</span></div>
      </div>
      <p>
        A compiler has maximum oracle strength because the implementation
        cannot argue with it. A complexity metric has minimum oracle
        strength because high complexity doesn't prove anything is wrong —
        it just suggests increased risk. The scale is ordinal (minimum →
        low → medium → high → maximum): a sensor two rungs up is stronger,
        not "twice as strong."
      </p>
      <div class="callout">
        <strong>Mutation's oracle is derivative.</strong> Mutation testing's
        high oracle is bounded by the test assertions underneath it — it
        only detects mutations that the test suite's oracle would catch.
        The strength reflects the test assertion's oracle, applied to a
        perturbation.
      </div>
      <div class="callout">
        <strong>"Type checker" spans a range.</strong> Structural type systems
        (TypeScript) catch a limited class of mismatches. Ownership and
        lifetime types (Rust) catch memory-safety bugs the compiler refuses
        to allow. Refinement types and SMT-backed verifiers (Dafny) can prove
        full correctness properties — the solver either confirms the
        invariant or produces a counterexample. The maximum rating applies
        to the strong end of that spectrum.
      </div>
    </section>

    <section class="property-detail">
      <span class="property-detail-num">02</span>
      <h2 class="property-detail-title">Independence</h2>
      <p class="property-detail-question">Can the thing being evaluated manipulate the sensor?</p>
      <p>
        This is extremely important for agents. A model writing
        <code>tests/</code> is allowed to write tests that make itself pass.
        The producer and evaluator should be separated wherever possible.
      </p>
      <div class="callout">
        An instruction saying "verify this" is weaker than a gate that
        literally refuses to proceed unless the verification command
        succeeded. Computational controls rather than prose rules.
      </div>
    </section>

    <section class="property-detail">
      <span class="property-detail-num">03</span>
      <h2 class="property-detail-title">Scope</h2>
      <p class="property-detail-question">What level of the system does it tell us about?</p>
      <div class="scope-ladder">
        <div class="scope-rung">Line <span class="scope-desc">A single line of code</span></div>
        <div class="scope-rung">Function <span class="scope-desc">A single function or method</span></div>
        <div class="scope-rung">Module <span class="scope-desc">A package or module</span></div>
        <div class="scope-rung">Service <span class="scope-desc">A single service or component</span></div>
        <div class="scope-rung">System <span class="scope-desc">The whole system, across services</span></div>
        <div class="scope-rung">User journey <span class="scope-desc">What the user experiences end-to-end</span></div>
      </div>
    </section>

    <section class="property-detail">
      <span class="property-detail-num">04</span>
      <h2 class="property-detail-title">Feedback latency</h2>
      <p class="property-detail-question">How long until the sensor tells you something?</p>
      <div class="latency-table">
        <div class="lat-row"><span class="lat-sensor">compiler</span><span class="lat-time">milliseconds</span><div class="lat-bar"><div class="lat-fill" style="width:5%"></div></div></div>
        <div class="lat-row"><span class="lat-sensor">unit tests</span><span class="lat-time">seconds</span><div class="lat-bar"><div class="lat-fill" style="width:12%"></div></div></div>
        <div class="lat-row"><span class="lat-sensor">integration</span><span class="lat-time">minutes</span><div class="lat-bar"><div class="lat-fill" style="width:30%"></div></div></div>
        <div class="lat-row"><span class="lat-sensor">mutation</span><span class="lat-time">minutes / hours</span><div class="lat-bar"><div class="lat-fill" style="width:50%"></div></div></div>
        <div class="lat-row"><span class="lat-sensor">canary</span><span class="lat-time">minutes</span><div class="lat-bar"><div class="lat-fill" style="width:35%"></div></div></div>
        <div class="lat-row"><span class="lat-sensor">production</span><span class="lat-time">hours / days</span><div class="lat-bar"><div class="lat-fill" style="width:70%"></div></div></div>
        <div class="lat-row"><span class="lat-sensor">incident</span><span class="lat-time">weeks</span><div class="lat-bar"><div class="lat-fill" style="width:100%"></div></div></div>
      </div>
    </section>

    <section class="property-detail">
      <span class="property-detail-num">05</span>
      <h2 class="property-detail-title">Actionability</h2>
      <p class="property-detail-question">Does it merely say "bad" or does it tell you what to fix?</p>
      <p>
        Three values, in order of how much the feedback directs the next action:
      </p>
      <div class="scope-ladder">
        <div class="scope-rung">Blocking <span class="scope-desc">A binary gate: pass or fail. The pipeline stops on failure, but the sensor does not say what to fix — a compiler error, a failing invariant gate, a smoke test that halts a rollout.</span></div>
        <div class="scope-rung">Exploratory <span class="scope-desc">A signal to investigate, not a verdict. It narrows where to look but prescribes nothing — a hotspot, a trace, a coverage gap on unchanged lines.</span></div>
        <div class="scope-rung">Guiding <span class="scope-desc">The feedback itself directs the next action. A mutation report shows the exact untested mutation; a linter diagnostic names the rule and the fix; a type error points at the expression and the expected type.</span></div>
      </div>
      <p>
        In Böckeler's framing, the interesting frontier is guiding sensors,
        where the feedback itself tells the agent what to do next.
      </p>
    </section>

    <section class="property-detail">
      <span class="property-detail-num">06</span>
      <h2 class="property-detail-title">Predictive vs retrospective</h2>
      <p class="property-detail-question">"This is wrong" or "this looks like things that became wrong before"?</p>
      <p>
        Predictive sensors fire before the code ships — a compiler error, a
        failed test, a mutation that survives. Retrospective sensors fire
        after — they tell you that past changes look like changes that
        caused trouble before: revert rate, incident correlation, escaped
        defect rate.
      </p>
      <p>
        This dimension is <em>when</em> the signal arrives, not <em>what
        kind</em> of feedback it gives. That is a separate axis —
        <a href="#actionability">actionability</a>: blocking, exploratory,
        guiding. The two are correlated but not the same: most predictive
        sensors gate (a compiler error blocks the build), and most
        retrospective sensors warn (revert rate is a signal, not a gate).
        But the correlation is not a rule. <em>Build provenance &amp;
        SBOM</em> is retrospective — it fires after the build — and
        <em>blocking</em>: an unattested artifact does not ship. A
        retrospective sensor can gate; a predictive sensor can merely warn.
        Read the two dimensions independently.
      </p>
      <p>
        You don't need to understand <code>FooManagerFactoryImpl</code>. You
        can observe: <em>27 changes in six months, 8 reverts, 4 incidents,
        touched by 11 teams.</em> That's a retrospective signal — a black-box
        sensor of maintainability.
      </p>
      <p>
        The catalog splits roughly evenly: predictive sensors catch bugs
        before they ship; retrospective sensors tell you where the bugs came
        from. Both matter — a sensor stack with only predictive sensors has
        no feedback loop; one with only retrospective sensors has no gate.
      </p>
    </section>
  </div>"""

    page_html = html_page("Framework", body, canonical="framework/")
    out_path = output_dir / "framework" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)


def generate_about_page(output_dir):
    """Generate the about page."""

    body = f"""  <section class="page-header">
    <p class="eyebrow">About</p>
    <h1 class="page-title">About the Observatory</h1>
    <p class="page-lede">
      An open reference for the signals software emits — not "code quality
      metrics," but epistemic sensors: measurement instruments pointed at
      different failure modes.
    </p>
  </section>

  <div class="about-content">
    <h2>The problem</h2>
    <p>
      Software is increasingly an <a href="/glossary/#opaque-artifact" class="wikilink">opaque
      artifact</a>. We cannot — and increasingly do not want to — fully
      understand every implementation. Code is produced by agents, by teams
      we'll never meet, by systems that span services we don't own. The
      question is no longer "is this code good?" The question is:
      <em>what independent observations would cause us to update our belief
      that this software is correct?</em>
    </p>

    <h2>Epistemic sensors, not quality metrics</h2>
    <p>
      We would not call these "quality metrics." We'd call them
      <a href="/catalog/" class="wikilink">epistemic sensors</a>. Their
      job is to reduce uncertainty about a system that we cannot — or
      increasingly do not want to — fully understand.
    </p>

    <h2>The framework</h2>
    <p>
      The catalog is organized into <a href="/catalog/" class="wikilink">{len(FAMILIES)}
      families</a> of sensors, each asking a different question about the
      system. Every sensor is characterized along
      <a href="/framework/" class="wikilink">six dimensions</a>:
      oracle strength, independence, scope, feedback latency,
      actionability, and predictive vs retrospective. The
      <a href="/atlas/" class="wikilink">atlas</a> arranges them as a
      navigational matrix — families on one axis, confidence stack layers
      on the other.
    </p>

    <h2>Inspirations</h2>
    <p>
      <strong>Birgitta Böckeler's "guides &amp; sensors" framing.</strong>
      Sensors are tools that give an agent feedback about what it has done.
      The interesting frontier is guiding sensors, where the feedback itself
      tells the agent what to do next.
    </p>
    <p>
      <strong>Honeycomb's conception of observability.</strong>
      Don't merely collect predetermined health metrics; preserve enough
      information to ask questions you didn't know you would need to ask.
    </p>

    <h2>Maintained by</h2>
    <p>
      The Software Observatory is built and maintained by
      <a href="https://justin.abrah.ms/" class="wikilink">Justin Abrahms</a>
      — a principal engineer working on agent-assisted software delivery and
      the sensors that let us assess what agents produce. The catalog grows
      out of that work: if agents can produce software faster than humans can
      inspect it, code review cannot remain the primary mechanism for
      establishing quality, and we need a living catalog of the signals we
      can use instead.
    </p>
    <p>
      Reach out via <a href="mailto:justin@abrah.ms" class="wikilink">email</a>,
      <a href="https://bsky.app/profile/justin.abrah.ms" class="wikilink">Bluesky</a>,
      or <a href="https://github.com/justinabrahms" class="wikilink">GitHub</a>.
      Errors and gaps in the catalog are best filed in the
      <a href="https://github.com/justinabrahms/software-observatory/issues"
      class="wikilink">issue tracker</a>.
    </p>

    <h2>Contributing</h2>
    <p>
      The Observatory is meant to be an open reference, and the field should
      be able to correct it. The catalog applies a producer-evaluator
      principle to itself: the author shouldn't be the only evaluator.
      Independent review of the content is welcome and explicitly invited.
    </p>
    <p>
      The best way to contribute right now:
    </p>
    <ul>
      <li>
        <strong>File an issue</strong> at the
        <a href="https://github.com/justinabrahms/software-observatory/issues"
        class="wikilink">GitHub tracker</a> for a factual error, a missing
        sensor, a taxonomy challenge, or a depth gap.
      </li>
      <li>
        <strong>Open a pull request</strong> with a new or revised
        <code>content/sensors/*.md</code>. Keep the opening paragraph
        self-contained; match the frontmatter shape in
        <a href="https://github.com/justinabrahms/software-observatory/blob/main/CONTRIBUTING.md"
        class="wikilink">CONTRIBUTING.md</a>; run the build and the link
        checker before submitting.
      </li>
      <li>
        <strong>Propose a family change</strong> (adding, renumbering, or
        reclassifying a family) via an issue first — these touch
        <code>FAMILIES</code> in <code>build.py</code> and the color tokens
        in <code>css/observatory.css</code>, so they're worth discussing
        before the work.
      </li>
    </ul>
    <p>
      See
      <a href="https://github.com/justinabrahms/software-observatory/blob/main/CONTRIBUTING.md"
      class="wikilink">CONTRIBUTING.md</a>
      in the repository for the full guide — frontmatter shape, the
      relative-link gotcha, build and link-check commands, and style
      conventions.
    </p>

    <h2>License</h2>
    <p>
      All content on the Software Observatory is published under
      <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" class="wikilink">CC BY-NC-SA 4.0</a>.
      You are free to share and adapt the material for non-commercial purposes,
      provided you give appropriate credit and distribute contributions under
      the same license.
    </p>
  </div>"""

    page_html = html_page("About", body, canonical="about/")
    out_path = output_dir / "about" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)


def generate_contact_page(output_dir):
    """Generate the contact page."""
    body = """  <section class="page-header">
    <p class="eyebrow">Contact</p>
    <h1 class="page-title">Contact</h1>
    <p class="page-lede">
      The Software Observatory is maintained by Justin Abrahms. The best
      way to reach out depends on what you need.
    </p>
  </section>

  <div class="about-content">
    <h2>Errors and gaps in the catalog</h2>
    <p>
      If you've found a factual error, a missing sensor, a taxonomy challenge,
      or a depth gap, the best path is the
      <a href="https://github.com/justinabrahms/software-observatory/issues"
      class="wikilink">GitHub issue tracker</a>. That keeps the discussion
      public and linkable, and it's where the work gets tracked.
    </p>

    <h2>Contributions</h2>
    <p>
      Pull requests are welcome — see
      <a href="https://github.com/justinabrahms/software-observatory/blob/main/CONTRIBUTING.md"
      class="wikilink">CONTRIBUTING.md</a> for the frontmatter shape, the
      relative-link gotcha, and the build and link-check commands.
    </p>

    <h2>Direct contact</h2>
    <p>
      For anything that doesn't fit an issue or a PR:
    </p>
    <ul>
      <li><a href="mailto:justin@abrah.ms" class="wikilink">justin@abrah.ms</a> — email</li>
      <li><a href="https://bsky.app/profile/justin.abrah.ms" class="wikilink">@justin.abrah.ms on Bluesky</a></li>
      <li><a href="https://github.com/justinabrahms" class="wikilink">github.com/justinabrahms</a></li>
    </ul>
    <p>
      The Observatory is a personal project; response times may vary.
    </p>
  </div>"""

    page_html = html_page("Contact", body, canonical="contact/")
    out_path = output_dir / "contact" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)


def generate_privacy_page(output_dir):
    """Generate the privacy page."""
    body = """  <section class="page-header">
    <p class="eyebrow">Privacy</p>
    <h1 class="page-title">Privacy</h1>
    <p class="page-lede">
      The Software Observatory is a static website. It collects no personal
      data and uses privacy-respecting, cookieless analytics.
    </p>
  </section>

  <div class="about-content">
    <h2>What we collect</h2>
    <p>
      Aggregate visit statistics only. The site uses
      <a href="https://www.goatcounter.com" class="wikilink">GoatCounter</a>,
      a self-hosted, open-source analytics tool running on the same server
      as the site (stats.softwareobservatory.com). It records page views,
      referrers, country, browser, and screen size. It sets no cookies,
      stores no IP addresses, and cannot track you across sites or across
      visits. There are no forms and no backend database behind the site
      itself. The server logs standard request metadata (IP address, request
      path, timestamp) for operational purposes — diagnosing abuse and
      misconfiguration — but these logs are not shared, sold, or used to
      build profiles of visitors.
    </p>

    <h2>Third-party resources</h2>
    <p>
      The site loads fonts from
      <a href="https://fonts.google.com" class="wikilink">Google Fonts</a>.
      Google may collect request metadata (IP address, referer) when your
      browser fetches the stylesheet. This is governed by
      <a href="https://policies.google.com/privacy" class="wikilink">Google's
      privacy policy</a>, not this one.
    </p>

    <h2>GitHub</h2>
    <p>
      The source code lives on
      <a href="https://github.com/justinabrahms/software-observatory"
      class="wikilink">GitHub</a>. If you file an issue or open a pull
      request, GitHub processes your contribution under its own terms.
    </p>

    <h2>Changes</h2>
    <p>
      If the site ever adds comments or any other data-collecting feature,
      this page will be updated to describe it before the feature ships.
    </p>

    <h2>Contact</h2>
    <p>
      Questions about this policy: <a href="mailto:justin@abrah.ms"
      class="wikilink">justin@abrah.ms</a>.
    </p>
  </div>"""

    page_html = html_page("Privacy", body, canonical="privacy/")
    out_path = output_dir / "privacy" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)


# ── Main ────────────────────────────────────────────────────────────────────

def generate_glossary_page(output_dir):
    """Generate the glossary page: definitions of the core vocabulary used
    across the site, cross-linked to the framework and catalog."""

    entries = [
        ("epistemic-sensor",
         "Epistemic sensor",
         "A measurement instrument pointed at a failure mode. The term is "
         "deliberately not \"quality metric\": a metric aggregates or scores, "
         "while a sensor reduces uncertainty about a specific property of the "
         "system. A compiler is a sensor of structural validity; mutation "
         "testing is a sensor of test sensitivity; observability events are "
         "sensors of what actually happened. Each sensor measures one thing — "
         '<a href="/glossary/#no-single-sensor" class="wikilink">no single sensor measures correctness</a>. The catalog is organized into '
         f'<a href="/catalog/" class="wikilink">{len(FAMILIES)} families</a> of '
         "epistemic sensor, each asking a different question about the system."),
        ("opaque-artifact",
         "Opaque artifact",
         "Software we cannot — or do not want to — fully understand by "
         "reading. Code is increasingly produced by agents, by teams we'll "
         "never meet, and by systems that span services we don't own. The "
         "question for an opaque artifact is not \"is this code good?\" but "
         '"<em>what independent observations would cause us to update our '
         'belief that this software is correct?</em>\" The Observatory is a '
         "catalog of those observations."),
        ("oracle",
         "Oracle",
         "An oracle is the thing that tells you whether a given behavior is "
         "correct. A compiler error is a perfect oracle of structural validity "
         "— the implementation cannot argue with it. A test assertion is a "
         "strong oracle for the specific case it checks. A complexity metric "
         "is a weak oracle — high complexity doesn't prove anything is wrong. "
         '<a href="/framework/" class="wikilink">Oracle strength</a> is one '
         "of the six dimensions every sensor is characterized along."),
        ("oracle-strength",
         "Oracle strength",
         "How confidently a sensor knows that something is wrong. The scale "
         "runs from maximum (a compiler error — the code cannot argue) to low "
         "(a complexity metric — it suggests risk but proves nothing). See the "
         '<a href="/framework/" class="wikilink">framework page</a> for the '
         "full ranking."),
        ("independence",
         "Independence",
         "Whether the thing being evaluated can manipulate the sensor. A model "
         "writing <code>tests/</code> is allowed to write tests that make itself "
         "pass — that's low independence. A compiler is maximum independence — "
          "the code cannot talk its way past a type error. Independence is "
          "especially important for AI-generated code: the producer and the "
          "evaluator should be separated wherever possible. See "
          '<a href="/framework/" class="wikilink">the framework</a> and '
          '<a href="/sensors/second-agent-review/" class="wikilink">'
          "second-agent review</a>."),
        ("scope",
         "Scope",
         "What level of the system the sensor tells you about: a single line, "
         "a function, a module, a service, the whole system, or a user journey. "
         "A type checker has function-level scope; observability events have "
         'system-level scope. See <a href="/framework/" class="wikilink">'
         "the framework</a>."),
        ("feedback-latency",
         "Feedback latency",
         "How long until the sensor tells you something. A compiler reports in "
         "milliseconds; an escaped-defect-rate sensor reports in months. "
         "Latency determines where in the lifecycle a sensor is useful — you "
         "can't gate a merge on a signal that takes weeks. See "
         '<a href="/framework/" class="wikilink">the framework</a>.'),
        ("actionability",
         "Actionability",
         "Whether a sensor merely flags a problem or tells you what to fix. "
         "Three values: <strong>blocking</strong> — a binary gate that halts "
         "the pipeline (compiler error, invariant gate); "
         "<strong>exploratory</strong> — a signal to investigate that narrows "
         "where to look but prescribes nothing (hotspot, trace, coverage gap); "
         "<strong>guiding</strong> — the feedback itself directs the next "
         "action (mutation report shows the untested mutation, linter names "
         'the rule and fix). See <a href="/framework/" class="wikilink">'
         "the framework</a>."),
        ("evidence-tier",
         "Evidence label",
         "A label assigned to each publication reference, describing the "
         "<em>study</em> rather than the claim: <strong>controlled "
         "study</strong> (controlled experiment or large-N study with a "
         "comparison group), <strong>observational study</strong> "
         "(observational study on production data, no control group), "
         "<strong>case study</strong> (single-organization case study or "
         "engineering report with numbers), <strong>argument</strong> "
         "(experience report — not measured, but rendered visibly as "
         "unmeasured). The label tells you what kind of evidence backs "
         "the claim, so you can weigh it accordingly."),
        ("guiding-sensor",
         "Guiding sensor",
         "A sensor whose feedback directs the next action, not just whether "
         "something is wrong. A mutation testing report shows the exact "
         "untested mutation — the agent knows what to write a test for. A "
         "complexity score just says \"this is complex\" and leaves the agent "
         "to figure out what to do. The distinction comes from Birgitta "
         "Böckeler's \"guides &amp; sensors\" framing."),
        ("predictive-vs-retrospective",
         "Predictive vs retrospective",
         "Whether the sensor fires before the code ships (predictive — a "
         "compiler error before merge) or after (retrospective — revert "
         "rate, incident correlation). This is <em>when</em> the signal "
         "arrives, not <em>what kind</em> of feedback it gives — that is "
         "actionability. The two are correlated but not the same: a "
         "retrospective sensor can still gate (build provenance blocks an "
         "unattested artifact). See "
         '<a href="/framework/" class="wikilink">the framework</a>.'),
         ("confidence-stack",
         "Confidence stack",
         "The layers of evidence that accumulate as code moves from authoring "
         "to production: compilation, types, tests, mutation, integration, "
         "canary, production events, outcomes. No single layer is sufficient; "
         "the combination constrains uncertainty from multiple directions. "
         'The <a href="/atlas/" class="wikilink">atlas</a> arranges the '
         "stack as a navigational matrix."),
        ("metamorphic-testing",
         "Metamorphic testing",
         "A testing technique where you don't know the correct answer, but you "
         "know how the answer should change when the input changes. If "
         "<code>f(x) == f(-x)</code> for a square root, then "
         "<code>sqrt(4) == sqrt(-4)</code> must hold. You don't need an oracle; "
         "you need a relation. See "
         '<a href="/sensors/metamorphic-testing/" class="wikilink">the entry</a>.'),
         ("high-cardinality",
          "High cardinality",
          "A property of observability events: each event carries enough "
          "distinct fields (user_id, cart_id, order_id, deployment, git_sha) "
          "that you can slice the data along dimensions you didn't know you'd "
          "need. The opposite of pre-aggregated metrics, which answer only "
          "predetermined questions. See "
           '<a href="/sensors/observability-events/" class="wikilink">the entry</a>.'),
         ("no-single-sensor",
          "No single sensor measures correctness",
          "A refrain that recurs across the homepage, the framework, and "
          "this glossary — deliberately. The repetition is the point: the "
          "Observatory's central claim is that correctness is not a scalar "
          "any one sensor measures, and stating it once would understate "
          "it. Each occurrence links back here so a reader who notices the "
          "repetition can verify it is intentional."),
     ]

    sections = ""
    for slug, term, definition in entries:
        sections += f"""    <section class="glossary-entry">
      <h2 class="glossary-term" id="{slug}">{html.escape(term)}</h2>
      <p class="glossary-definition">{definition}</p>
    </section>
"""

    body = f"""  <section class="page-header">
    <p class="eyebrow">Glossary</p>
    <h1 class="page-title">Glossary</h1>
    <p class="page-lede">
      The core vocabulary the Observatory uses to talk about software
      correctness. These terms appear throughout the catalog, the atlas, and
      the framework; this page collects their definitions in one place.
    </p>
  </section>

  <div class="about-content">
{sections.rstrip()}
  </div>"""

    page_html = html_page("Glossary", body, canonical="glossary/")
    out_path = output_dir / "glossary" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)


def generate_categories_page(sensors, output_dir):
    """Generate the categories page: an index of all non-family categories
    with the sensors in each, anchorable by slug."""
    # Collect non-family categories (family-matching ones already link to
    # the catalog, so we only list categories that have no family match).
    cats = {}
    for s in sensors:
        for cat in s.get("categories", []):
            fam = FAMILY_BY_SLUG.get(cat.lower().replace(" ", "-"), {})
            if fam:
                continue
            cats.setdefault(cat, []).append(s)

    # Build sections, sorted by category name
    sections = ""
    for cat in sorted(cats):
        cat_slug = re.sub(r"[^a-z0-9]+", "-", cat.lower()).strip("-")
        items = ""
        for s in sorted(cats[cat], key=lambda x: x["title"]):
            items += f'        <li><a href="/sensors/{s["slug"]}/">{html.escape(s["title"])}</a></li>\n'
        sections += f"""      <section class="category-section">
        <h2 class="category-title" id="{cat_slug}">{html.escape(cat)}</h2>
        <ul class="category-sensor-list">
{items.rstrip()}
        </ul>
      </section>
"""

    body = f"""  <section class="page-header">
    <p class="eyebrow">Categories</p>
    <h1 class="page-title">Sensor Categories</h1>
    <p class="page-lede">
      Cross-cutting tags that span sensor families. Family-level categories
      link to the <a href="/catalog/" class="wikilink">catalog</a>; the
      tags below collect sensors across families that share a theme.
    </p>
  </section>

  <div class="about-content">
{sections.rstrip()}
  </div>"""

    page_html = html_page("Sensor Categories", body, canonical="categories/")
    out_path = output_dir / "categories" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)


def generate_search_index(sensors, output_dir):
    """Write search-index.json: title, family, url, and plain-text blurb
    for every sensor, plus an entry per family."""
    import json
    entries = []
    for f in FAMILIES:
        entries.append({
            "title": f["name"],
            "kind": "family",
            "family": f["name"],
            "url": f"/catalog/#{f['slug']}",
            "blurb": f["question"],
        })
    for s in sensors:
        fam = FAMILY_BY_SLUG.get(s.get("family", ""), {})
        blurb = blurb_text(s.get("body_html", ""), limit=160)
        entries.append({
            "title": s["title"],
            "kind": "sensor",
            "family": fam.get("name", ""),
            "url": f"/sensors/{s['slug']}/",
            "blurb": blurb,
        })
    with open(output_dir / "search-index.json", "w") as f:
        json.dump(entries, f, indent=1, sort_keys=True)


SITE_URL = "https://softwareobservatory.com"


def generate_sitemap(sensors, output_dir):
    """Write sitemap.xml listing every indexable URL."""
    urls = [
        ("", ""),
        ("catalog/", ""),
        ("atlas/", ""),
        ("framework/", ""),
        ("about/", ""),
        ("contact/", ""),
        ("privacy/", ""),
        ("glossary/", ""),
        ("categories/", ""),
    ]
    for s in sensors:
        urls.append((f"sensors/{s['slug']}/", ""))
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, _ in urls:
        loc = f"{SITE_URL}/{path}" if path else SITE_URL
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        lines.append("  </url>")
    lines.append("</urlset>")
    with open(output_dir / "sitemap.xml", "w") as f:
        f.write("\n".join(lines) + "\n")


def generate_robots(output_dir):
    """Write robots.txt pointing at the sitemap."""
    content = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n"
    with open(output_dir / "robots.txt", "w") as f:
        f.write(content)


def generate_rss(sensors, output_dir):
    """Write rss.xml — a feed of all sensor entries, newest first."""
    import datetime
    sorted_sensors = sorted(
        sensors,
        key=lambda s: s.get("last_reviewed", ""),
        reverse=True,
    )
    pub_date = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S +0000"
    )
    items = ""
    for s in sorted_sensors:
        fam = FAMILY_BY_SLUG.get(s.get("family", ""), {})
        blurb = blurb_text(s.get("body_html", ""), limit=200)
        items += f"""    <item>
      <title>{html.escape(s['title'])}</title>
      <link>{SITE_URL}/sensors/{s['slug']}/</link>
      <guid>{SITE_URL}/sensors/{s['slug']}/</guid>
      <description>{html.escape(blurb)}</description>
      <category>{html.escape(fam.get('name', ''))}</category>
    </item>
"""
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Software Observatory</title>
    <link>{SITE_URL}</link>
    <description>A catalog of epistemic sensors for software correctness.</description>
    <language>en</language>
    <lastBuildDate>{pub_date}</lastBuildDate>
{items.rstrip()}
  </channel>
</rss>"""
    with open(output_dir / "rss.xml", "w") as f:
        f.write(feed)


def generate_404(sensors, output_dir):
    """Write 404.html with recovery links for agents and humans."""
    body = f"""  <section class="page-header">
    <p class="eyebrow">404</p>
    <h1 class="page-title">Not found</h1>
    <p class="page-lede">
      This page doesn't exist. Here's where to look instead:
    </p>
  </section>

  <div class="about-content">
    <h2>Find your way</h2>
    <ul>
      <li><a href="/" class="wikilink">Homepage</a> — the thesis and the confidence landscape</li>
      <li><a href="/catalog/" class="wikilink">Sensor catalog</a> — all {len(sensors)} sensors across {len(FAMILIES)} families</li>
      <li><a href="/atlas/" class="wikilink">Sensor atlas</a> — families arranged by lifecycle stage</li>
      <li><a href="/framework/" class="wikilink">Framework</a> — the six dimensions every sensor is characterized along</li>
      <li><a href="/glossary/" class="wikilink">Glossary</a> — definitions of the core vocabulary</li>
      <li><a href="/categories/" class="wikilink">Categories</a> — cross-cutting tags that span families</li>
    </ul>
    <h2>For agents</h2>
    <p>
      Sitemap: <a href="sitemap.xml">/sitemap.xml</a> — all indexable URLs.
      Machine-readable catalog: <a href="search-index.json">/search-index.json</a>.
      Agent instructions: <a href="llms.txt">/llms.txt</a>.
    </p>
  </div>"""
    page_html = html_page("Not found", body, canonical="404.html")
    with open(output_dir / "404.html", "w") as f:
        f.write(page_html)


def generate_llms_txt(sensors, output_dir):
    """Write llms.txt — agent-readable summary with when-to-use guidance."""
    lines = [
        "# Software Observatory",
        "",
        "> A catalog of epistemic sensors for software correctness — the observable signals that reduce uncertainty about whether a system is correct, maintainable, and behaving as intended.",
        "",
        f"The Software Observatory catalogs the signals we can observe about software, characterizes each along six dimensions (oracle strength, independence, scope, feedback latency, actionability, predictive vs retrospective), and arranges them into {len(FAMILIES)} families.",
        "",
        "## When to use this",
        "",
        "Use this catalog when a user asks:",
        "- What tests to add for a new codebase or feature",
        "- How to evaluate AI-generated code (second-agent review, independence, mechanical gates)",
 "- What 'observability' means in practice vs. traditional monitoring",
 "- For a taxonomy of software quality signals / verification techniques",
 "- What the difference is between coverage, mutation testing, and property-based testing",
 "- How to set up a CI pipeline that actually catches bugs (mechanical gates, not prose rules)",
 "- What sensors to combine for a greenfield project, a regulated industry, or a legacy rescue",
 "",
        "## When NOT to use this",
        "",
        "Do not use this catalog for:",
        "- Language-specific syntax questions (use the language's own docs)",
        "- Tool configuration details (link to the tool's own docs; this catalog names tools but doesn't configure them)",
        "- Framework-specific testing setup (e.g. how to configure Jest; use the Jest docs)",
        "",
        "## How to navigate",
        "",
        f"- Catalog: /catalog/ — all {len(sensors)} sensors organized by family",
        "- Atlas: /atlas/ — families arranged as a matrix by lifecycle stage",
        "- Framework: /framework/ — the six dimensions",
        "- Glossary: /glossary/ — definitions of core terms (oracle, independence, epistemic sensor, etc.)",
        "- Individual entries: /sensors/<slug>/ (e.g. /sensors/mutation-testing/)",
        "",
        "## Machine-readable surfaces",
        "",
        "- Sitemap: /sitemap.xml",
        "- Search index: /search-index.json (title, family, url, blurb per sensor)",
        "- RSS: /rss.xml",
        "",
        "## Sensor families",
        "",
    ]
    for f in FAMILIES:
        lines.append(f"- {f['name']}: {f['question']} (see /catalog/#{f['slug']})")
    lines.append("")
    with open(output_dir / "llms.txt", "w") as f:
        f.write("\n".join(lines))


def assert_family_count(output_dir):
    """Scan generated HTML for prose family-count strings and fail the build
    if any digit-based count disagrees with len(FAMILIES).

    Catches drift where a page hard-codes "N families" instead of computing
    the count from the FAMILIES data structure.
    """
    import re
    expected = len(FAMILIES)
    pattern = re.compile(r"(\d+)\s+families?", re.IGNORECASE)
    mismatches = []
    for html_path in output_dir.rglob("*.html"):
        try:
            text = html_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for m in pattern.finditer(text):
            found = int(m.group(1))
            if found != expected:
                mismatches.append((html_path.name, m.group(0)))
    if mismatches:
        details = "; ".join(f"{name}: {snippet!r}" for name, snippet in mismatches)
        raise AssertionError(
            f"Family-count drift: FAMILIES has {expected} entries but generated "
            f"HTML says otherwise — {details}. Compute the count from "
            f"len(FAMILIES) instead of hard-coding it."
        )


def assert_family_examples(sensors):
    """Warn if a family's `examples` string names a sensor owned by a
    different family.

    Each family's examples list should be accurate to its rows. The check
    matches comma-separated example tokens against sensor titles
    (case-insensitive, either side subsumes the other) and flags tokens
    that resolve to a sensor in another family.
    """
    # Map lowercased sensor title -> family slug
    title_to_family = {}
    for s in sensors:
        title_to_family[s["title"].lower()] = s.get("family", "")
    warnings = []
    for fam in FAMILIES:
        fam_slug = fam["slug"]
        examples = fam.get("examples", "")
        for token in (t.strip().lower() for t in examples.split(",")):
            if not token:
                continue
            for title, owner in title_to_family.items():
                # Match only on exact (case-insensitive) token == title, so
                # generic words like "contract" don't false-match "Contract
                # & Refinement Types" when they mean "Contract Tests".
                if token == title:
                    if owner and owner != fam_slug:
                        warnings.append(
                            f'family {fam_slug!r} examples name '
                            f'{token!r} but sensor {title!r} is owned by '
                            f'family {owner!r}'
                        )
    if warnings:
        print("  WARNING: family examples / ownership mismatches:")
        for w in warnings:
            print(f"    {w}")
        print("  (Fix the examples list in FAMILIES or reassign the sensor.)")


def assert_see_also_resolves(sensors):
    """Fail the build if any see_also token does not resolve to a sensor ID,
    a family slug, or the literal 'atlas'.

    Unresolved tokens are silently dropped by resolve_see_also; this check
    surfaces them so dangling references don't accumulate.
    """
    sensors_by_id = {s["id"] for s in sensors}
    family_slugs = {f["slug"] for f in FAMILIES}
    unresolved = []
    for sensor in sensors:
        for ref in sensor.get("see_also", []):
            if ref in sensors_by_id or ref in family_slugs or ref == "atlas":
                continue
            unresolved.append((sensor["id"], sensor["slug"], ref))
    if unresolved:
        details = "; ".join(
            f"{sid} ({slug}): {ref!r}" for sid, slug, ref in unresolved
        )
        raise AssertionError(
            f"Unresolved see_also tokens — {details}. Each see_also entry "
            f"must be a sensor ID, a family slug, or the literal 'atlas'."
        )


def assert_family_and_stack_level(sensors):
    """Fail the build when a sensor's `family` or `stack_level` does not
    match a known slug.

    A typo in frontmatter silently drops the sensor off the catalog and
    atlas (the detail page still generates, so check_links can't catch
    it). This check surfaces the mismatch.
    """
    family_slugs = {f["slug"] for f in FAMILIES}
    stack_slugs = {s["slug"] for s in STACK_LAYERS}
    bad = []
    for sensor in sensors:
        fam = sensor.get("family", "")
        if fam and fam not in family_slugs:
            bad.append((sensor["id"], sensor["slug"], "family", fam))
        lvl = sensor.get("stack_level", "")
        if lvl and lvl not in stack_slugs:
            bad.append((sensor["id"], sensor["slug"], "stack_level", lvl))
    if bad:
        details = "; ".join(
            f"{sid} ({slug}): {field}={val!r}" for sid, slug, field, val in bad
        )
        raise AssertionError(
            f"Unrecognized family/stack_level slugs — {details}. "
            f"Valid families: {sorted(family_slugs)}. "
            f"Valid stack levels: {sorted(stack_slugs)}."
        )


def main():
    print("Loading sensors...")
    sensors = load_sensors()
    print(f"  Found {len(sensors)} sensors")

    # Build lookup tables
    sensors_by_id = {s["id"]: s for s in sensors}
    families_by_slug = FAMILY_BY_SLUG

    # Compute backlinks
    backlinks = compute_backlinks(sensors)
    for sid, bls in backlinks.items():
        print(f"  {sid}: {len(bls)} backlinks")

    output_dir = OUTPUT_DIR

    # Remove stale output from the old /pages/*.html layout
    stale_pages = output_dir / "pages"
    if stale_pages.exists():
        shutil.rmtree(stale_pages)
    for stale in ("index.html",):
        pass  # index.html is still the root output, regenerated below

    (output_dir / "sensors").mkdir(parents=True, exist_ok=True)

    print("Generating search index...")
    generate_search_index(sensors, output_dir)
    print("  search-index.json")

    print("Generating sitemap and robots...")
    generate_sitemap(sensors, output_dir)
    print("  sitemap.xml")
    generate_robots(output_dir)
    print("  robots.txt")

    print("Generating RSS feed...")
    generate_rss(sensors, output_dir)
    print("  rss.xml")

    print("Generating 404 page...")
    generate_404(sensors, output_dir)
    print("  404.html")

    print("Generating llms.txt...")
    generate_llms_txt(sensors, output_dir)
    print("  llms.txt")

    # Copy markdown sources for content negotiation (Accept: text/markdown)
    md_dir = output_dir / "md" / "sensors"
    md_dir.mkdir(parents=True, exist_ok=True)
    for filepath in sorted((CONTENT_DIR / "sensors").glob("*.md")):
        shutil.copy2(filepath, md_dir / filepath.name)
    print("  md/sensors/*.md (for content negotiation)")

    print("Generating pages...")
    generate_index_page(sensors, output_dir)
    print("  index.html")

    generate_catalog_page(sensors, output_dir)
    print("  catalog/")

    generate_atlas_page(sensors, output_dir)
    print("  atlas/")

    generate_framework_page(sensors, output_dir)
    print("  framework/")

    generate_about_page(output_dir)
    print("  about/")

    generate_contact_page(output_dir)
    print("  contact/")

    generate_privacy_page(output_dir)
    print("  privacy/")

    generate_glossary_page(output_dir)
    print("  glossary/")

    generate_categories_page(sensors, output_dir)
    print("  categories/")

    for sensor in sensors:
        generate_sensor_page(sensor, backlinks, sensors_by_id, families_by_slug, output_dir)
        print(f"  sensors/{sensor['slug']}/")

    print("Exporting CLI dataset...")
    import export_cli_data
    export_cli_data.export()
    print("  cli/data/sensors.json")

    print("Checking family-count consistency...")
    assert_family_count(output_dir)
    print("  OK")

    print("Checking family examples / ownership...")
    assert_family_examples(sensors)

    print("Checking see_also resolution...")
    assert_see_also_resolves(sensors)
    print("  OK")

    print("Checking family / stack_level slugs...")
    assert_family_and_stack_level(sensors)
    print("  OK")

    print("Done.")


if __name__ == "__main__":
    main()
