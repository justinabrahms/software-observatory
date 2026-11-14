#!/usr/bin/env python3
"""Stage the deploy allow-list under a PR prefix, or safely unpack a CI artifact."""
import argparse
import re
import shutil
import stat
import subprocess
import zipfile
from pathlib import Path, PurePosixPath

TEXT = {'.html', '.css', '.js', '.json', '.xml', '.txt', '.md', '.svg'}
STATIC = TEXT | {'.png', '.jpg', '.jpeg', '.webp', '.ico', '.woff', '.woff2'}


def unpack(archive, output):
    with zipfile.ZipFile(archive) as bundle:
        entries = bundle.infolist()
        if sum(item.file_size for item in entries) > 100_000_000:
            raise ValueError('Preview exceeds 100 MB')
        # Validate the whole archive before writing any files.
        for item in entries:
            path = PurePosixPath(item.filename)
            mode = item.external_attr >> 16
            if (path.is_absolute() or '..' in path.parts or
                    '\\' in item.filename or stat.S_ISLNK(mode) or
                    any(part.startswith('.') for part in path.parts) or
                    (not item.is_dir() and path.suffix not in STATIC and
                     path.name not in {'LICENSE', 'LICENSE-CODE', 'LICENSE-CONTENT'})):
                raise ValueError(f'Unsafe preview member: {item.filename}')
        if not any(item.filename == 'index.html' for item in entries):
            raise ValueError('Preview has no index.html')
        bundle.extractall(output)


def stage(root, output, number, project):
    from observatory.config import SITE_URL

    if not project or not re.fullmatch(r'[A-Za-z0-9_.-]+', project) or project in {'.', '..'}:
        raise ValueError('Invalid Pages project name')
    prefix = f'/{project}/previews/pr-{number}'
    public = subprocess.check_output(
        ['make', '-s', 'print-deploy-public'], cwd=root, text=True).split()
    for name in public:
        source = root / name
        if source.is_dir():
            shutil.copytree(source, output / name, dirs_exist_ok=True)
        elif source.is_file():
            output.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, output / name)
    # Rewrite literal root URLs in HTML, JSON search results, CSS, and JS
    # (including dynamically constructed sensor links). External // URLs stay put.
    for path in output.rglob('*'):
        if path.is_file() and path.suffix in TEXT:
            body = path.read_text()
            body = re.sub(r'''(?<=["'`(])/(?!/)''', prefix + '/', body)
            body = body.replace(SITE_URL + '/', prefix + '/')
            if path.suffix == '.html':
                body = re.sub(r'<script\b[^>]*data-goatcounter[^>]*>.*?</script>', '', body, flags=re.S)
                body = body.replace('<head>', '<head>\n  <meta name="robots" content="noindex, nofollow">', 1)
                body = body.replace('<body>', f'<body>\n  <div class="container" role="note"><p>PR #{number} preview. This is a proposed change.</p></div>', 1)
            path.write_text(body)
    (output / 'robots.txt').write_text('User-agent: *\nDisallow: /\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--number', type=int)
    parser.add_argument('--project', help='GitHub repository name (Pages project prefix)')
    parser.add_argument('--archive', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('--output must be a new directory')
    if args.archive:
        unpack(args.archive, args.output)
    elif args.number and args.number > 0 and args.project:
        stage(Path(__file__).resolve().parents[1], args.output, args.number, args.project)
    else:
        parser.error('supply --archive or a positive --number with --project')
