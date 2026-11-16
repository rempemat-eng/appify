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

func _loose(root: Node2D, at: Vector2, archer: Node2D, dir := Vector2.RIGHT, lift := 20.0) -> Arrow:
	var arrow := Arrow.new()
	root.add_child(arrow)
	arrow.setup(at, lift, dir, archer)
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
	assert_object(Impact.hit_stop(get_tree())).is_null()
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
	var timer := Impact.hit_stop(get_tree())
	assert_object(timer).is_not_null()
	# the hold's length, without the wall clock (#509 follow-up): its timer counts exactly HIT_STOP
	assert_float(Impact.HIT_STOP).is_equal(0.05)            # pinned: 3 frames at 60 (#515 audit)
	assert_float(timer.time_left).is_equal_approx(Impact.HIT_STOP, 0.000001)
	assert_float(Engine.time_scale).is_equal(Impact.HOLD_SCALE)
	assert_object(Impact.hit_stop(get_tree())).is_null()   # one hold at a time
	var start := Time.get_ticks_msec()
	while Engine.time_scale < 1.0 and Time.get_ticks_msec() - start < 1000:
		await get_tree().process_frame
	var held := Time.get_ticks_msec() - start
	assert_float(Engine.time_scale).is_equal(1.0)
	# a real-time timer: it ends within a frame of HIT_STOP (on a loaded machine the frame it starts in can be
	# long, so the lower end is only "it held"; check:godot measured 28 ms once, 16 Nov)
	assert_int(held).is_between(1, int(Impact.HIT_STOP * 1000.0) + 120)

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

## A solid's drawn face (the generators' `impact_face` height in texels and `impact_material`) takes an arrow
## stuck only when it crossed the box's south edge below the face's top and the face is timber or earth
## (#509 round 2, F1b and S1). Any other edge, a hit above the face's top, or stone: the arrow drops, never moved.
func _faced(root: Node2D, height: float, material: String) -> StaticBody2D:
	var house := _wall(root, 160, 60, 200, 140)
	house.set_meta("impact_face", height)
	house.set_meta("impact_material", material)
	return house

## Shoots one arrow at a faced box from `at` along `dir` at `lift`; returns the mark it left.
func _shoot_at_face(height: float, material: String, at: Vector2, dir: Vector2, lift := 20.0) -> Impact:
	var root := _stage()
	var archer := _archer(root, at)
	_faced(root, height, material)
	await _settle()
	await _fly(_loose(root, at, archer, dir.normalized(), lift))
	var fx := _impacts(root)
	assert_int(fx.size()).is_equal(1)
	var mark: Impact = fx[0]
	root.remove_child(mark)                              # kept for the asserts; the stage and its solids go
	auto_free(mark)
	root.free()
	return mark

func test_a_timber_face_takes_an_arrow_from_the_south_and_drops_every_other() -> void:
	# from the south, below the top: stuck, at the arrow's own height, the shaft in the y-sort, the puff over
	var stuck := await _shoot_at_face(90.0, "timber", Vector2(180, 200), Vector2.UP)
	assert_int(stuck.kind).is_equal(Impact.Kind.WALL)
	# drawn where the arrow met the face, 20 up (the arrow's own height), but y-sorted FRONT south of the box,
	# so the house (sorted by its feet at the box's edge) never covers it (#509 follow-up)
	assert_float(stuck.global_position.y).is_equal(140.0 + Impact.FRONT)
	assert_float(stuck.global_position.y - stuck.lift).is_between(140.0 - 20.0 - 1.0, 140.0 - 20.0 + Arrow.RADIUS + Arrow.SPEED / 60.0)
	assert_str(stuck.face_material).is_equal("timber")
	assert_bool(stuck.burst_on_ground()).is_false()
	assert_int(stuck.z_index).is_equal(0)
	assert_int((stuck.get_node("Burst") as Node2D).z_index).is_equal(1)
	assert_float(_run_out(stuck)).is_less_equal(Impact.STUCK + Impact.FADE + 1.0 / 60.0 + 0.0001)
	# a shallow shot east-south-east across the north edge (the audit's dir (0.95, 0.31)): it drops
	var shallow := await _shoot_at_face(90.0, "timber", Vector2(130, 40), Vector2(0.95, 0.31))
	assert_int(shallow.kind).is_equal(Impact.Kind.DROP)
	assert_float(shallow.global_position.y).is_less_equal(60.0 + 1.0)
	# straight in from the north: it drops behind, knocked back north
	var behind := await _shoot_at_face(90.0, "timber", Vector2(180, 10), Vector2.DOWN)
	assert_int(behind.kind).is_equal(Impact.Kind.DROP)
	assert_vector(behind.drift).is_equal(Vector2(0, -4))
	# a side edge no body declares (the west edge, flying east): it drops
	var side := await _shoot_at_face(90.0, "timber", Vector2(100, 100), Vector2.RIGHT)
	assert_int(side.kind).is_equal(Impact.Kind.DROP)
	assert_vector(side.drift).is_equal(Vector2(-4, 0))

func test_an_arrow_above_a_faces_top_drops_and_is_never_moved_down() -> void:
	# a north shot flies 61 to 67 texels up (docs/physics.md); a 36 texel wall: it drops
	var high := await _shoot_at_face(36.0, "timber", Vector2(180, 200), Vector2.UP, 61.0)
	assert_int(high.kind).is_equal(Impact.Kind.DROP)
	assert_float(high.lift).is_equal(61.0)                 # it falls from where it was, not from the wall top
	# the same wall, 33 up (its top less FACE_TOP): stuck at 33
	var low := await _shoot_at_face(36.0, "timber", Vector2(180, 200), Vector2.UP, 33.0)
	assert_int(low.kind).is_equal(Impact.Kind.WALL)
	assert_float(140.0 - (low.global_position.y - low.lift)).is_less_equal(33.0)   # drawn at most 33 above the wall's foot
	var over := await _shoot_at_face(36.0, "timber", Vector2(180, 200), Vector2.UP, 34.0)
	assert_int(over.kind).is_equal(Impact.Kind.DROP)

func test_stone_never_takes_an_arrow_it_drops_with_grey_chips() -> void:
	var stone := await _shoot_at_face(110.0, "stone", Vector2(180, 200), Vector2.UP)
	assert_int(stone.kind).is_equal(Impact.Kind.DROP)
	assert_str(stone.face_material).is_equal("stone")
	assert_vector(Vector2(stone._chip().r, stone._chip().g)).is_equal(Vector2(Impact.STONE_CHIP.r, Impact.STONE_CHIP.g))
	assert_bool(stone.burst_on_ground()).is_true()           # chips and grey dust at the foot, in the y-sort
	# no face at all (a prop with a foot box): plain dust, no chips
	var plain := Impact.new()
	auto_free(plain)
	assert_float(plain._chip().a).is_equal(0.0)
	# the faces the zones declare
	var cross: Node = auto_free(load("res://zones/crossroads/crossroads.tscn").instantiate())
	var hut_face := Impact.face_of(cross.get_node("Walls/Building_hut"))
	assert_float(float(hut_face.height)).is_equal(90.0)
	assert_str(String(hut_face.material)).is_equal("timber")
	assert_str(String(Impact.face_of(cross.get_node("Walls/Building_library")).material)).is_equal("stone")
	assert_str(String(Impact.face_of(cross.get_node("Walls/Face_lane_face")).material)).is_equal("stone")
	assert_float(float(Impact.face_of(cross.get_node("Walls/Face_terrace_bank_e")).height)).is_equal(0.0)
	var vault: Node = auto_free(load("res://zones/undercroft/undercroft.tscn").instantiate())
	for side in ["Walls/Wall_south", "Walls/Wall_corridor_s", "Walls/Wall_west_s", "Walls/Wall_east"]:
		assert_float(float(Impact.face_of(vault.get_node(side)).height)).override_failure_message(side).is_equal(0.0)
	var hall := Impact.face_of(vault.get_node("Walls/Wall_north_hall"))
	assert_float(float(hall.height)).is_equal(120.0)
	assert_str(String(hall.material)).is_equal("stone")

## #509 follow-up: the timber houses stand on stone plinths (the north cottages' and the Ferns' rubble walls to
## 63 texels, the hut's to 11), and their windows take no arrow. A timber wall above the plinth still does.
func _shoot_at_house(at_x: float, lift: float, stone_below: float, windows: Array, timber: Array = [],
		dir := Vector2.UP) -> Impact:
	var root := _stage()
	var at := Vector2(at_x, 200)
	var archer := _archer(root, at)
	var house := _faced(root, 110.0, "timber")             # box x 160-200, centre 180
	house.set_meta("impact_stone_below", stone_below)
	house.set_meta("impact_no_stick", windows)
	house.set_meta("impact_timber", timber)
	await _settle()
	await _fly(_loose(root, at, archer, dir.normalized(), lift))
	var fx := _impacts(root)
	assert_int(fx.size()).is_equal(1)
	var mark: Impact = fx[0]
	root.remove_child(mark)
	auto_free(mark)
	root.free()
	return mark

func test_a_plinth_drops_the_arrow_with_stone_and_a_window_drops_it_plain() -> void:
	var window := [Rect2(-12, 54, 10, 36)]                 # x 168-178 from the centre 180, lift 54-90
	# into the plinth (lift 20, plinth to 63): stone dust and chips, never stuck
	var plinth := await _shoot_at_house(190.0, 20.0, 63.0, window)
	assert_int(plinth.kind).is_equal(Impact.Kind.DROP)
	assert_str(plinth.face_material).is_equal("stone")
	# at the plinth's top row (63): still stone
	var top := await _shoot_at_house(190.0, 63.0, 63.0, window)
	assert_int(top.kind).is_equal(Impact.Kind.DROP)
	assert_str(top.face_material).is_equal("stone")
	# above the plinth, beside the window (lift 66): timber, stuck
	var timber := await _shoot_at_house(190.0, 66.0, 63.0, window)
	assert_int(timber.kind).is_equal(Impact.Kind.WALL)
	assert_str(timber.face_material).is_equal("timber")
	assert_float(timber.global_position.y - timber.lift).is_between(140.0 - 66.0 - 1.0, 140.0 - 66.0 + Arrow.RADIUS + Arrow.SPEED / 60.0)
	# into the window (x 172, lift 66): it drops, plain dust, no chips
	var glass := await _shoot_at_house(172.0, 66.0, 63.0, window)
	assert_int(glass.kind).is_equal(Impact.Kind.DROP)
	assert_str(glass.face_material).is_equal("")
	assert_float(glass._chip().a).is_equal(0.0)
	# the same answers from face_hit itself, at the edges of the window
	var house := StaticBody2D.new()
	auto_free(house)
	var shape := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(40, 80)
	shape.shape = rect
	shape.position = Vector2(180, 100)
	house.add_child(shape)
	add_child(house)
	house.set_meta("impact_face", 110)
	house.set_meta("impact_material", "timber")
	house.set_meta("impact_stone_below", 63)
	house.set_meta("impact_no_stick", window)
	assert_str(Impact.face_hit(house, Vector2(168, 150), 66.0)).is_equal("window")
	assert_str(Impact.face_hit(house, Vector2(178, 150), 66.0)).is_equal("stick")    # the window's right edge is open
	assert_str(Impact.face_hit(house, Vector2(170, 150), 53.0)).is_equal("stone")
	assert_str(Impact.face_hit(house, Vector2(190, 150), 64.0)).is_equal("stick")    # beside the window
	assert_str(Impact.face_hit(house, Vector2(170, 150), 108.0)).is_equal("drop")    # above the top less FACE_TOP
	assert_str(Impact.face_hit(house, Vector2(170, 50), 66.0)).is_equal("drop")      # from the north

## #515 audit: a door is timber through the plinth band, and the window and door checks use where the arrow
## met the face, not the point one step before.
func test_a_door_in_the_plinth_band_is_timber() -> void:
	var door := [Rect2(-20, 0, 15, 84)]                    # x 160-175 from the centre 180, lift 0-84
	var window := [Rect2(5, 54, 10, 36)]                   # x 185-195
	# a diagonal shot (north-east) into the door at lift 40, inside the plinth (63): it sticks, timber
	var into_door := await _shoot_at_house(137.0, 40.0, 63.0, window, door, Vector2(0.5, -1))   # meets the face near x 167
	assert_int(into_door.kind).is_equal(Impact.Kind.WALL)
	assert_str(into_door.face_material).is_equal("timber")
	# beside the door at the same height: the plinth, stone
	var plinth := await _shoot_at_house(188.0, 40.0, 63.0, window, door)
	assert_int(plinth.kind).is_equal(Impact.Kind.DROP)
	assert_str(plinth.face_material).is_equal("stone")

func test_the_face_is_read_where_the_arrow_met_it() -> void:
	var house := StaticBody2D.new()
	auto_free(house)
	var shape := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(40, 80)
	shape.shape = rect
	shape.position = Vector2(180, 100)
	house.add_child(shape)
	add_child(house)
	house.set_meta("impact_face", 110)
	house.set_meta("impact_material", "timber")
	house.set_meta("impact_stone_below", 63)
	house.set_meta("impact_no_stick", [Rect2(5, 54, 10, 36)])
	house.set_meta("impact_timber", [Rect2(-20, 0, 15, 84)])
	# one step before it was at x 178 (beside the window); it met the face at x 188, in the window
	assert_str(Impact.face_hit(house, Vector2(178, 150), 66.0, 188.0)).is_equal("window")
	assert_str(Impact.face_hit(house, Vector2(178, 150), 66.0)).is_equal("stick")          # without the contact x
	# it met the door's x (165) inside the plinth band: timber; one step before it was beside the door (178)
	assert_str(Impact.face_hit(house, Vector2(178, 150), 40.0, 165.0)).is_equal("stick")
	assert_str(Impact.face_hit(house, Vector2(178, 150), 40.0)).is_equal("stone")
	# the door wins where it overlaps a window (the north cottages' purple door over its window's corner)
	house.set_meta("impact_no_stick", [Rect2(-10, 54, 10, 36)])
	house.set_meta("impact_timber", [Rect2(-12, 0, 15, 84)])
	assert_str(Impact.face_hit(house, Vector2(178, 150), 60.0, 175.0)).is_equal("stick")

func test_the_crossroads_houses_declare_their_plinths_and_windows() -> void:
	var cross: Node = auto_free(load("res://zones/crossroads/crossroads.tscn").instantiate())
	var hut := Impact.face_of(cross.get_node("Walls/Building_hut"))
	assert_float(float(hut.stone_below)).is_equal(11.0)
	assert_array(hut.no_stick).is_equal([Rect2(-89, 54, 33, 36), Rect2(55, 54, 33, 36)])
	assert_array(hut.timber).is_empty()
	var cottages := Impact.face_of(cross.get_node("Walls/Building_north_cottages"))
	assert_float(float(cottages.stone_below)).is_equal(63.0)
	assert_array(cottages.no_stick).is_equal([Rect2(-61, 52, 37, 40), Rect2(11, 52, 37, 40)])
	assert_array(cottages.timber).is_equal([Rect2(-140, 0, 62, 84), Rect2(37, 0, 69, 84)])
	var fern := Impact.face_of(cross.get_node("Walls/Building_fern_cottage"))
	assert_float(float(fern.stone_below)).is_equal(63.0)
	assert_array(fern.no_stick).is_equal([Rect2(13, 54, 33, 36)])
	assert_array(fern.timber).is_equal([Rect2(-92, 0, 67, 85)])

## #509 follow-up: the arrow's last ground point is taken after its start is settled. Against a wall the start
## moves to the archer's feet, and the "one step before" point must be there, not at the bow's tip.
func test_the_last_point_is_where_the_arrow_really_starts() -> void:
	var root := _stage()
	var archer := _archer(root, Vector2(100, 100))
	_wall(root, 116, 60, 164, 140)
	await _settle()
	var arrow := _loose(root, Vector2(135, 100), archer)    # the tip is inside the wall: it starts at the feet
	assert_vector(arrow.global_position).is_equal(Vector2(100, 100))
	assert_vector(arrow._prev).is_equal(Vector2(100, 100))

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
	# #509 round 2, S2: a shot's ring has no arrow to fall first; it starts at once where the shot ended
	assert_bool(ring[0].shaft).is_false()
	assert_vector(ring[0].drift).is_equal(Vector2.ZERO)
	assert_float(ring[0].lifetime()).is_equal(Impact.RING)

## #509 round 1, P3: the arrow's restore never ends a melee hold that began while it held.
## The hold's timer counts real time, not the held world's: under the hold's 0.06 time scale, 20 ms of real
## time take at least 10 ms off it (a timer that followed the scale would lose about 1.2 ms). Waiting longer
## only takes more off, so the wall clock here is a lower bound on time passed, never a bound on the hold.
func test_the_holds_timer_ignores_the_time_scale() -> void:
	var timer := Impact.hit_stop(get_tree())
	assert_object(timer).is_not_null()
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < 20:
		await get_tree().process_frame
	assert_float(Impact.HIT_STOP - timer.time_left).is_greater_equal(0.010)

func test_an_arrow_hold_does_not_cut_a_melee_hold_short() -> void:
	# the restore itself, called as its timer would call it (no wall clock: deterministic)
	assert_object(Impact.hit_stop(get_tree())).is_not_null()
	var arrow_hold := Impact.hold_token()
	Engine.time_scale = 0.05                              # the melee's hold (actors/player.gd _hitstop) begins
	Impact.release_hold(arrow_hold)
	assert_float(Engine.time_scale).is_equal(0.05)        # still the melee's: the arrow's restore left it
	Engine.time_scale = 1.0                               # the melee's own restore
	# an older arrow hold never ends a newer one
	assert_object(Impact.hit_stop(get_tree())).is_not_null()
	var older := Impact.hold_token()
	Engine.time_scale = 1.0                               # cut short by someone else
	assert_object(Impact.hit_stop(get_tree())).is_not_null()
	var newer := Impact.hold_token()
	Impact.release_hold(older)
	assert_float(Engine.time_scale).is_equal(Impact.HOLD_SCALE)
	Impact.release_hold(newer)
	assert_float(Engine.time_scale).is_equal(1.0)
	# and through the real timer, the melee's hold is still there after the arrow's would have ended
	assert_object(Impact.hit_stop(get_tree())).is_not_null()
	Engine.time_scale = 0.05
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < int(Impact.HIT_STOP * 1000.0) + 80:
		await get_tree().process_frame
	assert_float(Engine.time_scale).is_equal(0.05)

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
