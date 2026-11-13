---
id: SO-007e
title: A/B Testing
family: change
family_num: '07'
oracle: high
oracle_note: a statistically significant difference is a fact about users, not a guess
independence: medium
independence_note: the experiment is independent of the implementation, but the metric is chosen by the team
scope: system
scope_note: user behavior at the system level
latency: days
actionability: guiding
actionability_note: the metric and the variant tell you what to ship, not just that something changed
type: predictive
type_note: predicts which version will produce better outcomes
stack_level: user-outcome
categories:
- Change
- Controlled Experiments
see_also:
- SO-007
- SO-007b
- SO-015
- SO-009
- SO-012d
- change
last_reviewed: '2026-08-26'
references:
- title: 'Trustworthy Online Controlled Experiments: A Practical Guide to A/B Testing'
  year: 2020
  tier: II
  url: https://experimentguide.com
  kind: publication
  authors: Ron Kohavi, Diane Tang, Ya Xu
  venue: Cambridge University Press
- title: 'Seven Rules of Thumb for Web Site Experimenters'
  year: 2014
  tier: II
  url: https://doi.org/10.1145/2623330.2623341
  kind: publication
  authors: Ron Kohavi, Alex Deng, Roger Longbotham, Ya Xu
  venue: KDD 2014
- title: 'Online Controlled Experiments at Large Scale'
  year: 2013
  tier: II
  url: https://doi.org/10.1145/2487575.2488217
  kind: publication
  authors: Ron Kohavi, Alex Deng, Brian Frasca, Toby Walker, Ya Xu, Nils Pohlmann
  venue: KDD 2013
- title: 'Peeking at A/B Tests: Why It Matters, and What to Do About It'
  year: 2017
  tier: II
  url: https://doi.org/10.1145/3097983.3097992
  kind: publication
  authors: Ramesh Johari, Pete Koomen, Leonid Pekelis, David Walsh
  venue: KDD 2017
- title: GrowthBook
  url: https://www.growthbook.io
  kind: tool
  description: Open-source feature flagging and A/B testing platform
- title: Statsig
  url: https://www.statsig.com
  kind: tool
  description: Experimentation and feature flagging platform
- title: Optimizely
  url: https://www.optimizely.com
  kind: tool
  description: Experimentation platform with stats engine
- title: LaunchDarkly
  url: https://launchdarkly.com
  kind: tool
  description: Feature management with experimentation
---

Did users actually behave differently? An A/B test splits traffic between
two versions and measures whether the treatment changes a user outcome
metric — click-through, conversion, retention, latency-experienced. It is
the strongest sensor in the user-outcome layer because it is *controlled*:
the difference is attributable to the change, not to the weather.

## Controlled, not retrospective

The Outcome column is mostly retrospective. [Revert rate](revert-rate.html),
[incident correlation](incident-correlation.html), and
[escaped defect rate](escaped-defect-rate.html) observe what happened and
ask whether the change correlates with trouble. A/B testing is different:
it assigns users to variants *before* observing them, so the difference in
outcomes is caused by the change, not merely associated with it. The
retrospective sensors answer "did this change look like trouble?"; A/B
testing answers "did this change produce the outcome we intended?"

That distinction — causal, not correlational — is why A/B testing sits in
the Change family rather than Evolution. Evolution sensors watch history;
A/B testing runs an experiment.

## In practice

A reading is a measured difference on a metric you named before the
experiment started — either an improvement, or a confirmation that
nothing got worse by more than the amount you agreed to tolerate:

```
Experiment: checkout-redesign-v3
  Variant: control (N=48,210)  treatment (N=48,182)
  Metric: checkout_completion_rate
    control:   0.2341  (95% CI: 0.2298–0.2384)
    treatment: 0.2412  (95% CI: 0.2369–0.2455)
    lift: +3.0%  (95% CI: +1.2% to +4.9%)   p = 0.001
  Guardrail: p99 latency
    control: 820ms   treatment: 835ms   delta: +15ms (within +50ms guardrail)
  Decision: ship treatment
```

Reading that block doesn't take a statistics background, but it does
take knowing what three of those numbers are for.

**The interval is the answer; the point estimate is the headline.** The
lift reads `+3.0%`, but the honest result is the range next to it:
`+1.2% to +4.9%`. Strictly, a 95% interval is a claim about the
procedure — repeat the experiment many times and 95% of the intervals
you compute this way would contain the true effect. Read day to day, it
means: the real effect is probably somewhere in that range, and every
number in it is a result you should be willing to live with. This one
never touches zero, so the change plausibly did something. An interval
of `-1% to +7%` includes "made things slightly worse" and is not a win;
it is *we still don't know*.

**The p-value only answers "could this be noise?"** `p = 0.001` means:
if the change truly did nothing, a difference at least this large would
turn up about one run in a thousand by luck alone. That's all it says.
It does not say the effect is large, that it matters, or that it will
hold next quarter — a trivial effect measured on enough users produces
a tiny p-value. Which is why the interval, not the p-value, is the
number to argue about.

**N is what makes either of them trustworthy.** Few users means a wide
interval, and a wide interval can only detect enormous effects. Working
out how many users you need to see the smallest effect you'd actually
act on is called a *power analysis*, and it is the one piece of
statistics worth doing before the experiment rather than after. Skip it
and you can run an experiment that was arithmetically incapable of
finding what you were looking for.

None of this is math anyone should be doing by hand. An experimentation
platform computes the intervals, holds the stopping rule, verifies the
split was actually random, and refuses to show you the metric you
invented after the fact. That is what the tooling is *for*: it makes
the honest analysis the cheap one. Judge a platform on that — one that
reports a p-value with no interval, or lets you stop the moment the
number turns green, is a tool for making the numbers agree with you.

Three habits matter when reading a result:

1. **Read the guardrails before the headline metric.** Guardrails are
   the limits you agreed to in advance — p99 latency, error rate, crash
   rate — and they are pass/fail, not part of a trade you negotiate
   after seeing conversion. In the run above the treatment cost +15ms
   against a +50ms guardrail, so it passed. Had it cost +200ms, the
   treatment doesn't ship, however good conversion looked.
2. **Check the sample size before the significance.** A result that
   crossed the significance line on 2,000 users is a hint, not a
   decision: at that size the interval is wide enough that the
   plausible effects run from "barely anything" to "implausibly
   large." Look at how many users it took before you look at whether
   it won.
3. **Distrust the metric you didn't name in advance.** A win on a
   metric chosen after seeing the results is a fishing trip. The metric
   was chosen before the experiment started, or the number is not a
   measurement.

## How it gets gamed

A/B tests are easy to make say what you want:

- **Peek and stop.** Watching the result every day and stopping the
  moment it looks like a win. Random noise wanders, so given enough
  looks it will eventually wander across the line on its own — checking
  repeatedly and stopping at the first good number finds "effects" that
  aren't there. The fix is deciding the stopping rule before you start:
  a fixed sample size, or a method built to be checked repeatedly
  (sequential testing), which most platforms offer.
- **Metric shopping.** Running 40 metrics and reporting the one that
  moved. The fix is a single primary metric, chosen before launch.
- **Run it too small and call it "no effect."** An experiment with too
  few users that finds no significant difference is not evidence of no
  effect; it is evidence of nothing. The interval, not the p-value,
  tells you which one you're holding: an interval of -8% to +9% rules
  out almost nothing.
- **Dilute the treatment.** If 5% of users see the treatment but the
  metric is computed over all users (including the 95% who saw
  control), the lift is diluted toward zero and the experiment can't
  detect anything. Exposure bugs are the most common silent failure.

The meta-signal is the ratio of experiments that shipped to
experiments that found a significant effect. A platform where every
experiment wins is either very good at picking winners or not
actually measuring.

## Response playbook

When an A/B test concludes:

1. **Check the guardrails first.** If any guardrail breached, the
   treatment doesn't ship regardless of the headline metric.
2. **Read the confidence interval, not just the point estimate.** A
   3% lift with a CI of -1% to +7% is not a win; it's "we don't know."
3. **If the change was meant to be neutral, check it against the
   margin you set.** Many refactors are supposed to change nothing a
   user can feel. "No significant difference" is not the same claim as
   "inside the margin we agreed to" — an experiment too small to detect
   a 5% drop reports no significant difference even when there is a 5%
   drop.
4. **Record the decision and the reason.** An experiment that
   concluded and was then overridden by opinion is a sensor that was
   ignored; track it like a suppression.

## What it cannot detect

A/B testing measures the outcomes you instrumented, on the users you
exposed, over the time you ran it. It cannot detect effects that take
longer than the experiment to appear (network effects, retention over
months), effects on users who were excluded from the experiment, or
effects on metrics you didn't think to measure. For long-horizon
outcomes, see [escaped defect rate](escaped-defect-rate.html) and
[error budget impact](error-budget-impact.html); for whether the
change is safe to expose in the first place, see
[canary analysis](canary-analysis.html) and
[shadow traffic](shadow-traffic.html).
