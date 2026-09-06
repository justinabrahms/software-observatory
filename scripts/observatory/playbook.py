"""The playbook: shape checks and derived facts for content/playbook/*.md.

A play is the situational counterpart to a catalog entry. The catalog
answers "what is this sensor?"; a play answers "I am in situation X, what
do I point at it?". Three kinds:

  symptom         one thing the reader noticed, one doubt behind it, one
                  sensor to point at it, and the play to run if the doubt
                  survives.
  starting-point  where the reader is (the sensors already running) and an
                  ordered list of what to add, each step closing a doubt
                  the previous ones left open.
  composition     a minimal stack for one shape of system, composed by
                  distinct doubts closed rather than one sensor per family.

Every edge a play claims (this sensor closes / reveals that doubt) must
already be in content/doubts.yaml. The playbook is a route through the
doubt graph, so it may not assert an edge the graph does not have; the
gate in gates.py fails the build on one that is missing, and the pages
compute "what is already closed" and "what this stack leaves open" from
the yaml rather than from anything the play says.
"""

import re

KINDS = ("symptom", "starting-point", "composition")
KIND_LABELS = {
    "symptom": "Symptom",
    "starting-point": "Starting point",
    "composition": "Composition",
}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SYMPTOM_SECTIONS = ("Point this at it", "Reading it", "If the doubt survives")


def _rows(play):
    """The sensor rows of a play: steps for a starting point, stack for a
    composition, one synthetic row for a symptom. Each is a dict with
    sensor / closes / reveals, so the derived facts can treat kinds alike."""
    if play["kind"] == "starting-point":
        return play.get("steps") or []
    if play["kind"] == "composition":
        return play.get("stack") or []
    return []


def shape_errors(plays, doubts, sensors):
    """Every way a play file can be malformed, as a list of messages."""
    by_slug = {s["slug"]: s for s in sensors}
    by_id = {d["id"]: d for d in doubts}
    play_slugs = {p["slug"] for p in plays}
    errors = []

    def closes_ok(sensor, did):
        return did in by_id and sensor in by_id[did]["closed_by"]

    def reveals_ok(sensor, did):
        return did in by_id and sensor in by_id[did]["revealed_by"]

    def check_rows(where, rows, key):
        for i, row in enumerate(rows):
            sensor = row.get("sensor") if isinstance(row, dict) else None
            at = f"{where}: {key}[{i + 1}]"
            if not sensor or sensor not in by_slug:
                errors.append(f"{at} names unknown sensor {sensor!r}")
                continue
            closes = list(row.get("closes") or [])
            reveals = list(row.get("reveals") or [])
            if not closes and not reveals:
                errors.append(f"{at} ({sensor}) claims no doubt; a row must close or reveal one")
            for did in closes:
                if not closes_ok(sensor, did):
                    errors.append(f"{at}: doubts.yaml does not say {sensor} closes {did}")
            for did in reveals:
                if not reveals_ok(sensor, did):
                    errors.append(f"{at}: doubts.yaml does not say {sensor} reveals {did}")
            if not str(row.get("why") or "").strip():
                errors.append(f"{at} ({sensor}) has no why")

    for p in plays:
        where = f"playbook/{p['slug']}.md"
        if not SLUG_RE.match(p["slug"]):
            errors.append(f"{where}: filename must be a lowercase slug")
        kind = p.get("kind")
        if kind not in KINDS:
            errors.append(f"{where}: kind must be one of {', '.join(KINDS)} (got {kind!r})")
            continue
        if not str(p.get("title") or "").strip():
            errors.append(f"{where}: title is required")

        if kind == "symptom":
            for field in ("noticed",):
                if not str(p.get(field) or "").strip():
                    errors.append(f"{where}: {field} is required")
            did, sensor = p.get("doubt"), p.get("sensor")
            if did not in by_id:
                errors.append(f"{where}: doubt names unknown doubt {did!r}")
            if sensor not in by_slug:
                errors.append(f"{where}: sensor names unknown sensor {sensor!r}")
            if did in by_id and sensor in by_slug and not (closes_ok(sensor, did) or reveals_ok(sensor, did)):
                errors.append(f"{where}: doubts.yaml does not say {sensor} closes or reveals {did}")
            nxt = p.get("next")
            if nxt and nxt not in play_slugs:
                errors.append(f"{where}: next names unknown play {nxt!r}")
            if nxt == p["slug"]:
                errors.append(f"{where}: next points at itself")
            if p.get("sections") != list(SYMPTOM_SECTIONS):
                errors.append(f"{where}: body must have exactly these h2 sections in order: "
                              + ", ".join(SYMPTOM_SECTIONS)
                              + f" (got {p.get('sections')})")

        elif kind == "starting-point":
            if not str(p.get("where") or "").strip():
                errors.append(f"{where}: where is required")
            for s in p.get("have") or []:
                if s not in by_slug:
                    errors.append(f"{where}: have names unknown sensor {s!r}")
            if not p.get("steps"):
                errors.append(f"{where}: steps is required")
            check_rows(where, p.get("steps") or [], "steps")
            # The page says "each step closes a doubt the previous ones left
            # open". Two closers of one doubt count once (the composition
            # rule), so a step that only re-closes is not a step.
            covered = set(doubts_closed_by(p.get("have") or [], doubts))
            covered |= set(doubts_revealed_by(p.get("have") or [], doubts))
            for i, row in enumerate(p.get("steps") or []):
                if not isinstance(row, dict):
                    continue
                claimed = list(row.get("closes") or []) + list(row.get("reveals") or [])
                for did in claimed:
                    if did in covered:
                        errors.append(f"{where}: steps[{i + 1}] ({row.get('sensor')}) claims "
                                      f"{did}, which `have` or an earlier step already covers; "
                                      "two closers of one doubt count once")
                covered |= set(claimed)
            for i, sk in enumerate(p.get("skip") or []):
                if not isinstance(sk, dict) or sk.get("sensor") not in by_slug:
                    errors.append(f"{where}: skip[{i + 1}] names unknown sensor")
                elif not str(sk.get("reason") or "").strip():
                    errors.append(f"{where}: skip[{i + 1}] ({sk['sensor']}) has no reason")

        elif kind == "composition":
            if not str(p.get("shape") or "").strip():
                errors.append(f"{where}: shape is required")
            if not p.get("stack"):
                errors.append(f"{where}: stack is required")
            check_rows(where, p.get("stack") or [], "stack")
            closed = {}
            for row in p.get("stack") or []:
                for did in (row.get("closes") or []) if isinstance(row, dict) else []:
                    if did in closed:
                        errors.append(f"{where}: {did} is closed by both {closed[did]} and "
                                      f"{row.get('sensor')}; a stack composes by distinct doubts")
                    closed[did] = row.get("sensor")
            for i, lo in enumerate(p.get("left_open") or []):
                if not isinstance(lo, dict) or lo.get("doubt") not in by_id:
                    errors.append(f"{where}: left_open[{i + 1}] names unknown doubt")
                elif not str(lo.get("reason") or "").strip():
                    errors.append(f"{where}: left_open[{i + 1}] ({lo['doubt']}) has no reason")
                elif lo["doubt"] in closed:
                    errors.append(f"{where}: {lo['doubt']} is both closed by {closed[lo['doubt']]} "
                                  "and left open")
    return errors


def doubts_closed_by(slugs, doubts):
    """Doubt ids (in vocabulary order) that at least one of `slugs` closes."""
    slugs = set(slugs)
    return [d["id"] for d in doubts if slugs & set(d["closed_by"])]


def doubts_revealed_by(slugs, doubts):
    slugs = set(slugs)
    return [d["id"] for d in doubts if slugs & set(d["revealed_by"])]


def stack_coverage(play, doubts):
    """For a starting point or composition: (closed ids, revealed ids,
    untouched ids), all in vocabulary order. Untouched excludes anything the
    play deliberately lists as left_open."""
    closed, revealed = set(), set()
    if play["kind"] == "starting-point":
        closed |= set(doubts_closed_by(play.get("have") or [], doubts))
    for row in _rows(play):
        closed |= set(row.get("closes") or [])
        revealed |= set(row.get("reveals") or [])
    left_open = {lo["doubt"] for lo in play.get("left_open") or []}
    order = [d["id"] for d in doubts]
    return (
        [i for i in order if i in closed],
        [i for i in order if i in revealed and i not in closed],
        [i for i in order if i not in closed and i not in revealed and i not in left_open],
    )


def plays_by_sensor(plays):
    """{sensor slug: [play, ...]} for every play that names the sensor
    anywhere it acts (not in `have` or `skip`, which are the reader's
    existing state, and not in prose)."""
    out = {}
    for p in plays:
        named = set()
        if p["kind"] == "symptom":
            named.add(p.get("sensor"))
        for row in _rows(p):
            named.add(row.get("sensor"))
        for s in sorted(x for x in named if x):
            out.setdefault(s, []).append(p)
    return out


def sort_key(play):
    return (KINDS.index(play["kind"]), play.get("order", 100), play["title"].lower())
