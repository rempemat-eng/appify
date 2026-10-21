import { useEffect, useRef } from 'react';
import { Image, View, type ImageSourcePropType } from 'react-native';
import Animated, {
  cancelAnimation,
  Easing,
  runOnJS,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withTiming,
  type SharedValue,
} from 'react-native-reanimated';
import { useReducedMotion } from '@/lib/motion';
import { useAppActive } from '@/lib/app-active';
import { JOURNEY, journeyLayers, journeyVehicles } from '@/lib/journey-assets';
import { BodyText } from '@/components/pixel-feedback';
import { PixelButton } from '@/components/game-ui';
import { PixelFrame } from '@/components/pixel-frame';
import { GuardianPet } from '@/components/guardian-pet';
import { useGame } from '@/lib/game';
import { flightOf } from '@/lib/rocket-flight';
import { RocketScene } from '@/components/rocket-journey';

const TRIP_MS = 3200;
const STILL_MS = 700; // reduced motion: a still frame, then on

/** One scrolling layer: copies side by side, slid left by its share of the trip. */
function Strip({
  source,
  loops,
  t,
  loopW,
  h,
  top,
  copies,
}: {
  source: ImageSourcePropType;
  loops: number;
  t: SharedValue<number>;
  loopW: number;
  h: number;
  top: number;
  copies: number;
}) {
  const style = useAnimatedStyle(() => ({
    transform: [{ translateX: Math.round(((t.value * loops) % 1) * loopW) - loopW }],
  }));
  return (
    <Animated.View style={[{ position: 'absolute', left: 0, top, flexDirection: 'row' }, style]}>
      {Array.from({ length: copies }, (_, i) => (
        <Image
          key={`copy-${i}`}
          source={source}
          resizeMode="stretch"
          style={{ width: loopW, height: h }}
        />
      ))}
    </Animated.View>
  );
}

export type JourneyVehicle = 'train' | 'maglev' | 'carts' | 'rocket' | 'shuttle' | 'ferry';

/**
 * The trip between regions (world-atlas.md, "Seamless travel": between regions the
 * journey is the transition). The view from beside the line: sky, far land and near
 * land scroll past at their own speeds while the train holds the middle. Up to Halcyon
 * and down again the rocket flies, and to the moon and back the lander
 * (components/rocket-journey.tsx). It plays once, can be skipped, stops if the screen goes
 * inactive (and then simply arrives), and is a still frame with reduced motion (the rocket
 * and the lander: a short cross-fade from the first still to the last). Arriving is the
 * only thing it does, and never after the journey has left the screen.
 */
export function Journey({
  to,
  label,
  width,
  height,
  u,
  onArrive,
  insetTop = 0,
  insetBottom = 0,
  ms = TRIP_MS,
  onSkip,
  vehicle,
}: {
  to: keyof typeof journeyLayers;
  label: string;
  width: number;
  height: number;
  u: number;
  onArrive: () => void;
  /** Safe-area room at the top and bottom, so the label and SKIP stay clear of it. */
  insetTop?: number;
  insetBottom?: number;
  /** How long this leg takes (a trip of several legs plays each a little quicker). */
  ms?: number;
  /** SKIP ends the whole trip (defaults to arriving at the end of this leg). */
  onSkip?: () => void;
  /** What carries the companion on this line (defaults by destination). */
  vehicle?: JourneyVehicle;
}) {
  const reduced = useReducedMotion();
  const active = useAppActive();
  const t = useSharedValue(0);
  const done = useRef(false);
  // (cleared when the journey leaves the screen: a finish still on its way then does nothing)
  const alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);
  const ride: JourneyVehicle =
    vehicle ?? (to === 'space' ? 'rocket' : to === 'moon' ? 'shuttle' : 'train');
  const flight = flightOf(ride, to);
  // the rocket and the lander keep their own beats, so their clock runs evenly
  const easing = flight ? Easing.linear : Easing.inOut(Easing.quad);
  // reduced motion: the first still, then the last faded in over it
  const fade = useSharedValue(0);
  const skip = () => {
    if (done.current) return;
    done.current = true;
    (onSkip ?? onArrive)();
  };
  useEffect(() => {
    const finish = () => {
      if (done.current || !alive.current) return;
      done.current = true;
      onArrive();
    };
    if (!active) {
      cancelAnimation(t);
      cancelAnimation(fade);
      finish();
      return undefined;
    }
    if (reduced) {
      if (flight) fade.set(withDelay(STILL_MS * 0.35, withTiming(1, { duration: STILL_MS * 0.3 })));
      const s = setTimeout(finish, STILL_MS);
      return () => {
        clearTimeout(s);
        cancelAnimation(fade);
      };
    }
    t.set(
      withTiming(1, { duration: ms, easing }, (finished) => {
        if (finished) runOnJS(finish)();
      }),
    );
    return () => cancelAnimation(t);
  }, [active, reduced, t, fade, onArrive, ms, easing, flight]);

  const layers = journeyLayers[to];
  const lw = JOURNEY.width * u; // one loop of a layer
  const lh = JOURNEY.height * u;
  // the band at twice the grid on a tall screen, the rest filled with sky above and ground below
  const scale = height > 2.4 * lh ? 2 : 1;
  const viewH = lh * scale;
  const top = (height - viewH) / 2;
  const copies = Math.ceil(width / (lw * scale)) + 2;
  const bob = useAnimatedStyle(() => ({
    transform: [{ translateY: Math.round(Math.sin(t.value * 80) * 0.6 * u * scale) }],
  }));
  const rider =
    ride === 'maglev'
      ? journeyVehicles.maglev
      : ride === 'ferry'
        ? journeyVehicles.ferry
        : journeyVehicles.carts;
  const engine = journeyVehicles.engine;
  const coach = journeyVehicles.carriage;
  // the companion rides along: on the coach roof, or sat in the first coal tub
  const player = useGame((st) => st.player);
  const k = u * scale;
  const petPx = 32 * k;
  const railY = top + JOURNEY.rail * k;
  // the ferry sits in the swell, its waterline a little below the sea's surface line
  const riderTop = railY - (rider.h + (ride === 'maglev' ? 3 : ride === 'ferry' ? -6 : -2)) * k;
  const chrome = (
    <>
      <View
        style={{
          position: 'absolute',
          top: insetTop + 16,
          left: 0,
          right: 0,
          alignItems: 'center',
        }}
      >
        <PixelFrame tone="paper" style={{ paddingVertical: 4 * u, paddingHorizontal: 8 * u }}>
          <BodyText
            style={{ fontFamily: 'PixelifySans_700Bold', fontSize: 14 }}
          >{`TO ${label}`}</BodyText>
        </PixelFrame>
      </View>
      <View style={{ position: 'absolute', bottom: insetBottom + 16, right: 16, width: 110 }}>
        <PixelButton small light label="SKIP" onPress={skip} />
      </View>
    </>
  );
  if (flight)
    return (
      <View
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          width,
          height,
          overflow: 'hidden',
          backgroundColor: '#05040A',
          zIndex: 10,
        }}
      >
        {reduced ? (
          <StillPair
            flight={flight}
            width={width}
            height={height}
            u={u}
            ms={ms}
            fade={fade}
            insetTop={insetTop}
            insetBottom={insetBottom}
          />
        ) : (
          <RocketScene
            flight={flight}
            t={t}
            width={width}
            height={height}
            u={u}
            ms={ms}
            insetTop={insetTop}
            insetBottom={insetBottom}
          />
        )}
        {chrome}
      </View>
    );
  return (
    <View
      // @ts-expect-error dataSet is a react-native-web prop (crisp pixel scaling via CSS)
      dataSet={{ pixel: 'true' }}
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        width,
        height,
        overflow: 'hidden',
        backgroundColor: layers.below,
        zIndex: 10,
      }}
    >
      <View
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          width,
          height: top + 1,
          backgroundColor: layers.above,
        }}
      />
      {/* speeds in loops per trip: the near land rushes, the sky barely moves */}
      <Strip
        source={layers.sky}
        loops={0.25}
        t={t}
        loopW={lw * scale}
        h={viewH}
        top={top}
        copies={copies}
      />
      <Strip
        source={layers.far}
        loops={1}
        t={t}
        loopW={lw * scale}
        h={viewH}
        top={top}
        copies={copies}
      />
      <Strip
        source={layers.near}
        loops={4}
        t={t}
        loopW={lw * scale}
        h={viewH}
        top={top}
        copies={copies}
      />
      <Animated.View style={[{ position: 'absolute', left: 0, top: 0, width, height }, bob]}>
        {ride === 'train' ? (
          <>
            <Image
              source={engine.source}
              resizeMode="stretch"
              style={{
                position: 'absolute',
                left: width * 0.42 - (engine.w * k) / 2,
                top: railY - (engine.h - 3) * k,
                width: engine.w * k,
                height: engine.h * k,
              }}
            />
            <Image
              source={coach.source}
              resizeMode="stretch"
              style={{
                position: 'absolute',
                left: width * 0.42 + (engine.w * k) / 2 - 2 * k,
                top: railY - (coach.h - 3) * k,
                width: coach.w * k,
                height: coach.h * k,
              }}
            />
            {player && (
              <View
                style={{
                  position: 'absolute',
                  left: width * 0.42 + (engine.w * k) / 2 + 2 * k,
                  top: railY - (coach.h - 3) * k - petPx + 3 * k,
                  width: petPx,
                  height: petPx,
                }}
              >
                <GuardianPet player={player} size={petPx} facing="left" bob={false} decorative />
              </View>
            )}
          </>
        ) : (
          <>
            {ride === 'carts' && player && (
              <View
                style={{
                  position: 'absolute',
                  left: width * 0.5 - (rider.w * k) / 2 - 3 * k,
                  top: railY - (rider.h - 2) * k - petPx + 13 * k,
                  width: petPx,
                  height: petPx,
                }}
              >
                <GuardianPet player={player} size={petPx} facing="left" bob={false} decorative />
              </View>
            )}
            {ride === 'ferry' && player && (
              // on the ferry's foredeck, in front of the cabin
              <View
                style={{
                  position: 'absolute',
                  left: width * 0.5 - (rider.w * k) / 2 + 8 * k,
                  top: riderTop + 22 * k - petPx + 3 * k,
                  width: petPx,
                  height: petPx,
                  zIndex: 1,
                }}
              >
                <GuardianPet player={player} size={petPx} facing="left" bob={false} decorative />
              </View>
            )}
            {/* the maglev floats a little above the line; the mine carts sit on it */}
            <Image
              source={rider.source}
              resizeMode="stretch"
              style={{
                position: 'absolute',
                left: width * 0.5 - (rider.w * k) / 2,
                top: riderTop,
                width: rider.w * k,
                height: rider.h * k,
              }}
            />
          </>
        )}
      </Animated.View>
      {chrome}
    </View>
  );
}

/** Reduced motion for the rocket and the lander: the first still (on the pad, or docked),
 *  and the last faded in over it. Nothing else moves. */
function StillPair({
  flight,
  width,
  height,
  u,
  ms,
  fade,
  insetTop,
  insetBottom,
}: {
  flight: NonNullable<ReturnType<typeof flightOf>>;
  width: number;
  height: number;
  u: number;
  ms: number;
  fade: SharedValue<number>;
  insetTop: number;
  insetBottom: number;
}) {
  const first = useSharedValue(0);
  const last = useSharedValue(1);
  const fadeIn = useAnimatedStyle(() => ({ opacity: fade.value }));
  return (
    <>
      <RocketScene
        flight={flight}
        t={first}
        width={width}
        height={height}
        u={u}
        ms={ms}
        insetTop={insetTop}
        insetBottom={insetBottom}
      />
      <Animated.View
        style={[{ position: 'absolute', left: 0, top: 0, width, height }, fadeIn]}
        pointerEvents="none"
      >
        <RocketScene
          flight={flight}
          t={last}
          width={width}
          height={height}
          u={u}
          ms={ms}
          insetTop={insetTop}
          insetBottom={insetBottom}
        />
      </Animated.View>
    </>
  );
}
