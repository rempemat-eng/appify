"""Trees whose trunks are not oak: the birch and the beech, their crowns painted from the 1x
master (foliage.py) on a trunk drawn for the species, and the checks that keep a tree whole
(Claude B, lane B; lane R 25 Oct 17:08 findings 3 and 4).

Why: the kit's tree path reads a master's trunk by colour (red-brown wood), so a pale birch
trunk and a grey beech trunk were read as foliage or not at all. The birch was painted whole as
foliage, which left a broken ochre stripe for a trunk; the beech's grey-green bark was read as
leaves and its crown painted down over a short oak stub. Here the trunk is read by shape
instead: the master's narrow column under its crown, whatever its colour.

    split_master(A)            the crown alone and the trunk's geometry (master px)
    trunk4(d, species, ...)    a birch or beech trunk in props.py's 2x units
    tree_sprite(A, d, seed, species)  (img, anchor, alpha, ex): the crown on its trunk
    trunk_connected(alpha, foot)      faults if the trunk does not run unbroken from the foot
                                      into the crown
    crown_opacity(alpha)              the share of the crown's row hull that is drawn

The birch: chalk-white bark (plaster), lit on the left and cool grey on the right, dark
lenticel dashes across it, black diamond scars under old branches, and the bark darkening and
fissuring towards the foot. The beech: smooth pewter-grey bark (stone_cool), a soft lit band,
faint rings, a few lighter lichen flecks and buttressed roots spreading at the foot.
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from . import foliage as F5
from . import raster as pk
from .props import _out, _sprite

SPECIES = ('birch', 'beech')
CROWN_FLOOR = 0.9      # a crown's opaque share of its row hull (the d2 crowns: 0.97 to 0.99)


# ------------------------------------------------------------------------------------------------
def split_master(A: np.ndarray, grow: float = 1.5, flare_rows: int = 6):
    """(crown-only master, trunk) from a 1x tree master. The trunk is the column at the bottom:
    going up from above the root flare (the last `flare_rows`), the rows stay within `grow`
    times the trunk's own width (its median over the 8 rows above the flare); the first wider
    row is the crown. trunk = dict(x0, x1, cx, top, foot, w) in master px."""
    al = A[..., 3] > 0
    H1, W1 = al.shape
    widths = np.array([np.count_nonzero(al[y]) for y in range(H1)])
    rows = np.nonzero(widths)[0]
    foot = int(rows.max()) + 1
    ref = widths[max(0, foot - flare_rows - 8):foot - flare_rows]
    ref = ref[ref > 0]
    wref = float(np.median(ref)) if len(ref) else 4.0
    lim = max(wref * grow, wref + 3)
    top = foot - flare_rows
    y = top - 1
    while y >= 0 and 0 < widths[y] <= lim:
        top = y
        y -= 1
    trunk = np.zeros_like(al)
    trunk[top:foot] = al[top:foot]
    mid = [np.nonzero(al[yy])[0] for yy in range(top, max(top + 1, foot - flare_rows))]
    mid = [r for r in mid if len(r)]
    xs0 = np.median([r.min() for r in mid]) if mid else W1 / 2 - 2
    xs1 = np.median([r.max() for r in mid]) + 1 if mid else W1 / 2 + 2
    crown = A.copy()
    crown[trunk] = 0
    return crown, dict(x0=float(xs0), x1=float(xs1), cx=float((xs0 + xs1) / 2), top=int(top), foot=foot,
                       w=float(xs1 - xs0), mask=trunk)


# ------------------------------------------------------------------------------------------------
def trunk4(d, species, length, width, seed=5, into=10.0):
    """A trunk `length` world px from the foot to where the crown starts, `width` world px
    wide, carried `into` world px on up behind the crown. Returns (img, (ax, ay) foot, alpha)."""
    rng = np.random.default_rng(seed)
    L, Wd, In = length * 2.0, width * 2.0, into * 2.0
    hw = Wd / 2
    pad = 12 if species == 'beech' else 8
    sp = _sprite(d, Wd + 2 * pad + 10, L + In + 8, (Wd + 2 * pad + 10) / 2, 3)
    g = sp.g
    top = -(L + In)
    taper = 0.78 if species == 'birch' else 0.86
    flare = 2.0 if species == 'birch' else 5.5
    pts = [(-hw * taper, top), (hw * taper, top), (hw, -L * 0.35), (hw + flare * 0.35, -5.0),
           (hw + flare, -0.6), (hw * 0.4, -1.2), (0.0, 0.0), (-hw * 0.4, -1.2), (-hw - flare, -0.4),
           (-hw - flare * 0.35, -5.0), (-hw, -L * 0.35)]
    tr = pk.round_mask(g.poly(pts), 1)
    if species == 'beech':                        # buttress roots: two more spreading ribs
        for sx in (-1, 1):
            tr |= g.capsule(sx * hw * 0.5, -7.0, sx * (hw + flare + 1.5), -0.4, 1.4, 0.9)
    if species == 'birch':
        sp.add('trunk', tr, 'plaster', base=4, lo=2, hi=5, z=1, mode='cyl', k=1.1)
        p = sp.part('trunk')
        # the shaded third turns cool grey, the lit edge stays chalk
        u = (g.X + hw) / max(1.0, Wd)
        p.famarr = np.where(u > 0.66, 'stone_cool', 'plaster').astype(object)
        sp.mark('trunk', u > 0.66, 1)
        sp.mark('trunk', u > 0.86, -1)
        # dark bark patches where the white has cracked off, in bands across the trunk
        for _ in range(int(L / 14)):
            y = rng.uniform(top + In, -L * 0.25)
            x0 = rng.uniform(-hw, 0)
            sp.mark('trunk', g.capsule(x0, y, x0 + rng.uniform(hw * 0.6, Wd), y + rng.uniform(-0.8, 0.8), 0.9), -2)
        # lenticels: short dark dashes across the trunk, in clusters, densest low down
        dash = np.zeros_like(tr)
        for _ in range(int(L / 1.5)):
            y = rng.uniform(top + 2, -4)
            x0 = rng.uniform(-hw, hw * 0.4)
            ln = rng.uniform(1.6, hw * 0.9)
            dash |= g.capsule(x0, y, min(hw, x0 + ln), y + rng.uniform(-0.3, 0.3), 0.45)
        sp.add('lenticel', dash & tr, 'stone', base=1, lo=0, hi=2, z=1.5, flat=True, outline=False, casts=False)
        sp.mark('lenticel', g.X > hw * 0.3, -1)
        # black diamond scars under old branches, and one branch stub up into the crown
        for _ in range(int(rng.integers(2, 4))):
            cx, cy = rng.uniform(-hw * 0.5, hw * 0.5), rng.uniform(top + In * 0.6, -L * 0.3)
            sc = g.poly([(cx, cy - 2.2), (cx + 1.6, cy), (cx, cy + 1.4), (cx - 1.6, cy)])
            sp.add(f'scar{_}', sc & tr, 'stone', base=0, lo=0, hi=1, z=1.6, flat=True, outline=False, casts=False)
        # the foot: the bark dark and fissured
        base = tr & (g.Y > -L * 0.18)
        fis = np.zeros_like(tr)
        for _ in range(int(Wd / 2.5)):
            x = rng.uniform(-hw - 1, hw + 1)
            fis |= g.capsule(x, -0.5, x + rng.uniform(-0.5, 0.5), -L * rng.uniform(0.08, 0.2), 0.55)
        sp.add('foot', base, 'stone_warm', base=2, lo=0, hi=3, z=1.4, mode='cyl', k=1.0)
        sp.mark('foot', fis, -1)
        sp.mark('foot', g.Y < -L * 0.15, 1)
    else:
        sp.add('trunk', tr, 'stone_cool', base=3, lo=1, hi=5, z=1, mode='cyl', k=1.0)
        # smooth bark: a soft lit band on the left, faint rings, lichen flecks, darker roots
        u = (g.X + hw) / max(1.0, Wd)
        sp.mark('trunk', (u > 0.12) & (u < 0.3) & (g.Y < -6), 1)
        for _ in range(int(L / 7)):
            y = rng.uniform(top + 3, -8)
            sp.mark('trunk', g.capsule(-hw, y, hw * rng.uniform(0.2, 0.9), y + rng.uniform(-0.6, 0.6), 0.4), -1)
        fl = np.zeros_like(tr)
        for _ in range(int(L / 9)):
            fl |= g.ellipse(rng.uniform(-hw * 0.7, hw * 0.2), rng.uniform(top + 4, -10), rng.uniform(0.8, 1.4), 0.7)
        if (fl & tr).any():
            sp.add('fleck', fl & tr, 'stone', base=4, lo=3, hi=5, z=1.5, flat=True, outline=False, casts=False)
        sp.mark('trunk', g.Y > -3.0, -1)
    # the dark band where the crown's shade falls on the trunk (hidden higher up by the crown)
    sp.mark('trunk', g.Y < -L + 3.0, -1)
    return _out(sp)


# ------------------------------------------------------------------------------------------------
def tree_sprite(A: np.ndarray, d, seed, species, crease_depth=1.5):
    """The master's crown painted at density d on the species' trunk, joined: the trunk runs up
    behind the crown, so no gap shows. Returns (img, anchor (foot, texels), alpha, ex)."""
    assert species in SPECIES, species
    crown, tk = split_master(A)
    out, _, (pad, sx, sy) = F5.paint(crown, d, seed=seed, blossoms=False, legs=False, crease_depth=crease_depth)
    cal = out[..., 3] > 0
    H1, W1 = A.shape[:2]
    length = tk['foot'] - tk['top']
    into = max(6.0, (H1 - length) * 0.3)
    tr, (tax, tay), _ = trunk4(d, species, length, max(3.0, tk['w']), seed=seed + 1, into=into)
    fx, fy = pad + tk['cx'] * sx, pad + tk['foot'] * sy       # the trunk foot in the crown image
    oxc, oyc = max(0.0, tax - fx), max(0.0, tay - fy)         # where the crown image goes
    oxt, oyt = oxc + fx - tax, oyc + fy - tay                 # and the trunk image
    Wc = int(np.ceil(max(oxc + out.shape[1], oxt + tr.width)))
    Hc = int(np.ceil(max(oyc + out.shape[0], oyt + tr.height)))
    c = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0))
    c.alpha_composite(tr, (int(round(oxt)), int(round(oyt))))
    c.alpha_composite(Image.fromarray(out), (int(round(oxc)), int(round(oyc))))
    a = np.asarray(c)[..., 3] > 0
    ys, xs = np.nonzero(a)
    anc = ((xs.min() + xs.max() + 1) / 2, ys.max() + 1)
    crown_rows = np.nonzero(cal.any(1))[0]
    ch = (crown_rows.max() + 1 - crown_rows.min()) / d if len(crown_rows) else H1 / 2
    ex = dict(w=W1, h=H1, tw=int(np.clip(round(tk['w']), 3, W1 * 0.2)), ch=int(ch * 0.9),
              foot=(oxt + tax, oyt + tay), crown_mask_rows=(int(oyc + crown_rows.min()), int(oyc + crown_rows.max() + 1)))
    return c, anc, a, ex


# ------------------------------------------------------------------------------------------------
def crown_opacity(alpha: np.ndarray, rows=None) -> float:
    """The drawn share of the row hull (each row from its first to its last opaque texel)."""
    ys = np.nonzero(alpha.any(1))[0]
    if rows is not None:
        ys = ys[(ys >= rows[0]) & (ys < rows[1])]
    hull = fill = 0
    for y in ys:
        r = np.nonzero(alpha[y])[0]
        hull += r.max() - r.min() + 1
        fill += len(r)
    return fill / max(1, hull)


def trunk_connected(alpha: np.ndarray, foot=None, d: float = 2.0) -> list:
    """Faults if the tree does not stand on one unbroken trunk: going up from the foot, a band
    a texel either side of the trunk's centre is drawn in every row until the row widens into
    the crown (2.5 times the trunk), and the whole picture is one piece (bar specks)."""
    out = []
    ys, xs = np.nonzero(alpha)
    if not len(ys):
        return ['nothing drawn']
    y1 = ys.max()
    if foot is None:
        r = np.nonzero(alpha[y1 - max(1, int(2 * d))])[0]
        cx = (r.min() + r.max()) / 2
    else:
        cx = foot[0]
    cx = int(round(cx))
    # trunk width a little above the root flare
    yr = y1 - int(6 * d)
    r = np.nonzero(alpha[yr])[0]
    tw = (r.max() - r.min() + 1) if len(r) else 3
    y = y1 - max(1, int(round(d)))          # above the outline and the roots' notch
    while y >= ys.min():
        r = np.nonzero(alpha[y])[0]
        if len(r) and r.max() - r.min() + 1 > 2.5 * tw and y < yr:
            break
        band = alpha[y, max(0, cx - 1):cx + 2]
        if not band.all():
            out.append(f'trunk broken at texel row {y} ({(y1 - y) / d:.0f} world px above the foot)')
            break
        y -= 1
    if y < ys.min():
        out.append('no crown above the trunk')
    lab, n = ndi.label(alpha)
    if n > 1:
        sizes = ndi.sum(alpha, lab, range(1, n + 1))
        main = sizes.max()
        loose = sizes.sum() - main
        if loose > 0.02 * alpha.sum():
            out.append(f'{n} pieces, {loose / alpha.sum():.1%} of it apart from the tree')
    return out
