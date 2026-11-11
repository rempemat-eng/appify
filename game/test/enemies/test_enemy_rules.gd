extends GdUnitTestSuite
## The enemy rules of 10 Nov, for the mossling (actors/enemy.gd) and the Undercroft's creatures
## (enemies/slice_enemy.gd): no healing on the walk home and full health 3 s after it; a hit wakes an idle
## enemy and its camp mates when the archer is within 330; an enemy that cannot come for the archer cannot
## be hurt by them (asleep and out of range, or at its leash limit: the arrow glances off); the way home
## leads round a solid, and a walk that cannot be finished is given up cleanly; and no noticing by nearness
## for a moment after a zone becomes ready. The movement tests run on real physics steps.

const MOSSLING := preload("res://actors/enemy.tscn")

var _archer: Node2D

func _host() -> Node2D:
	var host: Node2D = auto_free(Node2D.new())
	add_child(host)
	_archer = Node2D.new()
	host.add_child(_archer)
	_archer.position = Vector2(5000, 5000)
	return host

func _mossling(host: Node2D, at: Vector2) -> Enemy:
	var e: Enemy = MOSSLING.instantiate()
	e.position = at
	host.add_child(e)
	e.target = _archer
	return e

func _creature(host: Node2D, at: Vector2, role := "rusher") -> SliceEnemy:
	var e := SliceEnemy.new()
	e.role = role
	e.position = at
	host.add_child(e)
	e.target = _archer
	return e

func _steps(n: int) -> void:
	for i in n:
		await get_tree().physics_frame

func _wall(host: Node2D, rect: Rect2) -> void:
	var body := StaticBody2D.new()
	body.collision_layer = 1
	var shape := CollisionShape2D.new()
	var box := RectangleShape2D.new()
	box.size = rect.size
	shape.shape = box
	body.position = rect.get_center()
	body.add_child(shape)
	host.add_child(body)

# --- the mossling -------------------------------------------------------------------------------------

func test_a_mossling_does_not_heal_on_the_walk_home_and_is_whole_three_seconds_after() -> void:
	var host := _host()
	var e := _mossling(host, Vector2.ZERO)
	e.hp = 1
	_archer.position = Vector2(100, 0)        # inside its aggro radius: it comes
	await _steps(3)
	assert_str(String(e.state)).is_equal("chase")
	e.global_position = Vector2(280, 0)       # dragged nearly to its leash limit
	_archer.position = Vector2(5000, 5000)    # and the target runs off
	await _steps(2)
	assert_str(String(e.state)).is_equal("leash")
	await _steps(60)                          # a second of the walk home
	assert_str(String(e.state)).is_equal("leash")
	assert_int(e.hp).is_equal(1)              # main healed 1 every 30 physics frames of the walk
	await _steps(60)                          # 280 px at 152 px a second: home by now
	assert_str(String(e.state)).is_equal("idle")
	assert_vector(e.global_position).is_equal(e.home)
	assert_int(e.hp).is_equal(1)
	await _steps(int(Enemy.HOME_HEAL_TIME * 60.0) - 70)
	assert_int(e.hp).is_equal(1)              # not yet three seconds at home
	await _steps(80)
	assert_int(e.hp).is_equal(e.max_hp)

func test_a_hit_wakes_an_idle_mossling_and_its_camp_mates_when_the_archer_is_within_330() -> void:
	var host := _host()
	var a := _mossling(host, Vector2(0, 0))
	var b := _mossling(host, Vector2(40, 30))
	var far := _mossling(host, Vector2(0, 400))    # same camp, out of earshot (aggro radius 165)
	for e: Enemy in [a, b, far]:
		e.set_physics_process(false)
	_archer.position = Vector2(-250, 0)            # outside the 165 aggro radius, inside 330
	a.hsm.update(0.1)
	assert_str(String(a.state)).is_equal("idle")
	a.take_hit(1, Vector2.RIGHT)
	assert_int(a.hp).is_equal(2)
	assert_str(String(a.state)).is_equal("chase")
	assert_str(String(b.state)).is_equal("chase")
	assert_str(String(far.state)).is_equal("idle")

## Played on 10 Nov: shot from 320, the arrow's knock pushed the mossling past its 330 lose radius; it
## gave the archer up, walked the 20 px home and was shot again asleep, three times, without ever coming.
func test_a_mossling_woken_by_a_shot_keeps_coming_when_the_arrow_knocks_it_past_330() -> void:
	var host := _host()
	var e := _mossling(host, Vector2.ZERO)
	var mate := _mossling(host, Vector2(30, 0))          # 350 from the archer, in earshot, the archer on its ground
	_archer.position = Vector2(-320, 0)
	await _steps(2)
	e.take_hit(1, Vector2.RIGHT, 270.0)                  # the arrow's own knockback
	await _steps(9)                                      # the stagger (0.14 s) is just over
	assert_float(e.global_position.distance_to(_archer.position)).is_greater(e.lose_radius)   # knocked past 330 ...
	await _steps(21)
	assert_str(String(e.state)).is_equal("chase")        # ... and it still comes
	assert_float(e.global_position.x).is_less(0.0)
	assert_str(String(mate.state)).is_equal("chase")
	await _steps(120)
	assert_float(e.global_position.distance_to(_archer.position)).is_less(200.0)
	assert_float(mate.global_position.distance_to(_archer.position)).is_less(230.0)
	# once it has not been hit for PROVOKED_TIME, an archer who has run off is given up as before
	_archer.position = Vector2(-5000, 0)
	await _steps(int(Enemy.PROVOKED_TIME * 60.0))
	assert_str(String(e.state)).is_not_equal("chase")

func test_an_arrow_from_beyond_330_glances_off_an_idle_mossling() -> void:
	var host := _host()
	var e := _mossling(host, Vector2.ZERO)
	e.set_physics_process(false)
	var glances := [0]
	e.glanced.connect(func() -> void: glances[0] += 1)
	_archer.position = Vector2(-340, 0)
	e.take_hit(1, Vector2.RIGHT)
	assert_int(e.hp).is_equal(3)
	assert_str(String(e.state)).is_equal("idle")
	assert_int(glances[0]).is_equal(1)
	assert_float(e.glance_t).is_greater(0.0)
	assert_vector(e.velocity).is_equal(Vector2.ZERO)     # no knockback either: it does not react

func test_a_mossling_at_its_leash_limit_is_not_a_target_and_turns_on_a_hit_from_inside_its_ground() -> void:
	var host := _host()
	var e := _mossling(host, Vector2.ZERO)
	e.set_physics_process(false)
	# pulled to its leash limit (300 from home) by an archer who then stands 60 px beyond it
	_archer.position = Vector2(100, 0)
	e.hsm.update(0.016)
	e.global_position = Vector2(301, 0)
	_archer.position = Vector2(361, 0)
	e.hsm.update(0.016)
	assert_str(String(e.state)).is_equal("leash")
	e.take_hit(1, Vector2.LEFT)
	assert_int(e.hp).is_equal(3)                         # 361 from home: past leash 300 + its reach 51
	assert_str(String(e.state)).is_equal("leash")
	e.hsm.update(0.5)
	assert_float(e.velocity.x).is_less(0.0)              # still walking home
	# the same walk home, hit by an archer standing inside its ground: it turns round
	e.global_position = Vector2(200, 0)
	_archer.position = Vector2(200, 120)
	e.take_hit(1, Vector2.UP)
	assert_int(e.hp).is_equal(2)
	assert_str(String(e.state)).is_equal("chase")

func test_a_mossling_walks_home_round_a_solid_in_its_way() -> void:
	var host := _host()
	var e := _mossling(host, Vector2(0, 200))            # home
	_wall(host, Rect2(-48, 88, 96, 24))                  # a bench across the straight way home
	await _steps(2)
	_archer.position = Vector2(0, 60)
	await _steps(2)
	e.global_position = Vector2(0, 0)                    # north of the bench, dead on
	_archer.position = Vector2(5000, 5000)
	await _steps(2)
	assert_str(String(e.state)).is_equal("leash")
	await _steps(240)                                    # 4 s; main was still on the bench after 30 s
	assert_str(String(e.state)).is_equal("idle")
	assert_vector(e.global_position).is_equal(e.home)

func test_a_mossling_that_cannot_get_home_gives_up_and_is_put_there() -> void:
	var host := _host()
	var e := _mossling(host, Vector2(0, 250))
	for r: Rect2 in [Rect2(-60, -60, 120, 12), Rect2(-60, 48, 120, 12), Rect2(-60, -60, 12, 120), Rect2(48, -60, 12, 120)]:
		_wall(host, r)                                   # a closed pen
	await _steps(2)
	_archer.position = Vector2(0, 150)
	await _steps(2)
	e.global_position = Vector2(0, 0)                    # inside the pen
	_archer.position = Vector2(5000, 5000)
	await _steps(2)
	assert_str(String(e.state)).is_equal("leash")
	var budget := Enemy.LEASH_GIVE_UP + 2.0 * 250.0 / (e.speed * 1.3)
	await _steps(int((budget - 0.5) * 60.0))
	assert_str(String(e.state)).is_equal("leash")        # still trying
	await _steps(60)
	assert_str(String(e.state)).is_equal("idle")
	assert_vector(e.global_position).is_equal(e.home)

func test_a_mossling_does_not_notice_by_nearness_just_after_the_zone_is_ready_but_a_hit_wakes_it() -> void:
	var host := _host()
	var e := _mossling(host, Vector2.ZERO)
	var other := _mossling(host, Vector2(0, 900))
	for m: Enemy in [e, other]:
		m.set_physics_process(false)
	var zone: Zone = auto_free(Zone.new())
	Zones.zone_changed.emit(zone)                        # what a load, a door or getting up sends
	_archer.position = Vector2(100, 0)                   # well inside its aggro radius
	for i in 24:
		e._physics_process(0.1)                          # 2.4 s
	assert_str(String(e.state)).is_equal("idle")
	for i in 2:
		e._physics_process(0.1)
	assert_str(String(e.state)).is_equal("chase")        # 2.5 s after the zone was ready
	_archer.position = Vector2(100, 900)
	other.take_hit(1, Vector2.RIGHT)
	assert_str(String(other.state)).is_equal("chase")    # a hit does not wait for the grace

# --- the Undercroft's creatures -------------------------------------------------------------------------

func test_a_creature_is_whole_three_seconds_after_it_is_home_and_not_before() -> void:
	var host := _host()
	var e := _creature(host, Vector2.ZERO, "shield")
	e.set_physics_process(false)
	_archer.position = Vector2(200, 0)
	e.step(0.01)
	assert_str(e.state).is_equal("approach")
	e.take_hit(3, Vector2.RIGHT)                         # from behind its facing: full damage
	assert_int(e.hp).is_equal(5)
	e.global_position = Vector2(150, 0)
	_archer.position = Vector2(5000, 5000)               # the target leaves its leash
	e.step(0.01)
	assert_str(e.state).is_equal("leash")
	e.step(0.5)
	assert_int(e.hp).is_equal(5)
	e.global_position = e.home
	e.step(0.01)
	assert_str(e.state).is_equal("idle")
	e.step(SliceEnemy.HOME_HEAL_TIME - 0.1)
	assert_int(e.hp).is_equal(5)
	e.step(0.2)
	assert_int(e.hp).is_equal(8)

func test_a_hit_wakes_an_idle_creature_and_its_near_mates_and_glances_from_out_of_reach() -> void:
	var host := _host()
	var a := _creature(host, Vector2.ZERO)
	var b := _creature(host, Vector2(200, 0), "shooter")
	var far := _creature(host, Vector2(0, 600), "elite")
	for e: SliceEnemy in [a, b, far]:
		e.set_physics_process(false)
	var glances := [0]
	a.glanced.connect(func() -> void: glances[0] += 1)
	# beyond 330: the arrow reaches (its range is about 400) but does no harm and wakes nobody
	_archer.position = Vector2(-340, 0)
	a.take_hit(1, Vector2.RIGHT)
	assert_int(a.hp).is_equal(4)
	assert_str(a.state).is_equal("idle")
	assert_int(glances[0]).is_equal(1)
	# inside 330 and outside the 300 at which it notices by itself: the hit lands and the camp answers
	_archer.position = Vector2(-320, 0)
	a.step(0.01)
	assert_str(a.state).is_equal("idle")
	a.take_hit(1, Vector2.RIGHT)
	assert_int(a.hp).is_equal(3)
	assert_str(a.state).is_equal("approach")
	assert_str(b.state).is_equal("idle")                 # b is 520 from the archer: it cannot come from idle
	_archer.position = Vector2(100, 100)
	var c := _creature(host, Vector2(0, 40))
	c.set_physics_process(false)
	a.hsm.dispatch(&"idle")
	a.take_hit(1, Vector2.RIGHT)
	assert_str(c.state).is_equal("approach")             # a mate in earshot wakes with it
	assert_str(far.state).is_equal("idle")
	# walking home because the archer left its leash: no harm from out there
	_archer.position = Vector2(SliceEnemy.LEASH + 40.0, 0)
	a.global_position = Vector2(SliceEnemy.LEASH - 20.0, 0)
	a.step(0.01)
	assert_str(a.state).is_equal("leash")
	var hp := a.hp
	a.take_hit(1, Vector2.LEFT)
	assert_int(a.hp).is_equal(hp)
	assert_str(a.state).is_equal("leash")
	for e: SliceEnemy in [a, b, c, far]:
		e._cancel_attack()

func test_a_creature_gives_the_player_a_moment_after_the_zone_is_ready() -> void:
	var host := _host()
	var e := _creature(host, Vector2.ZERO)
	e.set_physics_process(false)
	var zone: Zone = auto_free(Zone.new())
	Zones.zone_changed.emit(zone)
	_archer.position = Vector2(193, 0)                   # the Undercroft's start is 193 from its first rusher
	e.step(SliceEnemy.ARRIVAL_GRACE - 0.1)
	assert_str(e.state).is_equal("idle")
	e.step(0.2)
	assert_str(e.state).is_equal("approach")
	e._cancel_attack()

func test_a_creature_walks_home_round_a_solid_in_its_way() -> void:
	var host := _host()
	var e := _creature(host, Vector2(0, 200))
	_wall(host, Rect2(-48, 88, 96, 24))
	await _steps(2)
	e.global_position = Vector2(0, 0)
	e.hsm.dispatch(&"leash")
	await _steps(300)                                    # 5 s at 144 px a second
	assert_str(e.state).is_equal("idle")
	assert_vector(e.global_position).is_equal(e.home)

# --- finite effects and reduced motion ------------------------------------------------------------------

func test_giving_up_the_walk_fades_in_at_home_and_is_instant_under_reduced_motion() -> void:
	var host := _host()
	for reduced: bool in [false, true]:
		SaveGame.data.settings.reduced_motion = reduced
		var e := _mossling(host, Vector2(0, 300 if reduced else 0))
		e.set_physics_process(false)
		e.global_position += Vector2(200, 0)
		e.hsm.dispatch(&"aggro")
		e.hsm.update(0.016)                              # the target is far: it turns for home
		assert_str(String(e.state)).is_equal("leash")
		e._leash_t = e._leash_budget                     # the walk has taken as long as it may
		e.hsm.update(0.016)
		assert_str(String(e.state)).is_equal("idle")
		assert_vector(e.global_position).is_equal(e.home)
		if reduced:
			assert_float(e._fade).is_equal(0.0)
		else:
			assert_float(e._fade).is_equal(Enemy.HOP_FADE)
			for i in 30:
				e._physics_process(0.02)                 # the fade is finite: over after HOP_FADE
			assert_float(e._fade).is_equal(0.0)
			assert_float(e.sprite.modulate.a).is_equal(1.0)
	SaveGame.data.settings.reduced_motion = false

func test_the_glance_mark_is_finite() -> void:
	var host := _host()
	var e := _mossling(host, Vector2.ZERO)
	e.set_physics_process(false)
	_archer.position = Vector2(-400, 0)
	e.take_hit(1, Vector2.RIGHT)
	assert_float(e.glance_t).is_equal(Glance.TIME)
	for i in 20:
		e._physics_process(0.02)
	assert_float(e.glance_t).is_equal(0.0)

func test_a_creature_that_cannot_get_home_gives_up_and_is_put_there() -> void:
	var host := _host()
	var e := _creature(host, Vector2.ZERO)
	e.set_physics_process(false)
	e.global_position = Vector2(300, 0)
	e.hsm.dispatch(&"leash")
	e.step(0.016)
	assert_str(e.state).is_equal("leash")
	e.step(SliceEnemy.LEASH_GIVE_UP + 2.0 * 300.0 / SliceEnemy.LEASH_SPEED - 0.1)   # it never moves here: physics is off
	assert_str(e.state).is_equal("leash")
	e.step(0.2)
	assert_str(e.state).is_equal("idle")
	assert_vector(e.global_position).is_equal(e.home)

# --- 11 Nov, after the audit of #468 ---------------------------------------------------------------------

## The numbers themselves (the tests above read the constants; these pin them).
func test_the_approved_numbers_are_three_seconds_at_home_330_to_wake_and_a_grace_of_two_and_a_half() -> void:
	assert_float(Enemy.HOME_HEAL_TIME).is_equal(3.0)
	assert_float(SliceEnemy.HOME_HEAL_TIME).is_equal(3.0)
	assert_float(Enemy.ARRIVAL_GRACE).is_equal(2.5)
	assert_float(SliceEnemy.ARRIVAL_GRACE).is_equal(2.5)
	assert_float(SliceEnemy.WAKE).is_equal(330.0)
	var host := _host()
	var e := _mossling(host, Vector2.ZERO)
	var c := _creature(host, Vector2(900, 0))
	assert_float(e.wake_radius).is_equal(330.0)
	# a wall met at any angle is slid along (the engine's default refuses under 15 degrees)
	assert_float(e.wall_min_slide_angle).is_equal(0.0)
	assert_float(c.wall_min_slide_angle).is_equal(0.0)

## Played by the audit: a mossling's lunge hit a player standing 354 px from its home, and their arrows
## glanced off it at 24 px and at 9 px. Whoever it strikes at can strike back.
func test_a_mossling_that_winds_up_lunges_or_recovers_can_always_be_hurt() -> void:
	var host := _host()
	var e := _mossling(host, Vector2.ZERO)
	e.set_physics_process(false)
	_archer.position = Vector2(100, 0)
	e.hsm.update(0.016)
	e.global_position = Vector2(299, 0)                  # just inside its leash
	_archer.position = Vector2(345, 0)                   # within its 51 px reach: it winds up
	e.hsm.update(0.016)
	assert_str(String(e.state)).is_equal("windup")
	_archer.position = Vector2(360, 0)                   # off its ground now (past 351 from home)
	e.take_hit(1, Vector2.LEFT)
	assert_int(e.hp).is_equal(2)
	e.hsm.update(Enemy.WINDUP_TIME + 0.01)
	assert_str(String(e.state)).is_equal("lunge")
	e.global_position = Vector2(370, 0)
	e.take_hit(1, Vector2.LEFT)
	assert_int(e.hp).is_equal(1)
	e.hsm.update(Enemy.LUNGE_TIME + 0.01)
	assert_str(String(e.state)).is_equal("recover")
	e.max_hp = 9
	e.hp = 9
	e.take_hit(1, Vector2.LEFT)
	assert_int(e.hp).is_equal(8)
	e.hsm.update(Enemy.RECOVER_TIME + 0.01)              # and once it turns for home it is out of it again
	assert_str(String(e.state)).is_equal("leash")
	e.take_hit(1, Vector2.LEFT)
	assert_int(e.hp).is_equal(8)

func test_a_camp_mate_whose_ground_the_archer_is_not_on_stays_asleep() -> void:
	var host := _host()
	var a := _mossling(host, Vector2.ZERO)
	var b := _mossling(host, Vector2(100, 0))            # in earshot; the archer is 420 from its home
	for e: Enemy in [a, b]:
		e.set_physics_process(false)
	_archer.position = Vector2(-320, 0)
	a.take_hit(1, Vector2.RIGHT)
	assert_str(String(a.state)).is_equal("chase")
	assert_str(String(b.state)).is_equal("idle")

func test_a_creature_hit_on_its_walk_home_by_someone_inside_its_leash_turns_round() -> void:
	var host := _host()
	var e := _creature(host, Vector2.ZERO)
	e.set_physics_process(false)
	e.global_position = Vector2(200, 0)
	e.hsm.dispatch(&"leash")
	assert_str(e.state).is_equal("leash")
	_archer.position = Vector2(200, 150)
	e.take_hit(1, Vector2.UP)
	assert_int(e.hp).is_equal(3)
	assert_str(e.state).is_equal("approach")
	e._cancel_attack()

func test_the_chase_goes_round_a_solid_for_a_mossling_and_a_creature() -> void:
	var host := _host()
	_wall(host, Rect2(-48, 88, 96, 24))
	var m := _mossling(host, Vector2(0, 0))
	var c := _creature(host, Vector2(0, 20))
	await _steps(2)
	_archer.position = Vector2(0, 200)                   # straight through the bench
	m.take_hit(0, Vector2.DOWN, 0.0)                     # wakes both (one camp)
	await _steps(240)
	assert_float(m.global_position.y).is_greater(112.0)  # past the bench: on main's movement both stay north of it
	assert_float(c.global_position.y).is_greater(112.0)
	c._cancel_attack()

## Played by the audit: shot from (600, 1720), two mosslings ran into the pocket at (610, 1570) between two
## solids and stayed there in `chase` for the rest of the run. A chase that gains no ground is given up.
func test_a_chase_that_gains_no_ground_is_given_up_and_the_mossling_goes_home() -> void:
	var host := _host()
	var e := _mossling(host, Vector2(0, 0))
	# a pocket open to the north (towards home), closed towards the archer
	for r: Rect2 in [Rect2(-60, 248, 120, 12), Rect2(-60, 140, 12, 120), Rect2(48, 140, 12, 120)]:
		_wall(host, r)
	await _steps(2)
	_archer.position = Vector2(0, 320)
	e.take_hit(1, Vector2.DOWN, 0.0)
	assert_str(String(e.state)).is_equal("chase")
	await _steps(int((200.0 / (e.speed * Enemy.RUN_IN) + Enemy.CHASE_GIVE_UP - 0.4) * 60.0))
	assert_str(String(e.state)).is_equal("chase")        # in the pocket, still trying
	await _steps(60)
	assert_str(String(e.state)).is_not_equal("chase")    # given up
	var hp := e.hp
	e.take_hit(1, Vector2.DOWN, 0.0)                     # no way to this archer: no harm, no waking
	assert_int(e.hp).is_equal(hp)
	await _steps(240)
	assert_str(String(e.state)).is_equal("idle")
	assert_vector(e.global_position).is_equal(e.home)
	await _steps(int(Enemy.NO_WAY_TIME * 60.0))          # later it answers a shot again
	e.take_hit(1, Vector2.DOWN, 0.0)
	assert_int(e.hp).is_less(e.max_hp)

func test_the_real_pocket_at_610_1570_in_the_woodland_does_not_hold_the_camp() -> void:
	var root: Node2D = auto_free(Node2D.new())
	add_child(root)
	var player: Player = auto_free(load("res://actors/player.tscn").instantiate())
	player.input_enabled = false
	SaveGame.reset()
	Zones.current = null
	Zones.attach(root, player)
	assert_bool(Zones.go_to("woodland", "start")).is_true()
	player.global_position = Vector2(600, 1720)
	player.set_physics_process(false)
	await _steps(3)
	var camp := Zones.current.get_node("Actors/MeadowCamp")
	var first := camp.get_node("Mossling1") as Enemy
	first.take_hit(1, Vector2.UP, 0.0)
	assert_str(String(first.state)).is_equal("chase")
	await _steps(600)                                    # 10 s: on 89445b6a two were still circling at (610, 1570)
	for m in camp.get_children():
		if m is Enemy and not (m as Enemy).dead:
			var e := m as Enemy
			var held := e.state == &"chase" and e.global_position.distance_to(Vector2(610, 1570)) < 60.0
			assert_bool(held).override_failure_message("%s still in the pocket at %s" % [e.name, e.global_position]).is_false()
	Zones.current.queue_free()
	Zones.current = null
	SaveGame.reset()

func test_a_creature_whose_approach_gains_no_ground_goes_home() -> void:
	var host := _host()
	var e := _creature(host, Vector2.ZERO)
	e.set_physics_process(false)                         # it cannot move: no ground gained
	_archer.position = Vector2(250, 0)
	e.step(0.016)
	assert_str(e.state).is_equal("approach")
	for i in 24:
		e.step(0.1)                                      # 2.4 s without a px gained
	assert_str(e.state).is_equal("approach")
	for i in 3:
		e.step(0.1)
	assert_str(e.state).is_equal("idle")                 # given up; it was at home already
	e.take_hit(1, Vector2.LEFT)
	assert_str(e.state).is_equal("idle")
	assert_int(e.hp).is_equal(4)                         # no harm while it has no way
	e._cancel_attack()

## The proposal of 11 Nov: woken by a shot, a mossling and a rusher run in 1.6 times as fast until their
## first wind-up. Walking up to them starts the fight at the old pace.
func test_woken_by_a_shot_it_runs_in_faster_until_its_first_wind_up() -> void:
	assert_float(Enemy.RUN_IN).is_equal(1.6)
	assert_float(SliceEnemy.RUN_IN).is_equal(1.6)
	var host := _host()
	var shot := _mossling(host, Vector2.ZERO)
	var near := _mossling(host, Vector2(0, 2000))
	var rusher := _creature(host, Vector2(0, 4000))
	var shield := _creature(host, Vector2(0, 6000), "shield")
	for n: Node in [shot, near, rusher, shield]:
		n.set_physics_process(false)
	_archer.position = Vector2(300, 0)
	shot.take_hit(1, Vector2.LEFT, 0.0)
	shot._stagger = 0.0
	shot.hsm.update(0.016)
	assert_float(shot.velocity.length()).is_equal_approx(117.0 * 1.6, 0.5)
	shot.global_position = Vector2(260, 0)
	shot.hsm.update(0.016)                               # in reach: the wind-up ends the run
	assert_str(String(shot.state)).is_equal("windup")
	shot.hsm.update(Enemy.WINDUP_TIME + 0.01)
	shot.hsm.update(Enemy.LUNGE_TIME + 0.01)
	_archer.position = Vector2(0, 0)
	shot.hsm.update(Enemy.RECOVER_TIME + 0.01)
	shot.hsm.update(0.016)
	assert_float(shot.velocity.length()).is_equal_approx(117.0, 0.5)
	# noticed by nearness: the old pace
	_archer.position = Vector2(150, 2000)
	near.hsm.update(0.016)
	near.hsm.update(0.016)
	assert_str(String(near.state)).is_equal("chase")
	assert_float(near.velocity.length()).is_equal_approx(117.0, 0.5)
	# the rusher runs in; the shield bearer does not
	_archer.position = Vector2(320, 4000)
	rusher.take_hit(1, Vector2.LEFT)
	rusher.step(0.016)
	assert_float(rusher.velocity.length()).is_equal_approx(102.0 * 1.6, 0.5)
	_archer.position = Vector2(320, 6000)
	shield.take_hit(1, Vector2.LEFT)
	shield.step(0.016)
	assert_float(shield.velocity.length()).is_equal_approx(102.0, 0.5)
	rusher._cancel_attack()
	shield._cancel_attack()
