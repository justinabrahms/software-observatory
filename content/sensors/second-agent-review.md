---
id: SO-011d
title: Second-Agent Review
family: ai-sensors
family_num: "11"
oracle: medium
independence: high
scope: module
latency: minutes
actionability: guiding
type: predictive
stack_level: static-analysis
categories:
  - AI-Generated
  - Agent Safety
see_also:
  - SO-011
  - SO-011b
  - SO-011c
  - SO-010
---

An independent agent reviews the first agent's output. A sensor that applies
*adversarial pressure* to AI-generated code without human-in-the-loop
latency.

Second-agent review is the [independent review](independent-review.html)
pattern applied to AI: a different model (or different session, different
prompt) examines the code and attempts to find problems. The independence is
structural — the second agent didn't write the code and has different
assumptions.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Medium — depends on reviewer agent capability |
| Independence | High — separate agent, separate context |
| Scope | Module-level |
| Feedback latency | Minutes |
| Actionability | Guiding — reviewer agent reports specific issues |
| Type | Predictive |

## What it cannot detect

Two agents from the same model family may share blind spots. True
independence requires different architectures, training data, or prompts.
Also, agent review quality is unproven — it may miss problems that human
review would catch.
