"""One sensor entry page: /sensors/<slug>/."""

import html
import re

from vocabulary import REFERENCE_KINDS_WITH_OWN_SECTION

from ..components import note_hover_html, provisional_note_html
from ..config import SITE_URL
from ..content import resolve_see_also, sensor_og_image
from ..dates import _iso_date
from ..jsonld import (
    AUTHOR_LD,
    CATALOG_TERMSET_ID,
    CONTENT_LICENSE,
    ORGANIZATION_LD,
    breadcrumb_ld,
    family_termset_id,
    sensor_rating_properties,
)
from ..layout import html_page
from ..render import blurb_text
from ..review import review_dd_html
from ..taxonomy import FAMILY_BY_SLUG, LATENCY_WORDS, TIER_LABELS, family_url


def generate_sensor_page(sensor, backlinks, sensors_by_id, families_by_slug,
                         output_dir, published=None, as_of=None):
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
        others = [r for r in references if r.get("kind") not in REFERENCE_KINDS_WITH_OWN_SECTION]

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
                cat_links += f'          <a href="{family_url(fam["slug"])}" class="cat-link">{html.escape(cat)}</a>\n'
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
                url = family_url(fam['slug'])
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

    # One trail, two renderings: the visible breadcrumb and the
    # BreadcrumbList below are generated from this list.
    breadcrumb_trail = [("Catalog", "/catalog/")]
    if family_slug:
        breadcrumb_trail.append((family_name, family_url(family_slug)))
    breadcrumb_trail.append((sensor["title"], None))
    breadcrumb_html = " › ".join(
        f'<a href="{path}">{html.escape(name)}</a>' if path else html.escape(name)
        for name, path in breadcrumb_trail
    )

    body = f"""  <div class="wiki-layout">
    <article class="signal-detail">
      <p class="breadcrumb">{breadcrumb_html}</p>

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
          <dt>Family</dt>           <dd><a href="{family_url(family_slug)}" class="wikilink">{html.escape(family_name)}</a></dd>
          <dt>Oracle</dt>          <dd>{html.escape(sensor.get('oracle', '').title())}{note_hover_html(sensor.get('oracle_note'))}</dd>
          <dt>Independence</dt>     <dd>{html.escape(sensor.get('independence', '').title())}{note_hover_html(sensor.get('independence_note'))}</dd>{provisional_note_html(sensor.get('provisional'))}
          <dt>Scope</dt>           <dd>{html.escape(sensor.get('scope', '').replace('-', ' ').title())}{note_hover_html(sensor.get('scope_note'))}</dd>
          <dt>Latency</dt>         <dd>{html.escape(LATENCY_WORDS[sensor.get('latency', '')].capitalize())}{note_hover_html(sensor.get('latency_note'))}</dd>
          <dt>Actionability</dt>   <dd>{html.escape(sensor.get('actionability', '').title())}{note_hover_html(sensor.get('actionability_note'))}</dd>
          <dt>Type</dt>             <dd>{html.escape(sensor.get('type', '').title())}{note_hover_html(sensor.get('type_note'))}</dd>
          <dt>Entry ID</dt>        <dd>{html.escape(sensor.get('id', ''))}</dd>
          <dt>Reviewed</dt>        <dd>{review_dd_html(sensor, as_of)}</dd>
        </dl>
      </div>
{backlink_html}
{cat_sidebar_html}
    </aside>
  </div>"""

    # The catalog-card blurb is already a self-contained opening sentence
    # about this sensor specifically — exactly what a search snippet or a
    # Slack unfurl should say.
    # Structured data. The entry is both an article and a term in the
    # catalog's vocabulary, so it is typed as both; the breadcrumb is built
    # from the same trail that renders the visible one above.
    blurb = blurb_text(sensor.get("body_html", ""), 200)
    date_published = (published or {}).get(sensor["slug"]) or _iso_date(
        sensor.get("last_reviewed")
    )
    article_ld = {
        "@type": ["TechArticle", "DefinedTerm"],
        "@id": f"{SITE_URL}/sensors/{sensor['slug']}/#entry",
        "headline": sensor["title"],
        "name": sensor["title"],
        "description": blurb,
        "termCode": sensor.get("id", ""),
        "url": f"{SITE_URL}/sensors/{sensor['slug']}/",
        "mainEntityOfPage": f"{SITE_URL}/sensors/{sensor['slug']}/",
        "inLanguage": "en",
        "license": CONTENT_LICENSE,
        "author": AUTHOR_LD,
        "publisher": {"@id": ORGANIZATION_LD["@id"]},
        "inDefinedTermSet": {"@id": CATALOG_TERMSET_ID},
        "isPartOf": {"@id": CATALOG_TERMSET_ID},
    }
    if date_published:
        article_ld["datePublished"] = date_published
    reviewed = _iso_date(sensor.get("last_reviewed"))
    if reviewed:
        article_ld["dateModified"] = reviewed
    if family_slug:
        article_ld["about"] = {
            "@type": "Thing",
            "@id": family_termset_id(family_slug),
            "name": family_name,
            "url": f"{SITE_URL}{family_url(family_slug)}",
        }
    if categories:
        article_ld["keywords"] = ", ".join(categories)
    # oracle/independence/scope/latency/actionability/type as PropertyValues
    # whose propertyID resolves to the dimension's definition on /framework/.
    # Without this the ratings are six bare strings with nothing saying what
    # they are values OF.
    ratings = sensor_rating_properties(sensor)
    if ratings:
        article_ld["additionalProperty"] = ratings

    page_html = html_page(
        f"{sensor['title']}",
        body,
        canonical=f"sensors/{sensor['slug']}/",
        description=blurb,
        og_image=sensor_og_image(sensor["slug"]),
        og_type="article",
        json_ld=[article_ld, breadcrumb_ld(breadcrumb_trail)],
    )
    out_path = output_dir / "sensors" / sensor["slug"] / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)
