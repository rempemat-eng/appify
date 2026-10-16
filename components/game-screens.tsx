import { useEffect, useRef, useState } from 'react';
import {
  FlatList,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  TextInput,
  View,
  useWindowDimensions,
} from 'react-native';
import { router, useIsFocused } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ArrowUp, ArrowDown, Bot, Heart } from 'lucide-react-native';
import { cozy as c } from '@/lib/cozy';
import { backendConfigured } from '@/lib/bilt';
import { dockClearance, gameColumn, gameLayout } from '@/lib/layout';
import { useReducedMotion } from '@/lib/motion';
import { useAppActive } from '@/lib/app-active';
import { bot, feedback, hats, missions, status, useGame, type Player } from '@/lib/game';
import { matchup } from '@/lib/battle';
import { grasslings, growthStage, levelPreview } from '@/lib/grasslings';
import { budgetVoice, dayKey } from '@/lib/offline-rules';
import { gardenTips, type GardenTipId } from '@/lib/first-session';
import { guardianPlayer, isVisitorId, visitorInfo } from '@/lib/visitors';
import { FriendCode } from '@/components/friend-code';
import { DailyRhythmCard } from '@/components/daily-rhythm';
import { GuardianPet } from '@/components/guardian-pet';
import { GardenVisitor, GuardianPicker } from '@/components/visitors';
import { GardenTip } from '@/components/garden-guide';
import { Meter, Page, Pet, PixelButton, PixelText, StatusChip, styles } from '@/components/game-ui';
import { PixelProp, PixelScene } from '@/components/pixel-scenes';
import { GardenWorld } from '@/components/garden-world';
import { WorldPreview } from '@/components/world-scene';
import { useGardenView } from '@/lib/garden-view';
import type { BreakIntention, CompanionMemory } from '@/lib/companion-memories';
import { BreakIntentionPicker } from '@/components/companion-memories';
import { GardenKeepsakeShelf, GardenKeepsakeSheet } from '@/components/garden-keepsakes';
import { GardenJourney } from '@/components/garden-journey';
import { BodyText, Dialogue } from '@/components/pixel-feedback';
import { CozyBackground, CozyPanel, CozySheet } from '@/components/cozy-ui';
import { PixelBurst } from '@/components/cozy-motion';
import {
  GardenProgress,
  GardenStreak,
  RecentBreaks,
  PlayPause,
  TogetherInvite,
  usePlayPaused,
} from '@/components/offline-garden';
const lines = {
  grumpy: ['my leaves could use a breather.', 'a quiet pause would be nice. the garden can wait.'],
  exposed: ["we're exposed. i can hear the notifications.", 'put the phone down. trust me.'],
  care: ['a little time to settle in.', 'welcome home. have a look around.'],
  idle: ["touch grass? i'll wait.", 'i am small but i am mighty'],
};
export function HomeScreen() {
  const [gardenView, setGardenView] = useGardenView();
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
  useEffect(() => {
    if (coaching && p?.mode === 'awake') useGame.getState().seeTip(coaching);
  }, [coaching, p?.mode]);
  const [statsOpen, setStatsOpen] = useState(false);
  const [companionSheet, setCompanionSheet] = useState({ focused, open: false });
  if (companionSheet.focused !== focused) setCompanionSheet({ focused, open: false });
  const companionsOpen = companionSheet.focused === focused && companionSheet.open;
  const setCompanionsOpen = (open: boolean) => setCompanionSheet({ focused, open });
  const [keepsakeSheet, setKeepsakeSheet] = useState<{
    focused: boolean;
    memory: CompanionMemory | null;
  }>({ focused, memory: null });
  if (keepsakeSheet.focused !== focused) setKeepsakeSheet({ focused, memory: null });
  const openMemory = keepsakeSheet.focused === focused ? keepsakeSheet.memory : null;
  const gardenActive =
    focused &&
    appActive &&
    !busy &&
    !statsOpen &&
    !companionsOpen &&
    !openMemory &&
    p?.mode === 'awake';
  const [crumbs, setCrumbs] = useState(false);
  const [line, setLine] = useState(0);
  const raidId = useGame((s) => s.alerts[0]?.raid.id);
  const [raidFeedback, setRaidFeedback] = useState({ raidId, slumped: Boolean(raidId) });
  if (raidFeedback.raidId !== raidId) setRaidFeedback({ raidId, slumped: Boolean(raidId) });
  useEffect(() => {
    if (!raidId) return undefined;
    const timer = setTimeout(() => setRaidFeedback({ raidId, slumped: false }), 10000);
    return () => clearTimeout(timer);
  }, [raidId]);
  useEffect(() => {
    if (reduced || !gardenActive) return undefined;
    const timer = setInterval(() => {
      setLine((n) => n + 1);
    }, 6000);
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
  const guardian = guardianPlayer(p);
  const narrowControls = Math.min(width, gameLayout.maxWidth) < 380;
  const state = status(p, now);
  const speech = paused
    ? budgetVoice
    : (voice ??
      (p.mood < 30
        ? lines.grumpy
        : state.kind === 'exposed'
          ? lines.exposed
          : state.kind === 'care'
            ? lines.care
            : lines.idle)[line % 2]);
  return (
    <Page>
      <View style={{ flexDirection: 'row', gap: 8, alignItems: 'center' }}>
        <View style={{ flex: 1, minWidth: 0, gap: 3 }}>
          <BodyText
            numberOfLines={1}
            style={{ fontSize: 11, lineHeight: 15, fontFamily: 'Nunito_800ExtraBold' }}
          >
            {guardian.pet_name}&apos;s little corner
          </BodyText>
          <PixelText style={{ fontSize: 16, lineHeight: 22 }}>GARDEN</PixelText>
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Take a nap"
          onPress={() => {
            feedback('select');
            useGame.getState().sleep();
          }}
          style={({ pressed }) => ({
            minHeight: 44,
            paddingHorizontal: 12,
            gap: 6,
            flexDirection: 'row',
            alignItems: 'center',
            borderRadius: 14,
            borderWidth: 2,
            borderColor: c.napOutline,
            backgroundColor: c.rest,
            transform: [{ translateY: pressed && !reduced ? 2 : 0 }],
            boxShadow: pressed ? undefined : '0 2px 0 rgba(92,78,131,0.3)',
          })}
        >
          <PixelProp kind="moon" size={16} tint={c.napOutline} />
          <BodyText style={{ fontFamily: 'Nunito_800ExtraBold', fontSize: 12 }}>NAP</BodyText>
        </Pressable>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Open garden stats"
          onPress={() => setStatsOpen(true)}
          style={{
            minHeight: 44,
            paddingHorizontal: 12,
            justifyContent: 'center',
            borderRadius: 14,
            borderWidth: 1,
            borderColor: c.outline,
            backgroundColor: c.paper,
          }}
        >
          <BodyText style={{ fontSize: 12, fontFamily: 'Nunito_800ExtraBold' }}>STATS</BodyText>
        </Pressable>
      </View>
      <View style={{ paddingHorizontal: 8, marginBottom: -8, zIndex: 1 }}>
        <Dialogue
          text={coaching ? gardenTips[coaching].text : speech}
          speech
          onDismiss={coaching ? () => setLesson({ key, id: null }) : undefined}
        />
      </View>
      <View
        style={{
          marginHorizontal: -gameLayout.gutter,
          borderBottomLeftRadius: 24,
          borderBottomRightRadius: 24,
          overflow: 'hidden',
        }}
      >
        <GardenWorld
          active={gardenActive}
          memories={memories}
          view={gardenView}
          width={Math.min(width, gameLayout.maxWidth)}
          player={p}
          grumpy={p.mood < 30}
          sleepy={paused}
          onFeed={() => {
            useGame.getState().feed();
            setCrumbs(true);
          }}
        />
        <GardenVisitor />
        {crumbs && <PixelBurst />}
      </View>
      <View
        style={{
          flexDirection: 'row',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 8,
        }}
      >
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`Change companion, ${guardian.pet_name} is active`}
          onPress={() => setCompanionsOpen(true)}
          style={{
            backgroundColor: c.glass,
            paddingHorizontal: 12,
            minHeight: 44,
            maxWidth: '100%',
            justifyContent: 'center',
            borderRadius: 999,
          }}
        >
          <BodyText
            numberOfLines={1}
            style={{ fontFamily: 'Nunito_800ExtraBold', fontSize: 12, flexShrink: 1 }}
          >
            {guardian.pet_name} · CHANGE
          </BodyText>
        </Pressable>
        <View
          accessibilityRole="progressbar"
          accessibilityLabel={`Mood: ${p.mood < 30 ? 'grumpy' : paused ? 'sleepy' : 'happy'}`}
          accessibilityValue={{ min: 0, max: 100, now: p.mood }}
          style={{
            flexDirection: 'row',
            alignItems: 'center',
            gap: 6,
            backgroundColor: c.glass,
            borderRadius: 999,
            paddingHorizontal: 10,
            paddingVertical: 4,
          }}
        >
          <Heart size={14} strokeWidth={2} color={p.mood < 30 ? c.error : c.ink} />
          <View
            style={{
              width: 48,
              height: 6,
              borderRadius: 3,
              backgroundColor: c.faded,
              overflow: 'hidden',
            }}
          >
            <View
              style={{
                width: `${Math.max(0, Math.min(100, p.mood))}%`,
                height: '100%',
                backgroundColor: p.mood < 30 ? c.error : c.moss,
              }}
            />
          </View>
          <BodyText numberOfLines={1} style={{ fontSize: 11, fontFamily: 'Nunito_800ExtraBold' }}>
            {p.mood < 30 ? 'GRUMPY' : paused ? 'SLEEPY' : 'HAPPY'}
          </BodyText>
        </View>
      </View>
      <BodyText style={{ textAlign: 'center', fontSize: 12, marginTop: -6 }}>
        tap to wander · water the flowers, visit the reading nook or say hello at the pond
      </BodyText>
      <View
        accessibilityRole="radiogroup"
        accessibilityLabel="Garden view"
        style={{ flexDirection: 'row', alignSelf: 'center', gap: 6 }}
      >
        {(
          [
            ['flat', 'TOP-DOWN'],
            ['tilt', '2.5D · BETA'],
          ] as const
        ).map(([mode, label]) => (
          <Pressable
            key={mode}
            accessibilityRole="radio"
            accessibilityState={{ checked: gardenView === mode }}
            aria-checked={gardenView === mode}
            onPress={() => {
              feedback('select');
              setGardenView(mode);
            }}
            style={{
              minHeight: 44,
              paddingHorizontal: 12,
              justifyContent: 'center',
              borderRadius: 999,
              borderWidth: 1,
              borderColor: c.outline,
              backgroundColor: gardenView === mode ? c.rest : c.paper,
            }}
          >
            <BodyText style={{ fontSize: 11, fontFamily: 'Nunito_800ExtraBold' }}>{label}</BodyText>
          </Pressable>
        ))}
      </View>
      <GardenKeepsakeShelf
        memories={memories}
        onOpen={(memory) => setKeepsakeSheet({ focused, memory })}
        onPlan={() => router.push('/missions')}
      />
      <GardenProgress />
      <View style={{ gap: 6 }}>
        <PixelButton label="TAKE A NAP" gold={paused} onPress={() => useGame.getState().sleep()} />
        <BodyText style={{ textAlign: 'center', fontSize: 12 }}>
          put your phone down · simulated
        </BodyText>
      </View>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 10 }}>
        <View style={narrowControls ? { flexGrow: 1, flexBasis: '46%' } : { flex: 1 }}>
          <PixelButton
            label="MY DECK"
            small
            light
            onPress={() => useGame.setState({ deckOpen: true })}
          />
        </View>
        <View style={narrowControls ? { flexGrow: 1, flexBasis: '46%' } : { flex: 1 }}>
          <PixelButton
            label={
              paused
                ? 'TAKE A BREAK'
                : p.mood >= 100
                  ? 'FULL'
                  : p.grass < 5
                    ? 'NEED 5 GRASS'
                    : 'FEED · 5'
            }
            small
            light
            disabled={paused || p.mood >= 100 || p.grass < 5}
            onPress={() => {
              useGame.getState().feed();
              setCrumbs(true);
            }}
          />
        </View>
        <View style={narrowControls ? { flexGrow: 1, flexBasis: '100%' } : { flex: 1 }}>
          <PixelButton label="JOURNAL" small light onPress={() => router.push('/journal')} />
        </View>
      </View>
      <GuardianPicker
        player={p}
        open={companionsOpen}
        onOpenChange={setCompanionsOpen}
        showCard={false}
      />
      <GardenJourney
        player={p}
        onMissions={() => router.push('/missions')}
        onJournal={() => router.push('/journal')}
        onCompanions={() => setCompanionsOpen(true)}
        onSpar={() => router.push('/arena')}
      />
      <DailyRhythmCard />
      <GardenKeepsakeSheet
        memory={openMemory}
        onClose={() => setKeepsakeSheet({ focused, memory: null })}
        onJournal={() => {
          setKeepsakeSheet({ focused, memory: null });
          router.push('/journal?tab=memories');
        }}
      />
      <Modal
        visible={statsOpen}
        transparent
        animationType="none"
        onRequestClose={() => setStatsOpen(false)}
      >
        <View
          style={{
            flex: 1,
            justifyContent: 'flex-end',
            padding: 16,
            paddingBottom: insets.bottom + 16,
            backgroundColor: c.shadow,
          }}
        >
          <CozySheet
            style={{
              padding: gameLayout.gutter,
              gap: 12,
              width: '100%',
              maxWidth: gameLayout.maxWidth - gameLayout.gutter * 2,
              alignSelf: 'center',
            }}
          >
            <PixelText style={{ fontSize: 16 }}>GARDEN STATS</PixelText>
            <ScrollView
              style={{ maxHeight: height * 0.5 }}
              contentContainerStyle={{ gap: 12, paddingBottom: 16 }}
            >
              <BodyText style={{ fontFamily: 'Nunito_800ExtraBold' }}>
                Today ·{' '}
                {new Date(now).toLocaleDateString(undefined, {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                })}
              </BodyText>
              <GardenProgress />
              <BodyText>
                {isVisitorId(guardian.guardian)
                  ? visitorInfo(guardian.guardian).name
                  : grasslings[p.species].name}{' '}
                · {grasslings[guardian.species].habit}
              </BodyText>
              <BodyText>
                Level {p.level} · {growthStage(p.level)}
              </BodyText>
              <BodyText>Mood {p.mood} / 100</BodyText>
              <Meter value={p.mood} />
              <BodyText>Next common card in {15 - (p.offline_seconds % 15)} simulated MIN</BodyText>
              <BodyText>
                Level {levelPreview(p.level).next} · {levelPreview(p.level).cost} GRASS ·{' '}
                {levelPreview(p.level).unlock}
              </BodyText>
              <GardenStreak />
              <RecentBreaks />
            </ScrollView>
            <PixelButton label="DONE" onPress={() => setStatsOpen(false)} />
          </CozySheet>
        </View>
      </Modal>
    </Page>
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
      {missions.map((m, index) => {
        const locked = p.level < m.level;
        return (
          <CozyPanel key={m.id} style={{ padding: 12, gap: 10, opacity: locked ? 0.85 : 1 }}>
            <WorldPreview
              world={(['park', 'book', 'mountain'] as const)[index]}
              player={p}
              height={compact ? 96 : 132}
            />
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <BodyText style={{ fontFamily: 'Nunito_800ExtraBold', fontSize: 16, flex: 1 }}>
                {m.name}
              </BodyText>
              <BodyText
                style={{
                  fontFamily: 'Nunito_800ExtraBold',
                  fontSize: 12,
                  paddingHorizontal: 8,
                  paddingVertical: 2,
                  borderRadius: 999,
                  overflow: 'hidden',
                  backgroundColor: c.rest,
                }}
              >
                {m.duration} MIN
              </BodyText>
            </View>
            <BodyText style={{ fontSize: 12, lineHeight: 18 }}>
              {m.id === 'park'
                ? 'Pond paths, curious neighbours and a little room to wander.'
                : m.id === 'book'
                  ? 'A library lane where your companion can linger over a story.'
                  : 'A quiet ridge above the garden, with a cabin to return to.'}
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
            <BodyText style={{ fontFamily: 'Nunito_800ExtraBold', fontSize: 16 }}>
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
            setMerchant("you can't afford that, doomscroller.");
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
          <BodyText style={{ fontFamily: 'Nunito_800ExtraBold' }}>Moss the merchant</BodyText>
          <BodyText style={{ fontSize: 12 }}>{merchant}</BodyText>
        </View>
      </View>
      <View style={{ flexDirection: 'row', alignItems: 'baseline', marginTop: 12 }}>
        <BodyText style={{ fontFamily: 'Nunito_800ExtraBold', fontSize: 16, flex: 1 }}>
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
                    borderRadius: 999,
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
                  fontFamily: 'Nunito_800ExtraBold',
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
                    if (!paused) setMerchant("you can't afford that, doomscroller.");
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
        <BodyText style={{ fontFamily: 'Nunito_800ExtraBold' }}>#{rank}</BodyText>
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
              style={{ flexShrink: 1, fontFamily: 'Nunito_800ExtraBold' }}
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
        <Bot color={c.ink} size={24} />
        <BodyText style={{ fontSize: 16, fontFamily: 'Nunito_800ExtraBold' }}>Sparring</BodyText>
      </View>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
        <Pet dave level={p.level} size={96} bob={false} />
        <View style={{ flex: 1 }}>
          <BodyText style={{ fontFamily: 'Nunito_800ExtraBold' }}>DOOMSCROLL DAVE</BodyText>
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
      <BodyText style={{ fontSize: 16, fontFamily: 'Nunito_800ExtraBold', marginTop: 12 }}>
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
          paddingBottom: dockClearance(insets.bottom),
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
