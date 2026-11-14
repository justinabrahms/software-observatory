#!/usr/bin/env python3
"""Wait for the exact published revision and verify its same-origin page links."""
import argparse
import json
import time
from urllib.parse import urlsplit
from urllib.request import urlopen


def verify(data, fetch=urlopen):
    home = data['links'][0]['url']
    origin = urlsplit(home).netloc

    def read(url):
        with fetch(url, timeout=15) as response:
            final = urlsplit(response.url)
            if response.status != 200 or final.scheme != 'https' or final.netloc != origin:
                raise ValueError(f'Preview redirected outside its isolated origin: {url}')
            return response.read().decode()

    if data.get('sha'):
        revision_url = home + 'preview-revision.json?sha=' + data['sha']
        if json.loads(read(revision_url)).get('sha') != data['sha']:
            raise ValueError('Pages is still serving an older preview revision')
    for link in data['links']:
        body = read(link['url'])
        if 'name="robots" content="noindex, nofollow"' not in body:
            raise ValueError(f"Preview is missing noindex: {link['url']}")
        anchor = urlsplit(link['url']).fragment
        if anchor and f'id="{anchor}"' not in body:
            raise ValueError(f"Preview is missing the linked section: {link['url']}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest')
    parser.add_argument('--wait', type=int, default=0)
    args = parser.parse_args()
    with open(args.manifest) as file:
        data = json.load(file)
    deadline = time.monotonic() + args.wait
    while True:
        try:
            verify(data)
            break
        except (OSError, ValueError) as error:
            if time.monotonic() >= deadline:
                raise SystemExit(f'Preview verification failed: {error}')
            print(f'Waiting for Pages: {error}', flush=True)
            time.sleep(5)
    print(f"Verified revision {data.get('sha', '(unspecified)')} and all preview links")
