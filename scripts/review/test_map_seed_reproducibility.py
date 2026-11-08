"""Small real-consumer seed controls; never generate the raw continent.

Run: python3 -m unittest scripts.review.test_map_seed_reproducibility -v
The prospective contract is stable across processes, including the documented -I
launch which ignores PYTHONHASHSEED. Historical map equality is not tested here.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
import zlib


# A probe launched with -I deliberately receives only the already-installed
# scientific dependency locations from its parent test interpreter. This allows
# an isolated scratch dependency target without pretending PYTHONPATH survives -I.
if __name__ == '__main__' and sys.argv[1:2] == ['--probe']:
    sys.path[:0] = json.loads(sys.argv[2])

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BLOCKOUT = ROOT / 'docs/vision/research/blockout'
sys.path.insert(0, str(BLOCKOUT))
import geo5 as g
import towns55 as tw


def consumer_probe():
    """Execute the real consumers in a tiny paint context, with no world build.

    Actual meander arithmetic and Town RNGs run. Large-canvas line rasterisation,
    noise arithmetic and city painting are replaced with bounded fixture inputs;
    the recorded seeds prove the real route/settlement call-site bindings.
    """
    shape = (12, 12)
    yy, xx = np.mgrid[:shape[0], :shape[1]]
    route_seeds = []
    settlement_seeds = []
    real_meander = g.meander

    def meander(points, amplitude, seed, step=120):
        route_seeds.append(seed)
        return real_meander(points, amplitude, seed, step)

    def noise(_scale, seed, octaves=4):
        settlement_seeds.append(seed)
        return np.random.default_rng(seed).uniform(-1, 1, shape)

    def line_mask(*_args, **_kwargs):
        return np.zeros(shape, dtype=bool)

    source = {'K': np.full(shape, 'broadleaf', dtype='<U12'),
              'barriers': {}, 'h': np.zeros(shape)}
    with patch.multiple(g, H=shape[0], W=shape[1], PX=xx * 8 + 4, PY=yy * 8 + 4,
                        ROUTES={'Seed route': ([(16, 16), (40, 32), (72, 64)], 'path', [])},
                        SETTLE={'Seed settlement': (48, 48, 36, 'fixture')},
                        meander=meander, noise=noise, line_mask=line_mask,
                        raster=lambda *_: (np.zeros(shape), np.zeros(shape), 0),
                        city=lambda *_: None):
        g.routes(source)
        points = source['route_px']['Seed route']
        route_seed = route_seeds[0]
        g.settle(source)

    def stream(**kwargs):
        town = tw.Town({}, 'Seed town', (0, 0), 'fixture', (1, 2),
                       'fixture purpose', 'fixture setting', **kwargs)
        return town.rng.integers(0, 2 ** 31, size=12).tolist()

    return {'route_seed': route_seed, 'route_points': points,
            'settlement_seed': settlement_seeds[0],
            'settlement_ground_sha256': hashlib.sha256(source['K'].tobytes()).hexdigest(),
            'town_default': stream(), 'town_none': stream(seed=None),
            'town_zero': stream(seed=0), 'town_explicit': stream(seed=109)}


def dependency_paths():
    paths = set()
    for name in ('numpy', 'scipy', 'PIL', 'skimage'):
        spec = importlib.util.find_spec(name)
        if spec is None or not spec.submodule_search_locations:
            raise RuntimeError('missing test dependency: ' + name)
        paths.add(str(Path(next(iter(spec.submodule_search_locations))).parent))
    return sorted(paths)


class MapSeedReproducibility(unittest.TestCase):
    def test_name_seed_matches_existing_unsigned_crc32_utf8_convention(self):
        for name in ('123456789', 'Seed route', 'Seed settlement', 'Seed town',
                     'the Glint\N{RIGHT SINGLE QUOTATION MARK}s falls', ''):
            for modulus in (1, 997, 1000, 2 ** 31):
                with self.subTest(name=name, modulus=modulus):
                    self.assertEqual(g.stable_name_seed(name, modulus),
                                     zlib.crc32(name.encode('utf-8')) % modulus)
        self.assertEqual(zlib.crc32(b'123456789'), 0xcbf43926)

    def test_actual_route_and_settlement_consumers_keep_their_moduli(self):
        with patch.object(g, 'stable_name_seed', wraps=g.stable_name_seed) as seed:
            result = consumer_probe()
        self.assertEqual(result['route_seed'], zlib.crc32(b'Seed route') % 1000)
        self.assertEqual(result['settlement_seed'], zlib.crc32(b'Seed settlement') % 997)
        self.assertEqual(seed.call_args_list[0].args, ('Seed route', 1000))
        self.assertEqual(seed.call_args_list[1].args, ('Seed settlement', 997))

    def test_default_and_none_town_seed_use_shared_name_binding(self):
        with patch.object(g, 'stable_name_seed', wraps=g.stable_name_seed) as seed:
            result = consumer_probe()
        self.assertEqual(result['town_default'], result['town_none'])
        expected = np.random.default_rng(zlib.crc32(b'Seed town') % (2 ** 31))
        self.assertEqual(result['town_default'], expected.integers(0, 2 ** 31, size=12).tolist())
        self.assertEqual([call.args for call in seed.call_args_list[2:]],
                         [('Seed town', 2 ** 31), ('Seed town', 2 ** 31)])

    def test_explicit_numeric_town_seeds_including_zero_bypass_name_fallback(self):
        for value in (0, 1, 109, 2 ** 32 - 1, np.int64(208)):
            with self.subTest(seed=int(value)), patch.object(
                    g, 'stable_name_seed', side_effect=AssertionError('explicit seed used fallback')):
                town = tw.Town({}, 'Seed town', (0, 0), 'fixture', (1, 2),
                               'fixture purpose', 'fixture setting', seed=value)
                self.assertEqual(town.rng.integers(0, 2 ** 31, size=12).tolist(),
                                 np.random.default_rng(value).integers(0, 2 ** 31, size=12).tolist())
                positional = tw.Town({}, 'Seed town', (0, 0), 'fixture', (1, 2),
                                     'fixture purpose', 'fixture setting', (), (), value)
                self.assertEqual(positional.rng.integers(0, 2 ** 31, size=12).tolist(),
                                 np.random.default_rng(value).integers(0, 2 ** 31, size=12).tolist())

    def test_real_consumers_reproduce_under_normal_and_isolated_launches(self):
        paths = json.dumps(dependency_paths())
        outputs = []
        for isolated, hash_seed in ((False, '0'), (False, '91'),
                                    (True, '0'), (True, '91'), (True, None)):
            with self.subTest(isolated=isolated, hash_seed=hash_seed):
                env = dict(os.environ)
                if hash_seed is None:
                    env.pop('PYTHONHASHSEED', None)
                else:
                    env['PYTHONHASHSEED'] = hash_seed
                args = [sys.executable] + (['-I'] if isolated else [])
                result = subprocess.run(args + [str(Path(__file__).resolve()), '--probe', paths],
                                        cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                output = json.loads(result.stdout)
                self.assertEqual(output['ignore_environment'], int(isolated))
                outputs.append(output['consumers'])
        self.assertTrue(outputs)
        for output in outputs[1:]:
            self.assertEqual(output, outputs[0])
        expected = np.random.default_rng(0).integers(0, 2 ** 31, size=12).tolist()
        self.assertEqual(outputs[0]['town_zero'], expected)


if __name__ == '__main__':
    if sys.argv[1:2] == ['--probe']:
        print(json.dumps({'ignore_environment': sys.flags.ignore_environment,
                          'consumers': consumer_probe()}, sort_keys=True))
    else:
        unittest.main()
