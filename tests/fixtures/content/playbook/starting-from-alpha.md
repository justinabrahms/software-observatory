---
kind: starting-point
title: "You have Alpha and nothing else"
where: >-
  One probe, no signal, no atlas.
have:
  - alpha-probe
steps:
  - sensor: beta-signal
    closes: [wrong-logic]
    why: >-
      Alpha closes nothing; Beta is the only closer of wrong logic.
  - sensor: gamma-unreviewed
    reveals: [late-effects]
    why: Reveals late effects after the fact, which nothing closes.
skip:
  - sensor: delta-escape
    reason: It has no doubt edge yet.
---

A short body paragraph, to prove the body renders under the steps.
