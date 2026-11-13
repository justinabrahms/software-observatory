#!/usr/bin/env python3
"""Exercise preview path isolation and the privileged artifact boundary."""
import json
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from preview import stage, unpack


class PreviewTests(unittest.TestCase):
    def test_publisher_has_no_production_credentials_or_arbitrary_base_url(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / '.github/workflows/preview-publish.yml').read_text()
        self.assertNotIn('secrets.', workflow)
        self.assertNotIn('PREVIEW_BASE_URL', workflow)
        self.assertIn('actions/deploy-pages@', workflow)

    def test_staging_keeps_navigation_search_and_assets_in_preview(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'js').mkdir()
            (root / 'js/main.js').write_text("fetch('/search-index.json'); const link = `<a href=\"/sensors/${slug}/\">`;")
            (root / 'index.html').write_text('''<head><script data-goatcounter="https://stats.invalid/count" src="https://stats.invalid/count.js"></script></head><a href="/catalog/#runtime">Catalog</a><img src="//external.invalid/a.png">''')
            (root / 'search-index.json').write_text(json.dumps([{'url': '/sensors/example/'}]))
            (root / 'private.txt').write_text('must not ship')
            output = root / 'output'
            with patch('subprocess.check_output', return_value='index.html js search-index.json'):
                stage(root, output, 42, 'example')
            html = (output / 'index.html').read_text()
            self.assertIn('href="/example/previews/pr-42/catalog/#runtime"', html)
            self.assertIn('src="//external.invalid/a.png"', html)
            self.assertIn('noindex, nofollow', html)
            self.assertNotIn('data-goatcounter', html)
            self.assertFalse((output / 'private.txt').exists())
            self.assertIn("fetch('/example/previews/pr-42/search-index.json')", (output / 'js/main.js').read_text())
            self.assertIn('/example/previews/pr-42/sensors/${slug}/', (output / 'js/main.js').read_text())
            self.assertEqual(json.loads((output / 'search-index.json').read_text())[0]['url'], '/example/previews/pr-42/sensors/example/')

    def test_archive_rejects_traversal_symlinks_and_nonstatic_files_before_writing(self):
        for name in ['../escape.html', '/escape.html', 'js\\escape.js', '.ssh/key.txt', 'run.py', 'CNAME', 'link.html']:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with zipfile.ZipFile(root / 'artifact.zip', 'w') as bundle:
                    bundle.writestr('index.html', '<title>Preview</title>')
                    info = zipfile.ZipInfo(name)
                    if name == 'link.html':
                        info.external_attr = (stat.S_IFLNK | 0o777) << 16
                    bundle.writestr(info, 'untrusted')
                with self.assertRaises(ValueError):
                    unpack(root / 'artifact.zip', root / 'output')
                self.assertFalse((root / 'output').exists())

    def test_valid_static_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with zipfile.ZipFile(root / 'artifact.zip', 'w') as bundle:
                bundle.writestr('index.html', '<title>Preview</title>')
                bundle.writestr('js/main.js', '/* static */')
            unpack(root / 'artifact.zip', root / 'output')
            self.assertTrue((root / 'output/js/main.js').exists())


if __name__ == '__main__':
    unittest.main()
