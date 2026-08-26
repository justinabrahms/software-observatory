"""Dates: normalization, first-seen publication dates, and the catalog epoch.

The build must never read the wall clock — every date it renders comes from
content or from git history, so two builds of the same corpus are
byte-identical."""

import re
from pathlib import Path

from . import config


def _iso_date(value):
    """Normalize a frontmatter date (str or datetime.date) to YYYY-MM-DD, or
    return None if it isn't one."""
    text = str(value or "")[:10]
    return text if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text) else None


def _git_first_seen():
    """{slug: YYYY-MM-DD} for every content/sensors/*.md, from the commit
    that added it. Returns {} when git is unavailable or the history is
    shallow — the caller falls back to the committed cache."""
    import subprocess
    try:
        proc = subprocess.run(
            ["git", "-C", str(config.SITE_ROOT), "log", "--reverse", "--diff-filter=A",
             "--format=@%aI", "--name-only", "--", "content/sensors"],
            capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    if proc.returncode != 0:
        return {}
    dates, current = {}, None
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("@"):
            current = line[1:11]
        elif line.endswith(".md") and current:
            dates.setdefault(Path(line).stem, current)
    return dates


def first_seen_dates(sensors):
    """{slug: YYYY-MM-DD} publication dates for the feed.

    Git is the honest source for "when did this entry appear", but it is not
    always reachable (shallow checkouts, tarball builds), so answers are
    cached in scripts/first_seen.json. The cache wins wherever it has an
    entry — that keeps the dates stable even if history is later rewritten —
    and git only fills in slugs the cache has never seen. Anything neither
    knows about falls back to `last_reviewed`.
    """
    import json
    cache = {}
    try:
        with open(config.FIRST_SEEN_PATH) as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            cache = {k: v for k, v in loaded.items() if _iso_date(v)}
    except (OSError, ValueError):
        pass

    slugs = {s["slug"] for s in sensors}
    dates = {k: v for k, v in cache.items() if k in slugs}
    missing = slugs - set(dates)
    if missing:
        for slug, date in _git_first_seen().items():
            if slug in missing:
                dates[slug] = date
    for s in sensors:
        dates.setdefault(s["slug"], _iso_date(s.get("last_reviewed")) or "1970-01-01")

    if dates != cache:
        with open(config.FIRST_SEEN_PATH, "w") as f:
            json.dump(dates, f, indent=1, sort_keys=True)
            f.write("\n")
    return dates


def catalog_as_of(sensors, published=None):
    """The newest date anywhere in the catalog's own data (YYYY-MM-DD).

    DETERMINISM: this is the reference date for everything the build renders
    about time — the llms-full.txt header, the review-age display. It is
    derived from content (review dates and first-seen dates), never from the
    clock, because a build that changes nothing must produce a byte-identical
    tree (#91). datetime.now() here would rewrite every sensor page every day.
    """
    dates = [_iso_date(s.get("last_reviewed")) for s in sensors]
    dates += [_iso_date(d) for d in (published or {}).values()]
    dates = [d for d in dates if d]
    return max(dates) if dates else None
