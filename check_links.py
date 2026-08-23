"""
Link checker for the generated site.

Checks internal links, anchors, and asset references in the committed
HTML output (index.html, pages/**). External links are checked only with
--external (network required); internal checks are fully offline.

Usage:
    .venv/bin/python check_links.py            # internal only
    .venv/bin/python check_links.py --external # also check outbound links

Exit status is 1 if any broken link is found, so it can gate CI.
"""

import html.parser
import json
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urlparse, urldefrag

SITE_ROOT = Path(__file__).parent
HTML_GLOBS = ["index.html", "pages/**/*.html"]

SKIP_SCHEMES = ("mailto:", "tel:", "javascript:", "data:")


class LinkCollector(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        for attr in ("href", "src"):
            if attr in attrs:
                self.links.append(attrs[attr])


def collect_pages():
    pages = []
    for pattern in HTML_GLOBS:
        pages.extend(SITE_ROOT.glob(pattern))
    return sorted(set(pages))


def parse_page(path):
    parser = LinkCollector()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser.links, parser.ids


def check_internal(pages):
    """Every href/src that doesn't leave the site must resolve, and any
    #fragment must exist in the target page."""
    ids_cache = {}

    def ids_for(path):
        if path not in ids_cache:
            _, ids = parse_page(path)
            ids_cache[path] = ids
        return ids_cache[path]

    broken = []
    for page in pages:
        links, _ = parse_page(page)
        for link in links:
            if link.startswith(SKIP_SCHEMES):
                continue
            url, frag = urldefrag(link)
            if not url:
                target = page
            elif url.startswith(("http://", "https://", "//")):
                continue
            else:
                target = (page.parent / url).resolve()
                try:
                    target.relative_to(SITE_ROOT.resolve())
                except ValueError:
                    broken.append((page, link, "escapes site root"))
                    continue
            if not target.exists():
                broken.append((page, link, "missing file"))
                continue
            if frag and target.suffix == ".html":
                if frag not in ids_for(target):
                    broken.append((page, link, f"missing anchor #{frag}"))
    return broken


def check_external(pages):
    """HEAD every outbound http(s) link once."""
    externals = set()
    for page in pages:
        links, _ = parse_page(page)
        for link in links:
            if link.startswith(("http://", "https://")):
                externals.add(link)

    broken = []
    for url in sorted(externals):
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0 link-check"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status >= 400:
                    broken.append((url, f"HTTP {resp.status}"))
        except urllib.error.HTTPError as e:
            if e.code == 405:  # HEAD not allowed; try GET
                try:
                    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 link-check"}), timeout=10) as resp:
                        if resp.status >= 400:
                            broken.append((url, f"HTTP {resp.status}"))
                except Exception as e2:
                    broken.append((url, str(e2)))
            else:
                broken.append((url, f"HTTP {e.code}"))
        except Exception as e:
            broken.append((url, str(e)))
    return broken, len(externals)


def main():
    pages = collect_pages()
    print(f"Checking {len(pages)} pages...")

    broken_internal = check_internal(pages)
    for page, link, why in broken_internal:
        print(f"  BROKEN {page.relative_to(SITE_ROOT)}: {link} ({why})")

    failures = len(broken_internal)

    if "--external" in sys.argv:
        print("Checking external links...")
        broken_ext, total_ext = check_external(pages)
        print(f"  {total_ext} external links checked")
        for url, why in broken_ext:
            print(f"  BROKEN external: {url} ({why})")
        failures += len(broken_ext)

    if failures:
        print(f"\n{failures} broken link(s) found.")
        sys.exit(1)
    print("All links OK.")


if __name__ == "__main__":
    main()
