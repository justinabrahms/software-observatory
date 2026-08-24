"""
Link checker for the generated site.

Checks internal links, anchors, and asset references in the committed
HTML output (index.html, pages/**). External links are checked only with
--external (network required); internal checks are fully offline.

External link checks use a TTL cache (default 90 days). A URL that was
confirmed working within the cache lifetime is trusted without a network
request; only expired entries are re-checked. The cache is keyed by URL
(so a URL cited in multiple entries is fetched once) and stored in
.link-cache.json at the site root. 403 and other 4xx responses that are
not 404/410 are treated as "unknown" (not failures) because many sites
block non-browser user agents.

Usage:
    .venv/bin/python check_links.py            # internal only
    .venv/bin/python check_links.py --external # also check outbound links
    .venv/bin/python check_links.py --external --ttl 30  # 30-day cache

Exit status is 1 if any broken link is found, so it can gate CI.
"""

import html.parser
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urlparse, urldefrag

SITE_ROOT = Path(__file__).resolve().parent.parent
HTML_GLOBS = ["index.html", "404.html", "catalog/**/*.html", "sensors/**/*.html",
              "atlas/**/*.html", "framework/**/*.html", "about/**/*.html",
              "contact/**/*.html", "privacy/**/*.html", "glossary/**/*.html",
              "categories/**/*.html"]

SKIP_SCHEMES = ("mailto:", "tel:", "javascript:", "data:")
# URLs that are infrastructure (preconnect hints, CDN origins) not content
# links; checking them produces false positives.
SKIP_URLS = {"https://fonts.googleapis.com", "https://fonts.gstatic.com"}

CACHE_FILE = SITE_ROOT / ".link-cache.json"
DEFAULT_TTL = 90 * 24 * 3600  # 90 days in seconds
# HTTP statuses that are "unknown" — the site may block bots, so don't fail.
UNKNOWN_STATUSES = {401, 403, 429}
# Definitively broken statuses.
BROKEN_STATUSES = {404, 410, 451}


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
                # Directory-style URLs (/catalog/, /sensors/<slug>/) resolve
                # to index.html inside the directory.
                resolved = url
                if resolved.startswith("/"):
                    resolved = resolved.lstrip("/")
                    target = (SITE_ROOT / resolved).resolve()
                else:
                    target = (page.parent / resolved).resolve()
                if target.is_dir():
                    target = target / "index.html"
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


def load_cache():
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except (json.JSONDecodeError, ValueError):
            pass
    return {}


def save_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache, indent=2, sort_keys=True))


def check_external(pages, ttl=DEFAULT_TTL):
    """HEAD every outbound http(s) link once, with a TTL cache.

    Cached successes younger than ttl are trusted. Only expired or
    unseen URLs are fetched. 403/401/429 are "unknown" (not failures).
    Cache is keyed by URL so duplicates across entries are fetched once.
    """
    externals = set()
    for page in pages:
        links, _ = parse_page(page)
        for link in links:
            if link.startswith(("http://", "https://")) and link not in SKIP_URLS:
                externals.add(link)

    cache = load_cache()
    now = time.time()
    broken = []
    checked = 0
    cached = 0

    for url in sorted(externals):
        entry = cache.get(url)
        if entry and entry.get("status") == "ok" and (now - entry.get("ts", 0)) < ttl:
            cached += 1
            continue

        checked += 1
        result = _check_url(url)
        if result == "ok":
            cache[url] = {"status": "ok", "ts": now}
        elif result == "unknown":
            cache[url] = {"status": "unknown", "ts": now}
        else:
            cache[url] = {"status": "broken", "ts": now, "reason": result}
            broken.append((url, result))

    save_cache(cache)
    return broken, len(externals), checked, cached


def _check_url(url):
    """Return 'ok', 'unknown', or a reason string for broken URLs.

    Try HEAD first; if HEAD returns a broken or ambiguous status, fall
    back to GET before declaring the URL broken. Many sites (bsky.app,
    etc.) return 404 to HEAD but 200 to GET.
    """
    ua = "Mozilla/5.0 link-check"
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": ua})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in BROKEN_STATUSES:
                return _check_url_get(url, ua)
            if resp.status >= 400:
                return "unknown"
            return "ok"
    except urllib.error.HTTPError as e:
        if e.code in BROKEN_STATUSES:
            return _check_url_get(url, ua)
        if e.code in UNKNOWN_STATUSES or e.code == 405:
            return _check_url_get(url, ua)
        return f"HTTP {e.code}"
    except Exception as e:
        return str(e)


def _check_url_get(url, ua):
    """GET fallback used when HEAD is broken, blocked, or unsupported."""
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": ua}),
            timeout=10,
        ) as resp:
            if resp.status in BROKEN_STATUSES:
                return f"HTTP {resp.status}"
            if resp.status >= 400:
                return "unknown"
            return "ok"
    except urllib.error.HTTPError as e:
        if e.code in BROKEN_STATUSES:
            return f"HTTP {e.code}"
        if e.code in UNKNOWN_STATUSES:
            return "unknown"
        return f"HTTP {e.code}"
    except Exception as e:
        return str(e)


def main():
    pages = collect_pages()
    print(f"Checking {len(pages)} pages...")

    broken_internal = check_internal(pages)
    for page, link, why in broken_internal:
        print(f"  BROKEN {page.relative_to(SITE_ROOT)}: {link} ({why})")

    failures = len(broken_internal)

    if "--external" in sys.argv:
        ttl = DEFAULT_TTL
        for i, arg in enumerate(sys.argv):
            if arg == "--ttl" and i + 1 < len(sys.argv):
                ttl = int(sys.argv[i + 1]) * 24 * 3600
        print(f"Checking external links (TTL {ttl // (24 * 3600)} days)...")
        broken_ext, total_ext, checked, cached = check_external(pages, ttl=ttl)
        print(f"  {total_ext} external links: {checked} checked, {cached} cached")
        for url, why in broken_ext:
            print(f"  BROKEN external: {url} ({why})")
        failures += len(broken_ext)

    if failures:
        print(f"\n{failures} broken link(s) found.")
        sys.exit(1)
    print("All links OK.")


if __name__ == "__main__":
    main()
