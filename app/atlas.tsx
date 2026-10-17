import { useState } from 'react';
import { View, useWindowDimensions } from 'react-native';
import { Stack, router } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { AtlasWalk } from '@/components/atlas-walk';
import { PixelButton } from '@/components/game-ui';
import type { RegionId } from '@/lib/region-walk';

const regionIds: RegionId[] = ['valley', 'steam', 'west', 'lava', 'neon', 'space'];
const regionNames: Record<RegionId, string> = {
  valley: 'VALLEY',
  steam: 'COGSWORTH',
  west: 'DUST GULCH',
  lava: 'CALDERA',
  neon: 'NEON',
  space: 'SPACE',
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
  const bar = 56 + insets.bottom;
  return (
    <View style={{ flex: 1, backgroundColor: '#1E1917' }}>
      <Stack.Screen options={{ headerShown: false }} />
      <AtlasWalk key={region} region={region} width={width} height={height - bar} />
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
              onPress={() => setRegion(r)}
            />
          </View>
        ))}
      </View>
    </View>
  );
}
