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
import { worldCatalogue } from '@/lib/world-catalogue';
import {
  regionTiles,
  regionWalk,
  tileAt,
  tileOrigin,
  type RegionId,
  type TileId,
} from '@/lib/region-walk';
import { residentLines, residentRoutes } from '@/lib/resident-routes';
import {
  PLACE_RADIUS,
  doors,
  exitWalk,
  exits,
  inGardenYard,
  missionPlaces,
  keepsakeChest,
  passAt,
  regionPoint,
  rings,
  travelBy,
  travelPoints,
  travelRoute,
  travelVehicle,
  type ExitId,
  type MissionPlaceId,
} from '@/lib/world-places';
import { restoreWorld } from '@/lib/world-save';
import { useUi } from '@/lib/ui';
import { prefetchRegion } from '@/lib/zone-prefetch';
import { WorldMap } from '@/components/world-map';
import { HUT_DOOR, type Point } from '@/lib/garden-path';
import { DecoratePanel } from '@/components/decorate-panel';
import {
  areaOf,
  checkDecor,
  decorBox,
  decorFootprint,
  tapToDecorate,
  foundKeepsakes,
  hutWalk,
  keepsakes,
  walkWithDecor,
  type DecorHand,
  type DecorPlacement,
} from '@/lib/decor';
import { decorImages } from '@/lib/decor-assets';

const regionNames: Record<RegionId, string> = {
  valley: 'THE VALLEY',
  steam: 'COGSWORTH',
  west: 'DUST GULCH',
  lava: 'THE EMBER LANDS',
  neon: 'NEON HARBOUR',
  space: 'HALCYON STATION',
  moon: 'LUMEN',
  home: 'THE NAP HUT',
};
const placeIds: MissionPlaceId[] = ['book', 'park', 'mountain', 'shop', 'arena', 'garden'];
const shortNames: Record<RegionId, string> = {
  valley: 'the valley',
  steam: 'Cogsworth',
  west: 'Dust Gulch',
  lava: 'the Ember Lands',
  neon: 'Neon Harbour',
  space: 'Halcyon',
  moon: 'Lumen',
  home: 'home',
};
const travelOrder: RegionId[] = ['valley', 'steam', 'west', 'lava', 'neon', 'space', 'moon'];
const exitIds: ExitId[] = ['gate', 'trail', 'west', 'east'];
const noZones: readonly string[] = [];
const insideDoor = regionPoint(doors.inside);
/** Where on the garden screen a point counts as home: the garden's yard, or the hut's
 *  front door seen from inside (garden pixels), else null. */
const homeAt = (region: RegionId, at: Point): Point | null =>
  region === 'home'
    ? Math.hypot(at.x - insideDoor.x, at.y - insideDoor.y) <= 10
      ? HUT_DOOR
      : null
    : inGardenYard(region, at);

type Card =
  | { kind: 'mission'; id: 'book' | 'park' | 'mountain' }
  | { kind: 'shop' | 'arena' | 'garden' }
  | { kind: 'travel' }
  | { kind: 'hut' | 'inside' | 'chest' }
  | { kind: 'ring' }
  | { kind: 'chat'; who: string };

/** The places to show by name in a region, so you can see where things are and walk there. */
function placeMarkers(region: RegionId, card: Card | null) {
  const out: { id: string; x: number; y: number; label: string; selected?: boolean }[] = [];
  const add = (id: string, at: Point, label: string, selected = false) =>
    out.push({ id, x: at.x, y: at.y, label, selected });
  const station = travelPoints[region];
  if (station)
    add('travel', regionPoint(station), travelBy[region] ?? 'STATION', card?.kind === 'travel');
  rings
    .filter((r) => r.region === region)
    .forEach((r, i) => add(`ring-${i}`, regionPoint(r), 'SPARRING RING', card?.kind === 'ring'));
  if (region === 'home') {
    add('inside', regionPoint(doors.inside), 'FRONT DOOR', card?.kind === 'inside');
    add('chest', regionPoint(keepsakeChest), 'KEEPSAKE CHEST', card?.kind === 'chest');
  }
  if (region === 'valley') {
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

/** Keepsakes as things standing in a scene (their feet in region pixels). */
function decorExtras(list: readonly DecorPlacement[]) {
  return list.map((p) => {
    const b = decorBox(p.item, p.x, p.y);
    return {
      key: `decor-${p.item}`,
      src: decorImages[p.item],
      x: b.left,
      y: b.top,
      w: b.w,
      h: b.h,
      // a rug lies under everything; the rest stand at their feet
      z: b.flat ? 2 : p.y,
    };
  });
}
const gardenOrigin = (() => {
  const t = regionTiles('valley').find((x) => x.id === 'garden');
  return t ? tileOrigin('valley', t) : { x: 0, y: 0 };
})();

const near = (a: Point, b: Point) => Math.hypot(a.x - b.x, a.y - b.y) <= PLACE_RADIUS * 1.6;

/** What, if anything, happens where the companion stands. */
function cardAt(region: RegionId, at: Point): Card | null {
  if (region === 'home')
    return near(at, regionPoint(doors.inside))
      ? { kind: 'inside' }
      : near(at, regionPoint(keepsakeChest))
        ? { kind: 'chest' }
        : null;
  const station = travelPoints[region];
  if (station && near(at, regionPoint(station))) return { kind: 'travel' };
  if (rings.some((r) => r.region === region && near(at, regionPoint(r)))) return { kind: 'ring' };
  // a resident on their route beside the companion says hello
  for (const [who, route] of Object.entries(residentRoutes)) {
    const tile = regionTiles(region).find((t) => t.id === route.zone);
    if (!tile) continue;
    const o = tileOrigin(region, tile);
    const ax = o.x + route.from[0];
    const ay = o.y + route.from[1];
    const bx = o.x + route.to[0];
    const by = o.y + route.to[1];
    const t = Math.max(
      0,
      Math.min(
        1,
        ((at.x - ax) * (bx - ax) + (at.y - ay) * (by - ay)) /
          Math.max(1, (bx - ax) ** 2 + (by - ay) ** 2),
      ),
    );
    if (Math.hypot(at.x - (ax + (bx - ax) * t), at.y - (ay + (by - ay) * t)) <= 18)
      return { kind: 'chat', who };
  }
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
    const place = placeIds.find((id) => id === link.place);
    if (place) return { region: 'valley', at: regionPoint(missionPlaces[place]), key: 0 };
    const station = travelOrder.find((r) => r === link.station);
    const stop = station ? travelPoints[station] : undefined;
    if (station && stop) return { region: station, at: regionPoint(stop), key: 0 };
    if (walkOut) return { region: 'valley', at: walkOut.start, key: 0 };
    if (link.from === 'hut') return { region: 'home', at: regionPoint(doors.inside), key: 0 };
    if (exit) return { region: 'valley', at: regionPoint(exits[exit]), key: 0 };
    const saved = restoreWorld(useGame.getState().world);
    if (saved) return { region: saved.region, at: { x: saved.x, y: saved.y }, key: 0 };
    return { region: 'valley', at: regionPoint(exits.gate), key: 0 };
  });
  const [card, setCard] = useState<Card | null>(() => cardAt(spawn.region, spawn.at));
  const [zone, setZone] = useState<TileId | undefined>(
    () => tileAt(spawn.region, spawn.at.x, spawn.at.y)?.id,
  );
  // a trip is the stations it stops at (the lines in world-places.ts), the destination
  // last, and which leg is playing
  // where the world opened counts as walked (the map inks it in); later walks, journeys
  // and doors record their own steps
  const [opening] = useState(spawn);
  useEffect(() => {
    walkWorld(opening.region, opening.at.x, opening.at.y, true);
  }, [opening, walkWorld]);
  const [cardBox, setCardBox] = useState(0);
  const [mapOpen, setMapOpen] = useState(false);
  // Decorating the hut (C12): the keepsakes set out, the one in hand and where it was
  // last tapped. Only inside the hut, and never during a journey.
  const decor = useGame((s) => s.decor);
  const visited = useGame((s) => s.world?.visited ?? noZones);
  const found = useMemo(() => foundKeepsakes(visited), [visited]);
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
  // the garden's keepsakes stand in the valley's copy of the garden too
  const valleyDecor = useMemo(
    () =>
      decor
        .filter((p) => areaOf(p) === 'garden')
        .map((p) => ({ ...p, x: p.x + gardenOrigin.x, y: p.y + gardenOrigin.y })),
    [decor],
  );
  const valleyWalk = useMemo(
    () => (valleyDecor.length ? walkWithDecor(regionWalk('valley'), valleyDecor) : undefined),
    [valleyDecor],
  );
  const valleyExtras = useMemo(() => decorExtras(valleyDecor), [valleyDecor]);
  // where the companion stands and which zones it has walked, for the map (only while it is open)
  const worldSpot = useGame((s) => (mapOpen ? s.world : null));
  const [trip, setTrip] = useState<{ legs: RegionId[]; leg: number } | null>(null);
  const dest = trip ? trip.legs[trip.legs.length - 1] : null;
  const reduced = useReducedMotion();
  const [goal, setGoal] = useState<{ point: Point; key: number } | undefined>(() =>
    walkOut && spawn.key === 0 ? { point: walkOut.goal, key: 1 } : undefined,
  );
  // Walking back into the garden's yard from outside it is going home: the garden
  // screen picks up at the same spot. Inside the hut, walking back to the front door
  // steps out into the garden. (Arriving at either, by a door or a journey, waits until
  // the companion has walked away once, or a few steps.)
  const outside = useRef(!homeAt(spawn.region, spawn.at));
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
    const g = homeAt(spawn.region, at);
    if (!g) {
      outside.current = true;
      return;
    }
    // (or having walked a few steps from where it arrived: never left standing in the
    // valley's copy of the garden)
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
    if (station) {
      const at = regionPoint(station);
      setSpawn((s) => ({ region: dest, at, key: s.key + 1 }));
      setGoal(undefined);
      setZone(tileAt(dest, at.x, at.y)?.id);
      outside.current = !homeAt(dest, at);
      walkWorld(dest, at.x, at.y, true);
      setCard({ kind: 'travel' });
    }
    setTrip(null);
  }, [dest, walkWorld]);
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

  // back to the garden screen, standing at `at` (garden pixels) when given
  const goHome = (at?: Point) => {
    if (!navigation.isFocused()) return;
    if (!at) {
      router.replace('/');
      return;
    }
    feedback('select');
    useUi.setState({
      homeArrival: { x: Math.round(at.x), y: Math.round(at.y), key: String(Date.now()) },
    });
    router.replace('/');
  };
  const enter = (region: RegionId, at: Point) => {
    feedback('select');
    setDecorating(false);
    setHand(null);
    setSpawn((s) => ({ region, at, key: s.key + 1 }));
    setGoal(undefined);
    setZone(tileAt(region, at.x, at.y)?.id);
    outside.current = !homeAt(region, at);
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
    if (card.kind === 'chest')
      return (
        <>
          <BodyText style={{ fontSize: 16, fontFamily: 'PixelifySans_700Bold' }}>
            THE KEEPSAKE CHEST
          </BodyText>
          <BodyText style={{ fontSize: 13 }}>
            {found.length} of {keepsakes.length} keepsakes found. Every place you walk leaves one;
            set them out anywhere in the hut, and move them whenever you like.
          </BodyText>
          <PixelButton
            small
            label="DECORATE"
            onPress={() => {
              feedback('select');
              setHand(null);
              setDecorating(true);
            }}
          />
        </>
      );
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
    if (card.kind === 'ring')
      return (
        <>
          <BodyText style={{ fontSize: 16, fontFamily: 'PixelifySans_700Bold' }}>
            SPARRING RING
          </BodyText>
          <BodyText style={{ fontSize: 13 }}>
            The same friendly ring as in town: spar with Doomscroll Dave or get ready for raids.
          </BodyText>
          <PixelButton
            small
            label="TO THE RING"
            onPress={() =>
              navigation.isFocused() &&
              router.push({ pathname: '/arena', params: { ring: spawn.region } })
            }
          />
        </>
      );
    if (card.kind === 'chat')
      return (
        <>
          <BodyText style={{ fontSize: 16, fontFamily: 'PixelifySans_700Bold' }}>
            {card.who.toUpperCase()}
          </BodyText>
          <BodyText style={{ fontSize: 14 }}>
            “{residentLines[card.who] ?? 'hello there.'}”
          </BodyText>
        </>
      );
    if (card.kind === 'garden')
      return (
        <>
          <BodyText style={{ fontSize: 16, fontFamily: 'PixelifySans_700Bold' }}>
            HOME GARDEN
          </BodyText>
          <BodyText style={{ fontSize: 13 }}>
            The meadow, the pond and your companion’s bed.
          </BodyText>
          <PixelButton small label="BACK TO THE GARDEN" onPress={() => goHome()} />
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
          <PixelButton small label="STEP OUTSIDE" onPress={() => goHome(HUT_DOOR)} />
        </>
      );
    // a station: the lines leave from here; further places change on the way
    const routes = travelOrder
      .filter((r) => r !== spawn.region && travelPoints[r])
      .map((r) => ({ r, route: travelRoute(spawn.region, r) }))
      .filter((x) => x.route.length > 0)
      .sort((a, b) => a.route.length - b.route.length);
    const direct = routes.filter((x) => x.route.length === 1);
    const further = routes.filter((x) => x.route.length > 1);
    return (
      <>
        <BodyText style={{ fontSize: 16, fontFamily: 'PixelifySans_700Bold' }}>
          {travelBy[spawn.region] ?? 'THE STATION'}
        </BodyText>
        <BodyText style={{ fontSize: 13 }}>
          Where to? The journey is free; skip it any time.
        </BodyText>
        {[direct, further].map((group, g) =>
          group.length ? (
            <View key={g === 0 ? 'direct' : 'further'} style={{ gap: 4 }}>
              {g === 1 && (
                <BodyText style={{ fontSize: 12 }}>Further, changing on the way:</BodyText>
              )}
              <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
                {group.map(({ r, route }) => (
                  <View key={r} style={{ width: '48%', gap: 2 }}>
                    <PixelButton
                      small
                      light
                      label={regionNames[r]}
                      disabled={away || !!trip}
                      onPress={() => {
                        feedback('select');
                        // the places on the way load while the journey plays
                        route.forEach(prefetchRegion);
                        setTrip({ legs: route, leg: 0 });
                      }}
                    />
                    {route.length > 1 && (
                      <BodyText numberOfLines={1} style={{ fontSize: 11, lineHeight: 13 }}>
                        {route.length === 2
                          ? `via ${shortNames[route[0]]}`
                          : `via ${shortNames[route[0]]} · ${route.length - 1} changes`}
                      </BodyText>
                    )}
                  </View>
                ))}
              </View>
            </View>
          ) : null,
        )}
      </>
    );
  };

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
              walk={
                spawn.region === 'home'
                  ? homeWalk
                  : spawn.region === 'valley'
                    ? valleyWalk
                    : undefined
              }
              extras={
                spawn.region === 'home'
                  ? homeExtras
                  : spawn.region === 'valley'
                    ? valleyExtras
                    : undefined
              }
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
            to={trip.legs[trip.leg] === 'home' ? 'valley' : trip.legs[trip.leg]}
            label={
              trip.leg < trip.legs.length - 1
                ? `${regionNames[trip.legs[trip.leg]]}, THEN ${regionNames[dest]}`
                : regionNames[dest]
            }
            ms={trip.legs.length > 1 ? 2200 : undefined}
            vehicle={travelVehicle(
              trip.leg === 0 ? spawn.region : trip.legs[trip.leg - 1],
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
