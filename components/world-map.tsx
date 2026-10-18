import { useState } from 'react';
import { Image, PixelRatio, Pressable, ScrollView, View } from 'react-native';
import { BodyText } from '@/components/pixel-feedback';
import { PixelButton } from '@/components/game-ui';
import { FrameShape, PixelFrame, frameTones } from '@/components/pixel-frame';
import { zoneNames } from '@/components/atlas-walk';
import { regionBounds, regionTiles, tileOrigin, type RegionId } from '@/lib/region-walk';
import { regionPoint, travelBy, travelLinks, travelPoints } from '@/lib/world-places';
import { zoneMapTiles } from '@/lib/zone-assets';

/** A zone on the map: 40 x 72 map pixels, one for every 8 zone pixels (map_tiles.py). */
const MAP_W = 40;
const MAP_H = 72;
const FOG = '#D9CBA4';
const FOG_EDGE = '#B8A57C';
const FOREST = '#3E5A3E';

export type MapRegion = { id: RegionId; name: string };

/**
 * The world map (world-atlas.md; Matt, 18 Oct: "an ingame world map where you can
 * discover new places"). Each region is drawn from its zones' paper-map tiles; a zone
 * the companion has walked is inked in, the rest wait under fog with a "?". Regions are
 * listed along the lines that join them, and one you have never reached is a "?" too.
 * Looking at the map changes nothing and grants nothing.
 */
export function WorldMap({
  regions,
  current,
  here,
  visited,
  width,
  height,
  insetTop,
  insetBottom,
  onClose,
}: {
  regions: readonly MapRegion[];
  /** the region the companion is in */
  current: RegionId;
  /** where it stands, in that region's pixels */
  here: { x: number; y: number } | null;
  /** zones it has walked (the save's `world.visited`) */
  visited: readonly string[];
  width: number;
  height: number;
  insetTop: number;
  insetBottom: number;
  onClose: () => void;
}) {
  const [shown, setShown] = useState<RegionId>(current);
  // the room the map has, measured, so it always fits between the header and the key
  const [room, setRoom] = useState({ w: 0, h: 0 });
  const seen = (zone: string) => zone === 'garden' || visited.includes(zone);
  // a region is on the map once the companion has stood in it (the valley always is)
  const known = (r: RegionId) =>
    r === current || r === 'valley' || regionTiles(r).some((t) => visited.includes(t.id));
  const b = regionBounds(shown);
  const tiles = regionTiles(shown);
  // whole device pixels per map pixel, as large as fits beside the header and the lines
  const dpr = PixelRatio.get();
  const fit = Math.min(room.w / (b.tileCols * MAP_W), room.h / (b.tileRows * MAP_H));
  const k = Math.max(1 / dpr, Math.floor(fit * dpr) / dpr);
  const mapW = b.tileCols * MAP_W * k;
  const mapH = b.tileRows * MAP_H * k;
  const pin = shown === current && here ? { x: (here.x / 8) * k, y: (here.y / 8) * k } : null;
  const station = travelPoints[shown];
  const stop = station ? regionPoint(station) : null;
  const lines = travelLinks
    .filter(([a, c]) => a === shown || c === shown)
    .map(([a, c]) => (a === shown ? c : a));
  const nameOf = (r: RegionId) => regions.find((x) => x.id === r)?.name ?? r;
  return (
    <View
      accessibilityViewIsModal
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        width,
        height,
        backgroundColor: 'rgba(30,25,23,0.72)',
        paddingTop: insetTop + 8,
        paddingBottom: insetBottom + 8,
        paddingHorizontal: Math.max(8, (width - 560) / 2),
        zIndex: 5000,
      }}
    >
      <PixelFrame tone="paper" style={{ flex: 1, padding: 12, gap: 10 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <View style={{ flex: 1 }}>
            <BodyText
              accessibilityRole="header"
              style={{ fontFamily: 'PixelifySans_700Bold', fontSize: 18 }}
            >
              MAP · {known(shown) ? nameOf(shown) : '???'}
            </BodyText>
            <BodyText style={{ fontSize: 12, lineHeight: 15 }}>
              Places you have walked are inked in; the rest wait under the fog.
            </BodyText>
          </View>
          <View style={{ width: 96 }}>
            <PixelButton small light label="CLOSE" onPress={onClose} />
          </View>
        </View>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={{ flexGrow: 0 }}
          contentContainerStyle={{ gap: 6 }}
        >
          {regions.map((r) => {
            const open = known(r.id);
            const selected = r.id === shown;
            return (
              <Pressable
                key={r.id}
                accessibilityRole="button"
                accessibilityLabel={
                  open ? `Show ${r.name} on the map` : 'A place you have not found yet'
                }
                accessibilityState={{ selected, disabled: !open }}
                disabled={!open}
                onPress={() => setShown(r.id)}
                style={{ minHeight: 44, paddingHorizontal: 10, justifyContent: 'center' }}
              >
                <FrameShape tone={selected ? frameTones.paper : frameTones.wood} unit={2} />
                <BodyText
                  style={{
                    fontSize: 12,
                    fontFamily: 'PixelifySans_700Bold',
                    opacity: open ? 1 : 0.55,
                  }}
                >
                  {r.id === current ? '● ' : ''}
                  {open ? r.name : '???'}
                </BodyText>
              </Pressable>
            );
          })}
        </ScrollView>
        <View
          onLayout={(e) => {
            const { width: w, height: h } = e.nativeEvent.layout;
            setRoom((r) => (r.w === w && r.h === h ? r : { w, h }));
          }}
          style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}
        >
          {room.w > 0 && (
            <View
              accessibilityLabel={`Map of ${nameOf(shown)}`}
              style={{
                width: mapW,
                height: mapH,
                backgroundColor: shown === 'valley' ? FOREST : '#2A2420',
              }}
            >
              {tiles.map((t) => {
                const o = tileOrigin(shown, t);
                const left = (o.x / 8) * k;
                const top = (o.y / 8) * k;
                const w = MAP_W * k;
                const h = MAP_H * k;
                return seen(t.id) ? (
                  <Image
                    key={t.id}
                    accessibilityLabel={zoneNames[t.id]}
                    source={zoneMapTiles[t.id]}
                    resizeMode="stretch"
                    // @ts-expect-error dataSet is a react-native-web prop (crisp pixel scaling)
                    dataSet={{ pixel: 'true' }}
                    style={{ position: 'absolute', left, top, width: w, height: h }}
                  />
                ) : (
                  <View
                    key={t.id}
                    accessibilityLabel="A place you have not walked yet"
                    style={{
                      position: 'absolute',
                      left,
                      top,
                      width: w,
                      height: h,
                      backgroundColor: FOG,
                      borderWidth: Math.max(1, Math.round(k)),
                      borderColor: FOG_EDGE,
                      borderStyle: 'dashed',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <BodyText
                      style={{ fontSize: 22, color: FOG_EDGE, fontFamily: 'PixelifySans_700Bold' }}
                    >
                      ?
                    </BodyText>
                  </View>
                );
              })}
              {stop && station && seen(station.zone) && (
                <View
                  pointerEvents="none"
                  style={{
                    position: 'absolute',
                    left: (stop.x / 8) * k - 6,
                    top: (stop.y / 8) * k - 6,
                    width: 12,
                    height: 12,
                    backgroundColor: '#3B6FA8',
                    borderWidth: 2,
                    borderColor: '#F4EBD0',
                  }}
                />
              )}
              {pin && (
                <View
                  pointerEvents="none"
                  accessibilityLabel="You are here"
                  style={{
                    position: 'absolute',
                    left: pin.x - 7,
                    top: pin.y - 7,
                    alignItems: 'center',
                  }}
                >
                  <View
                    style={{
                      width: 14,
                      height: 14,
                      backgroundColor: '#C8443A',
                      borderWidth: 2,
                      borderColor: '#F4EBD0',
                    }}
                  />
                </View>
              )}
            </View>
          )}
        </View>
        <View style={{ gap: 4 }}>
          <View style={{ flexDirection: 'row', gap: 12, flexWrap: 'wrap' }}>
            <Legend colour="#C8443A" label="you" />
            {station && (
              <Legend colour="#3B6FA8" label={(travelBy[shown] ?? 'station').toLowerCase()} />
            )}
            <Legend colour={FOG} edge={FOG_EDGE} label="not walked yet" />
          </View>
          {lines.length > 0 && (
            <BodyText style={{ fontSize: 12, lineHeight: 16 }}>
              Lines from here: {lines.map((r) => (known(r) ? nameOf(r) : '???')).join(' · ')}
            </BodyText>
          )}
        </View>
      </PixelFrame>
    </View>
  );
}

function Legend({ colour, edge, label }: { colour: string; edge?: string; label: string }) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
      <View
        style={{
          width: 10,
          height: 10,
          backgroundColor: colour,
          borderWidth: edge ? 1 : 0,
          borderColor: edge,
        }}
      />
      <BodyText style={{ fontSize: 12 }}>{label}</BodyText>
    </View>
  );
}
