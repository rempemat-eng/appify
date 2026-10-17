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

// the units pixelScale produces: 1x desktop and 2x phones up to 3x phones and retina desktops
for (const u of [1, 4 / 3, 1.5, 1.6, 2]) {
  const whole = (value: number) => Math.abs(value / u - Math.round(value / u)) < 1e-9;
  // a bar's controls sit as far from its top and bottom as from its sides
  assert.ok(
    Math.abs((hudBarHeight(u) - u - barControl(u)) / 2 - contentInset(u)) < 1e-9,
    `HUD inset at ${u}`,
  );
  assert.ok(
    Math.abs((hotbarHeight(u) - u - hotbarSlot(u)) / 2 - contentInset(u)) < 1e-9,
    `hotbar inset at ${u}`,
  );
  // siblings sit one inset apart, inside a frame's own edge
  assert.ok(Math.abs(siblingGap(u) - space.inset * u) < 1e-9);
  assert.ok(
    Math.abs(contentInset(u) - siblingGap(u) - space.border * u) < 1e-9,
    'content clears the frame edge',
  );
  // sheets are roomier than bars, and every inset lands on the pixel grid
  assert.ok(panelInset(u) > contentInset(u));
  for (const value of [contentInset(u), panelInset(u), siblingGap(u), barControl(u), hotbarSlot(u)])
    assert.ok(whole(value), 'insets and controls are whole art pixels');
  // hotbar slots are full touch targets on their own
  assert.ok(hotbarSlot(u) >= 44 - 1e-9, `hotbar slot at ${u} is a 44 px target`);
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
  'PASS: interface tokens keep equal insets on every side of bars and sheets at every shared-grid unit, whole art-pixel spacing, 44 px hotbar slots and a descending type scale.',
);
