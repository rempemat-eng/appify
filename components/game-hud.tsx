import { Pressable, Text, View, useWindowDimensions } from 'react-native';
import type { ComponentProps, ReactNode } from 'react';
import type { Tabs } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { cozy as c } from '@/lib/cozy';
import { backendConfigured } from '@/lib/bilt';
import { clock, feedback, status, useGame } from '@/lib/game';
import { remainingPlay } from '@/lib/offline-rules';
import { guardianPlayer } from '@/lib/visitors';
import { gameSideInset, hudLayout } from '@/lib/layout';
import { openSheet } from '@/lib/ui';
import {
  FrameFill,
  FrameShape,
  PixelFrame,
  frameTones,
  usePixelUnit,
} from '@/components/pixel-frame';
import { barControl, contentInset, hotbarSlot, layers, siblingGap, type } from '@/lib/ui-tokens';
import { PixelProp } from '@/components/pixel-scenes';
import { GuardianPet } from '@/components/guardian-pet';
import { GrassRoll } from '@/components/pixel-feedback';
import type { PropKind } from '@/lib/scene-art';

type BottomTabBarProps = Parameters<NonNullable<ComponentProps<typeof Tabs>['tabBar']>>[0];

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
  /** a fixed width snaps the fill to whole pixels; leave it out to stretch */
  width?: number;
  color: string;
  unit: number;
}) {
  const share = max > 0 ? Math.max(0, Math.min(max, value)) / max : 0;
  const filled =
    width === undefined
      ? (`${Math.round(share * 100)}%` as const)
      : Math.round(share * (width - 2 * unit));
  return (
    <View
      style={{
        width,
        alignSelf: width === undefined ? 'stretch' : undefined,
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

/** A HUD stat: one inset well holding an icon and its value, the same height as the portrait. */
function StatChip({
  unit: u,
  icon,
  tint,
  children,
  ...press
}: {
  unit: number;
  icon: PropKind;
  tint?: string;
  children: ReactNode;
} & Pick<
  ComponentProps<typeof Pressable>,
  'accessibilityLabel' | 'accessibilityHint' | 'onPress' | 'onLongPress' | 'accessibilityRole'
>) {
  const body = (
    <>
      <FrameFill fill={layers.well} outline={c.outline} inset />
      <PixelProp kind={icon} size={8 * u} tint={tint} />
      {children}
    </>
  );
  const style = {
    height: barControl(u),
    flexDirection: 'row',
    alignItems: 'center',
    gap: siblingGap(u),
    paddingHorizontal: contentInset(u) - u,
  } as const;
  // A 44 px target even though the drawn well is 36 px tall on phones.
  const hitSlop = Math.max(0, Math.ceil((44 - barControl(u)) / 2));
  return press.onPress ? (
    <Pressable accessibilityRole="button" hitSlop={hitSlop} {...press} style={style}>
      {body}
    </Pressable>
  ) : (
    <View
      accessible
      accessibilityRole="text"
      accessibilityLabel={press.accessibilityLabel}
      style={style}
    >
      {body}
    </View>
  );
}

/**
 * The floating heads-up display shared by every tab: who is with you, how the
 * garden's shield is doing, GRASS, the real-time play allowance and the menu.
 * Symmetric: one inset on all four sides and between every control (coherence
 * plan, step 3), and every control is the same height.
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
  const control = barControl(u);
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
          flexDirection: 'row',
          alignItems: 'center',
          gap: siblingGap(u),
          padding: contentInset(u),
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
            gap: siblingGap(u),
          }}
        >
          <View
            style={{
              width: control,
              height: control,
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
            <Text numberOfLines={1} style={[type.label, { color: c.ink }]}>
              {guardian.pet_name}
            </Text>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: u }}>
              <PixelProp kind="heart" size={6 * u} tint={p.mood < 30 ? c.error : '#C8574A'} />
              <View style={{ flex: 1, maxWidth: 24 * u }}>
                <PixelBar value={p.mood} color={p.mood < 30 ? c.error : c.positive} unit={u} />
              </View>
            </View>
          </View>
        </Pressable>
        <StatChip
          unit={u}
          icon="shield"
          tint={shieldTone}
          accessibilityLabel={`Garden shield: ${state.label}${state.kind === 'care' ? `, ${state.left} seconds left` : ''}. Opens the garden guide`}
          onPress={() => useGame.setState({ guideOpen: true })}
          onLongPress={() => useGame.getState().change({ care_until: 0, recovery_until: 0 })}
        >
          <Text style={[type.label, { color: state.kind === 'exposed' ? c.error : c.ink }]}>
            {shieldText}
          </Text>
        </StatChip>
        <StatChip unit={u} icon="grass" accessibilityLabel={`${p.grass} grass`}>
          {p.grass >= 10000 ? (
            <Text style={[type.label, { color: c.ink }]}>
              {new Intl.NumberFormat('en-GB', {
                notation: 'compact',
                maximumFractionDigits: 1,
              }).format(p.grass)}
            </Text>
          ) : (
            <GrassRoll value={p.grass} size={12} />
          )}
        </StatChip>
        <StatChip
          unit={u}
          icon="hourglass"
          accessibilityLabel={`${left} seconds of play left. Long press to reset demo play budget.`}
          accessibilityHint="Opens the guide to the real-time play allowance and simulated break clock."
          onPress={() => useGame.setState({ guideOpen: true })}
          onLongPress={() => useGame.getState().resetBudget()}
        >
          <Text style={[type.label, { color: left ? c.ink : c.error }]}>{clock(left)}</Text>
        </StatChip>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`Open the menu. ${live ? 'Garden synced' : backendConfigured ? 'No signal' : 'Local garden, saved on this device'}`}
          hitSlop={Math.max(0, Math.ceil((44 - control) / 2))}
          onPress={() => {
            feedback('select');
            openSheet('menu');
          }}
          style={{
            width: control,
            height: control,
            alignItems: 'center',
            justifyContent: 'center',
          }}
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

/**
 * The pixel hotbar: four places and a raised NAP button in the middle. Every slot
 * is an inset well with the same gap to the bar's edges as to its neighbours.
 */
export function GameHotbar({ state, navigation }: BottomTabBarProps) {
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const u = usePixelUnit();
  const awake = useGame((s) => s.player?.mode === 'awake');
  const side = gameSideInset(width) - 8;
  const slotHeight = hotbarSlot(u);
  const napWidth = 30 * u;
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
          height: slotHeight,
          alignItems: 'center',
          justifyContent: 'center',
          gap: u,
        }}
      >
        {focused ? (
          <FrameShape tone={frameTones.leaf} unit={u} />
        ) : (
          <FrameFill fill={layers.well} outline={c.outline} inset />
        )}
        <PixelProp kind={meta.icon} size={12 * u} />
        <Text
          numberOfLines={1}
          style={[
            type.label,
            { fontSize: 10, lineHeight: 12, color: focused ? c.buttonInk : c.ink },
          ]}
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
          flexDirection: 'row',
          alignItems: 'center',
          gap: siblingGap(u),
          padding: contentInset(u),
        }}
      >
        {slot(0)}
        {slot(1)}
        <View style={{ width: napWidth }} />
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
          marginLeft: -napWidth / 2,
          // its bottom lines up with the slots' bottom edge; it rises above the bar
          bottom: u + contentInset(u),
          width: napWidth,
          height: slotHeight + 12 * u,
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
        <PixelProp kind="moon" size={16 * u} tint="#FFF3CF" />
        <Text style={[type.label, { fontSize: 13, lineHeight: 16, color: '#FFF7E2' }]}>NAP</Text>
      </Pressable>
    </View>
  );
}
