#!/usr/bin/env python3
"""Build a trusted Pages landing page over persisted PR snapshots."""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
numbers = sorted(int(p.name[3:]) for p in (root / 'previews').glob('pr-*')
                 if p.is_dir() and re.fullmatch(r'pr-[1-9][0-9]*', p.name))
links = '\n'.join(f'<li><a href="previews/pr-{n}/">PR #{n}</a></li>' for n in numbers)
(root / 'index.html').write_text(f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="robots" content="noindex, nofollow">
<title>Software Observatory PR previews</title></head>
<body><h1>Software Observatory PR previews</h1>
<p>Unreviewed changes. This site is separate from production.</p><ul>{links}</ul></body></html>
''')
(root / 'robots.txt').write_text('User-agent: *\nDisallow: /\n')
(root / '.nojekyll').touch()
if (root / 'CNAME').exists():
    raise SystemExit('Preview snapshots must never contain a CNAME')
