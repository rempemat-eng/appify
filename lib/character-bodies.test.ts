/**
 * Body plans (art/characters/bodies/<id>.json): one per folk and familiar, the data the
 * rig builds each character from. They must match the animation spec's cast and cells,
 * use only house palette families, and keep every anchor inside the cell.
 */
import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import { ANIMATION } from './character-animation';

type Part = {
  name: string;
  families: string[];
  joint: string;
  layer: Record<string, number>;
  facings: string[];
  motion: string;
  painter: boolean;
};
type Body = {
  id: string;
  kind: string;
  template: string;
  heightWorld: number;
  cell: string;
  families: string[];
  glows: string[];
  signature: string;
  parts: Part[];
  anchors: {
    perch?: Record<string, number[]>;
    holdOn?: Record<string, number[]>;
    growth?: number[];
  };
};

const dir = new URL('../art/characters/bodies/', import.meta.url);
const palette: unknown = JSON.parse(
  readFileSync(new URL('../art/house-palette.json', import.meta.url), 'utf8'),
);
const ramps =
  typeof palette === 'object' && palette !== null && 'ramps' in palette ? palette.ramps : {};
const RAMPS = new Set(Object.keys(ramps ?? {}));
const GLOWS = new Set(['lamp', 'neon_pink', 'neon_cyan', 'lava', 'glowflora']);
const JOINTS = new Set(['foot', 'hip', 'chest', 'head', 'hand', 'back', 'tail', 'float']);
const TEMPLATES = new Set(['biped', 'smallBiped', 'largeBiped', 'wideBiped', 'familiar', 'flyer']);

function isBody(x: unknown): x is Body {
  return typeof x === 'object' && x !== null && 'id' in x && 'parts' in x && 'anchors' in x;
}

const inside = (pt: number[], w: number, h: number) =>
  pt[0] >= 0 && pt[0] < w && pt[1] >= 0 && pt[1] < h;

const bodies = new Map<string, Body>();
for (const file of readdirSync(dir).filter((f) => f.endsWith('.json'))) {
  const parsed: unknown = JSON.parse(readFileSync(new URL(file, dir), 'utf8'));
  assert.ok(isBody(parsed), `${file}: a body plan`);
  assert.equal(`${parsed.id}.json`, file, `${file}: named by its id`);
  bodies.set(parsed.id, parsed);
}

const folk = ANIMATION.cast.folk;
const familiars = ANIMATION.cast.familiars;
assert.equal(bodies.size, folk.length + familiars.length, 'one body plan per folk and familiar');

for (const b of bodies.values()) {
  const spec = folk.find((f) => f.id === b.id) ?? familiars.find((f) => f.id === b.id);
  assert.ok(spec, `${b.id}: in the animation spec's cast`);
  assert.equal(b.heightWorld, spec.heightWorld, `${b.id}: height matches the spec`);
  assert.equal(b.cell, spec.cell, `${b.id}: cell matches the spec`);
  assert.ok(TEMPLATES.has(b.template), `${b.id}: template ${b.template}`);
  assert.ok(b.signature.length > 0, `${b.id}: has a signature`);
  for (const f of b.families) assert.ok(RAMPS.has(f), `${b.id}: family ${f} is a house ramp`);
  for (const g of b.glows) assert.ok(GLOWS.has(g), `${b.id}: glow ${g}`);
  assert.ok(b.parts.length >= 6, `${b.id}: a rig needs parts`);
  assert.ok(
    b.parts.some((p) => p.painter),
    `${b.id}: a face painter`,
  );
  for (const p of b.parts) {
    const where = `${b.id}.${p.name}`;
    assert.ok(JOINTS.has(p.joint), `${where}: joint ${p.joint}`);
    for (const f of ['S', 'E', 'W', 'N']) {
      assert.equal(typeof p.layer[f], 'number', `${where}: layer for ${f}`);
    }
    for (const f of p.families) {
      assert.ok(RAMPS.has(f) || GLOWS.has(f), `${where}: family ${f}`);
    }
  }
  const cell = ANIMATION.cells[b.cell];
  for (const [pose, pt] of Object.entries(b.anchors.perch ?? {})) {
    assert.ok(inside(pt, cell.w * 2, cell.h * 2), `${b.id}: perch ${pose} inside the cell`);
  }
  const perch = ANIMATION.cells.familiarPerch;
  for (const [pose, pt] of Object.entries(b.anchors.holdOn ?? {})) {
    assert.ok(
      inside(pt, perch.w * 2, perch.h * 2),
      `${b.id}: hold-on ${pose} inside the perch cell`,
    );
  }
  if (b.kind === 'familiar') assert.ok(b.anchors.growth, `${b.id}: a head-top growth anchor`);
}

const parts = [...bodies.values()].reduce((n, b) => n + b.parts.length, 0);
console.log(
  `PASS: ${bodies.size} body plans (${parts} parts) match the cast, the cells and the house palette.`,
);
