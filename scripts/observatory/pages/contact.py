"""The contact page: /contact/."""

from ..layout import html_page
from ..jsonld import breadcrumb_ld, page_ld


def generate_contact_page(output_dir):
    """Generate the contact page."""
    body = """  <section class="page-header page-header--reading">
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

    description = (
        "How to reach the Observatory — corrections, missing sensors, "
        "citations to add, and where to file each kind of change."
    )
    page_html = html_page(
        "Contact", body, canonical="contact/",
        description=description,
        json_ld=[
            page_ld("ContactPage", "Contact", "/contact/", description),
            breadcrumb_ld([("Contact", None)]),
        ],
    )
    out_path = output_dir / "contact" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)
