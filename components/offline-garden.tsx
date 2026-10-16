import { Fragment } from 'react';
import { Pressable, ScrollView, View } from 'react-native';
import Animated, { FadeIn, FadeOut } from 'react-native-reanimated';
import { useRouter } from 'expo-router';
import { Sprout, Users, Moon } from 'lucide-react-native';
import { cozy as c } from '@/lib/cozy';
import { clock, missions, useGame, type Player } from '@/lib/game';
import Svg, { Rect } from 'react-native-svg';
import {
  budgetVoice,
  dailyProgress,
  dayKey,
  emptyDay,
  gardenStreak,
  remainingPlay,
} from '@/lib/offline-rules';
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
        {[1, 2, 3, 4, 5, 6].map((y) => {
          const x = y < 4 ? y : 7 - y;
          return (
            <Fragment key={y}>
              <Rect x={x} y={y} width={1} height={1} fill={c.ink} />
              <Rect x={7 - x} y={y} width={1} height={1} fill={c.ink} />
            </Fragment>
          );
        })}
        <Rect x={2} y={2} width={4} height={1} fill={left ? c.focus : c.error} />
        <Rect x={3} y={3} width={2} height={2} fill={left ? c.focus : c.error} />
        <Rect x={2} y={6} width={4} height={1} fill={left ? c.focus : c.error} />
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
  const progress = dailyProgress(offline);
  return (
    <View style={{ gap: 6 }}>
      <BodyText style={{ fontSize: 12, fontFamily: 'Nunito_800ExtraBold' }}>
        {progress.complete ? 'Daily goal complete' : `${progress.total} / 120 simulated MIN today`}
      </BodyText>
      <View
        accessibilityRole="progressbar"
        accessibilityLabel={`Daily goal ${progress.complete ? 'complete' : 'progress'}: ${progress.total} simulated MIN today; goal 120 simulated MIN`}
        accessibilityValue={{ min: 0, max: 120, now: progress.value }}
        style={{ height: 6, borderRadius: 3, backgroundColor: c.faded }}
      >
        <View
          style={{
            height: 6,
            borderRadius: 3,
            width: `${progress.percent}%`,
            backgroundColor: c.positive,
          }}
        />
      </View>
      {progress.complete && (
        <BodyText style={{ fontSize: 12 }}>{progress.total} simulated MIN today</BodyText>
      )}
    </View>
  );
}
export function RecentBreaks() {
  const history = useGame((s) => s.recentBreaks);
  return (
    <View style={{ gap: 12, paddingTop: 12 }}>
      <BodyText style={{ fontFamily: 'Nunito_800ExtraBold', fontSize: 16 }}>Recent breaks</BodyText>
      {!history.length && (
        <View style={{ gap: 8 }}>
          <Moon color={c.ink} size={20} strokeWidth={2} />
          <BodyText>Your next completed nap or mission will appear here.</BodyText>
        </View>
      )}
      {history.slice(0, 5).map((entry) => (
        <Animated.View
          entering={FadeIn}
          exiting={FadeOut}
          key={entry.id}
          style={{ gap: 4, paddingBottom: 12, borderBottomWidth: 1, borderBottomColor: c.outline }}
        >
          <BodyText style={{ fontFamily: 'Nunito_800ExtraBold' }}>
            {entry.mission
              ? (missions.find((m) => m.id === entry.mission)?.name ?? 'Mission')
              : 'Nap'}
            {entry.early ? ' · returned early' : ''}
          </BodyText>
          <BodyText style={{ fontSize: 12 }}>
            {new Date(entry.completedAt).toLocaleString(undefined, {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
              hour: 'numeric',
              minute: '2-digit',
            })}
          </BodyText>
          <BodyText style={{ fontSize: 12 }}>
            {entry.minutes.toLocaleString()} simulated MIN · {entry.grass.toLocaleString()} GRASS ·{' '}
            {entry.cards} {entry.cards === 1 ? 'card' : 'cards'}
          </BodyText>
        </Animated.View>
      ))}
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
