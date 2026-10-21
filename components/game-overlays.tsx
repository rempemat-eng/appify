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
  View,
  useWindowDimensions,
  type ViewStyle,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { PixelIcon } from '@/components/pixel-icon';
import { bot, clock, feedback, missions, useGame, gameStore, type Player } from '@/lib/game';
import { GardenGuide } from '@/components/garden-guide';
import { WelcomeBack } from '@/components/visitors';
import { guardianPlayer } from '@/lib/visitors';
import { DeckPanel } from '@/components/habit-cards';
import { GardenRecap } from '@/components/offline-garden';
import { BattleScreen } from '@/components/game-battle';
import { Pet, PixelButton, PixelText } from '@/components/game-ui';
import { SeedPacket, Planting, PetalFall, DreamDustFlight } from '@/components/grassling-feedback';
import { grasslings, growthStage } from '@/lib/grasslings';
import { GardenWorld } from '@/components/garden-world';
import { WorldScene } from '@/components/world-scene';
import { PixelScene } from '@/components/pixel-scenes';
import { BodyText, Dialogue } from '@/components/pixel-feedback';
import { FrameFill, PixelInput } from '@/components/pixel-frame';
import { useReducedMotion } from '@/lib/motion';
import { breakIntentionLabel } from '@/lib/companion-memories';
import { topGameOverlay } from '@/lib/overlay-priority';
import Animated, { FadeIn } from 'react-native-reanimated';
import { gameColumn, gameSideInset, hudClearance } from '@/lib/layout';
import { switchKeys } from '@/lib/switch-keys';
import { SaveRecovery, cancelFreshStart } from '@/components/save-recovery';

/** No focus ring on a container that only anchors focus (web only; React Native has none). */
const quietFocus: ViewStyle = { outlineWidth: 0 };
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
        {/* The modal's focus trap focuses the first focusable thing inside it. Without this
            anchor that was the Mossling's seed, whose focus ring read as a choice made before
            any tap; now focus starts on the title, quietly (no ring), and Tab reaches the
            seeds next. */}
        <View tabIndex={-1} style={[{ gap: 16 }, Platform.OS === 'web' ? quietFocus : null]}>
          <NapAttackWordmark />
          <BodyText style={{ fontSize: 15 }}>nap to grow. wake to play.</BodyText>
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
                      alignItems: 'center',
                      flex: 1,
                      minHeight: 100,
                      gap: 8,
                      paddingVertical: 10,
                      transform: [{ translateY: picked && species === s ? -12 : 0 }],
                    }}
                  >
                    {picked && species === s && <FrameFill tone="gold" depth={1} />}
                    <SeedPacket species={s} size={64} />
                    <View style={{ paddingHorizontal: 8, paddingVertical: 5 }}>
                      <FrameFill />
                      <BodyText style={{ fontSize: 13, lineHeight: 18 }}>
                        {grasslings[s].name}
                      </BodyText>
                    </View>
                    <View style={{ paddingHorizontal: 7, paddingVertical: 4 }}>
                      <FrameFill tone="parchment" />
                      <PixelText style={{ fontSize: 10 }}>{grasslings[s].habit}</PixelText>
                    </View>
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
              <PixelInput
                accessibilityLabel="Your name"
                value={name}
                onChangeText={(value) => {
                  setName(value);
                  setError(false);
                }}
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
              <PixelInput
                accessibilityLabel="Grassling name"
                value={petName}
                onChangeText={setPetName}
                autoCapitalize="characters"
                maxLength={10}
                autoCorrect={false}
                onSubmitEditing={hatch}
              />
            </View>
          </>
        )}
        <View style={{ paddingBottom: bottom + 20, gap: 12, width: '100%' }}>
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
function ScreenOff({
  confirmEarlyReturn,
  onRequestReturn,
  onKeepExploring,
  onReturnEarly,
}: {
  confirmEarlyReturn: boolean;
  onRequestReturn: () => void;
  onKeepExploring: () => void;
  onReturnEarly: () => void;
}) {
  const [skip, setSkip] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const quiet = useGame((s) => s.quietView);
  const p = useGame((s) => s.player)!;
  const now = useGame((s) => s.now);
  const offStart = useGame((s) => s.offStart);
  const offDreamDust = useGame((s) => s.offGrass);
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
  const { height: screenHeight } = useWindowDimensions();
  // The nap window is 0.62 of its width, but on a short screen (an iPhone SE, 667 px) it
  // gives way so the napped / Dream Dust chip and WAKE UP fit without scrolling: about 520 px
  // of the screen hold the rest. Never below 0.38 of its width; unchanged on taller phones.
  const napView = (w: number) =>
    Math.round(Math.max(w * 0.38, Math.min(w * 0.62, screenHeight - 520)));
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
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            pointerEvents: 'none',
          }}
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
                REAL DEMO COUNTDOWN · UNTIL COMPLETE
              </BodyText>
            </View>
          )}
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
              borderRadius: 0,
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
          <View
            style={{
              flexDirection: 'row',
              flexWrap: 'wrap',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 10,
            }}
          >
            <Pressable
              accessibilityRole="switch"
              accessibilityLabel="Quiet view"
              accessibilityHint="Hides the decorative scenery. Your demo timer and wake controls stay available."
              accessibilityState={{ checked: quiet }}
              aria-checked={quiet}
              {...switchKeys(() => gameStore.getState().setQuietView(!quiet))}
              onPress={() => gameStore.getState().setQuietView(!quiet)}
              style={{
                minWidth: 44,
                minHeight: 44,
                paddingHorizontal: 16,
                paddingVertical: 10,
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <FrameFill tone={quiet ? 'nap' : 'night'} outline={c.nap} />
              <BodyText
                style={{ color: c.paper, fontFamily: 'PixelifySans_700Bold', fontSize: 12 }}
              >
                QUIET VIEW · {quiet ? 'ON' : 'OFF'}
              </BodyText>
            </Pressable>
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
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <FrameFill tone={helpOpen ? 'nap' : 'night'} outline={c.nap} />
              <PixelText style={{ color: c.paper }}>?</PixelText>
            </Pressable>
          </View>
          {quiet && (
            <BodyText style={{ color: c.paper, textAlign: 'center', fontSize: 12 }}>
              Scenery is hidden. There is nothing here you need to watch.
            </BodyText>
          )}
          {helpOpen && (
            <BodyText
              style={{
                color: c.paper,
                backgroundColor: c.night,
                borderRadius: 0,
                padding: 12,
                fontSize: 12,
                textAlign: 'center',
              }}
            >
              Demo timer only. Sleep and phone inactivity are not measured.{' '}
              {m
                ? 'This demo mission finishes automatically. Its rewards are saved, and your garden stays shielded until you return.'
                : 'This nap has no end timer. Choose WAKE UP when you want to return.'}
            </BodyText>
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
                  : '+50% DREAM DUST IF BOTH COMPLETE 10 SIMULATED MIN'}
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
                    borderRadius: 0,
                    overflow: 'hidden',
                    borderWidth: 2,
                    borderColor: c.napOutline,
                  }}
                >
                  {/* Your Grassling's journey: a 2.5D diorama of where it went. */}
                  <WorldScene
                    world={m.id === 'book' ? 'book' : m.id === 'mountain' ? 'mountain' : 'park'}
                    width={napWidth - 4}
                    // a window that follows the companion, as the nap garden does
                    viewportHeight={napView(napWidth - 4)}
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
                    borderRadius: 0,
                    overflow: 'hidden',
                    borderWidth: 2,
                    borderColor: c.napOutline,
                  }}
                >
                  <GardenWorld
                    memories={memories}
                    width={napWidth - 4}
                    // a window onto the hut and bed, not the whole tall garden
                    viewportHeight={napView(napWidth - 4)}
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
              <View style={{ paddingVertical: 10, paddingHorizontal: 14 }}>
                <FrameFill tone="lantern" depth={1} />
                <PixelText style={{ color: c.paper, textAlign: 'center', lineHeight: 22 }}>
                  {`NAPPED ${p.offline_seconds - offStart} SIMULATED MIN\n+${p.grass - offDreamDust} DREAM DUST`}
                </PixelText>
              </View>
            </View>
          )}
          {m ? (
            <>
              <BodyText style={{ color: c.paper, fontFamily: 'PixelifySans_500Medium' }}>
                {m.duration} simulated offline MIN · {m.reward} Dream Dust on completion
              </BodyText>
            </>
          ) : null}
        </View>
      </ScrollView>
      <View style={{ gap: 12, paddingTop: 12, paddingBottom: 8 }}>
        <PixelText
          style={{ color: c.body, textAlign: 'center', backgroundColor: c.night, padding: 6 }}
        >
          {m
            ? 'EARLY RETURN · NO COMPLETION REWARD · CARDS STAY'
            : '+1 DREAM DUST / SIMULATED OFFLINE MIN'}
        </PixelText>
        {togetherId && message && (
          <BodyText style={{ color: c.paper, textAlign: 'center' }}>{message}</BodyText>
        )}
        {confirmEarlyReturn && m ? (
          <View accessibilityLiveRegion="polite" style={{ gap: 12, padding: 16 }}>
            <FrameFill tone="lantern" depth={1} />
            <PixelText style={{ color: c.paper, textAlign: 'center' }}>RETURN EARLY?</PixelText>
            <BodyText style={{ color: c.paper, textAlign: 'center', fontSize: 13 }}>
              No mission completion rewards, including the {m.reward} Dream Dust bonus. Cards
              already earned stay yours.
            </BodyText>
            <PixelButton label="KEEP EXPLORING" onPress={onKeepExploring} />
            <PixelButton label="RETURN EARLY" small light onPress={onReturnEarly} />
          </View>
        ) : (
          <PixelButton label="WAKE UP" light onPress={onRequestReturn} />
        )}
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
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          pointerEvents: 'none',
        }}
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
        <PixelIcon name="arena" size={48} />
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
        {item.raid.attacker_won && <DreamDustFlight toLeft={false} />}
        <Dialogue
          text={
            item.raid.attacker_won
              ? `i wilted. they stole ${item.raid.grass_amount} dream dust`
              : 'raid repelled! +20 dream dust'
          }
          style={{ alignSelf: 'stretch' }}
        />
        <PixelIcon name="shield" size={32} />
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
  const missionReturnPending = useGame((s) => s.missionReturnPending);
  const recap = useGame((s) => s.recap);
  // A save that could not be loaded is answered before anything else, onboarding
  // included: its GROW path would otherwise advance while hatching stays blocked.
  const saveLoadProblem = useGame((s) => s.saveLoadProblem);
  const recovering = ready && Boolean(saveLoadProblem);
  const [returnPrompt, setReturnPrompt] = useState<string | null>(null);
  const insets = useSafeAreaInsets();
  const isScreenOff = !!p && p.mode !== 'awake';
  const overlay = topGameOverlay({
    ready,
    hasPlayer: Boolean(p),
    napping: isScreenOff && !missionReturnPending,
    welcome: Boolean(cardReward),
    recap: Boolean(recap),
    battle: Boolean(battle),
    alert: Boolean(alert),
    growth: Boolean(flash),
    guide: guideOpen,
    deck: deckOpen,
  });
  const earlyReturnKey = p?.mode === 'mission' ? `${p.mission_id}:${p.mission_ends_at}` : null;
  const confirmEarlyReturn =
    overlay === 'nap' && earlyReturnKey !== null && returnPrompt === earlyReturnKey;
  function requestReturn() {
    if (earlyReturnKey !== null) setReturnPrompt(earlyReturnKey);
    else void gameStore.getState().wake();
  }
  const visible = overlay !== null || recovering;
  useEffect(() => {
    if (!flash) return undefined;
    const timeout = setTimeout(() => useGame.setState({ flash: null }), 1600);
    return () => clearTimeout(timeout);
  }, [flash]);
  // a notice ("TRAILHOP wandered off.") is read and goes by itself; OK still closes it
  useEffect(() => {
    if (!message) return undefined;
    const timeout = setTimeout(() => {
      if (useGame.getState().message === message) useGame.setState({ message: null });
    }, 7000);
    return () => clearTimeout(timeout);
  }, [message]);
  function dismiss() {
    // Escape and Back only close the START FRESH confirmation; the screen stays.
    if (recovering) {
      cancelFreshStart();
      return;
    }
    if (!ready || !p) return;
    switch (overlay) {
      case 'nap':
        if (earlyReturnKey !== null) setReturnPrompt(confirmEarlyReturn ? null : earlyReturnKey);
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
            paddingBottom: overlay === 'welcome' ? 0 : insets.bottom,
            backgroundColor: overlay === 'nap' && !recovering ? c.night : c.paper,
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
            ) : recovering && saveLoadProblem ? (
              <SaveRecovery problem={saveLoadProblem} />
            ) : !p ? (
              <Onboarding />
            ) : overlay === 'nap' ? (
              <ScreenOff
                confirmEarlyReturn={confirmEarlyReturn}
                onRequestReturn={requestReturn}
                onKeepExploring={() => setReturnPrompt(null)}
                onReturnEarly={() => {
                  setReturnPrompt(null);
                  void gameStore.getState().wake();
                }}
              />
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
            // under the HUD, never over its menu, Dream Dust and timers
            top: hudClearance(insets.top),
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
