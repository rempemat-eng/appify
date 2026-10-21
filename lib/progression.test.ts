import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import {
  folkById,
  openRegions,
  openStops,
  progression,
  regionById,
  road,
  stories,
  storyById,
  taskWords,
  wayByLabel,
  waysBefore,
} from './progression';
import { routeGates, routeStops, worldThresholds } from './world-routes';
import { worldWays } from './world-ways';

/**
 * The progression spine (art/story/progression.json) and the resident stories
 * (art/story/stories.json) against each other, against Claude G's route graph
 * (lib/world-routes.ts), the ways catalogue (lib/world-ways.ts), the cast (cast.md) and
 * Matt's rules for stories. Data only: no game rule is exercised here.
 */

const { regions, folk, outings, comforts, home, start } = progression;
const labels = road.map((w) => w.id);

// The road: W1 to W9 in order, each way's prerequisites earlier on the road.
assert.deepEqual(labels, ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8', 'W9']);
road.forEach((way, i) => {
  for (const before of way.after)
    assert.ok(labels.indexOf(before) < i, `${way.id} comes after ${before} on the road`);
  assert.ok(way.dust > 0, `${way.id} has a Dream Dust price`);
  assert.ok(taskWords(way.task).length > 0);
  assert.ok(
    worldWays.some((w) => w.id === way.catalogueId),
    `${way.id} names a way in lib/world-ways.ts (${way.catalogueId})`,
  );
  if (way.threshold !== null)
    assert.ok(
      worldThresholds.some((t) => t.id === way.threshold),
      `${way.id}'s threshold ${way.threshold} is one of Claude G's`,
    );
  for (const stop of way.opensStops) assert.ok(stop in routeStops, `${way.id} opens ${stop}`);
});
assert.deepEqual(waysBefore('W9'), ['W3', 'W7', 'W8']);
assert.deepEqual(waysBefore('W6'), ['W5']);

// Matt's prices and tasks for the road (world-unlocks.md 2.4) stay as the catalogue has them.
for (const way of road) {
  const entry = worldWays.find((w) => w.id === way.catalogueId)!;
  assert.equal(way.dust, entry.grass, `${way.id} costs what the catalogue says`);
  assert.equal(way.task.kind, entry.task?.kind, `${way.id}'s task kind matches the catalogue`);
}

// The walkable world after each opening matches Claude G's gate steps exactly.
for (const step of routeGates) {
  if (step.open === 'start') {
    assert.deepEqual([...start.stopsOpen].sort(), [...step.reached].sort(), 'start stops');
    continue;
  }
  const upto = labels.slice(0, labels.findIndex((l) => l === step.open) + 1);
  assert.deepEqual(openStops(new Set(upto)), [...step.reached].sort(), `stops with ${step.open}`);
}

// Regions: open from the start or behind exactly one way that names them; one story each.
assert.deepEqual(openRegions(new Set()), start.regionsOpen);
assert.equal(regions.length, 11);
for (const region of regions) {
  if (region.opensWith !== null) {
    const way = wayByLabel(region.opensWith);
    assert.ok(way?.opensRegions.includes(region.id), `${region.opensWith} opens ${region.id}`);
  }
  assert.ok(storyById(region.story), `${region.id} has its story`);
  assert.ok(region.spots.length >= 3, `${region.id} has at least three rest spots`);
  const ids = region.spots.map((s) => s.id);
  assert.equal(new Set(ids).size, ids.length, `${region.id}'s spot ids are unique`);
  assert.ok(
    region.spots.some((s) => s.night),
    `${region.id} has somewhere to spend a night`,
  );
  if (region.plan.file && region.plan.pr === null)
    assert.ok(existsSync(region.plan.file), `${region.plan.file} exists on main`);
}
for (const way of road)
  for (const id of way.opensRegions)
    assert.equal(regionById(id)?.opensWith, way.id, `${id} opens with ${way.id}`);
assert.equal(regions.filter((r) => r.spots.some((s) => s.default)).length, 1, 'one default spot');

// Fourteen folk, one per night of the moon (cast.md): three starters and eleven apprentices.
assert.equal(folk.length, 14);
assert.deepEqual(
  folk.map((f) => f.night),
  Array.from({ length: 14 }, (_, i) => i + 1),
);
assert.deepEqual(
  folk.filter((f) => f.joins.kind === 'start').map((f) => f.id),
  start.folkChoice,
);
for (const f of folk)
  if (f.joins.kind === 'story') {
    const story = storyById(f.joins.story);
    assert.ok(story, `${f.id} joins through a story`);
    assert.equal(story.apprentice, f.id, `${f.id} is ${story.id}'s apprentice`);
    assert.equal(f.home, story.region);
  }
assert.equal(folkById(progression.journeyEnd.folk)?.night, 14, 'the journey ends with night 14');
assert.ok(storyById(start.othersJoin.story), 'the other starters join through a real story');

// Stories: three chapters each, set at the region's own spots, in the house voice.
assert.equal(stories.length, 11);
const banned =
  /\b(missed|late|failed|hurry|should|streak|self-care|mindfulness|boundaries|while you slept|all night)\b|!/;
for (const story of stories) {
  const region = regionById(story.region)!;
  assert.equal(region.story, story.id);
  assert.deepEqual(
    story.chapters.map((c) => c.n),
    [1, 2, 3],
  );
  story.chapters.forEach((c) => {
    assert.ok(
      region.spots.some((s) => s.id === c.spot),
      `${story.id} ch ${c.n} is set at one of ${region.id}'s spots (${c.spot})`,
    );
    assert.equal(c.beat, c.beat.toLowerCase(), `${story.id} ch ${c.n}'s beat is lowercase`);
    assert.ok(c.beat.split(/\s+/).length < 40, `${story.id} ch ${c.n}'s beat is short`);
    assert.doesNotMatch(c.beat, banned, `${story.id} ch ${c.n}'s beat`);
    assert.ok(c.lines.length >= 2 && c.lines.length <= 4);
    for (const line of c.lines) {
      assert.equal(line.text, line.text.toLowerCase(), `${story.id}: "${line.text}"`);
      assert.ok(line.text.length <= 90, `${story.id}: "${line.text}" fits a bubble`);
      assert.doesNotMatch(line.text, banned, `${story.id}: "${line.text}"`);
    }
    assert.equal(c.change === null, c.n === 1, `${story.id}: chapters 2 and 3 leave a change`);
  });
  for (const text of [story.join.ask, story.rival?.invite ?? '']) {
    assert.ok(text.length <= 90);
    assert.doesNotMatch(text, banned);
  }
  assert.equal(story.rival === null, region.ring === null || story.id === 'valley');
}

// Outings never pay above Book Club's rate (gameplay-regions G3) and sit at their region's spots.
for (const outing of outings) {
  const region = regionById(outing.region)!;
  assert.ok(
    region.spots.some((s) => s.id === outing.spot),
    `${outing.id} sits at a spot`,
  );
  if (outing.status === 'proposal') {
    assert.ok(outing.dust / outing.minutes <= 2, `${outing.id} pays at most 2 a minute`);
    assert.ok(outing.dust <= 240);
  }
}

// Comforts and the home: Dust only, after their way, never gating a place.
for (const comfort of comforts) {
  assert.ok(regionById(comfort.region));
  if (comfort.after) assert.ok(wayByLabel(comfort.after), `${comfort.id} after a real way`);
  if (comfort.afterStory) assert.ok(storyById(comfort.afterStory));
}
const steps = home.steps.map((s) => s.id);
home.steps.forEach((step, i) => {
  if (step.after) assert.ok(steps.indexOf(step.after) < i, `${step.id} after ${step.after}`);
  assert.ok(step.dust > 0 && step.restMinutes > 0);
});

console.log(
  `Progression spine: ${road.length} ways, ${regions.length} regions, ${folk.length} folk, ${stories.length} stories, ${outings.length} outings, ${comforts.length} comforts, ${home.steps.length} home steps.`,
);
