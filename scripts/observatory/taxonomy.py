"""The sensor taxonomy: families, stack layers, lifecycle stages, and the
scales every page renders sensors against.

Pure data plus one URL helper. Nothing here renders a page, and nothing here
reads the filesystem, so the validators (scripts/check_frontmatter.py) can
import the controlled vocabularies straight out of the renderer's own tables
instead of keeping a second copy."""


# ── Sensor family metadata ──────────────────────────────────────────────────

FAMILIES = [
    {
        "slug": "structural",
        "num": "01",
        "name": "Structural",
        "icon": "\u25a0",
        "question": "Is this artifact internally coherent?",
        "examples": "Compiler, type checker, linter, formatter, schema validator",
        "stack_levels": ["compilation", "static-analysis"],
    },
    {
        "slug": "behavioral",
        "num": "02",
        "name": "Behavioral",
        "icon": "●",
        "question": "Does it do what we expect?",
        "examples": "Unit, integration, E2E, contract, snapshot tests",
        "stack_levels": ["behavioral-tests", "integration-tests"],
    },
    {
        "slug": "test-effectiveness",
        "num": "03",
        "name": "Test Effectiveness",
        "icon": "▲",
        "question": "Do our tests actually detect failures?",
        "examples": "Coverage, diff coverage, mutation testing",
        "stack_levels": ["mutation-testing"],
    },
    {
        "slug": "invariants",
        "num": "04",
        "name": "Invariants",
        "icon": "◆",
        "question": "What must always be true?",
        "examples": "Balance >= 0, every FK valid, every request has one ID",
        "stack_levels": ["static-analysis", "production-behavior"],
    },
    {
        "slug": "adversarial",
        "num": "05",
        "name": "Adversarial",
        "icon": "✖",
        "question": "Can we make our evidence of correctness fail?",
        "examples": "Fuzzing, fault injection, chaos, metamorphic testing",
        "stack_levels": ["property-metamorphic", "mutation-testing"],
    },
    {
        "slug": "runtime",
        "num": "06",
        "name": "Runtime",
        "icon": "○",
        "question": "What is it actually doing?",
        "examples": "Logs, traces, metrics, profiles, high-cardinality events",
        "stack_levels": ["production-behavior"],
    },
    {
        "slug": "change",
        "num": "07",
        "name": "Change",
        "icon": "→",
        "question": "What did this change actually affect?",
        "examples": "API compatibility, canary, shadow traffic, error budget, A/B testing",
        "stack_levels": ["canary-shadow", "user-outcome"],
    },
    {
        "slug": "architecture",
        "num": "08",
        "name": "Architecture",
        "icon": "▣",
        "question": "Is the system becoming harder to reason about?",
        "examples": "Dependency graphs, coupling, fitness functions, hotspots",
        "stack_levels": ["static-analysis"],
    },
    {
        "slug": "evolution",
        "num": "09",
        "name": "Evolution",
        "icon": "⟳",
        "question": "Does this look like changes that caused trouble before?",
        "examples": "Revert rate, regression rate, churn, incident correlation",
        "stack_levels": ["user-outcome"],
    },
    {
        "slug": "comprehension",
        "num": "10",
        "name": "Human Comprehension",
        "icon": "✔",
        "question": "Can another observer understand and challenge this?",
        "examples": "Review, explainability tests, documentation drift, onboarding",
        "stack_levels": ["static-analysis", "behavioral-tests", "production-behavior", "user-outcome"],
    },
]


FAMILY_BY_SLUG = {f["slug"]: f for f in FAMILIES}


# Per-family editorial matter for /families/<slug>/. `belongs` states the
# inclusion criterion — the thing that makes an entry a member rather than a
# neighbour — and `contested` names the placements that are genuinely
# arguable. Taxonomy without a stated criterion is just a list of ten buckets.
FAMILY_RATIONALE = {
    "structural": {
        "belongs":
            "A sensor belongs here if it can reach its verdict by reading the "
            "artifact — its source, its types, its schema, its bill of "
            "materials — without running it against real inputs. The oracle is "
            "the artifact's own internal consistency: the code either "
            "type-checks or it does not, and the implementation cannot argue "
            "with the answer.",
        "contested":
            "Build Provenance & SBOM is about where an artifact came from "
            "rather than whether its text is coherent; it sits here because it "
            "is a claim you can check without executing anything. Model "
            "Checking and Theorem Proving establish facts about behaviour, not "
            "structure, and are grouped here because they establish them "
            "before the system runs.",
    },
    "behavioral": {
        "belongs":
            "These sensors run the system on inputs a human chose and compare "
            "what happened against an answer a human supplied. The oracle is "
            "external and specific: it is exactly as good as the example, and "
            "it says nothing about the cases nobody wrote down.",
        "contested":
            "Synthetic Monitoring runs the same chosen-input check against "
            "production, which makes it as much a runtime sensor as a "
            "behavioural one. It is grouped here because its oracle is a "
            "scripted expectation rather than an observation of real traffic.",
    },
    "test-effectiveness": {
        "belongs":
            "Every entry here points at the test suite rather than at the "
            "system. They answer a second-order question — would these tests "
            "have noticed? — which makes this the one family whose subject is "
            "other sensors.",
        "contested":
            "Escaped Defect Rate measures the whole delivery pipeline after "
            "the fact and could equally sit in Evolution. The coverage entries "
            "are weak oracles by construction: they can prove a line was never "
            "executed, never that a behaviour was established.",
    },
    "invariants": {
        "belongs":
            "This family is defined by the shape of the claim, not by where it "
            "is enforced: a property stated once that must hold for every "
            "state or every execution. The same invariant may be checked by a "
            "type, a database constraint, an assertion in production, or a "
            "gate before promotion.",
        "contested":
            "Because enforcement is spread across the lifecycle, entries here "
            "deliberately overlap Structural (Statically Checked Invariants) "
            "and Runtime (Runtime Invariants). The interesting fact about an "
            "invariant is that somebody stated it, not which mechanism happens "
            "to check it.",
    },
    "adversarial": {
        "belongs":
            "The sensor supplies its own inputs or its own faults. Nobody "
            "wrote down the case that fails; the technique searched for it. "
            "That is what separates this family from Behavioral, whose inputs "
            "are all human-chosen.",
        "contested":
            "Static Security Analysis executes nothing and is adversarial in "
            "intent rather than in mechanism. Property-Based Testing and "
            "Metamorphic Testing straddle Behavioral: they check properties a "
            "human stated, but generate the inputs themselves.",
    },
    "runtime": {
        "belongs":
            "These sensors describe what the system actually did, in the wild, "
            "with no expected answer to compare against. They have the weakest "
            "oracles in the catalog and the widest scope: they cannot tell you "
            "something is wrong, only what happened.",
        "contested":
            "Load Testing is a chosen-input experiment rather than a passive "
            "observation and could sit in Behavioral or Adversarial. It is "
            "here because what it measures is runtime behaviour under "
            "conditions the code cannot see for itself.",
    },
    "change": {
        "belongs":
            "Every entry compares two things: the version before a change and "
            "the version after, or the population exposed to it and the "
            "population that was not. The unit of observation is a change, not "
            "a system.",
        "contested":
            "A/B Testing measures user outcome rather than correctness, and "
            "Incremental Build Correctness is arguably structural. Both are "
            "here because their verdict is about the effect of one specific "
            "change.",
    },
    "architecture": {
        "belongs":
            "These sensors measure the shape of the system rather than its "
            "behaviour — how the parts depend on each other, and how expensive "
            "it is becoming to reason about them. None of them can tell you "
            "the system is wrong; they tell you it is getting harder to know.",
        "contested":
            "Live Service Graph Discovery observes production traffic, which "
            "makes it a runtime sensor whose subject happens to be "
            "architecture. Everything here has a weak oracle: high coupling is "
            "a smell, not a defect.",
    },
    "evolution": {
        "belongs":
            "These sensors read history rather than the current artifact. They "
            "are retrospective and statistical — they answer \u201cdoes this look "
            "like changes that caused trouble before?\u201d and can never be a "
            "verdict on one specific change.",
        "contested":
            "DORA Metrics describe the delivery system rather than the "
            "software, and Incident Correlation overlaps Runtime. Everything "
            "here is a base rate: useful for directing attention, useless as "
            "proof.",
    },
    "comprehension": {
        "belongs":
            "In this family the instrument is another mind, or a proxy for "
            "one. The question is not whether the system works but whether a "
            "second observer can follow it, reproduce the reasoning, and "
            "disagree with it.",
        "contested":
            "Second-Agent Review raises the independence question directly: "
            "two instances of the same model share failure modes, so the "
            "sensor is worth only as much as the second observer is actually "
            "different. Documentation Drift is mechanically checkable and "
            "could sit in Structural.",
    },
}


def family_url(slug):
    """Canonical URL of a family.

    Families were `#anchors` on /catalog/ until #123 promoted them to pages.
    The anchors still exist on the catalog page and still resolve, so old
    inbound links keep working; everything the build emits points here.
    """
    return f"/families/{slug}/"


# Confidence stack layers (top to bottom)
STACK_LAYERS = [
    {"slug": "user-outcome",          "label": "User outcome",           "desc": "Does the system produce the intended result for users?"},
    {"slug": "production-behavior",   "label": "Production behavior",   "desc": "What is it actually doing in the real world?"},
    {"slug": "canary-shadow",         "label": "Canary / shadow",       "desc": "Does the new version behave differently from the old?"},
    {"slug": "integration-tests",     "label": "Integration tests",    "desc": "Does it work connected to its real dependencies?"},
    {"slug": "behavioral-tests",      "label": "Behavioral tests",      "desc": "Does it do what we expect for given inputs?"},
    {"slug": "property-metamorphic",  "label": "Property / metamorphic","desc": "Does it obey generalized properties across input spaces?"},
    {"slug": "mutation-testing",      "label": "Mutation testing",      "desc": "Would our tests detect plausible wrong implementations?"},
    {"slug": "static-analysis",      "label": "Static analysis / types","desc": "Is it internally coherent and structurally valid?"},
    {"slug": "compilation",           "label": "Compilation",          "desc": "Is it a valid inhabitant of the language?"},
    {"slug": "source-text",           "label": "Source text",           "desc": "The opaque artifact itself."},
]


# Lifecycle stages for the atlas grid (left to right: when the signal arrives).
# Each stage folds in one or more confidence-stack levels; the stack remains
# the narrative model, this is the operational one.
LIFECYCLE_STAGES = [
    {"slug": "build",      "label": "Build",      "desc": "Signals available before the code runs.",
     "levels": ["source-text", "compilation", "static-analysis"]},
    {"slug": "test",       "label": "Test",       "desc": "Signals from exercising the system with chosen inputs.",
     "levels": ["mutation-testing", "property-metamorphic", "behavioral-tests", "integration-tests"]},
    {"slug": "deploy",     "label": "Deploy",     "desc": "Signals from rolling a change out safely.",
     "levels": ["canary-shadow"]},
    {"slug": "production", "label": "Production", "desc": "Signals from the live system.",
     "levels": ["production-behavior"]},
    {"slug": "outcome",    "label": "Outcome",    "desc": "Signals about real-world results and history.",
     "levels": ["user-outcome"]},
]


STAGE_BY_LEVEL = {}


for _stage in LIFECYCLE_STAGES:
    for _lvl in _stage["levels"]:
        STAGE_BY_LEVEL[_lvl] = _stage["slug"]


# Scatter positions for the homepage latency/efficacy diagram, keyed by
# confidence-stack layer slug. x = feedback latency (0=instant, 100=slow),
# y = efficacy of the signal (0=suggestive, 100=definitive). Hand-tuned;
# "source-text" is not a sensor and is intentionally absent.
STACK_SCATTER = {
    "compilation":          {"x": 4,  "y": 82},
    "static-analysis":      {"x": 14, "y": 64},
    "mutation-testing":     {"x": 46, "y": 78},
    "property-metamorphic": {"x": 42, "y": 62},
    "behavioral-tests":     {"x": 32, "y": 48},
    "integration-tests":    {"x": 56, "y": 58},
    "canary-shadow":        {"x": 66, "y": 50},
    "production-behavior":  {"x": 82, "y": 42},
    "user-outcome":         {"x": 94, "y": 92},
}


# Ordinal scales mapping sensor frontmatter onto the same axes
TIER_LABELS = {
    "I":   "controlled study",
    "II":  "observational study",
    "III": "case study",
    "IV":  "argument",
}


LATENCY_X = {
    "milliseconds": 6,
    "seconds": 20,
    "minutes": 42,
    "minutes-hours": 56,
    "hours": 62,
    "seconds-hours": 68,
    "days": 76,
    "weeks": 90,
    "months": 95,
    "varies": 50,
}


ORACLE_Y = {
    "minimum": 14,
    "low": 30,
    "medium": 50,
    "high": 72,
    "maximum": 92,
}


# ── Oracle strength bar widths ──────────────────────────────────────────────

ORACLE_WIDTHS = {
    "maximum": 100,
    "high": 90,
    "medium": 60,
    "low": 40,
    "minimum": 20,
}


INDEPENDENCE_DOTS = {
    "maximum": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    "minimum": 1,
}


LATENCY_LABELS = {
    "milliseconds": "ms",
    "seconds": "s",
    "minutes": "m",
    "minutes-hours": "m-h",
    "hours": "h",
    "seconds-hours": "s-h",
    "days": "d",
    "weeks": "w",
    "months": "mo",
    "varies": "varies",
}


# Full-word forms for display contexts where the abbreviation alone is opaque
# (card badges, sensor page sidebar). Defaults to the key itself with hyphens
# spelled out as "to"; entries below only exist to reorder compound ranges.
class _LatencyWords(dict):
    def __missing__(self, key):
        return key.replace("-", " to ")


LATENCY_WORDS = _LatencyWords({
    "minutes-hours": "minutes to hours",
    "seconds-hours": "seconds to hours",
})
