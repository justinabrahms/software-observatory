---
id: SO-T02
title: Beta Signal
family: behavioral
family_num: 2
oracle: medium
oracle_note: a failure is real, a pass proves only that this case passed
independence: low
independence_note: the same person writes the code and the check
scope: function
latency: minutes
actionability: guiding
type: predictive
stack_level: behavioral-tests
categories:
- Behavioral
see_also:
- SO-T01
last_reviewed: '2026-03-02'
references:
- title: The Only Reference Beta Signal Has
  url: https://example.invalid/beta-reference
  kind: publication
  year: 2010
  tier: II
  authors: D. Fixture
---

Beta Signal is the fixture entry that carries a fenced code block and a
table, because both go through the markdown extensions (`fenced_code`,
`tables`, `smarty`) and both have their own escaping behaviour.

```python
def beta(signal: str) -> bool:
    # Angle brackets and ampersands inside a code fence: <b> & "quotes"
    return signal != "<not a tag>"
```

| Condition | Verdict | Note |
| --- | --- | --- |
| Signal present | pass | the ordinary case |
| Signal absent | fail | `&` and `<` survive here too |
| Signal ambiguous | inconclusive | an em-dash --- and "smart quotes" |

A second paragraph, so that the blurb extractor has a first paragraph to
truncate and a second one to ignore.
