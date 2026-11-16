extends GdUnitTestSuite
## Where a shot stops (actors/impact.gd; Matt, 16 Nov: "projectiles should more visibly hit things on
## impact"): the mark is at the contact, is the right kind, frees itself within its lifetime, holds the world
## only on a hit that counted and never under reduced motion, and changes no number of the fight.

var _reduced := false

func before_test() -> void:
	_reduced = bool(SaveGame.data.settings.reduced_motion)
	SaveGame.data.settings.reduced_motion = false

func after_test() -> void:
	SaveGame.data.settings.reduced_motion = _reduced
	Engine.time_scale = 1.0

func _stage() -> Node2D:
	var root: Node2D = auto_free(Node2D.new())
	add_child(root)
	return root

func _archer(root: Node2D, at: Vector2) -> Node2D:
	var a := Node2D.new()
	a.add_to_group("player")
	a.position = at
	root.add_child(a)
	return a

func _wall(root: Node2D, x0: float, y0: float, x1: float, y1: float) -> StaticBody2D:
	var body := StaticBody2D.new()
	body.collision_layer = 1
	body.collision_mask = 0
	var shape := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(x1 - x0, y1 - y0)
	shape.shape = rect
	body.add_child(shape)
	body.position = Vector2((x0 + x1) / 2.0, (y0 + y1) / 2.0)
	root.add_child(body)
	return body

func _loose(root: Node2D, at: Vector2, archer: Node2D, dir := Vector2.RIGHT) -> Arrow:
	var arrow := Arrow.new()
	root.add_child(arrow)
	arrow.setup(at, 20.0, dir, archer)
	return arrow

func _settle() -> void:
	await get_tree().physics_frame
	await get_tree().physics_frame

func _impacts(root: Node) -> Array[Impact]:
	var out: Array[Impact] = []
	for n in root.get_children():
		if n is Impact and not n.is_queued_for_deletion():
			out.append(n)
	return out

## Flies the arrow until it is gone; returns the last place it was seen.
func _fly(arrow: Arrow, frames := 60) -> Vector2:
	var last := arrow.global_position
	for i in frames:
		await get_tree().physics_frame
		if not is_instance_valid(arrow):
			break
		last = arrow.global_position
	return last

## Runs an effect's own clock by hand: returns the seconds it took to free itself (INF if it did not).
func _run_out(fx: Impact, step := 1.0 / 60.0, limit := 3.0) -> float:
	fx.set_process(false)
	var t := 0.0
	while t < limit:
		fx._process(step)
		t += step
		if fx.is_queued_for_deletion():
			return t
	return INF

func test_an_arrow_that_hurts_a_creature_leaves_a_star_and_sticks_where_it_struck() -> void:
	var root := _stage()
	var archer := _archer(root, Vector2(100, 100))
	var foe: Enemy = load("res://actors/enemy.tscn").instantiate()
	foe.position = Vector2(200, 100)
	root.add_child(foe)
	await _settle()
	foe.set_physics_process(false)             # it stays where it is, so the mark stays at the contact
	var hp := foe.hp
	var arrow := _loose(root, Vector2(126, 100), archer)
	var last := await _fly(arrow)
	assert_bool(is_instance_valid(arrow)).is_false()   # the arrow itself still goes the moment it stops
	assert_int(foe.hp).is_equal(hp - 1)
	var fx := _impacts(root)
	assert_int(fx.size()).is_equal(1)
	var hit := fx[0]
	assert_int(hit.kind).is_equal(Impact.Kind.HIT)
	assert_bool(hit.shaft).is_true()
	assert_object(hit.follow).is_same(foe)
	# on the creature's drawn body (the placeholder's frame middle: 30 texels tall from 30 up), not in the air
	assert_float(hit.lift).is_equal(minf(20.0, 15.0))
	# at the contact: where the arrow was when it met the creature (one physics step of flight at most)
	assert_float(hit.global_position.distance_to(last)).is_less_equal(Arrow.SPEED / 60.0 + 1.0)
	assert_float(hit.global_position.distance_to(foe.global_position)).is_less(40.0)
	assert_float(hit.global_position.x).is_less(foe.global_position.x)
	assert_int(hit.z_index).is_equal(0)                       # the stuck arrow y-sorts with the creature
	assert_int((hit.get_node("Burst") as Node2D).z_index).is_equal(1)   # the star is drawn over (0.2 s)
	assert_bool(hit.burst_on_ground()).is_false()
	# it frees itself within its lifetime
	var gone := _run_out(hit)
	assert_float(gone).is_less_equal(hit.lifetime() + 1.0 / 60.0 + 0.0001)
	assert_float(hit.lifetime()).is_equal_approx(Impact.STUCK + Impact.FADE, 0.0001)

func test_the_star_has_four_drawings_and_the_stuck_arrow_rides_on_the_creature() -> void:
	var root := _stage()
	var foe := Node2D.new()
	root.add_child(foe)
	foe.position = Vector2(50, 50)
	var hit := Impact.spawn(root, Impact.Kind.HIT, Vector2(40, 50), 20.0, Vector2.RIGHT, true, foe)
	hit.set_process(false)
	var frames: Array[int] = []
	hit._process(Impact.FRAME / 4.0)                   # sampled a quarter and three quarters into each drawing
	for i in 8:
		frames.append(hit.burst_frame())
		hit._process(Impact.FRAME / 2.0)
	assert_array(frames).is_equal([0, 0, 1, 1, 2, 2, 3, 3])
	assert_int(hit.burst_frame()).is_equal(-1)          # the star is over by 0.2 s
	foe.position += Vector2(6, 0)                     # knocked
	hit._process(0.01)
	assert_vector(hit.global_position).is_equal(Vector2(46, 50))

func test_reduced_motion_holds_nothing_and_shows_one_still_drawing() -> void:
	SaveGame.data.settings.reduced_motion = true
	assert_bool(Impact.hit_stop(get_tree())).is_false()
	assert_float(Engine.time_scale).is_equal(1.0)
	var root := _stage()
	var hit := Impact.spawn(root, Impact.Kind.HIT, Vector2(40, 50), 20.0, Vector2.RIGHT, true)
	assert_bool(hit.reduced).is_true()
	hit.set_process(false)
	var seen := {}
	var t := 0.0
	while not hit.is_queued_for_deletion():
		seen[hit.burst_frame()] = true
		hit._process(1.0 / 60.0)
		t += 1.0 / 60.0
	assert_array(seen.keys()).contains_exactly_in_any_order([1, -1])   # one still drawing, then none
	assert_float(t).is_less_equal(Impact.STUCK + 1.0 / 60.0 + 0.0001)  # no fade
	for kind: Impact.Kind in [Impact.Kind.CLINK, Impact.Kind.WALL, Impact.Kind.DROP, Impact.Kind.SPLAT]:
		assert_float(Impact.lifetime_of(kind, true)).is_less_equal(Impact.STUCK)

func test_reduced_motion_skips_the_hit_stop_of_an_arrow_that_counts() -> void:
	SaveGame.data.settings.reduced_motion = true
	var root := _stage()
	var archer := _archer(root, Vector2(100, 100))
	var foe: Enemy = load("res://actors/enemy.tscn").instantiate()
	foe.position = Vector2(200, 100)
	root.add_child(foe)
	await _settle()
	var scales: Array[float] = []
	var arrow := _loose(root, Vector2(126, 100), archer)
	for i in 40:
		await get_tree().physics_frame
		scales.append(Engine.time_scale)
	assert_bool(is_instance_valid(arrow)).is_false()
	assert_int(foe.hp).is_equal(foe.max_hp - 1)
	assert_float(scales.min()).is_equal(1.0)

func test_a_hit_that_counts_holds_the_world_for_a_moment_and_lets_it_go() -> void:
	assert_bool(Impact.hit_stop(get_tree())).is_true()
	assert_float(Engine.time_scale).is_equal(Impact.HOLD_SCALE)
	assert_bool(Impact.hit_stop(get_tree())).is_false()   # one hold at a time
	var start := Time.get_ticks_msec()
	while Engine.time_scale < 1.0 and Time.get_ticks_msec() - start < 1000:
		await get_tree().process_frame
	var held := Time.get_ticks_msec() - start
	assert_float(Engine.time_scale).is_equal(1.0)
	assert_int(held).is_between(int(Impact.HIT_STOP * 1000.0) - 20, int(Impact.HIT_STOP * 1000.0) + 120)

func test_an_arrow_that_glances_off_leaves_steel_streaks_and_no_hold() -> void:
	var root := _stage()
	var archer := _archer(root, Vector2(-300, 100))   # 500 from the creature: beyond its wake radius
	var foe: Enemy = load("res://actors/enemy.tscn").instantiate()
	foe.position = Vector2(200, 100)
	root.add_child(foe)
	await _settle()
	foe.set_physics_process(false)
	var scales: Array[float] = []
	var arrow := _loose(root, Vector2(126, 100), archer)
	for i in 40:
		await get_tree().physics_frame
		scales.append(Engine.time_scale)
		if not is_instance_valid(arrow):
			break
	assert_bool(is_instance_valid(arrow)).is_false()
	assert_int(foe.hp).is_equal(foe.max_hp)                # it glanced off
	assert_float(foe.glance_t).is_greater(0.0)
	var fx := _impacts(root)
	assert_int(fx.size()).is_equal(1)
	assert_int(fx[0].kind).is_equal(Impact.Kind.CLINK)
	assert_float(scales.min()).is_equal(1.0)
	assert_float(_run_out(fx[0])).is_less_equal(Impact.lifetime_of(Impact.Kind.CLINK, false) + 1.0 / 60.0 + 0.0001)

## #509 round 1, F1: a prop has only a box at its foot (woodland_birch: 21 x 12 world px), so an arrow that meets
## it has nothing drawn to stick in at its height. It falls to the prop's foot, knocked back off it.
func test_a_prop_with_only_a_foot_box_drops_the_arrow_at_its_foot() -> void:
	var root := _stage()
	var archer := _archer(root, Vector2(100, 100))
	_wall(root, 160, 94, 181, 106)                 # a birch's foot box, no face
	await _settle()
	var last := await _fly(_loose(root, Vector2(126, 100), archer))
	var fx := _impacts(root)
	assert_int(fx.size()).is_equal(1)
	assert_int(fx[0].kind).is_equal(Impact.Kind.DROP)   # no stuck shaft
	assert_bool(fx[0].shaft).is_true()                   # the arrow is drawn falling, then lying
	assert_float(fx[0].global_position.distance_to(last)).is_less_equal(Arrow.SPEED / 60.0 + 1.0)
	assert_vector(fx[0].drift).is_equal(Vector2(-4, 0))  # back off the prop, not into it
	assert_bool(fx[0].burst_on_ground()).is_true()       # the dust is at ground level, in the y-sort
	assert_int(fx[0].z_index).is_equal(0)
	assert_float(_run_out(fx[0])).is_less_equal(Impact.FALL + Impact.STUCK + Impact.FADE + 1.0 / 60.0 + 0.0001)

## A solid that says it has a drawn face (a house, a terrace face: the generators' `impact_face`) takes the
## arrow stuck in its face; met from its north side, the same face drops the arrow behind it.
func test_a_solid_with_a_face_takes_the_arrow_stuck_and_drops_it_from_behind() -> void:
	var root := _stage()
	var archer := _archer(root, Vector2(100, 100))
	var house := _wall(root, 160, 60, 200, 140)
	house.set_meta("impact_face", true)
	await _settle()
	var last := await _fly(_loose(root, Vector2(126, 100), archer))
	var fx := _impacts(root)
	assert_int(fx.size()).is_equal(1)
	assert_int(fx[0].kind).is_equal(Impact.Kind.WALL)
	assert_bool(fx[0].shaft).is_true()
	assert_float(fx[0].lift).is_equal(20.0)                 # on the face, at the arrow's height
	assert_float(fx[0].global_position.distance_to(last)).is_less_equal(Arrow.SPEED / 60.0 + 1.0)
	assert_float(fx[0].global_position.x).is_between(160.0 - Arrow.RADIUS - Arrow.SPEED / 60.0, 160.0 + Arrow.RADIUS + 1.0)
	assert_bool(fx[0].burst_on_ground()).is_false()          # the puff on the face is drawn over (Burst, z 1)
	assert_int(fx[0].z_index).is_equal(0)                    # the stuck shaft y-sorts at its ground point
	assert_int((fx[0].get_node("Burst") as Node2D).z_index).is_equal(1)
	assert_float(_run_out(fx[0])).is_less_equal(Impact.STUCK + Impact.FADE + 1.0 / 60.0 + 0.0001)
	# from the north (flying south into its back): it never sticks, it drops behind the house
	var back := _stage()
	var archer2 := _archer(back, Vector2(180, -20))
	var house2 := _wall(back, 160, 60, 200, 140)
	house2.set_meta("impact_face", true)
	await _settle()
	await _fly(_loose(back, Vector2(180, 10), archer2, Vector2.DOWN))
	var behind := _impacts(back)
	assert_int(behind.size()).is_equal(1)
	assert_int(behind[0].kind).is_equal(Impact.Kind.DROP)
	assert_vector(behind[0].drift).is_equal(Vector2(0, -4))  # knocked back north, further behind
	assert_float(behind[0].global_position.y).is_less(60.0 + Arrow.RADIUS + 1.0)
	assert_bool(Impact.has_face(house2, Vector2.DOWN)).is_false()
	assert_bool(Impact.has_face(house2, Vector2.UP)).is_true()
	assert_bool(Impact.has_face(house2, Vector2.LEFT)).is_true()

## #509 round 1, F2: the dropped arrow is drawn in the y-sort at its ground point, so a house whose foot is
## further south (a roof over it) is drawn after it and covers it. Only the burst up on a thing is z 1.
func test_a_dropped_arrow_behind_a_house_is_covered_by_its_roof() -> void:
	var zone: Node2D = auto_free(Node2D.new())
	zone.y_sort_enabled = true
	add_child(zone)
	var house := Sprite2D.new()                       # drawn up from its feet at y 140, as the kit's pictures are
	house.texture = PlaceholderTexture2D.new()
	(house.texture as PlaceholderTexture2D).size = Vector2(80, 120)
	house.centered = false
	house.offset = Vector2(-40, -120)
	house.position = Vector2(180, 140)
	zone.add_child(house)
	var fx := Impact.spawn(zone, Impact.Kind.DROP, Vector2(180, 56), 60.0, Vector2.DOWN, true)
	fx.drift = Vector2(0, -4)
	await get_tree().process_frame
	assert_int(fx.z_index).is_equal(0)
	assert_bool(fx.z_as_relative).is_true()
	assert_bool(fx.burst_on_ground()).is_true()           # its dust is on the ground too, in the y-sort
	# the roof covers it: same z, and the house's feet are further south, so the y-sort draws the house after it
	assert_int(house.z_index).is_equal(fx.z_index)
	assert_float(house.global_position.y).is_greater(fx.global_position.y + fx.drift.y)
	# where the arrow lies is inside the roof's picture (drawn from y 20 to 140)
	var lying := fx.global_position + fx.drift
	assert_bool(Rect2(house.position + house.offset, Vector2(80, 120)).has_point(lying)).is_true()

## #509 round 1, F3: a flight that ends over water sinks (no dust, no arrow lying on it); over another low
## solid (a bench, a stump, a bush) nothing is left lying on it; on the ground it drops as before.
func test_a_flight_that_ends_over_water_sinks_and_over_a_low_prop_leaves_nothing() -> void:
	for case in ["water", "low", "ground"]:
		var root := _stage()
		var archer := _archer(root, Vector2(100, 100))
		if case != "ground":
			var low := StaticBody2D.new()
			low.collision_layer = 17                       # layers 1 and 5: feet stop, shots fly over
			low.collision_mask = 0
			var shape := CollisionShape2D.new()
			var rect := RectangleShape2D.new()
			rect.size = Vector2(400, 200)
			shape.shape = rect
			shape.position = Vector2(126, 100 + Arrow.SPEED * Arrow.LIFETIME)
			if case == "water":
				shape.set_meta("impact_water", true)       # as tools/gen_zone.py writes the low terrain
			low.add_child(shape)
			root.add_child(low)
		await _settle()
		var far := await _fly(_loose(root, Vector2(126, 100), archer, Vector2.DOWN), 90)
		assert_float(far.y - 100.0).is_greater(Arrow.SPEED * Arrow.LIFETIME * 0.9)   # it flew over
		var fx := _impacts(root)
		match case:
			"water":
				assert_int(fx.size()).is_equal(1)
				assert_int(fx[0].kind).is_equal(Impact.Kind.SINK)
				assert_float(_run_out(fx[0])).is_less_equal(Impact.FALL + Impact.RING + 1.0 / 60.0 + 0.0001)
			"low":
				assert_int(fx.size()).is_equal(0)
			"ground":
				assert_int(fx.size()).is_equal(1)
				assert_int(fx[0].kind).is_equal(Impact.Kind.DROP)
		root.free()                                        # its solids leave the space before the next case
	# the seed too: over water a ring, never a splat on the water
	var pond := _stage()
	var water := StaticBody2D.new()
	water.collision_layer = 17
	water.collision_mask = 0
	var ws := CollisionShape2D.new()
	var wr := RectangleShape2D.new()
	wr.size = Vector2(600, 600)
	ws.shape = wr
	ws.set_meta("impact_water", true)
	water.add_child(ws)
	pond.add_child(water)
	await _settle()
	var shot := SliceEnemyShot.new()
	pond.add_child(shot)
	shot.global_position = Vector2(-100, 0)
	for i in 120:
		await get_tree().physics_frame
		if not is_instance_valid(shot) or shot.finished:
			break
	var ring := _impacts(pond)
	assert_int(ring.size()).is_equal(1)
	assert_int(ring[0].kind).is_equal(Impact.Kind.SINK)

## #509 round 1, P3: the arrow's restore never ends a melee hold that began while it held.
func test_an_arrow_hold_does_not_cut_a_melee_hold_short() -> void:
	assert_bool(Impact.hit_stop(get_tree())).is_true()
	Engine.time_scale = 0.05                              # the melee's hold (actors/player.gd _hitstop) begins
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < int(Impact.HIT_STOP * 1000.0) + 80:
		await get_tree().process_frame
	assert_float(Engine.time_scale).is_equal(0.05)        # still the melee's: the arrow's restore left it
	Engine.time_scale = 1.0                               # the melee's own restore
	# and an older arrow hold never ends a newer one
	assert_bool(Impact.hit_stop(get_tree())).is_true()
	var first := Time.get_ticks_msec()
	while Time.get_ticks_msec() - first < 30:
		await get_tree().process_frame
	Engine.time_scale = 1.0                               # cut short by someone else 30 ms in
	assert_bool(Impact.hit_stop(get_tree())).is_true()    # a second hold: the first's restore (at 50 ms) must not end it
	var second := Time.get_ticks_msec()
	while Engine.time_scale < 1.0 and Time.get_ticks_msec() - second < 1000:
		await get_tree().process_frame
	assert_int(Time.get_ticks_msec() - second).is_greater_equal(int(Impact.HIT_STOP * 1000.0) - 5)

func test_a_creatures_shot_splats_on_a_wall_and_on_the_player_in_its_colours() -> void:
	var root := _stage()
	_wall(root, 160, 60, 200, 140)
	await _settle()
	var shot := SliceEnemyShot.new()
	root.add_child(shot)
	shot.global_position = Vector2(120, 100)
	var last := shot.global_position
	for i in 60:
		await get_tree().physics_frame
		if not is_instance_valid(shot) or shot.finished:
			break
		last = shot.global_position
	var fx := _impacts(root)
	assert_int(fx.size()).is_equal(1)
	assert_int(fx[0].kind).is_equal(Impact.Kind.SPLAT)
	assert_array(fx[0].tint).is_equal(Impact.SEED_TINT)
	assert_float(fx[0].global_position.x).is_equal_approx(160.0, 0.6)   # where the ray met the solid
	assert_float(fx[0].global_position.y).is_equal_approx(last.y, 0.01)
	assert_float(fx[0].lift).is_equal(0.0)                 # no face: at the solid's foot, on the ground
	assert_bool(fx[0].burst_on_ground()).is_true()
	assert_float(_run_out(fx[0])).is_less_equal(Impact.FRAME * Impact.FRAMES + 1.0 / 60.0 + 0.0001)
	# a thorn on the player: the hurt is the player's, the splat is the thorn's
	var p: Player = auto_free(load("res://actors/player.tscn").instantiate())
	add_child(p)
	p.global_position = Vector2(400, 400)
	await _settle()
	var hp := p.hp
	var th := ThornbackThorn.new()
	th.direction = Vector2.RIGHT
	root.add_child(th)
	th.global_position = Vector2(360, 400)
	for i in 60:
		await get_tree().physics_frame
		if not is_instance_valid(th) or th.finished:
			break
	assert_int(p.hp).is_equal(hp - 1)
	var splats := _impacts(root).filter(func(n: Impact) -> bool: return n.tint == Impact.THORN_TINT)
	assert_int(splats.size()).is_equal(1)
	assert_float(splats[0].global_position.distance_to(p.global_position)).is_less(Arrow.RADIUS + 9.0 + 20.0)
	assert_float(splats[0].lift).is_equal(12.0)           # on the player, at the thorn's own height

## Rule numbers as main had them on 16 Nov (cef25d2b): the marks are drawing and sound only.
func test_no_damage_or_knockback_number_changed() -> void:
	assert_float(Arrow.SPEED).is_equal(140.0 * 3.0)
	assert_float(Arrow.LIFETIME).is_equal(0.9)
	assert_float(Arrow.KNOCKBACK).is_equal(90.0 * 3.0)
	assert_float(Arrow.RADIUS).is_equal(4.0)
	assert_float(SliceEnemyShot.SPEED).is_equal(80.0 * 3.0)
	var shot := SliceEnemyShot.new()
	assert_int(shot.damage).is_equal(1)
	assert_float(shot.lifetime).is_equal(1.4)
	shot.free()
	assert_float(ThornbackThorn.SPEED).is_equal(70.0 * 3.0)
	assert_float(ThornbackThorn.LIFETIME).is_equal(2.4)
	# an arrow that counts still takes one heart of five and knocks the mossling along its flight at KNOCKBACK
	var root := _stage()
	var archer := _archer(root, Vector2(100, 100))
	var foe: Enemy = load("res://actors/enemy.tscn").instantiate()
	foe.position = Vector2(200, 100)
	root.add_child(foe)
	await _settle()
	foe.set_physics_process(false)
	var arrow := _loose(root, Vector2(126, 100), archer)
	await _fly(arrow)
	assert_int(foe.max_hp - foe.hp).is_equal(1)
	assert_vector(foe.velocity).is_equal(Vector2.RIGHT * Arrow.KNOCKBACK)
	assert_float(foe._stagger).is_equal(0.14)
	assert_float(foe._flash).is_equal(0.12)
