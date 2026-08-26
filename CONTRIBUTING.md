# Contributing to the Software Observatory

The Observatory is meant to be an open reference, and the field should be
able to correct it. The catalog applies a producer-evaluator principle to
itself: the author shouldn't be the only evaluator. Independent review of
the content is welcome and explicitly invited.

## Ways to contribute

- **[Propose a sensor](https://github.com/justinabrahms/software-observatory/issues/new?template=sensor-proposal.yml)**
  — the contribution this project most wants. The form asks for the six
  property ratings and for what the sensor *cannot* detect; a proposal that
  arrives already rated is arguable, which is worth more than one that is
  merely described. You do not have to open a PR.
- **[Correct an entry](https://github.com/justinabrahms/software-observatory/issues/new?template=correction.yml)**
  — a factual error, a rating you disagree with, a claim without a source, a
  dead link.
- **[Challenge the taxonomy](https://github.com/justinabrahms/software-observatory/issues/new?template=taxonomy.yml)**
  — a family added, renumbered, or reclassified, a dimension redefined, a
  stack level wrong. File the issue *before* the work: these touch `FAMILIES`
  in `scripts/build.py` and the `--fam-<slug>` color tokens in
  `css/observatory.css`, they re-rate existing entries, and they are a major
  version bump (see [Releasing](#releasing)).
- **Open a pull request** with a new or revised `content/sensors/*.md`.

Conduct is covered by the [Code of Conduct](.github/CODE_OF_CONDUCT.md);
security reports go to the [security policy](.github/SECURITY.md), privately,
not to a public issue.

## Before you submit

Set up the venv once. Dependencies are pinned in the tracked
`requirements.txt`; `.venv/` itself is gitignored, so it is not a manifest
and never was:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Then run **one command** before every PR:

```sh
make check
```

That is the whole contract. `make check` runs every gate CI runs, in the
order CI runs them — frontmatter and vocabulary validation
(`scripts/check_frontmatter.py`), the offline citation check, the build, the
internal link and anchor check, the CLI smoke test, and the deploy-manifest
check — and prints `All gates passed.` when it is green. If it is green
locally, CI is green.

Please do not substitute the individual scripts for it. Running the build and
the link checker by hand was what this file used to ask for, and it misses
the frontmatter gate entirely: that gate rejects an unknown `family`, an
out-of-vocabulary reference kind, or a `stack_level` typo, all of which
otherwise fail in CI *after* you have opened the PR. It broke CI once while
being mentioned in no human-facing document, which is why there is now one
documented command instead of a list to remember.

The build regenerates `index.html`, the section directories (`catalog/`,
`atlas/`, `framework/`, …), `sensors/<slug>/index.html`, `search-index.json`
and `cli/data/sensors.json` in place at the repo root. Everything except
`cli/data/sensors.json` is gitignored build output — do not commit it.

Network checks (external links and citation URLs) are deliberately **not**
in `make check`: they are slow and flaky, and CI runs them weekly on a
schedule. Run `make check-external` yourself if you have added outbound
links and want to be sure.

## What does not go in a tracked file

This repo is public, and a public file is reconnaissance whether or not it
contains a secret. Keep the following out of anything git tracks — issues
and PR descriptions included:

- hostnames and IP addresses of servers
- usernames, SSH key paths, and rsync or deploy destinations
- account numbers with any provider (DNS, registrar, hosting, CDN)
- paths to credential files, on any machine
- anything at all about *other* projects' infrastructure

Operator-only notes live in an untracked `OPERATIONS.md` at the repo root
(gitignored). If you need something from it, ask.

## Adding a sensor

1. Create `content/sensors/<slug>.md`. The filename stem becomes the URL
   slug (`/sensors/<slug>/`).
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
4. Run `make check` (above). A `family` with no matching entry in
   `FAMILIES` silently drops the sensor off the catalog and atlas (the
   detail page still generates) — check the build output counts.
5. Open the PR.

### Relative-link gotcha

Link to other entries by **bare filename**, not by URL. `fix_link_depths()`
rewrites those to site-absolute URLs at render time, so a page emits correct
links no matter what depth it is served from:

- `[type checker](type-checker.html)` for a sibling sensor → `/sensors/type-checker/`
- `[catalog](catalog.html#behavioral)` for a catalog section → `/catalog/#behavioral`
- Root-relative and absolute URLs are left alone

Targets it does not recognise are left untouched, and `check_links.py` (part
of `make check`) will flag them.

## Editing an existing sensor

Open `content/sensors/<slug>.md` directly. The frontmatter is the source of
truth for the properties table, atlas placement, and backlinks; the body is
the source for the blurb and the entry content. Run `make check` after
editing.

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

## Releasing

Two things in this repo carry version numbers, and they are **not the same
number**. Saying so out loud is the point of this section: two version
numbers in one repo is exactly the kind of thing that drifts silently.

### 1. The catalog (git tags, `vX.Y.Z`)

The tag versions *the framework and the catalog* — the taxonomy, the
dimensions, and the entries. Semantic versioning, read against the question
"does an existing property table still mean what it meant?":

| Bump | When | Examples |
|------|------|----------|
| **major** | A taxonomy change. Anything that changes what an existing rating *means*, or where an existing entry *sits*. | A dimension added, removed, or redefined; a rating scale re-anchored; a family added, merged, split, or renumbered; the confidence stack restructured; an entry removed for failing the inclusion test. |
| **minor** | New material that leaves existing meanings intact. | A new sensor entry; a new section or page; a substantive new subsection in an existing entry; new `see_also` edges. |
| **patch** | Corrections. Nothing added, nothing removed, no taxonomy touched. | Typos, prose clarifications, dead links, citation fixes, a rating corrected because it was *wrong under the current scale* (as opposed to changed because the scale moved — that is a major). |

The rule of thumb: **if a reader who cited the previous version would now be
citing something different, it is a major.** A re-rating pass across the
catalog is a major even though no dimension changed, because the numbers a
citation pointed at have moved.

Tag from `main`, annotated, and let the CHANGELOG section for that date be
the release notes:

```sh
git tag -a v1.0.0 -m "Catalog v1.0.0"
git push origin v1.0.0
gh release create v1.0.0 --title "v1.0.0" --notes-file <the CHANGELOG section>
```

### 2. The npm CLI (`cli/package.json`, currently 0.2.1)

The npm package `softwareobservatory` is **versioned separately and always
has been**. It tracks the *CLI and MCP server's own behaviour* — commands,
flags, JSON-RPC surface — not the catalog. A catalog release does not bump
it, and a CLI release does not bump the catalog.

They do touch in one place: `cli/data/sensors.json` is committed build
output, so every npm release ships a snapshot of the catalog, and CI
publishes the package on every push to `main` where the version changed.
That means the npm package can legitimately carry catalog content newer than
the newest catalog tag. That is expected, not a bug — but it is also how the
two numbers would quietly diverge into confusion, so:

- **Every npm release's CHANGELOG entry names the catalog state it embeds**
  (the last catalog tag, plus "+ N commits" if it is ahead).
- **Never** raise `cli/package.json` to match a catalog tag to make them
  "line up". They are different artifacts with different compatibility
  promises; a coincidental match is worse than an obvious mismatch, because
  it invites people to assume a relationship that does not exist.

### Release checklist

1. `make check` is green on `main`.
2. Write the CHANGELOG section for the release, including a **Decisions**
   subsection if anything was decided rather than merely done.
3. Update `CITATION.cff`: set `version:` and `date-released:` (ISO date) to
   the release being cut. Re-validate:
   `cffconvert --validate -i CITATION.cff`.
4. Commit, tag, push, and cut the GitHub release (commands above).
5. If the CLI changed, bump `cli/package.json` on its own schedule and note
   the embedded catalog state in the CHANGELOG.

### Getting a DOI (Zenodo) — one-time, about ten minutes

Zenodo mints the DOI **on the GitHub release event**, so the toggle has to
be flipped *before* the tag exists. A release cut first is not archived
retroactively; it has to be re-cut.

1. Sign in at <https://zenodo.org> with the GitHub account that owns the
   repo, and authorise the GitHub integration when prompted.
2. Go to <https://zenodo.org/account/settings/github/> and switch the
   toggle **on** for `justinabrahms/software-observatory`. (If the repo is
   not listed, use "Sync now" — Zenodo caches the repo list.)
3. **Only now** cut the release, per the checklist above. Zenodo watches for
   the release webhook and archives the tarball within a minute or two.
4. Zenodo mints **two** DOIs: a *version DOI* for that release, and a
   *concept DOI* that always resolves to the newest version. **The concept
   DOI is the one to publish** — on the site, in the README badge, and in
   `CITATION.cff`. The version DOI is for citing a specific snapshot.
5. Add the concept DOI to `CITATION.cff` as a top-level `doi:` (and the
   version DOI under `identifiers:` if you want both), then re-validate and
   commit. GitHub's "Cite this repository" button picks it up from there.
6. Check the Zenodo record's metadata — it is populated from `CITATION.cff`,
   so authors, title, licence and keywords should already be right. Fix them
   on Zenodo if not, and fix `CITATION.cff` so the next release is right at
   the source.

Every subsequent GitHub release is archived automatically; there is nothing
to repeat.

## License

By contributing, you agree your content contributions will be licensed
under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/),
the same license as the rest of the site content.
