# Security Policy

## What this project is

A static website, a Python generator that runs on the maintainer's machine
and in CI, and a zero-dependency Node CLI/MCP server published to npm as
`softwareobservatory`. There is no server-side application, no database, no
user accounts, and no data collected from visitors. That rules out most of
the vulnerability classes people go looking for.

## In scope

- Anything in the published npm package `softwareobservatory`: the CLI, and
  in particular the MCP server, which reads untrusted JSON-RPC on stdin.
- Anything that would let a pull request execute code in CI, exfiltrate the
  deploy key or the npm publish identity, or write to the deploy target.
- Anything served by <https://softwareobservatory.com> that could run in a
  visitor's browser: XSS in generated pages, or a Content-Security-Policy
  gap.
- Sensitive information disclosed by a tracked file — hostnames, IPs, account
  numbers, credential paths. This has happened before (issue #118); please
  report it privately rather than in a public issue, which would republish it.

## Out of scope

- Missing security headers with no demonstrated impact, and scanner output
  submitted without a working attack.
- Anything about the *content* of the catalog. If you think an entry is wrong
  about a security tool, that is a
  [correction](https://github.com/justinabrahms/software-observatory/issues/new?template=correction.yml),
  not a vulnerability.
- Social engineering, physical access, and denial of service against the
  static host.

## How to report

Email <justin@abrah.ms> with "security" in the subject line. Include what you
found, how to reproduce it, and what an attacker gets out of it.

Please do not open a public issue for a security report, especially not one
that discloses infrastructure details.

## What to expect

One maintainer, no on-call rotation: expect an acknowledgement within about a
week. If the report is valid, the fix and the reasoning are recorded in
`CHANGELOG.md`, and you will be credited there unless you ask not to be.
There is no bug bounty.
