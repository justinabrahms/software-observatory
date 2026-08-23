#!/usr/bin/env python3
"""
Software Observatory — static site generator.

Reads markdown files with YAML frontmatter from content/, renders HTML
pages using templates, computes backlinks from see_also references, and
writes everything to the site root.

Usage:
    .venv/bin/python build.py [--watch]
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


SITE_ROOT = Path(__file__).parent
CONTENT_DIR = SITE_ROOT / "content"
OUTPUT_DIR = SITE_ROOT
CSS_DIR = SITE_ROOT / "css"
JS_DIR = SITE_ROOT / "js"

# ── Sensor family metadata ──────────────────────────────────────────────────

FAMILIES = [
    {
        "slug": "structural",
        "num": "01",
        "name": "Structural",
        "question": "Is this artifact internally coherent?",
        "examples": "Compiler, type checker, linter, formatter, schema validator",
        "stack_levels": ["compilation", "static-analysis"],
    },
    {
        "slug": "behavioral",
        "num": "02",
        "name": "Behavioral",
        "question": "Does it do what we expect?",
        "examples": "Unit, integration, E2E, contract, snapshot tests",
        "stack_levels": ["behavioral-tests", "integration-tests"],
    },
    {
        "slug": "test-effectiveness",
        "num": "03",
        "name": "Test Effectiveness",
        "question": "Do our tests actually detect failures?",
        "examples": "Coverage, diff coverage, mutation testing",
        "stack_levels": ["mutation-testing"],
    },
    {
        "slug": "invariants",
        "num": "04",
        "name": "Invariants",
        "question": "What must always be true?",
        "examples": "Balance >= 0, every FK valid, every request has one ID",
        "stack_levels": ["static-analysis", "production-behavior"],
    },
    {
        "slug": "adversarial",
        "num": "05",
        "name": "Adversarial",
        "question": "Can we make our evidence of correctness fail?",
        "examples": "Fuzzing, mutation testing, fault injection, chaos",
        "stack_levels": ["property-metamorphic", "mutation-testing"],
    },
    {
        "slug": "runtime",
        "num": "06",
        "name": "Runtime",
        "question": "What is it actually doing?",
        "examples": "Logs, traces, metrics, profiles, high-cardinality events",
        "stack_levels": ["production-behavior"],
    },
    {
        "slug": "change",
        "num": "07",
        "name": "Change",
        "question": "What did this change actually affect?",
        "examples": "Diff coverage, API compatibility, canary, shadow traffic",
        "stack_levels": ["canary-shadow"],
    },
    {
        "slug": "architecture",
        "num": "08",
        "name": "Architecture",
        "question": "Is the system becoming harder to reason about?",
        "examples": "Dependency graphs, coupling, fitness functions, hotspots",
        "stack_levels": ["static-analysis"],
    },
    {
        "slug": "evolution",
        "num": "09",
        "name": "Evolution",
        "question": "Does this look like changes that caused trouble before?",
        "examples": "Revert rate, regression rate, churn, incident correlation",
        "stack_levels": ["user-outcome"],
    },
    {
        "slug": "comprehension",
        "num": "10",
        "name": "Human Comprehension",
        "question": "Can another observer understand and challenge this?",
        "examples": "Review, explainability tests, documentation drift, onboarding",
        "stack_levels": [],
    },
    {
        "slug": "ai-sensors",
        "num": "11",
        "name": "AI-Generated Code",
        "question": "What evidence do we have that this change is safe?",
        "examples": "Agent sensor stacks, computational gates, independence",
        "stack_levels": [],
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
    "hours-seconds": "h-s",
    "days": "d",
    "weeks": "w",
    "varies": "varies",
}


# ── Markdown rendering ──────────────────────────────────────────────────────

def render_markdown(text):
    """Render markdown to HTML."""
    md = markdown.Markdown(extensions=["tables", "fenced_code", "smarty"])
    return md.convert(text)


def fix_link_depths(html_str, pages_depth=""):
    """Fix relative URLs in rendered markdown HTML for the current page depth.
    
    pages_depth is the relative path to pages/ from the current page.
    For pages/*.html, pages_depth="" (links like catalog.html are correct).
    For pages/sensors/*.html, pages_depth="../" (links need ../ prefix).
    
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
    
    if not pages_depth:
        return html_str
    
    # Fix relative links: prefix pages/-relative URLs with pages_depth
    # Match href="something.html or href="sensors/... but not http/https/#
    def fix_href(match):
        full = match.group(0)
        url = match.group(1)
        if url.startswith(('http://', 'https://', '#', 'mailto:')):
            return full
        return f'href="{pages_depth}{url}"'
    
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

    for filepath in sorted(sensor_dir.glob("*.md")):
        meta, body = parse_frontmatter(filepath)
        slug = filepath.stem
        meta["slug"] = slug
        meta["body_html"] = fix_link_depths(render_markdown(body), pages_depth="../")
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


def resolve_see_also(see_also_ids, sensors_by_id, families_by_slug, pages_depth=""):
    """Resolve see_also IDs to objects with title, slug, family, url.
    pages_depth: relative path to pages/ (e.g. '' for pages/, '../' for pages/sensors/)."""
    results = []
    for ref in see_also_ids:
        if ref in sensors_by_id:
            s = sensors_by_id[ref]
            results.append({
                "title": s["title"],
                "family": FAMILY_BY_SLUG.get(s.get("family", ""), {}).get("name", ""),
                "family_slug": s.get("family", ""),
                "url": f"{pages_depth}sensors/{s['slug']}.html",
            })
        elif ref in families_by_slug:
            f = families_by_slug[ref]
            results.append({
                "title": f["name"],
                "family": "Family",
                "family_slug": f["slug"],
                "url": f"{pages_depth}catalog.html#{f['slug']}",
            })
        elif ref == "atlas":
            results.append({
                "title": "Confidence Stack",
                "family": "Atlas",
                "family_slug": "atlas",
                "url": f"{pages_depth}atlas.html",
            })
    return results


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

def html_head(title, depth=""):
    """depth is '' for root, '../' for pages/, '../../' for pages/sensors/"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)} — Software Observatory</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=JetBrains+Mono:wght@400;500;600&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{depth}css/observatory.css">
</head>"""


def html_header(nav_depth="", root_depth=""):
    """nav_depth: relative path to pages/. root_depth: relative path to site root."""
    nav_items = [
        ("catalog.html", "Catalog"),
        ("atlas.html", "Atlas"),
        ("framework.html", "Framework"),
        ("about.html", "About"),
    ]
    nav_html = "\n".join(f'      <a href="{nav_depth}{href}">{label}</a>' for href, label in nav_items)
    return f"""  <header class="site-header">
    <a href="{root_depth}index.html" class="logo">
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
    <div class="search-box" data-root-depth="{root_depth}">
      <input type="search" class="search-input" placeholder="Search sensors…" aria-label="Search sensors" autocomplete="off">
      <div class="search-results" hidden></div>
    </div>
  </header>"""


def html_footer(root_depth="", nav_depth=""):
    return f"""  <footer class="site-footer">
    <div class="footer-inner">
      <p class="footer-tagline">Software Observatory — a catalog of epistemic sensors for software.</p>
      <p class="footer-copy">© 2026 Software Observatory · <a href="{nav_depth}about.html">About</a> · <span class="license-badge">CC BY-NC-SA 4.0</span></p>
    </div>
  </footer>"""


def html_page(title, body_content, root_depth="", nav_depth=""):
    """root_depth: relative path to site root (for css/js).
    nav_depth: relative path to pages/ (for nav links)."""
    return f"""{html_head(title, root_depth)}
<body>
{html_header(nav_depth, root_depth)}
{body_content}
{html_footer(root_depth, nav_depth)}
  <script src="{root_depth}js/main.js"></script>
</body>
</html>"""


# ── Page generators ─────────────────────────────────────────────────────────

def generate_sensor_page(sensor, backlinks, sensors_by_id, families_by_slug, output_dir):
    """Generate a single sensor detail page."""
    depth = "../../"  # pages/sensors/*.html
    family = FAMILY_BY_SLUG.get(sensor.get("family", ""), {})
    family_name = family.get("name", sensor.get("family", ""))
    family_slug = family.get("slug", "")

    # Resolve see_also (sensor pages are in pages/sensors/, so pages/ is ../)
    see_also_items = resolve_see_also(sensor.get("see_also", []), sensors_by_id, families_by_slug, pages_depth="../")

    # Resolve backlinks
    backlink_items = []
    for bl in backlinks.get(sensor["id"], []):
        backlink_items.append({
            "title": bl["from_title"],
            "url": f"{bl['from_slug']}.html",
            "context": bl["context"],
        })

    # Categories
    categories = sensor.get("categories", [])

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
                cat_links += f'          <a href="../catalog.html#{fam["slug"]}" class="cat-link">{html.escape(cat)}</a>\n'
            else:
                cat_links += f'          <a href="#" class="cat-link">{html.escape(cat)}</a>\n'
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
            url = f"../catalog.html#{fam['slug']}" if fam else "#"
            items += f'          <li><a href="{url}">Category: {html.escape(cat)}</a></li>\n'
        cat_sidebar_html = f"""      <div class="sidebar-box">
        <h3 class="sidebar-heading">Related categories</h3>
        <ul class="sidebar-cat-list">
{items.rstrip()}
        </ul>
      </div>"""

    body = f"""  <div class="wiki-layout">
    <article class="signal-detail">
      <p class="breadcrumb"><a href="../catalog.html">Catalog</a> › <a href="../catalog.html#{family_slug}">{html.escape(family_name)}</a> › {html.escape(sensor['title'])}</p>

      <header class="signal-detail-header">
        <h1 class="signal-detail-title">{html.escape(sensor['title'])}</h1>
        <div class="signal-detail-meta">
          <span class="tag tag-family">{html.escape(family_name)}</span>
          <span class="tag tag-confidence">{html.escape(sensor.get('oracle', '').title())} oracle</span>
        </div>
      </header>

      <div class="signal-detail-body">
        {sensor['body_html']}

        {see_also_html}

{cat_html}
      </div>
    </article>

    <aside class="wiki-sidebar">
      <div class="sidebar-box">
        <h3 class="sidebar-heading">Sensor properties</h3>
        <dl class="meta-list">
          <dt>Family</dt>           <dd><a href="../catalog.html#{family_slug}" class="wikilink">{html.escape(family_name)}</a></dd>
          <dt>Oracle</dt>          <dd>{html.escape(sensor.get('oracle', '').title())}</dd>
          <dt>Independence</dt>     <dd>{html.escape(sensor.get('independence', '').title())}</dd>
          <dt>Scope</dt>           <dd>{html.escape(sensor.get('scope', '').replace('-', ' ').title())}</dd>
          <dt>Latency</dt>         <dd>{html.escape(LATENCY_LABELS.get(sensor.get('latency', ''), sensor.get('latency', '')))}</dd>
          <dt>Actionability</dt>   <dd>{html.escape(sensor.get('actionability', '').title())}</dd>
          <dt>Entry ID</dt>        <dd>{html.escape(sensor.get('id', ''))}</dd>
        </dl>
      </div>
{backlink_html}
{cat_sidebar_html}
    </aside>
  </div>"""

    page_html = html_page(f"{sensor['title']}", body, root_depth="../../", nav_depth="../")
    out_path = output_dir / "pages" / "sensors" / f"{sensor['slug']}.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)


def generate_catalog_page(sensors, output_dir):
    """Generate the catalog page with all 11 families."""
    depth = "../"

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
            lat = LATENCY_LABELS.get(s.get("latency", ""), s.get("latency", ""))
            title = s["title"]
            slug = s["slug"]

            # Get first paragraph from body as blurb (strip HTML tags)
            import re as re_mod
            body_text = re_mod.sub(r'<[^>]+>', '', s.get("body_html", ""))
            first_para = body_text.split("\n")[0][:200]

            cards += f"""          <article class="signal-card" onclick="window.location='sensors/{slug}.html'">
            <div class="signal-card-meta">
              <span class="tag tag-family">{html.escape(family['name'])}</span>
            </div>
            <h3 class="signal-card-title"><a href="sensors/{slug}.html" class="wikilink">{html.escape(title)}</a></h3>
            <p class="signal-card-blurb">{html.escape(first_para)}</p>
            <div class="signal-card-footer">
              <span class="oracle-meter">{oracle_d} Oracle</span>
              <span class="latency-badge">{html.escape(lat)}</span>
            </div>
          </article>\n"""

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
        filter_families += f'          <li data-family="{f["slug"]}">{html.escape(f["name"])} <span class="count">{count}</span></li>\n'

    total = len(sensors)

    body = f"""  <section class="page-header">
    <p class="eyebrow">The Catalog</p>
    <h1 class="page-title">Sensor Catalog</h1>
    <p class="page-lede">
      A catalog of <a href="#" class="wikilink">epistemic sensors</a> — the
      observable signals that increase our confidence that a system is correct,
      maintainable, and behaving as intended. Organized into eleven families.
      Each entry documents what the sensor can detect, what it cannot detect,
      how easily it can be gamed, and what evidence it produces.
    </p>
  </section>

  <div class="catalog-layout">
    <aside class="filter-sidebar">
      <div class="filter-group">
        <h3 class="filter-heading">Sensor Family</h3>
        <ul class="filter-list" id="family-filter">
          <li class="active" data-family="all">All Families <span class="count">{total}</span></li>
{filter_families.rstrip()}
        </ul>
      </div>
    </aside>

    <div class="catalog-content">
{sections_html.rstrip()}
    </div>
  </div>"""

    page_html = html_page("Sensor Catalog", body, root_depth="../", nav_depth="")
    out_path = output_dir / "pages" / "catalog.html"
    with open(out_path, "w") as f:
        f.write(page_html)


def generate_atlas_page(sensors, output_dir):
    """Generate the atlas page: a family x lifecycle-stage grid, plus a
    dependency map of how families lean on each other."""
    depth = "../"

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
            <a href="catalog.html#{family['slug']}" class="matrix-fam-name">{html.escape(family['name'])}</a>
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
                    chips += f'<a href="sensors/{s["slug"]}.html" class="matrix-chip">{html.escape(s["title"])}</a>\n'
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
        nodes_svg += f"""          <a href="catalog.html#{f['slug']}" class="dep-node" data-family="{f['slug']}">
            <circle cx="{x:.1f}" cy="{y:.1f}" r="9" class="dep-node-dot" />
            <text class="dep-node-label" x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}">{html.escape(f['name'])}</text>
          </a>
"""

    dep_graph_svg = f"""      <svg class="dep-graph" viewBox="0 0 1120 920" role="img" aria-label="Family dependency graph">
{edges_svg.rstrip()}
{labels_svg.rstrip()}
{nodes_svg.rstrip()}
      </svg>"""

    # Family map
    family_map = ""
    for f in FAMILIES:
        family_map += f"""        <a href="catalog.html#{f['slug']}" class="family-map-card">
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
        <a href="catalog.html" class="wikilink">sensor family</a> — a question
        you're asking about the system. Each column is a stage of the software
        lifecycle — <em>when</em> the signal becomes available, from authoring
        the code on the left to observing real-world outcomes on the right.
        For the narrative version of how evidence accumulates, see the
        <a href="../index.html#confidence-stack" class="wikilink">confidence stack</a>.
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
      <h2 class="section-heading">Eleven families at a glance</h2>
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
    </div>
  </div>"""

    page_html = html_page("Sensor Atlas", body, root_depth="../", nav_depth="")
    out_path = output_dir / "pages" / "atlas.html"
    with open(out_path, "w") as f:
        f.write(page_html)


def generate_index_page(sensors, output_dir):
    """Generate the homepage."""
    depth = ""

    # Featured sensor
    featured = next((s for s in sensors if s["id"] == "SO-003"), sensors[0] if sensors else None)
    featured_family = FAMILY_BY_SLUG.get(featured.get("family", ""), {}) if featured else {}

    # Families grid
    families_grid = ""
    for f in FAMILIES:
        families_grid += f"""        <a href="pages/catalog.html#{f['slug']}" class="family-card">
          <span class="family-num">{f['num']}</span>
          <h3 class="family-name">{html.escape(f['name'])}</h3>
          <p class="family-question">"{html.escape(f['question'])}"</p>
          <p class="family-examples">{html.escape(f['examples'])}</p>
        </a>
"""

    # Recent entries
    recent_html = ""
    for s in sensors[:6]:
        fam = FAMILY_BY_SLUG.get(s.get("family", ""), {})
        recent_html += f"""        <li class="entry">
          <span class="entry-family">{html.escape(fam.get('name', ''))}</span>
          <a href="pages/sensors/{s['slug']}.html" class="entry-title wikilink" style="border-bottom:none">{html.escape(s['title'])}</a>
          <span class="entry-blurb">{html.escape(re.sub(r'<[^>]+>', '', s.get('body_html', '')).split(chr(10))[0][:120])}</span>
        </li>
"""

    # Stack preview
    stack_layers_html = ""
    for layer in STACK_LAYERS:
        cls = "stack-bottom" if layer["slug"] == "source-text" else ""
        if layer["slug"] == "user-outcome":
            cls = "stack-top"
        stack_layers_html += f"""        <div class="stack-layer {cls}">
          <span class="stack-label">{html.escape(layer['label'])}</span>
          <span class="stack-desc">{html.escape(layer['desc'])}</span>
        </div>
"""

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
          Observatory is a catalog of <a href="pages/catalog.html" class="wikilink">epistemic sensors</a>:
          the observable signals that reduce uncertainty about whether a system
          is correct, maintainable, and behaving as intended. Not "code quality
          metrics." Measurement instruments pointed at different failure modes.
        </p>
        <div class="hero-actions">
          <a href="pages/catalog.html" class="btn btn-primary">Browse the catalog →</a>
          <a href="pages/atlas.html" class="btn btn-ghost">Open the atlas</a>
        </div>
      </div>
      <div class="hero-visual" aria-hidden="true">
        <div class="ring ring-1"></div>
        <div class="ring ring-2"></div>
        <div class="ring ring-3"></div>
        <div class="ring ring-4"></div>
        <div class="ring-dot dot-1"></div>
        <div class="ring-dot dot-2"></div>
        <div class="ring-dot dot-3"></div>
        <div class="ring-dot dot-4"></div>
        <div class="ring-dot dot-5"></div>
      </div>
    </section>

    <section class="core-insight">
      <blockquote class="big-quote">
        <p>
          No single sensor measures correctness. Coverage measures execution.
          <a href="pages/sensors/mutation-testing.html" class="wikilink">Mutation testing</a> measures
          test sensitivity. <a href="pages/sensors/type-checker.html" class="wikilink">Types</a> measure
          a particular class of structural inconsistency.
          <a href="pages/sensors/contract-tests.html" class="wikilink">Contracts</a> measure boundary
          assumptions. <a href="pages/sensors/observability-events.html" class="wikilink">Observability</a>
          measures what actually happened and preserves enough dimensionality
          to investigate unknown unknowns.
        </p>
        <p>They are all measurement instruments pointed at different failure modes.</p>
      </blockquote>
    </section>

    <section class="families-section">
      <h2 class="section-heading">Eleven sensor families</h2>
      <p class="section-lede">
        The catalog is organized into eleven families, each asking a different
        question about the system. Together, they form a mesh of independent
        evidence — no single sensor is sufficient, but the combination
        constrains uncertainty from multiple directions.
      </p>
      <div class="families-grid">
{families_grid.rstrip()}
      </div>
    </section>

    <section class="stack-preview" id="confidence-stack">
      <h2 class="section-heading">The confidence stack</h2>
      <p class="section-lede">
        Sensors are not peers. They form a hierarchy — from the cheapest, most
        certain signals at the bottom to the most expensive, most meaningful
        signals at the top. Each layer depends on the layers below it.
      </p>
      <div class="stack-diagram">
{stack_layers_html.rstrip()}
      </div>
      <div class="stack-cta">
        <a href="pages/atlas.html" class="btn btn-ghost">Open the atlas →</a>
      </div>
    </section>

    <section class="featured-signal">
      <div class="featured-meta">
        <span class="tag tag-family">{html.escape(featured_family.get('name', ''))}</span>
        <span class="tag tag-confidence">High oracle strength</span>
      </div>
      <h2 class="featured-title"><a href="pages/sensors/{featured['slug']}.html" class="wikilink" style="border-bottom:none">{html.escape(featured['title'])}</a></h2>
      <p class="featured-blurb">
        Take <code>if user.is_admin: allow()</code> and mutate it to
        <code>if not user.is_admin: allow()</code>. If all your tests still
        pass, your tests did not actually establish the behavior you thought
        they established. Mutation testing is a sensor of test
        <em>sensitivity</em> rather than test <em>presence</em> — and it may
        be one of the most interesting sensors in the entire catalog.
      </p>
      <div class="featured-cta">
        <a href="pages/sensors/{featured['slug']}.html">Read the full entry →</a>
      </div>
    </section>

    <section class="recent">
      <h2 class="section-heading">Catalog entries</h2>
      <ul class="entry-list">
{recent_html.rstrip()}
      </ul>
    </section>
  </main>"""

    page_html = html_page("Software Observatory", body, root_depth="", nav_depth="pages/")
    out_path = output_dir / "index.html"
    with open(out_path, "w") as f:
        f.write(page_html)


def generate_framework_page(sensors, output_dir):
    """Generate the framework page."""
    depth = "../"

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
        The important thing is that no single sensor measures
        <em>correctness</em>. Each sensor measures one thing. Coverage
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
        <div class="bar-row"><span class="bar-label">compiler error</span><div class="bar-track"><div class="bar-fill" style="width:100%"></div></div><span class="bar-pct">10/10</span></div>
        <div class="bar-row"><span class="bar-label">type error</span><div class="bar-track"><div class="bar-fill" style="width:100%"></div></div><span class="bar-pct">10/10</span></div>
        <div class="bar-row"><span class="bar-label">test assertion</span><div class="bar-track"><div class="bar-fill" style="width:90%"></div></div><span class="bar-pct">9/10</span></div>
        <div class="bar-row"><span class="bar-label">mutation</span><div class="bar-track"><div class="bar-fill" style="width:90%"></div></div><span class="bar-pct">9/10</span></div>
        <div class="bar-row"><span class="bar-label">linter</span><div class="bar-track"><div class="bar-fill" style="width:80%"></div></div><span class="bar-pct">8/10</span></div>
        <div class="bar-row"><span class="bar-label">coverage</span><div class="bar-track"><div class="bar-fill" style="width:40%"></div></div><span class="bar-pct">4/10</span></div>
        <div class="bar-row"><span class="bar-label">complexity</span><div class="bar-track"><div class="bar-fill" style="width:20%"></div></div><span class="bar-pct">2/10</span></div>
        <div class="bar-row"><span class="bar-label">code review</span><div class="bar-track"><div class="bar-fill" style="width:60%"></div></div><span class="bar-pct">6/10</span></div>
      </div>
      <p>
        A compiler has maximum oracle strength because the implementation
        cannot argue with it. A complexity metric has low oracle strength
        because high complexity doesn't prove anything is wrong — it just
        suggests increased risk.
      </p>
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
        This is where guiding sensors become particularly interesting. A
        guiding sensor doesn't just flag a problem — it tells the agent what
        to do next. In Böckeler's framing, the interesting frontier is sensors
        where the feedback itself directs the next action.
      </p>
    </section>

    <section class="property-detail">
      <span class="property-detail-num">06</span>
      <h2 class="property-detail-title">Predictive vs retrospective</h2>
      <p class="property-detail-question">"This is wrong" or "this looks like things that became wrong before"?</p>
      <p>
        You don't need to understand <code>FooManagerFactoryImpl</code>. You
        can observe: <em>27 changes in six months, 8 reverts, 4 incidents,
        touched by 11 teams.</em> That's a signal — a black-box sensor of
        maintainability.
      </p>
    </section>
  </div>"""

    page_html = html_page("Framework", body, root_depth="../", nav_depth="")
    out_path = output_dir / "pages" / "framework.html"
    with open(out_path, "w") as f:
        f.write(page_html)


def generate_about_page(output_dir):
    """Generate the about page."""
    depth = "../"

    body = """  <section class="page-header">
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
      Software is increasingly an <a href="#" class="wikilink">opaque
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
      <a href="catalog.html" class="wikilink">epistemic sensors</a>. Their
      job is to reduce uncertainty about a system that we cannot — or
      increasingly do not want to — fully understand.
    </p>

    <h2>The framework</h2>
    <p>
      The catalog is organized into <a href="catalog.html" class="wikilink">eleven
      families</a> of sensors, each asking a different question about the
      system. Every sensor is characterized along
      <a href="framework.html" class="wikilink">six dimensions</a>:
      oracle strength, independence, scope, feedback latency,
      actionability, and predictive vs retrospective. The
      <a href="atlas.html" class="wikilink">atlas</a> arranges them as a
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

    <h2>Contributing</h2>
    <p>
      Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod
      tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
      veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
      commodo consequat.
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

    page_html = html_page("About", body, root_depth="../", nav_depth="")
    out_path = output_dir / "pages" / "about.html"
    with open(out_path, "w") as f:
        f.write(page_html)


# ── Main ────────────────────────────────────────────────────────────────────

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
            "url": f"pages/catalog.html#{f['slug']}",
            "blurb": f["question"],
        })
    for s in sensors:
        fam = FAMILY_BY_SLUG.get(s.get("family", ""), {})
        blurb = re.sub(r"<[^>]+>", "", s.get("body_html", "")).split("\n")[0][:160]
        entries.append({
            "title": s["title"],
            "kind": "sensor",
            "family": fam.get("name", ""),
            "url": f"pages/sensors/{s['slug']}.html",
            "blurb": blurb,
        })
    with open(output_dir / "search-index.json", "w") as f:
        json.dump(entries, f, indent=1)


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

    print("Generating search index...")
    generate_search_index(sensors, output_dir)
    print("  search-index.json")

    print("Generating pages...")
    generate_index_page(sensors, output_dir)
    print("  index.html")

    generate_catalog_page(sensors, output_dir)
    print("  pages/catalog.html")

    generate_atlas_page(sensors, output_dir)
    print("  pages/atlas.html")

    generate_framework_page(sensors, output_dir)
    print("  pages/framework.html")

    generate_about_page(output_dir)
    print("  pages/about.html")

    for sensor in sensors:
        generate_sensor_page(sensor, backlinks, sensors_by_id, families_by_slug, output_dir)
        print(f"  pages/sensors/{sensor['slug']}.html")

    print("Done.")


if __name__ == "__main__":
    main()
