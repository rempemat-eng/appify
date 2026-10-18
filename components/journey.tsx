import { useEffect, useRef } from 'react';
import { Image, View, type ImageSourcePropType } from 'react-native';
import Animated, {
  cancelAnimation,
  Easing,
  runOnJS,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
  type SharedValue,
} from 'react-native-reanimated';
import { useReducedMotion } from '@/lib/motion';
import { useAppActive } from '@/lib/app-active';
import { JOURNEY, journeyLayers, journeyVehicles } from '@/lib/journey-assets';
import { BodyText } from '@/components/pixel-feedback';
import { PixelButton } from '@/components/game-ui';
import { PixelFrame } from '@/components/pixel-frame';

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

export type JourneyVehicle = 'train' | 'maglev' | 'carts' | 'capsule' | 'shuttle';

/**
 * The trip between regions (world-atlas.md, "Seamless travel": between regions the
 * journey is the transition). The view from beside the line: sky, far land and near
 * land scroll past at their own speeds while the train (or the elevator capsule)
 * holds the middle. It plays once, can be skipped, stops if the screen goes
 * inactive (and then simply arrives), and is a still frame with reduced motion.
 * Arriving is the only thing it does.
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
  const skip = () => {
    if (done.current) return;
    done.current = true;
    (onSkip ?? onArrive)();
  };
  useEffect(() => {
    const finish = () => {
      if (done.current) return;
      done.current = true;
      onArrive();
    };
    if (!active) {
      cancelAnimation(t);
      finish();
      return undefined;
    }
    if (reduced) {
      const s = setTimeout(finish, STILL_MS);
      return () => clearTimeout(s);
    }
    t.set(
      withTiming(1, { duration: ms, easing: Easing.inOut(Easing.quad) }, (finished) => {
        if (finished) runOnJS(finish)();
      }),
    );
    return () => cancelAnimation(t);
  }, [active, reduced, t, onArrive, ms]);

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
  const ride: JourneyVehicle =
    vehicle ?? (to === 'space' ? 'capsule' : to === 'moon' ? 'shuttle' : 'train');
  const flying = ride === 'capsule' || ride === 'shuttle';
  const flyer = ride === 'shuttle' ? journeyVehicles.shuttle : journeyVehicles.capsule;
  const rider = ride === 'maglev' ? journeyVehicles.maglev : journeyVehicles.carts;
  const engine = journeyVehicles.engine;
  const coach = journeyVehicles.carriage;
  const k = u * scale;
  const railY = top + JOURNEY.rail * k;
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
        {flying ? (
          <Image
            source={flyer.source}
            resizeMode="stretch"
            style={{
              position: 'absolute',
              left: width / 2 - (flyer.w * k) / 2,
              top: top + viewH * 0.3,
              width: flyer.w * k,
              height: flyer.h * k,
            }}
          />
        ) : ride === 'train' ? (
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
          </>
        ) : (
          // the maglev floats a little above the line; the mine carts sit on it
          <Image
            source={rider.source}
            resizeMode="stretch"
            style={{
              position: 'absolute',
              left: width * 0.5 - (rider.w * k) / 2,
              top: railY - (rider.h + (ride === 'maglev' ? 3 : -2)) * k,
              width: rider.w * k,
              height: rider.h * k,
            }}
          />
        )}
      </Animated.View>
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
    </View>
  );
}
