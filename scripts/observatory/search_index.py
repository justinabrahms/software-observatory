"""The client-side search index (search-index.json)."""

import html
import re

from .render import blurb_text
from .taxonomy import FAMILIES, FAMILY_BY_SLUG, family_url


SEARCH_STOPWORDS = frozenset("""
the a an and or but if of to in on for with is are was were be been being it its
this that these those as at by from not no you your we our they their he she his
her can could would should will may might must do does did done have has had
what which who when where why how all any both each few more most other some
such only own same so than too very just now into out up down over under again
""".split())


def search_terms(body_html, min_len=3):
    """Distinct lowercase words from a sensor body, for the search index.

    A deduplicated term set covers the whole entry; a truncated prose prefix
    only covers its opening, which is why searching 'flaky' or 'regression'
    used to return nothing.
    """
    text = html.unescape(re.sub(r"<[^>]+>", " ", body_html or ""))
    text = re.sub(r"[^A-Za-z0-9\s-]", " ", text).lower()
    return {
        w for w in text.split()
        if len(w) >= min_len and w not in SEARCH_STOPWORDS and not w.isdigit()
    }


def generate_search_index(sensors, output_dir):
    """Write search-index.json: title, family, url, and plain-text blurb
    for every sensor, plus an entry per family."""
    import json
    entries = []
    for f in FAMILIES:
        entries.append({
            "title": f["name"],
            "kind": "family",
            "family": f["name"],
            "url": family_url(f["slug"]),
            "blurb": f["question"],
        })
    for s in sensors:
        fam = FAMILY_BY_SLUG.get(s.get("family", ""), {})
        blurb = blurb_text(s.get("body_html", ""), limit=160)
        # "text" and "keywords" exist so search can match words that appear in
        # the body but not the title or blurb -- flaky, regression, performance.
        # A deduplicated term set rather than a prose prefix: a prefix misses
        # terms that appear late in the entry, which is most of them. Sorted so
        # the output is deterministic. js/main.js escapes on render, so these
        # stay unescaped here.
        text = " ".join(sorted(search_terms(s.get("body_html", ""))))
        keywords = " ".join(
            list(s.get("categories", []) or []) + s["slug"].split("-")
        ).lower()
        entries.append({
            "title": s["title"],
            "kind": "sensor",
            "family": fam.get("name", ""),
            "url": f"/sensors/{s['slug']}/",
            "blurb": blurb,
            "keywords": keywords,
            "text": text,
        })
    with open(output_dir / "search-index.json", "w") as f:
        json.dump(entries, f, indent=1, sort_keys=True)
