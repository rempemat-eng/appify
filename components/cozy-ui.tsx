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
import { useReducedMotion } from '@/lib/motion';
import { panelInset, type } from '@/lib/ui-tokens';

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
      style={[StyleSheet.absoluteFill, { borderRadius: 0 - 2, overflow: 'hidden' }]}
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
  safeBottom = 0,
}: {
  children: ReactNode;
  onSkip?: () => void;
  /** Sizing and gap only: every sheet shares one panel inset (`panelInset`). */
  style?: ViewStyle;
  /** Extra bottom room for a sheet that sits on the screen's bottom edge. */
  safeBottom?: number;
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
  // Layers (coherence plan, step 3): a wooden rim around a paper panel. Sizing goes
  // on the rim; padding and gaps go on the panel, so the rim never eats into content.
  const { outer, inner } = splitSheetStyle(style);
  return (
    <Animated.View
      onStartShouldSetResponderCapture={() => {
        skipAnimation();
        return false;
      }}
      onTouchStart={skipAnimation}
      style={[{ padding: 3 * u }, outer, motion]}
    >
      <FrameShape tone={frameTones.wood} unit={u} />
      <View
        style={[
          { padding: panelInset(u), paddingBottom: panelInset(u) + safeBottom, flexShrink: 1 },
          inner,
        ]}
      >
        <FrameShape tone={frameTones.paper} unit={u} />
        {/* Skips the entrance. It stays mounted (focus is never dropped) and only takes
            touches and focus while the sheet moves, over the top of the panel. */}
        <Pressable
          accessible={animating}
          accessibilityRole={animating ? 'button' : undefined}
          accessibilityLabel={animating ? 'Skip sheet animation' : undefined}
          focusable={animating}
          tabIndex={animating ? 0 : -1}
          pointerEvents={animating ? 'auto' : 'none'}
          onPress={animating ? skipAnimation : undefined}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 44,
            zIndex: 2,
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {animating && <Text style={[type.caption, { color: c.ink }]}>Skip</Text>}
        </Pressable>
        {children}
      </View>
    </Animated.View>
  );
}

const sizingKeys = new Set([
  'width',
  'minWidth',
  'maxWidth',
  'height',
  'minHeight',
  'maxHeight',
  'alignSelf',
  'position',
  'top',
  'left',
  'right',
  'bottom',
  'margin',
  'marginTop',
  'marginBottom',
  'marginLeft',
  'marginRight',
  'marginHorizontal',
  'marginVertical',
]);
const paddingKey = /^padding/;
/** Sizing belongs to the sheet's rim, gap and alignment to its panel; padding is the shared inset. */
function splitSheetStyle(style?: ViewStyle) {
  const flat: ViewStyle = StyleSheet.flatten(style) ?? {};
  const outer: ViewStyle = {};
  const inner: ViewStyle = {};
  for (const [key, value] of Object.entries(flat)) {
    if (paddingKey.test(key)) continue;
    Object.assign(sizingKeys.has(key) ? outer : inner, { [key]: value });
  }
  // a sheet that fills its space passes the fill on to its panel
  if (flat.flex !== undefined) {
    outer.flex = flat.flex;
    inner.flex = 1;
  }
  return { outer, inner };
}
