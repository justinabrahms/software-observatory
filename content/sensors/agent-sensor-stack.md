---
id: SO-011
title: Agent Sensor Stack
family: ai-sensors
family_num: '11'
oracle: high
independence: high
scope: system
latency: varies
actionability: guiding
type: predictive
stack_level: canary-shadow
categories:
- AI-Generated
- Agent Safety
see_also:
- SO-001
- SO-003
- SO-006
- SO-007
last_reviewed: 2026-08-23
references:
- title: 'Gender Shades: Intersectional Accuracy Disparities in Commercial Gender
    Classification'
  year: 2018
  tier: I
  url: http://proceedings.mlr.press/v81/buolamwini18a/buolamwini18a.pdf
  kind: paper
- title: 'Failing Loudly: An Empirical Study of Methods for Detecting Dataset Shift'
  year: 2019
  tier: I
  url: https://arxiv.org/pdf/1810.11953
  kind: paper
---

An agent should be surrounded by sensors. And crucially: the agent doesn't
get to declare success. The sensors declare success.

```
                 ┌──────────────┐
                 │   AGENT      │
                 │ writes code  │
                 └──────┬───────┘
                        │
          ┌─────────────┼──────────────┐
          ▼             ▼              ▼
      compiler        tests          linter
          │             │              │
          └─────────────┼──────────────┘
                        ▼
                  mutation test
                        │
                        ▼
                 integration test
                        │
                        ▼
                  canary sensor
                        │
                        ▼
                production events
                        │
                        ▼
                 outcome sensors
```

The agent sensor stack is the [confidence stack](atlas.html) applied to
AI-generated code: each layer is a gate the agent's output must pass before
it reaches production. The key principle is that the agent cannot self-certify
— [independence](framework.html) must be preserved at every layer.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — the combined stack is strong |
| Independence | High — if producer and evaluator are separated |
| Scope | System-level |
| Feedback latency | Varies by layer |
| Actionability | Guiding — each layer tells the agent what failed |
| Type | Predictive + Retrospective (varies by layer) |

## What it cannot detect

The stack is only as strong as its weakest layer. If the agent writes the
tests (low independence), the test layer provides no real signal. See
[producer-evaluator separation](producer-evaluator-separation.html).
