#!/usr/bin/env python3
"""
Software Observatory — static site generator.

Reads markdown files with YAML frontmatter from content/, renders HTML
pages using templates, computes backlinks from see_also references, and
writes everything to the site root.

This file is the entry point and the compatibility surface; the generator
itself lives in scripts/observatory/, one module per responsibility. Start
at observatory/__init__.py for the map, or observatory/site.py for the order
a build actually happens in.

The re-exports below are the names the sibling scripts import from here
(check_frontmatter.py, export_cli_data.py, gen_og.py, test_build.py). They
are constants and functions, so importing them by value is safe. The
build's *paths* are deliberately not re-exported: they are repointed at a
sandbox by scripts/test_build.py, and that only works when it assigns to
observatory.config, which is what every module reads them from.

Usage:
    .venv/bin/python build.py
"""

import sys

from observatory import config  # noqa: F401  (so `build.config.X` resolves)
from observatory.content import (  # noqa: F401
    load_sensors,
    og_card_items,
    parse_frontmatter,
)
from observatory.config import SITE_URL  # noqa: F401
from observatory.dates import first_seen_dates  # noqa: F401
from observatory.gates import JSON_LD_RE  # noqa: F401
from observatory.site import main
from observatory.taxonomy import (  # noqa: F401
    FAMILIES,
    FAMILY_BY_SLUG,
    INDEPENDENCE_DOTS,
    LATENCY_LABELS,
    ORACLE_WIDTHS,
    STACK_LAYERS,
)


if __name__ == "__main__":
    main(check_only="--check" in sys.argv)
