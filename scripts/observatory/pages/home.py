"""The homepage: /index.html."""

import hashlib
import html

from ..config import SITE_URL
from ..dates import _iso_date
from ..jsonld import (
    AUTHOR_LD,
    CATALOG_TERMSET_ID,
    CONTENT_LICENSE,
    ORGANIZATION_LD,
)
from ..layout import html_page
from ..render import blurb_text
from ..review import review_dates_discriminate, reviewed_newest_first
from ..taxonomy import (
    FAMILIES,
    FAMILY_BY_SLUG,
    LATENCY_X,
    ORACLE_Y,
    STACK_LAYERS,
    STACK_SCATTER,
    family_url,
)


def generate_index_page(sensors, output_dir):
    """Generate the homepage."""

    # Featured sensor
    featured = next((s for s in sensors if s["id"] == "SO-003"), sensors[0] if sensors else None)
    featured_family = FAMILY_BY_SLUG.get(featured.get("family", ""), {}) if featured else {}

    # Families grid
    families_grid = ""
    for f in FAMILIES:
        families_grid += f"""        <a href="{family_url(f["slug"])}" class="family-card">
          <span class="family-num">{f['num']}</span>
          <h3 class="family-name">{html.escape(f['name'])}</h3>
          <p class="family-question">"{html.escape(f['question'])}"</p>
          <p class="family-examples">{html.escape(f['examples'])}</p>
        </a>
"""

    # This list is "Recently reviewed" only when the review dates can actually
    # support that claim — see review_dates_discriminate(). While every entry
    # carries the same bulk stamp, sorting by it would be sorting by a
    # constant, so the section falls back to a fixed, spread-out starting set
    # and says so in its heading. When the stamps become real the ordering
    # switches over by itself; nothing has to be remembered.
    featured_slugs = [
        "type-checker", "mutation-testing", "fuzzing",
        "observability-events", "independent-review", "canary-analysis",
    ]
    sensors_by_slug = {s["slug"]: s for s in sensors}
    if review_dates_discriminate(sensors):
        recent_heading = "Recently reviewed"
        recent_sensors = reviewed_newest_first(sensors)[:len(featured_slugs)]
        show_review_date = True
    else:
        recent_heading = "Start here"
        recent_sensors = [
            sensors_by_slug[slug] for slug in featured_slugs
            if slug in sensors_by_slug
        ]
        show_review_date = False
    recent_html = ""
    for s in recent_sensors:
        fam = FAMILY_BY_SLUG.get(s.get("family", ""), {})
        reviewed = _iso_date(s.get("last_reviewed"))
        reviewed_html = (
            f'          <span class="entry-reviewed">reviewed {reviewed[:7]}</span>\n'
            if show_review_date and reviewed else ""
        )
        recent_html += f"""        <li class="entry">
          <span class="entry-family">{html.escape(fam.get('name', ''))}</span>
          <a href="/sensors/{s['slug']}/" class="entry-title wikilink">{html.escape(s['title'])}</a>
{reviewed_html}          <span class="entry-blurb">{html.escape(blurb_text(s.get('body_html', ''), 140))}</span>
        </li>
"""

    # Confidence scatter: feedback latency (x) against signal efficacy (y).
    # Two datasets — stack layers (hand-positioned) and individual sensors
    # (positioned from latency/oracle frontmatter, jittered to declutter).
    def scatter_layer_points():
        pts = ""
        for layer in STACK_LAYERS:
            pos = STACK_SCATTER.get(layer["slug"])
            if not pos:
                continue
            pts += f"""          <a href="/atlas/" class="scatter-point layer-point" style="left:{pos['x']}%;bottom:{pos['y']}%" data-label="{html.escape(layer['label'])}">
            <span class="scatter-dot"></span>
            <span class="scatter-tag">{html.escape(layer['label'])}</span>
          </a>
"""
        return pts.rstrip()

    def scatter_sensor_points():
        # Group by cell so overlapping sensors fan out deterministically
        cells = {}
        for s in sensors:
            x = LATENCY_X.get(s.get("latency", ""), 50)
            y = ORACLE_Y.get(s.get("oracle", ""), 50)
            cells.setdefault((x, y), []).append(s)
        pts = ""
        for (x, y), members in cells.items():
            n = len(members)
            for i, s in enumerate(members):
                # deterministic fan: hash the slug for a stable pseudo-random
                # offset within a disc that grows with cell population
                import math
                h = int(hashlib.md5(s["slug"].encode()).hexdigest(), 16)
                ang = (h % 360) * math.pi / 180
                rad = 2.2 * math.sqrt(i / max(n - 1, 1)) if n > 1 else 0
                spread = min(7, 1.5 + n * 0.55) if n > 1 else 0
                dx = math.cos(ang) * spread * rad / 2.2
                dy = math.sin(ang) * spread * rad / 2.2
                fam = FAMILY_BY_SLUG.get(s.get("family", ""), {}).get("name", "")
                fam_slug = s.get("family", "")
                fam_icon = FAMILY_BY_SLUG.get(fam_slug, {}).get("icon", "")
                pts += f"""          <a href="/sensors/{s['slug']}/" class="scatter-point sensor-point fam-{html.escape(fam_slug)}" style="left:{x + dx:.1f}%;bottom:{y + dy:.1f}%" data-label="{html.escape(s['title'])}" data-family="{html.escape(fam)}">
            <span class="scatter-dot" aria-hidden="true">{fam_icon}</span>
            <span class="scatter-tag">{html.escape(s['title'])}</span>
          </a>
"""
        return pts.rstrip()

    def scatter_legend():
        keys = ""
        for f in FAMILIES:
            keys += f"""          <span class="legend-key"><span class="legend-dot fam-{f['slug']}" aria-hidden="true">{f['icon']}</span>{html.escape(f['name'])}</span>
"""
        return keys.rstrip()

    scatter_html = f"""      <div class="scatter-toggle" role="group" aria-label="Scatter data">
        <button type="button" class="scatter-toggle-btn active" data-scatter="layers">Layers</button>
        <button type="button" class="scatter-toggle-btn" data-scatter="sensors">Sensors</button>
      </div>
      <div class="scatter-frame" data-scatter-mode="layers">
        <div class="scatter-y-label">efficacy of the signal</div>
        <div class="scatter-body">
          <div class="scatter-y-ticks">
            <span>definitive</span>
            <span>suggestive</span>
          </div>
          <div class="scatter-plot">
{scatter_layer_points()}
{scatter_sensor_points()}
          </div>
        </div>
        <div class="scatter-x-axis">
          <span>instant</span>
          <span>feedback latency →</span>
          <span>slow</span>
        </div>
        <p class="scatter-hint">Hover a point to name it. Click to open the entry.</p>
        <div class="scatter-legend">
{scatter_legend()}
        </div>
      </div>
      <details class="sr-only">
        <summary>Sensor list (latency × efficacy)</summary>
        <table>
          <thead><tr><th>Sensor</th><th>Family</th><th>Feedback latency</th><th>Efficacy (oracle)</th></tr></thead>
          <tbody>
{"".join(f'          <tr><td><a href="/sensors/{s["slug"]}/">{html.escape(s["title"])}</a></td><td>{html.escape(FAMILY_BY_SLUG.get(s.get("family",""),{}).get("name",""))}</td><td>{html.escape(s.get("latency",""))}</td><td>{html.escape(s.get("oracle",""))}</td></tr>\n' for s in sensors)}
          </tbody>
        </table>
      </details>"""

    body = f"""  <main id="main" tabindex="-1">
    <section class="hero">
      <div class="hero-inner">
        <p class="eyebrow">An industry resource</p>
        <h1 class="hero-title">
          What independent observations<br>
          <em>would cause us to believe</em><br>
          this software is correct?
        </h1>
        <p class="hero-lede">
          Software is increasingly an opaque artifact. We cannot — and often
          do not want to — fully understand every implementation. The Software
          Observatory is a catalog of <a href="/catalog/" class="wikilink">epistemic sensors</a>:
          the observable signals that reduce uncertainty about whether a system
          is correct, maintainable, and behaving as intended. Not "code quality
          metrics." Measurement instruments pointed at different failure modes.
        </p>
        <div class="hero-actions">
          <a href="/catalog/" class="btn btn-primary">Browse the catalog →</a>
          <a href="/atlas/" class="btn btn-ghost">Open the atlas</a>
        </div>
      </div>
      <div class="hero-visual" aria-hidden="true">
        <svg viewBox="0 24 400 336" class="hero-instruments">
          <g class="stars">
            <circle cx="52" cy="70" r="1.4"/>
            <circle cx="118" cy="128" r="1.1" class="twinkle"/>
            <circle cx="40" cy="208" r="1.5"/>
            <circle cx="96" cy="44" r="1.1" class="twinkle-b"/>
            <circle cx="338" cy="82" r="1.4"/>
            <circle cx="372" cy="202" r="1.1" class="twinkle"/>
            <circle cx="300" cy="156" r="1.2"/>
            <circle cx="276" cy="38" r="1.3" class="twinkle-b"/>
            <circle cx="150" cy="232" r="1.0"/>
            <circle cx="356" cy="262" r="1.2" class="twinkle"/>
            <circle cx="64" cy="148" r="1.0"/>
            <circle cx="176" cy="62" r="1.2" class="twinkle-b"/>
          </g>
          <circle cx="218" cy="112" r="64" class="halo"/>
          <circle cx="218" cy="112" r="46" class="artifact"/>

          <line x1="130.41" y1="242.03" x2="192.3" y2="150.15" class="sight-far" stroke-dasharray="5 7"/>
          <line x1="207.64" y1="193.91" x2="212.23" y2="157.64" class="sight"/>
          <line x1="284.59" y1="252.42" x2="237.71" y2="153.56" class="sight-far" stroke-dasharray="5 7"/>
          <path d="M-4 348 Q 200 318 404 340" class="ridge"/>

          <defs>
            <clipPath id="a0-slit"><path d="M114.79 310.24 A26.79 44 0 0 0 88 261 A39.03 44 0 0 1 127.03 308.05 A44 6.6 0 0 1 114.79 310.24 Z"/></clipPath>
            <clipPath id="a0-shell"><path d="M44 305 A44 44 0 0 1 132 305 A44 6.6 0 0 1 44 305 Z"/></clipPath>
            <clipPath id="a0-out">
              <rect x="-312" y="-134.84" width="800" height="400"
                    transform="rotate(33.96 88 305)"/>
            </clipPath>
          </defs>
          <path d="M49.28 305 L49.28 339 L126.72 339 L126.72 305 Z" class="drum"/>
          <line x1="49.28" y1="339" x2="126.72" y2="339" class="edge"/>
          <path d="M78.71 339 L78.71 330.61 A9.29 9.29 0 0 1 97.29 330.61 L97.29 339" class="detail"/>
          <path d="M49.28 306.98 A38.72 6.6 0 0 0 126.72 306.98" class="detail"/>
          <path d="M44 305 A44 44 0 0 1 132 305 A44 6.6 0 0 1 44 305 Z" class="shell"/>
          <g clip-path="url(#a0-shell)" class="seam">
            <path d="M88 261 A42.69 44 0 0 0 45.31 306.6"/>
            <path d="M88 261 A33.71 44 0 0 0 54.29 309.24"/>
            <path d="M88 261 A17.9 44 0 0 0 70.1 311.03"/>
            <path d="M88 261 A1.54 44 0 0 1 89.54 311.6"/>
            <path d="M88 261 A20.66 44 0 0 1 108.66 310.83"/>
            <path d="M74.4 263.15 A13.6 2.04 0 0 0 101.6 263.15"/>
            <path d="M54.29 276.72 A33.71 5.06 0 0 0 121.71 276.72"/>
          </g>
          <path d="M114.79 310.24 A26.79 44 0 0 0 88 261 A39.03 44 0 0 1 127.03 308.05 A44 6.6 0 0 1 114.79 310.24 Z" class="slit"/>
          <g clip-path="url(#a0-slit)">
            <g transform="rotate(33.96 88 305)">
              <path d="M84.15 229.08 L91.85 229.08 L91.39 307.2 L84.61 307.2 Z" class="tube-in"/>
              <line x1="84.15" y1="250.34" x2="91.85" y2="250.34" class="tube-band"/>
              <line x1="84.38" y1="273.11" x2="91.62" y2="273.11" class="tube-band"/>
            </g>
            <ellipse cx="130.41" cy="242.03" rx="3.85" ry="1.63" class="aperture"
                     transform="rotate(33.96 130.41 242.03)"/>
          </g>
          <g clip-path="url(#a0-out)"><g transform="rotate(33.96 88 305)">
              <path d="M84.15 229.08 L91.85 229.08 L91.39 318.2 L84.61 318.2 Z" class="tube"/>
              <line x1="84.15" y1="250.34" x2="91.85" y2="250.34" class="tube-band"/>
              <line x1="84.38" y1="273.11" x2="91.62" y2="273.11" class="tube-band"/>
            </g>
            <ellipse cx="130.41" cy="242.03" rx="3.85" ry="1.63" class="aperture"
                     transform="rotate(33.96 130.41 242.03)"/></g>
          <g clip-path="url(#a0-shell)">
            <path d="M88 261 A26.79 44 0 0 1 114.79 310.24" class="shutter"/>
            <path d="M88 261 A39.03 44 0 0 1 127.03 308.05" class="shutter"/>
            <path d="M88 261 A22.33 44 0 0 1 110.33 310.69" class="shutter-back"/>
            <path d="M88 261 A41.21 44 0 0 1 129.21 307.31" class="shutter-back"/>
          </g>
          <defs>
            <clipPath id="a1-slit"><path d="M217.21 294.74 A21.21 62 0 0 0 196 224 A39.85 62 0 0 1 235.85 293.12 A62 9.3 0 0 1 217.21 294.74 Z"/></clipPath>
            <clipPath id="a1-shell"><path d="M134 286 A62 62 0 0 1 258 286 A62 9.3 0 0 1 134 286 Z"/></clipPath>
            <clipPath id="a1-out">
              <rect x="-204" y="-174.59" width="800" height="400"
                    transform="rotate(7.21 196 286)"/>
            </clipPath>
          </defs>
          <path d="M141.44 286 L141.44 332 L250.56 332 L250.56 286 Z" class="drum"/>
          <line x1="141.44" y1="332" x2="250.56" y2="332" class="edge"/>
          <path d="M182.91 332 L182.91 321.17 A13.09 13.09 0 0 1 209.09 321.17 L209.09 332" class="detail"/>
          <path d="M141.44 288.79 A54.56 9.3 0 0 0 250.56 288.79" class="detail"/>
          <path d="M138.17 303.67 A57.83 10.23 0 0 0 253.83 303.67" class="detail"/>
          <line x1="138.17" y1="303.67" x2="138.17" y2="295.3" class="detail"/>
          <line x1="154.69" y1="310.83" x2="154.69" y2="302.46" class="detail"/>
          <line x1="171.21" y1="312.91" x2="171.21" y2="304.54" class="detail"/>
          <line x1="187.74" y1="313.8" x2="187.74" y2="305.43" class="detail"/>
          <line x1="204.26" y1="313.8" x2="204.26" y2="305.43" class="detail"/>
          <line x1="220.79" y1="312.91" x2="220.79" y2="304.54" class="detail"/>
          <line x1="237.31" y1="310.83" x2="237.31" y2="302.46" class="detail"/>
          <line x1="253.83" y1="303.67" x2="253.83" y2="295.3" class="detail"/>
          <path d="M134 286 A62 62 0 0 1 258 286 A62 9.3 0 0 1 134 286 Z" class="shell"/>
          <g clip-path="url(#a1-shell)" class="seam">
            <path d="M196 224 A60.16 62 0 0 0 135.84 288.25"/>
            <path d="M196 224 A47.49 62 0 0 0 148.51 291.98"/>
            <path d="M196 224 A25.22 62 0 0 0 170.78 294.5"/>
            <path d="M196 224 A2.16 62 0 0 1 198.16 295.29"/>
            <path d="M196 224 A50.16 62 0 0 1 246.16 291.47"/>
            <path d="M181 225.84 A15 2.25 0 0 0 211 225.84"/>
            <path d="M154.51 239.93 A41.49 6.22 0 0 0 237.49 239.93"/>
            <path d="M139.36 260.78 A56.64 8.5 0 0 0 252.64 260.78"/>
          </g>
          <path d="M217.21 294.74 A21.21 62 0 0 0 196 224 A39.85 62 0 0 1 235.85 293.12 A62 9.3 0 0 1 217.21 294.74 Z" class="slit"/>
          <g clip-path="url(#a1-slit)">
            <g transform="rotate(7.21 196 286)">
              <path d="M190.57 193.17 L201.43 193.17 L200.77 289.1 L191.23 289.1 Z" class="tube-in"/>
              <line x1="190.57" y1="219.16" x2="201.43" y2="219.16" class="tube-band"/>
              <line x1="190.9" y1="247.01" x2="201.1" y2="247.01" class="tube-band"/>
            </g>
            <ellipse cx="207.64" cy="193.91" rx="5.42" ry="1.15" class="aperture"
                     transform="rotate(7.21 207.64 193.91)"/>
          </g>
          <g clip-path="url(#a1-out)"><g transform="rotate(7.21 196 286)">
              <path d="M190.57 193.17 L201.43 193.17 L200.77 304.6 L191.23 304.6 Z" class="tube"/>
              <line x1="190.57" y1="219.16" x2="201.43" y2="219.16" class="tube-band"/>
              <line x1="190.9" y1="247.01" x2="201.1" y2="247.01" class="tube-band"/>
            </g>
            <ellipse cx="207.64" cy="193.91" rx="5.42" ry="1.15" class="aperture"
                     transform="rotate(7.21 207.64 193.91)"/></g>
          <g clip-path="url(#a1-shell)">
            <path d="M196 224 A21.21 62 0 0 1 217.21 294.74" class="shutter"/>
            <path d="M196 224 A39.85 62 0 0 1 235.85 293.12" class="shutter"/>
            <path d="M196 224 A13.95 62 0 0 1 209.95 295.06" class="shutter-back"/>
            <path d="M196 224 A45.34 62 0 0 1 241.34 292.34" class="shutter-back"/>
          </g>
          <defs>
            <clipPath id="a2-slit"><path d="M280.7 308.59 A29.3 34 0 0 1 310 272 A18.27 34 0 0 0 291.73 310.3 A34 5.1 0 0 1 280.7 308.59 Z"/></clipPath>
            <clipPath id="a2-shell"><path d="M276 306 A34 34 0 0 1 344 306 A34 5.1 0 0 1 276 306 Z"/></clipPath>
            <clipPath id="a2-out">
              <rect x="-90" y="-125.42" width="800" height="400"
                    transform="rotate(-25.37 310 306)"/>
            </clipPath>
          </defs>
          <path d="M280.08 306 L280.08 334 L339.92 334 L339.92 306 Z" class="drum"/>
          <line x1="280.08" y1="334" x2="339.92" y2="334" class="edge"/>
          <path d="M280.08 307.53 A29.92 5.1 0 0 0 339.92 307.53" class="detail"/>
          <path d="M276 306 A34 34 0 0 1 344 306 A34 5.1 0 0 1 276 306 Z" class="shell"/>
          <g clip-path="url(#a2-shell)" class="seam">
            <path d="M310 272 A32.99 34 0 0 0 277.01 307.23"/>
            <path d="M310 272 A1.19 34 0 0 1 311.19 311.1"/>
            <path d="M310 272 A15.96 34 0 0 1 325.96 310.5"/>
            <path d="M310 272 A27.51 34 0 0 1 337.51 309"/>
            <path d="M299.49 273.66 A10.51 1.58 0 0 0 320.51 273.66"/>
            <path d="M283.95 284.15 A26.05 3.91 0 0 0 336.05 284.15"/>
          </g>
          <path d="M280.7 308.59 A29.3 34 0 0 1 310 272 A18.27 34 0 0 0 291.73 310.3 A34 5.1 0 0 1 280.7 308.59 Z" class="slit"/>
          <g clip-path="url(#a2-slit)">
            <g transform="rotate(-25.37 310 306)">
              <path d="M307.02 246.7 L312.98 246.7 L312.62 307.7 L307.38 307.7 Z" class="tube-in"/>
              <line x1="307.02" y1="263.31" x2="312.98" y2="263.31" class="tube-band"/>
              <line x1="307.2" y1="281.1" x2="312.8" y2="281.1" class="tube-band"/>
            </g>
            <ellipse cx="284.59" cy="252.42" rx="2.97" ry="1.14" class="aperture"
                     transform="rotate(-25.37 284.59 252.42)"/>
          </g>
          <g clip-path="url(#a2-out)"><g transform="rotate(-25.37 310 306)">
              <path d="M307.02 246.7 L312.98 246.7 L312.62 316.2 L307.38 316.2 Z" class="tube"/>
              <line x1="307.02" y1="263.31" x2="312.98" y2="263.31" class="tube-band"/>
              <line x1="307.2" y1="281.1" x2="312.8" y2="281.1" class="tube-band"/>
            </g>
            <ellipse cx="284.59" cy="252.42" rx="2.97" ry="1.14" class="aperture"
                     transform="rotate(-25.37 284.59 252.42)"/></g>
          <g clip-path="url(#a2-shell)">
            <path d="M310 272 A29.3 34 0 0 0 280.7 308.59" class="shutter"/>
            <path d="M310 272 A18.27 34 0 0 0 291.73 310.3" class="shutter"/>
            <path d="M310 272 A31.18 34 0 0 0 278.82 308.03" class="shutter-back"/>
            <path d="M310 272 A14.64 34 0 0 0 295.36 310.6" class="shutter-back"/>
          </g>
        </svg>
      </div>
    </section>

    <section class="core-insight">
      <blockquote class="big-quote">
        <p>
          <a href="/glossary/#no-single-sensor" class="wikilink">No single sensor measures correctness</a>. Coverage measures execution.
          <a href="/sensors/mutation-testing/" class="wikilink">Mutation testing</a> measures
          test sensitivity. <a href="/sensors/type-checker/" class="wikilink">Types</a> measure
          a particular class of structural inconsistency.
          <a href="/sensors/contract-tests/" class="wikilink">Contracts</a> measure boundary
          assumptions. <a href="/sensors/observability-events/" class="wikilink">Observability</a>
          measures what actually happened and preserves enough dimensionality
          to investigate unknown unknowns.
        </p>
        <p>They are all measurement instruments pointed at different failure modes.</p>
      </blockquote>
    </section>

    <section class="families-section">
      <h2 class="section-heading">{len(FAMILIES)} sensor families</h2>
      <p class="section-lede">
        The catalog is organized into {len(FAMILIES)} families, each asking a different
        question about the system. Together, they form a mesh of independent
        evidence — no single sensor is sufficient, but the combination
        constrains uncertainty from multiple directions.
      </p>
      <div class="families-grid">
{families_grid.rstrip()}
      </div>
    </section>

    <section class="stack-preview" id="confidence-stack">
      <h2 class="section-heading">The confidence landscape</h2>
      <p class="section-lede">
        No single sensor is sufficient, so there is no total ordering across
        sensors — no "best" sensor. But each <em>dimension</em> (oracle
        strength, latency, scope) is a partial order, and the atlas's
        left-to-right axis is <em>time</em>, not quality. Each one trades
        <em>feedback latency</em> — how long you wait for the signal —
        against <em>efficacy</em>: how much the signal can actually tell
        you. Compilation is instant and definitive about validity; user
        outcomes are slow and definitive about everything that matters. Most
        sensors live somewhere in between.
      </p>
{scatter_html}
      <div class="stack-cta">
        <a href="/atlas/" class="btn btn-ghost">Open the atlas →</a>
      </div>
    </section>

    <section class="featured-signal">
      <div class="featured-meta">
        <span class="tag tag-family">{html.escape(featured_family.get('name', ''))}</span>
        <span class="tag tag-confidence">High oracle strength</span>
      </div>
      <h2 class="featured-title"><a href="/sensors/{featured['slug']}/" class="wikilink" style="border-bottom:none">{html.escape(featured['title'])}</a></h2>
      <p class="featured-blurb">
        Take <code>if user.is_admin: allow()</code> and mutate it to
        <code>if not user.is_admin: allow()</code>. If all your tests still
        pass, your tests did not actually establish the behavior you thought
        you established. Mutation testing is a sensor of test
        <em>sensitivity</em> rather than test <em>presence</em>.
      </p>
      <div class="featured-cta">
        <a href="/sensors/{featured['slug']}/">Read the full entry →</a>
      </div>
    </section>

    <section class="recent">
      <h2 class="section-heading">{recent_heading}</h2>
      <ul class="entry-list">
{recent_html.rstrip()}
      </ul>
    </section>
  </main>"""

    website_ld = [
        {
            "@type": "WebSite",
            "@id": f"{SITE_URL}/#website",
            "name": "Software Observatory",
            "url": SITE_URL,
            "description": "A catalog of epistemic sensors for software correctness.",
            "inLanguage": "en",
            "license": CONTENT_LICENSE,
            "author": {"@id": AUTHOR_LD["@id"]},
            "publisher": {"@id": ORGANIZATION_LD["@id"]},
            "hasPart": {"@id": CATALOG_TERMSET_ID},
        },
        ORGANIZATION_LD,
        AUTHOR_LD,
    ]

    page_html = html_page(
        "Software Observatory", body, canonical="", json_ld=website_ld,
        description=(
            f"{len(sensors)} epistemic sensors for software correctness: the "
            "signals that tell you whether a system works, what each one can "
            "detect, and what it cannot."
        ),
    )
    out_path = output_dir / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)
