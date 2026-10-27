extends GdUnitTestSuite
## W3 through the real W2 scene/export API, W5 relation engine and W6 Python validator.
const Operations := preload("res://addons/world_editor/operations.gd")
const Rules := preload("res://addons/world_editor/rules_adapter.gd")
const ZonePlan := preload("res://tools/kit_zone.gd")
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
