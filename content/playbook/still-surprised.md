---
order: 40
kind: starting-point
title: "You have everything and still get surprised"
where: >-
  A sensor from every family, each one honestly read. The last three
  incidents were things no check you own could have failed on, and the
  postmortem action item was to add another check.
have:
  - type-checker
  - example-based-tests
  - smoke-tests
  - mutation-testing
  - branch-coverage
  - runtime-invariants
  - property-based-testing
  - fault-injection
  - canary-analysis
  - load-testing
  - hotspot-analysis
  - change-coupling
  - decision-provenance
steps:
  - sensor: observability-events
    reveals: [unspecified-property]
    why: >-
      Closes nothing, and nothing on the list above reveals unspecified
      property either. Wide events with their identifying fields kept are
      what let you ask the question you did not have until the incident.
  - sensor: incident-correlation
    reveals: [late-effects]
    why: >-
      The events show a surprise the week it happens; nothing yet shows the
      one that arrives months later. This reads the incident record the
      previous step lets you write, and turns the surprises you have already
      had into a ranking of where the next one is likely to come from.
  - sensor: independent-review
    closes: [wrong-specification, missing-behavior, correlated-blind-spot]
    why: >-
      Every sensor on the list checks the code against something the author
      wrote down. A reader who starts from the specification closes the
      three doubts that are left, and nothing mechanical closes any of them.
---

Run the list above against [what each sensor proves](/what-each-sensor-proves/)
and every doubt with a closer is closed, apart from the three a reviewer
closes. That is the point of the list. The surprises are coming from the two
doubts that have no closer at all: unspecified property and late effects.

Unspecified property is why every check you own passes on the day the bug
ships. Your invariants, your properties, your canary tolerances and your
fault experiments each check something someone wrote down, and several of
them appear on the doubts page as sensors that get misread as closing this
doubt. The misreading is the surprise. Late effects are the same gap in time:
the canary ran for an hour, the experiment for two weeks, and the damage
arrived in month three after the comparison had ended.

Look at which sensors touch these two doubts and every one of them is
retrospective. [Observability events](observability-events.html) and
[incident correlation](incident-correlation.html) reveal unspecified property;
incident correlation, [error budget impact](error-budget-impact.html),
[revert rate](revert-rate.html) and
[escaped defect rate](escaped-defect-rate.html) reveal late effects. None of
them fire before shipping. A doubt only retrospective sensors can see is a
doubt no gate will ever close, and adding another gate to this list moves
nothing.

What moves is how much of production you can still ask about after the
surprise. An event carrying `user_id`, `request_id`, `deployment` and
`git_sha` can be sliced by a question nobody had yesterday. The same event
head-sampled, or with those fields dropped to save on the bill, has already
decided which questions you get to ask. Incident correlation then turns the
answers into a ranking you can fund. Keep the dimensionality and each
surprise costs one query instead of one incident.

The remaining three doubts are human. Wrong specification and missing
behavior are invisible to every sensor that checks code against a
description the author wrote, which is all of them.
[Independent review](independent-review.html) is the sensor whose reader
starts from the specification, and it is last on this list because it is
the only closer left.
