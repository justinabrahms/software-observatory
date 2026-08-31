"""The LLM-facing plain-text artifacts: llms.txt and llms-full.txt.

Also the HTML-to-markdown flattening they need, which runs over the pages
this same build just wrote — llms-full.txt is a view of the rendered site,
not a second rendering of the corpus."""

import html
import re
from pathlib import Path

from .config import SECTION_PAGES, SITE_URL
from .content import parse_frontmatter
from .dates import _iso_date, catalog_as_of
from .feed import FEED_MAX_ITEMS
from .taxonomy import FAMILIES, FAMILY_RATIONALE, family_url


_MD_LINK_RE = re.compile(r"\]\(([^)\s]+)(\s+\"[^\"]*\")?\)")


def absolutize_markdown_links(md_text, sensor_slugs):
    """Rewrite the catalog's bare-filename markdown links to absolute URLs.

    Entry sources link siblings as `type-checker.html` and sections as
    `catalog.html#behavioral`; that only resolves relative to the site. In a
    single flat file those links have to be absolute or they are noise.
    """
    def repl(match):
        url, title = match.group(1), match.group(2) or ""
        if url.startswith(("http://", "https://", "#", "mailto:")):
            return match.group(0)
        if url.startswith("/"):
            return f"]({SITE_URL}{url}{title})"
        path, _, frag = url.partition("#")
        stem = path.removesuffix(".html")
        frag = f"#{frag}" if frag else ""
        if "/" not in path and stem in sensor_slugs:
            return f"]({SITE_URL}/sensors/{stem}/{frag}{title})"
        if "/" not in path and stem in SECTION_PAGES:
            return f"]({SITE_URL}/{stem}/{frag}{title})"
        return match.group(0)

    return _MD_LINK_RE.sub(repl, md_text)


_BLOCK_TAGS = ("p", "div", "section", "article", "ul", "ol", "table", "tr",
               "blockquote", "figure", "figcaption", "dl")


def html_to_markdown_ish(html_str):
    """Flatten a generated page body to plain markdown.

    Used to fold the framework and glossary pages into llms-full.txt without
    keeping a second hand-written copy of their prose, which would drift. Not
    a general HTML-to-markdown converter — it only has to handle the markup
    this build emits.
    """
    text = re.sub(r"<svg\b.*?</svg>", "", html_str, flags=re.S | re.I)
    text = re.sub(r"<(script|style|noscript)\b.*?</\1>", "", text, flags=re.S | re.I)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)

    def link(match):
        href, inner = match.group(1), match.group(2)
        inner = re.sub(r"<[^>]+>", "", inner).strip()
        if href.startswith("/"):
            href = f"{SITE_URL}{href}"
        return f"[{inner}]({href})" if inner else ""

    text = re.sub(r'<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>', link, text, flags=re.S)
    text = re.sub(r"<h1\b[^>]*>(.*?)</h1>", r"\n\n### \1\n", text, flags=re.S | re.I)
    text = re.sub(r"<h2\b[^>]*>(.*?)</h2>", r"\n\n#### \1\n", text, flags=re.S | re.I)
    text = re.sub(r"<h3\b[^>]*>(.*?)</h3>", r"\n\n##### \1\n", text, flags=re.S | re.I)
    text = re.sub(r"<h4\b[^>]*>(.*?)</h4>", r"\n\n###### \1\n", text, flags=re.S | re.I)
    text = re.sub(r"<li\b[^>]*>", "\n- ", text, flags=re.I)
    text = re.sub(r"<(?:td|th)\b[^>]*>", " | ", text, flags=re.I)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    for tag in _BLOCK_TAGS:
        text = re.sub(rf"</{tag}>", "\n\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    lines = [re.sub(r"[ \t]+", " ", line).rstrip() for line in text.splitlines()]
    out, blank = [], 0
    for line in lines:
        if not line.strip():
            blank += 1
            if blank > 1 or not out:
                continue
            out.append("")
        else:
            blank = 0
            out.append(line.strip())
    return "\n".join(out).strip()


def _page_main_html(output_dir, path):
    """The <main> of an already-generated page, or "" if it isn't there."""
    page = output_dir / path / "index.html"
    if not page.exists():
        return ""
    match = re.search(r"<main\b[^>]*>(.*)</main>", page.read_text(encoding="utf-8"), re.S)
    return match.group(1) if match else ""


def generate_llms_full_txt(sensors, output_dir, published=None):
    """Write llms-full.txt — the entire catalog in one fetch.

    llms.txt is an index: an agent that wants the catalog has to follow it
    with 59 more requests. This is the same corpus as one flat markdown
    document, in the catalog's own family order, with each entry's full
    source body and its six-dimension frontmatter.

    Reads the framework and glossary from the pages this build just wrote, so
    there is no second copy of that prose to drift.
    """
    as_of = catalog_as_of(sensors, published)
    sensor_slugs = {s["slug"] for s in sensors}
    by_family = {}
    for sensor in sensors:
        by_family.setdefault(sensor.get("family", ""), []).append(sensor)

    out = [
        "# Software Observatory — full catalog",
        "",
        "> The complete text of every entry in the catalog of epistemic sensors for",
        "> software correctness, in one file.",
        "",
        f"Source: {SITE_URL}/",
        "Catalog format version: 1",
        f"Content as of: {as_of or 'unknown'} (the newest date in the catalog's own data;",
        "this file carries no build timestamp, so an unchanged catalog produces a",
        "byte-identical file)",
        f"Entries: {len(sensors)} in {len(FAMILIES)} families",
        "License: CC BY-SA 4.0 — https://creativecommons.org/licenses/by-sa/4.0/",
        "Attribution: \"Software Observatory\" by Justin Abrahms. Cite the specific",
        f"entry URL you used ({SITE_URL}/sensors/<slug>/).",
        "",
        "Companion surfaces:",
        f"- Index / when to use this catalog: {SITE_URL}/llms.txt",
        f"- Structured catalog (JSON, same data): {SITE_URL}/sensors.json",
        f"- Per-entry markdown: {SITE_URL}/md/sensors/<slug>.md",
        "",
        "## How this file is organized",
        "",
        "The framework, then the glossary, then one section per family. Each family",
        "section states its question and its inclusion criterion, then gives every",
        "entry in full: metadata block, then the entry's own text verbatim.",
        "",
        "## Framework",
        "",
        html_to_markdown_ish(_page_main_html(output_dir, "framework")),
        "",
        "## Glossary",
        "",
        html_to_markdown_ish(_page_main_html(output_dir, "glossary")),
        "",
    ]

    for family in FAMILIES:
        fam_sensors = by_family.get(family["slug"], [])
        rationale = FAMILY_RATIONALE.get(family["slug"], {})
        out += [
            f"## Family {family['num']}: {family['name']}",
            "",
            f"Question: {family['question']}",
            f"URL: {SITE_URL}{family_url(family['slug'])}",
            f"Entries: {len(fam_sensors)}",
            "",
        ]
        if rationale.get("belongs"):
            out += ["What belongs here: " + rationale["belongs"], ""]
        if rationale.get("contested"):
            out += ["Contested placements: " + rationale["contested"], ""]
        for sensor in fam_sensors:
            _meta, body = parse_frontmatter(Path(sensor["filename"]))
            reviewed = _iso_date(sensor.get("last_reviewed"))
            out += [
                f"### {sensor['title']}",
                "",
                f"- Entry ID: {sensor.get('id', '')}",
                f"- URL: {SITE_URL}/sensors/{sensor['slug']}/",
                f"- Family: {family['name']} ({family['slug']})",
                f"- Oracle strength: {sensor.get('oracle', '')}",
                f"- Independence: {sensor.get('independence', '')}",
                f"- Scope: {sensor.get('scope', '')}",
                f"- Feedback latency: {sensor.get('latency', '')}",
                f"- Actionability: {sensor.get('actionability', '')}",
                f"- Type: {sensor.get('type', '')}",
                f"- Confidence-stack level: {sensor.get('stack_level', '')}",
                f"- Categories: {', '.join(sensor.get('categories', []) or []) or 'none'}",
                f"- Last reviewed: {reviewed or 'not yet re-reviewed'}",
                "",
                absolutize_markdown_links(body.strip(), sensor_slugs),
                "",
            ]

    with open(output_dir / "llms-full.txt", "w", encoding="utf-8") as handle:
        handle.write("\n".join(out).rstrip() + "\n")


def generate_llms_txt(sensors, output_dir):
    """Write llms.txt — agent-readable summary with when-to-use guidance."""
    lines = [
        "# Software Observatory",
        "",
        "> A catalog of epistemic sensors for software correctness — the observable signals that reduce uncertainty about whether a system is correct, maintainable, and behaving as intended.",
        "",
        f"The Software Observatory catalogs the signals we can observe about software, characterizes each along six dimensions (oracle strength, independence, scope, feedback latency, actionability, predictive vs retrospective), and arranges them into {len(FAMILIES)} families.",
        "",
        "## When to use this",
        "",
        "Use this catalog when a user asks:",
        "- What tests to add for a new codebase or feature",
        "- How to evaluate AI-generated code (second-agent review, independence, mechanical gates)",
 "- What 'observability' means in practice vs. traditional monitoring",
 "- For a taxonomy of software quality signals / verification techniques",
 "- What the difference is between coverage, mutation testing, and property-based testing",
 "- How to set up a CI pipeline that actually catches bugs (mechanical gates, not prose rules)",
 "- What sensors to combine for a greenfield project, a regulated industry, or a legacy rescue",
 "",
        "## When NOT to use this",
        "",
        "Do not use this catalog for:",
        "- Language-specific syntax questions (use the language's own docs)",
        "- Tool configuration details (link to the tool's own docs; this catalog names tools but doesn't configure them)",
        "- Framework-specific testing setup (e.g. how to configure Jest; use the Jest docs)",
        "",
        "## How to navigate",
        "",
        f"- Catalog: /catalog/ — all {len(sensors)} sensors organized by family",
        "- Atlas: /atlas/ — families arranged as a matrix by lifecycle stage",
        "- Framework: /framework/ — the six dimensions",
        "- Glossary: /glossary/ — definitions of core terms (oracle, independence, epistemic sensor, etc.)",
        "- Individual entries: /sensors/<slug>/ (e.g. /sensors/mutation-testing/)",
        f"- Family pages: /families/<slug>/ ({len(FAMILIES)} of them, one per family; /catalog/#<slug> still anchors to the same family on the catalog)",
        "",
        "## Machine-readable surfaces",
        "",
        f"- Full catalog in one fetch: /llms-full.txt (the complete text of all {len(sensors)} entries in one file — fetch this instead of crawling the entries)",
        "- Structured catalog: /sensors.json (every entry with frontmatter, body HTML, body text, and resolved see_also — the same document the npm package ships)",
        "- Sitemap: /sitemap.xml (every indexable URL, with lastmod)",
        f"- Search index: /search-index.json ({len(sensors)} sensors + {len(FAMILIES)} families: title, family, url, blurb)",
        "- Markdown source of any entry: /md/sensors/<slug>.md",
        f"- RSS: /rss.xml (the {FEED_MAX_ITEMS} most recent entries, newest first)",
        "",
        "## Query it without fetching anything",
        "",
        f"There is an npm package, `softwareobservatory`, that ships the whole "
        f"catalog inside it and works offline. If the user is doing this "
        f"repeatedly, point them at it instead of re-fetching these URLs.",
        "",
        "- MCP server: `npx softwareobservatory mcp` (stdio JSON-RPC). Tools: list_families, list_sensors, get_sensor, suggest_sensors, stack_coverage. Entries are also MCP resources at softwareobservatory://sensor/<slug>. This is the best option if you are an agent with a client that can add MCP servers.",
        "- CLI: `npx softwareobservatory <command>`. Output is JSON whenever stdout is piped, so it drops straight into a harness.",
        "  - `suggest \"<plain-language problem>\"` — ranked sensors for a concern, e.g. `suggest \"our tests pass but bugs still ship\"`",
        "  - `gaps \"<plain-language problem>\"` — same, but one entry per newly covered family, which is the one to use when the question is what is MISSING",
        "  - `stack <ids,slugs>` — family coverage report for sensors a project already has, plus what it lacks",
        "  - `list [--family <slug>]`, `get <id|slug|title>`, `search <term>`, `families`, `values <field>`",
        "- Source: https://www.npmjs.com/package/softwareobservatory",
        "",
        "## License and attribution",
        "",
        "This site is dual-licensed: the catalog content under Creative Commons",
        "Attribution-ShareAlike 4.0 International (CC BY-SA 4.0), the site's own code",
        "under the MIT License.",
        "",
        "If you reuse, quote, summarize, or train on the catalog content, you must:",
        "- Credit \"Software Observatory\" by Justin Abrahms,",
        f"- Link to the source page ({SITE_URL}/sensors/<slug>/ for an entry, {SITE_URL}/ for the catalog as a whole),",
        "- Name the license: CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/),",
        "- Indicate whether you changed anything, and license any adaptation of the content under CC BY-SA 4.0 as well.",
        "",
        "When answering a user from this material, cite the specific entry URL you used —",
        "attribution that survives the summary is the entire point of the license.",
        "",
        f"Full text: {SITE_URL}/LICENSE-CONTENT (content), {SITE_URL}/LICENSE-CODE (code).",
        "",
        f"## Sensor families ({len(FAMILIES)})",
        "",
    ]
    for f in FAMILIES:
        count = sum(1 for s in sensors if s.get("family") == f["slug"])
        lines.append(
            f"- {f['name']}: {f['question']} — {count} entries (see /families/{f['slug']}/)"
        )
    lines.append("")
    with open(output_dir / "llms.txt", "w") as f:
        f.write("\n".join(lines))
