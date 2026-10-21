import { useEffect, useState } from 'react';
import { Image, View } from 'react-native';
import Animated, {
  runOnJS,
  useAnimatedReaction,
  useAnimatedStyle,
  useSharedValue,
  type SharedValue,
} from 'react-native-reanimated';
import { folkSheets, type FolkSheet } from '@/lib/folk-sprites';

/**
 * The walker in the perfected 2x design (scripts/art/native/chars.py, sheets in
 * lib/folk-sprites.ts): Bramble with idle and walk cycles on the rig's timing, and the
 * familiar a step behind (docs/vision/cast.md: "it follows a step behind"). Shown in a zone
 * drawn at art density 2 (lib/zone-native.ts); elsewhere the walker stays as before. The design
 * draws S and E today, W as its flipped placeholder; a facing without a row (N) shows S.
 *
 * Motion: the frame advances on the rig's timing table only while the screen is active and
 * motion is not reduced (the idle breath and the walk cycle are finite loops on a timer that
 * stops with the screen); with reduced motion the first frame of each facing holds still. A
 * walk that is interrupted keeps the last facing and returns to idle.
 */
export type Facing4 = 'S' | 'N' | 'E' | 'W';

const FOLLOW = 13; // world px the familiar keeps behind the folk
// the contact shadow's rows: a stepped oval (width share of each half-px row)
const CONTACT_ROWS = [
  { id: 'top', k: 0.55, r: 0 },
  { id: 'upper', k: 1, r: 1 },
  { id: 'lower', k: 1, r: 2 },
  { id: 'bottom', k: 0.55, r: 3 },
];

/** The facing of a step (dx, dy): the axis it moves most along. */
export function facingOf(dx: number, dy: number, prev: Facing4): Facing4 {
  'worklet';
  if (Math.abs(dx) < 0.01 && Math.abs(dy) < 0.01) return prev;
  if (Math.abs(dx) >= Math.abs(dy) * 0.9) return dx > 0 ? 'E' : 'W';
  return dy > 0 ? 'S' : 'N';
}

function useFrame(sheet: FolkSheet, action: 'idle' | 'walk', running: boolean) {
  const [i, setI] = useState(0);
  const timing = sheet.timing[action];
  useEffect(() => {
    if (!running) return undefined;
    let n = 0;
    let t: ReturnType<typeof setTimeout>;
    const tick = () => {
      n = (n + 1) % timing.frames;
      setI(n);
      t = setTimeout(tick, timing.ms[n] ?? 120);
    };
    t = setTimeout(tick, timing.ms[0] ?? 120);
    return () => {
      clearTimeout(t);
      setI(0);
    };
  }, [running, timing]);
  return running ? i % timing.frames : 0;
}

/** One frame of a sheet, its foot at (0, 0) of the parent (world units times u). */
function Frame({
  sheet,
  facing,
  action,
  i,
  u,
}: {
  sheet: FolkSheet;
  facing: Facing4;
  action: 'idle' | 'walk';
  i: number;
  u: number;
}) {
  const [fw, fh] = sheet.frame;
  const [ax, ay] = sheet.foot;
  const own = sheet.rows.indexOf(`${facing}_${action}`);
  const row = Math.max(0, own >= 0 ? own : sheet.rows.indexOf(`S_${action}`));
  const cols = Math.max(...Object.values(sheet.timing).map((t) => t.frames));
  return (
    <View
      pointerEvents="none"
      style={{
        position: 'absolute',
        left: Math.round(-ax * u),
        top: Math.round(-ay * u),
        width: Math.round(fw * u),
        height: Math.round(fh * u),
        overflow: 'hidden',
      }}
    >
      <Image
        source={sheet.src}
        resizeMode="stretch"
        style={{
          position: 'absolute',
          left: Math.round(-i * fw * u),
          top: Math.round(-row * fh * u),
          width: Math.round(cols * fw * u),
          height: Math.round(sheet.rows.length * fh * u),
        }}
      />
    </View>
  );
}

/** A contact shadow under a walker's feet: a small dark oval, pixel-stepped. */
function Contact({ w, u }: { w: number; u: number }) {
  return (
    <View pointerEvents="none" style={{ position: 'absolute', left: 0, top: 0 }}>
      {CONTACT_ROWS.map(({ id, k, r }) => (
        <View
          key={id}
          style={{
            position: 'absolute',
            left: Math.round((-w * k * 0.5 + 0.5) * u),
            top: Math.round((r * 0.5 - 1) * u),
            width: Math.round(w * k * u),
            height: Math.max(1, Math.round(0.5 * u)),
            backgroundColor: 'rgba(33,26,34,0.32)',
          }}
        />
      ))}
    </View>
  );
}

/** The folk, drawn inside the walker's box (its feet at the box's foot point, 16 and 30 world
 *  px from its top-left, as the companion's). */
export function FolkWalker({
  px,
  py,
  u,
  walking,
  active,
  reduced,
  folk = 'bramble',
  ghost = false,
}: {
  px: SharedValue<number>;
  py: SharedValue<number>;
  u: number;
  walking: boolean;
  active: boolean;
  reduced: boolean;
  folk?: string;
  ghost?: boolean;
}) {
  const body = folkSheets[folk];
  const [facing, setFacing] = useState<Facing4>('S');
  const last = useSharedValue({ x: px.get(), y: py.get() });
  useAnimatedReaction(
    () => ({ x: px.value, y: py.value }),
    (p) => {
      const dx = p.x - last.value.x;
      const dy = p.y - last.value.y;
      if (Math.abs(dx) + Math.abs(dy) > 0.25) {
        runOnJS(setFacing)(facingOf(dx, dy, 'S'));
        last.set(p);
      }
    },
  );
  const action = walking ? 'walk' : 'idle';
  const i = useFrame(body, action, active && !reduced);
  if (!body) return null;
  return (
    <View pointerEvents="none" style={{ position: 'absolute', left: 16 * u, top: 30 * u }}>
      {!ghost && <Contact w={11} u={u} />}
      <Frame sheet={body} facing={facing} action={action} i={i} u={u} />
    </View>
  );
}

/** The familiar a step behind: FOLLOW world px back along the way the folk came, its own
 *  facing from its own steps, sorted by its feet among the scene's things (region units, as
 *  the walker's box: feet at (px + ox, py + oy)). */
export function FolkFamiliar({
  px,
  py,
  ox = 0,
  oy = 0,
  u,
  walking,
  active,
  reduced,
  familiar = 'mossling',
}: {
  px: SharedValue<number>;
  py: SharedValue<number>;
  ox?: number;
  oy?: number;
  u: number;
  walking: boolean;
  active: boolean;
  reduced: boolean;
  familiar?: string;
}) {
  const pet = folkSheets[familiar];
  const [facing, setFacing] = useState<Facing4>('S');
  const fx = useSharedValue(px.get() + ox - FOLLOW * 0.7);
  const fy = useSharedValue(py.get() + oy - FOLLOW * 0.7);
  useAnimatedReaction(
    () => ({ x: px.value + ox, y: py.value + oy }),
    (p) => {
      const ex = p.x - fx.value;
      const ey = p.y - fy.value;
      const d = Math.hypot(ex, ey);
      if (d > FOLLOW) {
        const k = (d - FOLLOW) / d;
        fx.set(fx.value + ex * k);
        fy.set(fy.value + ey * k);
        runOnJS(setFacing)(facingOf(ex, ey, 'S'));
      }
    },
  );
  const style = useAnimatedStyle(() => ({
    transform: [{ translateX: Math.round(fx.value * u) }, { translateY: Math.round(fy.value * u) }],
    zIndex: Math.round(fy.value),
  }));
  const action = walking ? 'walk' : 'idle';
  const j = useFrame(pet, action, active && !reduced);
  if (!pet) return null;
  return (
    <Animated.View pointerEvents="none" style={[{ position: 'absolute', left: 0, top: 0 }, style]}>
      <Contact w={8} u={u} />
      <Frame sheet={pet} facing={facing} action={action} i={j} u={u} />
    </Animated.View>
  );
}
