extends Node
## Raids on Crossroads (game-design.md 7.6, on claude-a/game-design-v2; docs/vision/vertical-slice.md beat 8).
## Each raid is a JSON file in res://data/raids/ (the first night: data/raids/first_night.json). This
## autoload keeps the raid's state in the save and moves it on; world/raid_night.gd plays it in the zone and
## ui/raid_screen.gd is its prepare screen.
##
## The save holds one raid at a time (7.6: at most one pending), SaveGame.data.raid:
##   {id, state, postponed, wave, layout: {pad id: defence kind or ""}, repairs}
## and the states run:
##   none ........ no raid yet. The raid's `attention_if` (the lantern lit: shard_home:woodland) earns it;
##                 it is announced on the next walk into its zone from another zone, once `announce_if` holds.
##   announced ... the prepare screen is up: "Sound the anvil", or "Not tonight" while postponements are left.
##   postponed ... put off; asked again on the next walk into town.
##   pending ..... put off twice: it begins the next time the player walks into town (the screen still comes
##                 first, untimed, with no "Not tonight").
##   running ..... Hale has struck her anvil; `wave` is the wave under way.
##   won ......... the purse is paid (data/balance/glint.json raids.<id>), the reward's flags set, its
##                 offered restore added. It does not come again (Matt, 13 Nov: a one-off, and Hale says so).
##   lost ........ the lantern fell, or the player went down: the next walk into town offers the raid again
##                 (postponements anew).
## The stake (Matt, 13 Nov: "Shard dims until held"; the lantern dark and the square worse until a night is
## won, no progress or Glint lost): a lost night sets the raid's `lantern.dark_flag` (the first night: the
## save flag shard_lantern_dark) and its `repairs`, and only a won night clears them. While the flag holds
## the shard lantern stands dark and the repairs show in the zone (world/raid_night.gd), on every load and
## through every later state of the raid. A raid with no dark flag keeps the older rule: its repairs go on
## the next walk into town. Nothing else is taken: no quest, no restore, and no Glint, so going down while a
## night runs leaves no cache (game.gd asks `downed_in_a_night`; every other defeat keeps the cache rule).
## A save that is `lost` without the flag (made before 15 Nov) gets it on load, and one whose raid is won
## loses it.
## Nothing here reads a clock. Getting up after a defeat, or starting the game, is not a walk into town: a
## raid waiting on the screen (announced) or under way (running) shows the screen again at once, from wave 1.
## Leaving the zone while the raid runs puts it back to pending.

signal changed(state: String)
## The prepare screen should open (game.gd shows ui/raid_screen.gd). Emitted deferred, once the zone is in.
signal prepare_requested
## The night is over: true when the lantern held.
signal finished(won: bool)

const DIR := "res://data/raids"
const DENSITY := 3.0
## Every state a raid record can hold (SaveGame keeps the same list: a state it does not know loads as "none").
const STATES := ["none", "announced", "postponed", "pending", "running", "won", "lost"]

var defs: Dictionary = {}
var _from := ""          ## the zone the player was in before the one now loading ("" at the start of a run)
## How the last night was lost, until the zone has said so on screen: "down" when the player went down (the
## zone reloads, so the card shows on getting up), "" once told. Not saved: a quit after a loss tells nothing.
var loss_untold := ""
## True when the lantern was already dark as the last night was lost (a second loss): the cards then say it
## stays dark, not that it goes out. Not saved, as `loss_untold`.
var lost_while_dark := false
## False from the anvil until wave 1 comes (world/raid_night.gd holds it back until the player nears the
## square), so the tracker says the shardstruck are coming instead of counting a wave not there yet. Not
## saved: a night cut short comes back to the screen, and the anvil resets it.
var wave_begun := false

func _ready() -> void:
	load_dir(DIR)
	Zones.zone_changing.connect(_on_zone_changing)
	Zones.zone_changed.connect(_on_zone_changed)
	SaveGame.loaded.connect(_on_loaded)
	_on_loaded()

func _on_loaded() -> void:
	offer_restores()
	# a night lost before the stake existed: the record says lost, so the lantern is dark. A raid already won
	# is never dark, whatever a hand-edited or older save's flags say
	for id: String in defs:
		if won(id):
			_set_dark(defs[id], false)
	var def := current()
	if not def.is_empty() and state() == "lost" and not won(String(def.id)):
		_set_dark(def, true)

func load_dir(dir: String) -> void:
	var files := Array(DirAccess.get_files_at(dir))
	files.sort()
	for f: String in files:
		if f.ends_with(".json"):
			var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string(dir.path_join(f)))
			if typeof(doc) != TYPE_DICTIONARY or not doc.has("id") or not doc.has("waves"):
				push_error("Raids: %s is not a raid" % f)
				continue
			defs[doc.id] = doc

# --- the record ------------------------------------------------------------------------------
func rec() -> Dictionary:
	if not SaveGame.data.has("raid") or not SaveGame.data.raid is Dictionary:
		SaveGame.data.raid = SaveGame.fresh().raid
	return SaveGame.data.raid

func state() -> String:
	return String(rec().get("state", "none"))

## The raid the record is about, or the first not yet won whose zone is built ({} when there is none).
func current() -> Dictionary:
	var id := String(rec().get("id", ""))
	if defs.has(id):
		return defs[id]
	var ids := defs.keys()
	ids.sort()
	for other: String in ids:
		if not won(other):
			return defs[other]
	return {}

## True once raid `id` has been won (every one of its reward flags is set).
func won(id: String) -> bool:
	var flags: Array = defs.get(id, {}).get("reward", {}).get("flags", [])
	if flags.is_empty():
		return false
	for f: String in flags:
		if not SaveGame.has_flag(f):
			return false
	return true

func postponed() -> int:
	return int(rec().get("postponed", 0))

func postpones_left() -> int:
	return maxi(int(current().get("postpones", 2)) - postponed(), 0)

## True while the raid's attention has been earned and its announcement may come. A raid already won is
## never earned again (a one-off), whatever state its record holds.
func earned(def: Dictionary) -> bool:
	return not def.is_empty() and not won(String(def.get("id", ""))) \
		and Quests.check(def.get("attention_if")) and Quests.check(def.get("announce_if"))

func running() -> bool:
	return state() == "running"

# --- the stake: a lost night leaves the lantern dark until a night is held -------------------------
## The save flag that holds while raid `def`'s lantern is dark ("" when the raid has no such stake).
func dark_flag(def: Dictionary = {}) -> String:
	if def.is_empty():
		def = current()
	return String(def.get("lantern", {}).get("dark_flag", ""))

## True while the shard lantern of raid `def` (default: the current one) is dark: a night was lost and none
## has been held since.
func lantern_dark(def: Dictionary = {}) -> bool:
	var flag := dark_flag(def)
	return flag != "" and SaveGame.has_flag(flag)

func _set_dark(def: Dictionary, on: bool) -> void:
	var flag := dark_flag(def)
	if flag != "" and SaveGame.has_flag(flag) != on:
		SaveGame.set_flag(flag, on)

# --- moving on --------------------------------------------------------------------------------
func _to_state(st: String) -> void:
	rec().state = st
	changed.emit(st)

## The player walked into `zone_id` from `from_zone` ("" when the game starts there, or when they get up
## where they fell). Moves the raid on and returns true when the prepare screen should open.
func arrive(zone_id: String, from_zone: String) -> bool:
	var def := current()
	if def.is_empty() or zone_id != String(def.get("zone", "")):
		return false
	if won(String(def.id)):
		return false                  # a one-off: a won raid is not offered, begun or paid again
	var r := rec()
	var walked_in := from_zone != "" and from_zone != zone_id
	if walked_in and bool(r.get("repairs", false)) and not lantern_dark(def):
		r.repairs = false             # no stake: the villagers mended it while the player was away
		changed.emit(state())
	match state():
		"none":
			if walked_in and earned(def):
				r.id = String(def.id)
				r.postponed = 0
				_announce()
				return true
		"postponed", "pending":
			if walked_in:
				_announce()
				return true
		"lost":
			if walked_in:
				r.postponed = 0
				_announce()
				return true
		"announced":
			_announce()
			return true
		"running":
			# the game started (or reloaded) in the middle of a night: back to the screen, from wave 1
			r.wave = 0
			_announce()
			return true
	return false

func _announce() -> void:
	var def := current()
	SaveGame.set_flag("%s_announced" % def.id)
	_to_state("announced")
	prepare_requested.emit.call_deferred()

## "Not tonight": the raid waits for the next walk into town. False when no postponement is left.
func postpone() -> bool:
	if state() != "announced" or postpones_left() <= 0:
		return false
	rec().postponed = postponed() + 1
	SaveGame.set_flag("%s_postponed" % current().id)
	_to_state("postponed" if postpones_left() > 0 else "pending")
	return true

## "Sound the anvil": the night begins (world/raid_night.gd starts the waves on `changed`). Night one is
## called by Hale striking her anvil (Matt, 13 Nov); the village bell is rebuilt later, for the wolf moon.
func ring() -> bool:
	if state() != "announced":
		return false
	SaveGame.set_flag("%s_postponed" % current().id, false)
	rec().wave = 0
	wave_begun = false
	_to_state("running")
	Sound.play(&"raid_anvil")          # Hale at her anvil (Matt, 13 Nov); the bell is the wolf moon's
	return true

func wave_started(index: int) -> void:
	if running():
		rec().wave = index
		wave_begun = true

## The lantern held through the last wave: the purse, the reward's flags and the offered restore.
func win() -> int:
	if not running():
		return 0
	var def := current()
	var purse := int(GlintCache.balance().get("raids", {}).get(String(def.id), 0))
	SaveGame.add_glint(purse)
	for f: String in def.get("reward", {}).get("flags", []):
		SaveGame.set_flag(f)
	offer_restores()
	_set_dark(def, false)              # a night held: the lantern is lit again, and stays lit
	rec().repairs = false              # and the square is mended
	_to_state("won")
	finished.emit(true)
	return purse

## The lantern fell (`how` "lantern"), or the player went down ("down"): the lantern dark and the repairs
## showing until a night is held. Nothing else is taken.
func lose(how := "lantern") -> void:
	if not running():
		return
	loss_untold = how
	lost_while_dark = lantern_dark(current())
	rec().repairs = true
	_set_dark(current(), true)
	_to_state("lost")
	finished.emit(false)

func player_downed() -> void:
	if running():
		lose("down")

## True from the moment the player goes down while a night runs until the zone has told of it: game.gd asks
## it as the player falls (after `player_downed`), and leaves no cache of Glint for such a defeat (Matt,
## 13 Nov: no Glint is lost on a lost night).
func downed_in_a_night() -> bool:
	return state() == "lost" and loss_untold == "down"

# --- zones ----------------------------------------------------------------------------------
func _on_zone_changing(to_zone: String) -> void:
	_from = String(SaveGame.data.zone) if Zones.current != null and is_instance_valid(Zones.current) else ""
	# walking out mid-night: the raid waits, and begins again on the next walk into town
	if running() and _from == String(current().get("zone", "")) and to_zone != _from:
		_to_state("pending")

func _on_zone_changed(zone: Zone) -> void:
	arrive(zone.zone_id, _from)
	var def := current()
	if def.is_empty() or zone.zone_id != String(def.get("zone", "")):
		return
	var night := RaidNight.new()
	night.name = "RaidNight"
	night.def = def
	zone.add_child(night)

# --- the layout -------------------------------------------------------------------------------
## The defence kinds the player has: each needs its building restored (`needs`, a condition).
func kinds_owned(def: Dictionary = {}) -> Array:
	if def.is_empty():
		def = current()
	var out := []
	var kinds: Dictionary = def.get("kinds", {})
	var ids := kinds.keys()
	ids.sort()
	for k: String in ids:
		if Quests.check(kinds[k].get("needs")):
			out.append(k)
	return out

## What stands on `pad`: the last layout chosen, else the raid's prefill (every pad starts filled).
func pad_kind(pad: String, def: Dictionary = {}) -> String:
	if def.is_empty():
		def = current()
	var layout: Dictionary = rec().get("layout", {})
	var kind := String(layout.get(pad, def.get("prefill", "")))
	return kind if kind == "" or def.get("kinds", {}).has(kind) else String(def.get("prefill", ""))

## A tap on a pad: the next kind the player has, then empty, then round again. Returns the new kind.
func cycle_pad(pad: String) -> String:
	var def := current()
	var choices: Array = kinds_owned(def) + [""]
	var i := choices.find(pad_kind(pad, def))
	var next := String(choices[(i + 1) % choices.size()])
	var layout: Dictionary = rec().get("layout", {})
	layout[pad] = next
	rec().layout = layout
	changed.emit(state())
	return next

# --- places, from the zone's plan -------------------------------------------------------------
## The raid's pads, in world px: [{id, at: Vector2, why}], the plan's own where `plan` is true.
func pads(def: Dictionary = {}) -> Array:
	if def.is_empty():
		def = current()
	var plan: Dictionary = Village.plans.get(String(def.get("zone", "")), {})
	var out := []
	for pad: Dictionary in def.get("pads", []):
		var at: Variant = pad.get("at")
		if bool(pad.get("plan", false)):
			for p: Dictionary in plan.get("raid_pads", []):
				if p.id == pad.id:
					at = p.at
		if at is Array and (at as Array).size() == 2:
			out.append({"id": String(pad.id), "at": Vector2(float(at[0]), float(at[1])), "why": String(pad.get("why", "")),
				"span": float(pad.get("span", 0.0))})
		else:
			push_error("Raids: pad %s has no place" % pad.get("id", "?"))
	return out

## The raid's lane in world px: its own `lane_points` where it gives them, else the plan's `raid_lanes`.
func lane(def: Dictionary = {}) -> PackedVector2Array:
	if def.is_empty():
		def = current()
	var out := PackedVector2Array()
	if def.has("lane_points"):
		for p: Array in def.lane_points:
			out.append(Vector2(float(p[0]), float(p[1])))
		return out
	var plan: Dictionary = Village.plans.get(String(def.get("zone", "")), {})
	for l: Dictionary in plan.get("raid_lanes", []):
		if l.id == def.get("lane", ""):
			for p: Array in l.points:
				out.append(Vector2(float(p[0]), float(p[1])))
	return out

## The restore a won raid offers, in Village.sites while the raid is won in this save and gone again
## otherwise (a load, a new game). A plan that defines the same restore keeps its own entry: the first
## night's bell tower is the Crossroads plan's since 16 Nov, so this fallback no longer applies to it. Not offered before the win: the story model (test/story/test_story_model.gd)
## asks every site in Village.sites to be payable from every state.
func offer_restores() -> void:
	for id: String in defs:
		var offer: Dictionary = defs[id].get("reward", {}).get("offers", {})
		if offer.is_empty():
			continue
		var site: Dictionary = Village.sites.get(offer.id, {})
		if not site.is_empty() and not site.has("offered_by"):
			continue                                 # the plan's own entry
		if not won(id):
			Village.sites.erase(offer.id)
			continue
		site = offer.duplicate(true)
		site.plan = String(defs[id].get("zone", ""))
		site.offered_by = id
		Village.sites[offer.id] = site

## The HUD's tracker line while the night runs ("" otherwise).
func tracker_text() -> String:
	if not running():
		return ""
	var def := current()
	if not wave_begun:
		return "%s: Hold the shard lantern (the shardstruck are coming)" % def.get("title", def.id)
	return "%s: Hold the shard lantern (wave %d of %d)" % [def.get("title", def.id), int(rec().get("wave", 0)) + 1, (def.waves as Array).size()]
