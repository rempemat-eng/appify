import { useMemo } from 'react';
import { Image, type ImageSourcePropType } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useDerivedValue,
  type SharedValue,
} from 'react-native-reanimated';
import { animalAt, animalPlan, flatEvents } from '@/lib/animal-life';
import { zoneAnimals, type AnimalFrame, type ZoneId } from '@/lib/zone-maps';
import { zoneProps } from '@/lib/zone-assets';

/** A placed animal as the walk draws it: its still's box in region px and its depth. */
export type AnimalDrawable = {
  key: string;
  sprite: string;
  src: ImageSourcePropType;
  x: number;
  y: number;
  w: number;
  h: number;
  z: number;
};

/** Whether a sprite is an animal that lives (scripts/art/animal_frames.py). */
export const isAnimal = (sprite: string) => sprite in zoneAnimals;

/** The animal's own shadow sits above the ground and below every prop (as a flyer's). */
const SHADE_Z = 2;

/** One frame of one side: shown while the animal's state names it (side -1: either side). */
function Layer({
  frame,
  index,
  side,
  state,
  u,
  snap,
}: {
  frame: AnimalFrame;
  index: number;
  side: number;
  state: SharedValue<{ x: number; y: number; code: number }>;
  u: number;
  snap: (v: number) => number;
}) {
  const [key, dx, dy, w, h] = frame;
  const shown = useAnimatedStyle(() => {
    const code = state.value.code;
    return {
      opacity: code % 16 === index && (side < 0 || Math.floor(code / 16) === side) ? 1 : 0,
    };
  });
  return (
    <Animated.Image
      source={zoneProps[key]}
      resizeMode="stretch"
      style={[
        {
          position: 'absolute',
          left: snap(dx * u),
          top: snap(dy * u),
          width: snap(w * u),
          height: snap(h * u),
        },
        shown,
      ]}
    />
  );
}

/**
 * One animal (art-faults.md A9). Running, it lives on the walk's shared clock (stopped
 * with reduced motion or an inactive screen): its idle accents, and for the ones that move
 * a short wander from home and back, facing the way it goes with the frames drawn for that
 * side, its shadow going with it. Not running, it stands still as placed. It never takes a
 * tap (the whole scene layer ignores touches) and never changes the walk grid.
 */
export function Animal({
  d,
  zone,
  oid,
  clock,
  running,
  u,
  snap,
}: {
  d: AnimalDrawable;
  zone: ZoneId;
  oid: string;
  clock: SharedValue<number>;
  running: boolean;
  u: number;
  snap: (v: number) => number;
}) {
  const kind = zoneAnimals[d.sprite];
  const plan = useMemo(() => animalPlan(zone, oid, kind), [zone, oid, kind]);
  const flat = useMemo(() => flatEvents(plan), [plan]);
  const { period, phase } = plan;
  const walk = kind.walk;
  const stepMs = kind.stepMs;
  // the side and frame shown, as one code (side * 16 + frame), and the offset from home
  const state = useDerivedValue(() => {
    const at = animalAt(flat, period, phase, walk, stepMs, clock.value);
    return { x: at.x, y: at.y, code: at.side * 16 + at.frame };
  });
  const place = useAnimatedStyle(() => ({
    transform: [{ translateX: state.value.x * u }, { translateY: state.value.y * u }],
  }));
  const shade = kind.shade;
  const box = {
    position: 'absolute' as const,
    left: snap(d.x * u),
    top: snap(d.y * u),
    width: snap(d.w * u),
    height: snap(d.h * u),
  };
  const shadeStyle = shade && {
    position: 'absolute' as const,
    left: snap((d.x + shade[1]) * u),
    top: snap((d.y + shade[2]) * u),
    width: snap(shade[3] * u),
    height: snap(shade[4] * u),
    zIndex: SHADE_Z,
  };
  if (!running)
    return (
      <>
        {shade && shadeStyle && (
          <Image
            source={zoneProps[shade[0]]}
            resizeMode="stretch"
            style={{ ...shadeStyle, width: shadeStyle.width, height: shadeStyle.height }}
          />
        )}
        <Image
          source={d.src}
          resizeMode="stretch"
          style={{ ...box, width: box.width, height: box.height, zIndex: d.z }}
        />
      </>
    );
  // the east set, and the west set where it is drawn differently
  const sameWest = kind.west.every((f, i) => f[0] === kind.east[i]?.[0]);
  const sides: [number, readonly AnimalFrame[]][] = sameWest
    ? [[0, kind.east]]
    : [
        [0, kind.east],
        [1, kind.west],
      ];
  return (
    <>
      {shade && shadeStyle && (
        <Animated.Image
          source={zoneProps[shade[0]]}
          resizeMode="stretch"
          style={[shadeStyle, place]}
        />
      )}
      <Animated.View style={[{ ...box, zIndex: d.z }, place, { pointerEvents: 'none' }]}>
        {sides.flatMap(([side, frames]) =>
          frames
            .map((f, i) => ({ f, slot: i, id: `${side}:${i}:${f[0]}` }))
            .map(({ f, slot, id }) => (
              <Layer
                key={id}
                frame={f}
                index={slot}
                // (a kind drawn one way only shows the same pictures whichever way it goes)
                side={sameWest ? -1 : side}
                state={state}
                u={u}
                snap={snap}
              />
            )),
        )}
      </Animated.View>
    </>
  );
}
