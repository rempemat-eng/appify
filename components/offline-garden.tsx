import { Pressable, ScrollView, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Sprout, Users } from 'lucide-react-native';
import { cozy as c } from '@/lib/cozy';
import { clock, useGame, type Player } from '@/lib/game';
import Svg, { Rect } from 'react-native-svg';
import { budgetVoice, dayKey, emptyDay, gardenStreak, remainingPlay } from '@/lib/offline-rules';
import { Pet, PixelButton, PixelText, styles } from '@/components/game-ui';
import { BodyText, Dialogue } from '@/components/pixel-feedback';
import { PixelScene } from '@/components/pixel-scenes';
import { growthStage } from '@/lib/grasslings';
export function PlayMeter() {
  const budget = useGame((s) => s.rules.budget);
  const now = useGame((s) => s.now);
  const left = remainingPlay(budget, now);
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${left} seconds of play left. Long press to reset demo play budget.`}
      onLongPress={() => useGame.getState().resetBudget()}
      style={{
        minHeight: 44,
        paddingHorizontal: 6,
        borderRadius: 999,
        backgroundColor: c.paper,
        borderWidth: 1,
        borderColor: c.outline,
        flexDirection: 'row',
        alignItems: 'center',
        gap: 4,
      }}
    >
      <Svg width={16} height={16} viewBox="0 0 8 8">
        <Rect x={1} y={0} width={6} height={1} fill={c.ink} />
        <Rect x={1} y={7} width={6} height={1} fill={c.ink} />
        {[1, 2, 3, 4, 5, 6].map((y) => (
          <Rect
            key={y}
            x={y < 4 ? y : 7 - y}
            y={y}
            width={y === 3 || y === 4 ? 2 : 1}
            height={1}
            fill={left ? c.ink : c.error}
          />
        ))}
      </Svg>
      <View style={{ gap: 5 }}>
        <BodyText style={{ fontFamily: 'Nunito_800ExtraBold', fontSize: 11 }}>
          {clock(left)}
        </BodyText>
        <View style={{ width: 46, height: 4, backgroundColor: c.stone }}>
          <View
            style={{
              width: (46 * left) / 180,
              height: 4,
              backgroundColor: left ? c.moss : c.error,
            }}
          />
        </View>
      </View>
    </Pressable>
  );
}
export function usePlayPaused() {
  const budget = useGame((s) => s.rules.budget);
  const now = useGame((s) => s.now);
  return remainingPlay(budget, now) === 0;
}
export function PlayPause() {
  const paused = usePlayPaused();
  if (!paused) return null;
  return (
    <View style={{ gap: 12 }}>
      <Dialogue text={budgetVoice} />
      <PixelButton label="TAKE A NAP" gold onPress={() => useGame.getState().sleep()} />
      <BodyText style={{ textAlign: 'center', fontSize: 12 }}>
        put your phone down · simulated
      </BodyText>
    </View>
  );
}
export function GardenProgress() {
  const offline = useGame((s) => s.rules.days[dayKey(s.now)]?.offline ?? 0);
  return (
    <View style={{ gap: 6 }}>
      <BodyText style={{ fontSize: 12, fontFamily: 'Nunito_800ExtraBold' }}>
        TODAY {offline} / 120 MIN
      </BodyText>
      <View
        accessibilityRole="progressbar"
        accessibilityValue={{ min: 0, max: 120, now: Math.min(120, offline) }}
        style={{ height: 6, borderRadius: 3, backgroundColor: c.faded }}
      >
        <View
          style={{
            height: 6,
            borderRadius: 3,
            width: `${Math.min(100, (offline / 120) * 100)}%`,
            backgroundColor: c.positive,
          }}
        />
      </View>
    </View>
  );
}
export function GardenStreak() {
  const rules = useGame((s) => s.rules);
  const now = useGame((s) => s.now);
  const { streak } = gardenStreak(rules, dayKey(now));
  return (
    <View style={{ gap: 8 }}>
      <View style={{ flexDirection: 'row', gap: 8, alignItems: 'center' }}>
        <Sprout size={20} color={c.moss} />
        <PixelText>
          {streak} {streak === 1 ? 'DAY' : 'DAYS'} STREAK
        </PixelText>
      </View>
      {rules.togetherBadges > 0 && (
        <View style={{ flexDirection: 'row', gap: 8, alignItems: 'center' }}>
          <Users size={18} color={c.moss} />
          <PixelText>TOGETHER</PixelText>
        </View>
      )}
    </View>
  );
}
export function TogetherInvite({ rival }: { rival: Player }) {
  const sessions = useGame((s) => s.sessions);
  const me = useGame((s) => s.player);
  const pending = useGame((s) => s.togetherPending);
  const activeId = useGame((s) => s.togetherId);
  const session = sessions.find(
    (x) =>
      (x.player_a === rival.id || x.player_b === rival.id) &&
      (x.status === 'invited' || x.status === 'active'),
  );
  if (session?.status === 'active') return <BodyText>TOUCHING GRASS TOGETHER</BodyText>;
  const incoming = session?.player_b === me?.id;
  return (
    <PixelButton
      label={
        pending === rival.id
          ? 'CONNECTING...'
          : incoming
            ? 'ACCEPT'
            : session
              ? 'INVITE SENT'
              : 'INVITE TO TOUCH GRASS'
      }
      small
      light
      disabled={Boolean(pending) || Boolean(activeId) || Boolean(session && !incoming)}
      onPress={() => {
        if (incoming && session) void useGame.getState().acceptTogether(session);
        else void useGame.getState().inviteTogether(rival);
      }}
    />
  );
}
export function GardenRecap() {
  const router = useRouter();
  const p = useGame((s) => s.player)!;
  const key = useGame((s) => s.recap)!;
  const rules = useGame((s) => s.rules);
  const day = rules.days[key] ?? emptyDay();
  return (
    <View style={{ flex: 1, backgroundColor: c.paper, padding: 24, gap: 20 }}>
      <ScrollView contentContainerStyle={{ gap: 22, paddingBottom: 12 }}>
        <PixelText style={styles.title}>YESTERDAY&apos;S GARDEN</PixelText>
        <PixelScene
          species={p.species}
          level={p.level}
          height={190}
          style={{ alignItems: 'center', justifyContent: 'flex-end' }}
        >
          <Pet species={p.species} level={p.level} hat={p.hat} size={128} />
        </PixelScene>
        <View style={[styles.border, { padding: 16, gap: 18, backgroundColor: c.body }]}>
          {[
            [`${day.offline} MIN`, 'OFFLINE'],
            [String(day.cards), 'CARDS EARNED'],
            [String(Math.floor(day.grass)), 'GRASS EARNED'],
            [String(day.blocked), 'RAIDS BLOCKED OFFLINE'],
          ].map(([value, label]) => (
            <View key={label} style={{ gap: 7 }}>
              <PixelText>{label}</PixelText>
              <BodyText>{value}</BodyText>
            </View>
          ))}
          <View style={{ gap: 7 }}>
            <PixelText>GARDEN GROWTH</PixelText>
            <BodyText>
              {day.offline} MIN OF GROWTH · {growthStage(p.level)}
            </BodyText>
          </View>
        </View>
        <Dialogue
          text={
            day.offline >= 120
              ? 'you lived a little. i grew a little.'
              : day.offline > 0
                ? 'every minute away helps me grow.'
                : "let's spend today out in the world."
          }
        />
      </ScrollView>
      <PixelButton
        label="BACK TO REAL LIFE"
        onPress={() => {
          useGame.getState().dismissRecap();
          router.replace('/');
          useGame.getState().sleep();
        }}
      />
      <Pressable
        accessibilityRole="link"
        onPress={() => {
          useGame.getState().dismissRecap();
          router.replace('/');
        }}
        style={{ minHeight: 44, justifyContent: 'center', alignItems: 'center' }}
      >
        <PixelText style={{ textDecorationLine: 'underline' }}>OPEN GARDEN</PixelText>
      </Pressable>
    </View>
  );
}
