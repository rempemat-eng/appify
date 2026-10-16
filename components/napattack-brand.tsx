import { useEffect } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import Svg, { Rect } from 'react-native-svg';
import Animated, { useAnimatedStyle, useSharedValue, withTiming } from 'react-native-reanimated';
import { CozyBackground } from '@/components/cozy-ui';
import { cozy as c } from '@/lib/cozy';
import { petPixels } from '@/lib/pet-art';
import { useReducedMotion } from '@/lib/motion';
import { useGame } from '@/lib/game';

const edges = [
  [-2, 0],
  [2, 0],
  [0, -2],
  [0, 2],
  [-1, -1],
  [1, -1],
  [-1, 1],
  [1, 1],
] as const;
function Lettering({
  text,
  color,
  outline,
  size,
}: {
  text: string;
  color: string;
  outline: string;
  size: number;
}) {
  const type = { fontFamily: 'PressStart2P_400Regular', fontSize: size, lineHeight: size + 12 };
  return (
    <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
      {edges.map(([x, y]) => (
        <Text
          key={`${x},${y}`}
          accessible={false}
          style={[type, { position: 'absolute', left: x, top: y, color: outline }]}
        >
          {text}
        </Text>
      ))}
      <Text
        accessible={false}
        style={[
          type,
          {
            color,
            textShadowColor: c.shadow,
            textShadowOffset: { width: 0, height: 3 },
            textShadowRadius: 3,
          },
        ]}
      >
        {text}
      </Text>
    </View>
  );
}
export function NapAttackWordmark({ size = 24 }: { size?: number }) {
  return (
    <View
      accessible
      accessibilityRole="image"
      accessibilityLabel="NAPATTACK"
      style={{ alignSelf: 'center', flexDirection: 'row', paddingTop: 20, paddingHorizontal: 4 }}
    >
      <View>
        <Lettering text="NAP" color={c.nap} outline={c.napOutline} size={size} />
        <Text
          accessible={false}
          style={{
            position: 'absolute',
            right: 5,
            top: -17,
            color: c.napOutline,
            fontFamily: 'PressStart2P_400Regular',
            fontSize: 11,
          }}
        >
          z
        </Text>
      </View>
      <View>
        <Lettering text="ATTACK" color={c.roam} outline={c.leafOutline} size={size} />
        <Svg
          width={18}
          height={18}
          viewBox="0 0 9 9"
          style={{ position: 'absolute', top: -12, left: 4 }}
        >
          <Rect x={3} y={1} width={5} height={2} fill={c.leafOutline} />
          <Rect x={2} y={3} width={5} height={3} fill={c.leafOutline} />
          <Rect x={3} y={2} width={4} height={2} fill={c.roam} />
          <Rect x={2} y={4} width={3} height={1} fill={c.roam} />
          <Rect x={1} y={6} width={2} height={1} fill={c.leafOutline} />
        </Svg>
      </View>
    </View>
  );
}
export function SleepingGrassling({ size = 192 }: { size?: number }) {
  const unit = Math.max(1, Math.floor(size / 32));
  return (
    <Svg
      accessibilityLabel="A sleeping Grassling on a pillow"
      width={unit * 32}
      height={unit * 36}
      viewBox="0 0 32 36"
    >
      <Rect x={5} y={28} width={23} height={6} fill={c.napOutline} />
      <Rect x={3} y={29} width={27} height={3} fill={c.napOutline} />
      <Rect x={5} y={28} width={23} height={4} fill={c.rest} />
      <Rect x={4} y={29} width={25} height={2} fill={c.rest} />
      <Rect x={6} y={32} width={21} height={1} fill={c.paper} />
      <Rect x={27} y={24} width={2} height={5} fill={c.ink} />
      <Rect x={27} y={20} width={3} height={4} fill={c.leafOutline} />
      <Rect x={28} y={19} width={2} height={4} fill={c.roam} />
      {petPixels('BLOB', 1, null, true, false)
        .filter((p) => p.y < 30)
        .map((p) => (
          <Rect key={`${p.x},${p.y}`} x={p.x} y={p.y} width={1} height={1} fill={p.color} />
        ))}
    </Svg>
  );
}
export function NapAttackSplash({ onFinish }: { onFinish: (done: boolean) => void }) {
  const ready = useGame((s) => s.ready);
  const reduced = useReducedMotion();
  const alpha = useSharedValue(1);
  const motion = useAnimatedStyle(() => ({ opacity: alpha.value }));
  useEffect(() => {
    if (!ready) return undefined;
    const fade = setTimeout(
      () => alpha.set(withTiming(0, { duration: reduced ? 100 : 250 })),
      reduced ? 100 : 450,
    );
    const hide = setTimeout(() => onFinish(true), reduced ? 200 : 700);
    return () => {
      clearTimeout(fade);
      clearTimeout(hide);
    };
  }, [ready, reduced, alpha, onFinish]);
  return (
    <Animated.View
      pointerEvents="none"
      style={[
        StyleSheet.absoluteFill,
        { zIndex: 1000, alignItems: 'center', justifyContent: 'center', gap: 24 },
        motion,
      ]}
    >
      <CozyBackground />
      <NapAttackWordmark />
      <SleepingGrassling />
      <Text style={{ fontFamily: 'Nunito_600SemiBold', fontSize: 15, color: c.ink }}>
        nap to grow. wake to raid.
      </Text>
    </Animated.View>
  );
}
