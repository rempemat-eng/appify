import { useEffect, useRef, useState } from 'react';
import {
  FlatList,
  KeyboardAvoidingView,
  Platform,
  TextInput,
  View,
  useWindowDimensions,
} from 'react-native';
import { router, useIsFocused, useLocalSearchParams } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { PixelIcon } from '@/components/pixel-icon';
import { cozy as c } from '@/lib/cozy';
import { backendConfigured } from '@/lib/bilt';
import { gameColumn, gameLayout, hotbarClearance, hudClearance } from '@/lib/layout';
import { useReducedMotion } from '@/lib/motion';
import { useAppActive } from '@/lib/app-active';
import { bot, feedback, hats, status, useGame, type Player } from '@/lib/game';
import { matchup } from '@/lib/battle';
import { grasslings, growthStage, levelPreview } from '@/lib/grasslings';
import { budgetVoice, dayKey } from '@/lib/offline-rules';
import { gardenTips, type GardenTipId } from '@/lib/first-session';
import { guardianPlayer, isVisitorId, visitorInfo } from '@/lib/visitors';
import { FriendCode } from '@/components/friend-code';
import { GuardianPet } from '@/components/guardian-pet';
import { GardenVisitor } from '@/components/visitors';
import { GardenTip } from '@/components/garden-guide';
import { Page, Pet, PixelButton, PixelText, StatusChip } from '@/components/game-ui';
import { WorldWindow } from '@/components/atlas-walk';
import { missionPlaces, regionPoint, rings } from '@/lib/world-places';
import { GardenWorld } from '@/components/garden-world';
import { MissionDeparture } from '@/components/mission-departure';
import { openSheet, useUi } from '@/lib/ui';
import { useAmbience } from '@/lib/sound';
import { type CompanionMemory } from '@/lib/companion-memories';
import { GardenKeepsakeSheet } from '@/components/garden-keepsakes';
import { gardenMarker } from '@/components/garden-journey';
import { BodyText, Dialogue } from '@/components/pixel-feedback';
import { PixelFrame, PixelInput } from '@/components/pixel-frame';
import { CozyBackground, CozyPanel } from '@/components/cozy-ui';
import { PixelBurst } from '@/components/cozy-motion';
import { PlayPause, TogetherInvite, usePlayPaused } from '@/components/offline-garden';
const lines = {
  grumpy: ['my leaves could use a breather.', 'a quiet pause would be nice. the garden can wait.'],
  exposed: [
    'the garden feels a little open. a nap would put the shield back up.',
    'shall we rest for a bit? i will keep watch.',
  ],
  care: ['a little time to settle in.', 'welcome home. have a look around.'],
  idle: [
    'the grass is lovely today. you could go and touch some.',
    'i am small, but i am very good company.',
  ],
};
// Idle chatter shows for one tick in four, so the garden is mostly quiet.
const CHAT_TICK_MS = 6000;
export function HomeScreen() {
  const reduced = useReducedMotion();
  const focused = useIsFocused();
  const appActive = useAppActive();
  const { height, width } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const p = useGame((s) => s.player);
  const now = useGame((s) => s.now);
  const voice = useGame((s) => s.voice);
  const firstWake = useGame((s) => s.firstWake);
  const tips = useGame((s) => s.tips);
  const memories = useGame((s) => s.companionMemories);
  const sheet = useUi((s) => s.sheet);
  const paused = usePlayPaused();
  const busy = useGame((s) =>
    Boolean(
      s.message ||
      s.battle ||
      s.cardReward ||
      s.deckOpen ||
      s.recap ||
      s.alerts.length ||
      s.flash ||
      s.guideOpen,
    ),
  );
  const key = `${p?.id ?? ''}-${firstWake}-${paused}`;
  const candidate: GardenTipId | null = paused
    ? 'budget'
    : firstWake && !tips.includes('wake')
      ? 'wake'
      : !firstWake && !tips.includes('phone')
        ? 'phone'
        : null;
  const [lesson, setLesson] = useState({ key, id: candidate });
  if (lesson.key !== key) setLesson({ key, id: candidate });
  const coaching = busy ? null : lesson.id;
  const [keepsakeSheet, setKeepsakeSheet] = useState<{
    focused: boolean;
    memory: CompanionMemory | null;
  }>({ focused, memory: null });
  if (keepsakeSheet.focused !== focused) setKeepsakeSheet({ focused, memory: null });
  const openMemory = keepsakeSheet.focused === focused ? keepsakeSheet.memory : null;
  const gardenActive =
    focused && appActive && !busy && sheet === null && !openMemory && p?.mode === 'awake';
  // Day or night birdsong, only while the garden is the thing on screen.
  const hour = new Date(now).getHours();
  useAmbience(gardenActive ? (hour < 6 || hour >= 21 ? 'night' : 'day') : null);
  useEffect(() => {
    if (coaching && gardenActive) useGame.getState().seeTip(coaching);
  }, [coaching, gardenActive]);
  const [crumbs, setCrumbs] = useState(false);
  const [line, setLine] = useState(0);
  useEffect(() => {
    if (reduced || !gardenActive) return undefined;
    const timer = setInterval(() => {
      setLine((n) => n + 1);
    }, CHAT_TICK_MS);
    return () => clearInterval(timer);
  }, [reduced, gardenActive]);
  useEffect(() => {
    if (!voice) return undefined;
    const timer = setTimeout(() => {
      // A newer message must keep its own full reading time.
      if (useGame.getState().voice === voice) useGame.setState({ voice: null });
    }, 6000);
    return () => clearTimeout(timer);
  }, [voice]);
  useEffect(() => {
    if (!crumbs) return undefined;
    const timer = setTimeout(() => setCrumbs(false), 600);
    return () => clearTimeout(timer);
  }, [crumbs]);
  if (!p) return null;
  const state = status(p, now);
  const chatter = (
    p.mood < 30
      ? lines.grumpy
      : state.kind === 'exposed'
        ? lines.exposed
        : state.kind === 'care'
          ? lines.care
          : lines.idle
  )[Math.floor(line / 4) % 2];
  const say = coaching
    ? {
        text: gardenTips[coaching].text,
        hint: 'tap to dismiss',
        onPress: () => setLesson({ key, id: null }),
      }
    : voice
      ? { text: voice, onPress: () => useGame.setState({ voice: null }) }
      : paused
        ? { text: budgetVoice }
        : line % 4 === 1 || reduced
          ? { text: chatter }
          : null;
  const worldWidth = Math.min(width, gameLayout.maxWidth);
  return (
    <View style={{ flex: 1, backgroundColor: '#315C3B', alignItems: 'center' }}>
      <View style={{ width: worldWidth, height }}>
        <GardenWorld
          active={gardenActive}
          memories={memories}
          width={worldWidth}
          viewportHeight={height}
          player={p}
          grumpy={p.mood < 30}
          sleepy={paused}
          say={gardenActive ? say : null}
          marker={gardenMarker(p)}
          onKeepsakePress={(memory) => setKeepsakeSheet({ focused, memory })}
          onNap={() => openSheet('nap')}
          onFeed={() => {
            useGame.getState().feed();
            setCrumbs(true);
          }}
        />
        <View
          pointerEvents="box-none"
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            bottom: hotbarClearance(insets.bottom),
            height: 140,
          }}
        >
          <GardenVisitor active={gardenActive} />
          {crumbs && <PixelBurst />}
        </View>
      </View>
      <GardenKeepsakeSheet
        memory={openMemory}
        onClose={() => setKeepsakeSheet({ focused, memory: null })}
        onJournal={() => {
          setKeepsakeSheet({ focused, memory: null });
          router.push('/journal?tab=memories');
        }}
      />
    </View>
  );
}
export function MissionsScreen() {
  const focused = useIsFocused();
  return focused ? <MissionDeparture /> : null;
}
export function ShopScreen() {
  const paused = usePlayPaused();
  const p = useGame((s) => s.player);
  const [merchant, setMerchant] = useState('fresh hats for well-rested heads.');
  if (!p) return null;
  const preview = levelPreview(p.level);
  return (
    <Page>
      <PlayPause />
      <PixelText style={{ fontSize: 16 }}>GROW YOUR GARDEN</PixelText>
      <CozyPanel style={{ padding: 16, gap: 12 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
          <GuardianPet player={p} level={p.level + 1} size={96} bob={false} />
          <View style={{ flex: 1, gap: 4 }}>
            <BodyText style={{ fontFamily: 'PixelifySans_700Bold', fontSize: 16 }}>
              Level {p.level} → {p.level + 1}
            </BodyText>
            <BodyText>
              {p.level < 3
                ? `${growthStage(p.level)} → ${preview.stage}`
                : `${preview.stage} · LV ${preview.next}`}
            </BodyText>
            <BodyText style={{ fontSize: 12 }}>{preview.unlock}</BodyText>
          </View>
        </View>
        <PixelButton
          label={
            paused
              ? 'TAKE A BREAK'
              : p.grass < preview.cost
                ? `NEED ${preview.cost - p.grass} MORE GRASS`
                : `LEVEL UP · ${50 * p.level} GRASS`
          }
          disabled={paused || p.grass < p.level * 50}
          onDisabledPress={() => {
            if (paused) {
              feedback('error');
              return;
            }
            setMerchant('a few more GRASS for this one.');
            feedback('error');
          }}
          onPress={() => {
            useGame.getState().levelUp();
            setMerchant('fine choice. very hat.');
          }}
        />
      </CozyPanel>
      {/* the stall is a place: Moss's corner of Crossroads Town, as it is in the world */}
      <PixelFrame tone="leaf" style={{ padding: 4 }}>
        <WorldWindow region="valley" at={regionPoint(missionPlaces.shop)} height={150} />
      </PixelFrame>
      <PixelButton
        small
        light
        label="VISIT THE STALL"
        onPress={() => {
          // walk out of the gate to Moss's stall yourself (free, grants nothing)
          router.push({ pathname: '/world', params: { place: 'shop' } });
        }}
      />
      <View style={{ gap: 2 }}>
        <BodyText style={{ fontFamily: 'PixelifySans_700Bold' }}>Moss the merchant</BodyText>
        <BodyText style={{ fontSize: 12 }}>{merchant}</BodyText>
      </View>
      <View style={{ flexDirection: 'row', alignItems: 'baseline', marginTop: 12 }}>
        <BodyText style={{ fontFamily: 'PixelifySans_700Bold', fontSize: 16, flex: 1 }}>
          Hats
        </BodyText>
        <BodyText style={{ fontSize: 12 }}>
          {p.owned_hats.length} / {hats.length} owned
        </BodyText>
      </View>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 12 }}>
        {hats.map((h) => {
          const owned = p.owned_hats.includes(h.id);
          const equipped = p.hat === h.id;
          const short = h.cost - p.grass;
          return (
            <CozyPanel
              key={h.id}
              style={{
                padding: 10,
                gap: 8,
                alignItems: 'center',
                flexGrow: 1,
                flexBasis: '40%',
                borderColor: equipped ? c.moss : undefined,
              }}
            >
              {owned && (
                <BodyText
                  style={{
                    position: 'absolute',
                    top: 8,
                    right: 8,
                    fontSize: 10,
                    paddingHorizontal: 6,
                    borderRadius: 0,
                    overflow: 'hidden',
                    backgroundColor: equipped ? c.moss : c.body,
                    color: equipped ? c.paper : c.ink,
                  }}
                >
                  {equipped ? 'WEARING' : 'OWNED'}
                </BodyText>
              )}
              <GuardianPet player={p} hat={h.id} size={80} bob={false} />
              <BodyText
                style={{
                  fontFamily: 'PixelifySans_700Bold',
                  minHeight: 40,
                  textAlign: 'center',
                  textAlignVertical: 'center',
                }}
              >
                {h.id}
              </BodyText>
              <View style={{ alignSelf: 'stretch' }}>
                <PixelButton
                  small
                  light={!equipped && (owned || short > 0)}
                  label={
                    paused
                      ? 'TAKE A BREAK'
                      : equipped
                        ? 'TAKE OFF'
                        : owned
                          ? 'WEAR'
                          : short > 0
                            ? `NEED ${short} MORE`
                            : `${h.cost} GRASS`
                  }
                  disabled={paused || (!owned && short > 0)}
                  onDisabledPress={() => {
                    if (!paused) setMerchant('a few more GRASS for this one.');
                    feedback('error');
                  }}
                  onPress={() => {
                    useGame.getState().hatAction(h.id);
                    setMerchant(
                      equipped
                        ? 'bare-headed. bold.'
                        : owned
                          ? 'back in style.'
                          : 'fine choice. very hat.',
                    );
                  }}
                />
              </View>
            </CozyPanel>
          );
        })}
      </View>
    </Page>
  );
}
function RivalRow({
  p: account,
  me,
  rank,
  raiding,
  onRaid,
}: {
  p: Player;
  me: boolean;
  rank: number;
  raiding: string | null;
  onRaid: (p: Player) => void;
}) {
  const p = guardianPlayer(account);
  const now = useGame((s) => s.now);
  const paused = usePlayPaused();
  const raids = useGame((s) => s.rules.days[dayKey(s.now)]?.raids ?? 0);
  const mySpecies = useGame((s) => (s.player ? guardianPlayer(s.player).species : undefined));
  const type = mySpecies ? matchup(mySpecies, p.species) : 1;
  const exposed = status(p, now).kind === 'exposed';
  return (
    <CozyPanel style={{ padding: 16, gap: 12 }}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
        <BodyText style={{ fontFamily: 'PixelifySans_700Bold' }}>#{rank}</BodyText>
        <Pet
          species={p.species}
          visitor={p.guardian}
          level={p.level}
          hat={p.hat}
          size={64}
          bob={false}
        />
        <View style={{ flex: 1, gap: 4 }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
            <BodyText
              numberOfLines={1}
              style={{ flexShrink: 1, fontFamily: 'PixelifySans_700Bold' }}
            >
              {me ? 'YOU' : p.name}
            </BodyText>
            {!me && type > 1 && <PixelIcon name="arrowUp" size={16} />}
            {!me && type < 1 && <PixelIcon name="arrowDown" size={16} />}
          </View>
          <BodyText style={{ fontSize: 12 }}>
            {isVisitorId(p.guardian) ? visitorInfo(p.guardian).name : grasslings[p.species].name} ·{' '}
            {grasslings[p.species].habit}
          </BodyText>
          <BodyText style={{ fontSize: 12 }}>
            LV {p.level} · {p.grass} GRASS
          </BodyText>
        </View>
      </View>
      <StatusChip player={p} compact />
      <BodyText style={{ fontSize: 12 }}>
        {p.offline_seconds} OFFLINE MIN
        {!me && now - p.last_seen > 10000
          ? ` · seen ${Math.floor((now - p.last_seen) / 1000)} MIN ago`
          : ''}
      </BodyText>
      {!me && type !== 1 && (
        <BodyText style={{ fontSize: 12 }}>
          {type > 1 && mySpecies
            ? grasslings[mySpecies].advantage
            : grasslings[p.species].advantage}
        </BodyText>
      )}
      {!me && exposed && (
        <PixelButton
          label={
            raiding === p.id
              ? 'CHECKING…'
              : !backendConfigured
                ? 'ONLINE PLAY UNAVAILABLE'
                : paused
                  ? 'TAKE A BREAK'
                  : raids >= 3
                    ? 'NO RAIDS LEFT'
                    : 'RAID'
          }
          small
          danger
          disabled={!backendConfigured || !!raiding || paused || raids >= 3}
          onPress={() => onRaid(p)}
        />
      )}
      {!me && backendConfigured && <TogetherInvite rival={p} />}
    </CozyPanel>
  );
}
export function ArenaScreen() {
  const params = useLocalSearchParams<{ ring?: string }>();
  const ring = rings.find((r) => r.region === params.ring);
  const insets = useSafeAreaInsets();
  const reduced = useReducedMotion();
  const listRef = useRef<FlatList<Player>>(null);
  const rivalCodeRef = useRef<TextInput>(null);
  const focused = useIsFocused();
  const paused = usePlayPaused();
  const raids = useGame((s) => s.rules.days[dayKey(s.now)]?.raids ?? 0);
  const wins = useGame((s) => s.rules.days[dayKey(s.now)]?.sparringWins ?? 0);
  const p = useGame((s) => s.player);
  const rivals = useGame((s) => s.rivals);
  const live = useGame((s) => s.live);
  const [code, setCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [raiding, setRaiding] = useState<string | null>(null);
  if (!p) return null;
  const ownCode = code.trim().toUpperCase() === p.code;
  const validCode = /^[A-Z0-9]{4}$/.test(code.trim().toUpperCase());
  const canPair = backendConfigured && validCode && !ownCode && !pending;
  const ranked = [p, ...rivals].sort(
    (a, b) => b.offline_seconds - a.offline_seconds || a.name.localeCompare(b.name),
  );
  async function pair() {
    if (!canPair) return;
    setPending(true);
    setError(null);
    const result = await useGame.getState().pair(code);
    setPending(false);
    if (result) {
      setError(result);
      feedback('error');
    } else setCode('');
  }
  async function raid(target: Player) {
    setRaiding(target.id);
    await useGame.getState().startBattle(target);
    setRaiding(null);
  }
  const practicePanel = (
    <View style={{ marginTop: backendConfigured ? 24 : 0, gap: 12 }}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
        <PixelIcon name="arena" size={32} />
        <BodyText style={{ fontSize: 16, fontFamily: 'PixelifySans_700Bold' }}>Sparring</BodyText>
      </View>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
        <Pet dave level={p.level} size={96} bob={false} />
        <View style={{ flex: 1 }}>
          <BodyText style={{ fontFamily: 'PixelifySans_700Bold' }}>DOOMSCROLL DAVE</BodyText>
          <BodyText>LV {p.level} · MOOD 50</BodyText>
        </View>
      </View>
      {wins >= 3 && <BodyText>Dave is tired. Come back tomorrow.</BodyText>}
      <PixelButton
        label={paused ? 'TAKE A BREAK' : wins >= 3 ? 'SPAR · NO GRASS' : 'SPAR WITH DAVE'}
        disabled={paused}
        onPress={() => {
          // the spar happens where you are: a region's ring shows that region behind it
          useUi.setState({ battlePlace: ring?.region ?? null });
          void useGame.getState().startBattle(bot(p), true);
        }}
      />
      <PixelButton
        label="SIMULATE INCOMING RAID"
        light
        onPress={() => useGame.getState().incomingBot()}
      />
    </View>
  );
  const header = (
    <View style={{ gap: 12 }}>
      <PlayPause />
      <PixelText style={{ fontSize: 20 }}>{'A FRIENDLY\nSPAR.'}</PixelText>
      <BodyText style={{ fontSize: 12 }}>
        {backendConfigured ? `RAIDS LEFT TODAY: ${Math.max(0, 3 - raids)}` : 'PRACTICE ARENA'}
      </BodyText>
      {/* the ring is a place: the one you walked to, or the town's */}
      <PixelFrame tone="leaf" style={{ padding: 4 }}>
        <WorldWindow
          region={ring?.region ?? 'valley'}
          at={regionPoint(ring ?? missionPlaces.arena)}
          height={160}
        />
      </PixelFrame>
      {!ring && (
        <PixelButton
          small
          light
          label="WALK TO THE RING"
          onPress={() => {
            // walk out of the gate to the town's ring yourself (free, grants nothing)
            router.push({ pathname: '/world', params: { place: 'arena' } });
          }}
        />
      )}
      {backendConfigured && <GardenTip id="arena" eligible={focused} />}
      {!backendConfigured && (
        <BodyText style={{ fontSize: 12 }}>
          Practice with Dave here. Pairing, player raids and Together naps are unavailable in this
          local build.
        </BodyText>
      )}
      {!backendConfigured && practicePanel}
      {backendConfigured && (
        <CozyPanel style={{ padding: 16, gap: 12 }}>
          <FriendCode code={p.code} />
          <BodyText>Add rival</BodyText>
          <PixelInput
            ref={rivalCodeRef}
            accessibilityLabel="Rival code"
            value={code}
            onChangeText={(text) => {
              setCode(
                text
                  .trim()
                  .toUpperCase()
                  .replace(/[^A-Z0-9]/g, ''),
              );
              setError(null);
            }}
            autoCapitalize="characters"
            autoCorrect={false}
            maxLength={4}
            placeholder="ABCD"
            placeholderTextColor={c.shade}
            returnKeyType="done"
            onSubmitEditing={() => {
              if (canPair) void pair();
            }}
          />
          <PixelButton
            label={pending ? 'PAIRING…' : !validCode ? 'ENTER A 4-CHARACTER CODE' : 'PAIR'}
            disabled={!canPair}
            onPress={() => void pair()}
          />
          {ownCode && (
            <BodyText accessibilityLiveRegion="polite" style={{ fontSize: 12 }}>
              That’s your code. Enter a friend’s code to pair.
            </BodyText>
          )}
          {error && (
            <View style={{ gap: 8 }}>
              <Dialogue text={error} />
              <PixelButton
                small
                light
                label="TRY AGAIN"
                disabled={!canPair}
                onPress={() => void pair()}
              />
            </View>
          )}
        </CozyPanel>
      )}
      <BodyText style={{ fontSize: 16, fontFamily: 'PixelifySans_700Bold', marginTop: 12 }}>
        {backendConfigured ? 'Offline league' : 'Your garden'}
      </BodyText>
      {backendConfigured && !live && (
        <PixelButton
          small
          light
          label="RETRY CONNECTION"
          onPress={() => void useGame.getState().sync()}
        />
      )}
      {backendConfigured && !rivals.length && (
        <View style={{ alignItems: 'center', gap: 12, paddingVertical: 12 }}>
          <GuardianPet player={p} size={64} />
          <BodyText style={{ textAlign: 'center' }}>
            Swap codes with a friend and add their code above. Once paired, use their invite button
            to start a Together nap.
          </BodyText>
          {backendConfigured && (
            <PixelButton
              small
              light
              label="ADD A RIVAL"
              onPress={() => {
                setError(null);
                listRef.current?.scrollToOffset({ offset: 0, animated: !reduced });
                requestAnimationFrame(() => rivalCodeRef.current?.focus());
              }}
            />
          )}
        </View>
      )}
    </View>
  );
  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <CozyBackground />
      <FlatList
        ref={listRef}
        data={ranked}
        keyExtractor={(item) => item.id}
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={{
          padding: gameLayout.gutter,
          paddingTop: hudClearance(insets.top),
          paddingBottom: hotbarClearance(insets.bottom),
          gap: 12,
          ...gameColumn,
        }}
        ListHeaderComponent={header}
        ListFooterComponent={backendConfigured ? practicePanel : null}
        renderItem={({ item, index }) => (
          <RivalRow
            p={item}
            me={item.id === p.id}
            rank={index + 1}
            raiding={raiding}
            onRaid={(target) => void raid(target)}
          />
        )}
      />
    </KeyboardAvoidingView>
  );
}
