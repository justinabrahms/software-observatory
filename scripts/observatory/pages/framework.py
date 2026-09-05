"""The framework essay: /framework/."""

import html

from ..layout import html_page
from ..dates import catalog_as_of
from ..jsonld import breadcrumb_ld, framework_termset_ld, page_ld
from ..taxonomy import LATENCY_WORDS, LATENCY_X, ORACLE_WIDTHS


# The two charts on this page used to be hand-written rows naming sensors
# that were not entries ("complexity", "code review", "production") at
# widths that disagreed with ORACLE_WIDTHS. They are now drawn from the
# entries, one row per rung, so the chart cannot say something the catalog
# does not. The slugs are preferences; any catalog (including the test
# fixture) falls back to the first entry at each rung.
ORACLE_BAR_PREFERRED = {
    "maximum": "compiler",
    "high": "example-based-tests",
    "medium": "linter",
    "low": "line-coverage",
    "minimum": None,
}

LATENCY_ROW_PREFERRED = {
    "milliseconds": "compiler",
    "seconds": "example-based-tests",
    "minutes": "integration-tests",
    "minutes-hours": "mutation-testing",
    "hours": "business-invariants",
    "days": "revert-rate",
    "weeks": "incident-correlation",
    "months": "escaped-defect-rate",
}


def _pick(sensors, field, value, preferred):
    """The preferred entry at this rung if the catalog has it, else the
    first entry at the rung, else None."""
    by_slug = {s["slug"]: s for s in sensors}
    if preferred and preferred in by_slug and by_slug[preferred].get(field) == value:
        return by_slug[preferred]
    return next((s for s in sensors if s.get(field) == value), None)


def oracle_bar_rows(sensors):
    rows = ""
    for level, width in ORACLE_WIDTHS.items():
        s = _pick(sensors, "oracle", level, ORACLE_BAR_PREFERRED.get(level))
        if s is None:
            continue
        rows += (
            f'        <div class="bar-row"><span class="bar-label">'
            f'<a href="/sensors/{s["slug"]}/">{html.escape(s["title"])}</a></span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{width}%"></div></div>'
            f'<span class="bar-pct">{level}</span></div>\n'
        )
    return rows.rstrip()


def latency_rows(sensors):
    rows = ""
    for label in LATENCY_ROW_PREFERRED:
        s = _pick(sensors, "latency", label, LATENCY_ROW_PREFERRED[label])
        if s is None:
            continue
        rows += (
            f'        <div class="lat-row"><span class="lat-sensor">'
            f'<a href="/sensors/{s["slug"]}/">{html.escape(s["title"])}</a></span>'
            f'<span class="lat-time">{html.escape(LATENCY_WORDS[label])}</span>'
            f'<div class="lat-bar"><div class="lat-fill" style="width:{LATENCY_X[label]}%"></div></div></div>\n'
        )
    return rows.rstrip()


def generate_framework_page(sensors, output_dir):
    """Generate the framework page."""

    has_minimum = any(s.get("oracle") == "minimum" for s in sensors)
    minimum_note = "" if has_minimum else (
        "No entry currently rates minimum. A raw complexity score would: "
        "high complexity proves nothing is wrong, it only suggests risk. "
        "The catalog has no entry for one; "
        '<a href="/sensors/hotspot-analysis/" class="wikilink">hotspot '
        "analysis</a> consumes complexity as an input rather than reading "
        "it as a verdict."
    )

    body = f"""  <section class="page-header page-header--reading">
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
{oracle_bar_rows(sensors)}
      </div>
      <p>
        One entry per rung, drawn from the catalog. A compiler has maximum
        oracle strength because the implementation cannot argue with it;
        line coverage is low because the line ran, which says nothing
        about whether it was right. The scale is ordinal (minimum →
        low → medium → high → maximum): a sensor two rungs up is stronger,
        not "twice as strong." {minimum_note}
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
{latency_rows(sensors)}
      </div>
      <p>
        One entry per latency band, drawn from the catalog and placed on
        the same axis the homepage scatter uses.
      </p>
    </section>

    <section class="property-detail">
      <span class="property-detail-num">05</span>
      <h2 class="property-detail-title">Actionability</h2>
      <p class="property-detail-question">Does it merely say "bad" or does it tell you what to fix?</p>
      <p>
        Three values. One is about what the verdict does; the other two
        are about what the reading says.
      </p>
      <div class="scope-ladder">
        <div class="scope-rung">Blocking <span class="scope-desc">The verdict stops the pipeline. A pre-promotion gate refuses the rollout, a smoke test halts it, an unattested artifact does not ship. The message is the refusal; the diagnosis, if there is one, comes from somewhere else.</span></div>
        <div class="scope-rung">Exploratory <span class="scope-desc">A signal to investigate, not a verdict. It narrows where to look but prescribes nothing — a hotspot, a trace, a coverage gap on unchanged lines.</span></div>
        <div class="scope-rung">Guiding <span class="scope-desc">The feedback itself directs the next action. A mutation report shows the exact untested mutation; a linter diagnostic names the rule and the fix; a type error points at the expression and the expected type.</span></div>
      </div>
      <p>
        The values overlap in practice, and the rating records which one
        the reading is written for. Every build stops on a compiler error,
        yet the <a href="/sensors/compiler/" class="wikilink">compiler</a>
        is rated guiding, because its message names the file, the line and
        the expected type: it is written to be acted on. A
        <a href="/sensors/pre-promotion-invariant-gates/" class="wikilink">pre-promotion
        gate</a> is rated blocking because its message is the refusal.
        Between them sit sensors whose verdict is a gate and whose output
        is a diagnosis, such as a model checker's counter-example trace;
        those are rated by the gate, since that is what the team wires
        them up as. Whether a guiding sensor is also made a gate is a
        pipeline decision, not a property of the sensor.
      </p>
      <p>
        In <a href="https://martinfowler.com/articles/harness-engineering.html"
        class="wikilink">Böckeler's framing</a>, the interesting frontier is
        guiding sensors, where the feedback itself tells the agent what to
        do next.
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
