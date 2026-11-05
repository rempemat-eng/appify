"""logic.scale: how large every placed thing is, next to a person and next to the ground.

Matt, 26 Oct 15:40: "make sure the size ratios are correct of all the objects, objects vs
humans, background/ grass flats etc. vs objects".

The table is `scripts/review/sizes.json` (docs/vision/size-guide.md, "Art px at density 3"):
for every class of thing we place, a height and width range in art px at density 3 (an adult
is 74, a metre 43.5), each checked against Eastward at the same character height, plus the
ground's grain (tuft, clump, blotch, cobble and slab sizes), path widths and the cast's heights.

What is measured, and how:

  sprite    the opaque bounding box (alpha > 128, specks under 6 px dropped) of a placed picture,
            its class read from its name (or its zone kit's kind)
  door      the opening of every door of a building whose look is in its zone plan
            (`art.looks`): the run of the leaf's own paint (or the dark of an open doorway) up
            from the ground line and across, read by exact palette family; and its latch
  stair     the step pitch of every plan stair, from the period of the light and dark bands
            down the flight
  spec      a building look's storey (ground to eaves) and roof (eaves to ridge), in art px
  grain     a ground fill's marks (pixels 10 L off a 0.4 H median): a fill whose dark marks are
            smaller than Eastward's and denser is speckled; blotch sizes; cobble and slab sizes
            in the plan's paving; ripple lengths on water
  widths    a plan route's width against path, lane and road
  cast      every character's body height (rows of its main mass at least 6 px wide, so a spear
            or a floating pebble does not count) against adult, creature or Cairn

    python3 -m scripts.review.scale --markdown       # the size table for size-guide.md
    python3 -m scripts.review.scale --audit OUT.json # every placed asset, door, stair, fill and cast member

The asset gate (assets.review_rgba) runs `check_sprite`, `check_building` and `check_grain`;
the scene gate (scene.review_zone) runs `check_zone`.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from .core import REPO, GAME_H, Finding, lum, green_mask, water_mask

SIZES = json.load(open(os.path.join(REPO, 'scripts', 'review', 'sizes.json')))
A = float(SIZES['unit']['adult_art_px'])
CLASSES = SIZES['classes']
SEV = SIZES['severity']
GAME = os.path.join(REPO, 'game')

# pictures that are not one thing standing on the ground: overlays, effects, laid-out ground,
# puzzle pieces drawn into the floor
SKIP = ('_shadow', '_damage', 'fx/', 'smoke', 'forge_fire', 'beds', 'channel', 'seal_', 'alcove', 'crater')
SKIP_NAMES = ('ground', 'flow')


# ------------------------------------------------------------------------------------------
# classes
def base_name(name: str) -> str:
    b = os.path.splitext(os.path.basename(name))[0]
    b = re.sub(r'(_\d+|_[a-d])$', '', b)
    return b


def class_of(name: str, kind: str | None = None) -> str | None:
    """The size class of a placed picture, from its name (or its kit kind): an exact name first,
    then the longest class name contained in it."""
    low = name.lower()
    b = base_name(low)
    if any(s in low for s in SKIP) or b in SKIP_NAMES:
        return None
    zone = low.split('/')[0] if '/' in low else ''
    for k, v in SIZES.get('aliases', {}).items():
        if not k.startswith('_') and k.split('/')[0] == zone and b.startswith(k.split('/')[1]):
            return v
    # the whole name, then its words from the last (the head noun: smithy_rubble is rubble,
    # kit_lantern a lantern), then the kit's kind
    toks = b.split('_')
    cands = [b] + ['_'.join(toks[i:]) for i in range(1, len(toks))] + toks[::-1] + [(kind or '').lower()]
    for cand in cands:
        if not cand:
            continue
        if cand in CLASSES and CLASSES[cand]['measure'] == 'bbox':
            return cand
        for cid, c in CLASSES.items():
            if cand in c['names']:
                return cid
    # a class name inside the name counts only where it starts a word (haystack is hay, but churn is
    # not an urn and timetable is not a table: the detail audit of 4 Nov sized the churn stand as a barrel)
    best = None
    for cid, c in CLASSES.items():
        for n in c['names']:
            if ('_' + n) in ('_' + b) and (best is None or len(n) > len(best[1])):
                best = (cid, n)
    return best[0] if best else None


def tol(bound: float) -> float:
    return max(SEV['polish_min_px'], SEV['polish_within'] * bound)


def judge(subject: str, cid: str, what: str, v: float, rng, box, unit='art px', fix_extra='') -> list[Finding]:
    """A finding when v lies outside rng: polish within the tolerance, fault beyond it."""
    lo, hi = rng
    if lo <= v <= hi:
        return []
    off = lo - v if v < lo else v - hi
    bound = lo if v < lo else hi
    sev = 'polish' if off <= tol(bound) else 'fault'
    c = CLASSES.get(cid, {})
    word = 'small' if v < lo else 'big'
    why = c.get('eastward', '')
    msg = (f'{subject}: {what} {v:.0f} {unit} ({v / A:.2f} A) is too {word} for a {cid.replace("_", " ")}: '
           f'the size table gives {lo} to {hi} ({lo / A:.2f} to {hi / A:.2f} A)')
    if why:
        msg += f'; Eastward at the same character height: {why}'
    fix = (f'redraw it {lo} to {hi} art px {what.split()[0]} (target about {round((lo + hi) / 2)}), '
           f'checked beside Bramble (74 art px) in the asset sheet{fix_extra}')
    return [Finding('logic.scale', sev, tuple(int(x) for x in box), msg, fix, score=float(v),
                    threshold=float(hi if v > hi else lo), subject=subject,
                    extra={'class': cid, 'measure': what, 'range': [lo, hi], 'value': float(v)})]


# ------------------------------------------------------------------------------------------
# sprites
def opaque_box(alpha: np.ndarray, min_px: int = 6):
    """The opaque bounding box without specks (components under min_px pixels)."""
    lab, n = ndi.label(alpha, structure=np.ones((3, 3)))
    if n == 0:
        return None
    areas = ndi.sum(alpha, lab, range(1, n + 1))
    keep = np.isin(lab, 1 + np.nonzero(areas >= min_px)[0])
    if not keep.any():
        keep = alpha
    ys, xs = np.nonzero(keep)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def measure_sprite(alpha: np.ndarray) -> dict | None:
    b = opaque_box(alpha)
    if b is None:
        return None
    return dict(box=b, w=b[2] - b[0], h=b[3] - b[1])


def check_sprite(alpha: np.ndarray, subject: str, kind: str | None = None, density: float = 3.0,
                 offset=(0, 0)) -> list[Finding]:
    """logic.scale on one placed picture: its opaque box against its class. `offset` moves the
    finding's box into a zone picture (the scene gate)."""
    cid = class_of(subject, kind)
    if not cid or CLASSES[cid]['measure'] != 'bbox':
        return []
    m = measure_sprite(alpha)
    if not m:
        return []
    k = 3.0 / density           # the table is at density 3
    c = CLASSES[cid]
    box = (m['box'][0] + offset[0], m['box'][1] + offset[1], m['box'][2] + offset[0], m['box'][3] + offset[1])
    fs = judge(subject, cid, 'tall', m['h'] * k, c['h'], box)
    if c['w'][1] > 0:
        fs += judge(subject, cid, 'wide', m['w'] * k, c['w'], box)
    return fs


# ------------------------------------------------------------------------------------------
# buildings: doors by exact palette family
_LUT = None


def palette_lut() -> dict:
    """Exact RGB -> parent family name for every colour of the house palette (the kit writes
    pictures from palette codes, so every pixel of a kit building is an exact entry)."""
    global _LUT
    if _LUT is None:
        art = os.path.join(REPO, 'scripts', 'art')
        if art not in sys.path:
            sys.path.insert(0, art)
        from scripts.art.native import palette as P
        lut = {}
        for f, r in P.RAMPS.items():
            for c in r:
                rgb = tuple(int(c.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)) if isinstance(c, str) else tuple(c[:3])
                lut.setdefault(rgb, P.parent(f))
        for f, c in P.EDGES.items():
            lut.setdefault(tuple(int(c.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)), 'edge')
        lut.setdefault(tuple(int(P.INK.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)), 'edge')
        _LUT = lut
    return _LUT


def family_names(rgba: np.ndarray) -> np.ndarray:
    lut = palette_lut()
    flat = rgba[..., :3].reshape(-1, 3)
    out = np.array([lut.get(tuple(int(v) for v in p), '?') for p in flat], dtype=object)
    out = out.reshape(rgba.shape[:2])
    out[rgba[..., 3] <= 128] = ''
    return out


def _run(seq, start, step, ok, gap=2):
    i, last, miss = start, start, 0
    while 0 <= i < len(seq):
        if ok(seq[i]):
            last, miss = i, 0
        else:
            miss += 1
            if miss > gap:
                break
        i += step
    return last


HARDWARE = {'iron', 'brass', 'edge', '?', ''}


def measure_opening(rgba: np.ndarray, cx: int, B: int, H: float = A) -> dict:
    """A door's opening: the families that fill the middle of the doorway (its paint, or the soot
    and hearth of an open mouth) followed up from the ground line and across."""
    fam = family_names(rgba)
    y0, y1 = max(0, B - int(0.62 * H)), B - int(0.36 * H)
    win = fam[y0:y1, max(0, cx - int(0.1 * H)):cx + int(0.1 * H) + 1].ravel()
    vals, cnt = np.unique([v for v in win if v not in ('', '?')], return_counts=True)
    fill = {v for v, n in zip(vals, cnt) if n >= 0.08 * len(win)}
    body = fill - HARDWARE or fill
    ok = lambda f: f in fill or f in ('edge', 'iron')
    col = list(fam[:, min(rgba.shape[1] - 1, cx + 2)])
    top = _run(col, B - int(0.5 * H), -1, ok)
    h = B - top + 1
    yrow = top + int(0.35 * h)
    row = list(fam[yrow, :])
    l, r = _run(row, cx, -1, ok), _run(row, cx, 1, ok)
    # the latch: a small brass or iron knot inside the leaf's east half
    handle = None
    if body and 'soot' not in body:
        sub = fam[top:B - 6, cx:r + 1]
        hw = np.isin(sub, ['brass'] if 'brass' not in body else ['iron'])
        lab, n = ndi.label(hw)
        best = None
        for sl in ndi.find_objects(lab) or []:
            hh, ww = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
            if max(hh, ww) <= 0.15 * H and (best is None or hh * ww > best[0]):
                best = (hh * ww, max(hh, ww), B - (top + (sl[0].start + sl[0].stop) / 2))
        if best:
            handle = dict(size=best[1], height=best[2])
    return dict(box=(l, top, r + 1, B + 1), h=h, w=r - l + 1, families=sorted(body), handle=handle)


def plan_looks(zone: str) -> dict:
    p = os.path.join(GAME, 'data', 'plans', zone + '.json')
    if not os.path.exists(p):
        return {}
    return (json.load(open(p)).get('art') or {}).get('looks') or {}


def check_building(rgba: np.ndarray, zone: str, name: str, look: dict | None = None, offset=(0, 0),
                   density: float = 3.0) -> list[Finding]:
    """The doors (opening and latch) and the look's storey and roof of one kit building."""
    look = look if look is not None else plan_looks(zone).get(base_name(name))
    if not look:
        return []
    q = lambda v: int(round(v * density))
    subject = f'{zone}/{name}'
    Hh = rgba.shape[0]
    L = 3 + q(look.get('overhang', 3))
    B = Hh - 3 - 1
    ox, oy = offset
    fs: list[Finding] = []
    doors = look.get('doors') or ([[look['door'], None]] if 'door' in look else [])
    for i, (dx, _) in enumerate(doors):
        cx = L + q(dx)
        m = measure_opening(rgba, cx, B)
        box = (m['box'][0] + ox, m['box'][1] + oy, m['box'][2] + ox, m['box'][3] + oy)
        cid = 'wide_door' if look.get('kind') == 'forge' else 'door'
        lab = f'{subject} door {i + 1}' if len(doors) > 1 else f'{subject} door'
        fs += judge(lab, cid, 'tall (opening, ground to lintel)', m['h'], CLASSES[cid]['h'], box)
        fs += judge(lab, cid, 'wide (opening)', m['w'], CLASSES[cid]['w'], box)
        if cid == 'door' and m['handle']:
            hc = CLASSES['door_handle']
            fs += judge(lab + ' latch', 'door_handle', 'across', m['handle']['size'], hc['h'], box)
            frac = m['handle']['height'] / max(1, m['h'])
            if not 0.35 <= frac <= 0.75:
                fs.append(Finding('logic.scale', 'polish', box,
                                  f'{lab}: the latch sits at {frac:.2f} of the door\'s height; a hand finds it at about 0.5 to 0.6',
                                  'move the latch to half to three fifths of the leaf\'s height', score=frac, threshold=0.6,
                                  subject=lab, extra={'class': 'door_handle', 'measure': 'height share'}))
    wall_h = look.get('wall_h', 40) * density
    fs += judge(subject + ' storey', 'storey', 'tall (ground to eaves)', wall_h, CLASSES['storey']['h'],
                (ox, oy, ox + rgba.shape[1], oy + Hh))
    roof_h = look.get('roof_h', round(look.get('depth', 40) * 0.55 + 10)) * density if 'roof_h' in look else None
    if roof_h:
        fs += judge(subject + ' roof', 'roof', 'tall (eaves to ridge)', roof_h, CLASSES['roof']['h'],
                    (ox, oy, ox + rgba.shape[1], oy + Hh))
    win = (look.get('win_h', 13) * density, look.get('win_w', 13) * density)
    if look.get('windows'):
        fs += judge(subject + ' windows', 'window', 'tall', win[0], CLASSES['window']['h'], (ox, oy, ox + rgba.shape[1], oy + Hh))
        fs += judge(subject + ' windows', 'window', 'wide', win[1], CLASSES['window']['w'], (ox, oy, ox + rgba.shape[1], oy + Hh))
    return fs


# ------------------------------------------------------------------------------------------
# stairs
def stair_pitch(rgb: np.ndarray, box, H: float = A) -> dict | None:
    """The step pitch of a flight: the period of its light and dark bands along the axis that
    repeats most strongly (autocorrelation peak between 0.1 and 0.45 H)."""
    x0, y0, x1, y1 = [int(v) for v in box]
    sub = lum(rgb[max(0, y0):y1, max(0, x0):x1])
    best = None
    for axis, prof in (('down', sub.mean(1)), ('across', sub.mean(0))):
        p = prof - ndi.uniform_filter1d(prof, max(3, int(0.6 * H)))
        n = len(p)
        if n < int(0.5 * H):
            continue
        ac = np.array([np.dot(p[:n - k], p[k:]) / max(1e-6, np.dot(p, p)) for k in range(n // 2)])
        lo, hi = int(0.1 * H), min(len(ac) - 1, int(0.45 * H))
        if hi <= lo:
            continue
        k = lo + int(np.argmax(ac[lo:hi + 1]))
        if best is None or ac[k] > best['strength']:
            dark = (p < 0).mean()
            best = dict(pitch=float(k), strength=float(ac[k]), axis=axis, riser=float(k * dark))
    return best if best and best['strength'] >= 0.25 else None


def plan_stairs(zone: str, density: float = 3.0) -> list[tuple]:
    p = os.path.join(GAME, 'data', 'plans', zone + '.json')
    if not os.path.exists(p):
        return []
    plan = json.load(open(p))
    out = []
    for s in plan.get('stairs') or []:
        x, y = s['at']
        w = s.get('width', 40)
        out.append((s.get('id', 'stair'), [(x - w / 2 + 4) * density, (y - 14) * density, (x + w / 2 - 4) * density, (y + 8) * density]))
    st = plan.get('stair')
    if isinstance(st, dict) and st.get('rect'):
        x, y, w, h = st['rect']
        out.append(('stair', [x * density, y * density, (x + w) * density, (y + h) * density]))
    return out


def check_stairs(rgb: np.ndarray, zone: str, density: float = 3.0) -> list[Finding]:
    fs = []
    for sid, box in plan_stairs(zone, density):
        m = stair_pitch(rgb, box)
        if not m:
            continue
        fs += judge(f'{zone}/{sid}', 'stair', 'step pitch', m['pitch'], CLASSES['stair']['h'], box)
    return fs


# ------------------------------------------------------------------------------------------
# ground grain
def local_median(L: np.ndarray, size: float, q: int = 3) -> np.ndarray:
    """A median over size x size px, taken on a 1/q copy (the base it gives is smooth; this is
    q^4 times quicker than the full-size filter)."""
    small = ndi.median_filter(L[::q, ::q], size=max(3, int(round(size / q)) | 1))
    return np.kron(small, np.ones((q, q)))[:L.shape[0], :L.shape[1]]


def marks(rgb: np.ndarray, H: float = A, thr: float = 10.0) -> dict:
    """The fill's marks (pixels at least thr L off a 0.4 H median): count per H square and the
    median size (larger side, in H) for light and dark marks; blotches (a 0.06 H blur at least
    5 L off a 1.2 H median, at least 0.1 H across)."""
    L = lum(rgb)
    base = local_median(L, 0.4 * H)
    dev = L - base
    out = {}
    area_H = L.size / (H * H)
    for sign, name in ((1, 'light'), (-1, 'dark')):
        m = (sign * dev) >= thr
        lab, n = ndi.label(m, structure=np.ones((3, 3)))
        if n == 0:
            out[name] = dict(density=0.0, size=0.0)
            continue
        sl = ndi.find_objects(lab)
        sz = np.array([max(a.stop - a.start, b.stop - b.start) for a, b in sl])
        area = ndi.sum(m, lab, range(1, n + 1))
        sz = sz[area >= 2]
        out[name] = dict(density=float(len(sz) / area_H), size=float(np.median(sz) / H) if len(sz) else 0.0)
    g = ndi.gaussian_filter(L, 0.06 * H)
    # the 1.2 H median on a quarter-size copy (the blur leaves nothing finer to lose)
    q = 4
    small = g[::q, ::q]
    big = ndi.median_filter(small, size=max(3, int(1.2 * H / q) | 1))
    big = np.kron(big, np.ones((q, q)))[:g.shape[0], :g.shape[1]]
    bd = np.abs(g - big) >= 5
    lab, n = ndi.label(bd)
    sz = np.array([])
    if n:
        sl = ndi.find_objects(lab)
        sz = np.array([max(a.stop - a.start, b.stop - b.start) for a, b in sl])
        sz = sz[ndi.sum(bd, lab, range(1, n + 1)) >= (0.1 * H) ** 2]
    out['blotch'] = dict(density=float(len(sz) / area_H), size=float(np.median(sz) / H) if len(sz) else 0.0)
    return out


def stones(rgb: np.ndarray, H: float = A, thr: float = 8.0) -> dict | None:
    """Laid stones (cobbles, setts, slabs): the pieces between dark joints, median width and
    height in art px."""
    L = lum(rgb)
    base = local_median(L, 0.3 * H)
    body = ndi.binary_opening((L - base) > -thr, iterations=1)
    lab, n = ndi.label(body)
    if n == 0:
        return None
    sl = ndi.find_objects(lab)
    area = ndi.sum(body, lab, range(1, n + 1))
    dims = np.array([(b.stop - b.start, a.stop - a.start) for a, b in sl])
    ok = (area >= (0.06 * H) ** 2) & (dims.max(1) <= 0.8 * H)
    if ok.sum() < 3:
        return None
    return dict(w=float(np.median(dims[ok, 0])), h=float(np.median(dims[ok, 1])), n=int(ok.sum()))


def ripples(rgb: np.ndarray, water: np.ndarray, H: float = A) -> dict | None:
    w = ndi.binary_erosion(water, iterations=2)
    if w.sum() < (0.5 * H) ** 2:
        return None
    ys, xs = np.nonzero(w)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    L = lum(rgb[y0:y1, x0:x1])
    base = local_median(L, 0.3 * H)
    m = w[y0:y1, x0:x1] & ((L - base) >= 12)
    lab, n = ndi.label(m, structure=np.ones((3, 3)))
    if not n:
        return None
    sl = ndi.find_objects(lab)
    ln = np.array([max(b.stop - b.start, a.stop - a.start) for a, b in sl])
    ln = ln[ln >= 3]
    if len(ln) < 3:
        return None
    return dict(length=float(np.median(ln)), n=int(len(ln)))


def _jpeg(rgb):
    from .bands import jpeg_roundtrip
    return jpeg_roundtrip(rgb)


def grain_tiles(rgb: np.ndarray, H: float = A, tile: float = 2.0, ignore: np.ndarray | None = None, jpeg=True, src=None):
    """Marks per tile of tile x tile H, each tagged grass (mostly green) or bare (dirt, paving,
    floor); tiles with water or much ignored ground are left out."""
    if src is None:
        src = _jpeg(rgb) if jpeg else rgb[..., :3]
    T = int(tile * H)
    gm = green_mask(rgb[..., :3])
    wm = water_mask(rgb[..., :3])
    out = []
    for y in range(0, rgb.shape[0] - T + 1, T):
        for x in range(0, rgb.shape[1] - T + 1, T):
            if wm[y:y + T, x:x + T].mean() > 0.05:
                continue
            if ignore is not None and ignore[y:y + T, x:x + T].mean() > 0.2:
                continue
            g = gm[y:y + T, x:x + T].mean()
            kind = 'grass' if g >= 0.7 else ('bare' if g <= 0.15 else None)
            if not kind:
                continue
            m = marks(src[y:y + T, x:x + T], H)
            out.append(dict(box=(x, y, x + T, y + T), kind=kind, **{k: v for k, v in m.items()}))
    return out


def check_grain(rgb: np.ndarray, H: float, subject: str, ignore: np.ndarray | None = None,
                paving: list | None = None, setts: list | None = None, jpeg=True) -> list[Finding]:
    """logic.scale on a ground fill: speckle (dark marks smaller and denser than Eastward's),
    blotch size, cobble and slab size in the named paved rects (art px), ripple length."""
    G = SIZES['grain']
    k = H / A
    fs: list[Finding] = []
    src = _jpeg(rgb) if jpeg else rgb[..., :3]
    tiles = grain_tiles(rgb, H, ignore=ignore, src=src)
    small = 0.75 * G['mark_size_H'][0]
    dense = 1.5 * G['mark_density_median']
    for kind in ('grass', 'bare'):
        ts = [t for t in tiles if t['kind'] == kind]
        if len(ts) < 2:
            continue
        sp = [t for t in ts if t['dark']['size'] < small and t['dark']['density'] > dense]
        size = float(np.median([t['dark']['size'] for t in ts]))
        dens = float(np.median([t['dark']['density'] for t in ts]))
        share = len(sp) / len(ts)
        if share >= 0.3:
            worst = max(sp, key=lambda t: t['dark']['density'])
            fs.append(Finding(
                'logic.scale', 'fault', worst['box'],
                f'{subject}: the {kind} fill is speckled at the wrong scale: its dark marks are {size * H:.1f} art px '
                f'({size:.3f} H) and {dens:.0f} to a H square in {share:.0%} of its tiles; Eastward\'s are '
                f'{G["mark_size_H"][0] * H:.1f} to {G["mark_size_H"][1] * H:.1f} art px at the same character height, '
                f'about {G["mark_density_median"]:.0f} to a H square',
                f'draw fewer, larger marks: tufts {G["tuft_px"][0] * k:.0f} to {G["tuft_px"][1] * k:.0f} art px in loose '
                f'clumps, soft blotches {G["blotch_px"][0] * k:.0f} to {G["blotch_px"][1] * k:.0f} across, and calm '
                'ground between them (eastward-edges.md 5.5)',
                score=size, threshold=small, subject=subject,
                extra={'class': 'grain', 'measure': f'{kind} dark marks', 'size_H': size, 'density': dens, 'share': share}))
        bl = [t['blotch']['size'] for t in ts if t['blotch']['size'] > 0]
        if len(bl) >= 3:
            b = float(np.median(bl))
            if not 0.25 <= b <= 1.1:
                fs.append(Finding('logic.scale', 'polish', ts[0]['box'],
                                  f'{subject}: the {kind} fill\'s blotches are {b * H:.0f} art px ({b:.2f} H) across; '
                                  f'Eastward\'s are {G["blotch_size_H"][0]:.2f} to {G["blotch_size_H"][1]:.2f} H',
                                  f'paint blotches {G["blotch_px"][0] * k:.0f} to {G["blotch_px"][1] * k:.0f} art px across',
                                  score=b, threshold=0.25, subject=subject, extra={'class': 'grain', 'measure': 'blotch'}))
    lo_c, hi_c = G['cobble_px']
    lo_s, hi_s = G['slab_px']
    for r in (paving or []) + (setts or []):
        x0, y0, x1, y1 = [int(v) for v in r]
        st = stones(src[y0:y1, x0:x1], H)
        if not st:
            continue
        size = max(st['w'], st['h']) / k
        if lo_c <= size <= hi_c or lo_s <= size <= hi_s:
            continue
        # the nearer of cobble and slab names the class
        cls, lo, hi = ('cobble', lo_c, hi_c) if size < (hi_c + lo_s) / 2 else ('slab', lo_s, hi_s)
        off = lo - size if size < lo else size - hi
        sev = 'polish' if off <= tol(lo if size < lo else hi) else 'fault'
        fs.append(Finding('logic.scale', sev, (x0, y0, x1, y1),
                          f'{subject}: the laid stones here are {st["w"]:.0f} x {st["h"]:.0f} art px; the size table gives '
                          f'{lo_c} to {hi_c} for a cobble or sett and {lo_s} to {hi_s} for a slab '
                          f'({G["cobble_eastward"]}; {G["slab_eastward"]})',
                          f'lay {cls}s {lo} to {hi} art px long', score=size, threshold=float(hi if size > hi else lo),
                          subject=subject, extra={'class': cls, 'measure': 'stone', 'value': size, 'range': [lo, hi]}))
    wm = water_mask(rgb[..., :3])
    rp = ripples(src, wm, H)
    if rp:
        lo, hi = G['ripple_px']
        v = rp['length'] / k
        if not lo <= v <= hi:
            ys, xs = np.nonzero(wm)
            fs.append(Finding('logic.scale', 'polish', (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1),
                              f'{subject}: ripple lines run {v:.0f} art px; Eastward\'s run {lo} to {hi} at our scale',
                              f'draw ripples {lo} to {hi} art px long, one or two px thick', score=v, threshold=float(hi),
                              subject=subject, extra={'class': 'ripple', 'measure': 'length'}))
    return fs


def grain_report(rgb: np.ndarray, H: float = A, ignore=None) -> dict:
    """Median marks per surface, for the audit."""
    tiles = grain_tiles(rgb, H, ignore=ignore)
    out = {}
    for kind in ('grass', 'bare'):
        ts = [t for t in tiles if t['kind'] == kind]
        if ts:
            out[kind] = {f'{w}_{q}': round(float(np.median([t[w][q] for t in ts])), 3)
                         for w in ('dark', 'light', 'blotch') for q in ('size', 'density')}
            out[kind]['tiles'] = len(ts)
    return out


# ------------------------------------------------------------------------------------------
# plan widths
def check_widths(zone: str) -> list[Finding]:
    p = os.path.join(GAME, 'data', 'plans', zone + '.json')
    if not os.path.exists(p):
        return []
    plan = json.load(open(p))
    d = 3.0
    fs = []
    W = SIZES['widths']
    for r in plan.get('routes') or []:
        kind = r.get('kind', 'path')
        if kind not in W:
            continue
        xs = [pt[0] for pt in r['points']]
        ys = [pt[1] for pt in r['points']]
        box = (min(xs) * d, min(ys) * d, max(xs) * d + 1, max(ys) * d + 1)
        lo, hi = W[kind]
        v = r.get('width', 24) * d
        if not lo <= v <= hi:
            off = lo - v if v < lo else v - hi
            fs.append(Finding('logic.scale', 'polish' if off <= tol(lo if v < lo else hi) else 'fault', box,
                              f'{zone}/{r.get("id")}: a {kind} {v:.0f} art px wide ({v / A:.2f} A); the size table gives {lo} to {hi} '
                              f'({W["_eastward"]})', f'make it {lo} to {hi} art px wide ({lo / d:.0f} to {hi / d:.0f} world px)',
                              score=v, threshold=float(hi if v > hi else lo), subject=f'{zone}/{r.get("id")}',
                              extra={'class': kind, 'measure': 'width'}))
    return fs


# ------------------------------------------------------------------------------------------
# the cast
CHARS = os.path.join(GAME, 'assets', 'characters')


def body_height(alpha: np.ndarray, foot_y: int, min_w: int = 9) -> int:
    """Feet to crown of the body: the largest 8-connected mass, rows at least min_w wide (a spear's head or a sprout on a head is narrower)."""
    lab, n = ndi.label(alpha, structure=np.ones((3, 3)))
    if n == 0:
        return 0
    areas = ndi.sum(alpha, lab, range(1, n + 1))
    m = lab == (1 + int(np.argmax(areas)))
    rows = np.nonzero(m.sum(1) >= min_w)[0]
    return int(foot_y - rows.min() + 1) if len(rows) else 0


def cast_class(cid: str) -> str:
    c = SIZES['cast']
    for k in ('creature_small', 'creature_medium', 'large'):
        if cid in c[k]:
            return k
    return c['default']


def measure_cast(cid: str) -> dict | None:
    d = os.path.join(CHARS, cid)
    mp = os.path.join(d, 'manifest.json')
    if not os.path.exists(mp):
        return None
    man = json.load(open(mp))
    fw, fh = man['frame_size']
    px, py = man['foot_pivot']
    hs, ws = [], []
    for dr in ('S', 'E'):
        p = os.path.join(d, 'sheets', f'idle_{dr}.png')
        if not os.path.exists(p):
            continue
        a = np.asarray(Image.open(p).convert('RGBA'))[..., 3] > 128
        for i in range(a.shape[1] // fw):
            f = a[:, i * fw:(i + 1) * fw]
            if not f.any():
                continue
            hs.append(body_height(f, py, 6 if cast_class(cid).startswith('creature') else 9))
            xs = np.nonzero(f.any(0))[0]
            ws.append(int(xs.max() - xs.min() + 1))
    if not hs:
        return None
    return dict(id=cid, h=float(np.median(hs)), w=float(np.median(ws)), target=man.get('body_height_target'),
                cls=cast_class(cid))


def check_cast(ids: list[str] | None = None) -> list[Finding]:
    ids = ids or sorted(os.listdir(CHARS))
    fs = []
    for cid in ids:
        m = measure_cast(cid)
        if not m:
            continue
        c = CLASSES[m['cls']]
        fs += judge(f'cast/{cid}', m['cls'], 'tall (body, feet to crown)', m['h'], c['h'], (0, 0, int(m['w']), int(m['h'])),
                    fix_extra=' (castwork rig scale; body_height_target in its manifest)')
    return fs


# ------------------------------------------------------------------------------------------
# a zone (the scene gate)
def check_zone(z, H: float = GAME_H) -> list[Finding]:
    """logic.scale on a loaded zone (scene.load_zone): every placed sprite, the buildings' doors,
    stairs, ground grain, cobbles and slabs in the plan's paving, and route widths."""
    fs: list[Finding] = []
    looks = plan_looks(z.id)
    d = 3.0
    for sp in z.sprites:
        if not sp.visible or any(k in sp.parent for k in ('Actors', 'Player')):
            continue
        name = os.path.splitext(os.path.basename(sp.path))[0]
        alpha = sp.rgba[..., 3] > 128
        off = (int(round(sp.box[0])), int(round(sp.box[1])))
        if base_name(name) in looks:
            fs += check_building(sp.rgba, z.id, name, looks[base_name(name)], offset=off)
        fs += check_sprite(alpha, f'{z.id}/{name}', sp.kind, offset=off)
    if z.ground is not None:
        rgb = z.ground[..., :3]
        fs += check_stairs(rgb, z.id)
        paving, setts = [], []
        p = os.path.join(GAME, 'data', 'plans', z.id + '.json')
        if os.path.exists(p):
            art = json.load(open(p)).get('art') or {}
            paving = [[x * d, y * d, (x + w) * d, (y + h) * d] for x, y, w, h in art.get('paving') or []]
            setts = [[x * d, y * d, (x + w) * d, (y + h) * d] for x, y, w, h in art.get('setts') or []]
        fs += check_grain(rgb, H, f'{z.id}/ground', paving=paving, setts=setts)
    fs += check_widths(z.id)
    return fs


# ------------------------------------------------------------------------------------------
# the asset gate
def plan_paving(zone: str, density: float = 3.0):
    p = os.path.join(GAME, 'data', 'plans', zone + '.json')
    if not os.path.exists(p):
        return [], []
    art = json.load(open(p)).get('art') or {}
    r = lambda rs: [[x * density, y * density, (x + w) * density, (y + h) * density] for x, y, w, h in rs or []]
    return r(art.get('paving')), r(art.get('setts'))


_SPEC = re.compile(r'(\d+(?:\.\d+)?)\s*to\s*(\d+(?:\.\d+)?)\s*(tall|wide)\b')
_SPEC_AT = re.compile(r'art px:\s*([^)]*)')


def spec_ranges(text: str | None) -> dict:
    """A kit piece's own size spec, from its `audit.size_class`: the ranges after "art px:" (its
    opaque box at density 3), e.g. "shelter (eave 2.7 m; art px: 150 to 180 tall, 120 to 160 wide)"
    gives {'tall': (150, 180), 'wide': (120, 160)}. Prose without "art px:" (a size-guide range in
    world px, a gate's opening) gives {}: nothing to check."""
    out = {}
    for seg in _SPEC_AT.findall(text or ''):
        for lo, hi, ax in _SPEC.findall(seg):
            out[ax] = (float(lo), float(hi))
    return out


_GUIDE = None


UNSIZED = 'unsized'      # a spec's head word for a piece no kind fits: it must say why in its parentheses
GROUND = 'ground'        # a piece of ground (terrain, a surface): measured by its grain, not a box


def _guide():
    global _GUIDE
    if _GUIDE is None:
        with open(os.path.join(REPO, 'scripts', 'art', 'size_guide.json'), encoding='utf-8') as fh:
            _GUIDE = json.load(fh)
    return _GUIDE


def kind_ranges(name: str):
    """A kind's height and width in art px at density 3 with its tolerance: sizes.json's bbox
    classes first (art px, `tol`), then the size guide's kinds (world px x 3, its own tolerance).
    None when the name is no measurable kind."""
    def ok(r):
        return isinstance(r, (list, tuple)) and len(r) == 2 and r[0] is not None and r[1] is not None
    c = CLASSES.get(name)
    if c and c.get('measure') == 'bbox':
        out = {}
        for ax, key in (('tall', 'h'), ('wide', 'w')):
            r = c.get(key)
            out[ax] = (r[0] - tol(r[0]), r[1] + tol(r[1])) if ok(r) else (0.0, float('inf'))
        return out
    k = _guide()['kinds'].get(name)
    if not k:
        return None
    d = 3.0                                                          # art px a world px at density 3
    t = float(_guide().get('tolerance', 2)) * d
    return {ax: ((k[key][0] * d - t, k[key][1] * d + t) if ok(k.get(key)) else (0.0, float('inf')))
            for ax, key in (('tall', 'h'), ('wide', 'w'))}


def guide_kind(size_class: str | None):
    """The kind a piece's size spec names as its head word ("water_mill (...)"), with its height and
    width in art px at density 3 and the tolerance (`kind_ranges`). Returns (head, ranges), (head,
    None) for the explicit `unsized` (no kind fits; the spec says why) and for `ground`, or (head,
    False) when the head word names no kind at all, which check_spec reports loudly rather than
    skipping (round 5 of the Act 1 detail audit, Claude A's ruling)."""
    head = (size_class or '').split('(')[0].strip().split(' ')[0] if size_class else ''
    if not head:
        return None
    if head in (UNSIZED, GROUND):
        return head, None
    r = kind_ranges(head)
    return (head, r) if r else (head, False)


# words that say nothing about what a thing is, left out when an `unsized` spec's reason is matched
# against the kinds' names and descriptions
_STOP = set("""a an and are as at be beside but by for from has in into is it its of on or out over the
their them then there this to under up with without no not one two three any every each own than that
what which who whose where when only alone kind kinds guide size sizes sized spec art px tall wide high
long deep across about cell cells piece pieces object objects thing things drawn draw ground run here
more most less least make made person world set""".split())


def _norm(w: str) -> str:
    w = w.lower().strip("'")
    if w.endswith("'s"):
        w = w[:-2]
    if len(w) > 4 and w.endswith('s') and not w.endswith('ss'):
        w = w[:-1]
    return w


def _words(text: str) -> set:
    out = set()
    for w in re.findall(r"[a-z][a-z']+", (text or '').lower().replace('_', ' ')):
        w = _norm(w)
        if len(w) > 2 and w not in _STOP:
            out.add(w)
    return out


def _kinds():
    seen = []
    for n in list(CLASSES) + list(_guide()['kinds']):
        if n not in seen and kind_ranges(n):
            seen.append(n)
    return seen


def _kind_ident(name: str) -> set:
    c = CLASSES.get(name)
    extra = (c.get('names') or []) if (c and c.get('measure') == 'bbox') else []
    return _words(' '.join([name] + list(extra)))


def _kind_desc(name: str) -> set:
    c = CLASSES.get(name)
    if c and c.get('measure') == 'bbox':
        return _words(c.get('real') or '')
    return _words((_guide()['kinds'].get(name) or {}).get('reason') or '')


_DESC_DF = None


def unsized_fits(size_class: str | None, got: dict | None = None) -> list:
    """The guide kinds an `unsized (why ...)` spec could have named. A kind is a lead when the spec's
    reason shares a word with the kind's name (a "bollard" it names) or a word that describes at
    most two kinds (a "signal" mast), and the kind's size range holds the drawn box or overlaps the
    spec's own art px ranges; unless a ruling in sizes.json's `unsized_rulings` says the piece is not
    that kind (the churn stand is not churns). Round 6 of the Act 1 detail audit (R6-3, R6-12):
    `unsized` is only for a piece no kind fits, and the v7 bitt (the guide's bollard) and semaphore
    (its pole, a signal mast) had kinds. Returns [(kind, shared words)]."""
    global _DESC_DF
    gk = guide_kind(size_class)
    if not gk or gk[0] != UNSIZED:
        return []
    if _DESC_DF is None:
        _DESC_DF = {}
        for n in _kinds():
            for w in _kind_desc(n):
                _DESC_DF[w] = _DESC_DF.get(w, 0) + 1
    reason = (size_class or '').split('(', 1)[-1].split('art px:')[0]
    low = reason.lower()
    sw = _words(reason)
    own = spec_ranges(size_class)
    rulings = SIZES.get('unsized_rulings') or []
    out = []
    for name in _kinds():
        if any(r.get('kind') == name and r.get('not', '').lower() in low for r in rulings):
            continue
        shared = (sw & _kind_ident(name)) | {w for w in sw & _kind_desc(name) if _DESC_DF.get(w, 0) <= 2}
        if not shared:
            continue
        r = kind_ranges(name)
        holds = got is not None and all(r[ax][0] <= got[ax] <= r[ax][1] for ax in ('tall', 'wide'))
        overlaps = bool(own) and all(ax in own and own[ax][0] <= r[ax][1] and own[ax][1] >= r[ax][0]
                                     for ax in ('tall', 'wide'))
        if holds or overlaps:
            out.append((name, sorted(shared)))
    return out


_KIT_SPECS = None


def kit_spec(path: str):
    """The size spec (`audit.size_class`) of the kit piece one of whose variant pictures is `path`
    (game/kit/props/index.json maps each variant to its PNG), or None for a picture no kit piece
    paints. The asset gate measures a kit picture against it (R6-12)."""
    global _KIT_SPECS
    if _KIT_SPECS is None:
        _KIT_SPECS = {}
        idx = os.path.join(GAME, 'kit', 'props', 'index.json')
        if os.path.exists(idx):
            with open(idx, encoding='utf-8') as fh:
                index = json.load(fh)
            specs, runs = {}, {}
            for pp in glob.glob(os.path.join(GAME, 'kit', 'pieces', '*', '*.json')):
                with open(pp, encoding='utf-8') as fh:
                    d = json.load(fh)
                specs[d.get('id')] = (d.get('audit') or {}).get('size_class')
                bd = (d.get('placement') or {}).get('boundary')
                if bd:
                    runs[d.get('id')] = {'joins': sorted(bd.get('joins') or []), 'span_cells': bd.get('span_cells', 1),
                                         'role': (d.get('placement') or {}).get('role')}
            for pid, e in index.items():
                if not isinstance(e, dict):
                    continue
                for vid, v in (e.get('variants') or {}).items():
                    png = (v or {}).get('png') or ''
                    if png.startswith('res://'):
                        run = dict(runs[pid], variant=vid) if pid in runs else None
                        _KIT_SPECS[os.path.normpath(os.path.join(GAME, png[len('res://'):]))] = (specs.get(pid), run)
    return (_KIT_SPECS.get(os.path.normpath(os.path.abspath(path))) or (None, None))[0]


def kit_run(path: str):
    """The run a kit picture is a cell of ({'joins', 'span_cells', 'role'} from its piece's
    placement.boundary: a fence, a drystone wall, a gate in one), or None for a whole object (round 7
    of the Act 1 detail audit, R7-2)."""
    kit_spec(path)
    return (_KIT_SPECS.get(os.path.normpath(os.path.abspath(path))) or (None, None))[1]


def check_spec(rgba: np.ndarray, size_class: str | None, subject: str, run: dict | None = None) -> list[Finding]:
    """logic.size_spec: the drawn picture's opaque box against the piece's own size spec (the detail
    audit of 4 Nov: the shelter drawn at a third of its 2.2 m, the millstones at 0.74 m of their 1.2 m,
    the barrow's portal at a third of its own size). Every picture of a piece is measured. The spec's
    head word names its kind ("water_mill (...)"), and the picture is measured against that kind's
    range too (logic.size_guide), so a spec cannot drift from the guide unseen (round 5 of the Act 1
    detail audit, R5-13: the v6 mill met its own 160 to 190 and was half the guide's water mill). A
    head word that names no kind is a fault, never a silent skip; `unsized (why ...)` says outright
    that no kind fits.

    `run` (kit_run) marks a cell of a run: a fence or wall cell is not a whole fence, so it is measured
    by its height only, and only where its height is the run's (a straight east-west cell; a cell
    running north-south or turning a corner draws the run's length down the screen). Round 7, R7-2: a
    run cell measured as a whole fence raised 93 false faults."""
    rng = spec_ranges(size_class)
    alpha = rgba[..., 3] > 128
    if not alpha.any():
        return []
    ys, xs = np.nonzero(alpha)
    got = {'tall': ys.max() - ys.min() + 1, 'wide': xs.max() - xs.min() + 1}
    axes = ('tall', 'wide')
    if run is not None:
        # a gate swung open draws its leaf down the screen, as a north-south cell does
        axes = ('tall',) if run.get('joins') == ['e', 'w'] and run.get('variant') != 'open' else ()
    out = []
    gk = guide_kind(size_class)
    if gk and gk[1] is False:
        out.append(Finding('logic.size_guide', 'fault', (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1),
                           f'{subject}: its size spec names "{gk[0]}", which is no kind in sizes.json or the size guide, so it '
                           'cannot be measured against one', 'name the kind it is as the spec\'s head word, rule a new kind into '
                           f'sizes.json and size-guide.md, or say "{UNSIZED} (why no kind fits; ...)"', subject=subject))
    elif gk and gk[0] == UNSIZED:
        for kind, shared in (unsized_fits(size_class, got) if run is None else []):
            out.append(Finding('logic.size_unsized', 'fault', (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1),
                               f'{subject}: its spec says no kind fits, but the guide\'s {kind} shares "{", ".join(shared)}" '
                               'with its reason and holds its size', f'head the spec "{kind} (...)" and measure it there, or rule '
                               'a new kind into sizes.json and size-guide.md (R6-3: unsized is only for a piece no kind fits)',
                               subject=subject))
    elif gk and gk[1]:
        kind, grng = gk
        for ax, (lo, hi) in grng.items():
            if ax not in axes:
                continue
            v = float(got[ax])
            if v < lo or v > hi:
                out.append(Finding('logic.size_guide', 'fault', (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1),
                                   f'{subject}: drawn {v:.0f} art px {ax}, the kind {kind} is {lo:.0f} to {hi:.0f} '
                                   f'(with its tolerance)',
                                   'redraw it to the guide in the generator (prop-logic rule 9), or rule a new kind into the '
                                   'size guide first', score=v, threshold=lo if v < lo else hi, subject=subject))
    for ax, (lo, hi) in rng.items():
        if ax not in axes:
            continue
        v = float(got[ax])
        if v < lo or v > hi:
            out.append(Finding('logic.size_spec', 'fault', (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1),
                               f'{subject}: drawn {v:.0f} art px {ax}, its own spec says {lo:.0f} to {hi:.0f} ({size_class})',
                               'redraw it to its spec in the generator (prop-logic rule 9: never stretch a bitmap), or correct '
                               'the spec if the spec is wrong', score=v, threshold=lo if v < lo else hi, subject=subject))
    return out


def check_asset(rgba: np.ndarray, subject: str, kind: str | None = None, H: float = GAME_H, density: float = 3.0,
                ground: bool = False, ignore: np.ndarray | None = None) -> list[Finding]:
    """logic.scale for the asset gate: a ground picture's grain (and its plan's paving and
    stairs), or a sprite's box (and a kit building's doors, storey and roof)."""
    zone, _, name = subject.partition('/')
    if ground:
        paving, setts = plan_paving(zone, density) if base_name(name) == 'ground' else ([], [])
        fs = check_grain(rgba[..., :3], H, subject, ignore=ignore, paving=paving, setts=setts)
        if base_name(name) == 'ground':
            fs += check_stairs(rgba[..., :3], zone, density)
        return fs
    fs = check_sprite(rgba[..., 3] > 128, subject, kind, density)
    fs += check_building(rgba, zone, name, density=density)
    return fs


def markdown() -> str:
    u = SIZES['unit']
    lines = [f'Art px at density 3. A = {u["adult_art_px"]} art px = {u["adult_m"]} m, so {u["art_px_per_m"]} art px a metre; '
             f'Eastward\'s adult is {u["eastward_adult_px"]} E px, so an Eastward length times {u["k_eastward"]} is ours.', '',
             '| Class | Height (art px) | Width (art px) | Height (A) | Real size | Eastward at the same character height | Chunky on purpose |',
             '| --- | --- | --- | --- | --- | --- | --- |']
    for cid, c in CLASSES.items():
        w = f'{c["w"][0]} to {c["w"][1]}' if c['w'][1] else ''
        lines.append(f'| {cid.replace("_", " ")} | {c["h"][0]} to {c["h"][1]} | {w} | {c["h_A"][0]:.2f} to {c["h_A"][1]:.2f} | '
                     f'{c["real"]} | {c["eastward"]} | {c.get("chunky") or ""} |')
    return '\n'.join(lines)


def audit(out: str) -> dict:
    """Every placed asset, building, stair, fill and cast member measured, with findings."""
    from . import scene as SN
    zones = json.load(open(os.path.join(GAME, 'data', 'zones.json')))
    rep = {'zones': {}, 'cast': [], 'findings': []}
    for zid in zones:
        z = SN.load_zone(zid)
        seen = {}
        for sp in z.sprites:
            name = os.path.splitext(os.path.basename(sp.path))[0]
            if name in seen or not sp.path.startswith('game/zones/'):
                continue
            m = measure_sprite(sp.rgba[..., 3] > 128)
            seen[name] = dict(cls=class_of(f'{zid}/{name}', sp.kind), **(m or {}))
            look = plan_looks(zid).get(base_name(name))
            if look:
                L = 3 + int(round(look.get('overhang', 3) * 3))
                B = sp.rgba.shape[0] - 4
                doors = look.get('doors') or ([[look['door'], None]] if 'door' in look else [])
                seen[name]['doors'] = [measure_opening(sp.rgba, L + int(round(dx * 3)), B) for dx, _ in doors]
                seen[name]['look'] = {k: look.get(k) for k in ('wall_h', 'roof_h', 'door_w', 'door_h', 'win_w', 'win_h')}
        fs = check_zone(z)
        gr = grain_report(z.ground[..., :3]) if z.ground is not None else {}
        rep['zones'][zid] = dict(assets=seen, grain=gr, stairs=[(s, stair_pitch(z.ground[..., :3], b)) for s, b in plan_stairs(zid)]
                                 if z.ground is not None else [])
        rep['findings'] += [dict(zone=zid, **f.to_json()) for f in fs]
    from . import assets as AS
    rep['kit'] = {}
    for k in AS.KIT:
        p = AS.render_kit(k)
        rgba = np.asarray(Image.open(p).convert('RGBA'))
        m = measure_sprite(rgba[..., 3] > 128)
        rep['kit'][k] = dict(cls=class_of('kit/' + k), **(m or {}))
        rep['findings'] += [dict(zone='kit', **f.to_json()) for f in check_sprite(rgba[..., 3] > 128, 'kit/' + k)]
    for cid in sorted(os.listdir(CHARS)):
        m = measure_cast(cid)
        if m:
            rep['cast'].append(m)
    rep['findings'] += [dict(zone='cast', **f.to_json()) for f in check_cast()]
    with open(out, 'w') as fh:
        json.dump(rep, fh, indent=1, default=lambda o: o if not isinstance(o, np.generic) else o.item())
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--markdown', action='store_true')
    ap.add_argument('--audit')
    ap.add_argument('--cast', action='store_true')
    a = ap.parse_args(argv)
    if a.markdown:
        print(markdown())
    if a.cast:
        for f in check_cast():
            print(f.severity.upper(), f.message)
    if a.audit:
        rep = audit(a.audit)
        bad = [f for f in rep['findings'] if f['severity'] != 'polish']
        print(f'{len(rep["findings"])} findings, {len(bad)} faults; report in {a.audit}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
