extends GdUnitTestSuite
## Authoring geometry: coordinates and footprints, independent of viewport sampling or art.

const Tools := preload("res://addons/world_editor/tools.gd")

func test_snap_matches_piece_schema_and_keeps_free_coordinates() -> void:
	assert_that(Tools.snap(Vector2(17, 37), "cell")).is_equal(Vector2(12, 48))
	assert_that(Tools.snap(Vector2(-17, -37), "cell")).is_equal(Vector2(-12, -48))
	assert_that(Tools.snap(Vector2(17, 37), "half")).is_equal(Vector2(12, 36))
	for mode in ["free", "none", "unknown"]:
		assert_that(Tools.snap(Vector2(17.25, -37.75), mode)).is_equal(Vector2(17.25, -37.75))
	assert_that(Tools.snap(Vector2(17.25, -37.75), "pixel")).is_equal(Vector2(17, -38))
	assert_that(Tools.snap(Vector2(5, 11), "cell", 8)).is_equal(Vector2(4, 8))
	assert_that(Tools.snap(Vector2(2.25, 3.5), "cell", 0)).is_equal(Vector2(2.25, 3.5))

func test_brush_and_rectangle_have_exact_inclusive_spans() -> void:
	assert_that(Tools.brush_cells(Vector2i(-2, 4), 1)).is_equal([Vector2i(-2, 4)])
	assert_that(Tools.brush_cells(Vector2i(-2, 4), 2)).is_equal([Vector2i(-2, 4), Vector2i(-1, 4), Vector2i(-2, 5), Vector2i(-1, 5)])
	assert_int(Tools.brush_cells(Vector2i.ZERO, 3).size()).is_equal(9)
	assert_that(Tools.rectangle_cells(Vector2i(2, 0), Vector2i(-1, -1))).is_equal([
		Vector2i(-1, -1), Vector2i(0, -1), Vector2i(1, -1), Vector2i(2, -1),
		Vector2i(-1, 0), Vector2i(0, 0), Vector2i(1, 0), Vector2i(2, 0)])

func test_brush_continuity_fills_pointer_jumps_in_both_directions() -> void:
	for endpoints in [[Vector2i(-4, 2), Vector2i(3, -2)], [Vector2i.ZERO, Vector2i(5, 5)], [Vector2i(-3, -4), Vector2i(-3, 5)]]:
		var cells := Tools.line_cells(endpoints[0], endpoints[1])
		assert_that(cells.front()).is_equal(endpoints[0])
		assert_that(cells.back()).is_equal(endpoints[1])
		for i in range(1, cells.size()):
			assert_int(absi(cells[i].x - cells[i - 1].x) + absi(cells[i].y - cells[i - 1].y)).is_equal(1)
		var backwards := Tools.line_cells(endpoints[1], endpoints[0])
		backwards.reverse()
		assert_that(backwards).is_equal(cells)
	assert_that(Tools.line_cells(Vector2i.ONE, Vector2i.ONE)).is_equal([Vector2i.ONE])

func test_route_straights_are_exactly_two_or_three_cells_wide() -> void:
	for width in [2, 3]:
		var horizontal := Tools.route_cells([Vector2i(-5, -2), Vector2i(8, -2)], width)
		var vertical := Tools.route_cells([Vector2i(2, -5), Vector2i(2, 8)], width)
		for x in range(-4, 8):
			assert_int(_in_column(horizontal, x)).is_equal(width)
		for y in range(-4, 8):
			assert_int(_in_row(vertical, y)).is_equal(width)
		assert_bool(horizontal.has(Vector2i.ZERO)).is_false()
		assert_bool(vertical.has(Vector2i(10, 0))).is_false()

func test_route_turn_caps_and_negative_coordinates_remain_connected() -> void:
	var waypoints := [Vector2i(-8, -3), Vector2i(4, -3), Vector2i(4, 8)]
	for width in [2, 3]:
		var cells := Tools.route_cells(waypoints, width)
		assert_bool(cells.has(Vector2i(-8, -3))).is_true()
		assert_bool(cells.has(Vector2i(4, 8))).is_true()
		assert_bool(cells.has(Vector2i(4, -3))).is_true()
		assert_int(_in_column(cells, -3)).is_equal(width)
		assert_int(_in_row(cells, 4)).is_equal(width)
		assert_int(_reachable_count(cells)).is_equal(cells.size())
		var reversed := waypoints.duplicate()
		reversed.reverse()
		assert_that(Tools.route_cells(reversed, width)).is_equal(cells)

func test_route_deduplicates_sorts_and_simplifies_sampling_staircases() -> void:
	var sampled: Array = []
	for i in range(-5, 7):
		sampled.append(Vector2i(i, i))
		sampled.append(Vector2i(i + 1, i))
	var cells := Tools.route_cells(sampled, 3)
	assert_that(cells).is_equal(Tools.route_cells([sampled.front(), sampled.back()], 3))
	var backwards := sampled.duplicate()
	backwards.reverse()
	assert_that(Tools.route_cells(backwards, 3)).is_equal(cells)
	var repeated := sampled.duplicate()
	for i in range(sampled.size() - 1, -1, -1):
		repeated.append(sampled[i])
	# Retracing a route creates no duplicate painted cells.
	var retraced := Tools.route_cells(repeated, 3)
	assert_that(retraced).is_equal(cells)
	var seen: Dictionary = {}
	for cell in retraced:
		assert_bool(seen.has(cell)).is_false()
		seen[cell] = true
	for i in range(1, retraced.size()):
		assert_bool(retraced[i].y > retraced[i - 1].y or (retraced[i].y == retraced[i - 1].y and retraced[i].x > retraced[i - 1].x)).is_true()
	assert_int(_reachable_count(retraced)).is_equal(retraced.size())

func test_route_handles_empty_duplicate_and_degenerate_paths() -> void:
	assert_that(Tools.route_cells([], 3)).is_equal([])
	for width in [2, 3]:
		assert_that(Tools.route_cells([Vector2i(-4, -2), Vector2i(-4, -2)], width)).is_equal(Tools.brush_cells(Vector2i(-4, -2), width))
	assert_that(Tools.route_cells([Vector2i.ZERO, Vector2i(7, 0)], 1)).is_equal(Tools.route_cells([Vector2i.ZERO, Vector2i(7, 0)], 2))

func test_facing_is_metadata_with_predictable_forward_and_reverse_steps() -> void:
	assert_str(Tools.next_facing("s")).is_equal("w")
	assert_str(Tools.next_facing("s", -1)).is_equal("e")
	assert_str(Tools.next_facing("N", 4)).is_equal("n")
	assert_str(Tools.next_facing("s", 9)).is_equal("w")

func _in_column(cells: Array[Vector2i], x: int) -> int:
	return cells.filter(func(cell: Vector2i) -> bool: return cell.x == x).size()

func _in_row(cells: Array[Vector2i], y: int) -> int:
	return cells.filter(func(cell: Vector2i) -> bool: return cell.y == y).size()

func _reachable_count(cells: Array[Vector2i]) -> int:
	if cells.is_empty():
		return 0
	var seen: Dictionary = {cells[0]: true}
	var pending: Array[Vector2i] = [cells[0]]
	while not pending.is_empty():
		var cell: Vector2i = pending.pop_back()
		for direction in [Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN]:
			var adjacent: Vector2i = cell + direction
			if not seen.has(adjacent) and cells.has(adjacent):
				seen[adjacent] = true
				pending.append(adjacent)
	return seen.size()
