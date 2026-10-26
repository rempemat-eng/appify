"""Logic checks on the animated cast, from each character's manifest and sheets
(game/assets/characters/<id>/). Ported from the independent cast audits of 25 Oct (castwork
AUDIT.md and AUDIT-2.md, scratchpad audit scripts metrics2.py, cont3.py, light.py):

  cast.foot_slide     a planted foot moves more than 2.5 px between drawings outside walks
  cast.walk_speed     the planted foot's speed in a side walk differs from the manifest walk_speed
  cast.seam           a loop's last drawing differs from its first far more than its own steps
  cast.equipment      a carried thing drops out for one drawing, pops in for one, or jumps in size
  cast.end_pose       a clip that hands back to idle ends in a pose 25 % or more away from idle
  cast.light          a facing lit from the right (west facings must be relit, not mirrored)

    python3 -m scripts.review.cast [ids...]       # all characters by default
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image

from .core import REPO, lum

CHARS = os.path.join(REPO, 'game', 'assets', 'characters')


def frame(cid: str, fr: dict) -> np.ndarray:
    sheet = os.path.join(CHARS, cid, 'sheets', os.path.basename(fr['sheet']) if 'sheet' in fr else '')
    x, y, w, h = fr['region']
    return np.asarray(Image.open(sheet).convert('RGBA').crop((x, y, x + w, y + h)))


def check(cid: str) -> list[dict]:
    m = json.load(open(os.path.join(CHARS, cid, 'manifest.json')))
    C = m['clips']
    out = []

    def add(det, sev, clip, facing, msg, fix):
        out.append(dict(detector=det, severity=sev, character=cid, clip=clip, facing=facing, message=msg, fix=fix))

    cache = {}

    def img(fr):
        k = (fr.get('sheet'), tuple(fr['region']))
        if k not in cache:
            cache[k] = frame(cid, fr)
        return cache[k]
    for cn, c in C.items():
        base = cn.replace('powered_', '').replace('_empty', '')
        for F, fc in c['facings'].items():
            frs = fc['frames']
            if base in ('idle', 'guard', 'primary', 'secondary', 'special', 'exit', 'hit', 'reload'):
                for ft in ('foot_R', 'foot_L'):
                    xs = [fr['anchors'].get(ft, [0, 0])[0] for fr in frs]
                    ys = [fr['anchors'].get(ft, [0, 0])[1] for fr in frs]
                    for i in range(1, len(xs)):
                        if ys[i] > -2 and ys[i - 1] > -2 and abs(xs[i] - xs[i - 1]) > 2.5:
                            add('cast.foot_slide', 'polish' if abs(xs[i] - xs[i - 1]) <= 6 else 'fault', cn, F,
                                f'{ft} slides {xs[i - 1]:.1f} to {xs[i]:.1f} px on the ground at drawing {i}',
                                'lift the foot 2 to 3 px in that drawing (or add a 40 ms in-between) and plant it in the next')
            if base == 'walk' and F in 'EW':
                d = c['durations']
                sp = []
                for i in range(1, len(frs)):
                    for ft in ('foot_R', 'foot_L'):
                        a, b = frs[i - 1]['anchors'].get(ft), frs[i]['anchors'].get(ft)
                        if a and b and a[1] > -1.6 and b[1] > -1.6:
                            sp.append(abs(b[0] - a[0]) / d[i - 1])
                if sp and abs(np.median(sp) - m['walk_speed']) > 6:
                    add('cast.walk_speed', 'fault', cn, F,
                        f'the planted foot moves at {np.median(sp):.0f} px/s, the manifest walks at {m["walk_speed"]}',
                        'match walk_speed to the planted foot (or the stride to the speed) so the feet do not skate')
            al = [img(fr)[..., 3] > 0 for fr in frs]
            if c.get('loop') and len(al) > 2:
                diffs = [(al[i] ^ al[i - 1]).sum() for i in range(1, len(al))]
                seam = (al[0] ^ al[-1]).sum()
                med = np.median(diffs)
                if seam > 2.5 * max(med, 10):
                    add('cast.seam', 'polish', cn, F, f'the loop pops at its seam ({seam} px change against a median step of {med:.0f})',
                        'make the last drawing lead into the first (or add the missing in-between)')
            tags = set().union(*[fr.get('equipment', {}).keys() for fr in frs]) if frs else set()
            for t in tags:
                if any(k in t for k in ('flash', 'fx', 'spark', 'muzzle', 'trail')):
                    continue          # effects blink by design
                v = [fr.get('equipment', {}).get(t, 0) for fr in frs]
                for i in range(1, len(v) - 1):
                    if v[i - 1] >= 8 and v[i + 1] >= 8 and v[i] < 2:
                        add('cast.equipment', 'fault' if min(v[i - 1], v[i + 1]) >= 20 else 'polish', cn, F,
                            f'{t} drops out for drawing {i} ({v})',
                            'keep the item visible (4 px or more) or hide it behind the body for a run of drawings, never one')
                    if v[i - 1] < 2 and v[i + 1] < 2 and v[i] >= 8:
                        add('cast.equipment', 'fault' if v[i] >= 20 else 'polish', cn, F,
                            f'{t} pops in for drawing {i} only ({v})',
                            'draw it in the neighbouring drawings too, or not at all')
            if not c.get('loop') and base not in ('defeat', 'stair_up', 'stair_down', 'exit', 'idle', 'walk') and 'idle' in C:
                rn = 'powered_idle' if cn.startswith('powered') and cn != 'powered_exit' and 'powered_idle' in C else 'idle'
                ref = C[rn]['facings'][F]['frames'][0]
                A, B = al[-1], img(ref)[..., 3] > 0
                if B.sum() and (A ^ B).sum() > 0.25 * B.sum():
                    add('cast.end_pose', 'polish', cn, F,
                        f'ends {100 * (A ^ B).sum() / B.sum():.0f} % away from {rn}, so the cut back to {rn} pops',
                        f'make the last drawing the {rn} stance, or blend through an in-between')
        if cn == 'idle':
            for F, fc in c['facings'].items():
                im = img(fc['frames'][0]).astype(float)
                a = im[..., 3] > 0
                L = lum(im[..., :3])
                both = a[:, :-1] & a[:, 1:] & (L[:, :-1] > 60) & (L[:, 1:] > 60)
                if both.sum() > 50:
                    lr = float((L[:, :-1] - L[:, 1:])[both].mean())
                    if lr < -1.0:
                        add('cast.light', 'fault', cn, F, f'lit from the right (left minus right {lr:+.2f} L a step)',
                            'relight the facing from the upper left; a west facing is redrawn, never mirrored')
    return out


def main(argv=None):
    ids = (argv if argv is not None else sys.argv[1:]) or sorted(os.listdir(CHARS))
    total = 0
    for cid in ids:
        if not os.path.exists(os.path.join(CHARS, cid, 'manifest.json')):
            continue
        fs = check(cid)
        total += sum(1 for f in fs if f['severity'] != 'polish')
        print(f'{cid}: {len(fs)} findings ({sum(1 for f in fs if f["severity"] == "fault")} faults)')
        for f in fs:
            print(f'  {f["severity"]:6s} {f["detector"]:16s} {f["clip"]} {f["facing"]}: {f["message"]}')
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main())
