#!/usr/bin/env python3
"""Download the official screenshots cited in docs/vision/research/world-references.md.

The images are other studios' art, so they are never committed. This script reads the
source table (section 11) of the doc, downloads exactly the image URLs listed there into
refs-cache/world/ (git-ignored), and names each file by its key, e.g. eastward-13.jpg.

Usage: python3 scripts/refs/fetch_references.py [--force]
"""

import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOC = os.path.join(ROOT, 'docs', 'vision', 'research', 'world-references.md')
OUT = os.path.join(ROOT, 'refs-cache', 'world')
# Only official hosts: Steam's CDN, the studios' press kits and nintendo.com's image CDN.
HOSTS = ('https://shared.akamai.steamstatic.com/', 'https://eastwardgame.com/',
         'https://sabotagestudio.com/', 'https://www.stardewvalley.net/', 'https://assets.nintendo.com/')
ROW = re.compile(r'^\|\s*([a-z0-9-]+/\d+)\s*\|[^|]*\|\s*(https://\S+)\s*\|\s*$')


def sources():
    """Return [(key, url)] from the doc's source table."""
    rows = []
    with open(DOC, encoding='utf-8') as fh:
        for line in fh:
            m = ROW.match(line.strip())
            if m and m.group(2).startswith(HOSTS):
                rows.append((m.group(1), m.group(2)))
    return rows


def extension(url):
    path = url.split('?', 1)[0]
    ext = os.path.splitext(path)[1].lower()
    return ext if ext in ('.jpg', '.jpeg', '.png') else '.jpg'  # nintendo.com URLs carry f_jpg


def main():
    force = '--force' in sys.argv
    rows = sources()
    if not rows:
        sys.exit('No sources found in ' + DOC)
    os.makedirs(OUT, exist_ok=True)
    failed = 0
    for key, url in rows:
        dest = os.path.join(OUT, key.replace('/', '-') + extension(url))
        if os.path.exists(dest) and not force:
            continue
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (NapAttack reference fetch)'})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp, open(dest, 'wb') as fh:
                fh.write(resp.read())
            print('ok  ', key)
        except Exception as exc:  # report and carry on, so one dead link does not stop the rest
            failed += 1
            print('FAIL', key, exc)
    print(f'{len(rows) - failed} of {len(rows)} references in {os.path.relpath(OUT, ROOT)}')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
