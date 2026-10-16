import { Fragment, useEffect, useLayoutEffect, useRef, useState } from 'react';
import {
  AccessibilityInfo,
  Image,
  Platform,
  Pressable,
  View,
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
import type { BreakIntention, CompanionMemory } from '@/lib/companion-memories';
import { gardenKeepsakes, gardenResponse, gardenSignature } from '@/lib/garden-life';
import { playPaused, useGame, type Player } from '@/lib/game';
import { collectionOf, guardianPlayer, visitorInfo } from '@/lib/visitors';
import { GARDEN, gardenHotspots, gardenObjects } from '@/lib/garden-map';
import { GARDEN_START, findPath, randomSpot, type Point } from '@/lib/garden-path';
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
import battleDay from '@/assets/battle/backdrop-day.png';
import battleNight from '@/assets/battle/backdrop-night.png';
import { GuardianPet } from '@/components/guardian-pet';
import { FloatingZ, Pet } from '@/components/game-ui';
import { BodyText } from '@/components/pixel-feedback';
import { GardenReactions, type GardenReaction, type Place } from '@/components/garden-reactions';
import { GardenKeepsakeArt } from '@/components/garden-keepsakes';

import ground0 from '@/assets/garden/ground-0.png';
import ground1 from '@/assets/garden/ground-1.png';
import ground2 from '@/assets/garden/ground-2.png';
import ground3 from '@/assets/garden/ground-3.png';
import treeImg from '@/assets/garden/tree.png';
import treeSmallImg from '@/assets/garden/tree_small.png';
import treeAutumnImg from '@/assets/garden/tree_autumn.png';
import pineImg from '@/assets/garden/pine.png';
import hutImg from '@/assets/garden/hut.png';
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
};

type Action = keyof typeof gardenHotspots;

// Wall clock for 'player touched recently' checks (only ever called from handlers).
const clock = () => Date.now();
const SPEED = 34; // native pixels per second, a gentle stroll
const START: Point = GARDEN_START;
const BED: Point = { x: 73, y: 76 };
const groundFrames = [ground0, ground1, ground2, ground3];

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

const companionSpots: Point[] = [
  { x: 74, y: 150 },
  { x: 160, y: 104 },
  { x: 30, y: 108 },
];

const noMemories: readonly CompanionMemory[] = [];
const keepsakeIntentions: readonly BreakIntention[] = ['rest', 'read', 'move', 'create'];
// Keepsakes sit on the edges of existing places, leaving the clearing and
// existing touch targets intact. All four use a 16-pixel native art frame.
const keepsakeLocations: Record<BreakIntention, Point> = {
  rest: { x: 130, y: 82 },
  read: { x: 100, y: 50 },
  move: { x: 154, y: 118 },
  create: { x: 44, y: 100 },
};

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
        left: Math.round(rect.left),
        top: Math.round(rect.top),
        width: Math.round(rect.width),
        height: Math.round(rect.height),
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
        x: 30 + ((i * 47) % 140) + Math.sin(t / 14 + i) * 8,
        y: 70 + ((i * 29) % 80) + Math.cos(t / 17 + i * 2) * 6,
        // A slow glow has no abrupt on/off frame or rapid flashing.
        opacity: 0.2 + ((Math.sin((t + i * 7) / 6) + 1) / 2) * 0.7,
      }))
    : [];
  const butterflies = day
    ? [0, 1].map((i) => ({
        x: 142 + Math.cos(t / 18 + i * 3) * (16 + i * 6),
        y: 112 + Math.sin(t / 11 + i * 2) * 9 - 6,
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
              x: 52 + Math.floor(age / 6),
              y: 29 - Math.floor(age / 2),
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

// ---- the world -----------------------------------------------------------
export function GardenWorld({
  width,
  player,
  grumpy,
  sleepy,
  onFeed,
  napping = false,
  active: screenActive = true,
  view = 'flat',
  memories = noMemories,
}: {
  width: number;
  player: Player;
  grumpy: boolean;
  sleepy: boolean;
  onFeed?: () => void;
  /** Night garden for the nap screen: pet asleep in its bed, no interaction. */
  napping?: boolean;
  /** Tab screens stay mounted; pause the world and cancel its actions on blur. */
  active?: boolean;
  /** 'flat' top-down, or 'tilt' 2.5D: tilted ground with upright billboard sprites. */
  view?: ViewMode;
  /** Explicitly kept memories only; this scene never creates or settles them. */
  memories?: readonly CompanionMemory[];
}) {
  const reduced = useReducedMotion();
  const appActive = useAppActive();
  const active = screenActive && appActive;
  const scale = width / GARDEN.width;
  // All placement goes through one projection (identity in flat view).
  const tilt = view === 'tilt';
  const proj = makeProjection(view, width, GARDEN, tilt ? Math.round(width * 0.14) : 0);
  const height = proj.height;
  const place: Place = (x, y, groundY = y) => lift(proj, x, y, groundY);
  const petPx = Math.max(32, Math.round((32 * scale) / 32) * 32); // matches Pet's snapping
  const companionPx = Math.max(32, Math.round(petPx / 2 / 32) * 32);
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
  const activeRef = useRef(active);
  const lastTouch = useRef(0);
  const journeyId = useRef(0);
  const journey = useRef<{ id: number; action: Action | null; end: Point } | null>(null);
  const napTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useLayoutEffect(() => {
    activeRef.current = active;
    if (active) return;
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

  // Water has four calm phases; the grass artwork holds each pose for two.
  useEffect(() => {
    if (reduced || !active) return undefined;
    const t = setInterval(() => setFrame((f) => (f + 1) % groundFrames.length), 400);
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
    const count = responseCount.current[kind]++;
    return gardenResponse(player, kind, count, memories);
  }

  function arrived(id: number, action: Action | null, point: Point) {
    if (!activeRef.current || id !== journeyId.current || journey.current?.id !== id) return;
    journey.current = null;
    pos.current = point;
    setWalking(false);
    setDestination(null);
    busy.current = false;
    if (action) act(action);
  }

  function walkTo(target: Point, action: Action | null = null) {
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
    journey.current = { id, action, end };
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
      const duration = Math.max(60, (d / SPEED) * 1000);
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
            useGame.getState().sleep();
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
        router.push('/arena');
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
          setEmote('♥');
        }
        break;
      case 'pond':
        respond('pond', companionLine('pond'), gardenHotspots.pond);
        setEmote('♪');
        break;
      case 'read':
        respond('read', companionLine('read'), gardenHotspots.read);
        setEmote('…');
        break;
      case 'water':
        respond('water', companionLine('water'), gardenHotspots.water);
        setEmote('♪');
        break;
      case 'lantern': {
        const next = !lanternOn;
        setLanternOverride(next);
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
    walkTo(unproject(proj, lx, ly + (tilt ? proj.horizon : 0)));
  }

  function onObjectPress(action: Action) {
    if (napping || !activeRef.current) return;
    lastTouch.current = clock();
    setFeedback(null);
    setReaction(null);
    const spot = gardenHotspots[action];
    setTag({ text: spot.label, x: spot.x, y: spot.y });
    walkTo({ x: spot.x, y: spot.y }, action);
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
    respond('pat', companionLine('pat'), pos.current);
  }

  const guardian = guardianPlayer(player);
  const companions = collectionOf(player)
    .filter((v) => v.befriendedAt !== null && v.id !== player.guardian)
    .slice(0, 3);
  const pond = groundRect(proj, 16, 118, 52, 30);
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
      style={{ width, height, overflow: 'hidden', backgroundColor: '#62A853', zIndex: 0 }}
    >
      {tilt && (
        <Image
          source={night ? battleNight : battleDay}
          resizeMode="stretch"
          style={{
            position: 'absolute',
            left: 0,
            // battle backdrop's horizon (native y 78 of 150) sits on the garden's far edge
            top: Math.round(proj.horizon - 80 * (width / 216)),
            width,
            height: Math.round(150 * (width / 216)),
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
            width,
            height: Math.round(GARDEN.height * scale),
          },
          tilt && {
            transform: [{ perspective: proj.persp }, { rotateX: `${TILT_DEG}deg` }],
            transformOrigin: '50% 100%',
          },
        ]}
      >
        <Image
          source={groundFrames[reduced ? 0 : frame]}
          resizeMode="stretch"
          style={{ width, height: Math.round(GARDEN.height * scale) }}
        />
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
          width,
          height: tilt ? height - proj.horizon : height,
        }}
      />
      {gardenObjects.map((o) => {
        // Upright billboard standing on its footprint (identity in flat view).
        const art = billboard(proj, o.x, o.y, o.w, o.h);
        const px1 = scale * art.f; // one art pixel on screen at this depth
        const sprite = <Sprite key={o.id} source={sprites[o.sprite]} rect={art} z={o.y + o.h} />;
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
        const artLeft = Math.round(art.left);
        const artTop = Math.round(art.top);
        const artWidth = Math.round(art.width);
        const artHeight = Math.round(art.height);
        const targetWidth = Math.max(44, artWidth);
        const targetHeight = Math.max(44, artHeight);
        const targetLeft = Math.max(
          0,
          Math.min(width - targetWidth, artLeft - (targetWidth - artWidth) / 2),
        );
        const targetTop = Math.max(
          0,
          Math.min(height - targetHeight, artTop - (targetHeight - artHeight) / 2),
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
                  left: imageLeft + Math.round(7 * px1),
                  top: imageTop + Math.round(10 * px1),
                  width: Math.round(3 * px1),
                  height: Math.round(6 * px1),
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
                action === 'lantern'
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
                  setTag({ text: gardenHotspots[action].label, x: o.x + o.w / 2, y: o.y });
              }}
              onPress={() => onObjectPress(action)}
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
      {keepsakeIntentions
        .filter((intention) => keepsakes[intention])
        .map((intention) => {
          const location = keepsakeLocations[intention];
          const foot = project(proj, location.x + 8, location.y + 16);
          const size = Math.max(16, Math.round(scale * foot.f) * 16);
          return (
            <View
              key={`keepsake-${intention}`}
              testID={`garden-keepsake-${intention}`}
              pointerEvents="none"
              aria-hidden
              accessibilityElementsHidden
              importantForAccessibility="no-hide-descendants"
              style={{
                position: 'absolute',
                left: Math.round(foot.sx - size / 2),
                top: Math.round(foot.sy - size),
                width: size,
                height: size,
                zIndex: location.y + 17,
              }}
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
          left: Math.max(0, Math.min(width - pondWidth, pond.left - (pondWidth - pond.width) / 2)),
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
              borderRadius: 10,
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
              project(proj, companionSpots[i].x, companionSpots[i].y).sy - companionPx * (30 / 32),
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
            top: 0,
            width,
            height,
            zIndex: 900,
            backgroundColor: night
              ? 'rgba(22,28,66,0.42)'
              : dusk
                ? 'rgba(240,128,70,0.16)'
                : 'rgba(255,200,150,0.12)',
          }}
        />
      )}
      {[
        ...(night ? [{ x: 48, y: 54, size: 8, ground: HUT_FOOT }] : []),
        ...(lanternOn ? [{ x: 123, y: 71, size: 7, ground: LANTERN_FOOT }] : []),
      ].map((light) => (
        <View
          key={`${light.x}-${light.y}`}
          pointerEvents="none"
          style={{
            position: 'absolute',
            left: Math.round(place(light.x, light.y, light.ground).sx),
            top: Math.round(place(light.x, light.y, light.ground).sy),
            width: Math.round(light.size * scale),
            height: Math.round(light.size * scale),
            borderRadius: Math.round(4 * scale),
            backgroundColor: 'rgba(255,214,120,0.35)',
            zIndex: 901,
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <View
            style={{
              width: Math.round(4 * scale),
              height: Math.round(4 * scale),
              backgroundColor: '#FFE08A',
            }}
          />
        </View>
      ))}
      <Ambient
        scale={scale}
        place={place}
        width={width}
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
      {tag && (
        <View
          pointerEvents="none"
          style={{
            position: 'absolute',
            left: Math.max(4, Math.min(width - 160, project(proj, tag.x, tag.y).sx - 80)),
            top: Math.max(4, project(proj, tag.x, tag.y).sy - 70),
            width: 160,
            alignItems: 'center',
            zIndex: 999,
          }}
        >
          <BodyText
            style={{
              fontSize: 12,
              fontFamily: 'Nunito_800ExtraBold',
              paddingHorizontal: 10,
              paddingVertical: 3,
              borderRadius: 999,
              overflow: 'hidden',
              backgroundColor: c.glass,
            }}
          >
            {tag.text}
          </BodyText>
        </View>
      )}
      {feedback && !napping && active && (
        <View
          pointerEvents="none"
          style={{
            position: 'absolute',
            left: Math.max(
              8,
              Math.min(width - 224, project(proj, feedback.x, feedback.y).sx - 108),
            ),
            top: Math.max(
              8,
              Math.min(
                height - 94,
                feedback.kind === 'pat' || feedback.y < 90
                  ? project(proj, feedback.x, feedback.y).sy + 12
                  : project(proj, feedback.x, feedback.y).sy - 86,
              ),
            ),
            width: Math.min(width - 16, 216),
            zIndex: 999,
            paddingHorizontal: 12,
            paddingVertical: 8,
            borderWidth: 2,
            borderColor: c.outline,
            borderRadius: 12,
            backgroundColor: c.paper,
            boxShadow: '0 3px 0 rgba(74,59,53,0.22)',
          }}
        >
          <BodyText
            role="status"
            aria-live="polite"
            accessibilityLiveRegion="polite"
            style={{ fontFamily: 'Nunito_800ExtraBold', fontSize: 13, lineHeight: 18 }}
          >
            {feedback.text}
          </BodyText>
        </View>
      )}
    </View>
  );
}
