"""Review provenance: how fresh a sensor entry's last human read is.

Ages are measured against the catalog's own newest date, never against the
wall clock (see dates.catalog_as_of) — a clock-dependent age rewrites every
sensor page the moment the month rolls over."""

import html

from .dates import _iso_date


# ── Review provenance ───────────────────────────────────────────────────────
#
# `last_reviewed` is a claim that a human read this entry on that day. The
# build must therefore render three states, not one: reviewed recently,
# reviewed a long time ago, and never re-reviewed. An absent date is a
# first-class answer — "not yet re-reviewed" is honest, and a date the author
# has not earned is not (#112).
#
# DETERMINISM: ages are measured against catalog_as_of() — the newest date in
# the catalog's own data — and never against datetime.now(). Wall-clock ages
# would rewrite all 59 sensor pages the moment the month rolled over, which is
# the churn #91 was fixed to stop. The trade-off is that "14 months ago" means
# "14 months older than the freshest thing in this catalog", which is what the
# tooltip says; it is a claim the artifact can actually support.

REVIEW_STALE_MONTHS = 12


def _months_between(earlier, later):
    """Whole months from one YYYY-MM-DD to another (never negative)."""
    import datetime
    a = datetime.date.fromisoformat(earlier)
    b = datetime.date.fromisoformat(later)
    months = (b.year - a.year) * 12 + (b.month - a.month)
    if b.day < a.day:
        months -= 1
    return max(months, 0)


def review_status(sensor, as_of):
    """How this entry's review date should be rendered.

    Returns {"reviewed": 'YYYY-MM-DD' or None, "months": int or None,
    "stale": bool}.
    """
    reviewed = _iso_date(sensor.get("last_reviewed"))
    if not reviewed or not as_of:
        return {"reviewed": reviewed, "months": None, "stale": False}
    months = _months_between(reviewed, as_of)
    return {
        "reviewed": reviewed,
        "months": months,
        "stale": months >= REVIEW_STALE_MONTHS,
    }


def review_dd_html(sensor, as_of):
    """The <dd> for the sensor page's "Reviewed" row."""
    status = review_status(sensor, as_of)
    if not status["reviewed"]:
        return (
            '<span class="review-unreviewed" title="This entry carries no '
            'last_reviewed date: nobody has re-read it since it was written. '
            'An absent date is reported as absent rather than filled in.">'
            "not yet re-reviewed</span>"
        )
    month = status["reviewed"][:7]
    if status["months"] is None:
        return html.escape(month)
    tooltip = html.escape(
        f"Age measured against {as_of}, the newest date in the catalog. "
        f"The build never uses the wall clock, so this page is byte-identical "
        f"between builds.",
        quote=True,
    )
    if status["months"] == 0:
        age = "current"
    elif status["months"] == 1:
        age = "1 month ago"
    else:
        age = f"{status['months']} months ago"
    classes = "review-age review-stale" if status["stale"] else "review-age"
    stale_mark = (
        f' <span class="review-stale-flag" title="Older than '
        f'{REVIEW_STALE_MONTHS} months.">stale</span>'
        if status["stale"] else ""
    )
    return (
        f'{html.escape(month)} <span class="{classes}" title="{tooltip}">'
        f"\u2014 {age}</span>{stale_mark}"
    )


def reviewed_newest_first(sensors):
    """Entries that carry a real review date, newest first.

    Entries without one are EXCLUDED rather than sorted as if they were
    fresh: a missing date is not a recent date.
    """
    dated = [s for s in sensors if _iso_date(s.get("last_reviewed"))]
    return sorted(
        dated,
        key=lambda s: (_iso_date(s["last_reviewed"]), s["slug"]),
        reverse=True,
    )


def review_dates_discriminate(sensors):
    """True when `last_reviewed` actually tells entries apart.

    Today every entry carries the same bulk stamp, so ordering by it is
    ordering by a constant and any "recently reviewed" list is a fiction.
    The moment the stamps become real — different dates, or some entries
    with no date at all — this returns True and the homepage switches to a
    genuine ordering on its own. Nobody has to remember to flip it.
    """
    return len({_iso_date(s.get("last_reviewed")) for s in sensors}) > 1
