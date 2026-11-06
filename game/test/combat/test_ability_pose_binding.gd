extends "res://test/combat/test_ability_sprite_presenter.gd"

var passive_calls := 0
var passive_clip := "walk"
var passive_facing := "W"
var passive_key := "walking"
var passive_bad := false
var passive_cancel := false

func _passive(snapshot: Dictionary, _action: String) -> Dictionary:
	passive_calls += 1
	if passive_cancel: driver.clear_presentation()
	var manifest := actor.sprite.manifest.duplicate(true)
	if passive_bad: manifest["foreign"] = true
	var info: Dictionary = manifest.clips[passive_clip]
	return {"key": passive_key, "manifest": manifest, "clip": passive_clip,
		"facing": passive_facing, "durations": info.durations}

func _idle_tick(active := true, guard := false) -> void:
	driver.tick({"active": active, "guard": guard, "aim": Vector2.RIGHT},
		{"character": "bramble", "move_actor": _move}, 0.1)

func _pose_setup() -> void:
	_setup()
	passive_calls = 0
	passive_clip = "walk"
	passive_facing = "W"
	passive_key = "walking"
	passive_bad = false
	passive_cancel = false
	assert_bool(actor.bind_ability_presentation(_provide, _contact, _passive)).is_true()

func test_passive_draws_real_body_without_contacts_or_simulation_changes() -> void:
	_pose_setup()
	var expected := driver.snapshot()
	for i in 3:
		_idle_tick()
		expected = AbilitySimulation.step(expected, {"aimX": 186, "aimY": 98}, 0.1)
	assert_str(actor.sprite.animation).is_equal("walk_W")
	assert_bool(actor.sprite.is_playing()).is_false()
	assert_int(actor.sprite.frame).is_greater(0)
	assert_int(passive_calls).is_greater(0)
	assert_array(contacts).is_empty()
	assert_dict(driver.snapshot()).is_equal(expected)

func test_contact_drawings_have_priority_over_passive_provider() -> void:
	_pose_setup()
	_idle_tick()
	var calls := passive_calls
	for i in 3: _tick()
	assert_int(contacts.size()).is_equal(1)
	assert_int(passive_calls).is_equal(calls)
	assert_str(actor.sprite.animation).is_equal("primary_W")
	for i in 6: _idle_tick()
	assert_int(passive_calls).is_greater(calls)
	assert_str(actor.sprite.animation).is_equal("walk_W")

func test_guard_poses_advance_and_inactive_time_freezes() -> void:
	_pose_setup()
	passive_clip = "guard"
	passive_key = "guarding"
	for i in 3: _idle_tick(true, true)
	assert_str(actor.sprite.animation).is_equal("guard_W")
	assert_int(actor.sprite.frame).is_greater(0)
	var frame := actor.sprite.frame
	var calls := passive_calls
	_idle_tick(false)
	assert_int(actor.sprite.frame).is_equal(frame)
	assert_int(passive_calls).is_equal(calls)
	assert_array(contacts).is_empty()

func test_explicit_state_change_restarts_and_facing_change_keeps_phase() -> void:
	_pose_setup()
	_idle_tick()
	_idle_tick()
	var frame := actor.sprite.frame
	passive_facing = "N"
	# A zero-elapsed fixed observation changes variant without advancing its phase.
	var consumer: AbilityContactConsumer = driver._presentation
	var before := driver.snapshot()
	var after := before.duplicate(true)
	after.tick += 1
	consumer.observe(before, after, 0.000001)
	assert_str(actor.sprite.animation).is_equal("walk_N")
	assert_int(actor.sprite.frame).is_equal(frame)
	passive_clip = "idle"
	passive_key = "standing"
	after.tick += 1
	consumer.observe(before, after, 0.01)
	assert_str(actor.sprite.animation).is_equal("idle_N")
	assert_int(actor.sprite.frame).is_equal(0)

func test_foreign_contract_fails_closed_and_valid_replacement_recovers() -> void:
	_pose_setup()
	_idle_tick()
	var frame := actor.sprite.frame
	passive_bad = true
	_idle_tick()
	assert_int(actor.sprite.frame).is_equal(frame)
	assert_str(actor.ability_presentation_error).is_equal("presentation manifest differs from loaded body")
	passive_bad = false
	_idle_tick()
	assert_str(actor.ability_presentation_error).is_empty()
	assert_array(contacts).is_empty()

func test_reentrant_provider_cancellation_cannot_show_departed_pose() -> void:
	_pose_setup()
	passive_cancel = true
	_idle_tick()
	assert_str(actor.sprite.animation).is_equal("idle_S")
	assert_int(driver.player_phase_observed.get_connections().size()).is_equal(0)
	assert_array(contacts).is_empty()

func test_reset_detach_reconfigure_and_scene_exit_release_passive_binding() -> void:
	for reason in ["reset", "detach", "reconfigure", "exit"]:
		_pose_setup()
		_idle_tick()
		assert_str(actor.sprite.animation).is_equal("walk_W")
		var calls := passive_calls
		match reason:
			"reset": actor.reset_motion()
			"detach": actor.detach_action_driver()
			"reconfigure": driver.configure(_source(), Vector2.ZERO)
			"exit": remove_child(actor)
		_idle_tick()
		assert_int(passive_calls).is_equal(calls)
		assert_int(driver.player_phase_observed.get_connections().size()).is_equal(0)
		assert_array(contacts).is_empty()
