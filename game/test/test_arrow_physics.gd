extends GdUnitTestSuite
## What an arrow meets (actors/arrow.gd, docs/physics.md): its start is tested as wide as its body, it flies
## over low solids (layer 5: water, a drop, a bench, a stump) and stops at every other one, and its archer
## is the player beside it, never whoever a tree-wide lookup returns first.

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

## A solid rectangle with its corners at (x0, y0) and (x1, y1); `layer` 1 is a wall, 17 a low solid.
func _solid(root: Node2D, x0: float, y0: float, x1: float, y1: float, layer := 1) -> StaticBody2D:
	var body := StaticBody2D.new()
	body.collision_layer = layer
	body.collision_mask = 0
	var shape := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(x1 - x0, y1 - y0)
	shape.shape = rect
	body.add_child(shape)
	body.position = Vector2((x0 + x1) / 2.0, (y0 + y1) / 2.0)
	root.add_child(body)
	return body

func _loose(root: Node2D, at: Vector2, dir := Vector2.RIGHT, archer: Node2D = null) -> Arrow:
	var arrow := Arrow.new()
	root.add_child(arrow)
	arrow.setup(at, 20.0, dir, archer)
	return arrow

func _settle() -> void:
	await get_tree().physics_frame
	await get_tree().physics_frame

## Flies the arrow until it is gone or `frames` have passed; returns the furthest x it reached.
func _fly(arrow: Arrow, frames: int) -> float:
	var furthest := arrow.global_position.x
	for i in frames:
		await get_tree().physics_frame
		if not is_instance_valid(arrow):
			break
		furthest = arrow.global_position.x
	return furthest

func test_the_start_is_tested_as_wide_as_the_arrow() -> void:
	# a corner 3 px beside the line from the feet (100, 100) to the tip (130, 100): a line passes it, the
	# arrow's body (4 px) does not. The arrow used to start at the tip, touching the corner, and died there.
	var root := _stage()
	var archer := _archer(root, Vector2(100, 100))
	_solid(root, 120, 103, 160, 150)
	await _settle()
	var arrow := _loose(root, Vector2(130, 100))
	assert_vector(arrow.global_position).is_equal(archer.global_position)   # walled off: it starts at the feet
	var furthest := await _fly(arrow, 40)
	assert_bool(is_instance_valid(arrow)).is_false()
	assert_float(furthest).is_greater(108.0)        # it flew before the corner stopped it ...
	assert_float(furthest).is_less(126.0)           # ... and stopped at the corner, not beyond it

func test_a_clear_path_still_starts_at_the_tip() -> void:
	var root := _stage()
	_archer(root, Vector2(100, 100))
	_solid(root, 120, 106, 160, 150)                # 6 px beside the line: the body passes
	await _settle()
	var arrow := _loose(root, Vector2(130, 100))
	assert_vector(arrow.global_position).is_equal(Vector2(130, 100))
	await _fly(arrow, 12)
	assert_bool(is_instance_valid(arrow)).is_true()
	assert_float(arrow.global_position.x).is_greater(170.0)

func test_an_arrow_flies_over_a_low_solid() -> void:
	var root := _stage()
	_archer(root, Vector2(100, 100))
	_solid(root, 150, 60, 190, 140, 17)             # a bench, a stump, a stream: layers 1 and 5
	await _settle()
	var arrow := _loose(root, Vector2(126, 100))
	var furthest := await _fly(arrow, 20)
	assert_bool(is_instance_valid(arrow)).is_true()
	assert_float(furthest).is_greater(200.0)

func test_a_low_solid_at_the_bow_does_not_move_the_start() -> void:
	var root := _stage()
	_archer(root, Vector2(100, 100))
	_solid(root, 112, 60, 150, 140, 17)             # the archer stands against a bench: the tip is over it
	await _settle()
	var arrow := _loose(root, Vector2(128, 100))
	assert_vector(arrow.global_position).is_equal(Vector2(128, 100))

func test_a_wall_behind_a_low_solid_still_stops_it() -> void:
	var root := _stage()
	_archer(root, Vector2(100, 100))
	_solid(root, 150, 60, 170, 140, 17)
	_solid(root, 200, 0, 240, 200)
	await _settle()
	var arrow := _loose(root, Vector2(126, 100))
	var furthest := await _fly(arrow, 40)
	assert_bool(is_instance_valid(arrow)).is_false()
	assert_float(furthest).is_between(172.0, 240.0)

func test_a_wall_seen_through_a_low_solid_walls_the_start_off() -> void:
	# the tip beyond a wall that stands behind a low solid: the low one is stepped past, the wall counts
	var root := _stage()
	var archer := _archer(root, Vector2(100, 100))
	_solid(root, 108, 60, 114, 140, 17)
	_solid(root, 116, 0, 164, 200)
	await _settle()
	var arrow := _loose(root, Vector2(170, 100))
	assert_vector(arrow.global_position).is_equal(archer.global_position)

func test_the_archer_is_the_player_beside_the_arrow() -> void:
	# another body in the "player" group, elsewhere in the tree and first in the group: the tree-wide lookup
	# took it for the archer and the arrow jumped to it
	var other_holder := _stage()
	_archer(other_holder, Vector2(100, 300))
	var root := _stage()
	var archer := _archer(root, Vector2(100, 100))
	_solid(root, 116, 0, 164, 200)
	await _settle()
	var arrow := _loose(root, Vector2(135, 100))    # the tip inside the wall
	assert_vector(arrow.global_position).is_equal(archer.global_position)

func test_the_archer_can_be_handed_over() -> void:
	var root := _stage()
	var near := _archer(root, Vector2(128, 100))    # nearest the tip, but not the one who shot
	var shooter := Node2D.new()
	shooter.position = Vector2(100, 40)
	root.add_child(shooter)
	_solid(root, 60, 60, 200, 80)                   # a wall between the shooter and the tip
	await _settle()
	var arrow := _loose(root, Vector2(130, 100), Vector2.DOWN, shooter)
	assert_vector(arrow.global_position).is_equal(shooter.global_position)
	assert_object(near).is_not_null()

func test_an_enemy_is_still_hit() -> void:
	var root := _stage()
	_archer(root, Vector2(100, 100))
	_solid(root, 140, 60, 160, 140, 17)             # low cover between them
	var foe: Enemy = load("res://actors/enemy.tscn").instantiate()
	foe.position = Vector2(200, 100)
	root.add_child(foe)
	await _settle()
	var hp := foe.hp
	var arrow := _loose(root, Vector2(126, 100))
	await _fly(arrow, 30)
	assert_bool(is_instance_valid(arrow)).is_false()
	assert_int(foe.hp).is_equal(hp - 1)
