# Changelog

All notable changes to the Software Observatory catalog are documented here.
Dates are when the change was reviewed/published, not when the content was
originally written.

## 2026-08-24

### Decisions (from multi-model critical review)

Five models (deepseek-v4-pro-0813, gemma-4-26b, glm-5-2, kimi,
ox-alpha-free) reviewed the site on 2026-08-24. Their feedback was compared
and triaged; the following rulings settle the open questions. Each is filed
as a GitHub issue (#70–#98) for the actionable breakdown. Rationale is
recorded here so a future contributor can understand *why* a decision was
made, not just *what* was decided.

#### Oracle scale (#76)

- **Drop the /10 numbers** from the framework page prose. The 10/10, 9/10,
  8/10, 4/10, 2/10 figures are single-rater gut calls presented as cardinal
  measurements. Replace with the 5-word ordinal enum (maximum/high/medium/
  low/minimum). Keep `ORACLE_Y` and `ORACLE_WIDTHS` numeric mappings for the
  scatter plot and bars (visual placement only, not rendered as numbers —
  the scatter needs coordinates to look nice).
- **Keep the definition as "oracle strength = how strong the truth-signal."**
  Do not redefine as "trustworthiness" or split into reliability/target. The
  scalar stays one field; prose carries the nuance. (The redefinition was
  considered and rejected — it would make coverage `high` because the
  reading "this line executed" is a fact, losing the "coverage tells you
  the code ran, not that it's correct" distinction that the scalar currently
  carries.)
- **Delete the "6/10 hides the independence dimension" callout** — the
  number it apologizes for is going, so the apology goes too.
- Rationale: four of five reviewing models flagged false precision as the
  central tension ("execution is cardinal where the thesis is ordinal"). The
  ordinal scale is what the data actually is.

#### Taxonomy (#70, #71, #72, #73, #74, #75)

- **Single-family ownership is the rule.** A sensor has one `family`. Drop
  "mutation testing" from Adversarial's `examples` list (owned by Test
  Effectiveness). Audit all `FAMILIES` examples for sensors claimed but not
  owned.
- **Move Contract & Refinement Types to structural.** It's `family:
  behavioral` but `stack_level: static-analysis` — pre-runtime static
  checking. The atlas currently shows a Build-column dot in the Behavioral
  row, which reads incoherently. Structural owns the static-analysis stack
  levels.
- **Keep the "Change" family as-is.** It's a grab bag (api-compat, feature
  flags, canary, shadow, error-budget, incremental-build) but the unifying
  axis ("something changed") is defensible.
- **Comprehension family needs atlas representation.** Its `stack_levels`
  is empty, so the whole family is absent from the atlas with no disclosure.
  Distribute its sensors across existing stack levels rather than adding a
  new level (proposed mapping in #75; flagged for review during
  implementation).
- **A/B testing is a sensor, not a new family.** Lives under Change, placed
  in the Outcome column (later in the timeline than feature flags). The
  user-outcome layer is *not* empty (six retrospective sensors already
  populate it) — A/B testing fills the controlled-experiment gap.
- **New sensors**: generic static analysis (structural), property-based
  testing (adversarial — it's adversarial against the implementation like
  fuzzing/metamorphic), load testing (runtime). Fold UI/E2E testing into
  `integration-tests.md` with a note rather than a new entry.
- Rationale: the catalog presents families as a partition; the atlas graph
  is the honest structure (a covering), but the catalog should not
  contradict itself by claiming sensors it doesn't own.

#### Evidence tiers (#78, #81)

- **Replace the I/II/III/IV rubric with inline English labels.** Render
  "controlled study," "observational study," "case study," "argument" on
  each reference. Drop the `/framework/#evidence-tiers` rubric section. Keep
  `tier:` in frontmatter for the CLI/search index but stop surfacing the
  rubric as a "dimension." Renumber the framework page to describe six
  dimensions, with evidence labeling as a separate rubric note.
- Rationale: tiers are unnecessarily opaque. Saying what you mean is more
  on-ethos than encoding it in roman numerals. (Ruling: option (c) — keep
  the data, retire the opaque labels.)

#### Independence (#79)

- **Keep the scalar; add a catalog filter** (filed as a feature request).
  Independence is ~85% predictable from `stack_level` (low for author-written
  build-time, high for runtime/adversarial). The deviations (mutation =
  medium, second-agent = low) are the interesting cases. Surface them by
  adding an independence filter to the catalog page — the most AI-relevant
  dimension is currently the least wired into navigation.
- **Hedge `second-agent-review` in prose.** Keep `independence: low` (the
  claim is defensible — same-model-family agents share training data) but
  add an inline annotation: "provisional; the field has not settled
  model-correlation effects." The scalar is the thing that gets quoted out
  of context; the hedge goes where the reader sees it.

#### Build-time gates — fail loudly (#84, #85, #86)

- **Fail the build on unresolved `see_also` tokens.** `resolve_see_also`
  silently drops unresolvable references (e.g. the `ai-sensors` fossil in
  `observability-events.md`). Fix the known fossil, then add a build-time
  check that exits non-zero on any unresolved token.
- **Fail the build on unknown `family` / `stack_level` slugs.** A typo
  silently drops a sensor off the catalog and atlas. Add a build-time check.
- **Delete the `--watch` docstring.** The flag is documented but `sys.argv`
  is never parsed. A documented CLI flag that does nothing is a small lie;
  deleting the docstring is cheaper than implementing file-watching for a
  feature with one user.
- Rationale: the site's thesis is that sensors should fail loudly, not
  silently. The build should do the same.

#### Scatter plot (#77, #83)

- **Relabel the x-axis to "feedback latency."** Drop the "effort" framing —
  effort (cost) and latency (time) are only loosely correlated, and fusing
  them reintroduces a total order the framework disavows.
- **Fix `hours-seconds`: rename to `seconds-hours`, fix the coordinate.**
  The key `hours-seconds`=50 sits between `minutes`=42 and `minutes-hours`=56,
  but the label reads "seconds to hours" which should sort after minutes.
  Rename to `seconds-hours` (consistent with `minutes-hours`) and place it
  between `hours` and `days` in `LATENCY_X`.

#### References (#87)

- **Rename `kind: paper` to `kind: publication`.** Keeps the two-value rubric
  (`publication` / `tool`); the "further reading" bucket for unrecognized
  kinds stays. Books and blog posts are publications, not papers — the
  `paper` label overstates the evidence type.
- **Critically review references for `second-agent-review` and
  `escaped-defect-rate`** — both have no references block. Backfill where
  literature exists; flag as "experience report / argument" where it
  doesn't. Same standard for the ~13 sensors with zero paper references.

#### `last_reviewed` — no change

The uniform `2026-08-24` stamp is initial generation. It will spread as
entries are re-reviewed. No change to the field or the RSS sort.

#### Smaller fixes — ethos: industry resource, integrity, approachable (#92–#98)

- **Replace `onclick` catalog cards with wrapping `<a>`.** Restores
  middle-click/ctrl-click; delete the JS keyboard shim.
- **Fix `see_also: atlas` link text** to "Sensor Atlas" (matches the page
  `<h1>`).
- **Add glossary to jumplink selector and footer.** The defining page should
  be linkable.
- **Unify three blurb functions on `blurb_text`.** Catalog, search, and RSS
  should show the same blurb for the same sensor.
- **Fix `check_links.py` globs.** Drop dead `pages/` dir; add `md/`,
  `llms.txt`, `rss.xml`, `search-index.json`. Keep 403 as "unknown"
  (academic publishers block bots — failing would be noise).
- **Add favicon** (◐ as `favicon.svg`).
- **Add a strict CSP header.** Defense-in-depth.
- **Add a light theme via `prefers-color-scheme`.** Don't exclude readers in
  bright ambient light; fix the `--fam-evolution` / `--fam-change` color
  collision in the process.
- **Delete `og.png~RF1a8e977.TMP`**; gitignore `*.TMP`.
- **Investigate `cli/data/sensors.json` drift** — fix if non-deterministic.
- **Change license to CC BY-SA** (drop NC). The NC clause blocks the
  commercial-docs reuse that would spread it; the site's ambition is an
  industry resource.
- **Keep "No single sensor measures correctness" as a mantra** but
  cross-link the three occurrences so a reader who notices can verify it's
  intentional.
- **Renumber framework page**: six dimensions, evidence as rubric note
  (ties to #78/#81).
- **Fix `type` vs `actionability` conflation in framework text.**
  `build-provenance-sbom` is retrospective + blocking, breaking the
  "predictive gates; retrospective warns" binary. Rewrite to acknowledge
  the 2D space (when × what-kind-of-feedback).
- **Accept actionability 64% "guiding"** for now; re-score only if a
  specific sensor feels wrong on review.

### Filed issues

- #70 Reconcile family count (ten vs eleven) and gate it in the build
- #71 Add missing sensors: static analysis, property-based testing, load testing
- #72 Move Contract & Refinement Types to structural
- #73 Drop dual-family membership for mutation testing; enforce single ownership
- #74 Add A/B testing / controlled experiments sensor under Change
- #75 Comprehension family needs atlas representation
- #76 Drop /10 oracle numbers; keep ordinal scale; keep scatter coordinates
- #77 Relabel scatter x-axis to "feedback latency"
- #78 Replace evidence tiers (I–IV) with inline English labels
- #79 Hedge second-agent-review independence in prose
- #80 Fix type vs actionability conflation in framework text
- #81 Keep "No single sensor measures correctness" as a mantra; cross-link
- #82 Renumber framework page: six dimensions, evidence as rubric note
- #83 Fix hours-seconds latency: rename to seconds-hours, fix coordinate
- #84 Fail loudly on unresolved see_also tokens
- #85 Fail loudly on unknown family / stack_level slugs
- #86 Delete the --watch docstring
- #87 Rename kind: paper to kind: publication
- #88 Fix see_also: atlas link text / page title mismatch
- #89 Unify three blurb functions on blurb_text
- #90 Fix check_links.py globs; keep 403 as "unknown"
- #91 Investigate cli/data/sensors.json drift
- #92 Replace onclick catalog cards with wrapping <a>
- #93 Glossary: add to jumplink selector and footer
- #94 Add favicon (◐ glyph)
- #95 Add strict Content-Security-Policy header
- #96 Add light theme via prefers-color-scheme; fix family color collisions
- #97 Delete stray og.png~RF1a8e977.TMP; gitignore *.TMP
- #98 Change license to CC BY-SA (drop NC)

## 2026-08-23

### Added
- Glossary page (`pages/glossary.html`) with 16 core vocabulary entries,
  linked from the nav and from the catalog/about placeholder links.
- Categories index page (`pages/categories.html`) listing all non-family
  categories with their sensors.
- `sitemap.xml` and `robots.txt` generated at build time.
- Canonical URLs, Open Graph, Twitter Card, and meta description tags on
  all pages.
- JSON-LD structured data (`WebSite` + `Person`) on the homepage.
- `last_reviewed` field in every sensor frontmatter.
- "Reviewed" date in each sensor page's properties sidebar.
- Frontmatter validator (`scripts/check_frontmatter.py`) — validates all
  sensor frontmatter against the known constants in `build.py`.
- CI pipeline (`.github/workflows/build-check-deploy.yml`) — builds, runs
  frontmatter + link checks, and deploys on push to `main`.
- `CONTRIBUTING.md` at the repo root.
- `README.md` at the repo root.
- Author identity (Justin Abrahms) in the footer, about page, and README.

### Changed
- Homepage "recent entries" section renamed to "Recently reviewed" and
  sorted by `last_reviewed` date instead of filename order.
- About page Contributing section replaced with real content (was Lorem
  ipsum).
- Category links on sensor pages now point to `pages/categories.html#<slug>`
  instead of dead `#` anchors.

### Fixed
- 75 broken inter-sensor links found and fixed by the link checker.
- Catalog card blurbs now take the full first paragraph and decode HTML
  entities correctly.
