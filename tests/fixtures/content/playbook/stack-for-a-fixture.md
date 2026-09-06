---
kind: composition
title: "A minimal stack for a fixture"
shape: >-
  Five sensors, two doubts, one of them unclosable.
stack:
  - sensor: beta-signal
    closes: [wrong-logic]
    why: The only closer.
  - sensor: epsilon-atlas
    reveals: [wrong-logic]
    why: Sees it after the fact too.
left_open:
  - doubt: late-effects
    reason: No fixture sensor closes it.
---
