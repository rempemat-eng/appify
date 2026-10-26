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
