"""The catalog index: /catalog/."""

import html

from ..components import sensor_card_html
from ..config import SITE_URL
from ..jsonld import (
    AUTHOR_LD,
    CATALOG_TERMSET_ID,
    CONTENT_LICENSE,
    ORGANIZATION_LD,
    breadcrumb_ld,
    catalog_dataset_ld,
    family_termset_id,
    sensor_term_ld,
)
from ..layout import html_page
from ..taxonomy import FAMILIES, family_url


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

        cards = "".join(sensor_card_html(s, family) for s in fam_sensors)

        sections_html += f"""      <section class="family-section" id="{family['slug']}" data-family="{family['slug']}">
        <div class="family-header">
          <span class="family-num">{family['num']}</span>
          <div>
            <h2 class="family-title"><a href="{family_url(family['slug'])}" class="wikilink">{html.escape(family['name'])}</a></h2>
            <p class="family-tagline">"{html.escape(family['question'])}"</p>
            <p class="family-more"><a href="{family_url(family['slug'])}">What belongs in this family \u2192</a></p>
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

    # Index of the family pages. /catalog/ stays the complete list; each
    # family also has a page of its own that can rank for its own topic.
    family_index = ""
    for f in FAMILIES:
        count = len(by_family.get(f["slug"], []))
        family_index += (
            f'          <li><a href="{family_url(f["slug"])}" class="wikilink">'
            f'{html.escape(f["name"])}</a><span class="count">{count}</span>'
            f'<span class="family-index-q">{html.escape(f["question"])}</span></li>\n'
        )

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
      <nav class="family-index" aria-label="Sensor families">
        <h2 class="section-heading">Families</h2>
        <ul class="family-index-list">
{family_index.rstrip()}
        </ul>
      </nav>

{sections_html.rstrip()}
    </div>
  </div>"""

    # The catalog IS a defined term set: 59 terms, each with a definition,
    # grouped into 10 families. Emitting it as one lets an entity extractor
    # read the vocabulary instead of guessing at 59 pages of prose.
    termset_ld = {
        "@type": "DefinedTermSet",
        "@id": CATALOG_TERMSET_ID,
        "name": "Software Observatory sensor catalog",
        "description": (
            f"{len(sensors)} epistemic sensors for software correctness, "
            f"grouped into {len(FAMILIES)} families."
        ),
        "url": f"{SITE_URL}/catalog/",
        "inLanguage": "en",
        "license": CONTENT_LICENSE,
        "creator": AUTHOR_LD,
        "publisher": {"@id": ORGANIZATION_LD["@id"]},
        "hasPart": [
            {"@id": family_termset_id(f["slug"])}
            for f in FAMILIES if by_family.get(f["slug"])
        ],
        "hasDefinedTerm": [
            sensor_term_ld(s, CATALOG_TERMSET_ID)
            for f in FAMILIES for s in by_family.get(f["slug"], [])
        ],
    }
    itemlist_ld = {
        "@type": "ItemList",
        "@id": f"{SITE_URL}/catalog/#itemlist",
        "name": "Sensor Catalog",
        "numberOfItems": len(sensors),
        "itemListOrder": "https://schema.org/ItemListUnordered",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": position,
                "name": entry["title"],
                "url": f"{SITE_URL}/sensors/{entry['slug']}/",
            }
            for position, entry in enumerate(
                [s for f in FAMILIES for s in by_family.get(f["slug"], [])], start=1
            )
        ],
    }

    page_html = html_page(
        "Sensor Catalog", body, canonical="catalog/",
        json_ld=[
            termset_ld,
            itemlist_ld,
            # sensors.json and llms-full.txt are served publicly and nothing
            # in the graph declared either existed, so the two most reusable
            # artifacts on the site were the least discoverable — and carried
            # no license with them.
            catalog_dataset_ld(len(sensors), len(FAMILIES)),
            breadcrumb_ld([("Catalog", None)]),
        ],
        description=(
            f"All {len(sensors)} epistemic sensors, grouped into the "
            f"{len(FAMILIES)} families — what each one detects, what it "
            "misses, and how strong its verdict is."
        ),
    )
    out_path = output_dir / "catalog" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)
