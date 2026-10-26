extends GdUnitTestSuite

class Mover extends RefCounted:
	var position := Vector2.ZERO
	var targets: Array[Vector2] = []
	var wall := INF

	func move_to(target: Vector2) -> Vector2:
		targets.append(target)
		position = Vector2(minf(target.x, wall), target.y)
		return position

func _decode(value: Variant) -> Variant:
	if value is Dictionary:
		if value.size() == 1 and value.has("__f64le"):
			return str(value.__f64le).hex_decode().decode_double(0)
		var result := {}
		for key in value:
			result[key] = _decode(value[key])
		return result
	if value is Array:
		return value.map(_decode)
	return value

func _source(id: String = "bramble") -> Dictionary:
	var bytes := FileAccess.get_file_as_bytes("res://test/combat/simulation-oracle.json.gz")
	var data: Dictionary = _decode(JSON.parse_string(bytes.decompress_dynamic(128 * 1024 * 1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8()))
	var source: Dictionary = data.baseline
	source.mode = "practice"
	source.player.id = id
	return source

func _controls() -> Dictionary:
	return {"active": true, "move": Vector2.ZERO, "aim": Vector2.RIGHT}

func _context(id: String, mover: Mover) -> Dictionary:
	return {"character": id, "move_actor": mover.move_to, "position": mover.position}

func test_resolver_runs_once_per_fixed_tick_and_actual_position_is_used() -> void:
	var source := _source()
	var d := AbilityArenaDriver.new()
	assert_bool(d.configure(source, Vector2(10, 20))).is_true()
	var mover := Mover.new()
	mover.wall = 10 + 86 * 3
	var controls := _controls()
	controls.move = Vector2.RIGHT
	d.tick(controls, _context("bramble", mover), 0.1)
	assert_int(mover.targets.size()).is_equal(6)
	assert_float(float(d.snapshot().tick)).is_equal(float(source.tick + 6))
	assert_float(d.snapshot().player.x).is_equal(float(86.0))
	assert_float(d.snapshot().player.walkDistance).is_equal(float(0.0))
	assert_vector(mover.position).is_equal(Vector2(268, 314))
	assert_float(float(source.tick)).is_equal(float(0))

func test_concrete_driver_preserves_single_release_resources_and_projectile_phase() -> void:
	var source := _source("pendle")
	source.player.ammo = 3
	source.player.maxAmmo = 3
	var d := AbilityArenaDriver.new()
	d.configure(source, Vector2.ZERO)
	var mover := Mover.new()
	var controls := _controls()
	controls.primary = true
	var expected := source.duplicate(true)
	for i in 6:
		d.tick(controls, _context("pendle", mover), 0.1)
		expected = AbilitySimulation.step(expected, {"primary": true, "aimX": 186, "aimY": 98}, 0.1)
	var actual := d.snapshot()
	assert_float(float(actual.statistics.actions.primary)).is_equal(float(expected.statistics.actions.primary))
	assert_float(float(actual.player.ammo)).is_equal(float(expected.player.ammo))
	assert_float(float(actual.serial)).is_equal(float(expected.serial))
	assert_int(actual.projectiles.size()).is_equal(expected.projectiles.size())
	assert_float(float(actual.tick)).is_equal(float(expected.tick))

func test_frame_partitioning_retains_one_accumulator_and_actor_movement() -> void:
	var fine := AbilityArenaDriver.new()
	var coarse := AbilityArenaDriver.new()
	fine.configure(_source(), Vector2.ZERO)
	coarse.configure(_source(), Vector2.ZERO)
	var a := Mover.new()
	var b := Mover.new()
	var controls := _controls()
	controls.move = Vector2.RIGHT
	for i in 6:
		fine.tick(controls, _context("bramble", a), 1.0 / 60.0)
	coarse.tick(controls, _context("bramble", b), 0.1)
	assert_vector(a.position).is_equal(b.position)
	assert_int(a.targets.size()).is_equal(6)
	assert_int(b.targets.size()).is_equal(6)
	assert_float(float(fine.snapshot().tick)).is_equal(float(coarse.snapshot().tick))

func test_inactive_clears_queued_controls_without_ticking_or_moving() -> void:
	var d := AbilityArenaDriver.new()
	d.configure(_source(), Vector2.ZERO)
	var mover := Mover.new()
	assert_bool(d.request("secondary", Vector2.RIGHT)).is_true()
	d.tick({"active": false}, _context("bramble", mover), 0.1)
	assert_float(float(d.snapshot().tick)).is_equal(float(0))
	assert_array(mover.targets).is_empty()
	d.tick(_controls(), _context("bramble", mover), 1.0 / 60.0)
	assert_float(float(d.snapshot().statistics.actions.secondary)).is_equal(float(0))

func test_direct_request_survives_a_subtick_but_does_not_replay() -> void:
	var d := AbilityArenaDriver.new()
	d.configure(_source(), Vector2.ZERO)
	var mover := Mover.new()
	d.request("primary", Vector2.UP)
	d.tick(_controls(), _context("bramble", mover), 1.0 / 120.0)
	assert_float(float(d.snapshot().tick)).is_equal(float(0))
	d.tick(_controls(), _context("bramble", mover), 1.0 / 120.0)
	assert_float(float(d.snapshot().statistics.actions.primary)).is_equal(float(1))
	assert_float(d.snapshot().player.dirY).is_equal(float(-1.0))
	for i in 6:
		d.tick(_controls(), _context("bramble", mover), 0.1)
	assert_float(float(d.snapshot().statistics.actions.primary)).is_equal(float(1))

func test_character_mismatch_cancel_invalid_time_and_missing_mover_do_not_tick() -> void:
	var d := AbilityArenaDriver.new()
	d.configure(_source(), Vector2.ZERO)
	var mover := Mover.new()
	for delta in [NAN, INF, 0.0, -1.0]:
		d.tick(_controls(), _context("bramble", mover), delta)
	d.tick(_controls(), {}, 0.1)
	d.tick(_controls(), _context("velvet", mover), 0.1)
	assert_float(float(d.snapshot().tick)).is_equal(float(0))
	d.cancel("reset_motion")
	d.tick(_controls(), _context("bramble", mover), 0.1)
	assert_float(float(d.snapshot().tick)).is_equal(float(0))
	assert_bool(d.request("primary", Vector2.RIGHT)).is_false()

func test_unknown_live_mode_and_unmapped_dodge_are_rejected_without_losing_state() -> void:
	var d := AbilityArenaDriver.new()
	assert_bool(d.configure(_source(), Vector2.ZERO)).is_true()
	var invalid := _source()
	invalid.mode = "live"
	assert_bool(d.configure(invalid, Vector2.ZERO)).is_false()
	assert_bool(d.configure({"mode": "practice", "player": {"id": "bramble"}}, Vector2.ZERO)).is_false()
	assert_bool(d.request("dodge", Vector2.RIGHT)).is_false()
	assert_str(d.snapshot().player.id).is_equal("bramble")
	var copy := d.snapshot()
	copy.player.hp = -100
	assert_float(d.snapshot().player.hp).is_greater(0)

func test_player_executes_driver_motion_without_default_walk_or_duplicate_launch() -> void:
	SaveGame.reset()
	var p: Player = auto_free(load("res://actors/player.tscn").instantiate())
	add_child(p)
	p.set_physics_process(false)
	p.input_enabled = true
	p.use_mouse_aim = false
	p.aim = Vector2.RIGHT
	var source := _source()
	p.global_position = Vector2(source.player.x, source.player.y) * 3.0
	var d := AbilityArenaDriver.new()
	d.configure(source, Vector2.ZERO)
	p.attach_action_driver(d)
	Input.action_press("move_right")
	await get_tree().physics_frame
	var start := p.global_position
	p.set_physics_process(true)
	await get_tree().physics_frame
	p.set_physics_process(false)
	Input.action_release("move_right")
	assert_float(float(d.snapshot().tick)).is_equal(float(1))
	assert_float(p.global_position.x - start.x).is_equal_approx(57.0 / 60.0 * 3.0, 0.00003)
	assert_float(d.snapshot().player.x * 3).is_equal_approx(p.global_position.x, 0.00003)
	assert_float(p._swing_t).is_zero()

func test_blocked_action_dash_is_resolved_before_walk_distance() -> void:
	var source := _source("iona")
	var spec := AbilityCatalogue.action("iona", "secondary")
	source.player.action = "secondary"
	source.player.actionReleased = false
	source.player.actionDuration = spec.duration_seconds
	source.player.actionElapsed = float(spec.release_seconds) - AbilitySimulation.DT
	var d := AbilityArenaDriver.new()
	d.configure(source, Vector2(10, 20))
	var mover := Mover.new()
	mover.wall = 268.0
	d.tick(_controls(), _context("iona", mover), AbilitySimulation.DT)
	assert_int(mover.targets.size()).is_equal(2) # committed dash, then ordinary movement
	assert_float(d.snapshot().player.x).is_equal(float(86.0))
	assert_float(d.snapshot().player.walkDistance).is_equal(float(0.0))

func test_real_player_collision_clips_driver_targets_and_reports_actual_ground() -> void:
	SaveGame.reset()
	var p: Player = auto_free(load("res://actors/player.tscn").instantiate())
	add_child(p)
	p.set_physics_process(false)
	p.input_enabled = true
	p.use_mouse_aim = false
	var source := _source()
	p.position = Vector2(258, 294)
	var wall: StaticBody2D = auto_free(StaticBody2D.new())
	var shape := CollisionShape2D.new()
	var box := RectangleShape2D.new()
	box.size = Vector2(10, 100)
	shape.shape = box
	wall.add_child(shape)
	wall.position = Vector2(280, 294)
	add_child(wall)
	var d := AbilityArenaDriver.new()
	d.configure(source, Vector2.ZERO)
	p.attach_action_driver(d)
	await get_tree().physics_frame
	Input.action_press("move_right")
	p.set_physics_process(true)
	for i in 10:
		await get_tree().physics_frame
	p.set_physics_process(false)
	Input.action_release("move_right")
	assert_float(p.position.x).is_less_equal(266.01) # wall's left face275 minus body radius9
	assert_float(p.position.x).is_greater(258.0)
	assert_float(d.snapshot().player.x * 3).is_equal_approx(p.position.x, 0.00003)
