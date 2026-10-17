import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { Image, ScrollView, View, useWindowDimensions } from 'react-native';
import { router } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { PixelProp, PixelScene } from '@/components/pixel-scenes';
import { sceneImages } from '@/lib/scene-assets';
import { worldCatalogue } from '@/lib/world-catalogue';
import Animated, {
  cancelAnimation,
  FadeIn,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withTiming,
} from 'react-native-reanimated';
import { useReducedMotion } from '@/lib/motion';
import { cards, cardIds, summarizeCardRewards } from '@/lib/cards';
import { useGame } from '@/lib/game';
import { cozy as c, panelStyle } from '@/lib/cozy';
import { collectionOf, guardianPlayer, visitorInfo, type Postcard } from '@/lib/visitors';
import { GuardianPet } from '@/components/guardian-pet';
import { MemoryReflection } from '@/components/companion-memories';
import { Pet, PixelButton, PixelText } from '@/components/game-ui';
import { BodyText, GrassRoll } from '@/components/pixel-feedback';
import { CozySheet, PaperFinish } from '@/components/cozy-ui';
import { LightSweep, PixelBurst } from '@/components/cozy-motion';
import { RewardCard } from '@/components/habit-cards';
import { gameLayout } from '@/lib/layout';
export function GardenVisitor({ active = true }: { active?: boolean }) {
  const activeRef = useRef(active);
  useLayoutEffect(() => {
    activeRef.current = active;
    return () => {
      activeRef.current = false;
    };
  }, [active]);
  const reduced = useReducedMotion();
  const waiting = useGame((s) => s.waitingVisitor);
  const now = useGame((s) => s.now);
  const friends = useGame((s) =>
    s.player ? collectionOf(s.player).filter((v) => v.befriendedAt !== null).length : 0,
  );
  const [celebration, setCelebration] = useState({ friends, show: false });
  if (friends !== celebration.friends || ((!active || reduced) && celebration.show))
    setCelebration({
      friends,
      show: active && !reduced && friends > celebration.friends,
    });
  useEffect(() => {
    if (!active || !celebration.show) return undefined;
    const timer = setTimeout(() => setCelebration({ friends, show: false }), 600);
    return () => clearTimeout(timer);
  }, [active, celebration.show, friends]);
  const peek = useSharedValue(0);
  useEffect(() => {
    cancelAnimation(peek);
    peek.set(0);
    if (!active || !waiting?.id || reduced) return undefined;
    peek.set(12);
    peek.set(withDelay(120, withTiming(0, { duration: 180 })));
    return () => {
      cancelAnimation(peek);
      peek.set(0);
    };
  }, [active, peek, reduced, waiting?.id]);
  const motion = useAnimatedStyle(() => ({ transform: [{ translateY: Math.round(peek.value) }] }));
  if (!active) return null;
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
      entering={reduced ? undefined : FadeIn.duration(100)}
      onTouchStart={() => {
        if (!activeRef.current) return;
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
        active={active}
        visitor={v.id}
        size={64}
        bob={false}
        onPress={() => {
          if (activeRef.current && useGame.getState().waitingVisitor?.id === v.id)
            useGame.getState().befriendVisitor();
        }}
        actionLabel={`Befriend ${v.name}, free`}
      />
      <BodyText style={{ fontSize: 11, fontFamily: 'PixelifySans_700Bold' }}>BEFRIEND</BodyText>
      <BodyText style={{ fontSize: 11 }}>
        {waiting.expiresAt ? Math.max(0, Math.ceil((waiting.expiresAt - now) / 1000)) : 10} MIN
      </BodyText>
    </Animated.View>
  );
}
export { CompanionPicker as GuardianPicker } from '@/components/companion-picker';
export function PostcardArt({ postcard }: { postcard: Postcard }) {
  const place = worldCatalogue[postcard.mission].postcardTitle;
  return (
    <View style={{ ...panelStyle, padding: 12, gap: 8 }}>
      <PaperFinish />
      <View
        pointerEvents="none"
        aria-hidden
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
        // @ts-expect-error dataSet is a react-native-web prop (nearest-neighbour pixels).
        dataSet={{ pixel: 'true' }}
        style={{
          alignItems: 'center',
          backgroundColor: c.body,
          padding: 6,
          borderWidth: 1,
          borderColor: c.inset,
          borderRadius: 6,
        }}
      >
        <Image
          source={sceneImages[postcard.mission]}
          resizeMode="contain"
          style={{ width: 216, height: 150 }}
        />
      </View>
      <BodyText style={{ fontFamily: 'PixelifySans_700Bold' }}>{place} POSTCARD</BodyText>
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
  const missionReturnPending = useGame((s) => s.missionReturnPending);
  const pendingMemories = useGame((s) => s.pendingMemories);
  const [keptMemory, setKeptMemory] = useState<string | null>(null);
  const waiting = useGame((s) => s.waitingVisitor);
  const p = useGame((s) => s.player);
  const [details, setDetails] = useState(false);
  const [skip, setSkip] = useState(false);
  const [hearted, setHearted] = useState(false);
  const { height, width } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const [containerHeight, setContainerHeight] = useState<number | null>(null);
  const [headingHeight, setHeadingHeight] = useState(26);
  const [footerHeight, setFooterHeight] = useState(124);
  const [sceneBounds, setSceneBounds] = useState(() => ({
    width: Math.min(width, gameLayout.maxWidth),
    height: Math.max(0, height * 0.36 - insets.top - insets.bottom),
  }));
  // The overlay already owns the top safe area. The sheet owns the bottom one.
  // Keep the usual 64% composition when it leaves enough room to read, but let
  // a short landscape window give its space to the scrollable reward content.
  const availableHeight = Math.max(
    0,
    Math.min(height - insets.top, containerHeight ?? height - insets.top),
  );
  const compact = availableHeight < 480;
  // Include the measured heading and both footer buttons so larger text leaves
  // its remaining space to the scrollable reward content.
  const sheetChrome =
    (compact ? 152 : 198) +
    insets.bottom +
    Math.max(0, headingHeight - (compact ? 24 : 26)) +
    Math.max(0, footerHeight - 56);
  const sheetMaxHeight = Math.min(availableHeight, Math.max(height * 0.64, sheetChrome + 144));
  const bodyMaxHeight = Math.max(0, sheetMaxHeight - sheetChrome);
  if (!reward || !p) return null;
  const scenePixel = Math.max(1, Math.floor(sceneBounds.width / 160));
  const scenePetSize = Math.max(0, Math.min(128, Math.floor((sceneBounds.height - 8) / 32) * 32));
  // Match PixelScene's measured integer scale, leaving room for the companion
  // above the ground even when the reward sheet takes most of a short window.
  const sceneGround = Math.min(
    39 * scenePixel,
    Math.max(0, Math.floor((sceneBounds.height - scenePetSize - 8) / scenePixel) * scenePixel),
  );
  const groups = cardIds
    .filter((id) => reward.cards.includes(id))
    .map((id) => ({ id, count: reward.cards.filter((card) => card === id).length }));
  const summary = reward.deckBefore ? summarizeCardRewards(reward.deckBefore, reward.cards) : null;
  const reflection = pendingMemories.find((offer) => offer.id === reward.settlementId);
  const friend =
    reward.visitor &&
    collectionOf(p).some((entry) => entry.id === reward.visitor && entry.befriendedAt !== null);
  return (
    <View
      onLayout={(event) => {
        const measuredHeight = Math.max(0, event.nativeEvent.layout.height);
        setContainerHeight((previous) => (previous === measuredHeight ? previous : measuredHeight));
      }}
      onStartShouldSetResponderCapture={() => {
        setSkip(true);
        return false;
      }}
      onTouchStart={() => setSkip(true)}
      style={{ flex: 1, justifyContent: 'flex-end', backgroundColor: c.paper }}
    >
      <View
        pointerEvents="none"
        onLayout={(event) => {
          const { width: sceneWidth, height: sceneHeight } = event.nativeEvent.layout;
          setSceneBounds((previous) =>
            previous.width === sceneWidth && previous.height === sceneHeight
              ? previous
              : { width: sceneWidth, height: sceneHeight },
          );
        }}
        style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}
      >
        <PixelScene
          sunrise
          species={guardianPlayer(p).species}
          level={p.level}
          groundInset={sceneGround}
          style={{
            height: '100%',
            borderWidth: 0,
            borderRadius: 0,
            alignItems: 'center',
            justifyContent: 'flex-end',
            paddingBottom: sceneGround,
          }}
        >
          {scenePetSize > 0 && <GuardianPet player={p} size={scenePetSize} bob={false} />}
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
          maxHeight: sheetMaxHeight,
          alignSelf: 'center',
          borderBottomLeftRadius: 0,
          borderBottomRightRadius: 0,
          padding: compact ? 12 : 16,
          paddingBottom: insets.bottom + (compact ? 12 : 16),
          gap: compact ? 8 : 12,
        }}
      >
        <PixelText
          accessibilityRole="header"
          onLayout={(event) => {
            const measuredHeight = Math.max(0, event.nativeEvent.layout.height);
            setHeadingHeight((previous) =>
              previous === measuredHeight ? previous : measuredHeight,
            );
          }}
          style={{
            fontSize: compact ? 14 : 16,
            lineHeight: compact ? 24 : 26,
            textAlign: 'center',
          }}
        >
          WELCOME BACK
        </PixelText>
        <ScrollView
          style={{ flexShrink: 1, maxHeight: bodyMaxHeight }}
          contentContainerStyle={{ gap: 12, paddingBottom: 12 }}
        >
          <BodyText style={{ textAlign: 'center' }}>
            {reward.minutes} simulated offline MIN
          </BodyText>
          {missionReturnPending && (
            <BodyText style={{ textAlign: 'center', fontSize: 12, lineHeight: 18 }}>
              Mission complete. Your rewards are saved and your garden is still shielded. Your care
              window and play time begin when you choose BACK TO THE GARDEN.
            </BodyText>
          )}
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
          {reward.visitor && (
            <View style={{ flexDirection: 'row', gap: 12, alignItems: 'center' }}>
              <View>
                <Pet visitor={reward.visitor} size={64} bob={false} />
                {hearted && <PixelBurst hearts skip={false} />}
              </View>
              <View style={{ flex: 1, gap: 8 }}>
                <BodyText style={{ fontFamily: 'PixelifySans_700Bold' }}>
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
          {reflection && (
            <BodyText style={{ fontSize: 12, lineHeight: 18 }}>
              Recent reflections are also in your Field Journal, so you can leave this one for
              later.
            </BodyText>
          )}
          {reflection && (
            <MemoryReflection
              offer={reflection}
              onKeep={() => {
                useGame.getState().recordCompanionMemory(reflection.id);
                if (
                  useGame.getState().companionMemories.some((memory) => memory.id === reflection.id)
                )
                  setKeptMemory(reflection.companion.name);
              }}
              onSkip={() => useGame.getState().dismissCompanionMemory(reflection.id)}
            />
          )}
          {keptMemory && (
            <BodyText accessibilityLiveRegion="polite" style={{ fontSize: 12 }}>
              A memory with {keptMemory} is saved in your Field Journal.
            </BodyText>
          )}
          {groups.length > 0 && (
            <>
              <BodyText style={{ fontFamily: 'PixelifySans_700Bold', textAlign: 'center' }}>
                {reward.cards.length.toLocaleString()}{' '}
                {reward.cards.length === 1 ? 'card' : 'cards'} earned
              </BodyText>
              <BodyText style={{ fontSize: 12, textAlign: 'center' }}>
                {summary ? `${summary.kept.toLocaleString()} of these kept · ` : ''}
                {p.deck.length}/20 in your deck
              </BodyText>
              {summary && (summary.previousReplaced > 0 || summary.earnedReplaced > 0) && (
                <BodyText style={{ fontSize: 12, textAlign: 'center' }}>
                  {summary.previousReplaced > 0
                    ? `${summary.previousReplaced.toLocaleString()} older ${summary.previousReplaced === 1 ? 'card was' : 'cards were'} replaced.`
                    : ''}
                  {summary.previousReplaced > 0 && summary.earnedReplaced > 0 ? ' ' : ''}
                  {summary.earnedReplaced > 0
                    ? `${summary.earnedReplaced.toLocaleString()} earned ${summary.earnedReplaced === 1 ? 'card was' : 'cards were'} replaced by later rewards.`
                    : ''}
                </BodyText>
              )}
              <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 12 }}>
                {groups.map((group, index) => (
                  <View
                    key={group.id}
                    style={{ width: groups.length === 1 ? '100%' : '47%', gap: 6 }}
                  >
                    <RewardCard id={group.id} index={index} skip={skip} />
                    <BodyText
                      accessibilityLabel={`${cards[group.id].name}: ${group.count} earned`}
                      style={{
                        alignSelf: 'center',
                        borderRadius: 999,
                        paddingHorizontal: 10,
                        paddingVertical: 3,
                        overflow: 'hidden',
                        backgroundColor: c.sage,
                        color: c.ink,
                        fontFamily: 'PixelifySans_700Bold',
                        fontSize: 12,
                        textAlign: 'center',
                      }}
                    >
                      ×{group.count.toLocaleString()} earned
                    </BodyText>
                  </View>
                ))}
              </View>
            </>
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
                  Your deck holds up to 20 cards. Once full, each new card replaces the weakest card
                  currently in the deck. Cards shown above are all the cards earned during this
                  break, including any replaced by later rewards.
                </BodyText>
              )}
            </>
          )}
          <BodyText style={{ fontSize: 12, lineHeight: 18 }}>
            Ready to put your phone down? Start an untimed demo nap.
          </BodyText>
          {waiting && waiting.id === reward.visitor && !friend && (
            <BodyText style={{ fontSize: 12, lineHeight: 18 }}>
              To invite this visitor along, use BEFRIEND above before starting a nap.
            </BodyText>
          )}
        </ScrollView>
        <View
          onLayout={(event) => {
            const measuredHeight = Math.max(0, event.nativeEvent.layout.height);
            setFooterHeight((previous) =>
              previous === measuredHeight ? previous : measuredHeight,
            );
          }}
          style={{ gap: compact ? 8 : 12 }}
        >
          <PixelButton
            label="BACK TO THE GARDEN"
            onPress={() => {
              useGame.getState().dismissCards();
              router.navigate('/');
            }}
          />
          <PixelButton
            label="START A NAP"
            small
            light
            onPress={() => {
              useGame.getState().dismissCards();
              router.replace('/');
              useGame.getState().sleep();
            }}
          />
        </View>
      </CozySheet>
    </View>
  );
}
export function JournalEmpty({ onPress }: { onPress: () => void }) {
  return (
    <View style={{ padding: 20, alignItems: 'center', gap: 16 }}>
      <PixelProp kind="book" size={32} />
      <BodyText style={{ textAlign: 'center' }}>
        Bring back your first postcard from a mission.
      </BodyText>
      <PixelButton label="GO ON A MISSION" onPress={onPress} />
    </View>
  );
}
