#!/usr/bin/env python3
"""Require every linked preview page to be served and marked noindex."""
import json
import sys
from urllib.request import urlopen

for link in json.load(open(sys.argv[1]))['links']:
    with urlopen(link['url'], timeout=30) as response:
        body = response.read().decode()
        if response.status != 200 or 'name="robots" content="noindex, nofollow"' not in body:
            raise SystemExit(f"Preview verification failed: {link['url']}")
    print(f"Verified {link['url']}")
