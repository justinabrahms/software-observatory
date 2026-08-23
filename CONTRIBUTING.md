# Contributing to the Software Observatory

The Observatory is meant to be an open reference, and the field should be
able to correct it. The catalog applies a producer-evaluator principle to
itself: the author shouldn't be the only evaluator. Independent review of
the content is welcome and explicitly invited.

## Ways to contribute

- **File an issue** at
  <https://github.com/justinabrahms/software-observatory/issues> for a
  factual error, a missing sensor, a taxonomy challenge, or a depth gap.
- **Open a pull request** with a new or revised `content/sensors/*.md`.
- **Propose a family change** (adding, renumbering, or reclassifying a
  family) via an issue first — these touch `FAMILIES` in `scripts/build.py`
  and the `--fam-<slug>` color tokens in `css/observatory.css`, so they're
  worth discussing before the work.

## Before you submit

You'll need the venv (deps `pyyaml` and `markdown` are pinned in `.venv/`,
which is gitignored). If you don't have it, create one:

```sh
python3 -m venv .venv
.venv/bin/pip install pyyaml markdown
```

Then build and check links:

```sh
.venv/bin/python scripts/build.py
.venv/bin/python scripts/check_links.py
```

The build regenerates `index.html`, `pages/*.html`, `pages/sensors/*.html`,
and `search-index.json` in place at the repo root. The link checker exits
non-zero on broken internal links or anchors — fix any failures before
opening the PR.

## Adding a sensor

1. Create `content/sensors/<slug>.md`. The filename stem becomes the URL
   slug (`pages/sensors/<slug>.html`).
2. Fill in the YAML frontmatter:

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
4. Build and check links (above). A `family` with no matching entry in
   `FAMILIES` silently drops the sensor off the catalog and atlas (the
   detail page still generates) — check the build output counts.
5. Open the PR.

### Relative-link gotcha

Markdown bodies are rendered once and reused at different directory depths.
`build.py` prefixes relative `href`s with `../` for files living in `pages/`,
but **bare filenames matching a sensor slug are left alone** — they're
sibling links that resolve inside `pages/sensors/`. So:

- `[type checker](type-checker.html)` for a sibling
- `[catalog](catalog.html#behavioral)` for a catalog section
- Root-relative and absolute URLs are left alone

`check_links.py` will catch any link that gets this wrong.

## Editing an existing sensor

Open `content/sensors/<slug>.md` directly. The frontmatter is the source of
truth for the properties table, atlas placement, and backlinks; the body is
the source for the blurb and the entry content. Rebuild and re-check links
after editing.

## Style

- **Markdown:** hard-wrap prose at ~70 characters (the existing entries do,
  and `blurb_text()` takes the first *paragraph*, not the first line).
- **HTML output:** 2-space indent, double quotes, CSS custom properties
  (`var(--accent)` etc.) for all colors; design tokens live in `:root` at
  the top of `css/observatory.css`.
- **Python in `build.py`:** 4-space indent, section banners like
  `# ── Sensor family metadata ────...`, f-strings everywhere. Match it.
- No em dashes in code. The CSS and prose content use them freely.
- Emoji-free UI.

## License

By contributing, you agree your content contributions will be licensed
under
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/),
the same license as the rest of the site content.
