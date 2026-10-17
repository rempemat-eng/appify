import { useEffect, useMemo, useRef, useState } from 'react';
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
  withSequence,
  withTiming,
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
import { zoneMaps, zoneOverhead } from '@/lib/zone-maps';
import { zoneGrounds, zoneProps } from '@/lib/zone-assets';
import { GuardianPet } from '@/components/guardian-pet';
import { ZoneLife } from '@/components/atlas-life';
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
const OWN_LIGHT: TileId[] = ['neon', 'station', 'lumen', 'caldera'];
// Where a lamp's light sits on its sprite (x, y from its top-left, in art pixels).
const LAMPS: Record<string, readonly [number, number]> = {
  lamp: [7, 8],
  gas_lamp: [8, 9],
  street_light: [12, 8],
  lantern: [7, 10],
  lighthouse: [22, 20],
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

/**
 * A walk across a whole region with no cuts between zones (world-atlas.md, "Seamless
 * travel"; living-world plan W1, first prototype). Tap anywhere to walk there: the
 * camera follows across zone borders, only the zones round the companion are
 * mounted, and a zone's name shows as you cross into it. Presentation only: it saves
 * nothing, grants nothing and costs nothing; the saved position comes with C19.
 */
export function AtlasWalk({
  region = 'valley',
  width,
  height,
}: {
  region?: RegionId;
  width: number;
  height: number;
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
  const grid = useMemo(() => {
    const garden = tiles.find((t) => t.id === 'garden');
    const g0 = garden ? tileOrigin(region, garden) : { x: 0, y: 0 };
    const startTile = garden ?? tiles[0];
    const first =
      startTile.id === 'garden'
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
  }, [region, tiles, bounds.width]);

  const px = useSharedValue(grid.start.x);
  const py = useSharedValue(grid.start.y);
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

  // Leaving the screen stops the walk where it is: no stale arrival later.
  useEffect(() => {
    if (active) return;
    cancelAnimation(px);
    cancelAnimation(py);
    pos.current = { x: px.get(), y: py.get() };
  }, [active, px, py]);

  const walkTo = (target: Point) => {
    cancelAnimation(px);
    cancelAnimation(py);
    const from0 = { x: px.get(), y: py.get() };
    pos.current = from0;
    const path = grid.walk.findPath(from0, target);
    if (!path.length) return;
    const end = path[path.length - 1];
    setFacing(end.x < from0.x ? 'left' : 'right');
    setWalking(true);
    let from = from0;
    const xs = [];
    const ys = [];
    for (const p of path) {
      const duration = Math.max(60, (Math.hypot(p.x - from.x, p.y - from.y) / SPEED) * 1000);
      xs.push(withTiming(p.x, { duration, easing: Easing.linear }));
      ys.push(withTiming(p.y, { duration, easing: Easing.linear }));
      from = p;
    }
    const arrive = () => {
      pos.current = end;
      setWalking(false);
      const tile = tileAt(region, end.x, end.y);
      if (tile) setHere(tile.id);
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

  const regionW = bounds.width * u;
  const regionH = bounds.height * u;
  const petPx = 32 * u;
  const cameraStyle = useAnimatedStyle(() => {
    const cx = Math.max(0, Math.min(regionW - width, px.value * u - width / 2));
    const cy = Math.max(0, Math.min(regionH - height, py.value * u - height * 0.55));
    return { transform: [{ translateX: -Math.round(cx) }, { translateY: -Math.round(cy) }] };
  });
  const petStyle = useAnimatedStyle(() => ({
    transform: [
      { translateX: Math.round(px.value * u - petPx / 2) },
      { translateY: Math.round(py.value * u - petPx * (30 / 32)) },
    ],
    zIndex: Math.round(py.value),
  }));

  // Mount the zone the companion is in and its neighbours (diagonals too), no more.
  const hereTile = tiles.find((t) => t.id === here) ?? tiles[0];
  const near = tiles.filter(
    (t) => Math.abs(t.col - hereTile.col) <= 1 && Math.abs(t.row - hereTile.row) <= 1,
  );
  const drawables = near.flatMap((t) => tileDrawables(region, t));

  const onPress = (e: GestureResponderEvent) => {
    // react-native-web reports the press position on the overlay as offsetX/offsetY
    const ne = e.nativeEvent as typeof e.nativeEvent & { offsetX?: number; offsetY?: number };
    const locationX = ne.locationX ?? ne.offsetX ?? 0;
    const locationY = ne.locationY ?? ne.offsetY ?? 0;
    const cx = Math.max(0, Math.min(regionW - width, px.get() * u - width / 2));
    const cy = Math.max(0, Math.min(regionH - height, py.get() * u - height * 0.55));
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
          {drawables.map((d) => (
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
          ))}
          {near.map((t) =>
            t.id === 'garden' ? null : (
              <ZoneLife
                key={`life-${t.id}`}
                zone={t.id}
                left={snap(tileOrigin(region, t).x * u)}
                top={snap(tileOrigin(region, t).y * u)}
                u={u}
                running={active && !reduced}
              />
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
      </View>
      {/* one transparent layer takes the taps, so their position is the window's */}
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={`Walk around ${zoneNames[here].toLowerCase()}. Tap where to go.`}
        onPress={onPress}
        style={{ position: 'absolute', left: 0, top: 0, width, height }}
      />
      {named && (
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
