"""Water logic on a picture: stair-stepped banks, ruler-straight diagonal channels, falls
that are flat bars or fed by nothing, and bridges that do not reach both banks.

docs/vision/world-rules.md 7 (water), eastward-edges.md 1.4 to 1.6 and 5.3. Matt, 25 Oct,
on the woodland: "staircase-stepped water banks, a straight diagonal stream, a flat white bar
waterfall, a footbridge that doesn't span the banks".
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from .core import Finding, water_mask, foam_mask, regions, slice_box, hsv, keys, lum, green_mask

# Thresholds, as fractions of the character height H (calibrated on Matt's flagged woodland,
# the pilot golden and Eastward 08, 12, 13, 17 and 37; scripts/review/calibrate.py).
STAIR_MIN_STEPS = 4          # this many same-direction teeth in a row make a staircase
STAIR_MIN_RUN = 2            # a tooth's riser and tread are at least 2 px (1 px steps are a chamfer)
STAIR_MAX_RUN = 0.5          # treads up to 0.5 H: water is natural, so even whole-cell teeth are a fault
STRAIGHT_MIN_LEN = 1.5       # a straight diagonal channel at least 1.5 H long
STRAIGHT_MAX_RES = 1.4       # px of residual from the fitted line
BRIDGE_LAND = 0.10           # a bridge rests at least 0.1 H on land beyond each bank
FALL_FED_GAP = 0.25          # a fall's lip has water within 0.25 H above it


def _water(native, alpha=None):
    m = water_mask(native, alpha)
    m = ndi.binary_closing(m, iterations=1)
    m = ndi.binary_fill_holes(m)
    return m


def _profiles(comp: np.ndarray):
    """Edge profiles of one water body: for each row, its west and east edge; for each column,
    its north and south edge (only where the body is a single run, so channels are clean)."""
    out = []
    ys, xs = np.nonzero(comp)
    for axis in (0, 1):
        lines = comp if axis == 0 else comp.T
        idx = np.nonzero(lines.any(1))[0]
        lo = np.full(len(idx), np.nan)
        hi = np.full(len(idx), np.nan)
        for j, t in enumerate(idx):
            r = np.nonzero(lines[t])[0]
            if len(r) and r[-1] - r[0] + 1 == len(r):
                lo[j], hi[j] = r[0], r[-1] + 1
        out.append((axis, idx, lo, hi))
    return out


def _stairs(t, e, H):
    """Runs of staircase teeth in an edge profile e(t). Consecutive non-zero steps merge into
    one riser (a 2 px riser drawn as 1 + 1 is still one tooth); flat runs between risers are
    treads. A staircase is at least STAIR_MIN_STEPS risers of the same sign, each at least
    STAIR_MIN_RUN px, with treads of STAIR_MIN_RUN px to STAIR_MAX_RUN H that repeat evenly
    (coefficient of variation under 0.5): a diagonal drawn as equal teeth.
    Returns (t0, t1, n_teeth, mean riser, mean tread)."""
    found = []
    if len(e) < 6:
        return found
    maxtread = max(STAIR_MIN_RUN + 1, STAIR_MAX_RUN * H)
    teeth = []          # (k_start, riser, tread_before) or None for a break
    k = 0
    n = len(e)
    tread = 0
    while k < n - 1:
        d = e[k + 1] - e[k]
        if np.isnan(d) or t[k + 1] - t[k] != 1 or abs(d) > 0.25 * H:
            teeth.append(None)
            tread = 0
            k += 1
            continue
        if d == 0:
            tread += 1
            k += 1
            continue
        k0 = k
        rise = 0.0
        while k < n - 1 and not np.isnan(e[k + 1] - e[k]) and e[k + 1] - e[k] != 0 \
                and np.sign(e[k + 1] - e[k]) == np.sign(d) and t[k + 1] - t[k] == 1:
            rise += e[k + 1] - e[k]
            k += 1
        teeth.append((k0, rise, tread + 1))
        tread = 0
    run = []

    def flush():
        if len(run) >= STAIR_MIN_STEPS:
            tr = np.array([r[2] for r in run[1:]], float)
            if len(tr) and tr.std() / max(tr.mean(), 1e-6) < 0.5:
                k0 = max(0, run[0][0] - int(run[0][2]))
                k1 = min(n - 1, run[-1][0] + 2)
                found.append((t[k0], t[k1], len(run), float(np.mean([abs(r[1]) for r in run])), float(tr.mean())))
    for tooth in teeth:
        good = tooth is not None and abs(tooth[1]) >= STAIR_MIN_RUN and tooth[2] <= maxtread
        if good and run and tooth[2] < STAIR_MIN_RUN:
            good = False
        if good and run and np.sign(tooth[1]) != np.sign(run[-1][1]):
            flush()
            run = []
        if good:
            run.append(tooth)
        else:
            flush()
            run = [tooth] if (tooth is not None and abs(tooth[1]) >= STAIR_MIN_RUN) else []
    flush()
    return found


def _straight(t, e, H):
    """Long straight diagonal stretches of an edge profile: windows of at least
    STRAIGHT_MIN_LEN H whose points sit within STRAIGHT_MAX_RES px of one line with a slope
    between 0.25 and 4 (not along x or y)."""
    found = []
    ok = ~np.isnan(e)
    L = int(STRAIGHT_MIN_LEN * H)
    if ok.sum() < L:
        return found
    tt, ee = t[ok].astype(float), e[ok]
    # judge straightness at the scale of the plan, not the pixel: a stair of small teeth on a
    # ruler line is still a ruler line
    win = max(3, int(0.3 * H) | 1)
    if len(ee) > win:
        pad = np.pad(ee, win // 2, mode='edge')
        ee = np.convolve(pad, np.ones(win) / win, mode='valid')
    tol = max(STRAIGHT_MAX_RES, 0.05 * H)
    j = 0
    while j + L <= len(tt):
        w = slice(j, j + L)
        if tt[j + L - 1] - tt[j] > 1.15 * L:
            j += L // 4
            continue
        A = np.vstack([tt[w], np.ones(L)]).T
        coef, *_ = np.linalg.lstsq(A, ee[w], rcond=None)
        res = np.abs(A @ coef - ee[w]).max()
        if res <= tol and 0.08 <= abs(coef[0]) <= 12:
            k = j + L
            while k < len(tt):          # grow while it stays straight
                A2 = np.vstack([tt[j:k + 1], np.ones(k + 1 - j)]).T
                c2, *_ = np.linalg.lstsq(A2, ee[j:k + 1], rcond=None)
                if np.abs(A2 @ c2 - ee[j:k + 1]).max() > tol:
                    break
                coef = c2
                k += 1
            found.append((tt[j], tt[k - 1], float(coef[0]), k - j))
            j = k
        else:
            j += max(1, L // 6)
    return found


def check_banks(native, H, alpha=None) -> list[Finding]:
    fs = []
    m = _water(native, alpha)
    lab, regs = regions(m, min_area=int(0.15 * H * H))
    for lid, sl, area in regs:
        comp = lab == lid
        box = slice_box(sl)
        stairs, straights = [], []
        for axis, idx, lo, hi in _profiles(comp):
            for e in (lo, hi):
                for (t0, t1, n, rise, tread) in _stairs(idx, e, H):
                    stairs.append((axis, t0, t1, n, rise, tread, e))
                pass
            a_lo = _straight(idx, lo, H)
            a_hi = _straight(idx, hi, H)
            # a ruler channel: both banks straight, parallel, over the same stretch
            for (t0, t1, slope, n) in a_lo:
                for (u0, u1, sl2, n2) in a_hi:
                    ov = min(t1, u1) - max(t0, u0)
                    if ov >= 0.5 * min(n, n2) and abs(slope - sl2) <= 0.15:
                        straights.append((axis, max(t0, u0), min(t1, u1), slope, int(ov), lo, idx))
        # one finding per staircase stretch, boxed in picture coordinates
        for axis, t0, t1, n, rise, tread, e in stairs:
            sel = (np.arange(len(e)))
            if axis == 0:     # profile along rows: t is y, e is x
                xs = [v for v in e if not np.isnan(v)]
                b = (int(np.nanmin(e)) - 2, int(t0) - 2, int(np.nanmax(e)) + 2, int(t1) + 2)
                seg = comp[int(t0):int(t1) + 1]
                xs = np.nonzero(seg.any(0))[0]
            else:
                b = (int(t0) - 2, int(np.nanmin(e)) - 2, int(t1) + 2, int(np.nanmax(e)) + 2)
            # narrow the box to the stretch itself
            if axis == 0:
                rows = slice(int(t0), int(t1) + 1)
                ev = e[(np.arange(len(e)) >= 0)]
            fs.append(Finding('logic.water_staircase', 'fault', _stretch_box(comp, axis, t0, t1),
                              f'water bank steps in a staircase of {n} teeth ({rise:.0f} px risers, '
                              f'{tread:.0f} px treads) along a diagonal',
                              'redraw the bank as a straight run along x or y that turns only at cell lines, '
                              'with 1 px wobble and rounded or chamfered corners (eastward-edges.md 1.4 to 1.6), '
                              'or as a smooth natural curve; never a run of equal teeth',
                              score=float(n), threshold=STAIR_MIN_STEPS, subject='water bank'))
        for axis, t0, t1, slope, n, e, idx in straights:
            fs.append(Finding('logic.water_straight', 'fault', _stretch_box(comp, axis, t0, t1),
                              f'both banks run ruler-straight and parallel on a diagonal for {n} px ({n / H:.1f} H): a drawn channel, not a stream',
                              'a stream follows the land: give it bends, pools and narrows, or lay a man-made '
                              'channel along x or y with a built edge (world-rules.md 7, art-faults rule 3)',
                              score=n / H, threshold=STRAIGHT_MIN_LEN, subject='water edge'))
    return _dedupe(fs)


def _stretch_box(comp, axis, t0, t1):
    t0, t1 = int(t0), int(t1) + 1
    if axis == 0:
        seg = comp[t0:t1]
        xs = np.nonzero(seg.any(0))[0]
        return (int(xs.min()) - 2, t0 - 2, int(xs.max()) + 3, t1 + 2) if len(xs) else (0, t0, 1, t1)
    seg = comp[:, t0:t1]
    ys = np.nonzero(seg.any(1))[0]
    return (t0 - 2, int(ys.min()) - 2, t1 + 2, int(ys.max()) + 3) if len(ys) else (t0, 0, t1, 1)


def _dedupe(fs):
    from .core import merge_findings
    return merge_findings(fs, iou=0.25)


# ------------------------------------------------------------------------------------------
def fall_mask(native):
    """A fall: a tall narrow band of pale or foamy blue-white water."""
    h, s, v = hsv(native)
    pale = (v >= 0.6) & (s <= 0.45) & (((h >= 180) & (h <= 240)) | (s <= 0.1))
    blue = water_mask(native)
    m = pale | (blue & ndi.binary_dilation(pale, iterations=2))
    return m


def check_falls(native, H) -> list[Finding]:
    fs = []
    m = fall_mask(native)
    lab, regs = regions(m, min_area=int(0.03 * H * H))
    water = _water(native)
    for lid, sl, area in regs:
        x0, y0, x1, y1 = slice_box(sl)
        w, hgt = x1 - x0, y1 - y0
        if hgt < 0.4 * H or hgt < 2.2 * w:
            continue
        comp = lab == lid
        if (comp[y0:y1, x0:x1].mean()) < 0.55:
            continue
        # a fall ends in water: a pool or stream within 0.3 H below its foot (ice and crystals do not)
        pool = water[y1 - 2:min(native.shape[0], y1 + int(0.3 * H)), max(0, x0 - 4):x1 + 4]
        if pool.sum() < 0.5 * w:
            continue
        # flat: a bar of constant width with straight sides and two tones doing most of the work
        sub = comp[y0:y1, x0:x1]
        rows = [np.nonzero(r)[0] for r in sub]
        widths = np.array([r[-1] - r[0] + 1 if len(r) else 0 for r in rows], float)
        q = len(widths) // 6
        widths = widths[q:len(widths) - q]          # the body, not the lip cap or the splash
        cv = float(widths.std() / max(widths.mean(), 1e-6))
        k = keys(native[y0:y1, x0:x1], 32)[sub]
        vals, cnt = np.unique(k, return_counts=True)
        top2 = np.sort(cnt)[::-1][:2].sum() / cnt.sum()
        # what it falls past: a fall drops over a face, so its flanks are rock or cliff, not turf
        ring = ndi.binary_dilation(comp, iterations=2) & ~comp & ~m
        g = green_mask(native) & ring
        turf = float(g.sum() / max(1, ring.sum()))
        if cv < 0.2 and top2 >= 0.5 and hgt >= 1.2 * H:
            fs.append(Finding('detail.fall_flat', 'fault', (x0, y0, x1, y1),
                              f'the fall is a flat bar: constant width (cv {cv:.2f}), straight sides, the two '
                              f'main tones cover {top2:.0%}',
                              'draw the fall as falling water: a white lip, streaks in 4 to 5 tones that '
                              'wander and break, a width that swells where it hits rock, spray and a churned '
                              'plunge pool (world-rules.md 7.2)', score=top2, threshold=0.5, subject='waterfall'))
        if turf > 0.2:
            fs.append(Finding('logic.fall_face', 'fault', (x0 - 3, y0, x1 + 3, y1),
                              f'the fall drops past turf ({turf:.0%} of its flanks are grass), not over a face',
                              'a fall needs a drop: put a rock or cliff face behind it from lip to pool, '
                              'with the lip on the higher ground (world-rules.md 7.2)',
                              score=turf, threshold=0.2, subject='waterfall'))
        # fed: water just above the lip
        gap = int(FALL_FED_GAP * H)
        above = water[max(0, y0 - gap):y0, max(0, x0 - 2):x1 + 2]
        if above.sum() < 0.3 * w:
            fs.append(Finding('logic.water_source', 'fault', (x0 - 4, max(0, y0 - gap), x1 + 4, y0 + 8),
                              'the fall pours from nothing: no stream or pool feeds its lip',
                              'run the stream to the lip and over it, as wide as the fall, or start the '
                              'water at a drawn spring (world-rules.md 7.1 and 7.2)',
                              score=float(above.sum()), threshold=0.3 * w, subject='waterfall'))
    return fs


# ------------------------------------------------------------------------------------------
def check_bridges(native, H) -> list[Finding]:
    """A crossing shows as one water body cut in two by a band that is not water: the bridge.
    Its deck (the colours found where the water would be) must carry on past both banks by
    BRIDGE_LAND H."""
    fs = []
    m = _water(native)
    lab, regs = regions(m, min_area=int(0.1 * H * H))
    boxes = [(lid, slice_box(sl)) for lid, sl, a in regs]
    k16 = keys(native, 16)
    for i, (la, A) in enumerate(boxes):
        for lb, B in boxes:
            if la == lb:
                continue
            # horizontal stream cut by a north-south bridge: A west of B
            if not (0 <= B[0] - A[2] <= 0.9 * H):
                continue
            ca, cb = lab == la, lab == lb
            ea = ca[:, max(A[0], A[2] - 3):A[2]]
            eb = cb[:, B[0]:B[0] + 3]
            ya, yb = np.nonzero(ea.any(1))[0], np.nonzero(eb.any(1))[0]
            if not len(ya) or not len(yb):
                continue
            top, bot = min(ya.min(), yb.min()), max(ya.max(), yb.max()) + 1
            if min(ya.max(), yb.max()) < max(ya.min(), yb.min()):
                continue            # not facing each other
            gx0, gx1 = A[2], B[0]
            if gx1 - gx0 < 4:
                continue
            cx0, cx1 = gx0 + (gx1 - gx0) // 5, gx1 - (gx1 - gx0) // 5
            mid = k16[top + 2:bot - 2, cx0:cx1]
            if mid.size == 0:
                continue
            deck = set(np.unique(mid).tolist())

            def reach(direction):
                y = top - 1 if direction < 0 else bot
                n = 0
                while 0 <= y < native.shape[0] and n < H:
                    row = k16[y, cx0:cx1]
                    if np.isin(row, list(deck)).mean() < 0.5:
                        break
                    n += 1
                    y += direction
                return n
            up, down = reach(-1), reach(+1)
            need = BRIDGE_LAND * H
            if min(up, down) < need:
                fs.append(Finding('logic.bridge_span', 'fault', (gx0 - 3, top - int(0.3 * H), gx1 + 3, bot + int(0.3 * H)),
                                  f'the bridge does not reach both banks: its deck rests {up} px past the north '
                                  f'bank and {down} px past the south bank (needs {need:.0f})',
                                  'lengthen the deck so both ends land on dry ground with an abutment or sleeper '
                                  'on each bank, and the path meeting each end (world-rules.md 7.5)',
                                  score=float(min(up, down)), threshold=need, subject='bridge'))
    return fs
