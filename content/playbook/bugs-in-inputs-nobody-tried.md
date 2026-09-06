---
order: 20
kind: symptom
title: "The bug was in an input nobody tried"
noticed: >-
  The failing input was a negative number, an empty list, a name with an
  accent in it. The tests used the same three tidy examples, and every one
  of them passed.
doubt: wrong-logic
sensor: property-based-testing
---

## Point this at it

[Property-based testing](property-based-testing.html), one property, on
the function that failed. Write it in Hypothesis, fast-check, QuickCheck,
or test.check, whichever your language has. The property can be modest:
the output is sorted, encoding then decoding returns the input, the
function does not throw for any list. Choose the generator so it covers
the shape that broke you, integers that go negative, lists that can be
empty, strings that are not ASCII. Run it with the default example count.

The generator is now supplying the inputs your examples left out, and it
is doing so from a description of the input space rather than from
anyone's memory of what has gone wrong before.

## Reading it

- Red: a shrunk counterexample, the smallest input the tool found that
  breaks the property. Check it by hand. Decide whether the code or the
  property is wrong; usually the code. Fix it, re-run the campaign, and
  pin the shrunk case as an ordinary example test.
- Green: no generated input broke this property in this run. That is a
  search across the input space, which three examples never were.
- It does not prove anything about properties you did not state. Watch
  the ratio of discarded examples to generated ones; if the property is
  being filtered until it passes, the green is hollow.

## If the doubt survives

If the property holds across the whole campaign and the wrong answers
keep arriving, the bug lives in something nobody has written a check
for. That is unspecified property, and no sensor closes it before
shipping. Observability events and incident correlation are how you find
out after the fact, and [the play for when you have everything and still
get surprised](/playbook/still-surprised/) is about making that
after-the-fact answer cheap.
