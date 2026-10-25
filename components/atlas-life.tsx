import { useEffect } from 'react';
import { Image, View, type ImageSourcePropType } from 'react-native';
import Animated, {
  cancelAnimation,
  Easing,
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withTiming,
  type SharedValue,
} from 'react-native-reanimated';
import { zoneMaps, type ZoneId } from '@/lib/zone-maps';
import { residentRoutes, type Facing, type ResidentRoute } from '@/lib/resident-routes';
import { residentSprites } from '@/lib/resident-sprites';
import { residentFacingFrames, residentFrames } from '@/lib/resident-assets';

/**
 * Small things that move by themselves in a zone (world-atlas.md, "A world that
 * feels alive"): steam from chimneys, vents and the engine, embers over the forge
 * and the shrine, spores drifting off Lumen's shrubs, gulls over the harbour,
 * butterflies in the valley (fireflies at night), falling leaves, lizards in the
 * desert, a fish jumping now and then, rain over Neon Harbour and the Skyport. Presentation only. Everything
 * runs from one clock per zone, stops when the screen is inactive and is absent
 * with reduced motion. Where things appear follows the zone's own props, so the
 * life always belongs to what is drawn. (Codex's C21 schedule will later decide
 * which of these are out at each time of day and weather.)
 */
type Kind =
  | 'puff'
  | 'ember'
  | 'spore'
  | 'gull'
  | 'butterfly'
  | 'rain'
  | 'firefly'
  | 'lizard'
  | 'fish'
  | 'leaf'
  | 'flake'
  | 'twinkle';
type Emitter = { kind: Kind; x: number; y: number; seed: number };

// Each period divides the clock's 36 s loop, so no particle jumps when it wraps.
const PERIOD = {
  puff: 3600,
  ember: 1800,
  spore: 6000,
  gull: 9000,
  butterfly: 6000,
  rain: 720,
  firefly: 4000,
  lizard: 9000,
  fish: 12000,
  leaf: 7200,
  twinkle: 4500,
  flake: 9000,
} as const;

// Where a prop gives off something, relative to its top-left in zone pixels.
const SOURCES: Record<string, { kind: Kind; dx: number; dy: number }[]> = {
  workshop: [{ kind: 'puff', dx: 74, dy: 2 }],
  workshop_round: [{ kind: 'puff', dx: 58, dy: 2 }],
  locomotive: [{ kind: 'puff', dx: 28, dy: 0 }],
  steam_puff: [{ kind: 'puff', dx: 11, dy: 8 }],
  cooling_vent: [{ kind: 'puff', dx: 15, dy: 6 }],
  forge: [
    { kind: 'ember', dx: 75, dy: 0 },
    { kind: 'ember', dx: 30, dy: 44 },
  ],
  ember_shrine: [{ kind: 'ember', dx: 15, dy: 8 }],
  // the crack still glowing near a burnt snag's foot
  charred_snag: [{ kind: 'ember', dx: 14, dy: 27 }],
  // camp fires: the ridge's and the oasis caravan's
  campfire: [{ kind: 'ember', dx: 13, dy: 3 }],
  fire_pit: [{ kind: 'ember', dx: 10, dy: 5 }],
  moon_shrub: [
    { kind: 'spore', dx: 10, dy: 6 },
    { kind: 'spore', dx: 22, dy: 4 },
  ],
  cottage: [{ kind: 'puff', dx: 16, dy: 2 }],
  cottage_b: [{ kind: 'puff', dx: 16, dy: 2 }],
  water_mill: [{ kind: 'puff', dx: 92, dy: 60 }],
  narrowboat: [{ kind: 'puff', dx: 48, dy: 0 }],
  noodle_stall: [{ kind: 'puff', dx: 52, dy: 22 }],
  foundry: [
    { kind: 'puff', dx: 27, dy: 0 },
    { kind: 'puff', dx: 123, dy: 6 },
    { kind: 'ember', dx: 72, dy: 62 },
  ],
};

function rainOver(drops: number): Emitter[] {
  return Array.from({ length: drops }, (_, i) => ({
    kind: 'rain' as const,
    x: (i * 89 + (i >> 3) * 13) % 320,
    y: (i * 157) % 576,
    seed: i,
  }));
}

function snowfall(flakes: number, seed: number): Emitter[] {
  return Array.from({ length: flakes }, (_, i) => ({
    kind: 'flake' as const,
    x: (i * 97 + seed) % 300,
    y: (i * 131 + seed * 3) % 480,
    seed: seed + i,
  }));
}

// stars twinkling over Lumen's horizon (the sky above y = 60, clear of the planet)
const LUMEN_STARS: Emitter[] = Array.from({ length: 14 }, (_, i) => ({
  kind: 'twinkle' as const,
  x: 8 + ((i * 97) % 300),
  y: 4 + ((i * 37) % 50),
  seed: 70 + i,
})).filter((e) => Math.hypot(e.x - 230, e.y - 150) > 124);

const ZONE_EXTRAS: Partial<Record<ZoneId, Emitter[]>> = {
  lumen: LUMEN_STARS,
  // and in Halcyon's viewports, above the planet's rim
  station: Array.from({ length: 8 }, (_, i) => ({
    kind: 'twinkle' as const,
    x: 30 + ((i * 113) % 260),
    y: 16 + ((i * 29) % 26),
    seed: 90 + i,
  })),
  harbour: [
    { kind: 'fish', x: 200, y: 470, seed: 53 },
    { kind: 'gull', x: 120, y: 360, seed: 1 },
    { kind: 'gull', x: 230, y: 430, seed: 2 },
    { kind: 'gull', x: 60, y: 300, seed: 3 },
  ],
  // sparks lifting off the lava round Hearthold and along the Scorch's channel
  hearthold: [
    { kind: 'ember', x: 28, y: 216, seed: 13 },
    { kind: 'ember', x: 282, y: 300, seed: 14 },
    { kind: 'ember', x: 120, y: 410, seed: 15 },
    { kind: 'ember', x: 180, y: 76, seed: 16 },
  ],
  scorch: [
    { kind: 'ember', x: 72, y: 240, seed: 17 },
    { kind: 'ember', x: 116, y: 500, seed: 18 },
  ],
  // the Frostline: a few flakes always drifting on the high ground
  saddle: snowfall(12, 70),
  summit: snowfall(12, 80),
  snowmelt: snowfall(9, 90),
  // the waterfall's spray rising off the pool
  headwaters: [
    { kind: 'puff', x: 214, y: 158, seed: 23 },
    { kind: 'puff', x: 226, y: 164, seed: 24 },
  ],
  // the Tidebloom Isles: gulls over the cove, fish in the lagoon by the pier
  cove: [
    { kind: 'gull', x: 230, y: 470, seed: 19 },
    { kind: 'gull', x: 120, y: 520, seed: 20 },
  ],
  landing: [
    { kind: 'fish', x: 60, y: 500, seed: 21 },
    { kind: 'fish', x: 200, y: 500, seed: 22 },
  ],
  // gulls over the Headland's sea (the castle moved to the Ember Lands, 18 Oct)
  headland: [
    { kind: 'gull', x: 200, y: 520, seed: 4 },
    { kind: 'gull', x: 80, y: 548, seed: 12 },
  ],
  town: [
    { kind: 'butterfly', x: 270, y: 196, seed: 5 },
    { kind: 'butterfly', x: 210, y: 470, seed: 6 },
  ],
  park: [
    { kind: 'butterfly', x: 60, y: 120, seed: 7 },
    { kind: 'butterfly', x: 270, y: 380, seed: 8 },
  ],
  woodland: [
    { kind: 'butterfly', x: 110, y: 140, seed: 9 },
    { kind: 'butterfly', x: 150, y: 170, seed: 10 },
    { kind: 'leaf', x: 60, y: 120, seed: 50 },
    { kind: 'leaf', x: 240, y: 300, seed: 51 },
    { kind: 'leaf', x: 140, y: 420, seed: 52 },
  ],
  riverside: [
    { kind: 'butterfly', x: 120, y: 420, seed: 11 },
    { kind: 'fish', x: 150, y: 298, seed: 40 },
    { kind: 'fish', x: 100, y: 302, seed: 41 },
  ],
  oasis: [
    { kind: 'lizard', x: 230, y: 140, seed: 42 },
    { kind: 'lizard', x: 60, y: 420, seed: 43 },
    { kind: 'lizard', x: 270, y: 260, seed: 44 },
    { kind: 'fish', x: 100, y: 296, seed: 45 },
  ],
  gulch: [
    { kind: 'lizard', x: 200, y: 360, seed: 46 },
    { kind: 'lizard', x: 260, y: 470, seed: 47 },
  ],
  halt: [
    { kind: 'butterfly', x: 220, y: 400, seed: 48 },
    { kind: 'leaf', x: 250, y: 200, seed: 49 },
  ],
  // steam off the hot pools, and where the hot stream meets the dying lava
  springs: [
    { kind: 'puff', x: 236, y: 150, seed: 20 },
    { kind: 'puff', x: 220, y: 156, seed: 21 },
    { kind: 'puff', x: 192, y: 228, seed: 22 },
    { kind: 'puff', x: 148, y: 306, seed: 23 },
    { kind: 'puff', x: 104, y: 382, seed: 24 },
    { kind: 'puff', x: 90, y: 536, seed: 25 },
    { kind: 'puff', x: 84, y: 540, seed: 26 },
  ],
  neon: [
    ...rainOver(90),
    // steam from the grates in the pavement
    { kind: 'puff', x: 118, y: 336, seed: 30 },
    { kind: 'puff', x: 238, y: 300, seed: 31 },
    { kind: 'puff', x: 66, y: 440, seed: 32 },
  ],
  // the same rain carries on over the Skyport and the whole city (the weather does not
  // stop at a border), a little lighter inland
  skyport: rainOver(70),
  market: rainOver(80),
  downtown: rainOver(80),
  docks: rainOver(80),
  point: rainOver(70),
  heights: rainOver(60),
  plaza: rainOver(70),
  waterfront: rainOver(70),
};

/** What is out in a zone; at night the butterflies give way to fireflies. */
export function zoneEmitters(zone: ZoneId, night = false): Emitter[] {
  const out: Emitter[] = [];
  zoneMaps[zone].objects.forEach(([, sprite, x, y], i) => {
    for (const s of SOURCES[sprite] ?? [])
      for (let k = 0; k < 3; k++)
        out.push({ kind: s.kind, x: x + s.dx, y: y + s.dy, seed: i * 7 + k });
  });
  const extras = (ZONE_EXTRAS[zone] ?? []).map((e) =>
    night && e.kind === 'butterfly' ? { ...e, kind: 'firefly' as const } : e,
  );
  return [...out, ...extras];
}

function Particle({ e, clock, u }: { e: Emitter; clock: SharedValue<number>; u: number }) {
  const period = PERIOD[e.kind];
  const phase = (((e.seed * 0.37) % 1) + 1) % 1;
  const style = useAnimatedStyle(() => {
    // each particle runs its own loop of `period` ms off the shared clock (ms)
    const t = (((clock.value / period + phase) % 1) + 1) % 1;
    let dx = 0;
    let dy = 0;
    let opacity = 1;
    let scale = 1;
    if (e.kind === 'puff') {
      dx = Math.sin(t * 6.28) * 2 + t * 6;
      dy = -t * 22;
      opacity = t < 0.15 ? t / 0.15 : 1 - (t - 0.15) / 0.85;
      scale = 0.6 + t * 1.2;
    } else if (e.kind === 'ember') {
      dx = Math.sin(t * 12.6 + phase * 6) * 3;
      dy = -t * 26;
      opacity = 1 - t;
    } else if (e.kind === 'spore') {
      dx = Math.sin(t * 6.28 + phase * 6) * 6;
      dy = -t * 16;
      opacity = Math.sin(t * 3.14);
    } else if (e.kind === 'gull') {
      dx = Math.cos(t * 6.28) * 46;
      dy = Math.sin(t * 6.28) * 14;
      scale = Math.cos(t * 6.28) > 0 ? 1 : -1;
    } else if (e.kind === 'butterfly') {
      dx = Math.cos(t * 6.28) * 16 + Math.sin(t * 18.8) * 3;
      dy = Math.sin(t * 12.6) * 7;
      scale = Math.sin(t * 50) > 0 ? 1 : 0.4; // wing beat
    } else if (e.kind === 'firefly') {
      dx = Math.sin(t * 6.28 + phase * 6) * 14 + Math.sin(t * 18.8) * 3;
      dy = Math.cos(t * 6.28) * 8;
      opacity = Math.max(0, Math.sin(t * 25 + phase * 9)); // slow blinks
    } else if (e.kind === 'twinkle') {
      // a star brightening and fading once in its loop, still otherwise
      const w = Math.max(0, Math.sin(t * Math.PI * 2));
      opacity = w > 0.7 ? 1 : w > 0.35 ? 0.5 : 0;
    } else if (e.kind === 'lizard') {
      // a dash, a long still sunbathe, a dash back
      const run = t < 0.08 ? t / 0.08 : t < 0.5 ? 1 : t < 0.58 ? 1 - (t - 0.5) / 0.08 : 0;
      dx = run * 26;
      dy = run * 4;
      scale = t < 0.5 ? 1 : -1;
    } else if (e.kind === 'fish') {
      // still water most of the time, then one jump: an arc and a ring
      const j = (t - 0.8) / 0.2;
      opacity = t > 0.8 ? 1 : 0;
      dx = j * 10;
      dy = t > 0.8 ? -Math.sin(j * 3.14) * 9 : 0;
      scale = j > 0.85 ? 2 : 1;
    } else if (e.kind === 'flake') {
      // a snowflake drifting down, swaying, faded in and out
      dx = Math.sin(t * 12.6 + phase * 6) * 5 + t * 8;
      dy = t * 60;
      opacity = t < 0.15 ? t / 0.15 : t > 0.8 ? (1 - t) / 0.2 : 1;
    } else if (e.kind === 'leaf') {
      dx = Math.sin(t * 12.6) * 8 + t * 10;
      dy = t * 70;
      opacity = t < 0.1 ? t / 0.1 : t > 0.85 ? (1 - t) / 0.15 : 1;
    } else {
      dx = -t * 12;
      dy = t * 120;
      opacity = 0.7;
    }
    return {
      opacity,
      transform: [
        { translateX: Math.round((e.x + dx) * u) },
        { translateY: Math.round((e.y + dy) * u) },
        e.kind === 'gull' || e.kind === 'butterfly' || e.kind === 'lizard'
          ? { scaleX: scale }
          : { scale },
      ],
    };
  });
  const px = Math.max(1, Math.round(u));
  const box = (w: number, h: number, color: string) => ({
    position: 'absolute' as const,
    left: 0,
    top: 0,
    width: w * px,
    height: h * px,
    backgroundColor: color,
  });
  if (e.kind === 'puff')
    return (
      <Animated.View style={[{ position: 'absolute', left: 0, top: 0 }, style]}>
        <View style={{ ...box(6, 3, '#E2E8EE'), left: 0, top: px }} />
        <View style={{ ...box(4, 2, '#F4F7FA'), left: px, top: 0 }} />
        <View style={{ ...box(2, 1, '#FFFFFF'), left: px, top: 0 }} />
      </Animated.View>
    );
  if (e.kind === 'ember') return <Animated.View style={[box(1, 1, '#FFB648'), style]} />;
  if (e.kind === 'spore') return <Animated.View style={[box(1, 1, '#6FF2D2'), style]} />;
  if (e.kind === 'rain') return <Animated.View style={[box(1, 5, '#B8C8E8'), style]} />;
  if (e.kind === 'firefly') return <Animated.View style={[box(1, 1, '#E8FF8A'), style]} />;
  if (e.kind === 'twinkle') return <Animated.View style={[box(1, 1, '#FFFFFF'), style]} />;
  if (e.kind === 'leaf') return <Animated.View style={[box(2, 1, '#E07A28'), style]} />;
  if (e.kind === 'flake') return <Animated.View style={[box(1, 1, '#FFFFFF'), style]} />;
  if (e.kind === 'fish')
    return (
      <Animated.View style={[{ position: 'absolute', left: 0, top: 0 }, style]}>
        <View style={{ ...box(3, 1, '#C8D4DC'), left: 0, top: 0 }} />
        <View style={{ ...box(1, 1, '#8A9AA8'), left: 3 * px, top: px }} />
      </Animated.View>
    );
  if (e.kind === 'lizard')
    return (
      <Animated.View style={[{ position: 'absolute', left: 0, top: 0 }, style]}>
        <View style={{ ...box(4, 1, '#5A6A3A'), left: 0, top: 0 }} />
        <View style={{ ...box(2, 1, '#3E4A28'), left: 4 * px, top: px }} />
      </Animated.View>
    );
  if (e.kind === 'gull')
    return (
      <Animated.View style={[{ position: 'absolute', left: 0, top: 0 }, style]}>
        <View style={{ ...box(3, 1, '#F2F4F6'), left: 0, top: px }} />
        <View style={{ ...box(3, 1, '#F2F4F6'), left: 3 * px, top: 0 }} />
        <View style={{ ...box(1, 1, '#2A2D36'), left: 3 * px, top: px }} />
      </Animated.View>
    );
  return (
    <Animated.View style={[{ position: 'absolute', left: 0, top: 0 }, style]}>
      <View style={{ ...box(2, 2, '#F6C6D8'), left: 0, top: 0 }} />
      <View style={{ ...box(2, 2, '#E8A0BC'), left: 2 * px, top: 0 }} />
    </Animated.View>
  );
}

const RESIDENT_PERIOD = 18000; // divides the 36 s clock
const STEP_MS = 220; // one walking frame

/**
 * A resident on their route: a pause at one end, the walk across, a pause, the walk
 * back. Two frames swap while walking. Walking, they face the way they go (away up the
 * screen, toward the viewer down it, else to that side); paused, they face their work
 * (`route.face`). Still at the start of the route when the clock is not running
 * (reduced motion or an inactive screen).
 */
const FACINGS: readonly Facing[] = ['front', 'back', 'east', 'west'];
function legFacingOf(dx: number, dy: number): Facing {
  'worklet';
  if (Math.abs(dy) > Math.abs(dx)) return dy < 0 ? 'back' : 'front';
  return dx >= 0 ? 'east' : 'west';
}
function Resident({
  id,
  route,
  clock,
  u,
}: {
  id: string;
  route: ResidentRoute;
  clock: SharedValue<number>;
  u: number;
}) {
  const { w, h } = residentSprites[id];
  const sides = residentFacingFrames[id];
  const frames: Record<Facing, readonly ImageSourcePropType[]> = {
    front: residentFrames[id],
    back: sides?.back ?? residentFrames[id],
    east: sides?.east ?? residentFrames[id],
    west: sides?.west ?? residentFrames[id],
  };
  const [fx, fy] = route.from;
  const [tx, ty] = route.to;
  const [atFrom, atTo] = route.face ?? ['front', 'front'];
  const there = legFacingOf(tx - fx, ty - fy);
  const home = legFacingOf(fx - tx, fy - ty);
  const phase = (((id.length * 0.13) % 1) + 1) % 1;
  const place = useAnimatedStyle(() => {
    const t = (((clock.value / RESIDENT_PERIOD + phase) % 1) + 1) % 1;
    // 0-.1 pause, .1-.45 there, .45-.6 pause, .6-.95 back, .95-1 pause
    const k =
      t < 0.1 ? 0 : t < 0.45 ? (t - 0.1) / 0.35 : t < 0.6 ? 1 : t < 0.95 ? 1 - (t - 0.6) / 0.35 : 0;
    const x = fx + (tx - fx) * k;
    const y = fy + (ty - fy) * k;
    return {
      transform: [
        { translateX: Math.round((x - w / 2) * u) },
        { translateY: Math.round((y - h + 2) * u) },
      ],
    };
  });
  const box = { position: 'absolute' as const, left: 0, top: 0 };
  // (one layer per facing; only the one they face shows)
  return (
    <Animated.View
      style={[{ position: 'absolute', left: 0, top: 0, width: w * u, height: h * u }, place]}
    >
      {FACINGS.map((f) => (
        <FacingLayer
          key={f}
          facing={f}
          frames={frames[f]}
          clock={clock}
          phase={phase}
          faces={[atFrom, there, atTo, home]}
          w={w}
          h={h}
          u={u}
          box={box}
        />
      ))}
    </Animated.View>
  );
}

function FacingLayer({
  facing,
  frames,
  clock,
  phase,
  faces,
  w,
  h,
  u,
  box,
}: {
  facing: Facing;
  frames: readonly ImageSourcePropType[];
  clock: SharedValue<number>;
  phase: number;
  /** paused at the start, walking there, paused at the end, walking back */
  faces: readonly [Facing, Facing, Facing, Facing];
  w: number;
  h: number;
  u: number;
  box: { position: 'absolute'; left: number; top: number };
}) {
  const [f0, f1, f2, f3] = faces;
  const shown = useAnimatedStyle(() => {
    const t = (((clock.value / RESIDENT_PERIOD + phase) % 1) + 1) % 1;
    const now = t < 0.1 || t >= 0.95 ? f0 : t < 0.45 ? f1 : t < 0.6 ? f2 : f3;
    // a one-pixel bob on the passing step, so they walk rather than glide
    const walking = (t > 0.1 && t < 0.45) || (t > 0.6 && t < 0.95);
    const passing = walking && Math.floor(clock.value / STEP_MS) % 2 === 1;
    return {
      opacity: now === facing ? 1 : 0,
      transform: [{ translateY: passing ? -Math.round(u) : 0 }],
    };
  });
  const step = useAnimatedStyle(() => {
    const t = (((clock.value / RESIDENT_PERIOD + phase) % 1) + 1) % 1;
    const walking = (t > 0.1 && t < 0.45) || (t > 0.6 && t < 0.95);
    return { opacity: walking && Math.floor(clock.value / STEP_MS) % 2 === 1 ? 1 : 0 };
  });
  return (
    <Animated.View style={[{ ...box, width: w * u, height: h * u }, shown]}>
      <Image
        source={frames[0]}
        resizeMode="stretch"
        style={{ ...box, width: w * u, height: h * u }}
      />
      <Animated.View style={[{ ...box, width: w * u, height: h * u }, step]}>
        <Image
          source={frames[1]}
          resizeMode="stretch"
          style={{ ...box, width: w * u, height: h * u }}
        />
      </Animated.View>
    </Animated.View>
  );
}

/** The people who live in a zone (static where the life layer is off). */
export function ZoneResidents({
  zone,
  left,
  top,
  u,
  running,
}: {
  zone: ZoneId;
  left: number;
  top: number;
  u: number;
  running: boolean;
}) {
  const clock = useSharedValue(0);
  useEffect(() => {
    cancelAnimation(clock);
    clock.set(0);
    if (!running) return undefined;
    clock.set(withRepeat(withTiming(36000, { duration: 36000, easing: Easing.linear }), -1, false));
    return () => cancelAnimation(clock);
  }, [running, clock]);
  const here = Object.entries(residentRoutes).filter(([, r]) => r.zone === zone);
  if (here.length === 0) return null;
  return (
    <View
      style={{
        position: 'absolute',
        left,
        top,
        width: 320 * u,
        height: 576 * u,
        zIndex: 150000,
        pointerEvents: 'none',
      }}
    >
      {here.map(([id, route]) => (
        <Resident key={id} id={id} route={route} clock={clock} u={u} />
      ))}
    </View>
  );
}

/** The life over one zone, positioned at the zone's top-left (in CSS px). */
export function ZoneLife({
  zone,
  left,
  top,
  u,
  running,
  night = false,
}: {
  zone: ZoneId;
  left: number;
  top: number;
  u: number;
  running: boolean;
  night?: boolean;
}) {
  const clock = useSharedValue(0);
  useEffect(() => {
    if (!running) {
      cancelAnimation(clock);
      return undefined;
    }
    // a long linear clock in ms; each particle loops on its own period from it
    clock.set(0);
    clock.set(withRepeat(withTiming(36000, { duration: 36000, easing: Easing.linear }), -1, false));
    return () => cancelAnimation(clock);
  }, [running, clock]);
  if (!running) return null;
  return (
    <View
      style={{
        position: 'absolute',
        left,
        top,
        width: 320 * u,
        height: 576 * u,
        zIndex: 200000,
        pointerEvents: 'none',
      }}
    >
      {zoneEmitters(zone, night).map((e) => (
        <Particle key={`${e.kind}-${e.x}-${e.y}-${e.seed}`} e={e} clock={clock} u={u} />
      ))}
    </View>
  );
}
