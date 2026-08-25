#!/usr/bin/env python3
"""
Single source of truth for the site's controlled vocabularies.

WHY THIS FILE EXISTS
--------------------
Commit 9b721ed renamed `kind: paper` to `kind: publication` across 44 content
files and updated the renderer in build.py, but not the allowed-value set in
check_frontmatter.py. The rename touched two of the three places that had to
agree, CI went red on every push for three days, and production stopped
deploying. The defect was not the missed edit; it was that the vocabulary had
three independent hand-maintained copies and no mechanism binding them.

Every controlled vocabulary that is NOT already derived from a build.py data
structure lives here, and only here. Fields validated against FAMILIES,
STACK_LAYERS, ORACLE_WIDTHS, INDEPENDENCE_DOTS and LATENCY_LABELS are already
single-sourced (check_frontmatter.py imports them from build.py) and did not
drift. The five sets below were the ones copied out by hand, and are therefore
the entire remaining drift surface.

CONSUMERS
---------
  * scripts/check_frontmatter.py  — validates content against these sets, and
    additionally asserts that build.py's renderer only ever compares a
    reference's `kind` against a value declared here (see
    `kind_literals_in_source`). That assertion binds all three places without
    build.py needing to import anything.
  * scripts/build.py              — should import REFERENCE_KIND_* rather than
    repeating the string literals inline. Until it does, the source-level
    assertion above is what keeps it honest.

TO CHANGE A VOCABULARY
----------------------
Edit the set here, then run `make check`. The frontmatter checker will tell you
which content files and which renderer literals still disagree.
"""

import ast
from pathlib import Path

# --------------------------------------------------------------------------
# Reference kinds
# --------------------------------------------------------------------------
# Maps a reference `kind` to the rendered section it is filed under. The bucket
# names are documentation of intent: build.py renders "tool" and "publication"
# as their own sections and sweeps everything else into "Further reading", so a
# new kind added here renders correctly without a renderer change — but a kind
# used in content and *not* listed here is a hard error.
#
# `paper` is deliberately NOT kept as a backwards-compatible alias for
# `publication`. No content file uses it (verified: content uses only tool,
# publication, other), and build.py gives a dedicated section only to "tool"
# and "publication" — so accepting `paper` would let a reference validate
# cleanly and then render into "Further reading" instead of "Publications".
# A value that passes the gate and renders wrong is worse than one the gate
# rejects with a message naming this file.
REFERENCE_KIND_BUCKETS = {
    "tool": "tools",
    "publication": "publications",
    "blog": "further-reading",
    "book": "further-reading",
    "spec": "further-reading",
    "other": "further-reading",
}
REFERENCE_KINDS = frozenset(REFERENCE_KIND_BUCKETS)

# The kinds build.py gives a dedicated section to. Anything else falls through
# to the catch-all bucket.
REFERENCE_KINDS_WITH_OWN_SECTION = frozenset(
    k for k, bucket in REFERENCE_KIND_BUCKETS.items() if bucket != "further-reading"
)

# Evidence-strength tiers on a reference.
REFERENCE_TIERS = frozenset({"I", "II", "III", "IV"})

# --------------------------------------------------------------------------
# Sensor-level vocabularies
# --------------------------------------------------------------------------
ACTIONABILITY = frozenset({"blocking", "exploratory", "guiding"})
SENSOR_TYPES = frozenset({"predictive", "retrospective"})
SCOPES = frozenset({"line", "function", "module", "service", "system", "user-journey"})


# --------------------------------------------------------------------------
# Drift detection
# --------------------------------------------------------------------------
def kind_literals_in_source(path):
    """Every string literal that `path` compares against a reference's `kind`.

    Parses the file and walks its comparisons looking for the shape

        <something>.get("kind") == "tool"
        <something>.get("kind") not in ("tool", "publication")

    returning {"tool", "publication"}. Uses the AST rather than a regex so
    formatting changes, line wrapping and comments cannot fool it.

    This is the binding between the renderer and this module. If build.py is
    renamed to compare against a kind that is not declared here (or this module
    is renamed and build.py is not), the returned set stops being a subset of
    REFERENCE_KINDS and check_frontmatter.py fails.
    """
    tree = ast.parse(Path(path).read_text(), filename=str(path))
    literals = set()

    def is_kind_get(node):
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "kind"
        )

    def collect(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            literals.add(node.value)
        elif isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            for elt in node.elts:
                collect(elt)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue

        # `x.get("kind") <op> "literal"` and the reversed `"literal" <op> x.get("kind")`
        if is_kind_get(node.left):
            for comparator in node.comparators:
                collect(comparator)
        elif any(is_kind_get(c) for c in node.comparators):
            collect(node.left)

    return literals


def imports_vocabulary(path):
    """True if `path` gets its vocabulary from this module by import.

    When build.py imports REFERENCE_KINDS (or friends) from here, the renderer
    and the declaration are bound structurally and the source-level probe above
    is redundant — a stale name becomes an ImportError instead of a silent
    mismatch. Until then the probe is the only thing holding them together, so
    check_frontmatter.py requires one binding or the other to be present.
    """
    tree = ast.parse(Path(path).read_text(), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[-1] == "vocabulary":
            return True
        if isinstance(node, ast.Import):
            if any(a.name.split(".")[-1] == "vocabulary" for a in node.names):
                return True
    return False
