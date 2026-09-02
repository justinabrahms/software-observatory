#!/usr/bin/env python3
"""Verify the live Caddy site block still matches the one tracked in this repo.

`infra/caddy/softwareobservatory.com.caddy` is a record, not a source: nothing
here applies it, so the only thing keeping it honest is a check that can fail.
An untested config file in a repo is worse than no file, because it is read as
true long after it stopped being true.

Read-only. It runs one `ssh <host> cat` against a world-readable file and
writes nothing. The host is deliberately not tracked here — this repo's public
files carry no hostnames — so pass it in:

    CADDY_HOST=user@example make check-caddy

The `tls` stanza is skipped on both sides: the tracked copy holds it back
because it names the DNS provider and its credential env var.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

REPO_FILE = Path(__file__).resolve().parent.parent / "infra" / "caddy" / "softwareobservatory.com.caddy"
REMOTE_FILE = "/etc/caddy/Caddyfile"
BLOCK_OPEN = "softwareobservatory.com, www.softwareobservatory.com {"


def extract_block(text, source):
    """Return the site block's lines, from its opening line to the closing brace."""
    lines = text.splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == BLOCK_OPEN)
    except StopIteration:
        sys.exit(f"check-caddy: no '{BLOCK_OPEN}' block found in {source}")
    for i in range(start + 1, len(lines)):
        if lines[i].rstrip() == "}":
            return lines[start:i + 1]
    sys.exit(f"check-caddy: unterminated site block in {source}")


def normalize(lines):
    """Drop comments, blank lines and the tls stanza; collapse indentation.

    What survives is the routing and header behaviour — the part that changes,
    and the part a reviewer is actually diffing.
    """
    out = []
    depth_skip = 0
    for line in lines:
        stripped = line.strip()
        if depth_skip:
            depth_skip += stripped.count("{") - stripped.count("}")
            continue
        if not stripped or stripped.startswith("#"):
            continue
        if re.match(r"^tls\s*\{", stripped):
            depth_skip = 1
            continue
        if stripped == "tls {":
            depth_skip = 1
            continue
        out.append(re.sub(r"\s+", " ", stripped))
    return out


def main():
    host = os.environ.get("CADDY_HOST")
    if not host:
        sys.exit(
            "check-caddy: set CADDY_HOST to the deploy host, e.g.\n"
            "    CADDY_HOST=user@example make check-caddy\n"
            "The host is not tracked in this repo; it is in OPERATIONS.md."
        )

    if not REPO_FILE.exists():
        sys.exit(f"check-caddy: tracked config missing at {REPO_FILE}")
    tracked = normalize(extract_block(REPO_FILE.read_text(), str(REPO_FILE)))

    try:
        result = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host, f"cat {REMOTE_FILE}"],
            capture_output=True, text=True, timeout=60,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        sys.exit(f"check-caddy: could not reach {host}: {exc}")
    if result.returncode != 0:
        sys.exit(f"check-caddy: ssh to {host} failed ({result.returncode}): {result.stderr.strip()}")

    live = normalize(extract_block(result.stdout, f"{host}:{REMOTE_FILE}"))

    if not tracked:
        sys.exit("check-caddy: tracked block normalized to nothing — the check would pass vacuously")

    if tracked == live:
        print(f"check-caddy: live config matches infra/caddy/ ({len(tracked)} directives).")
        return 0

    print("check-caddy: DRIFT — the live site block no longer matches this repo.")
    print(f"  tracked: {REPO_FILE}")
    print(f"  live:    {host}:{REMOTE_FILE}")
    print()
    for line in sorted(set(tracked) - set(live)):
        print(f"  in repo, not on server:  {line}")
    for line in sorted(set(live) - set(tracked)):
        print(f"  on server, not in repo:  {line}")
    if set(tracked) == set(live):
        print("  (same directives, different order)")
    print()
    print("check-caddy: reconcile by hand — see infra/caddy/README.md. Nothing")
    print("check-caddy: in this repo may write server config.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
