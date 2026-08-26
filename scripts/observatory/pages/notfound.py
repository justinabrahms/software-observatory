"""The 404 page: /404.html."""

from ..layout import html_page
from ..taxonomy import FAMILIES


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
      Search index: <a href="/search-index.json">/search-index.json</a>.
      Structured catalog: <a href="/sensors.json">/sensors.json</a>.
      Agent instructions: <a href="/llms.txt">/llms.txt</a>,
      full catalog in one file: <a href="/llms-full.txt">/llms-full.txt</a>.
    </p>
  </div>"""
    page_html = html_page(
        "Not found", body, canonical="404.html",
        description=(
            f"That page doesn't exist. Routes back into the catalog of "
            f"{len(sensors)} sensors, the atlas, the glossary, and the "
            "machine-readable surfaces."
        ),
    )
    with open(output_dir / "404.html", "w") as f:
        f.write(page_html)
