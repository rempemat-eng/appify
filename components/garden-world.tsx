import { Fragment, useEffect, useLayoutEffect, useRef, useState } from 'react';
import {
  AccessibilityInfo,
  Image,
  PixelRatio,
  Platform,
  Pressable,
  View,
  useWindowDimensions,
  type ImageSourcePropType,
} from 'react-native';
import Animated, {
  cancelAnimation,
  runOnJS,
  useAnimatedStyle,
  useSharedValue,
  withSequence,
  withTiming,
  Easing,
} from 'react-native-reanimated';
import { router } from 'expo-router';
import * as Haptics from 'expo-haptics';
import { cozy as c } from '@/lib/cozy';
import { useReducedMotion } from '@/lib/motion';
import { useAppActive } from '@/lib/app-active';
import { playSound } from '@/lib/sound';
import type { BreakIntention, CompanionMemory } from '@/lib/companion-memories';
import { gardenKeepsakes, gardenResponse, gardenSignature } from '@/lib/garden-life';
import { playPaused, useGame, type Player } from '@/lib/game';
import { collectionOf, guardianPlayer, visitorInfo } from '@/lib/visitors';
import {
  GARDEN,
  gardenAnchors,
  gardenHotspots,
  gardenWater,
  gardenObjects,
  gardenOrchard,
  gardenPlots,
  growthSpriteSizes,
} from '@/lib/garden-map';
import { growthImages } from '@/lib/garden-growth-assets';
import { meadowLine, orchardStage, plotStage } from '@/lib/garden-growth';
import {
  GARDEN_START,
  HUT_DOOR,
  atGardenExit,
  findPath,
  gardenExitToward,
  nearestWalkable,
  randomSpot,
  toCell,
  toPoint,
  walkable,
  type GardenExit,
  type Point,
} from '@/lib/garden-path';
import { STEP_MS, keySteps, useKeyboardWalk } from '@/lib/keyboard-walk';
import { useUi } from '@/lib/ui';
import {
  TILT_DEG,
  billboard,
  groundRect,
  lift,
  makeProjection,
  project,
  unproject,
  type ViewMode,
} from '@/lib/garden-projection';
import { GuardianPet } from '@/components/guardian-pet';
import { FloatingZ, Pet } from '@/components/game-ui';
import { BodyText } from '@/components/pixel-feedback';
import { GardenReactions, type GardenReaction, type Place } from '@/components/garden-reactions';
import { GardenKeepsakeArt } from '@/components/garden-keepsakes';
import { FrameShape, PixelTail, frameTones } from '@/components/pixel-frame';
import { contentInset, type } from '@/lib/ui-tokens';
import { pixelScale, snapToDevice } from '@/lib/pixel-scale';

import groundImg from '@/assets/garden/ground.png';
import stream0 from '@/assets/garden/water-stream-0.png';
import stream1 from '@/assets/garden/water-stream-1.png';
import stream2 from '@/assets/garden/water-stream-2.png';
import stream3 from '@/assets/garden/water-stream-3.png';
import pond0 from '@/assets/garden/water-pond-0.png';
import pond1 from '@/assets/garden/water-pond-1.png';
import pond2 from '@/assets/garden/water-pond-2.png';
import pond3 from '@/assets/garden/water-pond-3.png';
import treeImg from '@/assets/garden/tree.png';
import treeSmallImg from '@/assets/garden/tree_small.png';
import treeAutumnImg from '@/assets/garden/tree_autumn.png';
import pineImg from '@/assets/garden/pine.png';
import hutImg from '@/assets/garden/hut.png';
import lightLanternPool from '@/assets/garden/light-lantern-pool.png';
import lightLanternHalo from '@/assets/garden/light-lantern-halo.png';
import lightHutPool from '@/assets/garden/light-hut-pool.png';
import lightHutWindowL from '@/assets/garden/light-hut-window-l.png';
import lightHutWindowR from '@/assets/garden/light-hut-window-r.png';
import lightStallGlow from '@/assets/garden/light-stall-glow.png';
import lightStallPool from '@/assets/garden/light-stall-pool.png';
import bedImg from '@/assets/garden/bed.png';
import mailboxImg from '@/assets/garden/mailbox.png';
import stallImg from '@/assets/garden/stall.png';
import signpostImg from '@/assets/garden/signpost.png';
import bowlImg from '@/assets/garden/bowl.png';
import bushImg from '@/assets/garden/bush.png';
import rock0Img from '@/assets/garden/rock0.png';
import rock1Img from '@/assets/garden/rock1.png';
import fenceLImg from '@/assets/garden/fence_l.png';
import fenceRImg from '@/assets/garden/fence_r.png';
import gateImg from '@/assets/garden/gate.png';
import readingNookImg from '@/assets/garden/reading_nook.png';
import wateringCanImg from '@/assets/garden/watering_can.png';
import lanternImg from '@/assets/garden/lantern.png';
import meadowSignImg from '@/assets/garden/meadow_sign.png';
import groundTop from '@/assets/garden/ground-top.png';
import townTop from '@/assets/zones/town/top.png';

const sprites: Record<string, ImageSourcePropType> = {
  tree: treeImg,
  tree_small: treeSmallImg,
  tree_autumn: treeAutumnImg,
  pine: pineImg,
  hut: hutImg,
  bed: bedImg,
  mailbox: mailboxImg,
  stall: stallImg,
  signpost: signpostImg,
  bowl: bowlImg,
  bush: bushImg,
  rock0: rock0Img,
  rock1: rock1Img,
  fence_l: fenceLImg,
  fence_r: fenceRImg,
  gate: gateImg,
  reading_nook: readingNookImg,
  watering_can: wateringCanImg,
  lantern: lanternImg,
  meadow_sign: meadowSignImg,
};
const growthSize = (key: string): readonly [number, number] =>
  (growthSpriteSizes as Record<string, readonly [number, number]>)[key] ?? [16, 16];

type Action = keyof typeof gardenHotspots;

// Wall clock for 'player touched recently' checks (only ever called from handlers).
const clock = () => Date.now();
const SPEED = 34; // native pixels per second, a gentle stroll
const KEY_SPEED = 52; // walking by the keys: a purposeful trot, so crossing the garden is quick
const START: Point = GARDEN_START;
const BED: Point = gardenAnchors.bed;
// One still ground image; only the water moves, as small four-frame overlays.
const waterFrames: Record<(typeof gardenWater)[number]['id'], ImageSourcePropType[]> = {
  stream: [stream0, stream1, stream2, stream3],
  pond: [pond0, pond1, pond2, pond3],
};
// Night light (coherence plan, 6c): warm pools from the lantern, the hut's windows and
// the stall, in stepped pixel bands, laid over the night tint (scripts/art/garden.py).
const lightImages: Record<string, ImageSourcePropType> = {
  'lantern-pool': lightLanternPool,
  'lantern-halo': lightLanternHalo,
  'hut-pool': lightHutPool,
  'hut-window-l': lightHutWindowL,
  'hut-window-r': lightHutWindowR,
  'stall-glow': lightStallGlow,
  'stall-pool': lightStallPool,
};
const WATER_FRAMES = 4;
// Near the top of the clearing a speech bubble opens below the companion instead.
const TOP_FLIP = 80;

// Ground line (feet) of a generated object, for effects that float above it.
function footOf(id: string, fallback: number) {
  const o = gardenObjects.find((g) => g.id === id);
  return o ? o.y + o.h : fallback;
}
const HUT_FOOT = footOf('hut', 76);
const NOOK_FOOT = footOf('reading-nook', 64);
const LANTERN_FOOT = footOf('lantern', 88);

// Ground line for reaction effects that float above a prop (pixels in sprite space).
function reactionBase(r: GardenReaction): number | undefined {
  if (r.kind === 'read') return NOOK_FOOT;
  if (r.kind === 'lantern') return LANTERN_FOOT;
  if (r.kind === 'pat') return r.y; // the companion's feet
  return undefined; // water drops and pond ripples sit on the ground
}

const companionSpots: readonly Point[] = gardenAnchors.companionSpots;

const noMemories: readonly CompanionMemory[] = [];
const keepsakeIntentions: readonly BreakIntention[] = ['rest', 'read', 'move', 'create'];
// Keepsakes sit on the edges of existing places, leaving the clearing and
// existing touch targets intact. All four use a 16-pixel native art frame.
const keepsakeLocations: Record<BreakIntention, Point> = gardenAnchors.keepsakes;

// ---- crisp sprite --------------------------------------------------------
function Sprite({
  source,
  rect,
  z,
}: {
  source: ImageSourcePropType;
  rect: { left: number; top: number; width: number; height: number };
  z: number;
}) {
  return (
    <Image
      source={source}
      resizeMode="stretch"
      style={{
        position: 'absolute',
        left: rect.left,
        top: rect.top,
        width: rect.width,
        height: rect.height,
        zIndex: z,
      }}
    />
  );
}

// ---- ambient life (own clock, so only this layer re-renders) --------------
function Ambient({
  scale,
  place,
  width,
  height,
  rain,
  night,
  day,
  reduced,
  active,
}: {
  scale: number;
  place: Place;
  width: number;
  height: number;
  rain: boolean;
  night: boolean;
  day: boolean;
  reduced: boolean;
  active: boolean;
}) {
  const [t, setT] = useState(0);
  useEffect(() => {
    if (reduced || !active) return undefined;
    const timer = setInterval(() => setT((v) => v + 1), 110);
    return () => clearInterval(timer);
  }, [reduced, active]);
  const u = Math.max(1, Math.round(scale)); // one art pixel on screen
  const drops = rain
    ? Array.from({ length: 34 }, (_, i) => {
        const x = (i * 53 + Math.floor(i / 3) * 17) % GARDEN.width;
        const y = ((i * 41 + t * 7) % (GARDEN.height + 20)) - 10;
        return { x, y, i };
      })
    : [];
  const flies = night
    ? Array.from({ length: 7 }, (_, i) => ({
        id: `firefly-${i}`,
        x:
          gardenAnchors.fireflies.x +
          ((i * 47) % gardenAnchors.fireflies.w) +
          Math.sin(t / 14 + i) * 8,
        y:
          gardenAnchors.fireflies.y +
          ((i * 29) % gardenAnchors.fireflies.h) +
          Math.cos(t / 17 + i * 2) * 6,
        // A slow glow has no abrupt on/off frame or rapid flashing.
        opacity: 0.2 + ((Math.sin((t + i * 7) / 6) + 1) / 2) * 0.7,
      }))
    : [];
  const butterflies = day
    ? [0, 1].map((i) => ({
        x: gardenAnchors.butterflies.x + Math.cos(t / 18 + i * 3) * (16 + i * 6),
        y: gardenAnchors.butterflies.y + Math.sin(t / 11 + i * 2) * 9 - 6,
        flap: (t + i * 2) % 6 < 3,
        color: i ? '#F2D16B' : '#CFC4EC',
      }))
    : [];
  // Two small puffs share this layer's clock, rise once and dissolve. A long
  // quiet gap keeps the chimney from becoming a constant stream of particles.
  const smoke =
    !reduced && active
      ? [0, 10]
          .map((delay) => {
            const age = (t + 72 - delay) % 72;
            return {
              id: `smoke-${delay}`,
              age,
              x: gardenAnchors.chimney.x + Math.floor(age / 6),
              y: gardenAnchors.chimney.y - Math.floor(age / 2),
              opacity: Math.min(0.25, age / 12, Math.max(0, (22 - age) / 32)),
            };
          })
          .filter((puff) => puff.age < 22)
      : [];
  return (
    <View
      pointerEvents="none"
      style={{ position: 'absolute', left: 0, top: 0, width, height, zIndex: 950 }}
    >
      {drops.map((d) => {
        const q = place(d.x, d.y);
        return (
          <View
            key={d.i}
            style={{
              position: 'absolute',
              left: Math.round(q.sx),
              top: Math.round(q.sy),
              width: u,
              height: Math.round(u * 4 * q.f),
              backgroundColor: 'rgba(214,232,244,0.75)',
            }}
          />
        );
      })}
      {flies.map((f) => (
        <View
          key={f.id}
          style={{
            position: 'absolute',
            left: Math.round(place(f.x, f.y, f.y + 8).sx) - u,
            top: Math.round(place(f.x, f.y, f.y + 8).sy) - u,
            width: u * 3,
            height: u * 3,
            backgroundColor: 'rgba(246,231,140,0.28)',
            opacity: f.opacity,
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <View style={{ width: u, height: u, backgroundColor: '#FFF4B0' }} />
        </View>
      ))}
      {butterflies.map((b) => (
        <View
          key={b.color}
          style={{
            position: 'absolute',
            left: Math.round(place(b.x, b.y, b.y + 6).sx),
            top: Math.round(place(b.x, b.y, b.y + 6).sy),
            flexDirection: 'row',
            alignItems: 'center',
          }}
        >
          <View style={{ width: u * 2, height: b.flap ? u * 3 : u, backgroundColor: b.color }} />
          <View style={{ width: u, height: u * 2, backgroundColor: '#2A2421' }} />
          <View style={{ width: u * 2, height: b.flap ? u * 3 : u, backgroundColor: b.color }} />
        </View>
      ))}
      {smoke.map((puff) => (
        <View
          key={puff.id}
          style={{
            position: 'absolute',
            left: Math.round(place(puff.x, puff.y, HUT_FOOT).sx),
            top: Math.round(place(puff.x, puff.y, HUT_FOOT).sy),
            width: Math.round(4 * scale),
            height: Math.round(3 * scale),
            opacity: puff.opacity,
          }}
        >
          <View
            style={{
              position: 'absolute',
              left: Math.round(scale),
              width: Math.round(2 * scale),
              height: Math.round(3 * scale),
              backgroundColor: '#D3D8C9',
            }}
          />
          <View
            style={{
              position: 'absolute',
              top: Math.round(scale),
              width: Math.round(4 * scale),
              height: Math.round(scale),
              backgroundColor: '#D3D8C9',
            }}
          />
        </View>
      ))}
    </View>
  );
}

// ---- guidance marker -------------------------------------------------------
// A small "!" sign above the place the garden suggests next. It never blocks
// taps: the object underneath stays the thing to press.
function GardenMarker({ action, scale, bob }: { action: Action; scale: number; bob: boolean }) {
  const o = gardenObjects.find((g) => g.action === action);
  const spot = o ? { x: o.x + o.w / 2, y: o.y } : gardenHotspots[action];
  const u = Math.max(2, Math.round(scale));
  const w = 7 * u;
  return (
    <View
      pointerEvents="none"
      aria-hidden
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      style={{
        position: 'absolute',
        left: Math.round(spot.x * scale - w / 2),
        top: Math.round(spot.y * scale - 11 * u - (bob ? u : 0)),
        width: w,
        height: 9 * u,
        zIndex: 960,
        alignItems: 'center',
      }}
    >
      <FrameShape tone={frameTones.gold} unit={u} />
      <BodyText
        style={{
          fontFamily: 'PixelifySans_700Bold',
          fontSize: 6 * u,
          lineHeight: 9 * u,
          color: '#3B2A14',
        }}
      >
        !
      </BodyText>
    </View>
  );
}

// ---- the world -----------------------------------------------------------
export function GardenWorld({
  width,
  player,
  grumpy,
  sleepy,
  onFeed,
  onNap,
  napping = false,
  active: screenActive = true,
  view = 'flat',
  memories = noMemories,
  viewportHeight,
  marker = null,
  onKeepsakePress,
  say = null,
  padBottom = 0,
  arrival = null,
}: {
  width: number;
  player: Player;
  grumpy: boolean;
  sleepy: boolean;
  onFeed?: () => void;
  /** Home can attach its optional break idea to the existing nap action. */
  onNap?: () => void;
  /** Night garden for the nap screen: pet asleep in its bed, no interaction. */
  napping?: boolean;
  /** Tab screens stay mounted; pause the world and cancel its actions on blur. */
  active?: boolean;
  /** 'flat' top-down, or 'tilt' 2.5D: tilted ground with upright billboard sprites. */
  view?: ViewMode;
  /** Explicitly kept memories only; this scene never creates or settles them. */
  memories?: readonly CompanionMemory[];
  /**
   * Show the world through a window of this height. A camera follows the
   * companion and reveals the forest above the clearing; without it the whole
   * map is laid out at its natural height.
   */
  viewportHeight?: number;
  /** A gentle "!" above the place the garden suggests visiting next. */
  marker?: Action | null;
  /** Kept keepsakes become tappable when the screen can open them. */
  onKeepsakePress?: (memory: CompanionMemory) => void;
  /** Something the companion says, shown in a bubble that follows it. */
  say?: { text: string; onPress?: () => void; hint?: string } | null;
  /** Screen height covered at the bottom (the hotbar): the camera keeps the gate above it. */
  padBottom?: number;
  /** Walked in from the valley: stand here (garden pixels); a new key moves it again. */
  arrival?: { x: number; y: number; key: string } | null;
}) {
  const reduced = useReducedMotion();
  const appActive = useAppActive();
  const active = screenActive && appActive;
  // One art pixel is the game's shared pixel (coherence plan, step 6): the map is
  // wider than a phone and the camera follows the companion across it.
  const screen = useWindowDimensions();
  const dpr = PixelRatio.get();
  const scale = pixelScale(screen.width, dpr);
  // Art is placed on whole device pixels, so every art pixel stays crisp.
  const snap = (value: number) => snapToDevice(value, dpr);
  const snapRect = (r: { left: number; top: number; width: number; height: number }) => ({
    left: snap(r.left),
    top: snap(r.top),
    width: snap(r.width),
    height: snap(r.height),
  });
  const worldWidth = Math.round(GARDEN.width * scale);
  // All placement goes through one projection (identity in flat view).
  const tilt = view === 'tilt';
  const proj = makeProjection(view, worldWidth, GARDEN, tilt ? Math.round(worldWidth * 0.14) : 0);
  // How far the map overhangs the window; negative centres a narrower map.
  const spare = worldWidth - width;
  /** The window's left edge in world pixels when it follows a point at screen x. */
  const windowLeft = (sx: number) => {
    'worklet';
    return spare > 0 ? Math.min(spare, Math.max(0, sx - width / 2)) : spare / 2;
  };
  const height = proj.height;
  const place: Place = (x, y, groundY = y) => lift(proj, x, y, groundY);
  const camera = !tilt && viewportHeight !== undefined;
  const topBand = Math.round(GARDEN.top * scale);
  const viewHeight = camera ? viewportHeight : height;
  // the part of the window not under the hotbar: the camera can always bring the
  // fence and its gate up above it
  const seenHeight = Math.max(1, viewHeight - (camera ? padBottom : 0));
  const cameraMin = camera ? -topBand : 0;
  const cameraMax = camera ? Math.max(cameraMin, height - seenHeight) : 0;
  const lifetimeMinutes = player.offline_seconds;
  // Characters are drawn on the same grid as the world: 32 art pixels.
  const petPx = 32 * scale;
  const companionPx = 32 * scale;
  const home = napping ? BED : START;
  const px = useSharedValue(home.x);
  const py = useSharedValue(home.y);
  const pos = useRef<Point>({ ...home });
  const hour = new Date(useGame((s) => s.now)).getHours();
  const night = napping || hour < 6 || hour >= 21;
  const dusk = !night && hour >= 17;
  const dawn = !night && hour < 9;
  const [walking, setWalking] = useState(false);
  const [facing, setFacing] = useState<'left' | 'right'>('right');
  const [frame, setFrame] = useState(0);
  const [tag, setTag] = useState<{ text: string; x: number; y: number } | null>(null);
  const [emote, setEmote] = useState<string | null>(null);
  const [destination, setDestination] = useState<Point | null>(null);
  const [reaction, setReaction] = useState<GardenReaction | null>(null);
  const [feedback, setFeedback] = useState<{
    id: number;
    kind: GardenReaction['kind'];
    text: string;
    x: number;
    y: number;
  } | null>(null);
  const [lanternOverride, setLanternOverride] = useState<boolean | null>(null);
  const lanternOn = napping || (lanternOverride ?? night);
  const responseCount = useRef({ pond: 0, read: 0, water: 0, pat: 0, lantern: 0 });
  const reactionId = useRef(0);
  const [wasActive, setWasActive] = useState(active);
  if (wasActive !== active) {
    setWasActive(active);
    if (!active) {
      setWalking(false);
      setTag(null);
      setEmote(null);
      setDestination(null);
      setReaction(null);
      setFeedback(null);
    }
  }
  const busy = useRef(false);
  // walking out once: a held key's repeats must not open the valley twice as it opens
  const leaving = useRef(false);
  const activeRef = useRef(active);
  const lastTouch = useRef(0);
  const journeyId = useRef(0);
  const journey = useRef<{
    id: number;
    action: Action | null;
    end: Point;
    exit: GardenExit | 'door' | null;
  } | null>(null);
  const napTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useLayoutEffect(() => {
    activeRef.current = active;
    if (active) {
      leaving.current = false;
      return;
    }
    journeyId.current += 1;
    journey.current = null;
    cancelAnimation(px);
    cancelAnimation(py);
    pos.current = { x: px.get(), y: py.get() };
    busy.current = false;
    if (napTimer.current) clearTimeout(napTimer.current);
    napTimer.current = null;
  }, [active, px, py]);

  useEffect(
    () => () => {
      activeRef.current = false;
      journeyId.current += 1;
      journey.current = null;
      cancelAnimation(px);
      cancelAnimation(py);
      if (napTimer.current) clearTimeout(napTimer.current);
    },
    [px, py],
  );

  // Water has four calm phases; the grass is still.
  useEffect(() => {
    if (reduced || !active) return undefined;
    const t = setInterval(() => setFrame((f) => (f + 1) % WATER_FRAMES), 400);
    return () => clearInterval(t);
  }, [reduced, active]);

  useEffect(() => {
    if (!tag || !active) return undefined;
    const t = setTimeout(() => setTag(null), 1800);
    return () => clearTimeout(t);
  }, [tag, active]);
  useEffect(() => {
    if (!emote || !active) return undefined;
    const t = setTimeout(() => setEmote(null), 1400);
    return () => clearTimeout(t);
  }, [emote, active]);
  useEffect(() => {
    if (!reaction || !active) return undefined;
    const timer = setTimeout(
      () => setReaction((current) => (current?.id === reaction.id ? null : current)),
      4600,
    );
    return () => clearTimeout(timer);
  }, [reaction, active]);
  useEffect(() => {
    if (!feedback || !active) return undefined;
    if (Platform.OS !== 'web') AccessibilityInfo.announceForAccessibility(feedback.text);
    const timer = setTimeout(
      () => setFeedback((current) => (current?.id === feedback.id ? null : current)),
      6500,
    );
    return () => clearTimeout(timer);
  }, [feedback, active]);

  function respond(kind: GardenReaction['kind'], text: string, point: Point) {
    const id = ++reactionId.current;
    setTag(null);
    setFeedback({ id, kind, text, ...point });
    setReaction({
      id,
      kind,
      ...point,
      actor: { ...pos.current },
      signature: gardenSignature(player, reduced),
    });
  }

  function companionLine(kind: keyof typeof responseCount.current) {
    // Read, then write. React Compiler compiles `x = ref.current[k]++` as a
    // pre-increment, which skipped every first (memory) line.
    const count = responseCount.current[kind];
    responseCount.current[kind] = count + 1;
    return gardenResponse(player, kind, count, memories, grumpy);
  }

  function arrived(id: number, action: Action | null, point: Point) {
    if (!activeRef.current || id !== journeyId.current || journey.current?.id !== id) return;
    const exit = journey.current.exit;
    journey.current = null;
    pos.current = point;
    setWalking(false);
    setDestination(null);
    busy.current = false;
    if (action) act(action);
    else if (exit === 'door') {
      // in at the hut's door: the room inside picks up there (app/world.tsx)
      if (Math.hypot(point.x - HUT_DOOR.x, point.y - HUT_DOOR.y) <= 12)
        if (!leaving.current) {
          leaving.current = true;
          useUi.setState({ worldLink: { from: 'hut' } });
          router.push('/world');
        }
    } else if (exit && atGardenExit(exit, point)) leave(exit, point);
  }

  // Walking out: the valley picks up at this very spot and the companion walks on
  // through the gap (app/world.tsx); walking back in returns here.
  function leave(exit: GardenExit, at: Point) {
    if (napping || !activeRef.current || leaving.current) return;
    leaving.current = true;
    useUi.setState({ worldLink: { from: exit, ex: Math.round(at.x), ey: Math.round(at.y) } });
    router.push('/world');
  }

  function walkTo(target: Point, action: Action | null = null, door = false, speed = SPEED) {
    if (napping || !activeRef.current) return;
    const id = ++journeyId.current;
    cancelAnimation(px);
    cancelAnimation(py);
    if (napTimer.current) clearTimeout(napTimer.current);
    // Retarget from the displayed position, including a stroll interrupted mid-leg.
    const start = { x: px.get(), y: py.get() };
    pos.current = start;
    const path = findPath(start, target);
    const end = path[path.length - 1] ?? start;
    setDestination(action ? end : null);
    // a tap past the garden's edge (the gate, the trail, the meadow's sides) walks on out
    journey.current = {
      id,
      action,
      end,
      exit: door ? 'door' : action ? null : gardenExitToward(target),
    };
    if (!path.length) {
      arrived(id, action, end);
      return;
    }
    setFacing(end.x < start.x ? 'left' : 'right');
    if (reduced) {
      px.set(end.x);
      py.set(end.y);
      arrived(id, action, end);
      return;
    }
    busy.current = true;
    setWalking(true);
    let from = start;
    const xs = [];
    const ys = [];
    for (const p of path) {
      const d = Math.hypot(p.x - from.x, p.y - from.y);
      const duration = Math.max(60, (d / speed) * 1000);
      xs.push(withTiming(p.x, { duration, easing: Easing.linear }));
      ys.push(withTiming(p.y, { duration, easing: Easing.linear }));
      from = p;
    }
    px.set(withSequence(...xs));
    py.set(
      withSequence(
        ...ys,
        withTiming(end.y, { duration: 0 }, (finished) => {
          if (finished) runOnJS(arrived)(id, action, end);
        }),
      ),
    );
  }

  function act(action: Action) {
    const p = useGame.getState().player;
    if (!p || napping || !activeRef.current || p.mode !== 'awake') return;
    void Haptics.selectionAsync();
    switch (action) {
      case 'nap': {
        const id = journeyId.current;
        setEmote('z');
        napTimer.current = setTimeout(
          () => {
            if (!activeRef.current || id !== journeyId.current) return;
            napTimer.current = null;
            if (onNap) onNap();
            else useGame.getState().sleep();
          },
          reduced ? 0 : 500,
        );
        break;
      }
      case 'mail':
        router.push({ pathname: '/journal', params: { tab: 'postcards' } });
        break;
      case 'shop':
        router.push('/shop');
        break;
      case 'missions':
        router.push('/missions');
        break;
      case 'arena':
        // the gate opens on the valley: walk on out into the world
        leave('gate', pos.current);
        break;
      case 'feed':
        if (playPaused() || p.mood >= 100 || p.grass < 5) {
          useGame.setState({
            voice: playPaused()
              ? 'the bowl can wait. take a break first.'
              : p.mood >= 100
                ? 'i am full. thank you though.'
                : 'we need 5 GRASS for seeds.',
          });
          setEmote('…');
        } else {
          onFeed?.();
          playSound('munch');
          setEmote('♥');
        }
        break;
      case 'pond':
        playSound('splash');
        respond('pond', companionLine('pond'), gardenHotspots.pond);
        setEmote('♪');
        break;
      case 'read':
        playSound('page');
        respond('read', companionLine('read'), gardenHotspots.read);
        setEmote('…');
        break;
      case 'water':
        playSound('water');
        respond('water', companionLine('water'), gardenHotspots.water);
        setEmote('♪');
        break;
      case 'meadow':
        playSound('rustle');
        respond('meadow', meadowLine(lifetimeMinutes), gardenHotspots.meadow);
        setEmote('✿');
        break;
      case 'lantern': {
        const next = !lanternOn;
        setLanternOverride(next);
        playSound('lantern');
        respond(
          'lantern',
          next ? companionLine('lantern') : 'lights out. the stars can take over.',
          gardenHotspots.lantern,
        );
        if (!next) setReaction(null);
        break;
      }
    }
  }

  // Arrow keys / WASD (web): short walks in the held direction, sliding along walls.
  useKeyboardWalk(
    active && !napping,
    (dx, dy) => {
      const from = { x: px.get(), y: py.get() };
      // well past the next tick, so a held key never arrives (and re-renders) between ticks
      const reach = KEY_SPEED * (STEP_MS / 1000) * 2.5;
      for (const [ax, ay] of keySteps(dx, dy)) {
        const to = { x: from.x + ax * reach, y: from.y + ay * reach };
        const cell = toCell(to);
        if (walkable(cell.cx, cell.cy)) {
          walkTo(to, null, false, KEY_SPEED);
          return;
        }
      }
      // held against the garden's edge at an exit: on out into the valley
      const exit = gardenExitToward({ x: from.x + dx * 16, y: from.y + dy * 16 });
      if (exit && atGardenExit(exit, from)) leave(exit, from);
    },
    () => {},
  );

  // Back from the valley: stand where the companion walked in (no walk is under way:
  // the garden was off screen).
  const arrivalKey = arrival?.key;
  const arrivalAt = useRef(arrival);
  useEffect(() => {
    arrivalAt.current = arrival;
  });
  useLayoutEffect(() => {
    const a = arrivalAt.current;
    if (!arrivalKey || !a || napping) return;
    journeyId.current += 1;
    journey.current = null;
    cancelAnimation(px);
    cancelAnimation(py);
    const cell = nearestWalkable({ x: a.x, y: a.y });
    const p = toPoint(cell.cx, cell.cy);
    px.set(p.x);
    py.set(p.y);
    pos.current = p;
    busy.current = false;
    lastTouch.current = clock();
  }, [arrivalKey, napping, px, py]);

  // Idle life: wander, sniff the flowers, sit. Never while the player is acting.
  const walkRef = useRef(walkTo);
  const arriveRef = useRef(arrived);
  useEffect(() => {
    walkRef.current = walkTo;
    arriveRef.current = arrived;
  });
  useEffect(() => {
    if (!reduced || !active) return undefined;
    // An OS/app preference change also stops a stroll that was already in flight.
    const timer = setTimeout(() => {
      const pending = journey.current;
      if (!pending || !activeRef.current) return;
      cancelAnimation(px);
      cancelAnimation(py);
      px.set(pending.end.x);
      py.set(pending.end.y);
      arriveRef.current(pending.id, pending.action, pending.end);
    }, 0);
    return () => clearTimeout(timer);
  }, [reduced, active, px, py]);
  useEffect(() => {
    if (reduced || sleepy || napping || !active) return undefined;
    let timer: ReturnType<typeof setTimeout>;
    let emoteTimer: ReturnType<typeof setTimeout>;
    const tick = () => {
      if (!activeRef.current) return;
      if (!busy.current && clock() - lastTouch.current > 6000) {
        const roll = Math.random();
        if (roll < 0.5) walkRef.current(randomSpot(pos.current, 40));
        else if (roll < 0.7) {
          walkRef.current({ x: 142, y: 130 });
          emoteTimer = setTimeout(() => {
            if (activeRef.current && clock() - lastTouch.current > 6000) setEmote('♪');
          }, 2500);
        } else if (roll < 0.8) setEmote(grumpy ? '…' : '♪');
      }
      timer = setTimeout(tick, 4000 + Math.random() * 4000);
    };
    timer = setTimeout(tick, 2500);
    return () => {
      clearTimeout(timer);
      clearTimeout(emoteTimer);
    };
  }, [reduced, sleepy, grumpy, napping, active]);

  const petStyle = useAnimatedStyle(() => {
    const s = project(proj, px.value, py.value);
    return {
      transform: [
        { translateX: Math.round(s.sx - petPx / 2) },
        { translateY: Math.round(s.sy - petPx * (30 / 32)) },
        { scale: s.f },
      ],
      // Rest between the hut and bedding layers, under the garden's night light.
      zIndex: Math.round(py.value) + (napping ? 1 : 0),
    };
  });

  // Speech follows the companion; it flips below when the pet is near the top.
  // One speech style (coherence plan, step 3): a paper frame on the interface grid with
  // a tail pointing at whoever speaks, and one bubble at a time.
  const ui = scale;
  const [bubbleHeight, setBubbleHeight] = useState(0);
  const bubbleWidth = Math.min(width - 16, 232);
  const bubbleStyle = useAnimatedStyle(() => {
    const s = project(proj, px.value, py.value);
    const view0 = windowLeft(s.sx);
    const left = Math.min(
      view0 + width - bubbleWidth - 8,
      Math.max(view0 + 8, s.sx - bubbleWidth / 2),
    );
    const above = s.sy - petPx * 0.95 - bubbleHeight - 3 * ui;
    const top = py.value < TOP_FLIP ? s.sy + 3 * ui : above;
    return { transform: [{ translateX: Math.round(left) }, { translateY: Math.round(top) }] };
  });
  // The tail slides to stay over the companion when the bubble is held at the edge.
  const tailStyle = useAnimatedStyle(() => {
    const s = project(proj, px.value, py.value);
    const view0 = windowLeft(s.sx);
    const left = Math.min(
      view0 + width - bubbleWidth - 8,
      Math.max(view0 + 8, s.sx - bubbleWidth / 2),
    );
    const reach = bubbleWidth / 2 - 6 * ui;
    const dx = Math.max(-reach, Math.min(reach, s.sx - left - bubbleWidth / 2));
    return { transform: [{ translateX: Math.round(dx / ui) * ui }] };
  });
  const tailDown = useAnimatedStyle(() => ({ opacity: py.value < TOP_FLIP ? 0 : 1 }));
  const tailUp = useAnimatedStyle(() => ({ opacity: py.value < TOP_FLIP ? 1 : 0 }));
  const [tagWidth, setTagWidth] = useState<{ text: string; width: number } | null>(null);

  // The camera keeps the companion a little above centre and, when the map is wider
  // than the window, centred across it; both clamped to the map.
  const cameraStyle = useAnimatedStyle(() => {
    const x = windowLeft(project(proj, px.value, py.value).sx);
    if (!camera) return { transform: [{ translateX: -Math.round(x) }, { translateY: 0 }] };
    const target = py.value * scale - seenHeight * 0.55;
    const y = Math.min(cameraMax, Math.max(cameraMin, target));
    return { transform: [{ translateX: -Math.round(x) }, { translateY: -Math.round(y) }] };
  });

  function onGroundPress(e: {
    nativeEvent: { locationX?: number; locationY?: number; offsetX?: number; offsetY?: number };
  }) {
    if (napping || !activeRef.current) return;
    // Native gives locationX/Y; react-native-web click events only carry the DOM
    // offsetX/Y (relative to the full-size ground image), so fall back to those.
    // Keep this fallback: without it tapping the garden does nothing on web.
    const ne = e.nativeEvent;
    const lx = ne.locationX ?? ne.offsetX;
    const ly = ne.locationY ?? ne.offsetY;
    if (
      typeof lx !== 'number' ||
      typeof ly !== 'number' ||
      !Number.isFinite(lx) ||
      !Number.isFinite(ly)
    )
      return;
    lastTouch.current = clock();
    setTag(null);
    setFeedback(null);
    setReaction(null);
    // the tap surface starts at the horizon in 2.5D view
    playSound('steps');
    walkTo(unproject(proj, lx, ly + (tilt ? proj.horizon : 0)));
  }

  function onObjectPress(action: Action) {
    if (napping || !activeRef.current) return;
    lastTouch.current = clock();
    setFeedback(null);
    setReaction(null);
    const spot = gardenHotspots[action];
    setTag({ text: spot.label, x: spot.x, y: spot.y });
    playSound('steps');
    walkTo({ x: spot.x, y: spot.y }, action);
  }

  // The hut's door: walk up to it and go in.
  function goInside() {
    if (napping || !activeRef.current) return;
    lastTouch.current = clock();
    setFeedback(null);
    setReaction(null);
    setTag({ text: 'go inside the hut', x: HUT_DOOR.x, y: HUT_DOOR.y - 20 });
    playSound('steps');
    walkTo(HUT_DOOR, null, true);
  }

  function stopJourney() {
    journeyId.current += 1;
    journey.current = null;
    cancelAnimation(px);
    cancelAnimation(py);
    if (napTimer.current) clearTimeout(napTimer.current);
    napTimer.current = null;
    pos.current = { x: px.get(), y: py.get() };
    busy.current = false;
    setWalking(false);
    setDestination(null);
  }

  function patGuardian() {
    if (napping || !activeRef.current) return;
    lastTouch.current = clock();
    // A pat is a new intent. It must not leave a pending shop visit or nap behind.
    stopJourney();
    setEmote('♥');
    void Haptics.selectionAsync();
    playSound('boop');
    respond('pat', companionLine('pat'), pos.current);
  }

  const guardian = guardianPlayer(player);
  const companions = collectionOf(player)
    .filter((v) => v.befriendedAt !== null && v.id !== player.guardian)
    .slice(0, 3);
  const pond = groundRect(
    proj,
    gardenAnchors.pond.x,
    gardenAnchors.pond.y,
    gardenAnchors.pond.w,
    gardenAnchors.pond.h,
  );
  const keepsakes = gardenKeepsakes(memories);
  const pondWidth = Math.max(44, pond.width);
  const pondHeight = Math.max(44, pond.height);
  return (
    <View
      // @ts-expect-error dataSet is a react-native-web prop (sets data-pixel for crisp CSS scaling)
      dataSet={{ pixel: 'true' }}
      pointerEvents={napping || !active ? 'none' : 'auto'}
      // A nap garden is scenery: pointer-events alone still allows web keyboard focus.
      {...(Platform.OS === 'web' ? { inert: napping || !active } : {})}
      aria-hidden={napping || !active}
      accessibilityElementsHidden={napping || !active}
      importantForAccessibility={napping || !active ? 'no-hide-descendants' : 'auto'}
      style={{
        width,
        height: viewHeight,
        overflow: 'hidden',
        backgroundColor: '#315C3B',
        zIndex: 0,
      }}
    >
      <Animated.View
        style={[{ position: 'absolute', left: 0, top: 0, width: worldWidth, height }, cameraStyle]}
      >
        {camera && (
          <Image
            source={groundTop}
            resizeMode="stretch"
            style={{
              position: 'absolute',
              left: 0,
              top: -topBand,
              width: worldWidth,
              height: topBand,
            }}
          />
        )}
        {camera && (
          // past the gate the valley goes on: the top of the town lane, where walking
          // out of the gate leads (app/world.tsx)
          <Image
            source={townTop}
            resizeMode="stretch"
            style={{
              position: 'absolute',
              left: 0,
              top: height,
              width: worldWidth,
              height: Math.round(64 * scale),
            }}
          />
        )}
        {tilt && (
          // the retired tilt view's far edge: a plain sky band (the battle backdrop
          // images are no longer loaded by the garden, which saves phone memory)
          <View
            pointerEvents="none"
            style={{
              position: 'absolute',
              left: 0,
              top: 0,
              width: worldWidth,
              height: Math.max(0, Math.round(proj.horizon)),
              backgroundColor: night ? '#1A2142' : '#A9D3E6',
            }}
          />
        )}
        <View
          pointerEvents="none"
          style={[
            {
              position: 'absolute',
              left: 0,
              top: proj.bottom - Math.round(GARDEN.height * scale),
              width: worldWidth,
              height: Math.round(GARDEN.height * scale),
            },
            tilt && {
              transform: [{ perspective: proj.persp }, { rotateX: `${TILT_DEG}deg` }],
              transformOrigin: '50% 100%',
            },
          ]}
        >
          <Image
            source={groundImg}
            resizeMode="stretch"
            style={{ width: worldWidth, height: Math.round(GARDEN.height * scale) }}
          />
          {gardenWater.map((water) => {
            const r = snapRect({
              left: water.x * scale,
              top: water.y * scale,
              width: water.w * scale,
              height: water.h * scale,
            });
            return (
              <Image
                key={water.id}
                source={waterFrames[water.id][reduced ? 0 : frame]}
                resizeMode="stretch"
                style={{
                  position: 'absolute',
                  left: r.left,
                  top: r.top,
                  width: r.width,
                  height: r.height,
                }}
              />
            );
          })}
          {destination && !napping && active && (
            <View
              style={{
                position: 'absolute',
                left: Math.round((destination.x - 3) * scale),
                top: Math.round((destination.y - 2) * scale),
                width: Math.round(6 * scale),
                height: Math.round(4 * scale),
                borderWidth: Math.max(1, Math.round(scale)),
                borderColor: '#FFF0B7',
                backgroundColor: 'rgba(81,107,55,0.3)',
              }}
            />
          )}
        </View>
        <Pressable
          accessibilityLabel={`Your garden. Tap to walk ${guardian.pet_name} around.`}
          disabled={napping || !active}
          onPress={onGroundPress}
          style={{
            position: 'absolute',
            left: 0,
            top: tilt ? proj.horizon : 0,
            width: worldWidth,
            height: tilt ? height - proj.horizon : height,
          }}
        />
        {gardenObjects.map((o) => {
          // Upright billboard standing on its footprint (identity in flat view).
          const art = billboard(proj, o.x, o.y, o.w, o.h);
          const px1 = scale * art.f; // one art pixel on screen at this depth
          const sprite = (
            <Sprite key={o.id} source={sprites[o.sprite]} rect={snapRect(art)} z={o.y + o.h} />
          );
          if (!o.action)
            return (
              <View
                key={o.id}
                pointerEvents="none"
                style={{ position: 'absolute', zIndex: o.y + o.h }}
              >
                {sprite}
              </View>
            );
          const action = o.action as Action;
          const isNewInteraction = action === 'read' || action === 'water' || action === 'lantern';
          const artLeft = snap(art.left);
          const artTop = snap(art.top);
          const artWidth = snap(art.width);
          const artHeight = snap(art.height);
          const targetWidth = Math.max(44, artWidth);
          const targetHeight = Math.max(44, artHeight);
          const targetLeft = snap(
            Math.max(0, Math.min(worldWidth - targetWidth, artLeft - (targetWidth - artWidth) / 2)),
          );
          const targetTop = snap(
            Math.max(0, Math.min(height - targetHeight, artTop - (targetHeight - artHeight) / 2)),
          );
          // These small props need a hit area above a nearby guardian, while
          // their artwork keeps its ordinary depth and can still sit behind it.
          const imageLeft = isNewInteraction ? artLeft : artLeft - targetLeft;
          const imageTop = isNewInteraction ? artTop : artTop - targetTop;
          const artwork = (
            <>
              <Image
                key={`${o.id}-image`}
                source={sprites[o.sprite]}
                resizeMode="stretch"
                style={{
                  position: 'absolute',
                  left: imageLeft,
                  top: imageTop,
                  width: artWidth,
                  height: artHeight,
                }}
              />
              {action === 'lantern' && !lanternOn && (
                <View
                  pointerEvents="none"
                  style={{
                    position: 'absolute',
                    left: imageLeft + snap(7 * px1),
                    top: imageTop + snap(11 * px1),
                    width: snap(5 * px1),
                    height: snap(10 * px1),
                    backgroundColor: '#71817A',
                    borderLeftWidth: Math.max(1, Math.round(px1)),
                    borderLeftColor: '#A6B69E',
                  }}
                />
              )}
              {isNewInteraction && !napping && active && (
                <View
                  pointerEvents="none"
                  style={{
                    position: 'absolute',
                    left: imageLeft + Math.round((o.w / 2 - 2) * px1),
                    top: imageTop - Math.round(5 * px1),
                    width: Math.round(4 * px1),
                    height: Math.round(4 * px1),
                    backgroundColor: '#FFF3CF',
                    borderWidth: Math.max(1, Math.round(px1)),
                    borderColor: '#647E46',
                  }}
                />
              )}
            </>
          );
          return (
            <Fragment key={o.id}>
              {isNewInteraction && (
                <View
                  key={`${o.id}-art`}
                  pointerEvents="none"
                  style={{ position: 'absolute', left: 0, top: 0, zIndex: o.y + o.h }}
                >
                  {artwork}
                </View>
              )}
              <Pressable
                key={o.id}
                accessibilityRole="button"
                accessibilityLabel={
                  o.id === 'hut'
                    ? 'go inside the hut'
                    : action === 'lantern'
                      ? `Turn the leaf lantern ${lanternOn ? 'off' : 'on'}`
                      : gardenHotspots[action].label
                }
                accessibilityHint={
                  action === 'read'
                    ? 'Walk to the bench and turn a page.'
                    : action === 'water'
                      ? 'Walk over and water the flowers.'
                      : action === 'lantern'
                        ? 'Walk to the post, then change its light.'
                        : undefined
                }
                aria-pressed={action === 'lantern' ? lanternOn : undefined}
                disabled={napping || !active}
                onFocus={() => {
                  if (activeRef.current && !napping)
                    setTag({
                      text: o.id === 'hut' ? 'go inside the hut' : gardenHotspots[action].label,
                      x: o.x + o.w / 2,
                      y: o.y,
                    });
                }}
                // the hut is walked into by its door; the bed beside it is the nap
                onPress={() => (o.id === 'hut' ? goInside() : onObjectPress(action))}
                style={{
                  position: 'absolute',
                  left: targetLeft,
                  top: targetTop,
                  width: targetWidth,
                  height: targetHeight,
                  zIndex: isNewInteraction ? 800 : o.y + o.h,
                }}
              >
                {!isNewInteraction && artwork}
              </Pressable>
            </Fragment>
          );
        })}
        {gardenPlots.map((plot, i) => {
          const stage = plotStage(lifetimeMinutes, i);
          const key = `plot_${plot.kind}_${stage}`;
          const [sw, sh] = growthSize(key);
          const hit = {
            left: Math.round(plot.x * scale),
            top: Math.round((plot.y - 6) * scale),
            width: Math.max(44, Math.round(plot.w * scale)),
            height: Math.max(44, Math.round((plot.h + 6) * scale)),
          };
          return (
            <Fragment key={plot.id}>
              {stage >= 0 && (
                <Sprite
                  source={growthImages[key]}
                  rect={snapRect({
                    left: plot.x * scale,
                    top: (plot.y - (sh - plot.h)) * scale,
                    width: sw * scale,
                    height: sh * scale,
                  })}
                  z={plot.y + plot.h}
                />
              )}
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={
                  stage < 0
                    ? 'An empty meadow bed, waiting for seeds'
                    : stage === 4
                      ? `A ${plot.kind} bed in bloom`
                      : `A ${plot.kind} bed, still growing`
                }
                disabled={napping || !active}
                onPress={() => onObjectPress('meadow')}
                style={{ position: 'absolute', ...hit, zIndex: plot.y + plot.h }}
              />
            </Fragment>
          );
        })}
        {gardenOrchard.map((pit, i) => {
          const stage = orchardStage(lifetimeMinutes, i);
          if (stage < 0) return null;
          const key = `orchard_${stage}`;
          const [sw, sh] = growthSize(key);
          return (
            <Pressable
              key={pit.id}
              accessibilityRole="button"
              accessibilityLabel={
                stage === 4 ? 'A fruit tree in the orchard' : 'A young tree in the orchard'
              }
              disabled={napping || !active}
              onPress={() => onObjectPress('meadow')}
              style={{
                position: 'absolute',
                left: Math.round((pit.x - sw / 2) * scale),
                top: Math.round((pit.y - sh) * scale),
                width: Math.max(44, Math.round(sw * scale)),
                height: Math.max(44, Math.round(sh * scale)),
                zIndex: pit.y,
              }}
            >
              <Image
                source={growthImages[key]}
                resizeMode="stretch"
                style={{ width: snap(sw * scale), height: snap(sh * scale) }}
              />
            </Pressable>
          );
        })}
        {marker && !napping && active && (
          <GardenMarker action={marker} scale={scale} bob={!reduced && frame % 2 === 1} />
        )}
        {keepsakeIntentions
          .filter((intention) => keepsakes[intention])
          .map((intention) => {
            const location = keepsakeLocations[intention];
            const foot = project(proj, location.x + 8, location.y + 16);
            const size = snap(16 * scale * foot.f);
            const memory = keepsakes[intention];
            const box = {
              position: 'absolute' as const,
              left: snap(foot.sx - size / 2),
              top: snap(foot.sy - size),
              width: size,
              height: size,
            };
            if (onKeepsakePress && memory && !napping)
              return (
                <Pressable
                  key={`keepsake-${intention}`}
                  testID={`garden-keepsake-${intention}`}
                  accessibilityRole="button"
                  accessibilityLabel={`Open the ${intention} keepsake from your break with ${memory.companion.name}`}
                  disabled={!active}
                  hitSlop={Math.max(0, Math.ceil((44 - size) / 2))}
                  onPress={() => {
                    if (!activeRef.current) return;
                    lastTouch.current = clock();
                    onKeepsakePress(memory);
                  }}
                  style={{ ...box, zIndex: 801 }}
                >
                  <GardenKeepsakeArt intention={intention} size={size} />
                </Pressable>
              );
            return (
              <View
                key={`keepsake-${intention}`}
                testID={`garden-keepsake-${intention}`}
                pointerEvents="none"
                aria-hidden
                accessibilityElementsHidden
                importantForAccessibility="no-hide-descendants"
                style={{ ...box, zIndex: location.y + 17 }}
              >
                <GardenKeepsakeArt intention={intention} size={size} />
              </View>
            );
          })}
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Look into the pond"
          disabled={napping || !active}
          onPress={() => onObjectPress('pond')}
          style={{
            position: 'absolute',
            left: Math.max(
              0,
              Math.min(worldWidth - pondWidth, pond.left - (pondWidth - pond.width) / 2),
            ),
            top: Math.max(
              0,
              Math.min(height - pondHeight, pond.top - (pondHeight - pond.height) / 2),
            ),
            width: pondWidth,
            height: pondHeight,
            zIndex: 1,
          }}
        />
        <Animated.View
          style={[
            {
              position: 'absolute',
              left: 0,
              top: 0,
              width: petPx,
              height: petPx,
              // Depth scaling must keep the sprite's feet on its projected path.
              transformOrigin: '50% 93.75%',
            },
            petStyle,
          ]}
        >
          {emote && (
            <View
              pointerEvents="none"
              style={{
                position: 'absolute',
                top: -petPx * 0.35,
                alignSelf: 'center',
                minWidth: 26,
                paddingHorizontal: 6,
                borderRadius: 0,
                borderWidth: 2,
                borderColor: c.outline,
                backgroundColor: c.paper,
                alignItems: 'center',
              }}
            >
              <BodyText style={{ fontSize: 13, lineHeight: 18 }}>{emote}</BodyText>
            </View>
          )}
          <GuardianPet
            active={active}
            player={player}
            size={petPx}
            facing={facing}
            walking={walking && !napping && active}
            grumpy={grumpy && !napping}
            yawning={sleepy}
            sleeping={napping}
            curled={napping}
            groundShadow={!napping}
            bob={!walking && !napping && active}
            gardenPose={
              active && !napping && !walking && reaction?.signature
                ? { id: reaction.id, kind: reaction.signature.pose }
                : undefined
            }
            onPress={patGuardian}
          />
        </Animated.View>
        {companions.map((v, i) => (
          <View
            key={v.id}
            style={{
              position: 'absolute',
              left: Math.round(
                project(proj, companionSpots[i].x, companionSpots[i].y).sx - companionPx / 2,
              ),
              top: Math.round(
                project(proj, companionSpots[i].x, companionSpots[i].y).sy -
                  companionPx * (30 / 32),
              ),
              width: companionPx,
              height: companionPx,
              transform: [{ scale: project(proj, companionSpots[i].x, companionSpots[i].y).f }],
              transformOrigin: '50% 93.75%',
              zIndex: companionSpots[i].y,
            }}
          >
            <Pet
              active={active}
              visitor={v.id}
              size={companionPx}
              sleeping={napping}
              facing={i % 2 ? 'left' : 'right'}
              bob={!napping && active}
              onPress={() => {
                if (napping || !activeRef.current) return;
                lastTouch.current = clock();
                stopJourney();
                setTag(null);
                setFeedback(null);
                setReaction(null);
                useGame.setState({
                  voice: `${visitorInfo(v.id).name.toLowerCase()} waves a leaf at you.`,
                });
              }}
            />
          </View>
        ))}
        {reaction && !napping && active && (
          <GardenReactions
            key={reaction.id}
            reaction={reaction}
            scale={scale}
            reduced={reduced}
            place={place}
            base={reactionBase(reaction)}
            actor={reaction.actor}
            signature={reaction.signature}
          />
        )}
        {(night || dusk || dawn) && (
          <View
            pointerEvents="none"
            style={{
              position: 'absolute',
              left: 0,
              top: camera ? -topBand : 0,
              width: worldWidth,
              height: height + (camera ? topBand : 0),
              zIndex: 900,
              backgroundColor: night
                ? 'rgba(22,28,66,0.42)'
                : dusk
                  ? 'rgba(240,128,70,0.16)'
                  : 'rgba(255,200,150,0.12)',
            }}
          />
        )}
        <View pointerEvents="none" style={{ position: 'absolute', left: 0, top: 0, zIndex: 901 }}>
          {gardenAnchors.lights
            .filter((light) => (light.kind === 'lantern' ? lanternOn : night))
            .map((light) => (
              <Image
                key={light.id}
                source={lightImages[light.id]}
                resizeMode="stretch"
                style={{
                  position: 'absolute',
                  left: snap(light.x * scale),
                  top: snap(light.y * scale),
                  width: snap(light.w * scale),
                  height: snap(light.h * scale),
                }}
              />
            ))}
        </View>
        <Ambient
          scale={scale}
          place={place}
          width={worldWidth}
          height={height}
          rain={grumpy && !napping}
          night={night}
          day={!night && !grumpy}
          reduced={reduced}
          active={active}
        />
        {napping && active && (
          <View
            pointerEvents="none"
            style={{
              position: 'absolute',
              left: Math.round(project(proj, BED.x, BED.y).sx),
              top: Math.round(project(proj, BED.x, BED.y).sy - petPx * 1.1),
              zIndex: 990,
            }}
          >
            <FloatingZ />
          </View>
        )}
        {tag &&
          !feedback &&
          (() => {
            const at = project(proj, tag.x, tag.y);
            const measured = tagWidth?.text === tag.text ? tagWidth.width : 0;
            const view0 = windowLeft(at.sx);
            const left = Math.max(
              view0 + 4,
              Math.min(view0 + width - measured - 4, at.sx - measured / 2),
            );
            const reach = Math.max(0, measured / 2 - 5 * ui);
            const tail = Math.max(-reach, Math.min(reach, at.sx - left - measured / 2));
            const tagHeight = type.label.lineHeight + 2 * contentInset(ui);
            return (
              <View
                pointerEvents="none"
                onLayout={(e) =>
                  setTagWidth({ text: tag.text, width: Math.round(e.nativeEvent.layout.width) })
                }
                style={{
                  position: 'absolute',
                  left: Math.round(left),
                  top: Math.max(4, Math.round(at.sy - tagHeight - 3 * ui)),
                  padding: contentInset(ui),
                  opacity: measured ? 1 : 0,
                  zIndex: 999,
                }}
              >
                <FrameShape tone={frameTones.paper} unit={ui} />
                <BodyText style={[type.label, { color: c.ink }]}>{tag.text.toUpperCase()}</BodyText>
                <PixelTail offset={tail} />
              </View>
            );
          })()}
        {say && !feedback && !tag && !napping && active && (
          <Animated.View
            onLayout={(e) => setBubbleHeight(Math.round(e.nativeEvent.layout.height))}
            style={[
              { position: 'absolute', left: 0, top: 0, width: bubbleWidth, zIndex: 998 },
              bubbleStyle,
            ]}
          >
            <Pressable
              accessibilityRole={say.onPress ? 'button' : 'text'}
              accessibilityLabel={say.text}
              accessibilityHint={say.hint}
              disabled={!say.onPress}
              onPress={say.onPress}
              style={{ padding: contentInset(ui) }}
            >
              <FrameShape tone={frameTones.paper} unit={ui} />
              <BodyText
                role="status"
                aria-live="polite"
                accessibilityLiveRegion="polite"
                style={type.body}
              >
                {say.text.toLowerCase()}
              </BodyText>
              {say.hint && (
                <BodyText style={[type.caption, { color: c.shade }]}>{say.hint}</BodyText>
              )}
              <Animated.View
                pointerEvents="none"
                style={[{ position: 'absolute', left: 0, right: 0, top: 0, bottom: 0 }, tailStyle]}
              >
                <Animated.View
                  style={[{ position: 'absolute', left: 0, right: 0, top: 0, bottom: 0 }, tailDown]}
                >
                  <PixelTail />
                </Animated.View>
                <Animated.View
                  style={[{ position: 'absolute', left: 0, right: 0, top: 0, bottom: 0 }, tailUp]}
                >
                  <PixelTail side="top" />
                </Animated.View>
              </Animated.View>
            </Pressable>
          </Animated.View>
        )}
        {feedback &&
          !napping &&
          active &&
          (() => {
            const at = project(proj, feedback.x, feedback.y);
            const w = Math.min(width - 16, 216);
            const view0 = windowLeft(at.sx);
            const left = Math.max(view0 + 8, Math.min(view0 + width - w - 8, at.sx - w / 2));
            const below = feedback.kind === 'pat' || feedback.y < 90;
            const reach = w / 2 - 6 * ui;
            const tail = Math.max(-reach, Math.min(reach, at.sx - left - w / 2));
            return (
              <View
                pointerEvents="none"
                style={{
                  position: 'absolute',
                  left: Math.round(left),
                  width: w,
                  padding: contentInset(ui),
                  zIndex: 999,
                  // anchored by the edge nearest the target, so the tail always reaches it
                  ...(below
                    ? { top: Math.round(Math.min(height - 94, at.sy + 12)) }
                    : { bottom: Math.round(Math.min(height - 8, height - at.sy + 24)) }),
                }}
              >
                <FrameShape tone={frameTones.paper} unit={ui} />
                <BodyText
                  role="status"
                  aria-live="polite"
                  accessibilityLiveRegion="polite"
                  style={type.body}
                >
                  {feedback.text}
                </BodyText>
                <PixelTail side={below ? 'top' : 'bottom'} offset={tail} />
              </View>
            );
          })()}
      </Animated.View>
    </View>
  );
}
