---
id: SO-001b
title: Compiler
family: structural
family_num: '01'
oracle: maximum
independence: maximum
scope: module
latency: milliseconds
actionability: guiding
type: predictive
stack_level: compilation
categories:
- Structural
- Syntactic Validity
- Maximum Oracle
see_also:
- SO-001
- SO-001c
- SO-001d
last_reviewed: 2026-08-23
references:
- title: 'Aho et al., ''Compilers: Principles, Techniques, and Tools'''
  kind: other
- title: GCC
  kind: tool
  url: ''
  description: GNU Compiler Collection
- title: Clang
  kind: tool
  url: ''
  description: LLVM C/C++/ObjC compiler
- title: rustc
  kind: tool
  url: ''
  description: The Rust compiler
- title: tsc
  kind: tool
  url: ''
  description: TypeScript compiler with type checking
---

The cheapest and most certain sensor. Is this thing even a valid inhabitant
of the language? If not, everything else is noise.

A compiler doesn't just check syntax — it resolves imports, validates
module structure, and produces an artifact. If the compiler fails, no
downstream sensor can run. This makes it the foundation of the [confidence
stack](atlas.html): every other sensor assumes compilation succeeded.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Maximum — the implementation cannot argue |
| Independence | Maximum — the compiler is external to the code |
| Scope | Module-level |
| Feedback latency | Milliseconds |
| Actionability | Guiding — exact error location and message |
| Type | Predictive |

## What it cannot detect

A compiler cannot detect [logical errors](mutation-testing.html) — a function
that compiles perfectly but returns the wrong answer. It also cannot detect
[architectural problems](catalog.html#architecture) or [runtime
behavior](observability-events.html).
