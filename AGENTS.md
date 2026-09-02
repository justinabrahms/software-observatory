# AGENTS.md — Software Observatory

Static site for [softwareobservatory.com](https://softwareobservatory.com): a
catalog of "epistemic sensors" for software correctness. No framework —
one Python generator script plus hand-written CSS/JS, and a zero-dependency
Node CLI/MCP server in `cli/` (published to npm as `softwareobservatory`).

## Commands

- **Build:** `.venv/bin/python scripts/build.py` — reads `content/sensors/*.md`,
  regenerates `index.html`, `<section>/index.html` (catalog, atlas, framework,
  glossary, about, contact, privacy, categories), `sensors/<slug>/index.html`,
  `search-index.json`, **and `cli/data/sensors.json`** (via
  `scripts/export_cli_data.py`) in place at the repo root. Site output is
  gitignored; `cli/data/sensors.json` is **committed** so the npm package can
  ship it. System `python3` is missing the `markdown` module; always use
  `.venv/bin/python`.
- **CLI test:** `node cli/test/smoke.mjs` (or `make cli-test`) — exercises
  every CLI command plus the MCP handshake. Needs Node >= 18, no npm
  dependencies.
- **Link check:** `.venv/bin/python scripts/check_links.py` — validates internal
  links and `#anchors` across all generated HTML, exits 1 on breakage
  (CI-gateable). `--external` also HEADs outbound links (needs network).
- **Preview:** `python3 -m http.server` from the repo root, then open
  `http://localhost:8000`.
- **Every gate: `make check`** — the one command to run before pushing.
  It runs `test`, `check-frontmatter`, `check-citations`, `build`,
  `check-links`, `cli-test` and `check-deploy`, in the order CI runs them, so
  green locally means green in CI. Run this instead of remembering the
  individual scripts; `scripts/check_frontmatter.py` gates every deploy and was
  mentioned in no human-facing doc, which is how it broke CI unnoticed.
- **Tests/lint:** `make test` runs `scripts/test_build.py` — golden-file
  snapshot tests over the fixture catalog in `tests/fixtures/content/`, plus a
  byte-for-byte determinism assertion and gate tests that prove a bad
  `family`/`see_also`/`stack_level` fails before any file is written. Stdlib
  `unittest`, no pytest, ~0.2s, no network and no browser. `make cli-test`
  covers the CLI (`cli/test/smoke.mjs`). After an *intentional* rendering
  change, re-bless with `make test-update` and commit the `tests/golden/` diff
  in the same commit — that diff is the review artifact. Do not eyeball the
  generated HTML in place of reading it.

Deps are pinned in the tracked `requirements.txt`; `.venv/` itself is
gitignored. Recreate it with
`python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`, which is
exactly what CI does. The `--watch` flag mentioned in the `scripts/build.py`
docstring is **not implemented** — `sys.argv` is never parsed.

## Deployment and local browser setup

These are documented in a private, untracked `OPERATIONS.md` at the repo root
(gitignored). They named the production host, its IP, the deploy key path, the
DNS account and the ACME credential path, which is free reconnaissance in a
public file and helps no contributor — see issue #118. Ask if you need them.

For tracked files the rule is: no hostnames, no IPs, no account numbers, no
credential paths, and nothing about other projects' infrastructure.

## Architecture

Everything flows through `scripts/build.py`, which is a thin entry point over
the `scripts/observatory/` package — one module per responsibility, mapped in
`observatory/__init__.py`. That package is the entire CMS:

1. `content.load_sensors()` parses every `content/sensors/*.md` (YAML
   frontmatter + markdown body) into a dict.
2. `content.compute_backlinks()` inverts `see_also:` references into a "What
   links here" list per sensor.
3. The page generators in `observatory/pages/` (`home.py`, `catalog.py`,
   `atlas.py`, `framework.py`, `about.py`, `sensor.py`, …) build HTML via
   **inline f-string templates** and write it directly to the site root.
4. `observatory/site.py` (`main()`) is the running order of a whole build,
   and `observatory/gates.py` holds everything that refuses to publish.

The `templates/` directory is **empty** — templates are f-strings in
`observatory/layout.py` (`html_head`, `html_header`, `html_footer`,
`html_page`) plus per-page `body = f"""..."""` blocks in
`observatory/pages/`. Do not look for Jinja.

Shared site data (the sensor families, confidence-stack layers, oracle
bar widths, latency labels, and the homepage scatter axes `STACK_SCATTER` /
`LATENCY_X` / `ORACLE_Y`) are module-level constants in
`observatory/taxonomy.py`. Adding or renumbering a family means editing
`FAMILIES` there
— and adding a `--fam-<slug>` color token in `css/observatory.css`, which
the homepage scatter legend and dots key off.

## Directory layout

| Path | Role |
|------|------|
| `scripts/build.py` | Entry point. Runs the build; re-exports the names the other scripts import. |
| `scripts/observatory/` | The generator, one module per responsibility (`taxonomy`, `render`, `content`, `layout`, `jsonld`, `pages/`, `gates`, `site`, …). Read `__init__.py` first. |
| `scripts/check_links.py` | Internal link/anchor validator over the generated HTML. |
| `scripts/export_cli_data.py` | Emits `cli/data/sensors.json`; runs at the end of every build. |
| `infra/caddy/` | The live Caddy site block, tracked as a record. Nothing in this repo applies it — the deploy key is pinned to static files on purpose. `CADDY_HOST=... make check-caddy` diffs repo against server, read-only; it is not in `make check` because CI cannot read the server's config. |
| `cli/` | Zero-dependency Node CLI + MCP server (npm package `softwareobservatory`). `bin/softwareobservatory.mjs` is the entry; `lib/core.mjs` holds query logic; `lib/mcp.mjs` is the stdio JSON-RPC server; `data/sensors.json` is committed build output. |
| `content/sensors/*.md` | Source of truth for sensor entries (YAML frontmatter). |
| `content/pages/` | Empty; reserved. |
| `.gitignore` note | `pages/` entry retained for historical output; new layout dirs (`catalog/`, `sensors/`, …) are also ignored. |
| `index.html`, `catalog/`, `atlas/`, `sensors/`, `search-index.json` | **Generated output** — gitignored, overwritten by every build; deploys ship it from the working tree. |
| `css/observatory.css` | Hand-written stylesheet (design tokens in `:root` at top). |
| `js/main.js` | No build step. Family filter, card a11y, header search dropdown, heading-jumplink copy buttons, homepage scatter toggle + legend isolation. |
| `archive-NMUHEr/` | Untracked crush release tarball. Ignore. |

## Adding a sensor (the main workflow)

1. Create `content/sensors/<slug>.md`. The filename stem becomes the URL
   slug (`/sensors/<slug>/`).
2. Fill in frontmatter — see any existing entry (e.g.
   `content/sensors/linter.md`) for the shape:

   ```yaml
   id: SO-XXX            # unique; see_also and backlinks key off this, NOT the slug
   title: ...
   family: structural    # must match a slug in observatory/taxonomy.py FAMILIES
   oracle: medium        # minimum|low|medium|high|maximum
   independence: high    # same scale
   scope: module         # free-form, rendered with - → space
   latency: milliseconds # must be a key of LATENCY_LABELS to get a short badge
   actionability: guiding
   type: predictive
   stack_level: static-analysis  # must match a STACK_LAYERS slug or the
                                 # sensor won't appear in the atlas grid;
                                 # each slug maps to a LIFECYCLE_STAGES
                                 # column via STAGE_BY_LEVEL
   categories: [...]     # display-only; a category matching a family slug
                         # (case-insensitive, spaces→hyphens) links to it
   see_also: [SO-001, ...]       # sensor IDs; family slugs and the literal
                                 # "atlas" also resolve (see resolve_see_also)
   ```
3. Run `.venv/bin/python scripts/build.py`. A `family` with no matching entry in
   `FAMILIES` silently drops the sensor off the catalog and atlas pages
   (the detail page still generates) — check build output counts.

### Relative-link gotcha

Markdown bodies link by **bare filename**: `[type checker](type-checker.html)`
for a sibling sensor, `[catalog](catalog.html#behavioral)` for a catalog
section. `fix_link_depths()` rewrites these to **site-absolute URLs**
(`/sensors/type-checker/`, `/catalog/#behavioral`) at render time, so every
page emits absolute links regardless of its own depth. Unrecognized targets
are left alone and `check_links.py` will flag them.

## Conventions

- **Generated files are gitignored.** `index.html`, the section directories
  (`catalog/`, `atlas/`, …), `sensors/`, and `search-index.json` are build
  output; run the build locally to preview, and `make deploy` rsyncs the
  freshly built working tree.
- **HTML style:** 2-space indent, double quotes, CSS custom properties
  (`var(--accent)` etc.) for all colors; design tokens live in `:root` at
  the top of `css/observatory.css`. Dark theme, Fraunces/Inter/JetBrains
  Mono loaded from Google Fonts.
- **Inline links in generated/prose HTML** get class `wikilink`;
  `fix_link_depths` auto-adds `class="body-link"` to markdown-rendered
  `<a>` tags lacking a class.
- **Python style in `scripts/observatory/`:** 4-space indent, section banners like
  `# ── Sensor family metadata ────...`, type hints absent, f-strings
  everywhere. Match it.
- No em dashes in code. The CSS and prose content use them freely.
- Emoji-free UI; the logo mark is a `◐` character.

## Gotchas

- Running the build is the only way to see changes to `css/` or `js/` take
  effect *structurally* (they're copied by reference, not processed), but
  content/template changes require a build + browser refresh. There is no
  dev server or watch mode.
- `generate_index_page` hard-codes featured sensor `SO-003` (mutation
  testing) and the "recent entries" are just the first 6 sensors by
  filename sort — not actually sorted by date.
- The catalog page's sensor blurb comes from `blurb_text()`: first rendered
  *paragraph* (not line — markdown source is hard-wrapped), tags stripped,
  entities decoded, cut at a sentence boundary inside 200 chars with a
  word-boundary ellipsis fallback. Keep the opening paragraph of each
  sensor self-contained.
- The atlas grid cell is keyed on `stack_level` (singular) matching
  `STACK_LAYERS` slugs exactly, which then fold into `LIFECYCLE_STAGES`
  columns via `STAGE_BY_LEVEL`; a typo yields a silently empty cell.
- The atlas dependency graph derives edges from `see_also` references to
  family slugs (`change-family`, plain slugs like `adversarial`, or sensor
  IDs resolved to their family); only the strongest ~14 edges are drawn.
- Content headings (h2/h3 in the main column) get ids injected at build
  time by `add_heading_ids()` inside `html_page`, slugified from the
  heading text and de-duped per page. The hover "copy jumplink" icons in
  `main.js` target a hard-coded selector list (`.section-heading`,
  `.property-detail-title`, `.family-title`, `.featured-title`,
  `.about-content h2`, `.signal-detail-body h2`) — extend both places when
  adding a new content section type.
