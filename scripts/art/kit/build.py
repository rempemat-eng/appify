"""Build the terrain kit's pictures from the piece library (docs/world-editor.md, "The kit").

    python3 -m scripts.art.kit.build            # build what changed into game/kit/terrain/
    python3 -m scripts.art.kit.build --all      # rebuild everything
    python3 -m scripts.art.kit.build --check    # fail if a picture is missing or stale

Each terrain piece's fill and each transition's tiles are painted once and cached by the hash of
their inputs (the piece's painter and arguments, the painters' sources, the palette), so editing
one material repaints only that material and the transitions that touch it. Outputs:

    fill_<id>.png        the periodic fill, PERIOD square; a texel's palette code in R (low byte)
                         and G (high byte)
    over_<id>.png        a transition's tiles (edges.layout: per mask, its crossing profiles times
                         the variants), ATLAS_COLS across; a texel's operation in R, its value
                         in G and B
    lut.png              the palette: code -> RGB, one row
    palette.png          the editor palette's swatches, one 24 x 24 tile per material, in
                         material-id order (materials.tres cuts it)
    materials.tres       the logical layer's TileSet: one tile per material, custom data
                         material (its piece id), material_id, walkable, surface, route
    manifest.json        all of the above, with the input hashes

The manifest is the one file Godot (world/terrain/terrain_kit.gd) and Python (Kit below) read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.art.native import ctx, load_biome  # noqa: E402

if not ctx._configured:
    ctx.configure(3.0, load_biome('woodland'), json.load(open(os.path.join(ROOT, 'art', 'scenes', 'woodland.json'))))

from scripts.art.kit import edges as E  # noqa: E402
from scripts.art.kit import fills as F  # noqa: E402
from scripts.art.kit import schema as S  # noqa: E402
from scripts.art.native import palette as PAL  # noqa: E402

OUT = os.path.join(ROOT, 'game', 'kit', 'terrain')
RES = 'res://kit/terrain/'
COMMON = ['scripts/art/native/softground.py', 'scripts/art/native/softgrid.py', 'scripts/art/native/palette.py',
          'scripts/art/native/terrain/noise.py', 'art/house-palette.json', 'scripts/art/native/accents.json']
SOURCES = {'terrain': COMMON + ['scripts/art/kit/fills.py'],
           'transition': COMMON + ['scripts/art/kit/edges.py']}


def _src_hash(kind: str) -> str:
    h = hashlib.sha256()
    for s in SOURCES[kind]:
        h.update(open(os.path.join(ROOT, s), 'rb').read())
    return h.hexdigest()


def input_hash(piece: dict, extra: str = '') -> str:
    h = hashlib.sha256(_src_hash(piece['kind']).encode())
    h.update(json.dumps(piece, sort_keys=True).encode())
    h.update(extra.encode())
    return h.hexdigest()[:16]


def load_library() -> dict:
    lib = {}
    for p in S.piece_files():
        piece = json.load(open(p))
        lib[piece['id']] = piece
    return lib


def _seed(*parts) -> int:
    return int(hashlib.sha256('/'.join(map(str, parts)).encode()).hexdigest()[:8], 16)


# ------------------------------------------------------------------------------------------------
# painting
# ------------------------------------------------------------------------------------------------
def paint_fill(piece: dict) -> np.ndarray:
    f = piece['terrain']['fill']
    assert f['module'] == 'scripts.art.kit.fills', f
    return F.PAINTERS[f['fn']](**f.get('args', {}))


def paint_transition(piece: dict, fills: dict, lib: dict) -> np.ndarray:
    """Every tile of the transition (edges.layout) into its atlas block: ATLAS_COLS tiles across."""
    t = piece['transition']
    fu = fills[t['upper']]
    fl = fills[t['lower']] if t['lower'] in fills else fu
    P = fu.shape[0]
    tiles = E.layout(t['variants'])
    rows = (len(tiles) + E.ATLAS_COLS - 1) // E.ATLAS_COLS
    fn = E.PAINTERS[t['painter']['fn']]
    out = np.zeros((rows * E.CELL, E.ATLAS_COLS * E.CELL, 2), np.int32)
    for idx, k, prof, v in tiles:
        s = _seed(piece['id'], k, prof, v)
        r = np.random.default_rng(s)
        oy, ox = 2 * int(r.integers(0, P // 2)), 2 * int(r.integers(0, P // 2))
        iy = (np.arange(E.N) + oy) % P
        ix = (np.arange(E.N) + ox) % P
        tile = fn(k, fu[np.ix_(iy, ix)], fl[np.ix_(iy, ix)], s % (2 ** 31), prof=prof, **t['painter'].get('args', {}))
        ty, tx = idx // E.ATLAS_COLS, idx % E.ATLAS_COLS
        out[ty * E.CELL:(ty + 1) * E.CELL, tx * E.CELL:(tx + 1) * E.CELL] = tile
    return out


def save_codes(path: str, codes: np.ndarray) -> None:
    a = np.zeros(codes.shape + (4,), np.uint8)
    a[..., 0] = codes & 255
    a[..., 1] = codes >> 8
    a[..., 3] = 255
    Image.fromarray(a, 'RGBA').save(path, optimize=True)


def load_codes(path: str) -> np.ndarray:
    a = np.asarray(Image.open(path).convert('RGBA')).astype(np.int32)
    return a[..., 0] | (a[..., 1] << 8)


def save_ops(path: str, ops: np.ndarray) -> None:
    a = np.zeros(ops.shape[:2] + (4,), np.uint8)
    a[..., 0] = ops[..., 0]
    a[..., 1] = ops[..., 1] & 255
    a[..., 2] = ops[..., 1] >> 8
    a[..., 3] = 255
    Image.fromarray(a, 'RGBA').save(path, optimize=True)


def load_ops(path: str) -> np.ndarray:
    a = np.asarray(Image.open(path).convert('RGBA')).astype(np.int32)
    return np.stack([a[..., 0], a[..., 1] | (a[..., 2] << 8)], -1)


# ------------------------------------------------------------------------------------------------
# the kit as data
# ------------------------------------------------------------------------------------------------
class Kit:
    """The built kit for Python tools (compose.render, sheets, the validator)."""

    def __init__(self, out: str = OUT):
        self.man = json.load(open(os.path.join(out, 'manifest.json')))
        self.period = self.man['period']
        self.variants = self.man['variants']
        self.fills, self.prio, self.ids, self.names, self.meta = {}, {}, {}, {}, {}
        for m in self.man['materials']:
            mid = m['material_id']
            self.fills[mid] = load_codes(os.path.join(out, m['fill']))
            self.prio[mid] = m['priority']
            self.ids[m['id']] = mid
            self.names[mid] = m['id']
            self.meta[mid] = m
        self.over, self.pairs = {}, {}
        for t in self.man['transitions']:
            ops = load_ops(os.path.join(out, t['png']))
            C = E.CELL
            self.over[t['id']] = [ops[(i // E.ATLAS_COLS) * C:(i // E.ATLAS_COLS + 1) * C,
                                      (i % E.ATLAS_COLS) * C:(i % E.ATLAS_COLS + 1) * C]
                                  for i, *_ in E.layout(t['variants'])]
            self.pairs[(self.ids[t['upper']], t['lower'])] = t['id']

    def pair_for(self, upper: int, lower: int):
        return self.pairs.get((upper, self.names.get(lower))) or self.pairs.get((upper, '*'))


# ------------------------------------------------------------------------------------------------
# outputs
# ------------------------------------------------------------------------------------------------
def write_tileset(path: str, mats: list) -> None:
    """The logical layer's TileSet (a hand-written .tres, format 3): one 24 x 24 tile per material
    cut from palette.png, with the custom data the validator, the walk mask and the dock read."""
    lines = ['[gd_resource type="TileSet" load_steps=3 format=3]', '',
             '[ext_resource type="Texture2D" path="%spalette.png" id="1"]' % RES, '',
             '[sub_resource type="TileSetAtlasSource" id="mats"]', 'texture = ExtResource("1")',
             'texture_region_size = Vector2i(24, 24)']
    for i, m in enumerate(mats):
        lines += ['%d:0/0 = 0' % i,
                  '%d:0/0/custom_data_0 = &"%s"' % (i, m['id']),
                  '%d:0/0/custom_data_1 = %d' % (i, m['material_id']),
                  '%d:0/0/custom_data_2 = %s' % (i, 'true' if m['walkable'] else 'false'),
                  '%d:0/0/custom_data_3 = &"%s"' % (i, m['surface']),
                  '%d:0/0/custom_data_4 = %s' % (i, 'true' if m.get('route') else 'false')]
    lines += ['', '[resource]', 'tile_size = Vector2i(24, 24)',
              'custom_data_layer_0/name = "material"', 'custom_data_layer_0/type = 21',
              'custom_data_layer_1/name = "material_id"', 'custom_data_layer_1/type = 2',
              'custom_data_layer_2/name = "walkable"', 'custom_data_layer_2/type = 1',
              'custom_data_layer_3/name = "surface"', 'custom_data_layer_3/type = 21',
              'custom_data_layer_4/name = "route"', 'custom_data_layer_4/type = 1',
              'sources/0 = SubResource("mats")', '']
    open(path, 'w').write('\n'.join(lines))


def build(force: bool = False, check: bool = False) -> int:
    os.makedirs(OUT, exist_ok=True)
    lib = load_library()
    mpath = os.path.join(OUT, 'manifest.json')
    old = json.load(open(mpath)) if os.path.exists(mpath) else {'materials': [], 'transitions': []}
    old_h = {m['id']: m['hash'] for m in old['materials'] + old['transitions']}
    terr = sorted([p for p in lib.values() if p['kind'] == 'terrain'], key=lambda p: p['terrain']['material_id'])
    trans = sorted([p for p in lib.values() if p['kind'] == 'transition'], key=lambda p: p['id'])
    stale, fills, mats, trs = [], {}, [], []
    for p in terr:
        h = input_hash(p)
        fp = os.path.join(OUT, 'fill_%s.png' % p['id'])
        if force or old_h.get(p['id']) != h or not os.path.exists(fp):
            stale.append(p['id'])
            if check:
                continue
            print('painting fill', p['id'])
            save_codes(fp, paint_fill(p))
        if not check or os.path.exists(fp):
            fills[p['id']] = load_codes(fp)
        t = p['terrain']
        mats.append({'id': p['id'], 'material_id': t['material_id'], 'priority': t['priority'],
                     'fill': os.path.basename(fp), 'walkable': t['walkable'], 'surface': t['surface'],
                     'route': t.get('route', False), 'water': t.get('water'), 'approval': p['approval']['state'],
                     'swatch': t.get('swatch', [0, 0]), 'hash': h})
    hashes = {m['id']: m['hash'] for m in mats}
    for p in trans:
        t = p['transition']
        h = input_hash(p, hashes.get(t['upper'], '') + hashes.get(t['lower'], ''))
        fp = os.path.join(OUT, 'over_%s.png' % p['id'])
        if force or old_h.get(p['id']) != h or not os.path.exists(fp):
            stale.append(p['id'])
            if not check:
                print('painting transition', p['id'])
                save_ops(fp, paint_transition(p, fills, lib))
        trs.append({'id': p['id'], 'upper': t['upper'], 'lower': t['lower'], 'png': os.path.basename(fp),
                    'variants': t['variants'], 'approval': p['approval']['state'], 'hash': h})
    if check:
        if stale:
            print('kit: stale or missing: %s (run python3 -m scripts.art.kit.build)' % ', '.join(stale))
            return 1
        print('kit: %d materials, %d transitions, up to date' % (len(mats), len(trs)))
        return 0
    vs = {t['variants'] for t in trs} or {4}
    assert len(vs) == 1, 'one variant count across the kit (the shader assumes it)'
    lut = np.zeros((1, 512, 4), np.uint8)
    lut[0, :len(PAL.LUT), :3] = PAL.LUT
    lut[0, :, 3] = 255
    Image.fromarray(lut, 'RGBA').save(os.path.join(OUT, 'lut.png'))
    pal = np.zeros((E.CELL, E.CELL * max(1, len(mats)), 4), np.uint8)
    for i, m in enumerate(mats):
        sy, sx = m['swatch']
        pal[:, i * E.CELL:(i + 1) * E.CELL] = PAL.to_rgba(fills[m['id']][sy:sy + E.CELL, sx:sx + E.CELL])
    Image.fromarray(pal, 'RGBA').save(os.path.join(OUT, 'palette.png'))
    write_tileset(os.path.join(OUT, 'materials.tres'), mats)
    man = {'cell': E.CELL, 'period': F.PERIOD, 'variants': vs.pop(), 'profiles': list(E.OFFS),
           'atlas_cols': E.ATLAS_COLS, 'lut': 'lut.png', 'palette': 'palette.png',
           'tileset': 'materials.tres', 'ops': {'keep': E.OP_KEEP, 'upper': E.OP_UPPER, 'delta': E.OP_DELTA, 'abs': E.OP_ABS},
           'materials': mats, 'transitions': trs}
    json.dump(man, open(mpath, 'w'), indent=1)
    print('kit: %d materials, %d transitions; repainted: %s' % (len(mats), len(trs), ', '.join(stale) or 'nothing'))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv)
    return build(force=a.all, check=a.check)


if __name__ == '__main__':
    sys.exit(main())
