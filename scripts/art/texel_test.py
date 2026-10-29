"""C50 parity and integration regressions: python3 scripts/art/texel_test.py.

The same decoded fixtures are passed to the real TypeScript measureDensity.
No generated art is changed. This test also exercises each tool's scale boundary.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from PIL import Image

from texel import measure_density, native_image
import size_check
import style_lint

ROOT = Path(__file__).resolve().parents[2]


def picture(density, scale, width=12, height=8):
    """Distinct adjacent texels force the requested density, including alpha."""
    tw, th, k = int(width * density), int(height * density), int(scale / density)
    image = Image.new('RGBA', (tw, th))
    image.putdata([(x * 13 % 256, y * 29 % 256, (x + y * tw) % 256,
                    0 if (x + y) % 5 == 0 else 255)
                   for y in range(th) for x in range(tw)])
    return image.resize((tw * k, th * k), Image.Resampling.NEAREST)


def fixture(name, image, scale):
    return dict(name=name, width=image.width, height=image.height, scale=scale,
                rgba=list(image.tobytes()))


class TexelTest(unittest.TestCase):
    def test_typescript_parity(self):
        cases = []
        expected = []
        for density, scale in [(1, 1), (1, 2), (1, 4), (1, 6),
                               (1.5, 3), (1.5, 6), (2, 2), (2, 4), (2, 6)]:
            image = picture(density, scale)
            cases.append(fixture(f'{density}x at {scale}', image, scale))
            expected.append(density)
        lone = picture(1, 4)
        lone.putpixel((1, 1), (11, 22, 33, 254))
        cases.append(fixture('lone off-grid image pixel', lone, 4))
        expected.append(None)
        transparent = picture(1, 4)
        pixels = list(transparent.get_flattened_data())
        transparent.putdata([(i % 256, 73, 99, 0) if p[3] == 0 else p
                             for i, p in enumerate(pixels)])
        cases.append(fixture('transparent RGB ignored', transparent, 4))
        expected.append(1)
        cases.append(fixture('non-whole texel dimensions', Image.new('RGBA', (5, 4)), 4))
        expected.append(None)
        # A fine canvas drawn with only coarse detail must still measure coarse.
        cases.append(fixture('coarse content', picture(1, 4), 4))
        expected.append(1)
        script = r"""const fs = require('node:fs'), vm = require('node:vm'), ts = require('typescript');
const moduleValue = { exports: {} };
vm.runInNewContext(ts.transpileModule(fs.readFileSync('lib/art-density.ts', 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }
}).outputText, { module: moduleValue, exports: moduleValue.exports, require });
const cases = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(cases.map(c => moduleValue.exports.measureDensity(
  Uint8Array.from(c.rgba), c.width, c.height, c.scale))));
"""
        actual_ts = json.loads(subprocess.check_output(
            ['node', '-e', script], input=json.dumps(cases), text=True, cwd=ROOT))
        actual_py = [measure_density(bytes(c['rgba']), c['width'], c['height'], c['scale'])
                     for c in cases]
        self.assertEqual(actual_py, expected)
        self.assertEqual(actual_ts, expected)

    def test_tool_measurements_keep_fine_detail_and_world_size(self):
        # One dark border texel and alternating fill: an erroneous /4 shrink loses
        # the fine grid and changes the outline, colour and lone-pixel measures.
        art = Image.new('RGBA', (8, 8), (0, 0, 0, 0))
        for y in range(1, 7):
            for x in range(1, 7):
                art.putpixel((x, y), (24, 24, 32, 255) if x in (1, 6) or y in (1, 6)
                             else (120 + 9 * ((x + y) % 2), 94, 67, 255))
        exported = art.resize((16, 16), Image.Resampling.NEAREST)  # density 2, export 4
        measured, density = native_image(exported, 4)
        self.assertEqual(density, 2)
        self.assertEqual(measured.size, art.size)
        self.assertEqual(measured.tobytes(), art.tobytes())
        self.assertEqual(style_lint.measure(exported, 4), style_lint.measure(art))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'fine.png'
            exported.save(path)
            self.assertEqual(size_check.measure(str(path), 4), (3, 3))  # six texels / 2
            script = r"""const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const file = path.resolve('scripts/check-sprites.cjs');
const source = fs.readFileSync(file, 'utf8').split('let sprites = 0;')[0];
const moduleValue = { exports: {} };
vm.runInNewContext(source + '\nmodule.exports = nativePixels;', {
  require, __dirname: path.dirname(file), module: moduleValue, console
});
const image = moduleValue.exports(process.argv[1], 4);
process.stdout.write(JSON.stringify([image.w, image.h, Array.from(image.at(1, 1))]));
"""
            measured_js = json.loads(subprocess.check_output(
                ['node', '-e', script, str(path)], cwd=ROOT, text=True))
            self.assertEqual(measured_js, [8, 8, list(art.getpixel((1, 1)))])

    def test_invalid_grid_is_not_silently_decimated(self):
        image = picture(2, 4)
        image.putpixel((1, 1), (1, 2, 3, 254))
        with self.assertRaisesRegex(ValueError, 'no supported texel grid'):
            native_image(image, 4)


if __name__ == '__main__':
    unittest.main()
