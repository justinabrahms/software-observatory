"""The glossary: /glossary/."""

import html
import re

from ..config import SITE_URL
from ..jsonld import (
    AUTHOR_LD,
    CONTENT_LICENSE,
    GLOSSARY_TERMSET_ID,
    breadcrumb_ld,
)
from ..layout import html_page
from ..render import meta_description
from ..taxonomy import FAMILIES


def generate_glossary_page(output_dir):
    """Generate the glossary page: definitions of the core vocabulary used
    across the site, cross-linked to the framework and catalog."""

    entries = [
        ("epistemic-sensor",
         "Epistemic sensor",
         "A measurement instrument pointed at a failure mode. The term is "
         "deliberately not \"quality metric\": a metric aggregates or scores, "
         "while a sensor reduces uncertainty about a specific property of the "
         "system. A compiler is a sensor of structural validity; mutation "
         "testing is a sensor of test sensitivity; observability events are "
         "sensors of what actually happened. Each sensor measures one thing — "
         '<a href="/glossary/#no-single-sensor" class="wikilink">no single sensor measures correctness</a>. The catalog is organized into '
         f'<a href="/catalog/" class="wikilink">{len(FAMILIES)} families</a> of '
         "epistemic sensor, each asking a different question about the system."),
        ("opaque-artifact",
         "Opaque artifact",
         "Software we cannot — or do not want to — fully understand by "
         "reading. Code is increasingly produced by agents, by teams we'll "
         "never meet, and by systems that span services we don't own. The "
         "question for an opaque artifact is not \"is this code good?\" but "
         '"<em>what independent observations would cause us to update our '
         'belief that this software is correct?</em>\" The Observatory is a '
         "catalog of those observations."),
        ("oracle",
         "Oracle",
         "An oracle is the thing that tells you whether a given behavior is "
         "correct. A compiler error is a perfect oracle of structural validity "
         "— the implementation cannot argue with it. A test assertion is a "
         "strong oracle for the specific case it checks. A complexity metric "
         "is a weak oracle — high complexity doesn't prove anything is wrong. "
         '<a href="/framework/" class="wikilink">Oracle strength</a> is one '
         "of the six dimensions every sensor is characterized along."),
        ("oracle-strength",
         "Oracle strength",
         "How confidently a sensor knows that something is wrong. The scale "
         "runs from maximum (a compiler error — the code cannot argue) to low "
         "(a complexity metric — it suggests risk but proves nothing). See the "
         '<a href="/framework/" class="wikilink">framework page</a> for the '
         "full ranking."),
        ("independence",
         "Independence",
         "Whether the thing being evaluated can manipulate the sensor. A model "
         "writing <code>tests/</code> is allowed to write tests that make itself "
         "pass — that's low independence. A compiler is maximum independence — "
          "the code cannot talk its way past a type error. Independence is "
          "especially important for AI-generated code: the producer and the "
          "evaluator should be separated wherever possible. See "
          '<a href="/framework/" class="wikilink">the framework</a> and '
          '<a href="/sensors/second-agent-review/" class="wikilink">'
          "second-agent review</a>."),
        ("scope",
         "Scope",
         "What level of the system the sensor tells you about: a single line, "
         "a function, a module, a service, the whole system, or a user journey. "
         "A type checker has function-level scope; observability events have "
         'system-level scope. See <a href="/framework/" class="wikilink">'
         "the framework</a>."),
        ("feedback-latency",
         "Feedback latency",
         "How long until the sensor tells you something. A compiler reports in "
         "milliseconds; an escaped-defect-rate sensor reports in months. "
         "Latency determines where in the lifecycle a sensor is useful — you "
         "can't gate a merge on a signal that takes weeks. See "
         '<a href="/framework/" class="wikilink">the framework</a>.'),
        ("actionability",
         "Actionability",
         "Whether a sensor merely flags a problem or tells you what to fix. "
         "Three values: <strong>blocking</strong> — a binary gate that halts "
         "the pipeline (compiler error, invariant gate); "
         "<strong>exploratory</strong> — a signal to investigate that narrows "
         "where to look but prescribes nothing (hotspot, trace, coverage gap); "
         "<strong>guiding</strong> — the feedback itself directs the next "
         "action (mutation report shows the untested mutation, linter names "
         'the rule and fix). See <a href="/framework/" class="wikilink">'
         "the framework</a>."),
        ("evidence-tier",
         "Evidence label",
         "A label assigned to each publication reference, describing the "
         "<em>study</em> rather than the claim: <strong>controlled "
         "study</strong> (controlled experiment or large-N study with a "
         "comparison group), <strong>observational study</strong> "
         "(observational study on production data, no control group), "
         "<strong>case study</strong> (single-organization case study or "
         "engineering report with numbers), <strong>argument</strong> "
         "(experience report — not measured, but rendered visibly as "
         "unmeasured). The label tells you what kind of evidence backs "
         "the claim, so you can weigh it accordingly."),
        ("guiding-sensor",
         "Guiding sensor",
         "A sensor whose feedback directs the next action, not just whether "
         "something is wrong. A mutation testing report shows the exact "
         "untested mutation — the agent knows what to write a test for. A "
         "complexity score just says \"this is complex\" and leaves the agent "
         "to figure out what to do. The distinction comes from Birgitta "
         "Böckeler's \"guides &amp; sensors\" framing."),
        ("predictive-vs-retrospective",
         "Predictive vs retrospective",
         "Whether the sensor fires before the code ships (predictive — a "
         "compiler error before merge) or after (retrospective — revert "
         "rate, incident correlation). This is <em>when</em> the signal "
         "arrives, not <em>what kind</em> of feedback it gives — that is "
         "actionability. The two are correlated but not the same: a "
         "retrospective sensor can still gate (build provenance blocks an "
         "unattested artifact). See "
         '<a href="/framework/" class="wikilink">the framework</a>.'),
         ("confidence-stack",
         "Confidence stack",
         "The layers of evidence that accumulate as code moves from authoring "
         "to production: compilation, types, tests, mutation, integration, "
         "canary, production events, outcomes. No single layer is sufficient; "
         "the combination constrains uncertainty from multiple directions. "
         'The <a href="/atlas/" class="wikilink">atlas</a> arranges the '
         "stack as a navigational matrix."),
        ("metamorphic-testing",
         "Metamorphic testing",
         "A testing technique where you don't know the correct answer, but you "
         "know how the answer should change when the input changes. You may not "
         "know what <code>sqrt(2)</code> is, but you know "
         "<code>sqrt(x * 4) == 2 * sqrt(x)</code> must hold. You don't need a "
         "specified oracle; the relation is a partial one. See "
         '<a href="/sensors/metamorphic-testing/" class="wikilink">the entry</a>.'),
         ("high-cardinality",
          "High cardinality",
          "A property of observability events: each event carries enough "
          "distinct fields (user_id, cart_id, order_id, deployment, git_sha) "
          "that you can slice the data along dimensions you didn't know you'd "
          "need. The opposite of pre-aggregated metrics, which answer only "
          "predetermined questions. See "
           '<a href="/sensors/observability-events/" class="wikilink">the entry</a>.'),
         ("no-single-sensor",
          "No single sensor measures correctness",
          "A refrain that recurs across the homepage, the framework, and "
          "this glossary — deliberately. The repetition is the point: the "
          "Observatory's central claim is that correctness is not a scalar "
          "any one sensor measures, and stating it once would understate "
          "it. Each occurrence links back here so a reader who notices the "
          "repetition can verify it is intentional."),
     ]

    sections = ""
    for slug, term, definition in entries:
        sections += f"""    <section class="glossary-entry">
      <h2 class="glossary-term" id="{slug}">{html.escape(term)}</h2>
      <p class="glossary-definition">{definition}</p>
    </section>
"""

    body = f"""  <section class="page-header page-header--reading">
    <p class="eyebrow">Glossary</p>
    <h1 class="page-title">Glossary</h1>
    <p class="page-lede">
      The core vocabulary the Observatory uses to talk about software
      correctness. These terms appear throughout the catalog, the atlas, and
      the framework; this page collects their definitions in one place.
    </p>
  </section>

  <div class="about-content">
{sections.rstrip()}
  </div>"""

    glossary_ld = {
        "@type": "DefinedTermSet",
        "@id": GLOSSARY_TERMSET_ID,
        "name": "Software Observatory glossary",
        "description": (
            "The vocabulary the catalog runs on: epistemic sensor, oracle, "
            "independence, actionability, and the rest."
        ),
        "url": f"{SITE_URL}/glossary/",
        "inLanguage": "en",
        "license": CONTENT_LICENSE,
        "creator": AUTHOR_LD,
        "hasDefinedTerm": [
            {
                "@type": "DefinedTerm",
                "@id": f"{SITE_URL}/glossary/#{slug}",
                "name": term,
                "description": meta_description(
                    html.unescape(re.sub(r"<[^>]+>", "", definition)), 300
                ),
                "url": f"{SITE_URL}/glossary/#{slug}",
                "inDefinedTermSet": {"@id": GLOSSARY_TERMSET_ID},
            }
            for slug, term, definition in entries
        ],
    }

    page_html = html_page(
        "Glossary", body, canonical="glossary/",
        json_ld=[glossary_ld, breadcrumb_ld([("Glossary", None)])],
        description=(
            "Definitions for the vocabulary the catalog runs on — epistemic "
            "sensor, oracle, independence, actionability, flakiness, and the "
            "rest, in one place."
        ),
    )
    out_path = output_dir / "glossary" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)
