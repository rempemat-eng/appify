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
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withRepeat,
  withSequence,
  withTiming,
} from 'react-native-reanimated';
import Svg, { Rect } from 'react-native-svg';
import { Shield, TriangleAlert, Moon, Sprout, Clock3 } from 'lucide-react-native';
import { palette as c, status, clock, useGame, type Player } from '@/lib/game';
import { petPixels } from '@/lib/pet-art';

export function PixelText({ style, ...props }: TextProps) {
  return <Text {...props} style={[styles.text, style]} />;
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
  onLongPress,
}: {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  light?: boolean;
  small?: boolean;
  danger?: boolean;
  gold?: boolean;
  energyCost?: number;
  onLongPress?: () => void;
}) {
  return (
    <View style={{ paddingRight: 4, paddingBottom: 4, opacity: disabled ? 0.45 : 1 }}>
      <View style={[StyleSheet.absoluteFill, { top: 4, left: 4, backgroundColor: c.ink }]} />
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={label}
        disabled={disabled}
        onPress={onPress}
        onLongPress={onLongPress}
        style={({ pressed }) => [
          {
            minHeight: small ? 42 : 54,
            paddingVertical: small ? 12 : 17,
            paddingHorizontal: 12,
            borderWidth: 2,
            borderColor: c.ink,
            backgroundColor: danger ? c.error : gold ? c.gold : light ? c.paper : c.positive,
            justifyContent: 'center',
            alignItems: 'center',
            transform: [{ translateX: pressed ? 4 : 0 }, { translateY: pressed ? 4 : 0 }],
          },
        ]}
      >
        <PixelText
          style={{
            color: danger ? c.flash : c.buttonInk,
            fontSize: small ? 11 : 12,
            textAlign: 'center',
            lineHeight: 20,
          }}
        >
          {label}
        </PixelText>
        {energyCost !== undefined && (
          <EnergyPips value={energyCost} color={danger ? c.flash : c.buttonInk} />
        )}
      </Pressable>
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
        <View
          key={pip}
          style={{
            width: 8,
            height: 8,
            borderWidth: 1,
            borderColor: color,
            backgroundColor: pip < value ? color : 'transparent',
          }}
        />
      ))}
    </View>
  );
}
function pixelCells(rows: string[]) {
  return rows.flatMap((row, y) =>
    Array.from(row, (pixel, x) => ({ id: `${x}-${y}`, pixel, x, y })),
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
}) {
  const reduced = useReducedMotion();
  const y = useSharedValue(0);
  const x = useSharedValue(0);
  const [stride, setStride] = useState(false);
  const [flashState, setFlashState] = useState({ hit, flashing: false });
  // A new hit starts its flash in the same render, not a cascading effect update.
  if (flashState.hit !== hit) setFlashState({ hit, flashing: hit !== 0 });
  const flashing = flashState.flashing;
  useEffect(() => {
    if (!walking || reduced) return undefined;
    const timer = setInterval(() => setStride((value) => !value), 250);
    return () => clearInterval(timer);
  }, [walking, reduced]);
  useEffect(() => {
    if (bob && !reduced)
      y.set(
        withRepeat(
          withSequence(withTiming(-3, { duration: 500 }), withTiming(0, { duration: 500 })),
          -1,
        ),
      );
    else y.set(0);
  }, [bob, reduced, y]);
  useEffect(() => {
    if (!hit) return undefined;
    const timer = setTimeout(() => setFlashState({ hit, flashing: false }), 140);
    if (!reduced)
      x.set(
        withSequence(
          withTiming(-6, { duration: 50 }),
          withTiming(6, { duration: 50 }),
          withTiming(-3, { duration: 50 }),
          withTiming(0, { duration: 60 }),
        ),
      );
    return () => clearTimeout(timer);
  }, [hit, reduced, x]);
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
  const pixels = petPixels(species, level, hat, sleeping, grumpy);
  const scaledSize = Math.max(32, Math.round(size / 32) * 32);
  return (
    <Animated.View
      accessibilityLabel={`${species} stage ${Math.min(3, level)} pet${grumpy ? ', grumpy' : ''}${sleeping ? ', sleeping' : ''}${hat ? ` wearing ${hat}` : ''}`}
      style={[{ width: scaledSize, height: scaledSize }, motion]}
    >
      <Svg
        width={scaledSize}
        height={scaledSize}
        viewBox="0 0 32 32"
        style={{ transform: [{ scaleX: facing === 'left' ? -1 : 1 }] }}
      >
        {pixels.map(({ x: rx, y: ry, color }) => (
          <Rect
            key={`${rx}-${ry}`}
            x={rx}
            y={walking && ry >= 26 && ry <= 28 && rx < 17 === stride ? ry - 1 : ry}
            width={1}
            height={1}
            fill={flashing ? c.flash : color}
          />
        ))}
      </Svg>
    </Animated.View>
  );
}
export function FloatingZ() {
  const y = useSharedValue(0);
  const reduced = useReducedMotion();
  useEffect(() => {
    if (!reduced)
      y.set(
        withRepeat(
          withSequence(withTiming(-10, { duration: 1500 }), withTiming(0, { duration: 0 })),
          -1,
        ),
      );
    else y.set(0);
  }, [reduced, y]);
  const animation = useAnimatedStyle(() => ({
    transform: [{ translateY: y.value }],
    opacity: 1 + y.value / 16,
  }));
  return (
    <Animated.View style={animation}>
      <PixelText style={{ color: c.body, fontSize: 24 }}>Z z z</PixelText>
    </Animated.View>
  );
}
export function PixelEgg({ cracking = false }: { cracking?: boolean }) {
  const value = useSharedValue(0);
  const reduced = useReducedMotion();
  useEffect(() => {
    if (!reduced)
      value.set(
        withRepeat(
          withSequence(
            withTiming(-5, { duration: cracking ? 70 : 300 }),
            withTiming(5, { duration: cracking ? 70 : 300 }),
          ),
          -1,
        ),
      );
  }, [cracking, reduced, value]);
  const animation = useAnimatedStyle(() => ({ transform: [{ rotate: `${value.value}deg` }] }));
  const egg = [
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
  return (
    <Animated.View style={animation}>
      <Svg width={132} height={132} viewBox="0 0 12 12">
        {pixelCells(egg).map(({ id, pixel, x, y }) =>
          pixel === '.' ? null : (
            <Rect key={id} x={x} y={y} width={1} height={1} fill={pixel === 'K' ? c.ink : c.body} />
          ),
        )}
        {cracking && (
          <>
            <Rect x={5} y={1} width={1} height={4} fill={c.ink} />
            <Rect x={6} y={4} width={2} height={1} fill={c.ink} />
            <Rect x={7} y={5} width={1} height={6} fill={c.ink} />
          </>
        )}
      </Svg>
    </Animated.View>
  );
}
export function Meter({
  value,
  max = 100,
  height = 12,
}: {
  value: number;
  max?: number;
  height?: number;
}) {
  return (
    <View
      accessibilityRole="progressbar"
      accessibilityValue={{ min: 0, max, now: value }}
      style={{ height, borderWidth: 2, borderColor: c.ink, backgroundColor: c.body, padding: 2 }}
    >
      <View
        style={{
          height: '100%',
          width: `${Math.max(0, Math.min(100, (value / max) * 100))}%`,
          backgroundColor: c.positive,
        }}
      />
    </View>
  );
}
export function StatusChip({ player, compact = false }: { player: Player; compact?: boolean }) {
  const now = useGame((s) => s.now);
  const state = status(player, now);
  const Icon =
    state.label === 'SCREEN OFF'
      ? Moon
      : state.kind === 'exposed'
        ? TriangleAlert
        : state.kind === 'care'
          ? Clock3
          : Shield;
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 5 }}>
      <Icon size={compact ? 12 : 14} color={c.ink} strokeWidth={2.5} />
      <PixelText numberOfLines={1} style={{ fontSize: 11, lineHeight: 17 }}>
        {state.label}
        {state.left ? ` ${clock(state.left)}` : ''}
      </PixelText>
    </View>
  );
}
export function GameHeader() {
  const p = useGame((s) => s.player);
  const live = useGame((s) => s.live);
  const top = useSafeAreaInsets().top;
  return (
    <View
      style={{
        paddingTop: top + 10,
        paddingHorizontal: 16,
        paddingBottom: 12,
        backgroundColor: c.paper,
        borderBottomWidth: 2,
        borderColor: c.ink,
      }}
    >
      <View
        style={{
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 6,
        }}
      >
        <Pressable
          accessibilityLabel="Pet protection status"
          onLongPress={() => p && useGame.getState().change({ care_until: 0, recovery_until: 0 })}
          style={{ flex: 1 }}
        >
          {p && <StatusChip player={p} />}
        </Pressable>
        <Pressable
          accessibilityLabel="Grass balance"
          onLongPress={() => p && useGame.getState().change({ grass: p.grass + 100 })}
          style={{ flexDirection: 'row', alignItems: 'center', gap: 5 }}
        >
          <Sprout size={19} color={c.ink} strokeWidth={2.5} />
          <PixelText style={{ fontSize: 13 }}>{p?.grass ?? 20}</PixelText>
        </Pressable>
      </View>
      <View style={{ flexDirection: 'row', gap: 5, alignItems: 'center', marginTop: 8 }}>
        <View style={{ width: 6, height: 6, backgroundColor: live ? c.shade : c.error }} />
        <PixelText style={{ fontSize: 11 }}>{live ? 'LIVE' : 'OFFLINE'}</PixelText>
      </View>
    </View>
  );
}
export function Page({ children, style }: { children: React.ReactNode; style?: ViewStyle }) {
  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: c.paper }}
      contentContainerStyle={[
        {
          padding: 20,
          paddingBottom: 36,
          gap: 24,
          width: '100%',
          maxWidth: 640,
          alignSelf: 'center',
        },
        style,
      ]}
    >
      {children}
    </ScrollView>
  );
}
export const styles = {
  text: { fontFamily: 'PressStart2P_400Regular', color: c.ink, fontSize: 11, lineHeight: 20 },
  title: { fontSize: 19, lineHeight: 30 },
  border: { borderWidth: 2, borderColor: c.ink },
  input: {
    fontFamily: 'PressStart2P_400Regular',
    color: c.ink,
    borderWidth: 2,
    borderColor: c.ink,
    backgroundColor: c.body,
    padding: 15,
    fontSize: 12,
    minHeight: 50,
    borderRadius: 0,
  },
  section: { gap: 14 },
} satisfies Record<string, TextStyle | ViewStyle>;
