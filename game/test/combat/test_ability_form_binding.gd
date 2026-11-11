extends "res://test/combat/test_ability_pose_binding.gd"
## Injected fixture clocks exercise the optional boundary, not production retiming.

var form_key := "powered-walk"
var form_facing := "W"
var form_bad := false
var form_cancel := false

func _durations(plan: Array) -> Array:
	var result: Array = []
	for segment in plan:
		var row: Array = []
		for i in segment.indices.size(): row.append(0.05)
		result.append(row)
	return result

func _form_provider(_snapshot: Dictionary, _action: String) -> Dictionary:
	if form_cancel: driver.clear_presentation()
	var manifest: Dictionary = actor.sprite.manifest.duplicate(true)
	var plan := AbilityFormPlan.build("bramble", "walk", true, false, manifest, form_facing)
	var durations := _durations(plan)
	if form_bad: durations[-1][0] = 0.0
	return {"key": form_key, "manifest": manifest, "plan": plan, "segment_durations": durations}

func _form_setup() -> void:
	_pose_setup()
	form_key = "powered-walk"
	form_facing = "W"
	form_bad = false
	form_cancel = false
	assert_bool(actor.bind_ability_presentation(_provide, _contact, _form_provider)).is_true()

func test_finite_form_timeline_preserves_exact_indices_and_clock_boundaries() -> void:
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/characters/brine/manifest.json"))
	var plan := AbilityFormPlan.build("brine", "defeat", true, true, manifest, "W")
	var track := AbilityFormTrack.new()
	assert_bool(track.configure("exit", manifest, plan, _durations(plan), 1)).is_true()
	assert_str(track.sample().clip).is_equal("powered_exit_empty")
	assert_int(track.advance(0.1).index).is_equal(2)
	assert_int(track.advance(0.051).index).is_equal(3)
	var sample := track.advance(0.05)
	assert_str(sample.clip).is_equal("defeat_empty")
	assert_int(sample.index).is_equal(0)
	assert_dict(sample.frame).is_equal(plan[1].frames[0])
	track.advance(100000.0)
	assert_bool(track.is_finished()).is_true()
	assert_int(track.sample().index).is_equal(plan[1].indices[-1])
	track.cancel()
	assert_dict(track.advance(1.0)).is_empty()

func test_bad_replacement_and_implicit_retime_preserve_the_valid_plan() -> void:
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/characters/bramble/manifest.json"))
	var plan := AbilityFormPlan.build("bramble", "walk", true, false, manifest, "W")
	var durations := _durations(plan)
	var track := AbilityFormTrack.new()
	assert_bool(track.configure("walk", manifest, plan, durations, 1)).is_true()
	var before := track.advance(0.11)
	var bad := durations.duplicate(true)
	bad[-1][0] = NAN
	assert_bool(track.configure("new", manifest, plan, bad, 2)).is_false()
	bad = durations.duplicate(true)
	bad[0][0] = 0.1
	assert_bool(track.configure("walk", manifest, plan, bad, 2)).is_false()
	var forged := plan.duplicate(true)
	forged[1].frames[0].anchors.clear()
	assert_bool(track.configure("new", manifest, forged, durations, 2)).is_false()
	assert_dict(track.sample()).is_equal(before)
	assert_bool(track.configure("walk", manifest, plan, durations, 2)).is_true()
	assert_int(track.sample().index).is_equal(before.index)

func test_facing_phase_pause_and_snapshot_isolation() -> void:
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/characters/bramble/manifest.json"))
	var west := AbilityFormPlan.build("bramble", "walk", true, false, manifest, "W")
	var north := AbilityFormPlan.build("bramble", "walk", true, false, manifest, "N")
	var track := AbilityFormTrack.new()
	assert_bool(track.configure("walk", manifest, west, _durations(west), 1)).is_true()
	var before := track.advance(0.11)
	assert_bool(track.configure("walk", manifest, north, _durations(north), 2)).is_true()
	assert_int(track.sample().index).is_equal(before.index)
	assert_str(track.sample().facing).is_equal("N")
	var held := track.sample()
	assert_dict(track.advance(100.0, false)).is_equal(held)
	assert_dict(track.advance(INF)).is_equal(held)
	held.frame.anchors.clear()
	assert_dict(track.sample().frame.anchors).is_not_empty()

func test_player_consumes_powered_boundaries_without_contacts_or_state_changes() -> void:
	_form_setup()
	driver.tick({"active": true, "aim": Vector2.RIGHT},
		{"character": "bramble", "move_actor": _move}, AbilitySimulation.DT)
	assert_str(actor.sprite.animation).is_equal("powered_idle_W")
	assert_int(actor.sprite.frame).is_equal(0)
	_idle_tick()
	assert_str(actor.sprite.animation).is_equal("powered_walk_W")
	var frame := actor.sprite.frame
	_idle_tick(false)
	assert_int(actor.sprite.frame).is_equal(frame)
	form_facing = "N"
	_idle_tick()
	assert_str(actor.sprite.animation).is_equal("powered_walk_N")
	for i in 20: _idle_tick()
	assert_str(actor.sprite.animation).is_equal("powered_idle_N")
	assert_int(actor.sprite.frame).is_equal(0)
	assert_array(contacts).is_empty()
	assert_float(driver.snapshot().player.specialRemaining).is_equal(0.0)

func test_form_binding_does_not_replace_contact_timeline_and_cancels_on_reset() -> void:
	_form_setup()
	_idle_tick()
	for i in 3: _tick()
	assert_int(contacts.size()).is_equal(1)
	assert_str(actor.sprite.animation).is_equal("primary_W")
	actor.reset_motion()
	assert_int(driver.player_phase_observed.get_connections().size()).is_equal(0)
	_idle_tick()
	assert_str(actor.sprite.animation).is_equal("idle_W")

func test_invalid_form_schedule_and_reentrant_detach_never_deliver_stale_drawing() -> void:
	_form_setup()
	_idle_tick()
	var frame := actor.sprite.frame
	form_bad = true
	_idle_tick()
	assert_int(actor.sprite.frame).is_equal(frame)
	assert_str(driver._presentation.last_error).is_equal("invalid form plan or implicit retiming")
	form_bad = false
	_idle_tick()
	assert_str(driver._presentation.last_error).is_empty()
	actor.reset_motion()
	_form_setup()
	form_cancel = true
	_idle_tick()
	assert_str(actor.sprite.animation).is_equal("idle_S")
	assert_array(contacts).is_empty()
	assert_int(driver.player_phase_observed.get_connections().size()).is_equal(0)
