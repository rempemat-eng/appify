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
  cancelAnimation,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
  withSequence,
  withRepeat,
  withSpring,
} from 'react-native-reanimated';
import { useReducedMotion } from '@/lib/motion';
import { cozy as c, panelStyle } from '@/lib/cozy';
import { artGeometry } from '@/lib/art-direction';
import { PixelProp } from '@/components/pixel-scenes';
import type { PropKind } from '@/lib/scene-art';
export function BodyText({ style, ...props }: TextProps) {
  return (
    <Text
      {...props}
      style={[
        { fontFamily: 'PixelifySans_500Medium', fontSize: 15, lineHeight: 22, color: c.ink },
        style,
      ]}
    />
  );
}
export function Dialogue({
  text,
  style,
  speech = false,
  onDismiss,
}: {
  text: string;
  style?: ViewStyle;
  speech?: boolean;
  onDismiss?: () => void;
}) {
  const reduced = useReducedMotion();
  const [shown, setShown] = useState({ text, count: reduced ? text.length : 0 });
  if (shown.text !== text) setShown({ text, count: reduced ? text.length : 0 });
  useEffect(() => {
    if (reduced || shown.count >= text.length) return undefined;
    const timer = setTimeout(() => setShown((old) => ({ ...old, count: old.count + 1 })), 22);
    return () => clearTimeout(timer);
  }, [shown.count, text, reduced]);
  const copy = speech ? text.toLowerCase() : text;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={text}
      accessibilityHint={
        onDismiss ? 'Tap to reveal, then dismiss the tip' : 'Tap to reveal the full message'
      }
      onPress={() => {
        if (shown.count < text.length && !reduced) setShown({ text, count: text.length });
        else onDismiss?.();
      }}
      style={[
        {
          ...panelStyle,
          minHeight: 56,
          padding: 12,
          paddingBottom: onDismiss ? 24 : 12,
        },
        style,
      ]}
    >
      <BodyText
        style={{
          fontFamily: speech ? 'PixelifySans_400Regular' : 'PixelifySans_500Medium',
          fontSize: 15,
          lineHeight: 21,
        }}
      >
        {reduced ? copy : copy.slice(0, shown.count) || ' '}
      </BodyText>
      {speech && (
        <View
          pointerEvents="none"
          style={{
            position: 'absolute',
            bottom: -10,
            left: '50%',
            width: 18,
            height: 18,
            backgroundColor: c.paper,
            borderRightWidth: 2,
            borderBottomWidth: 2,
            borderColor: c.outline,
            transform: [{ rotate: '45deg' }],
          }}
        />
      )}
      {onDismiss && (
        <BodyText style={{ position: 'absolute', right: 12, bottom: 4, fontSize: 11 }}>
          tap to dismiss
        </BodyText>
      )}
    </Pressable>
  );
}
export function GrassRoll({
  value,
  from = value,
  skip = false,
  size = 15,
}: {
  value: number;
  from?: number;
  skip?: boolean;
  size?: number;
}) {
  const reduced = useReducedMotion();
  const [roll, setRoll] = useState({ target: value, start: value, display: from, delta: 0, id: 0 });
  useEffect(() => {
    const timer = setInterval(
      () =>
        setRoll((old) => {
          const display =
            reduced || skip
              ? value
              : old.display +
                Math.sign(value - old.display) *
                  Math.max(1, Math.ceil(Math.abs(value - old.display) / 5));
          if (display === value) clearInterval(timer);
          if (old.target === value && old.display === display) return old;
          return {
            target: value,
            start: old.target === value ? old.start : old.display,
            display,
            delta: old.target === value ? old.delta : value - old.target,
            id: old.target === value ? old.id : old.id + 1,
          };
        }),
      35,
    );
    return () => clearInterval(timer);
  }, [value, reduced, skip]);
  return (
    <View>
      <Text
        style={{
          fontFamily: size >= 20 ? 'PressStart2P_400Regular' : 'PixelifySans_700Bold',
          fontSize: size,
          color: c.ink,
        }}
      >
        {reduced || skip ? value : roll.display}
      </Text>
      {!reduced && !skip && roll.delta !== 0 && <GrassDelta key={roll.id} amount={roll.delta} />}
    </View>
  );
}
function GrassDelta({ amount }: { amount: number }) {
  const reduced = useReducedMotion();
  const y = useSharedValue(8);
  const opacity = useSharedValue(1);
  useEffect(() => {
    y.set(withTiming(reduced ? 0 : -22, { duration: 600 }));
    opacity.set(withTiming(0, { duration: 600 }));
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
          backgroundColor: c.paper,
          borderRadius: 12,
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
}: {
  kind: PropKind;
  focused: boolean;
  color: ColorValue;
}) {
  const reduced = useReducedMotion();
  const y = useSharedValue(0);
  useEffect(() => {
    y.set(focused && !reduced ? withSpring(-3, { damping: 18, stiffness: 350 }) : 0);
  }, [focused, reduced, y]);
  const motion = useAnimatedStyle(() => ({ transform: [{ translateY: y.value }] }));
  return (
    <Animated.View
      accessible={false}
      aria-hidden
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      style={[
        {
          width: 40,
          height: 34,
          opacity: focused ? 1 : 0.65,
          borderRadius: artGeometry.controlRadius,
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: focused ? c.positive : c.transparent,
          boxShadow: focused ? `0 3px 0 ${c.depth}` : undefined,
        },
        motion,
      ]}
    >
      <PixelProp kind={kind} size={32} />
    </Animated.View>
  );
}
export function PixelDissolve() {
  const reduced = useReducedMotion();
  const opacity = useSharedValue(0);
  useEffect(() => {
    opacity.set(reduced ? 0.1 : 0.25);
    opacity.set(withTiming(0, { duration: reduced ? 100 : 150 }));
    return () => cancelAnimation(opacity);
  }, [opacity, reduced]);
  const motion = useAnimatedStyle(() => ({ opacity: opacity.value }));
  return (
    <Animated.View
      pointerEvents="none"
      style={[StyleSheet.absoluteFill, { backgroundColor: c.paper }, motion]}
    />
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
    return () => cancelAnimation(opacity);
  }, [active, reduced, opacity, duration]);
  const motion = useAnimatedStyle(() => ({ opacity: opacity.value }));
  return (
    <View style={style}>
      <Animated.View
        pointerEvents="none"
        style={[
          StyleSheet.absoluteFill,
          { borderRadius: style?.borderRadius ?? 14, backgroundColor: color ?? c.error },
          motion,
        ]}
      />
      {children}
    </View>
  );
}
export function BattleIntro({ skip = false }: { skip?: boolean }) {
  const reduced = useReducedMotion();
  const opacity = useSharedValue(0.2);
  useEffect(() => {
    opacity.set(skip ? 0 : withTiming(0, { duration: reduced ? 100 : 150 }));
  }, [opacity, reduced, skip]);
  const motion = useAnimatedStyle(() => ({ opacity: opacity.value }));
  return (
    <Animated.View
      pointerEvents="none"
      style={[StyleSheet.absoluteFill, { backgroundColor: c.paper }, motion]}
    />
  );
}
