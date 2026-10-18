import { useCallback, useState } from 'react';
import { ScrollView, View, useWindowDimensions } from 'react-native';
import { Stack, router, useLocalSearchParams, useNavigation } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { AtlasWalk, zoneNames } from '@/components/atlas-walk';
import { Journey } from '@/components/journey';
import { usePixelUnit, PixelFrame } from '@/components/pixel-frame';
import { PixelButton } from '@/components/game-ui';
import { BodyText } from '@/components/pixel-feedback';
import { feedback, missions, useGame } from '@/lib/game';
import { useAppActive } from '@/lib/app-active';
import { worldCatalogue } from '@/lib/world-catalogue';
import { tileAt, type RegionId, type TileId } from '@/lib/region-walk';
import {
  PLACE_RADIUS,
  doors,
  exits,
  missionPlaces,
  regionPoint,
  travelBy,
  travelPoints,
  type MissionPlaceId,
} from '@/lib/world-places';
import { restoreWorld } from '@/lib/world-save';
import type { Point } from '@/lib/garden-path';

const regionNames: Record<RegionId, string> = {
  valley: 'THE VALLEY',
  steam: 'COGSWORTH',
  west: 'DUST GULCH',
  lava: 'THE CALDERA',
  neon: 'NEON HARBOUR',
  space: 'HALCYON STATION',
  moon: 'LUMEN',
  home: 'THE NAP HUT',
};
const placeIds: MissionPlaceId[] = ['book', 'park', 'mountain', 'shop', 'arena', 'garden'];
const travelOrder: RegionId[] = ['valley', 'steam', 'west', 'lava', 'neon', 'space', 'moon'];

type Card =
  | { kind: 'mission'; id: 'book' | 'park' | 'mountain' }
  | { kind: 'shop' | 'arena' | 'garden' }
  | { kind: 'travel' }
  | { kind: 'hut' | 'inside' };

/** The places to show by name in a region, so you can see where things are and walk there. */
function placeMarkers(region: RegionId, card: Card | null) {
  const out: { id: string; x: number; y: number; label: string; selected?: boolean }[] = [];
  const add = (id: string, at: Point, label: string, selected = false) =>
    out.push({ id, x: at.x, y: at.y, label, selected });
  const station = travelPoints[region];
  if (station)
    add('travel', regionPoint(station), travelBy[region] ?? 'STATION', card?.kind === 'travel');
  if (region === 'home')
    add('inside', regionPoint(doors.inside), 'FRONT DOOR', card?.kind === 'inside');
  if (region === 'valley') {
    add('hut', regionPoint(doors.hut), 'THE NAP HUT', card?.kind === 'hut');
    const names: Record<MissionPlaceId, string> = {
      book: 'LIBRARY',
      park: 'PARK',
      mountain: 'MOUNTAIN CABIN',
      shop: "MOSS'S STALL",
      arena: 'SPARRING RING',
      garden: 'HOME GARDEN',
    };
    for (const id of placeIds) {
      const selected = card?.kind === 'mission' ? card.id === id : card?.kind === id;
      add(id, regionPoint(missionPlaces[id]), names[id], selected);
    }
  }
  return out;
}

const near = (a: Point, b: Point) => Math.hypot(a.x - b.x, a.y - b.y) <= PLACE_RADIUS * 1.6;

/** What, if anything, happens where the companion stands. */
function cardAt(region: RegionId, at: Point): Card | null {
  if (region === 'home') return near(at, regionPoint(doors.inside)) ? { kind: 'inside' } : null;
  const station = travelPoints[region];
  if (station && near(at, regionPoint(station))) return { kind: 'travel' };
  if (region !== 'valley') return null;
  if (near(at, regionPoint(doors.hut))) return { kind: 'hut' };
  for (const id of placeIds) {
    if (!near(at, regionPoint(missionPlaces[id]))) continue;
    if (id === 'shop' || id === 'arena' || id === 'garden') return { kind: id };
    return { kind: 'mission', id };
  }
  return null;
}

/**
 * The world beyond the garden (living-world plan W1/W2): walk out of the gate and on
 * through the valley's zones with no cuts between them, take the train, maglev or
 * elevator between regions from each region's station, and step into the hut. Missions
 * set out from their places (the same rules and rewards as the missions map); the
 * stall and the ring open their screens. Walking and travelling are free: they only
 * move the companion and record where it is.
 */
export default function World() {
  const params = useLocalSearchParams<{ from?: string; place?: string; station?: string }>();
  const { width, height } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const u = usePixelUnit();
  const navigation = useNavigation();
  const appActive = useAppActive();
  const player = useGame((s) => s.player);
  const battle = useGame((s) => s.battle);
  const pendingReturn = useGame((s) => s.missionReturnPending);
  const walkWorld = useGame((s) => s.walkWorld);

  // Where to begin: a named place, the gate or the trail, or where it last stood.
  const [spawn, setSpawn] = useState<{ region: RegionId; at: Point; key: number }>(() => {
    const place = placeIds.find((id) => id === params.place);
    if (place) return { region: 'valley', at: regionPoint(missionPlaces[place]), key: 0 };
    const station = travelOrder.find((r) => r === params.station);
    const stop = station ? travelPoints[station] : undefined;
    if (station && stop) return { region: station, at: regionPoint(stop), key: 0 };
    if (params.from === 'trail') return { region: 'valley', at: regionPoint(exits.trail), key: 0 };
    if (params.from === 'gate') return { region: 'valley', at: regionPoint(exits.gate), key: 0 };
    const saved = restoreWorld(useGame.getState().world);
    if (saved) return { region: saved.region, at: { x: saved.x, y: saved.y }, key: 0 };
    return { region: 'valley', at: regionPoint(exits.gate), key: 0 };
  });
  const [card, setCard] = useState<Card | null>(() => cardAt(spawn.region, spawn.at));
  const [zone, setZone] = useState<TileId | undefined>(
    () => tileAt(spawn.region, spawn.at.x, spawn.at.y)?.id,
  );
  const [trip, setTrip] = useState<RegionId | null>(null);
  const [goal, setGoal] = useState<{ point: Point; key: number } | undefined>(undefined);
  const walkToPlace = (id: string) => {
    const marker = placeMarkers(spawn.region, null).find((m) => m.id === id);
    if (!marker) return;
    feedback('select');
    setGoal((g) => ({ point: { x: marker.x, y: marker.y }, key: (g?.key ?? 0) + 1 }));
  };

  const settle = useCallback(
    (at: Point) => {
      walkWorld(spawn.region, at.x, at.y, true);
      setCard(cardAt(spawn.region, at));
    },
    [spawn.region, walkWorld],
  );
  const arrive = useCallback(() => {
    if (!trip) return;
    const station = travelPoints[trip];
    if (station) {
      const at = regionPoint(station);
      setSpawn((s) => ({ region: trip, at, key: s.key + 1 }));
      setGoal(undefined);
      walkWorld(trip, at.x, at.y, true);
      setCard({ kind: 'travel' });
    }
    setTrip(null);
  }, [trip, walkWorld]);

  const away = !player || player.mode !== 'awake' || !!battle || pendingReturn;
  const barH = 52;
  const cardH = card ? Math.min(260, height * 0.36) : 0;
  const viewH = height - insets.top - barH;

  const goHome = () => {
    if (!navigation.isFocused()) return;
    router.replace('/');
  };
  const enter = (region: RegionId, at: Point) => {
    feedback('select');
    setSpawn((s) => ({ region, at, key: s.key + 1 }));
    setGoal(undefined);
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

  const cardBody = () => {
    if (!card || !player) return null;
    if (card.kind === 'mission') {
      const mission = missions.find((m) => m.id === card.id);
      if (!mission) return null;
      const locked = player.level < mission.level;
      return (
        <>
          <BodyText style={{ fontSize: 16, fontFamily: 'PixelifySans_700Bold' }}>
            {mission.name}
          </BodyText>
          <BodyText style={{ fontSize: 13 }}>{worldCatalogue[card.id].description}</BodyText>
          <BodyText style={{ fontSize: 13 }}>
            {mission.duration} MIN · {mission.reward} GRASS ·{' '}
            {mission.id === 'mountain' ? 'EPIC' : 'RARE'} card · postcard
          </BodyText>
          <PixelButton
            small
            label={locked ? `LEVEL ${mission.level} NEEDED` : `START ${mission.name}`}
            disabled={locked || away || !appActive}
            onPress={() => startMission(mission.id)}
          />
        </>
      );
    }
    if (card.kind === 'shop' || card.kind === 'arena') {
      const shop = card.kind === 'shop';
      return (
        <>
          <BodyText style={{ fontSize: 16, fontFamily: 'PixelifySans_700Bold' }}>
            {shop ? "MOSS'S STALL" : 'SPARRING RING'}
          </BodyText>
          <BodyText style={{ fontSize: 13 }}>
            {shop
              ? 'Moss keeps the stall at the crossroads, with everything to grow your garden.'
              : 'A trodden ring by the square. Spar with Doomscroll Dave and get ready for raids.'}
          </BodyText>
          <PixelButton
            small
            label={shop ? "VISIT MOSS'S STALL" : 'TO THE RING'}
            onPress={() => navigation.isFocused() && router.push(shop ? '/shop' : '/arena')}
          />
        </>
      );
    }
    if (card.kind === 'garden')
      return (
        <>
          <BodyText style={{ fontSize: 16, fontFamily: 'PixelifySans_700Bold' }}>
            HOME GARDEN
          </BodyText>
          <BodyText style={{ fontSize: 13 }}>
            The meadow, the pond and your companion’s bed.
          </BodyText>
          <PixelButton small label="BACK TO THE GARDEN" onPress={goHome} />
        </>
      );
    if (card.kind === 'hut')
      return (
        <>
          <BodyText style={{ fontSize: 16, fontFamily: 'PixelifySans_700Bold' }}>
            THE NAP HUT
          </BodyText>
          <PixelButton
            small
            label="GO INSIDE"
            onPress={() => enter('home', regionPoint(doors.inside))}
          />
        </>
      );
    if (card.kind === 'inside')
      return (
        <>
          <BodyText style={{ fontSize: 16, fontFamily: 'PixelifySans_700Bold' }}>
            THE FRONT DOOR
          </BodyText>
          <PixelButton
            small
            label="STEP OUTSIDE"
            onPress={() => enter('valley', regionPoint(doors.hut))}
          />
        </>
      );
    // a station: the journeys to every other region leave from here
    return (
      <>
        <BodyText style={{ fontSize: 16, fontFamily: 'PixelifySans_700Bold' }}>
          {travelBy[spawn.region] ?? 'THE STATION'}
        </BodyText>
        <BodyText style={{ fontSize: 13 }}>
          Where to? The journey is free; skip it any time.
        </BodyText>
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
          {travelOrder
            .filter((r) => r !== spawn.region && travelPoints[r])
            .map((r) => (
              <View key={r} style={{ width: '48%' }}>
                <PixelButton
                  small
                  light
                  label={regionNames[r]}
                  disabled={away || !!trip}
                  onPress={() => {
                    feedback('select');
                    setTrip(r);
                  }}
                />
              </View>
            ))}
        </View>
      </>
    );
  };

  return (
    <View style={{ flex: 1, backgroundColor: '#1E1917', paddingTop: insets.top }}>
      <Stack.Screen options={{ headerShown: false }} />
      <View
        style={{
          height: barH,
          flexDirection: 'row',
          alignItems: 'center',
          gap: 8,
          paddingHorizontal: 8,
        }}
      >
        <View style={{ width: 120 }}>
          <PixelButton small light label="◀ GARDEN" onPress={goHome} />
        </View>
        <BodyText
          numberOfLines={1}
          style={{ flex: 1, color: '#F3E9D2', fontFamily: 'PixelifySans_700Bold', fontSize: 14 }}
        >
          {regionNames[spawn.region]}
          {zone ? ` · ${zoneNames[zone]}` : ''}
        </BodyText>
      </View>
      <View style={{ width, height: viewH }}>
        {away ? (
          <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 }}>
            <PixelFrame tone="paper" style={{ padding: 4 * u, gap: 8 }}>
              <BodyText>Your companion is away or resting. The world will wait.</BodyText>
              <PixelButton small label="BACK TO THE GARDEN" onPress={goHome} />
            </PixelFrame>
          </View>
        ) : (
          <AtlasWalk
            key={`${spawn.region}-${spawn.key}`}
            region={spawn.region}
            start={spawn.at}
            width={width}
            height={viewH}
            onZone={setZone}
            onSettle={settle}
            focusY={card ? 0.3 : 0.55}
            target={goal}
            markers={placeMarkers(spawn.region, card)}
            onMarker={walkToPlace}
          />
        )}
        {card && !away && !trip && (
          <View
            style={{
              position: 'absolute',
              left: 8,
              right: 8,
              bottom: insets.bottom + 8,
              maxHeight: cardH,
            }}
          >
            <PixelFrame tone="paper" style={{ padding: 4 * u }}>
              <ScrollView contentContainerStyle={{ gap: 6 }}>{cardBody()}</ScrollView>
            </PixelFrame>
          </View>
        )}
        {trip && (
          <Journey
            to={trip === 'home' ? 'valley' : trip}
            label={regionNames[trip]}
            width={width}
            height={viewH}
            u={u}
            onArrive={arrive}
          />
        )}
      </View>
    </View>
  );
}
