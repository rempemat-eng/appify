import { useState, type ReactNode } from 'react';
import { Modal, Pressable, ScrollView, View, useWindowDimensions } from 'react-native';
import { router } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { cozy as c } from '@/lib/cozy';
import { useGame } from '@/lib/game';
import { guardianPlayer } from '@/lib/visitors';
import { closeSheet, openSheet, useUi } from '@/lib/ui';
import type { BreakIntention } from '@/lib/companion-memories';
import { gameLayout } from '@/lib/layout';
import { CozySheet } from '@/components/cozy-ui';
import { PixelButton, PixelText } from '@/components/game-ui';
import { BodyText } from '@/components/pixel-feedback';
import { BreakIntentionPicker } from '@/components/companion-memories';
import { usePlayPaused } from '@/components/offline-garden';
import { DailyRhythmCard } from '@/components/daily-rhythm';
import { GameMenu } from '@/components/game-menu';
import { GuardianPicker } from '@/components/visitors';
import { WorldMap } from '@/components/world-map';
import { mapRegionOrder, regionNames } from '@/lib/world-map';

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

/** The world map over everything, opened from the menu's Map page: where the companion
 *  stands and the places it has walked (the same map as the world screen's). */
function WorldMapSheet() {
  const open = useUi((s) => s.sheet === 'map');
  const world = useGame((s) => s.world);
  const { width, height } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  if (!open) return null;
  return (
    <Modal visible transparent animationType="none" onRequestClose={closeSheet}>
      <WorldMap
        regions={mapRegionOrder.map((id) => ({ id, name: regionNames[id] }))}
        current={world?.region ?? 'valley'}
        here={world ? { x: world.x, y: world.y } : null}
        visited={world?.visited ?? noZones}
        width={width}
        height={height}
        insetTop={insets.top}
        insetBottom={insets.bottom}
        onClose={closeSheet}
      />
    </Modal>
  );
}
const noZones: readonly string[] = [];

/** Every global sheet, mounted once beside the tabs. */
export function GameMenus() {
  const p = useGame((s) => s.player);
  const sheet = useUi((s) => s.sheet);
  if (!p) return null;
  return (
    <>
      <NapSheet />
      <GameMenu />
      <WorldMapSheet />
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
