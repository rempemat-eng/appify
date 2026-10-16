import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { Image, View } from 'react-native';
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
import { useGame, type Player } from '@/lib/game';
import { WORLD, worldIds, worldMaps, type WorldId } from '@/lib/world-maps';
import { worldCatalogue } from '@/lib/world-catalogue';
import { worldImages, worldProps } from '@/lib/world-assets';
import { makeWalkGrid, type Point } from '@/lib/garden-path';
import {
  TILT_DEG,
  billboard,
  makeProjection,
  project,
  type ViewMode,
} from '@/lib/garden-projection';
import { GuardianPet } from '@/components/guardian-pet';
import { Pet } from '@/components/game-ui';

// Who you might bump into on each journey (scenery only: no rewards or rules).
export const worldResident = Object.fromEntries(
  worldIds.map((id) => [id, worldCatalogue[id].resident]),
);

const gridFor = (id: WorldId) =>
  makeWalkGrid(worldMaps[id].walk, {
    cell: WORLD.cell,
    width: WORLD.width,
    start: worldMaps[id].route[0],
  });
const grids = new Map(worldIds.map((id) => [id, gridFor(id)] as const));

const SPEED = 26; // a mission stroll is slower than a garden dash

/**
 * A mission world as a living 2.5D diorama: the companion strolls its route,
 * pausing to look around, while the player is away. Purely scenery, so it has
 * no touch targets and is hidden from assistive tech (the mission text says it).
 */
export function WorldScene({
  world,
  width,
  player,
  view = 'tilt',
  active: screenActive = true,
  still = false,
}: {
  world: WorldId;
  width: number;
  player: Player;
  view?: ViewMode;
  active?: boolean;
  /** static preview (Missions tab): no walking, no animation */
  still?: boolean;
}) {
  const reduced = useReducedMotion();
  const appActive = useAppActive();
  const active = screenActive && appActive;
  const map = worldMaps[world];
  const grid = grids.get(world) ?? gridFor(world);
  const tilt = view === 'tilt';
  const proj = makeProjection(view, width, WORLD, tilt ? Math.round(width * 0.14) : 0);
  const scale = proj.scale;
  const petPx = Math.max(32, Math.round(scale) * 32);
  const residentPx = Math.max(32, Math.round(petPx / 2 / 32) * 32);
  const hour = new Date(useGame((s) => s.now)).getHours();
  const night = hour < 6 || hour >= 21;
  const dusk = !night && hour >= 17;
  const moving = active && !still && !reduced;

  const start = map.route[0];
  const px = useSharedValue(start.x);
  const py = useSharedValue(start.y);
  const pos = useRef<Point>({ ...start });
  const leg = useRef(0);
  const [walking, setWalking] = useState(false);
  const [facing, setFacing] = useState<'left' | 'right'>('right');
  const [frame, setFrame] = useState(0);
  const [sceneWorld, setSceneWorld] = useState(world);
  if (sceneWorld !== world) {
    setSceneWorld(world);
    setWalking(false);
    setFacing('right');
  }

  // A mounted scene can be reused for another journey. It must start on that
  // world's route rather than drawing or pathfinding from the previous map.
  useLayoutEffect(() => {
    cancelAnimation(px);
    cancelAnimation(py);
    const origin = map.route[0];
    pos.current = { ...origin };
    leg.current = 0;
    px.set(origin.x);
    py.set(origin.y);
  }, [map, px, py]);

  useEffect(() => {
    if (!moving) return undefined;
    const t = setInterval(() => setFrame((f) => 1 - f), 800);
    return () => clearInterval(t);
  }, [moving]);

  // Stroll the route: walk a leg, pause to look around, then the next leg.
  useLayoutEffect(() => {
    if (!moving) return undefined;
    let alive = true;
    let pause: ReturnType<typeof setTimeout>;
    const next = () => {
      if (!alive) return;
      leg.current = (leg.current + 1) % map.route.length;
      const target = map.route[leg.current];
      const path = grid.findPath(pos.current, target);
      if (!path.length) {
        pause = setTimeout(next, 600);
        return;
      }
      const end = path[path.length - 1];
      setFacing(end.x < pos.current.x ? 'left' : 'right');
      setWalking(true);
      let from = pos.current;
      const xs = [];
      const ys = [];
      for (const p of path) {
        const duration = Math.max(80, (Math.hypot(p.x - from.x, p.y - from.y) / SPEED) * 1000);
        xs.push(withTiming(p.x, { duration, easing: Easing.linear }));
        ys.push(withTiming(p.y, { duration, easing: Easing.linear }));
        from = p;
      }
      const arrive = () => {
        if (!alive) return;
        pos.current = end;
        setWalking(false);
        pause = setTimeout(next, 1400 + Math.random() * 1600);
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
    pause = setTimeout(next, 900);
    return () => {
      alive = false;
      clearTimeout(pause);
      cancelAnimation(px);
      cancelAnimation(py);
      pos.current = { x: px.get(), y: py.get() };
      setWalking(false);
    };
  }, [moving, map, grid, px, py]);

  const petStyle = useAnimatedStyle(() => {
    const s = project(proj, px.value, py.value);
    return {
      transform: [
        { translateX: Math.round(s.sx - petPx / 2) },
        { translateY: Math.round(s.sy - petPx * (30 / 32)) },
        { scale: s.f },
      ],
      zIndex: Math.round(py.value),
    };
  });

  const resident = worldResident[world];
  const vs = project(proj, map.visitor.x, map.visitor.y);
  const groundH = Math.round(WORLD.height * scale);
  return (
    <View
      pointerEvents="none"
      aria-hidden
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      // @ts-expect-error dataSet is a react-native-web prop (crisp pixel scaling via CSS)
      dataSet={{ pixel: 'true' }}
      style={{
        width,
        height: proj.height,
        overflow: 'hidden',
        // ground colour fills the slivers beside the tilted plane's far corners
        backgroundColor: world === 'mountain' ? '#6A9468' : '#73A85E',
      }}
    >
      {tilt && (
        <Image
          source={worldImages[world].sky}
          resizeMode="stretch"
          style={{
            position: 'absolute',
            left: 0,
            top: Math.round(proj.horizon - 80 * (width / 216)),
            width,
            height: Math.round(150 * (width / 216)),
          }}
        />
      )}
      <View
        style={[
          { position: 'absolute', left: 0, top: proj.bottom - groundH, width, height: groundH },
          tilt && {
            transform: [{ perspective: proj.persp }, { rotateX: `${TILT_DEG}deg` }],
            transformOrigin: '50% 100%',
          },
        ]}
      >
        <Image
          source={worldImages[world].ground[moving ? frame : 0]}
          resizeMode="stretch"
          style={{ width, height: groundH }}
        />
      </View>
      {map.objects.map((o) => {
        const r = billboard(proj, o.x, o.y, o.w, o.h);
        return (
          <Image
            key={o.id}
            source={worldProps[o.sprite]}
            resizeMode="stretch"
            style={{
              position: 'absolute',
              left: Math.round(r.left),
              top: Math.round(r.top),
              width: Math.round(r.width),
              height: Math.round(r.height),
              zIndex: o.y + o.h,
            }}
          />
        );
      })}
      <View
        style={{
          position: 'absolute',
          left: Math.round(vs.sx - residentPx / 2),
          top: Math.round(vs.sy - residentPx * (30 / 32)),
          width: residentPx,
          height: residentPx,
          transform: [{ scale: vs.f }],
          transformOrigin: '50% 93.75%',
          zIndex: map.visitor.y,
        }}
      >
        <Pet visitor={resident} size={residentPx} bob={moving} active={moving} />
      </View>
      <Animated.View
        style={[
          {
            position: 'absolute',
            left: 0,
            top: 0,
            width: petPx,
            height: petPx,
            transformOrigin: '50% 93.75%',
          },
          petStyle,
        ]}
      >
        <GuardianPet
          player={player}
          size={petPx}
          facing={facing}
          walking={walking && moving}
          bob={!walking && moving}
          active={moving}
        />
      </Animated.View>
      {(night || dusk) && (
        <View
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            width,
            height: proj.height,
            zIndex: 900,
            backgroundColor: night ? 'rgba(22,28,66,0.42)' : 'rgba(240,128,70,0.14)',
          }}
        />
      )}
    </View>
  );
}

/** A cropped window onto a world, for mission cards (static, no walking). */
export function WorldPreview({
  world,
  player,
  height,
}: {
  world: WorldId;
  player: Player;
  height: number;
}) {
  const [width, setWidth] = useState(0);
  const full = width ? makeProjection('tilt', width, WORLD, Math.round(width * 0.14)).height : 0;
  return (
    <View
      onLayout={(e) => setWidth(Math.round(e.nativeEvent.layout.width))}
      style={{
        height,
        borderRadius: 14,
        overflow: 'hidden',
        borderWidth: 2,
        borderColor: '#2A2421',
      }}
    >
      {width > 0 && (
        <View style={{ position: 'absolute', left: 0, top: -Math.round((full - height) * 0.42) }}>
          <WorldScene world={world} width={width - 4} player={player} still />
        </View>
      )}
    </View>
  );
}
