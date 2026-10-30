extends GdUnitTestSuite

class ProbeDriver extends AbilityActionDriver:
	var ticks: Array[Dictionary] = []
	var requests: Array = []
	var cancelled: Array = []
	var characters: Array = []
	var busy := false

	func character_changed(id: String) -> void:
		characters.append(id)

	func is_busy() -> bool:
		return busy

	func request(action: String, direction: Vector2) -> bool:
		requests.append([action, direction])
		return true

	func tick(controls: Dictionary, context: Dictionary, delta: float) -> void:
		ticks.append({"controls": controls.duplicate(true), "context": context.duplicate(true), "delta": delta})

	func cancel(reason: String) -> void:
		cancelled.append(reason)

func before_test() -> void:
	SaveGame.reset()
	Dialogue.busy = false
	for action in ["attack", "ranged", "special", "dodge", "move_right"]:
		Input.action_release(action)

func after_test() -> void:
	for action in ["attack", "ranged", "special", "dodge", "move_right"]:
		Input.action_release(action)
	Dialogue.busy = false

func _player() -> Player:
	var p: Player = auto_free(load("res://actors/player.tscn").instantiate())
	add_child(p)
	p.set_physics_process(false)
	p.input_enabled = false
	p.use_mouse_aim = false
	return p

func test_driver_is_optional_and_refuses_mid_action_or_duplicate_attachment() -> void:
	var p := _player()
	var driver := ProbeDriver.new()
	assert_bool(p.start_shot()).is_true()
	assert_bool(p.attach_action_driver(driver)).is_false()
	p.reset_motion()
	assert_bool(p.attach_action_driver(driver)).is_true()
	assert_bool(p.attach_action_driver(ProbeDriver.new())).is_false()
	assert_array(driver.characters).is_equal(["bramble"])
	assert_bool(p.action_driver == driver).is_true()

func test_direct_actions_forward_without_legacy_timers_or_arrow_callbacks() -> void:
	var p := _player()
	var driver := ProbeDriver.new()
	p.attach_action_driver(driver)
	p.aim = Vector2.LEFT
	var shots := [0]
	p.shot_released.connect(func(_a: Node, _frame: int) -> void: shots[0] += 1)
	assert_bool(p.start_shot()).is_true()
	assert_bool(p.start_swing()).is_true()
	assert_bool(p.start_roll(Vector2.UP)).is_true()
	p._release(0)
	p._resolve_swing()
	assert_array(driver.requests).is_equal([["primary", Vector2.LEFT], ["primary", Vector2.LEFT], ["dodge", Vector2.UP]])
	assert_int(shots[0]).is_equal(0)
	assert_float(p._swing_t).is_equal(0.0)
	assert_float(p._roll_t).is_equal(0.0)
	assert_int(p.roll_charges).is_equal(Player.ROLL_CHARGES)
	assert_bool(p.hitbox.monitoring).is_false()

func test_held_inputs_forward_once_per_tick_without_legacy_launch() -> void:
	var p := _player()
	var driver := ProbeDriver.new()
	p.attach_action_driver(driver)
	p.input_enabled = true
	for action in ["attack", "ranged", "special", "dodge"]:
		Input.action_press(action)
	p._physics_process(1.0 / 60.0)
	p._physics_process(1.0 / 60.0)
	assert_int(driver.ticks.size()).is_equal(2)
	for tick in driver.ticks:
		assert_bool(tick.controls.primary).is_true()
		assert_bool(tick.controls.secondary).is_true()
		assert_bool(tick.controls.special).is_true()
		assert_bool(tick.controls.guard).is_false() # no unsolicited guard binding
	assert_array(driver.requests).is_empty()
	assert_bool(p.is_shooting()).is_false()
	assert_bool(p.is_rolling()).is_false()

func test_disabled_or_dialogue_frames_forward_neutral_controls_and_do_not_move() -> void:
	var p := _player()
	var driver := ProbeDriver.new()
	p.attach_action_driver(driver)
	for action in ["attack", "ranged", "special", "dodge", "move_right"]:
		Input.action_press(action)
	var start := p.global_position
	p._physics_process(1.0 / 60.0)
	p.input_enabled = true
	Dialogue.busy = true
	p._physics_process(1.0 / 60.0)
	assert_vector(p.global_position).is_equal(start)
	for tick in driver.ticks:
		assert_bool(tick.controls.active).is_false()
		for action in ["primary", "secondary", "special", "guard", "dodge"]:
			assert_bool(tick.controls[action]).is_false()
		assert_vector(tick.controls.move).is_equal(Vector2.ZERO)

func test_player_moves_once_and_driver_receives_post_collision_position() -> void:
	var p := _player()
	var driver := ProbeDriver.new()
	p.attach_action_driver(driver)
	p.input_enabled = true
	Input.action_press("move_right")
	await get_tree().physics_frame
	var start := p.global_position
	p.set_physics_process(true)
	await get_tree().physics_frame
	p.set_physics_process(false)
	assert_int(driver.ticks.size()).is_equal(1)
	assert_float(p.global_position.x - start.x).is_equal_approx(p.walk_speed / 60.0, 0.00001)
	assert_vector(driver.ticks[0].context.position).is_equal(p.global_position)
	assert_vector(driver.ticks[0].context.velocity).is_equal(Vector2.RIGHT * p.walk_speed)
	assert_str(driver.ticks[0].context.facing).is_equal("E")

func test_reset_detach_and_defeat_cancel_without_enabling_legacy_path_early() -> void:
	var p := _player()
	var driver := ProbeDriver.new()
	p.attach_action_driver(driver)
	p.reset_motion()
	assert_array(driver.cancelled).is_equal(["reset_motion"])
	assert_bool(p.take_damage(p.max_hp)).is_true()
	assert_array(driver.cancelled).is_equal(["reset_motion", "defeated"])
	assert_bool(p.start_shot()).is_false()
	assert_bool(p.set_character("velvet")).is_false()
	p.detach_action_driver()
	p.detach_action_driver()
	assert_array(driver.cancelled).is_equal(["reset_motion", "defeated", "detached"])
	assert_bool(p.is_defeated()).is_true()

func test_character_change_preserves_hp_and_position_but_refuses_busy_driver() -> void:
	var p := _player()
	var driver := ProbeDriver.new()
	p.attach_action_driver(driver)
	p.hp = 3
	p.position = Vector2(123, 45)
	driver.busy = true
	assert_bool(p.set_character("velvet")).is_false()
	assert_str(p.character).is_equal("bramble")
	driver.busy = false
	assert_bool(p.set_character("velvet")).is_true()
	assert_array(driver.characters).is_equal(["bramble", "velvet"])
	assert_int(p.hp).is_equal(3)
	assert_vector(p.position).is_equal(Vector2(123, 45))

func test_invalid_delta_never_ticks_and_detach_restores_legacy_actions() -> void:
	var p := _player()
	var driver := ProbeDriver.new()
	p.attach_action_driver(driver)
	for delta in [0.0, -1.0, INF, NAN]:
		p._physics_process(delta)
	assert_array(driver.ticks).is_empty()
	p.detach_action_driver()
	assert_bool(p.start_roll(Vector2.RIGHT)).is_true()
	assert_bool(p.is_rolling()).is_true()
