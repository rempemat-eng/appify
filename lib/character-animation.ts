/**
 * The shared character animation spec (art/characters/animation-spec.json) as
 * typed data, and a pure state machine that maps game events to animation
 * frames. Nothing here touches React, timers or the platform: a component
 * feeds it events and the clock, and draws the frame it returns. It never
 * delays or changes a game callback (docs/vision/characters/animation.md).
 */
import source from '../art/characters/animation-spec.json';

export type Facing = 'S' | 'N' | 'E' | 'W';
export type Phase = 'anticipate' | 'act' | 'settle' | 'hold';
export type Density = 1 | 1.5 | 2;
export const CHARACTER_SETS: readonly SetId[] = ['world', 'fight'];
export type KindId = 'folk' | 'familiar' | 'visitor' | 'resident' | 'rival';
export type SetId = 'world' | 'fight';

export type FrameSpec = {
  pose: string;
  ms: number;
  phase: Phase;
  dx?: number;
  dy?: number;
  effect?: string;
  impact?: boolean;
};

export type ReducedSpec = {
  hold?: number;
  pose?: string;
  ms?: number;
  skip?: boolean;
  effect?: string;
  stills?: { frame: number; ms: number }[];
};

export type StateSpec = {
  facings: Facing[];
  frames: FrameSpec[];
  loop?: boolean;
  repeats?: number;
  next?: string;
  overlay?: string;
  everyMs?: [number, number];
  speedSynced?: boolean;
  maxTotalMs?: number;
  impactAtMs?: number;
  reduced: ReducedSpec;
};

export type KindSpec = {
  sets: Partial<Record<SetId, Record<string, StateSpec>>>;
  /** A cell per set when they differ (the familiar's small perch sprite in fights). */
  setCells?: Partial<Record<SetId, string>>;
  framesPlanned?: number;
  effectsPlanned?: number;
};

export type CellSpec = { w: number; h: number; anchor: [number, number] };

export type EffectSpec = {
  frames: number;
  ms: number[];
  layer: 'ground' | 'over' | 'palette';
  loop: false | 'whileState';
  reduced: 'omit' | 'static';
};

export type GameEvent =
  | 'WALK_START'
  | 'FACE'
  | 'ARRIVE'
  | 'WALK_CANCEL'
  | 'REACT'
  | 'IDLE_BEAT'
  | 'NAP_START'
  | 'NAP_END'
  | 'FIGHT_ENTER'
  | 'CARD_ATTACK'
  | 'CARD_CAST'
  | 'CARD_GUARD'
  | 'TAKE_HIT'
  | 'KNOCKED_OUT'
  | 'WIN'
  | 'FIGHT_EXIT'
  | 'STILL_TURN'
  | 'BOW'
  | 'SCREEN_INACTIVE'
  | 'SCREEN_ACTIVE';

export type Transition = {
  from: string;
  on: GameEvent | GameEvent[];
  to: string | null;
  onlyFrom?: string[];
  notFrom?: string[];
};

type RawKind = KindSpec & {
  inherit?: { kind: KindId; set?: SetId; facings?: Facing[] }[];
};

type Raw = {
  version: number;
  authorDensity: number;
  densities: number[];
  facings: Facing[];
  walk: { speedWorldPerSec: number; strideWorld: number };
  cells: Record<string, CellSpec & { note?: string }>;
  sheet: { columns: number; maxSidePx: number };
  memoryBudgetBytes: { worldScreen: number; fightScreen: number };
  poses: Record<string, string>;
  kinds: Record<KindId, RawKind>;
  effects: Record<string, EffectSpec>;
  machine: {
    events: Record<GameEvent, string>;
    groups: Record<string, string[]>;
    initial: string;
    transitions: Transition[];
    familiarMap: Record<string, string>;
  };
  fightBeats: Record<
    string,
    | {
        state?: string;
        folkState?: string;
        familiarState?: string;
        frame?: number;
        effect?: string;
        onFoe?: boolean;
        folk?: string;
      }
    | string
  >;
  cast: {
    folk: {
      id: string;
      name: string;
      night: number;
      heightWorld: number;
      cell: string;
      firstSix?: boolean;
    }[];
    familiars: { id: string; family: string; heightWorld: number; cell: string }[];
    visitors: string[];
  };
};

const SETS = CHARACTER_SETS;

/** A light shape check, so the JSON is typed by a guard rather than a cast. */
function isSpec(x: unknown): x is Raw {
  if (typeof x !== 'object' || x === null) return false;
  const keys = new Set(Object.keys(x));
  return ['kinds', 'poses', 'effects', 'machine', 'cells', 'cast', 'sheet', 'walk'].every((key) =>
    keys.has(key),
  );
}

function load(x: unknown): Raw {
  if (!isSpec(x))
    throw new Error('art/characters/animation-spec.json: not a character animation spec');
  return x;
}

export const ANIMATION: Raw = load(source);

/** A kind with its inherited sets merged in (visitor = familiar; rival = resident + folk fight W). */
export function kindSpec(kind: KindId): KindSpec {
  const raw = ANIMATION.kinds[kind];
  const sets: KindSpec['sets'] = {};
  for (const inc of raw.inherit ?? []) {
    const parent = kindSpec(inc.kind);
    for (const setId of SETS) {
      const states = parent.sets[setId];
      if (!states || (inc.set && inc.set !== setId)) continue;
      const out: Record<string, StateSpec> = { ...sets[setId] };
      for (const [name, st] of Object.entries(states)) {
        const facings = inc.facings
          ? st.facings.filter((f) => inc.facings!.includes(f))
          : st.facings;
        if (facings.length) out[name] = { ...st, facings };
      }
      sets[setId] = out;
    }
  }
  for (const setId of SETS) {
    const own = raw.sets?.[setId];
    if (own) sets[setId] = { ...sets[setId], ...own };
  }
  return {
    sets,
    setCells: raw.setCells ?? ANIMATION.kinds[raw.inherit?.[0]?.kind ?? kind].setCells,
    framesPlanned: raw.framesPlanned,
    effectsPlanned: raw.effectsPlanned,
  };
}

export function stateOf(kind: KindId, name: string): { set: SetId; spec: StateSpec } | null {
  const k = kindSpec(kind);
  for (const setId of SETS) {
    const spec = k.sets[setId]?.[name];
    if (spec) return { set: setId, spec };
  }
  return null;
}

/** The drawn frames of one set: every distinct (pose, facing) pair, in sheet order. */
export function drawnFrames(kind: KindId, set: SetId): { pose: string; facing: Facing }[] {
  const states = kindSpec(kind).sets[set] ?? {};
  const seen = new Set<string>();
  const out: { pose: string; facing: Facing }[] = [];
  for (const st of Object.values(states)) {
    for (const facing of st.facings) {
      for (const f of st.frames) {
        const key = `${f.pose}:${facing}`;
        if (seen.has(key)) continue;
        seen.add(key);
        out.push({ pose: f.pose, facing });
      }
    }
  }
  return out;
}

export function frameCount(kind: KindId): number {
  const k = kindSpec(kind);
  return SETS.filter((s) => k.sets[s]).reduce((n, s) => n + drawnFrames(kind, s).length, 0);
}

/** Sheet size in art px at a density: a grid `columns` cells wide. */
export function sheetSize(kind: KindId, set: SetId, cellId: string, density: Density) {
  const cell = ANIMATION.cells[cellId];
  const frames = drawnFrames(kind, set).length;
  const cols = Math.min(ANIMATION.sheet.columns, frames);
  const rows = Math.ceil(frames / ANIMATION.sheet.columns);
  const w = cols * cell.w * density;
  const h = rows * cell.h * density;
  return { frames, w, h, bytes: w * h * 4 };
}

/** A rig px offset (authored at density 2) at another density. */
export const rigPx = (value: number, density: Density) =>
  Math.round((value * density) / ANIMATION.authorDensity);

/** Frame time for a speed-synced walk at a given speed, so the feet never slide. */
export function walkFrameMs(frames: number, speedWorldPerSec: number): number {
  return (1000 * ANIMATION.walk.strideWorld) / (speedWorldPerSec * frames);
}

// ---------------------------------------------------------------------------
// The state machine

export type AnimState = {
  state: string;
  facing: Facing;
  /** Clock time the state began. */
  since: number;
  paused: boolean;
};

export const initialAnim = (facing: Facing = 'S', now = 0): AnimState => ({
  state: ANIMATION.machine.initial,
  facing,
  since: now,
  paused: false,
});

function matches(from: string, state: string): boolean {
  if (from === '*') return true;
  if (from === state) return true;
  return ANIMATION.machine.groups[from]?.includes(state) ?? false;
}

/**
 * Apply one game event. The first matching transition wins; `null` ignores the
 * event, `same` keeps the state and its clock (only the facing changes).
 */
export function onEvent(
  kind: KindId,
  anim: AnimState,
  event: GameEvent,
  now: number,
  facing?: Facing,
): AnimState {
  const current = settle(kind, anim, now);
  for (const t of ANIMATION.machine.transitions) {
    const events = Array.isArray(t.on) ? t.on : [t.on];
    if (!events.includes(event) || !matches(t.from, current.state)) continue;
    if (t.onlyFrom && !t.onlyFrom.includes(current.state)) continue;
    if (t.notFrom && t.notFrom.includes(current.state)) continue;
    if (t.to === null) return current;
    if (t.to === 'paused') return { ...current, paused: true };
    if (t.to === 'resumed') return { ...current, paused: false, since: now };
    if (t.to === 'same') return { ...current, facing: facing ?? current.facing };
    const target = stateOf(kind, t.to) ? t.to : fallbackState(kind, t.to);
    if (!target) return current;
    return { state: target, facing: facing ?? current.facing, since: now, paused: current.paused };
  }
  return current;
}

/** A familiar or resident lacks some folk states (fidget, nap_down); map them to its nearest. */
function fallbackState(kind: KindId, name: string): string | null {
  if (kind === 'familiar' || kind === 'visitor') {
    const mapped = ANIMATION.machine.familiarMap[name];
    if (mapped && stateOf(kind, mapped)) return mapped;
  }
  return stateOf(kind, 'idle') ? 'idle' : null;
}

function totalMs(st: StateSpec): number {
  return st.frames.reduce((n, f) => n + f.ms, 0) * (st.repeats ?? 1);
}

function reducedMs(st: StateSpec): number {
  const r = st.reduced;
  if (r.skip) return 0;
  if (r.stills) return r.stills.reduce((n, s) => n + s.ms, 0);
  if (r.ms !== undefined) return r.ms;
  return Infinity;
}

/** Follow `next` links for finished one-shot states, so the clock can jump ahead. */
export function settle(kind: KindId, anim: AnimState, now: number, reduced = false): AnimState {
  let cur = anim;
  for (let guard = 0; guard < 8; guard++) {
    const found = stateOf(kind, cur.state);
    if (!found) return cur;
    const st = found.spec;
    if (st.loop || !st.next) return cur;
    const length = reduced ? reducedMs(st) : totalMs(st);
    if (cur.paused || now - cur.since < length) return cur;
    cur = { ...cur, state: st.next, since: cur.since + length };
  }
  return cur;
}

export type FrameOut = {
  state: string;
  pose: string;
  facing: Facing;
  phase: Phase;
  dx: number;
  dy: number;
  effect?: string;
  impact: boolean;
};

function facingFor(st: StateSpec, wanted: Facing): Facing {
  return st.facings.includes(wanted) ? wanted : st.facings[0];
}

/**
 * The frame to draw now. With reduced motion every state is a still or a cut;
 * a paused machine shows its state's first frame with no effect.
 */
export function frameAt(
  kind: KindId,
  anim: AnimState,
  now: number,
  opts: { reduced?: boolean; speedWorldPerSec?: number } = {},
): FrameOut {
  const reduced = !!opts.reduced;
  const a = settle(kind, anim, now, reduced);
  const found = stateOf(kind, a.state) ?? stateOf(kind, 'idle')!;
  const st = found.spec;
  const facing = facingFor(st, a.facing);
  const out = (f: FrameSpec, motion: boolean, effect?: string): FrameOut => ({
    state: a.state,
    pose: f.pose,
    facing,
    phase: f.phase,
    dx: motion ? (f.dx ?? 0) : 0,
    dy: motion ? (f.dy ?? 0) : 0,
    effect,
    impact: !!f.impact,
  });
  if (reduced) {
    const r = st.reduced;
    if (r.stills) {
      let t = now - a.since;
      for (const s of r.stills) {
        if (t < s.ms) return out(st.frames[s.frame], false);
        t -= s.ms;
      }
      return out(st.frames[r.stills[r.stills.length - 1].frame], false);
    }
    const base = st.frames[r.hold ?? 0];
    const pose = r.pose ? { ...base, pose: r.pose } : base;
    return out(pose, false, a.paused ? undefined : r.effect);
  }
  if (a.paused) return out(st.frames[0], false);
  const synced =
    st.speedSynced && opts.speedWorldPerSec
      ? walkFrameMs(st.frames.length, opts.speedWorldPerSec)
      : null;
  const lengths = st.frames.map((f) => synced ?? f.ms);
  const cycle = lengths.reduce((n, ms) => n + ms, 0);
  let t = now - a.since;
  if (st.loop) t = cycle > 0 ? t % cycle : 0;
  else t = Math.min(t, cycle * (st.repeats ?? 1)) % (cycle || 1);
  const ended = !st.loop && now - a.since >= cycle * (st.repeats ?? 1);
  if (ended) {
    const last = st.frames[st.frames.length - 1];
    return out(last, true);
  }
  for (let i = 0; i < st.frames.length; i++) {
    if (t < lengths[i] || lengths[i] === 0) return out(st.frames[i], true, st.frames[i].effect);
    t -= lengths[i];
  }
  return out(st.frames[st.frames.length - 1], true);
}
