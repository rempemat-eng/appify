# Sound

> **Superseded 21 Oct by [game-design.md](game-design.md)** in the `nap` and `wake` cues; combat sounds are to come (its section 14).

Sound is part of "one game, not an app with a game in it", but it stays decoration: it never gates a rule, a reward or a choice, and every cue is short and kind.

## The palette

- **Generated, like the art.** `scripts/audio/sounds.py` synthesises every sound from code (`npm run sound`). It writes `assets/sounds/*.wav` and `lib/sound-assets.ts`. Never hand-edit those. Change the generator and rerun it.
- **Soft and warm:** sine and triangle tones, gentle attacks, low-passed noise. No harsh square waves, no alarms. Even `raid` and `oops` are low and brief.
- **One scale:** notes come from C major pentatonic (`NOTE` in the generator), so any two cues sound kind together.
- **Finite:** every effect is under 2 seconds and fades to silence. Only the ambience loops repeat: the garden's day and night, and one each for the Frostline, Sunstone Reach and the Tidebloom Isles (Claude B, 18 Oct).
- **Loudness lives in the files.** iOS Safari ignores programmatic volume, so each file is mastered at its own level (effects peak around -18 to -28 dBFS since 18 Oct, when Matt asked for quieter effects; ambience around -24) and players always run at volume 1. There are no fades in code.
- **WAV, not MP3.** MP3 adds about 50 ms of encoder padding, which delays a tap and gaps a loop. Effects are tiny. The garden's two loops are 20 s of 16 kHz mono each; the three place loops are shorter and lower-rate so the palette fits its 2.75 MB budget (`check-sound.cjs`).

| Cue                                                     | Sound                                                                                            | Where it plays                                             |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------- |
| `tap`                                                   | a small wooden tok                                                                               | every `PixelButton`, and `feedback('select')`              |
| `chime`                                                 | three-note bell                                                                                  | `feedback('success')`                                      |
| `oops`                                                  | two low falling notes                                                                            | `feedback('error')`                                        |
| `hit`, `raid`                                           | soft thump, three low pulses                                                                     | battle and raid cues                                       |
| `nap`, `wake`                                           | falling lullaby, rising notes                                                                    | `sleep()` and a completed nap's `wake()`                   |
| `friend`, `levelup`, `reward`                           | bells with a little sparkle                                                                      | befriending, levelling up, finishing a mission             |
| `steps`                                                 | four soft footsteps                                                                              | a player's tap that starts a walk (not idle walks)         |
| `splash`, `page`, `water`, `rustle`                     | pond, book, watering can, meadow                                                                 | the garden action on arrival                               |
| `lantern`, `boop`, `munch`                              | glass ting, pat, crunch                                                                          | lantern, patting the companion, feeding                    |
| `ambience-day`, `ambience-night`                        | wind and birds; crickets, an owl                                                                 | Home, only while the garden is active                      |
| `ambience-frost`, `ambience-sunstone`, `ambience-isles` | high wind and a far raven; dry wind and the lava's rumble; surf, rain-forest birds and the falls | The world, in those places, not under a journey or the map |

## The engine (`lib/sound.ts`)

- `playSound(id)` plays an effect. It is a no-op until preferences have loaded, when effects are off, and on the web before the page's first tap or key (browsers refuse earlier audio, and expo-audio's web `play()` does not catch the refusal). The same cue within `REPEAT_MS` is one sound, so a button and its store cue do not double up.
- A replay may need an asynchronous rewind. Muting effects or stopping the sound system cancels pending replays and pauses active effects; turning sound back on does not revive old cues. A newer request for the same cue supersedes an older rewind. This lifecycle is covered by deferred boundary tests, not a claim about physical-device audio output.
- `useAmbience(id | null)` is the only way to start a loop. Home passes `'day'`, `'night'` (21:00 to 06:00) or `null` from the same `gardenActive` flag that pauses the garden. Any sheet, a tab change, the app going to the background or a nap stops it. In the world, `useZoneAmbience(zone)` picks the place's loop the same way.
- The store stays free of audio. `lib/game.ts` exposes `onFeedback()` and more specific `feedback()` kinds (`nap`, `wake`, `friend`, `levelup`, `reward`). `startSound()` (called once in `app/_layout.tsx`) maps every kind to a cue in `feedbackSounds`.
- On iOS and Android the audio session mixes with the player's own music, follows the silent switch and stops in the background (`setAudioModeAsync` in `startSound()`).
- The garden guide has three pixel switches: **Sound effects** and **Garden ambience** (on by default) and **Gentle sound** (off by default), all saved on the device.

## Playback rules (Claude M, 21 Oct; `lib/sound-rules.ts`)

`playSound` asks `cueAllowed` before every effect. Each cue has a tier:

| Tier        | Cues                                                                     | Rule                                                           |
| ----------- | ------------------------------------------------------------------------ | -------------------------------------------------------------- |
| **confirm** | `tap`, `chime`, `oops`                                                   | Always plays while effects are on: it tells you the tap landed |
| **moment**  | `nap`, `wake`, `friend`, `levelup`, `reward`, `hit`, `raid`              | Plays while effects are on                                     |
| **flavour** | `steps`, `splash`, `page`, `water`, `rustle`, `lantern`, `boop`, `munch` | At most one every 600 ms; none with Gentle sound               |

- **Mute** is the Sound effects switch (cancels pending rewinds and pauses active cues) and, for loops, the ambience switch. On native the phone's silent switch also mutes, and nothing plays in the background.
- **Gentle sound** is the reduced-stimulation setting: confirms and moments only, and no two effects start within 400 ms. It does not follow reduced motion on its own, because the two needs differ; the guide offers both side by side. Ambience keeps its own switch.
- A new cue must be given a tier in `cueTiers`; `check:sound` fails on a cue without one.

## Inventory (21 Oct)

- **18 effects and 5 loops, 2.71 MB of the 2.75 MB budget** (`check-sound.cjs`). The budget is full: new loops need either a larger budget or shorter, lower-rate beds.
- **Where they play:** the table above. The world plays only three place loops (Frostline, Sunstone, Isles, mapped by zone in `zoneAmbience`); every other zone, the city and the station are silent.
- **A known web bug, found by the play-test harness:** a cue paused while its `play()` is still starting raises an unhandled "The play() request was interrupted by a call to pause()" in Chromium (about one flow in eight). Codex's #141 (C25) catches exactly this; it waits only on four unrelated visual items, which move to Claude M's lane so #141 can land on its own.

## Proposed: a sound set per region (for Matt; not built)

Each region gets one bed loop in the same recipe as today's (generated, pentatonic, soft, mastered in the file), plus UI cues shared everywhere. Loops are 12 to 16 s, 11 kHz mono (about 0.3 MB each), so ten more cost about 3 MB: the budget would rise from 2.75 to about 6 MB, small beside the 24 to 50 MB of 2x art. Same rules as now: one loop at a time, only while its screen is active, never under a journey, the map or a sheet.

| Region (owner)                          | Bed loop                                                                        |
| --------------------------------------- | ------------------------------------------------------------------------------- |
| Home valley, garden (E)                 | today's day and night loops                                                     |
| Crossroads Town, valley villages (E)    | the valley loop with a far cart, a bell and voices kept low                     |
| Frostline and the massif (F)            | today's frost loop; glaciers add slow creaking ice                              |
| The Brackens (F)                        | wind in heather, a curlew, a far sheep bell                                     |
| Cogsworth and the coal hills (H)        | slow far gears, a steam sigh every few seconds, a train horn                    |
| The Narrows and Fernhollow (H)          | the river in the gorge; old forest: deep birds, creaking boughs                 |
| Neon Harbour, the Heights, docks (I)    | old town: gulls and water on stone; new town: rain hum and a soft electric buzz |
| The Lull delta, Lullford, Gullwick (I)  | slow river, reeds, frogs at night; gulls on the coast                           |
| Skyport and the Cape Road (I)           | high wind, a far engine drone                                                   |
| Tidebloom Isles, the Shell Bar (C)      | today's isles loop; the bar adds shallow lapping water                          |
| Sunstone Reach and the fire country (D) | today's sunstone loop; near Ember, a low rumble                                 |
| Halcyon Station and the moon            | a quiet station hum; the moon is silent but for your steps                      |

**Interface cues (shared):** a paper rustle when a sheet opens and a softer one when it closes, a wooden click for a switch (higher for on, lower for off), and a soft card slide in the battle. All are confirms, so Gentle sound keeps them. The volume of every new file follows today's levels (effects around -18 to -28 dBFS, loops around -24).

**Choices for Matt:** raise the sound budget to about 6 MB for the region loops; and whether night versions of the city loops are worth their bytes.

## Rules for new sounds

- Add the generator function, give it a pentatonic pitch and a soft envelope, and let `finish()` master it. `npm run check:sound` then checks that it is short, ends in silence and has a matching duration.
- Play a sound from a user's intent or a store cue, never from a timer, an idle animation or a background tick.
- Never use sound as the only signal. Everything audible also has a visible reaction or text.

## Not verified yet

The source harnesses cover asset shape, the engine's decisions and where Home and the garden ask for sound. Nobody has listened to the sounds on a phone, checked iOS silent mode, or checked mixing with music on a device. Treat them as first drafts to tune by ear.
