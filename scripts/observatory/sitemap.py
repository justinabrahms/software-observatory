"""sitemap.xml and robots.txt."""

from .config import SITE_URL
from .dates import _iso_date
from .taxonomy import FAMILIES


def sitemap_lastmods(sensors):
    """(per-sensor lastmod, site-wide lastmod).

    Derived from each entry's `last_reviewed` frontmatter rather than from
    file mtimes or wall-clock time: mtimes differ between a working copy and
    a fresh CI checkout, and anything clock-derived would rewrite sitemap.xml
    on every build (and re-upload it on every deploy). `last_reviewed` is
    content, versioned with the entry, and is exactly the date a crawler
    should re-check.

    Section pages are aggregates of the catalog, so they carry the newest
    entry date.
    """
    per_sensor = {}
    for s in sensors:
        d = _iso_date(s.get("last_reviewed"))
        if d:
            per_sensor[s["slug"]] = d
    site = max(per_sensor.values()) if per_sensor else None
    return per_sensor, site


def generate_sitemap(sensors, output_dir):
    """Write sitemap.xml listing every indexable URL with a <lastmod>."""
    per_sensor, site_lastmod = sitemap_lastmods(sensors)
    urls = [(path, site_lastmod) for path in (
        "", "catalog/", "atlas/", "framework/", "about/",
        "contact/", "privacy/", "glossary/", "categories/",
    )]
    for family in FAMILIES:
        urls.append((f"families/{family['slug']}/", site_lastmod))
    for s in sensors:
        urls.append((f"sensors/{s['slug']}/", per_sensor.get(s["slug"], site_lastmod)))
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, lastmod in urls:
        loc = f"{SITE_URL}/{path}" if path else SITE_URL
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        if lastmod:
            lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>")
    with open(output_dir / "sitemap.xml", "w") as f:
        f.write("\n".join(lines) + "\n")


def generate_robots(output_dir):
    """Write robots.txt pointing at the sitemap."""
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {SITE_URL}/sitemap.xml\n"
        "\n"
        "# Machine-readable surfaces (see /llms.txt for what they are for):\n"
        f"# Agent index:      {SITE_URL}/llms.txt\n"
        f"# Full catalog:     {SITE_URL}/llms-full.txt\n"
        f"# Structured data:  {SITE_URL}/sensors.json\n"
    )
    with open(output_dir / "robots.txt", "w") as f:
        f.write(content)
