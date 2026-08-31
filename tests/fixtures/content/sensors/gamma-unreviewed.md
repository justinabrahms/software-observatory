---
id: SO-T03
title: Gamma Unreviewed
family: behavioral
family_num: 2
oracle: low
independence: medium
scope: service
latency: hours
actionability: exploratory
type: retrospective
stack_level: integration-tests
---

Gamma Unreviewed deliberately carries no `last_reviewed` date, no
`see_also`, no `categories`, no `references`, and none of the optional
`*_note` fields. It is the honest-provenance path: an entry nobody has
re-read since it was written must render its review as "pending" rather
than borrowing a date from somewhere convenient. The entry itself is
complete either way — the label describes the review, not the content.

It is also the minimum-frontmatter case, so every optional-field branch in
the sensor page renderer is exercised in its absent form by at least one
fixture.
