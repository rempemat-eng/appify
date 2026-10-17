import { type ReactNode, useCallback, useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View, type ViewStyle } from 'react-native';
import { scheduleOnRN } from 'react-native-worklets';
import { LinearGradient } from 'expo-linear-gradient';
import Svg, { Rect } from 'react-native-svg';
import Animated, {
  cancelAnimation,
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
} from 'react-native-reanimated';
import { cozy as c } from '@/lib/cozy';
import {
  FrameShape,
  PixelFrame,
  frameTones,
  usePixelUnit,
  type FrameToneName,
} from '@/components/pixel-frame';
import { artGeometry } from '@/lib/art-direction';
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
      accessible={false}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      style={[
        StyleSheet.absoluteFill,
        { borderRadius: artGeometry.panelRadius - 2, overflow: 'hidden' },
      ]}
    >
      <View
        style={{
          position: 'absolute',
          top: 1,
          left: 8,
          right: 8,
          height: 2,
          backgroundColor: c.highlight,
        }}
      />
      <View
        style={{
          position: 'absolute',
          bottom: 1,
          left: 8,
          right: 8,
          height: 1,
          backgroundColor: c.inset,
        }}
      />
      <Svg width="100%" height="100%" opacity={0.1}>
        {Array.from({ length: 24 }, (_, i) => (
          <Rect
            key={i}
            x={`${(i * 37 + 7) % 100}%`}
            y={`${(i * 61 + 11) % 100}%`}
            width={i % 3 === 0 ? 3 : 1}
            height={1}
            fill={c.depth}
          />
        ))}
      </Svg>
    </View>
  );
}
export function CozyPanel({
  children,
  style,
  tone = 'paper',
}: {
  children: ReactNode;
  style?: ViewStyle;
  tone?: FrameToneName;
}) {
  return (
    <PixelFrame tone={tone} depth={1} style={style}>
      {children}
    </PixelFrame>
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
  const u = usePixelUnit();
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
      style={[{ padding: 3 * u }, style, motion]}
    >
      <FrameShape tone={frameTones.paper} unit={u} />
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
        <View style={{ height: 3, width: 32, borderRadius: 0, backgroundColor: c.depth }} />
        {animating && (
          <Text style={{ fontFamily: 'PixelifySans_500Medium', fontSize: 12, color: c.ink }}>
            Skip
          </Text>
        )}
      </Pressable>
      {children}
    </Animated.View>
  );
}
