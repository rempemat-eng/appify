"""House-style lint (docs/vision/house-style.md): report only, it never fails a build.

Each lane runs it on its own sprites to see how far they sit from the house style:

    python3 scripts/art/style_lint.py castle_props western_props   # prop modules
    python3 scripts/art/style_lint.py castle_props --sprites        # every sprite, not just the worst
    python3 scripts/art/style_lint.py --png path/to/ground.png      # a ground or any PNG (1x)
    python3 scripts/art/style_lint.py --png exported.png --scale 4 # image px per world px

What it measures, per sprite (finalized as the zones finalize it):

- palette   share of pixels on the house palette (art/house-palette.json, within one just
            visible step, OKLab 0.02), share on today's shared ramps (art/materials.json),
            the number of distinct colours (house rule: at most 64 for a prop, 128 for a
            building over 2,500 px) and the house families they come from (for
            information; a ramp and its two siblings are one family).
- outline   of the silhouette's outer ring: the share that is dark enough to read as an
            outline (OKLab L at most 0.42, or 0.15 below the fill it closes); the share drawn
            in one flat ink rather than the material's own edge tone; and the share doubled
            (a second dark ring inside the first, with lighter fill behind it).
- light     upper left: the mean lightness of the west quarter of each row minus the east
            quarter, and of the top quarter of each column minus the bottom quarter (OKLab
            L x 100). Both should be positive.
- clusters  lone pixels (unlike all four neighbours) and checker dither (unlike its four
            neighbours, like its four diagonals) as shares of the inside. Rivets and glints
            are allowed lone pixels, so a little is fine; dither on a sprite is not.

Each line ends with the rules a sprite misses, by short name. Nothing here changes art.
"""
from __future__ import annotations

import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import house_palette as hp  # noqa: E402
from texel import native_image  # noqa: E402

MAX_COLOURS = 64         # a prop
MAX_COLOURS_BIG = 128    # a building (over 2,500 px)
ON_HOUSE_MIN = 0.90
OUTLINE_DARK_MIN = 0.95
FLAT_INK_MAX = 0.25
DOUBLE_MAX = 0.10
ISOLATED_MAX = 0.06
CHECKER_MAX = 0.005
NEAR = 0.02

_PAL = hp.load()
_HOUSE_MAP = hp.colours(_PAL)
_HOUSE = list(_HOUSE_MAP)
_HOUSE_LAB = [hp.to_oklab(c) for c in _HOUSE]
with open(os.path.join(HERE, '..', '..', 'art', 'materials.json')) as _f:
    _MAT = json.load(_f)
_TODAY = {hp.hex_rgb(c) for r in _MAT['materials'].values() for c in r}
_INKS = {hp.hex_rgb(_MAT['outline']), hp.hex_rgb(_PAL['ink'])}
_cache: dict = {}


def _lab(c):
    c = c[:3]
    if c not in _cache:
        _cache[c] = hp.to_oklab(c)
    return _cache[c]


_near_cache: dict = {}


def house_match(c):
    """The house (ramp, tone) a colour is, within NEAR, or None."""
    c = c[:3]
    if c not in _near_cache:
        p = _lab(c)
        best, bd = None, NEAR * NEAR
        for col, q in zip(_HOUSE, _HOUSE_LAB):
            d = sum((x - y) ** 2 for x, y in zip(p, q))
            if d <= bd:
                best, bd = _HOUSE_MAP[col], d
        _near_cache[c] = best
    return _near_cache[c]


def on_house(c) -> bool:
    return house_match(c) is not None


def measure(img, scale: float = 1) -> dict:
    """Numbers at one pixel per measured texel; scale is image px per world px.

    Existing callers pass native texels (scale 1). Exported PNG callers must pass
    their export scale so a finer outline or lone texel cannot be decimated away.
    """
    img, _density = native_image(img, scale)
    px = img.load()
    w, h = img.size
    solid = {(x, y) for y in range(h) for x in range(w) if px[x, y][3] == 255}
    if not solid:
        return {}
    N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    ring = {p for p in solid if any((p[0] + dx, p[1] + dy) not in solid for dx, dy in N4)}
    inside = solid - ring
    L = {p: _lab(px[p])[0] for p in solid}
    cols = {px[p][:3] for p in solid}
    out = {
        'px': len(solid), 'colours': len(cols),
        'on_house': sum(1 for p in solid if on_house(px[p])) / len(solid),
        'on_today': sum(1 for p in solid if px[p][:3] in _TODAY) / len(solid),
        'families': len({hp.family(m[0]) for m in (house_match(c) for c in cols) if m}),
    }
    # outline
    is_sprite = len(ring) < len(solid) * 0.9 and any(px[x, y][3] == 0 for x in (0, w - 1) for y in (0, h - 1))
    if is_sprite and ring:
        dark = flat = dbl = 0
        for (x, y) in ring:
            fill = [L[(x + dx, y + dy)] for dx, dy in N4 if (x + dx, y + dy) in inside]
            ok = L[(x, y)] <= 0.42 or bool(fill and L[(x, y)] <= max(fill) - 0.15)
            dark += ok
            flat += px[x, y][:3] in _INKS
            for dx, dy in N4:
                n = (x + dx, y + dy)
                m2 = (x + 2 * dx, y + 2 * dy)   # a dark second ring with lighter fill behind it
                if n in inside and m2 in solid and abs(L[n] - L[(x, y)]) < 0.04 and L[n] <= 0.42 \
                        and L[m2] > L[(x, y)] + 0.15:
                    dbl += 1
                    break
        out.update(outline_dark=dark / len(ring), flat_ink=flat / len(ring), double=dbl / len(ring))
    # light: west quarter minus east quarter of each row, top minus bottom of each column
    rows, colsx = {}, {}
    for (x, y) in inside:
        rows.setdefault(y, []).append(x)
        colsx.setdefault(x, []).append(y)
    we, tb = [], []
    for y, xs in rows.items():
        xs.sort()
        q = max(1, len(xs) // 4)
        if len(xs) >= 8:
            we.append(sum(L[(x, y)] for x in xs[:q]) / q - sum(L[(x, y)] for x in xs[-q:]) / q)
    for x, ys in colsx.items():
        ys.sort()
        q = max(1, len(ys) // 4)
        if len(ys) >= 8:
            tb.append(sum(L[(x, y)] for y in ys[:q]) / q - sum(L[(x, y)] for y in ys[-q:]) / q)
    out['west_east'] = 100 * sum(we) / len(we) if we else 0.0
    out['top_bottom'] = 100 * sum(tb) / len(tb) if tb else 0.0
    # clusters
    iso = chk = 0
    for (x, y) in inside:
        c = px[x, y][:3]
        nb = [px[x + dx, y + dy][:3] for dx, dy in N4]
        if all(n != c for n in nb):
            iso += 1
            dg = [(x + dx, y + dy) for dx, dy in ((1, 1), (-1, -1), (1, -1), (-1, 1))]
            if all(d in solid and px[d][:3] == c for d in dg):
                chk += 1
    out['isolated'] = iso / max(1, len(inside))
    out['checker'] = chk / max(1, len(inside))
    return out


def misses(m: dict) -> list:
    bad = []
    cap = MAX_COLOURS_BIG if m.get('px', 0) > 2500 else MAX_COLOURS
    if m.get('colours', 0) > cap:
        bad.append('colours')
    if m.get('on_house', 1) < ON_HOUSE_MIN:
        bad.append('palette')
    if 'outline_dark' in m and m['outline_dark'] < OUTLINE_DARK_MIN:
        bad.append('outline-light')
    if m.get('flat_ink', 0) > FLAT_INK_MAX:
        bad.append('outline-flat-ink')
    if m.get('double', 0) > DOUBLE_MAX:
        bad.append('outline-double')
    if m.get('west_east', 1) < 0:
        bad.append('light-west')
    if m.get('isolated', 0) > ISOLATED_MAX:
        bad.append('speckle')
    if m.get('checker', 0) > CHECKER_MAX:
        bad.append('dither')
    return bad


def line(name: str, m: dict) -> str:
    s = (f'{name:28s} {m["colours"]:5d} {m.get("families", 0):3d} {100 * m["on_house"]:5.0f}% {100 * m["on_today"]:5.0f}% ')
    if 'outline_dark' in m:
        s += f'{100 * m["outline_dark"]:5.0f}% {100 * m["flat_ink"]:5.0f}% {100 * m["double"]:5.0f}% '
    else:
        s += f'{"-":>6s} {"-":>6s} {"-":>6s} '
    s += (f'{m["west_east"]:+6.1f} {m["top_bottom"]:+6.1f} {100 * m["isolated"]:5.1f}% {100 * m["checker"]:5.1f}%  '
          + ' '.join(misses(m)))
    return s


HEAD = (f'{"sprite":28s} {"cols":>5s} {"fam":>3s} {"house":>6s} {"today":>6s} {"dark":>6s} {"ink":>6s} {"dbl":>6s} '
        f'{"W-E":>6s} {"T-B":>6s} {"lone":>6s} {"dith":>6s}  misses')


def lint_module(mod: str, every: bool = False, worst: int = 6) -> dict:
    import style
    props = importlib.import_module(mod).props()
    rows = {}
    for key, sp in props.items():
        try:
            fin = style.finalize(sp, name=key)
        except ValueError:
            continue
        m = measure(fin.img, fin.density)
        if m:
            rows[key] = m
    print(f'\n== {mod}: {len(rows)} sprites')
    print(HEAD)
    keys = sorted(rows, key=lambda k: (-len(misses(rows[k])), k))
    for k in (keys if every else keys[:worst]):
        print(line(k, rows[k]))
    agg = {f: sum(r.get(f, 0) for r in rows.values()) / max(1, len(rows))
           for f in ('colours', 'families', 'on_house', 'on_today', 'outline_dark', 'flat_ink', 'double',
                     'west_east', 'top_bottom', 'isolated', 'checker')}
    agg['colours'] = round(agg['colours'])
    agg['families'] = round(agg['families'])
    print('-' * len(HEAD))
    print(line('mean', agg))
    counts = {}
    for r in rows.values():
        for b in misses(r):
            counts[b] = counts.get(b, 0) + 1
    print('sprites missing each rule:', ', '.join(f'{k} {v}' for k, v in sorted(counts.items(), key=lambda kv: -kv[1])) or 'none')
    return agg


def main(argv) -> int:
    every = '--sprites' in argv
    args = [a for a in argv if not a.startswith('--')]
    if '--png' in argv:
        from PIL import Image
        path = argv[argv.index('--png') + 1]
        # --png historically accepts native 1x input; preserve that default.
        # Exported pictures can state the export scale, never the drawing density.
        scale = float(argv[argv.index('--scale') + 1]) if '--scale' in argv else 1
        m = measure(Image.open(path), scale)
        print(HEAD)
        print(line(os.path.basename(path)[:28], m))
        return 0
    if '--all' in argv or not args:
        args = sorted(f[:-3] for f in os.listdir(HERE) if f.endswith('_props.py'))
    for mod in args:
        lint_module(mod, every)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
