"""Markdown rendering and the HTML post-processing every body goes through.

Sensor bodies are authored as markdown with bare-filename links between
entries; this module turns them into the site-absolute HTML the pages embed,
plus the derived strings (blurbs, meta descriptions, heading ids) built from
rendered HTML rather than from source markdown."""

import html
import markdown
import re

from .config import SECTION_PAGES


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


def meta_description(text, limit=158):
    """Squeeze `text` into a meta-description-sized string.

    Search results and link unfurls cut around 155-160 characters, so trim to
    a sentence boundary when there is a usable one and otherwise to a word
    boundary with an ellipsis — never mid-word.
    """
    t = " ".join(str(text or "").split())
    if len(t) <= limit:
        return t
    window = t[: limit + 1]
    ends = [m.end() for m in re.finditer(r"""[.!?]+["')\]]*(?=\s|$)""", window)]
    if ends and ends[-1] >= limit * 0.55:
        return window[: ends[-1]].rstrip()
    return window.rsplit(" ", 1)[0].rstrip(" ,;:—-") + "…"
