#!/usr/bin/env python3
"""
Which sensor entries are next in line for an editorial review pass.

The catalog records a human read as `last_reviewed:` in an entry's
frontmatter. An entry with no such key has never been read — the site renders
that as "pending" rather than inventing a date (see observatory/review.py).
This script answers the question that follows from that: *which ones, and in
what order?*

The queue is ordered by how long an entry has gone unread:

  1. Never reviewed, oldest-published first. A page that has been on the site
     since August and never re-read is further behind than one added last
     week, so first-seen date is the tiebreak, not slug order. First-seen
     dates are day-granular (that is all the cache stores), so entries added
     on the same day are ordered by slug — within one day the order carries
     no meaning and should not be read as one.
  2. Reviewed, oldest review first. Once the backlog is empty this is the
     whole queue, and `--stale` narrows it to the entries the site itself
     flags as stale (older than review.REVIEW_STALE_MONTHS).

First-seen dates come from the committed scripts/first_seen.json, falling
back to git for slugs the cache has never seen — the same two sources the
feed uses. Unlike the build, this script never writes that cache back: a
read-only listing tool must not dirty a tracked file as a side effect of
being run.

Ages are measured against the catalog's own newest date, never the wall
clock, for the same reason the build is (observatory/dates.catalog_as_of).

Usage:
    .venv/bin/python scripts/review_queue.py            # next 4, as a table
    .venv/bin/python scripts/review_queue.py -n 10      # next 10
    .venv/bin/python scripts/review_queue.py --all
    .venv/bin/python scripts/review_queue.py --reviewed # include reviewed
    .venv/bin/python scripts/review_queue.py --paths    # paths only, for xargs
    .venv/bin/python scripts/review_queue.py --json

    make review-queue            # the default view
    make review-queue N=10
"""

import argparse
import json
import sys
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SITE_ROOT / "scripts"))

from observatory import config
from observatory.content import parse_frontmatter
from observatory.dates import _git_first_seen, _iso_date, catalog_as_of
from observatory.review import REVIEW_STALE_MONTHS, review_status


def load_entries():
    """[{slug, path, title, family, last_reviewed}] for every sensor entry.

    Frontmatter only — this deliberately does not call content.load_sensors(),
    which renders every body to HTML. Nothing here looks at a body.
    """
    entries = []
    for path in sorted((config.CONTENT_DIR / "sensors").glob("*.md")):
        meta, _ = parse_frontmatter(path)
        entries.append({
            "slug": path.stem,
            "path": str(path.relative_to(SITE_ROOT)),
            "title": meta.get("title", path.stem),
            "family": meta.get("family", ""),
            "last_reviewed": _iso_date(meta.get("last_reviewed")),
        })
    return entries


def first_seen(entries):
    """{slug: YYYY-MM-DD}, cache first and git for the rest. Never writes."""
    dates = {}
    try:
        with open(config.FIRST_SEEN_PATH) as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            dates = {k: v for k, v in loaded.items() if _iso_date(v)}
    except (OSError, ValueError):
        pass

    missing = {e["slug"] for e in entries} - set(dates)
    if missing:
        dates.update({k: v for k, v in _git_first_seen().items() if k in missing})
    return dates


def build_queue(entries, as_of, published):
    """The entries in review order, each annotated with why it sits there."""
    for e in entries:
        e["first_seen"] = published.get(e["slug"], "")
        status = review_status(e, as_of)
        e["months"] = status["months"]
        e["stale"] = status["stale"]

    unreviewed = sorted(
        (e for e in entries if not e["last_reviewed"]),
        key=lambda e: (e["first_seen"] or "9999-99-99", e["slug"]),
    )
    reviewed = sorted(
        (e for e in entries if e["last_reviewed"]),
        key=lambda e: (e["last_reviewed"], e["slug"]),
    )
    return unreviewed, reviewed


def render_table(queue, as_of, totals):
    unreviewed_n, reviewed_n = totals
    slug_w = max([len(e["slug"]) for e in queue] + [len("entry")])
    fam_w = max([len(e["family"] or "—") for e in queue] + [len("family")])
    lines = [
        f"Review queue — {unreviewed_n} never reviewed, {reviewed_n} reviewed "
        f"(ages measured against {as_of}, the catalog's newest date)",
        "",
        f"  {'entry'.ljust(slug_w)}  {'family'.ljust(fam_w)}  "
        f"{'first seen'.ljust(10)}  reviewed",
    ]
    for e in queue:
        if e["last_reviewed"]:
            age = f"{e['last_reviewed']}"
            if e["months"] is not None:
                age += f"  ({e['months']}mo{', stale' if e['stale'] else ''})"
        else:
            age = "pending — never reviewed"
        lines.append(
            f"  {e['slug'].ljust(slug_w)}  {(e['family'] or '—').ljust(fam_w)}  "
            f"{(e['first_seen'] or '?').ljust(10)}  {age}"
        )
    lines += ["", "Files:"]
    lines += [f"  {e['path']}" for e in queue]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="List sensor entries in editorial-review order.",
    )
    parser.add_argument("-n", "--limit", type=int, default=4,
                        help="how many entries to show (default 4)")
    parser.add_argument("--all", action="store_true",
                        help="show the whole queue, ignoring --limit")
    parser.add_argument("--reviewed", action="store_true",
                        help="include already-reviewed entries, oldest review "
                             "first, after the never-reviewed ones")
    parser.add_argument("--stale", action="store_true",
                        help=f"only entries the site flags as stale (reviewed "
                             f"over {REVIEW_STALE_MONTHS} months ago); implies "
                             f"--reviewed")
    parser.add_argument("--paths", action="store_true",
                        help="print content paths only, one per line")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="print the queue as JSON")
    args = parser.parse_args(argv)

    entries = load_entries()
    published = first_seen(entries)
    as_of = catalog_as_of(entries, published)
    unreviewed, reviewed = build_queue(entries, as_of, published)

    if args.stale:
        queue = [e for e in reviewed if e["stale"]]
    elif args.reviewed:
        queue = unreviewed + reviewed
    else:
        queue = unreviewed
    if not args.all:
        queue = queue[:max(args.limit, 0)]

    if args.as_json:
        print(json.dumps({"as_of": as_of, "queue": queue}, indent=2))
    elif args.paths:
        for e in queue:
            print(e["path"])
    elif not queue:
        print("Review queue is empty — every entry carries a review date."
              if not args.stale else
              f"No entry is older than {REVIEW_STALE_MONTHS} months.")
    else:
        print(render_table(queue, as_of, (len(unreviewed), len(reviewed))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
