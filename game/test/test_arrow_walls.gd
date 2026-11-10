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
	var root := _scene(true)
	await get_tree().physics_frame
	await get_tree().physics_frame
	assert_bool(_loose(root, Vector2(135, 100)).is_queued_for_deletion()).is_true()   # tip inside the wall
	assert_bool(_loose(root, Vector2(170, 100)).is_queued_for_deletion()).is_true()   # tip beyond it

func test_an_arrow_in_the_open_flies() -> void:
	var root := _scene(false)
	await get_tree().physics_frame
	await get_tree().physics_frame
	assert_bool(_loose(root, Vector2(135, 100)).is_queued_for_deletion()).is_false()
