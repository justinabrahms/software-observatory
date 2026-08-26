"""The framework essay: /framework/."""

from ..layout import html_page
from ..dates import catalog_as_of
from ..jsonld import breadcrumb_ld, framework_termset_ld, page_ld


def generate_framework_page(sensors, output_dir):
    """Generate the framework page."""

    body = f"""  <section class="page-header">
    <p class="eyebrow">The Framework</p>
    <h1 class="page-title">Sensor Properties</h1>
    <p class="page-lede">
      We don't rank sensors as "good" or "bad." Every sensor is characterized
      along six dimensions that determine when it is useful, what it can and
      cannot detect, and what evidence it produces for an agent or human.
    </p>
  </section>

  <div class="framework-content">
    <div class="framework-intro">
      <p>
        The important thing is that <a href="/glossary/#no-single-sensor" class="wikilink">no single sensor measures
        <em>correctness</em></a>. Each sensor measures one thing. Coverage
        measures execution. Mutation measures test sensitivity. Types measure
        a particular class of structural inconsistency. Contracts measure
        boundary assumptions. Observability measures what actually happened
        and preserves enough dimensionality to investigate unknown unknowns.
      </p>
      <p>
        The question becomes: <em>what independent observations would cause us
        to update our belief that this software is correct?</em>
      </p>
    </div>

    <section class="property-detail">
      <span class="property-detail-num">01</span>
      <h2 class="property-detail-title">Oracle strength</h2>
      <p class="property-detail-question">How confidently does it know that something is wrong?</p>
      <div class="property-bars">
        <div class="bar-row"><span class="bar-label">compiler error</span><div class="bar-track"><div class="bar-fill" style="width:100%"></div></div><span class="bar-pct">maximum</span></div>
        <div class="bar-row"><span class="bar-label">type error</span><div class="bar-track"><div class="bar-fill" style="width:100%"></div></div><span class="bar-pct">maximum</span></div>
        <div class="bar-row"><span class="bar-label">test assertion</span><div class="bar-track"><div class="bar-fill" style="width:90%"></div></div><span class="bar-pct">high</span></div>
        <div class="bar-row"><span class="bar-label">mutation</span><div class="bar-track"><div class="bar-fill" style="width:90%"></div></div><span class="bar-pct">high</span></div>
        <div class="bar-row"><span class="bar-label">linter</span><div class="bar-track"><div class="bar-fill" style="width:80%"></div></div><span class="bar-pct">medium</span></div>
        <div class="bar-row"><span class="bar-label">coverage</span><div class="bar-track"><div class="bar-fill" style="width:40%"></div></div><span class="bar-pct">low</span></div>
        <div class="bar-row"><span class="bar-label">complexity</span><div class="bar-track"><div class="bar-fill" style="width:20%"></div></div><span class="bar-pct">minimum</span></div>
        <div class="bar-row"><span class="bar-label">code review</span><div class="bar-track"><div class="bar-fill" style="width:60%"></div></div><span class="bar-pct">medium</span></div>
      </div>
      <p>
        A compiler has maximum oracle strength because the implementation
        cannot argue with it. A complexity metric has minimum oracle
        strength because high complexity doesn't prove anything is wrong —
        it just suggests increased risk. The scale is ordinal (minimum →
        low → medium → high → maximum): a sensor two rungs up is stronger,
        not "twice as strong."
      </p>
      <div class="callout">
        <strong>Mutation's oracle is derivative.</strong> Mutation testing's
        high oracle is bounded by the test assertions underneath it — it
        only detects mutations that the test suite's oracle would catch.
        The strength reflects the test assertion's oracle, applied to a
        perturbation.
      </div>
      <div class="callout">
        <strong>"Type checker" spans a range.</strong> Structural type systems
        (TypeScript) catch a limited class of mismatches. Ownership and
        lifetime types (Rust) catch memory-safety bugs the compiler refuses
        to allow. Refinement types and SMT-backed verifiers (Dafny) can prove
        full correctness properties — the solver either confirms the
        invariant or produces a counterexample. The maximum rating applies
        to the strong end of that spectrum.
      </div>
    </section>

    <section class="property-detail">
      <span class="property-detail-num">02</span>
      <h2 class="property-detail-title">Independence</h2>
      <p class="property-detail-question">Can the thing being evaluated manipulate the sensor?</p>
      <p>
        This is extremely important for agents. A model writing
        <code>tests/</code> is allowed to write tests that make itself pass.
        The producer and evaluator should be separated wherever possible.
      </p>
      <div class="callout">
        An instruction saying "verify this" is weaker than a gate that
        literally refuses to proceed unless the verification command
        succeeded. Computational controls rather than prose rules.
      </div>
    </section>

    <section class="property-detail">
      <span class="property-detail-num">03</span>
      <h2 class="property-detail-title">Scope</h2>
      <p class="property-detail-question">What level of the system does it tell us about?</p>
      <div class="scope-ladder">
        <div class="scope-rung">Line <span class="scope-desc">A single line of code</span></div>
        <div class="scope-rung">Function <span class="scope-desc">A single function or method</span></div>
        <div class="scope-rung">Module <span class="scope-desc">A package or module</span></div>
        <div class="scope-rung">Service <span class="scope-desc">A single service or component</span></div>
        <div class="scope-rung">System <span class="scope-desc">The whole system, across services</span></div>
        <div class="scope-rung">User journey <span class="scope-desc">What the user experiences end-to-end</span></div>
      </div>
    </section>

    <section class="property-detail">
      <span class="property-detail-num">04</span>
      <h2 class="property-detail-title">Feedback latency</h2>
      <p class="property-detail-question">How long until the sensor tells you something?</p>
      <div class="latency-table">
        <div class="lat-row"><span class="lat-sensor">compiler</span><span class="lat-time">milliseconds</span><div class="lat-bar"><div class="lat-fill" style="width:5%"></div></div></div>
        <div class="lat-row"><span class="lat-sensor">unit tests</span><span class="lat-time">seconds</span><div class="lat-bar"><div class="lat-fill" style="width:12%"></div></div></div>
        <div class="lat-row"><span class="lat-sensor">integration</span><span class="lat-time">minutes</span><div class="lat-bar"><div class="lat-fill" style="width:30%"></div></div></div>
        <div class="lat-row"><span class="lat-sensor">mutation</span><span class="lat-time">minutes / hours</span><div class="lat-bar"><div class="lat-fill" style="width:50%"></div></div></div>
        <div class="lat-row"><span class="lat-sensor">canary</span><span class="lat-time">minutes</span><div class="lat-bar"><div class="lat-fill" style="width:35%"></div></div></div>
        <div class="lat-row"><span class="lat-sensor">production</span><span class="lat-time">hours / days</span><div class="lat-bar"><div class="lat-fill" style="width:70%"></div></div></div>
        <div class="lat-row"><span class="lat-sensor">incident</span><span class="lat-time">weeks</span><div class="lat-bar"><div class="lat-fill" style="width:100%"></div></div></div>
      </div>
    </section>

    <section class="property-detail">
      <span class="property-detail-num">05</span>
      <h2 class="property-detail-title">Actionability</h2>
      <p class="property-detail-question">Does it merely say "bad" or does it tell you what to fix?</p>
      <p>
        Three values, in order of how much the feedback directs the next action:
      </p>
      <div class="scope-ladder">
        <div class="scope-rung">Blocking <span class="scope-desc">A binary gate: pass or fail. The pipeline stops on failure, but the sensor does not say what to fix — a compiler error, a failing invariant gate, a smoke test that halts a rollout.</span></div>
        <div class="scope-rung">Exploratory <span class="scope-desc">A signal to investigate, not a verdict. It narrows where to look but prescribes nothing — a hotspot, a trace, a coverage gap on unchanged lines.</span></div>
        <div class="scope-rung">Guiding <span class="scope-desc">The feedback itself directs the next action. A mutation report shows the exact untested mutation; a linter diagnostic names the rule and the fix; a type error points at the expression and the expected type.</span></div>
      </div>
      <p>
        In Böckeler's framing, the interesting frontier is guiding sensors,
        where the feedback itself tells the agent what to do next.
      </p>
    </section>

    <section class="property-detail">
      <span class="property-detail-num">06</span>
      <h2 class="property-detail-title">Predictive vs retrospective</h2>
      <p class="property-detail-question">"This is wrong" or "this looks like things that became wrong before"?</p>
      <p>
        Predictive sensors fire before the code ships — a compiler error, a
        failed test, a mutation that survives. Retrospective sensors fire
        after — they tell you that past changes look like changes that
        caused trouble before: revert rate, incident correlation, escaped
        defect rate.
      </p>
      <p>
        This dimension is <em>when</em> the signal arrives, not <em>what
        kind</em> of feedback it gives. That is a separate axis —
        <a href="#actionability">actionability</a>: blocking, exploratory,
        guiding. The two are correlated but not the same: most predictive
        sensors gate (a compiler error blocks the build), and most
        retrospective sensors warn (revert rate is a signal, not a gate).
        But the correlation is not a rule. <em>Build provenance &amp;
        SBOM</em> is retrospective — it fires after the build — and
        <em>blocking</em>: an unattested artifact does not ship. A
        retrospective sensor can gate; a predictive sensor can merely warn.
        Read the two dimensions independently.
      </p>
      <p>
        You don't need to understand <code>FooManagerFactoryImpl</code>. You
        can observe: <em>27 changes in six months, 8 reverts, 4 incidents,
        touched by 11 teams.</em> That's a retrospective signal — a black-box
        sensor of maintainability.
      </p>
      <p>
        The catalog splits roughly evenly: predictive sensors catch bugs
        before they ship; retrospective sensors tell you where the bugs came
        from. Both matter — a sensor stack with only predictive sensors has
        no feedback loop; one with only retrospective sensors has no gate.
      </p>
    </section>
  </div>"""

    description = (
        "Six dimensions that characterize every sensor — oracle strength, "
        "independence, scope, latency, actionability, and predictive vs "
        "retrospective — and why ranking sensors is the wrong move."
    )
    # This page defines the vocabulary the other 59 pages are rated against,
    # and until now said so only in prose. framework_termset_ld() gives every
    # dimension a resolvable @id that each entry's ratings point back at.
    page_html = html_page(
        "Framework", body, canonical="framework/",
        description=description,
        json_ld=[
            # WebPage, not TechArticle, on purpose: TechArticle requires a
            # datePublished (gates.JSON_LD_REQUIRED) and this page does not
            # have one that is not invented. dateModified is real — it is
            # derived from the catalog's own content dates, never the clock.
            page_ld("WebPage", "Sensor Properties", "/framework/", description,
                    extra={"dateModified": catalog_as_of(sensors)}),
            framework_termset_ld(),
            breadcrumb_ld([("Framework", None)]),
        ],
    )
    out_path = output_dir / "framework" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)
