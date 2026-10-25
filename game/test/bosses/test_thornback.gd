extends GdUnitTestSuite
## The Thornback (bosses/thornback.gd): every telegraph lasts its full wind-up (never under 0.5 s), the phase
## change speeds the wind-ups and adds the slam, one attack at a time, the stagger window, the arena limit
## and the calm end. Stepped by hand (physics off), like Codex's enemy suites.

var _target: Player

func _boss(at := Vector2.ZERO) -> Thornback:
	_target = auto_free(load("res://actors/player.tscn").instantiate())
	_target.input_enabled = false
	_target.max_hp = 99
	add_child(_target)
	_target.set_physics_process(false)
	var boss: Thornback = auto_free(load("res://bosses/thornback.tscn").instantiate())
	boss.position = at
	add_child(boss)
	boss.set_physics_process(false)
	boss.target = _target
	return boss

## Steps until the boss winds up; returns the attack's name.
func _to_windup(boss: Thornback) -> String:
	for i in 40:
		boss.step(0.05)
		if boss.state == "windup":
			return boss.attack
	return ""

func test_each_telegraph_lasts_its_full_windup() -> void:
	var boss := _boss()
	_target.position = Vector2(400, 0)   # far: a charge first
	var seen := {}
	var signalled := []
	boss.telegraph_started.connect(func(a: String, s: float) -> void: signalled.append([a, s]))
	for round_ in 6:
		var name := _to_windup(boss)
		assert_str(name).is_not_empty()
		var w := boss.windup_time
		assert_float(w).is_greater_equal(Thornback.MIN_WINDUP)
		assert_float(w).is_equal_approx(float(Thornback.WINDUP[name][boss.phase - 1]), 0.0001)
		boss.step(w - 0.01)
		assert_str(boss.state).is_equal("windup")
		boss.step(0.02)
		assert_str(boss.state).is_equal("act")
		seen[name] = true
		boss._finish_attack(0.1)          # end the attack as its own resolution would
		for th in boss.thorns:
			th.finish()
		boss.step(0.2)
		_target.position = Vector2(400, 0) if round_ % 2 == 0 else Vector2(90, 0)
	assert_bool(seen.has("charge")).is_true()
	assert_bool(seen.has("volley")).is_true()
	assert_int(signalled.size()).is_equal(6)

func test_phase_two_is_faster_but_never_under_half_a_second_and_adds_the_slam() -> void:
	var boss := _boss()
	var changes := []
	boss.phase_changed.connect(func(p: int) -> void: changes.append(p))
	assert_int(boss.phase).is_equal(1)
	var before := boss.windup_for("charge")
	boss.step(0.05)  # dormant -> approach
	boss.take_hit(Thornback.MAX_HP - Thornback.PHASE2_AT, Vector2.LEFT)
	assert_int(boss.phase).is_equal(2)
	assert_array(changes).is_equal([2])
	assert_str(boss.state).is_equal("roar")
	for a in ["charge", "volley", "slam"]:
		assert_float(boss.windup_for(a)).is_greater_equal(0.5)
	assert_float(boss.windup_for("charge")).is_less(before)
	boss.step(Thornback.ROAR_TIME + 0.01)
	assert_str(boss.state).is_equal("approach")
	_target.position = Vector2(60, 0)   # near: the slam comes up in turn
	var names := []
	for i in 6:
		var n := _to_windup(boss)
		names.append(n)
		boss.step(boss.windup_time + 0.01)
		boss._finish_attack(0.05)
		for th in boss.thorns:
			th.finish()
		boss.step(0.1)
	assert_bool(names.has("slam")).is_true()

func test_one_attack_at_a_time_until_the_last_thorn_is_gone() -> void:
	var boss := _boss()
	_target.position = Vector2(120, 0)
	boss.phase = 1
	boss._next = 1                        # volley next
	assert_str(_to_windup(boss)).is_equal("volley")
	boss.step(boss.windup_time + 0.01)
	assert_str(boss.state).is_equal("act")
	assert_int(boss.thorns.size()).is_equal(Thornback.VOLLEY[0])
	assert_int(boss.attack_count()).is_equal(1)
	for i in 10:
		boss.step(0.1)
		assert_str(boss.state).is_not_equal("windup")
	for th in boss.thorns:
		th.finish()
	await get_tree().process_frame      # the thorns are freed, not only queued
	boss.step(0.35)
	assert_str(boss.state).is_equal("recover")
	assert_int(boss.attack_count()).is_equal(0)

func test_stagger_window_takes_double_damage() -> void:
	var boss := _boss()
	boss.step(0.05)
	boss._stagger(Thornback.STAGGER_TIME)
	assert_bool(boss.is_staggered()).is_true()
	var hp := boss.hp
	boss.take_hit(1, Vector2.LEFT)
	assert_int(boss.hp).is_equal(hp - 2)
	boss.step(Thornback.STAGGER_TIME + 0.01)
	assert_str(boss.state).is_equal("recover")

func test_charge_into_the_arena_edge_staggers() -> void:
	var boss := _boss(Vector2(300, 300))
	boss.arena = Rect2(100, 100, 400, 300)
	boss.home = boss.global_position
	_target.position = Vector2(480, 300)
	boss._next = 0
	assert_str(_to_windup(boss)).is_equal("charge")
	boss.step(boss.windup_time + 0.01)
	boss.global_position = Vector2(900, 300)   # carried past the edge by the charge
	boss._keep_in_arena()
	assert_bool(boss.arena.grow(1).has_point(boss.global_position)).is_true()
	assert_str(boss.state).is_equal("stagger")

func test_freed_not_killed() -> void:
	var boss := _boss()
	var freed := []
	boss.died.connect(func() -> void: freed.append(true))
	boss.step(0.05)
	boss.take_hit(Thornback.MAX_HP * 2, Vector2.LEFT)
	assert_array(freed).is_equal([true])
	assert_str(boss.state).is_equal("freed")
	assert_int(boss.collision_layer).is_equal(0)
	assert_bool(is_instance_valid(boss) and not boss.is_queued_for_deletion()).is_true()
	boss.take_hit(5, Vector2.LEFT)
	assert_array(freed).is_equal([true])
