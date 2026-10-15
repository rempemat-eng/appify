import { useCallback, useEffect, useRef, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { Bell, Smartphone, Shield, Snail, Leaf, FastForward } from 'lucide-react-native';
import Animated, {
  FadeIn,
  FadeOut,
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
  costs,
  createCombat,
  damaging,
  maxHp,
  moveName,
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
  return (
    <View style={[styles.border, { padding: 10, gap: 5, flex: 1, backgroundColor: c.body }]}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 5, flexWrap: 'wrap' }}>
        <PixelText numberOfLines={1} style={{ flexShrink: 1 }}>
          {p.pet_name}
        </PixelText>
        {f.guard && <Shield accessibilityLabel="Guard" size={14} color={c.ink} />}
        {f.slowed && <Snail accessibilityLabel="Slowed" size={14} color={c.ink} />}
        {f.notified && <Bell accessibilityLabel="Notification" size={14} color={c.ink} />}
        {f.doom && <Smartphone accessibilityLabel="Doomscrolling" size={14} color={c.ink} />}
      </View>
      <PixelText>
        LV {p.level} · {p.species}
      </PixelText>
      <Meter value={f.hp} max={maxHp(p)} />
      <EnergyPips value={f.energy} />
      <PixelText>
        {f.hp}/{maxHp(p)} HP
      </PixelText>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
        <Leaf size={14} color={c.ink} />
        <PixelText>ZEN {Math.round(zen(p) * 100)}%</PixelText>
      </View>
    </View>
  );
}

export function BattleScreen({ request }: { request: BattleRequest }) {
  // Snapshot the player for this battle; refs below are only action/timer locks.
  const [player] = useState(() => gameStore.getState().player!);
  const target = request.target;
  const [combat, setCombat] = useState(() => createCombat(player, target));
  const combatRef = useRef(combat);
  const [phase, setPhase] = useState<Phase>('choose');
  const phaseRef = useRef<Phase>('choose');
  const [auto, setAuto] = useState(false);
  const autoRef = useRef(false);
  const [cursor, setCursor] = useState(0);
  const timingStart = useRef(0);
  const selected = useRef<Move>('quick');
  const timing = useRef(1);
  const blocked = useRef(false);
  const blockWindow = useRef(600);
  const blockAuto = useRef(false);
  const [hit, setHit] = useState({ a: 0, d: 0 });
  const [attack, setAttack] = useState({ a: 0, d: 0 });
  const [damage, setDamage] = useState<(Impact & { id: number }) | null>(null);
  const [log, setLog] = useState('YOUR TURN. CHOOSE A MOVE.');
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
      if (
        phaseRef.current !== 'choose' ||
        !active() ||
        !available(move, combatRef.current.a, player)
      )
        return;
      selected.current = move;
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
    [active, changePhase, player],
  );
  function attackTap() {
    if (phaseRef.current !== 'timing') return;
    const progress = Math.min(1, (Date.now() - timingStart.current) / 1200);
    timing.current = timingAt(progress);
    feedback('select');
    changePhase('resolve');
  }
  function blockTap() {
    if (phaseRef.current !== 'block') return;
    // A late tap is not a block, even if the timeout has not been delivered yet.
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
      record('DISTRACTED BY A NOTIFICATION!');
      changePhase('skipped');
      return;
    }
    if (side === 'a') {
      changePhase('choose');
    } else {
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
  // Every phase owns its timers. Leaving a phase or cancelling a battle cancels its work.
  useEffect(() => {
    // AUTO is sampled once per phase, never a dependency of in-flight resolution.
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
      if (move === 'break') setFlash(true);
      const timers: ReturnType<typeof setTimeout>[] = [];
      const speed = phaseAuto ? 0.5 : 1;
      if (move === 'break') timers.push(setTimeout(() => setFlash(false), 180 * speed));
      const timer = setTimeout(() => {
        if (!active()) return;
        const resolution = resolveMove(
          combatRef.current,
          move,
          { a: player, d: target },
          timing.current,
          blocked.current,
        );
        // Commit only once, then animate each hit without changing battle/reward state.
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
    // autoRef applies to the next phase, so toggling AUTO never restarts an in-flight attack.
  }, [phase, player, target, active, nextTurn, record]);
  useEffect(() => {
    if (phase !== 'choose' || !auto) return undefined;
    const timer = setTimeout(() => select(chooseAI(combatRef.current.a, player)), 200);
    return () => clearTimeout(timer);
  }, [auto, phase, player, select]);
  const finished = phase === 'end' && combat.result !== null;
  const enabled = phase === 'choose' && !auto;
  const moveButton = (move: Move) => (
    <PixelButton
      label={moveName(move, player)}
      energyCost={costs[move]}
      small
      light={move !== 'heal'}
      disabled={!enabled || !available(move, combat.a, player)}
      onPress={() => select(move)}
    />
  );
  return (
    <View style={{ flex: 1, backgroundColor: c.paper }}>
      <View
        style={{
          paddingHorizontal: 16,
          paddingVertical: 12,
          gap: 10,
          borderBottomWidth: 2,
          borderColor: c.ink,
        }}
      >
        <PixelText style={{ textAlign: 'center', fontSize: 14 }}>
          {request.practice ? 'TRAINING BATTLE' : 'RIVAL RAID'}
        </PixelText>
        <View
          style={{
            flexDirection: 'row',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <PixelText>ROUND {Math.max(combat.a.turns, combat.d.turns)}/12</PixelText>
          <Pressable
            accessibilityRole="switch"
            accessibilityState={{ checked: auto }}
            accessibilityLabel="Auto battle at double speed"
            onPress={() => {
              const value = !autoRef.current;
              autoRef.current = value;
              setAuto(value);
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
            <PixelText>{auto ? 'ON' : 'OFF'}</PixelText>
          </Pressable>
        </View>
      </View>
      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={{
          padding: 14,
          gap: 16,
          width: '100%',
          maxWidth: 640,
          alignSelf: 'center',
        }}
      >
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
          <Info p={target} f={combat.d} />
          <View style={{ width: 96 }}>
            <Pet
              species={target.species}
              level={target.level}
              hat={target.hat}
              facing="left"
              grumpy={target.mood < 30}
              size={96}
              bob={false}
              hit={hit.d}
              attack={attack.d}
            />
            {damage?.side === 'd' && <Damage key={damage.id} amount={damage.amount} />}
          </View>
        </View>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
          <View style={{ width: 96 }}>
            <Pet
              species={player.species}
              level={player.level}
              hat={player.hat}
              grumpy={player.mood < 30}
              size={96}
              bob={false}
              hit={hit.a}
              attack={attack.a}
            />
            {damage?.side === 'a' && <Damage key={damage.id} amount={damage.amount} />}
          </View>
          <Info p={player} f={combat.a} />
        </View>
        <View
          accessibilityLiveRegion="polite"
          style={[styles.border, { padding: 12, minHeight: 84, backgroundColor: c.body }]}
        >
          <PixelText>{log}</PixelText>
        </View>
        {history.length > 1 && (
          <View style={{ gap: 8 }}>
            <PixelText>BATTLE LOG</PixelText>
            {history.slice(0, -1).map((entry) => (
              <PixelText key={entry.id} style={{ color: c.shade }}>
                {entry.line}
              </PixelText>
            ))}
          </View>
        )}
      </ScrollView>
      <View
        style={{
          padding: 14,
          gap: 10,
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
                style={[styles.border, { padding: 12, gap: 10, backgroundColor: c.body }]}
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
              <PixelText style={{ textAlign: 'center' }}>
                {phase === 'choose'
                  ? auto
                    ? 'AUTO · 2X SPEED'
                    : 'CHOOSE YOUR MOVE'
                  : 'BATTLE IN PROGRESS...'}
              </PixelText>
            )}
            <View style={{ flexDirection: 'row', gap: 8 }}>
              <View style={{ flex: 1 }}>{moveButton('quick')}</View>
              <View style={{ flex: 1 }}>{moveButton('signature')}</View>
            </View>
            <View style={{ flexDirection: 'row', gap: 8 }}>
              <View style={{ flex: 1 }}>{moveButton('guard')}</View>
              <View style={{ flex: 1 }}>{moveButton('heal')}</View>
            </View>
            {player.level >= 2 && (
              <PixelButton
                label={combat.a.breakUsed ? 'SCREEN BREAK USED' : 'SCREEN BREAK'}
                energyCost={3}
                small
                gold
                disabled={!enabled || !available('break', combat.a, player)}
                onPress={() => select('break')}
              />
            )}
            <PixelButton
              label="CANCEL BATTLE"
              small
              light
              onPress={() => gameStore.setState({ battle: null })}
            />
          </>
        )}
      </View>
      {flash && (
        <View
          pointerEvents="none"
          style={[StyleSheet.absoluteFill, { backgroundColor: c.flash }]}
        />
      )}
    </View>
  );
}
