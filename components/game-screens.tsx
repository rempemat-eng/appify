import { useEffect, useState } from 'react';
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
import { useReducedMotion } from '@/lib/motion';
import { bot, feedback, hats, missions, status, useGame, type Player } from '@/lib/game';
import { matchup } from '@/lib/battle';
import { petPixels } from '@/lib/pet-art';
import { visitorPixels } from '@/lib/visitor-art';
import { grasslings, growthStage, levelPreview } from '@/lib/grasslings';
import { budgetVoice, dayKey } from '@/lib/offline-rules';
import { gardenTips, type GardenTipId } from '@/lib/first-session';
import { collectionOf, guardianPlayer, isVisitorId, visitorInfo } from '@/lib/visitors';
import { FriendCode } from '@/components/friend-code';
import { GardenVisitor, GuardianPicker } from '@/components/visitors';
import { GardenTip } from '@/components/garden-guide';
import { Meter, Page, Pet, PixelButton, PixelText, StatusChip, styles } from '@/components/game-ui';
import { PixelScene } from '@/components/pixel-scenes';
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
  grumpy: ['i hate it here. put the phone down.', 'my pixels hurt.'],
  exposed: ["we're exposed. i can hear the notifications.", 'put the phone down. trust me.'],
  care: ['quick, tend the plot.', 'the clock is ticking, gardener.'],
  idle: ["touch grass? i'll wait.", 'i am small but i am mighty'],
};
export function HomeScreen() {
  const reduced = useReducedMotion();
  const { height, width } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const p = useGame((s) => s.player);
  const now = useGame((s) => s.now);
  const voice = useGame((s) => s.voice);
  const firstWake = useGame((s) => s.firstWake);
  const tips = useGame((s) => s.tips);
  const paused = usePlayPaused();
  const busy = useGame((s) =>
    Boolean(
      s.message || s.battle || s.cardReward || s.deckOpen || s.recap || s.alerts.length || s.flash,
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
  const [petTop, setPetTop] = useState(40);
  const [statsOpen, setStatsOpen] = useState(false);
  const [crumbs, setCrumbs] = useState(false);
  const [line, setLine] = useState(0);
  const raidId = useGame((s) => s.alerts[0]?.raid.id);
  const [raidFeedback, setRaidFeedback] = useState({ raidId, slumped: Boolean(raidId) });
  if (raidFeedback.raidId !== raidId)
    setRaidFeedback({ raidId, slumped: raidId ? true : raidFeedback.slumped });
  useEffect(() => {
    if (!raidId) return undefined;
    const timer = setTimeout(() => setRaidFeedback({ raidId, slumped: false }), 10000);
    return () => clearTimeout(timer);
  }, [raidId]);
  useEffect(() => {
    if (reduced) return undefined;
    const timer = setInterval(() => {
      setLine((n) => n + 1);
      useGame.setState({ voice: null });
    }, 6000);
    return () => clearInterval(timer);
  }, [reduced]);
  useEffect(() => {
    if (!crumbs) return undefined;
    const timer = setTimeout(() => setCrumbs(false), 600);
    return () => clearTimeout(timer);
  }, [crumbs]);
  if (!p) return null;
  const guardian = guardianPlayer(p);
  const homePixels = isVisitorId(guardian.guardian)
    ? visitorPixels(guardian.guardian, p.hat)
    : petPixels(guardian.species, p.level, p.hat, false, p.mood < 30);
  const rainCloudBottom = petTop + Math.min(...homePixels.map((pixel) => pixel.y)) * 4 - 12;
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
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <PixelText style={{ fontSize: 16 }}>YOUR GARDEN</PixelText>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Open garden stats"
          onPress={() => setStatsOpen(true)}
          style={{
            minHeight: 44,
            paddingHorizontal: 12,
            justifyContent: 'center',
            borderRadius: 999,
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
      <PixelScene
        species={p.species}
        level={p.level}
        player={p}
        rainCloudBottom={rainCloudBottom}
        height={Math.max(240, Math.round(Math.min(width, 640) * 0.55))}
        style={{
          marginHorizontal: -16,
          borderWidth: 0,
          borderTopLeftRadius: 0,
          borderTopRightRadius: 0,
          borderBottomLeftRadius: 24,
          borderBottomRightRadius: 24,
          alignItems: 'center',
          justifyContent: 'flex-end',
          paddingBottom: 16,
        }}
      >
        <View onLayout={(event) => setPetTop(event.nativeEvent.layout.y)}>
          <Pet
            species={guardian.species}
            visitor={guardian.guardian}
            level={p.level}
            hat={p.hat}
            grumpy={p.mood < 30}
            size={128}
            yawning={paused}
            slumped={raidFeedback.slumped}
          />
        </View>
        {crumbs && <PixelBurst />}
        <BodyText
          style={{
            backgroundColor: c.glass,
            paddingHorizontal: 12,
            paddingVertical: 4,
            borderRadius: 999,
            fontFamily: 'Nunito_800ExtraBold',
          }}
        >
          {guardian.pet_name}
        </BodyText>
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
            marginTop: 4,
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
        <View style={{ position: 'absolute', left: 4, bottom: 4, flexDirection: 'row' }}>
          {collectionOf(p)
            .filter((v) => v.befriendedAt !== null && v.id !== p.guardian)
            .slice(0, 3)
            .map((v) => (
              <Pet key={v.id} visitor={v.id} size={32} bob={false} />
            ))}
        </View>
        <GardenVisitor />
      </PixelScene>
      <GardenProgress />
      <View style={{ gap: 6 }}>
        <PixelButton label="TAKE A NAP" gold={paused} onPress={() => useGame.getState().sleep()} />
        <BodyText style={{ textAlign: 'center', fontSize: 12 }}>
          put your phone down · simulated
        </BodyText>
      </View>
      <View style={{ flexDirection: 'row', gap: 12 }}>
        <View style={{ flex: 1 }}>
          <PixelButton
            label="MY DECK"
            small
            light
            onPress={() => useGame.setState({ deckOpen: true })}
          />
        </View>
        <View style={{ flex: 1 }}>
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
        <View style={{ flex: 1 }}>
          <PixelButton label="JOURNAL" small light onPress={() => router.push('/journal')} />
        </View>
      </View>
      <GuardianPicker player={p} />
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
            style={{ padding: 16, gap: 12, width: '100%', maxWidth: 608, alignSelf: 'center' }}
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
  const p = useGame((s) => s.player);
  if (!p) return null;
  return (
    <Page>
      <PixelText style={{ fontSize: 16 }}>GO TOUCH GRASS</PixelText>
      {missions.map((m, index) => {
        const locked = p.level < m.level;
        return (
          <CozyPanel key={m.id} style={{ padding: 12, gap: 10, opacity: locked ? 0.85 : 1 }}>
            <PixelScene
              mini
              kind={(['park', 'book', 'mountain'] as const)[index]}
              species={p.species}
              level={p.level}
              height={120}
              groundInset={18}
              style={{ alignItems: 'center', justifyContent: 'flex-end', paddingBottom: 4 }}
            >
              <Pet species={p.species} level={p.level} hat={p.hat} size={56} bob={false} />
            </PixelScene>
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
            <BodyText style={{ fontSize: 12 }}>
              {m.reward} GRASS · +1 {m.id === 'mountain' ? 'EPIC' : 'RARE'} card · postcard
              {m.id === 'mountain' ? ' · new hat (or +50 GRASS if you own them all)' : ''}
            </BodyText>
            <PixelButton
              small
              light
              label={
                locked ? `LEVEL ${m.level} NEEDED` : p.mode !== 'awake' ? 'ON A BREAK' : 'START'
              }
              disabled={locked || p.mode !== 'awake'}
              onPress={() => useGame.getState().sleep(m.id)}
            />
          </CozyPanel>
        );
      })}
      <BodyText style={{ fontSize: 12, textAlign: 'center' }}>
        start a mission, put your phone down, and your Grassling comes back with rewards.
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
          <Pet species={p.species} level={p.level + 1} size={96} bob={false} />
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
              <Pet species={p.species} level={p.level} hat={h.id} size={80} bob={false} />
              <BodyText style={{ fontFamily: 'Nunito_800ExtraBold' }}>{h.id}</BodyText>
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
              : paused
                ? 'TAKE A BREAK'
                : raids >= 3
                  ? 'NO RAIDS LEFT'
                  : 'RAID'
          }
          small
          danger
          disabled={!!raiding || paused || raids >= 3}
          onPress={() => onRaid(p)}
        />
      )}
      {!me && <TogetherInvite rival={p} />}
    </CozyPanel>
  );
}
export function ArenaScreen() {
  const insets = useSafeAreaInsets();
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
  const canPair = validCode && !ownCode && !pending;
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
  const header = (
    <View style={{ gap: 12 }}>
      <PlayPause />
      <PixelText style={{ fontSize: 20 }}>{'LESS SCROLL.\nMORE GLORY.'}</PixelText>
      <BodyText style={{ fontSize: 12 }}>RAIDS LEFT TODAY: {Math.max(0, 3 - raids)}</BodyText>
      <PixelScene kind="town" height={160} />
      <GardenTip id="arena" eligible={focused} />
      <CozyPanel style={{ padding: 16, gap: 12 }}>
        <FriendCode code={p.code} />
        <BodyText>Add rival</BodyText>
        <TextInput
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
      <BodyText style={{ fontSize: 16, fontFamily: 'Nunito_800ExtraBold', marginTop: 12 }}>
        Offline league
      </BodyText>
      {!live && (
        <PixelButton
          small
          light
          label="RETRY CONNECTION"
          onPress={() => void useGame.getState().sync()}
        />
      )}
      {!rivals.length && (
        <View style={{ alignItems: 'center', gap: 12, paddingVertical: 12 }}>
          <Pet species={p.species} level={p.level} hat={p.hat} size={64} />
          <BodyText style={{ textAlign: 'center' }}>
            Swap codes with a friend and add their code above. Once paired, use their invite button
            to start a Together nap.
          </BodyText>
          <PixelButton
            small
            light
            label="ADD A RIVAL"
            onPress={() => {
              setCode('');
              setError('ENTER THEIR CODE ABOVE.');
            }}
          />
        </View>
      )}
    </View>
  );
  const footer = (
    <View style={{ marginTop: 24, gap: 12 }}>
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
  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <CozyBackground />
      <FlatList
        data={ranked}
        keyExtractor={(item) => item.id}
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={{
          padding: 16,
          paddingBottom: 112 + insets.bottom,
          gap: 12,
          maxWidth: 640,
          width: '100%',
          alignSelf: 'center',
        }}
        ListHeaderComponent={header}
        ListFooterComponent={footer}
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
