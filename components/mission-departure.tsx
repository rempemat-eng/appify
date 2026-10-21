import { useState } from 'react';
import { Modal, ScrollView, View, useWindowDimensions } from 'react-native';
import { router, useNavigation } from 'expo-router';
import { useUi } from '@/lib/ui';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { missions, feedback, useGame, type Player } from '@/lib/game';
import { useAppActive } from '@/lib/app-active';
import { artMaterials } from '@/lib/art-direction';
import { cozy as c } from '@/lib/cozy';
import { gameColumn, gameLayout, hotbarClearance, hudClearance } from '@/lib/layout';
import { worldCatalogue } from '@/lib/world-catalogue';
import { missionMapPlaces } from '@/lib/mission-map';
import { missionPlaces, regionPoint } from '@/lib/world-places';
import { AtlasWalk } from '@/components/atlas-walk';
import { type BreakIntention } from '@/lib/companion-memories';
import { BreakIntentionPicker } from '@/components/companion-memories';
import { CozyBackground, CozySheet } from '@/components/cozy-ui';
import { BodyText } from '@/components/pixel-feedback';
import { PixelButton } from '@/components/game-ui';
import { PixelFrame, usePixelUnit } from '@/components/pixel-frame';

export type MapPlaceId = keyof typeof missionMapPlaces;

/** The places that open another screen rather than a mission (lib/mission-places.ts). */
const routePlaces = {
  arena: {
    title: 'SPARRING RING',
    description: 'A trodden ring past the gate. Spar with Doomscroll Dave and get ready for raids.',
    action: 'TO THE SPARRING RING',
    path: '/arena',
  },
  shop: {
    title: "MOSS'S STALL",
    description: 'Moss keeps the stall at the crossroads, with everything to grow your garden.',
    action: "VISIT MOSS'S STALL",
    path: '/shop',
  },
  garden: {
    title: 'HOME GARDEN',
    description: 'Back through the gate to the hut, the meadow and your companion’s bed.',
    action: 'BACK TO THE GARDEN',
    path: '/',
  },
} as const;
type RoutePlaceId = keyof typeof routePlaces;
const isRoutePlace = (id: MapPlaceId): id is RoutePlaceId => id in routePlaces;

const placeOrder: MapPlaceId[] = ['book', 'mountain', 'park', 'shop', 'arena', 'garden'];
const placeDescription = (id: MapPlaceId) =>
  isRoutePlace(id) ? routePlaces[id].description : worldCatalogue[id].description;
const placeName = (id: MapPlaceId) =>
  isRoutePlace(id) ? routePlaces[id].title : worldCatalogue[id].postcardTitle;
// Milliseconds per art pixel walked, and the walk's bounds in milliseconds.
const WALK = { msPerPixel: 7, min: 320, max: 1400 };

/**
 * The valley itself, as the missions map (living-world plan W2): a window onto the
 * walkable world (the same zones you walk out of the gate into), the camera on the
 * chosen place with its name tags over the landmarks, and a row of place buttons. A
 * new choice sends the companion walking there along the real paths (squeezed into a
 * moment). Walking is presentation only and never starts or opens anything.
 */
export function MissionDestinationMap({
  selected,
  level,
  compact,
  onSelect,
}: {
  selected: MapPlaceId;
  level: number;
  compact: boolean;
  player?: Player;
  onSelect: (place: MapPlaceId) => void;
}) {
  const shared = usePixelUnit();
  const frameInset = 4 * shared;
  const [size, setSize] = useState({ w: 0, h: 0 });
  const [walkKey, setWalkKey] = useState(0);
  const [shownFor, setShownFor] = useState(selected);
  if (shownFor !== selected) {
    // a new choice: walk there (noticed during render, React's pattern for a changed value)
    setShownFor(selected);
    setWalkKey((k) => k + 1);
  }
  const locked = (id: MapPlaceId) => {
    const mission = missions.find((item) => item.id === id);
    return mission && level < mission.level ? mission.level : null;
  };
  const markers = placeOrder.map((id) => {
    const at = regionPoint(missionPlaces[id]);
    const lv = locked(id);
    return {
      id,
      x: at.x,
      y: at.y,
      label: `${placeName(id)}${lv ? ` · LV ${lv}` : ''}`,
      selected: id === selected,
    };
  });
  return (
    <View style={{ flex: 1, gap: 8 }}>
      <PixelFrame
        style={{ padding: frameInset, flex: 1, minHeight: compact ? 200 : 260 }}
        tone="leaf"
      >
        <View
          onLayout={(event) => {
            const { width: w, height: h } = event.nativeEvent.layout;
            setSize((s) => (Math.abs(s.w - w) < 0.5 && Math.abs(s.h - h) < 0.5 ? s : { w, h }));
          }}
          style={{ flex: 1, overflow: 'hidden', backgroundColor: artMaterials.grass[2] }}
        >
          {size.w > 0 && size.h > 0 && (
            <AtlasWalk
              region="valley"
              width={size.w}
              height={size.h}
              start={regionPoint(missionPlaces[selected])}
              target={{ point: regionPoint(missionPlaces[selected]), key: walkKey }}
              interactive={false}
              markers={markers}
              onMarker={(id) => {
                const place = placeOrder.find((p) => p === id);
                if (place) onSelect(place);
              }}
              maxWalkMs={WALK.max}
              showName={false}
            />
          )}
        </View>
      </PixelFrame>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ gap: 6 }}
      >
        {placeOrder.map((id) => (
          <View key={id} style={{ minWidth: 118 }}>
            <PixelButton
              small
              light={id !== selected}
              label={`${placeName(id)}${locked(id) ? ` · LV ${locked(id)}` : ''}`}
              onPress={() => onSelect(id)}
            />
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

/** Mounted only while the Missions tab is focused, so unfinished drafts expire on leaving. */
export function MissionDeparture() {
  const [selected, setSelected] = useState<MapPlaceId>('park');
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
  if (!player) return null;
  const locked = !!mission && player.level < mission.level;
  const busy = player.mode !== 'awake' || !!battle || pendingReturn || !appActive;
  const route = isRoutePlace(selected) ? routePlaces[selected] : null;
  const go = () => {
    // A stale tap after leaving the tab opens nothing; the screens keep their own guards.
    if (!route || !navigation.isFocused()) return;
    router.push(route.path);
  };
  const start = () => {
    if (!mission) return;
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
            THE VALLEY
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
          {route ? (
            <PixelFrame style={{ gap: 6 }}>
              <BodyText
                accessibilityRole="header"
                style={{ fontSize: 18, fontFamily: 'PixelifySans_700Bold' }}
              >
                {route.title}
              </BodyText>
              <BodyText style={{ fontSize: 13 }}>{route.description}</BodyText>
            </PixelFrame>
          ) : (
            mission && (
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
                <BodyText style={{ fontSize: 13 }}>{placeDescription(selected)}</BodyText>
                <BodyText style={{ fontSize: 13 }}>
                  {mission.reward} Dream Dust · {mission.id === 'mountain' ? 'EPIC' : 'RARE'} card ·
                  postcard
                  {mission.id === 'mountain' ? ' · new hat (or +50 Dream Dust if all owned)' : ''}
                </BodyText>
                <BodyText style={{ fontSize: 12, color: c.shade }}>
                  Returning early keeps common cards, without completion rewards. No need to watch
                  the journey.
                </BodyText>
              </PixelFrame>
            )
          )}
        </ScrollView>
        {/* the actions stay in one fixed block under the scrolling map and card, so none
            is ever covered: walking there and the break idea side by side, then the go */}
        {(selected !== 'garden' || (mission && !route)) && (
          <View style={{ flexDirection: 'row', gap: 8, alignItems: 'stretch' }}>
            {selected !== 'garden' && (
              <View style={{ flex: 1 }}>
                <PixelButton
                  small
                  light
                  label="WALK THERE"
                  disabled={busy}
                  onPress={() => {
                    // walk out of the gate and on to the place yourself (free, grants nothing)
                    if (!navigation.isFocused()) return;
                    useUi.setState({ worldLink: { place: selected } });
                    router.push('/world');
                  }}
                />
              </View>
            )}
            {!route && mission && (
              <View style={{ flex: 1 }}>
                <PixelButton
                  small
                  light
                  label={intention ? `IDEA: ${intention.toUpperCase()}` : 'BREAK IDEA'}
                  disabled={busy}
                  onPress={() => setIdeasOpen(true)}
                />
              </View>
            )}
          </View>
        )}
        {route ? (
          <PixelButton small label={route.action} onPress={go} />
        ) : (
          mission && (
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
          )
        )}
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
