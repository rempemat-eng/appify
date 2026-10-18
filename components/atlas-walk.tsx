import { Fragment, useEffect, useMemo, useRef, useState } from 'react';
import {
  Image,
  PixelRatio,
  Pressable,
  View,
  useWindowDimensions,
  type GestureResponderEvent,
  type ImageSourcePropType,
} from 'react-native';
import Animated, {
  cancelAnimation,
  Easing,
  runOnJS,
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withSequence,
  withTiming,
  type SharedValue,
} from 'react-native-reanimated';
import { useReducedMotion } from '@/lib/motion';
import { useAppActive } from '@/lib/app-active';
import { useGame } from '@/lib/game';
import { gardenAnchors, gardenObjects } from '@/lib/garden-map';
import { makeWalkGrid, type Point } from '@/lib/garden-path';
import { pixelScale, snapToDevice } from '@/lib/pixel-scale';
import {
  TILE,
  regionBounds,
  regionTiles,
  regionWalk,
  tileAt,
  tileOrigin,
  type RegionId,
  type RegionTile,
  type TileId,
} from '@/lib/region-walk';
import { zoneFrames, zoneMaps, zoneOverhead, zoneWindows } from '@/lib/zone-maps';
import { BEYOND_SPILL, zoneBeyond, zoneGrounds, zoneProps } from '@/lib/zone-assets';
import { GuardianPet } from '@/components/guardian-pet';
import { ZoneLife, ZoneResidents } from '@/components/atlas-life';
import { Pet } from '@/components/game-ui';
import { BodyText } from '@/components/pixel-feedback';
import { PixelFrame } from '@/components/pixel-frame';
import gardenGround from '@/assets/garden/ground.png';
import gStream from '@/assets/garden/water-stream-0.png';
import gPond from '@/assets/garden/water-pond-0.png';
import gTree from '@/assets/garden/tree.png';
import gTreeSmall from '@/assets/garden/tree_small.png';
import gTreeAutumn from '@/assets/garden/tree_autumn.png';
import gPine from '@/assets/garden/pine.png';
import gHut from '@/assets/garden/hut.png';
import gBed from '@/assets/garden/bed.png';
import gMailbox from '@/assets/garden/mailbox.png';
import gStall from '@/assets/garden/stall.png';
import gSignpost from '@/assets/garden/signpost.png';
import gBowl from '@/assets/garden/bowl.png';
import gBush from '@/assets/garden/bush.png';
import gRock0 from '@/assets/garden/rock0.png';
import gRock1 from '@/assets/garden/rock1.png';
import gFenceL from '@/assets/garden/fence_l.png';
import gFenceR from '@/assets/garden/fence_r.png';
import gGate from '@/assets/garden/gate.png';
import gNook from '@/assets/garden/reading_nook.png';
import gCan from '@/assets/garden/watering_can.png';
import gLantern from '@/assets/garden/lantern.png';
import gMeadowSign from '@/assets/garden/meadow_sign.png';
import gPot from '@/assets/garden/potted_plant.png';
import gBarrel from '@/assets/garden/barrel.png';
import gCrate from '@/assets/garden/crate.png';
import gSack from '@/assets/garden/sack.png';

// The garden as one tile of the valley: its ground, still water and props (its
// growing beds and hotspots belong to the real garden screen, not this walk).
const gardenSprites: Record<string, ImageSourcePropType> = {
  tree: gTree,
  tree_small: gTreeSmall,
  tree_autumn: gTreeAutumn,
  pine: gPine,
  hut: gHut,
  bed: gBed,
  mailbox: gMailbox,
  stall: gStall,
  signpost: gSignpost,
  bowl: gBowl,
  bush: gBush,
  rock0: gRock0,
  rock1: gRock1,
  fence_l: gFenceL,
  fence_r: gFenceR,
  gate: gGate,
  reading_nook: gNook,
  watering_can: gCan,
  lantern: gLantern,
  meadow_sign: gMeadowSign,
  potted_plant: gPot,
  barrel: gBarrel,
  crate: gCrate,
  sack: gSack,
};

export const zoneNames: Record<TileId, string> = {
  garden: 'HOME GARDEN',
  ridge: 'THE SNOWY RIDGE',
  halt: 'VALLEY HALT',
  oasis: 'THE DESERT OASIS',
  skyport: 'THE SKYPORT',
  canal: 'COGSWORTH CANAL',
  springs: 'CINDER SPRINGS',
  home: 'THE NAP HUT',
  woodland: 'THE WOODLAND',
  riverside: 'THE RIVERSIDE',
  town: 'CROSSROADS TOWN',
  park: 'TOWN PARK',
  harbour: 'DRIFTWOOD HARBOUR',
  castle: 'HEARTHOLD CASTLE',
  junction: 'COGSWORTH JUNCTION',
  gulch: 'DUST GULCH',
  caldera: 'EMBER CALDERA',
  neon: 'NEON HARBOUR',
  station: 'HALCYON STATION',
  lumen: 'LUMEN',
};

const SPEED = 40; // art pixels per second, a brisk walk
// Zones that keep their own light at every hour (no night tint).
const OWN_LIGHT: TileId[] = ['neon', 'skyport', 'station', 'lumen', 'caldera', 'springs', 'home'];
// Where a lamp's light sits on its sprite (x, y from its top-left, in art pixels).
const LAMPS: Record<string, readonly [number, number]> = {
  lamp: [7, 8],
  gas_lamp: [8, 9],
  street_light: [12, 8],
  lantern: [7, 10],
  lighthouse: [22, 20],
  fire_pit: [10, 8],
  stone_lantern: [8, 10],
  foundry: [72, 84],
  tube_station: [38, 30],
  campfire: [13, 10],
};
const NAME_MS = 2200; // how long a zone's name stays up after crossing into it

type Drawable = {
  key: string;
  sprite: string;
  src: ImageSourcePropType;
  x: number;
  y: number;
  w: number;
  h: number;
  z: number;
};

// Things afloat ride the water: up and down by one art pixel, each on its own phase.
const FLOATS: Record<string, number> = {
  boat_blue: 3400,
  boat_red: 3800,
  sailboat: 4200,
  narrowboat: 5200,
  ferry: 4600,
  buoy: 2600,
};
const FLOAT_LOOP = 36000; // the shared clock's loop; every period divides it

function Floating({
  d,
  clock,
  u,
  snap,
}: {
  d: Drawable;
  clock: SharedValue<number>;
  u: number;
  snap: (v: number) => number;
}) {
  const period = FLOATS[d.sprite] ?? 4000;
  const phase = (d.x * 7 + d.y * 3) % period;
  const style = useAnimatedStyle(() => ({
    transform: [
      {
        translateY: Math.round(Math.sin(((clock.value + phase) / period) * 2 * Math.PI) * 1) * u,
      },
    ],
  }));
  return (
    <Animated.Image
      source={d.src}
      resizeMode="stretch"
      style={[
        {
          position: 'absolute',
          left: snap(d.x * u),
          top: snap(d.y * u),
          width: snap(d.w * u),
          height: snap(d.h * u),
          zIndex: d.z,
        },
        style,
      ]}
    />
  );
}

// Things that turn (a windmill's sails): the sprite and its frames, one shown at a time.
const FRAME_MS = 400; // divides FLOAT_LOOP

function TurningFrame({
  src,
  index,
  count,
  clock,
  style,
}: {
  src: ImageSourcePropType;
  index: number;
  count: number;
  clock: SharedValue<number>;
  style: object;
}) {
  const shown = useAnimatedStyle(() => ({
    opacity: Math.floor(clock.value / FRAME_MS) % count === index ? 1 : 0,
  }));
  return <Animated.Image source={src} resizeMode="stretch" style={[style, shown]} />;
}

function Turning({
  d,
  clock,
  u,
  snap,
}: {
  d: Drawable;
  clock: SharedValue<number>;
  u: number;
  snap: (v: number) => number;
}) {
  const frames = zoneFrames[d.sprite] ?? [];
  const all: [string, ImageSourcePropType, number, number, number, number][] = [
    [d.sprite, d.src, 0, 0, d.w, d.h],
    ...frames.map(
      ([key, dx, dy, w, h]) =>
        [key, zoneProps[key] ?? d.src, dx, dy, w, h] as [
          string,
          ImageSourcePropType,
          number,
          number,
          number,
          number,
        ],
    ),
  ];
  return (
    <>
      {all.map(([name, src, dx, dy, w, h], i) => (
        <TurningFrame
          key={`${d.key}-${name}`}
          src={src}
          index={i}
          count={all.length}
          clock={clock}
          style={{
            position: 'absolute',
            left: snap((d.x + dx) * u),
            top: snap((d.y + dy) * u),
            width: snap(w * u),
            height: snap(h * u),
            zIndex: d.z,
          }}
        />
      ))}
    </>
  );
}

function tileDrawables(region: RegionId, tile: RegionTile): Drawable[] {
  const o = tileOrigin(region, tile);
  if (tile.id === 'garden') {
    return gardenObjects
      .filter((g) => gardenSprites[g.sprite])
      .map((g) => ({
        key: `garden-${g.id}`,
        sprite: g.sprite,
        src: gardenSprites[g.sprite],
        x: o.x + g.x,
        y: o.y + g.y,
        w: g.w,
        h: g.h,
        z: o.y + g.y + g.h,
      }));
  }
  return zoneMaps[tile.id].objects.map(([id, sprite, x, y, w, h]) => ({
    key: `${tile.id}-${id}`,
    sprite,
    src: zoneProps[sprite],
    x: o.x + x,
    y: o.y + y,
    w,
    h,
    z: zoneOverhead.includes(sprite) ? 100000 : o.y + y + h,
  }));
}

/** A name tag in the world: a place you can pick or walk to. */
export type WorldMarker = { id: string; x: number; y: number; label: string; selected?: boolean };

/**
 * A walk across a whole region with no cuts between zones (world-atlas.md, "Seamless
 * travel"; living-world plan W1). The camera follows across zone borders, only the
 * zones round the companion are mounted, and a zone's name shows as you cross into it.
 * Interactive, a tap walks there; otherwise the parent moves the companion with
 * `target` (the missions map). Walking only reports where the companion is
 * (`onZone`, `onSettle`): it grants nothing and costs nothing.
 */
export function AtlasWalk({
  region = 'valley',
  width,
  height,
  start,
  target,
  interactive = true,
  markers,
  onMarker,
  onZone,
  onSettle,
  maxWalkMs,
  showName = true,
  focusY = 0.55,
  padBottom = 0,
}: {
  region?: RegionId;
  width: number;
  height: number;
  /** where the companion stands first, in region pixels */
  start?: Point;
  /** walk here when `key` changes */
  target?: { point: Point; key: number };
  interactive?: boolean;
  markers?: WorldMarker[];
  onMarker?: (id: string) => void;
  onZone?: (zone: TileId) => void;
  /** where a walk ended (or stopped) */
  onSettle?: (at: Point) => void;
  /** squeeze a long walk into this many milliseconds (the missions map) */
  maxWalkMs?: number;
  showName?: boolean;
  /** where the companion sits down the window (0 top, 1 bottom) */
  focusY?: number;
  /** let the camera look past the region's bottom edge by this much (a card over the view) */
  padBottom?: number;
}) {
  const reduced = useReducedMotion();
  const active = useAppActive();
  const player = useGame((s) => s.player);
  const hour = new Date(useGame((s) => s.now)).getHours();
  const night = hour < 6 || hour >= 21;
  const screen = useWindowDimensions();
  const dpr = PixelRatio.get();
  const u = pixelScale(screen.width, dpr);
  const snap = (v: number) => snapToDevice(v, dpr);
  const bounds = regionBounds(region);
  const tiles = useMemo(() => regionTiles(region), [region]);
  // the start is read once (a moved start never teleports a walk under way)
  const [initial] = useState(start);
  const grid = useMemo(() => {
    const garden = tiles.find((t) => t.id === 'garden');
    const g0 = garden ? tileOrigin(region, garden) : { x: 0, y: 0 };
    const startTile = garden ?? tiles[0];
    const first = initial
      ? initial
      : startTile.id === 'garden'
        ? { x: g0.x + gardenAnchors.start.x, y: g0.y + gardenAnchors.start.y }
        : (() => {
            const o = tileOrigin(region, startTile);
            const [sx, sy] = Object.values(zoneMaps[startTile.id].stands)[0];
            return { x: o.x + sx, y: o.y + sy };
          })();
    return {
      start: first,
      walk: makeWalkGrid(regionWalk(region), {
        cell: TILE.cell,
        width: bounds.width,
        start: first,
      }),
    };
  }, [region, tiles, bounds.width, initial]);

  const px = useSharedValue(grid.start.x);
  const py = useSharedValue(grid.start.y);
  const landing = useSharedValue(0);
  // one slow clock for everything afloat; still with reduced motion or an inactive screen
  const bob = useSharedValue(0);
  useEffect(() => {
    if (!active || reduced) {
      cancelAnimation(bob);
      return undefined;
    }
    bob.set(0);
    bob.set(
      withRepeat(withTiming(FLOAT_LOOP, { duration: FLOAT_LOOP, easing: Easing.linear }), -1),
    );
    return () => cancelAnimation(bob);
  }, [active, reduced, bob]);
  const pos = useRef<Point>({ ...grid.start });
  const [walking, setWalking] = useState(false);
  const [facing, setFacing] = useState<'left' | 'right'>('right');
  const [here, setHere] = useState<TileId>(
    tileAt(region, grid.start.x, grid.start.y)?.id ?? 'garden',
  );
  const [named, setNamed] = useState<TileId | null>(here);

  // Show a zone's name for a moment after crossing into it: noticed during render
  // (React's pattern for reacting to a changed value), cleared by a timer.
  const [shownFor, setShownFor] = useState<TileId>(here);
  if (shownFor !== here) {
    setShownFor(here);
    setNamed(here);
  }
  useEffect(() => {
    if (!named) return undefined;
    const t = setTimeout(() => setNamed(null), NAME_MS);
    return () => clearTimeout(t);
  }, [named]);

  // While walking, check which zone the companion is in a few times a second (JS
  // side, so the mounted zones follow it across borders).
  useEffect(() => {
    if (!walking) return undefined;
    const t = setInterval(() => {
      const tile = tileAt(region, px.get(), py.get());
      if (tile) setHere(tile.id);
    }, 150);
    return () => clearInterval(t);
  }, [walking, region, px, py]);

  // The parent's callbacks, read through a ref so a new closure never restarts a walk.
  const calls = useRef({ onZone, onSettle });
  useEffect(() => {
    calls.current = { onZone, onSettle };
  });
  useEffect(() => {
    calls.current.onZone?.(here);
  }, [here]);

  // Leaving the screen stops the walk where it is: no stale arrival later.
  useEffect(() => {
    if (active) return;
    cancelAnimation(px);
    cancelAnimation(py);
    pos.current = { x: px.get(), y: py.get() };
    calls.current.onSettle?.(pos.current);
  }, [active, px, py]);

  const walkTo = (goal: Point) => {
    cancelAnimation(px);
    cancelAnimation(py);
    const from0 = { x: px.get(), y: py.get() };
    pos.current = from0;
    const path = grid.walk.findPath(from0, goal);
    if (!path.length) return;
    const end = path[path.length - 1];
    setFacing(end.x < from0.x ? 'left' : 'right');
    setWalking(true);
    let length = 0;
    let prev = from0;
    for (const p of path) {
      length += Math.hypot(p.x - prev.x, p.y - prev.y);
      prev = p;
    }
    // a long walk on the missions map is squeezed into a moment
    const squeeze = maxWalkMs ? Math.min(1, maxWalkMs / Math.max(1, (length / SPEED) * 1000)) : 1;
    let from = from0;
    const xs: number[] = [];
    const ys: number[] = [];
    path.forEach((p, i) => {
      const duration = Math.max(
        squeeze < 1 ? 8 : 60,
        (Math.hypot(p.x - from.x, p.y - from.y) / SPEED) * 1000 * squeeze,
      );
      // set off gently and slow into the last step (anticipate, act, settle); level between
      const first = i === 0;
      const last = i === path.length - 1;
      const easing =
        first && last
          ? Easing.inOut(Easing.quad)
          : first
            ? Easing.in(Easing.quad)
            : last
              ? Easing.out(Easing.quad)
              : Easing.linear;
      xs.push(withTiming(p.x, { duration: first || last ? duration * 1.25 : duration, easing }));
      ys.push(withTiming(p.y, { duration: first || last ? duration * 1.25 : duration, easing }));
      from = p;
    });
    const arrive = () => {
      pos.current = end;
      setWalking(false);
      if (!reduced && active) {
        // a small squash as the feet settle, then still
        landing.set(
          withSequence(withTiming(1, { duration: 90 }), withTiming(0, { duration: 170 })),
        );
      }
      const tile = tileAt(region, end.x, end.y);
      if (tile) setHere(tile.id);
      calls.current.onSettle?.(end);
    };
    px.set(withSequence(...xs));
    py.set(
      withSequence(
        ...ys,
        withTiming(end.y, { duration: 0 }, (finished) => {
          if (finished) runOnJS(arrive)();
        }),
      ),
    );
  };

  // The parent moves the companion by giving a new target key.
  const walkRef = useRef(walkTo);
  useEffect(() => {
    walkRef.current = walkTo;
  });
  const targetKey = target?.key;
  const targetPoint = useRef(target?.point);
  useEffect(() => {
    targetPoint.current = target?.point;
  });
  useEffect(() => {
    if (targetKey === undefined || !targetPoint.current) return;
    walkRef.current(targetPoint.current);
  }, [targetKey]);

  const regionW = bounds.width * u;
  const regionH = bounds.height * u;
  const petPx = 32 * u;
  const cameraStyle = useAnimatedStyle(() => {
    // a region narrower (or shorter) than the screen sits in its middle
    const cx =
      regionW <= width
        ? (regionW - width) / 2
        : Math.max(0, Math.min(regionW - width, px.value * u - width / 2));
    const cy =
      regionH <= height - padBottom
        ? (regionH - height + padBottom) / 2
        : Math.max(0, Math.min(regionH - height + padBottom, py.value * u - height * focusY));
    return { transform: [{ translateX: -Math.round(cx) }, { translateY: -Math.round(cy) }] };
  });
  const landStyle = useAnimatedStyle(() => ({
    // squash about the feet: shorter and a little wider, the bottom edge kept in place
    transform: [
      { translateY: landing.value * petPx * 0.04 },
      { scaleY: 1 - landing.value * 0.08 },
      { scaleX: 1 + landing.value * 0.05 },
    ],
  }));
  const petStyle = useAnimatedStyle(() => ({
    transform: [
      { translateX: Math.round(px.value * u - petPx / 2) },
      { translateY: Math.round(py.value * u - petPx * (30 / 32)) },
    ],
    zIndex: Math.round(py.value),
  }));

  // Mount the zone the companion is in and its neighbours (diagonals too), no more.
  const hereTile = tiles.find((t) => t.id === here) ?? tiles[0];
  // (on a wide screen the view spans more than one zone: mount as far as it can see)
  const reachX = 1 + Math.ceil(width / (2 * TILE.width * u));
  const reachY = 1 + Math.ceil(height / (2 * TILE.height * u));
  const near = tiles.filter(
    (t) => Math.abs(t.col - hereTile.col) <= reachX && Math.abs(t.row - hereTile.row) <= reachY,
  );
  const gaps: { col: number; row: number }[] = [];
  for (let col = hereTile.col - reachX; col <= hereTile.col + reachX; col++)
    for (let row = hereTile.row - reachY; row <= hereTile.row + reachY; row++) {
      const inside =
        col >= bounds.minCol &&
        row >= bounds.minRow &&
        col < bounds.minCol + bounds.tileCols &&
        row < bounds.minRow + bounds.tileRows;
      if (inside && !tiles.some((t) => t.col === col && t.row === row)) gaps.push({ col, row });
    }
  const drawables = near.flatMap((t) => tileDrawables(region, t));
  const panes = !night
    ? []
    : drawables.flatMap((d) =>
        (zoneWindows[d.sprite] ?? []).map(([wx, wy, ww, wh]) => {
          const x = d.x + wx;
          const y = d.y + wy;
          const clear = !drawables.some(
            (o) =>
              o !== d &&
              o.z > d.z &&
              o.x < x + ww &&
              o.x + o.w > x &&
              o.y < y + wh &&
              o.y + o.h > y,
          );
          return { key: `pane-${d.key}-${wx}-${wy}`, x, y, w: ww, h: wh, z: d.z, clear };
        }),
      );

  const onPress = (e: GestureResponderEvent) => {
    // react-native-web reports the press position on the overlay as offsetX/offsetY
    const ne = e.nativeEvent as typeof e.nativeEvent & { offsetX?: number; offsetY?: number };
    const locationX = ne.locationX ?? ne.offsetX ?? 0;
    const locationY = ne.locationY ?? ne.offsetY ?? 0;
    const cx =
      regionW <= width
        ? (regionW - width) / 2
        : Math.max(0, Math.min(regionW - width, px.get() * u - width / 2));
    const cy =
      regionH <= height - padBottom
        ? (regionH - height + padBottom) / 2
        : Math.max(0, Math.min(regionH - height + padBottom, py.get() * u - height * focusY));
    walkTo({ x: (locationX + cx) / u, y: (locationY + cy) / u });
  };

  return (
    <View style={{ width, height, overflow: 'hidden', backgroundColor: '#2F4630' }}>
      <View pointerEvents="none" style={{ position: 'absolute', left: 0, top: 0, width, height }}>
        <Animated.View
          // @ts-expect-error dataSet is a react-native-web prop (crisp pixel scaling via CSS)
          dataSet={{ pixel: 'true' }}
          style={[
            { position: 'absolute', left: 0, top: 0, width: regionW, height: regionH },
            cameraStyle,
          ]}
        >
          {/* old forest where the region's grid has no zone (the valley's corners) */}
          {gaps.map((g) => (
            <Image
              key={`beyond-${g.col}-${g.row}`}
              source={zoneBeyond}
              resizeMode="stretch"
              style={{
                // its crowns spill over the zones beside it (above their ground, under their props)
                position: 'absolute',
                left: snap(((g.col - bounds.minCol) * TILE.width - BEYOND_SPILL) * u),
                top: snap(((g.row - bounds.minRow) * TILE.height - BEYOND_SPILL) * u),
                width: snap((TILE.width + 2 * BEYOND_SPILL) * u),
                height: snap((TILE.height + 2 * BEYOND_SPILL) * u),
                zIndex: 1,
              }}
            />
          ))}
          {near.map((t) => {
            const o = tileOrigin(region, t);
            const left = snap(o.x * u);
            const top = snap(o.y * u);
            const w = snap(TILE.width * u);
            const h = snap(TILE.height * u);
            return (
              <View
                key={`ground-${t.id}`}
                style={{ position: 'absolute', left, top, width: w, height: h }}
              >
                <Image
                  source={t.id === 'garden' ? gardenGround : zoneGrounds[t.id]}
                  resizeMode="stretch"
                  style={{ position: 'absolute', left: 0, top: 0, width: w, height: h }}
                />
                {t.id === 'garden' && (
                  <>
                    <Image
                      source={gStream}
                      resizeMode="stretch"
                      style={{
                        position: 'absolute',
                        left: 0,
                        top: snap(282 * u),
                        width: w,
                        height: snap(38 * u),
                      }}
                    />
                    <Image
                      source={gPond}
                      resizeMode="stretch"
                      style={{
                        position: 'absolute',
                        left: snap(22 * u),
                        top: snap(186 * u),
                        width: snap(96 * u),
                        height: snap(56 * u),
                      }}
                    />
                  </>
                )}
              </View>
            );
          })}
          {drawables.map((d) =>
            FLOATS[d.sprite] && active && !reduced ? (
              <Floating key={d.key} d={d} clock={bob} u={u} snap={snap} />
            ) : zoneFrames[d.sprite] && active && !reduced ? (
              <Turning key={d.key} d={d} clock={bob} u={u} snap={snap} />
            ) : (
              <Image
                key={d.key}
                source={d.src}
                resizeMode="stretch"
                style={{
                  position: 'absolute',
                  left: snap(d.x * u),
                  top: snap(d.y * u),
                  width: snap(d.w * u),
                  height: snap(d.h * u),
                  zIndex: d.z,
                }}
              />
            ),
          )}
          {near.map((t) =>
            t.id === 'garden' ? null : (
              <Fragment key={`zone-${t.id}`}>
                <ZoneLife
                  zone={t.id}
                  left={snap(tileOrigin(region, t).x * u)}
                  top={snap(tileOrigin(region, t).y * u)}
                  u={u}
                  running={active && !reduced}
                  night={night && !OWN_LIGHT.includes(t.id)}
                />
                <ZoneResidents
                  zone={t.id}
                  left={snap(tileOrigin(region, t).x * u)}
                  top={snap(tileOrigin(region, t).y * u)}
                  u={u}
                  running={active && !reduced}
                />
              </Fragment>
            ),
          )}
          {night &&
            near
              .filter((t) => !OWN_LIGHT.includes(t.id))
              .map((t) => (
                <View
                  key={`night-${t.id}`}
                  style={{
                    position: 'absolute',
                    left: snap(tileOrigin(region, t).x * u),
                    top: snap(tileOrigin(region, t).y * u),
                    width: snap(TILE.width * u),
                    height: snap(TILE.height * u),
                    backgroundColor: 'rgba(22,28,66,0.42)',
                    zIndex: 150000,
                  }}
                />
              ))}
          {night &&
            // lamplight in the windows (panes recorded by the generator, zoneWindows): a pane
            // with nothing in front glows above the night tint; one that a nearer thing overlaps
            // stays at its building's depth (under the tint), so trees still hide it
            panes.map((p) => (
              <View
                key={p.key}
                pointerEvents="none"
                style={{
                  position: 'absolute',
                  left: snap(p.x * u),
                  top: snap(p.y * u),
                  width: snap(p.w * u),
                  height: snap(p.h * u),
                  backgroundColor: p.clear ? 'rgba(255,200,104,0.92)' : 'rgba(255,214,130,1)',
                  zIndex: p.clear ? 150001 : p.z,
                }}
              />
            ))}
          {night &&
            drawables
              .filter((d) => LAMPS[d.sprite])
              .map((d) => {
                const [lx, ly] = LAMPS[d.sprite];
                const cx = (d.x + lx) * u;
                const cy = (d.y + ly) * u;
                const foot = (d.y + d.h) * u;
                return (
                  <View
                    key={`light-${d.key}`}
                    pointerEvents="none"
                    style={{ position: 'absolute', zIndex: 150001 }}
                  >
                    <View
                      style={{
                        position: 'absolute',
                        left: cx - 14 * u,
                        top: foot - 6 * u,
                        width: 28 * u,
                        height: 12 * u,
                        borderRadius: 14 * u,
                        backgroundColor: 'rgba(255,214,122,0.22)',
                      }}
                    />
                    <View
                      style={{
                        position: 'absolute',
                        left: cx - 8 * u,
                        top: cy - 8 * u,
                        width: 16 * u,
                        height: 16 * u,
                        borderRadius: 8 * u,
                        backgroundColor: 'rgba(255,214,122,0.35)',
                      }}
                    />
                    <View
                      style={{
                        position: 'absolute',
                        left: cx - 3 * u,
                        top: cy - 3 * u,
                        width: 6 * u,
                        height: 6 * u,
                        borderRadius: 3 * u,
                        backgroundColor: 'rgba(255,240,200,0.8)',
                      }}
                    />
                  </View>
                );
              })}
          <Animated.View
            pointerEvents="none"
            style={[
              { position: 'absolute', left: 0, top: 0, width: petPx, height: petPx },
              petStyle,
            ]}
          >
            <Animated.View style={landStyle}>
              {player ? (
                <GuardianPet
                  player={player}
                  size={petPx}
                  facing={facing}
                  walking={walking && active && !reduced}
                  bob={!walking && !reduced && active}
                  active={active}
                  decorative
                />
              ) : (
                <Pet
                  size={petPx}
                  facing={facing}
                  walking={walking && !reduced}
                  active={active}
                  decorative
                />
              )}
            </Animated.View>
          </Animated.View>
        </Animated.View>
      </View>
      {/* one transparent layer takes the taps, so their position is the window's */}
      {interactive && (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`Walk around ${zoneNames[here].toLowerCase()}. Tap where to go.`}
          onPress={onPress}
          style={{ position: 'absolute', left: 0, top: 0, width, height }}
        />
      )}
      {markers && markers.length > 0 && (
        <Animated.View
          pointerEvents="box-none"
          style={[
            { position: 'absolute', left: 0, top: 0, width: regionW, height: regionH },
            cameraStyle,
          ]}
        >
          {markers.map((m) => (
            <Pressable
              key={m.id}
              disabled={!onMarker}
              accessibilityRole="button"
              accessibilityLabel={m.label}
              accessibilityState={{ selected: !!m.selected }}
              onPress={() => onMarker?.(m.id)}
              style={{
                position: 'absolute',
                left: m.x * u - 70,
                top: m.y * u - 56 * u,
                width: 140,
                minHeight: 44,
                alignItems: 'center',
                justifyContent: 'flex-end',
              }}
            >
              <PixelFrame
                tone={m.selected ? 'gold' : 'paper'}
                style={{ paddingVertical: 2 * u, paddingHorizontal: 4 * u, alignItems: 'center' }}
              >
                <BodyText
                  numberOfLines={1}
                  style={{ fontSize: 11, lineHeight: 13, fontFamily: 'PixelifySans_700Bold' }}
                >
                  {m.label}
                </BodyText>
              </PixelFrame>
            </Pressable>
          ))}
        </Animated.View>
      )}
      {showName && named && (
        <View
          pointerEvents="none"
          style={{ position: 'absolute', top: 12, left: 0, right: 0, alignItems: 'center' }}
        >
          <PixelFrame tone="paper" style={{ paddingVertical: 4 * u, paddingHorizontal: 8 * u }}>
            <BodyText style={{ fontFamily: 'PixelifySans_700Bold', fontSize: 14 }}>
              {zoneNames[named]}
            </BodyText>
          </PixelFrame>
        </View>
      )}
    </View>
  );
}

/**
 * A still window onto a place in the world (coherence plan step 10: the Shop and the
 * Arena are places): the companion standing there, the residents and life around it,
 * no walking. Measures its own width; only the zones round the place are mounted.
 */
export function WorldWindow({
  region,
  at,
  height,
}: {
  region: RegionId;
  at: Point;
  height: number;
}) {
  const [width, setWidth] = useState(0);
  return (
    <View
      onLayout={(event) => {
        const w = event.nativeEvent.layout.width;
        setWidth((old) => (Math.abs(old - w) < 0.5 ? old : w));
      }}
      style={{ height, overflow: 'hidden' }}
    >
      {width > 0 && (
        <AtlasWalk
          region={region}
          width={width}
          height={height}
          start={at}
          interactive={false}
          showName={false}
          focusY={0.62}
        />
      )}
    </View>
  );
}
