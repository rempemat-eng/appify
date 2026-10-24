import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  MYGAME_CHARACTERS,
  clipDuration,
  crossedRelease,
  makeMyGameWorldSupport,
  myGameClip,
  projectMyGameCharacter,
  sampleMyGameClip,
  type MyGameCharacterAsset,
  type MyGameClip,
} from './mygame-character';
import { WORLD_TILE, worldTiles, worldDecks, unrle } from './world-canvas';

const clip: MyGameClip = {
  frames: [0.1, 0.2, 0.05, 0.4].map((duration) => ({
    asset: 'strip.png',
    rect: [0, 0, 192, 192],
    atlasSize: [768, 192],
    cropOffset: [0, 0],
    duration,
  })),
  loop: false,
  releaseFrame: 2,
  holdFrame: 1,
  releaseAnchor: [50, -60],
};
assert.equal(clipDuration(clip), 0.75);
assert.equal(sampleMyGameClip(clip, 0.15).index, 1, 'weighted timing, not uniform pose index');
assert.equal(sampleMyGameClip(clip, 0.34).index, 2, 'brief release pose remains brief');
assert.equal(sampleMyGameClip(clip, 10).index, 3, 'one shot holds its final pose');
assert.equal(sampleMyGameClip(clip, 10).finished, true);
assert.equal(
  sampleMyGameClip({ ...clip, loop: true }, 0.9).index,
  1,
  'loop wraps weighted timeline',
);
assert.equal(
  sampleMyGameClip(clip, 0.5, { holding: true }).index,
  1,
  'guard freezes at authored hold',
);
assert.equal(sampleMyGameClip(clip, 0.5, { holding: true }).finished, false);
assert.equal(
  sampleMyGameClip(clip, 10, { holding: true, reducedMotion: true }).finished,
  false,
  'reduced-motion guard stays held too',
);
assert.equal(
  sampleMyGameClip(clip, 0.01, { reducedMotion: true }).index,
  2,
  'reduced motion presents act pose',
);
assert.ok(crossedRelease(clip, 0.25, 0.6), 'a slow render still observes the release crossing');
assert.equal(crossedRelease(clip, 0.6, 0.7), false, 'release is not repeated next frame');
assert.equal(crossedRelease(clip, 0.6, 0.1), false, 'clock reset cannot release the old action');
assert.equal(
  crossedRelease({ ...clip, loop: true }, 0.25, 0.6),
  false,
  'looping presentation cannot fire a combat release',
);

const geometry = {
  frameSize: [192, 192] as const,
  footPivot: [96, 172] as const,
  bodyHeight: 112,
  clips: { primary: clip },
};
const asset: MyGameCharacterAsset = { id: 'cairn', views: { E: geometry } };
assert.equal(
  myGameClip(asset, 'W', 'primary'),
  undefined,
  'missing west is never mirrored or relabelled',
);
assert.equal(
  myGameClip(asset, 'E', 'powered_secondary'),
  undefined,
  'missing abilities are never hidden by a base fallback',
);
const projectionInput = {
  asset: geometry,
  foot: { x: 100.2, y: 150.3 },
  supportHeight: 8,
  airborneHeight: 0,
  worldUnit: 2,
  assetPixelsPerWorldPixel: 4,
  devicePixelRatio: 2,
};
const grounded = projectMyGameCharacter(projectionInput);
const jumping = projectMyGameCharacter({ ...projectionInput, airborneHeight: 12 });
assert.equal(jumping.depth, grounded.depth, 'jumping preserves ground-foot sorting');
assert.equal(grounded.depth, 150, 'AtlasWalk zIndex uses unscaled region y, not rendered pixels');
assert.deepEqual(jumping.shadow, grounded.shadow, 'shadow remains on support');
assert.equal(jumping.top, grounded.top - 24, 'body rises by world height');
assert.equal(
  jumping.anchor([50, -60]).y,
  grounded.anchor([50, -60]).y - 24,
  'weapon anchor and body rise together',
);
assert.equal(
  grounded.left * 2,
  Math.round(grounded.left * 2),
  'snap the composite once to a device pixel',
);
assert.equal(grounded.crisp, true);
assert.equal(
  projectMyGameCharacter({ ...projectionInput, devicePixelRatio: 1 }).crisp,
  false,
  'half a device pixel is reported instead of called crisp',
);
assert.throws(() => projectMyGameCharacter({ ...projectionInput, assetPixelsPerWorldPixel: 0 }));

const support = makeMyGameWorldSupport({
  tileSize: WORLD_TILE.size,
  cellSize: WORLD_TILE.cell,
  tiles: worldTiles,
});
let checked = 0;
for (const [plane, tiles] of Object.entries(worldTiles)) {
  for (const [key, tile] of Object.entries(tiles)) {
    const [tx, ty] = key.split(',').map(Number);
    const walk = unrle(tile.walk),
      terrain = unrle(tile.terrain);
    for (let index = 0; index < walk.length; index++) {
      const cell = support(plane, {
        x: tx * 256 + (index % 64) * 4 + 2,
        y: ty * 256 + Math.floor(index / 64) * 4 + 2,
      });
      assert.equal(
        cell.walkable,
        walk[index] === '.',
        `${plane}/${key}/${index} actual passability`,
      );
      assert.equal(cell.material, terrain[index], `${plane}/${key}/${index} actual material`);
      assert.equal(cell.height, 0, 'current generated world has no authored terrace/deck height');
      checked++;
    }
  }
}
assert.equal(
  worldDecks.length,
  0,
  'current source has no stair/ramp/lift placement; do not invent one',
);
assert.equal(
  support('continent', { x: -0.1, y: 0 }).walkable,
  false,
  'negative point does not alias tile zero',
);
assert.equal(support('missing', { x: 100, y: 100 }).walkable, false);
const future = makeMyGameWorldSupport({
  tileSize: 8,
  cellSize: 4,
  tiles: { plane: { '0,0': { walk: '4.', terrain: '4.', deck: '4.' } } },
});
assert.equal(future('plane', { x: 2, y: 2 }).needsHeightResolver, true);
assert.equal(
  future('plane', { x: 2, y: 2 }).height,
  undefined,
  'unknown level is not silently flattened',
);

// Export validation checks baseline E coverage, explicit partial views and atlas integrity.
// oxlint-disable-next-line typescript/no-unsafe-type-assertion -- generated exporter output, exercised below.
const catalogue = JSON.parse(
  readFileSync(
    new URL('../prototypes/mygame-world-preview/characters.json', import.meta.url),
    'utf8',
  ),
) as Record<string, MyGameCharacterAsset>;
for (const id of MYGAME_CHARACTERS) {
  const character = catalogue[id];
  assert.ok(character, id);
  for (const [view, viewGeometry] of Object.entries(character.views)) {
    const clips = viewGeometry.clips;
    for (const required of view === 'E' || viewGeometry.status === 'complete'
      ? [
          'idle',
          'walk',
          'primary',
          'secondary',
          'special',
          'guard',
          'hit',
          'defeat',
          'jump',
          'stair_up',
          'stair_down',
          'powered_primary',
        ]
      : [])
      assert.ok(clips[required], `${id}/${view}/${required}`);
    for (const missing of viewGeometry.missingClips ?? [])
      assert.equal(
        clips[missing],
        undefined,
        `${id}/${view}: declared missing ${missing} stays missing`,
      );
    for (const [name, c] of Object.entries(clips)) {
      assert.ok(c.frames.length, `${id}/${view}/${name}`);
      assert.ok(clipDuration(c) > 0);
      for (const f of c.frames) {
        assert.ok(f.duration > 0);
        assert.ok(f.atlasSize.every((n) => n <= 4096));
        assert.ok(
          f.rect[0] >= 0 &&
            f.rect[1] >= 0 &&
            f.rect[0] + f.rect[2] <= f.atlasSize[0] &&
            f.rect[1] + f.rect[3] <= f.atlasSize[1],
        );
      }
    }
  }
}
console.log(
  `MyGame presentation bridge: weighted events, guard holds, exact views, anchors and ${checked} real world cells verified; ${MYGAME_CHARACTERS.length} character exports checked.`,
);
