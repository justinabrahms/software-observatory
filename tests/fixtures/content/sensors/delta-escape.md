---
id: SO-T04
title: 'Delta & </script><img src=x onerror=alert(1)>'
family: invariants
family_num: 4
oracle: maximum
oracle_note: 'a violated invariant is a defect, full stop <no ambiguity>'
independence: high
provisional: 'this rating is a placeholder while the dimension settles'
scope: system
latency: milliseconds
actionability: blocking
type: predictive
stack_level: static-analysis
categories:
- Invariants
- 'Escaping & Encoding'
see_also:
- invariants
- SO-T05
last_reviewed: '2026-02-20'
references:
- title: 'A Reference Whose Title Contains </script> & <b>markup</b>'
  url: https://example.invalid/escaping?a=1&b=2
  kind: tool
  description: 'Description with <angle brackets> & an ampersand'
---

Delta is the escaping fixture. Its title, one reference title, one reference
URL and one reference description all contain characters that must be
entity-encoded on the way into HTML: `<`, `>`, `&`, and a literal
`</script>` sequence that would otherwise close the surrounding element on
any page that emits the title inside a script block.

The title reaches the page title, the visible heading, the meta and
og:description machinery, the JSON-LD blocks, the search index, the RSS
feed and the llms.txt digests. Every one of those is a separate encoder,
which is exactly why one fixture entry is pointed at all of them.
