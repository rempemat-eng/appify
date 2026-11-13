extends GdUnitTestSuite
## Sound (core/sound.gd, core/sound_rules.gd, ui/sound_menu.gd, actors/player_sounds.gd; docs/vision/sound.md).
## The test runner is one of the silent runs: `Sound.active` is false here unless a test turns it on, and
## a test that does gives it a clock of its own, so nothing waits on a sound card or on the wall clock.
## What these hold: every cue named in the code exists and has a tier; the rules (tiers, the repeat guard,
## Gentle sound); the settings (saved, loaded, a save from before sound migrated to the defaults); the one
## loop and its crossfade and pause; the hooks at the game's moments; the Sound panel's touch layout.
## What they cannot hold: how anything sounds. Nobody has listened to these on a speaker in this suite.

const Audit := preload("res://tools/touch_audit.gd")
const Screen := preload("res://main/pixel_screen.gd")
const PATH := "user://test_sound_save.json"
const FIXTURES := "res://test/fixtures/saves/"

var _now := 0
var _heard: Array[StringName] = []
var _was_table: Dictionary

func before_test() -> void:
	SaveGame.reset()
	get_tree().paused = false
	_now = 100000
	_heard.clear()
	_was_table = Zones.table

func after_test() -> void:
	get_tree().paused = false
	if Sound.cue_started.is_connected(_on_cue):
		Sound.cue_started.disconnect(_on_cue)
	Sound.set_active(false)
	Sound.clock = Callable()
	Sound.hook_glance()
	Zones.table = _was_table
	Zones.current = null
	Zones.root = null
	SaveGame.reset()
	for file: String in [PATH, PATH + ".tmp"]:
		DirAccess.remove_absolute(ProjectSettings.globalize_path(file))

func _on_cue(cue: StringName) -> void:
	_heard.append(cue)

## Sound on for this test, on the test's clock, with its own per-frame stepping off (the tests step it).
func _listen() -> void:
	Sound.clock = func() -> int: return _now
	Sound.set_active(true)
	Sound.set_process(false)
	Sound.cue_started.connect(_on_cue)

func _frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame

# --- silent runs ------------------------------------------------------------------------------
func test_the_test_runner_and_the_play_driver_are_silent() -> void:
	assert_bool(Sound.active).is_false()
	assert_bool(Sound.is_processing()).is_false()
	assert_bool(Sound.play(&"glance")).is_false()
	assert_array(Sound.sounding()).is_empty()
	assert_int(Sound.get_child_count()).is_equal(0)      # no player was ever made
	assert_bool(Sound.wanted("Dummy", "x11", PackedStringArray())).is_false()
	assert_bool(Sound.wanted("PulseAudio", "headless", PackedStringArray())).is_false()
	assert_bool(Sound.wanted("PulseAudio", "x11", PackedStringArray(["--fresh", "--play=route.txt"]))).is_false()
	assert_bool(Sound.wanted("PulseAudio", "x11", PackedStringArray(["--fresh"]))).is_true()
	assert_bool(Sound.wanted("Dummy", "headless", PackedStringArray(["--play=route.txt", "--sound"]))).is_true()

# --- the cue table ----------------------------------------------------------------------------
func _game_scripts(dir := "res://", out: PackedStringArray = PackedStringArray()) -> PackedStringArray:
	for sub in DirAccess.get_directories_at(dir):
		if dir == "res://" and sub in ["addons", "test", "reports", "build"]:
			continue
		if not sub.begins_with("."):
			_game_scripts(dir.path_join(sub), out)
	for file in DirAccess.get_files_at(dir):
		if file.ends_with(".gd"):
			out.append(dir.path_join(file))
	return out

## Every cue the game's code names: the &"..." on any line that plays one, and the tables in core/sound.gd.
func _named_cues() -> Dictionary:
	var named := {}
	var call := RegEx.create_from_string("\\bplay\\(")
	var cue := RegEx.create_from_string("&\"([a-z0-9_]+)\"")
	for path in _game_scripts():
		var in_sound := path == "res://core/sound.gd"
		for line in FileAccess.get_file_as_string(path).split("\n"):
			var code := line.get_slice("#", 0)
			if call.search(code) == null or not (in_sound or code.contains("Sound.play(")):
				continue
			for m in cue.search_all(code):
				named[StringName(m.get_string(1))] = path
	for table: Dictionary in [Sound.TELLS, Sound.STRIKES, Sound.BOSS_TELLS, Sound.BOSS_ATTACKS, Sound.STEPS, Sound.CARDS]:
		for value: StringName in table.values():
			named[value] = "res://core/sound.gd"
	for fallback: StringName in [&"tell_rusher", &"enemy_strike", &"boss_tell_charge", &"boss_charge", &"step_grass", &"card_start"]:
		named[fallback] = "res://core/sound.gd"
	return named

func test_every_cue_named_in_code_exists_and_has_a_tier() -> void:
	var named := _named_cues()
	assert_int(named.size()).is_greater(40)
	for cue: StringName in named:
		assert_bool(Sound.effects.has(cue)).override_failure_message("%s plays '%s', which is not a cue" % [named[cue], cue]).is_true()
	for cue: StringName in Sound.effects:
		var def: Dictionary = Sound.effects[cue]
		assert_bool(SoundRules.TIERS.has(def.tier)).override_failure_message("%s has no tier" % cue).is_true()
		assert_bool(named.has(cue)).override_failure_message("the cue '%s' is made but never played" % cue).is_true()
		assert_float(float(def.seconds)).is_less_equal(2.0)
		assert_array(def.files).is_not_empty()
		for file: String in def.files:
			var stream := load(Sound.DIR + file) as AudioStreamWAV
			assert_object(stream).override_failure_message("%s does not load" % file).is_not_null()
			# plain 16-bit samples, mono, never looping: what was measured is what plays
			assert_int(stream.format).is_equal(AudioStreamWAV.FORMAT_16_BITS)
			assert_bool(stream.stereo).is_false()
			assert_int(stream.loop_mode).is_equal(AudioStreamWAV.LOOP_DISABLED)
			assert_float(stream.get_length()).is_less_equal(2.0)

func test_every_loop_is_used_and_loops_over_all_of_its_frames() -> void:
	var used: Array[StringName] = [Sound.NIGHT_LOOP]
	for id: StringName in Sound.ZONE_LOOPS.values():
		used.append(id)
	for id in used:
		assert_bool(Sound.loops.has(id)).override_failure_message("no loop '%s'" % id).is_true()
	for id: StringName in Sound.loops:
		assert_bool(used.has(id)).override_failure_message("the loop '%s' is made but never played" % id).is_true()
		var stream := Sound._loop_stream(id) as AudioStreamWAV
		assert_int(stream.format).is_equal(AudioStreamWAV.FORMAT_16_BITS)
		assert_int(stream.loop_mode).is_equal(AudioStreamWAV.LOOP_FORWARD)
		assert_int(stream.loop_begin).is_equal(0)
		assert_int(stream.loop_end).is_equal(int(Sound.loops[id].frames))
		assert_int(stream.data.size()).is_equal(int(Sound.loops[id].frames) * 2)
	# the slice's three zones each have one, and a lab zone has none
	for zone in ["woodland", "crossroads", "undercroft"]:
		assert_bool(Sound.ZONE_LOOPS.has(zone)).is_true()
	assert_bool(Sound.ZONE_LOOPS.has("kitlab")).is_false()

# --- the rules --------------------------------------------------------------------------------
func test_the_same_cue_twice_at_once_is_one_sound() -> void:
	var h := SoundRules.empty_history()
	assert_str(SoundRules.refusal(&"glance", "moment", 1000, h, false)).is_equal("")
	SoundRules.played(&"glance", "moment", 1000, h)
	assert_str(SoundRules.refusal(&"glance", "moment", 1000 + SoundRules.REPEAT_MS - 1, h, false)).is_equal("repeat")
	assert_str(SoundRules.refusal(&"glance", "moment", 1000 + SoundRules.REPEAT_MS, h, false)).is_equal("")
	# another cue is not a repeat
	assert_str(SoundRules.refusal(&"arrow_hit", "moment", 1001, h, false)).is_equal("")

func test_flavour_and_steps_keep_their_own_spacing() -> void:
	var h := SoundRules.empty_history()
	SoundRules.played(&"bow_draw", "flavour", 1000, h)
	assert_str(SoundRules.refusal(&"arrow_wall", "flavour", 1000 + SoundRules.FLAVOUR_GAP_MS - 1, h, false)).is_equal("flavour_gap")
	assert_str(SoundRules.refusal(&"arrow_wall", "flavour", 1000 + SoundRules.FLAVOUR_GAP_MS, h, false)).is_equal("")
	# a footstep does not wait for the flavour's gap, and a flavour does not wait for a footstep's
	assert_str(SoundRules.refusal(&"step_grass", "step", 1001, h, false)).is_equal("")
	SoundRules.played(&"step_grass", "step", 1001, h)
	assert_str(SoundRules.refusal(&"step_stone", "step", 1001 + SoundRules.STEP_GAP_MS - 1, h, false)).is_equal("step_gap")
	assert_str(SoundRules.refusal(&"step_stone", "step", 1001 + SoundRules.STEP_GAP_MS, h, false)).is_equal("")
	assert_str(SoundRules.refusal(&"arrow_wall", "flavour", 1000 + SoundRules.FLAVOUR_GAP_MS, h, false)).is_equal("")
	# confirms and moments are never spaced out while Gentle sound is off
	for tier in ["confirm", "moment"]:
		assert_str(SoundRules.refusal(&"other", tier, 1002, h, false)).is_equal("")

func test_gentle_sound_keeps_confirms_and_moments_400_ms_apart() -> void:
	var h := SoundRules.empty_history()
	for tier in ["flavour", "step"]:
		assert_str(SoundRules.refusal(&"x", tier, 5000, h, true)).is_equal("gentle")
	assert_str(SoundRules.refusal(&"ui_confirm", "confirm", 5000, h, true)).is_equal("")
	SoundRules.played(&"ui_confirm", "confirm", 5000, h)
	for tier in ["confirm", "moment"]:
		assert_str(SoundRules.refusal(&"other", tier, 5000 + SoundRules.GENTLE_GAP_MS - 1, h, true)).is_equal("gentle_gap")
		assert_str(SoundRules.refusal(&"other", tier, 5000 + SoundRules.GENTLE_GAP_MS, h, true)).is_equal("")
	# the same history with Gentle sound off: nothing waits
	assert_str(SoundRules.refusal(&"other", "moment", 5001, h, false)).is_equal("")

func test_play_follows_the_rules_and_the_settings() -> void:
	_listen()
	assert_bool(Sound.play(&"glance")).is_true()
	assert_array(Sound.sounding()).contains([&"glance"])
	assert_bool(Sound.play(&"glance")).is_false()                 # the repeat guard
	_now += SoundRules.REPEAT_MS
	assert_bool(Sound.play(&"glance")).is_true()
	assert_bool(Sound.play(&"step_grass")).is_true()
	assert_bool(Sound.play(&"step_stone")).is_false()              # a footstep's own gap
	assert_bool(Sound.play(&"no_such_cue")).is_false()
	# Gentle sound: no footsteps, no flavour, and the next moment waits 400 ms
	SaveGame.data.settings.gentle_sound = true
	_now += 1000
	assert_bool(Sound.play(&"step_grass")).is_false()
	assert_bool(Sound.play(&"bow_draw")).is_false()
	assert_bool(Sound.play(&"bow_release")).is_true()
	assert_bool(Sound.play(&"arrow_hit")).is_false()
	assert_bool(Sound.play(&"ui_confirm")).is_false()
	_now += SoundRules.GENTLE_GAP_MS
	assert_bool(Sound.play(&"ui_confirm")).is_true()
	SaveGame.data.settings.gentle_sound = false
	# effects off: nothing starts, and what is sounding stops when the menu says so
	_now += 1000
	assert_bool(Sound.play(&"raid_bell")).is_true()
	SaveGame.data.settings.sound_effects = false
	Sound.settings_changed()
	assert_array(Sound.sounding()).is_empty()
	_now += 1000
	assert_bool(Sound.play(&"raid_bell")).is_false()
	assert_bool(Sound.play(&"ui_confirm")).is_false()
	assert_array(_heard).is_equal([&"glance", &"glance", &"step_grass", &"bow_release", &"ui_confirm", &"raid_bell"])

func test_variants_take_turns() -> void:
	_listen()
	var files: Array = Sound.effects[&"step_grass"].files
	assert_int(files.size()).is_equal(4)
	var seen := []
	for i in 5:
		assert_bool(Sound.play(&"step_grass")).is_true()
		for p in Sound._players:
			if p.playing and Sound._player_cue[Sound._players.find(p)] == &"step_grass":
				seen.append(p.stream.resource_path.get_file())
		Sound.stop_effects()
		_now += SoundRules.STEP_GAP_MS
	# whichever comes first, the next three are the others in order, and the fifth is the first again
	var first := files.find("sfx/" + String(seen[0]))
	assert_int(first).is_greater_equal(0)
	for i in seen.size():
		assert_str(seen[i]).is_equal(String(files[(first + i) % 4]).get_file())

func test_a_ninth_cue_takes_the_oldest_players_place() -> void:
	_listen()
	var cues: Array[StringName] = [&"raid_horn", &"raid_bell", &"night_won", &"card_start", &"card_end", &"boss_freed", &"seal_open", &"built"]
	for cue in cues:
		_now += 1
		assert_bool(Sound.play(cue)).is_true()
	assert_int(Sound.sounding().size()).is_equal(Sound.POOL)
	_now += 1
	assert_bool(Sound.play(&"quest_done")).is_true()
	var now_sounding := Sound.sounding()
	assert_int(now_sounding.size()).is_equal(Sound.POOL)
	assert_bool(now_sounding.has(&"raid_horn")).is_false()
	assert_bool(now_sounding.has(&"quest_done")).is_true()

func test_a_larger_cue_for_the_same_moment_covers_a_smaller_one() -> void:
	_listen()
	assert_bool(Sound.play(&"quest_done")).is_true()
	assert_bool(Sound.play(&"quest_start", &"quest_done")).is_false()
	_now += SoundRules.REPEAT_MS
	assert_bool(Sound.play(&"quest_start", &"quest_done")).is_true()

# --- the pause --------------------------------------------------------------------------------
func test_the_pause_ends_the_worlds_effects_and_the_menu_answers() -> void:
	_listen()
	assert_bool(Sound.play(&"boss_roar")).is_true()
	assert_bool(Sound.play(&"talk")).is_true()
	get_tree().paused = true
	Sound._watch_pause()
	# the world's effect ended with the pause; the line's tok and the menu's own cue may finish
	assert_bool(Sound.sounding().has(&"boss_roar")).is_false()
	assert_bool(Sound.sounding().has(&"pause_open")).is_true()
	_now += 1000
	assert_bool(Sound.play(&"arrow_hit")).is_false()             # nothing of the world starts while it is held
	assert_bool(Sound.play(&"ui_confirm")).is_true()
	get_tree().paused = false
	Sound._watch_pause()
	assert_array(_heard).is_equal([&"boss_roar", &"talk", &"pause_open", &"ui_confirm", &"pause_close"])
	_now += 1000
	assert_bool(Sound.play(&"arrow_hit")).is_true()

# --- ambience ---------------------------------------------------------------------------------
func _loop(id: StringName) -> Dictionary:
	for state: Dictionary in Sound.loop_state():
		if state.id == id:
			return state
	return {}

func test_one_loop_at_a_time_crossfaded_and_held_under_the_pause() -> void:
	_listen()
	Sound.ambience(&"woodland")
	Sound.steer(0.0)
	assert_bool(_loop(&"woodland").playing).is_true()
	assert_float(_loop(&"woodland").gain).is_equal(0.0)           # it fades in, it does not start loud
	Sound.steer(Sound.CROSSFADE)
	assert_float(_loop(&"woodland").gain).is_equal(1.0)
	# a zone change: the new loop rises as the old one falls, then the old one stops
	Sound.ambience(&"undercroft")
	Sound.steer(Sound.CROSSFADE / 2.0)
	assert_float(_loop(&"woodland").gain).is_equal_approx(0.5, 0.001)
	assert_float(_loop(&"undercroft").gain).is_equal_approx(0.5, 0.001)
	Sound.steer(Sound.CROSSFADE / 2.0)
	assert_dict(_loop(&"woodland")).is_empty()
	assert_float(_loop(&"undercroft").gain).is_equal(1.0)
	var playing := 0
	for state: Dictionary in Sound.loop_state():
		playing += 1 if state.playing else 0
	assert_int(playing).is_equal(1)
	# the pause menu: silent within HOLD_FADE and held, not restarted
	get_tree().paused = true
	Sound.steer(Sound.HOLD_FADE)
	assert_float(_loop(&"undercroft").gain).is_equal(0.0)
	assert_bool(_loop(&"undercroft").held).is_true()
	Sound.steer(5.0)
	assert_bool(_loop(&"undercroft").held).is_true()
	get_tree().paused = false
	Sound.steer(0.1)
	assert_bool(_loop(&"undercroft").held).is_false()
	assert_float(_loop(&"undercroft").gain).is_greater(0.0)
	# no loop asked for (a lab zone): it fades out and stops
	Sound.ambience(&"")
	Sound.steer(Sound.CROSSFADE)
	assert_dict(_loop(&"undercroft")).is_empty()
	for state: Dictionary in Sound.loop_state():
		assert_bool(state.playing).is_false()

func test_the_ambience_switch_is_its_own() -> void:
	_listen()
	Sound.ambience(&"crossroads")
	Sound.steer(Sound.CROSSFADE)
	assert_float(_loop(&"crossroads").gain).is_equal(1.0)
	# effects off and Gentle sound on do not touch the loop
	SaveGame.data.settings.sound_effects = false
	SaveGame.data.settings.gentle_sound = true
	Sound.settings_changed()
	Sound.steer(1.0)
	assert_float(_loop(&"crossroads").gain).is_equal(1.0)
	# ambience off: the loop goes, and effects (switched back on) still play
	SaveGame.data.settings.sound_effects = true
	SaveGame.data.settings.gentle_sound = false
	SaveGame.data.settings.ambience = false
	Sound.steer(Sound.CROSSFADE)
	assert_dict(_loop(&"crossroads")).is_empty()
	assert_bool(Sound.play(&"glance")).is_true()
	SaveGame.data.settings.ambience = true
	Sound.steer(0.0)
	assert_bool(_loop(&"crossroads").playing).is_true()

func test_the_place_decides_the_loop() -> void:
	Zones.table = {"a": "res://test/fixtures/zone_a.tscn", "b": "res://test/fixtures/zone_b.tscn"}
	var root: Node2D = auto_free(Node2D.new())
	add_child(root)
	var player: Player = auto_free(load("res://actors/player.tscn").instantiate())
	player.input_enabled = false
	Zones.current = null
	Zones.attach(root, player)
	_listen()
	assert_str(Sound.place_loop()).is_equal("")
	Zones.go_to("a", "west")
	assert_str(Sound.place_loop()).is_equal("")                  # a zone with no loop of its own
	Zones.current.zone_id = "woodland"
	assert_str(Sound.place_loop()).is_equal("woodland")
	Zones.current.zone_id = "crossroads"
	assert_str(Sound.place_loop()).is_equal("crossroads")
	# the first night, rung in its zone: the night's loop, and the town's again when it ends
	SaveGame.data.raid = {"id": "first_night", "state": "running", "postponed": 0, "wave": 0, "layout": {}, "repairs": false}
	Raids.changed.emit("running")
	assert_str(Sound.place_loop()).is_equal("night")
	assert_str(Sound.wanted_loop()).is_equal("night")
	SaveGame.data.raid.state = "lost"
	Raids.changed.emit("lost")
	assert_str(Sound.wanted_loop()).is_equal("crossroads")

# --- settings ---------------------------------------------------------------------------------
func test_a_fresh_game_has_effects_and_ambience_on_and_gentle_off() -> void:
	assert_bool(SaveGame.setting("sound_effects")).is_true()
	assert_bool(SaveGame.setting("ambience")).is_true()
	assert_bool(SaveGame.setting("gentle_sound")).is_false()
	assert_int(SaveGame.VERSION).is_equal(2)

func test_a_save_from_before_sound_loads_with_the_defaults() -> void:
	# a save written by main on 13 Nov (version 1, before this), and the first night route's own
	for source: String in [FIXTURES + "v1-main-before-sound.json", "res://tools/routes/first_night.save.json", FIXTURES + "v1-village.json"]:
		var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(source))
		assert_int(int(doc.version)).is_equal(1)
		assert_bool(doc.settings.has("sound_effects")).is_false()
		var file := FileAccess.open(PATH, FileAccess.WRITE)
		file.store_string(JSON.stringify(doc))
		file.close()
		SaveGame.data.settings.gentle_sound = true                 # the running game's choice does not leak in
		assert_int(SaveGame.load_save(PATH)).is_equal(OK)
		assert_int(SaveGame.data.version).is_equal(2)
		assert_bool(SaveGame.data.settings.sound_effects).is_true()
		assert_bool(SaveGame.data.settings.ambience).is_true()
		assert_bool(SaveGame.data.settings.gentle_sound).is_false()
		# what the save did hold is kept
		assert_bool(SaveGame.data.settings.reduced_motion == doc.settings.reduced_motion).is_true()
		assert_str(SaveGame.data.settings.pixel_scale).is_equal(doc.settings.pixel_scale)
		assert_int(SaveGame.data.glint).is_equal(int(doc.glint))
		assert_str(SaveGame.data.zone).is_equal(doc.zone)

func test_sound_settings_save_and_load() -> void:
	# the version 2 fixture: every switch away from its default
	var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURES + "v2-sound.json"))
	var file := FileAccess.open(PATH, FileAccess.WRITE)
	file.store_string(JSON.stringify(doc))
	file.close()
	assert_int(SaveGame.load_save(PATH)).is_equal(OK)
	assert_bool(SaveGame.data.settings.sound_effects).is_false()
	assert_bool(SaveGame.data.settings.ambience).is_false()
	assert_bool(SaveGame.data.settings.gentle_sound).is_true()
	assert_dict(SaveGame.data).is_equal(SaveGame._migrate(doc))
	# and a round trip of each switch on its own
	for key: String in SaveGame.SOUND_SETTINGS:
		SaveGame.reset()
		SaveGame.data.settings[key] = not SaveGame.SOUND_SETTINGS[key]
		var before: Dictionary = SaveGame.data.duplicate(true)
		assert_int(SaveGame.save(PATH)).is_equal(OK)
		SaveGame.reset()
		assert_int(SaveGame.load_save(PATH)).is_equal(OK)
		assert_dict(SaveGame.data).is_equal(before)
	# a switch that is not a switch is a damaged save, refused like the other settings
	for key: String in SaveGame.SOUND_SETTINGS:
		assert_dict(SaveGame._migrate({"settings": {key: "yes"}})).is_empty()

func test_gentle_sound_and_reduced_motion_do_not_read_each_other() -> void:
	_listen()
	SaveGame.data.settings.reduced_motion = true
	assert_bool(SaveGame.setting("gentle_sound")).is_false()
	assert_bool(Sound.play(&"step_grass")).is_true()               # reduced motion alone silences nothing
	assert_bool(Sound.play(&"bow_draw")).is_true()
	SaveGame.data.settings.reduced_motion = false
	SaveGame.data.settings.gentle_sound = true
	assert_bool(SaveGame.setting("reduced_motion")).is_false()      # and Gentle sound stills nothing
	_now += 1000
	assert_bool(Sound.play(&"step_grass")).is_false()
	# the HUD's Glint cue sounds under reduced motion (its tint does not show then)
	SaveGame.data.settings.gentle_sound = false
	SaveGame.data.settings.reduced_motion = true
	var hud: Control = auto_free(load("res://ui/hud.gd").new())
	add_child(hud)
	_heard.clear()
	_now += 1000
	hud._glint_changed(3, 5)
	hud._glint_changed(5, 5)
	hud._glint_changed(5, 2)
	assert_array(_heard).is_equal([&"glint"])

# --- the Sound panel --------------------------------------------------------------------------
func _menus() -> Array:
	var host: Control = auto_free(Control.new())
	host.size = Screen.ART
	add_child(host)
	var pause: Control = load("res://ui/pause_menu.gd").new()
	host.add_child(pause)
	var sound := SoundMenu.new()
	sound.beside = pause
	host.add_child(sound)
	for menu: Control in [pause, sound]:
		menu.set_process(false)
		menu.show()
	return [pause, sound]

func test_the_sound_panel_sets_the_three_switches_and_saves() -> void:
	var path: String = SaveGame.path
	SaveGame.path = PATH
	var sound: SoundMenu = _menus()[1]
	var buttons := sound.find_children("*", "Button", true, false)
	assert_int(buttons.size()).is_equal(3)
	assert_str((buttons[0] as Button).text).is_equal("Sound effects: on")
	assert_str((buttons[1] as Button).text).is_equal("Ambience: on")
	assert_str((buttons[2] as Button).text).is_equal("Gentle sound: off")
	for b: Button in buttons:
		b.pressed.emit()
	assert_str((buttons[0] as Button).text).is_equal("Sound effects: off")
	assert_str((buttons[1] as Button).text).is_equal("Ambience: off")
	assert_str((buttons[2] as Button).text).is_equal("Gentle sound: on")
	var chosen: Dictionary = SaveGame.data.settings.duplicate(true)
	assert_bool(chosen.sound_effects).is_false()
	assert_bool(chosen.ambience).is_false()
	assert_bool(chosen.gentle_sound).is_true()
	# reduced motion and the pixel scale are left as they were
	assert_bool(chosen.reduced_motion).is_false()
	assert_str(chosen.pixel_scale).is_equal("fill")
	# each press saved at once
	SaveGame.reset()
	assert_int(SaveGame.load_save(PATH)).is_equal(OK)
	SaveGame.path = path
	assert_dict(SaveGame.data.settings).is_equal(chosen)

func test_the_sound_panel_follows_the_pause() -> void:
	var host: Control = auto_free(Control.new())
	add_child(host)
	var sound := SoundMenu.new()
	host.add_child(sound)
	await await_idle_frame()
	assert_bool(sound.visible).is_false()
	get_tree().paused = true
	await await_idle_frame()
	assert_bool(sound.visible).is_true()
	get_tree().paused = false
	await await_idle_frame()
	assert_bool(sound.visible).is_false()

func test_sound_rows_meet_44_points_beside_the_pause_menu_in_both_modes() -> void:
	var before := SaveGame.data.duplicate(true)
	var menus := _menus()
	var pause: Control = menus[0]
	var sound: SoundMenu = menus[1]
	for spec in [[1920, 1080, 1], [960, 540, 1], [874, 402, 1], [2622, 1206, 3], [667, 375, 1]]:
		var window := Vector2(spec[0], spec[1])
		for mode in ["fill", "whole"]:
			var k: float = Screen.choose_scale(window, mode)
			var offset := ((window - Screen.ART * k) / 2.0).floor()
			for menu: Control in [pause, sound]:
				assert_bool(menu.fit_screen(window, k, offset, spec[2], Rect2(Vector2.ZERO, window))).is_true()
			await get_tree().process_frame
			await get_tree().process_frame
			sound._stand_beside()
			var rows := Audit.measure_controls(sound)
			assert_int(rows.size()).is_equal(3)
			var result := Audit.audit(window, spec[2], mode, rows)
			assert_bool(result.ok).is_true()
			assert_bool(result.passes).override_failure_message(JSON.stringify(result)).is_true()
			# beside the pause menu, top to top, and no row of one panel over a row of the other
			assert_float(sound.position.y).is_equal(pause.position.y)
			assert_float(sound.position.x).is_equal(pause.position.x + pause.size.x + SoundMenu.GAP)
			var all := Audit.measure_controls(pause) + rows
			for i in all.size():
				for j in range(i + 1, all.size()):
					assert_bool(all[i].rect.intersects(all[j].rect)).is_false()
	# with a phone's safe insets: still inside
	var window := Vector2(2622, 1206)
	var insets := Vector4(30, 12, 16, 18)
	var safe := Rect2(Vector2(insets.x, insets.y) * 3.0, window - Vector2(insets.x + insets.z, insets.y + insets.w) * 3.0)
	for mode in ["fill", "whole"]:
		var k: float = Screen.choose_scale(window, mode)
		var offset := ((window - Screen.ART * k) / 2.0).floor()
		for menu: Control in [pause, sound]:
			assert_bool(menu.fit_screen(window, k, offset, 3.0, safe)).is_true()
		await get_tree().process_frame
		await get_tree().process_frame
		sound._stand_beside()
		var result := Audit.audit(window, 3.0, mode, Audit.measure_controls(sound), insets)
		assert_bool(result.passes).override_failure_message(JSON.stringify(result)).is_true()
	assert_dict(SaveGame.data).is_equal(before)

func test_focus_wraps_inside_the_panel_and_crosses_between_the_two() -> void:
	var menus := _menus()
	var pause: Control = menus[0]
	var sound: SoundMenu = menus[1]
	assert_bool(pause.fit_screen(Vector2(1920, 1080), 2.0, Vector2.ZERO, 1.0, Rect2(0, 0, 1920, 1080))).is_true()
	assert_bool(sound.fit_screen(Vector2(1920, 1080), 2.0, Vector2.ZERO, 1.0, Rect2(0, 0, 1920, 1080))).is_true()
	await get_tree().process_frame
	await get_tree().process_frame
	sound._stand_beside()
	var rows: Array = sound.get("_buttons")
	for i in rows.size():
		var b: Button = rows[i]
		assert_object(b.get_node(b.focus_neighbor_top)).is_same(rows[(i + 2) % 3])
		assert_object(b.get_node(b.focus_neighbor_bottom)).is_same(rows[(i + 1) % 3])
		assert_bool(b.pressed.is_connected(sound.toggle.bind(b.name))).is_true()
	# right from the pause menu lands in the Sound panel, and left from it comes back
	var pause_rows: Array = pause.get("_buttons")
	for b: Button in pause_rows:
		assert_bool(rows.has(b.find_valid_focus_neighbor(SIDE_RIGHT))).is_true()
	for b: Button in rows:
		assert_bool(pause_rows.has(b.find_valid_focus_neighbor(SIDE_LEFT))).is_true()

# --- hooks ------------------------------------------------------------------------------------
func test_a_glancing_arrow_clinks() -> void:
	_listen()
	Glance.clink(Vector2(10, 20))
	assert_array(_heard).is_equal([&"glance"])

func test_the_undercrofts_plate_and_lever() -> void:
	_listen()
	var plate: PressurePlate = auto_free(PressurePlate.new())
	plate.press()
	plate.press()                                                # already down: nothing more
	var lever: SealLever = auto_free(SealLever.new())
	assert_bool(lever.pull()).is_true()
	assert_bool(lever.pull()).is_false()
	assert_array(_heard).is_equal([&"plate", &"seal_open"])

func test_a_restore_sounds_the_build_first_then_the_coins() -> void:
	_listen()
	SaveGame.data.glint = 100
	assert_bool(Village.restore("forge")).is_true()
	assert_bool(Village.restore("forge")).is_false()
	# a flag told through Village.changed (the plate, the lever) is not a building
	Village.changed.emit("undercroft_plate")
	assert_array(_heard.slice(0, 2)).is_equal([&"built", &"pay"])
	assert_bool(_heard.slice(2).has(&"built")).is_false()
	# with Gentle sound the build is the one that stays
	SaveGame.reset()
	SaveGame.data.glint = 100
	SaveGame.data.settings.gentle_sound = true
	_heard.clear()
	_now += 5000
	Village.restore("forge")
	assert_array(_heard.slice(0, 1)).is_equal([&"built"])
	assert_bool(_heard.has(&"pay")).is_false()

func test_quests_lines_and_the_raid() -> void:
	_listen()
	Quests.started.emit("any")
	_now += 1000
	Quests.completed.emit("any")
	Quests.started.emit("next")                                  # the same line finished one and began another
	_now += 1000
	# a line opening and each press that turns it: the box's own tok (and the box is the only listener
	# Dialogue.opened has: Dialogue.talk takes a listener for a box and waits for it)
	assert_array(Dialogue.opened.get_connections()).is_empty()
	var box: PanelContainer = auto_free(load("res://ui/dialogue_box.gd").new())
	add_child(box)
	Dialogue.opened.emit("Hale", PackedStringArray(["A line.", "Another."]))
	_now += 1000
	box.advance()                                                # finishes the type-on
	_now += 1000
	box.advance()                                                # the next line
	_now += 1000
	Raids.prepare_requested.emit()
	_now += 1000
	Raids.finished.emit(true)
	_now += 1000
	Raids.finished.emit(false)
	assert_array(_heard).is_equal([&"quest_start", &"quest_done", &"talk", &"talk", &"talk", &"raid_horn", &"night_won", &"night_lost"])

func test_the_bell_the_hurdles_and_the_lantern() -> void:
	_listen()
	SaveGame.data.raid = {"id": "first_night", "state": "announced", "postponed": 0, "wave": 0, "layout": {}, "repairs": false}
	assert_bool(Raids.ring()).is_true()
	assert_bool(Raids.ring()).is_false()
	_now += 1000
	var hurdle: RaidBarricade = auto_free(RaidBarricade.new())
	hurdle.kind = {"hp": 2}
	add_child(hurdle)
	assert_bool(hurdle.batter(1)).is_false()
	_now += 1000
	assert_bool(hurdle.batter(1)).is_true()
	_now += 1000
	hurdle.batter(1)                                             # already down
	var lantern: RaidLantern = auto_free(RaidLantern.new())
	lantern.max_hp = 2
	add_child(lantern)
	assert_bool(lantern.batter(1)).is_false()
	_now += 1000
	assert_bool(lantern.batter(1)).is_true()                     # the blow that fells it: the night's own cue
	assert_array(_heard).is_equal([&"raid_bell", &"hurdle_hit", &"hurdle_break", &"lantern_hit"])

func test_a_walk_between_zones_sounds_its_door() -> void:
	Zones.table = {"a": "res://test/fixtures/zone_a.tscn", "b": "res://test/fixtures/zone_b.tscn"}
	var root: Node2D = auto_free(Node2D.new())
	add_child(root)
	var player: Player = auto_free(load("res://actors/player.tscn").instantiate())
	player.input_enabled = false
	Zones.current = null
	Zones.attach(root, player)
	_listen()
	Zones.go_to("a", "west")                                     # the game's start: not a walk
	assert_array(_heard).is_empty()
	_now += 1000
	Zones.go_to("a", "west")                                     # getting up where the player fell: not a walk
	assert_array(_heard).is_empty()
	_now += 1000
	Zones.go_to("b", "from_a")
	assert_array(_heard).is_equal([&"door"])
	_now += 1000
	Zones.current.zone_id = "undercroft"                          # up the stair, out of the hatch
	Zones.go_to("a", "west")
	assert_array(_heard).is_equal([&"door", &"door_stone"])

func test_the_players_cues_come_from_what_the_player_shows() -> void:
	_listen()
	var p: Player = auto_free(load("res://actors/player.tscn").instantiate())
	p.add_child(PlayerSounds.new())
	add_child(p)
	p.input_enabled = false
	p.use_mouse_aim = false
	p.aim = Vector2.RIGHT
	assert_bool(p.start_shot()).is_true()
	for i in 45:                                                 # the draw, the release and the clip's end
		_now += 17
		await get_tree().physics_frame
	assert_array(_heard).is_equal([&"bow_draw", &"bow_release"])
	_heard.clear()
	assert_bool(p.start_roll(Vector2.LEFT)).is_true()
	for i in 30:
		_now += 17
		await get_tree().physics_frame
	assert_array(_heard).is_equal([&"roll"])
	_heard.clear()
	assert_bool(p.take_damage(1)).is_true()
	for i in 45:                                                 # past the mercy frames
		_now += 17
		await get_tree().physics_frame
	p.hit_landed.emit(null, false)
	p.take_damage(p.hp)
	p.downed.emit()
	assert_array(_heard).is_equal([&"hurt", &"arrow_hit", &"downed", &"get_up"])
	# a defeat that loses the night leaves the moment to the night's cue
	_heard.clear()
	_now += 1000
	Raids.finished.emit(false)
	p.downed.emit()
	assert_array(_heard).is_equal([&"night_lost"])

func test_footsteps_fall_on_the_planted_drawings_while_walking() -> void:
	assert_bool(PlayerSounds.is_footfall(0, 12)).is_true()
	assert_bool(PlayerSounds.is_footfall(6, 12)).is_true()
	for drawing in [1, 2, 3, 4, 5, 7, 8, 9, 10, 11]:
		assert_bool(PlayerSounds.is_footfall(drawing, 12)).is_false()
	assert_bool(PlayerSounds.footfall_between(-1, 0, 12)).is_false()   # a walk just begun
	assert_bool(PlayerSounds.footfall_between(5, 6, 12)).is_true()
	assert_bool(PlayerSounds.footfall_between(4, 7, 12)).is_true()     # a slow frame that skipped the drawing
	assert_bool(PlayerSounds.footfall_between(11, 0, 12)).is_true()
	assert_bool(PlayerSounds.footfall_between(6, 6, 12)).is_false()
	assert_bool(PlayerSounds.footfall_between(1, 5, 12)).is_false()
	# the manifest agrees: the right foot is lowest on drawing 0 and the left on drawing 6
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/characters/bramble/manifest.json"))
	var frames: Array = manifest.clips.walk.facings.S.frames
	assert_int(frames.size()).is_equal(12)
	for foot: Array in [["foot_R", 0], ["foot_L", 6]]:
		var lowest := 0
		for i in frames.size():
			if float(frames[i].anchors[foot[0]][1]) > float(frames[lowest].anchors[foot[0]][1]):
				lowest = i
		assert_int(lowest).is_equal(foot[1])
	# walking with the real keys: steps come, about two a walk cycle, and none standing still
	_listen()
	var p: Player = auto_free(load("res://actors/player.tscn").instantiate())
	p.add_child(PlayerSounds.new())
	add_child(p)
	p.use_mouse_aim = false
	for i in 20:
		_now += 17
		await get_tree().physics_frame
	assert_array(_heard).is_empty()
	Input.action_press("move_right")
	for i in 90:                                                 # 1.5 s: three walk cycles of 0.486 s
		_now += 17
		await get_tree().physics_frame
	Input.action_release("move_right")
	var steps := _heard.filter(func(cue: StringName) -> bool: return cue == &"step_grass")
	assert_int(steps.size()).is_between(5, 7)
	assert_int(_heard.size()).is_equal(steps.size())
	_heard.clear()
	for i in 20:
		_now += 17
		await get_tree().physics_frame
	assert_array(_heard).is_empty()

func test_surfaces_follow_the_plans() -> void:
	assert_str(Sound.surface_at("woodland", Vector2(60, 60) * 3.0)).is_equal("grass")
	assert_str(Sound.surface_at("undercroft", Vector2(60, 60) * 3.0)).is_equal("stone")
	assert_str(Sound.surface_at("nowhere", Vector2.ZERO)).is_equal("grass")
	# the footbridge (the rect is the woodland scene's own bridge, art/scenes/woodland.json)
	var scene: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/sound/surfaces.json"))
	var bridge: Array = scene.woodland.areas[0].rect
	assert_str(Sound.surface_at("woodland", Vector2(bridge[0] + bridge[2] / 2.0, bridge[1] + bridge[3] / 2.0) * 3.0)).is_equal("wood")
	assert_str(Sound.surface_at("woodland", Vector2(bridge[0] - 4.0, bridge[1] + 4.0) * 3.0)).is_equal("grass")
	# the Crossroads stone is the plan's own paving
	var plan: Dictionary = Village.plans.crossroads
	var paving: Array = plan.art.paving
	var stone := []
	for area: Dictionary in scene.crossroads.areas:
		assert_str(area.surface).is_equal("stone")
		stone.append(area.rect)
	assert_int(stone.size()).is_equal(paving.size())
	for i in paving.size():
		for k in 4:
			assert_float(float(stone[i][k])).is_equal(float(paving[i][k]))
	assert_str(Sound.surface_at("crossroads", Vector2(320, 288) * 3.0)).is_equal("stone")    # the square
	assert_str(Sound.surface_at("crossroads", Vector2(60, 300) * 3.0)).is_equal("grass")
	for cue: StringName in Sound.STEPS.values():
		assert_str(Sound.tier_of(cue)).is_equal("step")
