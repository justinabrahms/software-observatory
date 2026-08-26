# Expected writing style

What the sensor pages are supposed to sound like, derived from review
feedback on the pages themselves. This is a living file: every round of
`/crit` on a sensor page that produces a general lesson gets appended
here, with the page it came from cited so the evidence is traceable.

It is not a style guide invented in advance. Every rule below was paid
for by a specific correction.

## The reader

**Assume a working engineer, not a specialist in the sensor's field.**
Jargon from the sensor's home discipline — statistics, formal methods,
compilers — is the writer's problem, not the reader's. Explain the
terms the page asks the reader to act on.

**Do not condescend by omission.** Explaining a concept for a
non-specialist does not license simplifying it into something false.
Where the honest version and the working version of an idea differ,
give both: the strict meaning, then how it is actually read day to day.
A reader who *does* know the field should not catch the page cheating.

> *ab-testing:* "Rewrite this page for people who are not familiar with
> statistics (but for those who are, don't skirt reality)."

**If a term isn't worth explaining, it isn't worth using.** The choice
is explain it or cut it — not use it undefined and hope.

> *ab-testing:* "non-inferiority isn't a term I know. Don't say it or
> explain it." (Cut, both occurrences, replaced with plain phrasing.)

## Claims have to survive being checked

**Rhetorical arithmetic gets caught.** A sentence that sounds decisive
because it puts two numbers side by side is worse than no sentence when
the numbers aren't comparable.

> *ab-testing:* "A 3% conversion lift with a 15% latency regression is
> a loss, not a win." → "the lift vs latency = loss makes no sense."
> Percentages of two unrelated quantities share nothing but a percent
> sign. Rewritten so the guardrail point stands on its own — guardrails
> are pass/fail limits agreed in advance — using the example block's own
> numbers.

**Worked examples get read as specifications.** Someone will check the
example against a system they actually run. An example that is merely
illustrative — a formula that holds only in a stripped-down case — is a
wrong claim, not a simplification.

> *business-invariants:* `order.total == sum(line_items)` → "pedantic,
> but is this total or subtotal?" It only holds for an order with no
> tax, no shipping and no discounts, on a page arguing that domain
> promises should be machine-checked.

**When a reviewer's nitpick is the page's own subject, promote it.** The
correction is worth more as a stated habit than as a silent fix.

**Prefer the page's own example over an invented one.** If there is a
sample reading on the page, argue from those numbers. It keeps the
claim checkable and stops made-up figures from carrying the argument.

## Each sensor answers exactly one question

**Know the question this sensor asks, and do not let it drift into a
neighbouring sensor's question.** Related sensors sound similar and are
easy to blur; the whole value of a catalog is that the entries are
distinct.

> *api-compatibility:* "Contract tests asks 'Did we break our
> consumers?' and API compatibility just says 'Did we make backwards
> incompatible changes?' It's possible to make a backwards incompatible
> change that no one depended on."

**State the boundary explicitly when two sensors are adjacent.** Naming
the neighbour and the difference in one line is worth more than a
`see_also` link.

**What the sensor cannot see is usually its strength, stated
backwards.** A limit is not an apology. API compatibility not knowing
who its consumers are is exactly why it costs seconds and holds as a
merge gate. Write limits that way where it is true.

**A sensor being silent where it was never asked is not gaming.** The
"How it gets gamed" section is for people routing around the sensor on
purpose, not for the sensor's honest scope. Correct scope described as
failure is a category error.

## References are part of the claim

**Every reference has to be about this sensor.** Not the general area,
not an adjacent technology with overlapping vocabulary — the thing the
page describes. A plausible-looking reference list is worse than a
short one, because it looks checked.

> *boundary-sensors:* the page was about static import rules, down to an
> example written in import-linter's contract syntax; all four
> references were runtime network tooling (Istio, Linkerd, Cilium,
> eBPF). "these tools aren't what's described below."

**Metadata and references have to agree.** A mismatch between the
frontmatter and the reference list is a signal that one of them was
never checked.

> *boundary-sensors:* "this says imports, but the references point at
> networking boundaries. That sounds wrong?"

**Reference the tool the example is written in.** If the page shows a
sample reading, the tool that produces that output belongs in the list.

**Don't reuse a neighbouring page's reference set.** Overlap suggests
the pages aren't as distinct as the catalog claims they are.

**Source the concept, not just the tooling.** A page that opens by
claiming to be a sensor of some property should cite where that
property comes from.

**Verify URLs and citation metadata before committing them.** DOIs
against Crossref, tool URLs against a real request.

## "What it cannot detect" is load-bearing

**The blind spots readers actually get hurt by are the ones that look
covered.** A limitation nobody would assume away is worth less than one
the page's own advice appears to handle and doesn't. When adding a
blind spot, check whether some earlier habit or playbook item looks
like it catches this case, and say why it doesn't.

> *build-provenance-sbom:* vendored code — "If it's just copy pasted or
> 'unzip the dependency into the source tree'.. the system is never
> going to find it." The page already told the reader to treat "not in
> the SBOM" as a finding, which sounds like the answer and isn't:
> that needs something in the artifact to disagree with the manifest,
> and vendored source disagrees with nothing.

**Explain why the sensor is blind, not just that it is.** "An SBOM
lists what the build *resolved*" is the sentence that makes the
limitation predictable — a reader who has it can work out the next
blind spot without being told.

**Scope the claim to this sensor.** Say what *this* sensor cannot see,
not what is undetectable in principle. If another tool can catch it,
say so and name what it costs, rather than overstating for effect.

## Prose

**No AI throat-clearing.** Constructions that announce structure
instead of carrying content get flagged on sight.

> *api-compatibility:* "So the reading has two halves and neither can be
> skipped." → "That wording is AI/bad. fix."

Symptoms to avoid: "has two halves and neither can be skipped," "it's
important to note," "there are three things to consider here,"
X-not-Y antithesis used as filler rather than for a real contrast.

**Say the thing, then stop.** The pages are short and declarative. A
sentence that only sets up the next sentence should be deleted and its
job given to the next sentence.

## Consequences of an edit

**A reframe is not done when the flagged paragraph is fixed.** Changing
what a page claims invalidates other claims elsewhere on it. After any
substantive change, re-read the whole page for sentences that now
contradict it — playbooks, gaming bullets, and the meta-signal line are
where the stale claims hide.

> *api-compatibility:* after the reframe, the playbook still credited
> the diff tool with catching default-value changes, and the
> meta-signal still measured consumer telemetry the page no longer
> claimed to use. Both had to go.
