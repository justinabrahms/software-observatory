#!/usr/bin/env python3
"""
Build the last commit and the working tree side by side, and diff the output.

This replaced the committed golden snapshot (tests/golden/). The snapshot was
the right net once, for the commit that split a 3,900-line build script into
a package, and it cost a re-bless on every prose edit after that without
catching anything. What a renderer refactor actually needs is the diff
between "before" and "after" on the real catalog, on demand. This is that.

    make diff-build            # HEAD vs working tree
    make diff-build BASE=v1.0  # any git rev vs working tree

Both sides are built into throwaway directories with the same isolation the
test suite uses: OG-card generation is stubbed (the real one drives headless
Chromium and deletes cards for slugs it was not handed), the CLI dataset goes
to the scratch tree rather than cli/data/, and git history is not consulted
for first-seen dates. Nothing in the repo is written.

The base side is taken from `git archive`, so it is the committed state of
that rev: untracked files and unstaged edits are the working tree's alone.

Exit status is 0 whether or not the trees differ; this is a report, not a
gate. The full unified diff is written to a file whose path is printed.
"""

import difflib
import io
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable

# Runs inside a checkout, with cwd at its root. Kept self-contained so it
# works against a base rev that predates this script.
DRIVER = r"""
import contextlib, io, sys
from pathlib import Path
sys.path.insert(0, "scripts")
from observatory import config, dates
import build, export_cli_data, gen_og

out = Path(sys.argv[1])
scratch = out.parent
config.OUTPUT_DIR = out
config.SITE_ROOT = scratch / "no-such-repo"
dates._git_first_seen = lambda: {}
export_cli_data.OUT_PATHS = (str(scratch / "sensors.json"), str(out / "sensors.json"))
gen_og.OG_DIR = scratch / "og" / "cards"
gen_og.MANIFEST_PATH = scratch / "og" / "manifest.json"
gen_og.generate = lambda items, force=False, quiet=False: {
    "written": 0, "skipped": len(items), "removed": 0, "error": "stubbed"}

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    build.main()
"""


def build_into(checkout, out):
    out.mkdir(parents=True)
    proc = subprocess.run([PY, "-", str(out)], input=DRIVER, text=True,
                          cwd=checkout, capture_output=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit(f"build failed in {checkout}")


def read_tree(root):
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*")) if p.is_file()
    }


def export_rev(rev, dest):
    dest.mkdir(parents=True)
    archive = subprocess.run(["git", "archive", "--format=tar", rev],
                             cwd=REPO_ROOT, capture_output=True, check=True)
    with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
        tar.extractall(dest)
    # The base needs the same interpreter and dependencies; point it at ours.
    (dest / ".venv").symlink_to(REPO_ROOT / ".venv")


def main(argv):
    rev = argv[1] if len(argv) > 1 else "HEAD"
    tmp = Path(tempfile.mkdtemp(prefix="so-diff-build-"))
    base_src = tmp / "base-src"
    export_rev(rev, base_src)

    build_into(base_src, tmp / "base" / "site")
    build_into(REPO_ROOT, tmp / "head" / "site")

    before = read_tree(tmp / "base" / "site")
    after = read_tree(tmp / "head" / "site")

    missing = sorted(set(before) - set(after))
    added = sorted(set(after) - set(before))
    changed = [p for p in sorted(set(before) & set(after)) if before[p] != after[p]]

    if not (missing or added or changed):
        print(f"No generated output differs between {rev} and the working tree.")
        return 0

    patch = tmp / "build.diff"
    with patch.open("w") as fh:
        for p in changed:
            a = before[p].decode("utf-8", "replace").splitlines(keepends=True)
            b = after[p].decode("utf-8", "replace").splitlines(keepends=True)
            fh.writelines(difflib.unified_diff(a, b, f"{rev}/{p}", f"worktree/{p}"))

    for label, paths in (("removed", missing), ("added", added), ("changed", changed)):
        if paths:
            print(f"{len(paths)} {label}:")
            for p in paths[:40]:
                print(f"  {p}")
            if len(paths) > 40:
                print(f"  ... and {len(paths) - 40} more")
    print(f"\nFull diff: {patch}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
