"""The gates: what refuses to publish.

Two kinds, and the difference matters. validate_sensors() answers everything
that can be answered from the loaded corpus and runs before a single byte is
written. assert_output_invariants() answers what can only be checked by
reading generated HTML, so it is a post-check, not a gate. See the "Gate
ordering" comment below."""

import re

from .taxonomy import FAMILIES, STACK_LAYERS


def assert_family_count(output_dir):
    """Scan generated HTML for prose family-count strings and fail the build
    if any digit-based count disagrees with len(FAMILIES).

    Catches drift where a page hard-codes "N families" instead of computing
    the count from the FAMILIES data structure.
    """
    import re
    expected = len(FAMILIES)
    pattern = re.compile(r"(\d+)\s+families?", re.IGNORECASE)
    mismatches = []
    for html_path in generated_html_paths(output_dir):
        try:
            text = html_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for m in pattern.finditer(text):
            found = int(m.group(1))
            if found != expected:
                mismatches.append((html_path.name, m.group(0)))
    if mismatches:
        details = "; ".join(f"{name}: {snippet!r}" for name, snippet in mismatches)
        raise AssertionError(
            f"Family-count drift: FAMILIES has {expected} entries but generated "
            f"HTML says otherwise — {details}. Compute the count from "
            f"len(FAMILIES) instead of hard-coding it."
        )


def assert_sensor_count(sensors, output_dir):
    """Scan generated output for prose sensor-count strings and fail the build
    if any disagrees with the number of files in content/sensors/.

    The sibling of assert_family_count: the build is the single source of
    truth for how many sensors there are, and a hard-coded "59 sensors" left
    behind in prose is a lie the moment an entry lands.
    """
    expected = len(sensors)
    pattern = re.compile(r"(\d+)\s+(?:epistemic\s+)?sensors\b", re.IGNORECASE)
    targets = generated_html_paths(output_dir)
    for extra in ("llms.txt", "llms-full.txt", "rss.xml", "search-index.json"):
        path = output_dir / extra
        if path.exists():
            targets.append(path)
    mismatches = []
    for path in targets:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for m in pattern.finditer(text):
            if int(m.group(1)) != expected:
                mismatches.append((path.name, m.group(0)))
    if mismatches:
        details = "; ".join(f"{name}: {snippet!r}" for name, snippet in mismatches)
        raise AssertionError(
            f"Sensor-count drift: content/sensors/ has {expected} entries but "
            f"generated output says otherwise — {details}. Compute the count "
            f"from len(sensors) instead of hard-coding it."
        )


# Directories the build itself writes HTML into. The gates below used to
# rglob the whole repo root, which also walked .venv/ (playwright ships HTML)
# and any archive-*/ tarball extract. A gate that reads files the build did
# not write is measuring somebody else's artifact.
GENERATED_HTML_DIRS = (
    "sensors", "catalog", "families", "atlas", "framework", "about",
    "contact", "privacy", "glossary", "categories",
)


GENERATED_HTML_FILES = ("index.html", "404.html")


def generated_html_paths(output_dir):
    """Every HTML file this build produced, sorted."""
    paths = [output_dir / name for name in GENERATED_HTML_FILES]
    for name in GENERATED_HTML_DIRS:
        paths.extend((output_dir / name).rglob("*.html"))
    return sorted(p for p in paths if p.exists())


JSON_LD_RE = re.compile(
    r'<script type="application/ld\+json">(.*?)</script>', re.S
)


# @type -> properties that must be present and non-empty for the block to be
# worth emitting at all. Structured data rots silently; this is the gate that
# notices.
JSON_LD_REQUIRED = {
    "WebSite": ("name", "url"),
    "DefinedTermSet": ("name", "url", "hasDefinedTerm"),
    "DefinedTerm": ("name", "description", "inDefinedTermSet"),
    "TechArticle": ("headline", "description", "author", "datePublished"),
    "BreadcrumbList": ("itemListElement",),
    "ItemList": ("itemListElement",),
    # A Dataset whose distribution or license went missing is worse than no
    # Dataset: it advertises reusable data and says nothing about the terms.
    "Dataset": ("name", "description", "url", "license", "distribution"),
    "DataDownload": ("contentUrl", "encodingFormat", "license"),
    # `name` only: a PropertyValue under additionalProperty carries a value,
    # but one under variableMeasured names a variable and correctly has none.
    # One rule cannot see which context it is in, so it asserts the invariant.
    "PropertyValue": ("name",),
    "WebPage": ("name", "description", "url"),
    "AboutPage": ("name", "description", "url"),
    "ContactPage": ("name", "description", "url"),
    "CollectionPage": ("name", "description", "url"),
}


def assert_json_ld_parses(output_dir):
    """Fail the build if any emitted JSON-LD block does not parse, or is
    missing a required property for its @type.

    Invalid structured data is invisible: the page renders, the block is
    ignored, and nobody notices for a year. Returns the number of blocks
    checked so the build log reports coverage rather than silence.
    """
    import json as _json

    def check(node, path, problems):
        if isinstance(node, list):
            for i, item in enumerate(node):
                check(item, f"{path}[{i}]", problems)
            return
        if not isinstance(node, dict):
            return
        types = node.get("@type", "")
        for t in (types if isinstance(types, list) else [types]):
            for prop in JSON_LD_REQUIRED.get(t, ()):
                if not node.get(prop):
                    problems.append(f"{path}: {t} missing {prop!r}")
        for key, value in node.items():
            # @graph is the one @-prefixed key that holds nodes rather than
            # metadata. Skipping every @-key skipped it too, so on any page
            # emitting more than one node — which is most of them — the gate
            # validated the wrapper and nothing inside it, and still reported
            # the block as OK. It checked 78 blocks and looked at 4 nodes.
            if key == "@graph":
                check(value, f"{path}.@graph", problems)
                continue
            if key.startswith("@"):
                continue
            check(value, f"{path}.{key}", problems)

    problems, blocks = [], 0
    for html_path in generated_html_paths(output_dir):
        text = html_path.read_text(encoding="utf-8")
        for raw in JSON_LD_RE.findall(text):
            blocks += 1
            rel = html_path.relative_to(output_dir)
            try:
                data = _json.loads(raw)
            except ValueError as exc:
                problems.append(f"{rel}: does not parse ({exc})")
                continue
            check(data, str(rel), problems)
    if problems:
        raise AssertionError(
            "Invalid JSON-LD — " + "; ".join(problems[:20])
            + (f" (+{len(problems) - 20} more)" if len(problems) > 20 else "")
        )
    return blocks


def assert_family_examples(sensors):
    """Fail the build if a family's `examples` string names a sensor owned
    by a different family.

    Each family's examples list should be accurate to its rows. The check
    matches comma-separated example tokens against sensor titles
    (case-insensitive, either side subsumes the other) and flags tokens
    that resolve to a sensor in another family.
    """
    # Map lowercased sensor title -> family slug
    title_to_family = {}
    for s in sensors:
        title_to_family[s["title"].lower()] = s.get("family", "")
    warnings = []
    for fam in FAMILIES:
        fam_slug = fam["slug"]
        examples = fam.get("examples", "")
        for token in (t.strip().lower() for t in examples.split(",")):
            if not token:
                continue
            for title, owner in title_to_family.items():
                # Match only on exact (case-insensitive) token == title, so
                # generic words like "contract" don't false-match "Contract
                # & Refinement Types" when they mean "Contract Tests".
                if token == title:
                    if owner and owner != fam_slug:
                        warnings.append(
                            f'family {fam_slug!r} examples name '
                            f'{token!r} but sensor {title!r} is owned by '
                            f'family {owner!r}'
                        )
    if warnings:
        details = "; ".join(warnings)
        raise AssertionError(
            f"Family examples / ownership mismatches — {details}. Fix the "
            f"examples list in FAMILIES or reassign the sensor."
        )


def assert_see_also_resolves(sensors):
    """Fail the build if any see_also token does not resolve to a sensor ID,
    a family slug, or the literal 'atlas'.

    Unresolved tokens are silently dropped by resolve_see_also; this check
    surfaces them so dangling references don't accumulate.
    """
    sensors_by_id = {s["id"] for s in sensors}
    family_slugs = {f["slug"] for f in FAMILIES}
    unresolved = []
    for sensor in sensors:
        for ref in sensor.get("see_also", []):
            if ref in sensors_by_id or ref in family_slugs or ref == "atlas":
                continue
            unresolved.append((sensor["id"], sensor["slug"], ref))
    if unresolved:
        details = "; ".join(
            f"{sid} ({slug}): {ref!r}" for sid, slug, ref in unresolved
        )
        raise AssertionError(
            f"Unresolved see_also tokens — {details}. Each see_also entry "
            f"must be a sensor ID, a family slug, or the literal 'atlas'."
        )


def assert_family_and_stack_level(sensors):
    """Fail the build when a sensor's `family` or `stack_level` does not
    match a known slug.

    A typo in frontmatter silently drops the sensor off the catalog and
    atlas (the detail page still generates, so check_links can't catch
    it). This check surfaces the mismatch.
    """
    family_slugs = {f["slug"] for f in FAMILIES}
    stack_slugs = {s["slug"] for s in STACK_LAYERS}
    bad = []
    for sensor in sensors:
        fam = sensor.get("family", "")
        if fam and fam not in family_slugs:
            bad.append((sensor["id"], sensor["slug"], "family", fam))
        lvl = sensor.get("stack_level", "")
        if lvl and lvl not in stack_slugs:
            bad.append((sensor["id"], sensor["slug"], "stack_level", lvl))
    if bad:
        details = "; ".join(
            f"{sid} ({slug}): {field}={val!r}" for sid, slug, field, val in bad
        )
        raise AssertionError(
            f"Unrecognized family/stack_level slugs — {details}. "
            f"Valid families: {sorted(family_slugs)}. "
            f"Valid stack levels: {sorted(stack_slugs)}."
        )


# ── Gate ordering ───────────────────────────────────────────────────────────
#
# THE RULE: nothing is written until every check that can run on the loaded
# model has passed.
#
# A gate that runs after promotion is not a gate — it is a post-mortem. Until
# #116 all four checks ran at the very end of main(), after 69 pages, the
# search index, the sitemap, the RSS feed AND the committed
# cli/data/sensors.json had already been written. A build that was going to
# fail still produced a complete, corrupt site first.
#
# So: validate_sensors() runs immediately after load_sensors() and before any
# generator. Only checks that genuinely need generated output (they grep the
# emitted HTML) may run afterwards, and they live in assert_output_invariants()
# so the split stays visible. If you add a check, it goes in validate_sensors()
# unless it physically cannot.
#
# Running the input gates first also fixes a second bug: a bad `family` slug
# used to die with a bare KeyError inside resolve_see_also / the atlas
# dependency graph during generation, so assert_family_and_stack_level's
# helpful "valid families are ..." message was unreachable. It is reachable now
# by construction, because generation no longer happens first.

def validate_sensors(sensors):
    """Every gate that can be answered from the loaded sensor data alone.

    Called before a single byte of output is written. Raises AssertionError
    on the first violated invariant.
    """
    print("Checking family / stack_level slugs...")
    assert_family_and_stack_level(sensors)
    print("  OK")

    print("Checking see_also resolution...")
    assert_see_also_resolves(sensors)
    print("  OK")

    print("Checking family examples / ownership...")
    assert_family_examples(sensors)
    print("  OK")


def assert_output_invariants(sensors, output_dir):
    """Gates that can only be answered by reading generated output.

    These grep the emitted HTML for prose that drifted away from the data, so
    they cannot run before generation. They are post-checks, not gates, and
    are labelled as such: a failure here means a bad site is already on disk.
    """
    print("Checking family-count consistency...")
    assert_family_count(output_dir)
    print("  OK")

    print("Checking sensor-count consistency...")
    assert_sensor_count(sensors, output_dir)
    print("  OK")

    print("Checking JSON-LD validity...")
    count = assert_json_ld_parses(output_dir)
    print(f"  OK ({count} blocks)")
