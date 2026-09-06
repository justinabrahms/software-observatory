---
order: 90
kind: symptom
title: "The same three files keep causing incidents"
noticed: >-
  Every postmortem this quarter names one of the same handful of files.
  Nobody has checked whether that is chance, and nobody has looked at the
  rest of the repository for the next one.
doubt: risk-concentrated
sensor: hotspot-analysis
---

## Point this at it

[Hotspot analysis](hotspot-analysis.html) over the last twelve months.
The cheap version is the git log: count commits per file, take the top
twenty, and put a complexity number next to each one, cyclomatic
complexity from whichever linter you already run that reports it.
git-quick-stats gives you the churn column; CodeScene does the whole
table as a product. Add the author count per file while you are there.

Then lay the incident list alongside it. The three files you know about
should be near the top. The ones you are looking for are the hot,
complex files that have not caused an incident yet.

## Reading it

- Red: a module that is hot, complex, and in the incident reports. Rank
  is a question that says look here first. Nine authors in one file is a
  coordination problem on its own, and a module that was cold six months
  ago and is hot now marks a change in how the team works.
- Green: the incidents do not concentrate, and the hot files have a
  clean record because the product churns there. The three files were
  coincidence.
- It does not prove why a module changes so often or whether it is
  correct. It says where to look, and nothing about what to fix.

## If the doubt survives

Once you know where the risk sits, the remaining question is why changes
keep landing there. Run the log for the module and ask what each change
was for; repeated changes for the same reason describe the abstraction
that is missing. If the churn crosses files that have no structural
dependency on each other, the doubt underneath is that nobody knows
where the coupling is, and [change coupling](change-coupling.html) is
the reading for that.
