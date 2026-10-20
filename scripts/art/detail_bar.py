"""The detail bar: is our art as detailed as the reference, at the same character height?

Matt, 20 Oct 01:19 and 01:24: "eastward level of detail is what you should be aiming for",
"it has to be reached" (AGENTS.md, art-style.md). This makes the comparison a number.

How it measures. Both images are brought to the same scale: the reference is resampled so
its adult stands as tall as ours (A = 25 px), each new pixel taking the most common colour of
the block it covers (so no blended in-between colours are invented and JPEG noise drops
out). Colours are quantised to 16 levels a channel. Then, per 16 x 16 px patch:

- tones     distinct colours covering at least 2 px
- shapes    4-connected regions of one colour of at least 2 px
- dressing  small regions (2 to 12 px) that are not the patch's main colour: tufts,
            pebbles, chips, flowers, highlights

and two cleanliness counts (art-style.md: detail comes in clusters of two or more pixels,
never single-pixel noise), so the bar cannot be met with speckle:

- isolated  the share of pixels whose colour differs from all four neighbours
- cluster   the mean size in px of the patch's one-colour regions

A surface passes when tones, shapes and dressing each reach TOLERANCE of the reference's
mean for the same kind of surface (face, rim, side, corner, stair, foot, ground), its
isolated share is at most the reference's plus ISOLATED_MARGIN, and its mean cluster is
at least CLUSTER_SHARE of the reference's.

Fair to compression. The references are official JPEG screenshots, and JPEG ringing adds
tones (a control: our own sheet blown up 6x and saved at quality 85 gains 5 tones a patch,
1 to 3 shapes). So ours is judged through the same pipe: scaled up to the reference's
adult height, saved as JPEG at the quality estimated from the reference's quantisation
table, and brought back down.

The reference baselines are numbers only, in detail_baselines.json, each with the official
URL of its screenshot, its box and its adult's height there; the images stay out of the
repo. `--measure` adds or refreshes one from a local copy of that screenshot.

Measuring your own art without the reference images. Every lane can check a sprite or a
ground against the numbers alone; the screenshots are only needed to add a baseline.

1. Render the thing at 1x (an adult resident 25 px tall, as every generator draws). A
   sprite on transparency: paste it on the ground it will stand on first, since a
   transparent background would count as a colour.
2. Pick a box that holds only the surface being judged, at least 34 px each way (two whole
   16 px patches and the 2 px resampling rounds away); a box a little larger than a
   multiple of 16 wastes nothing.
3. Run `python3 scripts/art/detail_bar.py MINE.png --box X0 Y0 X1 Y1 --kind roof`.
   The kinds and their reference values: `--list`. In a generator:
   `ok, counts, lines = detail_bar.check_image(img, box, 'roof')`.
4. FAIL with LOW means too little detail for that kind; NOISY means the detail is speckle
   (single pixels, tiny clusters): draw it as shapes of two or more pixels instead.

Kinds with baselines: face, rim, side, corner, stair, foot, ground, water (ponds and
channels with their banks), wood-front (plank walls, shop and false fronts), stone-wall
(stone footings and dressed walls), machinery (vehicles, hatches, metal), roof (tiles and
slates), facade (town fronts with windows and signs), hedge, tree (crowns), paving.

Run:
  python3 scripts/art/detail_bar.py OURS.png --box X0 Y0 X1 Y1 --kind face [--adult 25]
  python3 scripts/art/detail_bar.py --measure SHOT.jpg --box X0 Y0 X1 Y1 --adult 162 \\
      --key eastward-13-rim --kind rim --url https://...  [--game Eastward]
  python3 scripts/art/detail_bar.py --list
(terrace.py --bar runs it on the terrace test sheet, every kind at once.)
"""
from __future__ import annotations

import io
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINES = os.path.join(HERE, 'detail_baselines.json')
ADULT = 25          # our adult resident, feet to crown (verticality.md 5)
PATCH = 16
STEP = 16           # quantisation step a channel (16 levels)
TOLERANCE = 0.9     # ours must reach 90 % of the reference on every count
ISOLATED_MARGIN = 0.02   # and be no noisier: at most 2 points more isolated pixels
CLUSTER_SHARE = 0.9      # and clusters at least 90 % as large
KINDS = ('face', 'rim', 'side', 'corner', 'stair', 'foot', 'ground', 'water', 'wood-front', 'stone-wall',
         'machinery', 'roof', 'facade', 'hedge', 'tree', 'paving')


def quantised(img: Image.Image) -> np.ndarray:
    a = np.asarray(img.convert('RGB'), dtype=np.int32) // STEP
    return a[..., 0] * 256 + a[..., 1] * 16 + a[..., 2]


def to_scale(img: Image.Image, adult: float) -> np.ndarray:
    """The image as quantised colour keys at our scale (its adult = ADULT px): each output
    pixel is the most common key in the block of source pixels it covers."""
    key = quantised(img)
    f = adult / ADULT
    if abs(f - 1) < 1e-6:
        return key
    h, w = key.shape
    oh, ow = int(h / f), int(w / f)
    out = np.zeros((oh, ow), np.int32)
    for y in range(oh):
        y0, y1 = int(y * f), max(int(y * f) + 1, int((y + 1) * f))
        for x in range(ow):
            x0, x1 = int(x * f), max(int(x * f) + 1, int((x + 1) * f))
            v, c = np.unique(key[y0:y1, x0:x1], return_counts=True)
            out[y, x] = v[c.argmax()]
    return out


def _regions(k: np.ndarray):
    """Sizes of the 4-connected one-colour regions of a patch."""
    h, w = k.shape
    seen = np.zeros(k.shape, bool)
    sizes = []
    for y in range(h):
        for x in range(w):
            if seen[y, x]:
                continue
            st, n = [(y, x)], 0
            seen[y, x] = True
            while st:
                a, b = st.pop()
                n += 1
                for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    c, d = a + da, b + db
                    if 0 <= c < h and 0 <= d < w and not seen[c, d] and k[c, d] == k[a, b]:
                        seen[c, d] = True
                        st.append((c, d))
            sizes.append((int(k[y, x]), n))
    return sizes


def counts(key: np.ndarray) -> dict:
    """Mean tones, shapes and dressing per PATCH x PATCH square (whole patches only)."""
    t, s, d, iso, cl = [], [], [], [], []
    h, w = key.shape
    pad = np.pad(key, 1, mode='edge')
    lone = (pad[1:-1, 1:-1] != pad[:-2, 1:-1]) & (pad[1:-1, 1:-1] != pad[2:, 1:-1]) & \
        (pad[1:-1, 1:-1] != pad[1:-1, :-2]) & (pad[1:-1, 1:-1] != pad[1:-1, 2:])
    for y in range(0, h - PATCH + 1, PATCH):
        for x in range(0, w - PATCH + 1, PATCH):
            k = key[y:y + PATCH, x:x + PATCH]
            v, c = np.unique(k, return_counts=True)
            main = v[c.argmax()]
            t.append(int((c >= 2).sum()))
            regs = _regions(k)
            s.append(sum(1 for (_v, n) in regs if n >= 2))
            d.append(sum(1 for (v2, n) in regs if 2 <= n <= 12 and v2 != main))
            iso.append(float(lone[y:y + PATCH, x:x + PATCH].mean()))
            cl.append(PATCH * PATCH / len(regs))
    if not t:
        raise ValueError(f'detail_bar: the box is smaller than one {PATCH} px patch at our scale')
    return {'tones': round(float(np.mean(t)), 2), 'shapes': round(float(np.mean(s)), 2),
            'dressing': round(float(np.mean(d)), 2), 'isolated': round(float(np.mean(iso)), 3),
            'cluster': round(float(np.mean(cl)), 2), 'patches': len(t)}


def jpeg_quality(img: Image.Image) -> int | None:
    """The libjpeg quality whose luminance table matches the image's, or None (not a JPEG)."""
    q = getattr(img, 'quantization', None)
    if not q:
        return None
    want = list(q[0])
    best, bd = None, 1e9
    probe = Image.new('RGB', (8, 8))
    for qual in range(40, 101):
        b = io.BytesIO()
        probe.save(b, 'JPEG', quality=qual)
        b.seek(0)
        d = sum(abs(a - c) for a, c in zip(list(Image.open(b).quantization[0]), want))
        if d < bd:
            best, bd = qual, d
    return best


def through_jpeg(img: Image.Image, adult: float, quality: int | None) -> Image.Image:
    """Our image as the reference was shot: blown up to its adult height (nearest) and saved
    at its JPEG quality."""
    f = adult / ADULT
    big = img.resize((max(1, round(img.width * f)), max(1, round(img.height * f))), Image.NEAREST)
    if not quality:
        return big
    b = io.BytesIO()
    big.save(b, 'JPEG', quality=quality)
    b.seek(0)
    return Image.open(b).convert('RGB')


def measure(path: str, box, adult: float) -> dict:
    src = Image.open(path)
    q = jpeg_quality(src)
    img = src.convert('RGB').crop(tuple(box))
    return {**counts(to_scale(img, adult)), 'jpeg_quality': q}


def load() -> dict:
    with open(BASELINES) as f:
        return json.load(f)


def bar(kind: str, base: dict | None = None) -> dict:
    """The reference's counts for a kind of surface: the mean over its baselines, with the
    adult height and JPEG quality they were shot at."""
    base = base or load()
    rows = [b for b in base['baselines'].values() if b['kind'] == kind]
    if not rows:
        raise KeyError(f'detail_bar: no baseline for {kind}')
    out = {m: round(float(np.mean([b[m] for b in rows])), 3) for m in ('tones', 'shapes', 'dressing', 'isolated', 'cluster')}
    out['adult_px'] = float(np.mean([b['adult_px'] for b in rows]))
    qs = [b.get('jpeg_quality') for b in rows if b.get('jpeg_quality')]
    out['jpeg_quality'] = int(round(np.mean(qs))) if qs else None
    return out


def judge(ours: dict, ref: dict) -> tuple[bool, list]:
    lines, ok = [], True
    for m in ('tones', 'shapes', 'dressing'):
        good = ours[m] >= TOLERANCE * ref[m]
        ok &= good
        lines.append(f'{m} {ours[m]:5.1f} / {ref[m]:5.1f} {"ok" if good else "LOW"}')
    good = ours['isolated'] <= ref['isolated'] + ISOLATED_MARGIN
    ok &= good
    lines.append(f'isolated {ours["isolated"]:.3f} / {ref["isolated"]:.3f} {"ok" if good else "NOISY"}')
    good = ours['cluster'] >= CLUSTER_SHARE * ref['cluster']
    ok &= good
    lines.append(f'cluster {ours["cluster"]:4.1f} / {ref["cluster"]:4.1f} {"ok" if good else "NOISY"}')
    return ok, lines


def check_image(img: Image.Image, box, kind: str, adult: float = ADULT, base=None):
    """Our crop judged against the kind's bar, through the reference's own pipe."""
    ref = bar(kind, base)
    crop = img.convert('RGB').crop(tuple(box))
    if adult != ADULT:   # bring ours to A = 25 first
        crop = crop.resize((round(crop.width * ADULT / adult), round(crop.height * ADULT / adult)), Image.NEAREST)
    shot = through_jpeg(crop, ref['adult_px'], ref['jpeg_quality'])
    ours = counts(to_scale(shot, ref['adult_px']))
    ok, lines = judge(ours, ref)
    return ok, ours, lines


def main(argv):
    if '--list' in argv:
        for k, b in load()['baselines'].items():
            print(f'{k:28s} {b["kind"]:7s} tones {b["tones"]:5.1f} shapes {b["shapes"]:5.1f} '
                  f'dressing {b["dressing"]:5.1f} isolated {b.get("isolated", 0):.3f} '
                  f'cluster {b.get("cluster", 0):4.1f}  {b["url"]}')
        return 0
    box = [int(v) for v in argv[argv.index('--box') + 1:argv.index('--box') + 5]]
    adult = float(argv[argv.index('--adult') + 1]) if '--adult' in argv else ADULT
    kind = argv[argv.index('--kind') + 1]
    if '--measure' in argv:
        path = argv[argv.index('--measure') + 1]
        key = argv[argv.index('--key') + 1]
        url = argv[argv.index('--url') + 1]
        game = argv[argv.index('--game') + 1] if '--game' in argv else 'Eastward'
        c = measure(path, box, adult)
        base = load() if os.path.exists(BASELINES) else {'about': __doc__.split('\n')[0], 'baselines': {}}
        base['baselines'][key] = {'game': game, 'url': url, 'box': box, 'adult_px': adult, 'kind': kind, **c}
        with open(BASELINES, 'w') as f:
            json.dump(base, f, indent=1)
            f.write('\n')
        print(key, c)
        return 0
    ok, ours, lines = check_image(Image.open(argv[0]), box, kind, adult)
    print(f'{kind}: ' + '; '.join(lines) + f'  -> {"PASS" if ok else "FAIL"}')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
