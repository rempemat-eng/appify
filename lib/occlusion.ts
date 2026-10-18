/**
 * Whether the companion is hidden behind something drawn in front of it (a building, a
 * tree, a forge), so the walk can show its outline through it (art-style.md, "The
 * companion stays readable"). Pure and box-based: a sprite's box is its whole image, so
 * a see-through corner can count too, which only shows the outline over the companion
 * itself. Nothing here changes where anyone can walk.
 */
export type Box = { x: number; y: number; w: number; h: number; z: number };

/** The companion's body in art pixels, from its feet (it is drawn 32 x 32, feet at 30). */
export function bodyBox(feet: { x: number; y: number }) {
  return { x: feet.x - 10, y: feet.y - 26, w: 20, h: 24 };
}

/** The share of the body a thing in front must cover before the outline shows. */
export const HIDDEN_SHARE = 0.4;

/** True when the boxes in front of the feet (deeper z) cover enough of the body. */
export function hiddenBehind(boxes: readonly Box[], feet: { x: number; y: number }): boolean {
  const b = bodyBox(feet);
  const area = b.w * b.h;
  // the most any one thing covers (two half-covering things side by side rarely hide it)
  let most = 0;
  for (const o of boxes) {
    if (o.z <= feet.y) continue;
    const w = Math.min(o.x + o.w, b.x + b.w) - Math.max(o.x, b.x);
    const h = Math.min(o.y + o.h, b.y + b.h) - Math.max(o.y, b.y);
    if (w > 0 && h > 0) most = Math.max(most, w * h);
  }
  return most >= area * HIDDEN_SHARE;
}
