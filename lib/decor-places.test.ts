import assert from 'node:assert/strict';
import {
  checkDecor,
  decorDepth,
  hutSurfaces,
  placeOf,
  raised,
  restoreDecor,
  snapDecorFor,
  tapToDecorate,
  turnHand,
  walkWithDecor,
  hutWalk,
} from './decor';
import { decorSizes } from './decor-sizes';
import { zoneMaps } from './zone-maps';

// Decorating that makes sense (coherence plan H1): small keepsakes stand on the hut's
// surfaces as well as its floor, take no floor there, and any keepsake can be turned.
let checks = 0;
const ok = (c: unknown, m: string) => {
  assert.ok(c, m);
  checks++;
};

const surfaces = hutSurfaces();
ok(
  surfaces.length >= 6,
  'the hut has surfaces: the mantel, the bookcase, the counter, the table, the sill',
);
for (const s of surfaces) {
  const under = zoneMaps.home.objects.find(
    ([, , x, y, w, h]) => s.x >= x && s.x < x + w && s.y >= y && s.y <= y + h,
  );
  ok(under || s.on === 'the window sill', `${s.on} at (${s.x}, ${s.y}) lies on the furniture`);
}
ok(
  placeOf('shell_bowl') === 'surface' && placeOf('stool') === 'floor',
  'small things may go on surfaces',
);

const [mantel] = surfaces;
ok(checkDecor('hut', [], 'shell_bowl', mantel.x, mantel.y).ok, 'a bowl stands on the mantel');
ok(!checkDecor('hut', [], 'stool', mantel.x, mantel.y).ok, 'a stool does not');
ok(raised({ item: 'shell_bowl', x: mantel.x, y: mantel.y }), 'on the mantel it is raised');
const hearth = zoneMaps.home.objects.find(([id]) => id === 'hearth');
ok(
  hearth && decorDepth({ item: 'shell_bowl', x: mantel.x, y: mantel.y }) > hearth[3] + hearth[5],
  'it is drawn in front of the hearth it stands on',
);
ok(
  !raised({ item: 'shell_bowl', x: mantel.x, y: mantel.y, area: 'garden' }),
  'never raised in the garden',
);
ok(checkDecor('hut', [], 'shell_bowl', 160, 380).ok, 'small things may still stand on the floor');
const both = [{ item: 'shell_bowl', x: mantel.x, y: mantel.y }];
ok(
  !checkDecor('hut', both, 'star_globe', mantel.x, mantel.y).ok,
  'two keepsakes never share a surface',
);
const rows = walkWithDecor(hutWalk(), both);
ok(
  rows.join('') === walkWithDecor(hutWalk(), []).join(''),
  'a keepsake on a surface takes no floor',
);

const near = snapDecorFor('shell_bowl', 'hut', { x: mantel.x + 5, y: mantel.y + 6 });
ok(near.x === mantel.x && near.y === mantel.y, 'a tap near the mantel sets it on the mantel');
const stoolSnap = snapDecorFor('stool', 'hut', { x: mantel.x + 5, y: mantel.y + 6 });
ok(stoolSnap.x % 4 === 0 && stoolSnap.y % 4 === 0, 'a floor keepsake snaps to the floor grid');

const tap = tapToDecorate(
  [],
  'hut',
  { item: 'shell_bowl', at: null, flip: true },
  { x: mantel.x, y: mantel.y },
);
ok(
  tap.hand?.flip === true && tap.walk !== true && tap.walk !== null,
  'the hand keeps its turn and walks to the floor',
);
if (tap.walk && tap.walk !== true)
  ok(tap.walk.y > mantel.y, 'the companion walks to the floor in front of it');
ok(turnHand({ item: 'stool', at: null }).flip === true, 'TURN turns it');
ok(!turnHand({ item: 'stool', at: null, flip: true }).flip, 'and back');

const restored = restoreDecor(
  [
    { item: 'stool', x: 160, y: 380, flip: true },
    { item: 'rag_rug', x: 120, y: 380, flip: 'yes' },
  ],
  [],
);
ok(
  restored[0].flip === true && restored[1] && !('flip' in restored[1]),
  'a save keeps a turn, and only a real one',
);
ok(
  Object.keys(decorSizes).every((k) => placeOf(k) === 'floor' || placeOf(k) === 'surface'),
  'every keepsake has a place',
);
console.log(`Decor places: ${checks} checks passed.`);
