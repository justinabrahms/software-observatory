"""The privacy page: /privacy/."""

from ..layout import html_page
from ..jsonld import breadcrumb_ld, page_ld


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

    description = (
        "A static site with cookieless, self-hosted analytics: what is "
        "counted, what is never collected, and what leaves your browser."
    )
    page_html = html_page(
        "Privacy", body, canonical="privacy/",
        description=description,
        json_ld=[
            page_ld("WebPage", "Privacy", "/privacy/", description),
            breadcrumb_ld([("Privacy", None)]),
        ],
    )
    out_path = output_dir / "privacy" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)
