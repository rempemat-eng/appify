"""The kit's detail bar against a hand-painted zone (docs/world-editor.md, "Measured against the
painted woodland"). Matt, 27 Oct 17:00: the hand-painted woodland is the bar, so a kit material is
offered for approval only when its baked ground reaches it on water, paths and tree shadows.

Both grounds are the same zone (the kit plan was made from the painted one's plan), so one set of
regions from the kit plan's cells is measured on both:

  water     the water cells and one cell of bank round them
  path      the route cells and one cell of verge
  shadow    the tree pieces' crown shadows (screen.tree_shadow_hd at their feet)
  lawn      the open lawn (lawn cells a cell from anything else, out of the shadows): held to
            the painted grain both ways, edges within 8 % and tones at most 10 % over
  tiers     the face bands under raised ground (kit only: the painted woodland has none; it is
            measured against the plateau swatch that Matt liked, softgrid_swatches sw_plateau)

Per region:
  edges     the share of right and down neighbour pairs whose colours differ by more than 20
            (RGB distance): MEASURE.md's edge share, the density of marks
  tones     distinct colours per 24 x 24 window inside the region (mean)
  lone      pixels unlike all four neighbours (speckle; lower is calmer)
  flat      the share of pixels inside a 7 x 7 window of one colour (flat fill; lower is better)
and per outline (water and path, the material's own pixels): teeth and jags (review/edges.py) and
`ruler`, the share of the outline in straight runs of 24 texels or more (a ruler edge).

The kit passes a region when edges and tones reach 95 % of the painted, flat is at most the
painted's plus 0.02, and teeth, jags and ruler stay within the painted's plus a small margin.

    python3 -m scripts.art.kit.detail_bar [--zone woodland_kit] [--painted PNG] [--out DIR]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from scripts.art.kit import bake as BK
from scripts.art.kit.schema import ROOT
from scripts.review import edges as ED

CELL = 24


def _rgb(p):
    return np.asarray(Image.open(p).convert('RGB')).astype(int)


def texture(rgb: np.ndarray, m: np.ndarray) -> dict:
    a = rgb
    dr = np.sqrt(((a[:, 1:] - a[:, :-1]) ** 2).sum(-1)) > 20
    dd = np.sqrt(((a[1:] - a[:-1]) ** 2).sum(-1)) > 20
    mr, md = m[:, 1:] & m[:, :-1], m[1:] & m[:-1]
    edges = (dr[mr].sum() + dd[md].sum()) / max(1, mr.sum() + md.sum())
    key = a[..., 0] * 65536 + a[..., 1] * 256 + a[..., 2]
    # distinct colours in each 24 x 24 window that lies at least 90 % in the region (mean)
    tw = []
    for y in range(0, m.shape[0] - 23, 24):
        for x in range(0, m.shape[1] - 23, 24):
            mm = m[y:y + 24, x:x + 24]
            if mm.mean() >= 0.9:
                tw.append(len(np.unique(key[y:y + 24, x:x + 24][mm])))
    tones = float(np.mean(tw)) if tw else 0.0
    P = np.pad(key, 1, mode='edge')
    lone = (key != P[:-2, 1:-1]) & (key != P[2:, 1:-1]) & (key != P[1:-1, :-2]) & (key != P[1:-1, 2:])
    flat_c = (ndi.maximum_filter(key, size=7) == ndi.minimum_filter(key, size=7))
    flat = ndi.binary_dilation(flat_c, structure=np.ones((7, 7), bool))
    return dict(edges=round(float(edges), 4), tones=round(float(tones), 2), lone=round(float(lone[m].mean()), 4),
                flat=round(float(flat[m].mean()), 4), px=int(m.sum()))


def fam_mask(rgb, fams) -> np.ndarray:
    """Pixels whose colour is a palette code of one of `fams` (both grounds are drawn in the house
    palette, so a colour names its material family exactly)."""
    from scripts.art.native.palette import LUT, FI
    key = rgb[..., 0] * 65536 + rgb[..., 1] * 256 + rgb[..., 2]
    want = []
    for f in fams:
        for t in range(8):
            c = FI[f] * 8 + t
            if c < len(LUT):
                r, g, b = (int(v) for v in LUT[c][:3])
                want.append(r * 65536 + g * 256 + b)
    return np.isin(key, want)


def blue(rgb):
    return fam_mask(rgb, ('water', 'water_warm', 'water_cool'))


def _blue_rgb(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return (b > r + 30) & (b > g + 5)


def pathlike(rgb):
    return fam_mask(rgb, ('path', 'path_warm', 'path_cool'))


def _pathlike_rgb(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return (r > g + 12) & (r > b + 30)


def ruler(m: np.ndarray) -> float:
    """The share of the outline's profile in straight runs of CELL texels or more."""
    tot = long_ = 0
    for arr in (m, m.T):
        cols = np.nonzero(arr.any(0))[0]
        if len(cols) < 4:
            continue
        sub = arr[:, cols]
        for prof in (np.argmax(sub, 0), sub.shape[0] - 1 - np.argmax(sub[::-1], 0)):
            run = 1
            for k in range(1, len(prof)):
                if prof[k] == prof[k - 1] and cols[k] == cols[k - 1] + 1:
                    run += 1
                else:
                    tot += run
                    long_ += run if run >= CELL else 0
                    run = 1
            tot += run
            long_ += run if run >= CELL else 0
    return long_ / max(1, tot)


def outline(m: np.ndarray, region: np.ndarray) -> dict:
    # the material's body, not its marks: a ripple's lit line or a pebble on the path is not
    # its outline (a 3 x 3 majority, holes filled)
    m = ndi.uniform_filter(m.astype(float), 3) > 0.5
    m = ndi.binary_fill_holes(m)
    mm = m & region
    lab, n = ndi.label(mm)
    if n == 0:
        return dict(teeth=0.0, jags=0.0, ruler=0.0)
    sizes = ndi.sum(mm, lab, range(1, n + 1))
    keep = np.isin(lab, 1 + np.nonzero(sizes > 400)[0])
    e = ED.measure(keep)
    return dict(teeth=round(e['teeth'], 4), jags=round(e['jags'], 4), ruler=round(ruler(keep), 4))


def regions(plan: dict, H: int, W: int) -> dict:
    from scripts.art.native import screen as SN
    lib = BK._pieces_lib()
    idx = json.load(open(os.path.join(ROOT, 'game', 'kit', 'props', 'index.json')))
    mat = np.array([[plan['legend'].get(c, '') for c in r] for r in plan['rows']])
    paint = {m: (lib[m]['terrain'].get('paint') or {}) for m in set(mat.ravel()) if m in lib}
    wc = np.isin(mat, [m for m, p in paint.items() if p.get('fn') == 'water'])
    pc = np.isin(mat, [m for m, p in paint.items() if p.get('fn') == 'dirt'])
    tx = lambda c: np.kron(ndi.binary_dilation(c, iterations=1), np.ones((CELL, CELL), bool))[:H, :W]  # noqa: E731
    out = {'water': tx(wc), 'path': tx(pc) & ~tx(wc)}
    sh = np.zeros((H, W), bool)
    for p in plan.get('pieces', []):
        e = idx.get(p['piece']) or {}
        if 'mask' in (e.get('shadow') or {}):
            img, _anc = BK._sprite(e, p.get('variant'))
            ex, _k = BK._tree_ex(p['piece'], img)
            sh |= SN.tree_shadow_hd(p['at'][0] / 3.0, p['at'][1] / 3.0, ex, W, H)
    out['shadow'] = sh & ~out['water'] & ~out['path']
    lc = np.isin(mat, ['lawn'])
    out['lawn'] = np.kron(lc & ~ndi.binary_dilation(~lc, iterations=1), np.ones((CELL, CELL), bool))[:H, :W] & ~sh
    falls = np.zeros((H, W), bool)
    for p in plan.get('pieces', []):
        if (((lib.get(p['piece']) or {}).get('rendering') or {}).get('paint') or {}).get('fn') == 'fall':
            x, y = p['at']
            falls[max(0, y - 72):y + 48, max(0, x - 60):x + 60] = True
    out['_falls'] = falls
    return out


def compare(zone: str, painted: str, out_dir: str | None = None) -> dict:
    plan = json.load(open(os.path.join(BK.ZONES, zone + '.json')))
    kit_png = BK.out_path(zone)
    A, B = _rgb(painted), _rgb(kit_png)
    H, W = min(A.shape[0], B.shape[0]), min(A.shape[1], B.shape[1])
    A, B = A[:H, :W], B[:H, :W]
    regs = regions(plan, H, W)
    res = {}
    for name, m in regs.items():
        if name.startswith('_'):
            continue
        a, b = texture(A, m), texture(B, m)
        if name in ('water', 'path'):
            f = blue if name == 'water' else pathlike
            # a fall is not a bank: its sheet and foam are left out of the outline
            mo = m & ~regs['_falls']
            a.update(outline(f(A), mo))
            b.update(outline(f(B), mo))
        ok = (b['edges'] >= 0.95 * a['edges'] and b['tones'] >= 0.95 * a['tones'] and b['flat'] <= a['flat'] + 0.02)
        if name == 'lawn':
            # the open lawn is held to the painted grain both ways: as calm, not busier
            ok = abs(b['edges'] - a['edges']) <= 0.08 * a['edges'] and b['tones'] <= 1.1 * a['tones'] and b['flat'] <= a['flat'] + 0.02
        if 'ruler' in a:
            ok = ok and b['teeth'] <= max(a['teeth'] + 0.01, 0.03) and b['jags'] <= max(a['jags'] + 0.01, 0.03) and b['ruler'] <= a['ruler'] + 0.05
        res[name] = {'painted': a, 'kit': b, 'pass': bool(ok)}
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        json.dump(res, open(os.path.join(out_dir, 'detail_bar_%s.json' % zone), 'w'), indent=1)
    return res


def face_cells(plan: dict) -> np.ndarray:
    t = np.array([[int(c) for c in r] for r in plan['tiers']])
    f = np.zeros(t.shape, bool)
    for k in (1, 2):
        f[k:] |= t[:-k] > t[k:]
    return f


def compare_tiers(zone: str = 'kitlab_tiers', swatch: str | None = None) -> dict:
    """The kit's earth faces (a lab's face cells, the lip's top rows, stairs and falls left out)
    against the plateau swatch's face (softgrid_swatches.sw_plateau: rim at 40 world px, face 16 high,
    from x 0 to 104 world px, its log steps from 40 to 64 left out)."""
    if swatch is None:
        return {}
    plan = json.load(open(os.path.join(BK.ZONES, zone + '.json')))
    B = _rgb(BK.out_path(zone))
    H, W = B.shape[:2]
    m = np.kron(face_cells(plan), np.ones((CELL, CELL), bool))[:H, :W]
    m &= ~(np.kron(face_cells(plan), np.ones((CELL, CELL), bool))[:H, :W] & ~np.roll(np.kron(face_cells(plan), np.ones((CELL, CELL), bool)), 8, 0)[:H, :W])
    for p in plan.get('pieces', []):
        x, y = p['at']
        if p['piece'].startswith(('log_steps', 'waterfall')):
            m[max(0, y - 80):y + 40, max(0, x - 60):x + 60] = False
    A = _rgb(swatch)
    sm = np.zeros(A.shape[:2], bool)
    sm[128:166, 0:120] = True
    sm[128:166, 192:312] = True
    a, b = texture(A, sm), texture(B, m)
    ok = b['edges'] >= 0.95 * a['edges'] and b['tones'] >= 0.95 * a['tones'] and b['flat'] <= a['flat'] + 0.02
    return {'tiers': {'painted': a, 'kit': b, 'pass': bool(ok)}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--zone', default='woodland_kit')
    ap.add_argument('--painted', default=os.path.join(ROOT, 'game', 'zones', 'woodland', 'art', 'ground.png'))
    ap.add_argument('--out')
    ap.add_argument('--swatch', help='softgrid_swatches swatch_0_plateau.png, for the tiers')
    a = ap.parse_args(argv)
    res = compare(a.zone, a.painted, a.out)
    res.update(compare_tiers(swatch=a.swatch))
    print('%-7s %-8s %7s %7s %7s %7s %7s %7s %7s' % ('region', 'ground', 'edges', 'tones', 'lone', 'flat', 'teeth', 'jags', 'ruler'))
    for name, r in res.items():
        for k in ('painted', 'kit'):
            v = r[k]
            print('%-7s %-8s %7.4f %7.2f %7.4f %7.4f %7s %7s %7s' % (name, k, v['edges'], v['tones'], v['lone'], v['flat'],
                                                                    v.get('teeth', '-'), v.get('jags', '-'), v.get('ruler', '-')))
        if a.out:
            json.dump(res, open(os.path.join(a.out, 'detail_bar_%s.json' % a.zone), 'w'), indent=1)
        print('%-7s %s' % (name, 'PASS' if r['pass'] else 'BELOW THE BAR'))
    return 0 if all(r['pass'] for r in res.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
