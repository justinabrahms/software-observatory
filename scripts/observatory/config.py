"""Where the build reads from, where it writes to, and what it calls itself.

These are the knobs the golden-file suite repoints: scripts/test_build.py
builds the fixture corpus into a temp tree by assigning to the four path
constants below. That only works if the code reads them through this module
at call time — `from .config import CONTENT_DIR` would snapshot the repo path
at import time and the sandbox would silently build the real content/ into
the real site root. So the modules that touch a path import the module
(`from . import config`) and say `config.CONTENT_DIR`. Immutable constants
(SITE_URL, SECTION_PAGES) are imported by value; nothing repoints them.
"""

from pathlib import Path


SITE_ROOT = Path(__file__).resolve().parents[2]
CONTENT_DIR = SITE_ROOT / "content"
OUTPUT_DIR = SITE_ROOT
CSS_DIR = SITE_ROOT / "css"
JS_DIR = SITE_ROOT / "js"

# Section pages rendered as clean directory URLs: /catalog/ -> catalog/index.html.
# Markdown bodies link these by bare filename (catalog.html#behavioral), and
# fix_link_depths rewrites them using this set.
SECTION_PAGES = {
    "catalog", "atlas", "framework", "glossary", "about",
    "contact", "privacy", "categories",
}

SITE_URL = "https://softwareobservatory.com"

# Committed cache of "when did this entry first appear", so the feed's dates
# survive a shallow CI checkout (actions/checkout fetches depth 1, where git
# can no longer see the commit that added a file).
FIRST_SEEN_PATH = SITE_ROOT / "scripts" / "first_seen.json"
