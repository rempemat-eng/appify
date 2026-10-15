import { useCallback, useEffect, useRef, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, View, useWindowDimensions } from 'react-native';
import { Bell, Shield, FastForward, ChevronDown } from 'lucide-react-native';
import Animated, {
  FadeIn,
  FadeOut,
  SlideInLeft,
  SlideInRight,
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withTiming,
} from 'react-native-reanimated';
import { feedback, palette as c, gameStore, type BattleRequest, type Player } from '@/lib/game';
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
import { EnergyPips, Meter, Pet, PixelButton, PixelText, styles } from '@/components/game-ui';
import { PixelScene, RaidGarden } from '@/components/pixel-scenes';
import { grasslingName, grasslings } from '@/lib/grasslings';
import { GrassFlight } from '@/components/grassling-feedback';
import { BodyText, BattleIntro, Pulse } from '@/components/pixel-feedback';
import { HabitCard } from '@/components/habit-cards';
import { cardDetails } from '@/lib/cards';

type Phase = 'choose' | 'timing' | 'block' | 'resolve' | 'waiting' | 'skipped' | 'end';
function Damage({ amount }: { amount: number }) {
  const y = useSharedValue(0);
  const opacity = useSharedValue(1);
  const reduced = useReducedMotion();
  useEffect(() => {
    y.set(withTiming(reduced ? 0 : -30, { duration: 700 }));
    opacity.set(withTiming(0, { duration: 800 }));
  }, [opacity, reduced, y]);
  const animated = useAnimatedStyle(() => ({
    opacity: opacity.value,
    transform: [{ translateY: y.value }],
  }));
  return (
    <Animated.View
      style={[
        {
          position: 'absolute',
          top: 0,
          left: 12,
          zIndex: 5,
          backgroundColor: c.paper,
          padding: 8,
          borderWidth: 2,
          borderColor: c.ink,
        },
        animated,
      ]}
    >
      <PixelText style={{ fontSize: 16 }}>-{amount}</PixelText>
    </Animated.View>
  );
}
function Info({ p, f }: { p: Player; f: Fighter }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <View style={{ backgroundColor: c.body, borderWidth: 2, borderColor: c.shade }}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={`${grasslingName(p)}, ${f.hp} of ${maxHp(p)} HP, ${f.energy} energy. Show details`}
        accessibilityState={{ expanded }}
        onPress={() => {
          setExpanded(!expanded);
          feedback('select');
        }}
        style={{ flexDirection: 'row', alignItems: 'center', gap: 8, padding: 6 }}
      >
        <BodyText numberOfLines={1} style={{ width: 110, fontSize: 11 }}>
          {grasslingName(p)}
        </BodyText>
        <View style={{ flex: 1 }}>
          <Meter value={f.hp} max={maxHp(p)} height={10} />
        </View>
        <EnergyPips value={f.energy} />
        <ChevronDown size={14} color={c.ink} />
      </Pressable>
      {expanded && (
        <View style={{ padding: 8, flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
          <BodyText>
            LV {p.level} · {p.id === 'bot' ? 'WEED' : grasslings[p.species].habit} · ZEN{' '}
            {Math.round(zen(p) * 100)}% · {f.hp}/{maxHp(p)} HP
          </BodyText>
          {f.guard && <Shield accessibilityLabel="Guarded" size={14} color={c.ink} />}
          {f.notified && (
            <Bell accessibilityLabel="Distracted, next turn skipped" size={14} color={c.ink} />
          )}
          {f.nextEnergy > 0 && <BodyText>+1 ENERGY NEXT TURN</BodyText>}
        </View>
      )}
    </View>
  );
}
export function BattleScreen({ request }: { request: BattleRequest }) {
  const [player] = useState(() => gameStore.getState().player!);
  const reduced = useReducedMotion();
  const { width } = useWindowDimensions();
  const petSize = Math.min(192, Math.floor(Math.min(width, 640) / 64) * 32);
  const [lifted, setLifted] = useState<number | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [stageHeight, setStageHeight] = useState(280);
  const target = request.target;
  const [combat, setCombat] = useState(() => createCombat(player, target));
  const combatRef = useRef(combat);
  const [phase, setPhase] = useState<Phase>('choose');
  const phaseRef = useRef<Phase>('choose');
  const [auto, setAuto] = useState(false);
  const autoRef = useRef(false);
  const [cursor, setCursor] = useState(0);
  const timingStart = useRef(0);
  const selected = useRef<Move>('stretch');
  const timing = useRef(1);
  const blocked = useRef(false);
  const blockWindow = useRef(600);
  const blockAuto = useRef(false);
  const [hit, setHit] = useState({ a: 0, d: 0 });
  const [attack, setAttack] = useState({ a: 0, d: 0 });
  const [damage, setDamage] = useState<(Impact & { id: number }) | null>(null);
  const [log, setLog] = useState('YOUR TURN. LIFT A CARD, TAP AGAIN TO PLAY.');
  const [flash, setFlash] = useState(false);
  const [history, setHistory] = useState<{ id: number; line: string }[]>([]);
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
  const record = useCallback((line: string) => {
    const entry = { id: ++historyId.current, line };
    setLog(line);
    setHistory((old) => [...old.slice(-23), entry]);
  }, []);
  const select = useCallback(
    (move: Move) => {
      if (phaseRef.current !== 'choose' || !active() || !available(move, combatRef.current.a))
        return;
      selected.current = move;
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
      record('RAID TIMED OUT');
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
      timing.current = computerTiming();
      blocked.current = false;
      if (damaging(move)) {
        blockAuto.current = autoRef.current;
        blockWindow.current = blockAuto.current ? 300 : 600;
        timingStart.current = Date.now();
        changePhase('block');
      } else changePhase('resolve');
    }
  }, [active, changePhase, publish, record, target]);
  useEffect(() => {
    const phaseAuto = autoRef.current;
    if (phase === 'timing') {
      let frame = 0;
      function sweep() {
        if (phaseRef.current !== 'timing') return;
        const progress = Math.min(1, (Date.now() - timingStart.current) / 1200);
        setCursor(progress);
        if (progress < 1) frame = requestAnimationFrame(sweep);
        else {
          timing.current = 0.6;
          phaseRef.current = 'resolve';
          setPhase('resolve');
        }
      }
      frame = requestAnimationFrame(sweep);
      return () => cancelAnimationFrame(frame);
    }
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
      const move = selected.current;
      if (damaging(move)) setAttack((old) => ({ ...old, [side]: old[side] + 1 }));
      if (move === 'digital_sunset') setFlash(true);
      const timers: ReturnType<typeof setTimeout>[] = [];
      const speed = phaseAuto ? 0.5 : 1;
      if (move === 'digital_sunset') timers.push(setTimeout(() => setFlash(false), 180 * speed));
      const timer = setTimeout(() => {
        if (!active()) return;
        const resolution = resolveMove(
          combatRef.current,
          move,
          { a: player, d: target },
          timing.current,
          blocked.current,
        );
        combatRef.current = resolution.state;
        const impacts = resolution.impacts;
        if (!impacts.length) setCombat(resolution.state);
        record(resolution.log);
        impacts.forEach((impact, i) => {
          timers.push(
            setTimeout(
              () => {
                if (!active()) return;
                setCombat({
                  ...resolution.state,
                  [impact.side]: { ...resolution.state[impact.side], hp: impact.hp },
                });
                setHit((old) => ({ ...old, [impact.side]: old[impact.side] + 1 }));
                setDamage({ ...impact, id: Date.now() + i });
                feedback('hit');
              },
              i * 200 * speed,
            ),
          );
        });
        timers.push(
          setTimeout(
            () => {
              setFlash(false);
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
        setFlash(false);
      };
    }
    return undefined;
  }, [phase, player, target, active, nextTurn, record]);
  useEffect(() => {
    if (phase !== 'choose' || !auto) return undefined;
    const timer = setTimeout(() => select(chooseAI(combatRef.current.a, player)), 200);
    return () => clearTimeout(timer);
  }, [auto, phase, player, select]);
  const finished = phase === 'end' && combat.result !== null;
  const enabled = phase === 'choose' && !auto;
  const handCounts = new Map<string, number>();
  const handCards = combat.a.hand.map((id) => {
    const occurrence = (handCounts.get(id) ?? 0) + 1;
    handCounts.set(id, occurrence);
    return { id, key: `${id}-${occurrence}` };
  });
  return (
    <View style={{ flex: 1, backgroundColor: c.paper }}>
      <View pointerEvents="none" style={StyleSheet.absoluteFill}>
        <PixelScene
          species={target.species}
          level={target.level}
          style={{ height: '100%', borderWidth: 0 }}
        />
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
            <BodyText>ROUND {Math.max(combat.a.turns, combat.d.turns)}/12</BodyText>
          </View>
          <Pressable
            accessibilityRole="switch"
            accessibilityState={{ checked: auto }}
            accessibilityLabel="Auto raid at double speed"
            onPress={() => {
              const value = !autoRef.current;
              autoRef.current = value;
              setAuto(value);
              setLifted(null);
              feedback('select');
            }}
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              gap: 5,
              padding: 8,
              borderWidth: 2,
              borderColor: c.ink,
              backgroundColor: auto ? c.gold : c.body,
            }}
          >
            <PixelText>AUTO</PixelText>
            <FastForward size={16} color={c.ink} />
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
          onLayout={(event) => setStageHeight(event.nativeEvent.layout.height)}
          style={{
            flex: 1,
            minHeight: 280,
            flexDirection: 'row',
            alignItems: 'flex-end',
            justifyContent: 'space-around',
            paddingBottom: (stageHeight * 14) / 64,
          }}
        >
          <RaidGarden attacker={player} defender={target} />
          <Animated.View
            entering={reduced ? FadeIn.duration(150) : SlideInLeft.delay(780).duration(240)}
            style={{ width: petSize }}
          >
            <Pet
              species={player.species}
              level={player.level}
              hat={player.hat}
              facing="right"
              grumpy={player.mood < 30}
              size={petSize}
              bob={false}
              hit={hit.a}
              attack={attack.a}
              slumped={combat.a.hp <= 0 || (finished && combat.result === false)}
              victory={finished && combat.result === true}
            />
            {damage?.side === 'a' && <Damage key={damage.id} amount={damage.amount} />}
          </Animated.View>
          <Animated.View
            entering={reduced ? FadeIn.duration(150) : SlideInRight.delay(780).duration(240)}
            style={{ width: petSize }}
          >
            <Pet
              species={target.species}
              level={target.level}
              hat={target.hat}
              facing="left"
              dave={target.id === 'bot'}
              grumpy={target.mood < 30}
              size={petSize}
              bob={false}
              hit={hit.d}
              attack={attack.d}
              slumped={combat.d.hp <= 0 || (finished && combat.result === true)}
              victory={finished && combat.result === false}
            />
            {damage?.side === 'd' && <Damage key={damage.id} amount={damage.amount} />}
          </Animated.View>
          {finished && combat.result && !request.practice && <GrassFlight />}
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Expand raid log"
          accessibilityState={{ expanded: showHistory }}
          onPress={() => {
            setShowHistory(!showHistory);
            feedback('select');
          }}
          style={{ backgroundColor: c.paper, paddingHorizontal: 12, paddingVertical: 6 }}
        >
          <BodyText accessibilityLiveRegion="polite" numberOfLines={showHistory ? undefined : 2}>
            {log}
          </BodyText>
        </Pressable>
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
          backgroundColor: c.paper,
          padding: 10,
          gap: 8,
          borderTopWidth: 2,
          borderColor: c.ink,
          width: '100%',
          maxWidth: 640,
          alignSelf: 'center',
        }}
      >
        {finished ? (
          <Animated.View entering={FadeIn} exiting={FadeOut} style={{ gap: 14 }}>
            <PixelText style={{ textAlign: 'center', fontSize: 16 }}>
              {combat.result ? 'VICTORY!' : 'RAID FAILED.'}
            </PixelText>
            <PixelButton
              label="CONTINUE"
              onPress={() => {
                if (committed.current || !active()) return;
                committed.current = true;
                gameStore.getState().finishBattle(combat.result!, target, request.practice);
              }}
            />
          </Animated.View>
        ) : (
          <>
            {phase === 'timing' ? (
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Tap the action bar in the centre"
                onPress={attackTap}
                style={[styles.border, { padding: 10, gap: 8, backgroundColor: c.body }]}
              >
                <PixelText style={{ textAlign: 'center' }}>TAP IN THE CENTRE!</PixelText>
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
            ) : phase === 'block' ? (
              <PixelButton label="BLOCK!" gold onPress={blockTap} />
            ) : (
              <BodyText style={{ textAlign: 'center' }}>
                {phase === 'choose'
                  ? auto
                    ? 'AUTO · 2X SPEED'
                    : lifted === null
                      ? 'LIFT A CARD · TAP AGAIN TO PLAY'
                      : 'TAP LIFTED CARD TO PLAY'
                  : 'RAID IN PROGRESS...'}
              </BodyText>
            )}
            {lifted !== null && enabled && combat.a.hand[lifted] && (
              <BodyText style={{ fontSize: 11, lineHeight: 16 }}>
                {cardDetails[combat.a.hand[lifted]]}
              </BodyText>
            )}
            <View style={{ flexDirection: 'row', gap: 5, paddingTop: 10 }}>
              {handCards.map(({ id, key }, index) => (
                <HabitCard
                  key={key}
                  id={id}
                  compact={combat.a.handLimit === 4}
                  species={player.species}
                  selected={lifted === index}
                  disabled={!enabled || !available(id, combat.a)}
                  onPress={() => {
                    if (!enabled) return;
                    if (lifted === index) select(id);
                    else {
                      setLifted(index);
                      feedback('select');
                    }
                  }}
                />
              ))}
            </View>
            <BodyText style={{ textAlign: 'center', fontSize: 11 }}>
              DRAW {combat.a.draw.length} · DISCARD {combat.a.discard.length}
            </BodyText>
            <View style={{ flexDirection: 'row', gap: 8 }}>
              <View style={{ flex: 1 }}>
                <PixelButton
                  label="PASS · +1E"
                  small
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
          </>
        )}
      </View>
      <BattleIntro />
      {flash && (
        <View
          pointerEvents="none"
          style={[StyleSheet.absoluteFill, { backgroundColor: c.flash }]}
        />
      )}
    </View>
  );
}
