import { cozy as c } from '@/lib/cozy';
import { NapAttackWordmark } from '@/components/napattack-brand';
import { CozyBackground } from '@/components/cozy-ui';
import { LightSweep, GrowthFrames } from '@/components/cozy-motion';
import * as Haptics from 'expo-haptics';
import { useEffect, useRef, useState } from 'react';
import {
  Pressable,
  KeyboardAvoidingView,
  Modal,
  Platform,
  ScrollView,
  TextInput,
  View,
  useWindowDimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Shield, Swords } from 'lucide-react-native';
import { bot, clock, feedback, missions, useGame, gameStore, type Player } from '@/lib/game';
import { GardenGuide } from '@/components/garden-guide';
import { WelcomeBack } from '@/components/visitors';
import { guardianPlayer } from '@/lib/visitors';
import { DeckPanel } from '@/components/habit-cards';
import { GardenRecap } from '@/components/offline-garden';
import { BattleScreen } from '@/components/game-battle';
import { Pet, PixelButton, PixelText, styles } from '@/components/game-ui';
import { SeedPacket, Planting, PetalFall, GrassFlight } from '@/components/grassling-feedback';
import { grasslings, growthStage } from '@/lib/grasslings';
import { GardenWorld } from '@/components/garden-world';
import { WorldScene } from '@/components/world-scene';
import { PixelScene } from '@/components/pixel-scenes';
import { BodyText, Dialogue } from '@/components/pixel-feedback';
import { useReducedMotion } from '@/lib/motion';
import { useGardenView } from '@/lib/garden-view';
import { breakIntentionLabel } from '@/lib/companion-memories';
import { topGameOverlay } from '@/lib/overlay-priority';
import Animated, { FadeIn } from 'react-native-reanimated';
import { gameColumn, gameSideInset } from '@/lib/layout';
function Onboarding() {
  const reduced = useReducedMotion();
  const [step, setStep] = useState(0);
  const [picked, setPicked] = useState(false);
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
    timer.current = setTimeout(
      () => {
        void gameStore.getState().hatch(name, petName, species);
      },
      reduced ? 0 : 1400,
    );
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
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <CozyBackground />
      <ScrollView
        style={{ flex: 1 }}
        automaticallyAdjustKeyboardInsets
        keyboardDismissMode="on-drag"
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
          <NapAttackWordmark />
          <BodyText style={{ fontSize: 15 }}>nap to grow. wake to raid.</BodyText>
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
                      setPicked(true);
                      feedback('select');
                    }}
                    accessibilityState={{ selected: picked && species === s }}
                    style={{
                      borderRadius: 14,
                      alignItems: 'center',
                      flex: 1,
                      minHeight: 100,
                      gap: 12,
                      paddingVertical: 8,
                      borderWidth: 2,
                      borderColor: picked && species === s ? c.moss : 'transparent',
                      backgroundColor: picked && species === s ? c.amber : 'transparent',
                      transform: [{ translateY: picked && species === s ? -12 : 0 }],
                    }}
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
              Plant a seed. Your Grassling naps and grows while you spend time away.
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
        <View style={{ paddingBottom: bottom + 20, gap: 12, width: '100%' }}>
          {step === 0 && !picked && (
            <PixelText style={{ textAlign: 'center' }}>PICK A SEED FIRST</PixelText>
          )}
          <PixelButton
            label={step === 0 ? (picked ? 'PLANT A SEED' : 'PICK A SEED FIRST') : 'GROW MY GARDEN'}
            disabled={step === 0 && !picked}
            onPress={() => (step === 0 ? setStep(1) : hatch())}
          />
          {step === 1 && <PixelButton label="CHANGE SEED" small light onPress={() => setStep(0)} />}
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
function ScreenOff() {
  const [gardenView] = useGardenView();
  const [skip, setSkip] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const [quiet, setQuiet] = useState(false);
  const p = useGame((s) => s.player)!;
  const now = useGame((s) => s.now);
  const offStart = useGame((s) => s.offStart);
  const offGrass = useGame((s) => s.offGrass);
  const breakContext = useGame((s) => s.activeBreakContext);
  const memories = useGame((s) => s.companionMemories);
  const togetherId = useGame((s) => s.togetherId);
  const session = useGame((s) => s.sessions.find((x) => x.id === s.togetherId));
  const rival = useGame((s) =>
    s.rivals.find(
      (x) => x.id === (session?.player_a === p.id ? session?.player_b : session?.player_a),
    ),
  );
  const message = useGame((s) => s.message);
  const sharedMinutes = session?.started_at
    ? Math.max(0, Math.floor((now - Date.parse(session.started_at)) / 1000))
    : 0;
  const m = missions.find((x) => x.id === p.mission_id);
  const guardian = guardianPlayer(p);
  const [napWidth, setNapWidth] = useState(0);
  return (
    <View
      onStartShouldSetResponderCapture={() => {
        setSkip(true);
        return false;
      }}
      onTouchStart={() => setSkip(true)}
      style={{
        flex: 1,
        backgroundColor: c.night,
        padding: 24,
        justifyContent: 'space-between',
        alignItems: 'stretch',
      }}
    >
      {!quiet && (
        <View
          pointerEvents="none"
          style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
        >
          {m && (
            <PixelScene
              kind="night"
              skyOnly
              species={guardian.species}
              level={p.level}
              player={p}
              style={{ height: '100%', borderWidth: 0 }}
            />
          )}
          <LightSweep night skip={skip} />
        </View>
      )}
      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={{
          flexGrow: 1,
          justifyContent: 'space-between',
          gap: 16,
          paddingBottom: 16,
        }}
      >
        <View style={{ alignItems: 'center', gap: 10, paddingTop: 8 }}>
          <PixelText
            accessibilityRole="header"
            style={{ color: c.paper, textAlign: 'center', fontSize: 14, lineHeight: 25 }}
          >
            A LITTLE TIME FOR YOU
          </PixelText>
          <BodyText style={{ color: c.paper, textAlign: 'center', lineHeight: 22 }}>
            {guardian.pet_name} is settling in. Put your phone down and make a little room for
            yourself.
          </BodyText>
          {breakContext && (
            <BodyText style={{ color: c.paper, textAlign: 'center', fontSize: 12 }}>
              Your break idea: {breakIntentionLabel(breakContext.intention)} · a reflection is
              optional when you return
            </BodyText>
          )}
          <PixelText
            style={{
              color: c.paper,
              textAlign: 'center',
              fontSize: 13,
              lineHeight: 24,
              backgroundColor: c.night,
              borderRadius: 14,
              padding: 8,
            }}
          >
            {m ? 'EXPLORING · SHIELDED UNTIL RETURN' : 'NAPPING · GARDEN SHIELDED'}
          </PixelText>
          <BodyText style={{ color: c.paper, textAlign: 'center', fontSize: 12 }}>
            {m
              ? `${m.duration} simulated MIN · ${m.duration}-second demo`
              : 'Untimed nap · simulated · 1 real second = 1 simulated MIN'}
          </BodyText>
          <BodyText style={{ color: c.paper, textAlign: 'center', fontSize: 12 }}>
            {m
              ? 'This demo mission returns home automatically when its timer ends. Shielding ends with the mission.'
              : 'This nap has no end timer. Choose WAKE UP when you want to return.'}
          </BodyText>
          <Pressable
            accessibilityRole="switch"
            accessibilityLabel="Quiet view"
            accessibilityHint="Hides the decorative scenery. Your demo timer and wake controls stay available."
            accessibilityState={{ checked: quiet }}
            aria-checked={quiet}
            onPress={() => setQuiet((value) => !value)}
            style={{
              minWidth: 44,
              minHeight: 44,
              paddingHorizontal: 16,
              paddingVertical: 10,
              borderRadius: 22,
              borderWidth: 1,
              borderColor: c.napOutline,
              backgroundColor: c.night,
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <BodyText style={{ color: c.paper, fontFamily: 'Nunito_800ExtraBold', fontSize: 12 }}>
              QUIET VIEW · {quiet ? 'ON' : 'OFF'}
            </BodyText>
          </Pressable>
          {quiet && (
            <BodyText style={{ color: c.paper, textAlign: 'center', fontSize: 12 }}>
              Scenery is hidden. There is nothing here you need to watch.
            </BodyText>
          )}
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={
              helpOpen ? 'Close nap information' : 'About the simulated nap timer'
            }
            accessibilityState={{ expanded: helpOpen }}
            aria-expanded={helpOpen}
            onPress={() => setHelpOpen((open) => !open)}
            style={{
              minWidth: 44,
              minHeight: 44,
              borderRadius: 22,
              backgroundColor: c.night,
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <PixelText style={{ color: c.paper }}>?</PixelText>
          </Pressable>
          {helpOpen && (
            <BodyText
              style={{
                color: c.paper,
                backgroundColor: c.night,
                borderRadius: 14,
                padding: 12,
                fontSize: 12,
                textAlign: 'center',
              }}
            >
              Demo timer only. Sleep and phone inactivity are not measured.
            </BodyText>
          )}
          {m && (
            <View style={{ alignItems: 'center', gap: 4 }}>
              <PixelText style={{ color: c.paper, textAlign: 'center' }}>{m.name}</PixelText>
              <PixelText
                accessibilityLabel={`${clock(Math.max(0, Math.ceil((p.mission_ends_at - now) / 1000)))} remaining in this demo mission`}
                style={{ color: c.paper, fontSize: 26, lineHeight: 40 }}
              >
                {clock(Math.max(0, Math.ceil((p.mission_ends_at - now) / 1000)))}
              </PixelText>
              <BodyText style={{ color: c.paper, fontSize: 11 }}>
                REAL DEMO COUNTDOWN · UNTIL HOME
              </BodyText>
            </View>
          )}
        </View>
        <View style={{ alignItems: 'center', gap: 14, flex: m ? undefined : 1 }}>
          {togetherId && (
            <View style={{ gap: 12, alignItems: 'center' }}>
              <PixelText style={{ color: c.paper }}>TOUCH GRASS TOGETHER</PixelText>
              <PixelText style={{ color: c.body }}>SHARED TIMER: {sharedMinutes} MIN</PixelText>
              <PixelText
                style={{
                  color: session?.status === 'failed' ? c.body : c.gold,
                  textAlign: 'center',
                  lineHeight: 22,
                }}
              >
                {session?.status === 'failed'
                  ? 'TOGETHER ENDED EARLY · ORDINARY REWARDS KEPT'
                  : '+50% GRASS IF BOTH COMPLETE 10 SIMULATED MIN'}
              </PixelText>
            </View>
          )}
          {m ? (
            <View
              onLayout={(event) => setNapWidth(event.nativeEvent.layout.width)}
              style={{ width: '100%', alignItems: 'center' }}
            >
              {!quiet && napWidth > 0 && (
                <View
                  style={{
                    borderRadius: 18,
                    overflow: 'hidden',
                    borderWidth: 2,
                    borderColor: c.napOutline,
                  }}
                >
                  {/* Your Grassling's journey: a 2.5D diorama of where it went. */}
                  <WorldScene
                    world={m.id === 'book' ? 'book' : m.id === 'mountain' ? 'mountain' : 'park'}
                    width={napWidth - 4}
                    player={p}
                  />
                </View>
              )}
            </View>
          ) : (
            <View
              onLayout={(event) => setNapWidth(event.nativeEvent.layout.width)}
              style={{ width: '100%', alignItems: 'center', gap: 12 }}
            >
              {!quiet && napWidth > 0 && (
                <View
                  style={{
                    borderRadius: 18,
                    overflow: 'hidden',
                    borderWidth: 2,
                    borderColor: c.napOutline,
                  }}
                >
                  <GardenWorld
                    memories={memories}
                    view={gardenView}
                    width={napWidth - 4}
                    player={p}
                    grumpy={false}
                    sleepy={false}
                    napping
                  />
                </View>
              )}
              {!quiet && togetherId && rival && (
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                  <Pet
                    species={guardianPlayer(rival).species}
                    visitor={guardianPlayer(rival).guardian}
                    level={rival.level}
                    hat={rival.hat}
                    sleeping
                    curled
                    bob={false}
                    groundShadow={false}
                    size={64}
                  />
                  <BodyText style={{ color: c.paper }}>{rival.pet_name} is napping too</BodyText>
                </View>
              )}
              <View
                style={{
                  padding: 8,
                  borderRadius: 14,
                  borderWidth: 2,
                  borderColor: c.gold,
                  backgroundColor: c.night,
                }}
              >
                <PixelText style={{ color: c.paper, textAlign: 'center', lineHeight: 22 }}>
                  {`NAPPED ${p.offline_seconds - offStart} SIMULATED MIN\n+${p.grass - offGrass} GRASS`}
                </PixelText>
              </View>
            </View>
          )}
          {m ? (
            <>
              <BodyText style={{ color: c.paper, fontFamily: 'Nunito_600SemiBold' }}>
                {m.duration} simulated offline MIN · {m.reward} GRASS on completion
              </BodyText>
            </>
          ) : null}
        </View>
      </ScrollView>
      <View style={{ gap: 12, paddingTop: 12, paddingBottom: 8 }}>
        <PixelText
          style={{ color: c.body, textAlign: 'center', backgroundColor: c.night, padding: 6 }}
        >
          {m ? 'EARLY RETURN · EARNED CARDS STAY WITH YOU' : '+1 GRASS / SIMULATED OFFLINE MIN'}
        </PixelText>
        {togetherId && message && (
          <BodyText style={{ color: c.paper, textAlign: 'center' }}>{message}</BodyText>
        )}
        <PixelButton label="WAKE UP" light onPress={() => void gameStore.getState().wake()} />
      </View>
    </View>
  );
}
function DefenderAlert() {
  useEffect(() => {
    void Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
  }, []);
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
  const reduced = useReducedMotion();
  const { width } = useWindowDimensions();
  const sideInset = gameSideInset(width);
  const ready = useGame((s) => s.ready);
  const p = useGame((s) => s.player);
  const battle = useGame((s) => s.battle);
  const alert = useGame((s) => s.alerts[0]);
  const message = useGame((s) => s.message);
  const flash = useGame((s) => s.flash);
  const guideOpen = useGame((s) => s.guideOpen);
  const deckOpen = useGame((s) => s.deckOpen);
  const cardReward = useGame((s) => s.cardReward);
  const recap = useGame((s) => s.recap);
  const insets = useSafeAreaInsets();
  const isScreenOff = !!p && p.mode !== 'awake';
  const overlay = topGameOverlay({
    ready,
    hasPlayer: Boolean(p),
    napping: isScreenOff,
    welcome: Boolean(cardReward),
    recap: Boolean(recap),
    battle: Boolean(battle),
    alert: Boolean(alert),
    growth: Boolean(flash),
    guide: guideOpen,
    deck: deckOpen,
  });
  const visible = overlay !== null;
  useEffect(() => {
    if (!flash) return undefined;
    const timeout = setTimeout(() => useGame.setState({ flash: null }), 1600);
    return () => clearTimeout(timeout);
  }, [flash]);
  function dismiss() {
    if (!ready || !p) return;
    switch (overlay) {
      case 'nap':
        void gameStore.getState().wake();
        break;
      case 'welcome':
      case 'deck':
        gameStore.getState().dismissCards();
        break;
      case 'recap':
        gameStore.getState().dismissRecap();
        break;
      case 'alert':
        gameStore.getState().dismissAlert();
        break;
      case 'growth':
        useGame.setState({ flash: null });
        break;
      case 'guide':
        useGame.setState({ guideOpen: false });
        break;
      default:
        break;
    }
  }
  return (
    <>
      <Modal visible={visible} animationType="none" statusBarTranslucent onRequestClose={dismiss}>
        <View
          style={{
            flex: 1,
            paddingTop: insets.top,
            paddingBottom: !isScreenOff && cardReward ? 0 : insets.bottom,
            backgroundColor: isScreenOff ? c.night : c.paper,
          }}
        >
          {/* Same centred phone-width column as the tab screens (Page maxWidth), so
              overlays don't stretch across wide browser windows. The backdrop above
              still fills the screen. */}
          <View style={[gameColumn, { flex: 1 }]}>
            {overlay === 'loading' ? (
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
            ) : overlay === 'nap' ? (
              <ScreenOff />
            ) : overlay === 'welcome' ? (
              <WelcomeBack />
            ) : overlay === 'recap' ? (
              <GardenRecap />
            ) : overlay === 'battle' && battle ? (
              <BattleScreen key={`${battle.target.id}-${battle.practice}`} request={battle} />
            ) : overlay === 'alert' && alert ? (
              <DefenderAlert key={alert.raid.id} />
            ) : overlay === 'growth' && flash ? (
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
                <GrowthFrames player={p} />
                <PixelButton
                  label="BACK TO THE GARDEN"
                  onPress={() => useGame.setState({ flash: null })}
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
            ) : overlay === 'guide' ? (
              <GardenGuide onClose={() => useGame.setState({ guideOpen: false })} />
            ) : overlay === 'deck' ? (
              <DeckPanel />
            ) : null}
          </View>
        </View>
      </Modal>
      {!visible && message && (
        <Animated.View
          key={message}
          entering={reduced ? undefined : FadeIn.duration(100)}
          style={{
            position: 'absolute',
            top: insets.top + 12,
            left: sideInset,
            right: sideInset,
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
