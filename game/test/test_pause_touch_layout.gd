extends GdUnitTestSuite

const Audit := preload("res://tools/touch_audit.gd")
const Screen := preload("res://main/pixel_screen.gd")

func _menu() -> Control:
	var menu: Control = auto_free(load("res://ui/pause_menu.gd").new())
	add_child(menu)
	menu.set_process(false)
	menu.show()
	return menu

func test_real_pause_rows_meet_44_points_in_both_modes_and_declared_ratios() -> void:
	var before := SaveGame.data.duplicate(true)
	var menu := _menu()
	for spec in [[1920, 1080, 1], [960, 540, 1], [874, 402, 1], [2622, 1206, 3], [667, 375, 1]]:
		var window := Vector2(spec[0], spec[1])
		for mode in ["fill", "whole"]:
			var k: float = Screen.choose_scale(window, mode)
			var offset := ((window - Screen.ART * k) / 2.0).floor()
			assert_bool(menu.fit_screen(window, k, offset, spec[2], Rect2(Vector2.ZERO, window))).is_true()
			await get_tree().process_frame
			await get_tree().process_frame
			var controls := Audit.measure_controls(menu)
			assert_int(controls.size()).is_equal(4)
			var result := Audit.audit(window, spec[2], mode, controls)
			assert_bool(result.ok).is_true()
			assert_bool(result.passes).override_failure_message(JSON.stringify(result)).is_true()
			for i in controls.size():
				for j in range(i + 1, controls.size()):
					assert_bool(controls[i].rect.intersects(controls[j].rect)).is_false()
	assert_dict(SaveGame.data).is_equal(before)

func test_actual_control_bounds_fit_declared_safe_insets_even_with_cropped_world() -> void:
	var menu := _menu()
	var window := Vector2(2622, 1206)
	var ratio := 3.0
	var insets := Vector4(30, 12, 16, 18)
	var safe := Rect2(Vector2(insets.x, insets.y) * ratio, window - Vector2(insets.x + insets.z, insets.y + insets.w) * ratio)
	for mode in ["fill", "whole"]:
		var k: float = Screen.choose_scale(window, mode)
		var offset := ((window - Screen.ART * k) / 2.0).floor()
		assert_bool(menu.fit_screen(window, k, offset, ratio, safe)).is_true()
		await get_tree().process_frame
		await get_tree().process_frame
		var result := Audit.audit(window, ratio, mode, Audit.measure_controls(menu), insets)
		assert_bool(result.passes).override_failure_message(JSON.stringify(result)).is_true()

func test_screen_layout_preserves_action_connections_and_cyclic_focus_order() -> void:
	var menu := _menu()
	var buttons: Array = menu.get("_buttons")
	var methods := ["_resume", "_toggle_motion", "_toggle_scale", "_quit"]
	assert_int(buttons.size()).is_equal(4)
	for i in buttons.size():
		var button: Button = buttons[i]
		assert_bool(button.pressed.is_connected(Callable(menu, methods[i]))).is_true()
		assert_object(button.get_node(button.focus_neighbor_top)).is_same(buttons[(i + 3) % 4])
		assert_object(button.get_node(button.focus_neighbor_bottom)).is_same(buttons[(i + 1) % 4])

func test_invalid_projection_does_not_change_last_valid_layout_or_settings() -> void:
	var before := SaveGame.data.duplicate(true)
	var menu := _menu()
	assert_bool(menu.fit_screen(Vector2(960, 540), 1.0, Vector2.ZERO, 1.0, Rect2(0, 0, 960, 540))).is_true()
	await get_tree().process_frame
	await get_tree().process_frame
	var targets := Audit.measure_controls(menu)
	for scale_ in [0.0, -1.0, NAN, INF]:
		assert_bool(menu.fit_screen(Vector2(960, 540), scale_, Vector2.ZERO, 1.0, Rect2(0, 0, 960, 540))).is_false()
	assert_bool(menu.fit_screen(Vector2(960, 540), 1.0, Vector2.ZERO, 0.0, Rect2(0, 0, 960, 540))).is_false()
	assert_bool(menu.fit_screen(Vector2(960, 540), 1.0, Vector2.ZERO, 1.0, Rect2(-1, 0, 960, 540))).is_false()
	assert_array(Audit.measure_controls(menu)).is_equal(targets)
	assert_dict(SaveGame.data).is_equal(before)

func test_pixel_screen_delivers_projection_to_menu_inside_real_subviewport() -> void:
	var host: Node = auto_free(Screen.new())
	var container := SubViewportContainer.new()
	container.name = "Screen"
	host.add_child(container)
	var viewport := SubViewport.new()
	viewport.size = Vector2i(Screen.ART)
	container.add_child(viewport)
	var canvas := CanvasLayer.new()
	viewport.add_child(canvas)
	var menu: Control = load("res://ui/pause_menu.gd").new()
	canvas.add_child(menu)
	add_child(host)
	menu.set_process(false)
	menu.show()
	await get_tree().process_frame
	await get_tree().process_frame
	var window := Vector2(get_window().size)
	var ratio := DisplayServer.screen_get_scale()
	if not is_finite(ratio) or ratio <= 0.0:
		ratio = 1.0
	assert_float(menu.get("_screen_scale")).is_equal(host.scale_k)
	assert_vector(menu.get("_screen_offset")).is_equal(container.position)
	assert_vector(menu.get("_safe_pixels").size).is_equal(window)
	assert_int(Audit.measure_controls(menu).size()).is_equal(4)
	# The dummy headless display may be only 64x64, which cannot fit four
	# 44-point rows. Check transport/focus here; declared usable sizes are above.
	var before := SaveGame.data.duplicate(true)
	var button: Button = menu.get("_buttons")[0]
	assert_float(button.custom_minimum_size.y).is_equal(maxf(UiStyle.TOUCH, ceilf(44.0 * ratio / host.scale_k)))
	button.grab_focus()
	assert_object(viewport.gui_get_focus_owner()).is_same(button)
	var next: Button = menu.get("_buttons")[1]
	assert_object(button.get_node(button.focus_neighbor_bottom)).is_same(next)
	next.grab_focus()
	assert_object(viewport.gui_get_focus_owner()).is_same(next)
	assert_dict(SaveGame.data).is_equal(before)
