import { useEffect, useRef, useState } from 'react';
import {
  Pressable,
  KeyboardAvoidingView,
  Modal,
  Platform,
  ScrollView,
  TextInput,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Shield, Swords } from 'lucide-react-native';
import {
  bot,
  clock,
  feedback,
  missions,
  palette as c,
  useGame,
  gameStore,
  type Player,
} from '@/lib/game';
import { DeckPanel } from '@/components/habit-cards';
import { BattleScreen } from '@/components/game-battle';
import { FloatingZ, Pet, PixelButton, PixelText, styles } from '@/components/game-ui';
import { SeedPacket, Planting, PetalFall, GrassFlight } from '@/components/grassling-feedback';
import { grasslings, growthStage } from '@/lib/grasslings';
import { PixelScene } from '@/components/pixel-scenes';
import { BodyText, Dialogue, Pulse } from '@/components/pixel-feedback';
import Animated, { FadeIn, SlideInDown, useReducedMotion } from 'react-native-reanimated';
function Onboarding() {
  const [step, setStep] = useState(0);
  const [species, setSpecies] = useState<Player['species']>('BLOB');
  const [name, setName] = useState('');
  const [petName, setPetName] = useState('PIXEL');
  const [error, setError] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const bottom = useSafeAreaInsets().bottom;
  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
    },
    [],
  );
  function hatch() {
    if (!name.trim()) {
      setError(true);
      feedback('error');
      return;
    }
    setStep(2);
    timer.current = setTimeout(() => {
      void gameStore.getState().hatch(name, petName, species);
    }, 1400);
  }
  if (step === 2)
    return (
      <View
        style={{
          flex: 1,
          backgroundColor: c.paper,
          alignItems: 'center',
          justifyContent: 'center',
          gap: 30,
        }}
      >
        <PixelScene
          kind="nest"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            height: '100%',
            borderWidth: 0,
          }}
        />
        <Planting>
          <Pet species={species} size={192} bob={false} />
        </Planting>
        <PixelText style={{ fontSize: 17 }}>PLANTED!</PixelText>
      </View>
    );
  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: c.paper }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={{
          flexGrow: 1,
          padding: 24,
          paddingTop: 32,
          gap: 26,
          width: '100%',
          maxWidth: 560,
          alignSelf: 'center',
        }}
      >
        <View style={{ gap: 16 }}>
          <PixelText style={{ fontSize: 21, lineHeight: 33 }}>{'SCREENA\nGOTCHI'}</PixelText>
          <View style={{ height: 4, backgroundColor: c.night, width: 52 }} />
          <PixelText style={{ fontSize: 11, lineHeight: 21 }}>
            {'PUT YOUR PHONE DOWN.\nGROW A GRASSLING.'}
          </PixelText>
        </View>
        {step === 0 ? (
          <>
            <PixelText style={{ fontSize: 14, lineHeight: 24, marginTop: 8 }}>
              CHOOSE YOUR SEED
            </PixelText>
            <PixelScene
              kind="nest"
              height={230}
              style={{ justifyContent: 'flex-end', paddingBottom: 32 }}
            >
              <View style={{ flexDirection: 'row', justifyContent: 'space-around', gap: 4 }}>
                {(['BLOB', 'RAT', 'CUBE'] as const).map((s) => (
                  <Pressable
                    key={s}
                    accessibilityRole="button"
                    accessibilityLabel={`Plant ${grasslings[s].name}, habit ${grasslings[s].habit}`}
                    onPress={() => {
                      setSpecies(s);
                      setStep(1);
                      feedback('select');
                    }}
                    style={{ alignItems: 'center', flex: 1, minHeight: 100, gap: 12 }}
                  >
                    <SeedPacket species={s} size={64} />
                    <BodyText style={{ backgroundColor: c.paper, padding: 3 }}>
                      {grasslings[s].name}
                    </BodyText>
                    <PixelText style={{ fontSize: 11, backgroundColor: c.paper, padding: 3 }}>
                      {grasslings[s].habit}
                    </PixelText>
                  </Pressable>
                ))}
              </View>
            </PixelScene>
            <BodyText style={{ textAlign: 'center' }}>
              Plant a seed. Offline time helps it grow.
            </BodyText>
          </>
        ) : (
          <>
            <PixelScene
              species={species}
              height={190}
              style={{ alignItems: 'center', justifyContent: 'flex-end', paddingBottom: 16 }}
            >
              <Planting key={species}>
                <Pet species={species} size={120} bob={false} />
              </Planting>
            </PixelScene>
            <PixelText>
              {grasslings[species].name} · {grasslings[species].habit}
            </PixelText>
            <Dialogue text={grasslings[species].line} />
            <View style={{ gap: 12 }}>
              <PixelText>GARDENER NAME</PixelText>
              <TextInput
                accessibilityLabel="Your name"
                value={name}
                onChangeText={(value) => {
                  setName(value);
                  setError(false);
                }}
                style={styles.input}
                autoCapitalize="characters"
                maxLength={10}
                placeholder="HUMAN"
                placeholderTextColor={c.shade}
                autoCorrect={false}
              />
              {error && <Dialogue text="give yourself a name." />}
            </View>
            <View style={{ gap: 12 }}>
              <PixelText>GRASSLING NAME</PixelText>
              <TextInput
                accessibilityLabel="Grassling name"
                value={petName}
                onChangeText={setPetName}
                style={styles.input}
                autoCapitalize="characters"
                maxLength={10}
                autoCorrect={false}
                onSubmitEditing={hatch}
              />
            </View>
          </>
        )}
      </ScrollView>
      <View
        style={{
          padding: 24,
          paddingBottom: bottom + 20,
          gap: 12,
          width: '100%',
          maxWidth: 560,
          alignSelf: 'center',
        }}
      >
        <PixelButton
          label={step === 0 ? 'PLANT A SEED' : 'GROW MY GARDEN'}
          onPress={() => (step === 0 ? setStep(1) : hatch())}
        />
        {step === 1 && <PixelButton label="CHANGE SEED" small light onPress={() => setStep(0)} />}
      </View>
    </KeyboardAvoidingView>
  );
}
function ScreenOff() {
  const p = useGame((s) => s.player)!;
  const now = useGame((s) => s.now);
  const offStart = useGame((s) => s.offStart);
  const offGrass = useGame((s) => s.offGrass);
  const m = missions.find((x) => x.id === p.mission_id);
  return (
    <View
      style={{
        flex: 1,
        backgroundColor: c.night,
        padding: 24,
        justifyContent: 'space-between',
        alignItems: 'stretch',
      }}
    >
      <View
        pointerEvents="none"
        style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
      >
        <PixelScene
          kind="night"
          species={p.species}
          level={p.level}
          player={p}
          style={{ height: '100%', borderWidth: 0 }}
        />
      </View>
      <View style={{ alignItems: 'center', gap: 16, paddingTop: 20 }}>
        <Shield color={c.paper} size={30} />
        <PixelText
          style={{
            color: c.paper,
            textAlign: 'center',
            fontSize: 13,
            lineHeight: 24,
            backgroundColor: c.night,
            padding: 8,
          }}
        >
          {'SCREEN OFF.\nGARDEN SHIELDED.'}
        </PixelText>
        {m && <PixelText style={{ color: c.paper, textAlign: 'center' }}>{m.name}</PixelText>}
      </View>
      <View style={{ alignItems: 'center', gap: 28 }}>
        {!m && <FloatingZ />}
        {m ? (
          <PixelScene
            player={p}
            species={p.species}
            level={p.level}
            kind={m.id === 'book' ? 'book' : m.id === 'mountain' ? 'mountain' : 'park'}
            height={225}
            style={{
              width: '100%',
              alignItems: 'center',
              justifyContent: 'flex-end',
              paddingBottom: 15,
            }}
          >
            <Pet species={p.species} level={p.level} hat={p.hat} walking size={160} />
          </PixelScene>
        ) : (
          <Pet species={p.species} level={p.level} hat={p.hat} sleeping size={160} />
        )}
        {m ? (
          <>
            <PixelText style={{ color: c.paper, fontSize: 26, lineHeight: 40 }}>
              {clock(Math.max(0, Math.ceil((p.mission_ends_at - now) / 1000)))}
            </PixelText>
            <PixelText style={{ color: c.body }}>UNTIL HOME · MIN</PixelText>
          </>
        ) : (
          <Pulse active color={c.gold} style={{ padding: 12, borderWidth: 2, borderColor: c.gold }}>
            <PixelText style={{ color: c.paper, textAlign: 'center', lineHeight: 26 }}>
              {`OFFLINE ${p.offline_seconds - offStart} MIN\n+${p.grass - offGrass} GRASS`}
            </PixelText>
          </Pulse>
        )}
      </View>
      <View style={{ gap: 18, paddingBottom: 24 }}>
        <PixelText style={{ color: c.body, textAlign: 'center' }}>
          {m ? 'WAKE EARLY = MISSION FAILED' : '+1 GRASS / MIN. KEEP IT DOWN.'}
        </PixelText>
        <PixelButton label="WAKE UP" light onPress={() => gameStore.getState().wake()} />
      </View>
    </View>
  );
}
function DefenderAlert() {
  const item = useGame((s) => s.alerts[0]);
  const [pending, setPending] = useState(false);
  const [slumped, setSlumped] = useState(true);
  useEffect(() => {
    const timer = setTimeout(() => setSlumped(false), 10000);
    return () => clearTimeout(timer);
  }, []);
  if (!item) return null;
  const a = item.attacker;
  const p = gameStore.getState().player!;
  async function revenge() {
    if (!a || pending) return;
    setPending(true);
    await gameStore.getState().startBattle(a.id === 'bot' ? bot(p) : a, a.id === 'bot', true);
    gameStore.getState().dismissAlert();
    setPending(false);
  }
  return (
    <View style={{ flex: 1, padding: 24, backgroundColor: c.paper }}>
      <View
        pointerEvents="none"
        style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
      >
        <PixelScene
          species={p.species}
          level={p.level}
          style={{ height: '100%', borderWidth: 0 }}
        />
      </View>
      <ScrollView
        contentContainerStyle={{
          flexGrow: 1,
          justifyContent: 'center',
          alignItems: 'center',
          gap: 24,
        }}
      >
        <Swords size={42} color={c.ink} />
        <PixelText
          style={{
            fontSize: 17,
            lineHeight: 30,
            textAlign: 'center',
            backgroundColor: c.paper,
            padding: 12,
          }}
        >
          {`${a?.name ?? 'A RIVAL'}\nRAIDED YOU!`}
        </PixelText>
        <Pet
          species={p.species}
          level={p.level}
          hat={p.hat}
          grumpy={p.mood < 30}
          slumped={slumped && item.raid.attacker_won}
          size={120}
        />
        {item.raid.attacker_won && <GrassFlight toLeft={false} />}
        <Dialogue
          text={
            item.raid.attacker_won
              ? `i wilted. they stole ${item.raid.grass_amount} grass`
              : 'raid repelled! +20 grass'
          }
          style={{ alignSelf: 'stretch' }}
        />
        <Shield size={26} color={c.ink} />
        <PixelText style={{ textAlign: 'center', backgroundColor: c.paper, padding: 8 }}>
          RECOVERY SHIELD: 60 MIN
        </PixelText>
      </ScrollView>
      <View style={{ gap: 12, paddingTop: 24 }}>
        <PixelButton
          label={pending ? 'CHECKING...' : 'REVENGE'}
          disabled={!a || pending}
          onPress={() => void revenge()}
        />
        <PixelButton label="OK" light onPress={() => gameStore.getState().dismissAlert()} />
      </View>
    </View>
  );
}
export function GameOverlays() {
  const ready = useGame((s) => s.ready);
  const p = useGame((s) => s.player);
  const battle = useGame((s) => s.battle);
  const alert = useGame((s) => s.alerts[0]);
  const message = useGame((s) => s.message);
  const flash = useGame((s) => s.flash);
  const deckOpen = useGame((s) => s.deckOpen);
  const cardReward = useGame((s) => s.cardReward);
  const insets = useSafeAreaInsets();
  const reduced = useReducedMotion();
  const isScreenOff = !!p && p.mode !== 'awake';
  const visible =
    !ready || !p || isScreenOff || !!battle || !!alert || !!flash || deckOpen || !!cardReward;
  useEffect(() => {
    if (!flash) return undefined;
    const timeout = setTimeout(() => useGame.setState({ flash: null }), 1600);
    return () => clearTimeout(timeout);
  }, [flash]);
  function dismiss() {
    if (!ready || !p) return;
    if (isScreenOff) gameStore.getState().wake();
    else if (battle) useGame.setState({ battle: null });
    else if (alert) gameStore.getState().dismissAlert();
    else if (cardReward || deckOpen) gameStore.getState().dismissCards();
    else useGame.setState({ message: null, flash: null });
  }
  return (
    <>
      <Modal visible={visible} animationType="none" statusBarTranslucent onRequestClose={dismiss}>
        <View
          style={{
            flex: 1,
            paddingTop: insets.top,
            paddingBottom: insets.bottom,
            backgroundColor: isScreenOff ? c.night : c.paper,
          }}
        >
          {!ready ? (
            <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: 20 }}>
              <PixelScene
                kind="nest"
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  height: '100%',
                  borderWidth: 0,
                }}
              />
              <Pet species="BLOB" walking size={64} />
              <BodyText>one moment. tiny legs.</BodyText>
            </View>
          ) : !p ? (
            <Onboarding />
          ) : isScreenOff ? (
            <ScreenOff />
          ) : battle ? (
            <BattleScreen key={`${battle.target.id}-${battle.practice}`} request={battle} />
          ) : alert ? (
            <DefenderAlert key={alert.raid.id} />
          ) : flash ? (
            <View
              style={{
                flex: 1,
                justifyContent: 'center',
                alignItems: 'center',
                gap: 32,
                padding: 24,
                backgroundColor: c.flash,
              }}
            >
              <PixelScene
                species={p.species}
                level={p.level}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  height: '100%',
                  borderWidth: 0,
                }}
              />
              <Pet
                species={p.species}
                level={p.level}
                hat={p.hat}
                victory={flash.includes('VICTORY')}
              />
              {flash.includes('BLOOMED') && <PetalFall />}
              <BodyText style={{ backgroundColor: c.paper, padding: 6 }}>
                {growthStage(p.level)}
              </BodyText>
              <PixelText
                style={{
                  fontSize: 16,
                  lineHeight: 30,
                  textAlign: 'center',
                  backgroundColor: c.paper,
                  padding: 12,
                }}
              >
                {flash}
              </PixelText>
            </View>
          ) : cardReward ? (
            <DeckPanel reward />
          ) : deckOpen ? (
            <DeckPanel />
          ) : null}
        </View>
      </Modal>
      {!visible && message && (
        <Animated.View
          key={message}
          entering={reduced ? FadeIn : SlideInDown.duration(180)}
          style={{
            position: 'absolute',
            top: insets.top + 12,
            left: 16,
            right: 16,
            zIndex: 100,
            gap: 8,
          }}
        >
          <Dialogue text={message} />
          <PixelButton label="OK" small light onPress={() => useGame.setState({ message: null })} />
        </Animated.View>
      )}
    </>
  );
}
