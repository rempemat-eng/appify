import assert from 'node:assert/strict';
import {
  PLOT_STAGES,
  TREE_STAGES,
  meadowLine,
  meadowSummary,
  orchardSownAt,
  orchardStage,
  plotSownAt,
  plotStage,
} from './garden-growth';
import { gardenOrchard, gardenPlots, growthSpriteSizes } from './garden-map';

// A new garden is an empty meadow, and bad input never throws or grows anything.
for (const bad of [0, -5, Number.NaN, Number.NEGATIVE_INFINITY]) {
  assert.equal(meadowSummary(bad).planted, 0);
  for (let i = 0; i < plotSownAt.length; i++) assert.equal(plotStage(bad, i), -1);
}
assert.equal(plotStage(1000, 99), -1, 'unknown beds stay empty');

// Growth only moves forward as minutes accumulate.
for (let i = 0; i < plotSownAt.length; i++) {
  let previous = -1;
  for (let m = 0; m <= 400; m++) {
    const s = plotStage(m, i);
    assert.ok(s >= previous && s >= -1 && s < PLOT_STAGES, `bed ${i} at ${m}`);
    previous = s;
  }
  assert.equal(plotStage(plotSownAt[i], i), 0, 'a bed is sown at its threshold');
}
for (let i = 0; i < orchardSownAt.length; i++) {
  let previous = -1;
  for (let m = 0; m <= 1500; m += 5) {
    const s = orchardStage(m, i);
    assert.ok(s >= previous && s < TREE_STAGES, `tree ${i} at ${m}`);
    previous = s;
  }
  assert.equal(orchardStage(5000, i), TREE_STAGES - 1, 'every tree eventually fruits');
}

// The sign always points at the next change until the meadow is complete.
assert.ok(meadowSummary(0).nextIn === plotSownAt[0]);
const full = meadowSummary(5000);
assert.equal(full.nextIn, null);
assert.equal(full.blooming, plotSownAt.length);
assert.equal(full.fruiting, orchardSownAt.length);
for (const m of [0, 12, 75, 260, 5000]) {
  const line = meadowLine(m);
  assert.ok(line.length > 10 && line.length < 110, line);
  assert.ok(
    !/GRASS|DREAM DUST|reward|streak|lose|wilt/i.test(line),
    'the meadow never nags or rewards',
  );
}

// The generated map has a bed and a pit for every growth slot, and every stage has art.
assert.equal(gardenPlots.length, plotSownAt.length);
assert.equal(gardenOrchard.length, orchardSownAt.length);
for (const plot of gardenPlots)
  for (let s = 0; s < PLOT_STAGES; s++)
    assert.ok(`plot_${plot.kind}_${s}` in growthSpriteSizes, `${plot.kind} stage ${s} art`);
for (let s = 0; s < TREE_STAGES; s++) assert.ok(`orchard_${s}` in growthSpriteSizes);

console.log('PASS: meadow growth is monotonic, bounded, fully illustrated and never nags.');
