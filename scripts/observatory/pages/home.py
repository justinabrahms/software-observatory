"""The homepage: /index.html."""


from ..config import SITE_URL
from ..jsonld import (
    AUTHOR_LD,
    CATALOG_TERMSET_ID,
    CONTENT_LICENSE,
    ORGANIZATION_LD,
)
from ..layout import html_page


def generate_index_page(sensors, output_dir):
    """Generate the homepage."""

    body = f"""  <main id="main" tabindex="-1">
    <section class="hero">
      <div class="hero-inner">
        <p class="eyebrow">A thought experiment about software quality</p>
        <h1 class="hero-title">
          If you couldn't read the source code,<br>
          <em>how would you know it was good?</em>
        </h1>
        <p class="hero-lede">
          Treat the software as an opaque artifact. You can still observe
          whether a test notices a changed behavior, whether a contract holds,
          and what happens to real users. Each signal answers a different
          question. The Observatory maps what those signals can tell us — and
          what they leave unknown.
        </p>
        <div class="hero-actions">
          <a href="#without-source" class="btn btn-primary">Try the thought experiment ↓</a>
          <a href="/catalog/" class="btn btn-ghost">Explore the catalog</a>
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

    <section class="thought-experiment" id="without-source" aria-labelledby="thought-title">
      <div class="thought-intro">
        <p class="eyebrow">Without the source</p>
        <h2 id="thought-title">What would change your mind?</h2>
        <p>Someone says the system works. You cannot inspect its implementation.
          What could you observe that would make you more confident?</p>
        <p>No single observation settles the question. Each one rules out a
          particular way the software could be wrong.</p>
      </div>
      <div class="thought-observations">
        <a href="/sensors/mutation-testing/" class="thought-observation">
          <span class="thought-number">01 / TEST SENSITIVITY</span>
          <h3>A changed condition makes a test fail.</h3>
          <p>The suite notices that behavior changed. It cannot tell you whether
            the intended behavior was right in the first place.</p>
          <span class="thought-link">Examine mutation testing →</span>
        </a>
        <a href="/sensors/contract-tests/" class="thought-observation">
          <span class="thought-number">02 / BOUNDARY AGREEMENT</span>
          <h3>A consumer's contract still holds.</h3>
          <p>One system still meets another's expectations. The rest of the
            workflow may still be wrong.</p>
          <span class="thought-link">Examine contract tests →</span>
        </a>
        <a href="/sensors/canary-analysis/" class="thought-observation">
          <span class="thought-number">03 / LIVE BEHAVIOR</span>
          <h3>A canary behaves normally under real traffic.</h3>
          <p>The release has not shifted the signals you watch. That cannot
            establish that users get the outcome they need.</p>
          <span class="thought-link">Examine canary analysis →</span>
        </a>
        <div class="thought-next">
          <p>Which observations would you want <em>together</em>?</p>
          <a href="/catalog/" class="btn btn-primary">Explore all {len(sensors)} sensors →</a>
          <a href="/framework/#combining-sensors" class="thought-framework">How the signals combine</a>
        </div>
      </div>
    </section>

    <section class="evidence-case" aria-labelledby="evidence-case-title">
      <div class="evidence-case-story">
        <p class="eyebrow">A worked example</p>
        <h2 id="evidence-case-title">What does a successful payment response tell us?</h2>
        <p>Suppose the payment endpoint reports success, but the order never
          enters the paid state. The response tells us the endpoint answered.
          It does not establish that the business promise was kept.</p>
        <a href="/playbook/prod-says-200-answer-was-wrong/" class="evidence-case-link">Read the full example →</a>
      </div>
      <div class="evidence-case-readings">
        <div class="evidence-case-reading">
          <span class="evidence-case-label">OBSERVED</span>
          <p>The payment endpoint responded successfully.</p>
        </div>
        <div class="evidence-case-reading">
          <span class="evidence-case-label">STILL UNKNOWN</span>
          <p>Whether the order entered the paid state.</p>
        </div>
        <div class="evidence-case-reading">
          <span class="evidence-case-label">A SECOND OBSERVATION</span>
          <p>Check that every payment event has an order in state paid
            within an hour.</p>
          <a href="/sensors/business-invariants/" class="wikilink">Examine business invariants →</a>
        </div>
      </div>
    </section>

    <section class="confidence-story" id="confidence-stack" aria-labelledby="confidence-title">
      <div class="confidence-intro">
        <p class="eyebrow">The confidence stack</p>
        <h2 id="confidence-title">You do not get one verdict.<br><em>You build a case.</em></h2>
        <p>Evidence arrives at different times and from different vantage
          points. Each observation narrows a different doubt. A green result
          from one says nothing about the claims measured by the others.</p>
      </div>
      <ol class="confidence-steps">
        <li>
          <span class="confidence-step-num">01 / BEFORE IT RUNS</span>
          <h3>Is the artifact internally coherent?</h3>
          <p>A <a href="/sensors/type-checker/" class="wikilink">type checker</a>
            catches contradictions in the program. It cannot know whether the
            behavior is useful or intended.</p>
        </li>
        <li>
          <span class="confidence-step-num">02 / BEFORE IT SHIPS</span>
          <h3>Does the behavior meet a stated expectation?</h3>
          <p><a href="/sensors/contract-tests/" class="wikilink">Contract tests</a>
            check a boundary another system depends on. They say nothing about
            expectations nobody stated.</p>
        </li>
        <li>
          <span class="confidence-step-num">03 / WHILE IT RUNS</span>
          <h3>What happened outside the test environment?</h3>
          <p><a href="/sensors/observability-events/" class="wikilink">Events</a>
            and <a href="/sensors/canary-analysis/" class="wikilink">canaries</a>
            show live behavior. They only see what you chose to record and compare.</p>
        </li>
        <li>
          <span class="confidence-step-num">04 / AFTER USERS MEET IT</span>
          <h3>Did the system keep its promise?</h3>
          <p><a href="/sensors/business-invariants/" class="wikilink">Business invariants</a>
            test outcomes the domain requires. A pass covers those promises,
            in that window, and no others.</p>
        </li>
      </ol>
      <a href="/atlas/" class="confidence-atlas-link">See all layers in the atlas →</a>
    </section>

    <section class="research-next" aria-labelledby="research-next-title">
      <p class="eyebrow">Continue the inquiry</p>
      <h2 id="research-next-title">What would convince you about your system?</h2>
      <p>The catalog has {len(sensors)} instruments. Each entry says what it can
        observe, what it cannot detect, and what evidence it produces. Start
        with a claim you want to test, then look for observations that do not
        share the same blind spot.</p>
      <div class="research-next-actions">
        <a href="/catalog/" class="btn btn-primary">Explore the catalog →</a>
        <a href="/what-each-sensor-proves/" class="btn btn-ghost">Start from a doubt</a>
      </div>
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
            "If you could not read the source code, how would you know the "
            f"software was good? Explore {len(sensors)} independent signals, "
            "what each reveals, and what remains unknown."
        ),
    )
    out_path = output_dir / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)
