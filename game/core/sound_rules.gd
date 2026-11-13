class_name SoundRules
extends RefCounted
## The playback rules (docs/vision/sound.md, "Playback rules"; the old app's lib/sound-rules.ts, carried
## over). Pure, so the tests can hold them without a sound card: core/sound.gd asks `refusal` before every
## effect and tells `played` when one starts.
##
## Every cue has a tier (game/audio/cues.json, written by scripts/audio/game_sounds.py):
##   confirm   the answer to a press (a menu choice, a line turning, the pause menu). Always plays while
##             effects are on: it tells the player the press landed.
##   moment    a beat of the game (a shot, a hit, a tell, a door, a quest, the bell). Plays while effects
##             are on.
##   flavour   pleasant once, tiring when stacked (the bow's creak, an arrow in a wall): at most one every
##             FLAVOUR_GAP_MS, and none with Gentle sound.
##   step      the footsteps, which have their own spacing so they never use up the flavour's: at most one
##             every STEP_GAP_MS, and none with Gentle sound.
## The same cue asked for twice within REPEAT_MS is one sound (a hook and a signal for the same moment).
##
## Gentle sound (the pause menu, off by default) is the reduced-stimulation setting: confirms and moments
## only, and no two effects start within GENTLE_GAP_MS of each other. It is its own switch: reduced motion
## does not turn it on, and it does not touch the ambience, which has its own.

const TIERS := ["confirm", "moment", "flavour", "step"]
const REPEAT_MS := 90
const FLAVOUR_GAP_MS := 600
const STEP_GAP_MS := 200
const GENTLE_GAP_MS := 400
const NEVER := -1000000

## When each kind of cue last started (ms): `any`, `flavour`, `step`, and per cue under `cue`.
static func empty_history() -> Dictionary:
	return {"any": NEVER, "flavour": NEVER, "step": NEVER, "cue": {}}

## "" when `cue` may start at `now` (ms), else why not: "repeat", "gentle", "gentle_gap", "flavour_gap"
## or "step_gap".
static func refusal(cue: StringName, tier: String, now: int, history: Dictionary, gentle: bool) -> String:
	if now - int(history.cue.get(cue, NEVER)) < REPEAT_MS:
		return "repeat"
	if gentle and (tier == "flavour" or tier == "step"):
		return "gentle"
	if gentle and now - int(history.any) < GENTLE_GAP_MS:
		return "gentle_gap"
	if tier == "flavour" and now - int(history.flavour) < FLAVOUR_GAP_MS:
		return "flavour_gap"
	if tier == "step" and now - int(history.step) < STEP_GAP_MS:
		return "step_gap"
	return ""

## Records that `cue` started at `now`.
static func played(cue: StringName, tier: String, now: int, history: Dictionary) -> void:
	history.any = now
	history.cue[cue] = now
	if tier == "flavour" or tier == "step":
		history[tier] = now
