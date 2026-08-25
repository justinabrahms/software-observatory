#!/usr/bin/env python3
"""
Citation validator for sensor entries.

Validates the `references:` entries in the YAML frontmatter of every
content/sensors/*.md. Where check_frontmatter.py checks that a reference is
*well-formed*, this checks that it is *true*: that the URL resolves, and that
the work sitting at that URL is actually the work being cited.

Three classes of check:

  completeness (offline, always runs)
      A `kind: publication` entry must carry authors and a year. A citation
      with no url AND no authors is a placeholder, not a reference.
      check_frontmatter.py requires a url for `kind: tool` but not for
      `kind: publication`, which is backwards; this closes that gap.

  reachability (--external)
      The url resolves. HEAD first, GET fallback. 401/403/429 are "unknown"
      (publishers block bots) rather than broken -- same policy as
      check_links.py.

  identity (--external)
      For URLs whose metadata is machine-readable, the cited title and
      authors must match the work actually at that URL:

        arXiv   -- export.arxiv.org API (authoritative title + author list).
                   An id the API does not return does not exist.
        DOI     -- api.crossref.org/works/<doi> (title, authors, and `type`:
                   a DOI resolving to `proceedings` is a whole volume, not a
                   paper).
        venue   -- for citations with neither an id nor a DOI, a Crossref
                   search: if the cited author/venue/volume/year slot is
                   occupied by a differently-titled work, the title is wrong.
        HTML    -- Highwire `citation_title` / `citation_author` meta tags,
                   which ACM, Springer, IEEE and friends emit.
        PDF     -- the title block on page 1, read with poppler's pdftotext
                   if it is installed. Advisory only (a NOTE, never a
                   failure).

      Titles are normalized hard (case, punctuation, accents, LaTeX,
      whitespace) and compared with a similarity threshold, so formatting
      differences do not fire. Authors are compared as surname sets and only
      fire on zero overlap.

      Every identity check abstains rather than guesses. Crossref not
      knowing a work is never treated as evidence against it; only a
      positive contradiction -- a different work in the same author / venue
      / volume / year slot -- is a finding.

      Two deliberate limits on the PDF check. It reads only the *title
      block* at the top of page 1, never the body: a paper's prose routinely
      contains the phrase a wrong title was built from ("the CompCert C
      compiler" appears inside a paper actually titled "Formal verification
      of a realistic compiler"), so whole-document matching would pass the
      very errors it is meant to catch. And it only ever emits a NOTE,
      because it depends on pdftotext being installed -- a check that fails
      the build on one machine and passes on another is not a gate, it is a
      coin flip. Title errors that must fail are caught against publisher
      metadata, which is available everywhere.

Network results are cached in .citation-cache.json at the site root with a
90-day TTL, in the same shape as check_links.py's .link-cache.json
({key: {"status", "ts", "reason", ...}}), but in a separate file because
citation verdicts carry richer data (the fetched title and authors) and are
keyed per citation, not per URL. The key hashes the citation's url, title,
authors and year, so editing any of those invalidates the cached verdict.

NOTE: .citation-cache.json should be added to .gitignore (alongside
.link-cache.json). It is a local cache, not a build artifact.

Usage:
    .venv/bin/python scripts/check_citations.py              # offline only
    .venv/bin/python scripts/check_citations.py --external   # + network
    .venv/bin/python scripts/check_citations.py --external --ttl 30
    .venv/bin/python scripts/check_citations.py --external --verbose

Exit status is 1 if any citation fails, so it can gate CI alongside
check_links.py and check_frontmatter.py.
"""

import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

SITE_ROOT = Path(__file__).resolve().parent.parent
SENSOR_DIR = SITE_ROOT / "content" / "sensors"

CACHE_FILE = SITE_ROOT / ".citation-cache.json"
DEFAULT_TTL = 90 * 24 * 3600  # 90 days in seconds

USER_AGENT = (
    "Mozilla/5.0 (compatible; softwareobservatory-citation-check/1.0; "
    "+https://softwareobservatory.com/)"
)
TIMEOUT = 20

# Same status policy as check_links.py: many academic publishers block
# non-browser agents, so 401/403/429 is "we can't tell", not "broken".
UNKNOWN_STATUSES = {401, 403, 429}
BROKEN_STATUSES = {404, 410, 451}

ARXIV_API = "http://export.arxiv.org/api/query"
ARXIV_BATCH = 20
CROSSREF_API = "https://api.crossref.org/works/"
CROSSREF_SEARCH = "https://api.crossref.org/works?"

# Politeness: arXiv asks for ~3s between API requests; Crossref throttles
# anonymous callers with 429s well before that.
HOST_DELAY = {"export.arxiv.org": 3.0, "api.crossref.org": 1.6}
DEFAULT_DELAY = 0.35

# Similarity floors. Above these, two strings are the same work with
# different formatting; below, they are different works.
TITLE_SIM = 0.72          # cited title vs authoritative metadata title
VENUE_SIM = 0.75          # cited venue vs Crossref container-title
PDF_TITLE_SIM = 0.75      # cited title vs the title block on the PDF's page 1

# A PDF is downloaded in full only up to this; bigger ones abstain rather
# than pull tens of megabytes on every audit. A truncated PDF yields no text,
# which the caller already treats as "cannot tell".
PDF_FETCH_LIMIT = 4_000_000
# How much of page 1 counts as the title block. Measured over this site's
# PDFs: every correctly-cited paper scores >= 0.94 within the first 800
# normalized characters, while a paper cited under the wrong title scores
# 0.45 -- because the wrong title's words do appear in the body prose, just
# not in the title block.
PDF_TITLE_WINDOW = 800

# Crossref record types that are individual scholarly works, i.e. the kind
# of thing a `venue` field claims the citation is.
SCHOLARLY_TYPES = {"journal-article", "proceedings-article", "book-chapter"}

# Venues that are not in Crossref at all; searching for them only invites
# spurious matches against unrelated journals.
NON_SCHOLARLY_VENUE = re.compile(
    r"\b(blog|newsletter|website|docs?|manual|talk|slides|report|"
    r"whitepaper|wiki|youtube|podcast)\b", re.I)

# Crossref `type` values that are containers, not individual works. A
# citation of a paper that resolves to one of these points at the wrong
# object (the whole proceedings volume instead of the paper).
CONTAINER_TYPES = {
    "proceedings", "journal", "journal-issue", "journal-volume",
    "book-series", "report-series", "proceedings-series",
}

# Failure classes, in report order.
CLASS_COMPLETENESS = "completeness"
CLASS_REACHABILITY = "reachability"
CLASS_TITLE = "identity/title"
CLASS_AUTHORS = "identity/authors"
CLASS_EXISTENCE = "identity/existence"
CLASS_TYPE = "identity/type"
CLASS_NOTE = "note"       # advisory only; never fails the run
CLASS_ORDER = [
    CLASS_COMPLETENESS, CLASS_EXISTENCE, CLASS_REACHABILITY,
    CLASS_TITLE, CLASS_AUTHORS, CLASS_TYPE,
]


# --------------------------------------------------------------------------
# Frontmatter
# --------------------------------------------------------------------------

def parse_frontmatter(filepath):
    content = filepath.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    return yaml.safe_load(parts[1]) or {}


def collect_citations():
    """Every reference entry across all sensors, with its provenance."""
    citations = []
    for path in sorted(SENSOR_DIR.glob("*.md")):
        try:
            meta = parse_frontmatter(path)
        except yaml.YAMLError as e:
            print(f"  SKIP {path.name}: YAML parse error: {e}")
            continue
        refs = meta.get("references") or []
        if not isinstance(refs, list):
            continue
        for i, ref in enumerate(refs):
            if not isinstance(ref, dict):
                continue
            citations.append({
                "file": path.name,
                "index": i,
                "kind": (ref.get("kind") or "").strip(),
                "title": (ref.get("title") or "").strip(),
                "url": (ref.get("url") or "").strip(),
                "authors": (str(ref.get("authors")).strip()
                            if ref.get("authors") else ""),
                "year": ref.get("year"),
                "venue": (ref.get("venue") or "").strip(),
            })
    return citations


# --------------------------------------------------------------------------
# Normalization and comparison
# --------------------------------------------------------------------------

LATEX_CMD = re.compile(r"\\[a-zA-Z]+\s*")
STOPWORDS = {"a", "an", "the", "of", "for", "and", "on", "in", "to", "with"}


def normalize_title(s):
    """Fold case, accents, LaTeX, punctuation and whitespace away."""
    if not s:
        return ""
    s = s.replace("$", " ")
    s = LATEX_CMD.sub(" ", s)
    s = s.replace("{", " ").replace("}", " ")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def title_similarity(a, b):
    """1.0 for the same title; tolerant of subtitles and formatting."""
    na, nb = normalize_title(a), normalize_title(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    # A citation that drops or adds a subtitle is still the same work.
    if na.startswith(nb) or nb.startswith(na):
        return 1.0
    ratio = difflib.SequenceMatcher(None, na, nb).ratio()
    # Content-word overlap catches reordered/abbreviated forms.
    wa = {w for w in na.split() if w not in STOPWORDS}
    wb = {w for w in nb.split() if w not in STOPWORDS}
    if wa and wb:
        jaccard = len(wa & wb) / len(wa | wb)
        ratio = max(ratio, jaccard)
    return ratio


AUTHOR_SPLIT = re.compile(r",| and | & |;|\band others\b", re.I)
AUTHOR_NOISE = {
    "et", "al", "etal", "others", "jr", "sr", "ii", "iii", "phd", "dr",
}
NAME_PARTICLES = {"van", "von", "der", "den", "de", "di", "du", "la", "le",
                  "el", "al", "bin", "ibn", "da", "dos", "st"}


def surnames(authors):
    """Best-effort surname set from a free-form author string."""
    out = set()
    if not authors:
        return out
    for chunk in AUTHOR_SPLIT.split(authors):
        chunk = chunk.strip()
        if not chunk:
            continue
        norm = normalize_title(chunk)
        tokens = [t for t in norm.split()
                  if t and t not in AUTHOR_NOISE and not t.isdigit()]
        # Drop single-letter initials.
        tokens = [t for t in tokens if len(t) > 1]
        if not tokens:
            continue
        last = tokens[-1]
        # "van der Sterr" -> keep the particle-joined form too.
        if len(tokens) >= 2 and tokens[-2] in NAME_PARTICLES:
            out.add(tokens[-2] + last)
        if last in NAME_PARTICLES and len(tokens) >= 2:
            last = tokens[-2] + last
        out.add(last)
    return {s for s in out if len(s) > 1}


def author_overlap(cited, real):
    """Fraction of the smaller surname set that appears in the other.

    Deliberately lenient: we are looking for *zero* overlap (a citation
    attributed to entirely the wrong people), not for exact author lists.
    """
    a, b = surnames(cited), surnames(real)
    if not a or not b:
        return None
    def same(x, y):
        if x == y:
            return True
        # Containment only for names long enough that it isn't a coincidence
        # ("Costa" inside "DaCosta" is a match; "Ma" inside "Marquez" is not).
        return (min(len(x), len(y)) >= 5 and (x in y or y in x))

    hits = sum(1 for x in a if any(same(x, y) for y in b))
    return hits / min(len(a), len(b))


# --------------------------------------------------------------------------
# Cache (same shape/policy as check_links.py, separate file)
# --------------------------------------------------------------------------

def load_cache():
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except (json.JSONDecodeError, ValueError):
            pass
    return {}


def save_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache, indent=2, sort_keys=True))


def cache_key(check, cit):
    """Key a verdict to both the check and the citation's content, so that
    editing the title/authors/year/url invalidates the cached verdict."""
    payload = json.dumps(
        [check, cit["url"], cit["title"], cit["authors"], str(cit["year"])],
        sort_keys=True,
    )
    return f"{check}:{hashlib.sha256(payload.encode()).hexdigest()[:20]}"


# --------------------------------------------------------------------------
# Network
# --------------------------------------------------------------------------

_last_request = {}


def _throttle(url):
    host = urllib.parse.urlparse(url).netloc
    delay = HOST_DELAY.get(host, DEFAULT_DELAY)
    last = _last_request.get(host)
    if last is not None:
        wait = delay - (time.time() - last)
        if wait > 0:
            time.sleep(wait)
    _last_request[host] = time.time()


def fetch(url, method="GET", limit=2_000_000):
    """Return (status, body_bytes, content_type, final_url).

    status is an int, or a string describing a transport error.
    """
    _throttle(url)
    req = urllib.request.Request(
        url, method=method, headers={"User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = b"" if method == "HEAD" else resp.read(limit)
            ctype = resp.headers.get("Content-Type", "")
            return resp.status, body, ctype, resp.geturl()
    except urllib.error.HTTPError as e:
        try:
            body = e.read(limit)
        except Exception:
            body = b""
        ctype = e.headers.get("Content-Type", "") if e.headers else ""
        # e.url is where the error actually happened, which after a redirect
        # is not the url we asked for. The difference matters -- see
        # check_reachable.
        return e.code, body, ctype, getattr(e, "url", None) or url
    except Exception as e:
        return str(e), b"", "", url


def check_reachable(url):
    """'ok', 'unknown: <why>', or a reason string for a dead url.

    HEAD first, then GET, like check_links.py. Only a definitive HTTP status
    (404/410/451) is reported as dead. Everything else -- a timeout, a reset
    connection, a 5xx, a bot filter -- is "unknown" and retried once first.

    That is stricter than check_links.py on purpose. A transport error is a
    statement about the network at this instant, not about the citation: a
    single slow response from a working university web server produced two
    "url is dead" failures against a paper that is perfectly fine. A checker
    that reports the weather cannot be trusted about the citations.
    """
    status, _, _, _ = fetch(url, method="HEAD", limit=0)
    if isinstance(status, int) and 200 <= status < 400:
        return "ok"
    # HEAD is unreliable (405s, bot filters, sites that 404 HEAD but 200 GET).
    for attempt in (1, 2):
        status, _, _, final = fetch(url, method="GET", limit=1024)
        if isinstance(status, int):
            if 200 <= status < 400:
                return "ok"
            if status in BROKEN_STATUSES:
                if _redirected_elsewhere(url, final):
                    return (f"unknown: redirected to {final} which returns "
                            f"HTTP {status} -- the host is reorganised or "
                            f"having an outage, so this says nothing about "
                            f"the citation")
                return f"HTTP {status}"
            return f"unknown: HTTP {status}"
        if attempt == 1:
            time.sleep(3)
    return f"unknown: {status}"


def _redirected_elsewhere(url, final):
    """Did the request end up on a different host than the one cited?

    Berkeley's web server spent an afternoon 302-ing every ~user path to an
    "active incident" page that itself 404s. Read naively that is a dead
    citation; read correctly it is somebody else's outage. A paper that is
    really gone 404s at its own host -- as all of the genuinely dead urls in
    this catalog do.
    """
    if not final or final == url:
        return False
    try:
        return (urllib.parse.urlparse(url).netloc.lower()
                != urllib.parse.urlparse(final).netloc.lower())
    except ValueError:
        return False


# --- arXiv ----------------------------------------------------------------

ARXIV_ID = re.compile(
    r"arxiv\.org/(?:abs|pdf|html|ps)/((?:[a-z-]+(?:\.[A-Z]{2})?/)?\d{4,7}\.?\d{0,5})",
    re.I,
)


def arxiv_id(url):
    m = ARXIV_ID.search(url or "")
    if not m:
        return None
    aid = m.group(1)
    aid = re.sub(r"v\d+$", "", aid)
    return aid.rstrip(".")


def fetch_arxiv(ids, verbose=False):
    """({id: {'title':..., 'authors': [...]}}, set_of_ids_actually_queried).

    Missing ids are simply absent from a successful response -- that is the
    signal that the paper does not exist. Ids in a batch whose request failed
    are NOT in the returned set, so a flaky API can never be mistaken for a
    nonexistent paper. Fetched in batches to be a good citizen.
    """
    found = {}
    answered = set()
    ids = sorted(set(ids))
    for i in range(0, len(ids), ARXIV_BATCH):
        batch = ids[i:i + ARXIV_BATCH]
        url = (f"{ARXIV_API}?max_results={len(batch)}"
               f"&id_list={','.join(batch)}")
        if verbose:
            print(f"    arXiv API: {len(batch)} id(s)")
        status, body, _, _ = fetch(url, limit=4_000_000)
        if not isinstance(status, int) or status != 200 or not body:
            print(f"  WARN arXiv API unavailable ({status}); "
                  f"skipping identity check for {len(batch)} citation(s)")
            continue
        answered.update(batch)
        for entry in _parse_arxiv_feed(body.decode("utf-8", "replace")):
            found[entry["id"]] = entry
    return found, answered


def _parse_arxiv_feed(xml):
    """Minimal Atom scrape -- the feed is machine-generated and regular."""
    out = []
    for chunk in re.findall(r"<entry>(.*?)</entry>", xml, re.S):
        m = re.search(r"<id>\s*https?://arxiv\.org/abs/([^\s<]+)\s*</id>", chunk)
        if not m:
            continue
        aid = re.sub(r"v\d+$", "", m.group(1))
        tm = re.search(r"<title>(.*?)</title>", chunk, re.S)
        title = _unxml(tm.group(1)) if tm else ""
        authors = [_unxml(a) for a in
                   re.findall(r"<author>\s*<name>(.*?)</name>", chunk, re.S)]
        out.append({"id": aid, "title": title, "authors": authors})
    return out


def _unxml(s):
    s = re.sub(r"\s+", " ", s).strip()
    for a, b in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                 ("&quot;", '"'), ("&apos;", "'")):
        s = s.replace(a, b)
    return s


# --- DOI / Crossref -------------------------------------------------------

DOI_RE = re.compile(r"(10\.\d{4,9}/[^\s\"'<>?#]+)")


def doi_from_url(url):
    if not url:
        return None
    u = urllib.parse.unquote(url)
    if not re.search(r"(doi\.org/|/doi/|/chapter/|/article/|/book/)", u, re.I):
        return None
    m = DOI_RE.search(u)
    if not m:
        return None
    return m.group(1).rstrip(".").rstrip("/")


def fetch_crossref(doi):
    """(metadata_dict, error_string). metadata is None when unavailable."""
    status, body, _, _ = fetch(CROSSREF_API + urllib.parse.quote(doi),
                               limit=2_000_000)
    if status == 404:
        return None, "not registered with Crossref"
    if not isinstance(status, int) or status != 200:
        return None, f"unavailable ({status})"
    try:
        msg = json.loads(body.decode("utf-8", "replace"))["message"]
    except Exception as e:
        return None, f"unparseable ({e})"
    titles = msg.get("title") or []
    authors = [
        " ".join(x for x in (a.get("given"), a.get("family")) if x) or
        (a.get("name") or "")
        for a in (msg.get("author") or [])
    ]
    return {
        "title": titles[0] if titles else "",
        "authors": [a for a in authors if a],
        "type": msg.get("type", ""),
    }, None


def crossref_search(title, author, year, rows=5):
    """Ask Crossref what work matches this citation. None if unavailable.

    Used for citations with no arXiv id and no DOI in their url, where the
    only handle on the work is title + author + venue + year.
    """
    params = {
        "query.bibliographic": title,
        "rows": str(rows),
        "select": "title,author,container-title,volume,issue,type,DOI,issued",
    }
    if author:
        params["query.author"] = author
    if year:
        params["filter"] = (f"from-pub-date:{int(year) - 1}-01-01,"
                            f"until-pub-date:{int(year) + 1}-12-31")
    url = CROSSREF_SEARCH + urllib.parse.urlencode(params)
    for attempt in (1, 2):
        status, body, _, _ = fetch(url, limit=3_000_000)
        if status == 200:
            try:
                return json.loads(body.decode("utf-8", "replace"))["message"]["items"]
            except Exception:
                return None
        if status == 429 and attempt == 1:
            time.sleep(5)
            continue
        return None
    return None


def corroborate_with_crossref(cit):
    """Is there a *different* work where this citation says its work is?

    Fires only on the tight case: Crossref has no record whose title matches
    the citation, but it does have a scholarly record with the same author,
    the same year, the same container (journal/proceedings name), and the
    same volume/issue -- i.e. the slot the citation describes is occupied by
    a differently-titled work. That is a mis-titled citation, not a missing
    one. Anything looser abstains: Crossref's coverage is not a census, and
    "not found" alone is never treated as evidence.

    Returns (reason, doi) on a finding, None when it abstains.
    """
    sn = sorted(surnames(cit["authors"]))
    items = crossref_search(cit["title"], sn[0] if sn else "", cit["year"])
    if not items:
        return None
    if max((title_similarity(cit["title"], (it.get("title") or [""])[0])
            for it in items), default=0.0) >= TITLE_SIM:
        return None  # corroborated: the work exists under the cited title

    venue_nums = set(re.findall(r"\d+", cit["venue"]))
    venue_words = re.sub(r"\d+", " ", cit["venue"])
    for it in items:
        if it.get("type") not in SCHOLARLY_TYPES:
            continue
        families = " ".join(a.get("family", "") for a in it.get("author") or [])
        overlap = author_overlap(cit["authors"], families)
        if not overlap:
            continue
        years = (it.get("issued", {}).get("date-parts") or [[None]])[0]
        if not years or not years[0] or abs(int(years[0]) - int(cit["year"])) > 1:
            continue
        container = (it.get("container-title") or [""])[0]
        if title_similarity(venue_words, container) < VENUE_SIM:
            continue
        if venue_nums:
            slot = {str(it.get("volume") or ""), str(it.get("issue") or "")}
            if not (venue_nums & slot):
                continue
        found = (it.get("title") or [""])[0]
        where = container
        if it.get("volume"):
            where += f" {it['volume']}"
            if it.get("issue"):
                where += f"({it['issue']})"
        return (f'title mismatch: {where} {years[0]} by '
                f'{families or cit["authors"]} is "{found}", not '
                f'"{cit["title"]}" (doi {it.get("DOI")}); Crossref has no '
                f"work under the cited title", it.get("DOI"))
    return None


# --- PDF text (via poppler's pdftotext, if present) -----------------------

_PDFTOTEXT = None


def pdftotext_available():
    """poppler's pdftotext, or None. Optional: absent means "abstain"."""
    global _PDFTOTEXT
    if _PDFTOTEXT is None:
        _PDFTOTEXT = shutil.which("pdftotext") or ""
    return _PDFTOTEXT or None


def pdf_page1_text(body):
    """Text of page 1, via pdftotext. '' when it cannot be read.

    Shelling out to poppler rather than parsing PDF streams here is
    deliberate: poppler handles the font encodings, ligatures, hyphenation
    and layout that hand-rolled extraction gets wrong. An earlier version of
    this checker did parse the streams itself and read the real ICSE 2014
    paper "Coverage Is Not Strongly Correlated with Test Suite
    Effectiveness" as "Coverage Is Not Str ongl y with T est Suite Eff
    ectiveness" -- dropping a word outright and falsely accusing a correct
    citation. No Python dependency is added; if pdftotext is missing the
    check abstains.
    """
    exe = pdftotext_available()
    if not exe or body[:5] != b"%PDF-":
        return ""
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as fh:
            fh.write(body)
            tmp = fh.name
        proc = subprocess.run([exe, "-f", "1", "-l", "1", "-q", tmp, "-"],
                              capture_output=True, timeout=30)
        return proc.stdout.decode("utf-8", "replace")
    except Exception:
        return ""
    finally:
        if tmp:
            try:
                os.unlink(tmp)
            except OSError:
                pass


def squash(s):
    """Normalized with every separator removed, for matching against text
    extracted from a document, where line and word breaks are arbitrary."""
    return normalize_title(s).replace(" ", "")


def title_in_block(title, text):
    """0..1: how much of `title` appears, in order, inside `text`.

    Sums the matching runs of >= 4 characters, so a single dropped ligature
    or hyphen costs a few points rather than the whole match.
    """
    a, b = squash(title), squash(text)
    if not a or not b:
        return 0.0
    if a in b:
        return 1.0
    m = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return sum(x.size for x in m.get_matching_blocks() if x.size >= 4) / len(a)


# --- HTML metadata -------------------------------------------------------

META_RE = re.compile(rb"<meta\b[^>]*>", re.I)


def html_meta(body):
    """{'citation_title': str, 'citation_author': [str, ...]} if present."""
    title = ""
    authors = []
    for tag in META_RE.findall(body[:600_000]):
        t = tag.decode("utf-8", "replace")
        name = re.search(r'(?:name|property)\s*=\s*["\']([^"\']+)["\']', t, re.I)
        content = re.search(r'content\s*=\s*["\']([^"\']*)["\']', t, re.I)
        if not name or not content:
            continue
        key = name.group(1).strip().lower()
        val = _unxml(content.group(1))
        if key == "citation_title" and not title:
            title = val
        elif key in ("citation_author", "citation_authors") and val:
            authors.append(val)
    return {"citation_title": title, "citation_author": authors}


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------

def label(cit):
    return f'{cit["file"]}: references[{cit["index"]}] "{cit["title"]}"'


def check_completeness(citations):
    """Offline. A publication must be attributable and datable."""
    failures = []
    warnings = []
    for cit in citations:
        if cit["kind"] != "publication":
            continue
        missing = []
        if not cit["authors"]:
            missing.append("authors")
        if not cit["year"]:
            missing.append("year")
        if not cit["url"]:
            # A url-less citation is acceptable only when it is still
            # identifiable offline (a book, a classic paper): author + year.
            if missing:
                missing.append("url")
            else:
                warnings.append(
                    f"{label(cit)}: no url (identifiable offline as "
                    f'{cit["authors"]}, {cit["year"]}) -- not verifiable here')
        if missing:
            failures.append((CLASS_COMPLETENESS, cit,
                             "publication is missing " + ", ".join(missing)
                             + " -- unverifiable placeholder"))
    return failures, warnings


def run_network_checks(citations, ttl, verbose=False):
    """Reachability + identity for every publication with a url."""
    cache = load_cache()
    now = time.time()
    failures = []
    warnings = []
    stats = {"checked": 0, "cached": 0, "unknown": 0}

    targets = [c for c in citations
               if c["kind"] == "publication" and c["url"]]

    # --- identity: arXiv (batched; the API asks for 3s between requests) ---
    need_arxiv = []
    for cit in targets:
        aid = arxiv_id(cit["url"])
        if not aid:
            continue
        cit["_arxiv"] = aid
        if not _fresh(cache, cache_key("arxiv", cit), now, ttl):
            need_arxiv.append(aid)
        else:
            stats["cached"] += 1
    arxiv_meta, arxiv_answered = (
        fetch_arxiv(need_arxiv, verbose=verbose) if need_arxiv else ({}, set())
    )

    for cit in targets:
        aid = cit.get("_arxiv")
        if not aid:
            continue
        key = cache_key("arxiv", cit)
        if _fresh(cache, key, now, ttl):
            continue
        if aid not in arxiv_meta:
            if aid not in arxiv_answered:
                continue  # API was unavailable; don't invent a verdict
            reason = (f"arXiv {aid} does not exist -- the arXiv API returns "
                      f"no paper for this id")
            cache[key] = {"status": "broken", "ts": now, "reason": reason}
            failures.append((CLASS_EXISTENCE, cit, reason))
            stats["checked"] += 1
            continue
        stats["checked"] += 1
        meta = arxiv_meta[aid]
        sim = title_similarity(cit["title"], meta["title"])
        overlap = author_overlap(cit["authors"], ", ".join(meta["authors"]))
        problems = []
        if sim < TITLE_SIM:
            problems.append(
                f'title mismatch: arXiv {aid} is "{meta["title"]}" '
                f"(similarity {sim:.2f})")
        elif overlap is not None and overlap == 0:
            problems.append(
                f"author mismatch: arXiv {aid} is by "
                f'{", ".join(meta["authors"])} -- no surname in common with '
                f'the cited "{cit["authors"]}"')
        if problems:
            cls = CLASS_TITLE if sim < TITLE_SIM else CLASS_AUTHORS
            cache[key] = {"status": "broken", "ts": now,
                          "reason": problems[0],
                          "fetched_title": meta["title"],
                          "fetched_authors": meta["authors"]}
            failures.append((cls, cit, problems[0]))
        else:
            cache[key] = {"status": "ok", "ts": now,
                          "fetched_title": meta["title"],
                          "fetched_authors": meta["authors"]}

    # --- identity: DOI / Crossref ---
    for cit in targets:
        doi = doi_from_url(cit["url"])
        if not doi:
            continue
        cit["_doi"] = doi
        key = cache_key("doi", cit)
        if _fresh(cache, key, now, ttl):
            stats["cached"] += 1
            continue
        if verbose:
            print(f"    Crossref: {doi}")
        meta, err = fetch_crossref(doi)
        stats["checked"] += 1
        if meta is None:
            if err.startswith("not registered"):
                reason = f"DOI {doi} is {err}"
                cache[key] = {"status": "broken", "ts": now, "reason": reason}
                failures.append((CLASS_EXISTENCE, cit, reason))
            else:
                cache[key] = {"status": "unknown", "ts": now, "reason": err}
                stats["unknown"] += 1
            continue
        problems = []
        cls = None
        if meta["type"] in CONTAINER_TYPES:
            cls = CLASS_TYPE
            problems.append(
                f'DOI {doi} is a {meta["type"]} '
                f'("{meta["title"]}"), not a paper -- the citation points at '
                f"the whole volume")
        else:
            sim = title_similarity(cit["title"], meta["title"])
            overlap = author_overlap(cit["authors"], ", ".join(meta["authors"]))
            if meta["title"] and sim < TITLE_SIM:
                cls = CLASS_TITLE
                problems.append(
                    f'title mismatch: DOI {doi} is "{meta["title"]}" '
                    f"(similarity {sim:.2f})")
            elif overlap is not None and overlap == 0:
                cls = CLASS_AUTHORS
                problems.append(
                    f"author mismatch: DOI {doi} is by "
                    f'{", ".join(meta["authors"][:6])} -- no surname in common '
                    f'with the cited "{cit["authors"]}"')
        if problems:
            cache[key] = {"status": "broken", "ts": now, "reason": problems[0],
                          "fetched_title": meta["title"],
                          "fetched_authors": meta["authors"],
                          "fetched_type": meta["type"]}
            failures.append((cls, cit, problems[0]))
        else:
            cache[key] = {"status": "ok", "ts": now,
                          "fetched_title": meta["title"],
                          "fetched_authors": meta["authors"],
                          "fetched_type": meta["type"]}

    # --- identity: title corroboration for citations with no id ---
    # A citation with neither an arXiv id nor a DOI can still be checked, if
    # it names a venue: ask Crossref what actually sits in that venue slot.
    for cit in citations:
        if cit["kind"] != "publication":
            continue
        if cit.get("_arxiv") or cit.get("_doi"):
            continue
        if not (cit["authors"] and cit["year"] and cit["venue"]):
            continue
        if NON_SCHOLARLY_VENUE.search(cit["venue"]):
            continue
        key = cache_key("xref", cit)
        if _fresh(cache, key, now, ttl):
            stats["cached"] += 1
            continue
        if verbose:
            print(f"    Crossref search: {cit['title'][:60]}")
        stats["checked"] += 1
        found = corroborate_with_crossref(cit)
        if found:
            reason, doi = found
            cache[key] = {"status": "broken", "ts": now, "reason": reason,
                          "fetched_doi": doi}
            failures.append((CLASS_TITLE, cit, reason))
        else:
            # Abstain rather than assert: Crossref not knowing a work is not
            # evidence against it. Only a positive corroboration is cached.
            cache[key] = {"status": "ok", "ts": now,
                          "reason": "no contradicting record in Crossref"}

    # --- reachability + document identity (one fetch per citation) ---
    for cit in targets:
        key = cache_key("fetch", cit)
        if _fresh(cache, key, now, ttl):
            stats["cached"] += 1
            # Advisory findings are stored with the verdict, so a cached run
            # reports the same thing a fresh one does.
            if cache[key].get("note"):
                warnings.append(f'{label(cit)}: {cache[key]["note"]}')
            continue
        if verbose:
            print(f"    fetch: {cit['url']}")
        stats["checked"] += 1
        verdict = check_reachable(cit["url"])
        if verdict.startswith("unknown"):
            why = verdict.split(":", 1)[1].strip() if ":" in verdict else ""
            cache[key] = {"status": "unknown", "ts": now,
                          "reason": why or "ambiguous status"}
            stats["unknown"] += 1
            warnings.append(f"{label(cit)}: {cit['url']} could not be "
                            f"verified ({why or 'blocked'}); not counted "
                            f"as a failure")
            continue
        if verdict != "ok":
            cache[key] = {"status": "broken", "ts": now, "reason": verdict}
            failures.append((CLASS_REACHABILITY, cit,
                             f"url is dead: {cit['url']} ({verdict})"))
            continue

        # Reachable. If the document itself carries metadata, use it -- but
        # only for citations arXiv/Crossref did not already adjudicate.
        entry = {"status": "ok", "ts": now}
        if not cit.get("_arxiv") and not cit.get("_doi"):
            doc = _document_identity(cit)
            if doc:
                cls, reason, extra = doc
                entry.update(extra)
                if cls == CLASS_NOTE:
                    # Advisory: worth a human's eye, not worth failing a
                    # build over. See _document_identity for why.
                    entry["note"] = reason
                    warnings.append(f"{label(cit)}: {reason}")
                elif cls:
                    entry["status"] = "broken"
                    entry["reason"] = reason
                    failures.append((cls, cit, reason))
        cache[key] = entry

    save_cache(cache)
    return failures, warnings, stats, len(targets)


def _document_identity(cit):
    """Identity check against the fetched document itself.

    Returns (class|None, reason, extra_cache_fields), or None when the
    document offers nothing trustworthy to check against. A class of
    CLASS_NOTE is advisory and does not fail the run.

    For a PDF: does the cited title appear in the title block at the top of
    page 1? Measured over this site's PDFs, every correctly-cited paper
    scores >= 0.94 and the one paper cited under a wrong title scores 0.45,
    so the threshold sits in a wide gap. Abstains whenever the extraction is
    thin -- cover page, scanned image, missing pdftotext, or a PDF too large
    for the fetch limit -- because "no text" is not evidence.

    For HTML: publisher-declared Highwire metadata only.
    """
    status, body, ctype, final = fetch(cit["url"], method="GET",
                                       limit=PDF_FETCH_LIMIT)
    if not isinstance(status, int) or not (200 <= status < 400) or not body:
        return None

    if body[:5] == b"%PDF-" or "pdf" in (ctype or "").lower():
        page1 = pdf_page1_text(body)
        block = squash(page1)[:PDF_TITLE_WINDOW]
        if len(block) < 200:
            # Cover page, scanned image, oversized PDF truncated by the
            # fetch limit, or no pdftotext: nothing to compare against.
            return None
        score = title_in_block(cit["title"], block)
        if score >= PDF_TITLE_SIM:
            return (None, "", {"pdf_title_match": round(score, 2)})
        first = " ".join(page1.split())[:90]
        return (CLASS_NOTE,
                f'the PDF at {cit["url"]} does not show the cited title in '
                f"its title block ({score:.0%} match); page 1 begins "
                f'"{first}"',
                {"pdf_title_match": round(score, 2)})

    if "html" not in (ctype or "").lower() and body[:20].lstrip()[:1] != b"<":
        return None
    meta = html_meta(body)
    if not meta["citation_title"]:
        return None
    sim = title_similarity(cit["title"], meta["citation_title"])
    if sim >= TITLE_SIM:
        return (None, "", {"fetched_title": meta["citation_title"]})
    # Only fire when the page is genuinely about someone else's work.
    if meta["citation_author"]:
        overlap = author_overlap(cit["authors"], ", ".join(meta["citation_author"]))
        if overlap is None or overlap > 0:
            return (None, "", {"fetched_title": meta["citation_title"]})
    return (CLASS_TITLE,
            f'title mismatch: the page at {cit["url"]} declares '
            f'"{meta["citation_title"]}" (similarity {sim:.2f})',
            {"fetched_title": meta["citation_title"],
             "fetched_authors": meta["citation_author"]})


def _fresh(cache, key, now, ttl):
    entry = cache.get(key)
    return bool(entry and entry.get("status") == "ok"
                and (now - entry.get("ts", 0)) < ttl)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    argv = sys.argv[1:]
    external = "--external" in argv
    verbose = "--verbose" in argv or "-v" in argv
    ttl = DEFAULT_TTL
    for i, arg in enumerate(argv):
        if arg == "--ttl" and i + 1 < len(argv):
            ttl = int(argv[i + 1]) * 24 * 3600

    citations = collect_citations()
    pubs = [c for c in citations if c["kind"] == "publication"]
    print(f"Checking {len(citations)} references "
          f"({len(pubs)} publications) across "
          f"{len(list(SENSOR_DIR.glob('*.md')))} sensors...")

    failures, warnings = check_completeness(citations)

    if external:
        print(f"Verifying citations against the network "
              f"(TTL {ttl // (24 * 3600)} days)...")
        net_fail, net_warn, stats, n = run_network_checks(
            citations, ttl, verbose=verbose)
        failures += net_fail
        warnings += net_warn
        print(f"  {n} publication urls: {stats['checked']} checked, "
              f"{stats['cached']} from cache, {stats['unknown']} unknown "
              f"(bot-blocked, not counted as failures)")
    else:
        print("  (offline: completeness only; pass --external to verify "
              "urls and metadata)")

    if warnings:
        print(f"\n{len(warnings)} note(s) -- advisory, these do not "
              f"fail the run:")
        for w in warnings:
            print(f"  NOTE {w}")

    if failures:
        by_class = {}
        for cls, cit, reason in failures:
            by_class.setdefault(cls, []).append((cit, reason))
        print(f"\n{len(failures)} citation problem(s):")
        for cls in CLASS_ORDER:
            items = by_class.get(cls)
            if not items:
                continue
            print(f"\n  [{cls}] {len(items)}")
            for cit, reason in items:
                print(f"    FAIL {label(cit)}")
                print(f"         {reason}")
        print("\nSummary by class: " + ", ".join(
            f"{cls}={len(by_class[cls])}"
            for cls in CLASS_ORDER if cls in by_class))
        return 1

    print(f"\nAll {len(pubs)} publication citations OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
