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

class Nudged extends Node:
	var count := 0
	func nudge(_d: Vector2) -> void:
		count += 1

func test_charge_commit_glints_and_nudges_the_camera_once() -> void:
	var boss := _boss()
	var cam: Nudged = auto_free(Nudged.new())
	cam.add_to_group("camera_nudge")
	add_child(cam)
	_target.position = Vector2(400, 0)
	boss._next = 0
	assert_str(_to_windup(boss)).is_equal("charge")
	assert_float(boss.windup_time).is_greater_equal(Thornback.MIN_WINDUP)
	boss.step(boss.windup_time - 0.01)
	assert_float(boss._flash).is_equal(0.0)
	assert_int(cam.count).is_equal(0)
	boss.step(0.02)
	assert_str(boss.state).is_equal("act")
	assert_float(boss._flash).is_greater(0.0)
	assert_int(cam.count).is_equal(1)
	boss.step(Thornback.FLASH_TIME + 0.01)
	assert_float(boss._flash).is_equal(0.0)

## Plays `count` attacks against a target handled by `between` (called before each wind-up is sought) and
## returns [attack name, seconds since the start] for each.
func _attacks(boss: Thornback, count: int, between: Callable) -> Array:
	var out := []
	var t := 0.0
	for i in count:
		for j in 80:
			between.call(t)
			boss.step(0.05)
			t += 0.05
			if boss.state == "windup":
				break
		out.append([boss.attack, t])
		boss.step(boss.windup_time + 0.01)
		t += boss.windup_time + 0.01
		boss._finish_attack(0.1)
		for th in boss.thorns:
			th.finish()
		boss.thorns.clear()
		boss.step(0.15)
		t += 0.15
	return out

## 10 Nov: close in (under 83) every charge became a volley, whose thorns start 60 px out and fly outward:
## a player standing beside it was never hit in phase 1 (73 s and 100 s in play). Staying close in for
## CLING_TIME now brings the charge there too.
func test_a_player_who_stays_close_in_is_charged() -> void:
	var boss := _boss()
	_target.position = Vector2(27, 0)            # where the play-test stood untouched
	var seen := _attacks(boss, 6, func(_t: float) -> void: pass)
	var charges := seen.filter(func(a: Array) -> bool: return a[0] == "charge")
	assert_int(charges.size()).is_greater_equal(2)
	assert_float(float(charges[0][1])).is_greater_equal(Thornback.CLING_TIME)   # not in the first 2 s close in
	assert_float(float(charges[0][1])).is_less(10.0)                           # and within about 10 s
	assert_str(str(seen[0][0])).is_equal("volley")                              # the first answer close in is still the volley

## Small steps do not reset the count (a step every two seconds would otherwise keep the volley for good).
func test_shuffling_about_close_in_is_charged_too() -> void:
	var boss := _boss()
	var spots := [Vector2(40, 0), Vector2(0, 45), Vector2(-40, 0), Vector2(0, -45)]
	var seen := _attacks(boss, 6, func(t: float) -> void: _target.position = spots[int(t / 0.8) % 4])
	assert_bool(seen.any(func(a: Array) -> bool: return a[0] == "charge")).is_true()

func test_a_player_who_only_passes_close_by_still_gets_the_volley() -> void:
	var boss := _boss()
	# in for a second and a half, out to 90 for half a second, again and again
	var t := 0.0
	while t < 12.0:
		_target.position = Vector2(40, 0) if fmod(t, 2.0) < 1.5 else Vector2(90, 0)
		boss.step(0.05)
		t += 0.05
		assert_bool(boss.player_clings()).is_false()
	boss._next = 0                               # the charge's turn
	assert_str(boss.choose_attack(40.0)).is_equal("volley")
	boss._close_t = Thornback.CLING_TIME
	assert_str(boss.choose_attack(40.0)).is_equal("charge")
	for th in boss.thorns:
		th.finish()

## A charge used to end the moment the body touched any solid. Leaning on a wall when it committed, it
## staggered before the strike had its turn, and a wall behind or beside it stopped it too.
func test_a_charge_ends_on_a_solid_in_its_way_and_only_after_its_strike() -> void:
	var boss := _boss(Vector2(0, 0))
	var wall := StaticBody2D.new()
	var shape := CollisionShape2D.new()
	var box := RectangleShape2D.new()
	box.size = Vector2(400, 40)
	shape.shape = box
	wall.add_child(shape)
	wall.position = Vector2(0, -18.0 - Thornback.BODY_RADIUS - 20.0)   # its body touches the wall's south face
	add_child(auto_free(wall))
	_target.max_hp = 99
	_target.hp = 99
	_target.position = Vector2(0, -50)           # between it and the wall, inside its body's reach
	boss.set_physics_process(true)
	var staggers := [0]
	boss.staggered.connect(func() -> void: staggers[0] += 1)
	boss._next = 0
	boss._close_t = Thornback.CLING_TIME          # it has been clung to
	for i in 200:
		await get_tree().physics_frame
		if boss.state == "stagger":
			break
	assert_str(boss.state).is_equal("stagger")
	assert_int(staggers[0]).is_equal(1)
	assert_int(_target.hp).is_equal(97)           # the charge struck (2) before the wall ended it
	# a charge along the wall is not ended by the wall it runs beside
	boss.hsm.dispatch(&"approach")
	_target.position = Vector2(400, -18)
	boss._next = 0
	for i in 200:
		await get_tree().physics_frame
		if boss.state == "act":
			break
	assert_str(boss.attack).is_equal("charge")
	for i in 12:
		await get_tree().physics_frame
	assert_str(boss.state).is_equal("act")
	assert_float(boss.global_position.x).is_greater(40.0)

## The arena rect stops short of the chamber's walls. A player in the strip under the north, east or
## south wall was "outside": the boss went to sleep and took every arrow. The strips now count as inside;
## the west edge (the door) stays exact.
func test_the_wall_strips_count_as_the_arena_but_the_door_side_does_not() -> void:
	var boss := _boss(Vector2(300, 250))
	boss.arena = Rect2(100, 100, 400, 300)
	for p: Vector2 in [Vector2(300, 88), Vector2(515, 250), Vector2(300, 410)]:
		_target.position = p
		assert_bool(boss.player_in_arena()).override_failure_message("%s should count as the arena" % p).is_true()
	_target.position = Vector2(94, 250)          # west of it: the door side
	assert_bool(boss.player_in_arena()).is_false()
	_target.position = Vector2(300, 60)          # beyond the strip
	assert_bool(boss.player_in_arena()).is_false()

## From outside the arena it cannot come for the archer, so it cannot be hurt from there (on main 41 arrows
## through the open seal freed it asleep in 32 s).
func test_no_harm_from_outside_the_arena() -> void:
	var boss := _boss(Vector2(300, 250))
	boss.arena = Rect2(100, 100, 400, 300)
	var glances := [0]
	boss.glanced.connect(func() -> void: glances[0] += 1)
	_target.position = Vector2(94, 250)
	boss.step(0.05)
	assert_str(boss.state).is_equal("dormant")
	boss.take_hit(5, Vector2.RIGHT)
	assert_int(boss.hp).is_equal(Thornback.MAX_HP)
	assert_str(boss.state).is_equal("dormant")
	assert_int(glances[0]).is_equal(1)
	_target.position = Vector2(140, 250)         # one step in: the same arrow lands and it wakes
	boss.take_hit(5, Vector2.RIGHT)
	assert_int(boss.hp).is_equal(Thornback.MAX_HP - 5)
	assert_str(boss.state).is_equal("approach")

## Whoever it strikes at can strike back: the glance is only for a boss that sleeps or walks about.
func test_while_it_attacks_it_can_be_hurt_from_outside_the_arena() -> void:
	var boss := _boss(Vector2(300, 250))
	boss.arena = Rect2(100, 100, 400, 300)
	_target.position = Vector2(140, 250)
	assert_str(_to_windup(boss)).is_not_empty()
	_target.position = Vector2(60, 250)          # stepped out during the wind-up
	boss.take_hit(1, Vector2.RIGHT)
	assert_int(boss.hp).is_equal(Thornback.MAX_HP - 1)
	boss._stagger(1.0)
	boss.take_hit(1, Vector2.RIGHT)
	assert_int(boss.hp).is_equal(Thornback.MAX_HP - 3)   # the stagger's double damage too
	boss._finish_attack(0.0)
	boss.hsm.dispatch(&"approach")
	boss.step(0.016)                             # nobody in the arena: back to sleep
	assert_str(boss.state).is_equal("dormant")
	boss.take_hit(1, Vector2.RIGHT)
	assert_int(boss.hp).is_equal(Thornback.MAX_HP - 3)

## The audit's corner (11 Nov): in the real chamber, standing still at (2220, 181) north of the rubble, every
## charge ended on the rubble with the stagger, 103 to 126 px short, and the Thornback was shot down in 23 s
## without a heart lost. A charge now goes through rubble and stumps and is stopped by walls and the arena's
## edge only, so it reaches the corner; the same behind the south-east stump.
func test_in_the_real_chamber_the_charge_reaches_the_corners_behind_the_rubble_and_the_stump() -> void:
	for spot: Vector2 in [Vector2(2220, 181), Vector2(2208, 590)]:
		SaveGame.reset()
		for f: String in ["camp_cleared:undercroft_rooms", "undercroft_plate", "undercroft_seal_open"]:
			SaveGame.set_flag(f)
		var root: Node2D = auto_free(Node2D.new())
		add_child(root)
		var player: Player = auto_free(load("res://actors/player.tscn").instantiate())
		player.input_enabled = false
		Zones.current = null
		Zones.attach(root, player)
		assert_bool(Zones.go_to("undercroft", "arena")).is_true()
		player.global_position = spot
		var boss := get_tree().get_first_node_in_group("thornback_live") as Thornback
		var staggers_before_a_hit := [0]
		boss.staggered.connect(func() -> void:
			if player.hp == player.max_hp:
				staggers_before_a_hit[0] += 1)
		var frames := 0
		while player.hp == player.max_hp and frames < 900:   # 15 s
			await get_tree().physics_frame
			frames += 1
			player.global_position = spot if player.hp == player.max_hp else player.global_position
		assert_int(player.hp).override_failure_message("standing still at %s: not hit in 15 s" % spot).is_less(player.max_hp)
		assert_int(staggers_before_a_hit[0]).override_failure_message("at %s it staggered %d times before it ever struck" % [spot, staggers_before_a_hit[0]]).is_equal(0)
		assert_bool(boss.arena.grow(1.0).has_point(boss.global_position)).is_true()
		root.remove_child(Zones.current)
		Zones.current.free()
		Zones.current = null
	SaveGame.reset()

## Part D: a thorn flies over a low solid (a stump, rubble on layer 5) and is stopped by a wall.
func test_a_thorn_flies_over_a_low_solid_and_stops_at_a_wall() -> void:
	var th: ThornbackThorn = auto_free(ThornbackThorn.new())
	add_child(th)
	var low: StaticBody2D = auto_free(StaticBody2D.new())
	low.collision_layer = Arrow.WALLS | Arrow.LOW
	var wall: StaticBody2D = auto_free(StaticBody2D.new())
	th._on_body(low)
	assert_bool(th.finished).is_false()
	th._on_body(wall)
	assert_bool(th.finished).is_true()
