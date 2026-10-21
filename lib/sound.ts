import { useEffect } from 'react';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { createAudioPlayer, setAudioModeAsync, type AudioPlayer } from 'expo-audio';
import { create } from 'zustand';
import { onFeedback, type FeedbackKind } from '@/lib/game';
import { ambienceLoops, soundEffects, type AmbienceId, type SoundId } from '@/lib/sound-assets';
import { cueAllowed, emptyHistory, played } from '@/lib/sound-rules';

/**
 * Sound is decoration (docs/vision/sound.md). It never gates a rule or a
 * reward, every effect is short and finite, and only the garden ambience loops.
 * Loudness is baked into the files, so players always run at volume 1.
 */
const keys = {
  effects: 'napattack-sound-effects',
  ambience: 'napattack-sound-ambience',
  gentle: 'napattack-sound-gentle',
};

// This callable Zustand store is a Hook: the use-prefix keeps compiler calls unconditional.
export const useSoundPreference = create<{
  effects: boolean;
  ambience: boolean;
  /** Gentle sound, the reduced-stimulation setting (lib/sound-rules.ts): off by default */
  gentle: boolean;
  loaded: boolean;
  setEffects: (on: boolean) => Promise<void>;
  setAmbience: (on: boolean) => Promise<void>;
  setGentle: (on: boolean) => Promise<void>;
}>((set) => ({
  effects: true,
  ambience: true,
  gentle: false,
  loaded: false,
  setEffects: async (effects) => {
    await AsyncStorage.setItem(keys.effects, JSON.stringify(effects));
    if (!effects) stopEffects();
    set({ effects });
  },
  setAmbience: async (ambience) => {
    await AsyncStorage.setItem(keys.ambience, JSON.stringify(ambience));
    set({ ambience });
  },
  setGentle: async (gentle) => {
    await AsyncStorage.setItem(keys.gentle, JSON.stringify(gentle));
    set({ gentle });
  },
}));

/** Every feedback cue in the store has one sound. */
export const feedbackSounds: Record<FeedbackKind, SoundId> = {
  select: 'tap',
  success: 'chime',
  error: 'oops',
  hit: 'hit',
  raid: 'raid',
  nap: 'nap',
  wake: 'wake',
  friend: 'friend',
  levelup: 'levelup',
  reward: 'reward',
};

/** The same sound twice within this window is one sound (a button and its cue). */
export const REPEAT_MS = 90;

// Browsers refuse to start audio before the page has had a user gesture, and
// expo-audio's web play() does not catch that refusal (an unhandled NotAllowedError),
// so play nothing until the browser itself counts a gesture.
let activated = Platform.OS !== 'web';
type Activation = { hasBeenActive: boolean };
function browserActivation(): Activation | undefined {
  const nav =
    typeof navigator === 'undefined'
      ? undefined
      : (navigator as Navigator & { userActivation?: Activation });
  return nav?.userActivation;
}
function userActive() {
  if (activated) return true;
  if (browserActivation()?.hasBeenActive) activated = true;
  return activated;
}

const effectPlayers = new Map<SoundId, AudioPlayer>();
const lastPlayed = new Map<SoundId, number>();
const effectRequests = new Map<SoundId, number>();
let cueHistory = emptyHistory();
let effectEpoch = 0;

/** Mute and root cleanup invalidate rewinds as well as currently playing cues. */
function stopEffects() {
  effectEpoch++;
  for (const player of effectPlayers.values()) {
    try {
      player.pause();
    } catch {
      // Audio cleanup must never interrupt a setting change or app teardown.
    }
  }
}

function effectPlayer(id: SoundId) {
  let player = effectPlayers.get(id);
  if (!player) {
    player = createAudioPlayer(soundEffects[id]);
    effectPlayers.set(id, player);
  }
  return player;
}

export function playSound(id: SoundId) {
  const preference = useSoundPreference.getState();
  if (!preference.loaded || !preference.effects || !userActive()) return;
  const now = Date.now();
  if (now - (lastPlayed.get(id) ?? Number.NEGATIVE_INFINITY) < REPEAT_MS) return;
  // the playback rules: tiers, the flavour gap and Gentle sound (lib/sound-rules.ts)
  if (!cueAllowed(id, now, cueHistory, preference.gentle)) return;
  cueHistory = played(id, now, cueHistory);
  lastPlayed.set(id, now);
  const epoch = effectEpoch;
  const request = (effectRequests.get(id) ?? 0) + 1;
  effectRequests.set(id, request);
  try {
    const player = effectPlayer(id);
    if (player.currentTime > 0) {
      void player
        .seekTo(0)
        .then(() => {
          const latest = useSoundPreference.getState();
          if (
            effectEpoch === epoch &&
            effectRequests.get(id) === request &&
            latest.loaded &&
            latest.effects &&
            userActive()
          )
            player.play();
        })
        .catch(() => {});
    } else player.play();
  } catch {
    // Audio is decoration: a failed sound never breaks a tap.
  }
}

let requested: AmbienceId | null = null;
let current: { id: AmbienceId; player: AudioPlayer } | null = null;
const ambiencePlayers = new Map<AmbienceId, AudioPlayer>();
function applyAmbience() {
  const preference = useSoundPreference.getState();
  const want = preference.loaded && preference.ambience && userActive() ? requested : null;
  if (current && current.id !== want) {
    current.player.pause();
    current = null;
  }
  if (!want || current) return;
  try {
    let player = ambiencePlayers.get(want);
    if (!player) {
      player = createAudioPlayer(ambienceLoops[want]);
      player.loop = true;
      ambiencePlayers.set(want, player);
    }
    player.play();
    current = { id: want, player };
  } catch {
    current = null;
  }
}

/** Which ambience the visible screen wants; null stops it. */
export function setAmbience(id: AmbienceId | null) {
  requested = id;
  applyAmbience();
}

/** Plays a garden loop while `id` is set and the calling screen is mounted. */
export function useAmbience(id: AmbienceId | null) {
  useEffect(() => {
    setAmbience(id);
    return () => setAmbience(null);
  }, [id]);
}

/**
 * The loop each place out in the world plays (coherence plan B3): wind and a far raven on
 * the Frostline, dry wind over the lava's rumble across Sunstone Reach, and surf, birds
 * and the falls on the Tidebloom Isles. Zones not listed stay quiet, as before.
 */
export const zoneAmbience: Readonly<Record<string, AmbienceId>> = {
  hollow: 'frost',
  snowmelt: 'frost',
  saddle: 'frost',
  summit: 'frost',
  gulch: 'sunstone',
  oasis: 'sunstone',
  scorch: 'sunstone',
  hearthold: 'sunstone',
  caldera: 'sunstone',
  springs: 'sunstone',
  landing: 'isles',
  rainforest: 'isles',
  headwaters: 'isles',
  cove: 'isles',
};

/**
 * Plays the loop of the zone being walked, while the calling screen is mounted; pass
 * null while the walk is not the visible, active screen (a journey, the map, a sheet).
 * Like the garden's loop it follows the ambience switch and stops in the background.
 */
export function useZoneAmbience(zone: string | null) {
  useAmbience(zone === null ? null : (zoneAmbience[zone] ?? null));
}

// A missing or unreadable setting means on: sound is the default experience.
const savedOn = (result: PromiseSettledResult<string | null>) =>
  result.status !== 'fulfilled' || result.value !== 'false';
export async function loadSoundPreference() {
  const [effects, ambience, gentle] = await Promise.allSettled([
    AsyncStorage.getItem(keys.effects),
    AsyncStorage.getItem(keys.ambience),
    AsyncStorage.getItem(keys.gentle),
  ]);
  useSoundPreference.setState({
    effects: savedOn(effects),
    ambience: savedOn(ambience),
    // Gentle sound is opt-in: only a saved 'true' turns it on
    gentle: gentle.status === 'fulfilled' && gentle.value === 'true',
    loaded: true,
  });
}

/**
 * Called once from the app root. Mixes with the player's own music, stays
 * silent when the phone's ring/silent switch is off, and stops in the background.
 */
export function startSound() {
  if (Platform.OS !== 'web')
    void setAudioModeAsync({
      playsInSilentMode: false,
      interruptionMode: 'mixWithOthers',
      shouldPlayInBackground: false,
    }).catch(() => {});
  void loadSoundPreference();
  const stopFeedback = onFeedback((kind) => playSound(feedbackSounds[kind]));
  const stopPreference = useSoundPreference.subscribe(applyAmbience);
  // A gesture counts once the browser says so: a touch's pointerdown does not (activation
  // comes with its pointerup or touchend), so starting audio there was refused. Browsers
  // without navigator.userActivation get the same rule from the event itself.
  const markActive = (event?: Event) => {
    const browser = browserActivation();
    if (browser) {
      if (!browser.hasBeenActive) return;
    } else if (
      event?.type === 'pointerdown' &&
      (event as Event & { pointerType?: string }).pointerType !== 'mouse'
    )
      return;
    activated = true;
    applyAmbience();
  };
  const gestures = ['pointerdown', 'pointerup', 'touchend', 'keydown'] as const;
  const web = Platform.OS === 'web' && typeof window !== 'undefined';
  if (web)
    for (const type of gestures) window.addEventListener(type, markActive, { capture: true });
  return () => {
    stopFeedback();
    stopPreference();
    stopEffects();
    if (web)
      for (const type of gestures) window.removeEventListener(type, markActive, { capture: true });
    setAmbience(null);
  };
}
