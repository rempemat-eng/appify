import { useState } from 'react';
import { Image, Modal, Pressable, ScrollView, View, useWindowDimensions } from 'react-native';
import { useNavigation } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Polyline } from 'react-native-svg';
import { missions, feedback, useGame } from '@/lib/game';
import { useAppActive } from '@/lib/app-active';
import { artMaterials } from '@/lib/art-direction';
import { cozy as c } from '@/lib/cozy';
import { gameColumn, gameLayout, hotbarClearance, hudClearance } from '@/lib/layout';
import { worldIds, worldMaps, type WorldId } from '@/lib/world-maps';
import { worldCatalogue } from '@/lib/world-catalogue';
import { worldProps } from '@/lib/world-assets';
import { type BreakIntention } from '@/lib/companion-memories';
import { BreakIntentionPicker } from '@/components/companion-memories';
import { CozyBackground, CozySheet } from '@/components/cozy-ui';
import { BodyText } from '@/components/pixel-feedback';
import { PixelButton } from '@/components/game-ui';
import { PixelFrame } from '@/components/pixel-frame';

// Presentation anchors only. Mission rules and landmark art live in their catalogues.
const anchors: Record<WorldId, { x: number; y: number }> = {
  park: { x: 18, y: 74 },
  book: { x: 50, y: 50 },
  mountain: { x: 82, y: 26 },
};

/** One still map, not three simultaneously mounted world scenes. */
export function MissionDestinationMap({
  selected,
  level,
  compact,
  onSelect,
}: {
  selected: WorldId;
  level: number;
  compact: boolean;
  onSelect: (world: WorldId) => void;
}) {
  const { fontScale } = useWindowDimensions();
  const mapHeight = Math.round((compact ? 144 : 280) * Math.max(1, fontScale ?? 1));
  return (
    <PixelFrame style={{ padding: 0, height: mapHeight }} tone="leaf">
      <View
        // @ts-expect-error dataSet is a react-native-web prop (shared crisp-art CSS)
        dataSet={{ pixel: 'true' }}
        style={{ flex: 1, overflow: 'hidden' }}
      >
        <View
          pointerEvents="none"
          aria-hidden
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
          style={{ position: 'absolute', inset: 0 }}
        >
          <Svg width="100%" height="100%" viewBox="0 0 192 128" preserveAspectRatio="none">
            <Polyline
              points={compact ? '35,64 157,64' : '96,124 96,95 35,95 96,95 96,64 96,33 157,33'}
              stroke={artMaterials.path[0]}
              strokeWidth={8}
              fill="none"
            />
            <Polyline
              points={compact ? '35,64 157,64' : '96,124 96,95 35,95 96,95 96,64 96,33 157,33'}
              stroke={artMaterials.path[3]}
              strokeWidth={5}
              fill="none"
            />
          </Svg>
          {!compact &&
            [
              [5, 12],
              [29, 10],
              [34, 68],
              [71, 78],
              [92, 63],
            ].map(([x, y]) => (
              <Image
                key={`${x}-${y}`}
                source={worldProps.tree}
                resizeMode="contain"
                style={{ position: 'absolute', left: `${x}%`, top: `${y}%`, width: 36, height: 48 }}
              />
            ))}
        </View>
        {worldIds.map((id) => {
          const mission = missions.find((item) => item.id === id);
          const landmark = worldMaps[id].objects.find(
            (object) => object.id === worldCatalogue[id].previewLandmark,
          );
          if (!mission || !landmark) return null;
          const chosen = id === selected;
          const locked = level < mission.level;
          return (
            <Pressable
              key={id}
              accessibilityRole="button"
              accessibilityLabel={`${mission.name}${locked ? `, level ${mission.level} needed` : ''}`}
              accessibilityState={{ selected: chosen }}
              aria-pressed={chosen}
              onPress={() => onSelect(id)}
              style={{
                position: 'absolute',
                left: `${anchors[id].x}%`,
                top: `${compact ? 50 : anchors[id].y}%`,
                width: 88,
                minHeight: 84,
                marginLeft: -44,
                marginTop: -56,
              }}
            >
              <PixelFrame tone={chosen ? 'gold' : 'paper'} style={{ alignItems: 'center', gap: 2 }}>
                <Image
                  accessible={false}
                  source={worldProps[landmark.sprite]}
                  resizeMode="contain"
                  style={{ width: 64, height: 50 }}
                />
                <BodyText
                  style={{
                    fontSize: 11,
                    lineHeight: 14,
                    textAlign: 'center',
                    fontFamily: 'PixelifySans_700Bold',
                  }}
                >
                  {worldCatalogue[id].postcardTitle}
                </BodyText>
                {locked && (
                  <BodyText style={{ fontSize: 11, lineHeight: 14 }}>LV {mission.level}</BodyText>
                )}
              </PixelFrame>
            </Pressable>
          );
        })}
      </View>
    </PixelFrame>
  );
}

/** Mounted only while the Missions tab is focused, so unfinished drafts expire on leaving. */
export function MissionDeparture() {
  const [selected, setSelected] = useState<WorldId>('park');
  const [intention, setIntention] = useState<BreakIntention | null>(null);
  const [ideasOpen, setIdeasOpen] = useState(false);
  const player = useGame((state) => state.player);
  const battle = useGame((state) => state.battle);
  const pendingReturn = useGame((state) => state.missionReturnPending);
  const appActive = useAppActive();
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();
  const { height } = useWindowDimensions();
  const compact = height < 680;
  const mission = missions.find((item) => item.id === selected);
  if (!player || !mission) return null;
  const locked = player.level < mission.level;
  const busy = player.mode !== 'awake' || !!battle || pendingReturn || !appActive;
  const start = () => {
    // Check live state as well as disabled presentation; stale/double taps grant nothing.
    const latest = useGame.getState();
    if (
      !navigation.isFocused() ||
      !appActive ||
      !latest.player ||
      latest.player.mode !== 'awake' ||
      latest.player.level < mission.level ||
      latest.battle ||
      latest.missionReturnPending
    )
      return;
    latest.sleep(mission.id, intention);
    if (useGame.getState().player?.mode === 'mission') {
      setIntention(null);
      setIdeasOpen(false);
    }
  };
  return (
    <View style={{ flex: 1 }}>
      <CozyBackground />
      <View
        style={[
          gameColumn,
          {
            flex: 1,
            paddingHorizontal: gameLayout.gutter,
            paddingTop: hudClearance(insets.top),
            paddingBottom: hotbarClearance(insets.bottom),
            gap: 8,
          },
        ]}
      >
        <ScrollView contentContainerStyle={{ flexGrow: 1, gap: 12, paddingBottom: 8 }}>
          <BodyText
            accessibilityRole="header"
            style={{ fontSize: 18, fontFamily: 'PixelifySans_700Bold' }}
          >
            BEYOND THE GARDEN GATE
          </BodyText>
          <MissionDestinationMap
            selected={selected}
            level={player.level}
            compact={compact}
            onSelect={(id) => {
              setSelected(id);
              feedback('select');
            }}
          />
          <PixelFrame style={{ gap: 6 }}>
            <BodyText
              accessibilityRole="header"
              style={{ fontSize: 18, fontFamily: 'PixelifySans_700Bold' }}
            >
              {mission.name}
            </BodyText>
            <BodyText>
              {mission.duration} MIN · {mission.duration}s in this demo
            </BodyText>
            <BodyText style={{ fontSize: 13 }}>{worldCatalogue[selected].description}</BodyText>
            <BodyText style={{ fontSize: 13 }}>
              {mission.reward} GRASS · {selected === 'mountain' ? 'EPIC' : 'RARE'} card · postcard
              {selected === 'mountain' ? ' · new hat (or +50 GRASS if all owned)' : ''}
            </BodyText>
            <BodyText style={{ fontSize: 12, color: c.shade }}>
              Returning early keeps common cards, without completion rewards. No need to watch the
              journey.
            </BodyText>
          </PixelFrame>
        </ScrollView>
        <View style={{ flexDirection: 'row', gap: 8, alignItems: 'stretch' }}>
          <View style={{ flex: 1 }}>
            <PixelButton
              small
              light
              label={intention ? `IDEA: ${intention.toUpperCase()}` : 'BREAK IDEA'}
              disabled={busy}
              onPress={() => setIdeasOpen(true)}
            />
          </View>
          <View style={{ flex: 2 }}>
            <PixelButton
              small
              label={
                locked
                  ? `LEVEL ${mission.level} NEEDED`
                  : busy
                    ? 'ON A BREAK'
                    : `START ${mission.name}`
              }
              disabled={locked || busy}
              onPress={start}
            />
          </View>
        </View>
      </View>
      {ideasOpen && (
        <Modal transparent visible animationType="none" onRequestClose={() => setIdeasOpen(false)}>
          <View
            style={{ flex: 1, justifyContent: 'center', padding: 16, backgroundColor: c.ambient }}
          >
            <CozySheet
              style={{
                width: '100%',
                maxWidth: gameLayout.maxWidth - 32,
                alignSelf: 'center',
                maxHeight: height - insets.top - insets.bottom - 32,
                gap: 12,
              }}
            >
              <ScrollView>
                <BreakIntentionPicker value={intention} onChange={setIntention} disabled={busy} />
              </ScrollView>
              <PixelButton label="BACK TO MAP" onPress={() => setIdeasOpen(false)} />
            </CozySheet>
          </View>
        </Modal>
      )}
    </View>
  );
}
