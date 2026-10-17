import { Pressable, Text, View, useWindowDimensions } from 'react-native';
import type { ComponentProps } from 'react';
import type { Tabs } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { cozy as c } from '@/lib/cozy';
import { backendConfigured } from '@/lib/bilt';
import { clock, feedback, status, useGame } from '@/lib/game';
import { remainingPlay, PLAY_LIMIT_MS } from '@/lib/offline-rules';
import { guardianPlayer } from '@/lib/visitors';
import { gameSideInset, hudLayout } from '@/lib/layout';
import { openSheet } from '@/lib/ui';
import { FrameShape, PixelFrame, frameTones, usePixelUnit } from '@/components/pixel-frame';
import { PixelProp } from '@/components/pixel-scenes';
import { GuardianPet } from '@/components/guardian-pet';
import { GrassRoll } from '@/components/pixel-feedback';
import type { PropKind } from '@/lib/scene-art';

type BottomTabBarProps = Parameters<NonNullable<ComponentProps<typeof Tabs>['tabBar']>>[0];

const label = { fontFamily: 'PixelifySans_700Bold', color: c.ink } as const;

/** A square pixel meter: dark well, flat fill, no rounded ends. */
export function PixelBar({
  value,
  max = 100,
  width,
  color,
  unit,
}: {
  value: number;
  max?: number;
  width: number;
  color: string;
  unit: number;
}) {
  const filled = Math.round((Math.max(0, Math.min(max, value)) / max) * (width - 2 * unit));
  return (
    <View
      style={{
        width,
        height: 3 * unit,
        backgroundColor: '#3B2F2A',
        padding: unit,
        flexDirection: 'row',
      }}
    >
      <View style={{ width: filled, height: unit, backgroundColor: color }} />
      <View style={{ flex: 1, height: unit, backgroundColor: '#8C7A64' }} />
    </View>
  );
}

function MenuGlyph({ unit: u, color }: { unit: number; color: string }) {
  return (
    <View style={{ gap: u }}>
      {[0, 1, 2].map((i) => (
        <View key={i} style={{ width: 7 * u, height: u, backgroundColor: color }} />
      ))}
    </View>
  );
}

/**
 * The floating heads-up display shared by every tab: who is with you, how the
 * garden's shield is doing, GRASS, the real-time play allowance and the menu.
 */
export function GameHud() {
  const p = useGame((s) => s.player);
  const now = useGame((s) => s.now);
  const live = useGame((s) => s.live);
  const budget = useGame((s) => s.rules.budget);
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const u = usePixelUnit();
  if (!p) return null;
  const guardian = guardianPlayer(p);
  const state = status(p, now);
  const left = remainingPlay(budget, now);
  const mood = p.mood < 30 ? 'GRUMPY' : 'HAPPY';
  const shieldTone = state.kind === 'exposed' ? c.error : state.kind === 'care' ? c.amber : c.nap;
  const shieldText =
    state.kind === 'care' ? clock(state.left) : state.kind === 'exposed' ? 'OPEN' : 'SAFE';
  const side = gameSideInset(width) - 8;
  return (
    <View
      pointerEvents="box-none"
      style={{
        position: 'absolute',
        top: insets.top + hudLayout.gap,
        left: side,
        right: side,
        zIndex: 40,
      }}
    >
      <PixelFrame
        tone="glass"
        depth={1}
        style={{
          minHeight: hudLayout.height - u,
          flexDirection: 'row',
          alignItems: 'center',
          gap: 2 * u,
          paddingVertical: u,
          paddingHorizontal: 2 * u,
        }}
      >
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`${guardian.pet_name}, ${mood.toLowerCase()}. Change companion`}
          onPress={() => {
            feedback('select');
            openSheet('companions');
          }}
          style={{
            flex: 1,
            minWidth: 0,
            minHeight: 44,
            flexDirection: 'row',
            alignItems: 'center',
            gap: 2 * u,
          }}
        >
          <View
            style={{
              width: 18 * u,
              height: 18 * u,
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <FrameShape tone={frameTones.parchment} unit={u} />
            <GuardianPet
              player={p}
              size={32}
              bob={false}
              active={false}
              groundShadow={false}
              grumpy={p.mood < 30}
              decorative
            />
          </View>
          <View style={{ flex: 1, minWidth: 0, gap: u }}>
            <Text numberOfLines={1} style={[label, { fontSize: 13, lineHeight: 15 }]}>
              {guardian.pet_name}
            </Text>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: u }}>
              <PixelProp kind="heart" size={12} tint={p.mood < 30 ? c.error : '#C8574A'} />
              <PixelBar
                value={p.mood}
                width={22 * u}
                color={p.mood < 30 ? c.error : c.positive}
                unit={u}
              />
            </View>
          </View>
        </Pressable>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`Garden shield: ${state.label}${state.kind === 'care' ? `, ${state.left} seconds left` : ''}. Opens the garden guide`}
          onPress={() => useGame.setState({ guideOpen: true })}
          onLongPress={() => useGame.getState().change({ care_until: 0, recovery_until: 0 })}
          style={{
            minHeight: 44,
            minWidth: 44,
            alignItems: 'center',
            justifyContent: 'center',
            gap: u / 2,
          }}
        >
          <PixelProp kind="shield" size={16} tint={shieldTone} />
          <Text
            style={[
              label,
              { fontSize: 11, lineHeight: 13, color: state.kind === 'exposed' ? c.error : c.ink },
            ]}
          >
            {shieldText}
          </Text>
        </Pressable>
        <View
          accessible
          accessibilityRole="text"
          accessibilityLabel={`${p.grass} grass`}
          style={{
            minHeight: 44,
            minWidth: 44,
            alignItems: 'center',
            justifyContent: 'center',
            gap: u / 2,
          }}
        >
          <PixelProp kind="grass" size={16} />
          {p.grass >= 10000 ? (
            <Text style={[label, { fontSize: 12, lineHeight: 14 }]}>
              {new Intl.NumberFormat('en-GB', {
                notation: 'compact',
                maximumFractionDigits: 1,
              }).format(p.grass)}
            </Text>
          ) : (
            <GrassRoll value={p.grass} size={12} />
          )}
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`${left} seconds of play left. Long press to reset demo play budget.`}
          accessibilityHint="Opens the guide to the real-time play allowance and simulated break clock."
          onPress={() => useGame.setState({ guideOpen: true })}
          onLongPress={() => useGame.getState().resetBudget()}
          style={{
            minHeight: 44,
            minWidth: 48,
            alignItems: 'center',
            justifyContent: 'center',
            gap: u,
          }}
        >
          <Text style={[label, { fontSize: 12, lineHeight: 14, color: left ? c.ink : c.error }]}>
            {clock(left)}
          </Text>
          <PixelBar
            value={left * 1000}
            max={PLAY_LIMIT_MS}
            width={20 * u}
            color={left ? c.focus : c.error}
            unit={u}
          />
        </Pressable>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`Open the menu. ${live ? 'Garden synced' : backendConfigured ? 'No signal' : 'Local garden, saved on this device'}`}
          onPress={() => {
            feedback('select');
            openSheet('menu');
          }}
          style={{ width: 44, height: 44, alignItems: 'center', justifyContent: 'center' }}
        >
          <FrameShape tone={frameTones.parchment} unit={u} />
          <MenuGlyph unit={u} color={c.ink} />
          <View
            style={{
              position: 'absolute',
              right: 3 * u,
              top: 3 * u,
              width: u,
              height: u,
              backgroundColor: live || !backendConfigured ? c.moss : c.error,
            }}
          />
        </Pressable>
      </PixelFrame>
    </View>
  );
}

const tabs: Record<string, { label: string; icon: PropKind }> = {
  index: { label: 'HOME', icon: 'house' },
  missions: { label: 'MISSIONS', icon: 'map' },
  arena: { label: 'ARENA', icon: 'swords' },
  shop: { label: 'SHOP', icon: 'bag' },
};

/** The pixel hotbar: four places and a raised NAP button in the middle. */
export function GameHotbar({ state, navigation }: BottomTabBarProps) {
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const u = usePixelUnit();
  const awake = useGame((s) => s.player?.mode === 'awake');
  const side = gameSideInset(width) - 8;
  const slot = (index: number) => {
    const route = state.routes[index];
    if (!route) return null;
    const meta = tabs[route.name] ?? { label: route.name.toUpperCase(), icon: 'house' as const };
    const focused = state.index === index;
    return (
      <Pressable
        key={route.key}
        accessibilityRole="tab"
        accessibilityState={{ selected: focused }}
        aria-selected={focused}
        accessibilityLabel={meta.label}
        onPress={() => {
          const event = navigation.emit({
            type: 'tabPress',
            target: route.key,
            canPreventDefault: true,
          });
          if (!focused && !event.defaultPrevented) {
            feedback('select');
            navigation.navigate(route.name, route.params);
          }
        }}
        style={{
          flex: 1,
          minHeight: 44,
          alignItems: 'center',
          justifyContent: 'center',
          gap: u / 2,
        }}
      >
        {focused && <FrameShape tone={frameTones.leaf} unit={u} />}
        <PixelProp kind={meta.icon} size={24} />
        <Text
          style={[label, { fontSize: 10, lineHeight: 12, color: focused ? c.buttonInk : c.ink }]}
        >
          {meta.label}
        </Text>
      </Pressable>
    );
  };
  return (
    <View
      pointerEvents="box-none"
      style={{
        position: 'absolute',
        left: side,
        right: side,
        bottom: insets.bottom + hudLayout.gap,
      }}
    >
      <PixelFrame
        tone="paper"
        depth={1}
        style={{
          height: hudLayout.hotbar - u,
          flexDirection: 'row',
          alignItems: 'stretch',
          gap: u,
          padding: 2 * u,
        }}
      >
        {slot(0)}
        {slot(1)}
        <View style={{ width: 30 * u }} />
        {slot(2)}
        {slot(3)}
      </PixelFrame>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Take a nap"
        accessibilityHint="Choose an optional break idea, then put your phone down"
        disabled={!awake}
        onPress={() => {
          feedback('select');
          openSheet('nap');
        }}
        style={({ pressed }) => ({
          position: 'absolute',
          left: '50%',
          marginLeft: -15 * u,
          bottom: 3 * u,
          width: 30 * u,
          height: hudLayout.hotbar + 6 * u,
          alignItems: 'center',
          justifyContent: 'center',
          gap: u,
          transform: [{ translateY: pressed ? u : 0 }],
          opacity: awake ? 1 : 0.6,
        })}
      >
        <FrameShape
          tone={{
            ...frameTones.nap,
            fill: frameTones.nap.base,
            light: frameTones.nap.base,
            dark: frameTones.nap.base,
          }}
          unit={u}
          offset={2 * u}
          bevel={false}
        />
        <FrameShape tone={frameTones.nap} unit={u} />
        <PixelProp kind="moon" size={32} tint="#FFF3CF" />
        <Text style={[label, { fontSize: 13, lineHeight: 15, color: '#FFF7E2' }]}>NAP</Text>
      </Pressable>
    </View>
  );
}
