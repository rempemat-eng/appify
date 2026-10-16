import { useEffect, useState } from 'react';
import { FlatList, View } from 'react-native';
import { Stack, router, useLocalSearchParams } from 'expo-router';
import { Tabs } from 'heroui-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Rect } from 'react-native-svg';
import { cozy as c, panelStyle } from '@/lib/cozy';
import { CozyBackground } from '@/components/cozy-ui';
import { feedback, startGame, useGame } from '@/lib/game';
import { collectionOf, postcardsOf, visitorHint, visitors } from '@/lib/visitors';
import { visitorPixels } from '@/lib/visitor-art';
import { Pet, PixelButton, PixelText } from '@/components/game-ui';
import { BodyText } from '@/components/pixel-feedback';
import { JournalEmpty, PostcardArt } from '@/components/visitors';
import { goBackOrReplace } from '@/lib/navigation';

const habitTint = {
  REST: { fill: '#EFE9F7', edge: c.nap },
  ROAM: { fill: '#E6F1E1', edge: c.leafOutline },
  FOCUS: { fill: '#F8EEDA', edge: c.goldFrame },
} as const;
const rarityDots = { COMMON: 1, UNCOMMON: 2, RARE: 3 } as const;

export default function FieldJournal() {
  const params = useLocalSearchParams<{ tab?: string }>();
  const [tab, setTab] = useState(params.tab === 'postcards' ? 'postcards' : 'visitors');
  const p = useGame((s) => s.player);
  const insets = useSafeAreaInsets();
  useEffect(() => {
    startGame();
  }, []);
  const collection = p ? collectionOf(p) : [];
  const postcards = p
    ? postcardsOf(p).map((_, index, cards) => cards[cards.length - 1 - index])
    : [];
  return (
    <View
      style={{
        flex: 1,
        backgroundColor: c.paper,
        padding: 12,
        paddingBottom: Math.max(12, insets.bottom),
        gap: 16,
        width: '100%',
        maxWidth: 640,
        alignSelf: 'center',
      }}
    >
      <CozyBackground />
      <Stack.Screen
        options={{
          title: 'FIELD JOURNAL',
          headerStyle: { backgroundColor: c.paper },
          headerTintColor: c.ink,
          headerTitleStyle: { fontFamily: 'Nunito_600SemiBold' },
          contentStyle: { backgroundColor: c.paper },
        }}
      />
      <View style={{ gap: 8 }}>
        <PixelText style={{ fontSize: 18 }}>
          MET {collection.length} / {visitors.length}
        </PixelText>
        <View
          accessibilityRole="progressbar"
          accessibilityValue={{ min: 0, max: visitors.length, now: collection.length }}
          style={{
            height: 10,
            borderRadius: 999,
            borderWidth: 2,
            borderColor: c.outline,
            backgroundColor: c.body,
            overflow: 'hidden',
          }}
        >
          <View
            style={{
              height: '100%',
              width: `${(collection.length / visitors.length) * 100}%`,
              backgroundColor: c.roam,
            }}
          />
        </View>
      </View>
      <Tabs
        value={tab}
        onValueChange={(value) => {
          setTab(value);
          feedback('select');
        }}
      >
        <Tabs.List
          style={{ backgroundColor: c.body, borderRadius: 14, borderWidth: 2, borderColor: c.ink }}
        >
          <Tabs.Indicator style={{ borderRadius: 14, backgroundColor: c.paper }} />
          <Tabs.Trigger value="visitors">
            <Tabs.Label style={{ color: c.ink, fontFamily: 'Nunito_600SemiBold' }}>
              VISITORS
            </Tabs.Label>
          </Tabs.Trigger>
          <Tabs.Trigger value="postcards">
            <Tabs.Label style={{ color: c.ink, fontFamily: 'Nunito_600SemiBold' }}>
              POSTCARDS
            </Tabs.Label>
          </Tabs.Trigger>
        </Tabs.List>
      </Tabs>
      {tab === 'visitors' ? (
        <FlatList
          data={visitors}
          numColumns={3}
          key="visitors"
          keyExtractor={(v) => v.id}
          columnWrapperStyle={{ gap: 6 }}
          contentContainerStyle={{ gap: 10 }}
          renderItem={({ item }) => {
            const met = collection.find((entry) => entry.id === item.id);
            const tint = habitTint[item.habit];
            const dots = rarityDots[item.rarity];
            return (
              <View
                accessibilityLabel={`${item.name}, ${item.habit}, ${item.rarity}, ${met ? `first met after ${met.minutes} offline minutes` : `not met yet, appears on ${visitorHint(item.rarity)}`}`}
                style={{
                  ...panelStyle,
                  flex: 1,
                  alignItems: 'center',
                  paddingVertical: 10,
                  paddingHorizontal: 4,
                  gap: 4,
                  backgroundColor: met ? tint.fill : c.paper,
                  borderColor: met ? tint.edge : c.outline,
                }}
              >
                <View style={{ flexDirection: 'row', gap: 3, alignSelf: 'flex-end' }}>
                  {[0, 1, 2].map((i) => (
                    <View
                      key={i}
                      style={{
                        width: 6,
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: i < dots ? tint.edge : c.faded,
                      }}
                    />
                  ))}
                </View>
                {met ? (
                  <Pet visitor={item.id} size={64} bob={false} />
                ) : (
                  <Svg width={64} height={64} viewBox="0 0 32 32" opacity={0.35}>
                    {visitorPixels(item.id).map((pixel) => (
                      <Rect
                        key={`${pixel.x}-${pixel.y}`}
                        x={pixel.x}
                        y={pixel.y}
                        width={1}
                        height={1}
                        fill={tint.edge}
                      />
                    ))}
                  </Svg>
                )}
                <BodyText
                  numberOfLines={1}
                  style={{ fontFamily: 'Nunito_800ExtraBold', fontSize: 11 }}
                >
                  {item.name}
                </BodyText>
                <BodyText style={{ fontSize: 10, color: tint.edge, fontFamily: 'Nunito_800ExtraBold' }}>
                  {item.habit}
                </BodyText>
                <BodyText numberOfLines={2} style={{ fontSize: 10, textAlign: 'center' }}>
                  {met ? `met after ${met.minutes} MIN` : visitorHint(item.rarity)}
                </BodyText>
              </View>
            );
          }}
        />
      ) : (
        <FlatList
          key="postcards"
          data={postcards}
          keyExtractor={(item) => item.id}
          contentContainerStyle={{ gap: 16, flexGrow: 1 }}
          renderItem={({ item }) => <PostcardArt postcard={item} />}
          ListEmptyComponent={<JournalEmpty onPress={() => router.replace('/missions')} />}
        />
      )}
      <PixelButton label="BACK TO THE GARDEN" light onPress={() => goBackOrReplace('/')} />
    </View>
  );
}
