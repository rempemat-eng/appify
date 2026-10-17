import { useEffect, useRef, useState } from 'react';
import {
  FlatList,
  KeyboardAvoidingView,
  Platform,
  TextInput,
  View,
  useWindowDimensions,
} from 'react-native';
import { router, useIsFocused } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ArrowUp, ArrowDown } from 'lucide-react-native';
import { cozy as c } from '@/lib/cozy';
import { artGeometry } from '@/lib/art-direction';
import { backendConfigured } from '@/lib/bilt';
import { gameColumn, gameLayout, hotbarClearance, hudClearance } from '@/lib/layout';
import { useReducedMotion } from '@/lib/motion';
import { useAppActive } from '@/lib/app-active';
import { bot, feedback, hats, missions, status, useGame, type Player } from '@/lib/game';
import { matchup } from '@/lib/battle';
import { grasslings, growthStage, levelPreview } from '@/lib/grasslings';
import { budgetVoice, dayKey } from '@/lib/offline-rules';
import { gardenTips, type GardenTipId } from '@/lib/first-session';
import { guardianPlayer, isVisitorId, visitorInfo } from '@/lib/visitors';
import { FriendCode } from '@/components/friend-code';
import { GuardianPet } from '@/components/guardian-pet';
import { GardenVisitor } from '@/components/visitors';
import { GardenTip } from '@/components/garden-guide';
import { Page, Pet, PixelButton, PixelText, StatusChip, styles } from '@/components/game-ui';
import { PixelProp, PixelScene } from '@/components/pixel-scenes';
import { GardenWorld } from '@/components/garden-world';
import { WorldPreview } from '@/components/world-scene';
import { isWorldId } from '@/lib/world-maps';
import { worldCatalogue } from '@/lib/world-catalogue';
import { openSheet, useUi } from '@/lib/ui';
import {
  type BreakIntention,
  type CompanionMemory,
} from '@/lib/companion-memories';
import { BreakIntentionPicker } from '@/components/companion-memories';
import { GardenKeepsakeSheet } from '@/components/garden-keepsakes';
import { gardenMarker } from '@/components/garden-journey';
import { BodyText, Dialogue } from '@/components/pixel-feedback';
import { CozyBackground, CozyPanel } from '@/components/cozy-ui';
import { PixelBurst } from '@/components/cozy-motion';
import {
  PlayPause,
  TogetherInvite,
  usePlayPaused,
} from '@/components/offline-garden';
const lines = {
  grumpy: ['my leaves could use a breather.', 'a quiet pause would be nice. the garden can wait.'],
  exposed: [
    'the garden feels a little open. a nap would put the shield back up.',
    'shall we rest for a bit? i will keep watch.',
  ],
  care: ['a little time to settle in.', 'welcome home. have a look around.'],
  idle: ['the grass is lovely today. you could go and touch some.', 'i am small, but i am very good company.'],
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
  const [intention, setIntention] = useState<BreakIntention | null>(null);
  const { height } = useWindowDimensions();
  const compact = height < 760;
  const p = useGame((s) => s.player);
  if (!p) return null;
  return (
    <Page>
      <PixelText style={{ fontSize: 16 }}>GO TOUCH GRASS</PixelText>
      <BodyText style={{ fontSize: 12, lineHeight: 18 }}>
        Choose a place for your companion and an optional break idea for you. Any idea fits any
        place. Demo time: 1 real second = 1 simulated MIN.
      </BodyText>
      <BreakIntentionPicker
        value={intention}
        onChange={setIntention}
        disabled={p.mode !== 'awake'}
      />
      {missions.map((m) => {
        const locked = p.level < m.level;
        const world = isWorldId(m.id) ? m.id : null;
        return (
          <CozyPanel key={m.id} style={{ padding: 12, gap: 10, opacity: locked ? 0.85 : 1 }}>
            {world && <WorldPreview world={world} player={p} height={compact ? 132 : 176} />}
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <BodyText style={{ fontFamily: 'PixelifySans_700Bold', fontSize: 16, flex: 1 }}>
                {m.name}
              </BodyText>
              <BodyText
                style={{
                  fontFamily: 'PixelifySans_700Bold',
                  fontSize: 12,
                  paddingHorizontal: 8,
                  paddingVertical: 2,
                  borderRadius: artGeometry.tagRadius,
                  overflow: 'hidden',
                  backgroundColor: c.rest,
                }}
              >
                {m.duration} MIN
              </BodyText>
            </View>
            <BodyText style={{ fontSize: 12, lineHeight: 18 }}>
              {world ? worldCatalogue[world].description : 'A little room for time away.'}
            </BodyText>
            <BodyText style={{ fontSize: 12, color: c.shade }}>
              About {m.duration} seconds in this demo
            </BodyText>
            <BodyText style={{ fontSize: 12 }}>
              {m.reward} GRASS · +1 {m.id === 'mountain' ? 'EPIC' : 'RARE'} card · postcard
              {m.id === 'mountain' ? ' · new hat (or +50 GRASS if you own them all)' : ''}
            </BodyText>
            <PixelButton
              small
              light
              label={
                locked
                  ? `LEVEL ${m.level} NEEDED`
                  : p.mode !== 'awake'
                    ? 'ON A BREAK'
                    : `START ${m.name}`
              }
              disabled={locked || p.mode !== 'awake'}
              onPress={() => {
                useGame.getState().sleep(m.id, intention);
                if (useGame.getState().player?.mode === 'mission') setIntention(null);
              }}
            />
          </CozyPanel>
        );
      })}
      <BodyText style={{ fontSize: 12, textAlign: 'center' }}>
        Finish for the mission rewards shown above. Returning early keeps any common-card earnings,
        but gives no mission completion reward.
      </BodyText>
    </Page>
  );
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
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
        <PixelScene kind="market" mini height={80} style={{ width: 96 }} />
        <View style={{ flex: 1 }}>
          <BodyText style={{ fontFamily: 'PixelifySans_700Bold' }}>Moss the merchant</BodyText>
          <BodyText style={{ fontSize: 12 }}>{merchant}</BodyText>
        </View>
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
                    borderRadius: artGeometry.tagRadius,
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
            {!me && type > 1 && <ArrowUp size={14} color={c.moss} />}
            {!me && type < 1 && <ArrowDown size={14} color={c.error} />}
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
        <PixelProp kind="swords" size={32} />
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
        onPress={() => void useGame.getState().startBattle(bot(p), true)}
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
      <PixelText style={{ fontSize: 20 }}>{'LESS SCROLL.\nMORE GLORY.'}</PixelText>
      <BodyText style={{ fontSize: 12 }}>
        {backendConfigured ? `RAIDS LEFT TODAY: ${Math.max(0, 3 - raids)}` : 'PRACTICE ARENA'}
      </BodyText>
      <PixelScene kind="town" height={160} />
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
          <TextInput
            ref={rivalCodeRef}
            accessibilityLabel="Rival code"
            style={styles.input}
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
