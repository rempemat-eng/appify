"""Puddle design options (Claude J folk sheets, 21 Oct): the oilskin cut and how much frog shows.

Puddle (id `puddle`): a frog in fisherman's oilskins and red wellies, the bargee's apprentice
on the Lull (night 6). Trickster, passive Tide. 36 art px tall (18 world). Cell 56 x 60,
foot anchor (28, 54).

    A  Sou'wester and long coat: only the wide frog face and the red wellies show.
    B  Short smock and a rolled net: bare green arms and legs, eye bumps on top.
    C  Dungaree waders and a tin bucket: bare green head, arms and chest, oilskin to the chest.

Run from the repo root:  python3 scripts/art/characters/designs/puddle.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sheetkit as sk  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
OUT_PNG = os.path.join(REPO, 'docs', 'vision', 'characters', 'designs', 'puddle-options.png')
OUT_JSON = os.path.join(REPO, 'docs', 'vision', 'characters', 'designs', 'puddle.json')
SCRATCH = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '.char-views')), 'puddle')

W, H = 56, 60
AX, AY = 28, 54          # foot anchor: boot soles sit on row 53, the outline on 54

SKIN, BELLY, OIL, BOOT = 'leaf', 'plaster', 'brass_warm', 'berry'


# --- helpers -----------------------------------------------------------------------
def part(fig, mask, fam, **kw):
    fig.shade(mask, fam, **kw)
    return set(mask)


def keep(fig, *pts):
    """Pixels that may stand alone on purpose: eye glints, rivets, toggles, a nostril."""
    if not hasattr(fig, 'keep'):
        fig.keep = set()
    fig.keep.update(pts)


def despeckle(fig, passes=2):
    """Paint over lone pixels the shading leaves at part edges (house-style 4): each takes
    its neighbours' commonest colour, its own family first. Kept pixels and ink stay."""
    kept = getattr(fig, 'keep', set())
    for _ in range(passes):
        changes = {}
        for (x, y), v in fig.px.items():
            if v[0] == 'ink' or (x, y) in kept or (x, y) in fig.fixed:
                continue
            nb = [fig.px.get((x + dx, y + dy)) for dx, dy in sk.N4]
            if None in nb or any(n == v for n in nb):
                continue
            same = [n for n in nb if n[0] == v[0] and n[0] != 'ink']
            pool = same or [n for n in nb if n[0] != 'ink']
            if pool:
                changes[(x, y)] = max(sorted(set(pool), key=str), key=pool.count)
        if not changes:
            break
        fig.px.update(changes)


def finish(fig):
    despeckle(fig)
    fig.outline()


def shadow_under(fig, mask, fam_ok=None, tone=1, rows=1):
    """A part casts a hard shadow on what lies just under it (a joint is a recess)."""
    for (x, y) in mask:
        for r in range(1, rows + 1):
            q = (x, y + r)
            if q in mask or q not in fig.px:
                break
            f, t = fig.px[q]
            if f in ('ink', '_edge', '_lit'):
                break
            if fam_ok and f not in fam_ok:
                break
            fig.px[q] = (f, min(t, tone))


def crease(fig, x, y, n=2, fam=OIL, lit=5, dark=2, d=1, mask=None):
    """Oilskin crease: a sharp bright stepped line (2 px runs) with its dark side under it."""
    pts = []
    for i in range(n):
        pts += [(x + d * 2 * i, y + i), (x + d * (2 * i + 1), y + i)]
    for (px, py) in pts:
        if mask is None or (px, py) in mask:
            fig.put(px, py, fam, lit)
        if mask is None or (px, py + 1) in mask:
            if (px, py + 1) not in pts:
                fig.put(px, py + 1, fam, dark)


def eye_S(fig, cx, cy, look=0):
    """A big frog eye seen from the front: a lit leaf bump, a plaster white, an ink pupil
    2 x 2 and a glint. cx, cy is the bump's centre."""
    bump = fig.ellipse(cx, cy, 3.2, 3.0)
    part(fig, bump, SKIN, glint=False)
    white = fig.rect(int(cx) - 2, int(cy) - 1, int(cx) + 1, int(cy) + 1, knock=1)
    fig.fill(white, BELLY, 5)
    px0 = int(cx) - 1 + look
    for p in ((px0, int(cy) - 1), (px0 + 1, int(cy) - 1), (px0, int(cy)), (px0 + 1, int(cy))):
        fig.put(*p, 'ink', 0)
    fig.put(px0, int(cy) - 1, BELLY, 5)       # glint at the pupil's upper left
    keep(fig, (px0, int(cy) - 1))
    # the lid: a dark lid line over the white (a recess)
    return bump


def eye_side(fig, cx, cy, d):
    """Profile eye: one bump on top of the head, pupil towards the facing."""
    bump = fig.ellipse(cx, cy, 3.0, 2.8)
    part(fig, bump, SKIN, glint=False)
    x0 = int(cx) - 1
    fig.fill(fig.rect(x0, int(cy) - 1, x0 + 2, int(cy) + 1, knock=1), BELLY, 5)
    px = x0 + (1 if d > 0 else 0)
    for p in ((px, int(cy) - 1), (px + 1, int(cy) - 1), (px, int(cy)), (px + 1, int(cy))):
        fig.put(*p, 'ink', 0)
    fig.put(px, int(cy) - 1, BELLY, 5)
    keep(fig, (px, int(cy) - 1))
    return bump


def mouth_S(fig, x0, x1, y):
    """The wide frog smile: a dark line with corners turned up and a lit lip over it."""
    for x in range(x0 + 1, x1):
        fig.put(x, y, SKIN, 0)
    fig.put(x0, y - 1, SKIN, 0)
    fig.put(x1, y - 1, SKIN, 0)
    fig.put(x0 + 1, y - 1, SKIN, 1)
    fig.put(x1 - 1, y - 1, SKIN, 1)


def welly(fig, x0, x1, y0, y1=53, cuff=True):
    m = fig.rect(x0, y0, x1, y1, knock=1)
    part(fig, m, BOOT, glint=False)
    if cuff:   # the turned cuff: a lit band, a dark line under it
        for x in range(x0, x1 + 1):
            if (x, y0) in m:
                fig.put(x, y0, BOOT, 4 if x < (x0 + x1) / 2 + 1 else 3)
            fig.put(x, y0 + 1, BOOT, 1 if x > x0 else 2)
    for x in range(x0, x1 + 1):        # the sole
        if (x, y1) in m:
            fig.put(x, y1, BOOT, 0 if x > x0 + 1 else 1)
    return m


def drops(fig, pts):
    """Water flicked off: 2 px drops in water 1 to 2, outside the outline pass."""
    for (x, y) in pts:
        fig.put(x, y, 'water', 2)
        fig.put(x, y + 1, 'water', 1)


# --- option A: sou'wester and long coat ---------------------------------------------------
def draw_A(view):
    f = sk.Fig(W, H)
    if view in ('S', 'F'):
        fid = view == 'F'
        # back flap of the sou'wester, behind the face and over the shoulders
        flap = f.ellipse(28, 31, 12.5, 4.5)
        flap = {p for p in flap if p[1] >= 29}
        part(f, flap, OIL, glint=False)
        # wellies first, the coat hem overlaps them
        b1 = welly(f, 20, 26, 48)
        b2 = welly(f, 30, 36, 48)
        # long oilskin coat: a bell from the collar to the shins
        coat = f.poly([(20, 33), (36, 33), (40, 50), (16, 50)])
        coat -= f.rect(16, 49, 17, 50) | f.rect(39, 49, 40, 50)
        part(f, coat, OIL, soft=-0.1)
        shadow_under(f, coat, (BOOT,), 0)
        # two long folds from the yoke to the hem: a dark band with a lit band to its west
        for fx, y0 in ((23, 40), (34, 40)):
            for y in range(y0, 49):
                if (fx, y) in coat:
                    f.put(fx, y, OIL, 2 if fx < 28 else 1)
                if (fx - 1, y) in coat:
                    f.put(fx - 1, y, OIL, 4 if fx < 28 else 3)
        # front opening and toggles, creases (sharp bright, dark side under)
        for y in range(36, 50):
            f.put(28, y, OIL, 1)
            f.put(29, y, OIL, 3 if y < 46 else 2)
        for y in (38, 42, 46):
            f.put(27, y, 'timber', 1)
            f.put(27, y - 1, 'timber', 4)
            keep(f, (27, y), (27, y - 1))
        crease(f, 19, 45, 1, mask=coat)
        crease(f, 30, 42, 1, mask=coat, lit=4)
        crease(f, 22, 38, 1, mask=coat)
        # hem: a turned band, lit on the left
        for x in range(17, 40):
            if (x, 49) in coat:
                f.put(x, 49, OIL, 3 if x < 28 else 1)
        # sleeves and webbed hands
        if fid:   # right arm raised holding the hat up, left on the hip
            sl = f.poly([(18, 34), (22, 34), (21, 44), (16, 44)])
            part(f, sl, OIL)
            part(f, f.ellipse(18.5, 45, 2.4, 2.0), SKIN, glint=False)
            sr = f.poly([(34, 33), (38, 34), (42, 24), (39, 22)])
            part(f, sr, OIL)
            crease(f, 37, 29, 1, mask=sr)
            part(f, f.ellipse(41.5, 21.5, 2.2, 2.0), SKIN, glint=False)
        else:
            sl = f.poly([(18, 34), (22, 34), (21, 45), (15, 45)])
            sr = f.poly([(34, 34), (38, 34), (41, 45), (35, 45)])
            part(f, sl, OIL)
            part(f, sr, OIL, soft=0.2)
            crease(f, 17, 40, 1, mask=sl)
            crease(f, 36, 39, 1, mask=sr, lit=4)
            part(f, f.ellipse(18, 46.5, 2.4, 2.0), SKIN, glint=False)
            part(f, f.ellipse(38, 46.5, 2.4, 2.0), SKIN, glint=False)
        # the wide face under the brim
        face = f.ellipse(28, 30.5, 10.5, 4.5)
        part(f, face, SKIN, glint=False)
        # pale throat and chin under the smile
        throat = {p for p in f.ellipse(28, 33.5, 7.5, 2.3) if p[1] >= 32}
        f.fill(throat, BELLY, 4)
        for p in throat:
            if p[0] >= 31:
                f.put(*p, BELLY, 3)
        mouth_S(f, 20, 36, 32)
        # collar: the coat's raised collar under the chin
        col = f.rect(20, 34, 36, 35, knock=1)
        part(f, col, OIL)
        shadow_under(f, col, (OIL,), 2)
        if fid:
            # hat lifted off, tipped, water flicked from the brim: the head's top shows
            top = f.ellipse(28, 27, 9.5, 3.6)
            part(f, top, SKIN)
            eye_S(f, 23.0, 26.5, look=1)
            eye_S(f, 33.0, 26.5, look=1)
            brim = f.poly([(33, 17), (47, 13), (50, 16), (36, 21)])
            part(f, brim, OIL)
            crown = f.ellipse(42, 14.5, 4.2, 3.0)
            part(f, crown, OIL)
            crease(f, 39, 13, 1, mask=crown)
            finish(f)
            drops(f, [(51, 19), (48, 22), (53, 14), (45, 24)])
        else:
            # eyes peek out under the brim
            eye_S(f, 22.5, 29.5)
            eye_S(f, 33.5, 29.5)
            # sou'wester: a wide brim (top plane lit) and a soft crown
            brim = f.ellipse(28, 25.5, 13, 3.0)
            part(f, brim, OIL)
            for x in range(16, 41):   # the brim's front lip, its underside dark
                if (x, 27) in brim:
                    f.put(x, 27, OIL, 2 if x < 30 else 1)
            shadow_under(f, brim, (SKIN, BELLY), 1)
            # the eyes stay bright: re-light their whites
            for cx in (22, 33):
                f.put(cx - 1, 29, BELLY, 5)
            crown = f.ellipse(28, 21.5, 7, 4.3)
            part(f, crown, OIL)
            crease(f, 24, 20, 1, mask=crown)
            band = {p for p in crown if p[1] == 24}
            for p in band:
                f.put(*p, OIL, 2 if p[0] < 31 else 1)
            finish(f)
        return f

    d = 1 if view == 'E' else -1
    X = lambda x: AX + d * x  # noqa: E731  (x measured towards the facing)
    # back flap trailing behind the head
    flap = f.poly([(X(-2), 28), (X(-10), 29), (X(-11), 35), (X(-3), 35)])
    part(f, flap, OIL, glint=False)
    # far boot (a tone darker), near boot
    bfar = welly(f, min(X(-1), X(5)), max(X(-1), X(5)), 48)
    for p in bfar:
        fam, t = f.px[p]
        f.put(*p, fam, max(0, t - 1))
    bnear = welly(f, min(X(-4), X(2)), max(X(-4), X(2)), 49)
    coat = f.poly([(X(-6), 33), (X(5), 33), (X(8), 50), (X(-10), 50)])
    part(f, coat, OIL)
    shadow_under(f, coat, (BOOT,), 0)
    crease(f, min(X(-6), X(-3)), 44, 2, mask=coat, d=1)
    crease(f, min(X(0), X(3)), 40, 1, mask=coat, lit=4)
    for x in range(AX - 12, AX + 12):
        if (x, 49) in coat:
            f.put(x, 49, OIL, 2)
    # the head: long and wide, snout towards the facing
    head = f.ellipse(X(2.5), 30.5, 8.5, 4.6)
    part(f, head, SKIN, glint=False)
    jaw = {p for p in f.ellipse(X(3), 33.4, 6, 2) if p[1] >= 33}
    f.fill(jaw, BELLY, 4)
    # the smile runs from the snout back under the eye
    xs = sorted(range(min(X(-3), X(10)), max(X(-3), X(10)) + 1), key=lambda x: d * x)
    for x in xs[1:]:
        f.put(x, 32, SKIN, 0)
    f.put(xs[0], 31, SKIN, 0)
    eye_side(f, X(5), 28.6, d)
    # nostril
    f.put(X(9), 29, SKIN, 1)
    keep(f, (X(9), 29))
    # collar
    col = f.poly([(X(-5), 34), (X(6), 34), (X(6), 35), (X(-6), 36)])
    part(f, col, OIL)
    # sleeve hangs at the side, the hand peeks out
    sl = f.poly([(X(-2), 34), (X(2), 34), (X(3), 45), (X(-3), 45)])
    part(f, sl, OIL, soft=0.15)
    crease(f, min(X(-2), X(1)), 40, 1, mask=sl)
    for (x, y) in sl:   # the sleeve stands proud of the coat: its back and cuff in shade
        if (x - d, y) not in sl and (x - d, y) in coat:
            f.put(x - d, y, OIL, 1)
        if (x, y + 1) not in sl:
            f.put(x, y, OIL, 2)
    part(f, f.ellipse(X(1.5), 46.2, 2.0, 1.7), SKIN, glint=False)
    # sou'wester, brim longer at the back
    brim = f.poly([(X(-13), 26), (X(-6), 23), (X(7), 23), (X(11), 25), (X(7), 27), (X(-10), 28)])
    part(f, brim, OIL)
    shadow_under(f, brim, (SKIN, BELLY), 1)
    crown = f.ellipse(X(-1), 21, 6.4, 3.8)
    part(f, crown, OIL)
    crease(f, min(X(-4), X(-2)), 19, 1, mask=crown)
    for p in crown:
        if p[1] == 23:
            f.put(*p, OIL, 1)
    finish(f)
    return f


# --- option B: short smock, bare arms, rolled net -------------------------------------
NET = 'path'


def net_roll(f, pts, w=2.6):
    """A rolled net: a sausage of twine with knot rows as 2 px clusters and a cork float."""
    m = set()
    (x0, y0), (x1, y1) = pts
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        t = i / n
        m |= f.ellipse(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, w, w)
    part(f, m, NET, glint=False)
    # knot rows: short dark dashes across the roll, lit pair above each
    for i in range(2, n - 1, 3):
        t = i / n
        cx, cy = int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t)
        for p in ((cx, cy), (cx, cy + 1)):
            if p in m:
                f.put(*p, NET, 1)
        if (cx - 1, cy) in m:
            f.put(cx - 1, cy, NET, 4)
        if (cx - 1, cy - 1) in m:
            f.put(cx - 1, cy - 1, NET, 4)
    return m


def frog_head_bare(f, cx, cy, look=0, mouth=True):
    head = f.ellipse(cx, cy, 10.5, 5.6)
    part(f, head, SKIN)
    throat = {p for p in f.ellipse(cx, cy + 3.5, 7.5, 2.6) if p[1] >= cy + 2.6}
    f.fill(throat, BELLY, 4)
    for p in throat:
        if p[0] >= cx + 3:
            f.put(*p, BELLY, 3)
    if mouth:
        mouth_S(f, int(cx) - 8, int(cx) + 8, int(cy + 2))
    # the eye bumps sit on top of the head and break the silhouette
    eye_S(f, cx - 5.5, cy - 4.5, look)
    eye_S(f, cx + 5.5, cy - 4.5, look)
    # cheek dabs: a sibling cluster under each eye
    for x0 in (int(cx) - 7, int(cx) + 5):
        f.put(x0, int(cy), 'leaf_warm', 4)
        f.put(x0 + 1, int(cy), 'leaf_warm', 4)
    return head


def draw_B(view):
    f = sk.Fig(W, H)
    if view in ('S', 'F'):
        fid = view == 'F'
        # bare green legs, tall wellies
        legs = f.rect(22, 41, 25, 46) | f.rect(31, 41, 34, 46)
        part(f, legs, SKIN, glint=False)
        welly(f, 20, 26, 45)
        welly(f, 30, 36, 45)
        # short smock, flared, to the hips
        smock = f.poly([(21, 32), (35, 32), (38, 43), (18, 43)])
        smock -= {(18, 42), (37, 42), (18, 43), (37, 43)}
        part(f, smock, OIL)
        shadow_under(f, smock, (SKIN,), 1)
        for x in range(18, 39):
            if (x, 42) in smock:
                f.put(x, 42, OIL, 2 if x < 28 else 1)
        # the kangaroo pocket: a seam (tone 1) with a lit lip
        for x in range(24, 32):
            f.put(x, 38, OIL, 1)
            f.put(x, 37, OIL, 4 if x < 28 else 3)
        crease(f, 20, 39, 1, mask=smock)
        crease(f, 31, 34, 1, mask=smock, lit=4)
        # bare green arms out of short sleeves
        ls = f.poly([(19, 32), (23, 32), (22, 37), (17, 36)])
        part(f, ls, OIL)
        rs = f.poly([(33, 32), (37, 32), (39, 36), (34, 37)])
        part(f, rs, OIL, soft=0.2)
        la = f.poly([(17, 37), (21, 37), (20, 42), (17, 42)])
        part(f, la, SKIN, glint=False)
        ra = f.poly([(35, 37), (39, 37), (39, 42), (36, 42)])
        part(f, ra, SKIN, glint=False)
        shadow_under(f, ls, (SKIN,), 1)
        shadow_under(f, rs, (SKIN,), 1)
        part(f, f.ellipse(18.5, 43.2, 2.2, 1.8), SKIN, glint=False)
        part(f, f.ellipse(37.5, 43.2, 2.2, 1.8), SKIN, glint=False)
        # the rolled net, slung from the right shoulder to the left hip, a cork float
        roll = net_roll(f, ((37, 31), (20, 41)), 2.2)
        part(f, f.ellipse(19.5, 44.5, 1.8, 1.8), 'clay', glint=False)
        part(f, f.rect(28, 35, 29, 37), 'clay', glint=False)
        # the head
        head = frog_head_bare(f, 28, 27.5, look=(1 if fid else 0), mouth=not fid)
        if fid:
            # the fly-catch: mouth open, the tongue flicked out to the right, a fly at its tip
            for x in range(21, 35):
                f.put(x, 30, SKIN, 0)
            for x in range(23, 33):
                f.put(x, 31, BOOT, 2)
            tongue = [(33, 30), (34, 29), (35, 29), (36, 28), (37, 28), (38, 27), (39, 27),
                      (40, 26), (41, 26), (42, 25), (43, 25)]
            for (x, y) in tongue:
                f.put(x, y, BOOT, 3)
                f.put(x, y + 1, BOOT, 2)
            f.put(44, 24, BOOT, 4)
            f.put(45, 24, BOOT, 3)
            f.put(44, 25, BOOT, 3)
            f.put(45, 25, BOOT, 2)
            finish(f)
            # the fly: a dark body, two pale wings
            f.put(46, 22, 'ink', 0)
            f.put(47, 22, 'ink', 0)
            f.put(46, 21, 'sky', 1)
            f.put(47, 21, 'sky', 1)
        else:
            finish(f)
        return f

    d = 1 if view == 'E' else -1
    X = lambda x: AX + d * x  # noqa: E731
    lo, hi = (lambda a, b: min(X(a), X(b))), (lambda a, b: max(X(a), X(b)))
    # far leg darker
    fl = f.rect(lo(1, 4), 41, hi(1, 4), 46)
    part(f, fl, SKIN, glint=False)
    bf = welly(f, lo(-1, 5), hi(-1, 5), 45)
    for p in fl | bf:
        fam, t = f.px[p]
        f.put(*p, fam, max(0, t - 1))
    nl = f.rect(lo(-3, 0), 41, hi(-3, 0), 47)
    part(f, nl, SKIN, glint=False)
    welly(f, lo(-5, 1), hi(-5, 1), 46)
    # the net, coiled and slung on the back: seen end on, a round coil
    coil = f.ellipse(X(-7.5), 36.5, 3.8, 4.2)
    part(f, coil, NET, glint=False)
    ring = f.ellipse(X(-7.5), 36.5, 2.2, 2.5) - f.ellipse(X(-7.5), 36.5, 1.1, 1.3)
    for p in ring:
        if p[1] >= 36 or (p[0] - X(-7.5)) * d > 0:
            f.put(*p, NET, 1)
    for p in f.ellipse(X(-7.5), 36.5, 1.1, 1.3):
        f.put(*p, NET, 4)
    part(f, f.ellipse(X(-8), 41.5, 1.6, 1.5), 'clay', glint=False)
    smock = f.poly([(X(-5), 32), (X(5), 32), (X(7), 43), (X(-8), 43)])
    part(f, smock, OIL)
    shadow_under(f, smock, (SKIN,), 1)
    for x in range(AX - 10, AX + 10):
        if (x, 42) in smock:
            f.put(x, 42, OIL, 2)
    crease(f, lo(-4, -1), 38, 1, mask=smock)
    # sleeve and bare arm swinging a little forward
    sl = f.poly([(X(-2), 32), (X(3), 32), (X(3), 36), (X(-2), 36)])
    part(f, sl, OIL)
    arm = f.poly([(X(-1), 36), (X(3), 36), (X(4), 41), (X(1), 42)])
    part(f, arm, SKIN, glint=False)
    shadow_under(f, sl, (SKIN,), 1)
    part(f, f.ellipse(X(2.8), 42.5, 2.0, 1.7), SKIN, glint=False)
    # head
    head = f.ellipse(X(2.5), 27.5, 9, 5.2)
    part(f, head, SKIN)
    jaw = {p for p in f.ellipse(X(3), 31, 6.5, 2) if p[1] >= 31}
    f.fill(jaw, BELLY, 4)
    xs = sorted(range(lo(-3, 11), hi(-3, 11) + 1), key=lambda x: d * x)
    for x in xs[1:]:
        f.put(x, 30, SKIN, 0)
    f.put(xs[0], 29, SKIN, 0)
    eye_side(f, X(4), 23.2, d)
    f.put(X(9), 26, SKIN, 1)
    keep(f, (X(9), 26))
    finish(f)
    return f


# --- option C: dungaree waders and a tin bucket ------------------------------------------
TIN = 'iron'


def bucket(f, x0, y0, tip=False):
    """A tin bucket: a lit rim ellipse, a body with a sheen at the upper left, a wire handle."""
    body = f.poly([(x0, y0 + 1), (x0 + 7, y0 + 1), (x0 + 6, y0 + 8), (x0 + 1, y0 + 8)])
    part(f, body, TIN)
    for y in range(y0 + 2, y0 + 7):          # sheen band in the left third
        f.put(x0 + 1, y, TIN, 4)
        f.put(x0 + 2, y, TIN, 4)
    for x in range(x0 + 1, x0 + 7):           # a rolled seam half way
        f.put(x, y0 + 5, TIN, 1)
    rim = f.rect(x0, y0, x0 + 7, y0 + 1, knock=1)
    f.fill(rim, TIN, 4)
    for x in range(x0 + 1, x0 + 7):
        f.put(x, y0 + 1, 'water', 2)          # water in it
    f.put(x0 + 2, y0 + 1, 'water', 4)
    f.put(x0 + 3, y0 + 1, 'water', 4)
    return body | rim


def draw_C(view):
    f = sk.Fig(W, H)
    if view in ('S', 'F'):
        fid = view == 'F'
        # wader legs into the wellies (wellies are the waders' feet)
        if fid:
            # hopping on the left foot; the right welly held up, tipped out
            lg = f.rect(21, 42, 26, 48, knock=1)
            part(f, lg, OIL)
            welly(f, 20, 26, 48)
            rg = f.poly([(30, 42), (36, 42), (36, 46), (31, 46)])
            part(f, rg, OIL)
            foot = f.ellipse(34, 47, 3, 1.6)
            part(f, foot, SKIN, glint=False)
        else:
            lg = f.rect(21, 42, 26, 49, knock=1)
            rg = f.rect(30, 42, 35, 49, knock=1)
            part(f, lg, OIL)
            part(f, rg, OIL)
            welly(f, 20, 26, 49)
            welly(f, 30, 36, 49)
            crease(f, 21, 45, 1, mask=lg)
            crease(f, 31, 44, 1, mask=rg, lit=4)
        # the bib and seat: oilskin from the chest down
        bib = f.poly([(22, 33), (34, 33), (36, 43), (20, 43)])
        bare = f.poly([(20, 31), (36, 31), (36, 34), (20, 34)])
        part(f, bare, SKIN, glint=False)
        f.fill({p for p in bare if 24 <= p[0] <= 32}, BELLY, 4)
        part(f, bib, OIL)
        for x in range(21, 36):
            f.put(x, 42, OIL, 1)               # the crotch seam shadow
        f.put(28, 43, OIL, 1)
        # bib pocket and brass buckles
        for x in range(25, 31):
            f.put(x, 37, OIL, 1)
            f.put(x, 36, OIL, 4 if x < 28 else 3)
        for bx in (23, 33):
            f.put(bx, 33, TIN, 4)
            f.put(bx, 34, TIN, 2)
        crease(f, 22, 39, 1, mask=bib)
        # braces over the shoulders
        for y in range(31, 33):
            f.put(23, y, OIL, 3)
            f.put(24, y, OIL, 2)
            f.put(32, y, OIL, 3)
            f.put(33, y, OIL, 2)
        # bare arms; the right hand holds the bucket (or the welly)
        la = f.poly([(18, 32), (21, 32), (21, 41), (17, 41)])
        part(f, la, SKIN, glint=False)
        part(f, f.ellipse(18.6, 42.2, 2.2, 1.8), SKIN, glint=False)
        if fid:
            ra = f.poly([(35, 32), (38, 32), (42, 24), (39, 23)])
            part(f, ra, SKIN, glint=False)
            boot = f.poly([(39, 14), (45, 14), (45, 21), (42, 23), (39, 21)])
            part(f, boot, BOOT)
            for x in range(39, 46):
                f.put(x, 14, BOOT, 1)          # the open top, dark inside
                f.put(x, 15, BOOT, 0 if x > 39 else 1)
            part(f, f.ellipse(40.5, 23.5, 2, 1.8), SKIN, glint=False)
        else:
            ra = f.poly([(35, 32), (38, 32), (39, 40), (35, 40)])
            part(f, ra, SKIN, glint=False)
            # the bucket hangs from the right hand
            bucket(f, 36, 42)
            f.line([(37, 42), (38, 39), (41, 39), (43, 42)], TIN, 2)
            part(f, f.ellipse(38.5, 40.5, 2.0, 1.8), SKIN, glint=False)
        head = frog_head_bare(f, 28, 26.5, look=(1 if fid else 0))
        finish(f)
        if fid:
            drops(f, [(42, 10), (44, 8), (40, 7), (46, 11)])
        return f

    d = 1 if view == 'E' else -1
    X = lambda x: AX + d * x  # noqa: E731
    lo, hi = (lambda a, b: min(X(a), X(b))), (lambda a, b: max(X(a), X(b)))
    fg = f.rect(lo(0, 5), 42, hi(0, 5), 48, knock=1)
    part(f, fg, OIL)
    fb = welly(f, lo(-1, 6), hi(-1, 6), 48)
    for p in fg | fb:
        fam, t = f.px[p]
        f.put(*p, fam, max(0, t - 1))
    ng = f.rect(lo(-4, 1), 42, hi(-4, 1), 49, knock=1)
    part(f, ng, OIL)
    welly(f, lo(-5, 2), hi(-5, 2), 49)
    bare = f.poly([(X(-4), 31), (X(5), 31), (X(5), 34), (X(-4), 34)])
    part(f, bare, SKIN, glint=False)
    bib = f.poly([(X(-5), 33), (X(5), 33), (X(6), 43), (X(-7), 43)])
    part(f, bib, OIL)
    crease(f, lo(-5, -2), 39, 1, mask=bib)
    for y in range(31, 34):
        f.put(X(-2), y, OIL, 3)
    # the bucket hangs in front of the near hand
    arm = f.poly([(X(-1), 32), (X(2), 32), (X(3), 40), (X(0), 40)])
    part(f, arm, SKIN, glint=False)
    for (x, y) in arm:   # the arm stands proud of the bib: a shaded seam behind it
        if (x - d, y) not in arm and (x - d, y) in f.px and f.px[(x - d, y)][0] == OIL:
            f.put(x - d, y, OIL, 1)
    bucket(f, X(0) - 4, 43)
    f.line([(X(0) - 3, 43), (X(0) - 2, 41), (X(0) + 1, 41), (X(0) + 2, 43)], TIN, 2)
    part(f, f.ellipse(X(1.5), 41, 1.9, 1.7), SKIN, glint=False)
    head = f.ellipse(X(2.5), 26.5, 9, 5.2)
    part(f, head, SKIN)
    jaw = {p for p in f.ellipse(X(3), 30, 6.5, 2) if p[1] >= 30}
    f.fill(jaw, BELLY, 4)
    xs = sorted(range(lo(-3, 11), hi(-3, 11) + 1), key=lambda x: d * x)
    for x in xs[1:]:
        f.put(x, 29, SKIN, 0)
    f.put(xs[0], 28, SKIN, 0)
    eye_side(f, X(4), 22.2, d)
    f.put(X(9), 25, SKIN, 1)
    keep(f, (X(9), 25))
    finish(f)
    return f


# --- options -------------------------------------------------------------------------
OPTIONS = [
    dict(label='A', name="Sou'wester and long coat", draw=draw_A,
         palette=['leaf', 'plaster', 'brass', 'berry', 'timber'],
         question="Oilskin hides almost all of the frog: only the wide face, the eyes under the brim and the red wellies show.",
         pose='Bundled up and patient as a heron, coat buttoned, hands out of the sleeves: the bargee in miniature.',
         fidget="Lifts the sou'wester off and flicks the rain from its brim, eyes squinting up after the drops.",
         parts=[
             "sou'wester flap | brass | back | changes in all facings (behind the head in S, trailing in E/W) | head",
             "wellies L/R | berry | 1 | S/E/W, far boot a tone down in profile | foot",
             'long coat (bell) | brass | 2 | S/E/W, hem swings 1 px against the walk | hip',
             'sleeves + webbed hands L/R | brass, leaf | 3 | swing in walk; raise in fidget, cast, cheer | chest',
             'face (wide, smile, throat) | leaf, plaster | 4 | S/E/W profile snout | head',
             'eyes L/R (bump, white, pupil) | leaf, plaster, ink | 5 | blink overlay, look offsets | head',
             "sou'wester brim + crown | brass | 6 (top) | S/E/W; lifted off in fidget, pulled down in guard, falls in hit | head",
             'collar + toggles | brass, timber | 4 | S only | chest',
         ],
         notes=[
             'Works: the brim plus the bell coat is the strongest silhouette of the three (a little lamp-post), unlike Tam\'s round hat or Tally\'s fleece blob.',
             'Risk: the frog is mostly hidden; eyes must survive under the brim shadow, so their whites stay tone 5 and sit below the brim lip.',
             'Risk: nap curled and walk legs are mostly coat; a long hem costs extra walk frames to keep legs readable.',
             'Compared with Eastward-04 (New Dam market, the fishmonger and John at ~36 px): head about 40%, 3 px eyes, 4 tones in the coat, a hard brim shadow.',
         ]),
    dict(label='B', name='Short smock and rolled net', draw=draw_B,
         palette=['leaf', 'plaster', 'brass', 'berry', 'path'],
         question='A short oilskin smock to the hips: bare green arms and legs, the eye bumps on top of the bare head, a rolled net slung across.',
         pose='Springy and curious, weight on the toes of the wellies, chin up: always half a hop from the water.',
         fidget='Catches a fly: mouth snaps open, a long berry tongue flicks out to the side, the eyes swivel after it.',
         parts=[
             'legs L/R (bare) | leaf | 1 | S/E/W, far leg a tone down in profile | hip',
             'wellies L/R (tall) | berry | 1 | S/E/W | foot',
             'net roll + cork floats | path, clay | 2 (a sash in front in S, a coil on the back in E/W) | swaps layer by facing | chest -> back',
             'smock with pocket | brass | 3 | S/E/W, hem flares in hop | hip',
             'sleeves + bare arms + hands L/R | brass, leaf | 4 | swing in walk; wind-up, strike, cast | chest',
             'head (wide, throat, cheeks) | leaf, plaster | 5 | S/E/W | head',
             'eye bumps L/R | leaf, plaster, ink | 6 (top) | blink overlay, look offsets; break the silhouette | head',
             'tongue (fidget, strike) | berry | 7 | S fidget, fight strike E/W | head',
         ],
         notes=[
             'Works: the most frog of the three (two eye bumps on top, bare limbs), and the tongue gives the Trickster a ready strike and fidget.',
             'Risk: the net across the chest crowds 36 px; the brass smock must keep its creases sharp so it reads as oilskin, not a tunic.',
             'Distinct from Tam and Tally: no hat at all, the head is wider than the body and the eye bumps make a double peak.',
             'Compared with Eastward-04 (John, Sam and the market folk scaled to 36 px): bare limbs 3 px wide with a lit left column, 2 px knot clusters.',
         ]),
    dict(label='C', name='Dungaree waders and a tin bucket', draw=draw_C,
         palette=['leaf', 'plaster', 'brass', 'berry', 'iron'],
         question='Oilskin waders to the chest on braces: bare green head, arms and a pale chest show, the wellies are the waders\' feet; a tin bucket in hand.',
         pose='Sturdy and busy, bucket at the ready, bare head up: the apprentice on the job.',
         fidget='Hops on one foot and tips the water out of a welly, drops splashing out over the brim.',
         parts=[
             'wader legs L/R | brass | 1 | S/E/W, far leg a tone down in profile | hip',
             'wellies L/R | berry | 1 | S/E/W; one held up in fidget | foot',
             'chest (bare) + belly | leaf, plaster | 2 | S/E/W | chest',
             'bib + braces + buckles | brass, iron | 3 | S/E/W | chest',
             'arms + hands L/R | leaf | 4 | swing in walk; raise in fidget, cheer | chest',
             'bucket + wire handle | iron, water | 5 | hand prop; set down for nap and fight | hand',
             'head (wide, throat, cheeks) + eye bumps | leaf, plaster, ink | 6 | blink, look offsets | head',
         ],
         notes=[
             'Works: the waders give a sturdy dungaree block and the bucket a side bump; the bare chest and arms keep the frog visible.',
             'Risk: the bucket is a held prop, so fight and nap frames must park it; it makes C the widest silhouette.',
             'Risk: brass from chest to boots can read as one yellow block; the crotch seam and the braces have to stay dark.',
             'Compared with Eastward-04 (the overalls of the market grocer at ~36 px): a dark bib seam, metal sheen on the left third of the bucket.',
         ]),
]

VIEWS = [('S', 'S idle'), ('E', 'E idle'), ('W', 'W idle'), ('F', 'S fidget')]


def gates(m, lone=0.06):
    return {
        'on_house': m['on_house'] >= 0.999,
        'west_east': m['west_east'] > 0,
        'lone': m['isolated'] <= lone,
        'colours': m['colours'] <= 64,
        'outline_dark': m.get('outline_dark', 0) >= 0.95,
    }


# =====================================================================================
# FINAL (revision round, 21 Oct): option B, the short smock, with grafts
#   from A: a brass sou'wester pushed back, hanging behind the head on its chin cord
#   from C: braces over the smock instead of the net sash; the net is a small coil on the
#           back in every facing (one anchor, one layer)
# =====================================================================================
OUT_FINAL = os.path.join(REPO, 'docs', 'vision', 'characters', 'designs', 'puddle-final.png')
BRACE = 'berry'
FAM = 'grass'            # the stand-in Mossling on the perch (24 art px)


def despeckle_after(fig, passes=2):
    """After the outline: paint over inside pixels left lone against the outline (knocked
    corners, sleeve ends). Outline, ink and kept pixels stay."""
    kept = getattr(fig, 'keep', set())
    bad = ('ink', '_edge', '_lit')
    for _ in range(passes):
        changes = {}
        for (x, y), v in fig.px.items():
            if v[0] in bad or (x, y) in kept or (x, y) in fig.fixed:
                continue
            nb = [fig.px.get((x + dx, y + dy)) for dx, dy in sk.N4]
            if None in nb or any(n == v for n in nb):
                continue
            same = [n for n in nb if n[0] == v[0]]
            pool = same or [n for n in nb if n[0] not in bad]
            if pool:
                changes[(x, y)] = max(sorted(set(pool), key=str), key=pool.count)
        if not changes:
            break
        fig.px.update(changes)


def finish_final(fig):
    despeckle(fig)
    fig.outline()
    despeckle_after(fig)


def thick(f, a, b, r):
    """A limb: a capsule from a to b of radius r."""
    m = set()
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 2) + 1
    for i in range(n + 1):
        t = i / n
        m |= f.ellipse(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, r, r)
    return m


def oil_creases(f, mask, folds, d=1):
    """Oilskin: hard bright creases on short diagonal folds (tone 5 runs of 2 px, the fold's
    dark side tone 2 under them), only on the smock itself."""
    for (x, y, n, lit) in folds:
        crease(f, x, y, n, mask=mask, lit=lit, d=d)


def stiff_hem(f, mask, y, xlo, xhi):
    """A stiff hem: a lit roll (4 west, 3 east) and a hard dark row under it."""
    for x in range(xlo, xhi + 1):
        if (x, y - 1) in mask:
            f.put(x, y - 1, OIL, 4 if x < (xlo + xhi) / 2 else 3)
        if (x, y) in mask:
            f.put(x, y, OIL, 1)


def coil(f, cx, cy, r=3.6, dim=0):
    """The rolled net seen end on: a clear three-loop coil of twine (path)."""
    m = f.ellipse(cx, cy, r, r)
    part(f, m, NET, glint=False)
    for p in m:   # loops: rings at radius ~1.3 and ~2.6, dark on their lower right, lit upper left
        dx, dy = p[0] + 0.5 - cx, p[1] + 0.5 - cy
        rr = (dx * dx + dy * dy) ** 0.5
        if 1.0 <= rr < 1.9 or 2.4 <= rr < 3.0:
            f.put(*p, NET, 1 if dx + dy > -0.5 else 2)
        elif rr < 1.0:
            f.put(*p, NET, 4)
    if dim:
        for p in m:
            fam, t = f.px[p]
            f.put(*p, fam, max(0, t - dim))
    return m


def mossling(f, cx, by, d, curled=False):
    """Stand-in familiar: a round leaf-green blob, two ink eyes, a sprout; 24 art px tall."""
    if curled:
        blob = f.ellipse(cx, by - 5, 7.5, 5.5)
        part(f, blob, FAM)
        for x in (int(cx) - 3, int(cx) + 1):
            f.put(x, int(by) - 5, FAM, 1)
            f.put(x + 1, int(by) - 5, FAM, 1)
        sp = [(int(cx) + 5, int(by) - 10), (int(cx) + 6, int(by) - 10), (int(cx) + 7, int(by) - 9)]
        for p in sp:
            f.put(*p, 'leaf', 4)
        return blob
    blob = f.ellipse(cx, by - 9.5, 9.5, 10)
    part(f, blob, FAM)
    for p in blob:   # a lit cap and a dark crescent following the form
        dx, dy = p[0] + 0.5 - cx, p[1] + 0.5 - (by - 9.5)
        if dx * 0.6 + dy * 0.8 > 6.5:
            f.put(*p, FAM, 1)
    stem = [(int(cx), int(by) - 20), (int(cx), int(by) - 21), (int(cx), int(by) - 22)]
    for p in stem:
        f.put(*p, 'leaf', 3)
    for p in ((int(cx) - 2, int(by) - 23), (int(cx) - 1, int(by) - 23), (int(cx) - 1, int(by) - 22)):
        f.put(*p, 'leaf', 4)
    for p in ((int(cx) + 1, int(by) - 23), (int(cx) + 2, int(by) - 23), (int(cx) + 1, int(by) - 22)):
        f.put(*p, 'leaf', 2)
    ex = int(cx) + 2 * d
    for x in (ex - 3, ex + 2):
        f.put(x, int(by) - 11, 'ink', 0)
        f.put(x, int(by) - 10, 'ink', 0)
    return blob


# ---- S facing ------------------------------------------------------------------------
def final_S(fidget=False):
    f = sk.Fig(W, H)
    # back layer: the net coil on the back, peeking past the left shoulder (her left)
    coil(f, 40.5, 34.5, 3.4)
    # the sou'wester hangs behind the head: its brim shows either side under the cheeks
    brim = f.ellipse(28, 31.5, 14, 3.0)
    part(f, brim, OIL)
    for p in brim:
        if p[1] >= 32:
            f.put(*p, OIL, 2 if p[0] < 28 else 1)
    legs = f.rect(22, 41, 25, 46) | f.rect(31, 41, 34, 46)
    part(f, legs, SKIN, glint=False)
    welly(f, 20, 26, 45)
    welly(f, 30, 36, 45)
    smock = f.poly([(21, 32), (35, 32), (38.5, 43), (17.5, 43)])
    part(f, smock, OIL, soft=-0.1)
    shadow_under(f, smock, (SKIN,), 1)
    stiff_hem(f, smock, 42, 17, 38)
    for x in (17, 38):                 # the stiff hem stands out a pixel at each corner
        f.put(x, 42, OIL, 2 if x == 17 else 1)
    oil_creases(f, smock, [(20, 37, 2, 5), (30, 38, 1, 5), (26, 34, 1, 4), (33, 35, 1, 4)])
    # braces: berry straps from the shoulders to the hem, a brass button at each end
    for bx in (23, 32):
        for y in range(32, 42):
            f.put(bx, y, BRACE, 3 if bx < 28 else 2)
            f.put(bx + 1, y, BRACE, 2 if bx < 28 else 1)
        f.put(bx, 40, 'brass', 4)
        f.put(bx + 1, 40, 'brass', 4)
        keep(f, (bx, 40), (bx + 1, 40))
    # short stiff sleeves and bare arms
    ls = f.poly([(18.5, 32), (23, 32), (22, 36.5), (16.5, 36)])
    rs = f.poly([(33, 32), (37.5, 32), (39.5, 36), (34, 36.5)])
    part(f, ls, OIL)
    part(f, rs, OIL, soft=0.2)
    crease(f, 18, 33, 1, mask=ls)
    la = f.poly([(17, 37), (21, 37), (20, 42), (17, 42)])
    part(f, la, SKIN, glint=False)
    if fidget:
        ra = f.poly([(35, 37), (39, 37), (39, 42), (36, 42)])
    else:
        ra = f.poly([(35, 37), (39, 37), (39, 42), (36, 42)])
    part(f, ra, SKIN, glint=False)
    shadow_under(f, ls, (SKIN,), 1)
    shadow_under(f, rs, (SKIN,), 1)
    part(f, f.ellipse(18.5, 43.2, 2.2, 1.8), SKIN, glint=False)
    part(f, f.ellipse(37.5, 43.2, 2.2, 1.8), SKIN, glint=False)
    # head (B's), with the chin cord of the hanging hat across the pale throat
    frog_head_bare(f, 28, 27.5, look=(1 if fidget else 0), mouth=not fidget)
    for (x, y) in ((19, 30), (20, 31), (21, 31), (35, 31), (36, 31), (37, 30)):
        f.put(x, y, OIL, 1)
    if fidget:
        for x in range(21, 35):
            f.put(x, 30, SKIN, 0)
        for x in range(23, 33):
            f.put(x, 31, BOOT, 2)
        tongue = [(33, 30), (34, 29), (35, 29), (36, 28), (37, 28), (38, 27), (39, 27),
                  (40, 26), (41, 26), (42, 25), (43, 25)]
        for (x, y) in tongue:
            f.put(x, y, BOOT, 3)
            f.put(x, y + 1, BOOT, 2)
        for p, t in (((44, 24), 4), ((45, 24), 3), ((44, 25), 3), ((45, 25), 2)):
            f.put(*p, BOOT, t)
        finish_final(f)
        f.put(46, 22, 'ink', 0)
        f.put(47, 22, 'ink', 0)
        f.put(46, 21, 'sky', 1)
        f.put(47, 21, 'sky', 1)
    else:
        finish_final(f)
    return f


# ---- side facings (E and W drawn from the same parts, lit from the upper left) ----------
POSES = {
    #          body dx, dy, head dx, dy, lean, near arm, far arm, legs,   mouth,   eyes,    familiar
    'idle':   dict(bx=0, by=0, hx=0, hy=0, lean=0, near='down', far=None, legs='stand', mouth='smile', eyes='open', fam=False),
    'ready':  dict(bx=0, by=1, hx=1, hy=1, lean=1, near='fwd', far='fwd', legs='wide', mouth='smile', eyes='open', fam=True),
    'strike': dict(bx=2, by=1, hx=3, hy=1, lean=3, near='back', far='fwd', legs='step', mouth='tongue', eyes='open', fam=True),
    'cast':   dict(bx=0, by=0, hx=0, hy=-1, lean=0, near='up', far='up', legs='stand', mouth='smile', eyes='open', fam=True),
    'hit':    dict(bx=-2, by=0, hx=-3, hy=0, lean=-2, near='fling', far='fling', legs='stand', mouth='ouch', eyes='squeeze', fam=True),
    'sit':    dict(bx=0, by=6, hx=0, hy=5, lean=0, near='lap', far=None, legs='sit', mouth='smile', eyes='half', fam=True),
    'cheer':  dict(bx=0, by=-3, hx=0, hy=-3, lean=0, near='high', far='up', legs='air', mouth='open', eyes='happy', fam=True),
}
ARM = {'down': (1, 9), 'fwd': (6, 4), 'back': (-5, 7), 'up': (10, -8), 'high': (12, -10), 'fling': (-6, -3), 'lap': (5, 7)}


def final_side(d, pose):
    P = POSES[pose]
    f = sk.Fig(W, H)
    X = lambda x: int(round(AX + d * x))  # noqa: E731
    lo, hi = (lambda a, b: min(X(a), X(b))), (lambda a, b: max(X(a), X(b)))
    bx, by, hx, hy, lean = P['bx'], P['by'], P['hx'], P['hy'], P['lean']
    perch = None
    # 1 back: the net coil on the back (the same anchor in every facing)
    coil(f, X(-7.5 + bx - lean * 0.5), 37.5 + by, 3.4, dim=0)
    # 2 the hanging sou'wester, edge on behind the head
    hcx, hcy = X(2.5 + bx + hx), 27.5 + by + hy
    hb = f.ellipse(hcx - d * 9.5, hcy + 1.5, 2.6, 5.4)
    part(f, hb, OIL)
    hc = f.ellipse(hcx - d * 11.2, hcy + 1.5, 2.0, 3.4)
    part(f, hc, OIL)
    crease(f, min(hcx - d * 12, hcx - d * 11), int(hcy), 1, mask=hc)
    # 3 legs and wellies (the far one a tone down)
    legs = P['legs']
    if legs == 'sit':
        # sat down for a breather: knees up, wellies planted in front
        far_l = thick(f, (X(1), 48), (X(7), 43), 1.7)
        part(f, far_l, SKIN, glint=False)
        fw = welly(f, lo(6, 11), hi(6, 11), 46, 52)
        for p in far_l | fw:
            fam, t = f.px[p]
            f.put(*p, fam, max(0, t - 1))
        near_l = thick(f, (X(-1), 49), (X(6), 44), 1.8)
        part(f, near_l, SKIN, glint=False)
        welly(f, lo(4, 10), hi(4, 10), 47, 53)
    else:
        if legs == 'step':
            nf, ff = (2, 8), (-7, -1)
        elif legs == 'wide':
            nf, ff = (-6, 0), (1, 7)
        elif legs == 'air':
            nf, ff = (-4, 2), (1, 7)
        else:
            nf, ff = (-5, 1), (-1, 5)
        lift = -3 if legs == 'air' else 0
        fl = thick(f, (X(2.5 + bx), 41 + by), (X((ff[0] + ff[1]) / 2), 46 + lift), 1.6)
        part(f, fl, SKIN, glint=False)
        fb = welly(f, lo(*ff), hi(*ff), 45 + lift, 53 + lift)
        for p in fl | fb:
            fam, t = f.px[p]
            f.put(*p, fam, max(0, t - 1))
        nl = thick(f, (X(-1.5 + bx), 41 + by), (X((nf[0] + nf[1]) / 2), 47 + lift), 1.7)
        part(f, nl, SKIN, glint=False)
        welly(f, lo(*nf), hi(*nf), 46 + lift, 53 + lift)
    # 4 the far arm, behind the body
    sh = (X(1 + bx + lean * 0.5), 34 + by)
    if P['far']:
        ax, ay = ARM[P['far']]
        hand = (sh[0] + d * (ax + 1), sh[1] + ay - 1)
        arm = thick(f, sh, hand, 1.5)
        part(f, arm, SKIN, glint=False)
        hm = f.ellipse(hand[0] + 0.5, hand[1] + 0.5, 1.9, 1.8)
        part(f, hm, SKIN, glint=False)
        for p in arm | hm:
            fam, t = f.px[p]
            f.put(*p, fam, max(0, t - 1))
    # 5 the familiar on the shoulder away from the foe (behind the head, on the back shoulder)
    if P['fam']:
        pcx, pby = X(-9.5 + bx), 34 + by
        mossling(f, pcx, pby, d)
        perch = [pcx, pby]
    # 6 the smock: stiff, flared, bright creases, braces
    top = 32 + by
    sm = f.poly([(X(-5 + bx + lean), top), (X(5 + bx + lean), top), (X(7 + bx), 43 + by), (X(-8 + bx), 43 + by)])
    part(f, sm, OIL, soft=-0.1)
    shadow_under(f, sm, (SKIN,), 1)
    stiff_hem(f, sm, 42 + by, AX - 14, AX + 14)
    oil_creases(f, sm, [(lo(-5 + bx, -2 + bx), 38 + by, 2, 5), (lo(1 + bx, 3 + bx), 35 + by, 1, 4)], d=1)
    for y in range(top, 42 + by):    # the near brace
        bxp = X(0.5 + bx + lean * (42 + by - y) / 10.0)
        f.put(bxp, y, BRACE, 3 if d < 0 else 2)
        f.put(bxp + 1, y, BRACE, 2 if d < 0 else 1)
    # 8 the head, drawn as a form: brow, cheek, snout step
    head = f.ellipse(hcx, hcy, 9, 5.2)
    head = {p for p in head if not (d * (p[0] + 0.5 - hcx) > 6 and p[1] + 0.5 < hcy - 2.4)}
    part(f, head, SKIN)
    for p in head:   # the snout's front plane: lit in W (facing the light), shaded in E
        if d * (p[0] + 0.5 - hcx) > 6.2 and p[1] < hcy + 1.5:
            f.put(*p, SKIN, 4 if d < 0 else 2)
    cy0 = int(hcy)
    for x in (hcx - d * 1, hcx - d * 2):   # cheek: a lit pair behind the smile
        f.put(int(x), cy0, 'leaf_warm', 4)
        f.put(int(x), cy0 + 1, 'leaf_warm', 4)
    if perch:   # where the head overlaps the familiar, a dark contact rim keeps the two apart
        for (x, y) in head:
            for dx, dy in sk.N4:
                q = f.px.get((x + dx, y + dy))
                if q and q[0] == FAM and (x + dx, y + dy) not in head:
                    f.put(x, y, SKIN, 1)
                    break
    jaw = {p for p in f.ellipse(hcx + d * 0.5, hcy + 3.6, 6.5, 2) if p[1] >= hcy + 3.4 and p in head}
    f.fill(jaw, BELLY, 4)
    # the chin cord from the hat round the jaw
    f.line([(int(hcx - d * 7.5), int(hcy) + 2), (int(hcx - d * 3), int(hcy) + 4), (int(hcx + d * 1), int(hcy) + 4)], OIL, 1)
    # mouth
    mx0, mx1 = X(-3 + bx + hx), X(10.5 + bx + hx)
    xs = sorted(range(min(mx0, mx1), max(mx0, mx1) + 1), key=lambda x: d * x)
    my = int(hcy) + 2
    if P['mouth'] in ('open', 'tongue'):
        for x in xs[2:]:
            f.put(x, my - 1, SKIN, 0)
            f.put(x, my, 'ink', 0)
            f.put(x, my + 1, BOOT, 2)
        f.put(xs[1], my, SKIN, 0)
        if P['mouth'] == 'tongue':
            tx0 = xs[-1] + d
            for i in range(0, 6):
                x = tx0 + d * i
                if 0 <= x < W:
                    f.put(x, my, BOOT, 3)
                    f.put(x, my + 1, BOOT, 2)
            tip = tx0 + d * 6
            for p, t in (((tip, my - 1), 4), ((tip + d, my - 1), 3), ((tip, my), 3), ((tip + d, my), 3),
                         ((tip, my + 1), 2), ((tip + d, my + 1), 1)):
                f.put(*p, BOOT, t)
    elif P['mouth'] == 'ouch':
        for i, x in enumerate(xs[3:-2]):
            f.put(x, my + (i // 2) % 2, SKIN, 0)
    else:
        for x in xs[1:]:
            f.put(x, my, SKIN, 0)
        f.put(xs[0], my - 1, SKIN, 0)
    f.put(X(9 + bx + hx), int(hcy) - 1, SKIN, 1)   # nostril
    keep(f, (X(9 + bx + hx), int(hcy) - 1))
    # the eye bump on top, with a brow recess under it
    ex, ey = hcx + d * 1.5, hcy - 4.3
    bump = f.ellipse(ex, ey, 3.0, 2.8)
    part(f, bump, SKIN, glint=False)
    for x in range(int(ex) - 2, int(ex) + 3):
        if (x, int(ey) + 3) in head:
            f.put(x, int(ey) + 3, SKIN, 2)
    x0 = int(ex) - 1
    eyes = P['eyes']
    if eyes == 'squeeze':
        for p in ((x0, int(ey) - 1), (x0 + 1, int(ey)), (x0 + 2, int(ey))):
            f.put(*p, 'ink', 0)
    elif eyes == 'happy':
        for p in ((x0, int(ey)), (x0 + 1, int(ey) - 1), (x0 + 2, int(ey))):
            f.put(*p, 'ink', 0)
    else:
        f.fill(f.rect(x0, int(ey) - 1, x0 + 2, int(ey) + 1, knock=1), BELLY, 5)
        px = x0 + (1 if d > 0 else 0)
        for p in ((px, int(ey) - 1), (px + 1, int(ey) - 1), (px, int(ey)), (px + 1, int(ey))):
            f.put(*p, 'ink', 0)
        f.put(px, int(ey) - 1, BELLY, 5)
        keep(f, (px, int(ey) - 1))
        if eyes == 'half':   # a heavy lid over the top half
            for x in range(x0 - 1, x0 + 4):
                f.put(x, int(ey) - 1, SKIN, 2)
                f.put(x, int(ey) - 2, SKIN, 3)
    # 7 the near arm with a stiff short sleeve
    ax, ay = ARM[P['near']]
    hand = (sh[0] + d * ax, sh[1] + ay)
    arm = thick(f, sh, hand, 1.6)
    part(f, arm, SKIN, glint=False)
    slv = f.ellipse(sh[0] + 0.5, sh[1] + 0.5, 2.8, 2.6)
    part(f, slv, OIL)
    crease(f, sh[0] - 2, sh[1] - 1, 1, mask=slv)
    hm = f.ellipse(hand[0] + 0.5, hand[1] + 0.5, 2.0, 1.9)
    part(f, hm, SKIN, glint=False)
    if pose == 'cast':   # Tide: a turning ball of water gathered between the raised hands
        ocx, ocy = hand[0] + d * 1.5, hand[1] - 4.5
        orb = f.ellipse(ocx, ocy, 3.2, 3.0)
        part(f, orb, 'water')
        for p in orb:   # the current turning in it: a dark lower crescent, a lit streak
            if (p[0] + 0.5 - ocx) * 0.5 + (p[1] + 0.5 - ocy) > 1.4:
                f.put(*p, 'water', 2)
        f.put(int(ocx) - 1, int(ocy) - 1, 'water', 5)
        f.put(int(ocx), int(ocy) - 1, 'water', 5)
    finish_final(f)
    return f, perch


def final_nap():
    """nap_c: curled up belly down facing S, chin on the folded arms, the familiar curled at her side."""
    f = sk.Fig(W, H)
    brim = f.ellipse(27, 35.5, 9.5, 2.3)           # the sou'wester still hangs on her back
    part(f, brim, OIL)
    welly(f, 14, 19, 40, 46)                      # boots tucked up at the hips
    welly(f, 35, 40, 40, 46)
    back = f.ellipse(27, 40.0, 11, 5.0)            # the smock's back, a stiff dome
    part(f, back, OIL, soft=-0.1)
    oil_creases(f, back, [(19, 38, 1, 5), (30, 40, 1, 4)])
    coil(f, 34.5, 37.0, 2.6)                      # the coil rides on her back, her left side
    head = f.ellipse(27, 47.0, 11.5, 5.0)
    part(f, head, SKIN)
    shadow_under(f, back, (SKIN,), 1)
    for p in f.ellipse(27, 50.6, 7, 1.8):          # pale chin resting on the arms
        if p in head and p[1] >= 50:
            f.put(*p, BELLY, 4 if p[0] < 30 else 3)
    for cx in (20.5, 33.5):                        # eye bumps, shut: a lit lid over a dark lash arc
        b = f.ellipse(cx, 43.2, 3.4, 3.0)
        part(f, b, SKIN, glint=False)
        for p in b:                                # the bump's rim stands off the smock
            if (p[0], p[1] - 1) not in b:
                f.put(*p, SKIN, 2)
        c = int(cx)
        for p in ((c - 1, 42), (c, 42), (c + 1, 42)):
            f.put(*p, SKIN, 4)
        for p in ((c - 2, 43), (c - 1, 44), (c, 44), (c + 1, 44), (c + 2, 43)):
            f.put(*p, 'ink', 0)
    for x in range(22, 33):                        # a content smile
        f.put(x, 48, SKIN, 0)
    f.put(21, 47, SKIN, 0)
    f.put(33, 47, SKIN, 0)
    arms = f.rect(17, 51, 37, 53, knock=1)         # folded arms under the chin
    part(f, arms, SKIN, glint=False)
    for x in range(18, 37):
        if (x, 51) in arms and (x, 50) not in head:
            f.put(x, 51, SKIN, 2)
    f.put(27, 52, SKIN, 1)
    f.put(27, 53, SKIN, 1)
    mossling(f, 46.5, 53.5, -1, curled=True)
    finish_final(f)
    return f


FINAL_VIEWS = [
    ('S idle', lambda: (final_S(), None)), ('E idle', lambda: final_side(1, 'idle')),
    ('W idle', lambda: final_side(-1, 'idle')), ('S fidget', lambda: (final_S(True), None)),
    ('nap S', lambda: (final_nap(), None)),
    ('E ready', lambda: final_side(1, 'ready')), ('E strike', lambda: final_side(1, 'strike')),
    ('E cast', lambda: final_side(1, 'cast')), ('E hit', lambda: final_side(1, 'hit')),
    ('E sit', lambda: final_side(1, 'sit')), ('E cheer', lambda: final_side(1, 'cheer')),
    ('W ready', lambda: final_side(-1, 'ready')), ('W strike', lambda: final_side(-1, 'strike')),
]

FINAL = dict(
    label='B final', name='Short smock, braces, net coil and a pushed-back sou\'wester',
    chosen='B',
    grafts=["From A: a brass sou'wester pushed back off the head, hanging behind it on a chin cord "
            "(brim either side under the cheeks in S, edge on behind the head in E/W); the eye bumps stay the top of the silhouette.",
            'From C: berry braces over the smock in place of the net sash; the rolled net is a small three-loop coil on the back '
            'in every facing (one anchor, back layer).'],
    palette=['leaf', 'plaster', 'brass', 'berry', 'path'],
    pose='Springy and curious, weight on the toes of the wellies, chin up: always half a hop from the water.',
    fidget='Catches a fly: the mouth snaps open and a long berry tongue flicks out to the side (the same tongue is the strike).',
    parts=[
        'net coil | path | 0 back | anchor back (upper hip) | the same in all facings; S peeks past her left shoulder',
        "sou'wester (hanging) | brass | 1 | anchor back of head, chin cord to the jaw | S: brim either side; E/W: edge-on disc behind",
        'legs L/R (bare) | leaf | 2 | anchor hip | walk swing; far leg a tone down in profile; sit forward',
        'wellies L/R | berry | 2 | anchor foot | S/E/W; open top shows when sitting',
        'far arm + hand | leaf | 3 | anchor chest | E/W only, a tone down, behind the smock',
        'familiar perch | (familiar) | 4 | anchor back shoulder | E: x smaller, W: x larger; behind the head',
        'smock (stiff hem, creases) | brass | 5 | anchor hip | S/E/W; leans with the strike',
        'braces + buttons | berry, brass | 6 | anchor chest | S two straps, E/W the near strap',
        'near arm + stiff sleeve + hand | leaf, brass | 7 | anchor chest | walk, ready, strike, cast, hit, cheer',
        'head (form: brow, cheek, snout step, pale jaw) | leaf, plaster | 8 | anchor head | S/E/W',
        'eye bumps | leaf, plaster, ink | 9 | anchor head | blink, look, squeeze (hit), happy (cheer), half lid (sit)',
        'mouth + tongue | leaf, ink, berry | 10 | anchor head | smile, open, tongue (fidget, strike), ouch',
    ],
    notes=[
        'Oilskin: brass_warm with hard tone 5 creases on short diagonal folds, a stiff flared hem with a hard dark row under it.',
        'Braces sit on the smock; the net no longer crosses the chest, so cast and cheer keep the chest clear.',
        'Profiles: a snout step (the top front corner cut, the front plane lit in W and shaded in E), a brow recess under the eye bump, a lit cheek pair.',
        'Familiar: a 24 px grass-green Mossling stand-in on the back shoulder; it sits behind the head, so the eye bump stays the top of the silhouette.',
        'Compared with Eastward-04 (New Dam market: the fishmonger, John and the grocer scaled to ~36 px): head ~40%, 3 px eyes, 4 tones per garment, hard shadow under the hat brim.',
    ],
)


def build_final():
    views, nums, perches = [], {}, {}
    ok = True
    for cap, fn in FINAL_VIEWS:
        fig, perch = fn()
        img = fig.image()
        img.save(os.path.join(SCRATCH, f"final-{cap.replace(' ', '-')}.png"))
        views.append((cap, img))
        if perch:
            perches[cap] = perch
        m = sk.measure(img)
        g = gates(m, lone=0.04)
        bb = img.getbbox()
        ok &= all(g.values())
        nums[cap] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in m.items()}
        nums[cap]['height'] = bb[3] - bb[1]
        nums[cap]['bbox'] = list(bb)
        nums[cap]['gates_pass'] = all(g.values())
        print(f"final {cap:9s} h {bb[3] - bb[1]:2d} bbox {bb}  on house {100 * m['on_house']:5.1f}%  W-E {m['west_east']:+5.1f}  "
              f"lone {100 * m['isolated']:4.1f}%  colours {m['colours']:2d}  "
              f"outline dark {100 * m.get('outline_dark', 0):5.1f}%  "
              f"{'ok' if all(g.values()) else 'FAIL ' + ','.join(k for k, v in g.items() if not v)}")
    sk.design_sheet('Puddle final: B, the short smock (36 art px, cell 56 x 60)',
                    [dict(label='B final', name=FINAL['name'], views=views, parts=FINAL['parts'],
                          palette=FINAL['palette'], pose=FINAL['pose'],
                          notes=['Fidget: ' + FINAL['fidget']] + FINAL['grafts'] + FINAL['notes'])],
                    OUT_FINAL,
                    note='Grafts: sou\'wester pushed back (from A); braces and a back net coil (from C). Familiar: 24 px stand-in Mossling.')
    rec = {k: v for k, v in FINAL.items()}
    rec.update(perch_anchor=perches, measures=nums)
    print('final sheet', OUT_FINAL, '| all final gates pass' if ok else '| SOME FINAL GATES FAIL')
    return rec, ok


def main():
    os.makedirs(SCRATCH, exist_ok=True)
    sheet_opts, record = [], []
    all_ok = True
    for o in OPTIONS:
        views, nums = [], {}
        for key, cap in VIEWS:
            img = o['draw'](key).image()
            img.save(os.path.join(SCRATCH, f"{o['label']}-{cap.replace(' ', '-')}.png"))
            views.append((cap, img))
            m = sk.measure(img)
            g = gates(m)
            all_ok &= all(g.values())
            nums[cap] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in m.items()}
            nums[cap]['gates_pass'] = all(g.values())
            print(f"{o['label']} {cap:9s} on house {100 * m['on_house']:5.1f}%  W-E {m['west_east']:+5.1f}  "
                  f"lone {100 * m['isolated']:4.1f}%  colours {m['colours']:2d}  "
                  f"outline dark {100 * m.get('outline_dark', 0):5.1f}%  "
                  f"{'ok' if all(g.values()) else 'FAIL ' + ','.join(k for k, v in g.items() if not v)}")
        sheet_opts.append(dict(label=o['label'], name=o['name'], views=views, parts=o['parts'],
                               palette=o['palette'], pose=o['pose'],
                               notes=['Fidget: ' + o['fidget']] + o['notes']))
        record.append(dict(label=o['label'], name=o['name'], question=o['question'], parts=o['parts'],
                           palette=o['palette'], pose=o['pose'], fidget=o['fidget'], notes=o['notes'],
                           measures=nums))
    sk.design_sheet('Puddle: the oilskin cut and how much frog shows (36 art px, cell 56 x 60)',
                    sheet_opts, OUT_PNG,
                    note='Frog of the Lull, the bargee\'s apprentice. Leaf skin, plaster belly, brass oilskin, berry wellies.')
    final, final_ok = build_final()
    all_ok &= final_ok
    with open(OUT_JSON, 'w') as fh:
        json.dump(dict(id='puddle', height_art_px=36, cell=[W, H], anchor=[AX, AY],
                       question='The oilskin cut and how much frog shows', options=record,
                       final=final), fh, indent=1)
    print('sheet', OUT_PNG)
    print('all gates pass' if all_ok else 'SOME GATES FAIL')


if __name__ == '__main__':
    main()
