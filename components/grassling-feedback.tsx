import { useReducedMotion } from '@/lib/motion';
import { useEffect } from 'react';
import { StyleSheet, View } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withTiming,
} from 'react-native-reanimated';
import Svg, { Rect } from 'react-native-svg';
import { palette as c, type Player } from '@/lib/game';
import { petPixels } from '@/lib/pet-art';
import { PixelIcon } from '@/components/pixel-icon';

export function SeedPacket({ species, size = 64 }: { species: Player['species']; size?: number }) {
  const pixels = petPixels(species, 1, null, false, false);
  return (
    <Svg
      width={size}
      height={size * 1.25}
      viewBox="0 0 32 40"
      accessibilityLabel={`${species === 'BLOB' ? 'Mossling' : species === 'RAT' ? 'Roamling' : 'Pebbling'} seed packet`}
    >
      <Rect x={3} y={0} width={26} height={39} fill={c.ink} />
      <Rect x={4} y={1} width={24} height={37} fill={c.paper} />
      <Rect x={4} y={1} width={24} height={5} fill={c.body} />
      <Rect x={6} y={8} width={20} height={21} fill={c.stone} />
      {pixels.map((p) => (
        <Rect
          key={`${p.x}-${p.y}`}
          x={7 + p.x / 2}
          y={10 + p.y / 2}
          width={0.5}
          height={0.5}
          fill={p.color}
        />
      ))}
      <Rect x={7} y={32} width={18} height={2} fill={c.moss} />
      <Rect x={10} y={35} width={12} height={1} fill={c.ink} />
    </Svg>
  );
}
export function Planting({ children }: { children: React.ReactNode }) {
  const reduced = useReducedMotion();
  const progress = useSharedValue(0);
  useEffect(() => {
    progress.set(withTiming(1, { duration: reduced ? 0 : 900 }));
  }, [progress, reduced]);
  const rise = useAnimatedStyle(() => ({
    opacity: progress.value,
    transform: [{ translateY: reduced ? 0 : Math.round((1 - progress.value) * 65) }],
  }));
  const dirt = useAnimatedStyle(() => ({
    opacity: 1 - progress.value,
    transform: [{ translateY: -Math.round(progress.value * 65) }, { scale: 1 + progress.value }],
  }));
  return (
    <View style={{ alignItems: 'center' }}>
      <Animated.View style={rise}>{children}</Animated.View>
      <Animated.View
        pointerEvents="none"
        style={[{ position: 'absolute', bottom: 10, flexDirection: 'row', gap: 13 }, dirt]}
      >
        {[0, 1, 2, 3, 4].map((i) => (
          <View
            key={i}
            style={{ width: 6, height: 6, backgroundColor: c.shade, marginTop: (i % 2) * 16 }}
          />
        ))}
      </Animated.View>
    </View>
  );
}
export function PetalFall() {
  const reduced = useReducedMotion();
  const progress = useSharedValue(0);
  useEffect(() => {
    if (!reduced) progress.set(withTiming(1, { duration: 1600 }));
  }, [progress, reduced]);
  const motion = useAnimatedStyle(() => ({
    transform: [{ translateY: progress.value * 450 }],
    opacity: 1 - progress.value * 0.4,
  }));
  if (reduced) return null;
  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      <Animated.View style={[{ height: 200 }, motion]}>
        <Svg width="100%" height={200} viewBox="0 0 160 100">
          {Array.from({ length: 22 }, (_, i) => (
            <Rect
              key={i}
              x={(i * 43) % 156}
              y={(i * 31) % 97}
              width={3}
              height={i % 2 ? 2 : 4}
              fill={i % 3 ? c.body : c.error}
            />
          ))}
        </Svg>
      </Animated.View>
    </View>
  );
}
export function DreamDustFlight({ toLeft = true }: { toLeft?: boolean }) {
  const reduced = useReducedMotion();
  const progress = useSharedValue(0);
  useEffect(() => {
    if (!reduced) progress.set(withRepeat(withTiming(1, { duration: 1100 }), -1, false));
  }, [progress, reduced]);
  const motion = useAnimatedStyle(() => ({
    opacity: reduced ? 1 : 1 - Math.abs(progress.value - 0.5) * 2,
    transform: [
      { translateX: (toLeft ? -1 : 1) * Math.round(progress.value * 120) },
      { translateY: -Math.round(Math.sin(progress.value * Math.PI) * 30) },
    ],
  }));
  if (reduced) return null;
  return (
    <Animated.View
      pointerEvents="none"
      style={[
        {
          position: 'absolute',
          bottom: 28,
          left: toLeft ? '70%' : '25%',
          flexDirection: 'row',
          gap: 5,
        },
        motion,
      ]}
    >
      <PixelIcon name="dreamDust" size={16} />
      <PixelIcon name="dreamDust" size={24} />
      <PixelIcon name="dreamDust" size={16} />
    </Animated.View>
  );
}
