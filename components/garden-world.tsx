import { useEffect, useRef, useState } from 'react';
import { Image, Platform, Pressable, View, type ImageSourcePropType } from 'react-native';
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
import { playPaused, useGame, type Player } from '@/lib/game';
import { collectionOf, guardianPlayer, visitorInfo } from '@/lib/visitors';
import { GARDEN, gardenHotspots, gardenObjects, gardenWalk } from '@/lib/garden-map';
import { GuardianPet } from '@/components/guardian-pet';
import { FloatingZ, Pet } from '@/components/game-ui';
import { BodyText } from '@/components/pixel-feedback';

import ground0 from '@/assets/garden/ground-0.png';
import ground1 from '@/assets/garden/ground-1.png';
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
type Point = { x: number; y: number };

// Wall clock for 'player touched recently' checks (only ever called from handlers).
const clock = () => Date.now();
const SPEED = 34; // native pixels per second, a gentle stroll
const START: Point = { x: 96, y: 112 };
const BED: Point = { x: 73, y: 76 };

// ---- walk grid (4px cells, '#' = blocked) -----------------------------------
const rows = gardenWalk.length;
const cols = gardenWalk[0].length;
const walkable = (cx: number, cy: number) =>
  cy >= 0 && cy < rows && cx >= 0 && cx < cols && gardenWalk[cy][cx] === '.';
const toCell = (p: Point) => ({
  cx: Math.max(0, Math.min(cols - 1, Math.floor(p.x / GARDEN.cell))),
  cy: Math.max(0, Math.min(rows - 1, Math.floor(p.y / GARDEN.cell))),
});
const toPoint = (cx: number, cy: number): Point => ({
  x: cx * GARDEN.cell + GARDEN.cell / 2,
  y: cy * GARDEN.cell + GARDEN.cell / 2,
});

// Nearest walkable cell to a point (the pet stops at the edge of the pond, etc.).
function nearestWalkable(p: Point) {
  const { cx, cy } = toCell(p);
  for (let r = 0; r < 12; r++)
    for (let dy = -r; dy <= r; dy++)
      for (let dx = -r; dx <= r; dx++)
        if (Math.max(Math.abs(dx), Math.abs(dy)) === r && walkable(cx + dx, cy + dy))
          return { cx: cx + dx, cy: cy + dy };
  return toCell(START);
}

// Breadth-first search on the walk grid (8 directions), then thin to turning points.
function findPath(from: Point, to: Point): Point[] {
  const a = nearestWalkable(from);
  const b = nearestWalkable(to);
  const key = (x: number, y: number) => y * cols + x;
  const prev = new Map<number, number>();
  const queue: [number, number][] = [[a.cx, a.cy]];
  prev.set(key(a.cx, a.cy), -1);
  while (queue.length) {
    const [x, y] = queue.shift()!;
    if (x === b.cx && y === b.cy) break;
    for (const [dx, dy] of [
      [1, 0],
      [-1, 0],
      [0, 1],
      [0, -1],
      [1, 1],
      [1, -1],
      [-1, 1],
      [-1, -1],
    ]) {
      const nx = x + dx;
      const ny = y + dy;
      if (!walkable(nx, ny) || prev.has(key(nx, ny))) continue;
      if (dx && dy && (!walkable(x + dx, y) || !walkable(x, y + dy))) continue; // no corner cutting
      prev.set(key(nx, ny), key(x, y));
      queue.push([nx, ny]);
    }
  }
  if (!prev.has(key(b.cx, b.cy))) return [];
  const cells: [number, number][] = [];
  for (let k = key(b.cx, b.cy); k !== -1; k = prev.get(k)!)
    cells.unshift([k % cols, Math.floor(k / cols)]);
  // keep only cells where the direction changes, so the stroll looks smooth
  const out: Point[] = [];
  for (let i = 1; i < cells.length; i++) {
    const last = i === cells.length - 1;
    const turn =
      !last &&
      (cells[i + 1][0] - cells[i][0] !== cells[i][0] - cells[i - 1][0] ||
        cells[i + 1][1] - cells[i][1] !== cells[i][1] - cells[i - 1][1]);
    if (last || turn) out.push(toPoint(cells[i][0], cells[i][1]));
  }
  return out;
}

function randomSpot(near: Point, radius: number): Point {
  for (let i = 0; i < 30; i++) {
    const p = {
      x: near.x + (Math.random() * 2 - 1) * radius,
      y: near.y + (Math.random() * 2 - 1) * radius * 0.7,
    };
    const { cx, cy } = toCell(p);
    if (walkable(cx, cy)) return p;
  }
  return near;
}

const companionSpots: Point[] = [
  { x: 74, y: 150 },
  { x: 160, y: 104 },
  { x: 30, y: 108 },
];

const lines: Partial<Record<Action, string>> = {
  pond: 'a frog said hi. we are friends now.',
};

// ---- crisp sprite --------------------------------------------------------
function Sprite({
  source,
  x,
  y,
  w,
  h,
  scale,
  z,
}: {
  source: ImageSourcePropType;
  x: number;
  y: number;
  w: number;
  h: number;
  scale: number;
  z: number;
}) {
  return (
    <Image
      source={source}
      resizeMode="stretch"
      style={{
        position: 'absolute',
        left: Math.round(x * scale),
        top: Math.round(y * scale),
        width: Math.round(w * scale),
        height: Math.round(h * scale),
        zIndex: z,
      }}
    />
  );
}

// ---- ambient life (own clock, so only this layer re-renders) --------------
function Ambient({
  scale,
  width,
  height,
  rain,
  night,
  day,
  reduced,
}: {
  scale: number;
  width: number;
  height: number;
  rain: boolean;
  night: boolean;
  day: boolean;
  reduced: boolean;
}) {
  const [t, setT] = useState(0);
  useEffect(() => {
    if (reduced) return undefined;
    const timer = setInterval(() => setT((v) => v + 1), 110);
    return () => clearInterval(timer);
  }, [reduced]);
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
        x: 30 + ((i * 47) % 140) + Math.sin(t / 14 + i) * 8,
        y: 70 + ((i * 29) % 80) + Math.cos(t / 17 + i * 2) * 6,
        on: (t + i * 5) % 22 < 14,
      }))
    : [];
  const butterflies = day
    ? [0, 1].map((i) => ({
        x: 142 + Math.cos(t / 18 + i * 3) * (16 + i * 6),
        y: 112 + Math.sin(t / 11 + i * 2) * 9 - 6,
        flap: (t + i) % 4 < 2,
        color: i ? '#F2D16B' : '#CFC4EC',
      }))
    : [];
  return (
    <View
      pointerEvents="none"
      style={{ position: 'absolute', left: 0, top: 0, width, height, zIndex: 950 }}
    >
      {drops.map((d) => (
        <View
          key={d.i}
          style={{
            position: 'absolute',
            left: Math.round(d.x * scale),
            top: Math.round(d.y * scale),
            width: u,
            height: u * 4,
            backgroundColor: 'rgba(214,232,244,0.75)',
          }}
        />
      ))}
      {flies.map((f, i) =>
        f.on ? (
          <View
            key={i}
            style={{
              position: 'absolute',
              left: Math.round(f.x * scale) - u,
              top: Math.round(f.y * scale) - u,
              width: u * 3,
              height: u * 3,
              borderRadius: u * 2,
              backgroundColor: 'rgba(246,231,140,0.35)',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <View style={{ width: u, height: u, backgroundColor: '#FFF4B0' }} />
          </View>
        ) : null,
      )}
      {butterflies.map((b, i) => (
        <View
          key={i}
          style={{
            position: 'absolute',
            left: Math.round(b.x * scale),
            top: Math.round(b.y * scale),
            flexDirection: 'row',
            alignItems: 'center',
          }}
        >
          <View style={{ width: u * 2, height: b.flap ? u * 3 : u, backgroundColor: b.color }} />
          <View style={{ width: u, height: u * 2, backgroundColor: '#2A2421' }} />
          <View style={{ width: u * 2, height: b.flap ? u * 3 : u, backgroundColor: b.color }} />
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
}: {
  width: number;
  player: Player;
  grumpy: boolean;
  sleepy: boolean;
  onFeed?: () => void;
  /** Night garden for the nap screen: pet asleep in its bed, no interaction. */
  napping?: boolean;
}) {
  const reduced = useReducedMotion();
  const scale = width / GARDEN.width;
  const height = Math.round(GARDEN.height * scale);
  const petPx = Math.max(32, Math.round((32 * scale) / 32) * 32); // matches Pet's snapping
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
  const busy = useRef(false);
  const lastTouch = useRef(0);
  const journeyId = useRef(0);
  const journey = useRef<{ id: number; action: Action | null; end: Point } | null>(null);
  const napTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(
    () => () => {
      journeyId.current += 1;
      journey.current = null;
      cancelAnimation(px);
      cancelAnimation(py);
      if (napTimer.current) clearTimeout(napTimer.current);
    },
    [px, py],
  );

  // grass sway + water shimmer: alternate the two ground frames
  useEffect(() => {
    if (reduced) return undefined;
    const t = setInterval(() => setFrame((f) => 1 - f), 750);
    return () => clearInterval(t);
  }, [reduced]);

  useEffect(() => {
    if (!tag) return undefined;
    const t = setTimeout(() => setTag(null), 1800);
    return () => clearTimeout(t);
  }, [tag]);
  useEffect(() => {
    if (!emote) return undefined;
    const t = setTimeout(() => setEmote(null), 1400);
    return () => clearTimeout(t);
  }, [emote]);

  function arrived(id: number, action: Action | null, point: Point) {
    if (id !== journeyId.current || journey.current?.id !== id) return;
    journey.current = null;
    pos.current = point;
    setWalking(false);
    busy.current = false;
    if (action) act(action);
  }

  function walkTo(target: Point, action: Action | null = null) {
    if (napping) return;
    const id = ++journeyId.current;
    cancelAnimation(px);
    cancelAnimation(py);
    if (napTimer.current) clearTimeout(napTimer.current);
    // Retarget from the displayed position, including a stroll interrupted mid-leg.
    const start = { x: px.get(), y: py.get() };
    pos.current = start;
    const path = findPath(start, target);
    const end = path[path.length - 1] ?? start;
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
    if (!p || napping || p.mode !== 'awake') return;
    void Haptics.selectionAsync();
    switch (action) {
      case 'nap':
        setEmote('z');
        napTimer.current = setTimeout(() => useGame.getState().sleep(), reduced ? 0 : 500);
        break;
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
        useGame.setState({ voice: lines.pond ?? null });
        setEmote('!');
        break;
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
    if (!reduced) return undefined;
    // An OS/app preference change also stops a stroll that was already in flight.
    const timer = setTimeout(() => {
      const pending = journey.current;
      if (!pending) return;
      cancelAnimation(px);
      cancelAnimation(py);
      px.set(pending.end.x);
      py.set(pending.end.y);
      arriveRef.current(pending.id, pending.action, pending.end);
    }, 0);
    return () => clearTimeout(timer);
  }, [reduced, px, py]);
  useEffect(() => {
    if (reduced || sleepy || napping) return undefined;
    let timer: ReturnType<typeof setTimeout>;
    const tick = () => {
      if (!busy.current && clock() - lastTouch.current > 6000) {
        const roll = Math.random();
        if (roll < 0.5) walkRef.current(randomSpot(pos.current, 40));
        else if (roll < 0.7) {
          walkRef.current({ x: 142, y: 130 });
          setTimeout(() => setEmote('♪'), 2500);
        } else if (roll < 0.8) setEmote(grumpy ? '…' : '♪');
      }
      timer = setTimeout(tick, 4000 + Math.random() * 4000);
    };
    timer = setTimeout(tick, 2500);
    return () => clearTimeout(timer);
  }, [reduced, sleepy, grumpy, napping]);

  const petStyle = useAnimatedStyle(() => ({
    transform: [
      { translateX: Math.round(px.value * scale - petPx / 2) },
      { translateY: Math.round(py.value * scale - petPx * (30 / 32)) },
    ],
    // Rest between the hut and bedding layers, under the garden's night light.
    zIndex: Math.round(py.value) + (napping ? 1 : 0),
  }));

  function onGroundPress(e: { nativeEvent: { locationX: number; locationY: number } }) {
    lastTouch.current = clock();
    walkTo({ x: e.nativeEvent.locationX / scale, y: e.nativeEvent.locationY / scale });
  }

  function onObjectPress(action: Action) {
    lastTouch.current = clock();
    const spot = gardenHotspots[action];
    setTag({ text: spot.label, x: spot.x, y: spot.y });
    walkTo({ x: spot.x, y: spot.y }, action);
  }

  const guardian = guardianPlayer(player);
  const companions = collectionOf(player)
    .filter((v) => v.befriendedAt !== null && v.id !== player.guardian)
    .slice(0, 3);
  return (
    <View
      // @ts-expect-error dataSet is a react-native-web prop (sets data-pixel for crisp CSS scaling)
      dataSet={{ pixel: 'true' }}
      pointerEvents={napping ? 'none' : 'auto'}
      // A nap garden is scenery: pointer-events alone still allows web keyboard focus.
      {...(Platform.OS === 'web' ? { inert: napping } : {})}
      aria-hidden={napping}
      accessibilityElementsHidden={napping}
      importantForAccessibility={napping ? 'no-hide-descendants' : 'auto'}
      style={{ width, height, overflow: 'hidden', backgroundColor: '#62A853', zIndex: 0 }}
    >
      <Pressable
        accessibilityLabel={`Your garden. Tap to walk ${guardian.pet_name} around.`}
        onPress={onGroundPress}
        style={{ position: 'absolute', left: 0, top: 0, width, height }}
      >
        <Image source={frame ? ground1 : ground0} resizeMode="stretch" style={{ width, height }} />
      </Pressable>
      {gardenObjects.map((o) => {
        const sprite = (
          <Sprite
            key={o.id}
            source={sprites[o.sprite]}
            x={o.x}
            y={o.y}
            w={o.w}
            h={o.h}
            scale={scale}
            z={o.y + o.h}
          />
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
        const artLeft = Math.round(o.x * scale);
        const artTop = Math.round(o.y * scale);
        const artWidth = Math.round(o.w * scale);
        const artHeight = Math.round(o.h * scale);
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
        return (
          <Pressable
            key={o.id}
            accessibilityRole="button"
            accessibilityLabel={gardenHotspots[action].label}
            disabled={napping}
            onFocus={() => setTag({ text: gardenHotspots[action].label, x: o.x + o.w / 2, y: o.y })}
            onPress={() => onObjectPress(action)}
            style={{
              position: 'absolute',
              left: targetLeft,
              top: targetTop,
              width: targetWidth,
              height: targetHeight,
              zIndex: o.y + o.h,
            }}
          >
            <Image
              source={sprites[o.sprite]}
              resizeMode="stretch"
              style={{
                position: 'absolute',
                left: artLeft - targetLeft,
                top: artTop - targetTop,
                width: artWidth,
                height: artHeight,
              }}
            />
          </Pressable>
        );
      })}
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Look into the pond"
        onPress={() => onObjectPress('pond')}
        style={{
          position: 'absolute',
          left: Math.round(16 * scale),
          top: Math.round(118 * scale),
          width: Math.round(52 * scale),
          height: Math.round(30 * scale),
          zIndex: 1,
        }}
      />
      <Animated.View
        style={[{ position: 'absolute', left: 0, top: 0, width: petPx, height: petPx }, petStyle]}
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
          player={player}
          size={petPx}
          facing={facing}
          walking={walking && !napping}
          grumpy={grumpy && !napping}
          yawning={sleepy}
          sleeping={napping}
          curled={napping}
          groundShadow={!napping}
          bob={!walking && !napping}
          onPress={() => {
            lastTouch.current = clock();
            useGame.setState({ voice: grumpy ? 'hmph. ok. one pat.' : 'hehe. again.' });
          }}
        />
      </Animated.View>
      {companions.map((v, i) => (
        <View
          key={v.id}
          style={{
            position: 'absolute',
            left: Math.round(companionSpots[i].x * scale - petPx / 4),
            top: Math.round(companionSpots[i].y * scale - petPx / 2),
            zIndex: companionSpots[i].y,
          }}
        >
          <Pet
            visitor={v.id}
            size={Math.max(32, petPx / 2)}
            sleeping={napping}
            facing={i % 2 ? 'left' : 'right'}
            bob={!napping}
            onPress={() =>
              useGame.setState({
                voice: `${visitorInfo(v.id).name.toLowerCase()} waves a leaf at you.`,
              })
            }
          />
        </View>
      ))}
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
      {night &&
        [
          { x: 48, y: 54, size: 8 },
          { x: 124, y: 71, size: 7 },
        ].map((light) => (
          <View
            key={`${light.x}-${light.y}`}
            pointerEvents="none"
            style={{
              position: 'absolute',
              left: Math.round(light.x * scale),
              top: Math.round(light.y * scale),
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
        width={width}
        height={height}
        rain={grumpy && !napping}
        night={night}
        day={!night && !grumpy}
        reduced={reduced}
      />
      {napping && (
        <View
          pointerEvents="none"
          style={{
            position: 'absolute',
            left: Math.round(BED.x * scale),
            top: Math.round(BED.y * scale - petPx * 1.1),
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
            left: Math.max(4, Math.min(width - 160, tag.x * scale - 80)),
            top: Math.max(4, tag.y * scale - 70),
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
    </View>
  );
}
