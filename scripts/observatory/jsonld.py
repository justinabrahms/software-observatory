"""Structured data (JSON-LD) builders.

One serializer, used by every page. Hand-built JSON strings are how invalid
structured data gets shipped; everything here goes through json.dumps and
gates.assert_json_ld_parses() re-reads every emitted block before the build
is allowed to finish."""

from .config import SITE_URL
from .render import blurb_text


# ── Structured data (JSON-LD) ───────────────────────────────────────────────
#
# One serializer, used by every page. Hand-built JSON strings are how invalid
# structured data gets shipped: a quote or an em-dash in an entry title breaks
# the block, the page still renders, and nobody notices. Everything here goes
# through json.dumps, and assert_json_ld_parses() re-reads every emitted block
# out of the generated HTML before the build is allowed to finish.

AUTHOR_LD = {
    "@type": "Person",
    "@id": "https://softwareobservatory.com/#author",
    "name": "Justin Abrahms",
    "url": "https://justin.abrah.ms",
    "email": "mailto:justin@abrah.ms",
    "sameAs": [
        "https://github.com/justinabrahms",
        "https://bsky.app/profile/justin.abrah.ms",
        "https://www.linkedin.com/in/justinabrahms",
    ],
}


ORGANIZATION_LD = {
    "@type": "Organization",
    "@id": "https://softwareobservatory.com/#organization",
    "name": "Software Observatory",
    "url": "https://softwareobservatory.com",
    "logo": "https://softwareobservatory.com/og.png",
    "founder": {"@id": "https://softwareobservatory.com/#author"},
}


CONTENT_LICENSE = "https://creativecommons.org/licenses/by-sa/4.0/"


# @ids the blocks use to refer to each other rather than repeating themselves.
CATALOG_TERMSET_ID = "https://softwareobservatory.com/catalog/#defined-term-set"


GLOSSARY_TERMSET_ID = "https://softwareobservatory.com/glossary/#defined-term-set"


def family_termset_id(slug):
    return f"{SITE_URL}/families/{slug}/#defined-term-set"


def json_ld_script(json_ld):
    """Serialize one JSON-LD object, or several as an @graph.

    Accepts a dict, a list of dicts, or an already-serialized string (the
    homepage used to pass one). `<` is escaped so no content can close the
    surrounding <script> element.
    """
    import json as _json
    if isinstance(json_ld, (list, tuple)):
        payload = {"@context": "https://schema.org", "@graph": list(json_ld)}
    elif isinstance(json_ld, dict):
        payload = dict(json_ld)
        payload.setdefault("@context", "https://schema.org")
    else:
        return str(json_ld).replace("<", "\\u003c")
    return _json.dumps(payload, indent=2, ensure_ascii=False).replace("<", "\\u003c")


def breadcrumb_ld(trail):
    """BreadcrumbList from [(name, site-relative path or None), ...].

    Fed from the same list that renders the visible breadcrumb, so the two
    cannot disagree — which is the only reason visible-breadcrumb markup is
    worth emitting at all.
    """
    items = []
    for position, (name, path) in enumerate(trail, start=1):
        item = {
            "@type": "ListItem",
            "position": position,
            "name": name,
        }
        if path is not None:
            item["item"] = f"{SITE_URL}{path}"
        items.append(item)
    return {"@type": "BreadcrumbList", "itemListElement": items}


def sensor_term_ld(sensor, termset_id):
    """A sensor as a schema.org DefinedTerm."""
    return {
        "@type": "DefinedTerm",
        "@id": f"{SITE_URL}/sensors/{sensor['slug']}/#term",
        "name": sensor["title"],
        "description": blurb_text(sensor.get("body_html", ""), 200),
        "termCode": sensor.get("id", ""),
        "url": f"{SITE_URL}/sensors/{sensor['slug']}/",
        "inDefinedTermSet": {"@id": termset_id},
    }


# ── The rating vocabulary ───────────────────────────────────────────────────
#
# Every entry carries `oracle: high`, `independence: medium`, `scope: function`
# and three more — 59 entries rated against a six-dimension vocabulary that,
# until this block existed, was defined only as prose in <h3> headings on
# /framework/. Nothing machine-readable said what the dimensions were, and
# nothing bound a rating to its definition, so the ratings were loose strings
# to anyone reading the site with a parser.
#
# The anchors are the real heading ids on /framework/ (add_heading_ids
# generates them from the <h2> text), so every @id here resolves to the
# passage that defines the term. The descriptions are that section's own
# question, copied rather than paraphrased — a second wording of a definition
# is a second definition, and it will drift.

FRAMEWORK_TERMSET_ID = f"{SITE_URL}/framework/#defined-term-set"

# (frontmatter key, display name, /framework/ anchor, the section's question)
FRAMEWORK_DIMENSIONS = (
    ("oracle", "Oracle strength", "oracle-strength",
     "How confidently does it know that something is wrong?"),
    ("independence", "Independence", "independence",
     "Can the thing being evaluated manipulate the sensor?"),
    ("scope", "Scope", "scope",
     "What level of the system does it tell us about?"),
    ("latency", "Feedback latency", "feedback-latency",
     "How long until the sensor tells you something?"),
    ("actionability", "Actionability", "actionability",
     'Does it merely say "bad" or does it tell you what to fix?'),
    ("type", "Predictive vs retrospective", "predictive-vs-retrospective",
     '"This is wrong" or "this looks like things that became wrong before"?'),
)


def dimension_term_id(anchor):
    return f"{SITE_URL}/framework/#{anchor}"


def framework_termset_ld():
    """The six dimensions as a DefinedTermSet, one DefinedTerm each."""
    return {
        "@type": "DefinedTermSet",
        "@id": FRAMEWORK_TERMSET_ID,
        "name": "Sensor properties",
        "description": (
            "The six dimensions every entry in the Software Observatory "
            "catalog is characterized along."
        ),
        "url": f"{SITE_URL}/framework/",
        "inLanguage": "en",
        "license": CONTENT_LICENSE,
        "creator": AUTHOR_LD,
        "hasDefinedTerm": [
            {
                "@type": "DefinedTerm",
                "@id": dimension_term_id(anchor),
                "name": name,
                "description": question,
                "termCode": key,
                "url": dimension_term_id(anchor),
                "inDefinedTermSet": {"@id": FRAMEWORK_TERMSET_ID},
            }
            for key, name, anchor, question in FRAMEWORK_DIMENSIONS
        ],
    }


def sensor_rating_properties(sensor):
    """A sensor's ratings as PropertyValues bound to the framework's terms.

    propertyID is the dimension's @id on /framework/, so `oracle: high` stops
    being a bare string and becomes a value of a named, defined property that
    something else can resolve. Dimensions the entry does not rate are
    omitted rather than emitted empty.
    """
    properties = []
    for key, name, anchor, _question in FRAMEWORK_DIMENSIONS:
        value = sensor.get(key) or sensor.get("frontmatter", {}).get(key)
        if not value:
            continue
        prop = {
            "@type": "PropertyValue",
            "propertyID": dimension_term_id(anchor),
            "name": name,
            "value": str(value),
        }
        note = (sensor.get(f"{key}_note")
                or sensor.get("frontmatter", {}).get(f"{key}_note"))
        if note:
            prop["description"] = str(note)
        properties.append(prop)
    return properties


# ── The catalog as data ─────────────────────────────────────────────────────
#
# sensors.json is 890 KB of the entire catalog and llms-full.txt is the whole
# corpus as text. Both are served publicly and, before this block, nothing in
# the graph said either existed — so the most reusable artifacts on the site
# were also the least discoverable, and travelled with no license attached.
# `license` is repeated on each distribution deliberately: a DataDownload is
# routinely fetched on its own, and a license that only appears on the parent
# does not travel with the file.

CATALOG_DATASET_ID = f"{SITE_URL}/catalog/#dataset"


def catalog_dataset_ld(sensor_count, family_count):
    return {
        "@type": "Dataset",
        "@id": CATALOG_DATASET_ID,
        "name": "Software Observatory sensor catalog",
        "description": (
            f"{sensor_count} epistemic sensors for software correctness, in "
            f"{family_count} families, each characterized along six "
            "dimensions and annotated with what it cannot detect."
        ),
        "url": f"{SITE_URL}/catalog/",
        "inLanguage": "en",
        "isAccessibleForFree": True,
        "license": CONTENT_LICENSE,
        "creator": AUTHOR_LD,
        "publisher": {"@id": ORGANIZATION_LD["@id"]},
        "variableMeasured": [
            {
                "@type": "PropertyValue",
                "propertyID": dimension_term_id(anchor),
                "name": name,
                "description": question,
            }
            for _key, name, anchor, question in FRAMEWORK_DIMENSIONS
        ],
        "distribution": [
            {
                "@type": "DataDownload",
                "name": "Full catalog as JSON",
                "encodingFormat": "application/json",
                "contentUrl": f"{SITE_URL}/sensors.json",
                "license": CONTENT_LICENSE,
            },
            {
                "@type": "DataDownload",
                "name": "Full catalog as Markdown",
                "encodingFormat": "text/markdown",
                "contentUrl": f"{SITE_URL}/llms-full.txt",
                "license": CONTENT_LICENSE,
            },
        ],
    }


def page_ld(page_type, name, path, description, extra=None):
    """A plain page node, for the pages that are not a term set or an entry.

    These pages carried no structured data at all, which meant the license
    and the author were asserted on most of the site and silently absent on
    the rest.
    """
    node = {
        "@type": page_type,
        "@id": f"{SITE_URL}{path}#page",
        "name": name,
        "description": description,
        "url": f"{SITE_URL}{path}",
        "inLanguage": "en",
        "license": CONTENT_LICENSE,
        "isPartOf": {"@id": ORGANIZATION_LD["@id"]},
        "author": AUTHOR_LD,
    }
    if extra:
        node.update(extra)
    return node
