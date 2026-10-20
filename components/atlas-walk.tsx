import { Fragment, type ReactNode, useEffect, useMemo, useRef, useState } from 'react';
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
  useAnimatedReaction,
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withSequence,
  withTiming,
  type SharedValue,
} from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';
import { useReducedMotion } from '@/lib/motion';
import { cozy } from '@/lib/cozy';
import { STEP_MS, keySteps, useKeyboardWalk } from '@/lib/keyboard-walk';
import { useAppActive } from '@/lib/app-active';
import { useGame } from '@/lib/game';
import { gardenAnchors, gardenObjects } from '@/lib/garden-map';
import { makeWalkGrid, type Point } from '@/lib/garden-path';
import { pixelScale, snapToDevice } from '@/lib/pixel-scale';
import { prefetchRegion } from '@/lib/zone-prefetch';
import { WORLD_CANVAS } from '@/lib/world-flag';
import { WORLD_TILE, worldTiles } from '@/lib/world-canvas';
import { worldFlowArt, worldTileArt } from '@/lib/world-canvas-assets';
import {
  TILE_MOUNT_MARGIN,
  areaAt,
  areaWithHysteresis,
  areasNear,
  chunkFor,
  makeWorldWalk,
  propsFor,
  tileOriginOf,
  tilesToMount,
} from '@/lib/world-walk';
import { hiddenBehind } from '@/lib/occlusion';
import { hutImageKey } from '@/lib/decor';
import { hutImages } from '@/lib/garden-hut-assets';
import {
  MOUNT_MARGIN,
  TILE,
  cellsNear,
  regionBounds,
  regionTiles,
  regionLevels,
  regionWalk,
  tileOrigin,
  tileWithHysteresis,
  zonesToMount,
  ZONE_HYSTERESIS,
  type RegionId,
  type RegionTile,
  type TileId,
} from '@/lib/region-walk';
import {
  FLOW_FRAMES,
  FLOW_FRAME_MS,
  zoneDecks,
  zoneFlow,
  zoneFrames,
  zoneMaps,
  zoneOverhead,
  zoneTone,
  zoneWindows,
} from '@/lib/zone-maps';
import {
  BEYOND_SPILL,
  zoneBeyond,
  zoneBeyondAsh,
  zoneBeyondPeaks,
  zoneBeyondRegolith,
  zoneBeyondByRegion,
  zoneDeckArt,
  zoneFlowArt,
  zoneGrounds,
  zoneProps,
  zoneScenery,
} from '@/lib/zone-assets';
import { GuardianPet } from '@/components/guardian-pet';
import { ZoneLife, ZoneResidents } from '@/components/atlas-life';
import { Pet } from '@/components/game-ui';
import { BodyText } from '@/components/pixel-feedback';
import { PixelFrame, frameTones } from '@/components/pixel-frame';
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
  hollow: 'FIR HOLLOW',
  landing: 'LAGOON LANDING',
  rainforest: 'THE RAINFOREST',
  headwaters: 'THE HEADWATERS',
  cove: 'BLACK-SAND COVE',
  snowmelt: 'SNOWMELT LAKE',
  saddle: 'THE SNOW SADDLE',
  summit: 'THE HIGH LOOKOUT',
  hearthold: 'HEARTHOLD CASTLE',
  headland: 'THE HEADLAND',
  scorch: 'THE SCORCHED PASS',
  junction: 'COGSWORTH JUNCTION',
  gulch: 'DUST GULCH',
  caldera: 'EMBER CALDERA',
  neon: 'NEON HARBOUR',
  market: 'THE NIGHT MARKET',
  downtown: 'DOWNTOWN',
  heights: 'THE HEIGHTS',
  plaza: 'LANTERN PLAZA',
  waterfront: 'THE WATERFRONT',
  docks: 'THE DOCKS',
  point: 'BEACON POINT',
  station: 'HALCYON STATION',
  lumen: 'LUMEN',
};

const isTileId = (id: string | undefined): id is TileId => !!id && Object.hasOwn(zoneNames, id);
/** The place under a point, its name kept along an edge: the zone (the zones' path) or the
 *  area of the world canvas (lib/world-flag.ts; today the areas are the zones). */
function placeAt(region: RegionId, prev: TileId | undefined, x: number, y: number) {
  if (!WORLD_CANVAS) return tileWithHysteresis(region, prev, x, y)?.id;
  const area = prev
    ? areaWithHysteresis(region, prev, x, y, ZONE_HYSTERESIS)
    : areaAt(region, x, y);
  return isTileId(area?.id) ? area.id : undefined;
}

const SPEED = 40; // art pixels per second, a brisk walk
const KEY_SPEED = 52; // walking by the keys: a purposeful trot
/** Which way a leg of a walk faces; null for one that only goes up or down. */
const legFacing = (a: Point, b: Point) =>
  Math.abs(b.x - a.x) < 2 ? null : b.x < a.x ? ('left' as const) : ('right' as const);
// Zones lit by their own light on one side only: the hour's tint fades out across them
// toward that light (the Scorched Pass: Dust Gulch's night on its sandy west, the lava's
// glow on its east), so the light never stops at a tile edge (play-test 18 Oct, 1).
const FADE_LIGHT: Partial<Record<TileId, 'east'>> = { scorch: 'east' };
const clearOf = (c: string) => c.replace(/[\d.]+\)$/, '0)');
// Zones that keep their own light at every hour (no night tint).
const OWN_LIGHT: TileId[] = [
  'neon',
  'skyport',
  'market',
  'downtown',
  'heights',
  'plaza',
  'waterfront',
  'docks',
  'point',
  'station',
  'lumen',
  'caldera',
  'springs',
  'hearthold',
  'scorch',
  'home',
];
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

/** Something more standing in a scene (a keepsake): its image and box in region pixels,
 *  and its depth (its feet; 2 for a rug, which lies under everything). */
export type SceneExtra = {
  key: string;
  src: ImageSourcePropType;
  x: number;
  y: number;
  w: number;
  h: number;
  z: number;
  /** drawn mirrored (a keepsake turned to face the other way) */
  flip?: boolean;
};

type Drawable = {
  key: string;
  sprite: string;
  src: ImageSourcePropType;
  x: number;
  y: number;
  w: number;
  h: number;
  z: number;
  flip?: boolean;
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

// Moving water and lava (scripts/art/water_flow.py; Matt, 19 Oct: "water should have
// flowing animations"): one picture per zone with its frames stacked, clipped to the box
// round its water and stepped on the shared clock. The clock stops with reduced motion or
// an inactive screen, so the water holds still on its current frame.
function FlowLayer({
  zone,
  clock,
  u,
  snap,
}: {
  zone: TileId;
  clock: SharedValue<number>;
  u: number;
  snap: (v: number) => number;
}) {
  const rect = zone === 'garden' ? undefined : zoneFlow[zone];
  const art = zone === 'garden' ? undefined : zoneFlowArt[zone];
  const bh = rect ? snap(rect[3] * u) : 0;
  const style = useAnimatedStyle(() => ({
    transform: [{ translateY: -(Math.floor(clock.value / FLOW_FRAME_MS) % FLOW_FRAMES) * bh }],
  }));
  if (!rect || !art) return null;
  const [x, y, w] = rect;
  return (
    <View
      pointerEvents="none"
      style={{
        position: 'absolute',
        left: snap(x * u),
        top: snap(y * u),
        width: snap(w * u),
        height: bh,
        overflow: 'hidden',
      }}
    >
      <Animated.Image
        source={art}
        resizeMode="stretch"
        style={[
          { position: 'absolute', left: 0, top: 0, width: snap(w * u), height: bh * FLOW_FRAMES },
          style,
        ]}
      />
    </View>
  );
}

// The same moving water for one world tile (the world canvas): its box in tile pixels and
// its frames' picture (lib/world-canvas.ts worldTiles[plane][key].flow).
function FlowBox({
  rect,
  art,
  clock,
  u,
  snap,
}: {
  rect: readonly [number, number, number, number];
  art: ImageSourcePropType;
  clock: SharedValue<number>;
  u: number;
  snap: (v: number) => number;
}) {
  const [x, y, w, h] = rect;
  const bh = snap(h * u);
  const style = useAnimatedStyle(() => ({
    transform: [{ translateY: -(Math.floor(clock.value / FLOW_FRAME_MS) % FLOW_FRAMES) * bh }],
  }));
  return (
    <View
      pointerEvents="none"
      style={{
        position: 'absolute',
        left: snap(x * u),
        top: snap(y * u),
        width: snap(w * u),
        height: bh,
        overflow: 'hidden',
      }}
    >
      <Animated.Image
        source={art}
        resizeMode="stretch"
        style={[
          { position: 'absolute', left: 0, top: 0, width: snap(w * u), height: bh * FLOW_FRAMES },
          style,
        ]}
      />
    </View>
  );
}

// Things that fly (the castle's dragon; Matt, 18 Oct): with motion on, the perched
// sprite takes off and circles on the shared clock, beating its wings (its frames) and
// turning to face the way it flies, its shadow sliding over the ground below. With
// reduced motion, or off screen, it stays perched. Scenery only: it never blocks or
// grants anything. Orbit centre (dx, dy) from the perch, radii, period (divides the loop).
const FLYERS: Record<string, { dx: number; dy: number; rx: number; ry: number; period: number }> = {
  dragon: { dx: -40, dy: 96, rx: 132, ry: 92, period: 18000 },
};
const WING_MS = 300; // divides FLOAT_LOOP

function Flyer({
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
  const f = FLYERS[d.sprite];
  const frames = zoneFrames[d.sprite] ?? [];
  const fw = Math.max(...frames.map((fr) => fr[3]), d.w);
  const fh = Math.max(...frames.map((fr) => fr[4]), d.h);
  const cx = d.x + d.w / 2 + f.dx;
  const cy = d.y + d.h / 2 + f.dy;
  const body = useAnimatedStyle(() => {
    const a = (clock.value / f.period) * 2 * Math.PI;
    const x = cx + f.rx * Math.cos(a) - fw / 2;
    const y = cy + f.ry * Math.sin(a) - fh / 2;
    const right = -Math.sin(a) > 0;
    return {
      transform: [
        { translateX: Math.round(x) * u },
        { translateY: Math.round(y) * u },
        { scaleX: right ? 1 : -1 },
      ],
    };
  });
  const shadow = useAnimatedStyle(() => {
    const a = (clock.value / f.period) * 2 * Math.PI;
    return {
      transform: [
        { translateX: Math.round(cx + f.rx * Math.cos(a) - fw * 0.3) * u },
        { translateY: Math.round(cy + f.ry * Math.sin(a) + 56) * u },
      ],
    };
  });
  return (
    <>
      <Animated.View
        pointerEvents="none"
        style={[
          {
            position: 'absolute',
            left: 0,
            top: 0,
            width: snap(fw * 0.6 * u),
            height: snap(6 * u),
            borderRadius: snap(3 * u),
            backgroundColor: 'rgba(20,14,18,0.28)',
            zIndex: 2,
          },
          shadow,
        ]}
      />
      <Animated.View
        pointerEvents="none"
        style={[
          {
            position: 'absolute',
            left: 0,
            top: 0,
            width: snap(fw * u),
            height: snap(fh * u),
            zIndex: 100000,
          },
          body,
        ]}
      >
        {frames.map(([key, , , w, h], i) => (
          <TurningFrame
            key={key}
            src={zoneProps[key] ?? d.src}
            index={i}
            count={frames.length}
            clock={clock}
            ms={WING_MS}
            style={{
              position: 'absolute',
              left: snap(((fw - w) / 2) * u),
              top: snap(((fh - h) / 2) * u),
              width: snap(w * u),
              height: snap(h * u),
            }}
          />
        ))}
      </Animated.View>
    </>
  );
}

// Things that turn (a windmill's sails): the sprite and its frames, one shown at a time.
const FRAME_MS = 400; // divides FLOAT_LOOP

/** What lies past a region's zones at a grid cell: the valley's old forest; in Sunstone
 *  Reach open dunes round the desert and the volcano's flank round the fire country (the
 *  Scorched Pass and everything north and east of it). */
function beyondAt(region: RegionId, col: number, row: number) {
  // the land past the world painted for this very cell (scripts/art/scenery.py), where
  // there is one: it runs on from its neighbours without a seam
  const own = zoneScenery[`${region}:${col}:${row}`];
  if (own) return own;
  // (Sunstone: the volcano's ash flank round the fire country, desert north of the gulch)
  if (region === 'west' && (col >= 1 || (col >= 0 && row <= -2))) return zoneBeyondAsh;
  // the valley: mountains above the Frostline and the ridge, the sea past the harbour and
  // the headland, old forest east and west (Driftwood's west point meets the woods)
  if (region === 'valley' && row <= -1) return zoneBeyondPeaks;
  if (region === 'valley' && row >= 3) return zoneBeyondByRegion.isles;
  // Lumen's plain runs on below and beside it; above, only space (the backdrop)
  if (region === 'moon') return zoneBeyondRegolith;
  return zoneBeyondByRegion[region] ?? zoneBeyond;
}

/**
 * What shows past a region with no open country round it, when the screen sees past its
 * edge: the night over the city's water, space round the station and the moon, the dark
 * of the room. (The valley, the desert and the fire country draw their land instead.)
 */
const BACKDROP: Partial<Record<RegionId, string>> = {
  neon: '#100E1A',
  space: '#05060C',
  moon: '#05060C',
  home: '#1E1612',
  steam: '#2A2D36',
};

/** The companion's outline through whatever hides it: fades in, faint, never takes taps. */
function Ghost({
  px,
  py,
  ox = 0,
  oy = 0,
  u,
  size,
  reduced,
  children,
}: {
  px: SharedValue<number>;
  py: SharedValue<number>;
  ox?: number;
  oy?: number;
  u: number;
  size: number;
  reduced: boolean;
  children: ReactNode;
}) {
  const shown = useSharedValue(reduced ? GHOST : 0);
  useEffect(() => {
    if (!reduced) shown.set(withTiming(GHOST, { duration: 180, easing: Easing.out(Easing.quad) }));
    return () => cancelAnimation(shown);
  }, [reduced, shown]);
  // where the companion is drawn, without its depth (which would put this back behind)
  const style = useAnimatedStyle(() => ({
    opacity: shown.value,
    transform: [
      { translateX: Math.round((px.value + ox) * u - size / 2) },
      { translateY: Math.round((py.value + oy) * u - size * (30 / 32)) },
    ],
  }));
  return (
    <Animated.View
      pointerEvents="none"
      style={[
        { position: 'absolute', left: 0, top: 0, width: size, height: size, zIndex: 149999 },
        style,
      ]}
    >
      {children}
    </Animated.View>
  );
}
const GHOST = 0.42;

function TurningFrame({
  src,
  index,
  count,
  clock,
  style,
  ms = FRAME_MS,
}: {
  src: ImageSourcePropType;
  index: number;
  count: number;
  clock: SharedValue<number>;
  style: object;
  ms?: number;
}) {
  const shown = useAnimatedStyle(() => ({
    opacity: Math.floor(clock.value / ms) % count === index ? 1 : 0,
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

function tileDrawables(region: RegionId, tile: RegionTile, hut?: ImageSourcePropType): Drawable[] {
  const o = tileOrigin(region, tile);
  if (tile.id === 'garden') {
    return gardenObjects
      .filter((g) => gardenSprites[g.sprite])
      .map((g) => ({
        key: `garden-${g.id}`,
        sprite: g.sprite,
        // the hut as the player has made it (door colour, window boxes)
        src: g.sprite === 'hut' && hut ? hut : gardenSprites[g.sprite],
        x: o.x + g.x,
        y: o.y + g.y,
        w: g.w,
        h: g.h,
        z: o.y + g.y + g.h,
      }));
  }
  const props = zoneMaps[tile.id].objects.map(([id, sprite, x, y, w, h]) => ({
    key: `${tile.id}-${id}`,
    sprite,
    src: zoneProps[sprite],
    x: o.x + x,
    y: o.y + y,
    w,
    h,
    z: zoneOverhead.includes(sprite) ? 100000 : o.y + y + h,
  }));
  // A deck (two-level-walk.md) sorts by its front foot among the street's props: what
  // stands on the street behind it is covered; what stands on it draws above it all.
  const deck = zoneDecks[tile.id];
  const art = zoneDeckArt[tile.id];
  if (!deck || !art) return props;
  const front = deck.walk.reduce((last, row, r) => (row.includes('.') ? r : last), 0);
  return [
    ...props,
    {
      key: `${tile.id}-deck`,
      sprite: DECK,
      src: art.deck,
      x: o.x,
      y: o.y,
      w: TILE.width,
      h: TILE.height,
      z: o.y + (front + 1) * TILE.cell,
    },
  ];
}
const DECK = 'deck';

/** The props of the mounted world tiles (the world canvas): every prop whose picture
 *  reaches one of them, in region pixels, and the garden's own when it is near. */
function worldDrawables(
  region: RegionId,
  keys: readonly string[],
  zones: readonly RegionTile[],
  hut?: ImageSourcePropType,
): Drawable[] {
  const props: Drawable[] = propsFor(region, keys).map((p) => ({
    key: `w-${p.id}`,
    sprite: p.sprite,
    src: zoneProps[p.sprite],
    x: p.x,
    y: p.y,
    w: p.w,
    h: p.h,
    z: zoneOverhead.includes(p.sprite) ? 100000 : p.y + p.h,
  }));
  const garden = zones.find((t) => t.id === 'garden');
  return garden ? [...tileDrawables(region, garden, hut), ...props] : props;
}

/** The world canvas's ground (lib/world-flag.ts): the mounted world tiles, each its picture
 *  (or its one colour) and its moving water, and the garden's still water at the garden's
 *  place when the home layer is not drawing it. In region pixels, inside the camera. */
function WorldGround({
  region,
  keys,
  garden,
  clock,
  u,
  snap,
}: {
  region: RegionId;
  keys: readonly string[];
  garden: boolean;
  clock: SharedValue<number>;
  u: number;
  snap: (v: number) => number;
}) {
  const plane = chunkFor(region).plane;
  const size = snap(WORLD_TILE.size * u);
  const g = regionTiles(region).find((t) => t.id === 'garden');
  const go = g ? tileOrigin(region, g) : null;
  return (
    <>
      {keys.map((k) => {
        const t = worldTiles[plane][k];
        if (!t) return null;
        const o = tileOriginOf(region, k);
        const flow = worldFlowArt[plane][k];
        return (
          <View
            key={`tile-${k}`}
            style={{
              position: 'absolute',
              left: snap(o.x * u),
              top: snap(o.y * u),
              width: size,
              height: size,
              // a tile of one colour (open sea, deep forest) needs no picture
              backgroundColor: t.fill,
            }}
          >
            {t.art && !t.fill && (
              <Image
                source={worldTileArt[t.art]}
                resizeMode="stretch"
                style={{ position: 'absolute', left: 0, top: 0, width: size, height: size }}
              />
            )}
            {t.flow && flow && <FlowBox rect={t.flow} art={flow} clock={clock} u={u} snap={snap} />}
          </View>
        );
      })}
      {garden && go && (
        <>
          <Image
            source={gStream}
            resizeMode="stretch"
            style={{
              position: 'absolute',
              left: snap(go.x * u),
              top: snap(go.y * u) + snap(282 * u),
              width: snap(TILE.width * u),
              height: snap(38 * u),
            }}
          />
          <Image
            source={gPond}
            resizeMode="stretch"
            style={{
              position: 'absolute',
              left: snap(go.x * u) + snap(22 * u),
              top: snap(go.y * u) + snap(186 * u),
              width: snap(96 * u),
              height: snap(56 * u),
            }}
          />
        </>
      )}
    </>
  );
}

/** A name tag in the world: a place you can pick or walk to. */
/** Where the companion stands, as the parent hears it: the ground point (region pixels)
 *  under its feet, and `level` 1 when it is on a deck above that point
 *  (docs/vision/two-level-walk.md). Absent level: the ground. */
export type WalkSpot = Point & { level?: 1 };

export type WorldMarker = { id: string; x: number; y: number; label: string; selected?: boolean };

/**
 * A companion walked by the parent instead of by AtlasWalk (the home hub,
 * docs/vision/home-hub.md): its feet are (px + ox, py + oy) in region pixels. The parent
 * plans every walk; AtlasWalk draws, follows with the camera and reports the zone. When
 * `cam` is given, the camera's top-left (screen pixels in the region) is written to it, so
 * the parent's bubbles can keep inside the window.
 */
export type AtlasFollow = {
  px: SharedValue<number>;
  py: SharedValue<number>;
  ox: number;
  oy: number;
  cam?: SharedValue<{ x: number; y: number }>;
};

/** How the parent's companion looks (the home hub's emote, pose and moods). */
export type AtlasCompanion = {
  walking: boolean;
  facing: 'left' | 'right';
  grumpy?: boolean;
  yawning?: boolean;
  /** idle bobbing (the parent knows when it should rest) */
  bob?: boolean;
  pose?: { id: number; kind: 'nestle' | 'sniff' | 'ponder' };
  emote?: string | null;
};

// How long the camera eases to a new framing (a card opening or closing).
const FRAME_EASE_MS = 260;
// How often the feet are read while walking (the outline behind tall things, onMove).
const FEET_MS = 150;
// The companion's position is watched in blocks this size for zone and mount changes.
const BLOCK = 32;

/**
 * A walk across a whole region with no cuts between zones (world-atlas.md, "Seamless
 * travel"; living-world plan W1). The camera follows across zone borders, only the
 * zones the camera can see (and a margin) are mounted, and a zone's name shows as you
 * cross into it. Interactive, a tap walks there; otherwise the parent moves the companion
 * with `target` (the missions map), or walks it entirely (`follow`, the home hub).
 * Walking only reports where the companion is (`onZone`, `onSettle`): it grants nothing
 * and costs nothing.
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
  onMove,
  onSettle,
  onTap,
  walk: walkRows,
  extras,
  preview,
  maxWalkMs,
  showName = true,
  nameAtStart = true,
  nameTop = 12,
  focusY = 0.55,
  padBottom = 0,
  active: shown = true,
  follow,
  companion,
  homeLayer = false,
  scene,
  hits,
}: {
  region?: RegionId;
  width: number;
  height: number;
  /** where the companion stands first, in region pixels */
  start?: WalkSpot;
  /** walk here when `key` changes */
  target?: { point: Point; key: number };
  interactive?: boolean;
  markers?: WorldMarker[];
  onMarker?: (id: string) => void;
  onZone?: (zone: TileId) => void;
  /** Where the companion is, a few times a second while it walks. */
  onMove?: (at: WalkSpot) => void;
  /** where a walk ended (or stopped) */
  onSettle?: (at: WalkSpot) => void;
  /** A tap on the scene, in region pixels, before the companion walks: return true when
   *  the tap was used (no walk), a point to walk there instead, or nothing to walk to it.
   *  With `follow`, every tap goes here and AtlasWalk never walks by itself. */
  onTap?: (at: Point) => boolean | Point | void;
  /** the region's walk rows when something stands in the way (keepsakes in the hut);
   *  keep the same array while it is unchanged */
  walk?: readonly string[];
  /** more things standing in the scene, in region pixels (keepsakes) */
  extras?: readonly SceneExtra[];
  /** a thing about to be placed: drawn faint, its footprint green where it may stand, red
   *  where not */
  preview?: SceneExtra & { ok: boolean; foot: { x: number; y: number; w: number; h: number } };
  /** squeeze a long walk into this many milliseconds (the missions map) */
  maxWalkMs?: number;
  showName?: boolean;
  /** show the starting zone's name too (the home hub only names zones walked into) */
  nameAtStart?: boolean;
  /** how far down the window the zone's name sits (below a floating HUD) */
  nameTop?: number;
  /** where the companion sits down the window (0 top, 1 bottom) */
  focusY?: number;
  /** let the camera look past the region's bottom edge by this much (a card over the view) */
  padBottom?: number;
  /** false while the screen is covered or unfocused: clocks stop, walks stop */
  active?: boolean;
  /** the parent walks the companion (see AtlasFollow) */
  follow?: AtlasFollow;
  companion?: AtlasCompanion;
  /** the garden tile's life (its water, lights and lamps) is drawn by the home layer */
  homeLayer?: boolean;
  /** more things in the scene, drawn inside the camera among the props (each positioned
   *  in the region's screen pixels with its own depth as zIndex; never a wrapping view,
   *  which would stack it apart from the props) */
  scene?: ReactNode;
  /** hit areas and bubbles that follow the camera above the tap layer */
  hits?: ReactNode;
}) {
  const reduced = useReducedMotion();
  const appActive = useAppActive();
  const active = appActive && shown;
  const player = useGame((s) => s.player);
  const hutLook = useGame((s) => s.hutLook);
  const hour = new Date(useGame((s) => s.now)).getHours();
  const night = hour < 6 || hour >= 21;
  // the light of the hour (as on the garden screen): blue at night, warm at dusk, a
  // soft gold at dawn; places that make their own light keep it
  const tint = night
    ? 'rgba(22,28,66,0.42)'
    : hour >= 17
      ? 'rgba(240,128,70,0.16)'
      : hour < 9
        ? 'rgba(255,200,150,0.12)'
        : null;
  const screen = useWindowDimensions();
  const dpr = PixelRatio.get();
  const u = pixelScale(screen.width, dpr);
  const snap = useMemo(() => (v: number) => snapToDevice(v, dpr), [dpr]);
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
    // a region with decks walks on two levels laid side by side (two-level-walk.md)
    const levels = walkRows ? null : regionLevels(region);
    // (a start on a deck is on the deck level's half of the walk, drawn raised)
    const logical =
      levels && initial?.level === 1 ? { x: first.x + levels.offset, y: first.y } : first;
    const drawn =
      levels && logical !== first ? { x: first.x, y: first.y - levels.heightAt(logical) } : first;
    return {
      start: drawn,
      startLogical: logical,
      levels,
      // the world canvas walks the tiles in search windows (lib/world-walk.ts); keepsakes
      // in the hut and decks keep the whole grid
      walk:
        WORLD_CANVAS && !walkRows && !levels
          ? makeWorldWalk(region, logical)
          : makeWalkGrid(walkRows ?? levels?.rows ?? regionWalk(region), {
              cell: TILE.cell,
              width: levels ? levels.width : bounds.width,
              start: logical,
              links: levels?.links,
            }),
    };
  }, [region, tiles, bounds.width, initial, walkRows]);
  // Where a walk point is drawn: a point on the deck level is drawn over the ground it
  // stands above, raised by the deck's height. (Identity where a region has no decks.)
  const levels = grid.levels;
  const toScreen = (p: Point): Point =>
    levels && p.x >= levels.offset ? { x: p.x - levels.offset, y: p.y - levels.heightAt(p) } : p;
  // and a tap on the drawn scene: on a deck if a deck's surface is drawn there
  const fromScreen = (p: Point): Point => {
    if (!levels) return p;
    for (let h = 8; h <= 64; h += 4) {
      const q = { x: p.x + levels.offset, y: p.y + h };
      const c = grid.walk.toCell(q);
      if (grid.walk.walkable(c.cx, c.cy) && levels.heightAt(q) === h) return q;
    }
    return p;
  };
  const onDeck = useSharedValue(grid.startLogical === grid.start ? 0 : 1);
  // (the same, for drawing: whether the companion's outline can be hidden)
  const [upHere, setUpHere] = useState(grid.startLogical !== grid.start);
  const setLevel = (up: boolean) => {
    onDeck.set(up ? 1 : 0);
    setUpHere(up);
  };
  // what the parent hears: the ground point under the feet, and the level (a deck point
  // is reported as the ground it stands over, so places, doors and passes read it as is)
  const spotOf = (p: Point): WalkSpot =>
    levels && p.x >= levels.offset ? { x: p.x - levels.offset, y: p.y, level: 1 } : p;
  // the walk's own position under where the feet are drawn (on the deck while on it)
  const logicalOf = (drawn: Point): Point => (levels && onDeck.get() ? fromScreen(drawn) : drawn);

  const ownX = useSharedValue(grid.start.x);
  const ownY = useSharedValue(grid.start.y);
  // where the companion's feet are drawn: AtlasWalk's own walk, or the parent's
  const px = follow?.px ?? ownX;
  const py = follow?.py ?? ownY;
  const ox = follow?.ox ?? 0;
  const oy = follow?.oy ?? 0;
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
  const pos = useRef<Point>({ ...grid.startLogical });
  const [ownWalking, setWalking] = useState(false);
  const walking = companion?.walking ?? ownWalking;
  // where the feet are, a few times a second (for the outline behind tall things)
  const [feet, setFeet] = useState<Point>(grid.start);
  const [ownFacing, setFacing] = useState<'left' | 'right'>('right');
  const facing = companion?.facing ?? ownFacing;
  const [here, setHere] = useState<TileId>(
    placeAt(region, undefined, grid.start.x, grid.start.y) ?? 'garden',
  );
  const [named, setNamed] = useState<TileId | null>(nameAtStart ? here : null);

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

  // The parent's callbacks, read through a ref so a new closure never restarts a walk.
  const calls = useRef({ onZone, onSettle, onMove });
  useEffect(() => {
    calls.current = { onZone, onSettle, onMove };
  });
  // Where the feet are now: the zone (kept until the companion is a few steps over a
  // border, lib/region-walk.ts) and the point the mounted zones are chosen round.
  const noteFeet = (x: number, y: number) => {
    setHere((prev) => placeAt(region, prev, x, y) ?? prev);
    const fx = Math.round(x);
    const fy = Math.round(y);
    setFeet((f) => (f.x === fx && f.y === fy ? f : { x: fx, y: fy }));
  };
  const noteRef = useRef(noteFeet);
  useEffect(() => {
    noteRef.current = noteFeet;
  });
  const noteBlock = (x: number, y: number) => noteRef.current(x, y);
  // A move into another block (walking, or the parent setting the companion down
  // somewhere new) is noticed at once, so the zones round it mount before it is seen.
  useAnimatedReaction(
    () => [Math.floor((px.value + ox) / BLOCK), Math.floor((py.value + oy) / BLOCK)],
    (block, last) => {
      if (last && block[0] === last[0] && block[1] === last[1]) return;
      runOnJS(noteBlock)(px.value + ox, py.value + oy);
    },
  );
  // (the walk point and spot under drawn feet, read by timers with this render's levels)
  const spotRef = useRef({ logical: (drawn: Point) => drawn, spot: (p: Point): WalkSpot => p });
  useEffect(() => {
    spotRef.current = { logical: logicalOf, spot: spotOf };
  });
  // While walking, read the feet a few times a second (JS side), for the outline behind
  // tall things and the parent's onMove.
  useEffect(() => {
    if (!walking || !active) return undefined;
    const t = setInterval(() => {
      const x = px.get() + ox;
      const y = py.get() + oy;
      noteRef.current(x, y);
      const { logical, spot } = spotRef.current;
      calls.current.onMove?.(follow ? { x, y } : spot(logical({ x, y })));
    }, FEET_MS);
    return () => clearInterval(t);
  }, [walking, active, px, py, ox, oy, follow]);

  useEffect(() => {
    calls.current.onZone?.(here);
  }, [here]);

  // Leaving the screen stops the walk where it is: no stale arrival later. (A parent that
  // walks the companion stops its own walks.)
  useEffect(() => {
    if (active || follow) return;
    cancelAnimation(ownX);
    cancelAnimation(ownY);
    const { logical, spot } = spotRef.current;
    pos.current = logical({ x: ownX.get(), y: ownY.get() });
    calls.current.onSettle?.(spot(pos.current));
  }, [active, follow, ownX, ownY]);

  // glide: a keyboard step, retargeted every STEP_MS: level speed, no settle until the
  // keys are released
  const keysHeld = useRef(false);
  // a small squash as the feet settle after a walk, then still
  const settleSquash = () => {
    if (!reduced && active && !keysHeld.current)
      landing.set(withSequence(withTiming(1, { duration: 90 }), withTiming(0, { duration: 170 })));
  };
  // (the parent's walk ended: settle the same way)
  const squashRef = useRef(settleSquash);
  useEffect(() => {
    squashRef.current = settleSquash;
  });
  const wasWalking = useRef(walking);
  useEffect(() => {
    const was = wasWalking.current;
    wasWalking.current = walking;
    if (follow && was && !walking) squashRef.current();
  }, [walking, follow]);
  // A lift ride: the cab carries the feet straight between the lift's two ends as drawn,
  // then the walk goes on. (Reduced motion: at once.)
  const ride = (from: Point, to: Point, then: () => void) => {
    const a = toScreen(from);
    const b = toScreen(to);
    setLevel(!!levels && to.x >= levels.offset);
    const done = () => {
      pos.current = to;
      then();
    };
    if (reduced) {
      ownX.set(b.x);
      ownY.set(b.y);
      done();
      return;
    }
    ownX.set(a.x);
    ownX.set(withTiming(b.x, { duration: 900, easing: Easing.inOut(Easing.quad) }));
    ownY.set(
      withTiming(b.y, { duration: 900, easing: Easing.inOut(Easing.quad) }, (finished) => {
        if (finished) runOnJS(done)();
      }),
    );
  };
  const walkTo = (goal: Point, glide = false, then?: () => void) => {
    if (follow) return;
    cancelAnimation(ownX);
    cancelAnimation(ownY);
    // (the feet are drawn in screen terms; the walk's own position may be on the deck)
    const from0 = logicalOf({ x: ownX.get(), y: ownY.get() });
    pos.current = from0;
    const logical = grid.walk.findPath(from0, goal);
    // A walk to the other level with no stair on the way takes a lift: walk to the lift,
    // ride, walk on. Each part starts only when the one before has finished, so a tap
    // that interrupts it never rides a stale lift (two-level-walk.md, rule 5).
    if (levels && levels.lifts.length && !glide && !then) {
      const upper = (q: Point) => q.x >= levels.offset;
      const reached = logical.length ? logical[logical.length - 1] : from0;
      if (upper(reached) !== upper(goal)) {
        let best: { from: Point; to: Point; cost: number } | null = null;
        for (const [bottom, top] of levels.lifts) {
          const [mine, other] = upper(from0) ? [top, bottom] : [bottom, top];
          const leg1 = grid.walk.findPath(from0, mine);
          const leg2 = grid.walk.findPath(other, goal);
          const near = Math.hypot(from0.x - mine.x, from0.y - mine.y) < 6;
          if ((!leg1.length && !near) || !leg2.length) continue;
          const cost = leg1.length + leg2.length;
          if (!best || cost < best.cost) best = { from: mine, to: other, cost };
        }
        if (best) {
          const lift = best;
          walkTo(lift.from, false, () => ride(lift.from, lift.to, () => walkTo(goal)));
          return;
        }
      }
    }
    if (!logical.length) {
      then?.();
      return;
    }
    const lastLogical = logical[logical.length - 1];
    const path = logical.map(toScreen);
    const end = path[path.length - 1];
    const arrive = () => {
      pos.current = lastLogical;
      setLevel(!!levels && lastLogical.x >= levels.offset);
      setWalking(false);
      setFeet(end);
      settleSquash();
      const foot = spotOf(lastLogical);
      if (placeAt(region, undefined, foot.x, foot.y))
        setHere((prev) => placeAt(region, prev, foot.x, foot.y) ?? prev);
      calls.current.onSettle?.(foot);
      then?.();
    };
    // on a deck the feet draw above everything on the ground for the whole walk once the
    // first step is on it (a walk down a stair keeps it until it arrives)
    if (levels && logical.some((p) => p.x >= levels.offset)) setLevel(true);
    // face the way each leg goes; a leg that only goes up or down keeps the facing
    // (legs are measured where the feet are drawn: a walk that starts on a deck starts
    // from the deck as drawn, not from its half of the walk grid)
    const drawn0 = toScreen(from0);
    const firstFacing = legFacing(drawn0, path[0]) ?? legFacing(drawn0, end);
    if (firstFacing) setFacing(firstFacing);
    // reduced motion: instant walking (docs/vision/interface.md)
    if (reduced) {
      ownX.set(end.x);
      ownY.set(end.y);
      arrive();
      return;
    }
    setWalking(true);
    let length = 0;
    let prev = drawn0;
    for (const p of path) {
      length += Math.hypot(p.x - prev.x, p.y - prev.y);
      prev = p;
    }
    // a long walk on the missions map is squeezed into a moment
    const squeeze = maxWalkMs ? Math.min(1, maxWalkMs / Math.max(1, (length / SPEED) * 1000)) : 1;
    let from = drawn0;
    const xs: number[] = [];
    const ys: number[] = [];
    path.forEach((p, i) => {
      const duration = Math.max(
        squeeze < 1 ? 8 : 60,
        (Math.hypot(p.x - from.x, p.y - from.y) / (glide ? KEY_SPEED : SPEED)) * 1000 * squeeze,
      );
      // set off gently and slow into the last step (anticipate, act, settle); level between
      const first = i === 0;
      const last = i === path.length - 1;
      const easing = glide
        ? Easing.linear
        : first && last
          ? Easing.inOut(Easing.quad)
          : first
            ? Easing.in(Easing.quad)
            : last
              ? Easing.out(Easing.quad)
              : Easing.linear;
      const ms = !glide && (first || last) ? duration * 1.25 : duration;
      const next = path[i + 1];
      const nextFacing = next ? legFacing(p, next) : null;
      xs.push(
        withTiming(p.x, { duration: ms, easing }, (finished) => {
          if (finished && nextFacing) runOnJS(setFacing)(nextFacing);
        }),
      );
      ys.push(withTiming(p.y, { duration: ms, easing }));
      from = p;
    });
    ownX.set(withSequence(...xs));
    ownY.set(
      withSequence(
        ...ys,
        withTiming(end.y, { duration: 0 }, (finished) => {
          if (finished) runOnJS(arrive)();
        }),
      ),
    );
  };

  // Arrow keys / WASD (web): short glides in the held direction, sliding along walls.
  // (A parent that walks the companion listens to the keys itself.)
  useKeyboardWalk(
    interactive && active && !follow,
    (dx, dy) => {
      keysHeld.current = true;
      const from = logicalOf({ x: ownX.get(), y: ownY.get() });
      // well past the next tick, so a held key never arrives (and re-renders) between ticks
      const reach = KEY_SPEED * (STEP_MS / 1000) * 2.5;
      for (const [ax, ay] of keySteps(dx, dy)) {
        const to = { x: from.x + ax * reach, y: from.y + ay * reach };
        const c = grid.walk.toCell(to);
        if (grid.walk.walkable(c.cx, c.cy)) {
          walkTo(to, true);
          return;
        }
      }
    },
    () => {
      keysHeld.current = false;
    },
  );

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
  // where the land runs on past the region's top, the camera may look a little past
  // it, so a companion at a north-edge stand is not left under the header
  // (play-test 18 Oct, finding 9)
  const roomAbove = region === 'valley' || zoneBeyondByRegion[region] ? 96 : 0;
  // The camera keeps to the land you can walk on, plus a margin (art-faults.md, rule 13:
  // no screens full of what lies past the world), not to the region's whole rectangle.
  const land = (() => {
    const rows = walkRows ?? regionWalk(region);
    let x0 = Infinity;
    let x1 = -Infinity;
    let y0 = Infinity;
    let y1 = -Infinity;
    rows.forEach((row, r) => {
      const a = row.indexOf('.');
      if (a < 0) return;
      const b = row.lastIndexOf('.');
      x0 = Math.min(x0, a);
      x1 = Math.max(x1, b + 1);
      y0 = Math.min(y0, r);
      y1 = Math.max(y1, r + 1);
    });
    const PAD = 40;
    const c = TILE.cell;
    return {
      x0: Math.max(0, x0 * c - PAD) * u,
      x1: Math.min(bounds.width, x1 * c + PAD) * u,
      y0: Math.max(0, y0 * c - PAD) * u,
      y1: Math.min(bounds.height, y1 * c + PAD) * u,
    };
  })();
  const top = Math.max(-roomAbove, land.y0 - roomAbove);
  // The framing eases when it changes (a card opening below), instead of jumping.
  const focus = useSharedValue(focusY);
  const pad = useSharedValue(padBottom);
  useEffect(() => {
    focus.set(
      reduced
        ? focusY
        : withTiming(focusY, { duration: FRAME_EASE_MS, easing: Easing.out(Easing.quad) }),
    );
  }, [focusY, reduced, focus]);
  useEffect(() => {
    pad.set(
      reduced
        ? padBottom
        : withTiming(padBottom, { duration: FRAME_EASE_MS, easing: Easing.out(Easing.quad) }),
    );
  }, [padBottom, reduced, pad]);
  /** The camera's top-left (screen pixels in the region) for feet at (x, y): one
   *  function for what is drawn and where a tap lands. */
  const cameraAt = (x: number, y: number, f: number, b: number) => {
    'worklet';
    // land narrower (or shorter) than the screen sits in its middle
    const cx =
      land.x1 - land.x0 <= width
        ? (land.x0 + land.x1 - width) / 2
        : Math.max(land.x0, Math.min(land.x1 - width, x * u - width / 2));
    const cy =
      land.y1 - top <= height - b
        ? (top + land.y1 - height + b) / 2
        : Math.max(top, Math.min(land.y1 - height + b, y * u - height * f));
    return { x: cx, y: cy };
  };
  const cam = follow?.cam;
  useAnimatedReaction(
    () => cameraAt(px.value + ox, py.value + oy, focus.value, pad.value),
    (c) => {
      if (cam) cam.set(c);
    },
  );
  const cameraStyle = useAnimatedStyle(() => {
    const c = cameraAt(px.value + ox, py.value + oy, focus.value, pad.value);
    return { transform: [{ translateX: -Math.round(c.x) }, { translateY: -Math.round(c.y) }] };
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
      { translateX: Math.round((px.value + ox) * u - petPx / 2) },
      { translateY: Math.round((py.value + oy) * u - petPx * (30 / 32)) },
    ],
    // on a deck, above the ground and the deck itself (two-level-walk.md, drawing order)
    zIndex: Math.round(py.value + oy) + (onDeck.value ? 300000 : 0),
  }));

  // Mount the zones the camera can see from where the feet are, and a margin round them
  // (lib/region-walk.ts zonesToMount), no more: a phone keeps only a few zones' pictures.
  const seen = (() => {
    const c = cameraAt(feet.x, feet.y, focusY, padBottom);
    return { x0: c.x / u, y0: c.y / u, x1: (c.x + width) / u, y1: (c.y + height) / u };
  })();
  const [mounted, setMounted] = useState<TileId[]>(() =>
    WORLD_CANVAS ? [] : zonesToMount(region, seen),
  );
  // the world canvas mounts world tiles instead (at most 12 on a phone, lib/world-walk.ts)
  const [mountedTiles, setMountedTiles] = useState<string[]>(() =>
    WORLD_CANVAS ? tilesToMount(region, seen) : [],
  );
  const wantTiles = WORLD_CANVAS ? tilesToMount(region, seen, mountedTiles) : mountedTiles;
  if (wantTiles.length !== mountedTiles.length || wantTiles.some((k, i) => k !== mountedTiles[i]))
    setMountedTiles(wantTiles);
  const tilesKey = wantTiles.join(';');
  // the region's pictures load ahead of time, so a zone mounting at the edge of the view
  // draws at once (fetched, not decoded: only mounted zones take a phone's memory)
  useEffect(() => {
    prefetchRegion(region);
  }, [region]);
  // (with the world canvas, the zones near are those whose areas the view reaches: their
  // life, residents and light still go by zone)
  const want = WORLD_CANVAS
    ? areasNear(region, seen, TILE_MOUNT_MARGIN)
        .map((a) => a.area.id)
        .filter(isTileId)
    : zonesToMount(region, seen, mounted);
  if (want.length !== mounted.length || want.some((id, i) => id !== mounted[i])) setMounted(want);
  const mountKey = want.join(',');
  const near = useMemo(
    () => tiles.filter((t) => mountKey.split(',').includes(t.id)),
    [tiles, mountKey],
  );
  const gaps: { col: number; row: number }[] = [];
  const opensOut = region === 'valley' || region === 'moon' || !!zoneBeyondByRegion[region];
  for (const { col, row } of cellsNear(region, seen, MOUNT_MARGIN)) {
    const inside =
      col >= bounds.minCol &&
      row >= bounds.minRow &&
      col < bounds.minCol + bounds.tileCols &&
      row < bounds.minRow + bounds.tileRows;
    // past a region's edge (a region shorter or narrower than the screen) the land runs
    // on where it has open country round it; elsewhere the backdrop's colour shows
    if (
      inside
        ? !tiles.some((t) => t.col === col && t.row === row)
        : opensOut && !(region === 'moon' && row < 0)
    )
      gaps.push({ col, row });
  }
  // (the same scene while the mounted zones and keepsakes are the same, so a re-render
  // as the feet move does not rebuild every prop)
  const drawables = useMemo(
    () => [
      ...(WORLD_CANVAS
        ? worldDrawables(
            region,
            tilesKey ? tilesKey.split(';') : [],
            near,
            hutImages[hutImageKey(hutLook)],
          )
        : near.flatMap((t) => tileDrawables(region, t, hutImages[hutImageKey(hutLook)]))),
      ...(extras ?? []).map((e) => ({ ...e, sprite: `extra:${e.key}` })),
    ],
    [near, region, hutLook, extras, tilesKey],
  );
  // the home layer lights the garden itself (its lantern can be turned off)
  const lamps = drawables.filter(
    (d) => LAMPS[d.sprite] && !(homeLayer && d.key.startsWith('garden-')),
  );
  // behind a building or a big tree, the companion's outline shows through (a flyer's box
  // is not where it flies, so it never counts)
  // (on a deck the companion draws above everything on the street, so nothing hides it)
  const hidden =
    !upHere &&
    hiddenBehind(
      drawables.filter((d) => !FLYERS[d.sprite]),
      feet,
    );
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

  // the props' pictures, rebuilt only when the scene or the clocks change
  const props = useMemo(
    () =>
      drawables.map((d) =>
        FLYERS[d.sprite] && active && !reduced ? (
          <Flyer key={d.key} d={d} clock={bob} u={u} snap={snap} />
        ) : FLOATS[d.sprite] && active && !reduced ? (
          <Floating key={d.key} d={d} clock={bob} u={u} snap={snap} />
        ) : zoneFrames[d.sprite] && active && !reduced && !FLYERS[d.sprite] ? (
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
              transform: d.flip ? [{ scaleX: -1 }] : undefined,
            }}
          />
        ),
      ),
    [drawables, active, reduced, bob, u, snap],
  );

  const onPress = (e: GestureResponderEvent) => {
    // react-native-web reports the press position on the overlay as offsetX/offsetY
    const ne = e.nativeEvent as typeof e.nativeEvent & { offsetX?: number; offsetY?: number };
    const locationX = ne.locationX ?? ne.offsetX ?? 0;
    const locationY = ne.locationY ?? ne.offsetY ?? 0;
    const c = cameraAt(px.get() + ox, py.get() + oy, focus.get(), pad.get());
    const at = { x: (locationX + c.x) / u, y: (locationY + c.y) / u };
    const used = onTap?.(at);
    if (used === true || follow) return;
    walkTo(fromScreen(used ? used : at));
  };

  const pet = (shadow: boolean) =>
    player ? (
      <GuardianPet
        player={player}
        size={petPx}
        facing={facing}
        walking={walking && active && !reduced}
        bob={(companion?.bob ?? !walking) && !reduced && active}
        grumpy={companion?.grumpy}
        yawning={companion?.yawning}
        gardenPose={shadow ? companion?.pose : undefined}
        groundShadow={shadow}
        active={active}
        decorative
      />
    ) : (
      <Pet
        size={petPx}
        facing={facing}
        walking={walking && !reduced}
        groundShadow={shadow}
        active={active}
        decorative
      />
    );

  return (
    <View
      style={{ width, height, overflow: 'hidden', backgroundColor: BACKDROP[region] ?? '#2F4630' }}
    >
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
              source={beyondAt(region, g.col, g.row)}
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
          {WORLD_CANVAS && (
            <WorldGround
              region={region}
              keys={tilesKey ? tilesKey.split(';') : []}
              garden={!homeLayer && near.some((t) => t.id === 'garden')}
              clock={bob}
              u={u}
              snap={snap}
            />
          )}
          {(WORLD_CANVAS ? [] : near).map((t) => {
            const o = tileOrigin(region, t);
            const left = snap(o.x * u);
            const tileTop = snap(o.y * u);
            const w = snap(TILE.width * u);
            const h = snap(TILE.height * u);
            return (
              <View
                key={`ground-${t.id}`}
                style={{
                  position: 'absolute',
                  left,
                  top: tileTop,
                  width: w,
                  height: h,
                  // the ground's own colour under its picture, in case a phone drops it
                  backgroundColor: zoneTone[t.id],
                }}
              >
                <Image
                  source={t.id === 'garden' ? gardenGround : zoneGrounds[t.id]}
                  resizeMode="stretch"
                  style={{ position: 'absolute', left: 0, top: 0, width: w, height: h }}
                />
                <FlowLayer zone={t.id} clock={bob} u={u} snap={snap} />
                {/* the street under a deck, darker, and the deck's shadow on it */}
                {t.id !== 'garden' && zoneDeckArt[t.id] && (
                  <Image
                    source={zoneDeckArt[t.id]?.shadow}
                    resizeMode="stretch"
                    style={{ position: 'absolute', left: 0, top: 0, width: w, height: h }}
                  />
                )}
                {t.id === 'garden' && !homeLayer && (
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
          {props}
          {scene}
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
          {tint &&
            [
              ...near
                .filter((t) => !OWN_LIGHT.includes(t.id))
                .map((t) => ({ key: t.id, ...tileOrigin(region, t) })),
              // and what lies past the places, so the land beyond darkens with them
              ...(near.every((t) => OWN_LIGHT.includes(t.id))
                ? []
                : gaps.map((g) => ({
                    key: `gap-${g.col}-${g.row}`,
                    x: (g.col - bounds.minCol) * TILE.width,
                    y: (g.row - bounds.minRow) * TILE.height,
                  }))),
            ]
              .concat(
                near
                  .filter((t) => FADE_LIGHT[t.id])
                  .map((t) => ({ key: `fade-${t.id}`, fade: true, ...tileOrigin(region, t) })),
              )
              .map((c) =>
                'fade' in c ? (
                  <LinearGradient
                    key={`tint-${c.key}`}
                    pointerEvents="none"
                    colors={[tint, clearOf(tint)]}
                    start={{ x: 0, y: 0.5 }}
                    end={{ x: 0.7, y: 0.5 }}
                    style={{
                      position: 'absolute',
                      left: snap(c.x * u),
                      top: snap(c.y * u),
                      width: snap(TILE.width * u),
                      height: snap(TILE.height * u),
                      zIndex: 150000,
                    }}
                  />
                ) : (
                  <View
                    key={`tint-${c.key}`}
                    style={{
                      position: 'absolute',
                      left: snap(c.x * u),
                      top: snap(c.y * u),
                      width: snap(TILE.width * u),
                      height: snap(TILE.height * u),
                      backgroundColor: tint,
                      zIndex: 150000,
                    }}
                  />
                ),
              )}
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
            lamps.map((d) => {
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
            {companion?.emote && (
              <View
                pointerEvents="none"
                style={{
                  position: 'absolute',
                  top: -petPx * 0.35,
                  alignSelf: 'center',
                  minWidth: 26,
                  paddingHorizontal: 6,
                  borderWidth: 2,
                  borderColor: cozy.outline,
                  backgroundColor: cozy.paper,
                  alignItems: 'center',
                  zIndex: 1,
                }}
              >
                <BodyText style={{ fontSize: 13, lineHeight: 18 }}>{companion.emote}</BodyText>
              </View>
            )}
            <Animated.View style={landStyle}>{pet(true)}</Animated.View>
          </Animated.View>
          {preview && (
            // a keepsake about to be set down: its footprint lit green (it may stand
            // there) or red (not), the thing itself faint above it
            <View pointerEvents="none" style={{ position: 'absolute', zIndex: 149998 }}>
              <View
                style={{
                  position: 'absolute',
                  left: snap(preview.foot.x * u),
                  top: snap(preview.foot.y * u),
                  width: snap(preview.foot.w * u),
                  height: snap(preview.foot.h * u),
                  backgroundColor: preview.ok ? 'rgba(126,200,96,0.55)' : 'rgba(214,72,60,0.55)',
                  borderWidth: Math.max(1, Math.round(u)),
                  borderColor: preview.ok ? '#3E7A2E' : '#8A2A22',
                }}
              />
              <Image
                source={preview.src}
                resizeMode="stretch"
                style={{
                  position: 'absolute',
                  left: snap(preview.x * u),
                  top: snap(preview.y * u),
                  width: snap(preview.w * u),
                  height: snap(preview.h * u),
                  opacity: 0.8,
                  transform: preview.flip ? [{ scaleX: -1 }] : undefined,
                }}
              />
            </View>
          )}
          {hidden && (
            // the same companion again, faint, above everything but the night tint, so it
            // reads through what hides it and lines up with itself where nothing does
            <Ghost px={px} py={py} ox={ox} oy={oy} u={u} size={petPx} reduced={reduced}>
              {pet(false)}
            </Ghost>
          )}
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
                left: m.x * u - (m.selected ? 70 : 22),
                // the label's foot sits above a standing companion's head, so it never
                // covers the companion at the stand (play-test 18 Oct, finding 3)
                top: m.y * u - 50 * u - 44,
                width: m.selected ? 140 : 44,
                height: 44,
                alignItems: 'center',
                justifyContent: 'flex-end',
              }}
            >
              {m.selected ? (
                <PixelFrame
                  tone="gold"
                  style={{ paddingVertical: 2 * u, paddingHorizontal: 4 * u, alignItems: 'center' }}
                >
                  <BodyText
                    numberOfLines={1}
                    style={{ fontSize: 11, lineHeight: 13, fontFamily: 'PixelifySans_700Bold' }}
                  >
                    {m.label}
                  </BodyText>
                </PixelFrame>
              ) : (
                // a small pin over what can be visited: the name shows once it is chosen,
                // so labels never cover the place itself (Matt, 19 Oct, fault 20)
                <PixelFrame tone="paper" style={{ padding: 2 * u }}>
                  <View
                    style={{ width: 4 * u, height: 4 * u, backgroundColor: frameTones.gold.fill }}
                  />
                </PixelFrame>
              )}
            </Pressable>
          ))}
        </Animated.View>
      )}
      {hits && (
        <Animated.View
          pointerEvents="box-none"
          style={[
            { position: 'absolute', left: 0, top: 0, width: regionW, height: regionH },
            cameraStyle,
          ]}
        >
          {hits}
        </Animated.View>
      )}
      {showName && named && (
        <View
          pointerEvents="none"
          style={{ position: 'absolute', top: nameTop, left: 0, right: 0, alignItems: 'center' }}
        >
          <PixelFrame tone="paper" style={{ paddingVertical: 2 * u, paddingHorizontal: 6 * u }}>
            <BodyText style={{ fontFamily: 'PixelifySans_700Bold', fontSize: 12 }}>
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
