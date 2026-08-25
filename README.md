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

- **[Catalog](https://softwareobservatory.com/pages/catalog.html)** — 56
  sensor entries across ten families, each documenting what the sensor can
  detect, what it cannot, how easily it's gamed, and what evidence it
  produces.
- **[Atlas](https://softwareobservatory.com/pages/atlas.html)** — the
  families arranged as a navigational matrix: family on one axis, lifecycle
  stage on the other. Empty cells are questions nobody has instrumented yet.
- **[Framework](https://softwareobservatory.com/pages/framework.html)** —
  the six dimensions every sensor is characterized along: oracle strength,
  independence, scope, feedback latency, actionability, predictive vs
  retrospective.
- **[About](https://softwareobservatory.com/pages/about.html)** — the
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
content/sensors/*.md   Source of truth — one file per sensor (YAML frontmatter + markdown)
scripts/build.py      The generator: templates, data, and logic in one file
scripts/check_links.py Internal link/anchor validator over the generated HTML
scripts/export_cli_data.py Emits cli/data/sensors.json on every build
cli/                  Node CLI + MCP server (npm: softwareobservatory)
css/observatory.css    Hand-written stylesheet (design tokens in :root)
js/main.js            No build step — filter, search dropdown, scatter, jumplinks
index.html            Generated (gitignored)
pages/                Generated (gitignored)
search-index.json     Generated (gitignored)
```

`index.html`, `pages/`, and `search-index.json` are **build output** —
gitignored, overwritten by every build, and shipped from the working tree
on deploy. Don't edit them by hand; edit the sources and rebuild.

## Build

The generator is a single Python script. Deps (`pyyaml`, `markdown`) are
pinned in `.venv/` (gitignored).

```sh
.venv/bin/python scripts/build.py
```

This reads `content/sensors/*.md` and regenerates `index.html`,
`pages/*.html`, `pages/sensors/*.html`, and `search-index.json` in place at
the repo root. System `python3` may be missing the `markdown` module — use
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
   slug (`pages/sensors/<slug>.html`).
2. Fill in the YAML frontmatter. See any existing entry (e.g.
   [`content/sensors/linter.md`](content/sensors/linter.md)) for the shape:

   ```yaml
   id: SO-XXX              # unique; see_also and backlinks key off this, not the slug
   title: ...
   family: structural      # must match a slug in build.py FAMILIES
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

Markdown bodies are rendered once and reused at different directory depths.
`build.py` prefixes relative `href`s with `../` for files living in
`pages/`, but **bare filenames matching a sensor slug are left alone** —
they're sibling links that resolve inside `pages/sensors/`. So:
`[type checker](type-checker.html)` for a sibling,
`[catalog](catalog.html#behavioral)` for a catalog section. Root-relative
and absolute URLs are left alone. `check_links.py` will catch any link that
gets this wrong.

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

## License

Site content is published under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
Code is under the license in the repository.

## Acknowledgements

The framing draws on Birgitta Böckeler's "guides & sensors" distinction and
Honeycomb's conception of observability — preserving enough information to
ask questions you didn't know you would need to ask.
