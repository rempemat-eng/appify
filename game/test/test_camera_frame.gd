extends GdUnitTestSuite
## Screenshots and the first frame of a zone: the camera is on the player when a zone loads (not at the
## world's origin), and the shot check refuses a frame whose quarters are black.

func test_frame_covered_refuses_a_black_quarter() -> void:
	var game := load("res://game.gd")
	var full := Image.create(192, 108, false, Image.FORMAT_RGB8)
	full.fill(Color(0.4, 0.38, 0.36))
	assert_bool(game.frame_covered(full)).is_true()
	var broken := full.duplicate()
	broken.fill_rect(Rect2i(0, 0, 192, 54), Color.BLACK)
	broken.fill_rect(Rect2i(0, 54, 96, 54), Color.BLACK)
	assert_bool(game.frame_covered(broken)).is_false()

func test_camera_is_on_the_player_when_a_zone_loads() -> void:
	SaveGame.reset()
	var g: Node2D = auto_free(load("res://game.tscn").instantiate())
	add_child(g)
	var cam := g.get_node("Camera2D") as Camera2D
	assert_float(cam.global_position.distance_to(g.player.global_position)).is_less(60.0 * 3.0)
	Zones.go_to("crossroads", "start")
	assert_float(cam.global_position.distance_to(g.player.global_position)).is_less(60.0 * 3.0)
	Zones.current = null

func test_camera_follows_the_player_again_after_a_door() -> void:
	# The player leaves the tree while zones swap, and the phantom camera drops a target that exits the
	# tree. After a door the camera stayed where the swap left it (found by playing, 10 Nov).
	SaveGame.reset()
	var g: Node2D = auto_free(load("res://game.tscn").instantiate())
	add_child(g)
	var cam := g.get_node("Camera2D") as Camera2D
	Zones.go_to("crossroads", "woodland")
	g.player.global_position = Vector2(960, 1000)  # walk on, well inside the zone's camera limits
	for i in 90:
		await get_tree().physics_frame
	assert_float(cam.global_position.distance_to(g.player.global_position)).is_less(60.0 * 3.0)
	Zones.current = null

func test_the_pause_menu_still_gets_input_while_paused() -> void:
	# The game is drawn in a SubViewport. Its container hands input on only while it may process, so it
	# must keep running when the tree is paused, or neither Esc nor Resume can end the pause.
	# read from the packed scene: making the whole game here would leave its fonts and textures behind at exit
	var state := (load("res://main.tscn") as PackedScene).get_state()
	var mode := Node.PROCESS_MODE_INHERIT
	for n in state.get_node_count():
		if state.get_node_name(n) == &"Screen":
			for p in state.get_node_property_count(n):
				if state.get_node_property_name(n, p) == &"process_mode":
					mode = state.get_node_property_value(n, p)
	assert_int(mode).is_equal(Node.PROCESS_MODE_ALWAYS)
