import { useEffect } from 'react';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { createAudioPlayer, setAudioModeAsync, type AudioPlayer } from 'expo-audio';
import { create } from 'zustand';
import { onFeedback, type FeedbackKind } from '@/lib/game';
import { ambienceLoops, soundEffects, type AmbienceId, type SoundId } from '@/lib/sound-assets';

/**
 * Sound is decoration (docs/vision/sound.md). It never gates a rule or a
 * reward, every effect is short and finite, and only the garden ambience loops.
 * Loudness is baked into the files, so players always run at volume 1.
 */
const keys = { effects: 'napattack-sound-effects', ambience: 'napattack-sound-ambience' };

// This callable Zustand store is a Hook: the use-prefix keeps compiler calls unconditional.
export const useSoundPreference = create<{
  effects: boolean;
  ambience: boolean;
  loaded: boolean;
  setEffects: (on: boolean) => Promise<void>;
  setAmbience: (on: boolean) => Promise<void>;
}>((set) => ({
  effects: true,
  ambience: true,
  loaded: false,
  setEffects: async (effects) => {
    await AsyncStorage.setItem(keys.effects, JSON.stringify(effects));
    set({ effects });
  },
  setAmbience: async (ambience) => {
    await AsyncStorage.setItem(keys.ambience, JSON.stringify(ambience));
    set({ ambience });
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
// expo-audio's web play() does not catch that refusal, so wait for one.
let activated = Platform.OS !== 'web';
function userActive() {
  if (activated) return true;
  const nav =
    typeof navigator === 'undefined'
      ? undefined
      : (navigator as Navigator & { userActivation?: { hasBeenActive: boolean } });
  if (nav?.userActivation?.hasBeenActive) activated = true;
  return activated;
}

const effectPlayers = new Map<SoundId, AudioPlayer>();
const lastPlayed = new Map<SoundId, number>();
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
  lastPlayed.set(id, now);
  try {
    const player = effectPlayer(id);
    if (player.currentTime > 0) {
      void player
        .seekTo(0)
        .then(() => player.play())
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

// A missing or unreadable setting means on: sound is the default experience.
const savedOn = (result: PromiseSettledResult<string | null>) =>
  result.status !== 'fulfilled' || result.value !== 'false';
export async function loadSoundPreference() {
  const [effects, ambience] = await Promise.allSettled([
    AsyncStorage.getItem(keys.effects),
    AsyncStorage.getItem(keys.ambience),
  ]);
  useSoundPreference.setState({
    effects: savedOn(effects),
    ambience: savedOn(ambience),
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
  const markActive = () => {
    activated = true;
    applyAmbience();
  };
  const web = Platform.OS === 'web' && typeof window !== 'undefined';
  if (web) {
    window.addEventListener('pointerdown', markActive, { capture: true });
    window.addEventListener('keydown', markActive, { capture: true });
  }
  return () => {
    stopFeedback();
    stopPreference();
    if (web) {
      window.removeEventListener('pointerdown', markActive, { capture: true });
      window.removeEventListener('keydown', markActive, { capture: true });
    }
    setAmbience(null);
  };
}
