import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {
  DEFAULT_HUT_LOOK,
  hutBoxes,
  hutDoors,
  hutImageKey,
  hutPaths,
  restoreHutLook,
  type HutLook,
} from './decor';
import { gardenHutPaths } from './garden-map';
import { currentSaveFixture } from './fixtures/save-fixtures';
import { readSave, writeSave } from './save-data';

// The hut's outside (coherence plan, B1): a look the player chooses while decorating,
// saved beside the keepsakes. Old saves and damaged values fall back to the hut as it
// first stood; every look the panel offers has its drawing.
const root = path.resolve(__dirname, '..');

assert.deepEqual(restoreHutLook(undefined), DEFAULT_HUT_LOOK, 'a save from before the choices');
assert.deepEqual(restoreHutLook(null), DEFAULT_HUT_LOOK);
assert.deepEqual(restoreHutLook(['red']), DEFAULT_HUT_LOOK);
assert.deepEqual(
  restoreHutLook({ door: 'gold', boxes: 7, path: 'flagstones' }),
  { ...DEFAULT_HUT_LOOK, path: 'flagstones' },
  'an unknown part falls back alone; the known one stays',
);
const chosen: HutLook = { door: 'violet', boxes: 'herbs', path: 'flagstones' };
assert.deepEqual(restoreHutLook(chosen), chosen);
assert.notEqual(restoreHutLook(undefined), DEFAULT_HUT_LOOK, 'a copy, never the shared default');
console.log('PASS: a saved hut look is restored part by part, defaults for the rest');

// It survives the save file: written, read back and restored like the rest of the save.
const lookIn = (data: unknown) =>
  typeof data === 'object' && data !== null ? Reflect.get(data, 'hutLook') : undefined;
const saved = { ...currentSaveFixture(), hutLook: chosen };
const { raw } = writeSave(saved, null);
assert.deepEqual(restoreHutLook(lookIn(readSave(raw, (value) => value).data)), chosen);
const old = readSave(writeSave(currentSaveFixture(), null).raw, (value) => value);
assert.deepEqual(restoreHutLook(lookIn(old.data)), DEFAULT_HUT_LOOK);
console.log('PASS: the hut look round-trips through the save; an older save gets the default');

// Every door with every window planting is drawn, and every paved path has its overlay.
const assets = fs.readFileSync(path.join(root, 'lib', 'garden-hut-assets.ts'), 'utf8');
for (const door of hutDoors)
  for (const boxes of hutBoxes) {
    const key = hutImageKey({ door, boxes, path: 'earth' });
    assert.ok(assets.includes(`'${key}':`), `hutImages has ${key}`);
    const file =
      key === hutImageKey(DEFAULT_HUT_LOOK)
        ? path.join(root, 'assets', 'garden', 'hut.png')
        : path.join(root, 'assets', 'garden', 'hut', `${key}.png`);
    assert.ok(fs.existsSync(file), `${path.relative(root, file)} is drawn`);
  }
for (const surface of hutPaths.filter((p) => p !== 'earth')) {
  assert.ok(surface in gardenHutPaths, `gardenHutPaths places ${surface}`);
  assert.ok(fs.existsSync(path.join(root, 'assets', 'garden', `path-${surface}.png`)));
}
console.log(
  `PASS: ${hutDoors.length * hutBoxes.length} hut looks and ${hutPaths.length - 1} paved path drawn`,
);
