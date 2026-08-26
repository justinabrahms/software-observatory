"""Loading the sensor corpus and the derived views of it.

Frontmatter parsing, the corpus load, backlinks, see_also resolution, and the
per-sensor OG-card inputs. Everything here answers "what did the author
write", never "what does the page look like"."""

import yaml

from . import config
from .config import SITE_URL
from .render import fix_link_depths, render_markdown
from .taxonomy import FAMILY_BY_SLUG, family_url


# ── Frontmatter parsing ─────────────────────────────────────────────────────

def parse_frontmatter(filepath):
    """Parse a markdown file with YAML frontmatter. Returns (meta, body)."""
    with open(filepath, "r") as f:
        content = f.read()

    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2].strip()
    return meta, body


# ── Sensor loading ──────────────────────────────────────────────────────────

def load_sensors():
    """Load all sensor markdown files. Returns list of dicts."""
    sensors = []
    sensor_dir = config.CONTENT_DIR / "sensors"
    if not sensor_dir.exists():
        return sensors

    sensor_slugs = {p.stem for p in sensor_dir.glob("*.md")}
    for filepath in sorted(sensor_dir.glob("*.md")):
        meta, body = parse_frontmatter(filepath)
        slug = filepath.stem
        meta["slug"] = slug
        meta["body_html"] = fix_link_depths(render_markdown(body), sensor_slugs=sensor_slugs)
        meta["filename"] = str(filepath)
        sensors.append(meta)

    return sensors


def compute_backlinks(sensors):
    """For each sensor, find all other sensors that reference it in see_also."""
    by_id = {s["id"]: s for s in sensors}
    backlinks = {s["id"]: [] for s in sensors}

    for sensor in sensors:
        for ref_id in sensor.get("see_also", []):
            if ref_id in backlinks:
                ref_sensor = by_id.get(ref_id)
                if ref_sensor:
                    backlinks[ref_id].append({
                        "from_id": sensor["id"],
                        "from_title": sensor["title"],
                        "from_slug": sensor["slug"],
                        "from_family": sensor.get("family", ""),
                        "context": f"references this as a related sensor",
                    })

    return backlinks


def resolve_see_also(see_also_ids, sensors_by_id, families_by_slug):
    """Resolve see_also IDs to objects with title, slug, family, url.
    All urls are site-absolute."""
    results = []
    for ref in see_also_ids:
        if ref in sensors_by_id:
            s = sensors_by_id[ref]
            results.append({
                "title": s["title"],
                "family": FAMILY_BY_SLUG.get(s.get("family", ""), {}).get("name", ""),
                "family_slug": s.get("family", ""),
                "url": f"/sensors/{s['slug']}/",
            })
        elif ref in families_by_slug:
            f = families_by_slug[ref]
            results.append({
                "title": f["name"],
                "family": "Family",
                "family_slug": f["slug"],
                "url": family_url(f["slug"]),
            })
        elif ref == "atlas":
            results.append({
                "title": "Sensor Atlas",
                "family": "Atlas",
                "family_slug": "atlas",
                "url": "/atlas/",
            })
    return results


def og_card_items(sensors):
    """The inputs each per-sensor OG card is rendered from (see gen_og.py)."""
    return [
        {
            "slug": s["slug"],
            "title": s.get("title", ""),
            "family_slug": s.get("family", ""),
            "family_name": FAMILY_BY_SLUG.get(s.get("family", ""), {}).get(
                "name", s.get("family", "")
            ),
            "oracle": s.get("oracle", ""),
            "independence": s.get("independence", ""),
            "type": s.get("type", ""),
            "id": s.get("id", ""),
        }
        for s in sensors
    ]


def sensor_og_image(slug):
    """Absolute URL of a sensor's own OG card, or None if it hasn't been
    rendered (missing browser, new entry on a machine without playwright) —
    in which case the caller falls back to the site-wide card."""
    if (config.SITE_ROOT / "og" / "cards" / f"{slug}.png").exists():
        return f"{SITE_URL}/og/cards/{slug}.png"
    return None
