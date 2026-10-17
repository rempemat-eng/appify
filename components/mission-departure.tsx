import { useEffect, useRef, useState } from 'react';
import {
  Image,
  Modal,
  PixelRatio,
  Pressable,
  ScrollView,
  View,
  useWindowDimensions,
} from 'react-native';
import { router, useNavigation } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, {
  Easing,
  useAnimatedStyle,
  useSharedValue,
  withSequence,
  withTiming,
} from 'react-native-reanimated';
import { missions, feedback, useGame, type Player } from '@/lib/game';
import { useAppActive } from '@/lib/app-active';
import { useReducedMotion } from '@/lib/motion';
import { artMaterials } from '@/lib/art-direction';
import { cozy as c } from '@/lib/cozy';
import { gameColumn, gameLayout, hotbarClearance, hudClearance } from '@/lib/layout';
import { worldCatalogue } from '@/lib/world-catalogue';
import { missionMap, missionMapCross, missionMapImage, missionMapPlaces } from '@/lib/mission-map';
import { type BreakIntention } from '@/lib/companion-memories';
import { BreakIntentionPicker } from '@/components/companion-memories';
import { CozyBackground, CozySheet } from '@/components/cozy-ui';
import { BodyText } from '@/components/pixel-feedback';
import { PixelButton } from '@/components/game-ui';
import { GuardianPet } from '@/components/guardian-pet';
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

/** Where the camera looks for a place: its landmark and the spot in front of it. */
function focusOf(id: MapPlaceId) {
  const { tap, stand } = missionMapPlaces[id];
  return { x: tap.x + tap.w / 2, y: (tap.y + tap.h / 2 + stand.y) / 2 };
}

const clamp = (value: number, low: number, high: number) => Math.min(high, Math.max(low, value));

/** The map's offset that centres a place in the window, kept inside the map. */
function cameraFor(id: MapPlaceId, viewWidth: number, viewHeight: number, u: number) {
  const focus = focusOf(id);
  const mapWidth = missionMap.width * u;
  const mapHeight = missionMap.height * u;
  return {
    x: Math.round(clamp(viewWidth / 2 - focus.x * u, Math.min(0, viewWidth - mapWidth), 0)),
    y: Math.round(clamp(viewHeight / 2 - focus.y * u, Math.min(0, viewHeight - mapHeight), 0)),
  };
}

// The tallest the map window grows (CSS px), on short and on tall screens.
const MAP_VIEW = { compact: 260, tall: 380 };

/**
 * The map's pixel size: the shared grid unit, stepped down by whole device
 * pixels while more than a sixth of the map would sit outside the window, so
 * every place stays in view or close to it. Pure, so it can be tested.
 */
export function mapUnitFor(shared: number, dpr: number, viewWidth: number, maxHeight: number) {
  const ratio = dpr > 0 ? dpr : 1;
  let device = Math.max(1, Math.round(shared * ratio));
  const tooBig = (d: number) =>
    (missionMap.width * d) / ratio > viewWidth * 1.2 ||
    (missionMap.height * d) / ratio > maxHeight * 1.2;
  while (device > 1 && tooBig(device)) device--;
  return device / ratio;
}

const walkStep = (to: number, duration: number) =>
  withTiming(to, { duration, easing: Easing.linear });

/**
 * The land beyond the garden gate (living-world plan, L1): one generated still
 * map (scripts/art/mission_map.py) on the shared pixel grid, with a tap area and
 * name tag per place. The companion walks to the chosen place through the
 * crossroads; walking is presentation only and never starts or opens anything.
 */
export function MissionDestinationMap({
  selected,
  level,
  compact,
  player,
  onSelect,
}: {
  selected: MapPlaceId;
  level: number;
  compact: boolean;
  player?: Player;
  onSelect: (place: MapPlaceId) => void;
}) {
  const { width: windowWidth } = useWindowDimensions();
  const shared = usePixelUnit();
  const reduced = useReducedMotion();
  const frameInset = 4 * shared;
  const [viewWidth, setViewWidth] = useState(
    Math.min(windowWidth, gameLayout.maxWidth) - 2 * gameLayout.gutter - 2 * frameInset,
  );
  const maxHeight = compact ? MAP_VIEW.compact : MAP_VIEW.tall;
  const u = mapUnitFor(shared, PixelRatio.get(), viewWidth, maxHeight);
  const mapWidth = missionMap.width * u;
  const mapHeight = missionMap.height * u;
  const viewHeight = Math.min(mapHeight, maxHeight);
  const start = cameraFor(selected, viewWidth, viewHeight, u);
  const camX = useSharedValue<number>(start.x);
  const camY = useSharedValue<number>(start.y);
  const petX = useSharedValue<number>(missionMapPlaces[selected].stand.x);
  const petY = useSharedValue<number>(missionMapPlaces[selected].stand.y);
  const [walk, setWalk] = useState<{ facing: 'left' | 'right'; walking: boolean }>({
    facing: 'right',
    walking: false,
  });
  const from = useRef(selected);
  useEffect(() => {
    const previous = from.current;
    from.current = selected;
    const target = cameraFor(selected, viewWidth, viewHeight, u);
    const a = missionMapPlaces[previous].stand;
    const b = missionMapPlaces[selected].stand;
    let done: ReturnType<typeof setTimeout> | undefined;
    if (previous === selected || reduced) {
      // First frame, a resize or reduced motion: frame the place at once.
      camX.set(target.x);
      camY.set(target.y);
      petX.set(b.x);
      petY.set(b.y);
      done = setTimeout(() => setWalk((w) => (w.walking ? { ...w, walking: false } : w)), 0);
    } else {
      // Two legs along the roads: to the crossroads, then on to the place. A new
      // choice mid-walk starts from wherever the companion is.
      const first = Math.hypot(missionMapCross.x - a.x, missionMapCross.y - a.y);
      const second = Math.hypot(b.x - missionMapCross.x, b.y - missionMapCross.y);
      const total = clamp((first + second) * WALK.msPerPixel, WALK.min, WALK.max);
      const t1 = Math.round((total * first) / Math.max(1, first + second));
      const t2 = total - t1;
      petX.set(withSequence(walkStep(missionMapCross.x, t1), walkStep(b.x, t2)));
      petY.set(withSequence(walkStep(missionMapCross.y, t1), walkStep(b.y, t2)));
      const settle = { duration: total, easing: Easing.inOut(Easing.cubic) };
      camX.set(withTiming(target.x, settle));
      camY.set(withTiming(target.y, settle));
      done = setTimeout(() => setWalk((w) => ({ ...w, walking: false })), total);
      setWalk({ facing: b.x < a.x ? 'left' : 'right', walking: true });
    }
    return () => clearTimeout(done);
  }, [selected, reduced, viewWidth, viewHeight, u, camX, camY, petX, petY]);
  const petSize = 32 * u;
  const cameraStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: camX.value }, { translateY: camY.value }],
  }));
  const petStyle = useAnimatedStyle(() => ({
    transform: [
      { translateX: Math.round(petX.value) * u - petSize / 2 },
      { translateY: Math.round(petY.value) * u - petSize * (30 / 32) },
    ],
  }));
  return (
    <PixelFrame style={{ padding: frameInset }} tone="leaf">
      <View
        onLayout={(event) => {
          const measured = event.nativeEvent.layout.width;
          setViewWidth((w) => (Math.abs(w - measured) < 0.5 ? w : measured));
        }}
        // @ts-expect-error dataSet is a react-native-web prop (shared crisp-art CSS)
        dataSet={{ pixel: 'true' }}
        style={{ height: viewHeight, overflow: 'hidden', backgroundColor: artMaterials.grass[2] }}
      >
        <Animated.View
          style={[
            { position: 'absolute', left: 0, top: 0, width: mapWidth, height: mapHeight },
            cameraStyle,
          ]}
        >
          <Image
            accessible={false}
            source={missionMapImage}
            resizeMode="stretch"
            style={{ position: 'absolute', left: 0, top: 0, width: mapWidth, height: mapHeight }}
          />
          {player && (
            <Animated.View
              pointerEvents="none"
              style={[
                {
                  position: 'absolute',
                  left: 0,
                  top: 0,
                  width: petSize,
                  height: petSize,
                  zIndex: 2,
                },
                petStyle,
              ]}
            >
              <GuardianPet
                player={player}
                size={petSize}
                facing={walk.facing}
                walking={walk.walking && !reduced}
                bob={false}
                active={walk.walking && !reduced}
                decorative
              />
            </Animated.View>
          )}
          {placeOrder.map((id) => {
            const place = missionMapPlaces[id];
            const mission = missions.find((item) => item.id === id);
            const locked = !!mission && level < mission.level;
            return (
              <Pressable
                key={id}
                accessibilityRole="button"
                accessibilityLabel={`${placeName(id)}${locked && mission ? `, level ${mission.level} needed` : ''}`}
                accessibilityState={{ selected: id === selected }}
                aria-pressed={id === selected}
                onPress={() => onSelect(id)}
                style={{
                  position: 'absolute',
                  left: place.tap.x * u,
                  top: place.tap.y * u,
                  width: place.tap.w * u,
                  height: place.tap.h * u,
                  zIndex: 1,
                }}
              />
            );
          })}
          {/* Name tags sit above the companion, so a tag is never hidden by it. */}
          <View
            pointerEvents="none"
            aria-hidden
            accessibilityElementsHidden
            importantForAccessibility="no-hide-descendants"
            style={{ position: 'absolute', left: 0, top: 0, zIndex: 3 }}
          >
            {placeOrder.map((id) => {
              const place = missionMapPlaces[id];
              const mission = missions.find((item) => item.id === id);
              const locked = !!mission && level < mission.level;
              return (
                <View
                  key={id}
                  style={{
                    position: 'absolute',
                    left: place.label.x * u - 60,
                    top: place.label.y * u,
                    width: 120,
                    alignItems: 'center',
                  }}
                >
                  <PixelFrame
                    unit={shared}
                    tone={id === selected ? 'gold' : 'paper'}
                    style={{
                      paddingVertical: 2 * shared,
                      paddingHorizontal: 4 * shared,
                      alignItems: 'center',
                    }}
                  >
                    <BodyText
                      style={{ fontSize: 11, lineHeight: 13, fontFamily: 'PixelifySans_700Bold' }}
                    >
                      {placeName(id)}
                      {locked ? ` · LV ${mission.level}` : ''}
                    </BodyText>
                  </PixelFrame>
                </View>
              );
            })}
          </View>
        </Animated.View>
      </View>
    </PixelFrame>
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
            BEYOND THE GARDEN GATE
          </BodyText>
          <MissionDestinationMap
            selected={selected}
            level={player.level}
            compact={compact}
            player={player}
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
                  {mission.reward} GRASS · {mission.id === 'mountain' ? 'EPIC' : 'RARE'} card ·
                  postcard
                  {mission.id === 'mountain' ? ' · new hat (or +50 GRASS if all owned)' : ''}
                </BodyText>
                <BodyText style={{ fontSize: 12, color: c.shade }}>
                  Returning early keeps common cards, without completion rewards. No need to watch
                  the journey.
                </BodyText>
              </PixelFrame>
            )
          )}
        </ScrollView>
        {route ? (
          <PixelButton small label={route.action} onPress={go} />
        ) : (
          mission && (
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
