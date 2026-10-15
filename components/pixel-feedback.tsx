import { useEffect, useState } from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
  type ColorValue,
  type TextProps,
  type ViewStyle,
} from 'react-native';
import Animated, {
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withTiming,
  withSequence,
  withRepeat,
} from 'react-native-reanimated';
import Svg, { Polygon, Rect } from 'react-native-svg';
import { palette as c } from '@/lib/game';
import { PixelProp } from '@/components/pixel-scenes';
import type { PropKind } from '@/lib/scene-art';

export function BodyText({ style, ...props }: TextProps) {
  return (
    <Text
      {...props}
      style={[
        { fontFamily: 'Silkscreen_400Regular', fontSize: 14, lineHeight: 21, color: c.ink },
        style,
      ]}
    />
  );
}
export function Dialogue({ text, style }: { text: string; style?: ViewStyle }) {
  const reduced = useReducedMotion();
  const [shown, setShown] = useState({ text, count: reduced ? text.length : 0 });
  const [blink, setBlink] = useState(true);
  if (shown.text !== text) setShown({ text, count: reduced ? text.length : 0 });
  useEffect(() => {
    if (shown.count >= text.length) return undefined;
    const timer = setTimeout(() => setShown((old) => ({ ...old, count: old.count + 1 })), 22);
    return () => clearTimeout(timer);
  }, [shown.count, text]);
  useEffect(() => {
    if (reduced) return undefined;
    const timer = setInterval(() => setBlink((b) => !b), 600);
    return () => clearInterval(timer);
  }, [reduced]);
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={text}
      accessibilityHint="Tap to reveal the full message"
      onPress={() => setShown({ text, count: text.length })}
      style={[
        {
          minHeight: 64,
          padding: 14,
          paddingBottom: 21,
          backgroundColor: c.paper,
          borderWidth: 2,
          borderColor: c.ink,
        },
        style,
      ]}
    >
      <BodyText
        accessibilityElementsHidden
        importantForAccessibility="no"
        style={{ fontFamily: 'PressStart2P_400Regular', fontSize: 11, lineHeight: 21 }}
      >
        {text.slice(0, shown.count) || ' '}
      </BodyText>
      <View
        pointerEvents="none"
        style={{ position: 'absolute', right: 8, bottom: 6, opacity: blink ? 1 : 0 }}
      >
        <Svg width={10} height={6} viewBox="0 0 10 6">
          <Polygon points="0,0 10,0 5,6" fill={c.ink} />
        </Svg>
      </View>
    </Pressable>
  );
}
export function GrassRoll({ value }: { value: number }) {
  const [roll, setRoll] = useState({
    target: value,
    start: value,
    display: value,
    delta: 0,
    id: 0,
  });
  if (roll.target !== value)
    setRoll({
      target: value,
      start: roll.display,
      display: roll.display,
      delta: value - roll.target,
      id: roll.id + 1,
    });
  useEffect(() => {
    if (roll.display === roll.target) return undefined;
    const timer = setTimeout(
      () =>
        setRoll((old) => ({
          ...old,
          display:
            old.display +
            Math.sign(old.target - old.display) *
              Math.max(1, Math.ceil(Math.abs(old.target - old.display) / 5)),
        })),
      35,
    );
    return () => clearTimeout(timer);
  }, [roll.display, roll.target]);
  return (
    <View>
      <Text style={{ fontFamily: 'PressStart2P_400Regular', fontSize: 13, color: c.ink }}>
        {roll.display}
      </Text>
      {roll.delta !== 0 && <GrassDelta key={roll.id} amount={roll.delta} />}
    </View>
  );
}
function GrassDelta({ amount }: { amount: number }) {
  const reduced = useReducedMotion();
  const y = useSharedValue(8);
  const opacity = useSharedValue(1);
  useEffect(() => {
    y.set(withTiming(reduced ? 0 : -22, { duration: 1100 }));
    opacity.set(withTiming(0, { duration: 1600 }));
  }, [y, opacity, reduced]);
  const motion = useAnimatedStyle(() => ({
    opacity: opacity.value,
    transform: [{ translateY: y.value }],
  }));
  return (
    <Animated.View
      pointerEvents="none"
      style={[
        {
          position: 'absolute',
          right: 0,
          top: 0,
          flexDirection: 'row',
          alignItems: 'center',
          backgroundColor: c.paper,
          padding: 3,
          zIndex: 10,
        },
        motion,
      ]}
    >
      <BodyText style={{ color: amount > 0 ? c.moss : c.error }}>
        {amount > 0 ? '+' : ''}
        {amount}
      </BodyText>
      <PixelProp kind="grass" size={16} />
    </Animated.View>
  );
}
export function PixelTabIcon({
  kind,
  focused,
  color,
}: {
  kind: PropKind;
  focused: boolean;
  color: ColorValue;
}) {
  const reduced = useReducedMotion();
  const y = useSharedValue(0);
  useEffect(() => {
    if (focused && !reduced)
      y.set(withSequence(withTiming(-5, { duration: 100 }), withTiming(0, { duration: 150 })));
  }, [focused, reduced, y]);
  const motion = useAnimatedStyle(() => ({ transform: [{ translateY: y.value }] }));
  return (
    <Animated.View style={motion}>
      <PixelProp kind={kind} size={24} tint={color} />
    </Animated.View>
  );
}
// The tab layout keys this overlay by route to replay the dissolve on navigation.
export function PixelDissolve() {
  const opacity = useSharedValue(0);
  const reduced = useReducedMotion();
  useEffect(() => {
    if (!reduced) {
      opacity.set(0.75);
      opacity.set(withTiming(0, { duration: 180 }));
    }
  }, [opacity, reduced]);
  const motion = useAnimatedStyle(() => ({ opacity: opacity.value }));
  return (
    <Animated.View pointerEvents="none" style={[StyleSheet.absoluteFill, motion]}>
      <Svg width="100%" height="100%" viewBox="0 0 160 240" preserveAspectRatio="none">
        {Array.from({ length: 150 }, (_, i) => (
          <Rect key={i} x={(i * 43) % 160} y={(i * 71) % 240} width={8} height={8} fill={c.paper} />
        ))}
      </Svg>
    </Animated.View>
  );
}
export function Pulse({
  active,
  color,
  children,
  style,
  duration = 600,
}: {
  active: boolean;
  color?: string;
  duration?: number;
  children?: React.ReactNode;
  style?: ViewStyle;
}) {
  const reduced = useReducedMotion();
  const opacity = useSharedValue(0);
  useEffect(() => {
    opacity.set(
      active
        ? reduced
          ? 0.13
          : withRepeat(
              withSequence(withTiming(0.2, { duration }), withTiming(0.04, { duration })),
              -1,
            )
        : 0,
    );
  }, [active, reduced, opacity, duration]);
  const motion = useAnimatedStyle(() => ({ opacity: opacity.value }));
  return (
    <View style={style}>
      <Animated.View
        pointerEvents="none"
        style={[StyleSheet.absoluteFill, { backgroundColor: color ?? c.error }, motion]}
      />
      {children}
    </View>
  );
}
export function BattleIntro() {
  const reduced = useReducedMotion();
  const [visible, setVisible] = useState(!reduced);
  const [frame, setFrame] = useState(0);
  useEffect(() => {
    if (reduced) return undefined;
    let n = 0;
    const timer = setInterval(() => {
      n++;
      setFrame(n);
      if (n >= 12) {
        clearInterval(timer);
        setVisible(false);
      }
    }, 65);
    return () => clearInterval(timer);
  }, [reduced]);
  if (!visible) return null;
  return (
    <View pointerEvents="none" style={[StyleSheet.absoluteFill, { zIndex: 20 }]}>
      {frame < 6 ? (
        <View
          style={[
            StyleSheet.absoluteFill,
            { backgroundColor: frame % 2 === 0 ? c.flash : 'transparent' },
          ]}
        />
      ) : (
        <Svg width="100%" height="100%" viewBox="0 0 160 240" preserveAspectRatio="none">
          {Array.from({ length: 12 }, (_, i) => (
            <Polygon
              key={i}
              points={`${(frame - 6) * 55 - 330},${i * 24} ${(frame - 6) * 55 - 145},${i * 24} ${(frame - 6) * 55 - 265},${i * 24 + 20} ${(frame - 6) * 55 - 450},${i * 24 + 20}`}
              fill={c.ink}
            />
          ))}
        </Svg>
      )}
    </View>
  );
}
