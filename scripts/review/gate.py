"""The placement gate: only reviewed art reaches a zone.

Matt, 25 Oct 19:19: review art "after the props or background is first drawn ... before it
gets placed and left in the world"; and 8 Nov 00:05, asked "should only reviewed art be
placeable?": "6. yes". Every picture a zone scene places from game/zones/<zone>/art/ needs a
catalogue entry, art/catalogue/<zone>/<name>.json, written by
`npm run review:asset -- <zone>/<name> --record`, whose sha256 matches the file, and then:

  - reviewer verdict "pass" (set by an independent detail-auditor, docs/review-agents.md):
    placeable. The detectors' `status` does not decide: a reviewer may reject a detector
    finding as a false positive, and the record keeps the detectors' fail as evidence;
  - in art/catalogue/fix-queue.json, the queue seeded on 25 Oct from the art already in the
    world: placeable while it is redrawn and re-recorded and climbs out of the queue;
  - reviewer verdict "pending", "fail" or anything else, or no reviewer block: refused;
  - no entry, or a stale sha: refused.

    python3 -m scripts.review.gate --check            # every zone in game/data/zones.json (npm run check:kit)
    python3 -m scripts.review.gate --zone crossroads  # one zone

The zone generators (game/tools/gen_village.py, gen_zone.py) call `refusals()` before they
write a scene and stop when anything is refused.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
GAME = os.path.join(REPO, 'game')
CATALOGUE = os.path.join(REPO, 'art', 'catalogue')
QUEUE = os.path.join(CATALOGUE, 'fix-queue.json')
TEX = re.compile(r'path="res://zones/([^/"]+)/art/([^"]+)\.png"')


def record_path(zone: str, name: str) -> str:
    return os.path.join(CATALOGUE, zone, name.replace('/', '__') + '.json')


def queue() -> set:
    if not os.path.exists(QUEUE):
        return set()
    return {e['id'] for e in json.load(open(QUEUE)).get('queue', [])}


HOW = ('have a detail-auditor that did not draw it run its checklist and set the record\'s reviewer '
       'verdict (docs/review-agents.md, "The required step")')


def why_not(rid: str, verdict, rec: dict, reviewer: dict) -> str:
    """Why a recorded, current asset that is not in the fix queue may not be placed."""
    found = sorted({f['detector'] for f in rec.get('findings', []) if f.get('severity') != 'polish'})
    leads = f'; detector leads: {", ".join(found)}' if found else ''
    if verdict is None:
        return f'no reviewer verdict in its record{leads}: {HOW}'
    if verdict == 'pending':
        return f'not independently reviewed (reviewer verdict pending){leads}: {HOW}'
    if verdict == 'fail':
        who = reviewer.get('agent') or 'the reviewer'
        return (f'failed independent review ({who}: fail{leads}): fix it, re-record it '
                f'(npm run review:asset -- {rid} --record) and have it reviewed again')
    return f'reviewer verdict {verdict!r} is not "pass"{leads}: {HOW}'


def refusals(zone: str, names: list[str] | None = None, text: str | None = None) -> list[str]:
    """Why each placed asset may not be placed (empty when all may). `names` are art names
    (without .png) under game/zones/<zone>/art; `text` a scene's text to read them from."""
    if names is None:
        if text is None:
            zones = json.load(open(os.path.join(GAME, 'data', 'zones.json')))
            path = os.path.join(GAME, zones[zone].replace('res://', ''))
            text = open(path).read()
            base = path.replace('.tscn', '_base.tscn').replace(f'{zone}_base_base', f'{zone}_base')
            if os.path.exists(os.path.join(os.path.dirname(path), f'{zone}_base.tscn')):
                text += open(os.path.join(os.path.dirname(path), f'{zone}_base.tscn')).read()
        names = sorted({n for z, n in TEX.findall(text) if z == zone})
    q = queue()
    bad = []
    for n in names:
        png = os.path.join(GAME, 'zones', zone, 'art', n + '.png')
        if not os.path.exists(png):
            continue
        rid = f'{zone}/{n}'
        rp = record_path(zone, n)
        if not os.path.exists(rp):
            bad.append(f'{rid}: no review record (npm run review:asset -- {rid} --record, then have it reviewed)')
            continue
        rec = json.load(open(rp))
        sha = hashlib.sha256(open(png, 'rb').read()).hexdigest()
        if rec.get('sha256') != sha:
            bad.append(f'{rid}: changed since its record (npm run review:asset -- {rid} --record, '
                       'which resets its reviewer verdict to pending; then have it reviewed again)')
            continue
        if rid in q:
            continue
        reviewer = rec.get('reviewer') or {}
        verdict = reviewer.get('verdict')
        if verdict == 'pass':
            continue
        bad.append(f'{rid}: {why_not(rid, verdict, rec, reviewer)}')
    return bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--zone')
    a = ap.parse_args(argv)
    zones = json.load(open(os.path.join(GAME, 'data', 'zones.json')))
    ids = [a.zone] if a.zone else list(zones)
    bad = []
    for z in ids:
        bad += refusals(z)
    q = queue()
    print(f'[review gate] {len(ids)} zones, fix queue {len(q)} assets: '
          f'{"ok" if not bad else str(len(bad)) + " refused"}')
    for b in bad:
        print('REFUSED:', b)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
