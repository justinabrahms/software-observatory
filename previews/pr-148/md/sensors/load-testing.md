---
id: SO-006e
title: Load Testing
family: runtime
family_num: '06'
oracle: medium
oracle_note: a latency or error-rate break is real, but the threshold is a choice
independence: medium
independence_note: generated traffic is not real users
scope: system
latency: minutes
actionability: guiding
actionability_note: shows which endpoint and under what load it broke
type: predictive
type_note: catches failure modes before real traffic hits them
stack_level: production-behavior
categories:
- Runtime
- Performance
see_also:
- SO-006
- SO-006d
- SO-007
- runtime
references:
- title: A Survey on Load Testing of Large-Scale Software Systems
  year: 2015
  tier: II
  url: https://doi.org/10.1109/TSE.2015.2445340
  kind: publication
  authors: Zhen Ming Jiang, Ahmed E. Hassan
  venue: IEEE Transactions on Software Engineering 41(11)
- title: An Exploratory Study of the State of Practice of Performance Testing in
    Java-Based Open Source Projects
  year: 2017
  tier: II
  url: https://doi.org/10.1145/3030207.3030213
  kind: publication
  authors: Philipp Leitner, Cor-Paul Bezemer
  venue: ICPE 2017
- title: k6
  url: https://k6.io
  kind: tool
  description: Developer-centric load testing by Grafana
- title: Locust
  url: https://locust.io
  kind: tool
  description: Python-based distributed load testing
- title: Gatling
  url: https://gatling.io
  kind: tool
  description: Scala-based load testing with DSL
- title: JMeter
  url: https://jmeter.apache.org
  kind: tool
  description: Java load and performance testing
- title: Artillery
  url: https://www.artillery.io
  kind: tool
  description: Cloud-native load testing for HTTP and WebSocket
---

Does the system behave under the traffic it claims to handle? A load test
drives generated requests at a target rate and measures what breaks —
latency, errors, throughput — before real users do. The sensor most
practitioners reach for when "performance" is the question.

## In practice

A reading is a break at a concurrency level, with the endpoint and the
metric that broke:

Illustrative results from separate runs at increasing concurrency, not k6
console output. Each row summarizes one run against the same endpoint and
request mix. The limits were set before testing: p95 below 500 ms and
failed requests below 0.01%.

| Concurrent users | p95 latency | Failed requests | Requests/second | Verdict |
|------------------|-------------|-----------------|-----------------|---------|
| 200 | 210 ms | 0% | 980 | Pass |
| 300 | 840 ms | 0% | 1,220 | Fail: latency |
| 350 | 1,300 ms | 0.04% | 1,235 | Fail: latency and errors |
| 400 | 1,700 ms | 0.08% | 1,240 | Fail: latency and errors |
| 500 | 2,100 ms | 0.15% | 1,238 | Fail: latency and errors |

Three habits matter when reading these:

1. **Find the knee, not the red.** The interesting number is the
   concurrency range where latency rises sharply while throughput gains
   shrink. Here that happens between 200 and 300 users; more runs in
   that interval would locate it more closely. The table does not
   establish an exact capacity limit.
2. **Separate saturating from breaking.** Throughput plateauing means
   the system is saturated (busy, not broken); latency spiking and
   error rates rising means the system is breaking. Both are findings,
   but one is capacity and the other is a defect.
3. **Distrust the green.** A load test that stays green at the target
   load tells you the system handles *that* load, not that it handles
   *real* load. Real traffic is burstier, has a different mix, and
   arrives while the system is doing other things.

## How it gets gamed

Load tests are easy to make pass without measuring anything:

- **Test at the easy level.** Running the load test at the concurrency
  you know you handle and calling it "the load test." The sensor stays
  green because it was never asked the hard question.
- **Smooth the traffic.** Ramp-up profiles that distribute load
  evenly over minutes miss the burst that real traffic actually has.
  The average stays under the SLO while the tail blows past it.
- **Mock the dependencies.** Replacing the database or downstream
  services with stubs removes the bottleneck the test was meant to
  find. The test passes because it measures the harness, not the
  system.
- **Exclude the slow endpoints.** Configuring the test to hit only
  the cheap read paths keeps p(95) green while the write paths that
  actually do work go untested.

The meta-signal is the ratio of test traffic to production traffic. A
load test that drives less concurrency than the service already serves
in production is not testing anything.

## Response playbook

When a load test fails:

1. **Identify the bottleneck, not the symptom.** Latency spiking is a
   symptom; the bottleneck is the resource that saturated (CPU, DB
   pool, connection pool, lock contention) to cause it.
2. **Reproduce at a smaller scale.** A 500-VU failure is hard to
   debug; the same failure at 50 VUs is tractable. Bisect the
   concurrency to find where it starts.
3. **Fix the bottleneck, not the SLO.** Raising the latency threshold
   to pass the test converts a reading into a liability that surfaces
   under real load. Fix the resource or the algorithm.
4. **Pin the break level as a regression.** Record the concurrency
   where the system broke; the next run should reach it and pass, or
   the regression is real.

## What it cannot detect

A load test with synthetic traffic cannot detect failures that depend
on real traffic patterns — cache hit rates that depend on the actual
key distribution, or bugs that only trigger on the specific request
mix production sees. It also cannot detect correctness failures under
load: a system that returns wrong answers fast will pass a latency
test. For correctness under adversarial input, see [fuzzing](fuzzing.html);
for behavior under real traffic, see [shadow traffic](shadow-traffic.html)
and [canary analysis](canary-analysis.html).
