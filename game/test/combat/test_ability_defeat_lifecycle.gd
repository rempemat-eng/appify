extends "res://test/combat/test_ability_sprite_presenter.gd"

var terminal_bad := false
var terminal_detach := false
var down_count := 0

func _terminal() -> Dictionary:
	if terminal_detach: actor.detach_action_driver()
	var manifest: Dictionary = actor.sprite.manifest.duplicate(true)
	var plan := AbilityFormPlan.build(actor.character, "defeat", true, false, manifest, actor.facing)
	var durations: Array = []
	for segment in plan:
		var row: Array = []
		for index in segment.indices: row.append(0.05)
		durations.append(row)
	if terminal_bad: durations[0][0] = 0.0
	return {"id": actor.character, "powered": true, "harpoon_out": false,
		"manifest": manifest, "facing": actor.facing, "segment_durations": durations}

func _terminal_setup() -> void:
	_setup()
	terminal_bad = false
	terminal_detach = false
	down_count = 0
	actor.downed.connect(func() -> void: down_count += 1)
	assert_bool(actor.bind_ability_presentation(_provide, _contact)).is_true()
	assert_bool(actor.bind_ability_defeat(_terminal)).is_true()

func test_powered_exit_precedes_fall_and_downed_once_without_contacts() -> void:
	_terminal_setup()
	_tick()
	var canonical := driver.snapshot()
	assert_bool(actor.take_damage(actor.hp)).is_true()
	assert_str(actor.sprite.animation).is_equal("powered_exit_W")
	assert_int(actor.sprite.frame).is_equal(0)
	assert_int(driver.player_phase_observed.get_connections().size()).is_equal(0)
	actor._physics_process(0.151)
	assert_str(actor.sprite.animation).is_equal("powered_exit_W")
	assert_int(actor.sprite.frame).is_equal(3)
	actor._physics_process(0.05)
	assert_str(actor.sprite.animation).is_equal("defeat_W")
	assert_int(actor.sprite.frame).is_equal(0)
	assert_int(down_count).is_equal(0)
	actor._physics_process(5.0)
	assert_int(down_count).is_equal(1)
	actor._physics_process(5.0)
	assert_int(down_count).is_equal(1)
	assert_array(contacts).is_empty()
	assert_dict(driver.snapshot()).is_equal(canonical)

func test_cancelled_driver_without_terminal_contract_keeps_existing_defeat_handoff() -> void:
	_setup()
	down_count = 0
	actor.downed.connect(func() -> void: down_count += 1)
	assert_bool(actor.take_damage(actor.hp)).is_true()
	actor._physics_process(5.0)
	actor._physics_process(5.0)
	assert_int(down_count).is_equal(1)
	assert_str(actor.sprite.animation).is_equal("defeat_S")

func test_invalid_terminal_schedule_falls_back_and_reentrant_detach_cancels() -> void:
	_terminal_setup()
	terminal_bad = true
	assert_bool(actor.take_damage(actor.hp)).is_true()
	assert_str(actor.ability_presentation_error).is_equal("invalid explicit defeat schedule")
	assert_str(actor.sprite.animation).is_equal("defeat_S")
	actor._physics_process(5.0)
	assert_int(down_count).is_equal(1)
	_terminal_setup()
	terminal_detach = true
	actor.take_damage(actor.hp)
	assert_object(actor.action_driver).is_null()
	assert_object(actor._ability_defeat).is_null()
	assert_str(actor.sprite.animation).is_equal("defeat_S")

func test_heal_reset_and_scene_exit_cancel_terminal_playback() -> void:
	_terminal_setup()
	actor.take_damage(actor.hp)
	actor.heal_full()
	actor._physics_process(5.0)
	assert_str(actor.state).is_equal("idle")
	assert_int(down_count).is_equal(0)
	actor._iframe_t = 0.0
	assert_bool(actor.bind_ability_defeat(_terminal)).is_true()
	actor.take_damage(actor.hp)
	actor.reset_motion()
	assert_object(actor._ability_defeat).is_null()
	assert_str(actor.state).is_equal("idle")
	actor.heal_full()
	actor._iframe_t = 0.0
	assert_bool(actor.bind_ability_defeat(_terminal)).is_true()
	actor.take_damage(actor.hp)
	remove_child(actor)
	assert_object(actor._ability_defeat).is_null()
	assert_int(down_count).is_equal(0)

func test_terminal_track_keeps_all_crossings_and_brine_empty_variants() -> void:
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/characters/brine/manifest.json"))
	var plan := AbilityFormPlan.build("brine", "defeat", true, true, manifest, "N")
	var durations: Array = []
	for segment in plan:
		var row: Array = []
		for index in segment.indices: row.append(0.05)
		durations.append(row)
	var contract := {"id": "brine", "powered": true, "harpoon_out": true,
		"manifest": manifest, "facing": "N", "segment_durations": durations}
	var track := AbilityDefeatPlayback.new()
	assert_bool(track.configure(contract, 1)).is_true()
	var first := track.advance(0.0)
	assert_str(first[0].clip).is_equal("powered_exit_empty")
	assert_int(first[0].index).is_equal(0)
	var rest := track.advance(5.0)
	assert_int(rest.size()).is_equal(3 + plan[1].indices.size())
	assert_int(rest[0].index).is_equal(1)
	assert_str(rest[3].clip).is_equal("defeat_empty")
	assert_dict(rest[3].frame).is_equal(plan[1].frames[0])
	assert_bool(track.finished()).is_true()
	assert_array(track.advance(1.0)).is_empty()
	track.cancel()
	assert_bool(track.finished()).is_false()

func test_bad_replacement_preserves_terminal_clock_and_source_snapshots() -> void:
	_terminal_setup()
	var contract := _terminal()
	var track := AbilityDefeatPlayback.new()
	assert_bool(track.configure(contract, 1)).is_true()
	track.advance(0.151)
	var bad := contract.duplicate(true)
	bad.segment_durations[0][0] = NAN
	assert_bool(track.configure(bad, 2)).is_false()
	bad = contract.duplicate(true)
	bad.powered = "true"
	assert_bool(track.configure(bad, 2)).is_false()
	contract.manifest.clips.clear()
	assert_array(track.advance(INF)).is_empty()
	assert_array(track.advance(-1.0)).is_empty()
	var next := track.advance(0.05)
	assert_str(next[0].clip).is_equal("defeat")
	assert_int(next[0].index).is_equal(0)

func test_missing_terminal_sheet_falls_back_and_unbound_actor_rejects_provider() -> void:
	actor = _player()
	assert_bool(actor.bind_ability_defeat(_terminal)).is_false()
	_terminal_setup()
	actor.sprite.sprite_frames = actor.sprite.sprite_frames.duplicate(true)
	actor.sprite.sprite_frames.remove_animation("powered_exit_S")
	actor.take_damage(actor.hp)
	assert_str(actor.ability_presentation_error).is_equal("missing terminal drawing")
	assert_object(actor._ability_defeat).is_null()
	assert_str(actor.sprite.animation).is_equal("defeat_S")
	actor._physics_process(5.0)
	assert_int(down_count).is_equal(1)
