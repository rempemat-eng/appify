import { useEffect, useState } from 'react';
import { ScrollView, View, useWindowDimensions } from 'react-native';
import { router } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { PixelScene } from '@/components/pixel-scenes';
import Animated, {
  cancelAnimation,
  FadeIn,
  FadeOut,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withTiming,
} from 'react-native-reanimated';
import Svg, { Rect } from 'react-native-svg';
import { BookOpen } from 'lucide-react-native';
import { useReducedMotion } from '@/lib/motion';
import { cards, cardIds, summarizeCardRewards } from '@/lib/cards';
import { palette, useGame, type Player } from '@/lib/game';
import { cozy as c, panelStyle } from '@/lib/cozy';
import { collectionOf, visitorInfo, type Postcard } from '@/lib/visitors';
import { Pet, PixelButton, PixelText } from '@/components/game-ui';
import { BodyText, GrassRoll } from '@/components/pixel-feedback';
import { CozySheet, PaperFinish } from '@/components/cozy-ui';
import { LightSweep, PixelBurst } from '@/components/cozy-motion';
import { RewardCard } from '@/components/habit-cards';
export function GardenVisitor() {
  const reduced = useReducedMotion();
  const waiting = useGame((s) => s.waitingVisitor);
  const now = useGame((s) => s.now);
  const friends = useGame((s) =>
    s.player ? collectionOf(s.player).filter((v) => v.befriendedAt !== null).length : 0,
  );
  const [celebration, setCelebration] = useState({ friends, show: false });
  if (friends !== celebration.friends)
    setCelebration({ friends, show: friends > celebration.friends });
  useEffect(() => {
    if (!celebration.show) return undefined;
    const timer = setTimeout(() => setCelebration({ friends, show: false }), 600);
    return () => clearTimeout(timer);
  }, [celebration.show, friends]);
  const peek = useSharedValue(12);
  useEffect(() => {
    if (!waiting?.id) return undefined;
    peek.set(reduced ? 0 : withDelay(120, withTiming(0, { duration: 180 })));
    return () => cancelAnimation(peek);
  }, [peek, reduced, waiting?.id]);
  const motion = useAnimatedStyle(() => ({ transform: [{ translateY: Math.round(peek.value) }] }));
  if (!waiting)
    return celebration.show ? (
      <View
        pointerEvents="none"
        style={{ position: 'absolute', right: 40, bottom: 60, width: 64, height: 64 }}
      >
        <PixelBurst hearts />
      </View>
    ) : null;
  const v = visitorInfo(waiting.id);
  return (
    <Animated.View
      entering={FadeIn.duration(100)}
      onTouchStart={() => {
        cancelAnimation(peek);
        peek.set(0);
      }}
      style={[
        {
          ...panelStyle,
          position: 'absolute',
          right: 8,
          bottom: 16,
          alignItems: 'center',
          padding: 4,
        },
        motion,
      ]}
    >
      <PaperFinish />
      <Pet
        visitor={v.id}
        size={64}
        bob={false}
        onPress={() => useGame.getState().befriendVisitor()}
        actionLabel={`Befriend ${v.name}, free`}
      />
      <BodyText style={{ fontSize: 11, fontFamily: 'Nunito_800ExtraBold' }}>BEFRIEND</BodyText>
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
      <BodyText style={{ fontSize: 12, fontFamily: 'Nunito_800ExtraBold' }}>GUARDIAN</BodyText>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ gap: 12, paddingVertical: 4 }}
      >
        {[null, ...friends.map((v) => v.id)].map((id) => (
          <Animated.View
            key={id ?? 'starter'}
            entering={FadeIn.duration(100)}
            exiting={FadeOut.duration(100)}
            style={{
              ...panelStyle,
              borderColor: player.guardian === id ? c.moss : c.outline,
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
  const a = palette;
  const place =
    postcard.mission === 'park' ? 'PARK' : postcard.mission === 'book' ? 'LIBRARY' : 'MOUNTAIN';
  const pixels = new Map<string, { key: string; x: number; y: number; color: string }>();
  const rect = (x: number, y: number, w: number, h: number, color: string) => {
    for (let yy = y; yy < y + h; yy++)
      for (let xx = x; xx < x + w; xx++) {
        const key = `${xx}-${yy}`;
        pixels.set(key, { key, x: xx, y: yy, color });
      }
  };
  rect(0, 0, 64, 36, a.slate);
  rect(0, 28, 64, 8, a.moss);
  if (postcard.mission === 'park') {
    for (const x of [8, 27, 49]) {
      rect(x, 16, 3, 16, a.shade);
      rect(x - 6, 10, 15, 13, a.positive);
      rect(x - 3, 7, 9, 4, a.positive);
    }
    rect(17, 27, 25, 2, a.body);
    rect(20, 29, 2, 5, a.shade);
    rect(37, 29, 2, 5, a.shade);
    rect(19, 23, 21, 3, a.body);
  } else if (postcard.mission === 'book') {
    rect(8, 6, 48, 24, a.shade);
    rect(11, 9, 42, 18, a.body);
    for (const y of [11, 19]) {
      for (let x = 13; x < 50; x += 5) rect(x, y, 3, 6, x % 2 ? a.terracotta : a.moss);
      rect(11, y + 6, 42, 1, a.ink);
    }
    rect(23, 27, 19, 2, a.paper);
    rect(31, 24, 2, 4, a.ink);
  } else {
    for (let y = 3; y < 32; y++) {
      const w = Math.min(27, y - 2);
      rect(32 - w, y, w * 2 + 1, 1, y < 10 ? a.paper : a.shade);
    }
    for (let y = 13; y < 32; y++) {
      const w = y - 12;
      rect(12 - Math.floor(w / 2), y, w + 1, 1, a.stone);
    }
    rect(48, 5, 6, 6, a.gold);
  }
  return (
    <View style={{ ...panelStyle, padding: 12, gap: 8 }}>
      <PaperFinish />
      <View style={{ alignItems: 'center' }}>
        <Svg width={256} height={144} viewBox="0 0 64 36">
          {Array.from(pixels.values()).map((p) => (
            <Rect key={p.key} x={p.x} y={p.y} width={1} height={1} fill={p.color} />
          ))}
        </Svg>
      </View>
      <BodyText style={{ fontFamily: 'Nunito_800ExtraBold' }}>{place} POSTCARD</BodyText>
      <BodyText>{new Date(postcard.at).toLocaleDateString()}</BodyText>
    </View>
  );
}
export function WelcomeBack() {
  const togetherStatus = useGame(
    (s) => s.sessions.find((session) => session.id === s.cardReward?.sessionId)?.status,
  );
  const reportPending = useGame((s) =>
    s.pendingTogetherWakes.some((wake) => wake.sid === s.cardReward?.sessionId),
  );
  const reward = useGame((s) => s.cardReward);
  const waiting = useGame((s) => s.waitingVisitor);
  const p = useGame((s) => s.player);
  const [details, setDetails] = useState(false);
  const [skip, setSkip] = useState(false);
  const [hearted, setHearted] = useState(false);
  const { height, width } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  if (!reward || !p) return null;
  const groups = cardIds
    .filter((id) => reward.cards.includes(id))
    .map((id) => ({ id, count: reward.cards.filter((card) => card === id).length }));
  const summary = reward.deckBefore ? summarizeCardRewards(reward.deckBefore, reward.cards) : null;
  const friend =
    reward.visitor &&
    collectionOf(p).some((entry) => entry.id === reward.visitor && entry.befriendedAt !== null);
  return (
    <View
      onStartShouldSetResponderCapture={() => {
        setSkip(true);
        return false;
      }}
      onTouchStart={() => setSkip(true)}
      style={{ flex: 1, justifyContent: 'flex-end', backgroundColor: c.paper }}
    >
      <View pointerEvents="none" style={{ flex: 1, minHeight: 200 }}>
        <PixelScene
          sunrise
          species={p.species}
          level={p.level}
          style={{
            height: '100%',
            borderWidth: 0,
            borderRadius: 0,
            alignItems: 'center',
            justifyContent: 'flex-end',
            paddingBottom: 39 * Math.max(1, Math.floor(width / 160)),
          }}
        >
          <Pet
            species={p.species}
            visitor={p.guardian}
            level={p.level}
            hat={p.hat}
            size={128}
            bob={false}
          />
        </PixelScene>
        <LightSweep skip={skip} />
        <View
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: c.shadow,
          }}
        />
      </View>
      <CozySheet
        onSkip={() => setSkip(true)}
        style={{
          width: '100%',
          maxWidth: 640,
          maxHeight: height * 0.64,
          alignSelf: 'center',
          borderBottomLeftRadius: 0,
          borderBottomRightRadius: 0,
          padding: 16,
          paddingBottom: insets.bottom + 16,
          gap: 12,
        }}
      >
        <PixelText
          accessibilityRole="header"
          style={{ fontSize: 16, lineHeight: 26, textAlign: 'center' }}
        >
          WELCOME BACK
        </PixelText>
        <ScrollView
          style={{ flexShrink: 1, maxHeight: Math.max(80, height * 0.64 - 200 - insets.bottom) }}
          contentContainerStyle={{ gap: 12, paddingBottom: 12 }}
        >
          <BodyText style={{ textAlign: 'center' }}>{reward.minutes} offline MIN</BodyText>
          <View
            style={{ flexDirection: 'row', gap: 8, justifyContent: 'center', alignItems: 'center' }}
          >
            <BodyText>+</BodyText>
            <GrassRoll value={reward.grass} from={0} size={20} skip={skip} />
            <BodyText>GRASS</BodyText>
          </View>
          {togetherStatus === 'failed' && (
            <BodyText>Together ended early. Ordinary rewards kept.</BodyText>
          )}
          {reportPending && <BodyText>Together report pending · ordinary rewards saved</BodyText>}
          {reward.early && <BodyText>Early return · no mission completion reward</BodyText>}
          {reward.hat && <BodyText>+ {reward.hat}</BodyText>}
          {groups.length > 0 && (
            <>
              <BodyText style={{ fontFamily: 'Nunito_800ExtraBold', textAlign: 'center' }}>
                {reward.cards.length} {reward.cards.length === 1 ? 'card' : 'cards'} earned · deck{' '}
                {p.deck.length}/20
              </BodyText>
              <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 12 }}>
                {groups.map((group, index) => (
                  <View key={group.id} style={{ width: groups.length === 1 ? '100%' : '47%' }}>
                    <RewardCard id={group.id} index={index} skip={skip} />
                  </View>
                ))}
              </View>
            </>
          )}
          {reward.visitor && (
            <View style={{ flexDirection: 'row', gap: 12, alignItems: 'center' }}>
              <View>
                <Pet visitor={reward.visitor} size={64} bob={false} />
                {hearted && <PixelBurst hearts skip={false} />}
              </View>
              <View style={{ flex: 1, gap: 8 }}>
                <BodyText style={{ fontFamily: 'Nunito_800ExtraBold' }}>
                  {visitorInfo(reward.visitor).name} visited
                </BodyText>
                {waiting?.id === reward.visitor && !friend ? (
                  <PixelButton
                    small
                    label="BEFRIEND · FREE"
                    onPress={() => {
                      useGame.getState().befriendVisitor();
                      setHearted(true);
                    }}
                  />
                ) : (
                  <BodyText accessibilityLiveRegion="polite" style={{ fontSize: 12 }}>
                    {friend ? 'Your friend is in the garden.' : 'Recorded in your Field Journal.'}
                  </BodyText>
                )}
              </View>
            </View>
          )}
          {reward.postcard && <PostcardArt postcard={reward.postcard} />}
          {summary && (
            <>
              <PixelButton
                small
                light
                label={details ? 'HIDE DETAILS' : 'REWARD DETAILS'}
                onPress={() => setDetails(!details)}
              />
              {details && (
                <BodyText style={{ fontSize: 12 }}>
                  {summary.kept} new kept
                  {summary.previousReplaced
                    ? ` · ${summary.previousReplaced} previous replaced`
                    : ''}
                  {summary.earnedReplaced
                    ? ` · ${summary.earnedReplaced} earned then replaced`
                    : ''}
                  {groups.map((g) => ` · ${cards[g.id].name} ×${g.count}`).join('')}
                </BodyText>
              )}
            </>
          )}
        </ScrollView>
        <PixelButton
          label="BACK TO THE GARDEN"
          onPress={() => {
            useGame.getState().dismissCards();
            router.navigate('/');
          }}
        />
      </CozySheet>
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
