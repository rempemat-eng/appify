import assert from 'node:assert/strict';
import { PET_INDEX, hatSprites, petPalette, petSprites, visitorSprites } from './pet-sprites';

// Generated sprite data (scripts/art/pets.py) is well-formed: 32x32 rows, every
// character maps to a palette colour, so nothing renders as undefined.
const check = (rows: readonly string[], label: string, width = 32) => {
  assert.equal(rows.length <= 32, true, `${label} height`);
  for (const row of rows) {
    assert.equal(row.length, width, `${label} row width`);
    for (const ch of row)
      if (ch !== '.') {
        const i = PET_INDEX.indexOf(ch);
        assert.ok(i >= 0 && i < petPalette.length, `${label} colour ${ch}`);
      }
  }
};
for (const [species, stages] of Object.entries(petSprites))
  for (const [stage, sprite] of Object.entries(stages)) {
    for (const state of ['open', 'closed', 'grumpy', 'grumpy-closed'] as const)
      check(sprite[state], `${species} ${stage} ${state}`);
    assert.equal(sprite.hat.length, 2, `${species} hat anchor`);
  }
for (const [id, sprite] of Object.entries(visitorSprites)) {
  check(sprite.open, `${id} open`);
  check(sprite.closed, `${id} closed`);
}
for (const [hat, art] of Object.entries(hatSprites)) check(art.rows, hat, 17);
assert.ok(petPalette.every((c) => /^#[0-9A-F]{6}$/i.test(c)), 'palette is hex colours');

console.log('PASS: generated pet, visitor, Dave and hat sprites are well-formed.');
