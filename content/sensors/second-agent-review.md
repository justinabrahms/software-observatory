---
id: SO-011d
title: Second-Agent Review
family: ai-sensors
family_num: "11"
oracle: medium
oracle_note: 'depends on reviewer agent capability'
independence: high
independence_note: 'separate agent, separate context'
scope: module
latency: minutes
actionability: guiding
actionability_note: 'reviewer agent reports specific issues'
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
last_reviewed: 2026-08-23
---

An independent agent reviews the first agent's output. A sensor that applies
*adversarial pressure* to AI-generated code without human-in-the-loop
latency.

Second-agent review is the [independent review](independent-review.html)
pattern applied to AI: a different model (or different session, different
prompt) examines the code and attempts to find problems. The independence is
structural — the second agent didn't write the code and has different
assumptions.

## In practice

A reading is the reviewer agent's structured verdict, produced from the
diff alone:

```
verdict: changes_requested
findings:
  - severity: blocking
    file: src/checkout/retry.py
    claim: backoff doubles past the 30 s cap; the cap is checked
      before the multiply. repro: six retries from a cold start.
  - severity: question
    file: migrations/0042_drop_legacy_id.sql
    claim: batch/ship.py still selects orders.legacy_id; unclear
      which change lands first.
```

The useful parts are the falsifiable claims: a file, a behavior, and a
way to check it. Findings that only say "this looks suspicious" are
noise, from an agent or a human.

Reading it well:

- **Discount agreement with the author's rationale.** The reviewer
  should never see the producer's summary before the review. If it
  did, treat the verdict as contaminated. See [producer-evaluator
  separation](producer-evaluator-separation.html).
- **Verify blocking findings mechanically.** An agent's claim about a
  cap or a race is a hypothesis until a test reproduces it. Verdicts
  are cheap to produce, so they should be cheap to check.
- **Same-family reviewers undercount correlated errors.** Two models
  from the same lineage share blind spots, so an absent finding is
  weaker evidence than a present one. Reserve [computational
  gates](computational-gates.html) for what must not slip.

## How it gets gamed

The sensor is a model, and models are configured:

- **Same-family reviewer.** Producer and reviewer come from one model
  line, share the same training blind spots, and agree on the same
  wrong answer. The review is a mirror, not a second opinion.
- **Prompt capture.** The reviewer is handed the producer's rationale
  before the diff, and reviews the explanation instead of the code.
  Verdicts then correlate with the author's confidence, not the
  change's quality.
- **Rubber-stamp prompting.** "Be concise; only flag clear bugs"
  produces reviews that flag nothing. The prompt is a dial, and it is
  pointed at green.
- **Verdict laundering.** Agents trade roles, or the same session
  reviews its own output under a second name. Structurally this is
  self-review with extra steps.

The meta-signal is the reviewer's finding rate. A reviewer that finds
nothing, ever, across hundreds of changes, is not excellent; it is
captured or misconfigured.

## Response playbook

When the reviewer agent flags the change:

1. **Verify blocking findings mechanically.** The reviewer's claim
   about a cap, a race, or a missing check is a hypothesis. Write the
   reproducing test before accepting or dismissing it; a second
   agent's confidence is not evidence.
2. **Check what the reviewer saw.** If the reviewer prompt included
   the producer's rationale, treat the verdict as contaminated and
   re-run the review from the diff alone. The independence is in the
   context, not the model.
3. **Route questions back as tasks.** A finding like "unclear which
   change lands first" is a dependency the reviewer could not verify.
   Turn it into a concrete check: run the migration against a copy of
   the schema, or search for the column's readers.
4. **Do not let agreement end the review.** A reviewer that agrees
   with the producer on everything is either excellent or captured,
   and captured is more common. Spot-check a sample of approved
   changes with a different model family.
5. **Escalate repeated finding classes to a computational gate.** If
   the same kind of finding keeps appearing across reviews, the
   review layer is doing detection work that belongs in a [type
   checker](type-checker.html), a [linter](linter.html), or a test.
   Move the check left.

## What it cannot detect

Two agents from the same model family share the same training distribution
and will tend to agree on the same wrong answers — the "independence" is
illusory if both agents have the same blind spots. True independence
requires different model families, different training data, or different
architectures. A second agent from the same model is better than nothing
but is not the same as an independent evaluator.

Also, agent review quality is unproven — it may miss problems that human
review would catch. Pair with [computational
gates](computational-gates.html) for enforcement that doesn't depend on
review quality.
