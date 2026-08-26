"""The category index: /categories/."""

import html
import re

from ..layout import html_page
from ..jsonld import breadcrumb_ld, page_ld
from ..taxonomy import FAMILY_BY_SLUG


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

    description = (
        "Cross-cutting tags that cut across the sensor families — find "
        "every adversarial, mechanical, or production-only sensor in one "
        "list."
    )
    page_html = html_page(
        "Sensor Categories", body, canonical="categories/",
        description=description,
        json_ld=[
            page_ld("CollectionPage", "Sensor Categories", "/categories/", description),
            breadcrumb_ld([("Categories", None)]),
        ],
    )
    out_path = output_dir / "categories" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)
