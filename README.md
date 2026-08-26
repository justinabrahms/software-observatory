# Software Observatory

A catalog of **epistemic sensors** for software correctness — the observable
signals that reduce uncertainty about whether a system is correct,
maintainable, and behaving as intended. Not "code quality metrics."
Measurement instruments pointed at different failure modes.

Live at **<https://softwareobservatory.com>**.

Built and maintained by [Justin Abrahms](https://justin.abrah.ms/).

The central question the catalog tries to organize:

> What independent observations would cause us to believe this software is correct?

Software is increasingly an opaque artifact. We cannot — and often do not
want to — fully understand every implementation. The Observatory catalogs
the signals we *can* observe, characterizes each along six dimensions, and
arranges them into ten families so a reader can orient: *what question
am I asking?* and *when can I afford to learn the answer?*

## What's here

- **[Catalog](https://softwareobservatory.com/catalog/)** — 59
  sensor entries across ten families, each documenting what the sensor can
  detect, what it cannot, how easily it's gamed, and what evidence it
  produces.
- **[Atlas](https://softwareobservatory.com/atlas/)** — the
  families arranged as a navigational matrix: family on one axis, lifecycle
  stage on the other. Empty cells are questions nobody has instrumented yet.
- **[Framework](https://softwareobservatory.com/framework/)** —
  the six dimensions every sensor is characterized along: oracle strength,
  independence, scope, feedback latency, actionability, predictive vs
  retrospective.
- **[Glossary](https://softwareobservatory.com/glossary/)** — definitions
  of the core terms: oracle strength, independence, epistemic sensor.
- **[About](https://softwareobservatory.com/about/)** — the
  thesis, inspirations, and how to contribute.

## Querying the catalog (CLI / agents)

The full catalog ships in an npm package, so agents and scripts can query it
offline. JSON is the default output when stdout is piped; `mcp` speaks the
Model Context Protocol over stdio.

```sh
npx softwareobservatory list --family structural
npx softwareobservatory get SO-003
npx softwareobservatory suggest "our tests pass but bugs still ship"
npx softwareobservatory stack linter,SO-003,canary-analysis
npx softwareobservatory mcp   # MCP server for agent clients
```

See [cli/README.md](cli/README.md) for the full command reference and MCP
client configuration.

## Repository layout

```
content/sensors/*.md       Source of truth — one file per sensor (YAML frontmatter + markdown)
scripts/build.py           Entry point for the build
scripts/observatory/       The generator, split by responsibility (see __init__.py)
scripts/check_links.py     Internal link/anchor validator over the generated HTML
scripts/check_frontmatter.py Frontmatter schema validator over content/sensors/*.md
scripts/export_cli_data.py Emits cli/data/sensors.json on every build
cli/                       Node CLI + MCP server (npm: softwareobservatory)
css/observatory.css        Hand-written stylesheet (design tokens in :root)
js/main.js                 No build step — filter, search dropdown, scatter, jumplinks
templates/                 Page templates used by the generator

Generated (all gitignored, all written in place at the repo root):
index.html                 Homepage
catalog/ atlas/ framework/ glossary/ about/ contact/ privacy/ categories/
                           Section pages, one index.html each (clean URLs)
sensors/<slug>/index.html  One page per sensor
md/sensors/*.md            Markdown copies for Accept: text/markdown
search-index.json sitemap.xml robots.txt rss.xml llms.txt 404.html
cli/data/sensors.json      Catalog data for the npm package (committed, not gitignored)
```

Everything in the "generated" block is **build output** — overwritten by
every build and shipped from the working tree on deploy. Don't edit it by
hand; edit the sources and rebuild. The older `pages/*.html` layout is
retired: pages now live at clean directory URLs (`/catalog/`,
`/sensors/<slug>/`), and the build deletes any stale `pages/` directory it
finds.

## Build

The generator is a single Python script. Deps (`pyyaml`, `markdown`) are
pinned in `.venv/` (gitignored).

```sh
.venv/bin/python scripts/build.py
```

This reads `content/sensors/*.md` and regenerates `index.html`, the section
directories (`catalog/`, `atlas/`, ...), `sensors/<slug>/index.html`,
`search-index.json`, and the other feed/metadata files in place at the repo
root. System `python3` may be missing the `markdown` module — use
the venv.

## Preview

```sh
python3 -m http.server
```

Then open <http://localhost:8000>.

## Link check

```sh
.venv/bin/python scripts/check_links.py          # internal links + anchors
.venv/bin/python scripts/check_links.py --external  # also HEADs outbound (needs network)
```

Exits non-zero on broken links. CI-gateable.

## Deploy

`make deploy` builds, then rsyncs the working tree (minus sources and
tooling) to the production host. The deploy key is pinned by `rrsync -wo`
to the site's content directory, so the key can write nowhere else on the
host.

## Adding a sensor

1. Create `content/sensors/<slug>.md`. The filename stem becomes the URL
   slug (`/sensors/<slug>/`).
2. Fill in the YAML frontmatter. See any existing entry (e.g.
   [`content/sensors/linter.md`](content/sensors/linter.md)) for the shape:

   ```yaml
   id: SO-XXX              # unique; see_also and backlinks key off this, not the slug
   title: ...
   family: structural      # must match a slug in observatory/taxonomy.py FAMILIES
   oracle: medium          # minimum | low | medium | high | maximum
   independence: high      # same scale
   scope: module           # free-form, rendered with - → space
   latency: milliseconds  # must be a key of LATENCY_LABELS to get a short badge
   actionability: guiding
   type: predictive
   stack_level: static-analysis  # must match a STACK_LAYERS slug or the sensor
                                  # won't appear in the atlas grid
   categories: [...]       # display-only; a category matching a family slug
                           # (case-insensitive, spaces→hyphens) links to it
   see_also: [SO-001, ...] # sensor IDs; family slugs and the literal "atlas"
                           # also resolve
   ```

3. Write the markdown body. Keep the opening paragraph self-contained —
   it becomes the catalog card blurb and the homepage entry row.
4. Run `.venv/bin/python scripts/build.py`. A `family` with no matching
   entry in `FAMILIES` silently drops the sensor off the catalog and atlas
   (the detail page still generates) — check the build output counts.
5. Run the link checker.

### Relative-link gotcha

Write links in markdown bodies as bare filenames: `[type
checker](type-checker.html)` for another sensor,
`[catalog](catalog.html#behavioral)` for a section page. The renderer
(`observatory/render.py`, `fix_link_depths`) rewrites those to their site-absolute clean URLs
(`/sensors/type-checker/`, `/catalog/#behavioral`), so the same rendered
body works at any depth. Root-relative and absolute URLs are left alone.
`check_links.py` will catch any link that gets this wrong.

## Contributing

The Observatory is meant to be an open reference, and the field should be
able to correct it. The best way to contribute right now:

- **File an issue** at
  <https://github.com/justinabrahms/software-observatory/issues> for a
  factual error, a missing sensor, a taxonomy challenge, or a depth gap.
- **Open a pull request** with a new or revised `content/sensors/*.md`.
  Keep the opening paragraph self-contained; match the frontmatter shape
  above; run the build and the link checker before submitting.

The catalog applies a producer-evaluator principle to itself: the author
shouldn't be the only evaluator. Independent review of the content is
welcome and explicitly invited.

By opening a pull request you agree to license your contribution under the
license that already covers the files you touched: MIT for code, CC BY-SA
4.0 for catalog content. See [License](#license) below.

## License

This repository is dual-licensed. The split is by kind of file, not by
directory accident:

| What | License | File |
|------|---------|------|
| **Code** — `scripts/`, `cli/bin/`, `cli/lib/`, `cli/test/`, `css/`, `js/`, `templates/` | MIT (`MIT`) | [LICENSE-CODE](LICENSE-CODE) |
| **Content & data** — `content/sensors/*.md`, the generated site prose, `md/`, `rss.xml`, `llms.txt`, and `cli/data/sensors.json` | CC BY-SA 4.0 (`CC-BY-SA-4.0`) | [LICENSE-CONTENT](LICENSE-CONTENT) |

The code is MIT so it can be copied, vendored, and shipped without anyone
asking a lawyer first — including by license scanners in corporate CI, which
routinely block Creative Commons licenses on software. The catalog content
stays under CC BY-SA 4.0: it is prose, and attribution should travel with it.

The npm package `softwareobservatory` is MIT software that bundles CC BY-SA
4.0 data at `data/sensors.json`. Querying the CLI or the MCP server carries no
obligations; republishing the catalog content does.

### Attribution

Copy-paste this when you reuse the catalog content:

> "Software Observatory" by [Justin Abrahms](https://justin.abrah.ms/),
> <https://softwareobservatory.com>, licensed under [CC BY-SA
> 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

Plain text:

```
"Software Observatory" by Justin Abrahms (https://softwareobservatory.com),
licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/).
```

HTML:

```html
<a href="https://softwareobservatory.com">Software Observatory</a> by Justin
Abrahms, licensed under <a
href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a>.
```

ShareAlike means a work built on the catalog content is shared under CC BY-SA
4.0 too. Quoting an entry, linking to a sensor page, or having an agent read
the catalog to answer a question is not that — it is use, not redistribution.

## Acknowledgements

The framing draws on Birgitta Böckeler's "guides & sensors" distinction and
Honeycomb's conception of observability — preserving enough information to
ask questions you didn't know you would need to ask.
