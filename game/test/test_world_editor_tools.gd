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

func test_palette_groups_and_search_every_word() -> void:
	var fence := {"placement": {"role": "boundary", "purpose": "contain", "boundary": {"style": "wattle", "joins": ["e", "w"]}}}
	var cow := {"placement": {"role": "stock", "purpose": "live"}}
	assert_str(Tools.piece_category("fence_wattle_ew", fence)).is_equal("fences")
	assert_str(Tools.piece_category("farm_cow", cow)).is_equal("farm")
	assert_str(Tools.piece_category("commons_pump", {})).is_equal("commons")
	assert_str(Tools.piece_category("waterfall_2", {})).is_equal("water")
	assert_str(Tools.piece_category("woodland_oak", {})).is_equal("woodland")
	assert_str(Tools.piece_category("crossroads_well", {})).is_equal("village")
	assert_bool(Tools.palette_matches("farm_cow", "Cow", cow, "", "all")).is_true()
	assert_bool(Tools.palette_matches("farm_cow", "Cow", cow, "STOCK cow", "farm")).is_true()
	assert_bool(Tools.palette_matches("farm_cow", "Cow", cow, "cow pig", "")).is_false()
	assert_bool(Tools.palette_matches("farm_cow", "Cow", cow, "cow", "fences")).is_false()

func test_fence_cells_join_their_neighbours_and_a_gates_ends() -> void:
	assert_that(Tools.fence_cell(Tools.fence_foot(Vector2i(3, 5)))).is_equal(Vector2i(3, 5))
	assert_that(Tools.fence_foot(Vector2i(3, 5))).is_equal(Vector2(84, 144))
	# an L: an end, a corner, an end
	var l := Tools.fence_pieces("wattle", [Vector2i(0, 0), Vector2i(1, 0), Vector2i(1, 1)])
	assert_str(l[Vector2i(0, 0)]).is_equal("fence_wattle_e")
	assert_str(l[Vector2i(1, 0)]).is_equal("fence_wattle_sw")
	assert_str(l[Vector2i(1, 1)]).is_equal("fence_wattle_n")
	# a gate along x centred on (4, 0): the run's cell west of it joins its west end, and the
	# cell north of the gate's end does not join it
	var fixed := Tools.gate_ends(Vector2i(4, 0), ["e", "w"])
	var g := Tools.fence_pieces("rail", [Vector2i(1, 0), Vector2i(2, 0), Vector2i(3, -1)] + fixed.keys(), fixed)
	assert_str(g[Vector2i(2, 0)]).is_equal("fence_rail_ew")
	assert_str(g[Vector2i(3, -1)]).is_equal("")
	assert_bool(g.has(Vector2i(3, 0))).is_false()

func test_variants_cycle_and_cells_hash_the_same_way_every_time() -> void:
	assert_str(Tools.next_variant(["a", "b", "c"], "a")).is_equal("b")
	assert_str(Tools.next_variant(["a", "b", "c"], "c")).is_equal("a")
	assert_str(Tools.next_variant(["a", "b"], "missing")).is_equal("a")
	assert_str(Tools.next_variant([], "a")).is_equal("")
	var h := Tools.cell_hash(Vector2i(4, 9), 11)
	assert_float(h).is_equal(Tools.cell_hash(Vector2i(4, 9), 11))
	assert_bool(h >= 0.0 and h < 1.0).is_true()
	assert_bool(Tools.cell_hash(Vector2i(4, 9), 12) != h).is_true()
	assert_str(Tools.short_rule("rules.not_near")).is_equal("not near")

func test_a_door_path_snaps_to_the_door_centre_line() -> void:
	# the farm study's cottage door: its opening x 684 to 731 (centre 707.5, cell 29's middle), its foot y 288 (row 12 is before it)
	var door := {"x0": 684.0, "x1": 731.0, "y": 288.0}
	var line: Array = []
	for r in range(12, 17):
		line.append(Vector2i(30, r))
	var one := Tools.door_path_cells(line, door)
	# the two rows before the door move onto its centre line; past them the path may bend
	assert_bool(Vector2i(29, 12) in one and Vector2i(29, 13) in one).is_true()
	assert_bool(Vector2i(30, 12) in one or Vector2i(30, 13) in one).is_false()
	assert_bool(Vector2i(30, 14) in one and Vector2i(30, 16) in one).is_true()
	# two cells wide where the door wants an odd run: three, centred
	var wide := Tools.door_path_cells([Vector2i(30, 12), Vector2i(31, 12), Vector2i(30, 13), Vector2i(31, 13)], door)
	var row: Array = []
	for c in wide:
		if c.y == 12:
			row.append(c.x)
	row.sort()
	assert_that(row).is_equal([28, 29, 30])
	# a door whose centre is a cell's edge (x 312 to 359, centre 335.5): a one-cell stroke becomes two, either side of it
	var edge := Tools.door_path_cells([Vector2i(12, 12), Vector2i(12, 13)], {"x0": 312.0, "x1": 359.0, "y": 288.0})
	assert_bool(Vector2i(13, 12) in edge and Vector2i(14, 12) in edge and Vector2i(12, 12) not in edge).is_true()
	# a stroke that never reaches the door's row is left as it is
	var past := Tools.door_path_cells([Vector2i(30, 14), Vector2i(30, 15)], door)
	assert_that(past).is_equal([Vector2i(30, 14), Vector2i(30, 15)])

func test_a_gate_takes_the_span_centred_on_its_path() -> void:
	assert_int(Tools.centred_span([204.0, 180.0, 228.0, 156.0, 252.0], 252.0)).is_equal(4)
	assert_int(Tools.centred_span([204.0, 180.0, 228.0], 216.0)).is_equal(0)   # a two-cell path: no span centres, the nearest first
	assert_int(Tools.centred_span([204.0, 180.0], NAN)).is_equal(0)
	assert_int(Tools.centred_span([], 10.0)).is_equal(-1)
