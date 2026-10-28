extends GdUnitTestSuite
## W2: the packed scene is the authoring record, independent of a JSON sidecar.

const Tool := preload("res://tools/kit_zone.gd")
const LAB := "res://kit/zones/kitlab.json"

func _literal_gameplay_source(suffix: String) -> String:
	var source := Node2D.new()
	var actors := Node2D.new()
	actors.name = "Actors"
	source.add_child(actors)
	actors.owner = source
	var actor := Marker2D.new()
	actor.name = "ProtectedMarker"
	actor.position = Vector2(10, 20)
	actors.add_child(actor)
	actor.owner = source
	var spawns := Node2D.new()
	spawns.name = "Spawns"
	source.add_child(spawns)
	spawns.owner = source
	var marker := Marker2D.new()
	marker.name = "StoredSpawn"
	marker.position = Vector2(30, 40)
	marker.set_meta(&"kit_zone_id", "logical/spawn")
	spawns.add_child(marker)
	marker.owner = source
	var doors := Node2D.new()
	doors.name = "Doors"
	source.add_child(doors)
	doors.owner = source
	var door := Door.new()
	door.name = "StoredDoor"
	door.position = Vector2(12, 12)
	door.target_zone = "woodland"
	door.set_meta(&"kit_zone_entry", {"id": "logical/door", "rect": [0, 0, 1, 1], "to": "woodland"})
	doors.add_child(door)
	door.owner = source
	var shape := CollisionShape2D.new()
	shape.name = "Shape"
	var rectangle := RectangleShape2D.new()
	rectangle.size = Vector2(24, 24)
	shape.shape = rectangle
	door.add_child(shape)
	shape.owner = source
	var path := "user://w2_literal_gameplay_%s.tscn" % suffix
	var packed := PackedScene.new()
	assert_int(packed.pack(source)).is_equal(OK)
	assert_int(ResourceSaver.save(packed, path)).is_equal(OK)
	source.free()
	return path

func test_literal_spawn_id_cannot_move_an_inherited_actor() -> void:
	var path := _literal_gameplay_source("actor")
	var plan := _input_plan()
	plan["gameplay_from"] = path
	plan["spawns"] = {"../Actors/ProtectedMarker": [123, 456]}
	var root := _scene(plan)
	if root != null:
		assert_that((root.get_node("Actors/ProtectedMarker") as Marker2D).position).is_equal(Vector2(10, 20))
		assert_int(root.get_node("Spawns").get_child_count()).is_equal(2)
		var saved := _persist(root, "literal_actor")
		if saved != null:
			assert_that((saved.get_node("Actors/ProtectedMarker") as Marker2D).position).is_equal(Vector2(10, 20))
			_assert_plan(Tool.plan_from_scene(saved), plan)
	assert_int(DirAccess.remove_absolute(path)).is_equal(OK)

func test_distinct_logical_ids_survive_node_name_collisions_and_disk_round_trip() -> void:
	var plan := _input_plan()
	plan["spawns"] = {}
	plan["doors"] = []
	var ids := ["a/b", "a_b", ".", "..", "start:position"]
	for i in ids.size():
		plan.spawns[ids[i]] = [12 + i * 2, 24 + i * 3]
		plan.doors.append({"id": ids[i], "rect": [i, 0, 1, 1], "to": "woodland", "future": {"ordinal": i}})
	var root := _scene(plan)
	if root == null:
		return
	assert_int(root.get_node("Spawns").get_child_count()).is_equal(ids.size())
	assert_int(root.get_node("Doors").get_child_count()).is_equal(ids.size())
	var saved := _persist(root, "colliding_ids")
	if saved == null:
		return
	var exported := Tool.plan_from_scene(saved)
	_assert_plan(exported, plan)
	var rebuilt := _scene(exported)
	if rebuilt != null:
		var saved_again := _persist(rebuilt, "colliding_ids_again")
		if saved_again != null:
			_assert_plan(Tool.plan_from_scene(saved_again), plan)

func test_inherited_logical_ids_are_overridden_without_duplicate_children() -> void:
	var path := _literal_gameplay_source("override")
	var plan := _input_plan()
	plan["gameplay_from"] = path
	plan["spawns"] = {"logical/spawn": [42, 84]}
	plan["doors"] = [{"id": "logical/door", "rect": [1, 0, 1, 1], "to": "crossroads"}]
	var root := _scene(plan)
	if root != null:
		assert_int(root.get_node("Spawns").get_child_count()).is_equal(1)
		assert_int(root.get_node("Doors").get_child_count()).is_equal(1)
		var saved := _persist(root, "logical_override")
		if saved != null:
			_assert_plan(Tool.plan_from_scene(saved), plan)
	assert_int(DirAccess.remove_absolute(path)).is_equal(OK)

func test_inherited_logical_id_removals_stay_removed_after_disk_and_rebuild() -> void:
	var path := _literal_gameplay_source("removed")
	var plan := _input_plan()
	plan["gameplay_from"] = path
	plan["spawns"] = {"explicit": [12, 24]}
	plan["gameplay_removed"] = {"Spawns": ["logical/spawn"], "Doors": ["logical/door"]}
	var root := _scene(plan)
	if root != null:
		assert_int(root.get_node("Spawns").get_child_count()).is_equal(1)
		assert_int(root.get_node("Doors").get_child_count()).is_equal(0)
		var saved := _persist(root, "logical_removed")
		if saved != null:
			var exported := Tool.plan_from_scene(saved)
			_assert_plan(exported, plan)
			var rebuilt := _scene(exported)
			if rebuilt != null:
				assert_int(rebuilt.get_node("Spawns").get_child_count()).is_equal(1)
				assert_int(rebuilt.get_node("Doors").get_child_count()).is_equal(0)
				_assert_plan(Tool.plan_from_scene(rebuilt), plan)
	assert_int(DirAccess.remove_absolute(path)).is_equal(OK)

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

func test_moved_generated_spawn_survives_saved_scene_and_plan_rebuild() -> void:
	var original := {"zone": "w2_moved_fallback", "legend": {".": "lawn"}, "rows": ["....", "...."]}
	var root := _scene(original)
	if root == null:
		return
	var start := root.get_node("Spawns/start") as Marker2D
	assert_that(start.position).is_equal(Vector2(48, 24))
	start.position = Vector2(24, 12)
	var saved := _persist(root, "moved_fallback")
	if saved == null:
		return
	var expected := original.duplicate(true)
	expected["spawns"] = {"start": [24, 12]}
	var exported := Tool.plan_from_scene(saved)
	_assert_plan(exported, expected)
	var rebuilt := _scene(exported)
	if rebuilt == null:
		return
	assert_that((rebuilt.get_node("Spawns/start") as Marker2D).position).is_equal(Vector2(24, 12))
	_assert_plan(Tool.plan_from_scene(rebuilt), expected)

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

func test_deleted_inherited_spawn_and_door_stay_removed_across_saved_round_trips() -> void:
	var original := {"zone": "w2_inherited_removals", "legend": {".": "lawn"}, "rows": ["....", "...."], "gameplay_from": "res://zones/woodland/woodland.tscn"}
	var root := _scene(original)
	if root == null:
		return
	root.get_node("Spawns/start").free()
	root.get_node("Doors/ToCrossroads").free()
	var saved := _persist(root, "inherited_removals")
	if saved == null:
		return
	var expected := original.duplicate(true)
	expected["gameplay_removed"] = {"Spawns": ["start"], "Doors": ["ToCrossroads"]}
	var exported := Tool.plan_from_scene(saved)
	_assert_plan(exported, expected)
	for pass_index in 2:
		var rebuilt := _scene(exported)
		if rebuilt == null:
			return
		assert_object(rebuilt.get_node_or_null("Spawns/start")).is_null()
		assert_object(rebuilt.get_node_or_null("Doors/ToCrossroads")).is_null()
		# Unremoved gameplay is preserved while the deleted entries stay absent.
		assert_object(rebuilt.get_node_or_null("Spawns/crossroads")).is_not_null()
		assert_object(rebuilt.get_node_or_null("Doors/ToUndercroft")).is_not_null()
		assert_object(rebuilt.get_node_or_null("Actors/StoneSign")).is_not_null()
		var reloaded := _persist(rebuilt, "inherited_removals_%s" % pass_index)
		if reloaded == null:
			return
		exported = Tool.plan_from_scene(reloaded)
		_assert_plan(exported, expected)

func test_explicit_gameplay_overrides_revive_removed_inherited_ids() -> void:
	var plan := {"zone": "w2_revived_gameplay", "legend": {".": "lawn"}, "rows": ["....", "...."], "gameplay_from": "res://zones/woodland/woodland.tscn"}
	plan["gameplay_removed"] = {"Spawns": ["start"], "Doors": ["ToCrossroads"]}
	plan["spawns"] = {"start": [24, 12]}
	plan["doors"] = [{"id": "ToCrossroads", "rect": [3, 0, 1, 2], "to": "crossroads", "spawn": "new_return"}]
	var root := _scene(plan)
	if root == null:
		return
	var saved := _persist(root, "revived_gameplay")
	if saved == null:
		return
	assert_that((saved.get_node("Spawns/start") as Marker2D).position).is_equal(Vector2(24, 12))
	assert_str((saved.get_node("Doors/ToCrossroads") as Door).target_spawn).is_equal("new_return")
	var exported := Tool.plan_from_scene(saved)
	var rebuilt := _scene(exported)
	if rebuilt != null:
		assert_that((rebuilt.get_node("Spawns/start") as Marker2D).position).is_equal(Vector2(24, 12))
		assert_str((rebuilt.get_node("Doors/ToCrossroads") as Door).target_spawn).is_equal("new_return")
		_assert_plan(Tool.plan_from_scene(rebuilt), exported)

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

func _input_plan() -> Dictionary:
	return {"zone": "w2_inputs", "legend": {".": "lawn"}, "rows": ["..", ".."]}

func _assert_invalid_input(plan: Dictionary, field: String) -> void:
	var diagnostic := Tool.plan_error(plan)
	assert_bool(not diagnostic.is_empty() and diagnostic.contains(field)).override_failure_message(
		"Expected a useful %s diagnostic; got '%s' for %s" % [field, diagnostic, plan]).is_true()
	var root := Tool.scene_from_plan(plan)
	assert_object(root).override_failure_message("Malformed %s input allocated a scene: %s" % [field, plan]).is_null()
	if root != null:
		root.free()

func test_input_preflight_accepts_existing_plans_and_preserves_unknown_metadata() -> void:
	for plan in [_fixture(), JSON.parse_string(FileAccess.get_file_as_string(LAB))]:
		var before: Dictionary = plan.duplicate(true)
		assert_str(Tool.plan_error(plan)).is_empty()
		var root := _scene(plan)
		if root != null:
			_assert_plan(Tool.plan_from_scene(root), before)
		_assert_plan(plan, before)
	var future := _input_plan()
	# Unused legend aliases are retained metadata, not malformed glyphs.
	future.legend["future_material_alias"] = "lawn"
	future["future"] = {"nested": [null, {"data": [true, "opaque", 4.25]}]}
	future["pieces"] = [{"piece": "woodland_boulder", "at": [24, 24], "future": [null, {"anything": true}]}]
	future["doors"] = [{"id": "return", "rect": [0, 0, 1, 1], "to": "woodland", "future": {"anything": [null]}}]
	future["gameplay_removed"] = {"future": {"opaque": true}}
	assert_str(Tool.plan_error(future)).is_empty()
	var root := _scene(future)
	if root != null:
		_assert_plan(Tool.plan_from_scene(root), future)

func test_input_preflight_rejects_wrong_optional_row_and_legend_types() -> void:
	for value in [null, false, 1, [], {}, "", " "]:
		var plan := _input_plan()
		plan["zone"] = value
		_assert_invalid_input(plan, "zone")
	for value in [null, false, 1, {}, "..", [], [null], [1], ["..", "."]]:
		var plan := _input_plan()
		plan["rows"] = value
		_assert_invalid_input(plan, "rows")
	for field in ["tiers", "flow", "variants"]:
		for value in [null, false, 1, {}, "00", [0, 0], [null, null]]:
			var plan := _input_plan()
			plan[field] = value
			_assert_invalid_input(plan, field)
	for value in [null, 0, 1, "true", [], {}]:
		var plan := _input_plan()
		plan["lab"] = value
		_assert_invalid_input(plan, "lab")
	for value in [null, [], "lawn", {".": null}, {".": 1}, {1: "lawn"}]:
		var plan := _input_plan()
		plan["legend"] = value
		_assert_invalid_input(plan, "legend")

func test_input_preflight_rejects_malformed_piece_instances() -> void:
	for value in [null, {}, false, "piece", [null], [1], [[]], [{}], [{"piece": null}], [{"piece": 1}]]:
		var plan := _input_plan()
		plan["pieces"] = value
		_assert_invalid_input(plan, "pieces")
	for field in ["id", "variant", "facing", "stage"]:
		for value in [null, [], {}, 1, false]:
			var plan := _input_plan()
			var entry := {"piece": "woodland_boulder", "at": [24, 24]}
			entry[field] = value
			plan["pieces"] = [entry]
			_assert_invalid_input(plan, "pieces")
	var empty_id := _input_plan()
	empty_id["pieces"] = [{"id": "", "piece": "woodland_boulder", "at": [24, 24]}]
	_assert_invalid_input(empty_id, "pieces")

func test_input_preflight_rejects_bad_piece_and_spawn_positions() -> void:
	for value in [null, {}, [], [24], [24, 24, 24], ["24", 24], [24, "24"], [true, 24], [24, null], [NAN, 24], [24, INF], [-INF, 24], [1.0e100, 24]]:
		var piece_plan := _input_plan()
		piece_plan["pieces"] = [{"piece": "woodland_boulder", "at": value}]
		_assert_invalid_input(piece_plan, "pieces")
		var spawn_plan := _input_plan()
		spawn_plan["spawns"] = {"start": value}
		_assert_invalid_input(spawn_plan, "spawns")
	var missing_at := _input_plan()
	missing_at["pieces"] = [{"piece": "woodland_boulder"}]
	_assert_invalid_input(missing_at, "pieces")
	for value in [null, [], "start", false, {1: [24, 24]}]:
		var plan := _input_plan()
		plan["spawns"] = value
		_assert_invalid_input(plan, "spawns")

func test_input_preflight_rejects_malformed_doors_before_allocating_nodes() -> void:
	for value in [null, {}, false, "door", [null], [1], [[]], [{}], [{"id": null, "rect": [0, 0, 1, 1]}]]:
		var plan := _input_plan()
		plan["doors"] = value
		_assert_invalid_input(plan, "doors")
	for rect in [null, {}, [], [0, 0], [0, 0, 1], [0, 0, 1, 1, 1], ["0", 0, 1, 1], [0, false, 1, 1], [0, 0, NAN, 1], [0, INF, 1, 1], [0, 0, 0, 1], [0, 0, 1, -1]]:
		var plan := _input_plan()
		plan["doors"] = [{"id": "return", "rect": rect, "to": "woodland"}]
		_assert_invalid_input(plan, "doors")
	for field in ["id", "to", "target_zone", "spawn", "target_spawn"]:
		var plan := _input_plan()
		var door := {"id": "return", "rect": [0, 0, 1, 1]}
		door[field] = 1
		plan["doors"] = [door]
		_assert_invalid_input(plan, "doors")

func test_input_preflight_rejects_bad_gameplay_inheritance_containers() -> void:
	for value in [null, false, [], {}, 1]:
		var plan := _input_plan()
		plan["gameplay_from"] = value
		_assert_invalid_input(plan, "gameplay_from")
	for value in [null, false, [], "removed", {"Spawns": null}, {"Doors": {}}, {"Spawns": [null]}, {"Doors": [1]}]:
		var plan := _input_plan()
		plan["gameplay_removed"] = value
		_assert_invalid_input(plan, "gameplay_removed")

func test_removal_ids_are_literal_children_and_cannot_address_scene_ancestors() -> void:
	var plan := _input_plan()
	plan["gameplay_from"] = "res://zones/woodland/woodland.tscn"
	var baseline := _scene(plan)
	plan["gameplay_removed"] = {"Spawns": [".", "..", "../Ground", "missing"], "Doors": [".", "..", "../Actors", "start:position"]}
	var root := _scene(plan)
	if baseline == null or root == null:
		return
	for name_ in ["Ground", "Actors", "Spawns", "Doors"]:
		assert_object(root.get_node_or_null(NodePath(name_))).is_not_null()
	for name_ in ["Spawns", "Doors"]:
		var expected := []
		var actual := []
		for child in baseline.get_node(NodePath(name_)).get_children():
			expected.append(String(child.name))
		for child in root.get_node(NodePath(name_)).get_children():
			actual.append(String(child.name))
		assert_that(actual).is_equal(expected)

# subprocess.run supplies a hard timeout even if a GDScript error prevents the
# CLI's deferred _run from reaching quit. The wrapper uses only Python's stdlib.
const BOUNDED_INPUT_CLI := """
import json, os, pathlib, re, subprocess, sys, tempfile
reports = []
with tempfile.TemporaryDirectory(prefix='w2_input_cli_') as directory:
    base = pathlib.Path(directory)
    for index, case in enumerate(json.loads(pathlib.Path(sys.argv[3]).read_text(encoding='utf-8'))):
        folder = base / str(index)
        folder.mkdir()
        source = folder / 'plan.json'
        target = folder / 'scene.tscn'
        source.write_text(json.dumps(case['plan']), encoding='utf-8')
        sentinel = 'existing authored scene stays untouched\\n'
        if case.get('preserve'):
            target.write_text(sentinel, encoding='utf-8')
        env = dict(os.environ)
        for variable, child in [('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache')]:
            env[variable] = str(folder / child)
        command = [sys.argv[1], '--headless', '--audio-driver', 'Dummy', '--path', sys.argv[2],
                   '--script', 'res://tools/kit_zone.gd', '--', '--plan=' + str(source), '--out=' + str(target)]
        timed_out = False
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=20, env=env)
            code, output = result.returncode, result.stdout + result.stderr
        except subprocess.TimeoutExpired as error:
            timed_out = True
            code = 124
            chunks = [error.stdout or b'', error.stderr or b'']
            output = ''.join(chunk.decode(errors='replace') if isinstance(chunk, bytes) else chunk for chunk in chunks)
        reports.append(dict(name=case['name'], field=case.get('field', ''), code=code, timed_out=timed_out,
                            output=output, exists=target.exists(), preserve=case.get('preserve', False),
                            preserved=target.is_file() and target.read_text(encoding='utf-8') == sentinel,
                            clean=re.search(r'SCRIPT ERROR|^ERROR:|orphan|leak', output, re.I | re.M) is None))
print(json.dumps(reports))
"""

func test_real_cli_rejects_nested_bad_input_cleanly_without_overwriting_output() -> void:
	var bad_piece := _input_plan()
	bad_piece["pieces"] = [null]
	var bad_spawn := _input_plan()
	bad_spawn["spawns"] = {"start": [24]}
	var bad_door := _input_plan()
	bad_door["doors"] = [{"id": "return", "rect": [0, 0, 1]}]
	var blank_zone := _input_plan()
	blank_zone["zone"] = " "
	var empty_id := _input_plan()
	empty_id["pieces"] = [{"id": "", "piece": "woodland_boulder", "at": [24, 24]}]
	var literal_ids := _input_plan()
	literal_ids["gameplay_from"] = "res://zones/woodland/woodland.tscn"
	literal_ids["gameplay_removed"] = {"Spawns": [".."], "Doors": [".", "../Ground"]}
	var cases := [
		{"name": "null-piece", "field": "pieces", "plan": bad_piece},
		{"name": "short-spawn", "field": "spawns", "plan": bad_spawn},
		{"name": "short-door", "field": "doors", "plan": bad_door},
		{"name": "existing-output", "field": "pieces", "plan": bad_piece, "preserve": true},
		{"name": "blank-zone", "field": "zone", "plan": blank_zone},
		{"name": "empty-piece-id", "field": "pieces", "plan": empty_id},
		{"name": "literal-removal-ids", "plan": literal_ids},
		{"name": "valid-control", "plan": _input_plan()},
	]
	var output := []
	var python := OS.get_environment("PYTHON")
	if python.is_empty():
		python = "python3"
	# Pass JSON through a file; OS.execute's argument quoting is platform-specific.
	var case_path := ProjectSettings.globalize_path("user://w2_input_cli_cases.json")
	var file := FileAccess.open(case_path, FileAccess.WRITE)
	assert_object(file).is_not_null()
	if file == null:
		return
	file.store_string(JSON.stringify(cases))
	file.close()
	var code := OS.execute(python, ["-c", BOUNDED_INPUT_CLI, OS.get_executable_path(),
		ProjectSettings.globalize_path("res://"), case_path], output, true)
	assert_int(DirAccess.remove_absolute(case_path)).is_equal(OK)
	assert_int(code).override_failure_message("Bounded CLI wrapper failed: %s" % output).is_equal(0)
	var reports = JSON.parse_string("".join(output))
	assert_bool(reports is Array).override_failure_message("Bounded CLI wrapper did not return JSON: %s" % output).is_true()
	if not reports is Array:
		return
	assert_int(reports.size()).is_equal(cases.size())
	for report in reports:
		var detail := "%s: %s" % [report.name, report.output]
		assert_bool(report.timed_out).override_failure_message(detail).is_false()
		assert_bool(report.clean).override_failure_message(detail).is_true()
		if report.name in ["valid-control", "literal-removal-ids"]:
			assert_int(int(report.code)).override_failure_message(detail).is_equal(0)
			assert_bool(report.exists).override_failure_message(detail).is_true()
		else:
			assert_int(int(report.code)).override_failure_message(detail).is_equal(1)
			assert_bool(String(report.output).contains("kit_zone:") and String(report.output).contains(report.field)).override_failure_message(detail).is_true()
			if report.preserve:
				assert_bool(report.preserved).override_failure_message(detail).is_true()
			else:
				assert_bool(report.exists).override_failure_message(detail).is_false()
