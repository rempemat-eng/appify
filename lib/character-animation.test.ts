/**
 * The character animation spec (art/characters/animation-spec.json) holds the
 * motion rules in AGENTS.md: anticipate, act and settle; finite effects; a
 * reduced-motion variant for every state; west drawn, never mirrored; frame and
 * memory budgets; and a state machine that ignores stale arrivals and naps.
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  ANIMATION,
  CHARACTER_SETS,
  type Density,
  type KindId,
  type SetId,
  drawnFrames,
  frameAt,
  frameCount,
  initialAnim,
  kindSpec,
  onEvent,
  sheetSize,
  stateOf,
  walkFrameMs,
} from './character-animation';

const KINDS: KindId[] = ['folk', 'familiar', 'visitor', 'resident', 'rival'];
const DENSITIES: Density[] = [1, 1.5, 2];
assert.deepEqual(ANIMATION.densities, DENSITIES, 'the densities the spec covers');

// 1. Every pose is described, every state has frames and a reduced variant.
for (const kind of KINDS) {
  const k = kindSpec(kind);
  for (const [setId, states] of Object.entries(k.sets)) {
    for (const [name, st] of Object.entries(states)) {
      const where = `${kind}.${setId}.${name}`;
      assert.ok(st.frames.length > 0, `${where}: has frames`);
      assert.ok(st.facings.length > 0, `${where}: has facings`);
      assert.ok(st.reduced, `${where}: has a reduced-motion variant`);
      for (const f of st.frames) {
        assert.ok(ANIMATION.poses[f.pose], `${where}: pose ${f.pose} is described`);
        assert.ok(f.ms >= 0, `${where}: frame time`);
        if (f.effect && f.effect !== 'signature' && f.effect !== 'special') {
          assert.ok(ANIMATION.effects[f.effect], `${where}: effect ${f.effect} exists`);
        }
      }
      if (st.next) assert.ok(stateOf(kind, st.next), `${where}: next state ${st.next} exists`);
      // West is drawn wherever east is.
      if (st.facings.includes('E') && kind !== 'rival') {
        assert.ok(st.facings.includes('W'), `${where}: W drawn beside E`);
      }
    }
  }
}

// 2. Anticipate, act, settle.
const SELF_STARTED = [
  'walk_start',
  'react',
  'nap_down',
  'nap_up',
  'fidget',
  'attack',
  'cast',
  'guard',
  'victory',
  'cheer',
  'special',
];
const RECEIVED = ['hit', 'faint', 'cling'];
for (const kind of KINDS) {
  for (const states of Object.values(kindSpec(kind).sets)) {
    for (const [name, st] of Object.entries(states)) {
      if (SELF_STARTED.includes(name) && st.frames.length > 1) {
        assert.equal(st.frames[0].phase, 'anticipate', `${kind}.${name}: starts with anticipation`);
        const last = st.frames[st.frames.length - 1].phase;
        assert.ok(last === 'settle' || last === 'hold', `${kind}.${name}: ends settled`);
        assert.ok(
          st.frames.some((f) => f.phase === 'act'),
          `${kind}.${name}: acts`,
        );
      }
      if (RECEIVED.includes(name)) {
        assert.equal(st.frames[0].phase, 'act', `${kind}.${name}: a received blow starts with act`);
      }
    }
  }
}

// 3. Effects are finite, and each has a reduced form.
for (const [id, fx] of Object.entries(ANIMATION.effects)) {
  assert.equal(fx.ms.length, fx.frames, `${id}: one time per frame`);
  assert.ok(fx.loop === false || fx.loop === 'whileState', `${id}: finite or tied to its state`);
  assert.ok(fx.reduced === 'omit' || fx.reduced === 'static', `${id}: reduced form`);
  assert.ok(
    fx.ms.every((ms) => ms > 0 && ms <= 1000),
    `${id}: frame times`,
  );
}

// 4. Reduced motion: no translation, no loop, and it never shows a loop's later frames.
for (const kind of KINDS) {
  for (const [setId, states] of Object.entries(kindSpec(kind).sets)) {
    for (const name of Object.keys(states)) {
      for (let t = 0; t < 4000; t += 37) {
        const anim = { ...initialAnim('E', 0), state: name };
        const f = frameAt(kind, anim, t, { reduced: true });
        assert.equal(f.dx, 0, `${kind}.${setId}.${name}: no x motion when reduced`);
        assert.equal(f.dy, 0, `${kind}.${setId}.${name}: no y motion when reduced`);
      }
      const st = states[name];
      if (st.loop) {
        const a = { ...initialAnim('E', 0), state: name };
        const poses = new Set<string>();
        for (let t = 0; t < 5000; t += 50) poses.add(frameAt(kind, a, t, { reduced: true }).pose);
        assert.equal(poses.size, 1, `${kind}.${name}: a loop is a held still when reduced`);
      }
    }
  }
}

// 5. Frame budgets match the plan (cast.md 5 and fights.md 6).
for (const kind of KINDS) {
  const planned = kindSpec(kind).framesPlanned ?? ANIMATION.kinds[kind].framesPlanned;
  if (planned !== undefined)
    assert.equal(frameCount(kind), planned, `${kind}: ${frameCount(kind)} frames`);
}
assert.equal(frameCount('folk'), 77);
assert.equal(
  drawnFrames('folk', 'fight').length,
  26,
  'folk fight set: 12 a facing plus the bow, E and W (fights.md 6)',
);
assert.equal(drawnFrames('familiar', 'fight').length, 12, 'familiar on the shoulder: 6 a facing');
assert.equal(drawnFrames('rival', 'fight').length, 13, 'a rival fights facing west only');
assert.ok(drawnFrames('rival', 'fight').every((f) => f.facing === 'W'));

// 6. Sheets fit a texture at every density, cells land on whole pixels.
for (const [id, cell] of Object.entries(ANIMATION.cells)) {
  for (const d of DENSITIES) {
    assert.ok(
      Number.isInteger(cell.w * d) && Number.isInteger(cell.h * d),
      `${id}: whole px at ${d}x`,
    );
  }
  assert.ok(cell.anchor[1] < cell.h && cell.anchor[0] < cell.w, `${id}: anchor inside the cell`);
}
const sheetsOf = (kind: KindId): SetId[] => CHARACTER_SETS.filter((s) => kindSpec(kind).sets[s]);
for (const d of DENSITIES) {
  for (const cell of ['folk', 'folkSmall', 'folkSmallTall', 'folkLarge']) {
    for (const set of sheetsOf('folk')) {
      const s = sheetSize('folk', set, cell, d);
      assert.ok(
        s.w <= ANIMATION.sheet.maxSidePx && s.h <= ANIMATION.sheet.maxSidePx,
        `folk ${set} ${cell} @${d}x: ${s.w}x${s.h}`,
      );
    }
  }
}

// 7. Memory per screen at the authoring density.
const d2: Density = 2;
const world =
  sheetSize('folk', 'world', 'folkLarge', d2).bytes +
  sheetSize('familiar', 'world', 'familiar', d2).bytes +
  6 * sheetSize('resident', 'world', 'resident', d2).bytes;
assert.ok(world <= ANIMATION.memoryBudgetBytes.worldScreen, `world screen ${world} bytes`);
const fight =
  2 * sheetSize('folk', 'fight', 'folkLarge', d2).bytes +
  2 * sheetSize('familiar', 'fight', kindSpec('familiar').setCells?.fight ?? 'familiar', d2).bytes;
assert.equal(kindSpec('familiar').setCells?.fight, 'familiarPerch', 'the familiar perches small');
assert.equal(kindSpec('visitor').setCells?.fight, 'familiarPerch', 'so does a befriended visitor');
assert.ok(fight <= ANIMATION.memoryBudgetBytes.fightScreen, `fight screen ${fight} bytes`);

// 8. Timings fit the game's own timeline (the game leads, never the animation).
const napDown = stateOf('folk', 'nap_down')!.spec;
assert.ok(
  napDown.frames.reduce((n, f) => n + f.ms, 0) <= napDown.maxTotalMs!,
  'the sit-down ends before onNap',
);
for (const name of ['attack', 'cast']) {
  const st = stateOf('folk', name)!.spec;
  const i = st.frames.findIndex((f) => f.impact);
  const at = st.frames.slice(0, i).reduce((n, f) => n + f.ms, 0);
  assert.equal(at, st.impactAtMs, `${name}: impact frame at ${at} ms`);
  assert.ok(at <= 200, `${name}: impact shows within game-battle's 200 ms step`);
}
assert.equal(
  walkFrameMs(6, ANIMATION.walk.speedWorldPerSec),
  100,
  'six frames over a 24 px stride at 40 px/s',
);

// 9. The state machine.
{
  let a = initialAnim('S', 0);
  a = onEvent('folk', a, 'WALK_START', 0, 'E');
  assert.equal(a.state, 'walk_start');
  assert.equal(frameAt('folk', a, 200).state, 'walk', 'walk_start hands on to walk');
  a = onEvent('folk', a, 'FACE', 300, 'N');
  assert.equal(a.facing, 'N');
  assert.equal(a.since, 80, 'turning keeps the walk clock (the walk began when walk_start ended)');
  const stale = onEvent('folk', a, 'NAP_START', 400);
  assert.equal(stale.state, a.state, 'a nap never starts mid-walk');
  a = onEvent('folk', a, 'WALK_CANCEL', 500);
  assert.equal(a.state, 'walk_stop', 'an interrupted walk settles');
  a = onEvent('folk', a, 'ARRIVE', 1000);
  assert.equal(a.state, 'idle', 'a stale arrival after a cancel is ignored');
  a = onEvent('folk', a, 'NAP_START', 1000);
  assert.equal(a.state, 'nap_down');
  assert.equal(frameAt('folk', a, 1600).state, 'nap');
  assert.equal(onEvent('folk', a, 'REACT', 1700).state, 'nap', 'a tap does not wake a sleeper');
  const walked = onEvent('folk', a, 'WALK_START', 1700, 'W');
  assert.equal(walked.state, 'walk', 'a walk from a nap starts at once');
  a = onEvent('folk', a, 'NAP_END', 2000);
  assert.equal(a.state, 'nap_up');
  a = onEvent('folk', a, 'SCREEN_INACTIVE', 2100);
  assert.ok(a.paused);
  assert.equal(frameAt('folk', a, 9000).state, 'nap_up', 'a paused machine does not advance');
  assert.equal(frameAt('folk', a, 9000).effect, undefined, 'no effects while inactive');
  a = onEvent('folk', a, 'SCREEN_ACTIVE', 9000);
  assert.ok(!a.paused);

  let f = onEvent('folk', initialAnim('E', 0), 'FIGHT_ENTER', 0, 'E');
  assert.equal(f.state, 'ready');
  assert.equal(
    onEvent('folk', f, 'WALK_START', 10).state,
    'ready',
    'world events are ignored in a fight',
  );
  f = onEvent('folk', f, 'CARD_ATTACK', 100);
  assert.ok(frameAt('folk', f, 260).impact, 'impact frame shows 160 ms after the card');
  f = onEvent('folk', f, 'TAKE_HIT', 700);
  assert.equal(f.state, 'hit');
  f = onEvent('folk', f, 'KNOCKED_OUT', 800);
  assert.equal(frameAt('folk', f, 5000).pose, 'sit', 'the faint ends sitting, held');
  assert.equal(onEvent('folk', f, 'WIN', 5100).state, 'faint', 'no cheering after sitting down');
  assert.equal(onEvent('folk', f, 'BOW', 5200).state, 'bow', 'the loser stands for the bow');
  assert.equal(onEvent('folk', f, 'FIGHT_EXIT', 6000).state, 'idle');
  const still = onEvent(
    'folk',
    onEvent('folk', initialAnim('E', 0), 'FIGHT_ENTER', 0),
    'STILL_TURN',
    10,
  );
  assert.equal(still.state, 'still');
  assert.equal(frameAt('folk', still, 900).state, 'ready', 'a still turn settles back to ready');

  // The familiar maps folk-only states to its own.
  const fam = onEvent('familiar', initialAnim('S', 0), 'NAP_START', 0);
  assert.equal(fam.state, 'nap', 'the familiar curls up at once');
  const perch = onEvent('familiar', initialAnim('E', 0), 'FIGHT_ENTER', 0);
  assert.equal(perch.state, 'perch');
  assert.equal(onEvent('familiar', perch, 'TAKE_HIT', 10).state, 'cling');

  // Reduced motion: no loops, skips go straight on.
  const r = onEvent('folk', initialAnim('S', 0), 'WALK_START', 0, 'E');
  assert.equal(
    frameAt('folk', r, 1, { reduced: true }).pose,
    'idle_a',
    'a reduced walk is a standing still',
  );
}

// 10. Claude L's fight beats (lib/fight-content.ts) all map onto this spec.
for (const beat of [
  'ready',
  'windup',
  'strike',
  'impact',
  'cast',
  'guard',
  'hit',
  'heal',
  'stack',
  'special',
  'doze',
  'bell',
  'sitDown',
  'cheer',
  'bow',
]) {
  const b = ANIMATION.fightBeats[beat];
  assert.ok(b && typeof b === 'object', `beat ${beat} is mapped`);
  if (b.state) assert.ok(stateOf('folk', b.state), `beat ${beat}: state ${b.state}`);
  if (b.familiarState)
    assert.ok(stateOf('familiar', b.familiarState), `beat ${beat}: familiar ${b.familiarState}`);
  if (b.effect && b.effect !== 'signature')
    assert.ok(ANIMATION.effects[b.effect], `beat ${beat}: effect ${b.effect}`);
  if (b.frame !== undefined)
    assert.ok(stateOf('folk', b.state!)!.spec.frames[b.frame], `beat ${beat}: frame ${b.frame}`);
}
const impactBeat = ANIMATION.fightBeats.impact;
assert.ok(
  typeof impactBeat === 'object' &&
    impactBeat.frame !== undefined &&
    stateOf('folk', 'attack')!.spec.frames[impactBeat.frame].impact,
  'the impact beat is the impact frame of the attack',
);

// 11. Every transition's target exists somewhere; the cast matches cast.md.
const special = new Set(['same', 'paused', 'resumed']);
for (const t of ANIMATION.machine.transitions) {
  if (t.to === null || special.has(t.to)) continue;
  assert.ok(
    KINDS.some((k) => stateOf(k, t.to!)),
    `transition target ${t.to}`,
  );
}
const cast = readFileSync(new URL('../docs/vision/cast.md', import.meta.url), 'utf8');
assert.equal(ANIMATION.cast.folk.length, 14, 'fourteen folk');
assert.equal(ANIMATION.cast.folk.filter((f) => f.firstSix).length, 6);
for (const f of ANIMATION.cast.folk)
  assert.ok(cast.includes(`**${f.name}**`), `${f.name} is in cast.md`);
assert.deepEqual(
  ANIMATION.cast.folk.map((f) => f.night),
  Array.from({ length: 14 }, (_, i) => i + 1),
  'one folk a night, in cast.md order',
);
assert.equal(ANIMATION.cast.visitors.length, 9, 'nine visitors');
for (const f of ANIMATION.cast.folk)
  assert.ok(ANIMATION.cells[f.cell], `${f.name}: cell ${f.cell} exists`);

console.log(
  `PASS: character animation spec: folk ${frameCount('folk')} frames, familiar ${frameCount('familiar')}, resident ${frameCount('resident')}, rival ${frameCount('rival')}; world screen ${(world / 1048576).toFixed(2)} MB, fight ${(fight / 1048576).toFixed(2)} MB at 2x; anticipate-act-settle, finite effects, reduced motion and the state machine hold.`,
);
