import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { Image, PixelRatio, View, useWindowDimensions } from 'react-native';
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
import { GuardianPet } from '@/components/guardian-pet';
import { Pet } from '@/components/game-ui';
import { windowStart, worldPreviewFrame } from '@/lib/world-framing';
import { pixelScale, snapToDevice } from '@/lib/pixel-scale';

const gridFor = (id: WorldId) =>
  makeWalkGrid(worldMaps[id].walk, {
    cell: WORLD.cell,
    width: WORLD.width,
    start: worldMaps[id].route[0],
  });
const grids = new Map(worldIds.map((id) => [id, gridFor(id)] as const));

const SPEED = 26; // a mission stroll is slower than a garden dash

/**
 * A mission world as a living diorama in the flat 3/4 view, on the game's shared pixel
 * grid (coherence plan, step 7): the companion strolls its route, pausing to look
 * around, while the player is away, and the camera follows it. Purely scenery, so it
 * has no touch targets and is hidden from assistive tech (the mission text says it).
 */
export function WorldScene({
  world,
  width,
  player,
  active: screenActive = true,
  still = false,
  viewportHeight,
  focus,
}: {
  world: WorldId;
  width: number;
  player: Player;
  active?: boolean;
  /** static preview (Missions tab): no walking, no animation */
  still?: boolean;
  /** the window's height; the whole world's height when left out */
  viewportHeight?: number;
  /** a still window's top-left in world pixels (previews frame their landmark) */
  focus?: { left: number; top: number };
}) {
  const reduced = useReducedMotion();
  const appActive = useAppActive();
  const active = screenActive && appActive;
  const map = worldMaps[world];
  const grid = grids.get(world) ?? gridFor(world);
  const screen = useWindowDimensions();
  const dpr = PixelRatio.get();
  const scale = pixelScale(screen.width, dpr);
  const snap = (value: number) => snapToDevice(value, dpr);
  const worldWidth = Math.round(WORLD.width * scale);
  const worldHeight = Math.round(WORLD.height * scale);
  const viewHeight = Math.min(worldHeight, viewportHeight ?? worldHeight);
  const petPx = 32 * scale;
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

  const petStyle = useAnimatedStyle(() => ({
    transform: [
      { translateX: Math.round(px.value * scale - petPx / 2) },
      { translateY: Math.round(py.value * scale - petPx * (30 / 32)) },
    ],
    zIndex: Math.round(py.value),
  }));
  // The camera holds a preview's framing, or keeps the companion a little above
  // centre and across, clamped to the world.
  const cameraStyle = useAnimatedStyle(() => {
    const x = focus ? focus.left : windowStart(px.value * scale, width, worldWidth);
    const y = focus
      ? focus.top
      : Math.max(0, Math.min(worldHeight - viewHeight, py.value * scale - viewHeight * 0.55));
    return { transform: [{ translateX: -Math.round(x) }, { translateY: -Math.round(y) }] };
  });

  // Who you might bump into on this journey (scenery only: no rewards or rules).
  const resident = worldCatalogue[world].resident;
  const images = worldImages[world];
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
        height: viewHeight,
        overflow: 'hidden',
        backgroundColor: world === 'mountain' ? '#6A9468' : '#73A85E',
      }}
    >
      <Animated.View
        style={[
          { position: 'absolute', left: 0, top: 0, width: worldWidth, height: worldHeight },
          cameraStyle,
        ]}
      >
        <Image
          source={images.ground}
          resizeMode="stretch"
          style={{ position: 'absolute', left: 0, top: 0, width: worldWidth, height: worldHeight }}
        />
        {map.water.map((water) => (
          <Image
            key={`water-${water.x}-${water.y}`}
            source={images.water[moving ? frame : 0]}
            resizeMode="stretch"
            style={{
              position: 'absolute',
              left: snap(water.x * scale),
              top: snap(water.y * scale),
              width: snap(water.w * scale),
              height: snap(water.h * scale),
            }}
          />
        ))}
        {map.objects.map((o) => (
          <Image
            key={o.id}
            source={worldProps[o.sprite]}
            resizeMode="stretch"
            style={{
              position: 'absolute',
              left: snap(o.x * scale),
              top: snap(o.y * scale),
              width: snap(o.w * scale),
              height: snap(o.h * scale),
              zIndex: o.y + o.h,
            }}
          />
        ))}
        <View
          style={{
            position: 'absolute',
            left: Math.round(map.visitor.x * scale - petPx / 2),
            top: Math.round(map.visitor.y * scale - petPx * (30 / 32)),
            width: petPx,
            height: petPx,
            zIndex: map.visitor.y,
          }}
        >
          <Pet visitor={resident} size={petPx} bob={moving} active={moving} />
        </View>
        <Animated.View
          style={[{ position: 'absolute', left: 0, top: 0, width: petPx, height: petPx }, petStyle]}
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
              width: worldWidth,
              height: worldHeight,
              zIndex: 900,
              backgroundColor: night ? 'rgba(22,28,66,0.42)' : 'rgba(240,128,70,0.14)',
            }}
          />
        )}
      </Animated.View>
    </View>
  );
}

/** A window onto a world framed on its landmark, for mission cards (static, no walking). */
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
  const screen = useWindowDimensions();
  const scale = pixelScale(screen.width, PixelRatio.get());
  const sceneWidth = Math.max(0, width - 4);
  const frame = sceneWidth
    ? worldPreviewFrame(world, sceneWidth, Math.max(0, height - 4), scale)
    : null;
  return (
    <View
      onLayout={(e) => setWidth(Math.round(e.nativeEvent.layout.width))}
      style={{
        height: frame ? frame.height + 4 : height,
        borderRadius: 0,
        overflow: 'hidden',
        borderWidth: 2,
        borderColor: '#2A2421',
      }}
    >
      {frame && (
        <WorldScene
          world={world}
          width={sceneWidth}
          player={player}
          still
          viewportHeight={frame.height}
          focus={{ left: frame.left, top: frame.top }}
        />
      )}
    </View>
  );
}
