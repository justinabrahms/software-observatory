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
last_reviewed: '2026-08-24'
references:
- title: Exploring Statistical Change Point Detection Techniques for Performance Anomaly Detection at Mozilla
  year: 2026
  tier: I
  url: https://arxiv.org/abs/2606.18377
  kind: paper
  authors: Mohamed Bilel Besbes, Gregory Mierzwinski, Suhaib Mujahid, Philipp Leitner, Alexander Serebrenik, Dave Hunt, Diego Elias Costa
  venue: arXiv preprint
- title: 'FBDetect: Catching Tiny Performance Regressions at Hyperscale through In-Production Monitoring'
  year: 2024
  tier: III
  url: https://tangchq74.github.io/FBDetect-SOSP24.pdf
  kind: paper
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

A typical reading is a flame graph for one service covering the window
since the last deploy, diffed against the window before it. Width is
time; the story is what got wider.

```
$ pprof -top -base cpu.before.pb.gz cpu.after.pb.gz
Showing nodes accounting for 6.20s, 84% of 7.38s total
      flat  flat%   sum%        cum   cum%
     2.10s 28.45%  28.45%      2.10s  28.45%  encoding/json.Decode
     1.30s 17.62%  46.07%      3.40s  46.07%  api/serialize.renderPayload
```

| Frame | Share before | Share after | Reading |
|-------|--------------|-------------|---------|
| encoding/json.Decode | 9% | 28% | tripled; new payload shape |
| api/serialize.renderPayload | 16% | 17% | flat, not the regression |
| runtime.mallocgc | 6% | 12% | allocations follow the JSON |

Reading it well:

- **Diff, don't stare.** A wide frame may have been wide for months. The
  regression is the delta, so anchor every reading to a baseline window.
- **Charge the caller, not the leaf.** `Decode` is the leaf, but the fix
  usually lives in whichever handler started feeding it larger payloads.
- **Match profile type to symptom.** CPU profiles explain latency,
  allocation profiles explain memory, lock profiles explain stalls.
- **Overlay deploy markers.** A plateau that starts exactly at a deploy
  boundary is a suspect before you read a single frame.

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

1. **Diff against a baseline window.** Take the same profile type for the
   window before the regression and diff; confirm the regression is a
   delta, not a long-standing wide frame.
2. **Bisect by time to the deploy.** Overlay deploy markers on the
   profile timeline. If the plateau starts at a deploy, the regression is
   in that change set and [canary analysis](canary-analysis.html) or a
   revert decision is next.
3. **Charge the cost to a request.** Join the hot frames to
   [distributed traces](distributed-traces.html) or
   [observability events](observability-events.html) to find which
   endpoints and payloads feed the hotspot before touching code.
4. **Fix the biggest frame first.** A 30% frame yields more than four 7%
   frames for the same effort; resist scattering small optimizations
   across the graph.

## What it cannot detect

Profiling shows resource consumption, not [correctness](runtime-invariants.html).
A function that consumes 40% of CPU may be doing the wrong thing efficiently.
