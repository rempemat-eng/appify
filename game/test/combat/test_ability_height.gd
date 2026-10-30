extends "res://test/combat/test_ability_sprite_presenter.gd"
## Exercise real Player body elevation without changing ground or collision coordinates.

func test_height_updates_without_drawing_changes_and_landing_restores_ground() -> void:
	_setup()
	actor.sprite.position = Vector2(4, -2)
	var ground := actor.sprite.position
	var shape: Node2D = actor.get_node("Shape")
	var shape_position := shape.position
	var shadow := Node2D.new()
	actor.add_child(shadow)
	shadow.position = Vector2(1, 3)
	var actor_position := actor.position
	assert_bool(actor.bind_ability_presentation(_provide, _contact)).is_true()
	actor.ability_support_height = 7.0
	var snapshot := driver.snapshot()
	snapshot.player.vaultHeight = 9.0
	assert_bool(actor._present_ability_pose(snapshot, driver)).is_true()
	assert_vector(actor.sprite.position).is_equal(ground + Vector2(0, -34))
	assert_vector(actor.position).is_equal(actor_position)
	assert_vector(shape.position).is_equal(shape_position)
	assert_vector(shadow.position).is_equal(Vector2(1, 3))
	assert_str(actor.sprite.animation).is_equal("idle_S")
	snapshot.player.vaultHeight = 0.0
	actor._present_ability_pose(snapshot, driver)
	assert_vector(actor.sprite.position).is_equal(ground + Vector2(0, -7))
	actor.ability_support_height = 0.0
	actor._present_ability_pose(snapshot, driver)
	assert_vector(actor.sprite.position).is_equal(ground)

func test_height_validated_and_does_not_mutate_snapshot_or_anchor_offsets() -> void:
	_setup()
	actor.bind_ability_presentation(_provide, _contact)
	var snapshot := driver.snapshot()
	snapshot.player.vaultHeight = 5
	var before := snapshot.duplicate(true)
	var anchor := actor.sprite.anchor("hand_R")
	assert_bool(actor._present_ability_pose(snapshot, driver)).is_true()
	assert_dict(snapshot).is_equal(before)
	assert_vector(actor.sprite.anchor("hand_R")).is_equal(anchor)
	for invalid in [NAN, INF, -1.0, "5", null]:
		snapshot.player.vaultHeight = invalid
		assert_bool(actor._present_ability_pose(snapshot, driver)).is_false()
		assert_vector(actor.sprite.position).is_equal(Vector2(0, -15))
	snapshot.player.vaultHeight = 0
	actor.ability_support_height = NAN
	assert_bool(actor._present_ability_pose(snapshot, driver)).is_false()

func test_every_cancellation_restores_original_body_position() -> void:
	for reason in ["reset", "detach", "cancel", "reconfigure", "exit"]:
		_setup()
		actor.sprite.position = Vector2(3, 2)
		actor.bind_ability_presentation(_provide, _contact)
		var snapshot := driver.snapshot()
		snapshot.player.vaultHeight = 8
		actor._present_ability_pose(snapshot, driver)
		match reason:
			"reset": actor.reset_motion()
			"detach": actor.detach_action_driver()
			"cancel": driver.cancel("test")
			"reconfigure": driver.configure(_source(), Vector2.ZERO)
			"exit": remove_child(actor)
		assert_vector(actor.sprite.position).is_equal(Vector2(3, 2))
		# A departed binding cannot reapply its old elevation.
		assert_bool(actor._present_ability_pose(snapshot, driver)).is_false()

func test_rebinding_at_height_never_captures_raised_body_as_ground() -> void:
	_setup()
	actor.bind_ability_presentation(_provide, _contact)
	var snapshot := driver.snapshot()
	snapshot.player.vaultHeight = 6
	actor._present_ability_pose(snapshot, driver)
	assert_bool(actor.bind_ability_presentation(_provide, _contact)).is_true()
	actor._present_ability_pose(snapshot, driver)
	assert_vector(actor.sprite.position).is_equal(Vector2(0, -18))
	actor.reset_motion()
	assert_vector(actor.sprite.position).is_equal(Vector2.ZERO)

func test_driver_supplies_final_vault_height_without_an_action_drawing() -> void:
	_setup()
	var source := _source()
	# This fixture isolates movement height; no production input/kit mapping is added.
	source.player.vaultRemaining = 0.4
	source.player.vaultDuration = 0.5
	source.player.vaultHeight = 0.0
	source.player.vaultDirX = 1.0
	source.player.vaultDirY = 0.0
	driver.configure(source, Vector2.ZERO)
	actor.bind_ability_presentation(_provide, _contact)
	driver.tick({"active": true}, {"character": "bramble", "move_actor": _move}, 0.1)
	var height: float = driver.snapshot().player.vaultHeight
	assert_float(height).is_greater(0.0)
	assert_float(actor.sprite.position.y).is_equal_approx(-height * 3.0, 0.00001)
	assert_array(contacts).is_empty()
	var frozen := actor.sprite.position
	driver.tick({"active": false}, {"character": "bramble", "move_actor": _move}, 0.1)
	assert_vector(actor.sprite.position).is_equal(frozen)
	for i in 4:
		driver.tick({"active": true}, {"character": "bramble", "move_actor": _move}, 0.1)
	assert_float(actor.sprite.position.y).is_equal(0.0)

func test_height_applied_before_release_contact() -> void:
	_setup()
	actor.ability_support_height = 6
	var observed: Array = []
	actor.bind_ability_presentation(_provide, func(_sample: Dictionary) -> void:
		observed.append(actor.sprite.position.y))
	for i in 3: _tick()
	assert_array(observed).is_equal([-6.0])
