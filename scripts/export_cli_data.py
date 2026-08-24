"""Export the sensor catalog to cli/data/sensors.json for the npm CLI.

Reads every content/sensors/*.md (YAML frontmatter + markdown body) and
emits a single self-contained JSON document the CLI can query offline.
Reuses the parsing and rendering helpers from scripts/build.py so the two
stay in lockstep.

Run directly (.venv/bin/python scripts/export_cli_data.py) or via
scripts/build.py, which calls export() at the end of every build.
"""

import datetime
import html
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

import build

OUT_PATH = os.path.join(REPO_ROOT, "cli", "data", "sensors.json")

HTML_TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")
NON_WORD_RE = re.compile(r"[^\w]+")


def family_index(family_slug):
    """1-based position of the family in FAMILIES, for deterministic sorting."""
    for index, family in enumerate(build.FAMILIES, start=1):
        if family["slug"] == family_slug:
            return index
    return len(build.FAMILIES)


def to_search_text(body_html):
    """Flatten rendered body HTML to plain text (case preserved).

    Callers lowercase at comparison time; keeping the original case lets
    the CLI render readable entry text instead of a downcased blob."""
    text = HTML_TAG_RE.sub(" ", body_html)
    text = html.unescape(text)
    return WHITESPACE_RE.sub(" ", text).strip()


def tokenize(*parts):
    text = " ".join(parts).lower()
    return sorted({token for token in NON_WORD_RE.split(text) if len(token) >= 3})


def resolve_refs(refs, sensors_by_id):
    """Classify each see_also entry as a sensor ID, family slug, or page ref.

    Handles the `<family>-family` shorthand used in a few sources, which the
    site's own resolver silently drops.
    """
    sensor_ids = []
    family_slugs = []
    pages = []
    for ref in refs:
        if ref in sensors_by_id:
            sensor_ids.append(ref)
        elif ref in build.FAMILY_BY_SLUG:
            family_slugs.append(ref)
        elif ref.endswith("-family") and ref[: -len("-family")] in build.FAMILY_BY_SLUG:
            family_slugs.append(ref[: -len("-family")])
        else:
            pages.append(ref)
    return sensor_ids, family_slugs, pages


def json_default(value):
    # PyYAML turns unquoted dates like `last_reviewed: 2026-08-23` into
    # datetime.date objects; emit them as ISO strings.
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    return str(value)


def export():
    sensors = build.load_sensors()
    sensors_by_id = {s["id"]: s for s in sensors}

    out_sensors = []
    for sensor in sensors:
        see_also = sensor.get("see_also") or []
        ref_ids, ref_families, ref_pages = resolve_refs(see_also, sensors_by_id)
        body_text = to_search_text(sensor.get("body_html", ""))
        known_keys = {
            "id", "title", "family", "slug", "see_also", "body_html", "filename",
        }
        extra_frontmatter = {k: v for k, v in sensor.items() if k not in known_keys}
        out_sensors.append(
            {
                "id": sensor.get("id", ""),
                "slug": sensor["slug"],
                "title": sensor.get("title", sensor["slug"]),
                "family": sensor.get("family", ""),
                "frontmatter": extra_frontmatter,
                "body_html": sensor.get("body_html", ""),
                "body_text": body_text,
                "tokens": tokenize(sensor.get("id", ""), sensor["slug"], body_text.lower()),
                "see_also_ids": ref_ids,
                "see_also_families": ref_families,
                "see_also_pages": ref_pages,
                "url_path": "sensors/%s/" % sensor["slug"],
            }
        )
    out_sensors.sort(key=lambda s: (family_index(s["family"]), s["slug"]))

    counts = {}
    for sensor in out_sensors:
        counts[sensor["family"]] = counts.get(sensor["family"], 0) + 1
    families = [
        {
            "slug": f["slug"],
            "name": f["name"],
            "num": f["num"],
            "question": f["question"],
            "examples": f["examples"],
            "count": counts.get(f["slug"], 0),
        }
        for f in build.FAMILIES
    ]

    document = {
        "version": 1,
        "generated_at": datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "site": build.SITE_URL,
        "families": families,
        "sensors": out_sensors,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, ensure_ascii=False, default=json_default)
        handle.write("\n")
    return len(out_sensors), len(families)


if __name__ == "__main__":
    sensor_count, family_count = export()
    print("Wrote %s (%d sensors, %d families)" % (OUT_PATH, sensor_count, family_count))
