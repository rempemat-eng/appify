/**
 * The rocket and lander journeys' beats (Matt, 20 Oct: the rocket replaces the space
 * elevator; the lander to the moon stays). Pure and deterministic, so it can be tested
 * (lib/rocket-flight.test.ts) and run as worklets on the animation thread
 * (components/rocket-journey.tsx). Presentation only: it changes no journey time, cost,
 * unlock or rule; a leg lasts what it always did and only arrives at its end.
 *
 * Time is p, 0 to 1 over the leg. Space is the flight's column in art px: x 0 on the pad's
 * centre line, y 0 at the pad (down is positive), the station's docking port at y -dock.
 *
 * Four flights, each anticipate, act, settle:
 * - launch (the pad to Halcyon): venting on the pad; the gantry's arms swing back; ignition,
 *   the plume and smoke rolling out over the pad; lift-off slow, then accelerating; the
 *   camera follows up through two cloud layers into the dark and the stars; stage
 *   separation; the upper stage coasts up under Halcyon, its thrusters puff, a soft contact,
 *   the port's lamp turns green;
 * - return (Halcyon to the pad): undocking puffs; the upper stage falls tail first through
 *   the stars and the clouds; the retro-burn; its legs swing out; touchdown, the legs
 *   compress and settle while the exhaust rolls over the pad;
 * - descent (Halcyon to Lumen): the same with the lander; at the bottom its burn throws the
 *   regolith out in straight ballistic arcs that fall back at once (no air, no billowing),
 *   its hard black shadow sliding in to meet its feet;
 * - ascent (Lumen to Halcyon): ignition throws up the dust, lift-off, docking.
 */
export type Flight = 'launch' | 'return' | 'descent' | 'ascent';

/** Which flight a leg is: the rocket between the pad and Halcyon, the lander between
 *  Halcyon and Lumen; null for every other journey. */
export function flightOf(vehicle: string, to: string): Flight | null {
  if (vehicle === 'rocket') return to === 'space' ? 'launch' : 'return';
  if (vehicle === 'shuttle') return to === 'moon' ? 'descent' : 'ascent';
  return null;
}

export const onMoon = (f: Flight) => {
  'worklet';
  return f === 'descent' || f === 'ascent';
};
export const goingUp = (f: Flight) => {
  'worklet';
  return f === 'launch' || f === 'ascent';
};

/** The scene's layout (art px). The pad's numbers follow scripts/art/rocket.py's sprites. */
export const LAYOUT = {
  earth: {
    dock: 1900, // the port's contact line above the pad
    groundShow: 34, // how far below the pad the first frame reaches (above the hotbar)
    deck: 14, // the apron's top (the skyline's water meets it)
    mountTop: -1, // the launch table's top row (its surface is at y 0)
    boosterTop: -97, // the booster's picture top, standing on the table
    upperOnBooster: -159, // the upper stage's picture top while stacked (its skirt on the booster)
    upperLand: -75, // the upper stage's picture top standing on its deployed legs on the table
    upperLandDip: -71, // and with its legs compressed
    tower: 50, // the gantry's west edge
    arm0: -146, // the crew access arm's top (at the hatch)
    arm1: -64, // the umbilical arm's top
    cloudsLow: -760,
    cloudsHigh: -1110,
    sky: 14, // the sky column's foot
    starsFrom: -1330,
  },
  moon: {
    dock: 1000,
    groundShow: 30,
    horizon: -16, // the regolith's far edge
    padTop: -13,
    landerLand: -71, // the lander's picture top standing on its pad (legs out)
    landerDip: -68, // legs compressed
    landerSettle: -69,
    planet: [-82, -560] as const,
  },
} as const;

const smoother = (u: number) => {
  'worklet';
  const v = Math.min(1, Math.max(0, u));
  return v * v * v * (v * (v * 6 - 15) + 10);
};
const smootherSpeed = (u: number) => {
  'worklet';
  const v = Math.min(1, Math.max(0, u));
  return 30 * v * v * (v - 1) * (v - 1);
};

// the launch's beats (p)
export const LAUNCH = {
  armUmbilical: [0.1, 0.16] as const,
  armCrew: [0.14, 0.2] as const,
  ignite: 0.2,
  liftoff: 0.3,
  separation: 0.63,
  upperIgnite: 0.65,
  coast: 0.86,
  contact: 0.95,
  lampGreen: 0.965,
  rcs: [0.87, 0.92] as const,
};
// the way down's beats (the return and the moon descent)
export const LANDING = {
  undock: 0.05,
  rcs: [0.01, 0.035] as const,
  burn: [0.54, 0.86] as const,
  legsOut: [0.66, 0.72] as const,
  touchdown: 0.84,
  compress: 0.855,
  settle: 0.88,
};
// the moon ascent's beats
export const ASCENT = {
  ignite: 0.1,
  liftoff: 0.16,
  coast: 0.84,
  rcs: [0.87, 0.92] as const,
  contact: 0.95,
  lampGreen: 0.965,
};

/** How far the vehicle's reference (its picture's top) is above where it stands at the
 *  bottom of the flight, for each p: 0 on the ground, the full climb when docked. */
export function climb(f: Flight): number {
  'worklet';
  if (f === 'launch') return LAYOUT.earth.dock + LAYOUT.earth.upperOnBooster;
  if (f === 'return') return LAYOUT.earth.dock + LAYOUT.earth.upperLand;
  // (the ascent lifts off from its settled legs, the descent comes down onto outstretched ones)
  if (f === 'ascent') return LAYOUT.moon.dock + LAYOUT.moon.landerSettle;
  return LAYOUT.moon.dock + LAYOUT.moon.landerLand;
}

/** The altitude (px above the bottom of the flight) at p. */
export function altitude(f: Flight, p: number): number {
  'worklet';
  const A = climb(f);
  if (f === 'launch') return A * smoother((p - LAUNCH.liftoff) / (LAUNCH.contact - LAUNCH.liftoff));
  if (f === 'ascent') return A * smoother((p - ASCENT.liftoff) / (ASCENT.contact - ASCENT.liftoff));
  return A * (1 - smoother((p - LANDING.undock) / (LANDING.touchdown - LANDING.undock)));
}

/** The vehicle's picture top (world y) at p: the upper stage (launch, return) or the lander.
 *  A soft contact pushes 1 px past the port for a moment; touchdown dips onto the legs. */
export function vehicleTop(f: Flight, p: number): number {
  'worklet';
  const alt = Math.round(altitude(f, p));
  if (f === 'launch') {
    const push = p >= LAUNCH.contact && p < LAUNCH.lampGreen ? -1 : 0;
    return LAYOUT.earth.upperOnBooster - alt + push;
  }
  if (f === 'ascent') {
    const push = p >= ASCENT.contact && p < ASCENT.lampGreen ? -1 : 0;
    return LAYOUT.moon.landerSettle - alt + push;
  }
  const dip = p >= LANDING.compress;
  if (f === 'return') return (dip ? LAYOUT.earth.upperLandDip : LAYOUT.earth.upperLand) - alt;
  return (
    (p >= LANDING.settle
      ? LAYOUT.moon.landerSettle
      : dip
        ? LAYOUT.moon.landerDip
        : LAYOUT.moon.landerLand) - alt
  );
}

/** Which leg frame the vehicle shows: the upper stage 0 folded, 1 swinging out, 2 out,
 *  3 compressed; the lander 0 in flight, 1 touching, 2 compressed, 3 settled. */
export function legFrame(f: Flight, p: number): number {
  'worklet';
  if (f === 'launch') return 0;
  if (f === 'return') {
    if (p >= LANDING.compress) return 3;
    if (p >= LANDING.legsOut[1]) return 2;
    if (p >= LANDING.legsOut[0]) return 1;
    return 0;
  }
  if (f === 'ascent') return p < ASCENT.liftoff ? 3 : p < ASCENT.liftoff + 0.02 ? 1 : 0;
  if (p >= LANDING.settle) return 3;
  if (p >= LANDING.compress) return 2;
  if (p >= LANDING.touchdown) return 1;
  return 0;
}

/** The booster's picture top (world y) and its x, or null once it has fallen away. */
export function boosterAt(f: Flight, p: number): { x: number; y: number } | null {
  'worklet';
  if (f !== 'launch') return null;
  const base = LAYOUT.earth.boosterTop;
  if (p < LAUNCH.separation) return { x: 0, y: base - Math.round(altitude(f, p)) };
  const A = climb(f);
  const span = LAUNCH.contact - LAUNCH.liftoff;
  const u = (LAUNCH.separation - LAUNCH.liftoff) / span;
  const v = (A * smootherSpeed(u)) / span; // px per unit p at separation
  const d = p - LAUNCH.separation;
  const alt = A * smoother(u) + v * d * 0.45 - 9000 * d * d;
  return { x: -Math.round(d * 60), y: base - Math.round(alt) };
}

/** A flame's frame at p: -1 off, 0 and 1 igniting, 2 to 5 flickering at full. */
function flameFrame(p: number, on: number, off: number, ms: number): number {
  'worklet';
  if (p < on || p >= off) return -1;
  const age = (p - on) * ms;
  if (age < 60) return 0;
  if (age < 130) return 1;
  return 2 + (Math.floor(age / 55) % 4);
}

/** The engines burning at p: the booster's plume, the upper stage's or the lander's flame
 *  (each -1 when off). `ms` is the leg's length, so a flicker keeps its pace. */
export function flames(f: Flight, p: number, ms: number) {
  'worklet';
  if (f === 'launch')
    return {
      booster: flameFrame(p, LAUNCH.ignite, LAUNCH.separation, ms),
      upper: flameFrame(p, LAUNCH.upperIgnite, LAUNCH.coast, ms),
      lander: -1,
    };
  if (f === 'return')
    return { booster: -1, upper: flameFrame(p, LANDING.burn[0], LANDING.burn[1], ms), lander: -1 };
  if (f === 'descent')
    return { booster: -1, upper: -1, lander: flameFrame(p, LANDING.burn[0], LANDING.burn[1], ms) };
  return { booster: -1, upper: -1, lander: flameFrame(p, ASCENT.ignite, ASCENT.coast, ms) };
}

/** The gantry's arms: 0 attached .. 3 swung back (stowed for every flight but the launch's
 *  first beats). */
export function armFrames(f: Flight, p: number): [number, number] {
  'worklet';
  if (f !== 'launch') return [3, 3];
  const frame = (a: readonly [number, number]) =>
    p < a[0] ? 0 : p >= a[1] ? 3 : 1 + Math.floor(((p - a[0]) / (a[1] - a[0])) * 2.999);
  return [frame(LAUNCH.armCrew), frame(LAUNCH.armUmbilical)];
}

/** The ground shaking under ignition and lift-off: a whole art px to either side. */
export function shake(f: Flight, p: number): number {
  'worklet';
  if (f !== 'launch' || p < LAUNCH.ignite + 0.02 || p > LAUNCH.liftoff + 0.06) return 0;
  return Math.floor(p * 90) % 2 === 0 ? 1 : -1;
}

/** Thruster puffs: the times each fires (both sides at once), and its frame at p (-1 off). */
export function rcsFrame(f: Flight, p: number, ms: number): number {
  'worklet';
  const times = f === 'launch' ? LAUNCH.rcs : f === 'ascent' ? ASCENT.rcs : LANDING.rcs;
  for (const t of times) {
    const age = (p - t) * ms;
    if (age >= 0 && age < 180) return Math.min(2, Math.floor(age / 60));
  }
  return -1;
}

/** Whether the port's lamp is green: a vehicle is docked against it. */
export function docked(f: Flight, p: number): boolean {
  'worklet';
  if (f === 'launch') return p >= LAUNCH.lampGreen;
  if (f === 'ascent') return p >= ASCENT.lampGreen;
  return p < LANDING.undock;
}

/** The camera: the world y at the top of a screen `h` art px tall. It holds on the pad (or
 *  the ground) until the vehicle rises past a third of the screen, follows it, and holds on
 *  the station with the port 30 % down. Whole px, so every layer stays on the pixel grid. */
export function camera(f: Flight, p: number, h: number, top = 0, bottom = 0): number {
  'worklet';
  const moon = onMoon(f);
  const dock = moon ? LAYOUT.moon.dock : LAYOUT.earth.dock;
  const ground = moon ? LAYOUT.moon.groundShow : LAYOUT.earth.groundShow;
  // the part of the screen the HUD and the hotbar leave clear (art px from the top)
  const clear = Math.max(1, h - top - bottom);
  const atGround = ground - (h - bottom);
  const atDock = -dock - (top + Math.round(clear * 0.22));
  const follow = vehicleTop(f, p) - (top + Math.round(clear * 0.24));
  return Math.round(Math.min(atGround, Math.max(atDock, follow)));
}

// ---- smoke, steam and dust, decided once (deterministic) ------------------------------

/** A puff: born at `at`, lives `life` (p), from (x, y) rolling out by (dx, dy) as it grows
 *  through `grow` frames of its sheet, then breaks up and is gone. */
export type Puff = {
  kind: 'steam' | 'smoke' | 'fire';
  at: number;
  life: number;
  x: number;
  y: number;
  dx: number;
  dy: number;
  grow: number;
};
/** The frames of a puff sheet: growth 0..6, breaking up 7 and 8, gone 9. */
export const PUFF_GONE = 9;

const hash = (a: number, b: number) => {
  let h = (a * 374761393 + b * 668265263) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
};

/** Every puff of a flight (none on the airless moon). */
export function puffsFor(f: Flight): Puff[] {
  const out: Puff[] = [];
  if (onMoon(f)) return out;
  if (f === 'launch') {
    // venting: boil-off steam from the upper stage's valve and the cold tank, drifting east
    for (let i = 0; i < 7; i++)
      out.push({
        kind: 'steam',
        at: 0.005 + i * 0.03,
        life: 0.16,
        x: i % 2 ? 18 : -18,
        y: i % 2 ? -116 : -52,
        dx: (i % 2 ? 1 : -1) * (14 + hash(i, 1) * 12),
        dy: -10 - hash(i, 2) * 10,
        grow: 4,
      });
    // the plume hitting the trench: smoke rolling out over the apron both ways, lit by the
    // flame while it burns close, the last of it plain smoke
    for (let i = 0; i < 42; i++) {
      const side = i % 2 ? 1 : -1;
      const at = LAUNCH.ignite + 0.008 + i * 0.0085;
      out.push({
        kind: at < LAUNCH.liftoff + 0.04 ? 'fire' : 'smoke',
        at,
        life: 0.4 + hash(i, 3) * 0.16,
        x: side * (30 + hash(i, 4) * 10),
        y: 4 - hash(i, 5) * 10,
        dx: side * (34 + hash(i, 6) * 150),
        dy: -(2 + hash(i, 7) * 40),
        grow: 5 + Math.floor(hash(i, 8) * 1.99),
      });
    }
  } else {
    // the return: the retro plume on the table, rolling out once it reaches it, then steam
    for (let i = 0; i < 16; i++) {
      const side = i % 2 ? 1 : -1;
      out.push({
        kind: 'smoke',
        at: 0.74 + i * 0.008,
        life: 0.22,
        x: side * (26 + hash(i, 9) * 8),
        y: 4,
        dx: side * (60 + hash(i, 10) * 70),
        dy: -(4 + hash(i, 11) * 16),
        grow: 4 + Math.floor(hash(i, 12) * 2.99),
      });
    }
    for (let i = 0; i < 4; i++)
      out.push({
        kind: 'steam',
        at: 0.88 + i * 0.025,
        life: 0.1,
        x: (i % 2 ? 1 : -1) * 14,
        y: -40,
        dx: (i % 2 ? 1 : -1) * 10,
        dy: -12,
        grow: 3,
      });
  }
  return out;
}

/** Where a puff is at p and which frame it shows (PUFF_GONE before it is born and after). */
export function puffAt(q: Puff, p: number): { x: number; y: number; frame: number } {
  'worklet';
  const a = (p - q.at) / q.life;
  if (a < 0 || a >= 1) return { x: q.x, y: q.y, frame: PUFF_GONE };
  const ease = 1 - (1 - a) * (1 - a); // rolls out fast, then slows
  // grows quickly to its size, holds while it rolls, then breaks up
  const frame = a < 0.8 ? Math.min(q.grow, Math.floor((a / 0.3) * (q.grow + 1))) : a < 0.9 ? 7 : 8;
  return { x: Math.round(q.x + q.dx * ease), y: Math.round(q.y + q.dy * ease), frame };
}

/** A grain of regolith thrown by the lander's burn: born at `at` beside the nozzle, it flies
 *  a straight ballistic arc (`h` px high, `d` px out) for `life` and is gone when it lands. */
export type Grain = {
  at: number;
  life: number;
  x: number;
  d: number;
  h: number;
  tone: number;
  w: number;
};

/** The dust of a moon flight's burn (none on Earth). */
export function dustFor(f: Flight): Grain[] {
  if (!onMoon(f)) return [];
  const out: Grain[] = [];
  const [from, to] = f === 'descent' ? [0.74, 0.86] : [ASCENT.ignite + 0.01, ASCENT.liftoff + 0.1];
  // thrown low and fast, in straight arcs that come straight back down: most stay low
  // (a few px), some clear the horizon and show against the black sky
  for (let i = 0; i < 60; i++) {
    const side = i % 2 ? 1 : -1;
    const high = hash(i, 23);
    out.push({
      at: from + ((to - from) * i) / 60,
      life: 0.05 + hash(i, 20) * 0.08,
      x: side * (3 + Math.floor(hash(i, 21) * 8)),
      d: side * (26 + Math.floor(hash(i, 22) * 90)),
      h: high > 0.6 ? 14 + Math.floor((high - 0.6) * 45) : 3 + Math.floor(high * 14),
      tone: hash(i, 24) > 0.5 ? 5 : 4,
      w: hash(i, 25) > 0.55 ? 2 : 1,
    });
  }
  return out;
}

/** A grain's place at p (its arc: y = -4h a (1 - a), straight out in x), or null when it
 *  is not in the air. */
export function grainAt(g: Grain, p: number): { x: number; y: number } | null {
  'worklet';
  const a = (p - g.at) / g.life;
  if (a < 0 || a >= 1) return null;
  return { x: Math.round(g.x + g.d * a), y: Math.round(-4 * g.h * a * (1 - a)) };
}

/** The lander's shadow on the regolith: thrown down and to the right by the low sun, it
 *  slides in to meet the feet as the lander comes down; null when too high to fall on the
 *  pad's ground in view. */
export function shadowAt(f: Flight, p: number): { x: number } | null {
  'worklet';
  if (!onMoon(f)) return null;
  const alt = altitude(f, p);
  if (alt > 170) return null;
  return { x: Math.round(alt * 0.6) };
}
