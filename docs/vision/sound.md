# Sound

Sound is part of "one game, not an app with a game in it", but it stays decoration: it never gates a rule, a reward or a choice, and every cue is short and kind.

This page was written for the old Expo app, and its palette rules stand. The Godot game (`game/`) has its own generator, cue set and engine on the same rules: see [The Godot game](#the-godot-game-13-nov) below.

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

## The Godot game (13 Nov)

The three-zone slice (woodland, Crossroads, the Undercroft, the first night) has sound: 55 effect cues in 64 files and four ambience loops, 3.60 MB of WAV against a 4 MB budget. The palette rules are the ones above: generated from code, sine and triangle tones, gentle attacks, low-passed noise, C major pentatonic, every effect under 2 s and ending in silence, loudness in the files (effects peak between -18 and -28 dBFS, loops at -24), and sound as decoration only.

### The generator

- `scripts/audio/game_sounds.py` (`npm run sound:game`) writes `game/audio/sfx/*.wav` (22.05 kHz), `game/audio/ambience/*.wav` (12 kHz, 18 s) and `game/audio/cues.json`, the cue table the game reads. It imports the old generator's helpers (`scripts/audio/sounds.py`) and changes none of that script's outputs.
- Each sound's random numbers come from a seed made from its own name, so adding or reordering sounds never changes another file.
- `npm run check:sound-repro` (in `npm run check`, so in `verify`) regenerates everything in memory, compares every byte with the committed files, and holds each file to its shape: an effect lasts 0.05 to 2 s, starts and ends in silence and peaks between -18 and -28 dBFS; a loop peaks at -24 and joins end to start with a step no larger than the RMS of its own sample-to-sample steps; the whole palette stays under 4 MB. `--measure` prints peak, RMS, length and spectral centroid per file.
- After adding a sound, import the project (`$GODOT --headless --path game --import`), set `compress/mode=0` in the new `.wav.import` (plain 16-bit samples: what was measured is what plays; `test/test_sound.gd` fails on any other format), import again, and commit the WAV and its `.import`.
- WAV, not Ogg: the loops must reproduce byte for byte in CI, and an Ogg encode depends on the encoder's version. A WAV loop is sample-exact; `core/sound.gd` sets it to loop over all of its frames.

### The cues

Tiers are explained under [Playback rules](#playback-rules-godot). "Hook" is where the cue is asked for.

| Cue | Tier | Sound | Hook |
| --- | --- | --- | --- |
| `step_grass`, `step_stone`, `step_wood` (4 variants each, in turn) | step | a soft footstep: grass and earth, paving and the vault floor, the footbridge | `actors/player_sounds.gd`, on the two planted drawings of the walk; the surface from `data/sound/surfaces.json` |
| `bow_draw` | flavour | the stave creaking | `player_sounds.gd`: the clip becomes `primary` |
| `bow_release` | moment | the string's thrum (G3) and a breath of air | `Player.shot_released` |
| `arrow_hit` | moment | a soft thump with the shaft's thock: the arrow counted, the creature is hurt | `Player.hit_landed` |
| `arrow_wall` | flavour | one small tick of wood | `actors/arrow.gd`, stopping at a solid |
| `glance` | moment | a small dull clink (Matt, 11 Nov: an arrow from beyond reach must read as a miss) | `Glance.on_clink`, the hook `enemies/glance.gd` kept for it |
| `roll` | moment | cloth and ground, and the shoulder landing | `player_sounds.gd`: the clip becomes `dodge` |
| `hurt`, `downed`, `get_up` | moment | a low short "oof"; three slow falling notes; three rising | `Player.hurt` with hearts left or none; `Player.downed` (getting up at the zone's start) |
| `tell_mossling`, `tell_rusher`, `tell_shooter`, `tell_shield`, `tell_elite` | moment | leaves shaking faster; two snorts; a croak that swells; stone dragged; a deeper double huff. All quiet, all shorter than the wind-up they announce | `actors/enemy.gd` wind-up; `enemies/slice_enemy.gd` at `committed`; `enemies/raid_creature.gd` before it batters |
| `enemy_strike`, `enemy_spit` | moment | a lunge's whoosh; the toad's "pft" | the lunge; `slice_enemy.gd` at `released` |
| `enemy_freed` | moment | a breath and two soft rising notes: freed, not killed | `enemy.gd` and `slice_enemy.gd` where `died` is emitted |
| `boss_tell_charge`, `boss_tell_volley`, `boss_tell_slam` | moment | pawing scuffs over a rising growl; the shell rattling quicker; a swell that grows | `bosses/thornback.gd` `_start_windup` |
| `boss_charge`, `boss_volley`, `boss_slam` | moment | the rush; five small breaths of air; one deep soft thump | `thornback.gd` `_release` |
| `boss_roar`, `boss_stagger`, `boss_freed` | moment | the second phase: a low rough breath, low-passed, never a scream; a thud and a dazed wobble; the shell cracking and a quiet C major chord | `thornback.gd`: the `roar` state, `_stagger`, `_free` |
| `door`, `door_stone` | moment | a latch, a creak and the next place's air; stone on stone for the Undercroft's hatch and stair | `Zones.zone_changed`, in `core/sound.gd` (never `world/door.gd`): only a walk from one zone into another |
| `plate`, `seal_open` | moment | a stone click and settle; the lever's clank and the slab grinding down | `world/pressure_plate.gd`, `world/seal_lever.gd` |
| `glint` | moment | two small bright notes, a quarter second late so they follow the cue they come with | `ui/hud.gd` when the count rises |
| `cache` | moment | the pouch scooped up | `world/glint_cache_pickup.gd` |
| `pay`, `built` | moment | four coins counted out; two hammer taps and a warm chord, after the coins | `Village.changed` for a restore |
| `quest_start`, `quest_done` | moment | two rising notes; the three-note chime with a held note | `Quests.started`, `Quests.completed` |
| `talk` | confirm | a small wooden tok | `ui/dialogue_box.gd`: a line opening, and every press that turns one |
| `ui_confirm`, `ui_cancel` | confirm | a tok; two quick low falling notes | a setting changed, a pad tapped; "Not tonight" |
| `pause_open`, `pause_close` | confirm | two soft notes down; the same two up | `core/sound.gd` watching the pause |
| `card_start`, `card_end` | moment | a slow rise over an open fifth; the same notes coming home to C | `game.gd` `_show_due_card` (the opening and closing cards) |
| `rest` | moment | the old lullaby, shorter | `world/rest_spot.gd` |
| `raid_horn` | moment | a horn from the halt road, far off and low-passed, a short call and a long one | `Raids.prepare_requested` (the night announced) |
| `raid_bell` | moment | two strikes of the village bell | `Raids.ring()` |
| `raid_wave` | moment | two low pulses: brief, not an alarm | `world/raid_night.gd` `_next_wave` |
| `hurdle_hit`, `hurdle_break` | moment | a blow on wood and the rails rattling; a crack and the rails coming down | `world/raid_barricade.gd` `batter` |
| `lantern_hit` | moment | glass and iron ringing dully over the blow | `world/raid_lantern.gd` `batter` (not the blow that fells it: that is `night_lost`) |
| `night_won`, `night_lost` | moment | a rising run and a held note; three slow low notes down | `Raids.finished` |

| Loop | Sound | Where |
| --- | --- | --- |
| `woodland` | wind in the crowns, leaves stirring, birds near and far | the woodland |
| `crossroads` | low wind between the houses, sparrows kept far, a dove, a sign creaking, one far bell note | Crossroads |
| `undercroft` | low cave air that breathes, a hollow tone in the vaults, water dripping with two soft echoes | the Undercroft |
| `night` | crickets in two voices, low wind, two slow gusts | Crossroads while the first night runs (from the bell to the night's end) |

A creature's hurt and the arrow's hit are one moment (only an arrow hurts a creature), so they are one cue, `arrow_hit`. Paying at a build mark and the building restored are one moment too (`Village.restore` does both at once); they are two cues that start together, and `built` holds its first 0.38 s silent so the coins are heard first.

### The engine (`game/core/sound.gd`, autoload `Sound`)

- `Sound.play(cue)` plays an effect if the rules allow it and returns whether it started. `Sound.ambience(id)` names the one loop that should play.
- Two buses, `Effects` and `Ambience`, made at start. Eight effect players; a ninth cue at once takes the oldest one's place. Every effect is loaded at start.
- One loop at a time on two players. A zone change crossfades over 1.5 s at equal power. Under the pause menu the loop falls silent within 0.25 s and is held where it is until the game goes on. A zone with no loop (a lab zone) is silent.
- The pause ends the world's effects that are sounding; while the tree is paused only confirms start. Effects are not cut at a zone change: they are finite, the longest 1.95 s.
- Hooks: this autoload listens to the signals other autoloads already send (zones, quests, the village, raids, `Glance.on_clink`; not `Dialogue.opened`, where `Dialogue.talk` takes any listener for a dialogue box and waits for it). The rest are one-line `Sound.play` calls at the moment itself. The player's cues are read from the player by `actors/player_sounds.gd`, a child `game.gd` adds; `actors/player.gd` is not changed.
- **Silent runs.** `Sound` is inactive, and `play` and `ambience` do nothing, when the engine runs on the Dummy audio driver (every headless run, `check:godot`, the playtest runner, the screenshot recipes) and under the play driver (`--play`). `-- --sound` turns it on all the same and `--sound-trace` prints one `SOUND <physics frame> <cue> played|skipped:<why>` line per cue asked for, so a route can show which cues its play raises. A test turns it on with `Sound.set_active(true)` and gives it a clock.
- Where a larger cue covers the same moment, the smaller stays quiet: a quest accepted by the line that finished another (`quest_done`), getting up from the defeat that lost the night (`night_lost`), a walk into town with the night announced (the horn, not the door).

### Playback rules (Godot)

`game/core/sound_rules.gd` carries `lib/sound-rules.ts` over, with one tier more.

| Tier | Rule |
| --- | --- |
| **confirm** | Always plays while effects are on: it tells you the press landed. The only tier that starts while the game is paused |
| **moment** | Plays while effects are on |
| **flavour** | At most one every 600 ms; none with Gentle sound |
| **step** | The footsteps' own spacing, so they never use up the flavour's: at most one every 200 ms; none with Gentle sound |

- The same cue asked for twice within 90 ms is one sound.
- A new cue needs a tier in the generator's table; the generator refuses one without, and `test/test_sound.gd` fails on a cue named in code that does not exist, and on a cue made that nothing plays.

### Settings

The pause menu has a Sound panel beside it (`game/ui/sound_menu.gd`), with rows as tall as the pause menu's (44 logical points):

- **Sound effects** (on by default): off stops what is sounding and starts nothing.
- **Ambience** (on by default): the loop's own switch.
- **Gentle sound** (off by default): confirms and moments only, and no two effects within 400 ms. It does not follow Reduced motion and Reduced motion does not follow it.

They are saved with the other settings (`settings.sound_effects`, `settings.ambience`, `settings.gentle_sound`). The save's version went from 1 to 2 for them: a save from before sound loads with the defaults (`game/test/fixtures/saves/v1-main-before-sound.json`, a save written by main on 13 Nov).

### Not verified

Everything above was checked by measurement and by tests, not by ear. Nobody has listened to these sounds: not on a speaker, not on headphones, not on a phone. The measurements (peak, RMS, an A-weighted short-term level, the share of energy above 250 Hz, spectral centroid, loop seams, a spectrogram sheet) say that nothing is loud, bright or clicking; they cannot say that a cue sounds like what it is meant to be, or that the mix is pleasant. Treat every sound as a first draft to tune by ear. Not checked either: a real audio device (the container has none), the web export's autoplay rule (a browser plays nothing before the first key or click), and what a phone does when the app goes to the background.

