import { useEffect } from 'react';
import { View } from 'react-native';
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

/**
 * Small things that move by themselves in a zone (world-atlas.md, "A world that
 * feels alive"): steam from chimneys, vents and the engine, embers over the forge
 * and the shrine, spores drifting off Lumen's shrubs, gulls over the harbour,
 * butterflies in the valley, rain over Neon Harbour and the Skyport. Presentation only. Everything
 * runs from one clock per zone, stops when the screen is inactive and is absent
 * with reduced motion. Where things appear follows the zone's own props, so the
 * life always belongs to what is drawn. (Codex's C21 schedule will later decide
 * which of these are out at each time of day and weather.)
 */
type Kind = 'puff' | 'ember' | 'spore' | 'gull' | 'butterfly' | 'rain';
type Emitter = { kind: Kind; x: number; y: number; seed: number };

// Each period divides the clock's 36 s loop, so no particle jumps when it wraps.
const PERIOD = {
  puff: 3600,
  ember: 1800,
  spore: 6000,
  gull: 9000,
  butterfly: 6000,
  rain: 720,
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
  moon_shrub: [
    { kind: 'spore', dx: 10, dy: 6 },
    { kind: 'spore', dx: 22, dy: 4 },
  ],
  cottage: [{ kind: 'puff', dx: 16, dy: 2 }],
  cottage_b: [{ kind: 'puff', dx: 16, dy: 2 }],
  water_mill: [{ kind: 'puff', dx: 92, dy: 60 }],
};

function rainOver(drops: number): Emitter[] {
  return Array.from({ length: drops }, (_, i) => ({
    kind: 'rain' as const,
    x: (i * 89 + (i >> 3) * 13) % 320,
    y: (i * 157) % 576,
    seed: i,
  }));
}

const ZONE_EXTRAS: Partial<Record<ZoneId, Emitter[]>> = {
  harbour: [
    { kind: 'gull', x: 120, y: 360, seed: 1 },
    { kind: 'gull', x: 230, y: 430, seed: 2 },
    { kind: 'gull', x: 60, y: 300, seed: 3 },
  ],
  castle: [{ kind: 'gull', x: 200, y: 520, seed: 4 }],
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
  ],
  riverside: [{ kind: 'butterfly', x: 120, y: 420, seed: 11 }],
  neon: rainOver(90),
  // the same rain carries on over the Skyport (the weather does not stop at a border)
  skyport: rainOver(70),
};

export function zoneEmitters(zone: ZoneId): Emitter[] {
  const out: Emitter[] = [];
  zoneMaps[zone].objects.forEach(([, sprite, x, y], i) => {
    for (const s of SOURCES[sprite] ?? [])
      for (let k = 0; k < 3; k++)
        out.push({ kind: s.kind, x: x + s.dx, y: y + s.dy, seed: i * 7 + k });
  });
  return [...out, ...(ZONE_EXTRAS[zone] ?? [])];
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
        e.kind === 'gull'
          ? { scaleX: scale }
          : e.kind === 'butterfly'
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

/** The life over one zone, positioned at the zone's top-left (in CSS px). */
export function ZoneLife({
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
      pointerEvents="none"
      style={{ position: 'absolute', left, top, width: 320 * u, height: 576 * u, zIndex: 200000 }}
    >
      {zoneEmitters(zone).map((e) => (
        <Particle key={`${e.kind}-${e.x}-${e.y}-${e.seed}`} e={e} clock={clock} u={u} />
      ))}
    </View>
  );
}
