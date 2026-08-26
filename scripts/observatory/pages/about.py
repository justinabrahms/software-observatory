"""The about page: /about/."""

from ..layout import html_page
from ..jsonld import breadcrumb_ld, page_ld
from ..taxonomy import FAMILIES


def generate_about_page(output_dir):
    """Generate the about page."""

    body = f"""  <section class="page-header page-header--reading">
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
      Software is increasingly an <a href="/glossary/#opaque-artifact" class="wikilink">opaque
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
      <a href="/catalog/" class="wikilink">epistemic sensors</a>. Their
      job is to reduce uncertainty about a system that we cannot — or
      increasingly do not want to — fully understand.
    </p>

    <h2>The framework</h2>
    <p>
      The catalog is organized into <a href="/catalog/" class="wikilink">{len(FAMILIES)}
      families</a> of sensors, each asking a different question about the
      system. Every sensor is characterized along
      <a href="/framework/" class="wikilink">six dimensions</a>:
      oracle strength, independence, scope, feedback latency,
      actionability, and predictive vs retrospective. The
      <a href="/atlas/" class="wikilink">atlas</a> arranges them as a
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

    <h2>Maintained by</h2>
    <p>
      The Software Observatory is built and maintained by
      <a href="https://justin.abrah.ms/" class="wikilink">Justin Abrahms</a>
      — a principal engineer working on agent-assisted software delivery and
      the sensors that let us assess what agents produce. The catalog grows
      out of that work: if agents can produce software faster than humans can
      inspect it, code review cannot remain the primary mechanism for
      establishing quality, and we need a living catalog of the signals we
      can use instead.
    </p>
    <p>
      Reach out via <a href="mailto:justin@abrah.ms" class="wikilink">email</a>,
      <a href="https://bsky.app/profile/justin.abrah.ms" class="wikilink">Bluesky</a>,
      or <a href="https://github.com/justinabrahms" class="wikilink">GitHub</a>.
      Errors and gaps in the catalog are best filed in the
      <a href="https://github.com/justinabrahms/software-observatory/issues"
      class="wikilink">issue tracker</a>.
    </p>

    <h2>Contributing</h2>
    <p>
      The Observatory is meant to be an open reference, and the field should
      be able to correct it. The catalog applies a producer-evaluator
      principle to itself: the author shouldn't be the only evaluator.
      Independent review of the content is welcome and explicitly invited.
    </p>
    <p>
      The best way to contribute right now:
    </p>
    <ul>
      <li>
        <strong>File an issue</strong> at the
        <a href="https://github.com/justinabrahms/software-observatory/issues"
        class="wikilink">GitHub tracker</a> for a factual error, a missing
        sensor, a taxonomy challenge, or a depth gap.
      </li>
      <li>
        <strong>Open a pull request</strong> with a new or revised
        <code>content/sensors/*.md</code>. Keep the opening paragraph
        self-contained; match the frontmatter shape in
        <a href="https://github.com/justinabrahms/software-observatory/blob/main/CONTRIBUTING.md"
        class="wikilink">CONTRIBUTING.md</a>; run the build and the link
        checker before submitting.
      </li>
      <li>
        <strong>Propose a family change</strong> (adding, renumbering, or
        reclassifying a family) via an issue first — these touch
        <code>FAMILIES</code> in <code>build.py</code> and the color tokens
        in <code>css/observatory.css</code>, so they're worth discussing
        before the work.
      </li>
    </ul>
    <p>
      See
      <a href="https://github.com/justinabrahms/software-observatory/blob/main/CONTRIBUTING.md"
      class="wikilink">CONTRIBUTING.md</a>
      in the repository for the full guide — frontmatter shape, the
      relative-link gotcha, build and link-check commands, and style
      conventions.
    </p>

    <h2>License</h2>
    <p>
      All content on the Software Observatory is published under
      <a href="https://creativecommons.org/licenses/by-sa/4.0/" class="wikilink">CC BY-SA 4.0</a>.
      You are free to share and adapt the material for any purpose,
      provided you give appropriate credit and distribute contributions
      under the same license.
    </p>
  </div>"""

    description = (
        "Why the Observatory exists, who maintains it, how entries are "
        "researched and cited, and how to propose a sensor the catalog "
        "is missing."
    )
    page_html = html_page(
        "About", body, canonical="about/",
        description=description,
        json_ld=[
            page_ld("AboutPage", "About", "/about/", description),
            breadcrumb_ld([("About", None)]),
        ],
    )
    out_path = output_dir / "about" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)
