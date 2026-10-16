import { useEffect, useState } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  type TextProps,
  type TextStyle,
  type ViewStyle,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, {
  cancelAnimation,
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withSequence,
  withSpring,
  withTiming,
} from 'react-native-reanimated';
import Svg, { Rect } from 'react-native-svg';
import { Zap } from 'lucide-react-native';
import { Button } from 'heroui-native';
import { BlurView } from 'expo-blur';
import { LinearGradient } from 'expo-linear-gradient';
import * as Haptics from 'expo-haptics';
import { useReducedMotion } from '@/lib/motion';
import { cozy as c, panelStyle } from '@/lib/cozy';
import { CozyBackground } from '@/components/cozy-ui';
import { PlayMeter } from '@/components/offline-garden';
import { PixelProp } from '@/components/pixel-scenes';
import { GrassRoll, Pulse } from '@/components/pixel-feedback';
import { status, clock, useGame, type Player } from '@/lib/game';
import { visitorPixels } from '@/lib/visitor-art';
import { isVisitorId, visitorInfo } from '@/lib/visitors';
import { petPixels } from '@/lib/pet-art';
import { grasslings, growthStage } from '@/lib/grasslings';

export function PixelText({ style, ...props }: TextProps) {
  const display = (StyleSheet.flatten(style)?.fontSize ?? 15) >= 16;
  return (
    <Text
      {...props}
      style={[
        styles.text,
        style,
        { fontFamily: display ? 'PressStart2P_400Regular' : 'Nunito_800ExtraBold' },
      ]}
    />
  );
}
export function PixelButton({
  label,
  onPress,
  disabled = false,
  light = false,
  small = false,
  danger = false,
  gold = false,
  energyCost,
  supportingText,
  onLongPress,
  onDisabledPress,
  haptic = true,
}: {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  light?: boolean;
  small?: boolean;
  danger?: boolean;
  gold?: boolean;
  energyCost?: number;
  supportingText?: string;
  onLongPress?: () => void;
  onDisabledPress?: () => void;
  haptic?: boolean;
}) {
  const reduced = useReducedMotion();
  const depth = useSharedValue(0);
  const motion = useAnimatedStyle(() => ({ transform: [{ translateY: depth.value }] }));
  const fill = disabled
    ? c.faded
    : danger
      ? c.error
      : gold
        ? c.amber
        : light
          ? c.paper
          : c.positive;
  return (
    <View
      style={{
        paddingBottom: 4,
        borderRadius: 999,
        backgroundColor: danger ? c.terracotta : light ? c.stone : c.moss,
      }}
    >
      <Animated.View style={motion}>
        <Button
          animation={false}
          isDisabled={disabled && !onDisabledPress}
          accessibilityLabel={label}
          accessibilityState={{ disabled }}
          onPressIn={() => depth.set(withTiming(reduced ? 0 : 3, { duration: 80 }))}
          onPressOut={() => depth.set(reduced ? 0 : withSpring(0, { damping: 15, stiffness: 450 }))}
          onPress={() => {
            if (disabled) {
              onDisabledPress?.();
              return;
            }
            if (haptic) void Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            onPress();
          }}
          onLongPress={onLongPress}
          style={{
            minHeight: 52,
            borderRadius: 999,
            borderWidth: 2,
            borderColor: c.outline,
            backgroundColor: fill,
            paddingHorizontal: small ? 8 : 16,
            paddingVertical: 10,
            height: 'auto',
            flexDirection: 'column',
            gap: 0,
          }}
        >
          <LinearGradient
            pointerEvents="none"
            colors={[c.highlight, c.transparent]}
            style={[StyleSheet.absoluteFill, { borderRadius: 999, opacity: 0.18 }]}
          />
          <Button.Label
            numberOfLines={2}
            style={{
              fontFamily: 'Nunito_800ExtraBold',
              color: c.buttonInk,
              fontSize: small ? 12 : 15,
              lineHeight: 19,
              textAlign: 'center',
            }}
          >
            {label}
          </Button.Label>
          {supportingText && (
            <Text
              style={{
                fontFamily: 'Nunito_600SemiBold',
                color: c.buttonInk,
                fontSize: 12,
                textAlign: 'center',
              }}
            >
              {supportingText}
            </Text>
          )}
          {energyCost !== undefined && <EnergyPips value={energyCost} color={c.buttonInk} />}
        </Button>
      </Animated.View>
    </View>
  );
}
export function EnergyPips({ value, color = c.ink }: { value: number; color?: string }) {
  return (
    <View
      accessibilityLabel={`${value} energy`}
      style={{ flexDirection: 'row', gap: 5, marginTop: 5 }}
    >
      {[0, 1, 2].map((pip) => (
        <Zap
          key={pip}
          size={12}
          strokeWidth={2.5}
          color={color}
          fill={pip < value ? color : c.transparent}
          style={{ opacity: pip < value ? 1 : 0.4 }}
        />
      ))}
    </View>
  );
}
export function Pet({
  species = 'BLOB',
  size = 192,
  level = 1,
  facing = 'right',
  hat = null,
  grumpy = false,
  sleeping = false,
  walking = false,
  bob = true,
  hit = 0,
  attack = 0,
  victory = false,
  slumped = false,
  dave = false,
  yawning = false,
  visitor = null,
  onPress,
  actionLabel,
}: {
  species?: Player['species'];
  size?: number;
  level?: number;
  facing?: 'left' | 'right';
  hat?: string | null;
  grumpy?: boolean;
  sleeping?: boolean;
  walking?: boolean;
  bob?: boolean;
  hit?: number;
  attack?: number;
  victory?: boolean;
  slumped?: boolean;
  dave?: boolean;
  yawning?: boolean;
  visitor?: string | null;
  onPress?: () => void;
  actionLabel?: string;
}) {
  const reduced = useReducedMotion();
  const y = useSharedValue(0);
  const x = useSharedValue(0);
  const [breath, setBreath] = useState(false);
  const [stride, setStride] = useState(false);
  const [blink, setBlink] = useState(false);
  const [idle, setIdle] = useState<'rest' | 'yawn' | 'look'>('rest');
  const [heart, setHeart] = useState(false);
  const [flashState, setFlashState] = useState({ hit, flashing: false });
  if (flashState.hit !== hit) setFlashState({ hit, flashing: hit !== 0 });
  useEffect(() => {
    if (reduced || !bob || sleeping || walking) return undefined;
    const timer = setInterval(() => setBreath((v) => !v), 400);
    return () => clearInterval(timer);
  }, [reduced, bob, sleeping, walking]);
  useEffect(() => {
    if (reduced) return undefined;
    let timer: ReturnType<typeof setTimeout>;
    let close: ReturnType<typeof setTimeout>;
    function schedule() {
      timer = setTimeout(
        () => {
          setBlink(true);
          close = setTimeout(() => setBlink(false), 160);
          schedule();
        },
        3000 + Math.random() * 2000,
      );
    }
    schedule();
    return () => {
      clearTimeout(timer);
      clearTimeout(close);
    };
  }, [reduced]);
  useEffect(() => {
    if (!bob || sleeping || walking || reduced || slumped) return undefined;
    let timer: ReturnType<typeof setTimeout>;
    let reset: ReturnType<typeof setTimeout>;
    function schedule() {
      timer = setTimeout(
        () => {
          setIdle(Math.random() > 0.5 ? 'yawn' : 'look');
          reset = setTimeout(() => setIdle('rest'), 900);
          schedule();
        },
        10000 + Math.random() * 5000,
      );
    }
    schedule();
    return () => {
      clearTimeout(timer);
      clearTimeout(reset);
    };
  }, [bob, sleeping, walking, reduced, slumped]);
  useEffect(() => {
    if (victory && !reduced)
      y.set(withSequence(withTiming(-12, { duration: 160 }), withTiming(0, { duration: 180 })));
    return () => cancelAnimation(y);
  }, [victory, reduced, y]);
  useEffect(() => {
    if (!heart) return undefined;
    const timer = setTimeout(() => setHeart(false), 600);
    return () => clearTimeout(timer);
  }, [heart]);
  useEffect(() => {
    if (!walking || reduced) return undefined;
    const timer = setInterval(() => setStride((v) => !v), 250);
    return () => clearInterval(timer);
  }, [walking, reduced]);
  useEffect(() => {
    if (!hit) return undefined;
    const timer = setTimeout(() => setFlashState({ hit, flashing: false }), 34);
    x.set(
      reduced
        ? 0
        : withSequence(
            withTiming(facing === 'right' ? -4 : 4, { duration: 50 }),
            withTiming(0, { duration: 100 }),
          ),
    );
    return () => {
      clearTimeout(timer);
      cancelAnimation(x);
    };
  }, [hit, reduced, x, facing]);
  useEffect(() => {
    if (attack && !reduced)
      x.set(
        withSequence(
          withTiming(facing === 'right' ? 8 : -8, { duration: 100 }),
          withTiming(0, { duration: 160 }),
        ),
      );
  }, [attack, facing, reduced, x]);
  const motion = useAnimatedStyle(() => ({
    transform: [{ translateY: Math.round(y.value) }, { translateX: Math.round(x.value) }],
  }));
  const visitorId = isVisitorId(visitor) ? visitor : null;
  const petLabel = visitorId ? visitorInfo(visitorId).name : grasslings[species].name;
  const pixels = visitorId
    ? visitorPixels(visitorId, hat, sleeping || blink)
    : petPixels(species, level, hat, sleeping || blink || idle === 'yawn' || yawning, grumpy, dave);
  const scaledSize = Math.max(32, Math.round(size / 32) * 32);
  return (
    <Animated.View
      accessibilityLabel={`${dave ? 'DOOMSCROLL DAVE weed creature' : `${petLabel} ${growthStage(level)} Grassling`}${slumped ? ', wilted' : ''}${sleeping ? ', sleeping' : ''}`}
      style={[{ width: scaledSize, height: scaledSize }, motion]}
    >
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={actionLabel ?? `Greet ${petLabel}`}
        onPress={() => {
          cancelAnimation(y);
          cancelAnimation(x);
          y.set(0);
          x.set(0);
          setHeart(true);
          if (onPress) {
            onPress();
            return;
          }
          void Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          if (!reduced)
            y.set(
              withSequence(withTiming(-12, { duration: 140 }), withTiming(0, { duration: 200 })),
            );
        }}
      >
        {heart && (
          <View
            pointerEvents="none"
            style={{ position: 'absolute', top: -16, left: scaledSize / 2 - 16, zIndex: 4 }}
          >
            <PixelProp kind="heart" size={32} />
          </View>
        )}
        <Svg
          width={scaledSize}
          height={scaledSize}
          viewBox="0 0 32 32"
          style={{
            transform: [
              { scaleX: facing === 'left' ? -1 : 1 },
              { translateY: slumped ? 8 : 0 },
              { translateX: idle === 'look' ? 3 : 0 },
            ],
          }}
        >
          {pixels.map(({ x: rx, y: ry, color }) => (
            <Rect
              key={`${rx}-${ry}`}
              x={rx}
              y={
                walking && ry >= 26 && ry <= 28 && rx < 17 === stride
                  ? ry - 1
                  : bob && breath && !reduced && !sleeping && ry >= 16
                    ? ry - 1
                    : ry
              }
              width={1}
              height={1}
              fill={
                flashState.flashing && !reduced
                  ? c.flash
                  : slumped
                    ? color === c.ink || color === c.night
                      ? c.night
                      : c.wilt
                    : color
              }
            />
          ))}
          {(idle === 'yawn' || yawning) && <Rect x={21} y={22} width={3} height={3} fill={c.ink} />}
        </Svg>
      </Pressable>
    </Animated.View>
  );
}
export function FloatingZ() {
  const y = useSharedValue(0);
  const reduced = useReducedMotion();
  useEffect(() => {
    y.set(
      reduced
        ? 0
        : withRepeat(
            withSequence(withTiming(-10, { duration: 1500 }), withTiming(0, { duration: 0 })),
            -1,
          ),
    );
    return () => cancelAnimation(y);
  }, [reduced, y]);
  const motion = useAnimatedStyle(() => ({
    opacity: 1 + y.value / 16,
    transform: [{ translateY: y.value }],
  }));
  return (
    <Animated.View pointerEvents="none" style={motion}>
      <Text style={{ fontFamily: 'Nunito_800ExtraBold', color: c.paper, fontSize: 20 }}>z z z</Text>
    </Animated.View>
  );
}
export function PixelEgg({
  cracking = false,
  color = c.body,
  size = 96,
}: {
  cracking?: boolean;
  color?: string;
  size?: number;
}) {
  const reduced = useReducedMotion();
  const value = useSharedValue(0);
  useEffect(() => {
    value.set(
      reduced
        ? 0
        : withRepeat(
            withSequence(
              withTiming(-5, { duration: cracking ? 70 : 300 }),
              withTiming(5, { duration: cracking ? 70 : 300 }),
            ),
            -1,
          ),
    );
  }, [cracking, reduced, value]);
  const motion = useAnimatedStyle(() => ({ transform: [{ rotate: `${value.value}deg` }] }));
  const rows = [
    '....KKKK....',
    '..KKBBBBKK..',
    '.KBBBBBBBBK.',
    '.KBBBKKBBBK.',
    'KBBBBKKBBBBK',
    'KBBBBBBBBBBK',
    'KBBKKBBBBBBK',
    'KBBKKBBBBBBK',
    'KBBBBBBBBBBK',
    '.KBBBBBBBBK.',
    '..KKBBBBKK..',
    '....KKKK....',
  ];
  const pixels = rows.flatMap((row, y) =>
    Array.from(row, (p, x) => ({ x, y, p })).filter((pixel) => pixel.p !== '.'),
  );
  return (
    <Animated.View style={motion}>
      <Svg width={size} height={size} viewBox="0 0 12 12">
        {pixels.map((pixel) => (
          <Rect
            key={`${pixel.x}-${pixel.y}`}
            x={pixel.x}
            y={pixel.y}
            width={1}
            height={1}
            fill={pixel.p === 'K' ? c.ink : color}
          />
        ))}
        {cracking && <Rect x={6} y={1} width={1} height={10} fill={c.ink} />}
      </Svg>
    </Animated.View>
  );
}
export function Meter({
  value,
  max = 100,
  height = 12,
  color = c.positive,
}: {
  value: number;
  max?: number;
  height?: number;
  color?: string;
}) {
  return (
    <View
      accessibilityRole="progressbar"
      accessibilityValue={{ min: 0, max, now: value }}
      style={{
        height,
        borderRadius: 999,
        borderWidth: 1,
        borderColor: c.outline,
        backgroundColor: c.body,
        padding: 2,
      }}
    >
      <View
        style={{
          height: '100%',
          borderRadius: 999,
          width: `${Math.max(0, Math.min(100, (value / max) * 100))}%`,
          backgroundColor: color,
        }}
      />
    </View>
  );
}
export function StatusChip({ player, compact = false }: { player: Player; compact?: boolean }) {
  const now = useGame((s) => s.now);
  const state = status(player, now);
  const care = state.kind === 'care';
  const color =
    state.kind === 'exposed'
      ? c.danger
      : care
        ? c.amber
        : player.mode !== 'awake'
          ? c.night
          : c.terracotta;
  const label = `${compact && care ? 'CARE' : state.label}${care ? ` ${clock(state.left)}` : ''}`;
  return (
    <Pulse
      active={state.kind === 'exposed'}
      color={c.paper}
      duration={1400}
      style={{
        flexDirection: 'row',
        alignItems: 'center',
        gap: 4,
        paddingHorizontal: compact ? 6 : 10,
        paddingVertical: 8,
        borderRadius: 999,
        backgroundColor: color,
      }}
    >
      <PixelProp kind="shield" size={16} />
      <Text
        numberOfLines={1}
        style={{
          fontFamily: 'Nunito_800ExtraBold',
          fontSize: 11,
          lineHeight: 17,
          color: care ? c.buttonInk : c.paper,
        }}
      >
        {label}
      </Text>
    </Pulse>
  );
}
export function GameHeader() {
  const p = useGame((s) => s.player);
  const live = useGame((s) => s.live);
  const top = useSafeAreaInsets().top;
  return (
    <View style={{ paddingTop: top + 8, paddingHorizontal: 16, paddingBottom: 8, zIndex: 40 }}>
      <BlurView tint="light" intensity={35} style={StyleSheet.absoluteFill} />
      <View pointerEvents="none" style={[StyleSheet.absoluteFill, { backgroundColor: c.glass }]} />
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={p ? `Garden status: ${status(p).label}` : 'Garden status'}
          accessibilityHint="Long press to end protection in the demo"
          onLongPress={() => p && useGame.getState().change({ care_until: 0, recovery_until: 0 })}
          style={{ flex: 1, minHeight: 44, justifyContent: 'center', alignItems: 'flex-start' }}
        >
          {p && <StatusChip player={p} compact />}
        </Pressable>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`${p?.grass ?? 20} grass`}
          onLongPress={() => p && useGame.getState().change({ grass: p.grass + 100 })}
          style={{
            flexDirection: 'row',
            gap: 4,
            alignItems: 'center',
            minHeight: 44,
            paddingHorizontal: 6,
            borderRadius: 999,
            backgroundColor: c.paper,
            borderWidth: 1,
            borderColor: c.outline,
          }}
        >
          <PixelProp kind="grass" size={16} />
          <GrassRoll value={p?.grass ?? 20} />
        </Pressable>
        {p && <PlayMeter />}
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`Open garden guide. ${live ? 'Garden synced' : 'No signal'}`}
          onPress={() => useGame.setState({ guideOpen: true })}
          style={{
            width: 44,
            height: 44,
            borderRadius: 22,
            backgroundColor: c.paper,
            alignItems: 'center',
            justifyContent: 'center',
            borderWidth: 1,
            borderColor: c.outline,
          }}
        >
          <Text style={{ fontFamily: 'Nunito_800ExtraBold', fontSize: 20, color: c.ink }}>?</Text>
          <View
            style={{
              position: 'absolute',
              bottom: 4,
              width: 4,
              height: 4,
              borderRadius: 2,
              backgroundColor: live ? c.moss : c.error,
            }}
          />
        </Pressable>
      </View>
    </View>
  );
}
export function Page({ children, style }: { children: React.ReactNode; style?: ViewStyle }) {
  return (
    <View style={{ flex: 1 }}>
      <CozyBackground />
      <ScrollView
        contentContainerStyle={[
          {
            padding: 16,
            paddingBottom: 112,
            gap: 12,
            width: '100%',
            maxWidth: 640,
            alignSelf: 'center',
          },
          style,
        ]}
      >
        {children}
      </ScrollView>
    </View>
  );
}
export const styles = {
  text: { fontFamily: 'Nunito_800ExtraBold', color: c.ink, fontSize: 15, lineHeight: 22 },
  title: { fontSize: 20, lineHeight: 32 },
  border: panelStyle,
  input: {
    fontFamily: 'Nunito_600SemiBold',
    color: c.ink,
    borderWidth: 2,
    borderColor: c.outline,
    backgroundColor: c.paper,
    padding: 16,
    fontSize: 15,
    minHeight: 52,
    borderRadius: 14,
  },
  section: { gap: 12 },
} satisfies Record<string, TextStyle | ViewStyle>;
