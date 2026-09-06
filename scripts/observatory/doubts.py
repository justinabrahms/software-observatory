"""The doubt vocabulary: shape checks and derived facts.

content/doubts.yaml is loaded by content.load_doubts(). This module holds
everything the build derives from it, so that the gates in gates.py and
the page in pages/doubts.py read the same facts and cannot disagree.

Two kinds of thing live here:

  - Shape rules for the file itself (required fields, valid origins, a
    sensor in at most one list per doubt, revealed_by only for
    retrospective sensors). gates.py raises on these before writing.

  - Facts the page derives from it (families per list, origin counts).
"""

import re

EDGE_KEYS = ("misread_as_closing", "closed_by", "revealed_by")
ORIGINS = ("mined", "coverage")
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

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
