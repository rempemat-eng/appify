import { useCallback, useState } from 'react';
import { View, useWindowDimensions } from 'react-native';
import { Stack, router } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { AtlasWalk } from '@/components/atlas-walk';
import { Journey } from '@/components/journey';
import { usePixelUnit } from '@/components/pixel-frame';
import { PixelButton } from '@/components/game-ui';
import type { RegionId } from '@/lib/region-walk';

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
// Lumen is reached by shuttle from Halcyon: the same climb out of the atmosphere
const journeyFor = (r: RegionId) => (r === 'moon' ? 'space' : r);

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
            to={journeyFor(trip)}
            label={regionNames[trip]}
            width={width}
            height={height - bar}
            u={u}
            onArrive={arrive}
          />
        )}
      </View>
      <View
        style={{
          height: bar,
          paddingBottom: insets.bottom,
          paddingHorizontal: 8,
          flexDirection: 'row',
          gap: 6,
          alignItems: 'center',
        }}
      >
        <View style={{ flex: 1 }}>
          <PixelButton small light label="HOME" onPress={() => router.replace('/')} />
        </View>
        {regionIds.map((r) => (
          <View key={r} style={{ flex: 1 }}>
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
      </View>
    </View>
  );
}
