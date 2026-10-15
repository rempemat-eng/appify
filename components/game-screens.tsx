import { useReducedMotion } from '@/lib/motion';
import { useEffect, useState } from 'react';
import {
  FlatList,
  KeyboardAvoidingView,
  Platform,
  TextInput,
  View,
  useWindowDimensions,
} from 'react-native';
import { router, useIsFocused } from 'expo-router';
import { collectionOf, guardianPlayer, isVisitorId, visitorInfo } from '@/lib/visitors';
import { GardenVisitor, GuardianPicker } from '@/components/visitors';
import { GardenTip } from '@/components/garden-guide';
import { ArrowUp, ArrowDown, Bot } from 'lucide-react-native';
import Animated, { FadeIn, FadeOut } from 'react-native-reanimated';
import {
  bot,
  feedback,
  hats,
  missions,
  palette as c,
  status,
  useGame,
  type Player,
} from '@/lib/game';
import { matchup } from '@/lib/battle';
import { grasslings, growthStage, levelPreview } from '@/lib/grasslings';
import { Meter, Page, Pet, PixelButton, PixelText, StatusChip, styles } from '@/components/game-ui';
import { PixelProp, PixelScene } from '@/components/pixel-scenes';
import { BodyText, Dialogue } from '@/components/pixel-feedback';
import {
  GardenProgress,
  GardenStreak,
  PlayPause,
  TogetherInvite,
  usePlayPaused,
} from '@/components/offline-garden';
import { budgetVoice, dayKey } from '@/lib/offline-rules';
const lines = {
  grumpy: ['i hate it here. put the phone down.', 'my pixels hurt.'],
  exposed: ["we're exposed. i can hear the notifications.", 'put the phone down. trust me.'],
  care: ['quick, tend the plot.', 'the clock is ticking, gardener.'],
  idle: ["touch grass? i'll wait.", 'i am small but i am mighty'],
};
export function HomeScreen() {
  const reduced = useReducedMotion();
  const { height } = useWindowDimensions();
  const p = useGame((s) => s.player);
  const now = useGame((s) => s.now);
  const voice = useGame((s) => s.voice);
  const firstWake = useGame((s) => s.firstWake);
  const homeTipActive = useGame((s) => s.homeTipActive);
  const paused = usePlayPaused();
  const [crumbs, setCrumbs] = useState(false);
  const [line, setLine] = useState(0);
  const raidId = useGame((s) => s.alerts[0]?.raid.id);
  const [raidFeedback, setRaidFeedback] = useState({ raidId, slumped: Boolean(raidId) });
  if (raidFeedback.raidId !== raidId) {
    setRaidFeedback({ raidId, slumped: raidId ? true : raidFeedback.slumped });
  }
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
    const timer = setTimeout(() => setCrumbs(false), 1000);
    return () => clearTimeout(timer);
  }, [crumbs]);
  if (!p) return null;
  const guardian = guardianPlayer(p);
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
    <Page style={{ gap: 12, padding: 16 }}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <PixelText style={{ fontSize: 16 }}>YOUR GARDEN</PixelText>
        <View
          style={{ borderWidth: 2, borderColor: c.ink, paddingHorizontal: 6, paddingVertical: 3 }}
        >
          <PixelText>LV {p.level}</PixelText>
        </View>
      </View>
      <PixelScene
        species={p.species}
        level={p.level}
        player={p}
        height={height <= 700 ? 176 : 260}
        style={{ alignItems: 'center', justifyContent: 'flex-end', paddingBottom: 12 }}
      >
        <Pet
          species={guardian.species}
          visitor={guardian.guardian}
          level={p.level}
          hat={p.hat}
          grumpy={p.mood < 30}
          size={height <= 700 ? 128 : 192}
          yawning={paused}
          slumped={raidFeedback.slumped}
        />
        {crumbs && (
          <Animated.View
            entering={reduced ? undefined : FadeIn}
            exiting={reduced ? undefined : FadeOut}
            style={{ position: 'absolute', top: 100, flexDirection: 'row', gap: 25 }}
          >
            {[0, 1, 2, 3].map((n) => (
              <View
                key={n}
                style={{ width: 7, height: 7, backgroundColor: c.ink, marginTop: (n % 2) * 15 }}
              />
            ))}
          </Animated.View>
        )}
        <PixelText style={{ fontSize: 15, marginTop: 8, backgroundColor: c.paper, padding: 6 }}>
          {guardian.pet_name}
        </PixelText>
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
      <View style={{ gap: 9 }}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
          <PixelText>MOOD{p.mood < 30 ? ' · GRUMPY' : ''}</PixelText>
          <PixelText>{p.mood}/100</PixelText>
        </View>
        <Meter value={p.mood} height={18} />
      </View>
      <View style={{ zIndex: 20 }}>
        <GardenTip id="phone" eligible={!firstWake && p.mode === 'awake'} floating />
        <PixelButton
          label="PUT PHONE DOWN"
          supportingText="simulated break · 1 second = 1 offline MIN"
          gold={paused}
          onPress={() => useGame.getState().sleep()}
        />
      </View>
      <GardenProgress />
      <GuardianPicker player={p} />
      <View style={{ flexDirection: 'row', gap: 8 }}>
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
            label="FEED · 5 GRASS"
            small
            light
            disabled={paused || p.mood >= 100 || p.grass < 5}
            onPress={() => {
              useGame.getState().feed();
              setCrumbs(true);
            }}
          />
        </View>
      </View>
      <PixelButton label="FIELD JOURNAL" light small onPress={() => router.push('/journal')} />
      {!homeTipActive && <Dialogue text={speech} />}
      <BodyText>
        {isVisitorId(guardian.guardian)
          ? visitorInfo(guardian.guardian).name
          : grasslings[p.species].name}{' '}
        · {grasslings[guardian.species].habit} · {growthStage(p.level)}
      </BodyText>
      <GardenStreak />
      <BodyText style={{ textAlign: 'center' }}>{grasslings[p.species].line}</BodyText>
    </Page>
  );
}
export function MissionsScreen() {
  const p = useGame((s) => s.player);
  if (!p) return null;
  return (
    <Page style={{ padding: 12, gap: 8 }}>
      <PixelText style={{ fontSize: 15 }}>GO TOUCH GRASS</PixelText>
      <BodyText style={{ fontFamily: 'Inter_400Regular', fontSize: 12 }}>
        Simulated missions · 1 second = 1 offline MIN
      </BodyText>
      {missions.map((m, index) => {
        const locked = p.level < m.level;
        return (
          <View
            key={m.id}
            style={{
              flexDirection: 'row',
              gap: 10,
              alignItems: 'center',
              borderWidth: 2,
              borderColor: c.ink,
              backgroundColor: c.body,
              padding: 8,
            }}
          >
            <PixelProp kind={(['tree', 'library', 'mountain'] as const)[index]} size={44} />
            <View style={{ flex: 1, gap: 2 }}>
              <BodyText style={{ fontFamily: 'Inter_700Bold', fontSize: 13, lineHeight: 18 }}>
                {m.name}
              </BodyText>
              <BodyText style={{ fontFamily: 'Inter_400Regular', fontSize: 11, lineHeight: 16 }}>
                {m.duration} MIN offline · {m.duration}s demo
              </BodyText>
              <BodyText style={{ fontFamily: 'Inter_500Medium', fontSize: 11, lineHeight: 16 }}>
                {m.reward} GRASS · LV {m.level}
              </BodyText>
              <BodyText style={{ fontFamily: 'Inter_500Medium', fontSize: 11, lineHeight: 16 }}>
                +1 {m.id === 'mountain' ? 'EPIC' : 'RARE'} · postcard
              </BodyText>
              {m.id === 'mountain' && (
                <BodyText style={{ fontFamily: 'Inter_400Regular', fontSize: 11, lineHeight: 16 }}>
                  New hat · all owned: +50 GRASS
                </BodyText>
              )}
            </View>
            <View style={{ width: 68 }}>
              <PixelButton
                small
                light
                label={locked ? 'LV 2' : 'START'}
                disabled={locked || p.mode !== 'awake'}
                onPress={() => useGame.getState().sleep(m.id)}
              />
            </View>
          </View>
        );
      })}
      <BodyText style={{ fontFamily: 'Inter_400Regular', fontSize: 12 }}>
        Common cards stack. Postcards on completion. No per-minute GRASS.
      </BodyText>
    </Page>
  );
}
export function ShopScreen() {
  const paused = usePlayPaused();
  const p = useGame((s) => s.player);
  const [merchant, setMerchant] = useState('put the phone down. browse the hats.');
  if (!p) return null;
  const preview = levelPreview(p.level);
  return (
    <Page style={{ padding: 12, gap: 12 }}>
      <PlayPause />
      <PixelText style={{ fontSize: 15 }}>GROW YOUR GARDEN</PixelText>
      <View style={[styles.border, { padding: 12, gap: 10, backgroundColor: c.body }]}>
        <View
          style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}
        >
          <PixelText style={{ fontSize: 16 }}>LV {p.level}</PixelText>
          <ArrowUp size={24} color={c.ink} />
          <PixelText style={{ fontSize: 16 }}>LV {p.level + 1}</PixelText>
        </View>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
          <Pet species={p.species} level={p.level + 1} size={64} bob={false} />
          <View style={{ flex: 1 }}>
            <BodyText style={{ fontFamily: 'Inter_600SemiBold' }}>
              {p.level < 3
                ? `${growthStage(p.level)} → ${preview.stage}`
                : `${preview.stage} · LV ${preview.next}`}
            </BodyText>
            <BodyText style={{ fontFamily: 'Inter_400Regular' }}>{preview.unlock}</BodyText>
            <BodyText style={{ fontFamily: 'Inter_400Regular', fontSize: 12 }}>
              {p.grass < preview.cost
                ? `Need ${preview.cost - p.grass} more GRASS`
                : 'Ready to grow'}
            </BodyText>
          </View>
        </View>
        <PixelButton
          label={`LEVEL UP · ${50 * p.level} GRASS`}
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
      </View>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
        <PixelScene kind="market" mini height={68} style={{ width: 100 }} />
        <View style={{ flex: 1, gap: 3 }}>
          <BodyText style={{ fontFamily: 'Inter_700Bold' }}>Moss the merchant</BodyText>
          <BodyText style={{ fontFamily: 'Inter_400Regular', fontSize: 12 }}>{merchant}</BodyText>
        </View>
      </View>
      <PixelText style={{ fontSize: 16, marginTop: 4 }}>HATS</PixelText>
      {hats.map((h) => {
        const owned = p.owned_hats.includes(h.id);
        const equipped = p.hat === h.id;
        return (
          <View
            key={h.id}
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              gap: 16,
              paddingVertical: 10,
              borderBottomWidth: 8,
              backgroundColor: c.body,
              paddingHorizontal: 10,
              borderColor: c.shade,
            }}
          >
            <Pet species={p.species} level={p.level} size={96} hat={h.id} bob={false} />
            <View style={{ flex: 1, gap: 12 }}>
              <PixelText style={{ fontSize: 12 }}>{h.id}</PixelText>
              <BodyText style={{ fontFamily: 'Inter_500Medium', fontSize: 12 }}>
                {owned
                  ? equipped
                    ? 'Owned · equipped'
                    : 'Owned'
                  : `${h.cost} GRASS${p.grass < h.cost ? ` · need ${h.cost - p.grass} more` : ''}`}
              </BodyText>
              <PixelButton
                small
                light={!equipped}
                label={
                  equipped ? 'REMOVE' : owned ? 'EQUIP' : p.grass < h.cost ? 'NOT ENOUGH' : 'BUY'
                }
                disabled={paused || (!owned && p.grass < h.cost)}
                onDisabledPress={() => {
                  if (paused) {
                    feedback('error');
                    return;
                  }
                  setMerchant("you can't afford that, doomscroller.");
                  feedback('error');
                }}
                onPress={() => {
                  useGame.getState().hatAction(h.id);
                  setMerchant('fine choice. very hat.');
                }}
              />
            </View>
          </View>
        );
      })}
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
    <View
      style={{
        padding: 14,
        gap: 12,
        backgroundColor: me ? c.body : c.paper,
        borderWidth: 2,
        borderColor: c.ink,
      }}
    >
      <View style={{ flexDirection: 'row', gap: 12, alignItems: 'center' }}>
        <PixelText style={{ fontSize: 14 }}>#{rank}</PixelText>
        <PixelScene
          species={p.species}
          level={p.level}
          mini
          height={100}
          style={{ width: 100, alignItems: 'center', justifyContent: 'flex-end' }}
        >
          <Pet
            species={p.species}
            visitor={p.guardian}
            level={p.level}
            hat={p.hat}
            size={96}
            bob={false}
          />
        </PixelScene>
        <View style={{ flex: 1, gap: 4 }}>
          <View style={{ flexDirection: 'row', gap: 5, alignItems: 'center' }}>
            <PixelText numberOfLines={1} style={{ flexShrink: 1 }}>
              {me ? 'YOU' : p.name}
            </PixelText>
            {!me && type > 1 && (
              <ArrowUp
                accessibilityLabel={`Habit advantage: ${mySpecies ? grasslings[mySpecies].habit : ''} beats ${grasslings[p.species].habit}`}
                size={14}
                color={c.moss}
              />
            )}
            {!me && type < 1 && (
              <ArrowDown
                accessibilityLabel={`Habit disadvantage against ${grasslings[p.species].habit}`}
                size={14}
                color={c.error}
              />
            )}
          </View>
          <BodyText>
            {isVisitorId(p.guardian) ? visitorInfo(p.guardian).name : grasslings[p.species].name} ·{' '}
            {grasslings[p.species].habit}
          </BodyText>
          {!me && type !== 1 && (
            <BodyText>
              {type > 1 && mySpecies
                ? grasslings[mySpecies].advantage
                : grasslings[p.species].advantage}
            </BodyText>
          )}
          <PixelText>
            LV {p.level} · {p.grass} GRASS
          </PixelText>
        </View>
      </View>
      <View style={{ gap: 8 }}>
        <StatusChip player={p} compact />
        <PixelText>{p.offline_seconds} OFFLINE MIN</PixelText>
        {!me && now - p.last_seen > 10000 && (
          <PixelText>LAST SEEN {Math.floor((now - p.last_seen) / 1000)} MIN AGO</PixelText>
        )}
      </View>
      {!me && exposed && (
        <PixelButton
          label={raiding === p.id ? 'CHECKING...' : 'RAID'}
          danger
          small
          disabled={!!raiding || paused || raids >= 3}
          onPress={() => onRaid(p)}
        />
      )}
      {!me && <TogetherInvite rival={p} />}
    </View>
  );
}
export function ArenaScreen() {
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
  const ranked = [p, ...rivals].sort(
    (a, b) => b.offline_seconds - a.offline_seconds || a.name.localeCompare(b.name),
  );
  async function pair() {
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
    <View style={{ gap: 24 }}>
      <PlayPause />
      <PixelText>RAIDS LEFT TODAY: {Math.max(0, 3 - raids)}</PixelText>
      <PixelText style={styles.title}>{'LESS SCROLL.\nMORE GLORY.'}</PixelText>
      <PixelScene kind="town" height={160} />
      <GardenTip id="arena" eligible={focused} />
      <View style={[styles.border, { padding: 16, gap: 16, backgroundColor: c.body }]}>
        <PixelText>YOUR CODE: {p.code}</PixelText>
        <PixelText>ADD RIVAL</PixelText>
        <TextInput
          accessibilityLabel="Rival code"
          style={styles.input}
          value={code}
          onChangeText={(text) => setCode(text.toUpperCase().replace(/[^A-Z0-9]/g, ''))}
          autoCapitalize="characters"
          autoCorrect={false}
          maxLength={4}
          placeholder="ABCD"
          placeholderTextColor={c.shade}
          returnKeyType="done"
          onSubmitEditing={() => {
            if (code.length === 4 && !pending) void pair();
          }}
        />
        <PixelButton
          label={pending ? 'PAIRING...' : 'PAIR'}
          disabled={pending || code.length !== 4}
          onPress={() => void pair()}
        />
        {error && (
          <View style={{ gap: 8 }}>
            <Dialogue text={error} />
            <PixelButton
              small
              light
              label="TRY AGAIN"
              disabled={pending}
              onPress={() => void pair()}
            />
          </View>
        )}
      </View>
      <PixelText style={{ fontSize: 16 }}>OFFLINE LEAGUE</PixelText>
      {!live && (
        <PixelButton
          label="RETRY CONNECTION"
          small
          light
          onPress={() => void useGame.getState().sync()}
        />
      )}
      {!rivals.length && (
        <View style={{ alignItems: 'center', gap: 14, paddingVertical: 12 }}>
          <Pet species={p.species} level={p.level} hat={p.hat} size={64} />
          <BodyText
            style={{ textAlign: 'center' }}
          >{`it's quiet here. share my code: ${p.code}`}</BodyText>
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
    <View style={{ marginTop: 28, gap: 18 }}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
        <Bot color={c.ink} size={26} />
        <PixelText style={{ fontSize: 16 }}>SPARRING</PixelText>
      </View>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
        <Pet dave level={p.level} size={96} bob={false} />
        <View style={{ flex: 1, gap: 4 }}>
          <PixelText>DOOMSCROLL DAVE</PixelText>
          <PixelText>LV {p.level} · MOOD 50</PixelText>
        </View>
      </View>
      {wins >= 3 && (
        <PixelText style={{ lineHeight: 22 }}>DAVE IS TIRED. COME BACK TOMORROW.</PixelText>
      )}
      <PixelButton
        label={wins >= 3 ? 'SPAR · NO GRASS' : 'SPAR WITH DAVE'}
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
      style={{ flex: 1, backgroundColor: c.paper }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <FlatList
        data={ranked}
        keyExtractor={(item) => item.id}
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={{
          padding: 20,
          paddingBottom: 36,
          gap: 16,
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
