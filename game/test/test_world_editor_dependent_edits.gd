extends GdUnitTestSuite
## EDITOR-DEPENDENTS/r1: real W2 scene intake, W3 transactions, W5/W6 adapter.
## No injected library, approximate terrain mask, verdict provider or approval override.
## Native Node2D position/remove_child and TerrainGround.paint_tier are deliberately
## separate from W3: the candidate has no move/delete/tier transaction API.
const Operations := preload("res://addons/world_editor/operations.gd")
const Rules := preload("res://addons/world_editor/rules_adapter.gd")
const ZonePlan := preload("res://tools/kit_zone.gd")
var _fixtures: Array[Dictionary] = []
var _detached: Array[Node] = []

func after_test() -> void:
	for f in _fixtures:
		f.history.clear_history()
		f.history.free()
		if is_instance_valid(f.zone):
			f.zone.free()
	for node in _detached:
		if is_instance_valid(node):
			node.free()
	_fixtures.clear()
	_detached.clear()

func _fixture(lab_id: String = "kitlab_tiers") -> Dictionary:
	var plan: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://kit/zones/%s.json" % lab_id))
	assert_str(ZonePlan.plan_error(plan)).is_empty()
	var zone := ZonePlan.scene_from_plan(plan)
	assert_object(zone).is_not_null()
	add_child(zone)
	var history := UndoRedo.new()
	var ops := Operations.new()
	var ground := zone.get_node("Ground") as TerrainGround
	ops.configure(zone, ground, history, {
		"relation_evaluator": Callable(Rules, "placement"),
		"zone_validator": Callable(Rules, "validate_plan"),
	})
	var f := {"zone": zone, "ground": ground, "history": history, "ops": ops}
	_fixtures.append(f)
	return f

func _state(f: Dictionary) -> Dictionary:
	# Include the redo branch even when has_undo is false. A version-only assertion
	# would miss a refused operation silently destroying redo actions.
	var actions := []
	for i in f.history.get_history_count():
		actions.append(f.history.get_action_name(i))
	return {
		"document": ZonePlan.canonical(f.ops.export_plan().plan),
		"version": f.history.get_version(),
		"count": f.history.get_history_count(),
		"current": f.history.get_current_action(),
		"undo": f.history.has_undo(), "redo": f.history.has_redo(),
		"actions": actions, "baked": f.ground.baked,
		"baked_live": f.ground.showing_baked(),
	}

func _finding(result: Dictionary, check: String) -> bool:
	for diagnostic in result.get("diagnostics", []):
		if diagnostic.get("check", diagnostic.get("rule", "")) == check:
			return true
	return false

func _invalid(f: Dictionary, check: String) -> void:
	# Invalid drafts are allowed. No invented mutation rejection contract.
	var result: Dictionary = f.ops.validate()
	assert_bool(result.ok).override_failure_message(str(result)).is_false()
	assert_bool(_finding(result, check)).override_failure_message(str(result)).is_true()
	# W2 structural intake may accept a draft; W6 must still refuse the imported
	# current data. Do not confuse scene construction with shipping acceptance.
	var exported: Dictionary = f.ops.export_plan()
	assert_bool(exported.ok).is_true()
	var imported := ZonePlan.scene_from_plan(exported.plan)
	assert_object(imported).is_not_null()
	if imported != null:
		add_child(imported)
		var imported_plan := ZonePlan.plan_from_scene(imported)
		var review := Rules.validate_plan(imported_plan, KitRelations.default_library())
		assert_bool(review.ok).is_false()
		assert_bool(_finding(review, check)).override_failure_message(str(review)).is_true()
		imported.free()

func _mark_baked(f: Dictionary) -> void:
	# A tiny in-memory texture is a validity sentinel, never a replacement terrain
	# mask or a rendering-quality claim. All verdicts consume the real source cells.
	f.ground.baked = ImageTexture.create_from_image(Image.create_empty(1, 1, false, Image.FORMAT_RGBA8))
	assert_bool(f.ground.showing_baked()).is_true()

func test_startup_canary_real_intake_and_adapter() -> void:
	var f := _fixture()
	var result: Dictionary = f.ops.validate()
	assert_bool(result.ok).override_failure_message(str(result)).is_true()
	var roundtrip := ZonePlan.scene_from_plan(f.ops.export_plan().plan)
	assert_object(roundtrip).is_not_null()
	if roundtrip != null:
		roundtrip.free()

func test_paint_beneath_existing_footprint_refreshes_rules_and_undo_redo() -> void:
	var f := _fixture()
	assert_bool(f.ops.validate().ok).is_true()
	# Source boulder foot=(700,120), solid rect=(-4,-4,8,4) world px.
	# Cell (29,4) intersects that real solid; no sprite-box approximation.
	# Boundary control immediately outside the source solid: no route-clear fault.
	assert_bool(f.ops.paint_cells([Vector2i(30, 4)], "path").ok).is_true()
	assert_bool(f.ops.validate().ok).is_true()
	assert_bool(f.history.undo()).is_true()
	var before := ZonePlan.canonical(f.ops.export_plan().plan)
	_mark_baked(f)
	assert_bool(f.ops.paint_cells([Vector2i(29, 4)], "path").ok).is_true()
	assert_bool(f.ground.showing_baked()).is_false()
	_invalid(f, "rules.route_clear")
	assert_bool(f.history.undo()).is_true()
	assert_str(ZonePlan.canonical(f.ops.export_plan().plan)).is_equal(before)
	assert_bool(f.ground.showing_baked()).is_true()
	assert_bool(f.ops.validate().ok).is_true()
	assert_bool(f.history.redo()).is_true()
	_invalid(f, "rules.route_clear")

func test_route_relation_distance_boundary_and_interacting_water_prohibition() -> void:
	var f := _fixture()
	# Source bench foot=(408,168), occupied foot cell=(17,6); south route
	# currently at (17,7),(17,8). Two cells is the authored inclusive limit.
	var removed: Array = []
	for y in [7, 8]:
		for x in range(15, 20):
			if Vector2i(x, y) != Vector2i(17, 8):
				removed.append(Vector2i(x, y))
	assert_bool(f.ops.paint_cells(removed, "lawn").ok).is_true()
	assert_bool(f.ops.validate().ok).is_true()
	assert_bool(f.ops.paint_cells([Vector2i(17, 8)], "lawn").ok).is_true()
	_invalid(f, "rules.seating")
	assert_bool(f.history.undo()).is_true()
	assert_bool(f.ops.validate().ok).is_true()
	assert_bool(f.ops.paint_cells([Vector2i(17, 6)], "water").ok).is_true()
	_invalid(f, "rules.forbids")
	assert_bool(f.history.undo()).is_true()
	assert_bool(f.ops.validate().ok).is_true()

func test_tier_change_breaks_stair_deck_route_and_import_is_unshippable() -> void:
	var f := _fixture()
	assert_bool(f.ops.validate().ok).is_true()
	_mark_baked(f)
	# Actual Tiers API. This removes one head-rim cell over the two-cell stair.
	f.ground.paint_tier(Vector2i(19, 9), 0)
	# Validate before waiting for a TileMapLayer notification: current data wins.
	_invalid(f, "rules.stair")
	await get_tree().process_frame
	assert_bool(f.ground.showing_baked()).is_false()
	f.ground.paint_tier(Vector2i(19, 9), 1)
	assert_bool(f.ops.validate().ok).is_true()

func test_moving_stair_support_immediately_refreshes_validation_and_bake() -> void:
	var f := _fixture()
	var steps := f.zone.get_node("Props/steps") as KitPiece
	var original := steps.position
	assert_bool(f.ops.validate().ok).is_true()
	_mark_baked(f)
	steps.position += Vector2(0, 24)
	_invalid(f, "rules.stair")
	await get_tree().process_frame
	# Expected RED candidate: ordinary scene movement may leave the old bake green.
	assert_bool(f.ground.showing_baked()).override_failure_message("Moved painted stair must invalidate its previous baked ground").is_false()
	steps.position = original
	assert_bool(f.ops.validate().ok).is_true()

func test_deleting_stair_support_exposes_route_without_stale_bake() -> void:
	var f := _fixture()
	var steps := f.zone.get_node("Props/steps") as KitPiece
	assert_bool(f.ops.validate().ok).is_true()
	_mark_baked(f)
	steps.get_parent().remove_child(steps)
	_detached.append(steps)
	_invalid(f, "rules.tier_route")
	await get_tree().process_frame
	assert_bool(f.ground.showing_baked()).override_failure_message("Deleted painted stair must invalidate its previous baked ground").is_false()

func test_moving_related_seat_revalidates_instead_of_reusing_green() -> void:
	var f := _fixture()
	var bench := f.zone.get_node("Props/bench") as KitPiece
	assert_bool(f.ops.validate().ok).is_true()
	var original := bench.position
	bench.position = Vector2(48, 48)
	_invalid(f, "rules.seating")
	bench.position = original
	assert_bool(f.ops.validate().ok).is_true()

func test_rejections_preserve_document_and_existing_redo_branch() -> void:
	var f := _fixture()
	assert_bool(f.ops.paint_cells([Vector2i(0, 0)], "path").ok).is_true()
	assert_bool(f.history.undo()).is_true()
	var before := _state(f)
	assert_bool(f.ops.paint_cells([Vector2i(1, 0), Vector2i(40, 0)], "path").ok).is_false()
	assert_that(_state(f)).is_equal(before)
	assert_bool(f.ops.paint_cells([Vector2i(0, 0)], "path", "f").ok).is_false()
	assert_that(_state(f)).is_equal(before)
	# Real relation refusal, not a fake provider: boulder on the source route.
	assert_bool(f.ops.place_piece("woodland_boulder", Vector2(408, 192), {"id": "refused_rock"}).ok).is_false()
	assert_that(_state(f)).is_equal(before)
	assert_bool(f.history.redo()).is_true()
	assert_int(f.ground.material_at(Vector2i(0, 0))).is_equal(2)
