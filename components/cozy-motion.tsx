import { type ReactNode, useEffect, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import Animated, {
  cancelAnimation,
  useAnimatedStyle,
  useSharedValue,
  withSequence,
  withTiming,
} from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';
import { cozy as c } from '@/lib/cozy';
import { useReducedMotion } from '@/lib/motion';
import { CardIllustration } from '@/components/habit-cards';
import { PixelProp } from '@/components/pixel-scenes';
import { PixelText } from '@/components/game-ui';
import { GuardianPet } from '@/components/guardian-pet';
import { cards, type CardId } from '@/lib/cards';
import type { Player } from '@/lib/game';

// Effects never own game transitions. A skip only completes presentation.
export function LightSweep({ night = false, skip = false }: { night?: boolean; skip?: boolean }) {
  const reduced = useReducedMotion();
  const progress = useSharedValue(0);
  useEffect(() => {
    progress.set(skip ? 1 : withTiming(1, { duration: reduced ? 100 : night ? 1000 : 800 }));
    return () => cancelAnimation(progress);
  }, [progress, skip, reduced, night]);
  const motion = useAnimatedStyle(() => ({
    opacity: (1 - progress.value) * (night ? 0.65 : 0.45),
    transform: [{ translateX: reduced || night ? 0 : progress.value * 160 }],
  }));
  return (
    <Animated.View pointerEvents="none" style={[StyleSheet.absoluteFill, motion]}>
      <LinearGradient
        colors={[c.amber, c.paper, c.transparent]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={StyleSheet.absoluteFill}
      />
    </Animated.View>
  );
}
export function PixelBurst({ hearts = false, skip = false }: { hearts?: boolean; skip?: boolean }) {
  const reduced = useReducedMotion();
  const progress = useSharedValue(0);
  useEffect(() => {
    progress.set(skip ? 1 : withTiming(1, { duration: reduced ? 100 : 600 }));
    return () => cancelAnimation(progress);
  }, [progress, reduced, skip]);
  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      {Array.from({ length: 8 }, (_, i) => (
        <BurstParticle key={i} i={i} progress={progress} reduced={reduced} hearts={hearts} />
      ))}
    </View>
  );
}
function BurstParticle({
  i,
  progress,
  reduced,
  hearts,
}: {
  i: number;
  progress: ReturnType<typeof useSharedValue<number>>;
  reduced: boolean;
  hearts: boolean;
}) {
  const angle = (i * Math.PI) / 4;
  const motion = useAnimatedStyle(() => ({
    opacity: 1 - progress.value,
    transform: [
      { translateX: reduced ? 0 : Math.round(Math.cos(angle) * progress.value * 60) },
      {
        translateY: reduced
          ? 0
          : Math.round(Math.sin(angle) * progress.value * 50 - progress.value * 16),
      },
    ],
  }));
  return (
    <Animated.View style={[{ position: 'absolute', left: '50%', top: '50%' }, motion]}>
      <PixelProp kind={hearts ? 'heart' : 'grass'} size={16} />
    </Animated.View>
  );
}
export function PlayedCard({
  id,
  toLeft,
  distance,
  skip,
}: {
  id: CardId;
  toLeft: boolean;
  distance: number;
  skip: boolean;
}) {
  const reduced = useReducedMotion();
  const p = useSharedValue(0);
  useEffect(() => {
    p.set(skip ? 1 : withTiming(1, { duration: reduced ? 100 : 160 }));
    return () => cancelAnimation(p);
  }, [p, skip, reduced]);
  const motion = useAnimatedStyle(() => ({
    opacity: 1 - p.value,
    transform: [
      { translateX: reduced ? 0 : (toLeft ? -1 : 1) * p.value * distance },
      { translateY: reduced ? 0 : -Math.sin(p.value * Math.PI) * 48 },
      { rotate: `${reduced ? 0 : (toLeft ? -1 : 1) * p.value * 12}deg` },
    ],
  }));
  return (
    <Animated.View
      pointerEvents="none"
      style={[
        {
          position: 'absolute',
          left: toLeft ? '65%' : '12%',
          top: '40%',
          width: 64,
          padding: 8,
          borderRadius: 0,
          borderWidth: 2,
          borderColor: c.outline,
          backgroundColor: c.paper,
          zIndex: 10,
        },
        motion,
      ]}
    >
      <CardIllustration id={id} />
      <PixelText style={{ fontSize: 11 }} numberOfLines={2}>
        {cards[id].name}
      </PixelText>
    </Animated.View>
  );
}
export function PerfectImpact({
  children,
  perfect,
  skip,
  impact,
}: {
  children: ReactNode;
  perfect: boolean;
  skip: boolean;
  impact: number;
}) {
  const reduced = useReducedMotion();
  const x = useSharedValue(0);
  const alpha = useSharedValue(1);
  useEffect(() => {
    if (impact === 0) return undefined;
    x.set(
      perfect && !reduced && !skip
        ? withSequence(
            withTiming(-4, { duration: 30 }),
            withTiming(4, { duration: 30 }),
            withTiming(-4, { duration: 30 }),
            withTiming(4, { duration: 30 }),
            withTiming(0, { duration: 30 }),
          )
        : 0,
    );
    alpha.set(1);
    alpha.set(skip ? 0 : withTiming(0, { duration: reduced ? 100 : 600 }));
    return () => {
      cancelAnimation(x);
      cancelAnimation(alpha);
    };
  }, [x, alpha, perfect, reduced, skip, impact]);
  const shake = useAnimatedStyle(() => ({ transform: [{ translateX: x.value }] }));
  const stamp = useAnimatedStyle(() => ({ opacity: alpha.value }));
  return (
    <Animated.View style={[{ flex: 1 }, shake]}>
      {children}
      {perfect && (
        <Animated.View
          pointerEvents="none"
          style={[
            {
              position: 'absolute',
              top: 16,
              alignSelf: 'center',
              backgroundColor: c.amber,
              borderRadius: 0,
              padding: 12,
              zIndex: 20,
            },
            stamp,
          ]}
        >
          <PixelText style={{ fontSize: 16 }}>PERFECT!</PixelText>
        </Animated.View>
      )}
    </Animated.View>
  );
}
export function GrowthFrames({ player }: { player: Player }) {
  const reduced = useReducedMotion();
  const [frame, setFrame] = useState(0);
  useEffect(() => {
    let current = 0;
    const timer = setInterval(() => {
      current += 1;
      setFrame(current);
      if (current >= 2) clearInterval(timer);
    }, 150);
    return () => clearInterval(timer);
  }, []);
  return (
    <View>
      <GuardianPet
        player={player}
        level={reduced || frame >= 2 ? player.level : Math.max(1, player.level - 1)}
        bob={false}
        sleeping={!reduced && frame === 1}
      />
      <PixelBurst />
    </View>
  );
}
