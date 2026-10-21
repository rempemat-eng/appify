"""Tally, the drover's apprentice of the Brackens: three design options (Claude J lane).

Main question: lamb and cardigan. How the knit reads against natural fleece, and how she
carries the tally stick and the fold bell.

    A  Crook-staff drover: a fitted berry cardigan to the hip with the fleece curling out
       under the hem, a tall notched tally stick used as a crook, the fold bell on its hook.
    B  Collar-bell puffball: a black-faced lamb, a cropped sky cardigan over a round fleece
       belly, a short stick tucked in a strap at the hip, the bell on a collar ribbon.
    C  Big-cardigan clerk: an oversized brass cardigan to the knees with big buttons and
       rolled cuffs, the stick behind her ear like a pencil, a tin bell on a cord.

Views: S idle, E idle, W idle (W is drawn with its own light, never mirrored pixels) and
the S key pose of her fidget (counting). Design sheets are review material; production
frames come from the shared rig.

Run from the repo root:  python3 scripts/art/characters/designs/tally.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sheetkit as sk  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
OUT_PNG = os.path.join(ROOT, 'docs/vision/characters/designs/tally-options.png')
OUT_JSON = os.path.join(ROOT, 'docs/vision/characters/designs/tally.json')
OUT_FINAL = os.path.join(ROOT, 'docs/vision/characters/designs/tally-final.png')
SCRATCH = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '.char-views')), 'tally')

W, H = 64, 72
AX, AY = 32, 66          # foot anchor: soles fill row 65, their outline lands on row 66
SOLE = AY - 1
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


# --- painting helpers (local to this design; sheetkit stays untouched) -----------------
def tone(fig, p):
    v = fig.px.get(p)
    return v[1] if v and isinstance(v[1], int) else None


def fam_at(fig, p):
    v = fig.px.get(p)
    return v[0] if v else None


def cloth(fig, mask, fam, lit=2, dark=2, folds=(), top=True, bottom=True):
    """Cloth in vertical bands (house-style 5): a lit west band, the body, a shaded east
    band, a lit top row (shoulders) and a dark hem row. `folds` are x columns of tone 2
    (a fold is a recess), each with its lit lip one pixel to the west."""
    mask = set(mask)
    rows, cols = {}, {}
    for (x, y) in mask:
        rows.setdefault(y, []).append(x)
        cols.setdefault(x, []).append(y)
    for (x, y) in mask:
        xl, xr = min(rows[y]), max(rows[y])
        t = 3
        if x - xl < lit:
            t = 4
        elif xr - x < dark:
            t = 2
        if top and y == min(cols[x]) and t >= 3:
            t = 4
        if bottom and y == max(cols[x]):
            t = 1
        fig.put(x, y, fam, t)
    for fx in folds:
        for (x, y) in mask:
            if x == fx and y > min(cols[x]) + 1 and y < max(cols[x]):
                fig.put(x, y, fam, 2)
    return mask


def knit(fig, mask, fam, y0=0):
    """Knit as rows of 2 px loops: every second row carries dashes two pixels long, one
    tone down, the dashes staggered row to row so they read as stitches, not a grid."""
    for (x, y) in mask:
        r = y - y0
        if r % 2 == 1 and (x + (r // 2) % 2) % 3 != 2 and fam_at(fig, (x, y)) == fam:
            t = tone(fig, (x, y))
            if t is not None and t >= 2:
                fig.put(x, y, fam, t - 1)


def rib(fig, mask, fam):
    """Ribbed hem or cuff: alternate columns a tone apart (2 px tall at least)."""
    for (x, y) in mask:
        t = tone(fig, (x, y))
        if t is not None and fam_at(fig, (x, y)) == fam and x % 2 == 0:
            fig.put(x, y, fam, max(1, t - 1))


# Curl stamps: a = warm cap (tone 4), b = body (3), c = cool crescent (2), d = its
# deepest corner (1). Sibling ramps give the curls a warm-lit, violet-shaded turn.
CURL_BIG = ('.aab.',
            'abbcb',
            'bbccc',
            '.ccd.')
CURL_SMALL = ('aa.',
              'abc',
              '.cd')
CURL_TONE = {'a': ('_warm', 4), 'b': ('', 3), 'c': ('_cool', 2), 'd': ('_cool', 1)}


def curls(fig, lobes, fam, gbox, bias=0):
    """Fleece as clumped curls (house-style 5): each lobe is a hand-drawn curl, a warm lit
    cap at its upper left and a cool dark crescent at its lower right, corners knocked off
    so the edge scallops. Lobes are painted back (top) to front (bottom), so each front
    curl's lit cap sits against the shaded underside of the curl behind it. The mass as a
    whole is lit from the upper left: curls at its lower right sit a tone down."""
    gx, gy, grx, gry = gbox
    mine = set()
    for (cx, cy, r) in sorted(lobes, key=lambda l: (l[1], l[0])):
        stamp = CURL_BIG if r >= 2.2 else CURL_SMALL
        ox = round(cx) - len(stamp[0]) // 2
        oy = round(cy) - len(stamp) // 2
        ng = 0.55 * (cx - gx) / grx + 0.85 * (cy - gy) / gry
        shift = (-1 if ng > 0.5 else 0) + bias
        for j, row in enumerate(stamp):
            for i, ch in enumerate(row):
                if ch == '.':
                    continue
                suf, t = CURL_TONE[ch]
                fig.put(ox + i, oy + j, fam + suf, max(1, t + shift))
                mine.add((ox + i, oy + j))
    return mine


def pillow(fig, mask, fam, glint=False):
    """A round part (a face, a bell): the lit cap is a disc offset to the upper left and
    the dark crescent the outside of a larger offset disc, so the terminator follows the
    form instead of stepping across it in a straight diagonal."""
    mask = set(mask)
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    cx, cy = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2
    rx, ry = max(1.0, (max(xs) - min(xs) + 1) / 2), max(1.0, (max(ys) - min(ys) + 1) / 2)
    for (x, y) in mask:
        u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        t = 3
        if (u + 0.42) ** 2 + (v + 0.5) ** 2 < 0.42:
            t = 4
        if (u + 0.28) ** 2 + (v + 0.32) ** 2 > 1.05:
            t = 2
        if (x, y + 1) not in mask and (u > -0.3):
            t = min(t, 1 if u > 0.2 else 2)
        fig.put(x, y, fam, t)


def stick(fig, pts_from, pts_to, fam='timber', notch=3, lit_left=True):
    """A tally stick two pixels wide: a lit west column, a shaded east one, and notches
    cut across both as dark two-pixel nicks."""
    (x0, y0), (x1, y1) = pts_from, pts_to
    n = max(abs(x1 - x0), abs(y1 - y0))
    pts = [(round(x0 + (x1 - x0) * i / max(1, n)), round(y0 + (y1 - y0) * i / max(1, n))) for i in range(n + 1)]
    for (x, y) in pts:
        fig.put(x, y, fam, 4)
        fig.put(x + 1, y, fam, 2)
    if notch:
        for i, (x, y) in enumerate(pts):
            if 2 <= i < len(pts) - 2 and i % notch == 0:
                fig.put(x, y, fam, 1)
                fig.put(x + 1, y, fam, 1)
    return pts


def bell(fig, cx, top, fam='brass', tilt=0):
    """The fold bell, 5 x 5: a domed crown, a flared lip, a dark mouth and a clapper."""
    rows = [(cx - 1 + tilt, cx + 1 + tilt), (cx - 2 + tilt, cx + 1 + tilt), (cx - 2 + tilt, cx + 2 + tilt),
            (cx - 2, cx + 2), (cx - 3, cx + 3)]
    m = set()
    for j, (a, b) in enumerate(rows):
        for x in range(a, b + 1):
            m.add((x, top + j))
    for (x, y) in m:
        row = rows[y - top]
        t = 3
        if x == row[0] or y == top:
            t = 4
        if x >= row[1] - 0:
            t = 2
        fig.put(x, y, fam, t)
    fig.put(rows[1][0], top + 1, fam, 5)
    fig.put(rows[1][0], top + 2, fam, 5)
    for x in range(cx - 2, cx + 3):
        fig.put(x, top + 4, fam, 1)
    fig.put(cx - 3, top + 4, fam, 2)
    fig.put(cx + 3, top + 4, fam, 1)
    fig.put(cx, top + 5, fam, 1)          # clapper
    fig.put(cx + 1, top + 5, fam, 0)
    return m


def despeckle(fig, keep):
    """No speckle (house-style 4): a pixel unlike all four neighbours takes its most common
    neighbour, unless it is an eye, a glint, a nail or a rivet (`keep`)."""
    for _ in range(2):
        changes = {}
        for p, v in fig.px.items():
            if p in keep or v[0] in ('ink', '_edge', '_lit'):
                continue
            nb = [fig.px.get((p[0] + dx, p[1] + dy)) for dx, dy in N4]
            if any(n is None for n in nb):
                continue
            if all(n != v for n in nb):
                cand = [n for n in nb if n[0] not in ('ink', '_edge', '_lit')]
                if not cand:
                    continue
                best = max(cand, key=lambda n: (cand.count(n), n[0] == v[0]))
                changes[p] = best
        for p, v in changes.items():
            fig.px[p] = v


# --- the lamb ------------------------------------------------------------------------
class Opt:
    def __init__(self, label, face, knit_fam, legs, hoof, bell_fam, inner_ear, nose):
        self.label, self.face, self.knit, self.legs, self.hoof = label, face, knit_fam, legs, hoof
        self.bell, self.inner_ear, self.nose = bell_fam, inner_ear, nose


A = Opt('A', 'plaster', 'berry', 'plaster', 'timber', 'brass', 'berry', ('berry', 1))
B = Opt('B', 'slate', 'sky', 'slate', 'slate', 'brass', 'slate', ('slate', 0))
C = Opt('C', 'plaster', 'clay', 'plaster', 'timber', 'brass', 'plaster', ('timber', 1))


def legs_front(fig, o, top=57, xs=(28, 34), width=3, lift=None):
    for i, x0 in enumerate(xs):
        bot = SOLE - (2 if lift == i else 0)
        leg = fig.rect(x0, top, x0 + width - 1, bot - 2)
        cloth(fig, leg, o.legs, lit=1, dark=1, top=False, bottom=False)
        fig.fill(fig.rect(x0, bot - 1, x0 + width - 1, bot), o.hoof, 1)
        fig.put(x0, bot - 1, o.hoof, 2)
        if width > 2:
            fig.put(x0 + 1, bot - 1, o.hoof, 2)


def legs_side(fig, o, d, top=56, width=3):
    cx = AX
    for i, lx in enumerate((cx - d * 3, cx + d * 1)):
        x0 = lx if d == 1 else lx - width + 1
        leg = fig.rect(x0, top, x0 + width - 1, SOLE - 2)
        cloth(fig, leg, o.legs, lit=1, dark=1, top=False, bottom=False)
        if i == 0:   # the far leg sits a tone back
            for p in leg:
                fig.put(p[0], p[1], o.legs, max(1, tone(fig, p) - 1))
        fig.fill(fig.rect(x0, SOLE - 1, x0 + width - 1, SOLE), o.hoof, 1)
        fig.put(x0, SOLE - 1, o.hoof, 2)
        fig.put(x0 + 1, SOLE - 1, o.hoof, 2)


def ears_front(fig, o, cy, tilt=0, droop=0):
    for side in (-1, 1):
        base = 32 + tilt + side * 5
        tip = base + side * 7
        pts = [(base, cy - 3), (tip, cy - 1 + droop), (tip, cy + 1 + droop), (base, cy + 1)]
        if side < 0:
            pts = [(p[0] + 1, p[1]) for p in pts]
        ear = fig.poly(pts)
        colsy = {}
        for (x, y) in ear:
            colsy.setdefault(x, []).append(y)
        for (x, y) in ear:
            t = 3 if side < 0 else 2
            if y == min(colsy[x]):
                t += 1
            elif y == max(colsy[x]):
                t -= 1
            fig.put(x, y, o.face, t)
        # inner ear: a warm two-pixel cluster (a recess on a black face)
        ix = base + side * 3
        for k in range(2):
            if o.inner_ear == o.face:
                fig.put(ix + side * k, cy, o.face, 1)
            else:
                fig.put(ix + side * k, cy, o.inner_ear, 4)


def crown_front(fig, cy, tilt=0, big=1.0):
    lobes = [(28 + tilt, cy - 8, 3), (32 + tilt, cy - 8, 3), (36 + tilt, cy - 8, 3),
             (26 + tilt, cy - 5, 3), (30 + tilt, cy - 5, 3), (34 + tilt, cy - 5, 3), (38 + tilt, cy - 5, 3)]
    curls(fig, lobes, 'snow', (32 + tilt, cy - 6, 7.5, 4.5))


def face_front(fig, o, cy, tilt=0, eyes='open'):
    face = fig.ellipse(32 + tilt, cy, 6.5, 5.6)
    pillow(fig, face, o.face)
    for (x, y) in fig.ellipse(32 + tilt, cy + 3, 3.6, 2.2):
        if (x, y) in face and tone(fig, (x, y)) < 4 and o.face != 'slate':
            fig.put(x, y, o.face, tone(fig, (x, y)) + 1)
    nf, nt = o.nose
    for p in ((31, cy + 2), (32, cy + 2), (33, cy + 2), (32, cy + 3)):
        fig.put(p[0] + tilt, p[1], nf, nt)
    keep = set()
    if o.face == 'slate':
        if eyes == 'open':
            for ex in (28 + tilt, 35 + tilt):
                for yy in (cy - 2, cy - 1):
                    fig.put(ex, yy, 'ink', 0)
                    fig.put(ex + 1, yy, 'ink', 0)
                fig.put(ex, cy - 2, 'snow', 5)
                fig.put(ex, cy, 'snow_cool', 3)
                fig.put(ex + 1, cy, 'snow_cool', 3)
                keep |= {(ex, cy - 2), (ex, cy), (ex + 1, cy)}
        else:
            for ex in (28 + tilt, 35 + tilt):
                fig.put(ex, cy - 1, 'snow_cool', 3)
                fig.put(ex + 1, cy - 1, 'snow_cool', 3)
                fig.put(ex - 1 if ex < 32 else ex + 2, cy, 'snow_cool', 3)
                keep |= {(ex, cy - 1), (ex + 1, cy - 1), (ex - 1 if ex < 32 else ex + 2, cy)}
    else:
        if eyes in ('open', 'down'):
            for ex in (28 + tilt, 35 + tilt):
                top = cy - 2 + (1 if eyes == 'down' else 0)
                for dy in range(3 if eyes == 'open' else 2):
                    fig.put(ex, top + dy, 'ink', 0)
                    fig.put(ex + 1, top + dy, 'ink', 0)
                fig.put(ex, top, 'snow', 5)
                keep.add((ex, top))
                if eyes == 'down':   # a lid of face tone 1 above the lowered eye
                    fig.put(ex, top - 1, o.face, 2)
                    fig.put(ex + 1, top - 1, o.face, 2)
        else:  # closed, smiling arcs
            for ex in (28 + tilt, 35 + tilt):
                fig.put(ex, cy - 1, 'ink', 0)
                fig.put(ex + 1, cy - 1, 'ink', 0)
                fig.put(ex - 1 if ex < 32 else ex + 2, cy, 'ink', 0)
    # cheeks: a warm two-pixel blush on a cream face (berry tone 5)
    if o.face != 'slate' and o.inner_ear == 'berry':
        for bx in (27 + tilt, 36 + tilt):
            fig.put(bx, cy + 1, 'berry', 5)
            fig.put(bx + 1, cy + 1, 'berry', 5)
    return keep


def head_front(fig, o, dy=0, tilt=0, eyes='open', droop=0, before_ears=None):
    cy = 38 + dy
    if before_ears:
        before_ears(fig)
    ears_front(fig, o, cy, tilt, droop)
    keep = face_front(fig, o, cy, tilt, eyes)
    crown_front(fig, cy, tilt)
    return keep


def head_side(fig, o, d, dy=0, look=0, eyes='open'):
    """E (d=1) or W (d=-1): a long lamb muzzle forward, the ear hanging back, curls on top."""
    cx, cy = AX + d, 38 + dy
    ex = cx - d * 2
    if d == 1:
        ear = fig.poly([(ex, cy - 3), (ex - 7, cy + 1), (ex - 6, cy + 3), (ex + 1, cy + 1)])
    else:
        ear = fig.poly([(ex + 1, cy - 3), (ex + 8, cy + 1), (ex + 7, cy + 3), (ex, cy + 1)])
    colsy = {}
    for (x, y) in ear:
        colsy.setdefault(x, []).append(y)
    for (x, y) in ear:
        t = 3 if d == -1 else 2
        if y == min(colsy[x]):
            t += 1
        elif y == max(colsy[x]):
            t = 1
        fig.put(x, y, o.face, t)
    skull = fig.ellipse(cx - d * 0.5, cy, 5.6, 5.4)
    snout = fig.ellipse(cx + d * 4.5, cy + 2 + look, 3.3, 2.6)
    face = skull | snout
    pillow(fig, face, o.face)
    nf, nt = o.nose
    tipx = max(x for x, y in snout) if d == 1 else min(x for x, y in snout)
    fig.put(tipx, cy + 1 + look, nf, nt)
    fig.put(tipx, cy + 2 + look, nf, nt)
    fig.put(tipx - d, cy + 4 + look, o.face, 1)
    fig.put(tipx - 2 * d, cy + 4 + look, o.face, 1)
    keep = set()
    exx = cx + d * 2 if d == 1 else cx - 3
    if o.face == 'slate':
        for yy in (cy - 2, cy - 1):
            fig.put(exx, yy, 'ink', 0)
            fig.put(exx + 1, yy, 'ink', 0)
        fig.put(exx, cy - 2, 'snow', 5)
        fig.put(exx, cy, 'snow_cool', 3)
        fig.put(exx + 1, cy, 'snow_cool', 3)
        keep |= {(exx, cy - 2), (exx, cy), (exx + 1, cy)}
    else:
        top = cy - 2 + (1 if eyes == 'down' else 0)
        for yy in range(top, top + (3 if eyes == 'open' else 2)):
            fig.put(exx, yy, 'ink', 0)
            fig.put(exx + 1, yy, 'ink', 0)
        fig.put(exx, top, 'snow', 5)
        keep.add((exx, top))
    lobes = [(cx - d * 2, cy - 8, 3), (cx + d * 2, cy - 8, 3),
             (cx - d * 4, cy - 5, 3), (cx, cy - 5, 3), (cx + d * 3, cy - 4, 2),
             (cx - d * 5, cy - 2, 2)]
    curls(fig, lobes, 'snow', (cx, cy - 5, 7, 4))
    return keep


def sleeve(fig, o, pts, cuff_rows=2, hoof_at=None, darker=0):
    m = fig.poly(pts)
    cloth(fig, m, o.knit, lit=1, dark=1, bottom=False)
    if darker:
        for p in m:
            fig.put(p[0], p[1], o.knit, max(1, tone(fig, p) - darker))
    ymax = max(y for x, y in m)
    cuff = {p for p in m if p[1] > ymax - cuff_rows}
    rib(fig, cuff, o.knit)
    if hoof_at:
        x0, y0, w = hoof_at
        fig.fill(fig.rect(x0, y0, x0 + w - 1, y0 + 1), o.hoof, 2)
        fig.put(x0, y0, o.hoof, 3)
        fig.put(x0 + w - 1, y0 + 1, o.hoof, 1)
    return m


# --- option A: crook-staff drover ---------------------------------------------------
def a_staff(fig, o, x, top=22, bot=SOLE, d=1, tilt=0):
    stick(fig, (x, top + 2), (x, bot), notch=3)
    hook = [(x, top + 2), (x + d, top), (x + 2 * d, top - 1), (x + 3 * d, top - 1), (x + 4 * d, top),
            (x + 5 * d, top + 1), (x + 5 * d, top + 2)]
    for i, (hx, hy) in enumerate(hook):
        fig.put(hx, hy, 'timber', 4)
        if i >= 1:
            fig.put(hx, hy + 1, 'timber', 2)
    fig.put(x + 5 * d, top + 3, 'berry', 2)
    fig.put(x + 5 * d, top + 4, 'berry', 2)
    bell(fig, x + 5 * d, top + 5, o.bell, tilt=tilt)


def a_torso_front(fig, o, y_hem=55):
    curls(fig, [(26.5, y_hem + 0.8, 2.3), (30.2, y_hem + 1.6, 2.3), (34, y_hem + 1.6, 2.3), (37.6, y_hem + 0.8, 2.3)],
          'snow', (32, y_hem, 7, 3))
    body = fig.poly([(26, 43), (39, 43), (40.5, y_hem + 1), (23.5, y_hem + 1)])
    cloth(fig, body, o.knit, lit=2, dark=3, folds=(27, 37))
    knit(fig, {p for p in body if p[1] < y_hem - 1}, o.knit, y0=43)
    rib(fig, {p for p in body if p[1] >= y_hem - 1}, o.knit)
    # the open front: fleece chest in a V, the button band, two brass buttons
    curls(fig, [(30.8, 44.6, 1.9), (33.4, 44.6, 1.9), (32.2, 47.0, 1.6)], 'snow', (32, 45, 3, 3))
    for y in range(49, y_hem + 1):
        fig.put(32, y, o.knit, 1)
        fig.put(33, y, o.knit, 2)
    keep = set()
    for y in (50, 53):
        fig.put(31, y, 'brass', 4)
        keep.add((31, y))
    return keep


def option_a(view):
    o = A
    fig = sk.Fig(W, H)
    keep = set()
    if view == 'S':
        legs_front(fig, o)
        a_staff(fig, o, 43)
        keep |= a_torso_front(fig, o)
        sleeve(fig, o, [(24, 43), (28, 43), (27, 52), (23, 52)], hoof_at=(23, 52, 4))
        sleeve(fig, o, [(37, 43), (40, 43), (44, 50), (41, 51)], hoof_at=(41, 49, 3), darker=1)
        fig.put(43, 49, 'timber', 4)
        keep |= head_front(fig, o)
    elif view == 'Sf':
        # counting: she pulls the staff in, tilts her head to it and nicks a fresh notch
        legs_front(fig, o)
        a_staff(fig, o, 38, top=26, tilt=-1)
        keep |= a_torso_front(fig, o)
        sleeve(fig, o, [(24, 43), (28, 43), (34, 47), (31, 50)], hoof_at=(34, 47, 3))
        sleeve(fig, o, [(37, 43), (40, 43), (41, 50), (38, 51)], hoof_at=(38, 50, 3), darker=1)
        # the fresh notch, pale and new
        fig.put(38, 45, 'timber', 5)
        fig.put(39, 45, 'timber', 5)
        keep |= {(38, 45), (39, 45)}
        keep |= head_front(fig, o, dy=1, tilt=1, eyes='down', droop=1)
    else:
        d = 1 if view == 'E' else -1
        legs_side(fig, o, d)
        sx = AX + 7 if d == 1 else AX + 6
        if d == 1:   # E: the staff is in her far (left) hoof, so it stands behind her
            a_staff(fig, o, sx, d=1)
            sleeve(fig, o, [(AX + 2, 44), (AX + 5, 44), (sx + 1, 48), (sx - 1, 50)], hoof_at=(sx - 1, 47, 3), darker=1)
        curls(fig, [(AX - 3.6, 55.8, 2.3), (AX, 56.4, 2.3), (AX + 3.6, 55.8, 2.3)], 'snow', (AX, 54, 6, 3))
        body = fig.poly([(AX - 5, 43), (AX + 6, 43), (AX + 6.5, 56), (AX - 5.5, 56)])
        cloth(fig, body, o.knit, lit=2, dark=3)
        knit(fig, {p for p in body if p[1] < 54}, o.knit, y0=43)
        rib(fig, {p for p in body if p[1] >= 54}, o.knit)
        # her open front edge: a fleece strip and the button band
        fx = AX + 5 if d == 1 else AX - 5
        for y in range(44, 56):
            fig.put(fx, y, o.knit, 2 if d == 1 else 3)
        for y in (50, 53):
            fig.put(fx - d, y, 'brass', 4)
            keep.add((fx - d, y))
        if d == 1:
            sleeve(fig, o, [(AX - 2, 44), (AX + 1, 44), (AX + 1, 52), (AX - 2, 52)], hoof_at=(AX - 2, 52, 3))
        else:        # W: the staff is in her near (left) hoof, trailing at her back
            a_staff(fig, o, sx, d=1)
            sleeve(fig, o, [(AX - 1, 44), (AX + 2, 44), (sx + 1, 50), (sx - 1, 51)], hoof_at=(sx - 1, 49, 3))
            fig.put(sx + 1, 49, 'timber', 2)
        keep |= head_side(fig, o, d)
    fig.outline()
    despeckle(fig, keep)
    return fig


# --- option B: collar-bell puffball -------------------------------------------------
def b_belly_front(fig, cy=53):
    lobes = []
    for row, (yy, xs) in enumerate(((cy - 5, (28, 32, 36)), (cy - 2, (26, 30, 34, 38)),
                                    (cy + 1, (24, 28, 32, 36, 40)), (cy + 4, (26, 30, 34, 38)),
                                    (cy + 6, (30, 34)))):
        for x in xs:
            lobes.append((x, yy, 3))
    curls(fig, lobes, 'snow', (32, cy, 9, 6))


def b_strap_front(fig, o, y=55):
    keep = set()
    xs = [x for x in range(22, 43) if (x, y) in fig.px]
    for x in xs:
        fig.put(x, y, 'timber', 3 if x < 36 else 2)
        fig.put(x, y + 1, 'timber', 2 if x < 36 else 1)
    fig.put(xs[0], y, 'timber', 4)
    # brass buckle
    for p in ((29, y), (30, y), (29, y + 1), (30, y + 1)):
        fig.put(p[0], p[1], 'brass', 4 if p == (29, y) else 2)
    return keep


def option_b(view):
    o = B
    fig = sk.Fig(W, H)
    keep = set()
    if view in ('S', 'Sf'):
        f = view == 'Sf'
        legs_front(fig, o, top=58, xs=(28, 35), width=2)
        # stick tucked into the strap at her left hip, slanting out
        stick(fig, (41, 44), (37, 58), notch=3)
        b_belly_front(fig)
        b_strap_front(fig, o)
        bolero = fig.poly([(25, 43), (39.5, 43), (41, 50), (35, 50), (33.5, 45), (30.5, 45), (29, 50), (23, 50)])
        cloth(fig, bolero, o.knit, lit=2, dark=2)
        knit(fig, {p for p in bolero if p[1] < 49}, o.knit, y0=43)
        rib(fig, {p for p in bolero if p[1] >= 49}, o.knit)
        if not f:
            sleeve(fig, o, [(23, 43), (27, 43), (25, 52), (21, 52)], hoof_at=(21, 52, 4))
            sleeve(fig, o, [(37, 43), (41, 43), (43, 52), (40, 52)], hoof_at=(40, 52, 4), darker=1)
            keep |= head_front(fig, o)
            # collar ribbon and the fold bell at her throat
            for x in range(29, 36):
                fig.put(x, 44, 'sky', 2 if x < 34 else 1)
            bell(fig, 32, 45, o.bell)
        else:
            # counting on her hooves: one hoof up at her chin, the other rings the bell
            sleeve(fig, o, [(37, 43), (41, 43), (39, 49), (36, 49)], hoof_at=(35, 48, 3), darker=1)
            keep |= head_front(fig, o, eyes='closed', tilt=1)
            for x in range(29, 36):
                fig.put(x, 44, 'sky', 2 if x < 34 else 1)
            bell(fig, 33, 45, o.bell, tilt=1)
            # her right hoof up and out, counting: one, two, three
            sleeve(fig, o, [(24, 43), (27, 44), (22, 46), (19, 44)], cuff_rows=2)
            fig.fill(fig.rect(18, 40, 20, 43), 'slate', 3)
            fig.put(18, 40, 'slate', 4)
            fig.put(19, 40, 'slate', 4)
            fig.put(20, 43, 'slate', 1)
            fig.put(19, 41, 'slate', 2)
            fig.put(19, 42, 'slate', 2)
    else:
        d = 1 if view == 'E' else -1
        cx = AX
        legs_side(fig, o, d, top=57, width=2)
        if d == 1:   # E: the stick rides at her far (left) hip, its top shows behind her
            stick(fig, (cx - 6, 45), (cx - 3, 57), notch=3)
        lobes = []
        for (yy, xs) in ((49, (-5, -1, 3)), (52.5, (-7, -3, 1, 5)), (56, (-5, -1, 3)), (58, (-2, 2))):
            for x in xs:
                lobes.append((cx + d * x, yy, 2.6))
        curls(fig, lobes, 'snow', (cx, 53, 8, 6))
        strap = [(x, 55) for x in range(cx - 9, cx + 9) if (x, 55) in fig.px]
        for (x, y) in strap:
            fig.put(x, y, 'timber', 3 if x < cx + 4 else 2)
            fig.put(x, y + 1, 'timber', 2 if x < cx + 4 else 1)
        bolero = fig.poly([(cx - 5, 43), (cx + 5, 43), (cx + 5.5, 50), (cx - 6, 50)])
        cloth(fig, bolero, o.knit, lit=2, dark=2)
        knit(fig, {p for p in bolero if p[1] < 49}, o.knit, y0=43)
        rib(fig, {p for p in bolero if p[1] >= 49}, o.knit)
        if d == -1:  # W: the stick is at her near (left) hip, over the fleece
            stick(fig, (cx + 6, 45), (cx + 3, 57), notch=3)
        sleeve(fig, o, [(cx - 2, 44), (cx + 1, 44), (cx + 1, 52), (cx - 2, 52)], hoof_at=(cx - 2, 52, 3))
        keep |= head_side(fig, o, d)
        fx = cx + d * 4
        for x in range(cx + d * 1, fx + d, d):
            fig.put(x, 44, 'sky', 2)
        bell(fig, fx + d, 45, o.bell)
    fig.outline()
    despeckle(fig, keep)
    return fig


# --- option C: big-cardigan clerk ---------------------------------------------------
def c_coat_front(fig, o, hem=61):
    coat = fig.poly([(25, 43), (39.5, 43), (43.5, hem + 1), (20.5, hem + 1)])
    cloth(fig, coat, o.knit, lit=2, dark=3)
    knit(fig, {p for p in coat if p[1] < hem - 1}, o.knit, y0=43)
    rib(fig, {p for p in coat if p[1] >= hem - 1}, o.knit)
    # the deep shawl collar falls open over a fleece chest
    curls(fig, [(30.6, 44.8, 2.0), (33.6, 44.8, 2.0), (32.2, 47.4, 1.8)], 'snow', (32, 45, 3, 3))
    for (x, y) in ((28, 43), (28, 44), (29, 45), (29, 46), (30, 47), (30, 48), (31, 49)):
        fig.put(x, y, o.knit, 4)
        fig.put(x - 1, y, o.knit, 3)
    for (x, y) in ((36, 43), (36, 44), (35, 45), (35, 46), (34, 47), (34, 48), (33, 49)):
        fig.put(x, y, o.knit, 2)
        fig.put(x + 1, y, o.knit, 1)
    for y in range(50, hem + 1):
        fig.put(32, y, o.knit, 1)
    keep = set()
    # big buttons (timber, 2 x 2, lit corner)
    for by in (51, 55):
        fig.put(33, by, 'brass', 4)
        fig.put(34, by, 'brass', 3)
        fig.put(33, by + 1, 'brass', 3)
        fig.put(34, by + 1, 'brass', 1)
    # patch pockets: a rib lip and a shaded mouth
    for (x0, x1) in ((23, 28), (36, 41)):
        for x in range(x0, x1 + 1):
            fig.put(x, 54, o.knit, 4 if x < x1 else 3)
            fig.put(x, 55, o.knit, 1)
        for y in range(56, 59):
            fig.put(x1 + 1, y, o.knit, 1)
    return keep


def option_c(view):
    o = C
    fig = sk.Fig(W, H)
    keep = set()

    def ear_stick(f):
        stick(f, (43, 27), (37, 36), notch=3)

    if view in ('S', 'Sf'):
        fid = view == 'Sf'
        legs_front(fig, o, top=61, xs=(27, 35))
        keep |= c_coat_front(fig, o)
        if not fid:
            # a tin bell on a cord from the right pocket
            fig.put(40, 56, 'timber', 2)
            fig.put(41, 57, 'timber', 2)
            fig.put(41, 58, 'timber', 2)
            bell(fig, 42, 59, o.bell)
            sleeve(fig, o, [(23, 43), (27, 43), (24, 56), (19, 56)], cuff_rows=3, hoof_at=(20, 56, 3))
            sleeve(fig, o, [(37, 43), (41, 43), (45, 56), (40, 56)], cuff_rows=3, hoof_at=(42, 56, 3), darker=1)
            keep |= head_front(fig, o, before_ears=ear_stick)
        else:
            # the stick comes out from behind her ear; she notches it, tongue out in thought
            fig.put(40, 56, 'timber', 2)
            fig.put(41, 57, 'timber', 2)
            bell(fig, 42, 58, o.bell, tilt=1)
            keep |= head_front(fig, o, dy=1, eyes='down')
            # held up under her chin, slanting, the far end resting in her right hoof
            stick(fig, (41, 42), (29, 50), notch=3)
            sleeve(fig, o, [(23, 43), (27, 43), (31, 49), (27, 51)], cuff_rows=3, hoof_at=(28, 49, 3))
            sleeve(fig, o, [(37, 43), (41, 43), (40, 47), (36, 48)], cuff_rows=3, hoof_at=(36, 45, 3), darker=1)
            # the fresh notch, pale and new, just past her hoof
            fig.put(34, 47, 'timber', 5)
            fig.put(35, 47, 'timber', 5)
            keep |= {(34, 47), (35, 47)}
    else:
        d = 1 if view == 'E' else -1
        cx = AX
        legs_side(fig, o, d, top=61)
        coat = fig.poly([(cx - 6, 43), (cx + 6, 43), (cx + 8.5, 62), (cx - 8.5, 62)])
        cloth(fig, coat, o.knit, lit=2, dark=3)
        knit(fig, {p for p in coat if p[1] < 60}, o.knit, y0=43)
        rib(fig, {p for p in coat if p[1] >= 60}, o.knit)
        fx = cx + d * 6
        for y in range(44, 62):
            fig.put(fx - d * (0 if y < 50 else 1), y, o.knit, 1 if d == 1 else 2)
        for by in (51, 55):
            bx = fx - d * 3
            fig.put(bx, by, 'brass', 4)
            fig.put(bx + 1, by, 'brass', 3)
            fig.put(bx, by + 1, 'brass', 3)
            fig.put(bx + 1, by + 1, 'brass', 1)
        # pocket on the near side; the bell hangs from it
        for x in range(cx - 3, cx + 3):
            fig.put(x, 55, o.knit, 4)
            fig.put(x, 56, o.knit, 1)
        fig.put(cx - d * 3, 57, 'timber', 2)
        bell(fig, cx - d * 3, 57, o.bell)
        sleeve(fig, o, [(cx - 2, 44), (cx + 2, 44), (cx + 2, 54), (cx - 3, 54)], cuff_rows=3, hoof_at=(cx - 2, 54, 3))
        if d == 1:
            # the far ear hides the stick: only its top shows above the crown, behind
            stick(fig, (cx - 6, 26), (cx - 3, 32), notch=0)
            keep |= head_side(fig, o, d)
        else:
            keep |= head_side(fig, o, d)
            stick(fig, (cx + 7, 27), (cx + 2, 36), notch=3)
            # the near ear lies over it
            fig.put(cx + 3, 35, o.face, 3)
            fig.put(cx + 4, 35, o.face, 3)
    fig.outline()
    despeckle(fig, keep)
    return fig


# --- the sheet -----------------------------------------------------------------------
VIEWS = (('S', 'S idle'), ('E', 'E idle'), ('W', 'W idle'), ('Sf', 'S fidget'))

OPTIONS = [
    dict(
        label='A', name='Crook-staff drover: fitted berry knit, fleece under the hem, bell on the crook',
        question='The tally stick is a tall notched crook-staff; the fold bell hangs on its hook.',
        fn=option_a, palette=['snow', 'plaster', 'berry', 'timber', 'brass'],
        pose='Stands square by her staff like a shepherd on watch, chin up, already counting the dusk.',
        parts=[
            'staff (timber, brass bell on berry cord): layer 0 in E (far hoof), 5 in S/W; hand; swings in walk, raised in cheer, a guard bar in fight',
            'legs x2 (plaster, timber hooves): layer 1; hip; 6-frame swing, tuck in hop and nap',
            'fleece hem (snow curls): layer 2; hip; bobs 1 px a step',
            'cardigan torso (berry knit, rib hem, brass buttons): layer 3; hip; breath 1 px',
            'sleeves x2 (berry, timber hooves): far 1 tone back, layer 2/4; chest; swing, wind-up, cast',
            'head (plaster face, ears, snow crown): layer 6; chest; tilts in fidget, ears droop in nap',
            'ears x2 (plaster, berry inner): layer 5; head; flop on hop and hit',
        ],
        notes=[
            'Works: the tall crook gives the cast its only vertical prop line, so she reads at 2 px even beside Tam and Puffcap.',
            'Knit vs fleece: knit rows of 2 px dashes in berry, curls in snow at the crown, chest V and under the hem.',
            'Risk: the staff doubles the cell width in fights and walk frames; E holds it behind, W at her back.',
            'Compared with Eastward 05 (curly-haired woman, Sam): curls as 4-6 px lobes with lit caps, 3 tones a lobe.',
        ]),
    dict(
        label='B', name='Collar-bell puffball: black-faced lamb, cropped sky knit, round fleece belly',
        question='A short tally stick tucked in a strap at her hip; the bell on a collar ribbon at her throat.',
        fn=option_b, palette=['snow', 'slate', 'sky', 'timber', 'brass'],
        pose='A round, busy little lamb, hooves together, ready to trot off after a stray.',
        parts=[
            'legs x2 (slate, thin, slate hooves): layer 1; hip; quick 6-frame trot, tucked in nap',
            'fleece belly (snow curls, timber strap, brass buckle): layer 2; hip; squash 1 px on hop',
            'tally stick (timber): layer 1 in E, 3 in S/W; hip strap; jiggles on walk, drawn as a blade in strike',
            'bolero (sky knit, rib edge): layer 3; chest; breath',
            'sleeves x2 (sky, slate hooves): layer 2/4; chest; count, wind-up, guard',
            'bell (brass, sky ribbon): layer 5; chest; swings a step behind the body, rings in fidget and cast',
            'head (slate face, pale lower eye rims, slate ears, snow crown): layer 6; chest',
        ],
        notes=[
            'Works: the black face and legs against a white puffball read in two values at any size, and nobody else is round.',
            'Knit vs fleece: the knit is only a short sky bolero, so most of the body is fleece; the two meet in one clear line.',
            'Risk: on a black face the eyes need a pale lower rim and glint to read; the stick at the hip is small and hides in E.',
            'Compared with Eastward 05: the curly-haired woman\'s hair mass, here scaled to the whole belly.',
        ]),
    dict(
        label='C', name='Big-cardigan clerk: oversized clay knit to the knees, stick behind the ear',
        question='The tally stick rides behind her ear like a pencil; the brass fold bell hangs on a cord from her pocket.',
        fn=option_c, palette=['snow', 'plaster', 'clay', 'timber', 'brass'],
        pose='Swamped in a hand-me-down cardigan, sleeves rolled, a fussy little clerk of the flock.',
        parts=[
            'legs x2 (plaster stubs, timber hooves): layer 1; hip; short steps, the hem hides most of the swing',
            'cardigan coat (clay knit, brass buttons, patch pockets): layer 2; hip; the hem sways 1 px after each step',
            'bell (brass, on a timber cord from the pocket): layer 3; hip; swings and settles a frame late',
            'sleeves x2 (clay, rolled rib cuffs, timber hooves): layer 2/4; chest; flap in cheer and cast',
            'tally stick (timber): behind the ear, layer 5 (W), 0 (E); head; comes to the hoof in fidget and cast',
            'head (plaster face, ears, snow crown): layer 6; chest',
        ],
        notes=[
            'Works: the A-line coat makes a triangle no other folk has, and the big brass buttons and pockets read at 2 px.',
            'Knit vs fleece: a lot of knit, so the knit rows carry the material; fleece shows at the crown and the chest.',
            'Risk: legs vanish under the hem, so the walk leans on the hem sway; clay knit must stay apart from Bramble\'s fox-clay fur.',
            'Compared with Eastward 05: the woman in the purple cardigan (buttons, a placket line and a hem row at this height).',
        ]),
]


# =====================================================================================
# FINAL (revision round, 21 Oct): option B, the collar-bell puffball, with grafts.
#   - from C: the tally stick rides behind her LEFT ear like a pencil (anchored to the
#     head in every facing); it comes to the hoof only for the fidget and the cast.
#   - from C: a real cardigan, round over the fleece, to mid-thigh, with a button band.
#   - the knit moves from sky (Bramble's) to berry, drawn as rib columns, not dashes.
#   - eyes that read on the black face: a pale lower lid, a 2 px glint, a berry blush.
#   - profiles drawn as forms: brow, cheek and a snout step, lit from the upper left.
#   - the collar bell stays at her throat.
# =====================================================================================
F = Opt('final', 'slate', 'berry', 'slate', 'slate', 'brass', 'slate', ('slate', 0))
FAM_STICK = 'timber'


def rib_knit(fig, mask, fam, phase=0):
    """Knit as rib columns (house-style 5): every third column sits a tone down, so the
    cardigan reads as knitted ribs running down the body, never as brick."""
    for (x, y) in mask:
        if (x + phase) % 3 == 2 and fam_at(fig, (x, y)) == fam:
            t = tone(fig, (x, y))
            if t is not None and t >= 2:
                fig.put(x, y, fam, t - 1)


def thick(fig, a, b, w=3):
    """A limb as a filled quad of width w from point a to point b."""
    (x0, y0), (x1, y1) = a, b
    dx, dy = x1 - x0, y1 - y0
    n = max(1e-6, (dx * dx + dy * dy) ** 0.5)
    px, py = -dy / n * w / 2, dx / n * w / 2
    return fig.poly([(x0 + px, y0 + py), (x1 + px, y1 + py), (x1 - px, y1 - py), (x0 - px, y0 - py)]) | \
        fig.rect(round(x1 - w / 2), round(y1 - w / 2), round(x1 - w / 2) + w - 1, round(y1 - w / 2) + w - 1)


def f_limb(fig, a, b, fam, hoof=True, far=False, w=3, hoof_fam='slate'):
    """A sleeve (or a leg) with a hoof at its end; the far limb sits a tone back."""
    m = thick(fig, a, b, w)
    under = {}
    for (x, y) in m:   # the sleeve casts a seam shadow on the body beside and below it
        for q in ((x + 1, y), (x, y + 1), (x - 1, y)):
            if q not in m and fam_at(fig, q) == fam:
                under[q] = 1 if q[0] > x or q[1] > y else 2
    for q, t in under.items():
        fig.put(q[0], q[1], fam, t)
    cloth(fig, m, fam, lit=1, dark=1, top=True, bottom=False)
    if far:
        for p in m:
            fig.put(p[0], p[1], fam, max(1, tone(fig, p) - 1))
    if hoof:
        hx, hy = round(b[0]) - 1, round(b[1]) - 1
        h = fig.rect(hx, hy, hx + 2, hy + 1)
        fig.fill(h, hoof_fam, 2 if not far else 1)
        fig.put(hx, hy, hoof_fam, 3 if not far else 2)
        fig.put(hx + 2, hy + 1, hoof_fam, 1)
    return m


def f_eye(fig, x, y, keep, shape='open', w=3):
    """Black-face eye: ink 3 x 2, a 2 px glint on its top row, a pale lower lid."""
    if shape == 'open':
        for dx in range(w):
            for dy in range(3):
                fig.put(x + dx, y + dy - 1, 'ink', 0)
            fig.put(x + dx, y + 2, 'snow_cool', 3)
        fig.put(x, y - 1, 'snow', 5)
        fig.put(x, y, 'snow', 5)
        keep |= {(x, y - 1), (x, y)} | {(x + dx, y + 2) for dx in range(w)}
    elif shape == 'down':   # looking down at the stick: a heavy lid, the eye below it
        for dx in range(w):
            fig.put(x + dx, y + 1, 'ink', 0)
            fig.put(x + dx, y + 2, 'snow_cool', 3)
        fig.put(x, y + 1, 'snow', 5)
        fig.put(x + 1, y + 1, 'snow', 5)
        keep |= {(x, y + 1), (x + 1, y + 1)} | {(x + dx, y + 2) for dx in range(w)}
    else:                   # closed: a happy pale arc (or squeezed shut on a hit)
        up = shape == 'closed'
        for dx in range(w):
            fig.put(x + dx, y + (1 if up else 0) - (1 if up and dx == 1 else 0) + (0 if up else (1 if dx == 1 else 0)),
                    'snow_cool', 3)
        keep |= {(x + dx, y + yy) for dx in range(w) for yy in (-1, 0, 1, 2)}
    return keep


def f_head_front(fig, cy, keep, tilt=0, eyes='open', stick_on=True, droop=0):
    o = F
    if stick_on:   # behind her LEFT ear (screen right in S), poking up and out
        stick(fig, (43 + tilt, 27 + (cy - 38)), (38 + tilt, 36 + (cy - 38)), notch=3)
    ears_front(fig, o, cy, tilt, droop)
    face = fig.ellipse(32 + tilt, cy, 6.5, 5.6)
    pillow(fig, face, 'slate')
    # muzzle: a raised pillow (lit top row) over the lower face
    muz = fig.ellipse(32 + tilt, cy + 3, 3.4, 2.1)
    for (x, y) in muz:
        if (x, y) in face:
            fig.put(x, y, 'slate', 4 if y == min(q[1] for q in muz if q[0] == x) and x < 33 + tilt else 3)
    for p in ((31, cy + 3), (32, cy + 3), (33, cy + 3), (32, cy + 4)):
        fig.put(p[0] + tilt, p[1], 'slate', 0)
    # a berry blush under each eye: the warm expression
    for bx in (26 + tilt, 37 + tilt):
        fig.put(bx, cy + 2, 'berry', 4)
        fig.put(bx + 1, cy + 2, 'berry', 4)
        keep |= {(bx, cy + 2), (bx + 1, cy + 2)}
    for ex in (27 + tilt, 35 + tilt):
        f_eye(fig, ex, cy - 2, keep, eyes)
    crown_front(fig, cy, tilt)
    return keep


def f_head_side(fig, d, hx, hy, keep, eyes='open', stick_on=True, look=0, ear_lift=0):
    """Profile as a form: a skull pillow, a brow ridge under the curls, an eye with a pale
    lower lid, a cheek shadow, and the snout as its own pillow one step forward."""
    cx, cy = hx, hy
    if stick_on and d == 1:   # E: her left ear is the far one; the stick shows behind
        stick(fig, (cx - 6, 26 + (cy - 38)), (cx - 2, 33 + (cy - 38)), notch=3)
    ex = cx - d * 2
    if d == 1:
        ear = fig.poly([(ex, cy - 3), (ex - 7, cy + 1 - ear_lift), (ex - 6, cy + 3 - ear_lift), (ex + 1, cy + 1)])
    else:
        ear = fig.poly([(ex + 1, cy - 3), (ex + 8, cy + 1 - ear_lift), (ex + 7, cy + 3 - ear_lift), (ex, cy + 1)])
    colsy = {}
    for (x, y) in ear:
        colsy.setdefault(x, []).append(y)
    for (x, y) in ear:
        t = 3 if d == -1 else 2
        if y == min(colsy[x]):
            t += 1
        elif y == max(colsy[x]):
            t = 1
        fig.put(x, y, 'slate', t)
    skull = fig.ellipse(cx - d * 0.5, cy, 5.6, 5.4)
    pillow(fig, skull, 'slate')
    snout = fig.ellipse(cx + d * 4.6, cy + 2 + look, 3.2, 2.5)
    for (x, y) in snout:
        col = [q[1] for q in snout if q[0] == x]
        t = 3
        if y == min(col):
            t = 4                    # the bridge of the nose catches the light
        elif y == max(col):
            t = 1
        elif d == 1 and x == max(q[0] for q in snout):
            t = 2
        fig.put(x, y, 'slate', t)
    # the snout step: a shade line where the snout meets the cheek
    sx = round(cx + d * 1.6)
    for y in range(cy + 1 + look, cy + 4 + look):
        if (sx, y) in skull:
            fig.put(sx, y, 'slate', 2)
    tip = max(x for x, y in snout) if d == 1 else min(x for x, y in snout)
    fig.put(tip, cy + 1 + look, 'slate', 0)
    fig.put(tip, cy + 2 + look, 'slate', 0)
    # cheek shadow under the eye, blush on it
    ex0 = cx + (1 if d == 1 else -3)
    fig.put(ex0, cy + 2, 'berry', 4)
    fig.put(ex0 + 1, cy + 2, 'berry', 4)
    keep |= {(ex0, cy + 2), (ex0 + 1, cy + 2)}
    # brow ridge above the eye
    fig.put(ex0, cy - 3, 'slate', 4)
    fig.put(ex0 + 1, cy - 3, 'slate', 4)
    f_eye(fig, ex0, cy - 2, keep, eyes, w=2)
    lobes = [(cx - d * 2, cy - 8, 3), (cx + d * 2, cy - 8, 3),
             (cx - d * 4, cy - 5, 3), (cx, cy - 5, 3), (cx + d * 3, cy - 4, 2),
             (cx - d * 5, cy - 2, 2)]
    if d == 1:   # facing east, the front of her crown turns away from the light
        curls(fig, [l for l in lobes if l[0] <= cx], 'snow', (cx, cy - 5, 7, 4))
        curls(fig, [l for l in lobes if l[0] > cx], 'snow', (cx, cy - 5, 7, 4), bias=-1)
    else:
        curls(fig, lobes, 'snow', (cx, cy - 5, 7, 4))
    if stick_on and d == -1:  # W: her left ear is the near one; the stick lies over it
        stick(fig, (cx + 7, 27 + (cy - 38)), (cx + 2, 35 + (cy - 38)), notch=3)
        fig.put(cx + 3, cy - 2, 'slate', 3)
        fig.put(cx + 4, cy - 2, 'slate', 3)
    return keep


def f_body_front(fig, cy=51.5, rx=9.5, ry=7.6, hem=58):
    """The round cardigan over the fleece: two berry rib fronts falling open from the
    collar over a broad fleece belly, a button band on each edge (brass buttons on her
    right), a ribbed hem at mid-thigh."""
    coat = {p for p in fig.ellipse(32, cy, rx, ry) if 43 <= p[1] <= hem}
    pillow(fig, coat, 'berry')
    rib_knit(fig, coat, 'berry')
    rib(fig, {p for p in coat if p[1] >= hem - 1}, 'berry')
    opening = set()
    for y in range(45, hem + 1):
        hw = min(4, 0.6 + (y - 45) * 0.55) if y < 53 else max(2.5, 4 - (y - 53) * 0.35)
        for x in range(32 - int(hw), 32 + int(hw) + 1):
            opening.add((x, y))
    for (x, y) in opening:
        fig.put(x, y, 'snow', 3)
    rows = {}
    for (x, y) in opening:
        rows.setdefault(y, []).append(x)
    for y, xs in rows.items():
        fig.put(min(xs) - 1, y, 'berry', 4)
        fig.put(max(xs) + 1, y, 'berry', 1)
    # the fleece belly puffs out of the opening and a little below the hem
    lobes = [(32, 47, 2), (30, 50, 3), (34, 50, 3), (32, 53, 3), (29.5, 56, 3), (34.5, 56, 3), (32, 59, 3)]
    curls(fig, lobes, 'snow', (32, 52, 4, 6))
    keep = set()
    for by in (48, 52):
        xl = min(rows[by]) - 2
        fig.put(xl, by, 'brass', 4)
        fig.put(xl, by + 1, 'brass', 3)
        keep |= {(xl, by), (xl, by + 1)}
    return keep


def f_collar(fig, x0, x1, y, bx, by, tilt=0):
    for x in range(x0, x1 + 1):
        fig.put(x, y, 'timber', 3 if x < (x0 + x1) // 2 else 2)
    bell(fig, bx, by, 'brass', tilt=tilt)


def mossling(fig, cx, base, d, keep, curled=False):
    """Stand-in familiar (24 art px): a round leaf-green blob, two ink eyes, a sprout."""
    if curled:
        body = fig.ellipse(cx, base - 5, 7.5, 5.5)
        pillow(fig, body, 'leaf')
        for x in (cx - 3, cx + 1):
            fig.put(x, base - 6, 'ink', 0)
            fig.put(x + 1, base - 6, 'ink', 0)
        for (x, y, t) in ((cx + 4, base - 11, 4), (cx + 5, base - 11, 4), (cx + 6, base - 10, 3), (cx + 5, base - 12, 4)):
            fig.put(x, y, 'leaf_warm', t)
        return keep
    body = fig.ellipse(cx, base - 9, 8, 9)
    pillow(fig, body, 'leaf')
    ey = base - 11
    for ex in ((cx, cx + 4) if d == 1 else (cx - 5, cx - 1)):
        fig.put(ex, ey, 'ink', 0)
        fig.put(ex + 1, ey, 'ink', 0)
        fig.put(ex, ey + 1, 'ink', 0)
        fig.put(ex + 1, ey + 1, 'ink', 0)
    # sprout: a stem and two leaves
    top = base - 18
    fig.put(cx, top, 'leaf_warm', 3)
    fig.put(cx, top - 1, 'leaf_warm', 3)
    for (x, y, t) in ((cx - 1, top - 2, 4), (cx - 2, top - 2, 4), (cx - 2, top - 3, 4),
                      (cx + 1, top - 2, 3), (cx + 2, top - 2, 2), (cx + 2, top - 3, 3)):
        fig.put(x, y, 'leaf_warm', t)
    return keep


def final_front(view):
    fig = sk.Fig(W, H)
    keep = set()
    legs_front(fig, F, top=58, xs=(28, 35), width=2)
    keep |= f_body_front(fig)
    if view == 'S':
        f_limb(fig, (24, 45), (21, 54), 'berry')
        f_limb(fig, (40, 45), (43, 54), 'berry', far=True)
        for y in range(47, 53):
            fig.put(24 if y < 50 else 23, y, 'berry', 1)
            fig.put(40 if y < 50 else 41, y, 'berry', 1)
        keep = f_head_front(fig, 38, keep)
        f_collar(fig, 29, 35, 44, 32, 45)
    else:   # fidget: counting. The stick comes from behind her ear to her left hoof;
        # she peers down at it and nicks a fresh notch, her right hoof taps the bell.
        keep = f_head_front(fig, 39, keep, tilt=-1, eyes='down', stick_on=False, droop=1)
        f_collar(fig, 29, 35, 45, 32, 46, tilt=1)
        stick(fig, (41, 35), (41, 47), notch=3)
        fig.put(41, 41, 'timber', 5)
        fig.put(42, 41, 'timber', 5)
        keep |= {(41, 41), (42, 41)}
        f_limb(fig, (40, 46), (41, 48), 'berry', far=True)
        f_limb(fig, (24, 46), (29, 49), 'berry')
    fig.outline()
    despeckle(fig, keep)
    despeckle(fig, keep)
    return fig


POSES = {
    #          body x/y  head x/y   legs        near hand      far hand     eyes      stick   bell
    'idle':   (0, 0,     1, 0,     'stand',    (0, 53),       None,        'open',   'ear',  0),
    'ready':  (0, 1,     2, 0,     'wide',     (5, 47),       (3, 46),     'open',   'ear',  0),
    'strike': (3, 1,     6, 4,     'lunge',    (-6, 50),      (-5, 49),    'open',   'ear',  -1),
    'cast':   (0, 0,     -1, -1,   'wide',     (9, 39),       (4, 47),     'open',   'hand', 1),
    'hit':    (-3, 0,    -4, -1,   'stumble',  (4, 42),       (3, 44),     'squeeze', 'ear', -1),
    'sit':    (0, 6,     1, 0,     'sit',      (4, 55),       (3, 55),     'down',   'ear',  0),
    'cheer':  (0, -4,    -1, -1,   'jump',     (8, 35),       (-5, 34),    'closed', 'ear',  1),
}


def final_side(d, pose, familiar=False):
    bx, by, hx, hy, legs, near, far, eyes, stk, btilt = POSES[pose]
    fig = sk.Fig(W, H)
    keep = set()
    cx = AX + d * bx
    U = lambda u: cx + d * u   # noqa: E731  (forward is +u in either facing)
    perch = None
    if familiar:
        # the far shoulder, away from the foe: x smaller in E, larger in W
        perch = (round(U(-5)), 44 + by)
        mossling(fig, perch[0] - d * 5, perch[1] + 1, d, keep)
    # far arm, far leg (a tone back), drawn first
    if far:
        f_limb(fig, (U(-1), 45 + by), (U(far[0]), far[1] + (by if pose not in ('cheer', 'cast') else 0)), 'berry', far=True)
    hip = 58 + by
    if legs == 'stand':
        lg = [((-3, hip), (-3, SOLE - 1)), ((1, hip), (1, SOLE - 1))]
    elif legs == 'wide':
        lg = [((-3, hip), (-5, SOLE - 1)), ((1, hip), (3, SOLE - 1))]
    elif legs == 'lunge':
        lg = [((-2, hip), (-7, SOLE - 1)), ((2, hip), (6, SOLE - 1))]
    elif legs == 'stumble':
        lg = [((-2, hip), (-5, SOLE - 1)), ((1, hip), (5, SOLE - 3))]
    elif legs == 'sit':
        lg = [((2, hip - 3), (8, hip - 1)), ((4, hip - 2), (10, hip))]
    else:  # jump: legs tucked
        lg = [((-2, hip), (-3, hip + 4)), ((1, hip), (3, hip + 4))]
    if legs != 'sit':
        for i, (a, b) in enumerate(lg):
            f_limb(fig, (U(a[0]), a[1]), (U(b[0]), b[1]), 'slate', far=(i == 0), w=2, hoof_fam='slate')
    # round body: cardigan over fleece, the open front showing curls
    bcy = 51.5 + by
    coat = {p for p in fig.ellipse(cx, bcy, 8, 7.5) if 43 + by <= p[1] <= 58 + by}
    pillow(fig, coat, 'berry')
    rib_knit(fig, coat, 'berry')
    rib(fig, {p for p in coat if p[1] >= 57 + by}, 'berry')
    # in profile the cardigan wraps the round body; the fleece curls out under the hem
    curls(fig, [(U(-4), 58 + by, 3), (U(0), 59 + by, 3), (U(4), 58 + by, 3)], 'snow', (cx, 56 + by, 6, 3))
    for y in range(46 + by, 58 + by):
        e = round(U(4))
        if (e, y) in coat:
            fig.put(e, y, 'berry', 1 if d == 1 else 4)
    for yy in (49, 53):
        bxp = round(U(3))
        fig.put(bxp, yy + by, 'brass', 4)
        fig.put(bxp, yy + by + 1, 'brass', 3)
        keep |= {(bxp, yy + by), (bxp, yy + by + 1)}
    if legs == 'sit':   # sitting: both legs stick out in front, over the hem
        for i, (a, b) in enumerate(lg):
            f_limb(fig, (U(a[0]), a[1]), (U(b[0]), b[1]), 'slate', far=(i == 0), w=2, hoof_fam='slate')
    keep = f_head_side(fig, d, round(U(hx)), 38 + by + hy, keep, eyes=eyes, stick_on=(stk == 'ear'),
                       look=1 if pose == 'strike' else 0, ear_lift=2 if pose in ('hit', 'cheer') else 0)
    f_collar(fig, round(min(U(1), U(5))), round(max(U(1), U(5))), 44 + by, round(U(5)), 45 + by, tilt=btilt * d)
    # near arm last
    hand = (U(near[0]), near[1] + (by if pose not in ('cheer', 'cast') else 0))
    if stk == 'hand':   # cast: the stick held high, notch-side out
        stick(fig, (round(hand[0]), round(hand[1]) - 9), (round(hand[0]), round(hand[1]) + 1), notch=3)
        fig.put(round(hand[0]), round(hand[1]) - 6, 'timber', 5)
        fig.put(round(hand[0]) + 1, round(hand[1]) - 6, 'timber', 5)
        keep |= {(round(hand[0]), round(hand[1]) - 6), (round(hand[0]) + 1, round(hand[1]) - 6)}
    f_limb(fig, (U(0), 45 + by), hand, 'berry')
    fig.outline()
    despeckle(fig, keep)
    despeckle(fig, keep)
    return fig, perch


def final_nap():
    fig = sk.Fig(W, H)
    keep = set()
    # the familiar curled against her back, right side
    mossling(fig, 46, SOLE + 1, 1, keep, curled=True)
    # body: a curled round of cardigan, the fleece crown of her back showing on top
    coat = fig.ellipse(33, 58.5, 12, 7)
    pillow(fig, coat, 'berry')
    rib_knit(fig, coat, 'berry')
    curls(fig, [(30, 53, 3), (34, 52, 3), (38, 53, 3)], 'snow', (34, 53, 6, 2))
    # tucked hooves at the front
    for x0 in (27, 31):
        fig.fill(fig.rect(x0, 63, x0 + 2, 64), 'slate', 2)
        fig.put(x0, 63, 'slate', 3)
    # head resting low at the left, eyes shut, an ear flopped down, the stick still tucked
    hx, hy = 21, 58
    stick(fig, (18, 49), (22, 55), notch=3)
    ear = fig.poly([(23, 58), (28, 61), (27, 63), (22, 60)])
    for (x, y) in ear:
        fig.put(x, y, 'slate', 2 if y > 60 else 3)
    face = fig.ellipse(hx, hy, 5.5, 4.6)
    pillow(fig, face, 'slate')
    snout = fig.ellipse(hx - 3.5, hy + 2, 2.6, 2.1)
    for (x, y) in snout:
        fig.put(x, y, 'slate', 4 if y == min(q[1] for q in snout if q[0] == x) else 3)
    fig.put(min(x for x, y in snout), hy + 2, 'slate', 0)
    for dx in range(2):
        fig.put(19 + dx, hy - 1, 'snow_cool', 3)
    fig.put(21, hy - 2, 'snow_cool', 3)
    keep |= {(19, hy - 1), (20, hy - 1), (21, hy - 2)}
    fig.put(21, hy + 1, 'berry', 4)
    fig.put(22, hy + 1, 'berry', 4)
    keep |= {(21, hy + 1), (22, hy + 1)}
    curls(fig, [(20, hy - 5, 3), (24, hy - 4, 2), (17, hy - 3, 2)], 'snow', (20, hy - 5, 5, 3))
    f_collar(fig, 24, 27, 61, 26, 61, tilt=1)
    fig.outline()
    despeckle(fig, keep)
    despeckle(fig, keep)
    return fig


FINAL_VIEWS = (
    ('S idle', lambda: (final_front('S'), None)),
    ('E idle', lambda: final_side(1, 'idle')),
    ('W idle', lambda: final_side(-1, 'idle')),
    ('S fidget', lambda: (final_front('Sf'), None)),
    ('nap S', lambda: (final_nap(), None)),
    ('E ready', lambda: final_side(1, 'ready', True)),
    ('E strike', lambda: final_side(1, 'strike', True)),
    ('E cast', lambda: final_side(1, 'cast', True)),
    ('E hit', lambda: final_side(1, 'hit', True)),
    ('E sit', lambda: final_side(1, 'sit', True)),
    ('E cheer', lambda: final_side(1, 'cheer', True)),
    ('W ready', lambda: final_side(-1, 'ready', True)),
    ('W strike', lambda: final_side(-1, 'strike', True)),
)

FINAL = dict(
    label='B final', name='Collar-bell puffball (final): black-faced lamb, round berry cardigan, stick behind the ear',
    chosen='B',
    grafts=[
        'From C: the tally stick tucked behind her left ear like a pencil, anchored to the head in every facing; '
        'it comes to the hoof only for the fidget and the cast.',
        'From C: a real cardigan, round over the fleece, to mid-thigh, open down the front with a button band '
        '(three brass buttons) and a ribbed hem.',
        'Cast-wide: the knit moves from sky (Bramble\'s) to berry, drawn as rib columns.',
        'Eyes on the black face: ink 3 x 2 (2 x 2 in profile), a 2 px glint, a pale lower lid, a berry blush.',
        'Kept from B: the collar bell at her throat, the round fleece silhouette, the thin slate legs.',
    ],
    palette=['snow', 'slate', 'berry', 'timber', 'brass'],
    pose='A round, busy little lamb, hooves at her sides, ready to trot off after a stray; she headbutts in a fight.',
    parts=[
        'familiar perch: back shoulder (E: x smaller, W: x larger), behind the head; layer 0; chest',
        'far leg / far sleeve (slate / berry, a tone back): layer 1; hip / chest; all facings',
        'near leg (slate, thin, slate hoof): layer 2; hip; 6-frame trot, tucked in hop and nap, forward in sit',
        'cardigan body (berry rib, open front, brass buttons, rib hem) over the fleece belly (snow curls): '
        'layer 3; hip; breath 1 px, squash 1 px on hop; the opening moves to the front edge in E/W',
        'head (slate face, pale lower lids, berry blush, slate ears, snow crown): layer 4; chest; '
        'leads the strike (a headbutt), tilts in the fidget, ears lift on hit and cheer',
        'tally stick (timber, notched): layer 3.5 behind the LEFT ear (S: screen right; E: behind the head; '
        'W: over the near ear); head; to the near hoof in fidget and cast',
        'collar bell (brass on a timber strap): layer 5; chest; a free pendulum a frame behind the body, rings in fidget and cast',
        'near sleeve (berry rib, slate hoof): layer 6; chest; swing, guard, reach, raise',
    ],
    notes=[
        'Compared side by side with Eastward 05 at the same height: the curly-haired woman (curls as lobes with a lit '
        'cap and dark crescent) and the woman in the purple cardigan (placket, buttons, hem row).',
        'Works: the black face and legs against a white crown and a round berry body read in two values; '
        'nobody else in the cast is round, and the stick on the head reads in every facing.',
        'Strike is a headbutt (head leads, hooves back): sheep-like and keeps the stick out of the swing.',
        'Open: whether the stick should also come to the hoof for strike, and the bell\'s ring effect frames.',
    ],
)


def height(im):
    a = im.getchannel('A')
    ys = [y for y in range(im.height) if any(a.getpixel((x, y)) for x in range(im.width))]
    return ys[-1] - ys[0] + 1 if ys else 0


def build_final():
    views, nums, perches, ok = [], {}, {}, True
    for cap, fn in FINAL_VIEWS:
        fig, perch = fn()
        im = fig.image()
        views.append((cap, im))
        im.save(os.path.join(SCRATCH, 'final-' + cap.replace(' ', '-') + '.png'))
        m = sk.measure(im)
        g = dict(on_house=m['on_house'] >= 1.0, west_east=m['west_east'] > 0, lone=m['isolated'] <= 0.04,
                 colours=m['colours'] <= 64, outline_dark=m.get('outline_dark', 0) >= 0.95)
        ok &= all(g.values())
        print(f"final {cap:9s} h {height(im):2d}  on house {100*m['on_house']:5.1f}%  W-E {m['west_east']:+5.1f}  "
              f"lone {100*m['isolated']:4.1f}%  colours {m['colours']:2d}  outline dark {100*m.get('outline_dark', 0):5.1f}%"
              f"  {'ok' if all(g.values()) else 'MISS ' + ','.join(k for k, b in g.items() if not b)}")
        nums[cap] = {k: (round(v2, 4) if isinstance(v2, float) else v2) for k, v2 in m.items()}
        nums[cap]['height_px'] = height(im)
        if perch:
            perches[cap] = list(perch)
    entry = dict(label=FINAL['label'], name=FINAL['name'], views=views, parts=FINAL['parts'],
                 palette=FINAL['palette'], pose=FINAL['pose'], notes=FINAL['notes'])
    sk.design_sheet('Tally final (folk 4, the Brackens): B, the collar-bell puffball, with grafts', [entry], OUT_FINAL,
                    note='40 art px, cell 64 x 72, foot (32, 66). World S/E/W, fidget, nap; fight E and W with the '
                         'stand-in Mossling on the back shoulder.')
    return dict(chosen=FINAL['chosen'], name=FINAL['name'], grafts=FINAL['grafts'], parts=FINAL['parts'],
                palette=FINAL['palette'], pose=FINAL['pose'], perch_anchor=perches, measure=nums,
                notes=FINAL['notes'], _ok=ok)


def main():
    os.makedirs(SCRATCH, exist_ok=True)
    out = []
    ok = True
    for o in OPTIONS:
        o['views'] = []
        nums = {}
        for v, cap in VIEWS:
            im = o['fn'](v).image()
            o['views'].append((cap, im))
            im.save(os.path.join(SCRATCH, f"{o['label']}-{cap.replace(' ', '-')}.png"))
            m = sk.measure(im)
            g = dict(on_house=m['on_house'] >= 1.0, west_east=m['west_east'] > 0, lone=m['isolated'] <= 0.06,
                     colours=m['colours'] <= 64, outline_dark=m.get('outline_dark', 0) >= 0.95)
            ok &= all(g.values())
            print(f"{o['label']} {cap:9s} on house {100*m['on_house']:5.1f}%  W-E {m['west_east']:+5.1f}  "
                  f"lone {100*m['isolated']:4.1f}%  colours {m['colours']:2d}  outline dark {100*m.get('outline_dark', 0):5.1f}%"
                  f"  {'ok' if all(g.values()) else 'MISS ' + ','.join(k for k, b in g.items() if not b)}")
            nums[cap] = {k: (round(v2, 4) if isinstance(v2, float) else v2) for k, v2 in m.items()}
        out.append(dict(label=o['label'], name=o['name'], question=o['question'], parts=o['parts'],
                        palette=o['palette'], pose=o['pose'], notes=o['notes'], measure=nums))
    sk.design_sheet('Tally (folk 4, the Brackens): lamb and cardigan, tally stick and fold bell', OPTIONS, OUT_PNG,
                    note='40 art px, cell 64 x 72, foot (32, 66). Views: S, E, W idle and the S fidget key pose (counting).')
    final = build_final()
    ok &= final.pop('_ok')
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, 'w') as f:
        json.dump(dict(id='tally', height_art_px=40, cell=[W, H], foot=[AX, AY],
                       question='Lamb and cardigan: how the knit reads against natural fleece, and how she carries '
                                'the tally stick and bell.',
                       options=out, final=final), f, indent=2)
    print('gates', 'ok' if ok else 'MISS')


if __name__ == '__main__':
    main()
