import { Pressable, Text, View, useWindowDimensions } from 'react-native';
import type { ComponentProps, ReactNode } from 'react';
import type { Tabs } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { cozy as c } from '@/lib/cozy';
import { backendConfigured } from '@/lib/bilt';
import { clock, feedback, status, useGame } from '@/lib/game';
import { remainingPlay } from '@/lib/offline-rules';
import { guardianPlayer } from '@/lib/visitors';
import { gameSideInset, hudLayout, touchReach } from '@/lib/layout';
import { openSheet } from '@/lib/ui';
import {
  FrameFill,
  FrameShape,
  PixelFrame,
  frameTones,
  usePixelUnit,
} from '@/components/pixel-frame';
import {
  barControl,
  contentInset,
  hotbarSlot,
  iconSize,
  layers,
  siblingGap,
  type,
} from '@/lib/ui-tokens';
import { PixelIcon, type IconName } from '@/components/pixel-icon';
import { GuardianPet } from '@/components/guardian-pet';
import { DreamDustRoll } from '@/components/pixel-feedback';

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
        height: 4 * unit,
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

/** A HUD stat: one inset well holding an icon and its value, the same height as the portrait. */
function StatChip({
  unit: u,
  icon,
  muted = false,
  children,
  ...press
}: {
  unit: number;
  icon: IconName;
  /** greys the icon for an inactive state (an open garden shield) */
  muted?: boolean;
  children: ReactNode;
} & Pick<
  ComponentProps<typeof Pressable>,
  'accessibilityLabel' | 'accessibilityHint' | 'onPress' | 'onLongPress' | 'accessibilityRole'
>) {
  const body = (
    <>
      <FrameFill fill={layers.well} outline={c.outline} inset />
      <PixelIcon name={icon} size={iconSize.small(u)} muted={muted} />
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
  return press.onPress ? (
    <Pressable accessibilityRole="button" {...press} style={touchReach(44, barControl(u))}>
      <View style={style}>{body}</View>
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
 * garden's shield is doing, Dream Dust, the real-time play allowance and the menu.
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
              <PixelIcon name="heart" size={iconSize.small(u)} />
              <View style={{ flex: 1, maxWidth: 36 * u }}>
                <PixelBar value={p.mood} color={p.mood < 30 ? c.error : c.positive} unit={u} />
              </View>
            </View>
          </View>
        </Pressable>
        <StatChip
          unit={u}
          icon="shield"
          muted={state.kind === 'exposed'}
          accessibilityLabel={`Garden shield: ${state.label}${state.kind === 'care' ? `, ${state.left} seconds left` : ''}. Opens the garden guide`}
          onPress={() => useGame.setState({ guideOpen: true })}
          onLongPress={() => useGame.getState().change({ care_until: 0, recovery_until: 0 })}
        >
          <Text style={[type.label, { color: state.kind === 'exposed' ? c.error : c.ink }]}>
            {shieldText}
          </Text>
        </StatChip>
        <StatChip unit={u} icon="dreamDust" accessibilityLabel={`${p.grass} Dream Dust`}>
          {p.grass >= 10000 ? (
            <Text style={[type.label, { color: c.ink }]}>
              {new Intl.NumberFormat('en-GB', {
                notation: 'compact',
                maximumFractionDigits: 1,
              }).format(p.grass)}
            </Text>
          ) : (
            <DreamDustRoll value={p.grass} size={12} />
          )}
        </StatChip>
        <StatChip
          unit={u}
          icon="time"
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
          onPress={() => {
            feedback('select');
            openSheet('menu');
          }}
          style={touchReach(control)}
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
            <PixelIcon name="menu" size={iconSize.small(u)} />
            <View
              style={{
                position: 'absolute',
                right: 4 * u,
                top: 4 * u,
                width: u,
                height: u,
                backgroundColor: live || !backendConfigured ? c.moss : c.error,
              }}
            />
          </View>
        </Pressable>
      </PixelFrame>
    </View>
  );
}

const tabs: Record<string, { label: string; icon: IconName }> = {
  index: { label: 'HOME', icon: 'home' },
  missions: { label: 'MISSIONS', icon: 'missions' },
  arena: { label: 'ARENA', icon: 'arena' },
  shop: { label: 'SHOP', icon: 'shop' },
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
  const slot = (index: number) => {
    const route = state.routes[index];
    if (!route) return null;
    const meta = tabs[route.name] ?? { label: route.name.toUpperCase(), icon: 'home' as const };
    const focused = state.index === index;
    // (the world beyond the valley is part of HOME: its tab stays lit there, and a tap
    // on it goes back to the home hub)
    const lit = focused || (route.name === 'index' && state.routes[state.index]?.name === 'world');
    return (
      <Pressable
        key={route.key}
        accessibilityRole="tab"
        accessibilityState={{ selected: lit }}
        aria-selected={lit}
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
        {lit ? (
          <FrameShape tone={frameTones.leaf} unit={u} />
        ) : (
          <FrameFill fill={layers.well} outline={c.outline} inset />
        )}
        <PixelIcon name={meta.icon} size={iconSize.medium(u)} />
        <Text
          numberOfLines={1}
          style={[type.label, { fontSize: 10, lineHeight: 12, color: lit ? c.buttonInk : c.ink }]}
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
        {/* the nap sits in the row like the other slots, set apart only by its colour
            and a slightly larger icon, so it never rises over the screen above */}
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
            flex: 1,
            height: slotHeight,
            alignItems: 'center',
            justifyContent: 'center',
            gap: u,
            transform: [{ translateY: pressed ? u : 0 }],
            opacity: awake ? 1 : 0.6,
          })}
        >
          <FrameShape tone={frameTones.nap} unit={u} />
          <PixelIcon name="nap" size={iconSize.medium(u)} />
          <Text style={[type.label, { fontSize: 10, lineHeight: 12, color: '#FFF7E2' }]}>NAP</Text>
        </Pressable>
        {slot(2)}
        {slot(3)}
      </PixelFrame>
    </View>
  );
}
