@tool
extends RefCounted
## Optional disposable-editor acceptance run. No scene or library approval is saved.
## Open kitlab with --we-smoke-report=<absolute.json> (and optionally --we-capture=<absolute.png>).

static func run(plugin: EditorPlugin) -> Dictionary:
	var failures: Array[String] = []
	var root := EditorInterface.get_edited_scene_root()
	if root == null or not root.get_node_or_null("Ground") is TerrainGround:
		return {"ok": false, "failures": ["Open the kit lab scene before running editor acceptance."]}
	var ground := root.get_node("Ground") as TerrainGround
	plugin.call("_edit", ground)
	var manager := plugin.get_undo_redo()
	var original_rows := ground.cell_rows().duplicate(true)
	var original_variants := ground.variant_rows.duplicate()
	var original_bake := ground.showing_baked()
	var before_count := ground.pieces().size()
	var cleared: Array[Vector2i] = []
	for y in range(7):
		for x in range(8):
			cleared.append(Vector2i(x, y))
	var first: Dictionary = plugin.call("paint_cells", cleared, "lawn")
	var path: Array[Vector2i] = []
	for y in range(5, 7):
		for x in range(1, 8):
			path.append(Vector2i(x, y))
	var second: Dictionary = plugin.call("paint_cells", path, "path")
	if not bool(first.get("ok", false)) or not bool(second.get("ok", false)):
		failures.append("Editor painting was refused: %s / %s" % [first, second])
	var history := manager.get_history_undo_redo(manager.get_object_history_id(root))
	var bad: Dictionary = plugin.call("place_piece", "woodland_forest_bench", Vector2(108, 144), {"facing": "s"})
	if bool(bad.get("ok", false)):
		failures.append("A bench on the route was accepted.")
		history.undo()
	else:
		var seating := false
		for finding in bad.get("diagnostics", []):
			seating = seating or finding.get("check", finding.get("rule", "")) == "rules.seating"
		if not seating:
			failures.append("Route refusal did not retain the shared seating diagnostic: %s" % bad)
	var placed: Dictionary = plugin.call("place_piece", "woodland_forest_bench", Vector2(108, 120), {"facing": "s"})
	if not bool(placed.get("ok", false)):
		failures.append("A bench facing the route was refused: %s" % placed)
	else:
		if placed.node.owner != root or ground.pieces().size() != before_count + 1:
			failures.append("Editor placement did not preserve ownership/count.")
		if not history.undo() or ground.pieces().size() != before_count:
			failures.append("EditorUndoRedoManager could not undo piece placement.")
		if not history.redo() or ground.pieces().size() != before_count + 1:
			failures.append("EditorUndoRedoManager could not redo piece placement.")
		history.undo()
	if bool(second.get("changed", false)):
		history.undo()
	if bool(first.get("changed", false)):
		history.undo()
	await plugin.get_tree().process_frame
	if ground.cell_rows() != original_rows or ground.variant_rows != original_variants or ground.showing_baked() != original_bake:
		failures.append("Undo did not restore the exact original cells/variants/baked state.")
	history.clear_history()
	var gestures := await _exercise_gestures(plugin, ground, history, failures)
	var validation: Dictionary = plugin.call("validate_zone")
	if not bool(validation.get("ok", false)):
		failures.append("Restored lab failed full validation: %s" % validation)
	# These preflights must refuse before save/export/painter execution.
	plugin.set("_baking", true)
	var busy: Dictionary = plugin.call("bake_zone")
	plugin.set("_baking", false)
	if bool(busy.get("ok", false)) or busy.diagnostics[0].check != "editor.bake_busy":
		failures.append("Reentrant bake was not refused.")
	var nested := Node2D.new()
	plugin.set("zone", nested)
	var nested_bake: Dictionary = plugin.call("bake_zone")
	plugin.set("zone", root)
	nested.free()
	if bool(nested_bake.get("ok", false)) or nested_bake.diagnostics[0].check != "editor.bake_scene":
		failures.append("Bake of a scene other than the active root was not refused.")
	var had_plan := root.has_meta("kit_zone_plan")
	var seed: Dictionary = root.get_meta("kit_zone_plan", {}).duplicate(true)
	var cell_seed := seed.duplicate(true)
	cell_seed["coordinate_space"] = "cells"
	root.set_meta("kit_zone_plan", cell_seed)
	var cell_bake: Dictionary = plugin.call("bake_zone")
	if had_plan:
		root.set_meta("kit_zone_plan", seed)
	else:
		root.remove_meta("kit_zone_plan")
	if bool(cell_bake.get("ok", false)) or cell_bake.diagnostics[0].check != "editor.bake_coordinates":
		failures.append("Cell-coordinate bake was not refused before writing files.")
	var dock = plugin.get("dock")
	plugin.set("brush", "piece:woodland_forest_bench")
	dock.show_piece("woodland_forest_bench")
	if dock.mats.item_count == 0 or dock.pieces.item_count == 0:
		failures.append("Lab palette did not contain its candidate materials/pieces.")
	await plugin.get_tree().process_frame
	var captures: Array[String] = []
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--we-capture="):
			await RenderingServer.frame_post_draw
			var image := EditorInterface.get_base_control().get_viewport().get_texture().get_image()
			var path_name := arg.substr(13)
			if image == null or image.is_empty() or image.save_png(path_name) != OK:
				failures.append("Editor capture did not produce a real rendered image.")
			else:
				captures.append(path_name)
	return {"ok": failures.is_empty(), "failures": failures, "pieces": before_count, "palette_materials": dock.mats.item_count, "palette_pieces": dock.pieces.item_count, "gestures": gestures, "captures": captures}

static func _exercise_gestures(plugin: EditorPlugin, ground: TerrainGround, history: UndoRedo, failures: Array[String]) -> Dictionary:
	var settings := {}
	for key in ["brush", "tool_mode", "brush_size", "route_width"]:
		settings[key] = plugin.get(key)
	plugin.set("brush_size", 1)
	plugin.set("route_width", 2)
	# Expected cells describe simple user gestures; no brush/route implementation is called
	# to manufacture the oracle. All coordinates are converted through the real canvas transform.
	var cases := [
		{"name": "brush", "brush": "material:path", "mode": "brush", "points": [Vector2i(0, 0), Vector2i(3, 0)], "check": [Vector2i(0, 0), Vector2i(1, 0), Vector2i(2, 0), Vector2i(3, 0)]},
		{"name": "rectangle", "brush": "material:path", "mode": "rectangle", "points": [Vector2i(0, 0), Vector2i(2, 1)], "check": [Vector2i(0, 0), Vector2i(2, 0), Vector2i(0, 1), Vector2i(2, 1)]},
		{"name": "route", "brush": "material:path", "mode": "route", "points": [Vector2i(0, 0), Vector2i(5, 0), Vector2i(5, 4)], "check": [Vector2i(2, 0), Vector2i(2, 1), Vector2i(5, 4), Vector2i(6, 4)]},
		{"name": "variant", "brush": "variant:d", "mode": "brush", "points": [Vector2i(2, 2), Vector2i(4, 2)], "check": [Vector2i(2, 2), Vector2i(3, 2), Vector2i(4, 2)]},
	]
	for case in cases:
		var before := _state(ground)
		plugin.set("brush", case.brush)
		plugin.set("tool_mode", case.mode)
		var handled := _button(plugin, ground, case.points[0], true)
		for point in case.points.slice(1):
			_motion(plugin, ground, point, true)
		if not _same_state(ground, before) or history.has_undo():
			failures.append("%s gesture mutated the scene before release." % case.name)
		handled = _button(plugin, ground, case.points.back(), false) and handled
		if not handled or not history.has_undo():
			failures.append("%s gesture did not commit through canvas input." % case.name)
		for cell in case.check:
			var correct := ground.variant_at(cell) == "d" if case.name == "variant" else ground.material_at(cell) == ground.kit.material_id("path")
			if not correct:
				failures.append("%s gesture did not paint expected cell %s." % [case.name, cell])
		if not history.undo() or history.has_undo():
			failures.append("%s gesture was not one undoable transaction." % case.name)
		await plugin.get_tree().process_frame
		if not _same_state(ground, before):
			failures.append("%s gesture undo lost original cells, variants or bake." % case.name)
		while history.has_undo():
			history.undo() # retain failure evidence, but discard extra unexpected in-memory actions
		history.clear_history()
	plugin.set("brush", "material:path")
	plugin.set("tool_mode", "brush")
	for reason in ["escape", "lost_button"]:
		var before := _state(ground)
		_button(plugin, ground, Vector2i(0, 0), true)
		_motion(plugin, ground, Vector2i(3, 0), true)
		if reason == "escape":
			var escape := InputEventKey.new()
			escape.keycode = KEY_ESCAPE
			escape.pressed = true
			plugin.call("_forward_canvas_gui_input", escape)
		else:
			_motion(plugin, ground, Vector2i(3, 0), false)
		_button(plugin, ground, Vector2i(3, 0), false)
		await plugin.get_tree().process_frame
		if not _same_state(ground, before) or history.has_undo() or bool(plugin.get("painting")):
			failures.append("%s cancellation left scene changes or an active gesture." % reason)
		while history.has_undo():
			history.undo()
		history.clear_history()
	plugin.call("_cancel_stroke")
	for key in settings:
		plugin.set(key, settings[key])
	return {"cases": 6, "tools": ["brush", "rectangle", "route", "variant"], "cancellations": ["escape", "lost_button"]}

static func _state(ground: TerrainGround) -> Dictionary:
	return {"rows": ground.cell_rows().duplicate(true), "variants": ground.variant_rows.duplicate(), "texture": ground.baked, "baked": ground.showing_baked()}

static func _same_state(ground: TerrainGround, before: Dictionary) -> bool:
	return ground.cell_rows() == before.rows and ground.variant_rows == before.variants and ground.baked == before.texture and ground.showing_baked() == before.baked

static func _button(plugin: EditorPlugin, ground: TerrainGround, cell: Vector2i, pressed: bool) -> bool:
	var event := InputEventMouseButton.new()
	event.position = ground.get_global_transform_with_canvas() * ((Vector2(cell) + Vector2.ONE * 0.5) * ground.kit.cell)
	event.button_index = MOUSE_BUTTON_LEFT
	event.button_mask = MOUSE_BUTTON_MASK_LEFT if pressed else 0
	event.pressed = pressed
	return bool(plugin.call("_forward_canvas_gui_input", event))

static func _motion(plugin: EditorPlugin, ground: TerrainGround, cell: Vector2i, pressed: bool) -> void:
	var event := InputEventMouseMotion.new()
	event.position = ground.get_global_transform_with_canvas() * ((Vector2(cell) + Vector2.ONE * 0.5) * ground.kit.cell)
	event.button_mask = MOUSE_BUTTON_MASK_LEFT if pressed else 0
	plugin.call("_forward_canvas_gui_input", event)


static func run_lifecycle(plugin: EditorPlugin) -> Dictionary:
	var zone_plan := preload("res://tools/kit_zone.gd")
	var phase := ""
	var count := 0
	var mixed := false
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--we-lifecycle="):
			phase = arg.substr(15)
			count += 1
		mixed = mixed or arg.begins_with("--we-smoke-report=") or arg.begins_with("--we-capture=")
	var context: Dictionary = zone_plan.lifecycle_context(phase)
	var result := {"ok": false, "failures": [], "started_unix": Time.get_unix_time_from_system()}
	var failures: Array = result.failures
	if not bool(context.get("ok", false)):
		failures.append(context.get("message", "Invalid lifecycle context."))
		return zone_plan.lifecycle_finish(context, result)
	if count != 1 or phase not in ["author", "reopen"] or mixed or not Engine.is_editor_hint():
		failures.append("One editor lifecycle phase is required without legacy smoke/capture flags.")
		return zone_plan.lifecycle_finish(context, result)
	var scene := EditorInterface.get_edited_scene_root()
	var ground: TerrainGround = scene.get_node_or_null("Ground") as TerrainGround if scene != null else null
	if scene == null or scene.scene_file_path != zone_plan.LIFECYCLE_SCENE or ground == null or not ground.lab or ground.grid_size != Vector2i(8, 8):
		failures.append("Open the fresh named 8x8 private candidate lab scene.")
		return zone_plan.lifecycle_finish(context, result)
	plugin.call("_show_for_screenshot")
	plugin.call("_edit", ground)
	var operations: Object = plugin.get("operations")
	var metadata := {}
	var metadata_paths := {"lawn": "res://kit/pieces/terrain/lawn.json", "path": "res://kit/pieces/terrain/path.json", "woodland_forest_bench": "res://kit/pieces/prop/woodland_forest_bench.json"}
	for id in metadata_paths:
		var definition: Dictionary = operations.call("definition", id)
		var raw: Dictionary = zone_plan.lifecycle_read(metadata_paths[id])
		if raw.is_empty() or zone_plan.canonical(definition) != zone_plan.canonical(raw) or raw.get("approval", {}).get("state") not in ["candidate", "gated", "approved"]:
			failures.append("Original lab-legal piece metadata was missing or substituted: " + id)
		metadata[id] = {"approval": raw.get("approval", {}).get("state"), "sha256": FileAccess.get_sha256(metadata_paths[id]),
			"raw_collision": raw.get("geometry", {}).get("collision"), "compiled_collision": KitPiece.index().get(id, {}).get("collision")}
	result["piece_metadata"] = metadata
	if not failures.is_empty(): return zone_plan.lifecycle_finish(context, result)
	var expected_path: String = context.evidence.path_join("expected-plan.json")
	if phase == "author":
		var before: Dictionary = operations.call("export_plan")
		if not bool(before.get("ok", false)) or zone_plan.canonical(before.get("plan", {})) != zone_plan.canonical(zone_plan.lifecycle_probe_plan()):
			failures.append("Bootstrap scene differs from the unchanged persistence fixture's explicit lab clone.")
		for path in [expected_path, zone_plan.LIFECYCLE_PLAN, zone_plan.LIFECYCLE_PNG, zone_plan.LIFECYCLE_SIDECAR, zone_plan.LIFECYCLE_WALK]:
			if FileAccess.file_exists(path): failures.append("Fresh author output already exists: " + path)
		if not failures.is_empty(): return zone_plan.lifecycle_finish(context, result)
		var cells: Array[Vector2i] = []
		for y in range(5, 7):
			for x in range(1, 8): cells.append(Vector2i(x, y))
		var paint: Dictionary = plugin.call("paint_cells", cells, "path")
		var placement: Dictionary = plugin.call("place_piece", "woodland_forest_bench", Vector2(108, 120), {"id": "lifecycle_bench", "facing": "s", "variant": "forest_bench"})
		if not bool(paint.get("ok", false)) or not bool(placement.get("ok", false)):
			failures.append("Actual plugin painting/placement refused: %s / %s" % [paint, placement])
		if not failures.is_empty(): return zone_plan.lifecycle_finish(context, result)
		var piece := placement.get("node") as KitPiece
		var owned_walk := ground.get_node_or_null("KitWalk") as KitWalk
		if piece == null or piece.owner != scene or owned_walk == null or owned_walk.owner != scene or ground.pieces().size() != 1:
			failures.append("Authoring did not install owned piece/walk nodes.")
		var validation: Dictionary = plugin.call("validate_zone")
		if not bool(validation.get("ok", false)): failures.append("Actual full validator refused authored lab: " + str(validation))
		var snapshot: Dictionary = operations.call("export_plan")
		if not bool(snapshot.get("ok", false)): failures.append("Authored plan could not be exported.")
		if not failures.is_empty(): return zone_plan.lifecycle_finish(context, result)
		# Independent author intent, not a golden snapshot of whatever export returned.
		if not bool(paint.get("changed", false)) or piece.get("piece_id") != "woodland_forest_bench" or piece.name != &"lifecycle_bench" or piece.position != Vector2(108, 120) or piece.get("variant") != "forest_bench" or piece.get_meta(&"facing", "") != "s":
			failures.append("Actual authored piece or changed paint stroke differs from requested intent.")
		var authored_pieces: Array = snapshot.plan.get("pieces", [])
		if authored_pieces.size() != 1:
			failures.append("Export must contain exactly the one requested piece.")
		else:
			var entry: Dictionary = authored_pieces[0]
			if entry.get("id") != "lifecycle_bench" or entry.get("piece") != "woodland_forest_bench" or entry.get("at") != [108, 120] or entry.get("variant") != "forest_bench" or entry.get("facing") != "s":
				failures.append("Exported piece identity/options differ from author intent.")
		var path_cells := 0
		for y in range(8):
			for x in range(8):
				var wanted := "path" if x >= 1 and x <= 7 and y >= 5 and y <= 6 else "lawn"
				if wanted == "path": path_cells += 1
				var symbol: String = snapshot.plan.rows[y][x]
				if ground.material_at(Vector2i(x, y)) != ground.kit.material_id(wanted) or snapshot.plan.legend.get(symbol) != wanted:
					failures.append("Actual/exported material differs at cell(%d,%d)." % [x, y])
		var untouched_before: Dictionary = before.plan.duplicate(true)
		var untouched_after: Dictionary = snapshot.plan.duplicate(true)
		for key in ["rows", "legend", "pieces"]:
			untouched_before.erase(key)
			untouched_after.erase(key)
		if zone_plan.canonical(untouched_before) != zone_plan.canonical(untouched_after):
			failures.append("Authoring changed other seed fields, spawns, doors or extension metadata.")
		result["author_intent"] = {"path_cells": path_cells, "piece_count": authored_pieces.size(), "foot": [108, 120], "facing": "s", "variant": "forest_bench"}
		if not failures.is_empty(): return zone_plan.lifecycle_finish(context, result)
		if EditorInterface.save_scene() != OK or not zone_plan.lifecycle_write(expected_path, snapshot.plan):
			failures.append("Actual named scene save or expected-plan publication failed.")
		else:
			result["expected_plan_sha256"] = FileAccess.get_sha256(expected_path)
			result["scene_sha256"] = FileAccess.get_sha256(zone_plan.LIFECYCLE_SCENE)
			result["authoring_plan"] = snapshot.plan
	else:
		var author: Dictionary = zone_plan.lifecycle_prior(context, "author")
		var expected: Dictionary = zone_plan.lifecycle_read(expected_path)
		var snapshot: Dictionary = operations.call("export_plan")
		if author.is_empty() or expected.is_empty() or FileAccess.get_sha256(expected_path) != author.get("expected_plan_sha256") or FileAccess.get_sha256(zone_plan.LIFECYCLE_SCENE) != author.get("scene_sha256"):
			failures.append("Fresh reopen needs the successful distinct-process author receipt and exact saved files.")
		if not bool(snapshot.get("ok", false)) or zone_plan.canonical(snapshot.get("plan", {})) != zone_plan.canonical(expected) or metadata != author.get("piece_metadata"):
			failures.append("Fresh editor reopen changed authoring data or piece metadata.")
		for path in [zone_plan.LIFECYCLE_PLAN, zone_plan.LIFECYCLE_PNG, zone_plan.LIFECYCLE_SIDECAR, zone_plan.LIFECYCLE_WALK]:
			if FileAccess.file_exists(path): failures.append("Fresh reopen bake output already exists: " + path)
		if not failures.is_empty(): return zone_plan.lifecycle_finish(context, result)
		result["author_pid"] = author.pid
		result["author_report_sha256"] = FileAccess.get_sha256(String(context.evidence).path_join("author.json"))
		result["expected_plan_sha256"] = author.expected_plan_sha256
		var baked: Dictionary = plugin.call("bake_zone")
		result["bake_result"] = baked
		if not bool(baked.get("ok", false)): failures.append("Real positive bake/export/reimport failed: " + str(baked))
		var exported: Dictionary = zone_plan.lifecycle_read(zone_plan.LIFECYCLE_PLAN)
		var marker: Dictionary = zone_plan.lifecycle_read(zone_plan.LIFECYCLE_SIDECAR)
		var walk := ground.get_node_or_null("KitWalk") as KitWalk
		if zone_plan.canonical(exported) != zone_plan.canonical(expected) or marker.get("zone") != zone_plan.LIFECYCLE_ZONE or String(marker.get("hash", "")).length() != 16:
			failures.append("Real export or bake sidecar does not identify the authored probe.")
		if ground.baked == null or ground.baked.resource_path != zone_plan.LIFECYCLE_PNG or not ground.showing_baked() or ground.baked.get_size() != Vector2(192, 192):
			failures.append("Positive bake did not bind its actual192x192 texture.")
		if walk == null or walk.rows.is_empty() or walk.walk_text() != FileAccess.get_file_as_string(zone_plan.LIFECYCLE_WALK):
			failures.append("Positive bake did not export the actual active walk mask.")
		for key in ["scene", "png", "sidecar", "walk", "export"]:
			var paths := {"scene": zone_plan.LIFECYCLE_SCENE, "png": zone_plan.LIFECYCLE_PNG, "sidecar": zone_plan.LIFECYCLE_SIDECAR, "walk": zone_plan.LIFECYCLE_WALK, "export": zone_plan.LIFECYCLE_PLAN}
			if not FileAccess.file_exists(paths[key]): failures.append("Actual bake output absent: " + key)
			result[key + "_sha256"] = FileAccess.get_sha256(paths[key])
		# Deliberately NO extra save after bake. Fresh runtime must reveal any
		# missing baked binding caused by the production save-before-assignment order.
	if failures.is_empty():
		await plugin.get_tree().process_frame
		await RenderingServer.frame_post_draw
		var image := EditorInterface.get_base_control().get_viewport().get_texture().get_image()
		var capture: String = context.evidence.path_join(phase + ".png")
		if image == null or image.is_empty() or FileAccess.file_exists(capture) or image.save_png(capture) != OK:
			failures.append("Actual editor lifecycle capture failed.")
		else:
			result["capture"] = {"path": capture, "size": [image.get_width(), image.get_height()], "sha256": FileAccess.get_sha256(capture)}
	return zone_plan.lifecycle_finish(context, result)
