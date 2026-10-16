import { type ReactNode, useEffect } from 'react';
import { Pressable, StyleSheet, View, type ViewStyle } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Svg, { Circle } from 'react-native-svg';
import Animated, {
  cancelAnimation,
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
} from 'react-native-reanimated';
import { cozy as c, panelStyle } from '@/lib/cozy';
import { useReducedMotion } from '@/lib/motion';

export function CozyBackground() {
  return (
    <LinearGradient
      pointerEvents="none"
      colors={[c.paper, c.sage]}
      style={StyleSheet.absoluteFill}
    />
  );
}
export function PaperFinish() {
  return (
    <View
      pointerEvents="none"
      style={[StyleSheet.absoluteFill, { borderRadius: 12, overflow: 'hidden' }]}
    >
      <LinearGradient
        colors={[c.highlight, c.paper]}
        style={[StyleSheet.absoluteFill, { opacity: 0.45 }]}
      />
      <Svg width="100%" height="100%" opacity={0.065}>
        {Array.from({ length: 150 }, (_, i) => (
          <Circle
            key={i}
            cx={`${(i * 37) % 100}%`}
            cy={`${(i * 61) % 100}%`}
            r={i % 3 === 0 ? 0.7 : 0.4}
            fill={c.ink}
          />
        ))}
      </Svg>
    </View>
  );
}
export function CozyPanel({ children, style }: { children: ReactNode; style?: ViewStyle }) {
  return (
    <View style={[panelStyle, style]}>
      <PaperFinish />
      {children}
    </View>
  );
}
export function CozySheet({
  children,
  onSkip,
  style,
}: {
  children: ReactNode;
  onSkip?: () => void;
  style?: ViewStyle;
}) {
  const reduced = useReducedMotion();
  const y = useSharedValue(reduced ? 0 : 40);
  const alpha = useSharedValue(0);
  useEffect(() => {
    y.set(reduced ? 0 : withSpring(0, { damping: 22, stiffness: 240, overshootClamping: true }));
    alpha.set(withTiming(1, { duration: reduced ? 100 : 180 }));
    return () => {
      cancelAnimation(y);
      cancelAnimation(alpha);
    };
  }, [y, alpha, reduced]);
  const motion = useAnimatedStyle(() => ({
    opacity: alpha.value,
    transform: [{ translateY: y.value }],
  }));
  return (
    <Animated.View
      onStartShouldSetResponderCapture={() => {
        cancelAnimation(y);
        cancelAnimation(alpha);
        y.set(0);
        alpha.set(1);
        onSkip?.();
        return false;
      }}
      onTouchStart={() => {
        cancelAnimation(y);
        cancelAnimation(alpha);
        y.set(0);
        alpha.set(1);
        onSkip?.();
      }}
      style={[panelStyle, style, motion]}
    >
      <PaperFinish />
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Skip sheet animation"
        onPress={() => {
          cancelAnimation(y);
          cancelAnimation(alpha);
          y.set(0);
          alpha.set(1);
          onSkip?.();
        }}
        style={{ height: 24, alignItems: 'center', justifyContent: 'center' }}
      >
        <View
          style={{ height: 4, width: 36, borderRadius: 2, backgroundColor: c.shade, opacity: 0.4 }}
        />
      </Pressable>
      {children}
    </Animated.View>
  );
}
