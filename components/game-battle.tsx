import { useEffect, useRef, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import Animated, {
  FadeIn,
  FadeOut,
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withTiming,
} from 'react-native-reanimated';
import { feedback, palette as c, gameStore, type BattleRequest, type Player } from '@/lib/game';
import { Meter, Pet, PixelButton, PixelText, styles } from '@/components/game-ui';
const moves = {
  BLOB: ['BLOB SLAM', 'GOO SPIT', 'TOUCH GRASS'],
  RAT: ['PING SPAM', 'CABLE CHEW', 'TOUCH GRASS'],
  CUBE: ['BLUE LIGHT BEAM', 'GLITCH SLAP', 'TOUCH GRASS'],
};
function atk(p: Player) {
  return (5 + 2 * p.level) * (p.mood < 30 ? 0.7 : 1);
}
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
          left: 20,
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
function Info({ p, hp }: { p: Player; hp: number }) {
  return (
    <View style={[styles.border, { padding: 10, gap: 8, flex: 1, backgroundColor: c.body }]}>
      <PixelText numberOfLines={1}>{p.pet_name}</PixelText>
      <PixelText>LV {p.level}</PixelText>
      <Meter value={hp} max={50 + 10 * p.level} />
      <PixelText style={{ fontSize: 11 }}>
        {hp}/{50 + 10 * p.level} HP
      </PixelText>
    </View>
  );
}
export function BattleScreen({ request }: { request: BattleRequest }) {
  const player = useRef(gameStore.getState().player!).current;
  const target = request.target;
  const [splash, setSplash] = useState(true);
  const [hp, setHp] = useState({ a: 50 + 10 * player.level, d: 50 + 10 * target.level });
  const hpRef = useRef(hp);
  const [hit, setHit] = useState({ a: 0, d: 0 });
  const [damage, setDamage] = useState<{ side: 'a' | 'd'; amount: number; id: number } | null>(
    null,
  );
  const [log, setLog] = useState('THE BATTLE BEGINS!');
  const [flash, setFlash] = useState(false);
  const [abilityUsed, setAbilityUsed] = useState(false);
  const abilityRef = useRef(false);
  const defenderUsed = useRef(false);
  const turn = useRef(0);
  const [result, setResult] = useState<boolean | null>(null);
  const resultRef = useRef<boolean | null>(null);
  const flashTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const moveRef = useRef<(side: 'a' | 'd', ability?: boolean) => void>(() => {});
  function strike(side: 'a' | 'd', ability = false) {
    if (resultRef.current !== null || gameStore.getState().battle !== request) return;
    const source = side === 'a' ? player : target;
    const victim = side === 'a' ? target : player;
    const dest = side === 'a' ? 'd' : 'a';
    const critical = !ability && Math.random() < 0.15;
    const amount = Math.floor(
      (ability ? 25 : (atk(source) + Math.floor(Math.random() * 6)) * (critical ? 2 : 1)) *
        (victim.level >= 3 ? 0.8 : 1),
    );
    const next = { ...hpRef.current, [dest]: Math.max(0, hpRef.current[dest] - amount) };
    hpRef.current = next;
    setHp(next);
    setHit((old) => ({ ...old, [dest]: old[dest] + 1 }));
    setDamage({ side: dest, amount, id: Date.now() });
    setLog(
      `${source.pet_name} USED ${ability ? 'SCREEN BREAK' : moves[source.species][Math.floor(Math.random() * 3)]}!\n-${amount}${critical ? ' CRITICAL!' : ''}`,
    );
    feedback('hit');
    if (ability) {
      setFlash(true);
      if (flashTimeout.current) clearTimeout(flashTimeout.current);
      flashTimeout.current = setTimeout(() => setFlash(false), 180);
    }
    if (next[dest] <= 0) {
      const won = dest === 'd';
      resultRef.current = won;
      setResult(won);
      setLog(won ? `${target.pet_name} FAINTED!` : `${player.pet_name} FAINTED!`);
      return;
    }
    if (
      dest === 'd' &&
      target.level >= 2 &&
      !defenderUsed.current &&
      next.d < (50 + 10 * target.level) / 2
    ) {
      defenderUsed.current = true;
      strike('d', true);
    }
  }
  moveRef.current = strike;
  useEffect(() => {
    const start = setTimeout(() => setSplash(false), 1000);
    return () => {
      clearTimeout(start);
      if (flashTimeout.current) clearTimeout(flashTimeout.current);
    };
  }, []);
  useEffect(() => {
    if (splash) return undefined;
    const timer = setInterval(() => {
      if (resultRef.current !== null) return;
      moveRef.current(turn.current % 2 === 0 ? 'a' : 'd');
      turn.current += 1;
    }, 1000);
    return () => clearInterval(timer);
  }, [splash]);
  if (splash)
    return (
      <View
        style={{
          flex: 1,
          justifyContent: 'center',
          alignItems: 'center',
          gap: 24,
          padding: 24,
          backgroundColor: c.ink,
        }}
      >
        <Pet species={target.species} hat={target.hat} size={110} />
        <PixelText style={{ color: c.paper, textAlign: 'center', fontSize: 16, lineHeight: 28 }}>
          {`${player.pet_name}\nVS\n${target.pet_name}`}
        </PixelText>
        <Pet species={player.species} hat={player.hat} size={110} />
      </View>
    );
  return (
    <View
      style={{
        flex: 1,
        justifyContent: 'space-between',
        padding: 18,
        gap: 16,
        backgroundColor: c.paper,
      }}
    >
      <PixelText style={{ textAlign: 'center', fontSize: 14 }}>
        {request.practice ? 'TRAINING BATTLE' : 'RIVAL RAID'}
      </PixelText>
      <View style={{ flex: 1, justifyContent: 'space-evenly', gap: 28 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 14 }}>
          <Info p={target} hp={hp.d} />
          <View style={{ width: 104, alignItems: 'center' }}>
            <Pet
              species={target.species}
              hat={target.hat}
              grumpy={target.mood < 30}
              size={100}
              hit={hit.d}
            />
            {damage?.side === 'd' && <Damage key={damage.id} amount={damage.amount} />}
          </View>
        </View>
        <View style={{ height: 2, backgroundColor: c.shade }} />
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 14 }}>
          <View style={{ width: 104, alignItems: 'center' }}>
            <Pet
              species={player.species}
              hat={player.hat}
              grumpy={player.mood < 30}
              size={100}
              hit={hit.a}
            />
            {damage?.side === 'a' && <Damage key={damage.id} amount={damage.amount} />}
          </View>
          <Info p={player} hp={hp.a} />
        </View>
      </View>
      <View style={[styles.border, { padding: 16, minHeight: 100, backgroundColor: c.body }]}>
        <PixelText>{log}</PixelText>
      </View>
      {result !== null ? (
        <Animated.View entering={FadeIn} exiting={FadeOut} style={{ gap: 14 }}>
          <PixelText style={{ textAlign: 'center', fontSize: 16 }}>
            {result ? 'VICTORY!' : 'RAID FAILED.'}
          </PixelText>
          <PixelButton
            label="CONTINUE"
            onPress={() => gameStore.getState().finishBattle(result, target, request.practice)}
          />
        </Animated.View>
      ) : (
        <View style={{ gap: 12 }}>
          {player.level >= 2 && (
            <PixelButton
              label={abilityUsed ? 'SCREEN BREAK USED' : 'SCREEN BREAK · 25 DMG'}
              disabled={abilityUsed}
              onPress={() => {
                if (abilityRef.current) return;
                abilityRef.current = true;
                setAbilityUsed(true);
                strike('a', true);
              }}
            />
          )}
          <PixelButton
            label="CANCEL BATTLE"
            small
            light
            onPress={() => gameStore.setState({ battle: null })}
          />
        </View>
      )}
      {flash && (
        <View
          pointerEvents="none"
          style={[StyleSheet.absoluteFill, { backgroundColor: c.flash }]}
        />
      )}
    </View>
  );
}
