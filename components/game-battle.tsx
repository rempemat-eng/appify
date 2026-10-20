import { cozy as c } from '@/lib/cozy';
import { FrameFill } from '@/components/pixel-frame';
import { CozyBackground } from '@/components/cozy-ui';
import { PlayedCard, PixelBurst, PerfectImpact } from '@/components/cozy-motion';
import * as Haptics from 'expo-haptics';
import { useReducedMotion } from '@/lib/motion';
import { onSwitchKey } from '@/lib/switch-keys';
import { useCallback, useEffect, useRef, useState, type KeyboardEvent } from 'react';
import {
  PixelRatio,
  Pressable,
  ScrollView,
  StyleSheet,
  View,
  useWindowDimensions,
  Platform,
} from 'react-native';
import { pixelScale } from '@/lib/pixel-scale';
import { PixelIcon } from '@/components/pixel-icon';
import Animated, {
  FadeIn,
  FadeOut,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from 'react-native-reanimated';
import {
  feedback,
  gameStore,
  useGame,
  raidDreamDust,
  type BattleRequest,
  type Player,
} from '@/lib/game';
import { PlayMeter, usePlayPaused } from '@/components/offline-garden';
import { dayKey, emptyDay, sparringReward } from '@/lib/offline-rules';
import {
  available,
  beginTurn,
  chooseAI,
  computerTiming,
  createCombat,
  damaging,
  maxHp,
  resolveMove,
  timingAt,
  zen,
  type Combat,
  type Fighter,
  type Impact,
  type Move,
  type Side,
} from '@/lib/battle';
import { EnergyPips, Meter, Pet, PixelButton, PixelText } from '@/components/game-ui';
import { RaidGarden } from '@/components/pixel-scenes';
import { useUi } from '@/lib/ui';
import { guardianPlayer } from '@/lib/visitors';
import { grasslingName, grasslings } from '@/lib/grasslings';
import { DreamDustFlight } from '@/components/grassling-feedback';
import { BodyText, BattleIntro, Pulse } from '@/components/pixel-feedback';
import { HabitCard } from '@/components/habit-cards';
import { cardDetails, cards } from '@/lib/cards';
import { combatTurnId, createTurnResolutionGate } from '@/lib/turn-resolution';

type Phase = 'choose' | 'timing' | 'block' | 'resolve' | 'waiting' | 'skipped' | 'end';
function Damage({ amount, skip }: { amount: number; skip: boolean }) {
  const y = useSharedValue(0);
  const opacity = useSharedValue(1);
  const reduced = useReducedMotion();
  useEffect(() => {
    y.set(withTiming(reduced ? 0 : -30, { duration: 600 }));
    opacity.set(skip ? 0 : withTiming(0, { duration: reduced ? 100 : 600 }));
  }, [opacity, reduced, y, skip]);
  const animated = useAnimatedStyle(() => ({
    opacity: opacity.value,
    transform: [{ translateY: y.value }],
  }));
  return (
    <Animated.View
      style={[
        {
          position: 'absolute',
          top: 32,
          left: 12,
          zIndex: 5,
          padding: 10,
        },
        animated,
      ]}
    >
      <FrameFill depth={1} />
      <PixelText style={{ fontSize: 16 }}>-{amount}</PixelText>
    </Animated.View>
  );
}
function Info({ p, f }: { p: Player; f: Fighter }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <View>
      <FrameFill depth={1} />
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={`${grasslingName(p)}, ${f.hp} of ${maxHp(p)} HP, ${f.energy} energy. Show details`}
        accessibilityState={{ expanded }}
        aria-expanded={expanded}
        onPress={() => {
          setExpanded(!expanded);
          feedback('select');
        }}
        style={{ flexDirection: 'row', alignItems: 'center', gap: 8, padding: 6, minHeight: 48 }}
      >
        <BodyText
          style={{ width: 92, fontSize: 11, lineHeight: 16, fontFamily: 'PixelifySans_700Bold' }}
        >
          {grasslingName(p)}
        </BodyText>
        <View style={{ flex: 1, gap: 2 }}>
          <BodyText style={{ fontSize: 11, lineHeight: 14, fontFamily: 'PixelifySans_700Bold' }}>
            HP {f.hp}/{maxHp(p)}
          </BodyText>
          <Meter
            value={f.hp}
            max={maxHp(p)}
            height={20}
            color={f.hp < maxHp(p) * 0.25 ? c.danger : f.hp < maxHp(p) * 0.5 ? c.amber : c.moss}
          />
        </View>
        <View style={{ gap: 0 }}>
          <BodyText style={{ fontSize: 11, lineHeight: 14, fontFamily: 'PixelifySans_700Bold' }}>
            ENERGY
          </BodyText>
          <EnergyPips value={f.energy} />
        </View>
        <PixelIcon name="chevronDown" size={16} />
      </Pressable>
      {expanded && (
        <View style={{ padding: 8, flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
          <BodyText>
            LV {p.level} · {p.id === 'bot' ? 'WEED' : grasslings[p.species].habit} · ZEN{' '}
            {Math.round(zen(p) * 100)}% · {f.hp}/{maxHp(p)} HP
          </BodyText>
          {f.guard && <PixelIcon name="shield" label="Guarded" size={16} />}
          {f.notified && <PixelIcon name="bell" label="Distracted, next turn skipped" size={16} />}
          {f.nextEnergy > 0 && <BodyText>+1 ENERGY NEXT TURN</BodyText>}
        </View>
      )}
    </View>
  );
}
/**
 * How wide a hand card is: the whole hand side by side when it fits (cards 120 px or
 * wider), else wide enough to read with the next card peeking in at the edge, so it is
 * plain the hand scrolls on.
 */
function handCardWidth(screenWidth: number, count: number) {
  const room = Math.min(screenWidth, 640) - 32;
  if (count * 168 + (count - 1) * 12 <= room) return 168;
  const fit = Math.floor((room - (count - 1) * 12) / count);
  return fit >= 120 ? fit : Math.floor((room - 24) / 2.35);
}

export function BattleScreen({ request }: { request: BattleRequest }) {
  const paused = usePlayPaused();
  const reduced = useReducedMotion();
  const [player] = useState(() => guardianPlayer(gameStore.getState().player!));
  const { width, height } = useWindowDimensions();
  const rules = useGame((s) => s.rules);
  // a spar at a region's ring is fought in front of that region (presentation only)
  const [place] = useState(() => (request.practice ? useUi.getState().battlePlace : null));
  useEffect(() => () => useUi.setState({ battlePlace: null }), []);
  const [cardLesson, setCardLesson] = useState(
    () => request.practice && !gameStore.getState().tips.includes('card'),
  );
  const [timingLesson, setTimingLesson] = useState(
    () => request.practice && !gameStore.getState().tips.includes('timing'),
  );
  // The battle is a close-up of the world (coherence plan, step 7b): one art pixel is
  // a whole number of the shared grid's pixels, and the fighters, the field and the
  // platforms all use it. The zoom is as large as fits two fighters across and at least
  // 64 art pixels of field in the height left between the HP header and the card tray.
  const unit = pixelScale(width, PixelRatio.get());
  const stageHeight = Math.min(360, height - 420);
  const artFit = Math.min((Math.min(width, 640) - 24) / 80, stageHeight / 64, 8);
  const art = Math.max(2, Math.floor(artFit / unit)) * unit;
  const petSize = 32 * art;
  const [lifted, setLifted] = useState<number | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [target] = useState(() => guardianPlayer(request.target));
  const [combat, setCombat] = useState(() => createCombat(player, target));
  const combatRef = useRef(combat);
  const [turnResolution] = useState(() =>
    createTurnResolutionGate<ReturnType<typeof resolveMove>>(),
  );
  const [phase, setPhase] = useState<Phase>('choose');
  const phaseRef = useRef<Phase>('choose');
  const [auto, setAuto] = useState(false);
  const autoRef = useRef(false);
  const toggleAuto = () => {
    const value = !autoRef.current;
    autoRef.current = value;
    setCardLesson(false);
    setTimingLesson(false);
    setAuto(value);
    setLifted(null);
    feedback('select');
  };
  const [cursor, setCursor] = useState(0);
  const timingStart = useRef(0);
  const selected = useRef<Move>('stretch');
  const [playedMove, setPlayedMove] = useState<Move>('stretch');
  const timing = useRef(1);
  const blocked = useRef(false);
  const blockWindow = useRef(600);
  const blockAuto = useRef(false);
  const [hit, setHit] = useState({ a: 0, d: 0 });
  const [attack, setAttack] = useState({ a: 0, d: 0 });
  const [damage, setDamage] = useState<(Impact & { id: number; perfect: boolean }) | null>(null);
  const [skip, setSkip] = useState(false);
  const [log, setLog] = useState('YOUR TURN. LIFT A CARD, TAP AGAIN TO PLAY.');
  const [flashEndedTurn, setFlashEndedTurn] = useState<string | null>(null);
  const flash =
    phase === 'resolve' &&
    playedMove === 'digital_sunset' &&
    flashEndedTurn !== combatTurnId(combat);
  const [history, setHistory] = useState<{ id: number; line: string; summary: string }[]>([]);
  const historyId = useRef(0);
  const committed = useRef(false);
  const active = useCallback(() => gameStore.getState().battle === request, [request]);
  const changePhase = useCallback((value: Phase) => {
    phaseRef.current = value;
    setPhase(value);
  }, []);
  const publish = useCallback((value: Combat) => {
    combatRef.current = value;
    setCombat(value);
  }, []);
  const record = useCallback((line: string, summary = line) => {
    const entry = { id: ++historyId.current, line, summary };
    setLog(line);
    setHistory((old) => [...old.slice(-23), entry]);
  }, []);
  const select = useCallback(
    (move: Move) => {
      if (phaseRef.current !== 'choose' || !active() || !available(move, combatRef.current.a))
        return;
      setSkip(false);
      selected.current = move;
      setPlayedMove(move);
      setLifted(null);
      timing.current = 1;
      blocked.current = false;
      feedback('select');
      if (damaging(move) && !autoRef.current) {
        timingStart.current = Date.now();
        setCursor(0);
        changePhase('timing');
      } else {
        if (damaging(move)) timing.current = computerTiming();
        changePhase('resolve');
      }
    },
    [active, changePhase],
  );
  function attackTap() {
    if (phaseRef.current !== 'timing') return;
    if (timingLesson) {
      setTimingLesson(false);
      timingStart.current = Date.now();
      return;
    }
    timing.current = timingAt(Math.min(1, (Date.now() - timingStart.current) / 1200));
    feedback('select');
    changePhase('resolve');
  }
  function blockTap() {
    if (phaseRef.current !== 'block') return;
    blocked.current = Date.now() - timingStart.current <= blockWindow.current;
    if (blocked.current) feedback('select');
    changePhase('resolve');
  }
  const nextTurn = useCallback(() => {
    if (!active()) return;
    const current = combatRef.current;
    if (current.result !== null) {
      changePhase('end');
      return;
    }
    const side: Side = current.side === 'a' ? 'd' : 'a';
    const next = beginTurn(current, side);
    publish(next.state);
    if (next.state.timedOut) {
      record(request.practice ? 'SPARRING REACHED THE ROUND LIMIT' : 'RAID TIMED OUT');
      changePhase('end');
      return;
    }
    if (next.skipped) {
      record('DISTRACTED! NEXT TURN SKIPPED.');
      changePhase('skipped');
      return;
    }
    if (side === 'a') changePhase('choose');
    else {
      const move = chooseAI(next.state.d, target);
      selected.current = move;
      setPlayedMove(move);
      timing.current = computerTiming();
      blocked.current = false;
      if (damaging(move)) {
        blockAuto.current = autoRef.current;
        blockWindow.current = blockAuto.current ? 300 : 600;
        timingStart.current = Date.now();
        changePhase('block');
      } else changePhase('resolve');
    }
  }, [active, changePhase, publish, record, request.practice, target]);
  useEffect(() => {
    if (phase !== 'timing' || timingLesson) return undefined;
    let frame = 0;
    function sweep() {
      if (phaseRef.current !== 'timing') return;
      const progress = Math.min(1, (Date.now() - timingStart.current) / 1200);
      setCursor(progress);
      if (progress < 1) frame = requestAnimationFrame(sweep);
      else {
        timing.current = 0.6;
        changePhase('resolve');
      }
    }
    frame = requestAnimationFrame(sweep);
    return () => cancelAnimationFrame(frame);
  }, [phase, timingLesson, changePhase]);
  // Motion preferences only control presentation. They must not restart a turn's
  // gameplay timers after its card and damage have already been committed.
  useEffect(() => {
    if (phase !== 'resolve' || playedMove !== 'digital_sunset') return undefined;
    const turnId = combatTurnId(combatRef.current);
    const timer = setTimeout(() => setFlashEndedTurn(turnId), 180 * (autoRef.current ? 0.5 : 1));
    return () => clearTimeout(timer);
  }, [phase, playedMove]);
  useEffect(() => {
    const phaseAuto = autoRef.current;
    if (phase === 'block') {
      const timer = setTimeout(() => {
        if (phaseRef.current !== 'block') return;
        blocked.current = blockAuto.current && Math.random() < 0.6;
        phaseRef.current = 'resolve';
        setPhase('resolve');
      }, blockWindow.current);
      return () => clearTimeout(timer);
    }
    if (phase === 'waiting' || phase === 'skipped') {
      const timer = setTimeout(nextTurn, phaseAuto ? 400 : 800);
      return () => clearTimeout(timer);
    }
    if (phase === 'resolve') {
      const side = combatRef.current.side;
      const turnId = combatTurnId(combatRef.current);
      const move = selected.current;
      if (damaging(move)) setAttack((old) => ({ ...old, [side]: old[side] + 1 }));
      const timers: ReturnType<typeof setTimeout>[] = [];
      const speed = phaseAuto ? 0.5 : 1;
      const timer = setTimeout(() => {
        if (
          !active() ||
          phaseRef.current !== 'resolve' ||
          combatTurnId(combatRef.current) !== turnId
        )
          return;
        const beforeHp = combatRef.current[side].hp;
        const { value: resolution, first } = turnResolution.resolve(turnId, () =>
          resolveMove(
            combatRef.current,
            move,
            { a: player, d: target },
            timing.current,
            blocked.current,
          ),
        );
        combatRef.current = resolution.state;
        const impacts = resolution.impacts;
        if (!impacts.length) setCombat(resolution.state);
        const actor = side === 'a' ? player : target;
        const heal = resolution.state[side].hp - beforeHp;
        const summary = `${grasslingName(actor)} ${move === 'pass' ? 'passed' : `played ${cards[move].name}`}. ${timing.current === 1.5 && damaging(move) ? 'PERFECT! ' : ''}${impacts.length ? `-${impacts.reduce((sum, impact) => sum + impact.amount, 0)}${blocked.current ? ' · BLOCKED' : ''}` : move === 'deep_breath' ? 'BLOCK HALF · +1 ENERGY' : move === 'pass' ? '+1 ENERGY' : `+${Math.max(0, heal)} HP`}`;
        if (first) record(resolution.log, summary);
        impacts.forEach((impact, i) => {
          timers.push(
            setTimeout(
              () => {
                if (!active()) return;
                setCombat({
                  ...resolution.state,
                  [impact.side]: { ...resolution.state[impact.side], hp: impact.hp },
                });
                setSkip(false);
                setHit((old) => ({ ...old, [impact.side]: old[impact.side] + 1 }));
                setDamage({
                  ...impact,
                  id: Date.now() + i,
                  perfect: timing.current === 1.5 && damaging(move),
                });
                void Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
              },
              i * 200 * speed,
            ),
          );
        });
        timers.push(
          setTimeout(
            () => {
              setCombat(resolution.state);
              phaseRef.current = resolution.state.result === null ? 'waiting' : 'end';
              setPhase(phaseRef.current);
            },
            Math.max(1, impacts.length) * 200 * speed + 200 * speed,
          ),
        );
      }, 160 * speed);
      timers.push(timer);
      return () => {
        timers.forEach(clearTimeout);
      };
    }
    return undefined;
  }, [phase, player, target, active, nextTurn, record, turnResolution]);
  useEffect(() => {
    if (phase !== 'choose' || !auto) return undefined;
    const timer = setTimeout(() => select(chooseAI(combatRef.current.a, player)), 200);
    return () => clearTimeout(timer);
  }, [auto, phase, player, select]);
  const finished = phase === 'end' && combat.result !== null;
  const reward = request.practice
    ? sparringReward(rules.days[dayKey()] ?? emptyDay(), Boolean(combat.result))
    : raidDreamDust(Boolean(combat.result), target);
  useEffect(() => {
    if (finished && combat.result)
      void Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
  }, [finished, combat.result]);
  const enabled = phase === 'choose' && !auto;
  useEffect(() => {
    if (cardLesson && enabled) gameStore.getState().seeTip('card');
    if (timingLesson && phase === 'timing') gameStore.getState().seeTip('timing');
  }, [cardLesson, enabled, timingLesson, phase]);
  const handCounts = new Map<string, number>();
  const handCards = combat.a.hand.map((id) => {
    const occurrence = (handCounts.get(id) ?? 0) + 1;
    handCounts.set(id, occurrence);
    return { id, key: `${id}-${occurrence}` };
  });
  return (
    <PerfectImpact perfect={Boolean(damage?.perfect)} impact={damage?.id ?? 0} skip={skip}>
      <View
        onStartShouldSetResponderCapture={() => {
          setSkip(true);
          return false;
        }}
        onTouchStart={() => setSkip(true)}
        style={{ flex: 1, backgroundColor: c.paper }}
      >
        <CozyBackground />
        <View pointerEvents="none" style={StyleSheet.absoluteFill}>
          <Pulse
            active={combat.d.hp < maxHp(target) * 0.25}
            style={{ position: 'absolute', top: 0, bottom: 0, right: 0, width: '50%' }}
          />
          <Pulse
            active={combat.a.hp < maxHp(player) * 0.25}
            style={{ position: 'absolute', top: 0, bottom: 0, left: 0, width: '50%' }}
          />
        </View>
        <View
          style={{
            backgroundColor: c.paper,
            paddingHorizontal: 12,
            paddingVertical: 8,
            gap: 6,
            borderBottomWidth: 2,
            borderColor: c.ink,
          }}
        >
          <View
            style={{
              flexDirection: 'row',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <View style={{ flex: 1, gap: 6 }}>
              <PixelText>{request.practice ? 'SPARRING' : 'GARDEN RAID'}</PixelText>
              <BodyText
                style={{ fontFamily: 'PixelifySans_500Medium', fontSize: 11, lineHeight: 14 }}
              >
                ROUND {Math.max(combat.a.turns, combat.d.turns)}/12
              </BodyText>
            </View>
            <PlayMeter />
            <Pressable
              accessibilityRole="switch"
              accessibilityState={{ checked: auto }}
              aria-checked={auto}
              accessibilityLabel={
                request.practice ? 'Auto sparring at double speed' : 'Auto raid at double speed'
              }
              // Pressable's types omit web key events; RN Web passes them through.
              {...(Platform.OS === 'web'
                ? {
                    onKeyDown: (event: KeyboardEvent<HTMLElement>) =>
                      onSwitchKey(event, toggleAuto),
                  }
                : {})}
              onPress={toggleAuto}
              style={{
                borderRadius: 0,
                minHeight: 44,
                minWidth: 44,
                flexDirection: 'row',
                alignItems: 'center',
                gap: 5,
                padding: 10,
              }}
            >
              <FrameFill tone={auto ? 'gold' : 'paper'} depth={1} />
              <PixelText>AUTO</PixelText>
              <PixelIcon name="fast" size={16} />
              <BodyText>{auto ? 'ON' : 'OFF'}</BodyText>
            </Pressable>
          </View>
          <Info p={player} f={combat.a} />
          <Info p={target} f={combat.d} />
        </View>
        <ScrollView
          style={{ flex: 1 }}
          contentContainerStyle={{ flexGrow: 1, width: '100%', maxWidth: 640, alignSelf: 'center' }}
        >
          <View
            style={{
              flex: 1,
              minHeight: Math.max(petSize + 39 * art, stageHeight),
              flexDirection: 'row',
              alignItems: 'flex-end',
              justifyContent: 'center',
              paddingBottom: 24 * art - 3 * art,
            }}
          >
            <RaidGarden pixel={art} petSize={petSize} region={place} />
            <Animated.View
              entering={reduced ? undefined : FadeIn.duration(150)}
              style={{
                position: 'absolute',
                left: 12,
                bottom: 24 * art - 3 * art,
                width: petSize,
                alignItems: 'center',
              }}
            >
              <Pet
                species={player.species}
                visitor={player.guardian}
                level={player.level}
                hat={player.hat}
                facing="right"
                grumpy={player.mood < 30}
                size={petSize}
                bob={false}
                groundShadow={false}
                hit={hit.a}
                attack={attack.a}
                slumped={combat.a.hp <= 0 || (finished && combat.result === false)}
                victory={finished && combat.result === true}
              />
              {damage?.side === 'a' && (
                <Damage key={damage.id} amount={damage.amount} skip={skip} />
              )}
            </Animated.View>
            <Animated.View
              entering={reduced ? undefined : FadeIn.duration(150)}
              style={{
                position: 'absolute',
                right: 12,
                bottom: 24 * art - 3 * art,
                width: petSize,
                alignItems: 'center',
              }}
            >
              <Pet
                species={target.species}
                visitor={target.guardian}
                level={target.level}
                hat={target.hat}
                facing="left"
                dave={target.id === 'bot'}
                grumpy={target.mood < 30}
                size={petSize}
                bob={false}
                groundShadow={false}
                hit={hit.d}
                attack={attack.d}
                slumped={combat.d.hp <= 0 || (finished && combat.result === true)}
                victory={finished && combat.result === false}
              />
              {damage?.side === 'd' && (
                <Damage key={damage.id} amount={damage.amount} skip={skip} />
              )}
            </Animated.View>
            {phase === 'resolve' && playedMove !== 'pass' && (
              <PlayedCard
                key={`${attack.a}-${attack.d}-${combat.side}`}
                id={playedMove}
                toLeft={combat.side === 'd'}
                distance={Math.min(width, 640) * 0.55}
                skip={skip}
              />
            )}
            {damage && !skip && (
              <View
                key={`burst-${damage.id}`}
                pointerEvents="none"
                style={{
                  position: 'absolute',
                  left: damage.side === 'a' ? '12%' : '65%',
                  top: '25%',
                  width: petSize,
                  height: petSize,
                }}
              >
                <PixelBurst />
              </View>
            )}
            {finished && combat.result && !request.practice && <DreamDustFlight />}
          </View>
          {showHistory && history.length > 1 && (
            <View style={{ gap: 6, padding: 12, backgroundColor: c.paper }}>
              <PixelText>RAID LOG</PixelText>
              {history.slice(0, -1).map((entry) => (
                <BodyText key={entry.id}>{entry.line}</BodyText>
              ))}
            </View>
          )}
        </ScrollView>
        <View
          style={{
            maxHeight: Math.max(250, height * 0.48),
            padding: 16,
            gap: 12,
            width: '100%',
            maxWidth: 640,
            alignSelf: 'center',
          }}
        >
          <FrameFill />
          {!(phase === 'choose' || phase === 'timing' || phase === 'block') && (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Show full action history"
              accessibilityState={{ expanded: showHistory && history.length > 1 }}
              aria-expanded={showHistory && history.length > 1}
              onPress={() => {
                setShowHistory(!showHistory);
                feedback('select');
              }}
              style={{ minHeight: 44, padding: 10 }}
            >
              <FrameFill fill={c.body} inset />
              <View accessibilityLiveRegion="polite" style={{ gap: 4 }}>
                {history.length ? (
                  history.slice(-1).map((entry) => (
                    <BodyText
                      key={entry.id}
                      style={{ fontFamily: 'PixelifySans_500Medium', fontSize: 12, lineHeight: 17 }}
                    >
                      {entry.summary}
                    </BodyText>
                  ))
                ) : (
                  <BodyText
                    style={{ fontFamily: 'PixelifySans_500Medium', fontSize: 12, lineHeight: 17 }}
                  >
                    {log}
                  </BodyText>
                )}
              </View>
            </Pressable>
          )}
          <ScrollView style={{ flexShrink: 1 }} contentContainerStyle={{ gap: 8 }}>
            {finished ? (
              <Animated.View
                entering={reduced ? undefined : FadeIn}
                exiting={reduced ? undefined : FadeOut}
                style={{ gap: 14 }}
              >
                <PixelText style={{ textAlign: 'center', fontSize: 16 }}>
                  {request.practice
                    ? combat.result
                      ? 'SPARRING WON'
                      : 'SPARRING LOST'
                    : combat.result
                      ? 'VICTORY!'
                      : 'RAID FAILED.'}
                </PixelText>
                <BodyText
                  style={{ textAlign: 'center', fontFamily: 'PixelifySans_700Bold', fontSize: 16 }}
                >
                  {request.practice
                    ? reward > 0
                      ? `+${reward} DREAM DUST`
                      : 'NO DREAM DUST EARNED'
                    : combat.result
                      ? `YOU STOLE ${reward} DREAM DUST`
                      : `-${reward} DREAM DUST`}
                </BodyText>
                {!request.practice && (
                  <PixelText style={{ textAlign: 'center' }}>
                    RAIDS LEFT TODAY: {Math.max(0, 3 - (rules.days[dayKey()]?.raids ?? 0))}
                  </PixelText>
                )}
                {paused && (
                  <BodyText style={{ textAlign: 'center' }}>
                    Play time is up. Your result is safe.
                  </BodyText>
                )}
              </Animated.View>
            ) : (
              <>
                <View style={{ minHeight: 168, justifyContent: 'center', gap: 8 }}>
                  {phase === 'timing' ? (
                    <View style={{ gap: 8 }}>
                      <Pressable
                        accessibilityRole="button"
                        accessibilityLabel="Tap the action bar in the centre"
                        onPress={attackTap}
                        style={{ padding: 10, gap: 8 }}
                      >
                        <FrameFill fill={c.body} depth={1} />
                        <PixelText style={{ textAlign: 'center' }}>
                          {timingLesson ? 'TAP TO START' : 'TAP IN THE MIDDLE!'}
                        </PixelText>
                        <View
                          style={{
                            height: 32,
                            backgroundColor: c.error,
                            borderWidth: 2,
                            borderColor: c.ink,
                          }}
                        >
                          <View
                            style={{
                              position: 'absolute',
                              left: '28%',
                              width: '44%',
                              height: '100%',
                              backgroundColor: c.positive,
                            }}
                          />
                          <View
                            style={{
                              position: 'absolute',
                              left: '46%',
                              width: '8%',
                              height: '100%',
                              backgroundColor: c.gold,
                            }}
                          />
                          <View
                            style={{
                              position: 'absolute',
                              left: `${cursor * 98}%`,
                              width: 4,
                              height: '100%',
                              backgroundColor: c.ink,
                            }}
                          />
                        </View>
                      </Pressable>
                    </View>
                  ) : phase === 'block' ? (
                    <PixelButton label="BLOCK!" gold haptic={false} onPress={blockTap} />
                  ) : (
                    <>
                      <BodyText style={{ textAlign: 'center' }}>
                        {phase === 'choose'
                          ? auto
                            ? 'AUTO · 2X SPEED'
                            : lifted !== null && combat.a.hand[lifted]
                              ? cardDetails[combat.a.hand[lifted]]
                              : 'LIFT A CARD · TAP AGAIN TO PLAY'
                          : request.practice
                            ? 'SPARRING IN PROGRESS…'
                            : 'RAID IN PROGRESS…'}
                      </BodyText>
                      <ScrollView
                        horizontal
                        showsHorizontalScrollIndicator={false}
                        contentContainerStyle={{ gap: 12, paddingTop: 12, paddingBottom: 8 }}
                      >
                        {handCards.map(({ id, key }, index) => (
                          <View key={key} style={{ width: handCardWidth(width, handCards.length) }}>
                            <HabitCard
                              id={id}
                              species={player.species}
                              guided={
                                cardLesson &&
                                index ===
                                  combat.a.hand.findIndex((card) => available(card, combat.a))
                              }
                              selected={lifted === index}
                              disabled={!enabled || !available(id, combat.a)}
                              onPress={() => {
                                if (!enabled) return;
                                if (lifted === index) select(id);
                                else {
                                  setCardLesson(false);
                                  setLifted(index);
                                  feedback('select');
                                }
                              }}
                            />
                          </View>
                        ))}
                      </ScrollView>
                    </>
                  )}
                </View>
                <BodyText style={{ textAlign: 'center', fontSize: 11 }}>
                  DRAW {combat.a.draw.length} · DISCARD {combat.a.discard.length}
                </BodyText>
              </>
            )}
          </ScrollView>
          {finished ? (
            <PixelButton
              label={paused ? 'CONTINUE · TAKE A NAP' : 'CONTINUE'}
              onPress={() => {
                if (committed.current || !active()) return;
                committed.current = true;
                gameStore.getState().finishBattle(combat.result!, target, request.practice);
                if (paused) gameStore.getState().sleep();
              }}
            />
          ) : (
            <View style={{ flexDirection: 'row', gap: 12 }}>
              <View style={{ flex: 1 }}>
                <PixelButton
                  label={enabled ? 'PASS · +1 ENERGY' : 'WAIT YOUR TURN'}
                  small
                  haptic={false}
                  disabled={!enabled}
                  onPress={() => select('pass')}
                />
              </View>
              <View style={{ flex: 1 }}>
                <PixelButton
                  label={request.practice ? 'LEAVE' : 'CANCEL'}
                  small
                  light
                  onPress={() => gameStore.setState({ battle: null })}
                />
              </View>
            </View>
          )}
        </View>
        <BattleIntro skip={skip} />
        {flash && !reduced && (
          <View
            pointerEvents="none"
            style={[StyleSheet.absoluteFill, { backgroundColor: c.flash }]}
          />
        )}
      </View>
    </PerfectImpact>
  );
}
