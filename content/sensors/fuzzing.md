---
id: SO-005
title: Fuzzing
family: adversarial
family_num: 5
oracle: high
oracle_note: high for crashes, lower for correctness
independence: high
independence_note: inputs are generated independently of the implementation
scope: function
scope_note: usually function level
latency: minutes-hours
actionability: guiding
actionability_note: provides the exact input that triggers the failure
type: predictive
type_note: actively tries to break the system
stack_level: property-metamorphic
categories:
- Adversarial
see_also:
- SO-005b
- SO-003
- adversarial
last_reviewed: '2026-08-24'
references:
- title: Evaluating Fuzz Testing
  year: 2018
  tier: I
  url: https://dl.acm.org/doi/10.1145/3243734.3243804
  kind: publication
  authors: George Klees, Andrew Ruef, Benji Cooper, Shiyi Wei, Michael Hicks
  venue: ACM CCS 2018
- title: An Empirical Study of OSS-Fuzz Bugs
  year: 2021
  tier: II
  url: https://arxiv.org/pdf/2103.11518
  kind: publication
  authors: Zhen Yu Ding, Claire Le Goues
  venue: MSR 2021
- authors: Manes et al.
  title: 'The Art, Science, and Engineering of Fuzzing: A Survey'
  year: 2021
  kind: publication
  tier: IV
- title: libFuzzer
  url: https://llvm.org/docs/LibFuzzer.html
  kind: tool
  description: LLVM in-process fuzzer
- title: cargo-fuzz
  kind: tool
  url: https://rust-fuzz.github.io/book/cargo-fuzz.html
  description: Fuzzing for Rust
- title: AFL++
  kind: tool
  url: https://github.com/AFLplusplus/AFLplusplus
  description: Coverage-guided fuzzer
- title: CIFuzz
  kind: tool
  url: https://github.com/AdaLogics/fuzz-introspector
  description: Continuous fuzzing integration for CI
---

What happens on inputs humans didn't think of? Fuzzing is a sensor of
*robustness* against the infinite space of inputs the system will actually
encounter — including inputs no engineer would ever write deliberately.

## The oracle question

Property-based testing asks: "does the implementation obey generalized
properties across huge input spaces?" Fuzzing asks a simpler question: "does
it crash?" The oracle is cheap — panics, exceptions, assertions, memory
violations — but the coverage of input space is enormous.

```
# Coverage-guided fuzzing
1. Generate random or mutated input
2. Feed it to the system
3. Did new code paths execute?
   Yes → keep this input, mutate further
   No  → discard, try again
4. Did the system crash, panic, or violate an assertion?
   Yes → save the input as a finding
   No  → continue
```

> Fuzzing is particularly powerful because it explores the input space that
> humans systematically under-sample. An engineer writes tests for inputs
> they can imagine. A fuzzer discovers inputs they can't.

## In practice

A reading is a crash report: the sanitizer's verdict, the stack, and
the input that triggered it:

```
==4821==ERROR: AddressSanitizer: heap-buffer-overflow
  on address 0x60200000f7f1 at pc 0x4b2f1b
READ of size 1 at 0x60200000f7f1
    #0 parse_header   parser.c:142:9
    #1 parse_message  parser.c:87:12
    #2 main           harness.c:14:5

artifact_prefix='./crashes/';
test unit written to ./crashes/crash-8f3a2c
```

Reading it well:

1. **The saved input is the reading.** The stack trace explains where
   the system died; the file in `crashes/` is the evidence, and the
   only part that reproduces the bug. Commit it before anything else.
2. **Deduplicate by stack signature.** Ten thousand crash files can
   be one bug reached ten thousand ways. Grouping by the failing
   frames turns a wall of red into a triage list.
3. **No findings is a real reading, with conditions.** A long
   campaign that finds nothing says the explored input space is
   robust, and it means more when the coverage counter was still
   climbing. An empty report from a five-minute run means almost
   nothing.

## How it gets gamed

- **Exclude the crashing input.** Adding the crash artifact to an
  ignore list turns the finding into nothing; the bug stays live and
  the report stays clean.
- **Run it too short to find.** A five-minute campaign is a
  checkbox. Empty reports from short runs are not evidence of
  robustness, and campaign length is the lever being pulled.
- **Disable the oracle.** Turning off the assertion or memory checks
  that would have caught the crash removes the sensor while keeping
  the run.
- **Mark crashes as theoretical.** "Nobody would send that input" is
  how fuzzing findings die. The input space the fuzzer explores is
  exactly the one attackers and accidents sample.

The meta-signal is the ignored-findings list. Anything on it is a
live bug the team chose to keep.

## Response playbook

When the fuzzer finds a crash:

1. **Commit the crashing input first.** The file in the crashes
   directory is the reading; everything else is commentary. It is
   also the regression test for the fix.
2. **Deduplicate by stack signature.** Ten thousand crash files are
   often one bug reached ten thousand ways. Group by the failing
   frames before triaging.
3. **Classify under the sanitizer.** Memory error, assertion, or
   panic decides severity: the first two are often exploitable or
   corrupting, the last is a logic bug with a cheap fix.
4. **Fix the root cause, not the site.** Bounds-checking one
   location while the parser is still wrong invites the fuzzer to
   find the next location.
5. **Re-run the campaign against the fix.** The fix is confirmed
   when the original input and its neighborhood stop crashing, not
   when the code review lands.

## What it cannot detect

Fuzzing with a crash oracle cannot detect *wrong but non-crashing* behavior.
A function that returns the wrong answer without crashing will pass a fuzzer.
For correctness properties, pair fuzzing with [property-based
testing](metamorphic-testing.html) or [mutation testing](mutation-testing.html).
