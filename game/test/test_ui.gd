extends GdUnitTestSuite
## The interface (ui/): the pixel font draws without antialiasing or ligatures, the HUD's pictures sit on
## the art grid at their drawn sizes, and the pause menu follows the pause, sets reduced motion and the
## pixel scale in the save, and keeps every row at least 44 screen px tall at 2x.

func before_test() -> void:
	SaveGame.reset()

func after_test() -> void:
	get_tree().paused = false
	SaveGame.reset()

func test_pixel_font_is_crisp() -> void:
	var v := UiStyle.font() as FontVariation
	assert_object(v).is_not_null()
	var f := v.base_font as FontFile
	assert_int(f.antialiasing).is_equal(TextServer.FONT_ANTIALIASING_NONE)
	assert_int(f.hinting).is_equal(TextServer.HINTING_NONE)
	assert_int(f.subpixel_positioning).is_equal(TextServer.SUBPIXEL_POSITIONING_DISABLED)
	var liga := TextServerManager.get_primary_interface().name_to_tag("liga")
	assert_int(int(v.opentype_features.get(liga, 1))).is_equal(0)

func test_hud_pictures_on_the_grid() -> void:
	var sizes := {"heart_full": Vector2i(11, 10), "heart_empty": Vector2i(11, 10), "roll_full": Vector2i(9, 9),
		"roll_empty": Vector2i(9, 9), "glint": Vector2i(9, 11), "panel": Vector2i(12, 12), "key": Vector2i(9, 9)}
	for n in sizes:
		var t: Texture2D = load("res://ui/art/%s.png" % n)
		assert_object(t).is_not_null()
		assert_vector(Vector2(t.get_size())).is_equal(Vector2(sizes[n]))

func test_pause_menu_follows_the_pause_and_sets_settings() -> void:
	var menu: PanelContainer = auto_free(preload("res://ui/pause_menu.gd").new())
	add_child(menu)
	await await_idle_frame()
	assert_bool(menu.visible).is_false()
	get_tree().paused = true
	await await_idle_frame()
	assert_bool(menu.visible).is_true()
	var buttons := menu.find_children("*", "Button", true, false)
	assert_int(buttons.size()).is_equal(4)
	for b: Button in buttons:
		assert_float(b.size.y).is_greater_equal(UiStyle.TOUCH)
	(buttons[1] as Button).pressed.emit()
	assert_bool(SaveGame.setting("reduced_motion", false)).is_true()
	(buttons[2] as Button).pressed.emit()
	assert_str(str(SaveGame.setting("pixel_scale", "fill"))).is_equal("whole")
	(buttons[0] as Button).pressed.emit()
	assert_bool(get_tree().paused).is_false()
	await await_idle_frame()
	assert_bool(menu.visible).is_false()
