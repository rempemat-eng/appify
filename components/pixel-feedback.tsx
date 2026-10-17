import { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, View, type TextProps, type ViewStyle } from 'react-native';
import Animated, {
  cancelAnimation,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
  withSequence,
  withRepeat,
} from 'react-native-reanimated';
import { useReducedMotion } from '@/lib/motion';
import { cozy as c } from '@/lib/cozy';
import { FrameShape, PixelTail, frameTones, usePixelUnit } from '@/components/pixel-frame';
import { contentInset, type } from '@/lib/ui-tokens';
import { PixelIcon } from '@/components/pixel-icon';
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
  const u = usePixelUnit();
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
          minHeight: 44,
          padding: contentInset(u),
          paddingBottom: contentInset(u) + (onDismiss ? type.caption.lineHeight : 0),
        },
        style,
      ]}
    >
      {/* the one speech style (coherence plan, step 3), shared with the garden's bubbles */}
      <FrameShape tone={frameTones.paper} unit={u} />
      <BodyText style={type.body}>{reduced ? copy : copy.slice(0, shown.count) || ' '}</BodyText>
      {speech && <PixelTail />}
      {onDismiss && (
        <BodyText
          style={[
            type.caption,
            { position: 'absolute', right: contentInset(u), bottom: contentInset(u) - u },
          ]}
        >
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
          borderRadius: 0,
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
      <PixelIcon name="grass" size={16} />
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
