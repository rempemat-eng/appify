extends GdUnitTestSuite
## The roll (game-design.md 4.2): invulnerable for its first 0.26 s of 0.42, two charges, each back
## after 1.2 s; and the three-swing combo.

func before_test() -> void:
	SaveGame.reset()

func _player() -> Player:
	var p: Player = auto_free(load("res://actors/player.tscn").instantiate())
	add_child(p)
	p.input_enabled = false
	p.use_mouse_aim = false
	return p

func _frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame

func test_roll_grants_iframes() -> void:
	var p := _player()
	assert_bool(p.is_invulnerable()).is_false()
	assert_bool(p.start_roll(Vector2.RIGHT)).is_true()
	assert_bool(p.is_invulnerable()).is_true()
	assert_bool(p.take_damage(1)).is_false()
	assert_int(p.hp).is_equal(p.max_hp)

func test_iframes_end_before_the_roll_does() -> void:
	var p := _player()
	p.start_roll(Vector2.RIGHT)
	await _frames(20)  # 0.33 s: past the 0.26 s of invulnerability, still rolling
	assert_bool(p.is_invulnerable()).is_false()
	assert_bool(p.is_rolling()).is_true()
	assert_bool(p.take_damage(1)).is_true()
	assert_int(p.hp).is_equal(p.max_hp - 1)

func test_two_charges_then_recharge() -> void:
	var p := _player()
	assert_bool(p.start_roll(Vector2.LEFT)).is_true()
	await _frames(28)  # let the first roll finish
	assert_bool(p.start_roll(Vector2.LEFT)).is_true()
	await _frames(28)
	assert_int(p.roll_charges).is_equal(0)
	assert_bool(p.start_roll(Vector2.LEFT)).is_false()
	await _frames(40)  # 1.2 s after the first roll: one charge back
	assert_int(p.roll_charges).is_greater_equal(1)
	assert_bool(p.start_roll(Vector2.LEFT)).is_true()

func test_cannot_roll_while_rolling() -> void:
	var p := _player()
	assert_bool(p.start_roll(Vector2.UP)).is_true()
	assert_bool(p.start_roll(Vector2.UP)).is_false()
	assert_int(p.roll_charges).is_equal(1)

func test_combo_chains_to_a_finisher() -> void:
	var p := _player()
	for want in [1, 2, 3, 1]:
		assert_bool(p.start_swing()).is_true()
		assert_int(p.combo).is_equal(want)
		await _frames(13)  # the swing ends (0.18 s), inside the chain window

func test_melee_hits_an_enemy() -> void:
	var p := _player()
	var e: Enemy = auto_free(load("res://actors/enemy.tscn").instantiate())
	add_child(e)
	p.global_position = Vector2(100, 100)
	e.global_position = Vector2(100 + Player.SWING_REACH, 108)
	e.set_physics_process(false)
	p.aim = Vector2.RIGHT
	var hits := [0]
	p.hit_landed.connect(func(_t: Node, _h: bool) -> void: hits[0] += 1)
	await _frames(2)
	p.start_swing()
	await _frames(6)
	Engine.time_scale = 1.0
	assert_int(hits[0]).is_equal(1)
	assert_int(e.hp).is_equal(e.max_hp - 1)
