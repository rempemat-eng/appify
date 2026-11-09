"""The placement gate: only reviewed art reaches a zone.

Matt, 25 Oct 19:19: review art "after the props or background is first drawn ... before it
gets placed and left in the world"; and 8 Nov 00:05, asked "should only reviewed art be
placeable?": "6. yes". Every picture a zone scene places from game/zones/<zone>/art/ needs a
catalogue entry, art/catalogue/<zone>/<name>.json, written by
`npm run review:asset -- <zone>/<name> --record`, whose sha256 matches the file, and then:

  - reviewer verdict "pass" (set by an independent detail-auditor, docs/review-agents.md):
    placeable. The detectors' `status` does not decide: a reviewer may reject a detector
    finding as a false positive, and the record keeps the detectors' fail as evidence;
  - in art/catalogue/fix-queue.json, the queue of art already placed in the world when the gate
    was seeded on 25 Oct (never a new asset): placeable while it is redrawn and re-recorded and
    climbs out of the queue, and only while its entry holds (Claude A, 9 Nov): the entry's sha256
    is the picture's (a queued picture that changes is refused until it is reviewed), the entry
    names when it was queued, why, what clears it and the date it must be reviewed by (past that
    date it is refused), and an asset an auditor failed carries the auditor's fix list. A queued
    asset whose record now passes is reported: remove its entry;
  - reviewer verdict "pending", "fail" or anything else, or no reviewer block: refused;
  - no entry, or a stale sha: refused.

    python3 -m scripts.review.gate --check            # every zone in game/data/zones.json (npm run check:kit)
    python3 -m scripts.review.gate --zone crossroads  # one zone

The zone generators (game/tools/gen_village.py, gen_zone.py) call `refusals()` before they
write a scene and stop when anything is refused.
"""
from __future__ import annotations

import argparse
import datetime
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
# what every queue entry states (Claude A, 9 Nov): its picture's bytes, when and why it was queued,
# what clears it and the date it must be reviewed by
REQUIRED = ('id', 'sha256', 'queued', 'reason', 'clears_when', 'review_by')
TODAY = None            # the date expiry is judged on; None is today (tests set it)


def record_path(zone: str, name: str) -> str:
    return os.path.join(CATALOGUE, zone, name.replace('/', '__') + '.json')


def queue_entries() -> dict:
    """{asset id: its queue entry}."""
    if not os.path.exists(QUEUE):
        return {}
    return {e.get('id'): e for e in json.load(open(QUEUE)).get('queue', [])}


def queue() -> set:
    return set(queue_entries())


def _today() -> datetime.date:
    return TODAY or datetime.date.today()


def queue_fault(entry: dict, sha: str, verdict) -> str | None:
    """Why a queue entry does not let its asset be placed, or None when it holds."""
    missing = [k for k in REQUIRED if not entry.get(k)]
    if missing:
        return f'its fix-queue entry lacks {", ".join(missing)} (art/catalogue/fix-queue.json, docs/review-agents.md)'
    if entry['sha256'] != sha:
        return ('changed since it was queued (the fix-queue entry holds other bytes): re-record it '
                '(npm run review:asset -- <id> --record) and have it reviewed; a queue entry never covers a new picture')
    try:
        due = datetime.date.fromisoformat(str(entry['review_by']))
    except ValueError:
        return f'its fix-queue entry\'s review_by {entry["review_by"]!r} is not a date (YYYY-MM-DD)'
    if _today() > due:
        return f'its fix-queue entry expired on {due.isoformat()} (review_by): redraw it and have it reviewed, or remove it from the zone'
    if verdict == 'fail' and not entry.get('fix_list'):
        return 'failed independent review and its fix-queue entry carries no fix_list (the auditor\'s fixes)'
    return None


def advisories() -> list[str]:
    """Queued assets whose record now passes: their entries should go."""
    out = []
    for rid, e in sorted(queue_entries().items()):
        if not rid or '/' not in rid:
            continue
        zone, name = rid.split('/', 1)
        rp = record_path(zone, name)
        if os.path.exists(rp) and ((json.load(open(rp)).get('reviewer') or {}).get('verdict') == 'pass'):
            out.append(f'{rid}: its record passes independent review: remove it from art/catalogue/fix-queue.json')
    return out


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
    q = queue_entries()
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
        reviewer = rec.get('reviewer') or {}
        verdict = reviewer.get('verdict')
        if verdict == 'pass':
            continue
        if rid in q:
            fault = queue_fault(q[rid], sha, verdict)
            if fault is None:
                continue
            bad.append(f'{rid}: {fault.replace("<id>", rid)}')
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
    for adv in advisories():
        print('ADVISORY:', adv)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
