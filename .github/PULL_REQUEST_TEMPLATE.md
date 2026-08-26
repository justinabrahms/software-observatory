<!--
Thanks for contributing. Delete whichever sections do not apply — a typo fix
does not need a rating rationale.
-->

## What this changes

<!-- One or two sentences. -->

## Why

<!--
For a correction: what was wrong, and what settles it.
For a new sensor: why it belongs in the catalog and is not an existing entry
under a different name.
For a taxonomy change: link the issue where it was agreed. Taxonomy changes
should be discussed before the work, since they re-rate existing entries and
are a major version bump.
-->

## Ratings (new or changed sensors only)

<!--
Property table as it appears in the frontmatter, plus a line on each rating
that was not obvious — especially oracle strength and independence.
Comparisons to existing entries are the most useful form of argument.
Also state what the sensor cannot detect; every entry needs one.
-->

## Checklist

- [ ] `make check` passes locally (this is the whole gate: frontmatter and
      vocabulary, citations, build, internal links, CLI smoke test, deploy
      manifest — do not substitute running the build and link checker by
      hand, which misses the frontmatter gate)
- [ ] No generated output committed (`index.html`, `catalog/`, `sensors/`,
      `search-index.json`, … are gitignored; `cli/data/sensors.json` is the
      one exception and *is* committed)
- [ ] Empirical claims carry a source in `references:`
- [ ] Any tool output shown was produced by really running the tool
- [ ] No hostnames, IPs, account numbers, credential paths, or other
      projects' infrastructure in anything tracked
