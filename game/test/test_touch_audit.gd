extends GdUnitTestSuite

const Audit = preload("res://tools/touch_audit.gd")

func _targets() -> Array:
	return [{"id": "control", "rect": Rect2(100, 100, 44, 22)}]

func test_actual_scale_makes_22_texels_44_pixels_at_two_x_only() -> void:
	var two := Audit.audit(Vector2(1920, 1080), 1, "fill", _targets())
	assert_bool(two.ok).is_true()
	assert_bool(two.passes).is_true()
	assert_float(two.targets[0].height_points).is_equal(44.0)
	var one := Audit.audit(Vector2(960, 540), 1, "fill", _targets())
	assert_bool(one.ok).is_true()
	assert_bool(one.passes).is_false()
	assert_bool(one.targets[0].undersized).is_true()
	assert_str(one.findings[0].rule).is_equal("touch.minimum")

func test_hidpi_equivalent_windows_have_equal_logical_target_sizes() -> void:
	var one := Audit.audit(Vector2(874, 402), 1, "fill", _targets())
	var three := Audit.audit(Vector2(2622, 1206), 3, "fill", _targets())
	assert_float(one.targets[0].height_points).is_equal_approx(three.targets[0].height_points, 0.00001)
	assert_float(one.targets[0].height_points).is_less(17)
	assert_bool(three.targets[0].undersized).is_true()

func test_whole_mode_reports_clipped_world_in_small_windows() -> void:
	var fill := Audit.audit(Vector2(874, 402), 1, "fill", _targets())
	var whole := Audit.audit(Vector2(874, 402), 1, "whole", _targets())
	assert_bool(fill.world_clipped).is_false()
	assert_bool(whole.world_clipped).is_true()
	assert_float(whole.scale).is_equal(1.0)

func test_safe_area_clipping_is_separate_from_target_minimum() -> void:
	var targets := [{"id": "edge", "rect": Rect2(0, 0, 44, 44)}]
	var result := Audit.audit(Vector2(960, 540), 1, "fill", targets, Vector4(10, 5, 0, 0))
	assert_bool(result.targets[0].undersized).is_false()
	assert_bool(result.targets[0].clipped).is_true()
	assert_float(result.targets[0].visible_width_points).is_equal(34.0)
	assert_float(result.targets[0].visible_height_points).is_equal(39.0)
	assert_str(result.findings[0].rule).is_equal("touch.clipped")

func test_both_dimensions_and_completely_offscreen_targets_are_checked() -> void:
	var targets := [{"id": "thin", "rect": Rect2(100, 100, 20, 50)}, {"id": "outside", "rect": Rect2(1000, 1000, 50, 50)}]
	var result := Audit.audit(Vector2(960, 540), 1, "fill", targets)
	assert_bool(result.targets[0].undersized).is_true()
	assert_bool(result.targets[1].clipped).is_true()
	assert_float(result.targets[1].visible_width_points).is_equal(0.0)

func test_empty_inventory_is_not_a_touch_pass() -> void:
	var result := Audit.audit(Vector2(960, 540), 1, "fill", [])
	assert_bool(result.ok).is_true()
	assert_bool(result.passes).is_false()

func test_malformed_input_is_diagnostic_not_a_pass() -> void:
	for window in [null, Vector2.ZERO, Vector2(-1, 540), Vector2(INF, 540), Vector2(NAN, 540)]:
		assert_bool(Audit.audit(window, 1, "fill", _targets()).ok).is_false()
	for dpr in [null, true, 0, -1, INF, NAN, "3"]:
		assert_bool(Audit.audit(Vector2(960, 540), dpr, "fill", _targets()).ok).is_false()
	for rows in [null, {}, [null], [{}], [{"id": "x", "rect": Rect2(0, 0, -1, 44)}], [{"id": "x", "rect": Rect2(0, 0, 44, 44)}, {"id": "x", "rect": Rect2(0, 0, 44, 44)}]]:
		assert_bool(Audit.audit(Vector2(960, 540), 1, "fill", rows).ok).is_false()
	assert_bool(Audit.audit(Vector2(960, 540), 1, "bad", _targets()).ok).is_false()
	assert_bool(Audit.audit(Vector2(960, 540), 1, "fill", _targets(), Vector4(960, 0, 0, 0)).ok).is_false()

func test_input_and_output_ownership_are_independent() -> void:
	var targets := _targets()
	var before := targets.duplicate(true)
	var result := Audit.audit(Vector2(960, 540), 1, "fill", targets)
	result.targets[0].id = "changed"
	assert_array(targets).is_equal(before)

func test_actual_pause_menu_buttons_are_measured_without_changing_settings() -> void:
	var before := SaveGame.data.duplicate(true)
	var menu: Control = auto_free(load("res://ui/pause_menu.gd").new())
	add_child(menu)
	await get_tree().process_frame
	await get_tree().process_frame
	var targets := Audit.measure_controls(menu)
	assert_int(targets.size()).is_equal(4)
	for target in targets:
		assert_float(target.rect.size.y).is_equal(float(UiStyle.TOUCH))
	var result := Audit.audit(Vector2(874, 402), 1, "fill", targets)
	assert_bool(result.ok).is_true()
	assert_int(result.findings.size()).is_greater_equal(4)
	for target in result.targets:
		assert_bool(target.undersized).is_true()
	assert_dict(SaveGame.data).is_equal(before)

func test_finite_values_that_overflow_projection_are_not_successful_audits() -> void:
	var targets := [{"id": "huge", "rect": Rect2(1.0e38, 0, 1.0e38, 44)}]
	assert_bool(Audit.audit(Vector2(3840, 2160), 1, "fill", targets).ok).is_false()
