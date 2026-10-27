extends GdUnitTestSuite
## W2: the packed scene is the authoring record, independent of a JSON sidecar.

const Tool := preload("res://tools/kit_zone.gd")
const LAB := "res://kit/zones/kitlab.json"

func _fixture() -> Dictionary:
	return {
		"zone": "w2_fixture",
		"note": "Every editable field, with future metadata preserved.",
		"legend": {".": "lawn", "#": "path", "~": "water"},
		"rows": [".##~~~", "..#~~~", "......", "......"],
		"tiers": ["001100", "001100", "000000", "000000"],
		"flow": ["..>>>>", "..vv..", "<<....", "..^..."],
		"variants": ["......", "....a.", "......", "......"],
		"lab": true,
		"bake": false,
		"pieces": [
			{"id": "bench/a", "piece": "woodland_forest_bench", "at": [36.5, 72], "variant": "forest_bench", "facing": "W", "stage": "restored", "future": {"tag": "keep"}},
			{"piece": "woodland_boulder", "at": [108, 84], "variant": "b4"},
		],
		"doors": [
			{"id": "east", "rect": [5, 1, 1, 2], "to": "crossroads", "spawn": "woodland", "if": {"flags": ["opened"]}},
			{"id": "south", "rect": [2, 3, 2, 1], "target_zone": "woodland", "target_spawn": "start"},
		],
		"spawns": {"start": [18, 84], "return": [120, 60]},
		"future": {"z": [3, 2, 1], "a": {"keep": true}},
	}

func _scene(plan: Dictionary) -> Node2D:
	var root := Tool.scene_from_plan(plan)
	assert_object(root).is_not_null()
	if root != null:
		auto_free(root)
	return root

func _persist(root: Node2D, suffix: String) -> Node2D:
	var path := "user://w2_roundtrip_%s.tscn" % suffix
	var packed := PackedScene.new()
	assert_int(packed.pack(root)).is_equal(OK)
	assert_int(ResourceSaver.save(packed, path)).is_equal(OK)
	var reloaded := ResourceLoader.load(path, "PackedScene", ResourceLoader.CACHE_MODE_IGNORE) as PackedScene
	assert_object(reloaded).is_not_null()
	if reloaded == null:
		return null
	var result := reloaded.instantiate() as Node2D
	auto_free(result)
	assert_int(DirAccess.remove_absolute(path)).is_equal(OK)
	return result

func _assert_plan(actual: Dictionary, expected: Dictionary) -> void:
	assert_str(Tool.canonical(actual)).is_equal(Tool.canonical(expected))

func test_kitlab_packed_round_trip_needs_no_json_sidecar() -> void:
	var original: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(LAB))
	var root := _scene(original)
	if root == null:
		return
	var reloaded := _persist(root, "lab")
	if reloaded == null:
		return
	# Nothing at the generated zone's default JSON path is required by this API.
	_assert_plan(Tool.plan_from_scene(reloaded), original)
	assert_bool(reloaded.has_meta(&"kit_zone_plan")).is_true()

func test_pre_w2_committed_scene_exports_with_legacy_fallback() -> void:
	var packed := load("res://zones/kitlab/kitlab.tscn") as PackedScene
	var legacy := packed.instantiate() as Node2D
	auto_free(legacy)
	assert_bool(legacy.has_meta(&"kit_zone_plan")).is_false()
	assert_object(legacy.get_node_or_null("Doors")).is_null()
	var original: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(LAB))
	_assert_plan(Tool.plan_from_scene(legacy, original), original)

func test_comprehensive_packed_round_trip_preserves_every_field() -> void:
	var original := _fixture()
	var root := _scene(original)
	if root == null:
		return
	var reloaded := _persist(root, "all_fields")
	if reloaded == null:
		return
	_assert_plan(Tool.plan_from_scene(reloaded), original)
	var first := reloaded.get_node("Props").get_child(0) as KitPiece
	assert_str(String(first.get_meta(&"facing"))).is_equal("W")
	assert_str(String(first.get_meta(&"stage"))).is_equal("restored")
	assert_that(first.position).is_equal(Vector2(36.5, 72))
	var door := reloaded.get_node("Doors/east") as Door
	assert_that(door.position).is_equal(Vector2(132, 48))
	assert_that((door.get_node("Shape").shape as RectangleShape2D).size).is_equal(Vector2(24, 48))
	assert_str(door.target_zone).is_equal("crossroads")
	assert_str(door.target_spawn).is_equal("woodland")
	assert_that(JSON.parse_string(door.only_if)).is_equal({"flags": ["opened"]})
	var flow := reloaded.get_node("Ground/Flow") as TileMapLayer
	assert_float(flow.self_modulate.a).is_equal(0.0)
	assert_str(String(flow.get_cell_tile_data(Vector2i(2, 0)).get_custom_data("flow"))).is_equal(">")

func test_painting_one_cell_changes_exactly_one_row() -> void:
	var original := _fixture()
	var root := _scene(original)
	if root == null:
		return
	var cells := root.get_node("Ground/Cells") as TileMapLayer
	cells.set_cell(Vector2i(0, 2), 0, TerrainKit.shared().atlas_coords("path"))
	var expected := original.duplicate(true)
	expected.rows[2] = "#....."
	_assert_plan(Tool.plan_from_scene(root), expected)
	# Export neither mutates the caller's plan nor replays its old row blindly.
	assert_str(original.rows[2]).is_equal("......")

func test_scene_edits_to_tiers_flow_pieces_doors_and_spawns_are_exported() -> void:
	var original := _fixture()
	var root := _scene(original)
	if root == null:
		return
	var expected := original.duplicate(true)
	var tiers := root.get_node("Ground/Tiers") as TileMapLayer
	tiers.set_cell(Vector2i(0, 0), 0, Vector2i(2, 0))
	expected.tiers[0] = "201100"
	var flow := root.get_node("Ground/Flow") as TileMapLayer
	var glyphs: Array = flow.get_meta(&"glyphs")
	flow.set_cell(Vector2i(0, 0), 0, Vector2i(glyphs.find("^"), 0))
	expected.flow[0] = "^.>>>>"
	var piece := root.get_node("Props").get_child(0) as KitPiece
	piece.position += Vector2(12, 24)
	piece.set_meta(&"facing", "N")
	piece.set_meta(&"stage", "broken")
	expected.pieces[0].at = [48.5, 96]
	expected.pieces[0].facing = "N"
	expected.pieces[0].stage = "broken"
	var door := root.get_node("Doors/east") as Door
	door.position += Vector2(24, 0)
	door.target_zone = "undercroft"
	door.target_spawn = "hatch"
	door.only_if = ""
	expected.doors[0].rect = [6, 1, 1, 2]
	expected.doors[0].to = "undercroft"
	expected.doors[0].spawn = "hatch"
	expected.doors[0].erase("if")
	(root.get_node("Spawns/return") as Marker2D).position = Vector2(48, 84)
	expected.spawns["return"] = [48, 84]
	_assert_plan(Tool.plan_from_scene(root), expected)

func test_deleting_authored_nodes_does_not_resurrect_template_data() -> void:
	var original := _fixture()
	var root := _scene(original)
	if root == null:
		return
	root.get_node("Ground/Tiers").free()
	root.get_node("Ground/Flow").free()
	root.get_node("Props").get_child(0).free()
	root.get_node("Doors/east").free()
	root.get_node("Spawns/return").free()
	var expected := original.duplicate(true)
	expected.erase("tiers")
	expected.erase("flow")
	expected.pieces.remove_at(0)
	expected.doors.remove_at(0)
	expected.spawns.erase("return")
	_assert_plan(Tool.plan_from_scene(root), expected)

func test_explicit_cell_coordinates_scale_pieces_spawns_and_door_geometry() -> void:
	var original := _fixture()
	original["coordinate_space"] = "cells"
	original.pieces[0].at = [1.5, 3]
	original.pieces[1].at = [4.5, 3.5]
	original.spawns = {"start": [0.75, 3.5]}
	var root := _scene(original)
	if root == null:
		return
	assert_that((root.get_node("Props").get_child(0) as Node2D).position).is_equal(Vector2(36, 72))
	assert_that((root.get_node("Spawns/start") as Node2D).position).is_equal(Vector2(18, 84))
	assert_that((root.get_node("Doors/east") as Node2D).position).is_equal(Vector2(132, 48))
	var reloaded := _persist(root, "cell_units")
	if reloaded != null:
		_assert_plan(Tool.plan_from_scene(reloaded), original)

func test_missing_optional_fields_stay_absent() -> void:
	var original := {"zone": "w2_minimal", "legend": {".": "lawn"}, "rows": ["..", ".."]}
	var root := _scene(original)
	if root == null:
		return
	assert_object(root.get_node_or_null("Spawns/start")).is_not_null()
	_assert_plan(Tool.plan_from_scene(root), original)

func test_gameplay_from_is_persisted_and_explicit_spawn_override_wins() -> void:
	var original := {
		"zone": "w2_gameplay",
		"legend": {".": "lawn"},
		"rows": ["....", "....", "....", "...."],
		"gameplay_from": "res://zones/woodland/woodland.tscn",
		"spawns": {"start": [36, 48]},
	}
	var root := _scene(original)
	if root == null:
		return
	var reloaded := _persist(root, "gameplay")
	if reloaded == null:
		return
	assert_object(reloaded.get_node_or_null("Actors/StoneSign")).is_not_null()
	assert_object(reloaded.get_node_or_null("Actors/MeadowCamp")).is_not_null()
	assert_object(reloaded.get_node_or_null("Doors/ToCrossroads/Shape")).is_not_null()
	assert_str((reloaded.get_node("Doors/ToCrossroads") as Door).target_spawn).is_equal("woodland")
	assert_that((reloaded.get_node("Spawns/start") as Marker2D).position).is_equal(Vector2(36, 48))
	_assert_plan(Tool.plan_from_scene(reloaded), original)

func test_inherited_gameplay_edits_export_as_overrides() -> void:
	var original := {"zone": "w2_inherited_edits", "legend": {".": "lawn"}, "rows": ["....", "...."], "gameplay_from": "res://zones/woodland/woodland.tscn"}
	var root := _scene(original)
	if root == null:
		return
	(root.get_node("Spawns/start") as Marker2D).position = Vector2(24, 48)
	(root.get_node("Doors/ToCrossroads") as Door).target_spawn = "new_return"
	var plan := Tool.plan_from_scene(root)
	assert_that(plan.spawns).is_equal({"start": [24.0, 48.0]})
	assert_int(plan.doors.size()).is_equal(1)
	assert_str(plan.doors[0].id).is_equal("ToCrossroads")
	assert_str(plan.doors[0].spawn).is_equal("new_return")
	var rebuilt := _scene(plan)
	if rebuilt != null:
		assert_that((rebuilt.get_node("Spawns/start") as Marker2D).position).is_equal(Vector2(24, 48))
		assert_str((rebuilt.get_node("Doors/ToCrossroads") as Door).target_spawn).is_equal("new_return")

func test_unchanged_fractional_positions_keep_json_precision() -> void:
	var original := _fixture()
	original.pieces[0].at = [36.123456789, 72.987654321]
	original.spawns["start"] = [18.123456789, 84.987654321]
	var root := _scene(original)
	if root == null:
		return
	var reloaded := _persist(root, "fractional")
	if reloaded != null:
		_assert_plan(Tool.plan_from_scene(reloaded), original)

func test_rejects_malformed_dimensions_and_coordinate_space() -> void:
	for field in ["rows", "tiers", "flow", "variants"]:
		var plan := _fixture()
		plan[field] = ["."]
		assert_object(Tool.scene_from_plan(plan)).is_null()
	var bad := _fixture()
	bad["coordinate_space"] = "guessed"
	assert_object(Tool.scene_from_plan(bad)).is_null()
	bad = _fixture()
	bad.tiers[0] = "00x100"
	assert_object(Tool.scene_from_plan(bad)).is_null()
	bad = _fixture()
	bad.tiers[0] = "004100"
	assert_object(Tool.scene_from_plan(bad)).is_null()
	bad = _fixture()
	bad.flow[0] = "..X..."
	assert_object(Tool.scene_from_plan(bad)).is_null()

func test_canonical_json_sorts_nested_keys_and_preserves_array_order() -> void:
	var a := {"z": {"b": 2, "a": 1}, "a": [3, 2, 1]}
	var b := {"a": [3, 2, 1], "z": {"a": 1, "b": 2}}
	assert_str(Tool.canonical(a)).is_equal(Tool.canonical(b))
	assert_that(JSON.parse_string(Tool.canonical(a)).a).is_equal([3.0, 2.0, 1.0])
	assert_bool(Tool.canonical(a).ends_with("\n")).is_true()
