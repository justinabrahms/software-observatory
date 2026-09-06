---
order: 40
kind: composition
title: "A minimal stack for an internal tool with ten users"
shape: >-
  A small app one team uses. Every user is reachable by chat, and downtime
  costs minutes.
stack:
  - sensor: type-checker
    closes: [not-internally-consistent]
    why: Free with the toolchain, and it fires before anyone is bothered.
  - sensor: example-based-tests
    closes: [wrong-logic]
    why: The cases the team actually hit, pinned. Cheapest closer by far.
  - sensor: smoke-tests
    closes: [does-not-run-where-deployed]
    why: One request after deploy, so a user is not the smoke test.
left_open:
  - doubt: unasserted-execution
    reason: >-
      Ten people use every screen daily and say so in chat. Mutation
      testing is worth an afternoon once the tool touches money or
      permissions.
  - doubt: unjudged-observation
    reason: >-
      The users judge every observation. A wrong number on the screen gets
      a message within the hour.
  - doubt: unintended-change
    reason: >-
      The person who looked at that output yesterday notices it moved.
      Add snapshot tests when the users stop being people you can ask.
  - doubt: untested-conditions
    reason: >-
      There is no traffic to split a canary over. The users are the
      canary, and a bad deploy costs them minutes.
  - doubt: emergent-failure
    reason: >-
      Ten users on the real dependencies find the wiring bug within the
      hour. At this scale an integration suite costs more than the outage
      it prevents.
  - doubt: dependency-failure
    reason: >-
      When a dependency dies the tool dies, and someone posts in chat.
      Degrading gracefully matters when nobody can be told.
  - doubt: cannot-carry-load
    reason: >-
      Ten users is the load, and you know all of them.
  - doubt: late-effects
    reason: >-
      A slow drift in behavior is noticed by the same ten people, who are
      still here in month three to mention it.
  - doubt: unspecified-property
    reason: >-
      The check nobody wrote is the message a user sends. That message
      arrives within the hour, which is faster than any incident feed.
  - doubt: wrong-specification
    reason: >-
      The users wrote the spec, in chat, and they check the result against
      what they meant.
  - doubt: missing-behavior
    reason: >-
      The user who asked for the feature is the one who checks it shipped.
---

Every doubt left open here is closed by the users, and that is acceptable
while the sensor's cost stays bounded: a wrong reading reaches one of ten
named people, they tell you in chat, and the fix ships in minutes. The list
stops being acceptable when the user count grows past the people you can
name, when the tool starts touching money or permissions, or when a deploy
stops taking a minute. Each of those retires one of the reasons above;
re-read the list when it happens. [Synthetic
monitoring](synthetic-monitoring.html) closes the same doubt as the
[smoke test](smoke-tests.html), and probing a tool nobody uses at night
buys nothing here.
