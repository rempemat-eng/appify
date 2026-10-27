extends GdUnitTestSuite
## W3 through the real W2 scene/export API, W5 relation engine and W6 Python validator.
const Operations := preload("res://addons/world_editor/operations.gd")
const Rules := preload("res://addons/world_editor/rules_adapter.gd")
const ZonePlan := preload("res://tools/kit_zone.gd")
const Walk := preload("res://world/terrain/walk.gd")
var _fixtures: Array[Dictionary] = []

func after_test() -> void:
	for fixture in _fixtures:
		fixture.history.clear_history()
		fixture.history.free()
		if is_instance_valid(fixture.zone):
			fixture.zone.free()
	_fixtures.clear()

func _scene(_id: String) -> KitPiece:
	return KitPiece.new()

func _fixture(case_id: String) -> Dictionary:
	var envelope: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://kit/schema/relations.cases.json"))
	var entry: Dictionary = {}
	for candidate in envelope.cases:
		if candidate.id == case_id:
			entry = candidate.duplicate(true)
	assert_bool(entry.is_empty()).is_false()
	var plan: Dictionary = entry.plan.duplicate(true)
	var instance: Dictionary = plan.pieces[0].duplicate(true)
	plan.pieces = []
	plan["spawns"] = {"start": [0.5, 0.5]}
	var zone := ZonePlan.scene_from_plan(plan)
	add_child(zone)
	var library: Dictionary = entry.library.duplicate(true)
	for id in library:
		# Test-only intake metadata, not an approval change to a source piece.
		library[id]["kind"] = "prop"
		library[id]["approval"] = {"state": "approved"}
	var history := UndoRedo.new()
	var ops := Operations.new()
	ops.configure(zone, zone.get_node("Ground"), history, {
		"library": library, "index": {}, "scene_factory": _scene,
		"relation_evaluator": Callable(Rules, "placement"),
		"zone_validator": Callable(Rules, "validate_plan"),
	})
	var fixture := {"zone": zone, "history": history, "operations": ops, "instance": instance}
	_fixtures.append(fixture)
	return fixture

func _at(fixture: Dictionary) -> Vector2:
	return Vector2(fixture.instance.at[0], fixture.instance.at[1]) * 24.0

func test_real_engine_refuses_bench_on_route_with_unchanged_seating_message() -> void:
	var f := _fixture("bench_on_path_refused")
	var result: Dictionary = f.operations.place_piece("prop", _at(f), {"id": "test", "facing": "s"})
	assert_bool(result.ok).is_false()
	assert_str(result.diagnostics[0].check).is_equal("rules.seating")
	assert_str(result.diagnostics[0].message).is_equal("test: forbids on route")
	assert_int(f.zone.get_node("Props").get_child_count()).is_equal(0)
	assert_bool(f.history.has_undo()).is_false()

func test_real_engine_accepts_bench_facing_route_and_undo_redo_preserves_metadata() -> void:
	var f := _fixture("bench_beside_path")
	var result: Dictionary = f.operations.place_piece("prop", _at(f), {"id": "test", "facing": "s"})
	assert_bool(result.ok).is_true()
	assert_object(result.node.owner).is_same(f.zone)
	assert_str(result.node.get_meta("facing")).is_equal("s")
	var exported: Dictionary = f.operations.export_plan()
	assert_str(exported.plan.coordinate_space).is_equal("cells")
	assert_that(exported.plan.pieces[0].at).is_equal(f.instance.at)
	assert_bool(f.history.undo()).is_true()
	assert_int(f.zone.get_node("Props").get_child_count()).is_equal(0)
	assert_bool(f.history.redo()).is_true()
	assert_int(f.zone.get_node("Props").get_child_count()).is_equal(1)
	assert_str(f.operations.export_plan().plan.pieces[0].facing).is_equal("s")

func test_real_engine_refuses_a_seat_facing_away() -> void:
	var f := _fixture("bench_faces_away_from_path")
	var result: Dictionary = f.operations.preview_piece("prop", _at(f), {"id": "test", "facing": f.instance.facing})
	assert_bool(result.ok).is_false()
	assert_str(result.diagnostics[0].check).is_equal("rules.seating")

func test_validate_runs_production_physical_rules_on_the_actual_lab() -> void:
	var zone := (load("res://zones/kitlab/kitlab.tscn") as PackedScene).instantiate()
	add_child(zone)
	var history := UndoRedo.new()
	var ops := Operations.new()
	ops.configure(zone, zone.get_node("Ground"), history, {
		"relation_evaluator": Callable(Rules, "placement"),
		"zone_validator": Callable(Rules, "validate_plan"),
	})
	_fixtures.append({"zone": zone, "history": history, "operations": ops})
	var result: Dictionary = ops.validate()
	assert_bool(result.ok).override_failure_message(str(result)).is_true()
	for finding in result.diagnostics:
		assert_str(str(finding.get("severity", "fault"))).is_not_equal("fault")

func test_real_physical_validator_keeps_route_clear_failures() -> void:
	var f := _fixture("bench_on_path_refused")
	var snapshot: Dictionary = f.operations.export_plan()
	snapshot.plan.pieces = [f.instance]
	var library: Dictionary = {"prop": {
		"id": "prop", "kind": "structure", "approval": {"state": "approved"},
		"placement": {"role": "building", "snap": "cell"},
		"geometry": {"footprint": []}, "gameplay": {"blocks_move": true},
	}}
	var result := Rules.validate_plan(snapshot.plan, library)
	assert_bool(result.ok).is_false()
	var found := false
	for finding in result.diagnostics:
		found = found or finding.check == "rules.route_clear"
	assert_bool(found).override_failure_message(str(result)).is_true()

func _solid_scene(_id: String) -> KitPiece:
	var piece := (load("res://kit/props/woodland_forest_bench.tscn") as PackedScene).instantiate() as KitPiece
	piece.get_node("Solid").collision_layer = 5
	piece.set_meta("author_marker", "keep this scene metadata")
	return piece

func _walk_fixture() -> Dictionary:
	var plan := {"zone": "editor_walk_fixture", "lab": true, "legend": {".": "lawn"},
		"rows": ["........", "........", "........", "........", "........", "........"],
		"spawns": {"start": [12, 12]}, "author_note": {"source": "preserve"}}
	var zone := ZonePlan.scene_from_plan(plan)
	add_child(zone)
	var ground := zone.get_node("Ground") as TerrainGround
	await get_tree().process_frame
	await get_tree().physics_frame
	ground.variant_rows = PackedStringArray(["..f....."])
	ground.baked = ImageTexture.create_from_image(Image.create_empty(8, 8, false, Image.FORMAT_RGBA8))
	var definition: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://kit/pieces/prop/woodland_forest_bench.json"))
	# The fixture isolates editor/collision lifecycle; it does not promote source approval
	# or ask the authored bench's seating relations to validate a featureless test room.
	definition.approval.state = "approved"
	definition.placement = {"role": "clutter", "snap": "cell", "requires": [], "forbids": []}
	var history := UndoRedo.new()
	var ops := Operations.new()
	ops.configure(zone, ground, history, {"library": {"woodland_forest_bench": definition},
		"index": KitPiece.index(), "scene_factory": _solid_scene,
		"relation_evaluator": Callable(Rules, "placement")})
	var walk := Walk.new()
	walk.name = "KitWalk"
	ground.add_child(walk)
	walk.owner = zone
	assert_bool(walk.rebuild(ground)).is_true()
	var rebuild_results: Array[bool] = []
	# This is the real dependency call made by plugin._operations_changed at each
	# operation/undo/redo boundary; no substituted collision implementation is used.
	ops.changed.connect(func() -> void: rebuild_results.append(walk.rebuild(ground)))
	var f := {"zone": zone, "ground": ground, "history": history, "operations": ops,
		"walk": walk, "rebuild_results": rebuild_results, "original_rows": ground.cell_rows(),
		"original_variants": ground.variant_rows.duplicate(), "original_bake": ground.baked}
	_fixtures.append(f)
	return f

func _empty_walk_rows() -> PackedStringArray:
	return PackedStringArray(["................", "................", "................", "................",
		"................", "................", "................", "................", "................",
		"................", "................", "................"])

func _bench_walk_rows() -> PackedStringArray:
	var rows := _empty_walk_rows()
	# The real source bench's [-43.2,-12,86.4,12] solid at (96,72) occupies
	# eight 12-texel walk cells on row five, independently of its sprite extent.
	rows[5] = "....########...."
	return rows

func _assert_authoring_snapshot(f: Dictionary, baked_live: bool) -> void:
	assert_that(f.ground.cell_rows()).is_equal(f.original_rows)
	assert_that(f.ground.variant_rows).is_equal(f.original_variants)
	assert_object(f.ground.baked).is_same(f.original_bake)
	assert_bool(f.ground.showing_baked()).is_equal(baked_live)
	var snapshot: Dictionary = f.operations.export_plan()
	assert_bool(snapshot.ok).is_true()
	assert_that(snapshot.plan.author_note).is_equal({"source": "preserve"})
	assert_that(snapshot.plan.spawns.start).is_equal([12, 12])

func test_placement_walk_rebuild_undo_redo_restores_solid_layer_and_authoring_state() -> void:
	var f := await _walk_fixture()
	assert_that(f.walk.rows).is_equal(_empty_walk_rows())
	var result: Dictionary = f.operations.place_piece("woodland_forest_bench", Vector2(96, 72),
		{"id": "solid_bench", "facing": "e", "stage": "restored", "variant": "forest_bench"})
	assert_bool(result.ok).override_failure_message(str(result)).is_true()
	if not result.ok:
		return
	var piece := result.node as KitPiece
	var solid := piece.get_node("Solid") as StaticBody2D
	assert_int(solid.collision_layer).is_equal(0)
	assert_that(f.walk.rows).is_equal(_bench_walk_rows())
	assert_object(piece.owner).is_same(f.zone)
	assert_str(piece.get_meta("author_marker")).is_equal("keep this scene metadata")
	_assert_authoring_snapshot(f, false)
	assert_bool(f.history.undo()).is_true()
	assert_object(piece.get_parent()).is_null()
	assert_int(solid.collision_layer).is_equal(5)
	assert_that(f.walk.rows).is_equal(_empty_walk_rows())
	_assert_authoring_snapshot(f, true)
	assert_bool(f.history.redo()).is_true()
	assert_object(piece.owner).is_same(f.zone)
	assert_int(solid.collision_layer).is_equal(0)
	assert_that(f.walk.rows).is_equal(_bench_walk_rows())
	assert_str(piece.get_meta("stage")).is_equal("restored")
	assert_str(piece.get_meta("facing")).is_equal("e")
	_assert_authoring_snapshot(f, false)
	assert_that(f.rebuild_results).is_equal([true, true, true])
	# Disconnect the UI-bound callback before deliberately removing its dependency.
	for connection in f.operations.changed.get_connections():
		f.operations.changed.disconnect(connection.callable)
	f.walk.free()
	assert_int(solid.collision_layer).is_equal(5)
	assert_bool(solid.has_meta(&"kit_walk_body_owner")).is_false()
	assert_bool(solid.has_meta(&"kit_walk_body_original_layer")).is_false()

func test_scene_round_trip_with_active_walk_preserves_original_solid_layer() -> void:
	var f := await _walk_fixture()
	var result: Dictionary = f.operations.place_piece("woodland_forest_bench", Vector2(96, 72), {"id": "solid_bench"})
	assert_bool(result.ok).override_failure_message(str(result)).is_true()
	if not result.ok:
		return
	var packed := PackedScene.new()
	assert_int(packed.pack(f.zone)).is_equal(OK)
	var path := "user://w3_active_walk_round_trip.tscn"
	assert_int(ResourceSaver.save(packed, path)).is_equal(OK)
	var reloaded := ResourceLoader.load(path, "PackedScene", ResourceLoader.CACHE_MODE_IGNORE) as PackedScene
	assert_object(reloaded).is_not_null()
	if reloaded == null:
		DirAccess.remove_absolute(path)
		return
	var restored := reloaded.instantiate()
	add_child(restored)
	var restored_ground := restored.get_node("Ground") as TerrainGround
	var restored_walk := restored_ground.get_node("KitWalk") as KitWalk
	var restored_piece := restored.get_node("Props/solid_bench") as KitPiece
	var restored_solid := restored_piece.get_node("Solid") as StaticBody2D
	assert_bool(restored_walk.rebuild(restored_ground)).is_true()
	assert_that(restored_walk.rows).is_equal(_bench_walk_rows())
	assert_int(restored_solid.collision_layer).is_equal(0)
	assert_that(restored_ground.cell_rows()).is_equal(f.original_rows)
	assert_that(restored_ground.variant_rows).is_equal(f.original_variants)
	assert_str(restored_piece.get_meta("author_marker")).is_equal("keep this scene metadata")
	assert_object(restored_piece.owner).is_same(restored)
	restored_walk.free()
	assert_int(restored_solid.collision_layer).is_equal(5)
	assert_bool(restored_solid.has_meta(&"kit_walk_body_owner")).is_false()
	assert_bool(restored_solid.has_meta(&"kit_walk_body_original_layer")).is_false()
	restored.free()
	DirAccess.remove_absolute(path)
