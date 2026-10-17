import { useEffect, useState } from 'react';
import { FlatList, ScrollView, View, useWindowDimensions } from 'react-native';
import { Stack, router, useLocalSearchParams } from 'expo-router';
import { Tabs } from 'heroui-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Rect } from 'react-native-svg';
import { Check, Eye } from 'lucide-react-native';
import { cozy as c, panelStyle } from '@/lib/cozy';
import { gameLayout } from '@/lib/layout';
import { CozyBackground, CozyPanel } from '@/components/cozy-ui';
import { feedback, startGame, useGame } from '@/lib/game';
import { collectionOf, postcardsOf, visitorHint, visitors } from '@/lib/visitors';
import { visitorPixels } from '@/lib/visitor-art';
import { Pet, PixelButton, PixelText } from '@/components/game-ui';
import { BodyText } from '@/components/pixel-feedback';
import { JournalEmpty, PostcardArt } from '@/components/visitors';
import { goBackOrReplace } from '@/lib/navigation';
import { CompanionMemories, MemoryReflection } from '@/components/companion-memories';

const habitTint = {
  REST: { fill: '#EFE9F7', edge: c.nap },
  ROAM: { fill: '#E6F1E1', edge: c.leafOutline },
  FOCUS: { fill: '#F8EEDA', edge: c.goldFrame },
} as const;
const rarityDots = { COMMON: 1, UNCOMMON: 2, RARE: 3 } as const;

export default function FieldJournal() {
  const params = useLocalSearchParams<{ tab?: string }>();
  const requestedTab =
    params.tab === 'postcards' ? 'postcards' : params.tab === 'memories' ? 'memories' : 'visitors';
  const [selection, setSelection] = useState({ request: requestedTab, tab: requestedTab });
  if (selection.request !== requestedTab)
    setSelection({ request: requestedTab, tab: requestedTab });
  const tab = selection.request === requestedTab ? selection.tab : requestedTab;
  const [guideOpen, setGuideOpen] = useState(false);
  const p = useGame((s) => s.player);
  const memories = useGame((s) => s.companionMemories);
  const pendingMemories = useGame((s) => s.pendingMemories);
  const [keptMessage, setKeptMessage] = useState<string | null>(null);
  const [memoryPage, setMemoryPage] = useState(0);
  const memoryPages = Math.max(1, Math.ceil(memories.length / 5));
  const visibleMemoryPage = Math.min(memoryPage, memoryPages - 1);
  const pageMemories = [...memories]
    .sort((a, b) => b.completedAt - a.completedAt || b.recordedAt - a.recordedAt)
    .slice(visibleMemoryPage * 5, visibleMemoryPage * 5 + 5);
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  useEffect(() => {
    startGame();
  }, []);
  const collection = p ? collectionOf(p) : [];
  const metCount = visitors.filter((visitor) =>
    collection.some((entry) => entry.id === visitor.id),
  ).length;
  const friendCount = visitors.filter((visitor) =>
    collection.some((entry) => entry.id === visitor.id && entry.befriendedAt !== null),
  ).length;
  const columns = width < 440 ? 2 : 3;
  const postcards = p
    ? postcardsOf(p).map((_, index, cards) => cards[cards.length - 1 - index])
    : [];
  return (
    <View
      style={{
        flex: 1,
        backgroundColor: c.paper,
        padding: gameLayout.gutter,
        paddingBottom: Math.max(gameLayout.gutter, insets.bottom),
        gap: 12,
        width: '100%',
        maxWidth: gameLayout.maxWidth,
        alignSelf: 'center',
      }}
    >
      <CozyBackground />
      <Stack.Screen
        options={{
          title: 'FIELD JOURNAL',
          headerStyle: { backgroundColor: c.paper },
          headerTintColor: c.ink,
          headerTitleStyle: { fontFamily: 'PixelifySans_500Medium' },
          contentStyle: { backgroundColor: c.paper },
        }}
      />
      <View style={{ gap: 8 }}>
        <PixelText style={{ fontSize: 16, lineHeight: 25 }}>
          {tab === 'memories'
            ? `MEMORIES ${memories.length}`
            : `FRIENDS ${friendCount} / ${visitors.length}`}
        </PixelText>
        <BodyText style={{ fontSize: 12 }}>
          {tab === 'memories'
            ? 'Small moments you chose to keep with your companions.'
            : `${metCount} of ${visitors.length} met · befriend visitors to choose them as guardians`}
        </BodyText>
        {tab !== 'memories' && (
          <View
            accessibilityRole="progressbar"
            accessibilityLabel="Befriended visitors"
            accessibilityValue={{ min: 0, max: visitors.length, now: friendCount }}
            style={{
              height: 10,
              borderRadius: 0,
              borderWidth: 2,
              borderColor: c.outline,
              backgroundColor: c.body,
              overflow: 'hidden',
            }}
          >
            <View
              style={{
                height: '100%',
                width: `${(friendCount / visitors.length) * 100}%`,
                backgroundColor: c.roam,
              }}
            />
          </View>
        )}
      </View>
      <Tabs
        value={tab}
        onValueChange={(value) => {
          setSelection({ request: requestedTab, tab: value });
          feedback('select');
        }}
      >
        <Tabs.List
          style={{ backgroundColor: c.body, borderRadius: 0, borderWidth: 2, borderColor: c.ink }}
        >
          <Tabs.Indicator style={{ borderRadius: 0, backgroundColor: c.paper }} />
          <Tabs.Trigger value="visitors">
            <Tabs.Label style={{ color: c.ink, fontFamily: 'PixelifySans_500Medium' }}>
              VISITORS
            </Tabs.Label>
          </Tabs.Trigger>
          <Tabs.Trigger value="postcards">
            <Tabs.Label style={{ color: c.ink, fontFamily: 'PixelifySans_500Medium' }}>
              POSTCARDS
            </Tabs.Label>
          </Tabs.Trigger>
          <Tabs.Trigger value="memories">
            <Tabs.Label style={{ color: c.ink, fontFamily: 'PixelifySans_500Medium' }}>
              MEMORIES
            </Tabs.Label>
          </Tabs.Trigger>
        </Tabs.List>
      </Tabs>
      {tab === 'visitors' ? (
        <FlatList
          data={visitors}
          numColumns={columns}
          key={`visitors-${columns}`}
          keyExtractor={(v) => v.id}
          columnWrapperStyle={{ gap: 10 }}
          contentContainerStyle={{ gap: 10, paddingBottom: 6 }}
          ListFooterComponent={
            <CozyPanel style={{ padding: 12, gap: 7, marginTop: 2 }}>
              <BodyText style={{ fontFamily: 'PixelifySans_700Bold' }}>
                From visitor to friend
              </BodyText>
              <BodyText style={{ fontSize: 12, lineHeight: 18 }}>
                Tap BEFRIEND in the welcome-back recap, or tap the visitor in your garden before
                they leave. It is free. Meeting a visitor records them here; befriending lets you
                choose them as your guardian in the garden.
              </BodyText>
              <PixelButton
                small
                light
                label={guideOpen ? 'HIDE VISITOR GUIDE' : 'HOW VISITORS WORK'}
                onPress={() => setGuideOpen((value) => !value)}
              />
              {guideOpen && (
                <>
                  <BodyText style={{ fontSize: 12, lineHeight: 18 }}>
                    Your first visitor is guaranteed after 10 simulated MIN (10 seconds in this
                    demo). Later visits are a chance, not a guarantee. Rarity: 1 dot common · 2
                    uncommon · 3 rare.
                  </BodyText>
                  <BodyText style={{ fontSize: 12, lineHeight: 18 }}>
                    Demo time: 1 real second = 1 simulated MIN. Garden visitors stay for 10
                    simulated MIN (10 real seconds) after you close the recap. Phone use and sleep
                    are not measured.
                  </BodyText>
                </>
              )}
            </CozyPanel>
          }
          renderItem={({ item }) => {
            const met = collection.find((entry) => entry.id === item.id);
            const friend = collection.some(
              (entry) => entry.id === item.id && entry.befriendedAt !== null,
            );
            const state = friend ? 'FRIEND' : met ? 'MET' : 'UNSEEN';
            const tint = habitTint[item.habit];
            const dots = rarityDots[item.rarity];
            return (
              <View
                accessible
                accessibilityLabel={`${item.name}, ${item.habit}, ${item.rarity}. ${friend ? 'Befriended; available as a guardian in your garden.' : met ? 'Met, not befriended. Befriend this visitor while they are visiting your garden.' : `Unseen; may appear on ${visitorHint(item.rarity)}.`}${met ? ` First met after ${met.minutes} simulated offline minutes.` : ''}`}
                style={{
                  ...panelStyle,
                  flex: 1,
                  alignItems: 'center',
                  padding: 10,
                  gap: 7,
                  backgroundColor: met ? tint.fill : c.paper,
                  borderColor: met ? tint.edge : c.outline,
                }}
              >
                <View
                  accessibilityElementsHidden
                  importantForAccessibility="no-hide-descendants"
                  style={{ flexDirection: 'row', gap: 3, alignSelf: 'flex-end' }}
                >
                  {[0, 1, 2].map((i) => (
                    <View
                      key={i}
                      style={{
                        width: 6,
                        height: 6,
                        borderRadius: 0,
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
                  style={{ fontFamily: 'PixelifySans_700Bold', fontSize: 12, textAlign: 'center' }}
                >
                  {item.name}
                </BodyText>
                <BodyText
                  style={{ fontSize: 11, color: tint.edge, fontFamily: 'PixelifySans_700Bold' }}
                >
                  {item.habit}
                </BodyText>
                <View
                  style={{
                    minHeight: 25,
                    borderRadius: 0,
                    paddingHorizontal: 8,
                    paddingVertical: 3,
                    flexDirection: 'row',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 4,
                    backgroundColor: friend ? c.sage : met ? '#F4E5C8' : c.body,
                  }}
                >
                  {friend ? (
                    <Check size={12} color={c.ink} />
                  ) : met ? (
                    <Eye size={12} color={c.ink} />
                  ) : null}
                  <BodyText style={{ fontSize: 11, fontFamily: 'PixelifySans_700Bold' }}>
                    {state}
                  </BodyText>
                </View>
                <BodyText
                  style={{ fontSize: 11, lineHeight: 16, textAlign: 'center', minHeight: 32 }}
                >
                  {friend
                    ? 'Ready to guard'
                    : met
                      ? 'Befriend on a visit'
                      : visitorHint(item.rarity)}
                </BodyText>
              </View>
            );
          }}
        />
      ) : tab === 'postcards' ? (
        <FlatList
          key="postcards"
          data={postcards}
          keyExtractor={(item) => item.id}
          contentContainerStyle={{ gap: 16, flexGrow: 1 }}
          renderItem={({ item }) => <PostcardArt postcard={item} />}
          ListEmptyComponent={<JournalEmpty onPress={() => router.replace('/missions')} />}
        />
      ) : (
        <ScrollView contentContainerStyle={{ gap: 14, paddingBottom: 12 }}>
          {pendingMemories.map((offer) => (
            <MemoryReflection
              key={offer.id}
              offer={offer}
              onKeep={() => {
                useGame.getState().recordCompanionMemory(offer.id);
                if (useGame.getState().companionMemories.some((memory) => memory.id === offer.id)) {
                  setKeptMessage(`A memory with ${offer.companion.name} is saved.`);
                  setMemoryPage(0);
                }
              }}
              onSkip={() => useGame.getState().dismissCompanionMemory(offer.id)}
            />
          ))}
          {keptMessage && (
            <BodyText accessibilityLiveRegion="polite" style={{ fontSize: 12 }}>
              {keptMessage}
            </BodyText>
          )}
          <CompanionMemories memories={pageMemories} limit={5} />
          {memoryPages > 1 && (
            <View style={{ gap: 8 }}>
              <BodyText
                accessibilityLiveRegion="polite"
                style={{ fontSize: 12, textAlign: 'center' }}
              >
                Page {visibleMemoryPage + 1} of {memoryPages} · {memories.length} memories
              </BodyText>
              <View style={{ flexDirection: 'row', gap: 10 }}>
                <View style={{ flex: 1 }}>
                  <PixelButton
                    small
                    light
                    label="NEWER"
                    disabled={visibleMemoryPage === 0}
                    onPress={() => setMemoryPage(visibleMemoryPage - 1)}
                  />
                </View>
                <View style={{ flex: 1 }}>
                  <PixelButton
                    small
                    light
                    label="OLDER"
                    disabled={visibleMemoryPage === memoryPages - 1}
                    onPress={() => setMemoryPage(visibleMemoryPage + 1)}
                  />
                </View>
              </View>
            </View>
          )}
          <PixelButton
            small
            light
            label="PLAN ANOTHER BREAK"
            onPress={() => router.replace('/missions')}
          />
        </ScrollView>
      )}
      <PixelButton label="BACK TO THE GARDEN" light onPress={() => goBackOrReplace('/')} />
    </View>
  );
}
