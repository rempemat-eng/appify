import { useCallback, useState } from 'react';
import { ScrollView, View, useWindowDimensions } from 'react-native';
import { Stack, router } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { AtlasWalk } from '@/components/atlas-walk';
import { Journey } from '@/components/journey';
import { usePixelUnit } from '@/components/pixel-frame';
import { PixelButton } from '@/components/game-ui';
import type { RegionId } from '@/lib/region-walk';

const BUTTON_W = 88; // wide enough for a region's name and a 44 px touch target
const regionIds: RegionId[] = ['home', 'valley', 'steam', 'west', 'lava', 'neon', 'space', 'moon'];
const regionNames: Record<RegionId, string> = {
  valley: 'VALLEY',
  steam: 'COGSWORTH',
  west: 'DUST GULCH',
  lava: 'CALDERA',
  neon: 'NEON',
  space: 'HALCYON',
  moon: 'LUMEN',
  home: 'HOUSE',
};

/**
 * A preview of the open world (living-world plan W1): walk across the drawn zones
 * with no cuts between them. Not linked from the game yet; it saves nothing and
 * grants nothing. Open it at /atlas.
 */
export default function Atlas() {
  const { width, height } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const [region, setRegion] = useState<RegionId>('valley');
  const [trip, setTrip] = useState<RegionId | null>(null);
  const u = usePixelUnit();
  const arrive = useCallback(() => {
    if (trip) setRegion(trip);
    setTrip(null);
  }, [trip]);
  const bar = 56 + insets.bottom;
  return (
    <View style={{ flex: 1, backgroundColor: '#1E1917' }}>
      <Stack.Screen options={{ headerShown: false }} />
      <View style={{ width, height: height - bar }}>
        <AtlasWalk key={region} region={region} width={width} height={height - bar} />
        {trip && (
          <Journey
            to={trip === 'home' ? 'valley' : trip}
            label={regionNames[trip]}
            width={width}
            height={height - bar}
            u={u}
            onArrive={arrive}
          />
        )}
      </View>
      {/* a scrolling row, so every button keeps a full touch target however many regions */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={{ height: bar, flexGrow: 0 }}
        contentContainerStyle={{
          paddingBottom: insets.bottom,
          paddingHorizontal: 8,
          gap: 6,
          alignItems: 'center',
        }}
      >
        <View style={{ width: BUTTON_W }}>
          <PixelButton small light label="HOME" onPress={() => router.replace('/')} />
        </View>
        {regionIds.map((r) => (
          <View key={r} style={{ width: BUTTON_W }}>
            <PixelButton
              small
              light={r !== region}
              label={regionNames[r]}
              disabled={!!trip}
              onPress={() => {
                if (r === region) return;
                // the house is through the door, not a journey away
                if (r === 'home' || region === 'home') setRegion(r);
                else setTrip(r);
              }}
            />
          </View>
        ))}
      </ScrollView>
    </View>
  );
}
