import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ScrollView, View, useWindowDimensions } from 'react-native';
import { Stack, router, useLocalSearchParams, useNavigation } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeIn } from 'react-native-reanimated';
import { useReducedMotion } from '@/lib/motion';
import { AtlasWalk, zoneNames } from '@/components/atlas-walk';
import { Journey } from '@/components/journey';
import { usePixelUnit, PixelFrame } from '@/components/pixel-frame';
import { PixelButton } from '@/components/game-ui';
import { BodyText } from '@/components/pixel-feedback';
import { feedback, missions, useGame } from '@/lib/game';
import { useAppActive } from '@/lib/app-active';
import { tileAt, type RegionId, type TileId } from '@/lib/region-walk';
import {
  doors,
  exitWalk,
  exits,
  missionPlaces,
  passAt,
  regionPoint,
  stopIds,
  travelPoints,
  travelRoute,
  travelVehicle,
  type ExitId,
  type StopId,
} from '@/lib/world-places';
import { restoreWorld } from '@/lib/world-save';
import { useZoneAmbience } from '@/lib/sound';
import { useUi } from '@/lib/ui';
import { prefetchRegion } from '@/lib/zone-prefetch';
import { WorldMap } from '@/components/world-map';
import { HUT_DOOR, type Point } from '@/lib/garden-path';
import { DecoratePanel } from '@/components/decorate-panel';
import {
  areaOf,
  keepsake,
  newKeepsakes,
  checkDecor,
  decorBox,
  decorFootprint,
  tapToDecorate,
  foundKeepsakes,
  hutWalk,
  keepsakes,
  walkWithDecor,
  type DecorHand,
} from '@/lib/decor';
import { decorImages } from '@/lib/decor-assets';
import { cardAt, placeIds, placeMarkers, type Card } from '@/lib/world-cards';
import { HUB_REGION, hubOpening, toGarden } from '@/lib/home-hub';
import { PlaceCardBody, stopNames } from '@/components/place-card';
import { decorExtras } from '@/components/scene-decor';

const regionNames: Record<RegionId, string> = {
  valley: 'THE VALLEY',
  steam: 'COGSWORTH',
  west: 'SUNSTONE REACH',
  isles: 'TIDEBLOOM ISLES',
  neon: 'NEON HARBOUR',
  space: 'HALCYON STATION',
  moon: 'LUMEN',
  home: 'THE NAP HUT',
};
const travelOrder: RegionId[] = ['valley', 'steam', 'west', 'isles', 'neon', 'space', 'moon'];
const exitIds: ExitId[] = ['gate', 'trail', 'west', 'east'];
const noZones: readonly string[] = [];
const insideDoor = regionPoint(doors.inside);
/** Back to the home hub (the Home tab), standing at `at` (garden pixels) when given. */
function sendHome(focused: boolean, at?: Point) {
  if (!focused) return;
  if (!at) {
    router.replace('/');
    return;
  }
  feedback('select');
  useUi.setState({
    homeArrival: { x: Math.round(at.x), y: Math.round(at.y), key: String(Date.now()) },
  });
  router.replace('/');
}
/** Inside the hut, the front door seen from inside: walking back to it steps out into the
 *  garden (garden pixels), else null. (The valley itself is the home hub's,
 *  docs/vision/home-hub.md: this screen hands it over and never walks it.) */
const doorAt = (region: RegionId, at: Point): Point | null =>
  region === 'home' && Math.hypot(at.x - insideDoor.x, at.y - insideDoor.y) <= 10 ? HUT_DOOR : null;

/**
 * The world beyond the valley (living-world plan W1/W2): the inside of the hut, and the
 * regions the journeys reach (the train, maglev, elevator, shuttle and ferry between
 * their stations). The valley and the garden are the home hub's (the Home tab,
 * docs/vision/home-hub.md): a way in that would open in the valley hands over to it, and
 * a journey back to the valley lands there. Rings open their screen. Walking and
 * travelling are free: they only move the companion and record where it is.
 */
export default function World() {
  const params = useLocalSearchParams<{
    from?: string;
    place?: string;
    station?: string;
    ex?: string;
    ey?: string;
  }>();
  const { width, height } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const u = usePixelUnit();
  const navigation = useNavigation();
  const appActive = useAppActive();
  const player = useGame((s) => s.player);
  const battle = useGame((s) => s.battle);
  const pendingReturn = useGame((s) => s.missionReturnPending);
  const walkWorld = useGame((s) => s.walkWorld);

  // How the game opened the world (lib/ui.ts), read once; a typed address
  // (/world?station=moon) still works for testing.
  const [link] = useState(
    () =>
      useUi.getState().worldLink ?? {
        from: params.from,
        place: params.place,
        station: params.station,
        ex: params.ex ? Number(params.ex) : undefined,
        ey: params.ey ? Number(params.ey) : undefined,
      },
  );
  // A way in that opens in the valley belongs to the home hub: hand it over at once, at
  // that spot (lib/home-hub.ts). Read once, like the link.
  const [handOff] = useState(() => hubOpening(link, restoreWorld(useGame.getState().world)));
  // a journey chosen at a station in the hub: it starts at that station, already under way
  const linkTrip = 'trip' in link ? link.trip : undefined;
  const tripFrom = stopIds.find((r) => r === linkTrip?.from);
  const tripTo = stopIds.find((r) => r === linkTrip?.to);
  useEffect(() => {
    useUi.setState({ worldLink: null });
  }, []);
  // Walked out of the garden screen: the same spot in the valley's garden, walking on
  // out through the gap it left by.
  const exit = exitIds.find((id) => id === link.from);
  const walkOut =
    exit && Number.isFinite(link.ex) && Number.isFinite(link.ey)
      ? exitWalk(exit, Number(link.ex), Number(link.ey))
      : null;
  // Where to begin: a named place, the gate or the trail, or where it last stood.
  const [spawn, setSpawn] = useState<{ region: RegionId; at: Point; key: number }>(() => {
    if (tripFrom) {
      const stop = travelPoints[tripFrom];
      return { region: stop.region, at: regionPoint(stop), key: 0 };
    }
    const place = placeIds.find((id) => id === link.place);
    if (place) return { region: 'valley', at: regionPoint(missionPlaces[place]), key: 0 };
    const station = stopIds.find((r) => r === link.station);
    if (station) {
      const stop = travelPoints[station];
      return { region: stop.region, at: regionPoint(stop), key: 0 };
    }
    if (walkOut) return { region: 'valley', at: walkOut.start, key: 0 };
    if (link.from === 'hut') return { region: 'home', at: regionPoint(doors.inside), key: 0 };
    if (exit) return { region: 'valley', at: regionPoint(exits[exit]), key: 0 };
    const saved = restoreWorld(useGame.getState().world);
    if (saved) return { region: saved.region, at: { x: saved.x, y: saved.y }, key: 0 };
    return { region: 'valley', at: regionPoint(exits.gate), key: 0 };
  });
  const [card, setCard] = useState<Card | null>(() =>
    tripFrom ? null : cardAt(spawn.region, spawn.at),
  );
  const [zone, setZone] = useState<TileId | undefined>(
    () => tileAt(spawn.region, spawn.at.x, spawn.at.y)?.id,
  );
  // a trip is the stations it stops at (the lines in world-places.ts), the destination
  // last, and which leg is playing
  // where the world opened counts as walked (the map inks it in); later walks, journeys
  // and doors record their own steps
  const [opening] = useState(spawn);
  useEffect(() => {
    if (handOff) return;
    walkWorld(opening.region, opening.at.x, opening.at.y, true);
  }, [opening, walkWorld, handOff]);
  const [cardBox, setCardBox] = useState(0);
  const [mapOpen, setMapOpen] = useState(false);
  // Decorating the hut (C12): the keepsakes set out, the one in hand and where it was
  // last tapped. Only inside the hut, and never during a journey.
  const decor = useGame((s) => s.decor);
  const visited = useGame((s) => s.world?.visited ?? noZones);
  const found = useMemo(() => foundKeepsakes(visited), [visited]);
  // A place walked for the first time leaves its keepsake in the chest: say so quietly,
  // under the header, for a few seconds (nothing to press, nothing in the way).
  const [heard, setHeard] = useState(visited);
  const [foundNote, setFoundNote] = useState<string | null>(null);
  if (heard !== visited) {
    setHeard(visited);
    const fresh = visited.filter((z) => !heard.includes(z));
    let had = heard;
    for (const z of fresh) {
      const k = newKeepsakes(had, z).map(keepsake)[0];
      had = [...had, z];
      if (k)
        setFoundNote(`Keepsake found: ${k.name.toLowerCase()}. It waits in the chest at home.`);
    }
  }
  useEffect(() => {
    if (!foundNote) return undefined;
    const t = setTimeout(() => setFoundNote(null), 5000);
    return () => clearTimeout(t);
  }, [foundNote]);
  const [decorating, setDecorating] = useState(
    () => useUi.getState().worldLink?.decorate === true && spawn.region === 'home',
  );
  const [hand, setHand] = useState<DecorHand | null>(null);
  const homeWalk = useMemo(
    () =>
      walkWithDecor(
        hutWalk(),
        decor.filter((p) => areaOf(p) === 'hut'),
      ),
    [decor],
  );
  const homeExtras = useMemo(() => decorExtras(decor.filter((p) => areaOf(p) === 'hut')), [decor]);
  // where the companion stands and which zones it has walked, for the map (only while it is open)
  const worldSpot = useGame((s) => (mapOpen ? s.world : null));
  // a trip: the stop it left from, the stops it calls at (the destination last) and
  // which leg is playing
  const [trip, setTrip] = useState<{ from: StopId; legs: StopId[]; leg: number } | null>(() => {
    if (!tripFrom || !tripTo) return null;
    const legs = travelRoute(tripFrom, tripTo);
    // the places on the way load while the journey plays
    legs.forEach((stop) => prefetchRegion(travelPoints[stop].region));
    return legs.length ? { from: tripFrom, legs, leg: 0 } : null;
  });
  // the place's own sound (Claude B's ambience: the Frostline's wind, the isles' surf,
  // Sunstone's dry air), quiet under a journey or the map; mute, background and first-tap
  // rules ride on the garden's ambience
  useZoneAmbience(appActive && !trip && !mapOpen ? (zone ?? null) : null);
  const dest = trip ? trip.legs[trip.legs.length - 1] : null;
  const reduced = useReducedMotion();
  const [goal, setGoal] = useState<{ point: Point; key: number } | undefined>(() =>
    walkOut && spawn.key === 0 ? { point: walkOut.goal, key: 1 } : undefined,
  );
  // Inside the hut, walking back to the front door steps out into the garden (arriving
  // there waits until the companion has walked away once, or a few steps).
  const outside = useRef(!doorAt(spawn.region, spawn.at));
  // Walking to the end of a pass between regions walks on into the next (the desert
  // into the Ember Lands): the scene fades and the companion carries on. Arriving at a
  // pass waits until it has walked away once, so it never bounces straight back.
  const awayFromPass = useRef(!passAt(spawn.region, spawn.at));
  const throughPass = (at: Point) => {
    const pass = passAt(spawn.region, at);
    if (!pass) {
      awayFromPass.current = true;
      return;
    }
    if (!awayFromPass.current || !navigation.isFocused()) return;
    enter(pass.region, pass.at);
    setGoal((g) => ({ point: pass.goal, key: (g?.key ?? 0) + 1 }));
  };
  const homeward = (at: Point) => {
    const g = doorAt(spawn.region, at);
    if (!g) {
      outside.current = true;
      return;
    }
    if (!outside.current && Math.hypot(at.x - spawn.at.x, at.y - spawn.at.y) < 24) return;
    outside.current = false;
    goHome(g);
  };
  const walkToPlace = (id: string) => {
    const marker = placeMarkers(spawn.region, null).find((m) => m.id === id);
    if (!marker) return;
    feedback('select');
    setGoal((g) => ({ point: { x: marker.x, y: marker.y }, key: (g?.key ?? 0) + 1 }));
  };

  const settle = (at: Point) => {
    walkWorld(spawn.region, at.x, at.y, true);
    // (while decorating, the companion only carries keepsakes about the room)
    if (decorating) return;
    setCard(cardAt(spawn.region, at));
    homeward(at);
    throughPass(at);
  };
  const arrive = useCallback(() => {
    if (!dest) return;
    const station = travelPoints[dest];
    const region = station.region;
    const at = regionPoint(station);
    // back in the valley: the home hub picks up at the station
    if (region === HUB_REGION) {
      setTrip(null);
      sendHome(navigation.isFocused(), toGarden(at));
      return;
    }
    setSpawn((s) => ({ region, at, key: s.key + 1 }));
    setGoal(undefined);
    setZone(tileAt(region, at.x, at.y)?.id);
    outside.current = !doorAt(region, at);
    walkWorld(region, at.x, at.y, true);
    setCard({ kind: 'travel', stop: dest });
    setTrip(null);
  }, [dest, walkWorld, navigation]);
  // the end of one leg: change at that station and go on, or arrive
  const legDone = useCallback(() => {
    if (trip && trip.leg < trip.legs.length - 1) setTrip({ ...trip, leg: trip.leg + 1 });
    else arrive();
  }, [trip, arrive]);

  const away = !player || player.mode !== 'awake' || !!battle || pendingReturn;
  // a station's card lists every line, so it may take up to half the screen; it
  // scrolls when even that is not enough
  const cardH = decorating
    ? Math.min(320, height * 0.46)
    : !card
      ? 0
      : card.kind === 'travel'
        ? Math.min(420, height * 0.5)
        : Math.min(260, height * 0.36);
  const viewH = height;

  const goHome = (at?: Point) => sendHome(navigation.isFocused(), at);
  useEffect(() => {
    if (handOff) sendHome(navigation.isFocused(), handOff);
  }, [handOff, navigation]);
  const enter = (region: RegionId, at: Point) => {
    feedback('select');
    setDecorating(false);
    setHand(null);
    setSpawn((s) => ({ region, at, key: s.key + 1 }));
    setGoal(undefined);
    setZone(tileAt(region, at.x, at.y)?.id);
    outside.current = !doorAt(region, at);
    awayFromPass.current = !passAt(region, at);
    walkWorld(region, at.x, at.y, true);
    setCard(cardAt(region, at));
  };
  const startMission = (id: string) => {
    const mission = missions.find((m) => m.id === id);
    const latest = useGame.getState();
    if (
      !mission ||
      !navigation.isFocused() ||
      !appActive ||
      !latest.player ||
      latest.player.mode !== 'awake' ||
      latest.player.level < mission.level ||
      latest.battle ||
      latest.missionReturnPending
    )
      return;
    latest.sleep(mission.id, null);
    if (useGame.getState().player?.mode === 'mission') router.replace('/');
  };

  // Decorating: a tap on a keepsake in the room takes it in hand; with one in hand, a tap
  // on the floor is where it would go, and the companion carries it there.
  const placeDecor = useGame((s) => s.placeDecor);
  const storeDecor = useGame((s) => s.storeDecor);
  const decorTap = (at: Point): boolean | Point | void => {
    const r = tapToDecorate(decor, 'hut', hand, at);
    if (r.hand?.item !== hand?.item) feedback('select');
    setHand(r.hand);
    return r.walk ?? undefined;
  };
  const handCheck = hand?.at ? checkDecor('hut', decor, hand.item, hand.at.x, hand.at.y) : null;
  const preview = (() => {
    if (!hand?.at) return undefined;
    const b = decorBox(hand.item, hand.at.x, hand.at.y);
    return {
      key: 'preview',
      src: decorImages[hand.item],
      x: b.left,
      y: b.top,
      w: b.w,
      h: b.h,
      z: hand.at.y,
      ok: !!handCheck?.ok,
      foot: decorFootprint(hand.item, hand.at.x, hand.at.y),
    };
  })();

  const cardBody = () => {
    if (!card || !player) return null;
    return (
      <PlaceCardBody
        card={card}
        player={player}
        away={away}
        appActive={appActive}
        travelling={!!trip}
        found={found.length}
        keepsakeCount={keepsakes.length}
        act={{
          startMission,
          openShop: () => navigation.isFocused() && router.push('/shop'),
          openArena: (backdrop) =>
            navigation.isFocused() &&
            router.push(backdrop ? { pathname: '/arena', params: { ring: backdrop } } : '/arena'),
          travel: (here, route) => {
            feedback('select');
            // the places on the way load while the journey plays
            route.forEach((stop) => prefetchRegion(travelPoints[stop].region));
            setTrip({ from: here, legs: route, leg: 0 });
          },
          goHome: () => goHome(),
          goInside: () => enter('home', regionPoint(doors.inside)),
          stepOutside: () => goHome(HUT_DOOR),
          decorate: () => {
            feedback('select');
            setHand(null);
            setDecorating(true);
          },
        }}
      />
    );
  };

  // handing over to the home hub: nothing of the world shows on the way
  if (handOff) return <View style={{ flex: 1, backgroundColor: '#1E1917' }} />;
  return (
    <View style={{ flex: 1, backgroundColor: '#1E1917' }}>
      <Stack.Screen options={{ headerShown: false }} />
      <View style={{ width, height: viewH }}>
        {away ? (
          <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 }}>
            <PixelFrame tone="paper" style={{ padding: 4 * u, gap: 8 }}>
              <BodyText>Your companion is away or resting. The world will wait.</BodyText>
              <PixelButton small label="BACK TO THE GARDEN" onPress={() => goHome()} />
            </PixelFrame>
          </View>
        ) : (
          // each arrival (a journey's end, a door) fades in from the dark (none with reduced motion)
          <Animated.View
            key={`${spawn.region}-${spawn.key}`}
            entering={reduced ? undefined : FadeIn.duration(320)}
            style={{ width, height: viewH }}
          >
            <AtlasWalk
              region={spawn.region}
              start={spawn.at}
              width={width}
              height={viewH}
              onZone={setZone}
              onSettle={settle}
              onMove={(at) => {
                // the zones crossed on the way are walked too (the map inks them in)
                walkWorld(spawn.region, at.x, at.y);
                if (decorating) return;
                homeward(at);
                throughPass(at);
              }}
              // (never under the map or a journey: no walking, held keys included, behind them)
              interactive={!mapOpen && !trip}
              showName={false}
              focusY={card || decorating ? 0.3 : 0.55}
              padBottom={
                card || decorating ? Math.min(cardH, cardBox || cardH) + insets.bottom + 16 : 0
              }
              target={goal}
              markers={decorating ? undefined : placeMarkers(spawn.region, card)}
              onMarker={walkToPlace}
              walk={spawn.region === 'home' ? homeWalk : undefined}
              extras={spawn.region === 'home' ? homeExtras : undefined}
              preview={decorating ? preview : undefined}
              onTap={decorating ? decorTap : undefined}
            />
          </Animated.View>
        )}
        {(card || decorating) && !away && !trip && (
          <View
            // the camera keeps the scene above the card as it is, not as tall as it may grow
            onLayout={(e) => setCardBox(Math.round(e.nativeEvent.layout.height))}
            style={{
              position: 'absolute',
              // full width on a phone; a readable column on a wide screen
              left: Math.max(8, (width - 560) / 2),
              right: Math.max(8, (width - 560) / 2),
              bottom: insets.bottom + 8,
              maxHeight: cardH,
            }}
          >
            <PixelFrame tone="paper" style={{ padding: 4 * u }}>
              <ScrollView style={{ maxHeight: cardH - 8 * u }} contentContainerStyle={{ gap: 6 }}>
                {decorating ? (
                  <DecoratePanel
                    area="hut"
                    onArea={() => {
                      // out to the garden, still decorating
                      setDecorating(false);
                      setHand(null);
                      useUi.setState({ gardenDecorating: true });
                      goHome(HUT_DOOR);
                    }}
                    found={found}
                    placed={decor}
                    selected={hand?.item ?? null}
                    check={handCheck}
                    onSelect={(item) => setHand(item ? { item, at: null } : null)}
                    onPlace={() => {
                      if (!hand?.at) return;
                      if (placeDecor(hand.item, hand.at.x, hand.at.y).ok) {
                        feedback('select');
                        setHand(null);
                      }
                    }}
                    onStore={() => {
                      if (!hand) return;
                      storeDecor(hand.item);
                      feedback('select');
                      setHand(null);
                    }}
                    onDone={() => {
                      setDecorating(false);
                      setHand(null);
                      setCard(null);
                    }}
                  />
                ) : (
                  cardBody()
                )}
              </ScrollView>
            </PixelFrame>
          </View>
        )}
        {trip && dest && (
          <Journey
            key={trip.leg}
            to={trip.legs[trip.leg]}
            label={
              trip.leg < trip.legs.length - 1
                ? `${stopNames[trip.legs[trip.leg]]}, THEN ${stopNames[dest]}`
                : stopNames[dest]
            }
            ms={trip.legs.length > 1 ? 2200 : undefined}
            vehicle={travelVehicle(
              trip.leg === 0 ? trip.from : trip.legs[trip.leg - 1],
              trip.legs[trip.leg],
            )}
            width={width}
            height={viewH}
            u={u}
            onArrive={legDone}
            onSkip={arrive}
            insetTop={insets.top}
            insetBottom={insets.bottom}
          />
        )}
      </View>
      {/* the bar floats over the world like the game's HUD (the journey has its own label) */}
      {!trip && (
        <View
          pointerEvents="box-none"
          style={{
            position: 'absolute',
            top: insets.top + 8,
            left: 8,
            right: 8,
            flexDirection: 'row',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <View style={{ width: 112 }}>
            <PixelButton small light label="◀ GARDEN" onPress={() => goHome()} />
          </View>
          <PixelFrame
            tone="paper"
            style={{
              flex: 1,
              paddingVertical: 2 * u,
              paddingHorizontal: 4 * u,
              minHeight: 44,
              justifyContent: 'center',
            }}
          >
            <BodyText
              numberOfLines={1}
              style={{ fontFamily: 'PixelifySans_700Bold', fontSize: 13 }}
            >
              {regionNames[spawn.region]}
            </BodyText>
            {zone && (
              <BodyText numberOfLines={1} style={{ fontSize: 11, lineHeight: 13 }}>
                {zoneNames[zone]}
              </BodyText>
            )}
          </PixelFrame>
          <View style={{ width: 72 }}>
            <PixelButton small light label="MAP" onPress={() => setMapOpen(true)} />
          </View>
        </View>
      )}
      {foundNote && !trip && !mapOpen && (
        <Animated.View
          entering={reduced ? undefined : FadeIn.duration(240)}
          pointerEvents="none"
          accessibilityLiveRegion="polite"
          style={{
            position: 'absolute',
            top: insets.top + 8 + 52,
            left: Math.max(16, (width - 420) / 2),
            right: Math.max(16, (width - 420) / 2),
            alignItems: 'center',
          }}
        >
          <PixelFrame tone="paper" style={{ paddingVertical: 2 * u, paddingHorizontal: 4 * u }}>
            <BodyText style={{ fontSize: 12, lineHeight: 15, textAlign: 'center' }}>
              {foundNote}
            </BodyText>
          </PixelFrame>
        </Animated.View>
      )}
      {mapOpen && !trip && (
        <WorldMap
          regions={travelOrder.map((id) => ({ id, name: regionNames[id] }))}
          current={spawn.region}
          here={
            worldSpot && worldSpot.region === spawn.region
              ? { x: worldSpot.x, y: worldSpot.y }
              : spawn.at
          }
          visited={worldSpot?.visited ?? noZones}
          width={width}
          height={height}
          insetTop={insets.top}
          insetBottom={insets.bottom}
          onClose={() => setMapOpen(false)}
        />
      )}
    </View>
  );
}
