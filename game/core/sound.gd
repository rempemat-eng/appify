extends Node
## The game's sound (docs/vision/sound.md, "The Godot game"). Every sound is generated from code like the
## art (scripts/audio/game_sounds.py writes game/audio and its cue table, cues.json) and mastered in its
## file, so everything plays at volume 1; only an ambience crossfade moves a volume.
##
##   Sound.play(&"glance")       an effect, by cue. It asks the playback rules first (core/sound_rules.gd:
##                               tiers, the same-cue repeat guard, Gentle sound) and returns whether it started.
##   Sound.ambience(&"woodland") the one loop that should be playing ("" for none). The zone and the raid
##                               set it; a change crossfades, the pause menu holds it silent.
##
## Sound is decoration: nothing reads whether a cue played, no rule or reward waits on one, and every cue
## has a visible reaction of its own. Settings (the pause menu's Sound panel, ui/sound_menu.gd), saved with
## the others: `sound_effects` and `ambience` (on by default) and `gentle_sound` (off by default).
##
## Silent runs. The autoload is inactive, and `play` and `ambience` do nothing at all, when the engine has
## no sound card to play to (the Dummy audio driver: every headless run, check.sh, the playtest runner, the
## screenshot recipes) and under the play driver (`--play`). `-- --sound` turns it on all the same, and
## `--sound-trace` prints one line per cue asked for, so a route can show which cues its play raises
## (docs/godot.md). A test turns it on with `set_active(true)` and gives it a clock.
##
## This node hooks the cues that other autoloads already announce (a zone change, a quest, a restore, the
## raid's horn and its end, a glancing arrow). The rest are one-line `Sound.play` calls at the moment
## itself, and the player's are read from the player by actors/player_sounds.gd. It does not listen to
## Dialogue.opened: Dialogue.talk takes any listener there for a dialogue box and waits for it to close
## (13 Nov: with this node listening, every talk in a run without a box waited for ever). The box plays
## the line's tok itself (ui/dialogue_box.gd).

signal cue_started(cue: StringName)

const CUES := "res://audio/cues.json"
const SURFACES := "res://data/sound/surfaces.json"
const DIR := "res://audio/"
const BUS_EFFECTS := &"Effects"
const BUS_AMBIENCE := &"Ambience"
const POOL := 8               ## effect players; a ninth cue at once takes the oldest one's place
const CROSSFADE := 1.5        ## seconds from one loop to the next
const HOLD_FADE := 0.25       ## seconds to silence under the pause menu, or when ambience is switched off
const DENSITY := 3.0

## Which loop a zone plays (a zone not listed, a lab zone, is silent) and the loop of a raid's night.
const ZONE_LOOPS := {"woodland": &"woodland", "crossroads": &"crossroads", "undercroft": &"undercroft"}
const NIGHT_LOOP := &"night"
## Zones entered and left over stone (the hatch and the stair), not through a door.
const STONE_DOORS := ["undercroft"]
## Cues chosen by a value the game already has: a creature's role, the Thornback's attack, a surface, a card.
const TELLS := {"rusher": &"tell_rusher", "shooter": &"tell_shooter", "shield": &"tell_shield", "elite": &"tell_elite"}
const STRIKES := {"shooter": &"enemy_spit"}
const BOSS_TELLS := {"charge": &"boss_tell_charge", "volley": &"boss_tell_volley", "slam": &"boss_tell_slam"}
const BOSS_ATTACKS := {"charge": &"boss_charge", "volley": &"boss_volley", "slam": &"boss_slam"}
const STEPS := {"grass": &"step_grass", "stone": &"step_stone", "wood": &"step_wood"}
const CARDS := {"opening": &"card_start", "closing": &"card_end"}

var active := false                 ## false: every call here is a no-op (see "Silent runs" above)
var effects: Dictionary = {}        ## cue -> {files, tier, seconds, what} (cues.json)
var loops: Dictionary = {}          ## loop id -> {file, rate, frames, seconds, what}
var surfaces: Dictionary = {}       ## zone id -> {default, areas: [{rect, surface}]} in world px
var trace := false
var clock := Callable()             ## tests: a clock in ms, in place of the engine's

var _history := SoundRules.empty_history()
var _players: Array[AudioStreamPlayer] = []
var _player_cue: Array[StringName] = []
var _player_start: Array[int] = []
var _streams: Dictionary = {}
var _variant: Dictionary = {}       ## cue -> which of its files plays next (they take turns)
var _unknown: Dictionary = {}       ## cues asked for that do not exist, warned about once each
var _loop_players: Array[AudioStreamPlayer] = []
var _loop_ids: Array[StringName] = [&"", &""]
var _loop_gain: Array[float] = [0.0, 0.0]
var _place_loop: StringName = &""   ## what `ambience` last asked for
var _from_zone := ""                ## the zone the player was in before the one now loading
var _was_paused := false
var _last_usec := 0

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS   # the pause menu's own answers play while the tree is paused
	set_process(false)
	_load_tables()
	var args := OS.get_cmdline_user_args()
	trace = args.has("--sound-trace")
	hook_glance()
	Zones.zone_changing.connect(_on_zone_changing)
	Zones.zone_changed.connect(_on_zone_changed)
	Quests.completed.connect(func(_id: String) -> void: play(&"quest_done"))
	Quests.started.connect(func(_id: String) -> void: play(&"quest_start", &"quest_done"))
	Village.changed.connect(_on_village_changed)
	Raids.prepare_requested.connect(func() -> void: play(&"raid_horn"))
	Raids.changed.connect(func(_state: String) -> void: ambience(place_loop()))
	Raids.finished.connect(func(won: bool) -> void: play(&"night_won" if won else &"night_lost"))
	set_active(wanted(AudioServer.get_driver_name(), DisplayServer.get_name(), args))

## The game is closing. A stream still sounding when the engine shuts down is let go one mix step later,
## and with no step left the engine reported it as leaked ("1 resources still in use at exit": the loop,
## about every other run, 13 Nov). So everything stops here, and the audio thread gets a moment for that step.
const EXIT_WAIT_MS := 60
func _exit_tree() -> void:
	if not active:
		return
	for p: AudioStreamPlayer in _players + _loop_players:
		p.stop()
	OS.delay_msec(EXIT_WAIT_MS)

## Whether this run should make sound: not without a sound card or a window, and not under the play driver,
## unless `--sound` asks for it.
static func wanted(driver: String, display: String, args: PackedStringArray) -> bool:
	if args.has("--sound"):
		return true
	if driver == "Dummy" or display == "headless":
		return false
	for a in args:
		if a == "--play" or a.begins_with("--play="):
			return false
	return true

func set_active(on: bool) -> void:
	if on == active:
		return
	active = on
	set_process(on)
	if on:
		_ensure_players()
		_history = SoundRules.empty_history()
		_was_paused = get_tree().paused
		_last_usec = Time.get_ticks_usec()
		ambience(place_loop())
	else:
		stop_effects()
		for i in _loop_players.size():
			_loop_players[i].stop()
			_loop_ids[i] = &""
			_loop_gain[i] = 0.0

func _load_tables() -> void:
	var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string(CUES))
	if typeof(doc) != TYPE_DICTIONARY:
		push_error("Sound: %s is not a cue table (run npm run sound:game)" % CUES)
		return
	for cue: String in doc.get("effects", {}):
		effects[StringName(cue)] = doc.effects[cue]
	for id: String in doc.get("ambience", {}):
		loops[StringName(id)] = doc.ambience[id]
	var places: Variant = JSON.parse_string(FileAccess.get_file_as_string(SURFACES))
	surfaces = places if typeof(places) == TYPE_DICTIONARY else {}

# --- effects ----------------------------------------------------------------------------------
## Plays `cue` if the rules allow it now; true when it started. `unless` names a larger cue for the same
## moment: when that one has just started, this one stays quiet (a quest accepted by the line that
## finished another, getting up from the defeat that lost the night).
func play(cue: StringName, unless: StringName = &"") -> bool:
	if not active:
		return false
	if not effects.has(cue):
		if not _unknown.has(cue):
			_unknown[cue] = true
			push_warning("Sound: no cue '%s' (scripts/audio/game_sounds.py EFFECTS)" % cue)
		return false
	var tier := String(effects[cue].tier)
	var now := now_ms()
	var why := ""
	if not bool(SaveGame.setting("sound_effects", true)):
		why = "off"
	elif get_tree().paused and tier != "confirm":
		why = "paused"                           # the world is held: only the menu answers
	elif unless != &"" and now - int(_history.cue.get(unless, SoundRules.NEVER)) < SoundRules.REPEAT_MS:
		why = "covered"
	else:
		why = SoundRules.refusal(cue, tier, now, _history, bool(SaveGame.setting("gentle_sound", false)))
	if trace:
		print("SOUND %d %s %s" % [Engine.get_physics_frames(), cue, "played" if why == "" else "skipped:" + why])
	if why != "":
		return false
	SoundRules.played(cue, tier, now, _history)
	_start(cue, now)
	cue_started.emit(cue)
	return true

func now_ms() -> int:
	return int(clock.call()) if clock.is_valid() else Time.get_ticks_msec()

func _start(cue: StringName, now: int) -> void:
	var files: Array = effects[cue].files
	var turn := int(_variant.get(cue, 0)) % files.size()
	_variant[cue] = (turn + 1) % files.size()
	var slot := 0
	for i in _players.size():
		if not _players[i].playing:
			slot = i
			break
		if _player_start[i] < _player_start[slot]:
			slot = i                               # all busy: the oldest gives way
	var p := _players[slot]
	p.stream = _stream(String(files[turn]))
	p.play()
	_player_cue[slot] = cue
	_player_start[slot] = now

## Ends the effects that are sounding. With `keep_confirms`, a menu's own answer is left to finish.
func stop_effects(keep_confirms := false) -> void:
	for i in _players.size():
		if _players[i].playing and not (keep_confirms and tier_of(_player_cue[i]) == "confirm"):
			_players[i].stop()

## The cues sounding right now (for the tests).
func sounding() -> Array[StringName]:
	var out: Array[StringName] = []
	for i in _players.size():
		if _players[i].playing:
			out.append(_player_cue[i])
	return out

func tier_of(cue: StringName) -> String:
	return String(effects.get(cue, {}).get("tier", ""))

## A setting changed in the menu: effects switched off stop at once (the ambience follows `steer`).
func settings_changed() -> void:
	if active and not bool(SaveGame.setting("sound_effects", true)):
		stop_effects()

# --- cues chosen by what the game already knows -------------------------------------------------
func tell(role: String) -> void:
	play(TELLS.get(role, &"tell_rusher"))

func strike(role: String) -> void:
	play(STRIKES.get(role, &"enemy_strike"))

func boss_tell(attack: String) -> void:
	play(BOSS_TELLS.get(attack, &"boss_tell_charge"))

func boss_attack(attack: String) -> void:
	play(BOSS_ATTACKS.get(attack, &"boss_charge"))

func card(id: String) -> void:
	play(CARDS.get(id, &"card_start"))

## A footstep at `at` (global texels) on whatever lies there (data/sound/surfaces.json).
func step(at: Vector2) -> void:
	if not active:
		return
	var zone := Zones.current
	play(STEPS.get(surface_at(zone.zone_id if zone != null and is_instance_valid(zone) else "", at), &"step_grass"))

## "grass", "stone" or "wood" at a point of a zone: the first of the zone's areas that holds it, else the
## zone's default, else grass.
func surface_at(zone_id: String, at: Vector2) -> String:
	var place: Dictionary = surfaces.get(zone_id, {})
	var p := at / DENSITY
	for area: Dictionary in place.get("areas", []):
		var r: Array = area.rect
		if Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3])).has_point(p):
			return String(area.surface)
	return String(place.get("default", "grass"))

# --- ambience ---------------------------------------------------------------------------------
## Asks for the loop `id` ("" or an unknown id: none). `steer` moves the two loop players towards it.
func ambience(id: StringName) -> void:
	_place_loop = id if loops.has(id) else &""

## The loop the place the player stands in should play: the night's while a raid runs in this zone, else
## the zone's own, else none.
func place_loop() -> StringName:
	var zone := Zones.current
	if zone == null or not is_instance_valid(zone):
		return &""
	if Raids.running() and String(Raids.current().get("zone", "")) == zone.zone_id:
		return NIGHT_LOOP
	return ZONE_LOOPS.get(zone.zone_id, &"")

## The loop that should be heard right now: none while ambience is switched off.
func wanted_loop() -> StringName:
	return _place_loop if active and bool(SaveGame.setting("ambience", true)) else &""

## One step of the crossfade, `dt` seconds long: the wanted loop rises to full, any other falls to silence
## and stops. Under the pause menu the wanted loop falls silent too, and is held where it is until the
## game goes on. Equal power, so two loops crossing do not dip.
func steer(dt: float) -> void:
	if _loop_players.is_empty():
		return
	var want := wanted_loop()
	var held := get_tree().paused
	var slot := _loop_ids.find(want) if want != &"" else -1
	if want != &"" and slot == -1:
		slot = 0 if _loop_gain[0] <= _loop_gain[1] else 1
		_loop_players[slot].stream = _loop_stream(want)
		_loop_players[slot].stream_paused = false
		_loop_players[slot].volume_linear = 0.0
		_loop_players[slot].play()
		_loop_ids[slot] = want
		_loop_gain[slot] = 0.0
	var seconds := HOLD_FADE if held else CROSSFADE
	for i in _loop_players.size():
		if _loop_ids[i] == &"":
			continue
		var p := _loop_players[i]
		var rising := i == slot and not held
		_loop_gain[i] = move_toward(_loop_gain[i], 1.0 if rising else 0.0, dt / seconds)
		p.volume_linear = sqrt(_loop_gain[i])
		if rising:
			p.stream_paused = false
		elif _loop_gain[i] <= 0.0:
			if i == slot:
				p.stream_paused = true            # held under the pause menu: it goes on from here
			else:
				p.stop()
				_loop_ids[i] = &""

## What the two loop players hold and how loud (for the tests): [{id, gain, playing, held}].
func loop_state() -> Array:
	var out := []
	for i in _loop_players.size():
		out.append({"id": _loop_ids[i], "gain": _loop_gain[i], "playing": _loop_players[i].playing,
			"held": _loop_players[i].stream_paused})
	return out

func _process(_delta: float) -> void:
	# the wall clock: a hit-stop slows the engine's time, and a fade should not stall with it
	var now := Time.get_ticks_usec()
	var dt := clampf(float(now - _last_usec) / 1000000.0, 0.0, 0.25)
	_last_usec = now
	_watch_pause()
	steer(dt)

## The pause menu opening and closing (game.gd and ui/pause_menu.gd pause the tree; this only watches):
## the world's effects end with the pause, and the menu answers with its own two cues.
func _watch_pause() -> void:
	var paused := get_tree().paused
	if paused == _was_paused:
		return
	_was_paused = paused
	if paused:
		stop_effects(true)
		play(&"pause_open")
	else:
		play(&"pause_close")

# --- hooks ------------------------------------------------------------------------------------
## Every glancing arrow calls Glance.clink (enemies/glance.gd): this is the hook it was left for. A method,
## not a lambda: a lambda kept in that static variable outlived this script when the game closed, and the
## engine aborted on exit with a corrupted heap (13 Nov).
func hook_glance() -> void:
	Glance.on_clink = _on_clink

func _on_clink(_at: Vector2) -> void:
	play(&"glance")

func _on_zone_changing(_to: String) -> void:
	_from_zone = Zones.current.zone_id if Zones.current != null and is_instance_valid(Zones.current) else ""

## A walk from one zone into another sounds its door. The game's start and getting up where the player
## fell are not walks; and a walk into town with the night announced leaves the moment to the horn.
func _on_zone_changed(zone: Zone) -> void:
	ambience(place_loop())
	if _from_zone == "" or _from_zone == zone.zone_id:
		return
	if Raids.state() == "announced" and String(Raids.current().get("zone", "")) == zone.zone_id:
		return
	play(&"door_stone" if STONE_DOORS.has(zone.zone_id) or STONE_DOORS.has(_from_zone) else &"door")

## Village.changed carries a restore's id when a building is restored (and a flag's name for the
## Undercroft's plate and lever, which sound themselves). The build comes first, so Gentle sound keeps it.
func _on_village_changed(id: String) -> void:
	if Village.sites.has(id) and Village.is_restored(id):
		play(&"built")
		play(&"pay")

# --- players ----------------------------------------------------------------------------------
func _ensure_players() -> void:
	if not _players.is_empty():
		return
	for bus: StringName in [BUS_EFFECTS, BUS_AMBIENCE]:
		if AudioServer.get_bus_index(bus) == -1:
			AudioServer.add_bus()
			AudioServer.set_bus_name(AudioServer.bus_count - 1, bus)
			AudioServer.set_bus_send(AudioServer.bus_count - 1, &"Master")
	for i in POOL:
		var p := AudioStreamPlayer.new()
		p.name = "Effect%d" % i
		p.bus = BUS_EFFECTS
		add_child(p)
		_players.append(p)
		_player_cue.append(&"")
		_player_start.append(SoundRules.NEVER)
	for i in 2:
		var p := AudioStreamPlayer.new()
		p.name = "Loop%d" % i
		p.bus = BUS_AMBIENCE
		add_child(p)
		_loop_players.append(p)
	# every effect is loaded now, so the first shot of a fight does not wait on the disk
	for cue: StringName in effects:
		for file: String in effects[cue].files:
			_stream(file)

func _stream(file: String) -> AudioStream:
	if not _streams.has(file):
		_streams[file] = load(DIR + file)
	return _streams[file]

## A loop's stream, set to loop over all of its frames (the generator joins its end to its start).
func _loop_stream(id: StringName) -> AudioStream:
	var s := _stream(String(loops[id].file)) as AudioStreamWAV
	if s != null and s.loop_mode != AudioStreamWAV.LOOP_FORWARD:
		s.loop_mode = AudioStreamWAV.LOOP_FORWARD
		s.loop_begin = 0
		s.loop_end = int(loops[id].frames)
	return s
