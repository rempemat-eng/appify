import type { SoundId } from '@/lib/sound-assets';

/**
 * The playback rules (docs/vision/sound.md, "Playback rules"; Claude M, 21 Oct). Pure, so the
 * sound harness can test them; lib/sound.ts asks `cueAllowed` before every effect.
 *
 * Every cue has a tier:
 * - **confirm**: the answer to a tap (a button's tok, a success, an error). Always plays when
 *   effects are on: it is the sound that tells a player the tap landed.
 * - **moment**: a beat of the game (falling asleep, waking, a friend, a level, a reward, a hit).
 *   Plays when effects are on.
 * - **flavour**: the garden answering a touch (footsteps, the pond, the watering can, a pat).
 *   Pleasant once, tiring when stacked: at most one every FLAVOUR_GAP_MS, and none at all with
 *   Gentle sound on.
 *
 * Gentle sound (a switch beside Sound effects in the garden guide, off by default) is the
 * reduced-stimulation setting: confirms and moments stay, flavour cues stop, and no two
 * effects start within GENTLE_GAP_MS of each other. Ambience follows its own switch.
 * Sound is never the only signal, so nothing a player needs is lost.
 */
export type CueTier = 'confirm' | 'moment' | 'flavour';

export const cueTiers: Readonly<Record<SoundId, CueTier>> = {
  tap: 'confirm',
  chime: 'confirm',
  oops: 'confirm',
  hit: 'moment',
  raid: 'moment',
  nap: 'moment',
  wake: 'moment',
  friend: 'moment',
  levelup: 'moment',
  reward: 'moment',
  steps: 'flavour',
  splash: 'flavour',
  page: 'flavour',
  water: 'flavour',
  rustle: 'flavour',
  lantern: 'flavour',
  boop: 'flavour',
  munch: 'flavour',
};

/** The least time between two flavour cues (a player tapping props in a row hears one). */
export const FLAVOUR_GAP_MS = 600;
/** With Gentle sound on, the least time between any two effects. */
export const GENTLE_GAP_MS = 400;

export type CueHistory = { lastAny: number; lastFlavour: number };

export const emptyHistory = (): CueHistory => ({
  lastAny: Number.NEGATIVE_INFINITY,
  lastFlavour: Number.NEGATIVE_INFINITY,
});

/** Whether a cue may start now; `gentle` is the Gentle sound setting. */
export function cueAllowed(id: SoundId, now: number, history: CueHistory, gentle: boolean) {
  const tier = cueTiers[id];
  if (gentle && tier === 'flavour') return false;
  if (gentle && now - history.lastAny < GENTLE_GAP_MS) return false;
  if (tier === 'flavour' && now - history.lastFlavour < FLAVOUR_GAP_MS) return false;
  return true;
}

/** The history after a cue started. */
export function played(id: SoundId, now: number, history: CueHistory): CueHistory {
  return {
    lastAny: now,
    lastFlavour: cueTiers[id] === 'flavour' ? now : history.lastFlavour,
  };
}
