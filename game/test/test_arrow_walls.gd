extends GdUnitTestSuite
## Arrows start at the bow's tip, ahead of the archer. Against a thin wall that point lies inside or
## beyond the wall: the Thornback could be shot through the closed seal (found by playing, 10 Nov).

func _scene(with_wall: bool) -> Node2D:
	var root: Node2D = auto_free(Node2D.new())
	add_child(root)
	var archer := Node2D.new()
	archer.add_to_group("player")
	archer.position = Vector2(100, 100)
	root.add_child(archer)
	if with_wall:
		var wall := StaticBody2D.new()
		var shape := CollisionShape2D.new()
		var rect := RectangleShape2D.new()
		rect.size = Vector2(48, 200)
		shape.shape = rect
		wall.add_child(shape)
		wall.position = Vector2(140, 100)  # spans x 116 to 164
		root.add_child(wall)
	return root

func _loose(root: Node2D, at: Vector2) -> Arrow:
	var arrow := Arrow.new()
	root.add_child(arrow)
	arrow.setup(at, 20.0, Vector2.RIGHT)
	return arrow

func test_an_arrow_does_not_start_inside_or_beyond_a_wall() -> void:
	# the tip inside the wall (x 135) or beyond it (x 170): the arrow starts at the archer's feet and the wall stops it
	for tip_x in [135.0, 170.0]:
		var root := _scene(true)
		await get_tree().physics_frame
		await get_tree().physics_frame
		var arrow := _loose(root, Vector2(tip_x, 100))
		assert_float(arrow.global_position.x).is_equal(100.0)
		var furthest := 0.0
		for i in 40:
			await get_tree().physics_frame
			if not is_instance_valid(arrow):
				break
			furthest = arrow.global_position.x
		assert_bool(is_instance_valid(arrow)).is_false()
		assert_float(furthest).is_less(164.0)
		root.free()

func test_an_arrow_in_the_open_flies() -> void:
	var root := _scene(false)
	await get_tree().physics_frame
	await get_tree().physics_frame
	var arrow := _loose(root, Vector2(135, 100))
	assert_float(arrow.global_position.x).is_equal(135.0)   # no wall: it starts at the bow's tip
	for i in 10:
		await get_tree().physics_frame
	assert_bool(is_instance_valid(arrow)).is_true()
	assert_float(arrow.global_position.x).is_greater(160.0)

func test_a_wall_stops_an_arrow_in_flight() -> void:
	# loosed in front of the wall, the arrow must end at its face, not fly on behind it
	var root := _scene(true)
	await get_tree().physics_frame
	await get_tree().physics_frame
	var arrow := _loose(root, Vector2(60, 100))   # 56 px before the wall's face at x 116
	var furthest := 0.0
	for i in 40:
		await get_tree().physics_frame
		if not is_instance_valid(arrow):
			break
		furthest = arrow.global_position.x
	assert_bool(is_instance_valid(arrow)).is_false()
	assert_float(furthest).is_less(164.0)   # never beyond the wall's far face
