"""The per-family pages: /families/<slug>/."""

import html

from ..components import sensor_card_html
from ..config import SITE_URL
from ..jsonld import (
    AUTHOR_LD,
    CATALOG_TERMSET_ID,
    CONTENT_LICENSE,
    breadcrumb_ld,
    family_termset_id,
    sensor_term_ld,
)
from ..layout import html_page
from ..taxonomy import (
    FAMILIES,
    FAMILY_RATIONALE,
    LIFECYCLE_STAGES,
    STACK_LAYERS,
    STAGE_BY_LEVEL,
    family_url,
)


def family_description(family, count):
    """The family's own meta description. Unique per family by construction:
    it is built from that family's name, question and examples."""
    return (
        f"{family['name']} sensors ask: {family['question']} "
        f"{count} entries in the Software Observatory — {family['examples']}."
    )


def generate_family_pages(sensors, output_dir):
    """Generate /families/<slug>/ for every family.

    Ten topics that share one page compete with each other; ten pages do not.
    /catalog/ stays the complete index and keeps its `#<slug>` anchors, so
    every link that ever pointed at /catalog/#adversarial still resolves.
    """
    by_family = {}
    for sensor in sensors:
        by_family.setdefault(sensor.get("family", "uncategorized"), []).append(sensor)

    stack_by_slug = {layer["slug"]: layer for layer in STACK_LAYERS}
    stage_by_slug = {stage["slug"]: stage for stage in LIFECYCLE_STAGES}

    for index, family in enumerate(FAMILIES):
        fam_sensors = by_family.get(family["slug"], [])
        rationale = FAMILY_RATIONALE.get(family["slug"], {})

        cards = "".join(sensor_card_html(s, family) for s in fam_sensors)

        # Where in the lifecycle this family's signals arrive.
        levels_html = ""
        for level_slug in family.get("stack_levels", []):
            layer = stack_by_slug.get(level_slug)
            if not layer:
                continue
            stage = stage_by_slug.get(STAGE_BY_LEVEL.get(level_slug, ""), {})
            stage_label = f" — {html.escape(stage['label'])} stage" if stage else ""
            levels_html += (
                f'        <li><strong>{html.escape(layer["label"])}</strong>'
                f'{stage_label}. {html.escape(layer["desc"])}</li>\n'
            )

        prev_fam = FAMILIES[index - 1] if index > 0 else None
        next_fam = FAMILIES[index + 1] if index + 1 < len(FAMILIES) else None
        adjacent = ""
        if prev_fam:
            adjacent += (
                f'        <li>Previous: <a href="{family_url(prev_fam["slug"])}" '
                f'class="wikilink">{html.escape(prev_fam["name"])}</a> — '
                f'{html.escape(prev_fam["question"])}</li>\n'
            )
        if next_fam:
            adjacent += (
                f'        <li>Next: <a href="{family_url(next_fam["slug"])}" '
                f'class="wikilink">{html.escape(next_fam["name"])}</a> — '
                f'{html.escape(next_fam["question"])}</li>\n'
            )

        contested_html = ""
        if rationale.get("contested"):
            contested_html = f"""      <h2>Contested placements</h2>
      <p>{html.escape(rationale["contested"])}</p>
"""

        body = f"""  <article class="family-page">
    <p class="breadcrumb"><a href="/catalog/">Catalog</a> \u203a {html.escape(family['name'])}</p>

    <section class="page-header">
      <p class="eyebrow">Sensor family {family['num']}</p>
      <h1 class="page-title">{html.escape(family['name'])}</h1>
      <p class="page-lede">\u201c{html.escape(family['question'])}\u201d</p>
    </section>

    <div class="about-content">
      <h2>What belongs here</h2>
      <p>{html.escape(rationale.get("belongs", family["examples"]))}</p>

{contested_html}      <h2>Where its signals arrive</h2>
      <ul>
{levels_html.rstrip()}
      </ul>
      <p>
        The <a href="/atlas/" class="wikilink">atlas</a> places every family on
        the same lifecycle grid; the
        <a href="/framework/" class="wikilink">framework</a> defines the six
        dimensions each entry below is characterized along.
      </p>

      <h2 id="entries">Entries ({len(fam_sensors)})</h2>
    </div>

    <div class="signal-grid">
{cards.rstrip()}
    </div>

    <div class="about-content">
      <h2>Adjacent families</h2>
      <ul>
{adjacent.rstrip()}
        <li>All of them: the <a href="/catalog/" class="wikilink">complete catalog</a>
          (this family is also anchored there at
          <a href="/catalog/#{family['slug']}" class="wikilink">/catalog/#{family['slug']}</a>).</li>
      </ul>
    </div>
  </article>"""

        family_ld = {
            "@type": "DefinedTermSet",
            "@id": family_termset_id(family["slug"]),
            "name": f"{family['name']} sensors",
            "description": family_description(family, len(fam_sensors)),
            "url": f"{SITE_URL}{family_url(family['slug'])}",
            "inLanguage": "en",
            "license": CONTENT_LICENSE,
            "creator": AUTHOR_LD,
            "isPartOf": {"@id": CATALOG_TERMSET_ID},
            "hasDefinedTerm": [
                sensor_term_ld(s, family_termset_id(family["slug"]))
                for s in fam_sensors
            ],
        }
        crumbs = breadcrumb_ld([("Catalog", "/catalog/"), (family["name"], None)])

        # A family with no entries has no term set — hasDefinedTerm would be
        # [], which asserts "this vocabulary is empty" rather than saying
        # nothing. Every family is populated today, so this never fires on the
        # real catalog; it fired the moment the JSON-LD gate started looking
        # inside @graph, on a fixture corpus where most families are empty.
        nodes = [family_ld, crumbs] if fam_sensors else [crumbs]

        page_html = html_page(
            f"{family['name']} sensors",
            body,
            canonical=f"families/{family['slug']}/",
            description=family_description(family, len(fam_sensors)),
            json_ld=nodes,
        )
        out_path = output_dir / "families" / family["slug"] / "index.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as handle:
            handle.write(page_html)
