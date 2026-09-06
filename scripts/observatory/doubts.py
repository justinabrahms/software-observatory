"""The doubt vocabulary: shape checks and derived facts.

content/doubts.yaml is loaded by content.load_doubts(). This module holds
everything the build derives from it, so that the gates in gates.py and
the page in pages/doubts.py read the same facts and cannot disagree.

Two kinds of thing live here:

  - Shape rules for the file itself (required fields, valid origins, a
    sensor in at most one list per doubt, revealed_by only for
    retrospective sensors). gates.py raises on these before writing.

  - Prose claims. The page's "What the shape says" section makes specific
    claims about specific doubts ("wrong logic has an empty left side").
    Each is a Claim: does it apply to this catalog, does it hold, and what
    sentence it licenses. The gate fails the build when a claim applies
    and does not hold, so an edit to the yaml that falsifies a sentence
    fails CI instead of leaving a false sentence on the site. A claim that
    does not apply (its subjects are not in this catalog, as in the
    fixture corpus) renders nothing.
"""

import re
from collections import namedtuple

EDGE_KEYS = ("misread_as_closing", "closed_by", "revealed_by")
ORIGINS = ("mined", "coverage")
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

Claim = namedtuple("Claim", "applies holds label sentence")


def shape_errors(doubts, sensors):
    """Every way the yaml can be malformed, as a list of messages."""
    by_slug = {s["slug"]: s for s in sensors}
    errors = []
    seen = set()
    for i, d in enumerate(doubts):
        did = d.get("id")
        where = f"doubt #{i + 1} ({did or 'no id'})"
        if not did or not ID_RE.match(str(did)):
            errors.append(f"{where}: id must be a lowercase slug (it is the page anchor)")
        elif did in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(did)
        for field in ("name", "description"):
            if not str(d.get(field) or "").strip():
                errors.append(f"{where}: {field} is required")
        if d.get("origin") not in ORIGINS:
            errors.append(f"{where}: origin must be one of {', '.join(ORIGINS)} "
                          f"(got {d.get('origin')!r})")
        placed = {}
        for key in EDGE_KEYS:
            for slug in d.get(key, []):
                if slug not in by_slug:
                    errors.append(f"{where}: {key} names unknown sensor {slug}")
                    continue
                if slug in placed:
                    errors.append(f"{where}: {slug} is in both {placed[slug]} and {key}; "
                                  "a sensor takes one side of a doubt")
                placed[slug] = key
                if key == "revealed_by" and by_slug[slug].get("type") != "retrospective":
                    errors.append(f"{where}: revealed_by names {slug}, which is "
                                  f"type: {by_slug[slug].get('type')}; only a "
                                  "retrospective sensor reveals a doubt after the fact")
    return errors


def families_of(slugs, by_slug):
    return {by_slug[s]["family"] for s in slugs if s in by_slug}


def origin_counts(doubts):
    return {o: sum(1 for d in doubts if d.get("origin") == o) for o in ORIGINS}


def prose_claims(doubts, sensors):
    """The specific claims the page's prose makes, each checkable."""
    by_id = {d["id"]: d for d in doubts}
    by_slug = {s["slug"]: s for s in sensors}
    claims = []

    def get(did):
        return by_id.get(did)

    # Wrong logic: nothing is misread as closing it.
    d = get("wrong-logic")
    claims.append(Claim(
        applies=d is not None,
        holds=d is not None and not d["misread_as_closing"],
        label="wrong-logic has an empty misread side",
        sentence=(
            'And <em>wrong logic</em> has an empty left side: nobody reads a '
            'clean compile or type check as correct code. The belief engineers '
            'actually hold is that a class of bugs is gone, which is true.'),
    ))

    # Unasserted execution splits one family: everything that closes it is
    # in a single family, and that same family has sensors on the misread
    # side too (the coverage sensors and mutation testing are both
    # test-effectiveness). Snapshot tests, from another family, are also
    # misread, which is why the sentence names the closers' family and not
    # the whole left side.
    d = get("unasserted-execution")
    if d is not None:
        closer_fams = families_of(d["closed_by"], by_slug)
        misread_fams = families_of(d["misread_as_closing"], by_slug)
        holds = len(closer_fams) == 1 and closer_fams <= misread_fams
    else:
        holds = False
    claims.append(Claim(
        applies=d is not None,
        holds=bool(holds),
        label="unasserted-execution's closers share one family with some of its misread sensors",
        sentence=(
            '<em>Unasserted execution</em> splits one family: the coverage '
            'sensors are misread as closing it, and mutation testing, in the '
            'same family, closes it.'),
    ))

    # Escaped defect rate reveals late effects; it does not close them.
    d = get("late-effects")
    s = "escaped-defect-rate" in by_slug
    claims.append(Claim(
        applies=d is not None and s,
        holds=(d is not None and s and "escaped-defect-rate" in d["revealed_by"]
               and "escaped-defect-rate" not in d["closed_by"]),
        label="escaped-defect-rate reveals late-effects rather than closing it",
        sentence=(
            'Escaped defect rate cannot close <a href="#late-effects">late '
            'effects</a> before shipping; it is the sensor that shows, months '
            'later, that the doubt was real.'),
    ))

    # Missing behavior and wrong specification end at human review and
    # outcome sensors: every closer is in the comprehension family or at
    # the user-outcome rung.
    def ends_at_people(d):
        return all(
            by_slug[s]["family"] == "comprehension" or by_slug[s].get("stack_level") == "user-outcome"
            for s in d["closed_by"] if s in by_slug)
    a, b = get("missing-behavior"), get("wrong-specification")
    claims.append(Claim(
        applies=a is not None and b is not None,
        holds=a is not None and b is not None and ends_at_people(a) and ends_at_people(b),
        label="missing-behavior and wrong-specification close only at review or user-outcome sensors",
        sentence=(
            'Two doubts are nearly unclosable from inside the catalog. '
            '<em>Missing behavior</em> and <em>wrong specification</em> both '
            'end at human review and outcome sensors.'),
    ))
    return claims


def claim_failures(doubts, sensors):
    return [c.label for c in prose_claims(doubts, sensors) if c.applies and not c.holds]
