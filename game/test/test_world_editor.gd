extends GdUnitTestSuite
## Source TerrainGround/KitPiece and real UndoRedo transactions. Injected providers test only
## the delegation boundary; the shared relation engine's own fixtures establish its semantics.

const Operations := preload("res://addons/world_editor/operations.gd")
const ZonePlan := preload("res://tools/kit_zone.gd")
var _fixtures: Array[Dictionary] = []

func after_test() -> void:
	for fixture in _fixtures:
		fixture.history.clear_history()
		fixture.history.free() # UndoRedo is Object, not RefCounted; the editor owns its manager.
		if is_instance_valid(fixture.zone):
			fixture.zone.free()
	_fixtures.clear()

func _library() -> Dictionary:
	var result := {}
	for path in ["terrain/lawn", "terrain/path", "prop/woodland_forest_bench", "prop/woodland_oak"]:
		var piece: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://kit/pieces/%s.json" % path))
		# These are injected test definitions; no source approval record is changed.
		piece.approval.state = "approved"
		result[piece.id] = piece
	return result

func _allow(_plan: Dictionary, _instance: Dictionary, _library_data: Dictionary) -> Dictionary:
	return {"ok": true, "diagnostics": []}

func _scene(_id: String) -> KitPiece:
	return KitPiece.new()

func _fixture(extra: Dictionary = {}, lab: bool = true) -> Dictionary:
	var plan := {"zone": "editor_fixture", "lab": lab, "legend": {".": "lawn"}, "rows": ["........", "........", "........", "........", "........", "........"], "spawns": {"start": [36, 48]}}
	plan.merge(extra.get("plan", {}), true)
	var zone := ZonePlan.scene_from_plan(plan)
	var ground := zone.get_node("Ground") as TerrainGround
	var props := zone.get_node("Props") as Node2D
	var ordinary := Marker2D.new()
	ordinary.name = "OrdinaryAuthoringNode"
	props.add_child(ordinary)
	ordinary.owner = zone
	add_child(zone)
	var history := UndoRedo.new()
	var operations := Operations.new()
	var options := {"library": _library(), "index": KitPiece.index(), "scene_factory": _scene, "relation_evaluator": _allow}
	options.merge(extra, true)
	operations.configure(zone, ground, history, options)
	var fixture := {"zone": zone, "ground": ground, "history": history, "operations": operations, "options": options}
	_fixtures.append(fixture)
	return fixture

func test_paint_stroke_undo_redo_restores_exact_cells_variants_and_bake() -> void:
	var f := _fixture()
	var ground := f.ground as TerrainGround
	var image := Image.create_empty(8, 8, false, Image.FORMAT_RGBA8)
	ground.baked = ImageTexture.create_from_image(image)
	ground.variant_rows = PackedStringArray([".."])
	var baked := ground.baked
	var changes := [0]
	f.operations.changed.connect(func() -> void: changes[0] += 1)
	var result: Dictionary = f.operations.paint_cells([Vector2i(1, 1), Vector2i(2, 1), Vector2i(1, 1)], "path", "d")
	assert_bool(result.ok).is_true()
	assert_int(ground.material_at(Vector2i(1, 1))).is_equal(2)
	assert_int(ground.material_at(Vector2i(2, 1))).is_equal(2)
	assert_str(ground.variant_at(Vector2i(1, 1))).is_equal("d")
	assert_bool(ground.showing_baked()).is_false()
	assert_int(changes[0]).is_equal(1)
	assert_bool(f.history.undo()).is_true()
	assert_bool(f.history.has_undo()).is_false() # the entire stroke was one transaction
	assert_int(ground.material_at(Vector2i(1, 1))).is_equal(1)
	assert_int(ground.material_at(Vector2i(2, 1))).is_equal(1)
	assert_that(ground.variant_rows).is_equal(PackedStringArray([".."]))
	assert_object(ground.baked).is_same(baked)
	assert_bool(ground.showing_baked()).is_true()
	assert_bool(f.history.redo()).is_true()
	assert_int(ground.material_at(Vector2i(2, 1))).is_equal(2)
	assert_str(ground.variant_at(Vector2i(2, 1))).is_equal("d")
	assert_bool(ground.showing_baked()).is_false()
	assert_int(changes[0]).is_equal(3)

func test_bad_cell_refuses_the_whole_stroke_and_noop_adds_no_history() -> void:
	var f := _fixture()
	var result: Dictionary = f.operations.paint_cells([Vector2i(0, 0), Vector2i(8, 0)], "path")
	assert_bool(result.ok).is_false()
	assert_str(result.diagnostics[0].rule).is_equal("rules.bounds")
	assert_int(f.ground.material_at(Vector2i(0, 0))).is_equal(1)
	assert_bool(f.history.has_undo()).is_false()
	result = f.operations.paint_cells([Vector2(1.5, 1)], "path")
	assert_bool(result.ok).is_false()
	result = f.operations.paint_cells([Vector2i(0, 0)], "lawn")
	assert_bool(result.ok).is_true()
	assert_bool(result.changed).is_false()
	assert_bool(f.history.has_undo()).is_false()

func test_variant_only_does_not_erase_and_invalid_variant_refuses() -> void:
	var f := _fixture()
	assert_bool(f.operations.paint_cells([Vector2i(0, 0)], "", "f").ok).is_true()
	assert_int(f.ground.material_at(Vector2i(0, 0))).is_equal(1)
	assert_str(f.ground.variant_at(Vector2i(0, 0))).is_equal("f")
	var version: int = f.history.get_version()
	assert_bool(f.operations.paint_cells([Vector2i(0, 0)], "path", "unknown").ok).is_false()
	assert_bool(f.operations.paint_cells([Vector2i(0, 0)], "path", "f").ok).is_false() # lawn's daisies are not a path variant
	assert_bool(f.operations.paint_cells([Vector2i(0, 0)], "path").ok).is_false() # preserving f would make the new surface invalid
	assert_int(f.history.get_version()).is_equal(version)
	assert_bool(f.operations.paint_cells([Vector2i(0, 0)], "", "").ok).is_true()
	assert_int(f.ground.material_at(Vector2i(0, 0))).is_equal(0)
	assert_bool(f.history.undo()).is_true()
	assert_int(f.ground.material_at(Vector2i(0, 0))).is_equal(1)

func test_raw_approval_gates_materials_and_props_independently_of_built_index() -> void:
	var library := _library()
	library.path.approval.state = "candidate"
	library.woodland_forest_bench.approval.state = "candidate"
	var f := _fixture({"library": library}, false)
	assert_bool(f.operations.paint_cells([Vector2i(0, 0)], "path").ok).is_false()
	var result: Dictionary = f.operations.place_piece("woodland_forest_bench", Vector2(60, 72))
	assert_bool(result.ok).is_false()
	assert_str(result.diagnostics[0].rule).is_equal("rules.unapproved")
	assert_bool(f.history.has_undo()).is_false()
	var palette: Dictionary = f.operations.catalog()
	assert_int(palette.materials.size()).is_equal(1)
	assert_int(palette.pieces.size()).is_equal(1)
	assert_str(palette.pieces[0].id).is_equal("woodland_oak")

func test_labs_allow_candidates_but_never_concepts_rejected_or_retired() -> void:
	var f := _fixture()
	for state in ["candidate", "gated", "concept", "rejected", "retired", ""]:
		var library := _library()
		library.path.approval.state = state
		library.woodland_forest_bench.approval.state = state
		var options: Dictionary = f.options.duplicate(true)
		options.library = library
		f.operations.configure(f.zone, f.ground, f.history, options)
		var expected: bool = state in ["candidate", "gated"]
		assert_bool(f.operations.preview_piece("woodland_forest_bench", Vector2(60, 72)).ok).is_equal(expected)
		var material: Dictionary = f.operations.paint_cells([Vector2i(0, 0)], "path")
		assert_bool(material.ok).is_equal(expected)
		if expected:
			f.history.undo()
			f.history.clear_history()

func test_missing_or_malformed_rule_provider_refuses_without_mutation() -> void:
	var f := _fixture({"relation_evaluator": Callable()})
	var result: Dictionary = f.operations.place_piece("woodland_forest_bench", Vector2(60, 72))
	assert_bool(result.ok).is_false()
	assert_str(result.diagnostics[0].rule).is_equal("rules.provider_missing")
	assert_bool(f.history.has_undo()).is_false()
	assert_int(f.zone.get_node("Props").get_child_count()).is_equal(1)
	assert_bool(f.operations.validate().ok).is_false()
	f.options.relation_evaluator = func(_p: Dictionary, _i: Dictionary, _l: Dictionary) -> Dictionary: return {}
	f.operations.configure(f.zone, f.ground, f.history, f.options)
	assert_str(f.operations.preview_piece("woodland_forest_bench", Vector2(60, 72)).diagnostics[0].rule).is_equal("rules.provider_invalid")

func test_validate_checks_existing_concept_independently_of_the_rule_provider() -> void:
	var library := _library()
	library.woodland_forest_bench.approval.state = "concept"
	var f := _fixture({"library": library, "zone_validator": func(_p: Dictionary, _l: Dictionary) -> Dictionary: return {"ok": true, "diagnostics": []}})
	var piece := KitPiece.new()
	piece.piece_id = "woodland_forest_bench"
	f.zone.get_node("Props").add_child(piece)
	piece.owner = f.zone
	var result: Dictionary = f.operations.validate()
	assert_bool(result.ok).is_false()
	assert_str(result.diagnostics[0].rule).is_equal("rules.unapproved")

func test_refusal_preserves_shared_provider_rule_message_and_proposed_facing() -> void:
	var seen: Array[Dictionary] = []
	var evaluator := func(plan: Dictionary, instance: Dictionary, library: Dictionary) -> Dictionary:
		seen.append({"plan": plan, "instance": instance, "library": library})
		return {"ok": false, "diagnostics": [{"rule": "rules.seating", "message": "Seat needs a route edge in front."}]}
	var f := _fixture({"relation_evaluator": evaluator})
	var result: Dictionary = f.operations.place_piece("woodland_forest_bench", Vector2(61, 73), {"facing": "n"})
	assert_bool(result.ok).is_false()
	assert_str(result.message).is_equal("Seat needs a route edge in front.")
	assert_str(result.diagnostics[0].rule).is_equal("rules.seating")
	assert_int(seen.size()).is_equal(1)
	assert_that(seen[0].instance.at).is_equal([60.0, 72.0])
	assert_str(seen[0].instance.facing).is_equal("n")
	assert_int(seen[0].plan.get("pieces", []).size()).is_equal(0)
	assert_that(seen[0].library.woodland_forest_bench.placement.requires).is_equal(f.options.library.woodland_forest_bench.placement.requires)
	assert_bool(f.history.has_undo()).is_false()

func test_placement_undo_redo_keeps_scene_ownership_metadata_and_ordinary_nodes() -> void:
	var f := _fixture()
	var result: Dictionary = f.operations.place_piece("woodland_forest_bench", Vector2(61, 73), {"facing": "e", "stage": "restored", "variant": "forest_bench", "id": "seat_one"})
	assert_bool(result.ok).is_true()
	var piece := result.node as KitPiece
	assert_that(piece.position).is_equal(Vector2(60, 72))
	assert_object(piece.owner).is_same(f.zone)
	assert_str(piece.get_meta("facing")).is_equal("e")
	assert_str(piece.get_meta("stage")).is_equal("restored")
	assert_str(piece.get_meta("kit_zone_entry").variant).is_equal("forest_bench")
	assert_bool(f.history.undo()).is_true()
	assert_bool(is_instance_valid(piece)).is_true()
	assert_object(piece.get_parent()).is_null()
	assert_object(f.zone.get_node_or_null("Props/OrdinaryAuthoringNode")).is_not_null()
	assert_bool(f.history.redo()).is_true()
	assert_object(piece.owner).is_same(f.zone)
	assert_int(f.zone.get_node("Props").get_child_count()).is_equal(2)
	var snapshot: Dictionary = f.operations.export_plan()
	assert_bool(snapshot.ok).is_true()
	assert_str(snapshot.plan.pieces[0].id).is_equal("seat_one")
	assert_str(snapshot.plan.pieces[0].facing).is_equal("e")
	assert_str(snapshot.plan.pieces[0].stage).is_equal("restored")
	assert_that(snapshot.plan.pieces[0].at).is_equal([60.0, 72.0])
	var packed := PackedScene.new()
	assert_int(packed.pack(f.zone)).is_equal(OK)
	var restored := packed.instantiate()
	assert_object(restored.get_node_or_null("Props/seat_one")).is_not_null()
	assert_object(restored.get_node_or_null("Props/OrdinaryAuthoringNode")).is_not_null()
	assert_str(restored.get_node("Props/seat_one").get_meta("stage")).is_equal("restored")
	restored.free()

func test_cells_plan_units_survive_preview_placement_and_export() -> void:
	var f := _fixture({"plan": {"coordinate_space": "cells", "spawns": {"start": [1.5, 2]}}})
	var result: Dictionary = f.operations.place_piece("woodland_forest_bench", Vector2(61, 73), {"id": "cell_seat"})
	assert_bool(result.ok).is_true()
	assert_that(result.at).is_equal(Vector2(60, 72))
	assert_that(result.instance.at).is_equal([2.5, 3.0])
	assert_that(result.node.position).is_equal(Vector2(60, 72))
	var snapshot: Dictionary = f.operations.export_plan()
	assert_str(snapshot.plan.coordinate_space).is_equal("cells")
	assert_that(snapshot.plan.pieces[0].at).is_equal([2.5, 3.0])
	assert_that(snapshot.plan.spawns.start).is_equal([1.5, 2])

func test_instance_id_variant_orientation_and_bounds_refuse_before_history() -> void:
	var library := _library()
	library.woodland_forest_bench.placement.orientations = ["s"]
	var f := _fixture({"library": library})
	for options in [{"facing": "n"}, {"facing": "diagonal"}, {"variant": "missing"}, {"id": "invalid/name"}]:
		assert_bool(f.operations.place_piece("woodland_forest_bench", Vector2(60, 72), options).ok).is_false()
	assert_bool(f.operations.place_piece("woodland_forest_bench", Vector2(999, 72)).ok).is_false()
	assert_bool(f.history.has_undo()).is_false()
	assert_bool(f.operations.place_piece("woodland_forest_bench", Vector2(60, 72), {"id": "seat"}).ok).is_true()
	var version: int = f.history.get_version()
	assert_bool(f.operations.place_piece("woodland_forest_bench", Vector2(84, 72), {"id": "seat"}).ok).is_false()
	assert_int(f.history.get_version()).is_equal(version)

func test_instance_ids_preserve_ordinary_props_children_before_factory_or_history() -> void:
	var factories := [0]
	var factory := func(_id: String) -> KitPiece:
		factories[0] += 1
		return KitPiece.new()
	var f := _fixture({"scene_factory": factory})
	var ordinary: Node = f.zone.get_node("Props/OrdinaryAuthoringNode")
	var refused: Dictionary = f.operations.place_piece("woodland_forest_bench", Vector2(60, 72), {"id": "OrdinaryAuthoringNode"})
	assert_bool(refused.ok).is_false()
	assert_str(refused.diagnostics[0].rule).is_equal("rules.instance_id")
	assert_int(factories[0]).is_equal(0)
	assert_bool(f.history.has_undo()).is_false()
	assert_object(f.zone.get_node("Props/OrdinaryAuthoringNode")).is_same(ordinary)
	for id in ["woodland_forest_bench", "woodland_forest_bench_2"]:
		var child := Marker2D.new()
		child.name = id
		f.zone.get_node("Props").add_child(child)
		child.owner = f.zone
	var placed: Dictionary = f.operations.place_piece("woodland_forest_bench", Vector2(60, 72))
	assert_bool(placed.ok).is_true()
	assert_str(placed.instance.id).is_equal("woodland_forest_bench_3")
	assert_str(String(placed.node.name)).is_equal(placed.instance.id)
	assert_str(placed.node.get_meta("kit_zone_entry").id).is_equal(placed.instance.id)
	assert_int(factories[0]).is_equal(1)
	assert_bool(f.history.undo()).is_true()
	assert_object(f.zone.get_node("Props/woodland_forest_bench")).is_not_null()
	assert_object(f.zone.get_node("Props/woodland_forest_bench_2")).is_not_null()

func test_export_preserves_unknown_plan_fields_and_current_spawns() -> void:
	var f := _fixture({"plan": {"story": {"quest": "keep_me"}, "doors": [{"id": "gate", "rect": [0, 0, 1, 1], "to": "village"}], "gameplay_from": "res://test/fixtures/zone_a.tscn"}})
	var snapshot: Dictionary = f.operations.export_plan()
	assert_bool(snapshot.ok).is_true()
	assert_str(snapshot.plan.story.quest).is_equal("keep_me")
	assert_str(snapshot.plan.gameplay_from).is_equal("res://test/fixtures/zone_a.tscn")
	assert_str(snapshot.plan.doors[0].id).is_equal("gate")
	assert_that(snapshot.plan.spawns.start).is_equal([36, 48])
	assert_int(snapshot.plan.rows.size()).is_equal(6)
	assert_int(snapshot.plan.rows[0].length()).is_equal(8)
	var material: String = snapshot.plan.legend[snapshot.plan.rows[0][0]]
	assert_str(material).is_equal("lawn")

func test_legacy_scene_uses_existing_json_seed_without_writing_it() -> void:
	var path := "res://kit/zones/kitlab.json"
	var original := FileAccess.get_file_as_string(path)
	var seed: Dictionary = JSON.parse_string(original)
	var zone := (load("res://zones/kitlab/kitlab.tscn") as PackedScene).instantiate() as Node2D
	assert_bool(zone.has_meta(ZonePlan.PLAN_META)).is_false()
	add_child(zone)
	var history := UndoRedo.new()
	var operations := Operations.new()
	operations.configure(zone, zone.get_node("Ground") as TerrainGround, history, {"library": _library(), "index": KitPiece.index()})
	_fixtures.append({"zone": zone, "history": history, "operations": operations})
	var snapshot: Dictionary = operations.export_plan()
	assert_bool(snapshot.ok).is_true()
	assert_str(snapshot.plan.note).is_equal(seed.note)
	assert_bool(snapshot.plan.bake).is_equal(seed.bake)
	assert_str(snapshot.plan.zone).is_equal("kitlab")
	assert_str(FileAccess.get_file_as_string(path)).is_equal(original)

func test_undo_after_selection_change_targets_original_ground() -> void:
	var a := _fixture()
	var b := _fixture()
	assert_bool(a.operations.paint_cells([Vector2i(0, 0)], "path").ok).is_true()
	a.operations.configure(b.zone, b.ground, a.history, b.options)
	assert_bool(a.history.undo()).is_true()
	assert_int(a.ground.material_at(Vector2i(0, 0))).is_equal(1)
	assert_int(b.ground.material_at(Vector2i(0, 0))).is_equal(1)
	assert_object(a.operations.last_changed_ground).is_same(a.ground)

func test_validate_delegates_complete_snapshot_and_preserves_findings() -> void:
	var received: Array[Dictionary] = []
	var validator := func(plan: Dictionary, library: Dictionary) -> Dictionary:
		received.append({"plan": plan, "library": library})
		return {"ok": false, "diagnostics": [{"rule": "rules.walk", "message": "Start marker is blocked."}]}
	var f := _fixture({"zone_validator": validator})
	var result: Dictionary = f.operations.validate()
	assert_bool(result.ok).is_false()
	assert_str(result.message).is_equal("Start marker is blocked.")
	assert_str(result.diagnostics[0].rule).is_equal("rules.walk")
	assert_that(received[0].plan.spawns.start).is_equal([36, 48])
	assert_int(received[0].library.size()).is_equal(4)
