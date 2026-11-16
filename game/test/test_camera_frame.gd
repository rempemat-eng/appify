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

## Mac desktops (16:10 and taller, Retina pixels) and the usual 16:9 ones, windowed and fullscreen.
const WINDOWS := [Vector2(1440, 900), Vector2(1512, 982), Vector2(1470, 956), Vector2(1728, 1117),
	Vector2(2560, 1600), Vector2(3024, 1964), Vector2(3456, 2234), Vector2(3456, 2112), Vector2(1920, 1080),
	Vector2(1366, 768), Vector2(960, 540), Vector2(2560, 1080), Vector2(1080, 1920)]

func test_the_picture_is_centred_and_inside_the_window_at_every_size_in_both_scales() -> void:
	const Screen := preload("res://main/pixel_screen.gd")
	for win: Vector2 in WINDOWS:
		for mode: String in ["fill", "whole"]:
			var k: float = Screen.choose_scale(win, mode)
			var at: Vector2 = Screen.picture_at(win, k)
			var picture := Rect2(at, Screen.ART * k)
			assert_bool(Rect2(Vector2.ZERO, win).encloses(picture)).override_failure_message(
				"%s %s: the picture %s leaves the window" % [win, mode, picture]).is_true()
			# bars of the same size on both sides (the picture's top left is on a whole pixel, its size need not be)
			var right := win - picture.end
			assert_float(absf(right.x - at.x)).is_less(2.0)
			assert_float(absf(right.y - at.y)).is_less(2.0)
			# fill touches two sides; whole leaves less than one more step of bars
			if mode == "fill":
				assert_bool(is_equal_approx(picture.size.x, win.x) or is_equal_approx(picture.size.y, win.y)).is_true()
			else:
				assert_bool(Screen.ART.x * (k + 1.0) > win.x or Screen.ART.y * (k + 1.0) > win.y).is_true()

func test_the_window_never_opens_bigger_than_the_screen() -> void:
	const Screen := preload("res://main/pixel_screen.gd")
	# the project's 1920 x 1080 fits a 1920 x 1200 desktop as it is
	assert_vector(Vector2(Screen.window_size_for(Vector2i(1920, 1080), Vector2i(1920, 1175)))).is_equal(Vector2(1920, 1080))
	for room: Vector2i in [Vector2i(1440, 875), Vector2i(1280, 775), Vector2i(1366, 728), Vector2i(1512, 950), Vector2i(1080, 1890)]:
		var size: Vector2i = Screen.window_size_for(Vector2i(1920, 1080), room)
		assert_bool(size.x <= room.x and size.y <= room.y).override_failure_message("%s on %s" % [size, room]).is_true()
		assert_float(float(size.x) / float(size.y)).is_equal_approx(16.0 / 9.0, 0.01)

func test_the_camera_keeps_the_player_in_view_after_the_window_is_resized() -> void:
	# Matt's Mac, 16 Nov: after fullscreen the phantom camera's frame was the window's size (its manager
	# takes the root window's size on every resize), so in the 1728-texel woodland the camera's centre was
	# held at 982 at 3024 x 1964 and the player walked out of the picture.
	const Screen := preload("res://main/pixel_screen.gd")
	SaveGame.reset()
	# drawn in a 960 x 540 SubViewport, as main.tscn draws it
	var world: SubViewport = auto_free(SubViewport.new())
	world.size = Vector2i(Screen.ART)
	add_child(world)
	var g: Node2D = load("res://game.tscn").instantiate()
	world.add_child(g)
	var cam := g.get_node("Camera2D") as Camera2D
	var manager := get_tree().root.get_node("PhantomCameraManager")
	var was: Vector2i = manager.screen_size
	Zones.go_to("woodland", "start")
	# the fault as it was: a frame of the window's size stops the camera short of the south end
	manager.screen_size = Vector2i(3024, 1964)
	g.player.global_position = Vector2(505, 1660)
	for i in 90:
		await get_tree().physics_frame
	assert_float(absf(cam.get_screen_center_position().y - g.player.global_position.y)).is_greater(270.0)
	# the pixel screen keeps the frame at the picture's size through a resize mid-play
	Screen.pin_camera_frame(get_tree(), Vector2i(Screen.ART))
	get_tree().root.size_changed.emit()
	assert_vector(Vector2(manager.screen_size)).is_equal(Screen.ART)
	for spot: Vector2 in [Vector2(505, 1660), Vector2(410, 160), Vector2(910, 735), Vector2(130, 1150)]:
		g.player.global_position = spot
		for i in 90:
			await get_tree().physics_frame
		var on_screen: Vector2 = g.player.get_global_transform_with_canvas().origin
		assert_bool(Rect2(Vector2.ZERO, Screen.ART).grow(-24.0).has_point(on_screen)).override_failure_message(
			"the player at %s is at %s on the picture" % [spot, on_screen]).is_true()
	# and the manager no longer listens to the window: another resize leaves the frame alone
	get_tree().root.size_changed.emit()
	assert_vector(Vector2(manager.screen_size)).is_equal(Screen.ART)
	manager.screen_size = was if was != Vector2i(3024, 1964) else Vector2i(Screen.ART)
	Zones.current = null

func test_the_real_main_scene_keeps_the_player_in_the_picture_after_a_real_resize() -> void:
	# after the auditor's reproduction on #506: the real main.tscn and a real resize of the root window to a
	# Retina 16:10 size; it failed on the base (the player off the picture) and passes with the pin
	SaveGame.reset()
	var root := get_tree().root
	var was_size := root.size
	var main: Node = auto_free(load("res://main.tscn").instantiate())
	add_child(main)
	await get_tree().process_frame
	var manager := root.get_node("PhantomCameraManager")
	root.size = Vector2i(3024, 1964)
	root.size_changed.emit()
	await get_tree().process_frame
	assert_vector(Vector2(manager.screen_size)).is_equal(Vector2(960, 540))
	var g: Node = main.get_node("Screen/World/Game")
	Zones.go_to("woodland", "start")
	for spot: Vector2 in [Vector2(505, 1660), Vector2(910, 735), Vector2(130, 1150), Vector2(410, 160)]:
		g.player.global_position = spot
		for i in 90:
			await get_tree().physics_frame
		var on: Vector2 = g.player.get_global_transform_with_canvas().origin
		assert_bool(Rect2(Vector2.ZERO, Vector2(960, 540)).grow(-24.0).has_point(on)).override_failure_message(
			"the player at %s is at %s on the picture" % [spot, on]).is_true()
	root.size = was_size
	root.size_changed.emit()
	manager.screen_size = Vector2i(960, 540)
	Zones.current = null
