#!/usr/bin/env python3
"""
Frontmatter validator for sensor entries.

Checks every content/sensors/*.md frontmatter field against the known
constants in build.py: family, oracle, independence, latency, stack_level,
actionability, type, see_also, and id uniqueness. Exits 1 on any violation,
so it can gate CI alongside check_links.py.

Usage:
    .venv/bin/python scripts/check_frontmatter.py
"""

import sys
import glob
from pathlib import Path

import yaml

SITE_ROOT = Path(__file__).resolve().parent.parent
SENSOR_DIR = SITE_ROOT / "content" / "sensors"

sys.path.insert(0, str(SITE_ROOT / "scripts"))
from build import (
    FAMILIES,
    FAMILY_BY_SLUG,
    STACK_LAYERS,
    LATENCY_LABELS,
    ORACLE_WIDTHS,
    INDEPENDENCE_DOTS,
)

VALID_FAMILIES = {f["slug"] for f in FAMILIES}
VALID_STACK_LEVELS = {s["slug"] for s in STACK_LAYERS}
VALID_ORACLES = set(ORACLE_WIDTHS.keys())
VALID_INDEPENDENCE = set(INDEPENDENCE_DOTS.keys())
VALID_LATENCIES = set(LATENCY_LABELS.keys())
VALID_ACTIONABILITY = {"blocking", "exploratory", "guiding"}
VALID_TYPES = {"predictive", "retrospective", "adversarial"}

REQUIRED_FIELDS = [
    "id", "title", "family", "oracle", "independence",
    "scope", "latency", "actionability", "type", "stack_level",
]


def parse_frontmatter(filepath):
    with open(filepath) as f:
        content = f.read()
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    return yaml.safe_load(parts[1]) or {}, parts[2].strip()


def main():
    errors = []
    seen_ids = {}

    files = sorted(SENSOR_DIR.glob("*.md"))
    if not files:
        print("No sensor files found.")
        return 1

    for filepath in files:
        slug = filepath.stem
        loc = f"{filepath.name}"

        try:
            meta, _ = parse_frontmatter(filepath)
        except yaml.YAMLError as e:
            errors.append(f"{loc}: YAML parse error: {e}")
            continue

        for field in REQUIRED_FIELDS:
            if field not in meta:
                errors.append(f"{loc}: missing required field '{field}'")

        sid = meta.get("id", "")
        if sid:
            if sid in seen_ids:
                errors.append(
                    f"{loc}: duplicate id '{sid}' (also in {seen_ids[sid]})"
                )
            else:
                seen_ids[sid] = loc

        family = meta.get("family", "")
        if family and family not in VALID_FAMILIES:
            errors.append(
                f"{loc}: family '{family}' not in {sorted(VALID_FAMILIES)}"
            )

        oracle = meta.get("oracle", "")
        if oracle and oracle not in VALID_ORACLES:
            errors.append(
                f"{loc}: oracle '{oracle}' not in {sorted(VALID_ORACLES)}"
            )

        indep = meta.get("independence", "")
        if indep and indep not in VALID_INDEPENDENCE:
            errors.append(
                f"{loc}: independence '{indep}' not in {sorted(VALID_INDEPENDENCE)}"
            )

        latency = meta.get("latency", "")
        if latency and latency not in VALID_LATENCIES:
            errors.append(
                f"{loc}: latency '{latency}' not in {sorted(VALID_LATENCIES)}"
            )

        stack = meta.get("stack_level", "")
        if stack and stack not in VALID_STACK_LEVELS:
            errors.append(
                f"{loc}: stack_level '{stack}' not in {sorted(VALID_STACK_LEVELS)}"
            )

        action = meta.get("actionability", "")
        if action and action not in VALID_ACTIONABILITY:
            errors.append(
                f"{loc}: actionability '{action}' not in {sorted(VALID_ACTIONABILITY)}"
            )

        stype = meta.get("type", "")
        if stype and stype not in VALID_TYPES:
            errors.append(
                f"{loc}: type '{stype}' not in {sorted(VALID_TYPES)}"
            )

        see_also = meta.get("see_also", []) or []
        if not isinstance(see_also, list):
            errors.append(f"{loc}: see_also must be a list, got {type(see_also).__name__}")
        else:
            for ref in see_also:
                if not isinstance(ref, str):
                    errors.append(f"{loc}: see_also entry {ref!r} must be a string")

        categories = meta.get("categories", []) or []
        if not isinstance(categories, list):
            errors.append(f"{loc}: categories must be a list, got {type(categories).__name__}")

        reviewed = meta.get("last_reviewed", "")
        if reviewed:
            import re as _re
            if not _re.match(r"^\d{4}-\d{2}-\d{2}$", str(reviewed)):
                errors.append(f"{loc}: last_reviewed '{reviewed}' must be YYYY-MM-DD")

        if sid and see_also and sid in see_also:
            errors.append(f"{loc}: see_also references its own id '{sid}' (self-loop)")

        references = meta.get("references", []) or []
        if not isinstance(references, list):
            errors.append(f"{loc}: references must be a list, got {type(references).__name__}")
        else:
            VALID_KINDS = {"paper", "tool", "blog", "spec", "book", "other"}
            VALID_TIERS = {"I", "II", "III", "IV"}
            for i, ref in enumerate(references):
                if not isinstance(ref, dict):
                    errors.append(f"{loc}: references[{i}] must be a dict, got {type(ref).__name__}")
                    continue
                if not ref.get("title"):
                    errors.append(f"{loc}: references[{i}] missing 'title'")
                kind = ref.get("kind", "")
                if kind and kind not in VALID_KINDS:
                    errors.append(f"{loc}: references[{i}] kind '{kind}' not in {sorted(VALID_KINDS)}")
                if kind == "tool" and not ref.get("url"):
                    errors.append(f"{loc}: references[{i}] tool '{ref.get('title', '?')}' missing 'url'")
                tier = ref.get("tier", "")
                if tier and tier not in VALID_TIERS:
                    errors.append(f"{loc}: references[{i}] tier '{tier}' not in {sorted(VALID_TIERS)}")

    if errors:
        print(f"{len(errors)} frontmatter error(s) found:")
        for e in errors:
            print(f"  {e}")
        return 1

    print(f"All {len(files)} sensor frontmatters OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
