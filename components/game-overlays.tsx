import { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
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
import { BattleScreen } from '@/components/game-battle';
import { FloatingZ, Pet, PixelButton, PixelEgg, PixelText, styles } from '@/components/game-ui';
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
        <PixelEgg cracking />
        <PixelText style={{ fontSize: 17 }}>HATCHING...</PixelText>
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
            {"PUT YOUR PHONE DOWN.\nYOUR PET'S LIFE DEPENDS ON IT."}
          </PixelText>
        </View>
        {step === 0 ? (
          <>
            <PixelText style={{ fontSize: 14, lineHeight: 24, marginTop: 8 }}>
              CHOOSE YOUR STARTER
            </PixelText>
            <View style={{ gap: 14 }}>
              {(['BLOB', 'RAT', 'CUBE'] as const).map((s, index) => (
                <View
                  key={s}
                  style={{
                    borderWidth: 2,
                    borderColor: c.ink,
                    backgroundColor: species === s ? c.body : c.paper,
                  }}
                >
                  <PixelButton
                    label={`${species === s ? '> ' : ''}${s}`}
                    light={species !== s}
                    small
                    onPress={() => {
                      setSpecies(s);
                      feedback('select');
                    }}
                  />
                  <View
                    style={{
                      flexDirection: 'row',
                      alignItems: 'center',
                      gap: 20,
                      paddingHorizontal: 16,
                      paddingVertical: 9,
                    }}
                  >
                    <Pet species={s} size={96} bob={species === s} />
                    <PixelText style={{ flex: 1 }}>
                      {['SQUISHY TANK', 'FAST NIBBLER', 'GLITCHY GENIUS'][index]}
                    </PixelText>
                  </View>
                </View>
              ))}
            </View>
            <PixelText style={{ fontSize: 11 }}>SAME STATS. DIFFERENT PIXELS.</PixelText>
          </>
        ) : (
          <>
            <View style={{ alignItems: 'center', paddingVertical: 6 }}>
              <Pet species={species} size={120} />
            </View>
            <View style={{ gap: 12 }}>
              <PixelText>YOUR NAME</PixelText>
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
              {error && <PixelText accessibilityRole="alert">GIVE YOURSELF A NAME.</PixelText>}
            </View>
            <View style={{ gap: 12 }}>
              <PixelText>PET NAME</PixelText>
              <TextInput
                accessibilityLabel="Pet name"
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
          label={step === 0 ? `CHOOSE ${species}` : 'HATCH!'}
          onPress={() => (step === 0 ? setStep(1) : hatch())}
        />
        {step === 1 && (
          <PixelButton label="CHANGE STARTER" small light onPress={() => setStep(0)} />
        )}
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
      <View style={{ alignItems: 'center', gap: 16, paddingTop: 20 }}>
        <Shield color={c.paper} size={30} />
        <PixelText style={{ color: c.paper, textAlign: 'center', fontSize: 13, lineHeight: 24 }}>
          {'SCREEN OFF.\nPET SHIELDED.'}
        </PixelText>
        {m && <PixelText style={{ color: c.paper, textAlign: 'center' }}>{m.name}</PixelText>}
      </View>
      <View style={{ alignItems: 'center', gap: 28 }}>
        {!m && <FloatingZ />}
        <Pet
          species={p.species}
          level={p.level}
          hat={p.hat}
          sleeping={!m}
          walking={!!m}
          bob
          size={160}
        />
        {m ? (
          <>
            <PixelText style={{ color: c.paper, fontSize: 26, lineHeight: 40 }}>
              {clock(Math.max(0, Math.ceil((p.mission_ends_at - now) / 1000)))}
            </PixelText>
            <PixelText style={{ color: c.body }}>UNTIL HOME · MIN</PixelText>
          </>
        ) : (
          <PixelText style={{ color: c.paper, textAlign: 'center', lineHeight: 26 }}>
            {`OFFLINE ${p.offline_seconds - offStart} MIN\n+${p.grass - offGrass} GRASS`}
          </PixelText>
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
      <ScrollView
        contentContainerStyle={{
          flexGrow: 1,
          justifyContent: 'center',
          alignItems: 'center',
          gap: 24,
        }}
      >
        <Swords size={42} color={c.ink} />
        <PixelText style={{ fontSize: 17, lineHeight: 30, textAlign: 'center' }}>
          {`${a?.name ?? 'A RIVAL'}\nRAIDED YOU!`}
        </PixelText>
        <Pet species={p.species} level={p.level} hat={p.hat} grumpy={p.mood < 30} size={120} />
        <View style={[styles.border, { padding: 20, alignSelf: 'stretch' }]}>
          <PixelText style={{ textAlign: 'center', fontSize: 14, lineHeight: 27 }}>
            {item.raid.attacker_won
              ? `THEY STOLE\n${item.raid.grass_amount} GRASS`
              : 'RAID REPELLED!\n+20 GRASS'}
          </PixelText>
        </View>
        <Shield size={26} color={c.ink} />
        <PixelText style={{ textAlign: 'center' }}>RECOVERY SHIELD: 60 MIN</PixelText>
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
  const insets = useSafeAreaInsets();
  const isScreenOff = !!p && p.mode !== 'awake';
  const visible = !ready || !p || isScreenOff || !!battle || !!alert || !!message || !!flash;
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
    else useGame.setState({ message: null, flash: null });
  }
  return (
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
            <PixelEgg />
            <ActivityIndicator color={c.ink} />
            <PixelText>LOADING YOUR PIXELS...</PixelText>
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
            <Pet species={p.species} level={p.level} hat={p.hat} />
            <PixelText style={{ fontSize: 18, lineHeight: 34, textAlign: 'center' }}>
              {flash}
            </PixelText>
          </View>
        ) : (
          <View
            style={{
              flex: 1,
              backgroundColor: c.paper,
              padding: 24,
              justifyContent: 'center',
              gap: 28,
            }}
          >
            <View style={{ alignItems: 'center' }}>
              <Pet species={p.species} level={p.level} hat={p.hat} size={120} />
            </View>
            <PixelText style={{ textAlign: 'center', fontSize: 14, lineHeight: 28 }}>
              {message}
            </PixelText>
            <PixelButton label="OK" onPress={() => useGame.setState({ message: null })} />
          </View>
        )}
      </View>
    </Modal>
  );
}
