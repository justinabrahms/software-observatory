#!/usr/bin/env python3
"""
Frontmatter validator for sensor entries.

Checks every content/sensors/*.md frontmatter field against the known
constants in build.py: family, oracle, independence, latency, stack_level,
actionability, type, see_also, and id uniqueness. Exits 1 on any violation,
so it can gate CI alongside check_links.py.

It also refuses an entry that cites the same url twice under two titles; see
the duplicate-url check below for why that is a content error and not a tidy-up.

It also runs a vocabulary drift check (see `check_vocabulary_drift` below and
scripts/vocabulary.py) that asserts the three places a controlled vocabulary
lives — this validator, the renderer in build.py, and the content itself —
still agree. That check exists because commit 9b721ed renamed
`kind: paper` -> `kind: publication` in content and in build.py but not here,
and CI stayed red for three days.

Usage:
    .venv/bin/python scripts/check_frontmatter.py   # or: make check-frontmatter
"""

import sys
import glob
from collections import Counter
from pathlib import Path

import yaml

SITE_ROOT = Path(__file__).resolve().parent.parent
SENSOR_DIR = SITE_ROOT / "content" / "sensors"
# The renderer this file checks against: the module that actually filters a
# sensor's references by `kind`. It used to be build.py, which was the whole
# CMS; the reference renderer now lives in the package that replaced it, and
# the probe below has to read the file the literals are actually in.
RENDERER_PY = SITE_ROOT / "scripts" / "observatory" / "pages" / "sensor.py"

sys.path.insert(0, str(SITE_ROOT / "scripts"))
from build import (
    FAMILIES,
    FAMILY_BY_SLUG,
    STACK_LAYERS,
    LATENCY_LABELS,
    ORACLE_WIDTHS,
    INDEPENDENCE_DOTS,
)
from vocabulary import (
    ACTIONABILITY,
    REFERENCE_KINDS,
    REFERENCE_TIERS,
    SCOPES,
    SENSOR_TYPES,
    imports_vocabulary,
    kind_literals_in_source,
)

# Derived from build.py's own data structures: single-sourced by construction,
# cannot drift.
VALID_FAMILIES = {f["slug"] for f in FAMILIES}
VALID_STACK_LEVELS = {s["slug"] for s in STACK_LAYERS}
VALID_ORACLES = set(ORACLE_WIDTHS.keys())
VALID_INDEPENDENCE = set(INDEPENDENCE_DOTS.keys())
VALID_LATENCIES = set(LATENCY_LABELS.keys())

# Declared in scripts/vocabulary.py, the single source of truth for the
# vocabularies build.py does not already carry a data structure for. These used
# to be hand-copied literals here; that is what drifted.
VALID_ACTIONABILITY = ACTIONABILITY
VALID_TYPES = SENSOR_TYPES
VALID_SCOPES = SCOPES
VALID_KINDS = REFERENCE_KINDS
VALID_TIERS = REFERENCE_TIERS

# Where to send someone who hits a vocabulary error.
VOCAB_HINT = "declare it in scripts/vocabulary.py if it is intentional"

REQUIRED_FIELDS = [
    "id", "title", "family", "oracle", "independence",
    "scope", "latency", "actionability", "type", "stack_level",
]


def parse_frontmatter(filepath):
    with open(filepath) as f:
        content = f.read()
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    return yaml.safe_load(parts[1]) or {}, parts[2].strip()


def check_vocabulary_drift(used):
    """Assert the renderer, this validator, and the content still agree.

    Three independent copies of the reference-`kind` vocabulary have to match:
    scripts/vocabulary.py (the declaration), build.py (the renderer), and
    content/sensors/*.md (the corpus). Nothing bound them, so commit 9b721ed
    renamed two of the three and CI was red for three days.

    Two assertions close that loop, and either one alone catches that rename:

      1. Renderer binding. Every string literal build.py compares against a
         reference's `kind` must be a declared kind. A rename in build.py that
         is not mirrored in vocabulary.py fails here; a rename in vocabulary.py
         that is not mirrored in build.py fails here too, because build.py is
         then still comparing against the old name.

      2. Corpus attestation. Every kind used in content must be declared (that
         is the per-file check above, which is what went red). The inverse —
         a declared kind that no content uses — is reported as a WARNING, not
         an error, because a vocabulary may legitimately run ahead of the
         corpus. It is the signal that a rename left a dead name behind, which
         is exactly the state `paper` was in.

    Returns (errors, warnings).
    """
    errors = []
    warnings = []

    try:
        rendered_kinds = kind_literals_in_source(RENDERER_PY)
    except (OSError, SyntaxError) as e:
        errors.append(f"vocabulary: could not parse {RENDERER_PY.relative_to(SITE_ROOT)} to check kind literals: {e}")
        rendered_kinds = set()

    # If the renderer imports its vocabulary from vocabulary.py, the binding is
    # structural (a stale name is an ImportError) and the source probe is
    # redundant. Otherwise the probe is the only binding there is, so finding
    # zero `kind` comparisons means it has gone blind — fail rather than pass
    # vacuously, which is how this control would quietly become decoration.
    try:
        bound_by_import = imports_vocabulary(RENDERER_PY)
    except (OSError, SyntaxError):
        bound_by_import = False

    if not rendered_kinds and not bound_by_import:
        errors.append(
            f"vocabulary: found no `kind` comparisons in {RENDERER_PY.relative_to(SITE_ROOT)} and no import "
            "of scripts/vocabulary.py. Either the reference renderer was removed, or "
            "kind_literals_in_source() in scripts/vocabulary.py no longer matches how "
            "the renderer filters references. Fix the probe, or bind the renderer "
            "properly with `from vocabulary import REFERENCE_KINDS` — do not delete "
            "this check."
        )

    for literal in sorted(rendered_kinds - REFERENCE_KINDS):
        errors.append(
            f"vocabulary: {RENDERER_PY.relative_to(SITE_ROOT)} renders reference kind '{literal}', which is "
            f"not declared in scripts/vocabulary.py (declared: {sorted(REFERENCE_KINDS)}). "
            "The renderer and the vocabulary have drifted apart."
        )

    unattested = sorted(REFERENCE_KINDS - set(used["kind"]))
    if unattested:
        warnings.append(
            f"vocabulary: reference kind(s) {unattested} are declared in "
            "scripts/vocabulary.py but used by no content file. If a rename left them "
            "behind, delete them; if they are reserved for future use, leave them."
        )

    return errors, warnings


def main():
    errors = []
    seen_ids = {}
    used = {
        "kind": Counter(),
        "tier": Counter(),
        "actionability": Counter(),
        "type": Counter(),
        "scope": Counter(),
    }

    files = sorted(SENSOR_DIR.glob("*.md"))
    if not files:
        print("No sensor files found.")
        return 1

    for filepath in files:
        slug = filepath.stem
        loc = f"{filepath.name}"

        try:
            meta, _ = parse_frontmatter(filepath)
        except yaml.YAMLError as e:
            errors.append(f"{loc}: YAML parse error: {e}")
            continue

        for field in REQUIRED_FIELDS:
            if field not in meta:
                errors.append(f"{loc}: missing required field '{field}'")

        sid = meta.get("id", "")
        if sid:
            if sid in seen_ids:
                errors.append(
                    f"{loc}: duplicate id '{sid}' (also in {seen_ids[sid]})"
                )
            else:
                seen_ids[sid] = loc

        family = meta.get("family", "")
        if family and family not in VALID_FAMILIES:
            errors.append(
                f"{loc}: family '{family}' not in {sorted(VALID_FAMILIES)}"
            )

        oracle = meta.get("oracle", "")
        if oracle and oracle not in VALID_ORACLES:
            errors.append(
                f"{loc}: oracle '{oracle}' not in {sorted(VALID_ORACLES)}"
            )

        indep = meta.get("independence", "")
        if indep and indep not in VALID_INDEPENDENCE:
            errors.append(
                f"{loc}: independence '{indep}' not in {sorted(VALID_INDEPENDENCE)}"
            )

        latency = meta.get("latency", "")
        if latency and latency not in VALID_LATENCIES:
            errors.append(
                f"{loc}: latency '{latency}' not in {sorted(VALID_LATENCIES)}"
            )

        stack = meta.get("stack_level", "")
        if stack and stack not in VALID_STACK_LEVELS:
            errors.append(
                f"{loc}: stack_level '{stack}' not in {sorted(VALID_STACK_LEVELS)}"
            )

        action = meta.get("actionability", "")
        if action:
            used["actionability"][action] += 1
        if action and action not in VALID_ACTIONABILITY:
            errors.append(
                f"{loc}: actionability '{action}' not in {sorted(VALID_ACTIONABILITY)}"
            )

        scope = meta.get("scope", "")
        if scope:
            used["scope"][scope] += 1
        if scope and scope not in VALID_SCOPES:
            errors.append(
                f"{loc}: scope '{scope}' not in {sorted(VALID_SCOPES)}"
            )

        stype = meta.get("type", "")
        if stype:
            used["type"][stype] += 1
        if stype and stype not in VALID_TYPES:
            errors.append(
                f"{loc}: type '{stype}' not in {sorted(VALID_TYPES)}"
            )

        see_also = meta.get("see_also", []) or []
        if not isinstance(see_also, list):
            errors.append(f"{loc}: see_also must be a list, got {type(see_also).__name__}")
        else:
            for ref in see_also:
                if not isinstance(ref, str):
                    errors.append(f"{loc}: see_also entry {ref!r} must be a string")

        categories = meta.get("categories", []) or []
        if not isinstance(categories, list):
            errors.append(f"{loc}: categories must be a list, got {type(categories).__name__}")

        reviewed = meta.get("last_reviewed", "")
        if reviewed:
            import re as _re
            if not _re.match(r"^\d{4}-\d{2}-\d{2}$", str(reviewed)):
                errors.append(f"{loc}: last_reviewed '{reviewed}' must be YYYY-MM-DD")

        if sid and see_also and sid in see_also:
            errors.append(f"{loc}: see_also references its own id '{sid}' (self-loop)")

        references = meta.get("references", []) or []
        if not isinstance(references, list):
            errors.append(f"{loc}: references must be a list, got {type(references).__name__}")
        else:
            for i, ref in enumerate(references):
                if not isinstance(ref, dict):
                    errors.append(f"{loc}: references[{i}] must be a dict, got {type(ref).__name__}")
                    continue
                if not ref.get("title"):
                    errors.append(f"{loc}: references[{i}] missing 'title'")
                kind = ref.get("kind", "")
                if kind:
                    used["kind"][kind] += 1
                if kind and kind not in VALID_KINDS:
                    errors.append(
                        f"{loc}: references[{i}] kind '{kind}' not in "
                        f"{sorted(VALID_KINDS)} — {VOCAB_HINT}"
                    )
                if kind == "tool" and not ref.get("url"):
                    errors.append(f"{loc}: references[{i}] tool '{ref.get('title', '?')}' missing 'url'")
                tier = ref.get("tier", "")
                if tier:
                    used["tier"][tier] += 1
                if tier and tier not in VALID_TIERS:
                    errors.append(
                        f"{loc}: references[{i}] tier '{tier}' not in "
                        f"{sorted(VALID_TIERS)} — {VOCAB_HINT}"
                    )

            # One URL, one entry. Five entries cited the same page twice under
            # two names, and in three of them the second name misdescribed the
            # page it pointed at ('kubectl admission' for the Kubernetes
            # admission-controller docs, 'error budget calculators' for the SRE
            # Workbook's error-budget-*policy* chapter). Nobody spots that by
            # reading a reference list top to bottom, because each entry looks
            # fine on its own — it is only visible by grouping on the URL.
            # Trailing slashes are ignored: the same page reached two ways is
            # still the same page.
            seen = {}
            for i, ref in enumerate(references):
                if not isinstance(ref, dict):
                    continue
                url = (ref.get("url") or "").rstrip("/")
                if not url:
                    continue
                if url in seen:
                    first, first_title = seen[url]
                    errors.append(
                        f"{loc}: references[{i}] '{ref.get('title', '?')}' cites the "
                        f"same url as references[{first}] '{first_title}' ({url}). "
                        f"Merge them, or point one at the page it actually means."
                    )
                else:
                    seen[url] = (i, ref.get("title", "?"))

    vocab_errors, vocab_warnings = check_vocabulary_drift(used)
    errors.extend(vocab_errors)

    for w in vocab_warnings:
        print(f"WARNING: {w}")

    if errors:
        print(f"{len(errors)} frontmatter error(s) found:")
        for e in errors:
            print(f"  {e}")
        return 1

    print(f"All {len(files)} sensor frontmatters OK.")
    print(
        f"Vocabulary in sync: content, {RENDERER_PY.relative_to(SITE_ROOT)} and "
        f"scripts/vocabulary.py agree on reference kinds {sorted(used['kind'])}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
