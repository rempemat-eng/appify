import { useEffect, useState } from 'react';
import { FlatList, KeyboardAvoidingView, Platform, TextInput, View } from 'react-native';
import { Users, Mountain, BookOpen, Trees, Moon, ArrowUp, Bot } from 'lucide-react-native';
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
import { Meter, Page, Pet, PixelButton, PixelText, StatusChip, styles } from '@/components/game-ui';
const lines = {
  grumpy: ['i hate it here. put the phone down.', 'my pixels hurt.'],
  exposed: ["we're exposed. i can hear the notifications.", 'put the phone down. trust me.'],
  care: ['quick, do your stuff.', 'the clock is ticking, human.'],
  idle: ["touch grass? i'll wait.", 'i am small but i am mighty'],
};
export function HomeScreen() {
  const p = useGame((s) => s.player);
  const now = useGame((s) => s.now);
  const voice = useGame((s) => s.voice);
  const [crumbs, setCrumbs] = useState(false);
  const [line, setLine] = useState(0);
  useEffect(() => {
    const timer = setInterval(() => {
      setLine((n) => n + 1);
      useGame.setState({ voice: null });
    }, 6000);
    return () => clearInterval(timer);
  }, []);
  useEffect(() => {
    if (!crumbs) return undefined;
    const timer = setTimeout(() => setCrumbs(false), 1000);
    return () => clearTimeout(timer);
  }, [crumbs]);
  if (!p) return null;
  const state = status(p, now);
  const speech =
    voice ??
    (p.mood < 30
      ? lines.grumpy
      : state.kind === 'exposed'
        ? lines.exposed
        : state.kind === 'care'
          ? lines.care
          : lines.idle)[line % 2];
  return (
    <Page style={{ gap: 22 }}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <PixelText style={{ fontSize: 16 }}>SCREENAGOTCHI</PixelText>
        <View
          style={{ borderWidth: 2, borderColor: c.ink, paddingHorizontal: 6, paddingVertical: 3 }}
        >
          <PixelText>LV {p.level}</PixelText>
        </View>
      </View>
      <View style={{ marginTop: 4 }}>
        <View
          style={[
            styles.border,
            { padding: 16, backgroundColor: c.body, minHeight: 76, justifyContent: 'center' },
          ]}
        >
          <PixelText style={{ lineHeight: 21 }}>{speech}</PixelText>
        </View>
        <View
          style={{
            height: 12,
            width: 14,
            borderLeftWidth: 2,
            borderRightWidth: 2,
            borderBottomWidth: 2,
            borderColor: c.ink,
            backgroundColor: c.body,
            marginLeft: 38,
            marginTop: -2,
          }}
        />
      </View>
      <View
        style={{ alignItems: 'center', justifyContent: 'center', minHeight: 206, paddingTop: 18 }}
      >
        <Pet species={p.species} hat={p.hat} grumpy={p.mood < 30} />
        {crumbs && (
          <Animated.View
            entering={FadeIn}
            exiting={FadeOut}
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
        <View
          style={{ height: 5, width: 136, backgroundColor: c.shade, opacity: 0.4, marginTop: 5 }}
        />
        <PixelText style={{ fontSize: 15, marginTop: 16 }}>{p.pet_name}</PixelText>
      </View>
      <View style={{ gap: 9 }}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
          <PixelText>MOOD{p.mood < 30 ? ' · GRUMPY' : ''}</PixelText>
          <PixelText>{p.mood}/100</PixelText>
        </View>
        <Meter value={p.mood} height={18} />
      </View>
      <View
        style={{
          flexDirection: 'row',
          gap: 12,
          justifyContent: 'center',
          paddingVertical: 8,
          borderTopWidth: 2,
          borderBottomWidth: 2,
          borderColor: c.shade,
        }}
      >
        <PixelText>YOUR CODE:</PixelText>
        <PixelText style={{ fontSize: 15 }}>{p.code}</PixelText>
      </View>
      <View style={{ gap: 12 }}>
        <View
          style={{ flexDirection: 'row', gap: 8, alignItems: 'center', justifyContent: 'center' }}
        >
          <Moon size={16} color={c.ink} />
          <PixelText>PUT YOUR PHONE DOWN.</PixelText>
        </View>
        <PixelButton label="SIMULATE SCREEN OFF" onPress={() => useGame.getState().sleep()} />
        <PixelButton
          label="FEED · 5 GRASS"
          light
          disabled={p.mood >= 100 || p.grass < 5}
          onPress={() => {
            useGame.getState().feed();
            setCrumbs(true);
          }}
        />
      </View>
      <PixelText style={{ textAlign: 'center', fontSize: 11, lineHeight: 21 }}>
        YOUR PET&apos;S LIFE DEPENDS ON IT.
      </PixelText>
    </Page>
  );
}
export function MissionsScreen() {
  const p = useGame((s) => s.player);
  if (!p) return null;
  return (
    <Page>
      <PixelText style={styles.title}>GO TOUCH GRASS.</PixelText>
      <View style={[styles.border, { padding: 16, backgroundColor: c.body }]}>
        <PixelText>{'YOUR PET GOES OUT.\nYOUR PHONE STAYS OFF.'}</PixelText>
      </View>
      {missions.map((m, index) => {
        const Icon = [Trees, BookOpen, Mountain][index];
        const locked = p.level < m.level;
        return (
          <View
            key={m.id}
            style={{ gap: 16, borderBottomWidth: 2, borderColor: c.shade, paddingBottom: 24 }}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
              <Icon color={c.ink} size={28} strokeWidth={2.5} />
              <PixelText style={{ flex: 1, fontSize: 13 }}>{m.name}</PixelText>
            </View>
            <View style={{ flexDirection: 'row', gap: 16, justifyContent: 'space-between' }}>
              <PixelText>{m.duration} MIN</PixelText>
              <PixelText>+{m.reward} GRASS</PixelText>
            </View>
            {m.id === 'mountain' && <PixelText>+ RANDOM UNOWNED HAT</PixelText>}
            <PixelButton
              label={locked ? 'REQUIRES LV 2' : 'START MISSION'}
              light={index !== 0}
              disabled={locked || p.mode !== 'awake'}
              onPress={() => useGame.getState().sleep(m.id)}
            />
          </View>
        );
      })}
    </Page>
  );
}
export function ShopScreen() {
  const p = useGame((s) => s.player);
  if (!p) return null;
  const unlock =
    p.level === 1
      ? 'SCREEN BREAK · 25 DAMAGE'
      : p.level === 2
        ? 'THICK SKIN · -20% DAMAGE'
        : 'MORE HP. MORE ATK.';
  return (
    <Page>
      <PixelText style={styles.title}>POWER UP.</PixelText>
      <View style={[styles.border, { padding: 18, gap: 20, backgroundColor: c.body }]}>
        <View
          style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}
        >
          <PixelText style={{ fontSize: 16 }}>LV {p.level}</PixelText>
          <ArrowUp size={24} color={c.ink} />
          <PixelText style={{ fontSize: 16 }}>LV {p.level + 1}</PixelText>
        </View>
        <Pet species={p.species} size={88} bob={false} />
        <PixelText>{unlock}</PixelText>
        <PixelButton
          label={`LEVEL UP · ${50 * p.level} GRASS`}
          disabled={p.grass < p.level * 50}
          onPress={() => useGame.getState().levelUp()}
        />
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
              borderBottomWidth: 2,
              borderColor: c.shade,
            }}
          >
            <Pet species={p.species} size={64} hat={h.id} bob={false} />
            <View style={{ flex: 1, gap: 12 }}>
              <PixelText style={{ fontSize: 12 }}>{h.id}</PixelText>
              {!owned && <PixelText>{h.cost} GRASS</PixelText>}
              <PixelButton
                small
                light={!equipped}
                label={equipped ? 'EQUIPPED' : owned ? 'EQUIP' : 'BUY'}
                disabled={!owned && p.grass < h.cost}
                onPress={() => useGame.getState().hatAction(h.id)}
              />
            </View>
          </View>
        );
      })}
    </Page>
  );
}
function RivalRow({
  p,
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
  const now = useGame((s) => s.now);
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
        <Pet species={p.species} hat={p.hat} size={48} bob={false} />
        <View style={{ flex: 1, gap: 4 }}>
          <PixelText numberOfLines={1}>{me ? 'YOU' : p.name}</PixelText>
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
          disabled={!!raiding}
          onPress={() => onRaid(p)}
        />
      )}
    </View>
  );
}
export function ArenaScreen() {
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
      <PixelText style={styles.title}>{'LESS SCROLL.\nMORE GLORY.'}</PixelText>
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
            <PixelText accessibilityRole="alert">{error}</PixelText>
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
          <Users color={c.ink} size={30} />
          <PixelText style={{ textAlign: 'center' }}>
            {`NO RIVALS YET.\nSHARE YOUR CODE: ${p.code}`}
          </PixelText>
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
        <PixelText style={{ fontSize: 16 }}>TRAINING</PixelText>
      </View>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
        <Pet species="RAT" size={60} bob={false} />
        <View style={{ flex: 1, gap: 4 }}>
          <PixelText>DOOMSCROLL DAVE</PixelText>
          <PixelText>LV {p.level} · MOOD 50</PixelText>
        </View>
      </View>
      <PixelButton
        label="PRACTICE BATTLE"
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
