import { useState, type ReactNode } from 'react';
import { Modal, Pressable, ScrollView, Text, View, useWindowDimensions } from 'react-native';
import { router } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { cozy as c } from '@/lib/cozy';
import { feedback, useGame } from '@/lib/game';
import { grasslings, growthStage, levelPreview } from '@/lib/grasslings';
import { guardianPlayer, isVisitorId, visitorInfo } from '@/lib/visitors';
import { meadowSummary } from '@/lib/garden-growth';
import { closeSheet, openSheet, useUi } from '@/lib/ui';
import type { BreakIntention } from '@/lib/companion-memories';
import { gameLayout } from '@/lib/layout';
import { CozySheet } from '@/components/cozy-ui';
import { PixelButton, PixelText } from '@/components/game-ui';
import { BodyText } from '@/components/pixel-feedback';
import { FrameShape, frameTones, usePixelUnit } from '@/components/pixel-frame';
import { BreakIntentionPicker } from '@/components/companion-memories';
import { GardenJourney } from '@/components/garden-journey';
import {
  GardenProgress,
  GardenStreak,
  RecentBreaks,
  usePlayPaused,
} from '@/components/offline-garden';
import { DailyRhythmCard } from '@/components/daily-rhythm';
import { GuardianPicker } from '@/components/visitors';
import { PixelIcon, type IconName } from '@/components/pixel-icon';

// Close the sheet, then leave for another screen.
function go(path: '/journal' | '/missions' | '/arena') {
  closeSheet();
  router.push(path);
}

/** A bottom sheet in a transparent modal, framed like the rest of the game. */
export function GameSheet({
  visible,
  title,
  onClose,
  children,
}: {
  visible: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  const insets = useSafeAreaInsets();
  const { height } = useWindowDimensions();
  return (
    <Modal visible={visible} transparent animationType="none" onRequestClose={onClose}>
      <View style={{ flex: 1, justifyContent: 'flex-end' }}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Close"
          onPress={onClose}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: c.shadow,
          }}
        />
        <View
          style={{
            padding: 12,
            paddingBottom: insets.bottom + 12,
            width: '100%',
            maxWidth: gameLayout.maxWidth,
            alignSelf: 'center',
          }}
        >
          <CozySheet style={{ gap: 12, maxHeight: height * 0.86 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
              <PixelText
                accessibilityRole="header"
                style={{ flex: 1, minWidth: 0, fontSize: 16, lineHeight: 24 }}
              >
                {title}
              </PixelText>
              <PixelButton label="CLOSE" small light onPress={onClose} />
            </View>
            <ScrollView contentContainerStyle={{ gap: 12, paddingBottom: 4 }}>
              {children}
            </ScrollView>
          </CozySheet>
        </View>
      </View>
    </Modal>
  );
}

export function NapSheet() {
  const open = useUi((s) => s.sheet === 'nap');
  const p = useGame((s) => s.player);
  const paused = usePlayPaused();
  const [plan, setPlan] = useState<{ open: boolean; intention: BreakIntention | null }>({
    open,
    intention: null,
  });
  if (plan.open !== open) setPlan({ open, intention: null });
  if (!p) return null;
  const name = guardianPlayer(p).pet_name;
  // Leaving the sheet always forgets an unfinished idea.
  const close = () => {
    setPlan({ open: false, intention: null });
    closeSheet();
  };
  return (
    <GameSheet visible={open} title="TAKE A NAP" onClose={close}>
      <BodyText style={{ fontSize: 15, lineHeight: 21 }}>
        Put your phone down for a while. {name} will curl up in bed and keep the garden safe until
        you come back.
      </BodyText>
      <BreakIntentionPicker
        value={plan.intention}
        onChange={(intention) => setPlan({ open, intention })}
        disabled={p.mode !== 'awake'}
      />
      <PixelButton
        label="START NAP"
        gold={paused}
        disabled={p.mode !== 'awake'}
        onPress={() => {
          const intention = plan.intention;
          close();
          useGame.getState().sleep(undefined, intention);
        }}
      />
      <PixelButton
        label="OR EXPLORE A PLACE"
        small
        light
        onPress={() => {
          close();
          router.push('/missions');
        }}
      />
      <BodyText style={{ fontSize: 12, textAlign: 'center', color: c.shade }}>
        Demo time: 1 real second = 1 simulated MIN. +1 GRASS per MIN.
      </BodyText>
    </GameSheet>
  );
}

function MenuTile({
  icon,
  label,
  detail,
  onPress,
  disabled = false,
}: {
  icon: IconName;
  label: string;
  detail?: string;
  onPress: () => void;
  disabled?: boolean;
}) {
  const u = usePixelUnit();
  const [pressed, setPressed] = useState(false);
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={detail ? `${label}. ${detail}` : label}
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPressIn={() => setPressed(true)}
      onPressOut={() => setPressed(false)}
      onPress={() => {
        feedback('select');
        onPress();
      }}
      style={{
        flexBasis: '47%',
        flexGrow: 1,
        minHeight: 64,
        padding: 4 * u,
        gap: 2 * u,
        flexDirection: 'row',
        alignItems: 'center',
        opacity: disabled ? 0.55 : 1,
        transform: [{ translateY: pressed ? u : 0 }],
      }}
    >
      <FrameShape tone={pressed ? frameTones.parchment : frameTones.paper} unit={u} />
      <PixelIcon name={icon} size={24} />
      <View style={{ flex: 1, minWidth: 0 }}>
        <Text
          style={{ fontFamily: 'PixelifySans_700Bold', fontSize: 14, lineHeight: 17, color: c.ink }}
        >
          {label}
        </Text>
        {detail && (
          <Text
            numberOfLines={2}
            style={{
              fontFamily: 'PixelifySans_500Medium',
              fontSize: 11,
              lineHeight: 13,
              color: c.shade,
            }}
          >
            {detail}
          </Text>
        )}
      </View>
    </Pressable>
  );
}

function MenuSheet() {
  const open = useUi((s) => s.sheet === 'menu');
  const p = useGame((s) => s.player);
  const paused = usePlayPaused();
  if (!p) return null;
  const feedLabel = paused
    ? 'Take a break first'
    : p.mood >= 100
      ? 'Full and happy'
      : p.grass < 5
        ? 'Needs 5 GRASS'
        : '5 GRASS · +mood';
  const meadow = meadowSummary(p.offline_seconds);
  return (
    <GameSheet visible={open} title="GARDEN MENU" onClose={closeSheet}>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
        <MenuTile
          icon="companion"
          label="Companions"
          detail="Who comes along"
          onPress={() => openSheet('companions')}
        />
        <MenuTile
          icon="energy"
          label="My deck"
          detail="Your habit cards"
          onPress={() => {
            closeSheet();
            useGame.setState({ deckOpen: true });
          }}
        />
        <MenuTile
          icon="journal"
          label="Journal"
          detail="Visitors, postcards, memories"
          onPress={() => go('/journal')}
        />
        <MenuTile
          icon="bowl"
          label="Feed"
          detail={feedLabel}
          disabled={paused || p.mood >= 100 || p.grass < 5}
          onPress={() => {
            closeSheet();
            useGame.getState().feed();
          }}
        />
        <MenuTile
          icon="rhythm"
          label="Your rhythm"
          detail="Rest, focus, own time"
          onPress={() => openSheet('rhythm')}
        />
        <MenuTile
          icon="garden"
          label="Garden"
          detail={`${meadow.planted} of 9 meadow spots growing`}
          onPress={() => openSheet('stats')}
        />
        <MenuTile
          icon="signpost"
          label="Garden trail"
          detail="What to try next"
          onPress={() => openSheet('trail')}
        />
        <MenuTile
          icon="shield"
          label="How it works"
          detail="Shields, raids, play time"
          onPress={() => {
            closeSheet();
            useGame.setState({ guideOpen: true });
          }}
        />
      </View>
      <PixelButton label="BACK TO THE GARDEN" small light onPress={closeSheet} />
    </GameSheet>
  );
}

function StatsSheet() {
  const open = useUi((s) => s.sheet === 'stats');
  const p = useGame((s) => s.player);
  const now = useGame((s) => s.now);
  if (!p) return null;
  const guardian = guardianPlayer(p);
  const meadow = meadowSummary(p.offline_seconds);
  return (
    <GameSheet visible={open} title="YOUR GARDEN" onClose={closeSheet}>
      <BodyText style={{ fontFamily: 'PixelifySans_700Bold' }}>
        Today ·{' '}
        {new Date(now).toLocaleDateString(undefined, {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        })}
      </BodyText>
      <GardenProgress />
      <BodyText>
        {isVisitorId(guardian.guardian)
          ? visitorInfo(guardian.guardian).name
          : grasslings[p.species].name}{' '}
        · {grasslings[guardian.species].habit}
      </BodyText>
      <BodyText>
        Level {p.level} · {growthStage(p.level)} · mood {p.mood} / 100
      </BodyText>
      <BodyText>
        Meadow: {meadow.blooming} beds in bloom, {meadow.fruiting} fruit trees
        {meadow.nextIn === null
          ? '. Fully grown.'
          : `. Next growth in ${meadow.nextIn} simulated MIN.`}
      </BodyText>
      <BodyText>Next common card in {15 - (p.offline_seconds % 15)} simulated MIN</BodyText>
      <BodyText>
        Level {levelPreview(p.level).next} · {levelPreview(p.level).cost} GRASS ·{' '}
        {levelPreview(p.level).unlock}
      </BodyText>
      <GardenStreak />
      <RecentBreaks />
      <PixelButton label="DONE" onPress={closeSheet} />
    </GameSheet>
  );
}

function TrailSheet() {
  const open = useUi((s) => s.sheet === 'trail');
  const p = useGame((s) => s.player);
  if (!p) return null;
  return (
    <GameSheet visible={open} title="GARDEN TRAIL" onClose={closeSheet}>
      <GardenJourney
        player={p}
        onMissions={() => go('/missions')}
        onJournal={() => go('/journal')}
        onCompanions={() => openSheet('companions')}
        onSpar={() => go('/arena')}
      />
      <PixelButton label="DONE" small light onPress={closeSheet} />
    </GameSheet>
  );
}

/** Every global sheet, mounted once beside the tabs. */
export function GameMenus() {
  const p = useGame((s) => s.player);
  const sheet = useUi((s) => s.sheet);
  if (!p) return null;
  return (
    <>
      <NapSheet />
      <MenuSheet />
      <StatsSheet />
      <TrailSheet />
      <GuardianPicker
        player={p}
        open={sheet === 'companions'}
        onOpenChange={(next) => (next ? openSheet('companions') : closeSheet())}
        showCard={false}
      />
      <DailyRhythmCard
        active={sheet === 'rhythm'}
        open={sheet === 'rhythm'}
        onOpenChange={(next) => (next ? openSheet('rhythm') : closeSheet())}
        showCard={false}
      />
    </>
  );
}
