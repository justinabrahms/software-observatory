---
id: SO-001b
title: Compiler
family: structural
family_num: '01'
oracle: maximum
oracle_note: the implementation cannot argue
independence: maximum
independence_note: the compiler is external to the code
scope: module
latency: milliseconds
actionability: guiding
actionability_note: exact error location and message
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
last_reviewed: '2026-08-28'
references:
- title: 'Aho et al., ''Compilers: Principles, Techniques, and Tools'''
  kind: other
- title: GCC
  kind: tool
  url: https://gcc.gnu.org
  description: GNU Compiler Collection
- title: Clang
  kind: tool
  url: https://clang.llvm.org
  description: LLVM C/C++/ObjC compiler
- title: rustc
  kind: tool
  url: https://www.rust-lang.org
  description: The Rust compiler
- title: tsc
  kind: tool
  url: https://www.typescriptlang.org
  description: TypeScript compiler with type checking
---

Does this code compile? The cheapest and most certain sensor in the
catalog.

A compiler doesn't just check syntax — it resolves imports, validates
module structure, and produces an artifact. If the compiler fails, no
downstream sensor can run. This makes it the foundation of the [confidence
stack](atlas.html): every other sensor assumes compilation succeeded.

## In practice

A compiler reading is the most direct verdict in the catalog: pass
produces an artifact, fail produces a diagnostic pinned to a file,
line, and column. There is no score to interpret and no threshold to
set.

```
error[E0308]: mismatched types
  --> src/invoice.rs:42:12
   |
42 |     return total_with_tax;
   |            ^^^^^^^^^^^^^^ expected `u64`, found `f64`

error: could not compile `billing` (lib) due to 1 previous error
```

Two habits keep the reading honest. Fix diagnostics in the order they
appear, because one bad signature can cascade into dozens of
downstream errors, and clearing the first one is cheaper than
triaging the avalanche. And treat warnings as debts due now: an
unused result or an unreachable arm is the compiler downgrading a
verdict it could have made hard, and a codebase that ignores warnings
is training everyone to ignore errors too.

## Response playbook

When the compiler fires, the response is mechanical:

1. **Read the first error, not the last.** Later diagnostics are
   often consequences of the first failure. Fix, recompile, re-read.
2. **Trust the diagnostic over your memory of the code.** The
   compiler read the file you actually wrote, not the one you
   intended.
3. **If the message contradicts the source, rebuild clean.** Stale
   incremental state is the usual cause; clear the build cache and
   compile from scratch before suspecting the toolchain.
4. **Never silence the message to pass the build.** A cast, an
   `unsafe` block, or a suppression attribute converts a
   maximum-oracle verdict into a deferred bug.

## What it cannot detect

A compiler cannot detect [logical errors](mutation-testing.html) — a function
that compiles perfectly but returns the wrong answer. It also cannot detect
[architectural problems](catalog.html#architecture) or [runtime
behavior](observability-events.html).
