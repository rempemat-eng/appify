extends GdUnitTestSuite

var events: Array = []
var consumer: AbilityContactConsumer
var bad_clock := false
var cancel_on_drawing := false

func before_test() -> void:
	events = []
	bad_clock = false
	cancel_on_drawing = false
	consumer = AbilityContactConsumer.new()
	consumer.configure(_provide, _draw, _contact)

func _provide(state: Dictionary, action: String) -> Dictionary:
	var release := AbilityPlayerPhase._release_time(state.player)
	var duration := float(state.player.actionDuration)
	var frames := [{"anchors": {"tip": [-1.0, -2.0]}},
		{"anchors": {"tip": [-22.0, -30.5]}}, {"anchors": {"tip": [-3.0, -4.0]}}]
	return {"manifest": {"clips": {action: {"loop": false, "release_frame": 1,
		"facings": {"W": {"frames": frames}}}}}, "clip": action, "facing": "W",
		"durations": [release + (0.01 if bad_clock else 0.0), (duration - release) / 2.0, (duration - release) / 2.0]}

func _draw(sample: Dictionary) -> void:
	events.append({"kind": "draw", "index": sample.index, "token": sample.token})
	if cancel_on_drawing:
		consumer.cancel()

func _contact(sample: Dictionary) -> void:
	events.append({"kind": "contact", "index": sample.index, "token": sample.token,
		"offset": AbilityContactTrack.anchor(sample, "tip").offset})
	sample.frame.anchors.tip[0] = 999 # callback must not corrupt later events

func _state(action: String = "idle", elapsed: float = 0.0, count: int = 0) -> Dictionary:
	return {"player": {"id": "bramble", "action": action, "actionElapsed": elapsed,
		"actionDuration": 0.5, "hp": 100.0, "blocking": false},
		"statistics": {"actions": {"primary": count, "secondary": 0, "special": 0}}}

func _commit() -> void:
	consumer.observe(_state(), _state("primary", 0.0, 1), 1.0 / 60.0)

func test_draw_is_committed_before_contact_and_anchor_is_not_scaled_or_mirrored() -> void:
	_commit()
	consumer.observe(_state("primary", 0, 1), _state("primary", 0.2, 1), 0.2)
	assert_str(events[-2].kind).is_equal("draw")
	assert_str(events[-1].kind).is_equal("contact")
	assert_int(events[-2].index).is_equal(1)
	assert_vector(events[-1].offset).is_equal(Vector2(-22, -30.5))
	consumer.observe(_state("primary", 0.2, 1), _state("idle", 0, 1), 0.3)
	assert_int(events.filter(func(e: Dictionary) -> bool: return e.kind == "contact").size()).is_equal(1)

func test_finishing_and_recommitting_same_action_does_not_drop_previous_contact() -> void:
	_commit()
	consumer.observe(_state("primary", 0, 1), _state("primary", 0, 2), 0.5)
	assert_array(events.map(func(e: Dictionary) -> String: return e.kind)).is_equal(["draw", "draw", "contact", "draw", "draw"])
	assert_int(events[-1].token).is_equal(2)

func test_guard_death_and_identity_changes_cancel_without_stale_release() -> void:
	for reason in ["guard", "death", "identity"]:
		_commit()
		var after := _state("primary", 0.2, 1)
		if reason == "guard": after.player.blocking = true
		if reason == "death": after.player.hp = 0
		if reason == "identity": after.player.id = "velvet"
		consumer.observe(_state("primary", 0, 1), after, 0.2)
		consumer.observe(_state("primary", 0.2, 1), _state("idle", 0, 1), 1.0)
	assert_int(events.filter(func(e: Dictionary) -> bool: return e.kind == "contact").size()).is_equal(0)

func test_explicit_clock_mismatch_is_rejected_without_retiming() -> void:
	bad_clock = true
	_commit()
	assert_array(events).is_empty()
	assert_str(consumer.last_error).contains("canonical action clock")
	bad_clock = false
	consumer.observe(_state("primary", 0, 1), _state("primary", 0, 2), 0.5)
	assert_int(events.size()).is_equal(1)

func test_reentrant_cancel_stops_remaining_drawings_and_contact() -> void:
	_commit()
	cancel_on_drawing = true
	consumer.observe(_state("primary", 0, 1), _state("idle", 0, 1), 0.5)
	assert_int(events.size()).is_equal(2)
	assert_str(events[-1].kind).is_equal("draw")

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

func _move(target: Vector2) -> Vector2:
	return target

func test_driver_fixed_step_signal_presents_coarse_release_once_without_duplicate_simulation() -> void:
	var source := _source()
	var driver := AbilityArenaDriver.new()
	driver.configure(source, Vector2.ZERO)
	driver.player_phase_observed.connect(consumer.observe)
	var controls := {"active": true, "primary": true, "aim": Vector2.RIGHT}
	var context := {"character": "bramble", "move_actor": _move}
	var expected := source
	for step in 3:
		driver.tick(controls, context, 0.1)
		expected = AbilitySimulation.step(expected, {"primary": true, "aimX": 186, "aimY": 98}, 0.1)
	assert_int(events.filter(func(e: Dictionary) -> bool: return e.kind == "contact").size()).is_equal(1)
	assert_dict(driver.snapshot()).is_equal(expected)

func _tamper(before: Dictionary, after: Dictionary, _delta: float) -> void:
	before.player.hp = -999
	after.player.hp = -888
	after.projectiles.clear()

func test_observer_cannot_mutate_canonical_state() -> void:
	var source := _source()
	var expected := AbilitySimulation.step(source, {"primary": true}, 0.1)
	var actual := AbilitySimulation.step(source, {"primary": true}, 0.1, Callable(), _tamper)
	assert_dict(actual).is_equal(expected)

func test_invalid_time_and_invalid_reconfiguration_preserve_live_sequence() -> void:
	_commit()
	assert_bool(consumer.configure(Callable(), _draw, _contact)).is_false()
	for delta in [0.0, -1.0, NAN, INF]:
		consumer.observe(_state("primary", 0, 1), _state("primary", 0.2, 1), delta)
	assert_int(events.size()).is_equal(1)
	consumer.observe(_state("primary", 0, 1), _state("primary", 0.2, 1), 0.2)
	assert_str(events[-1].kind).is_equal("contact")

func _broken_provider(_state: Dictionary, _action: String) -> Dictionary:
	return {"manifest": {"clips": null}, "clip": "primary", "facing": "W", "durations": [0.5]}

func test_missing_clip_container_fails_closed_without_runtime_error() -> void:
	consumer.configure(_broken_provider, _draw, _contact)
	_commit()
	assert_array(events).is_empty()
	assert_str(consumer.last_error).is_equal("missing presentation clips")

func _cancel_provider(state: Dictionary, action: String) -> Dictionary:
	consumer.cancel()
	return _provide(state, action)

func test_provider_cancellation_cannot_resurrect_a_sequence() -> void:
	consumer.configure(_cancel_provider, _draw, _contact)
	_commit()
	consumer.observe(_state("primary", 0, 1), _state("primary", 0.3, 1), 0.3)
	assert_array(events).is_empty()

func test_duplicate_fixed_tick_cannot_advance_or_recommit_a_contact() -> void:
	var before := _state()
	var after := _state("primary", 0, 1)
	after.tick = 1
	consumer.observe(before, after, 0.1)
	consumer.observe(before, after, 0.1)
	assert_int(events.size()).is_equal(1)
	var contact := _state("primary", 0.2, 1)
	contact.tick = 2
	consumer.observe(after, contact, 0.2)
	consumer.observe(after, contact, 0.2)
	assert_int(events.filter(func(e: Dictionary) -> bool: return e.kind == "contact").size()).is_equal(1)
