extends GdUnitTestSuite

var drawings: Array = []
var contacts: Array = []
var driver: AbilityArenaDriver
var cancel_on_draw := false
var moves := 0
var moves_at_cancel := -1

func before_test() -> void:
	drawings = []
	contacts = []
	cancel_on_draw = false
	moves = 0
	moves_at_cancel = -1
	driver = AbilityArenaDriver.new()
	driver.configure(_source(), Vector2.ZERO)

func _decode(value: Variant) -> Variant:
	if value is Dictionary:
		if value.size() == 1 and value.has("__f64le"):
			return str(value.__f64le).hex_decode().decode_double(0)
		var result := {}
		for key in value: result[key] = _decode(value[key])
		return result
	if value is Array: return value.map(_decode)
	return value

func _source() -> Dictionary:
	var bytes := FileAccess.get_file_as_bytes("res://test/combat/simulation-oracle.json.gz")
	var data: Dictionary = _decode(JSON.parse_string(bytes.decompress_dynamic(128 * 1024 * 1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8()))
	data.baseline.mode = "practice"
	return data.baseline

func _provide(state: Dictionary, action: String) -> Dictionary:
	var release := AbilityPlayerPhase._release_time(state.player)
	var duration := float(state.player.actionDuration)
	return {"manifest": {"clips": {action: {"loop": false, "release_frame": 1,
		"facings": {"E": {"frames": [{"anchors": {}}, {"anchors": {"tip": [21, -30]}}]}}}}},
		"clip": action, "facing": "E", "durations": [release, duration - release]}

func _draw(sample: Dictionary) -> void:
	drawings.append(sample.duplicate(true))
	if cancel_on_draw and sample.index == 1:
		moves_at_cancel = moves
		driver.cancel("callback_detached")

func _contact(sample: Dictionary) -> void:
	contacts.append(sample.duplicate(true))

func _move(target: Vector2) -> Vector2:
	moves += 1
	return target

func _tick(delta := 0.1, active := true) -> void:
	driver.tick({"active": active, "primary": true, "aim": Vector2.RIGHT},
		{"character": "bramble", "move_actor": _move}, delta)

func _advance() -> void:
	for i in 3:
		_tick()

func _bind() -> void:
	assert_bool(driver.bind_presentation(_provide, _draw, _contact)).is_true()

func test_binding_emits_one_contact_after_its_drawing_without_second_simulation() -> void:
	_bind()
	var expected := _source()
	for i in 3:
		_tick()
		expected = AbilitySimulation.step(expected, {"primary": true, "aimX": 186, "aimY": 98}, 0.1)
	assert_int(contacts.size()).is_equal(1)
	assert_int(drawings[-1].index).is_equal(1)
	assert_vector(AbilityContactTrack.anchor(contacts[0], "tip").offset).is_equal(Vector2(21, -30))
	assert_dict(driver.snapshot()).is_equal(expected)

func test_replacing_binding_cancels_old_contact_and_has_one_listener() -> void:
	_bind()
	_tick(1.0 / 60.0)
	assert_int(drawings.size()).is_equal(1)
	_bind()
	assert_int(driver.player_phase_observed.get_connections().size()).is_equal(1)
	_advance()
	assert_array(contacts).is_empty() # replacement cannot join an old action mid-clock

func test_invalid_binding_keeps_valid_binding_and_clear_is_idempotent() -> void:
	_bind()
	assert_bool(driver.bind_presentation(Callable(), _draw, _contact)).is_false()
	_advance()
	assert_int(contacts.size()).is_equal(1)
	driver.clear_presentation()
	driver.clear_presentation()
	assert_int(driver.player_phase_observed.get_connections().size()).is_equal(0)
	_advance()
	assert_int(contacts.size()).is_equal(1)

func test_reconfigure_clears_old_sequence_and_requires_explicit_rebinding() -> void:
	_bind()
	_tick(1.0 / 60.0)
	assert_bool(driver.configure(_source(), Vector2.ZERO)).is_true()
	_advance()
	assert_int(drawings.size()).is_equal(1)
	assert_array(contacts).is_empty()
	_bind()
	assert_int(driver.player_phase_observed.get_connections().size()).is_equal(1)

func test_reentrant_cancel_at_contact_drawing_drops_contact_and_later_phases() -> void:
	_bind()
	cancel_on_draw = true
	_advance()
	assert_array(contacts).is_empty()
	assert_int(drawings.size()).is_equal(2)
	assert_int(driver.player_phase_observed.get_connections().size()).is_equal(0)
	_advance()
	assert_int(drawings.size()).is_equal(2)
	assert_bool(driver.bind_presentation(_provide, _draw, _contact)).is_false()
	assert_int(moves).is_equal(moves_at_cancel)

func test_inactive_time_freezes_bound_sequence_and_character_change_cancels() -> void:
	_bind()
	_tick(1.0 / 60.0)
	_tick(1.0, false)
	assert_int(drawings.size()).is_equal(1)
	assert_array(contacts).is_empty()
	driver.character_changed("velvet")
	assert_int(driver.player_phase_observed.get_connections().size()).is_equal(0)
	_advance()
	assert_array(contacts).is_empty()

func _player() -> Player:
	var p: Player = auto_free(load("res://actors/player.tscn").instantiate())
	add_child(p)
	p.set_physics_process(false)
	p.input_enabled = false
	p.use_mouse_aim = false
	assert_bool(p.attach_action_driver(driver)).is_true()
	return p

func test_player_reset_detach_and_defeat_cancel_pending_contacts() -> void:
	for reason in ["reset", "detach", "defeat"]:
		driver.configure(_source(), Vector2.ZERO)
		var p := _player()
		_bind()
		_tick(1.0 / 60.0)
		match reason:
			"reset": p.reset_motion()
			"detach": p.detach_action_driver()
			"defeat": p.take_damage(p.max_hp)
		_advance()
		assert_int(driver.player_phase_observed.get_connections().size()).is_equal(0)
		assert_array(contacts).is_empty()
		p.detach_action_driver()

func test_actor_scene_exit_cancels_pending_contacts_before_reentry() -> void:
	var p := _player()
	_bind()
	_tick(1.0 / 60.0)
	remove_child(p)
	_advance()
	assert_array(contacts).is_empty()
	assert_str(driver.last_error).is_equal("actor_exited_tree")
	add_child(p)
	p.set_physics_process(false)
	assert_bool(driver.bind_presentation(_provide, _draw, _contact)).is_false()
