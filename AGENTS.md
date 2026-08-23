# AGENTS.md — Software Observatory

Static site for [softwareobservatory.com](https://softwareobservatory.com): a
catalog of "epistemic sensors" for software correctness. No framework —
one Python generator script plus hand-written CSS/JS, and a zero-dependency
Node CLI/MCP server in `cli/` (published to npm as `softwareobservatory`).

## Commands

- **Build:** `.venv/bin/python scripts/build.py` — reads `content/sensors/*.md`,
  regenerates `index.html`, `pages/*.html`, `pages/sensors/*.html`,
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
- **Tests/lint:** `cli/test/smoke.mjs` covers the CLI. For site changes,
  verification = run the build and eyeball the generated HTML.

Deps (`pyyaml`, `markdown`) are already installed in `.venv/` (gitignored).
The `--watch` flag mentioned in the `scripts/build.py` docstring is **not
implemented** — `sys.argv` is never parsed.

## Deployment

Live at https://softwareobservatory.com (apex + `www`). `make deploy`
builds, then rsyncs the repo (minus sources and tooling) to
`observer@abrah.ms:.` using `~/.ssh/softwareobservatory-deploy`.

On the server (`moustachium`, 68.183.69.149), Caddy serves
`/srv/softwareobservatory.com` for `softwareobservatory.com, www...` with a
DNS-01 cert via the dnsimple plugin (token in `/etc/caddy/dnsimple.env`), so
certs are issued without waiting on DNS propagation. The `observer` user's
sole authorized key is pinned by `rrsync -wo /srv/softwareobservatory.com` —
the same one-key-per-site pattern as the `sublayer` deploys — which is why
the rsync destination is `.` rather than the absolute path. A/AAAA records
live in the dnsimple zone `softwareobservatory.com` (account 44245); both
point at 68.183.69.149.

## Driving a browser (style/visual work)

Two working paths on this machine (system `apt` is blocked and Chromium
needs `libasound.so.2`, which was extracted by hand into `.browser-libs/`):

- **chrome-devtools MCP** (preferred): configured in
  `~/.config/crush/crushrc` as MCP `chrome-devtools` — headless, isolated
  profile, `LD_LIBRARY_PATH=.browser-libs/usr/lib/x86_64-linux-gnu`,
  executable = the Playwright chromium-headless-shell in
  `~/.cache/ms-playwright/`. Gives `navigate_page`, `take_screenshot`,
  `take_snapshot`, `evaluate_script`, `list_console_messages`, etc.
  Restart the session after config changes for it to connect.
- **Playwright from the venv**: `playwright` is installed in `.venv`.
  Launch with
  `LD_LIBRARY_PATH="$PWD/.browser-libs/usr/lib/x86_64-linux-gnu" .venv/bin/python script.py`
  (the env var is mandatory or Chromium dies with exit 127 on libasound).

Serve the site first: `python3 -m http.server` from the repo root, then
point the browser at `http://localhost:8000/`.

## Architecture

Everything flows through `build.py` (~1500 lines). It is the entire CMS:

1. `load_sensors()` parses every `content/sensors/*.md` (YAML frontmatter +
   markdown body) into a dict.
2. `compute_backlinks()` inverts `see_also:` references into a "What links
   here" list per sensor.
3. Page generators (`generate_index_page`, `generate_catalog_page`,
   `generate_atlas_page`, `generate_framework_page`, `generate_about_page`,
   `generate_sensor_page`) build HTML via **inline f-string templates** and
   write it directly to the site root.

The `templates/` directory is **empty** — templates are f-strings inside
`build.py` (`html_head`, `html_header`, `html_footer`, `html_page`, plus
per-page `body = f"""..."""` blocks). Do not look for Jinja.

Shared site data (the 11 sensor families, confidence-stack layers, oracle
bar widths, latency labels, and the homepage scatter axes `STACK_SCATTER` /
`LATENCY_X` / `ORACLE_Y`) are module-level constants at the top of
`build.py`. Adding or renumbering a family means editing `FAMILIES` there
— and adding a `--fam-<slug>` color token in `css/observatory.css`, which
the homepage scatter legend and dots key off.

## Directory layout

| Path | Role |
|------|------|
| `scripts/build.py` | The whole generator. Templates + data + logic in one file. |
| `scripts/check_links.py` | Internal link/anchor validator over the generated HTML. |
| `scripts/export_cli_data.py` | Emits `cli/data/sensors.json`; runs at the end of every build. |
| `cli/` | Zero-dependency Node CLI + MCP server (npm package `softwareobservatory`). `bin/softwareobservatory.mjs` is the entry; `lib/core.mjs` holds query logic; `lib/mcp.mjs` is the stdio JSON-RPC server; `data/sensors.json` is committed build output. |
| `content/sensors/*.md` | Source of truth for sensor entries (YAML frontmatter). |
| `content/pages/` | Empty; reserved. |
| `index.html`, `pages/`, `search-index.json` | **Generated output** — gitignored, overwritten by every build; deploys ship it from the working tree. |
| `css/observatory.css` | Hand-written stylesheet (design tokens in `:root` at top). |
| `js/main.js` | No build step. Family filter, card a11y, header search dropdown, heading-jumplink copy buttons, homepage scatter toggle + legend isolation. |
| `archive-NMUHEr/` | Untracked crush release tarball. Ignore. |

## Adding a sensor (the main workflow)

1. Create `content/sensors/<slug>.md`. The filename stem becomes the URL
   slug (`pages/sensors/<slug>.html`).
2. Fill in frontmatter — see any existing entry (e.g.
   `content/sensors/linter.md`) for the shape:

   ```yaml
   id: SO-XXX            # unique; see_also and backlinks key off this, NOT the slug
   title: ...
   family: structural    # must match a slug in build.py FAMILIES
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

Markdown bodies are rendered once and reused at different directory depths.
`fix_link_depths()` prefixes relative `href`s with `../` for files living
in `pages/` (catalog.html, atlas.html, ...), but **bare filenames matching
a sensor slug are left alone** — they are sibling links that resolve inside
`pages/sensors/`. So: `[type checker](type-checker.html)` for a sibling,
`[catalog](catalog.html#behavioral)` for a catalog section. Root-relative
and absolute URLs are left alone. `check_links.py` will catch any link
that gets this wrong.

## Conventions

- **Generated files are gitignored.** `index.html`, `pages/`, and
  `search-index.json` are build output; run the build locally to preview,
  and `make deploy` rsyncs the freshly built working tree.
- **HTML style:** 2-space indent, double quotes, CSS custom properties
  (`var(--accent)` etc.) for all colors; design tokens live in `:root` at
  the top of `css/observatory.css`. Dark theme, Fraunces/Inter/JetBrains
  Mono loaded from Google Fonts.
- **Inline links in generated/prose HTML** get class `wikilink`;
  `fix_link_depths` auto-adds `class="body-link"` to markdown-rendered
  `<a>` tags lacking a class.
- **Python style in build.py:** 4-space indent, section banners like
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
