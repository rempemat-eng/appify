/**
 * Interface token rules (coherence plan, step 3): the symmetric-inset rule and the type
 * scale hold at every pixel unit a phone or tablet can produce. Source arithmetic only;
 * the browser pass measures the rendered bars.
 */
import assert from 'node:assert/strict';
import {
  barControl,
  contentInset,
  hotbarHeight,
  hotbarSlot,
  hudBarHeight,
  panelInset,
  siblingGap,
  space,
  type,
} from './ui-tokens';

for (const u of [2, 3, 4]) {
  // a bar's controls sit as far from its top and bottom as from its sides
  assert.equal((hudBarHeight(u) - u - barControl(u)) / 2, contentInset(u), `HUD inset at ${u}`);
  assert.equal((hotbarHeight(u) - u - hotbarSlot(u)) / 2, contentInset(u), `hotbar inset at ${u}`);
  // siblings sit one inset apart, inside a frame's own edge
  assert.equal(siblingGap(u), space.inset * u);
  assert.equal(contentInset(u) - siblingGap(u), space.border * u, 'content clears the frame edge');
  // sheets are roomier than bars, and every inset lands on the pixel grid
  assert.ok(panelInset(u) > contentInset(u));
  for (const value of [contentInset(u), panelInset(u), siblingGap(u)])
    assert.equal(value % u, 0, 'insets are whole pixels');
  // hotbar slots are full touch targets on their own
  assert.ok(hotbarSlot(u) >= 44, `hotbar slot at ${u} is a 44 px target`);
}
const sizes = Object.values(type).map((style) => style.fontSize);
assert.deepEqual(
  [...sizes].sort((a, b) => b - a),
  sizes,
  'type steps descend title, heading, body, label, caption',
);
for (const [name, style] of Object.entries(type))
  assert.equal(style.lineHeight % 4, 0, `${name} line height is a multiple of 4`);
console.log(
  'PASS: interface tokens keep equal insets on every side of bars and sheets at units 2-4, whole-pixel spacing, 44 px hotbar slots and a descending type scale.',
);
