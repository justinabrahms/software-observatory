---
id: SO-006c
title: Continuous Profiling
family: runtime
family_num: '06'
oracle: medium
oracle_note: shows where resources go, not whether it's correct
independence: high
independence_note: production samples
scope: system
latency: seconds
actionability: exploratory
actionability_note: you profile to find bottlenecks
type: retrospective
stack_level: production-behavior
categories:
- Runtime
- Production Sensors
see_also:
- SO-006
- SO-006b
- SO-006d
last_reviewed: '2026-09-03'
references:
- title: Exploring Statistical Change Point Detection Techniques for Performance Anomaly Detection at Mozilla
  year: 2026
  tier: I
  url: https://arxiv.org/abs/2606.18377
  kind: publication
  authors: Mohamed Bilel Besbes, Gregory Mierzwinski, Suhaib Mujahid, Philipp Leitner, Alexander Serebrenik, Dave Hunt, Diego Elias Costa
  venue: arXiv preprint
- title: 'FBDetect: Catching Tiny Performance Regressions at Hyperscale through In-Production Monitoring'
  year: 2024
  tier: III
  url: https://tangchq74.github.io/FBDetect-SOSP24.pdf
  kind: publication
  authors: Dong Young Yoon, Yang Wang, Miao Yu, Elvis Huang, Juan Ignacio Jones, Abhinay Kukkadapu, Osman Kocas, Jonathan Wiepert, Kapil Goenka, Sherry Chen, Yanjun Lin, Zhihui Huang, Jocelyn Kong, Michael Chow, Chunqiang Tang
  venue: SOSP '24
- title: Pyroscope
  kind: tool
  url: https://pyroscope.io
  description: Continuous profiling platform
- title: pprof
  kind: tool
  url: https://github.com/google/pprof
  description: Go profiling tool
- title: Parca
  kind: tool
  url: https://www.parca.dev
  description: Continuous profiling for Kubernetes
- title: Datadog Profiler
  kind: tool
  url: https://docs.datadoghq.com/profiler
  description: Always-on profiling in Datadog
---

Where did computation actually go? Not "CPU is 82%" but "this function
consumed 40% of the time in these specific requests." A sensor of *resource
reality*.

Continuous profiling samples production execution to show where CPU, memory,
allocations, and lock contention actually occur — not in synthetic
benchmarks, but in real traffic.

## In practice

A reading is a flame graph for one service over the window since the
last deploy, next to the same graph for the window before it. Each row
sits inside the frame above it, and a frame's width is its share of all
samples collected — its own work plus everything it called. A frame is
therefore never wider than its parent, and a frame's own work is the
width it does not pass down to a child.

```
$ pprof -http=:8080 cpu.before.pb.gz cpu.after.pb.gz

before  (7.02s of samples)
  ██████████                        31.0%  api/serialize.renderPayload
  █████                             15.0%  encoding/json.Decode
  ██                                 6.0%  runtime.mallocgc

after   (7.38s of samples)
  ███████████████████               58.1%  api/serialize.renderPayload
  █████████████                     40.5%  encoding/json.Decode
  ████                              12.1%  runtime.mallocgc
```

Subtracting each row from the one above it separates a frame's own work
from its subtree's — the same split `pprof -top` prints as `flat` and
`cum`:

| Frame | Before (own / subtree) | After (own / subtree) | Reading |
|-------|------------------------|-----------------------|---------|
| encoding/json.Decode | 9.0% / 15.0% | 28.5% / 40.5% | tripled; the payload shape changed |
| api/serialize.renderPayload | 16.0% / 31.0% | 17.6% / 58.1% | its own work barely moved |
| runtime.mallocgc | 6.0% / 6.0% | 12.1% / 12.1% | allocation follows the JSON it sits under |

Reading it well:

- **Anchor to a baseline.** `renderPayload` holds 58.1% of samples after
  the deploy, which looks like the regression until the earlier graph
  shows it already held 31.0%. Without the second profile there is
  nothing to subtract and no way to tell a new cost from an old one.
- **The widest leaf is rarely where the fix goes.** `Decode` tripled
  while `renderPayload`'s own work went 16.0% → 17.6%: the caller is not
  doing more, it is handing down more. Walk up from the hot leaf until
  you reach a frame whose behaviour actually changed.
- **Pick the profile type from the symptom.** CPU profiles explain
  latency, allocation profiles explain memory growth, and lock profiles
  explain stalls that appear in neither. A service that is slow but not
  busy looks unremarkable in the graph above.
- **Overlay deploy markers before reading frames.** A plateau that
  begins at a deploy boundary narrows the suspects to one change set,
  which is a smaller search than any frame-by-frame reading.

## How it gets gamed

Production profiles are hard to fake, but easy to lose:

- **Agent off, problem gone.** Profiling agents are the first casualty of a
  resource dispute: "the profiler costs 5% CPU, disable it." Once the
  agent is off, every regression it would have shown simply does not
  exist. Track agent coverage per service like an uptime number.
- **Benchmarks instead of production.** A passing benchmark proves the
  benchmark's workload is fine, not production's. Swapping synthetic
  numbers in for production profiles is gaming by substitution.
- **Optimizing the frame, not the workload.** Once people know which
  frames get scrutinized, effort concentrates on making those frames
  narrow while the real cost moves into serialization, allocation, or
  lock waits that nobody is diffing.

The meta-signal is profiling coverage: the share of services whose agent
is actually running. If it falls, the sensor is quietly going dark.

## Response playbook

When a profile shows a regression or a resource spike:

1. **Decide revert-or-fix before optimizing.** If the plateau begins at
   a deploy boundary, reverting that change set and re-profiling is
   cheaper than understanding it, and [canary
   analysis](canary-analysis.html) makes the same call on a smaller
   blast radius. Optimizing a regression you could have reverted is the
   expensive path.
2. **Charge the cost to a request.** Join the hot frames to
   [distributed traces](distributed-traces.html) or
   [observability events](observability-events.html) to find which
   endpoints and payloads feed the hotspot. `Decode` at 28.5% does not
   say which caller to fix; the trace says which route grew.
3. **Change one frame, then re-profile.** Optimizations interact —
   removing an allocation can move cost into lock contention rather than
   deleting it. Without a profile between each change you cannot
   attribute the improvement to any of them.
4. **Prefer one wide frame to several narrow ones.** Not because the
   arithmetic favours it — four 7% frames are 28%, near enough the same
   — but because every fix costs the same review, deploy and re-profile
   cycle whatever its size. The wide frame buys that percentage once
   instead of four times.

## What it cannot detect

Profiling shows resource consumption, not [correctness](runtime-invariants.html).
A function that consumes 40% of CPU may be doing the wrong thing efficiently.
