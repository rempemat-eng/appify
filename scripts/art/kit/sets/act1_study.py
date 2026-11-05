"""Two review studies for the Act 1 set (scripts/art/kit/sets/act1.py), each built only from kit
pieces and checked as a zone (not playable zones):

- **Driftwood quay**: the cliff-top turf and the path down to a quay of setts; the net rack, lobster
  pots and mooring bitts along its edge; a jetty out into the harbour with the harbour light at its
  head; the shingle beach with a boat drawn up on it; buoys on the water;
- **the Halt and the Millrace**: the halt's platform (its stone surface and its edge) along the lane,
  its shelter, lamps, semaphore, timetable board and the churn stand at the lane's end; the leat from
  its sluice turning east into the race under the mill's wheel; the landslip across the lane where
  it nears the leat, the fence it broke and the miller's spare stones in his yard; hives by the lane;
  Old Fang's barrow, its trod straight out of the portal to the field path, its kerb round its foot.

    python3 -m scripts.art.kit.sets.act1_study OUT_DIR [--scale 3]   # coast and valley, baked with every still

The checks are brackens_study's: kit_rules, relations, enclosures, placement_audit.check_plan and
the staging rules (`brackens_study.layout_faults`).
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
from PIL import Image

from scripts.art.kit.schema import ROOT

CELL = 24
# The valley's bank is one low earth step (eastward-edges.md 2.1: the low ledge, ours 12 to 16), not
# the shared tier's 48 px face: the study bakes with its own copy of the earth face's height, so the
# shared tier painters stay as they are (round 3 of the detail audit, R3-11).
LOW_FACE_PX = 14
EDGE_RUN = 'acbdcadbcbdacbd'


def coast() -> dict:
    W, H = 34, 18
    g = np.full((H, W), 'q', '<U1')
    g[0:3, :] = ','                                         # the cliff-top turf
    g[0:3, 15:17] = '#'                                     # the path down to the quay
    g[9:13, 0:19] = 's'                                     # the shingle beach
    g[9:, 19:] = '~'                                        # the harbour
    g[13:, 0:19] = '~'                                      # the sea over the beach's foot
    g[9:14, 26:32] = 'q'                                    # the jetty
    pieces = [
        {'id': 'light', 'piece': 'coast_harbour_light', 'at': [29 * CELL, 14 * CELL]},
        {'id': 'bitt_1', 'piece': 'coast_mooring_bitt', 'at': [20 * CELL + 12, 9 * CELL]},
        {'id': 'bitt_2', 'piece': 'coast_mooring_bitt', 'at': [24 * CELL + 12, 9 * CELL]},
        {'id': 'bitt_3', 'piece': 'coast_mooring_bitt', 'at': [31 * CELL + 12, 12 * CELL]},   # its coil on the jetty, not over the water
        {'id': 'net', 'piece': 'coast_net_rack', 'at': [22 * CELL, 6 * CELL]},
        {'id': 'pots_1', 'piece': 'coast_lobster_pots', 'at': [27 * CELL, 8 * CELL], 'variant': 'a'},
        {'id': 'pots_2', 'piece': 'coast_lobster_pots', 'at': [31 * CELL, 9 * CELL], 'variant': 'b'},
        {'id': 'boat', 'piece': 'coast_boat_beached', 'at': [12 * CELL, 12 * CELL]},
        {'id': 'buoy_1', 'piece': 'coast_buoy', 'at': [22 * CELL + 12, 14 * CELL]},
        {'id': 'buoy_2', 'piece': 'coast_buoy', 'at': [8 * CELL + 12, 16 * CELL]},
        {'id': 'buoy_3', 'piece': 'coast_buoy', 'at': [33 * CELL + 0, 16 * CELL]},
    ]
    return {'zone': 'act1_coast_study', 'note': 'Review study (scripts/art/kit/sets/act1_study.py), not a playable zone.',
            'legend': {',': 'lawn', '#': 'path', 'q': 'quay', 's': 'shingle', '~': 'water'},
            'rows': [''.join(r) for r in g], 'pieces': pieces, 'decor': []}


def valley() -> dict:
    W, H = 44, 30
    g = np.full((H, W), ',', '<U1')
    g[5:11, 2:19] = 'q'                                     # the platform's surface, stone (the coast's quay setts), its edge to its east end
    g[13:15, 0:25] = '#'                                    # the lane, ending short of the leat
    g[11:13, 3:5] = '#'                                     # the path up onto the platform
    g[0:20, 26:29] = '~'                                    # the leat (the Millrace), from its sluice
    g[18:20, 26:44] = '~'                                   # turning east into the mill's race, out under the study's edge
    tiers = np.zeros((H, W), int)
    tiers[0:12, 20:26] = 1                                  # a low earth bank between halt and leat (one step, LOW_FACE_PX)
    g[25:30, 30:32] = '#'                                   # the yard's track to the south
    g[23:25, 30:38] = '#'                                   # the yard it ends in, worn in front of the spare millstones
    g[21:23, 30:33] = '#'                                   # the cart track from the crossing at the loading door down to the yard
    g[15:29, 2:4] = '#'                                     # the field path from the lane to the barrow
    g[28:30, 2:13] = '#'
    g[27:28, 11:13] = '#'                                   # the trod straight out of the barrow's portal
    pieces = [
        # the halt
        # four edge cells shuffled, never the same twice running, so nothing repeats under 100 px
        *[{'id': 'edge_%d' % c, 'piece': 'halt_platform_edge', 'at': [c * CELL + 12, 11 * CELL], 'variant': EDGE_RUN[c - 5]}
          for c in range(5, 19)],
        {'id': 'shelter', 'piece': 'halt_waiting_shelter', 'at': [11 * CELL, 9 * CELL]},
        {'id': 'lamp_1', 'piece': 'halt_platform_lamp', 'at': [6 * CELL + 12, 9 * CELL]},
        {'id': 'lamp_2', 'piece': 'halt_platform_lamp', 'at': [16 * CELL + 12, 9 * CELL]},
        {'id': 'signal', 'piece': 'halt_semaphore', 'at': [19 * CELL + 12, 11 * CELL]},
        {'id': 'timetable', 'piece': 'halt_timetable_board', 'at': [7 * CELL, 16 * CELL]},
        {'id': 'churns', 'piece': 'halt_churn_stand', 'at': [1 * CELL + 12, 13 * CELL]},
        # the Millrace
        {'id': 'sluice', 'piece': 'mill_sluice', 'at': [27 * CELL + 12, 4 * CELL]},
        {'id': 'wheel', 'piece': 'mill_wheel', 'at': [37 * CELL, 18 * CELL]},   # the water mill, its wall's foot on the race
        {'id': 'slip', 'piece': 'mill_landslip', 'at': [22 * CELL + 12, 14 * CELL]},   # its torn lip at the bank's rim
        {'id': 'fence', 'piece': 'mill_fence_broken', 'at': [16 * CELL, 17 * CELL]},
        {'id': 'stones', 'piece': 'mill_millstones', 'at': [35 * CELL + 12, 23 * CELL]},   # in the yard beside the track's end
        # the hives by the lane
        {'id': 'hive', 'piece': 'hive_wbc', 'at': [10 * CELL + 12, 17 * CELL]},
        {'id': 'skep', 'piece': 'hive_skep', 'at': [12 * CELL + 12, 17 * CELL]},
        # Old Fang's barrow, its trod straight out of the portal, its kerb round its foot
        {'id': 'barrow', 'piece': 'barrow_entrance', 'at': [12 * CELL, 27 * CELL]},
        {'id': 'kerb_1', 'piece': 'barrow_kerb', 'at': [4 * CELL + 12, 26 * CELL], 'variant': 'a'},
        {'id': 'kerb_2', 'piece': 'barrow_kerb', 'at': [20 * CELL + 12, 26 * CELL], 'variant': 'b'},
        {'id': 'kerb_3', 'piece': 'barrow_kerb', 'at': [19 * CELL + 12, 23 * CELL], 'variant': 'c'},
    ]
    return {'zone': 'act1_valley_study', 'note': 'Review study (scripts/art/kit/sets/act1_study.py), not a playable zone.',
            'legend': {',': 'lawn', '#': 'path', '~': 'water', 'q': 'quay'}, 'dress': {'quay': 'flags'},
            'rows': [''.join(r) for r in g], 'tiers': [''.join(str(v) for v in r) for r in tiers], 'pieces': pieces, 'decor': [],
            'race': {'row': 18, 'rows': 2, 'from': 29, 'from_s': 26.5, 'wall': (30, 44), 'bridge': (751, 70)}}   # the crossing: x and width, in front of the loading door


def _paint(img, cv):
    """Lay a code canvas (-1 empty) over an RGBA image."""
    from scripts.art.native.palette import to_rgba
    g = np.asarray(img.convert('RGBA')).copy()
    rgba = to_rgba(cv)
    m = cv >= 0
    g[m] = rgba[m]
    return Image.fromarray(g, 'RGBA')


def low_bank(img, p, seed=331):
    """The valley's bank as one low earth ledge (eastward-edges.md 2.1 and 2.2, round 4 of the detail
    audit, R4-1): the lawn on its top, and along its south rim (wobbling a texel) the low face in
    LOW_FACE_PX rows: the lip a step darker, the rim line, the under-lip dark, two rows of shade, the
    earth body with clods, a dark foot with pebbles, the lower lawn's blades grown up over it here
    and there; its west side a narrow band, lit, with a broken dark line. Where the landslip lies the
    rim is torn back into a notch (act1.SLIP_NOTCH) and its scar is raw torn earth with roots."""
    from scripts.art.kit.sets import _common as K
    from scripts.art.kit.sets import act1 as A
    from scripts.art.native.palette import C
    tiers = np.array([[int(c) for c in r] for r in p['tiers']])
    R_, C_ = tiers.shape
    h, w = R_ * CELL, C_ * CELL
    cv = np.full((h, w), -1, np.int32)
    cols = np.nonzero(tiers.any(0))[0]
    x_w, x_e = cols.min() * CELL, (cols.max() + 1) * CELL
    rim = np.full(w, -1)
    for x in range(x_w, x_e):
        c = x // CELL
        rows = np.nonzero(tiers[:, c])[0]
        y = (rows.max() + 1) * CELL - 1
        y += int(round(0.8 * np.sin(x * 0.31) + 0.6 * (K.hsh(seed, x // 5) - 0.5)))
        dxw = x - x_w
        if dxw < 12:                                                   # the south-west corner rounded
            y -= int(round(12 - np.sqrt(max(0.0, 144 - (12 - dxw) ** 2))))
        rim[x] = y
    notch = np.zeros(w, int)
    torn = np.zeros(w, bool)
    for pc in p['pieces']:
        if pc['piece'] == 'mill_landslip':
            cx = int(pc['at'][0])
            half, depth = A.SLIP_NOTCH
            for x in range(cx - half, cx + half + 1):
                d = abs(x - cx) - (half - 6)
                k = depth if d <= 0 else int(round(depth * np.sqrt(max(0.0, 1 - (d / 6.0) ** 2))))
                notch[x] = k
                torn[x] = k > 0
    F = LOW_FACE_PX
    for x in range(x_w, x_e):
        if rim[x] < 0:
            continue
        y0 = rim[x] - notch[x] + 1
        # the bank's top ends a row higher in the notch: the lawn above the scar is the bank's own
        tr = torn[x]
        seq = ([C('grass', 4), C('grass_cool', 1), C('earth', 1), C('earth_cool', 2), C('earth', 2)] if tr else
               [C('grass_cool', 2), C('earth', 3), C('earth', 1), C('earth_cool', 2), C('earth', 2)])
        cv[y0 - 1, x] = seq[0]                                          # the lip
        for j, c in enumerate(seq[1:]):
            cv[y0 + j, x] = c
        for j in range(4, F - 3):                                       # the body
            cv[y0 + j, x] = C('earth', 3) if K.hsh(seed, x // 3, j // 2) > 0.25 else C('earth_warm', 3)
        for j in range(F - 3, F):                                       # the dark foot
            cv[y0 + j, x] = C('earth_cool', 1) if j == F - 1 else C('earth', 1)
        if tr and K.hsh(seed, x, 7) > 0.7:                              # roots hanging in the raw scar
            for j in range(3, 3 + 2 + int(3 * K.hsh(seed, x, 8))):
                cv[y0 + j, x] = C('timber_warm', 3) if j % 2 else C('timber', 2)
    # clods in the body: lit top, dark under; pebbles in the foot
    for x in range(x_w + 3, x_e - 4, 1):
        if rim[x] < 0 or K.hsh(seed, x, 11) > 0.12:
            continue
        y0 = rim[x] - notch[x] + 1
        yc = y0 + 5 + int(2 * K.hsh(seed, x, 12))
        wd = 3 + int(3 * K.hsh(seed, x, 13))
        cv[yc, x:x + wd] = C('earth', 4)
        cv[yc + 1, x:x + wd] = C('earth', 3)
        cv[yc + 2, x + 1:x + wd] = C('earth_cool', 1)
    for x in range(x_w + 2, x_e - 3):
        if rim[x] < 0 or K.hsh(seed, x, 14) > 0.08:
            continue
        y0 = rim[x] - notch[x] + 1
        cv[y0 + F - 3, x:x + 2] = C('stone', 3)
        cv[y0 + F - 2, x:x + 2] = C('stone_cool', 1)
    # the lower lawn grows up over the foot here and there
    for x in range(x_w, x_e):
        if rim[x] < 0 or torn[x] or K.hsh(seed, x // 2, 15) > 0.3:
            continue
        y0 = rim[x] + 1
        for j in range(1 + int(2 * K.hsh(seed, x, 16))):
            cv[y0 + F - 1 - j, x] = C('grass_cool', 2) if j == 0 else C('grass', 3)
    # the west side: a narrow band, lit facing west, a broken dark line outside it
    for y in range(0, int(rim[x_w + 12]) if rim[x_w + 12] > 0 else 0):
        xw = x_w + int(round(0.7 * np.sin(y * 0.27)))
        cv[y, xw] = C('earth', 4)
        cv[y, xw + 1] = C('earth', 3)
        cv[y, xw + 2] = C('grass_cool', 2)
        if K.hsh(seed, y // 3, 17) > 0.25:
            cv[y, xw - 1] = C('earth_cool', 1)
    return _paint(img, cv)


def platform_ends(img, p, seed=351):
    """The platform's two ends given a side face (round 5 of the detail audit, R5-7; eastward-edges
    3.3): along each end of the raised paving, from its back to the front's foot, a band of 2 texels
    (lit facing west, in shade facing east) and outside it a dark line broken every few texels, the
    near-black of a raised side."""
    from scripts.art.kit.sets import _common as K
    from scripts.art.native.palette import C
    rows = p['rows']
    cells = np.array([[c == 'q' for c in r] for r in rows])
    R_, C_ = cells.shape
    cv = np.full((R_ * CELL, C_ * CELL), -1, np.int32)
    ys_, xs_ = np.nonzero(cells)
    y0, y1 = ys_.min() * CELL, (ys_.max() + 1) * CELL + CELL           # down to the front's foot
    xw, xe = xs_.min() * CELL, (xs_.max() + 1) * CELL
    for y in range(y0, y1):
        if y < y1 - CELL:                                              # the west end: the paving's side (the path climbs on below)
            cv[y, xw] = C('stone', 4)
            cv[y, xw + 1] = C('stone', 3)
            if K.hsh(seed, y // 3, 1) > 0.2:
                cv[y, xw - 1] = C('void', 1)
        cv[y, xe - 2] = C('stone_cool', 2)
        cv[y, xe - 1] = C('stone_cool', 1)
        if K.hsh(seed, y // 3, 2) > 0.2:
            cv[y, xe] = C('void', 1)
    return _paint(img, cv)


def race_coping(img, p, seed=341):
    """Granite coping along the mill race on both banks, out of the water (round 4 of the detail
    audit, R4-5): long slabs whose top is lit, the front a tone down dropping to a wet foot in the
    water, dark joints at uneven spacing, a squared return at its west end where the leat's earth
    bank begins; on the north bank it stops at the mill's wall. The race itself is the study's own
    water, one painter for the leat and the race, carried on out under the study's edge."""
    from scripts.art.kit.sets import _common as K
    from scripts.art.native.palette import C
    rc = p['race']
    R_, C_ = len(p['rows']), len(p['rows'][0])
    h, w = R_ * CELL, C_ * CELL
    cv = np.full((h, w), -1, np.int32)
    yn, ys = rc['row'] * CELL, (rc['row'] + rc['rows']) * CELL
    wall0, wall1 = rc['wall'][0] * CELL + 8, rc['wall'][1] * CELL - 8
    for side, yedge in (('n', yn), ('s', ys)):
        # the south bank's coping runs on round the bend to meet the leat's earth bank (R5-5)
        x0 = int((rc.get('from_s', rc['from']) if side == 's' else rc['from']) * CELL)
        x = x0
        while x < w:
            ln = 18 + int(14 * K.hsh(seed, x, side == 'n'))
            for xx in range(x, min(w, x + ln)):
                if side == 'n' and wall0 <= xx < wall1:
                    continue
                alt = K.hsh(seed, x, 3) > 0.5                              # each slab its own sibling
                f4, f3, f1 = ('stone_warm', 'stone', 'stone_cool') if alt else ('stone', 'stone_warm', 'earth_cool')
                if side == 's':                                          # top on the bank, front into the water
                    rows = [(yedge - 3, C(f4, 4)), (yedge - 2, C(f3, 4)), (yedge - 1, C(f3, 3)), (yedge, C(f4, 3)),
                            (yedge + 1, C(f3, 2)), (yedge + 2, C(f1, 1))]
                else:
                    rows = [(yedge - 4, C(f4, 4)), (yedge - 3, C(f3, 4)), (yedge - 2, C(f3, 3)), (yedge - 1, C(f3, 2)),
                            (yedge, C(f1, 2)), (yedge + 1, C(f1, 1))]
                for yy, c in rows:
                    if 0 <= yy < h:
                        cv[yy, xx] = c
            j = min(w - 1, x + ln - 1)
            for yy in range((yedge - 4) if side == 'n' else (yedge - 3), (yedge + 2) if side == 'n' else (yedge + 3)):
                if 0 <= yy < h and cv[yy, j] >= 0:
                    cv[yy, j] = C('void', 2)                            # the joint
            x += ln
        # the squared return at the west end, where the earth bank begins
        for yy in range((yedge - 4) if side == 'n' else (yedge - 3), (yedge + 2) if side == 'n' else (yedge + 3)):
            if 0 <= yy < h:
                cv[yy, x0] = C('stone_warm', 4)
                cv[yy, x0 - 1] = C('stone_cool', 1)
    # a crossing of long slabs over the race in front of the mill's loading door, for the carts
    if rc.get('bridge'):
        bx0, bx1 = rc['bridge'][0], rc['bridge'][0] + rc['bridge'][1]
        for yy in range(yn - 4, ys + 3):
            for xx in range(bx0, bx1):
                k = (xx - bx0) // 10
                if yy == ys + 2:
                    c = C('stone_cool', 1)                              # its south face's foot
                elif yy >= ys:
                    c = C('stone', 2)                                   # its south face
                elif (xx - bx0) % 10 == 9:
                    c = C('stone_cool', 2)                              # the joint between slabs
                else:
                    c = C('stone_warm' if k % 2 else 'stone', 4 if yy < yn else 3)
                cv[yy, xx] = c
            cv[yy, bx0] = C('stone_warm', 4) if yy < ys else cv[yy, bx0]
            cv[yy, bx1 - 1] = C('stone_cool', 1)
    return _paint(img, cv)


def plans() -> list:
    return [coast(), valley()]


def faults(p) -> list:
    """Every rule check's faults on a plan, as messages."""
    from scripts.art.kit import enclosures as EN
    from scripts.art.kit import placement_audit as PA
    from scripts.art.kit import relations as RL
    from scripts.art.kit.sets import brackens_study as BS
    from scripts.review import kit_rules as KR
    out = ['kit_rules: ' + f['message'] for f in KR.check_zone(p) if f['severity'] == 'fault']
    out += ['relations: ' + f['message'] for f in RL.check_zone(p)]
    out += ['enclosures: ' + f['message'] for f in EN.check_zone(p, EN.library())]
    out += ['layout: ' + m for m in BS.layout_faults(p)]
    out += ['placement: ' + f['message'] for f in PA.check_plan(p)]
    return out


def render(p) -> Image.Image:
    """The bake of the plan's ground and every piece's still by foot (a loop shows frame 0, the
    reduced-motion picture)."""
    from scripts.art.kit import bake as BK
    from scripts.art.kit import compose as CO
    from scripts.art.kit.sets import coast as CS
    lib = None
    tiers = p.get('tiers')
    # the valley's bank is one low earth step drawn by the study (low_bank, eastward-edges.md 2.2), so
    # the bake runs without the tier and the shared tier painters stay as they are (R3-11, R4-1)
    q = dict(p, tiers=None) if tiers else p
    ground, _ = BK.bake(q, lib)
    img = ground.convert('RGBA')
    if any('q' in r or 's' in r for r in p['rows']) and 'quay' in p['legend'].values():
        plain, _ = BK.bake(dict(q, pieces=[]), lib)
        img = CS.dress(q, ground, plain).convert('RGBA')
    if tiers:
        img = low_bank(img, p)
    if p.get('race'):
        img = race_coping(img, p)
    idx = CO.piece_index()
    for pc in sorted(p['pieces'], key=lambda q: (q['at'][1], q['at'][0])):
        e = idx[pc['piece']]
        v = e['variants'].get(pc.get('variant')) or next(iter(e['variants'].values()))
        sp = Image.open(os.path.join(ROOT, 'game', v['png'][len('res://'):])).convert('RGBA')
        img.alpha_composite(sp, (int(pc['at'][0] - v['foot'][0]), int(pc['at'][1] - v['foot'][1])))
    if 'q' in ''.join(p['rows']) and (p.get('dress') or {}).get('quay') == 'flags':
        img = platform_ends(img, p)                                    # over the edge run, so its ends are closed too
    return img


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--scale', type=int, default=1)
    ap.add_argument('--tag', default='')
    a = ap.parse_args(argv)
    for p in plans():
        img = render(p)
        if a.scale > 1:
            img = img.resize((img.width * a.scale, img.height * a.scale), Image.NEAREST)
        path = os.path.join(a.out, '%s_%dx%s.png' % (p['zone'].replace('_study', ''), a.scale, a.tag))
        img.save(path)
        print('wrote', path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
