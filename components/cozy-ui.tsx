import { type ReactNode, useCallback, useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View, type ViewStyle } from 'react-native';
import { scheduleOnRN } from 'react-native-worklets';
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
  const [animating, setAnimating] = useState(!reduced);
  const active = useRef(!reduced);
  const finishAnimation = useCallback(() => {
    active.current = false;
    setAnimating(false);
  }, []);
  const y = useSharedValue(reduced ? 0 : 40);
  const alpha = useSharedValue(reduced ? 1 : 0);
  const skipAnimation = () => {
    if (!active.current) return;
    cancelAnimation(y);
    cancelAnimation(alpha);
    y.set(0);
    alpha.set(1);
    finishAnimation();
    onSkip?.();
  };
  useEffect(() => {
    if (reduced || !active.current) {
      cancelAnimation(y);
      cancelAnimation(alpha);
      y.set(0);
      alpha.set(1);
      finishAnimation();
      return undefined;
    }
    y.set(
      withSpring(0, { damping: 22, stiffness: 240, overshootClamping: true }, (finished) => {
        if (finished) scheduleOnRN(finishAnimation);
      }),
    );
    alpha.set(withTiming(1, { duration: 180 }));
    return () => {
      cancelAnimation(y);
      cancelAnimation(alpha);
    };
  }, [y, alpha, reduced, finishAnimation]);
  const motion = useAnimatedStyle(() => ({
    opacity: alpha.value,
    transform: [{ translateY: y.value }],
  }));
  return (
    <Animated.View
      onStartShouldSetResponderCapture={() => {
        skipAnimation();
        return false;
      }}
      onTouchStart={skipAnimation}
      style={[panelStyle, style, motion]}
    >
      <PaperFinish />
      <Pressable
        accessible={animating}
        accessibilityRole={animating ? 'button' : undefined}
        accessibilityLabel={animating ? 'Skip sheet animation' : undefined}
        focusable={animating}
        tabIndex={animating ? 0 : -1}
        onPress={animating ? skipAnimation : undefined}
        style={{
          minHeight: 44,
          width: 80,
          alignSelf: 'center',
          borderRadius: 12,
          alignItems: 'center',
          justifyContent: 'center',
          gap: 4,
        }}
      >
        <View
          style={{ height: 4, width: 36, borderRadius: 2, backgroundColor: c.shade, opacity: 0.4 }}
        />
        {animating && (
          <Text style={{ fontFamily: 'Nunito_600SemiBold', fontSize: 11, color: c.ink }}>Skip</Text>
        )}
      </Pressable>
      {children}
    </Animated.View>
  );
}
