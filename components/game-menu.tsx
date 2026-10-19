import { useState, type ReactNode } from 'react';
import { Modal, Pressable, ScrollView, Text, View, useWindowDimensions } from 'react-native';
import Animated, { FadeIn } from 'react-native-reanimated';
import { router } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { cozy as c } from '@/lib/cozy';
import { feedback, useGame, type Player } from '@/lib/game';
import { grasslings, growthStage, levelPreview } from '@/lib/grasslings';
import { collectionOf, guardianPlayer } from '@/lib/visitors';
import { meadowSummary } from '@/lib/garden-growth';
import { PLAY_LIMIT_MS, remainingPlay } from '@/lib/offline-rules';
import { cardDetails, cardIds, cards, type CardId } from '@/lib/cards';
import { closeAllSheets, closeSheet, openSheet, useUi, type MenuTab } from '@/lib/ui';
import { useReducedMotion } from '@/lib/motion';
import { gameLayout, touchReach } from '@/lib/layout';
import {
  contentInset,
  iconSize,
  layers,
  panelGap,
  panelInset,
  siblingGap,
  type,
} from '@/lib/ui-tokens';
import { PixelButton } from '@/components/game-ui';
import {
  FrameFill,
  FrameShape,
  frameTones,
  mixColor,
  usePixelUnit,
} from '@/components/pixel-frame';
import { PixelIcon, type IconName } from '@/components/pixel-icon';
import { GuardianPet } from '@/components/guardian-pet';
import { CardIllustration } from '@/components/habit-cards';
import { GardenJourney } from '@/components/garden-journey';
import {
  GardenProgress,
  GardenStreak,
  RecentBreaks,
  usePlayPaused,
} from '@/components/offline-garden';
import { DailyRhythmCard } from '@/components/daily-rhythm';
import { regionNames } from '@/lib/world-map';
import { zoneRegion } from '@/lib/region-walk';
import { MotionSetting, SoundSettings } from '@/components/garden-guide';

/**
 * The game menu (coherence plan, step 5): Stardew Valley's structure in NapAttack's
 * palette. A wooden frame around a parchment page, a row of icon tabs on top (the
 * active one raised and joined to the page), a close button in the corner, Escape and
 * Back. The pages reuse the game's existing content; nothing here changes a rule.
 */
const tabs: { id: MenuTab; label: string; title: string; icon: IconName }[] = [
  { id: 'companion', label: 'Companion', title: 'COMPANION', icon: 'companion' },
  { id: 'bag', label: 'Bag', title: 'BAG', icon: 'bag' },
  { id: 'journal', label: 'Journal', title: 'JOURNAL', icon: 'journal' },
  { id: 'garden', label: 'Garden', title: 'GARDEN', icon: 'garden' },
  { id: 'map', label: 'Map', title: 'MAP', icon: 'signpost' },
  { id: 'rhythm', label: 'Rhythm', title: 'RHYTHM', icon: 'rhythm' },
  { id: 'settings', label: 'Settings', title: 'SETTINGS', icon: 'settings' },
];

// Leave the menu entirely, then go to another screen.
function go(path: '/journal' | '/missions' | '/arena') {
  closeAllSheets();
  router.push(path);
}

export function GameMenu() {
  const open = useUi((s) => s.sheet === 'menu');
  const tab = useUi((s) => s.menuTab);
  const p = useGame((s) => s.player);
  const u = usePixelUnit();
  const reduced = useReducedMotion();
  const insets = useSafeAreaInsets();
  if (!p) return null;
  const page = tabs.find((t) => t.id === tab) ?? tabs[0];
  const rim = 4 * u;
  return (
    <Modal visible={open} transparent animationType="none" onRequestClose={closeSheet}>
      <View style={{ flex: 1 }}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Close the menu"
          onPress={closeSheet}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: c.shadow,
          }}
        />
        <Animated.View
          entering={reduced ? undefined : FadeIn.duration(140)}
          style={{
            flex: 1,
            width: '100%',
            maxWidth: gameLayout.maxWidth,
            maxHeight: 900,
            alignSelf: 'center',
            paddingTop: insets.top + 12,
            paddingBottom: insets.bottom + 12,
            paddingHorizontal: 12,
          }}
        >
          <View
            accessibilityRole="tablist"
            style={{
              flexDirection: 'row',
              alignItems: 'flex-end',
              gap: u,
              paddingHorizontal: rim + u,
              zIndex: 2,
            }}
          >
            {tabs.map((t) => (
              <MenuTabButton
                key={t.id}
                unit={u}
                icon={t.icon}
                label={t.label}
                active={t.id === page.id}
                onPress={() => {
                  if (t.id !== page.id) feedback('select');
                  useUi.setState({ menuTab: t.id });
                }}
              />
            ))}
          </View>
          <View style={{ flex: 1, padding: rim }}>
            <FrameShape tone={frameTones.wood} unit={u} />
            <View style={{ flex: 1, padding: panelInset(u), gap: panelGap(u) }}>
              <FrameShape tone={frameTones.paper} unit={u} />
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: panelGap(u) }}>
                <Text accessibilityRole="header" style={[type.title, { flex: 1, color: c.ink }]}>
                  {page.title}
                </Text>
                <CornerButton unit={u} label="Close the menu" icon="close" onPress={closeSheet} />
              </View>
              <ScrollView
                key={page.id}
                style={{ flex: 1 }}
                contentContainerStyle={{ gap: 2 * panelGap(u), paddingBottom: u }}
              >
                <MenuPage tab={page.id} player={p} unit={u} />
              </ScrollView>
            </View>
          </View>
        </Animated.View>
      </View>
    </Modal>
  );
}

/** A tab: wood when idle, parchment and raised into the page when active. */
function MenuTabButton({
  unit: u,
  icon,
  label,
  active,
  onPress,
}: {
  unit: number;
  icon: IconName;
  label: string;
  active: boolean;
  onPress: () => void;
}) {
  // the active tab reaches down over the wooden rim and the page's top edge
  // the active tab reaches down over the wooden rim (4) and the page's top edge (2)
  const reach = 6 * u;
  const height = Math.max(44, 30 * u); // a 44 px target on small phones too
  return (
    <Pressable
      accessibilityRole="tab"
      accessibilityLabel={label}
      accessibilityState={{ selected: active }}
      onPress={onPress}
      style={{
        flex: 1,
        maxWidth: 42 * u,
        minWidth: 44,
        height: active ? height + 3 * u + reach : height,
        marginBottom: active ? -reach : 0,
        paddingBottom: active ? reach : 0,
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: active ? 3 : 1,
      }}
    >
      <FrameShape tone={active ? frameTones.paper : frameTones.wood} unit={u} />
      {active && (
        // erase the tab's own bottom edge so it joins the page
        <View
          style={{
            position: 'absolute',
            left: u,
            right: u,
            bottom: 0,
            height: reach,
            backgroundColor: frameTones.paper.fill,
          }}
        />
      )}
      <PixelIcon name={icon} size={iconSize.medium(u)} />
    </Pressable>
  );
}

function CornerButton({
  unit: u,
  label,
  icon,
  onPress,
}: {
  unit: number;
  label: string;
  icon: IconName;
  onPress: () => void;
}) {
  const size = 27 * u;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      onPress={onPress}
      style={touchReach(size)}
    >
      <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
        <FrameShape tone={frameTones.parchment} unit={u} />
        <PixelIcon name={icon} size={iconSize.small(u)} />
      </View>
    </Pressable>
  );
}

function MenuPage({ tab, player, unit }: { tab: MenuTab; player: Player; unit: number }) {
  switch (tab) {
    case 'companion':
      return <CompanionPage player={player} unit={unit} />;
    case 'bag':
      return <BagPage player={player} unit={unit} />;
    case 'journal':
      return <JournalPage player={player} unit={unit} />;
    case 'garden':
      return <GardenPage player={player} unit={unit} />;
    case 'map':
      return <MapPage />;
    case 'rhythm':
      return <RhythmPage />;
    default:
      return <SettingsPage unit={unit} />;
  }
}

function Section({
  label,
  unit: u,
  children,
}: {
  label: string;
  unit: number;
  children: ReactNode;
}) {
  return (
    <View style={{ gap: panelGap(u) }}>
      <Text accessibilityRole="header" style={[type.label, { color: c.shade }]}>
        {label}
      </Text>
      {children}
    </View>
  );
}

/** A bar of ten pixel segments; filled ones carry a lit top row. */
function SegmentBar({
  value,
  max,
  color,
  unit: u,
}: {
  value: number;
  max: number;
  color: string;
  unit: number;
}) {
  const segments = 10;
  const filled = max > 0 ? Math.round(Math.max(0, Math.min(1, value / max)) * segments) : 0;
  const light = mixColor(color, '#FFFFFF', 0.35);
  return (
    <View
      style={{
        height: 8 * u,
        padding: u,
        flexDirection: 'row',
        gap: u,
        backgroundColor: c.outline,
      }}
    >
      {Array.from({ length: segments }, (_, index) => (
        <View
          key={index}
          style={{ flex: 1, backgroundColor: index < filled ? color : layers.well }}
        >
          {index < filled && <View style={{ height: u, backgroundColor: light }} />}
        </View>
      ))}
    </View>
  );
}

function StatRow({
  icon,
  label,
  value,
  max,
  text,
  color,
  unit: u,
}: {
  icon: IconName;
  label: string;
  value: number;
  max: number;
  text: string;
  color: string;
  unit: number;
}) {
  return (
    <View
      accessible
      accessibilityRole="progressbar"
      accessibilityLabel={`${label}: ${text}`}
      accessibilityValue={{ min: 0, max, now: Math.max(0, Math.min(max, value)) }}
      style={{ gap: u }}
    >
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: siblingGap(u) * 2 }}>
        <PixelIcon name={icon} size={iconSize.small(u)} />
        <Text style={[type.label, { flex: 1, color: c.ink }]}>{label}</Text>
        <Text style={[type.caption, { color: c.ink }]}>{text}</Text>
      </View>
      <SegmentBar value={value} max={max} color={color} unit={u} />
    </View>
  );
}

const clock = (seconds: number) =>
  `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;

function CompanionPage({ player: p, unit: u }: { player: Player; unit: number }) {
  const paused = usePlayPaused();
  const budget = useGame((s) => s.rules.budget);
  const now = useGame((s) => s.now);
  const guardian = guardianPlayer(p);
  const family = grasslings[guardian.species];
  const next = levelPreview(p.level);
  const left = remainingPlay(budget, now);
  const total = PLAY_LIMIT_MS / 1000;
  const meadow = meadowSummary(p.offline_seconds);
  const canFeed = !paused && p.mood < 100 && p.grass >= 5;
  const portrait = 54 * u;
  return (
    <>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: panelGap(u) * 2 }}>
        <View
          aria-hidden
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
          style={{ width: portrait, height: portrait, padding: 3 * u, overflow: 'hidden' }}
        >
          <FrameFill fill={artGrass} outline={c.outline} inset />
          <View
            style={{
              position: 'absolute',
              left: 3 * u,
              right: 3 * u,
              top: 3 * u,
              height: Math.round(portrait * 0.48),
              backgroundColor: artSky,
            }}
          />
          <View style={{ flex: 1, alignItems: 'center', justifyContent: 'flex-end' }}>
            <GuardianPet
              player={p}
              size={Math.round(portrait * 0.78)}
              bob={false}
              active={false}
              grumpy={p.mood < 30}
              decorative
            />
          </View>
        </View>
        <View style={{ flex: 1, minWidth: 0, gap: u }}>
          <Text numberOfLines={1} style={[type.heading, { color: c.ink }]}>
            {guardian.pet_name}
          </Text>
          <Text style={[type.label, { color: c.ink }]}>
            {family.habit} FAMILY · LEVEL {p.level}
          </Text>
          <Text style={[type.caption, { color: c.shade }]}>
            {growthStage(p.level)} · next: {next.unlock}
          </Text>
        </View>
      </View>
      <Section label="TODAY" unit={u}>
        <StatRow
          unit={u}
          icon="heart"
          label="MOOD"
          value={p.mood}
          max={100}
          text={`${p.mood}/100`}
          color={p.mood < 30 ? c.error : c.positive}
        />
        <StatRow
          unit={u}
          icon="grass"
          label={`GROWTH TO LEVEL ${next.next}`}
          value={p.grass}
          max={next.cost}
          text={`${Math.min(p.grass, next.cost)}/${next.cost} GRASS`}
          color={c.positive}
        />
        <StatRow
          unit={u}
          icon="time"
          label="PLAY TIME LEFT"
          value={left}
          max={total}
          text={clock(left)}
          color={left ? frameTones.gold.fill : c.error}
        />
        <StatRow
          unit={u}
          icon="flower"
          label="MEADOW"
          value={meadow.planted}
          max={9}
          text={`${meadow.planted} of 9 growing`}
          color={frameTones.nap.fill}
        />
      </Section>
      <View style={{ flexDirection: 'row', gap: panelGap(u) }}>
        <View style={{ flex: 1 }}>
          <PixelButton label="CHANGE" small light onPress={() => openSheet('companions')} />
        </View>
        <View style={{ flex: 1 }}>
          <PixelButton
            label="FEED · 5 GRASS"
            small
            disabled={!canFeed}
            onPress={() => {
              closeAllSheets();
              useGame.getState().feed();
            }}
          />
        </View>
      </View>
      <Text style={[type.caption, { color: c.shade }]}>
        {paused
          ? 'Play time is paused; feeding waits until you are back.'
          : p.mood >= 100
            ? `${guardian.pet_name} is full of good feelings.`
            : p.grass < 5
              ? 'Feeding needs 5 GRASS and lifts mood.'
              : 'Feeding uses 5 GRASS and lifts mood.'}
      </Text>
    </>
  );
}

const artGrass = '#8DAE5A';
const artSky = '#C6DDEE';

function BagPage({ player: p, unit: u }: { player: Player; unit: number }) {
  const [selected, setSelected] = useState<CardId | null>(null);
  const { width } = useWindowDimensions();
  // as many equal slots as fit across the well, at least 26 units each
  const gap = panelGap(u);
  const inner =
    Math.min(width, gameLayout.maxWidth) - 24 - 8 * u - 2 * panelInset(u) - 2 * contentInset(u);
  const columns = Math.max(3, Math.floor((inner + gap) / (39 * u + gap)));
  const slot = Math.floor((inner - gap * (columns - 1)) / columns);
  return (
    <>
      <Text style={[type.caption, { color: c.shade }]}>
        MY DECK · {p.deck.length}/20 · 15 offline MIN = 1 common card. Tap a card for details.
      </Text>
      <View
        style={{
          flexDirection: 'row',
          flexWrap: 'wrap',
          gap,
          padding: contentInset(u),
        }}
      >
        <FrameFill fill={layers.well} outline={c.outline} inset />
        {cardIds.map((id) => {
          const count = p.deck.filter((card) => card === id).length;
          const focused = selected === id;
          return (
            <Pressable
              key={id}
              accessibilityRole="button"
              accessibilityLabel={
                count ? `${cards[id].name}, ${count} in your deck` : 'Empty slot, not found yet'
              }
              accessibilityState={{ selected: focused, disabled: !count }}
              disabled={!count}
              onPress={() => {
                setSelected(focused ? null : id);
                feedback('select');
              }}
              style={{ width: slot, height: slot, alignItems: 'center', justifyContent: 'center' }}
            >
              <FrameShape tone={focused ? frameTones.leaf : frameTones.paper} unit={u} />
              {count > 0 && <CardIllustration id={id} size={32 * u} />}
              {count > 1 && (
                <Text
                  style={[
                    type.caption,
                    { position: 'absolute', right: 3 * u, bottom: u, color: c.ink },
                  ]}
                >
                  ×{count}
                </Text>
              )}
            </Pressable>
          );
        })}
      </View>
      {selected ? (
        <View accessibilityLiveRegion="polite" style={{ gap: u }}>
          <Text style={[type.heading, { color: c.ink }]}>{cards[selected].name}</Text>
          <Text style={[type.label, { color: c.ink }]}>
            {cards[selected].rarity} · {cards[selected].habit} · {cards[selected].effect}
          </Text>
          <Text style={[type.body, { color: c.ink }]}>{cardDetails[selected]}</Text>
        </View>
      ) : (
        <Text style={[type.body, { color: c.shade }]}>
          Cards come from time away. Empty slots are cards you have not found yet.
        </Text>
      )}
      <PixelButton
        label="SEE CARDS FULL SIZE"
        small
        light
        onPress={() => {
          closeAllSheets();
          useGame.setState({ deckOpen: true });
        }}
      />
    </>
  );
}

function JournalPage({ player: p, unit: u }: { player: Player; unit: number }) {
  const met = collectionOf(p);
  const friends = met.filter((entry) => entry.befriendedAt !== null).length;
  return (
    <>
      <Section label="FIELD JOURNAL" unit={u}>
        <JournalLine unit={u} icon="friends" text={`${met.length} of 9 visitors met`} />
        <JournalLine unit={u} icon="heart" text={`${friends} befriended`} />
        <JournalLine unit={u} icon="journal" text="Postcards and kept memories" />
      </Section>
      <PixelButton label="OPEN THE FIELD JOURNAL" small onPress={() => go('/journal')} />
    </>
  );
}

function JournalLine({ unit: u, icon, text }: { unit: number; icon: IconName; text: string }) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: siblingGap(u) * 2 }}>
      <PixelIcon name={icon} size={iconSize.small(u)} />
      <Text style={[type.body, { flex: 1, color: c.ink }]}>{text}</Text>
    </View>
  );
}

function GardenPage({ player: p, unit: u }: { player: Player; unit: number }) {
  const now = useGame((s) => s.now);
  const meadow = meadowSummary(p.offline_seconds);
  const next = levelPreview(p.level);
  return (
    <>
      <Section
        label={`TODAY · ${new Date(now)
          .toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
          .toUpperCase()}`}
        unit={u}
      >
        <GardenProgress />
      </Section>
      <Section label="MEADOW" unit={u}>
        <Text style={[type.body, { color: c.ink }]}>
          {meadow.blooming} beds in bloom, {meadow.fruiting} fruit trees
          {meadow.nextIn === null
            ? '. Fully grown.'
            : `. Next growth in ${meadow.nextIn} simulated MIN.`}
        </Text>
        <Text style={[type.body, { color: c.ink }]}>
          Next common card in {15 - (p.offline_seconds % 15)} simulated MIN. Level {next.next} costs{' '}
          {next.cost} GRASS: {next.unlock}.
        </Text>
      </Section>
      <GardenStreak />
      <RecentBreaks />
      <Section label="GARDEN TRAIL" unit={u}>
        <GardenJourney
          player={p}
          onMissions={() => go('/missions')}
          onJournal={() => go('/journal')}
          onCompanions={() => openSheet('companions')}
          onSpar={() => go('/arena')}
        />
      </Section>
    </>
  );
}

/** The map's page: where the companion is and how much of the world it has walked;
 *  the map itself opens over everything (one map for the whole game, home-hub.md
 *  phase 2). */
function MapPage() {
  const world = useGame((s) => s.world);
  const unit = usePixelUnit();
  const regionsSeen = new Set((world?.visited ?? []).map((z) => zoneRegion(z))).size;
  return (
    <Section label="THE WORLD" unit={unit}>
      <Text style={[type.body, { color: c.ink }]}>
        {world
          ? `In ${regionNames[world.region].toLowerCase().replace(/(^|\s)\S/g, (m) => m.toUpperCase())}. ${world.visited.length} ${world.visited.length === 1 ? 'place' : 'places'} walked in ${regionsSeen} ${regionsSeen === 1 ? 'region' : 'regions'}.`
          : 'Walk out of the garden gate and the map fills in as you go.'}
      </Text>
      <PixelButton label="OPEN THE MAP" small light onPress={() => openSheet('map')} />
    </Section>
  );
}

function RhythmPage() {
  const [editing, setEditing] = useState(false);
  return <DailyRhythmCard active open={editing} onOpenChange={setEditing} />;
}

function SettingsPage({ unit: u }: { unit: number }) {
  return (
    <>
      <MotionSetting />
      <SoundSettings />
      <Section label="HOW IT WORKS" unit={u}>
        <Text style={[type.body, { color: c.ink }]}>
          Shields, raids, play time and visitors, explained in the garden guide.
        </Text>
        <PixelButton
          label="OPEN THE GARDEN GUIDE"
          small
          light
          onPress={() => {
            closeAllSheets();
            useGame.setState({ guideOpen: true });
          }}
        />
      </Section>
      <Text style={[type.caption, { color: c.shade }]}>Local garden, saved on this device.</Text>
    </>
  );
}
