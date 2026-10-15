import { router } from 'expo-router';
import { FlatList, ScrollView, View } from 'react-native';
import Animated, { FadeIn, FadeOut } from 'react-native-reanimated';
import Svg, { Rect } from 'react-native-svg';
import { BookOpen } from 'lucide-react-native';
import { palette as c, useGame, type Player } from '@/lib/game';
import { collectionOf, visitorInfo, type Postcard } from '@/lib/visitors';
import { Pet, PixelButton, PixelText } from '@/components/game-ui';
import { BodyText } from '@/components/pixel-feedback';
import { RewardCard } from '@/components/habit-cards';

export function GardenVisitor() {
  const waiting = useGame((s) => s.waitingVisitor);
  const now = useGame((s) => s.now);
  if (!waiting) return null;
  const v = visitorInfo(waiting.id);
  return (
    <Animated.View
      entering={FadeIn}
      exiting={FadeOut}
      style={{
        position: 'absolute',
        right: 4,
        bottom: 52,
        alignItems: 'center',
        backgroundColor: c.paper,
        borderWidth: 2,
        borderColor: c.ink,
        padding: 3,
      }}
    >
      <Pet
        visitor={v.id}
        size={64}
        bob={false}
        onPress={() => useGame.getState().befriendVisitor()}
        actionLabel={`Befriend ${v.name}, free`}
      />
      <PixelText style={{ fontSize: 11 }}>BEFRIEND</PixelText>
      <BodyText style={{ fontSize: 11 }}>
        {waiting.expiresAt ? Math.max(0, Math.ceil((waiting.expiresAt - now) / 1000)) : 10} MIN
      </BodyText>
    </Animated.View>
  );
}
export function GuardianPicker({ player }: { player: Player }) {
  const friends = collectionOf(player).filter((v) => v.befriendedAt !== null);
  if (!friends.length) return null;
  return (
    <View style={{ gap: 4 }}>
      <PixelText>GUARDIAN</PixelText>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ gap: 8, paddingVertical: 4 }}
      >
        {[null, ...friends.map((v) => v.id)].map((id) => (
          <Animated.View
            key={id ?? 'starter'}
            entering={FadeIn}
            exiting={FadeOut}
            style={{
              borderWidth: 2,
              borderColor: player.guardian === id ? c.moss : c.ink,
              backgroundColor: player.guardian === id ? c.amber : c.paper,
              padding: 2,
            }}
          >
            <Pet
              visitor={id}
              species={player.species}
              level={player.level}
              hat={player.hat}
              size={64}
              bob={false}
              onPress={() => useGame.getState().selectGuardian(id)}
              actionLabel={`Select ${id ? visitorInfo(id).name : player.pet_name} as guardian${player.guardian === id ? ', selected' : ''}`}
            />
          </Animated.View>
        ))}
      </ScrollView>
    </View>
  );
}
export function PostcardArt({ postcard }: { postcard: Postcard }) {
  const place =
    postcard.mission === 'park' ? 'PARK' : postcard.mission === 'book' ? 'LIBRARY' : 'MOUNTAIN';
  const pixels: { key: string; x: number; y: number; color: string }[] = [];
  const layers = new Map<string, number>();
  const rect = (x: number, y: number, w: number, h: number, color: string) => {
    for (let yy = y; yy < y + h; yy++) {
      for (let xx = x; xx < x + w; xx++) {
        const coordinate = `${xx}-${yy}`;
        const layer = layers.get(coordinate) ?? 0;
        layers.set(coordinate, layer + 1);
        pixels.push({ key: `${coordinate}-${layer}`, x: xx, y: yy, color });
      }
    }
  };
  rect(0, 0, 64, 36, c.slate);
  rect(0, 28, 64, 8, c.moss);
  if (postcard.mission === 'park') {
    for (const x of [8, 27, 49]) {
      rect(x, 16, 3, 16, c.shade);
      rect(x - 6, 10, 15, 13, c.positive);
      rect(x - 3, 7, 9, 4, c.positive);
    }
    rect(17, 27, 25, 2, c.body);
    rect(20, 29, 2, 5, c.shade);
    rect(37, 29, 2, 5, c.shade);
    rect(19, 23, 21, 3, c.body);
  } else if (postcard.mission === 'book') {
    rect(8, 6, 48, 24, c.shade);
    rect(11, 9, 42, 18, c.body);
    for (const y of [11, 19]) {
      for (let x = 13; x < 50; x += 5) rect(x, y, 3, 6, x % 2 ? c.terracotta : c.moss);
      rect(11, y + 6, 42, 1, c.ink);
    }
    rect(23, 27, 19, 2, c.paper);
    rect(31, 24, 2, 4, c.ink);
  } else {
    for (let y = 3; y < 32; y++) {
      const w = Math.min(27, y - 2);
      rect(32 - w, y, w * 2 + 1, 1, y < 10 ? c.paper : c.shade);
    }
    for (let y = 13; y < 32; y++) {
      const w = y - 12;
      rect(12 - Math.floor(w / 2), y, w + 1, 1, c.stone);
    }
    rect(48, 5, 6, 6, c.gold);
  }
  return (
    <View
      style={{ borderWidth: 2, borderColor: c.ink, padding: 6, backgroundColor: c.body, gap: 6 }}
    >
      <Svg width="100%" height={144} viewBox="0 0 64 36" preserveAspectRatio="xMidYMid meet">
        {pixels.map((p) => (
          <Rect key={p.key} x={p.x} y={p.y} width={1} height={1} fill={p.color} />
        ))}
      </Svg>
      <PixelText>{place} POSTCARD</PixelText>
      <BodyText>{new Date(postcard.at).toLocaleDateString()}</BodyText>
    </View>
  );
}
export function WelcomeBack() {
  const reward = useGame((s) => s.cardReward);
  if (!reward) return null;
  return (
    <View style={{ flex: 1, padding: 16, justifyContent: 'center', backgroundColor: c.body }}>
      <View
        style={{
          width: '100%',
          maxWidth: 440,
          maxHeight: '100%',
          alignSelf: 'center',
          borderWidth: 3,
          borderColor: c.ink,
          backgroundColor: c.paper,
          padding: 12,
          gap: 14,
        }}
      >
        <FlatList
          data={reward.cards}
          numColumns={2}
          keyExtractor={(id, index) => `${id}-${index}`}
          style={{ flexGrow: 0, flexShrink: 1 }}
          columnWrapperStyle={{ gap: 12, justifyContent: 'center' }}
          contentContainerStyle={{ gap: 14, paddingVertical: 8 }}
          ListHeaderComponent={
            <View style={{ gap: 14, alignItems: 'center' }}>
              <PixelText style={{ fontSize: 18, lineHeight: 28, textAlign: 'center' }}>
                WELCOME BACK
              </PixelText>
              <BodyText style={{ textAlign: 'center' }}>{reward.minutes} MIN OFFLINE</BodyText>
              <PixelText style={{ fontSize: 18, lineHeight: 26 }}>+{reward.grass} GRASS</PixelText>
              {reward.hat && <BodyText>+ {reward.hat}</BodyText>}
              {reward.early && (
                <BodyText style={{ textAlign: 'center' }}>Mission ended early.</BodyText>
              )}
              {reward.cards.length > 0 && (
                <PixelText style={{ lineHeight: 22, textAlign: 'center' }}>
                  +{reward.cards.length} {reward.cards.length === 1 ? 'CARD' : 'CARDS'}
                </PixelText>
              )}
            </View>
          }
          renderItem={({ item, index }) => (
            <View style={{ flex: 1, maxWidth: 178 }}>
              <RewardCard id={item} index={index} />
            </View>
          )}
          ListFooterComponent={
            <View style={{ gap: 16 }}>
              {reward.visitor && (
                <View style={{ alignItems: 'center', gap: 5 }}>
                  <Pet visitor={reward.visitor} size={128} bob={false} />
                  <PixelText style={{ textAlign: 'center' }}>
                    {visitorInfo(reward.visitor).name} VISITED
                  </PixelText>
                  <BodyText style={{ textAlign: 'center', fontFamily: 'Inter_400Regular' }}>
                    someone visited while you were gone!
                  </BodyText>
                  <BodyText style={{ textAlign: 'center' }}>
                    Tap your visitor in the garden to befriend it.
                  </BodyText>
                </View>
              )}
              {reward.postcard && <PostcardArt postcard={reward.postcard} />}
            </View>
          }
        />
        <PixelButton
          label="BACK TO THE GARDEN"
          onPress={() => {
            useGame.getState().dismissCards();
            router.navigate('/');
          }}
        />
      </View>
    </View>
  );
}
export function JournalEmpty({ onPress }: { onPress: () => void }) {
  return (
    <View style={{ padding: 20, alignItems: 'center', gap: 16 }}>
      <BookOpen size={32} color={c.ink} />
      <BodyText style={{ textAlign: 'center' }}>
        Bring back your first postcard from a mission.
      </BodyText>
      <PixelButton label="GO ON A MISSION" onPress={onPress} />
    </View>
  );
}
