@tool
extends EditorPlugin
## W3 input/editor integration. Operations own transactions; W5/W6 own rules.
const Dock := preload("res://addons/world_editor/dock.gd")
const Operations := preload("res://addons/world_editor/operations.gd")
const Tools := preload("res://addons/world_editor/tools.gd")
const Rules := preload("res://addons/world_editor/rules_adapter.gd")
const Smoke := preload("res://addons/world_editor/smoke.gd")
const BakeJob := preload("res://addons/world_editor/bake_job.gd")

var dock
var operations := Operations.new()
var ground: TerrainGround
var zone: Node
var brush := ""
var tool_mode := "brush"
var brush_size := 1
var route_width := 2
var facing := "s"
var selected_variant := ""
var selected_stage := ""
var painting := false
var _stroke_start := Vector2i.ZERO
var _stroke_last := Vector2i.ZERO
var _stroke_points: Array[Vector2i] = []
var _stroke_cells: Array[Vector2i] = []
var _hover_local := Vector2.ZERO
var _has_hover := false
var _preview_key: Array = []
var _preview: Dictionary = {}
var _revision := 0
var _baking := false
var _bake_job: RefCounted
var _bake_zone_id := ""
var _bake_ground: TerrainGround
var _bake_zone: Node
var _bake_key := ""      ## the zone's plan when the painters started (Operations.bake_key)
signal bake_finished(result: Dictionary)
var _fence_style := ""
var clipboard: Array = []
var scatter := false
var scatter_density := 0.35
var _scatter_stroke := false
var _ghost_busy := ""
var _ghost_task := -1
var _followed_history: UndoRedo

func _enter_tree() -> void:
	operations.changed.connect(_operations_changed)
	# Godot's own move, delete, duplicate and inspector edits reach the zone through the editor's
	# history, not through operations: follow it, so the walk mask, shadows and previews keep up.
	var manager := get_undo_redo()
	if manager != null and not manager.history_changed.is_connected(_history_changed):
		manager.history_changed.connect(_history_changed)
	dock = Dock.new()
	dock.plugin = self
	dock.name = "World"
	add_control_to_dock(DOCK_SLOT_RIGHT_UL, dock)
	# Separate opt-in lifecycle: never schedule the old smoke alongside it.
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--we-lifecycle="):
			_run_editor_lifecycle.call_deferred()
			return
	var show_requested := false
	var smoke_requested := false
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--we-show="):
			show_requested = true
		if arg.begins_with("--we-smoke-report="):
			smoke_requested = true
	if smoke_requested:
		_run_automatic_editor_smoke.call_deferred(show_requested)
	elif show_requested:
		_show_when_ready.call_deferred()

func _exit_tree() -> void:
	_cancel_stroke()
	_reap_ghost_task()
	if _bake_job != null:
		_bake_job.cancel()             # a bake does not outlive the editor that asked for it
		_bake_job = null
	if operations.changed.is_connected(_operations_changed):
		operations.changed.disconnect(_operations_changed)
	var manager := get_undo_redo()
	if manager != null and manager.history_changed.is_connected(_history_changed):
		manager.history_changed.disconnect(_history_changed)
	_follow_history(null)
	if is_instance_valid(dock):
		remove_control_from_docks(dock)
		dock.queue_free()
	dock = null
	ground = null
	zone = null

func _handles(object: Object) -> bool:
	return _ground_of(object) != null

func _edit(object: Object) -> void:
	_cancel_stroke()
	var next := _ground_of(object)
	if next == null and Engine.is_editor_hint():
		# Deleting the selected piece (or clicking empty space) leaves nothing selected. The dock
		# stays on the open zone, so its palette, Validate and Export keep working; the canvas
		# takes clicks again as soon as anything in the zone is selected.
		next = _ground_of(EditorInterface.get_edited_scene_root())
	if next != null and next == ground and is_instance_valid(zone) and zone == ground.get_parent():
		# Another node of the same zone was selected: nothing to reload (re-reading the library's
		# 264 files on every click made selection lag, and wiped the status line).
		_revision += 1
		_preview_key.clear()
		return
	ground = next
	zone = ground.get_parent() if ground != null else null
	_follow_history(zone)
	operations.configure(zone, ground, get_undo_redo(), {
		"relation_evaluator": Callable(Rules, "placement"),
		"zone_validator": Callable(Rules, "validate_plan"),
		"install_walk": true,
	})
	_revision += 1
	_preview_key.clear()
	if is_instance_valid(dock):
		dock.set_zone(zone, ground)

## The zone's own undo history: its version changes on every commit, undo and redo, whoever made
## them (the manager's history_changed does not fire for an undo run on the history itself).
func _follow_history(target: Node) -> void:
	if is_instance_valid(_followed_history) and _followed_history.version_changed.is_connected(_history_changed):
		_followed_history.version_changed.disconnect(_history_changed)
	_followed_history = null
	var manager := get_undo_redo()
	if target == null or manager == null or not target.is_inside_tree():
		return
	_followed_history = manager.get_history_undo_redo(manager.get_object_history_id(target))
	if _followed_history != null and not _followed_history.version_changed.is_connected(_history_changed):
		_followed_history.version_changed.connect(_history_changed)

## Before a save or a tab switch: nothing of this process may reach the scene file.
func _apply_changes() -> void:
	operations.prepare_save(ground)

func _make_visible(visible: bool) -> void:
	if not visible:
		_cancel_stroke()

func _ground_of(object: Object) -> TerrainGround:
	if object is TerrainGround:
		return object
	if object is Node:
		var node: Node = object
		while node != null:
			var found := node.get_node_or_null("Ground") as TerrainGround
			if found != null:
				return found
			node = node.get_parent()
	return null

func _forward_canvas_gui_input(event: InputEvent) -> bool:
	if not is_instance_valid(ground) or brush.is_empty():
		if painting:
			_cancel_stroke()
		return false
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_ESCAPE:
			if painting:
				_cancel_stroke()
				return true
			# Escape with no stroke under way puts the brush down: the canvas goes back to
			# Godot's own select and move tools.
			_cancel_stroke()
			if is_instance_valid(dock):
				dock.select_tool()
			else:
				brush = ""
			return true
		if brush.begins_with("piece:") and event.keycode == KEY_V:
			if is_instance_valid(dock):
				dock.cycle_variant()
			return true
		if brush.begins_with("piece:") and event.keycode in [KEY_Q, KEY_E]:
			facing = Tools.next_facing(facing, -1 if event.keycode == KEY_Q else 1)
			refresh_preview()
			if is_instance_valid(dock):
				dock.show_piece(brush.substr(6))
			return true
	if not event is InputEventMouse:
		return false
	if event.alt_pressed or event.ctrl_pressed or event.meta_pressed:
		if painting:
			_cancel_stroke()
		return false
	var local: Vector2 = ground.get_global_transform_with_canvas().affine_inverse() * event.position
	var cell_size := ground.kit.cell if ground.kit != null else 24
	var cell := Vector2i(floori(local.x / cell_size), floori(local.y / cell_size))
	_hover_local = local
	_has_hover = true
	if event is InputEventMouseMotion:
		if painting and (event.button_mask & MOUSE_BUTTON_MASK_LEFT) == 0:
			_cancel_stroke()
		if painting:
			_extend_stroke(cell)
		if is_instance_valid(dock):
			dock.hover(cell, local)
		update_overlays()
		return painting
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			_fence_style = fence_style(brush.substr(6)) if brush.begins_with("piece:") else ""
			_scatter_stroke = brush.begins_with("piece:") and scatter and _fence_style == ""
			if brush == "group:":
				_say_result(operations.paste_group(clipboard, local), "Pasted the group")
				return true
			if brush.begins_with("gameplay:"):
				var options: Dictionary = dock.gameplay_options() if is_instance_valid(dock) else {}
				var made := operations.place_gameplay(brush.substr(9), local, options)
				_say_result(made, String(made.get("message", "Placed")))
				if bool(made.get("ok", false)):
					# one click, one node: put the brush down and show the node in the inspector
					if is_instance_valid(dock):
						dock.select_tool(String(made.get("message", "")))
					else:
						brush = ""
					if Engine.is_editor_hint() and made.get("node") is Node:
						EditorInterface.get_selection().clear()
						EditorInterface.get_selection().add_node(made.node)
						EditorInterface.edit_node(made.node)
				return true
			if brush.begins_with("piece:") and is_crossing(brush.substr(6)):
				_say_result(operations.place_crossing(brush.substr(6), local, _piece_options()), "Placed on the run")
				return true
			if brush.begins_with("piece:") and _fence_style == "" and not _scatter_stroke:
				_say_result(place_piece(brush.substr(6), local), "Placed piece")
				return true
			if not _inside(cell):
				return false
			painting = true
			_stroke_start = cell
			_stroke_last = cell
			_stroke_points = [cell]
			_stroke_cells.clear()
			_extend_stroke(cell)
			return true
		if painting:
			_extend_stroke(cell)
			var cells := _bounded_cells(_stroke_cells)
			_cancel_stroke()
			if _fence_style != "":
				var style := _fence_style
				_fence_style = ""
				_say_result(operations.place_fence_run(style, cells, _piece_options()), "Fence run placed")
				return true
			if _scatter_stroke:
				_scatter_stroke = false
				var zone_seed := String(zone.name).hash() if is_instance_valid(zone) else 7
				var scatter_options := _piece_options()
				scatter_options.merge({"density": scatter_density, "seed": zone_seed}, true)
				_say_result(operations.scatter(brush.substr(6), cells, scatter_options), "Scattered")
				return true
			if brush.begins_with("tier:"):
				var tier := int(brush.substr(5))
				var raised := operations.paint_tiers(cells, tier)
				_say_result(raised, String(raised.get("message", "")))
				return true
			if brush.begins_with("flow:"):
				var flowed := operations.paint_flow(cells, brush.substr(5))
				_say_result(flowed, String(flowed.get("message", "No flow changed.")))
				return true
			var material := brush.substr(9) if brush.begins_with("material:") else ""
			var variant := brush.substr(8) if brush.begins_with("variant:") else ""
			var painted := paint_cells(cells, material, variant)
			_say_result(painted, "Painted %d cells%s" % [painted.get("cells", cells).size(), ", centred on the door" if painted.get("snapped", false) else ""])
			return true
	return false

func _inside(cell: Vector2i) -> bool:
	return is_instance_valid(ground) and cell.x >= 0 and cell.y >= 0 and cell.x < ground.grid_size.x and cell.y < ground.grid_size.y

func _bounded_cells(cells: Array) -> Array[Vector2i]:
	var result: Array[Vector2i] = []
	for cell in cells:
		if _inside(cell) and cell not in result:
			result.append(cell)
	return result

func _extend_stroke(cell: Vector2i) -> void:
	if _scatter_stroke:
		for centre in Tools.line_cells(_stroke_last, cell):
			for target in Tools.brush_cells(centre, maxi(brush_size, 2)):
				if target not in _stroke_cells:
					_stroke_cells.append(target)
		_stroke_last = cell
		update_overlays()
		return
	if _fence_style != "":
		# a fence run follows the pointer cell by cell, four-connected, as the run will join
		for target in Tools.line_cells(_stroke_last, cell):
			if target not in _stroke_cells:
				_stroke_cells.append(target)
		_stroke_last = cell
		update_overlays()
		return
	match tool_mode:
		"rectangle":
			_stroke_cells = Tools.rectangle_cells(_stroke_start, cell)
		"route":
			if _stroke_points.is_empty() or _stroke_points.back() != cell:
				_stroke_points.append(cell)
			_stroke_cells = Tools.route_cells(_stroke_points, route_width)
		_:
			for centre in Tools.line_cells(_stroke_last, cell):
				for target in Tools.brush_cells(centre, brush_size):
					if target not in _stroke_cells:
						_stroke_cells.append(target)
	_stroke_last = cell
	update_overlays()

func _cancel_stroke() -> void:
	painting = false
	_stroke_points.clear()
	_stroke_cells.clear()
	_preview_key.clear()
	_has_hover = false
	update_overlays()

## The dock and non-UI acceptance tests share this operations API.
func paint_cells(cells: Array, material_id: String, variant: String = "") -> Dictionary:
	return operations.paint_cells(cells, material_id, variant)

## A gate or a stile: placed on an existing run (operations.place_crossing).
func is_crossing(id: String) -> bool:
	var boundary: Variant = operations.definition(id).get("placement", {}).get("boundary")
	return boundary is Dictionary and (bool(boundary.get("gate", false)) or bool(boundary.get("stile", false)))

## The live fault overlay's verdict for the ghost: cached, or worked out on a worker thread (the
## full validator runs a Python process) while the canvas keeps the relation engine's fast verdict.
func ghost_verdict(id: String, at: Vector2) -> Dictionary:
	var info := operations.ghost_plan(id, at, _piece_options())
	if info.is_empty():
		return {}
	var cached := operations.ghost_cached(info)
	if not cached.is_empty():
		return cached
	if _ghost_busy == "":
		_ghost_busy = String(info.key)
		_ghost_task = WorkerThreadPool.add_task(func() -> void:
			var verdict := operations.ghost_compute(info)
			_ghost_done.call_deferred(String(info.key), verdict))
	return {}

## Every WorkerThreadPool task must be waited for, or the pool never releases it: a task left
## unwaited (even an empty one) made the editor abort at exit with "corrupted size vs. prev_size in
## fastbins", exit 134, after any session in which a piece's ghost had been checked (10 Nov: 4 of 4
## runs before, none after; the same work on the main thread, or waited for, exits cleanly).
func _reap_ghost_task() -> void:
	if _ghost_task != -1:
		WorkerThreadPool.wait_for_task_completion(_ghost_task)
		_ghost_task = -1

func _ghost_done(key: String, verdict: Dictionary) -> void:
	_reap_ghost_task()
	operations.ghost_store(key, verdict)
	_ghost_busy = ""
	update_overlays()

## The fence style of a fence cell piece (a run is drawn by dragging), or "" for anything else
## (gates and stiles are placed one at a time, on their path).
func fence_style(id: String) -> String:
	var boundary: Variant = operations.definition(id).get("placement", {}).get("boundary")
	if not boundary is Dictionary or bool(boundary.get("gate", false)) or bool(boundary.get("stile", false)):
		return ""
	return String(boundary.get("style", ""))

## Copy the pieces selected in the scene tree or on the canvas (group copy, round 4).
func copy_selection() -> Dictionary:
	var nodes: Array = EditorInterface.get_selection().get_selected_nodes() if Engine.is_editor_hint() else []
	var result := operations.copy_group(nodes)
	if bool(result.get("ok", false)):
		clipboard = result.group
	return result

func place_piece(id: String, at: Vector2, options: Dictionary = {}) -> Dictionary:
	var chosen := _piece_options()
	chosen.merge(options, true)
	return operations.place_piece(id, at, chosen)

func _piece_options() -> Dictionary:
	var options := {"facing": facing}
	if not selected_variant.is_empty():
		options["variant"] = selected_variant
	if not selected_stage.is_empty():
		options["stage"] = selected_stage
	return options

func preview_piece(id: String, at: Vector2) -> Dictionary:
	var raw := operations.definition(id)
	var cell_size := ground.kit.cell if is_instance_valid(ground) and ground.kit != null else 24
	var snapped := Tools.snap(at, String(raw.get("placement", {}).get("snap", "cell")), cell_size)
	var key: Array = [id, snapped, facing, selected_variant, selected_stage, _revision]
	if key != _preview_key:
		_preview_key = key
		_preview = operations.preview_piece(id, at, _piece_options())
	return _preview.duplicate(true)

func refresh_preview() -> void:
	_preview_key.clear()
	update_overlays()

func refresh_library() -> void:
	operations.configure(zone, ground, get_undo_redo(), {
		"relation_evaluator": Callable(Rules, "placement"),
		"zone_validator": Callable(Rules, "validate_plan"),
		"install_walk": true,
	})
	_revision += 1
	_preview_key.clear()
	update_overlays()

func validate() -> Dictionary:
	return operations.validate()

func validate_zone() -> Dictionary:
	return validate()

func _operations_changed() -> void:
	_revision += 1
	_preview_key.clear()
	operations.refresh_derived(operations.last_changed_ground)
	update_overlays()

func _history_changed() -> void:
	_native_sync.call_deferred()

## After any action in the editor's history (ours or Godot's own): drop the cached preview, and
## when the placed pieces changed outside the dock, bring the derived data up to date.
func _native_sync() -> void:
	if not is_instance_valid(ground) or not ground.is_inside_tree():
		return
	_revision += 1
	_preview_key.clear()
	if operations.sync_native_edits():
		update_overlays()

## Save the zone and write its plan beside the others (the dock's Export plan).
func export_plan_file() -> Dictionary:
	if not is_instance_valid(zone) or not is_instance_valid(ground):
		return Rules.failure("editor.zone_missing", "Select a kit zone first.")
	if Engine.is_editor_hint():
		if zone != EditorInterface.get_edited_scene_root():
			return Rules.failure("editor.export_scene", "Open the zone as its own scene before exporting its plan.")
		if String(zone.scene_file_path).is_empty() or EditorInterface.save_scene() != OK:
			return Rules.failure("editor.save_failed", "The scene could not be saved; no plan was written.")
	return operations.export_plan_file()

func _forward_canvas_draw_over_viewport(overlay: Control) -> void:
	if not is_instance_valid(ground) or ground.kit == null or not _has_hover:
		return
	var transform := ground.get_global_transform_with_canvas()
	var cell_size := ground.kit.cell
	if brush == "group:":
		# the group's footprints where it would land
		var corner := (_hover_local / cell_size).floor() * cell_size
		for g in clipboard:
			var foot: Vector2 = corner + Vector2(g.get("offset", Vector2.ZERO))
			var c := Vector2i(floori(foot.x / cell_size), floori((foot.y - 1) / cell_size))
			_draw_rect(overlay, transform, Rect2(Vector2(c * cell_size), Vector2.ONE * cell_size), Color(0.9, 0.75, 0.4, 0.35))
		return
	if brush.begins_with("gameplay:"):
		# where the spawn, door or actor would stand (snapped to 4 world px)
		var point := transform * Tools.snap(_hover_local, "half", cell_size)
		var colour_g := Color(0.95, 0.6, 0.95, 0.95)
		overlay.draw_line(point - Vector2(8, 0), point + Vector2(8, 0), colour_g, 2.0)
		overlay.draw_line(point - Vector2(0, 8), point + Vector2(0, 8), colour_g, 2.0)
		overlay.draw_string(ThemeDB.fallback_font, point + Vector2(10, -10), brush.substr(9), HORIZONTAL_ALIGNMENT_LEFT, -1, 14, colour_g)
		return
	if brush.begins_with("tier:") or brush.begins_with("flow:"):
		_draw_height_and_flow(overlay, transform, cell_size)
	if not brush.begins_with("piece:") or (painting and (_fence_style != "" or _scatter_stroke)):
		var cell := Vector2i(floori(_hover_local.x / cell_size), floori(_hover_local.y / cell_size))
		var cells := _stroke_cells if painting else Tools.brush_cells(cell, brush_size)
		for target in _bounded_cells(cells):
			_draw_rect(overlay, transform, Rect2(Vector2(target * cell_size), Vector2.ONE * cell_size), Color(0.55, 0.8, 1.0, 0.22))
		if painting and _fence_style != "":
			# the pieces the run will choose: each cell's arms from its node
			var chosen: Dictionary = operations.preview_fence_run(_fence_style, _bounded_cells(_stroke_cells))
			for at in chosen:
				var id := String(chosen[at])
				var node := Vector2(at.x * cell_size + cell_size / 2.0, (at.y + 1) * cell_size)
				var joins := id.get_slice("_", id.get_slice_count("_") - 1) if id != "" else ""
				for side in joins:
					var arm: Vector2 = Vector2(Tools.SIDES[side]) * (cell_size / 2.0)
					overlay.draw_line(transform * node, transform * (node + arm), Color(0.95, 0.85, 0.3, 0.95) if id != "" else Color(1, 0.3, 0.3), 3.0)
				if id == "":
					overlay.draw_circle(transform * node, 3.0, Color(1, 0.3, 0.3))
		return
	var id := brush.substr(6)
	var result := preview_piece(id, _hover_local)
	var raw := operations.definition(id)
	var at: Vector2 = result.get("at", Tools.snap(_hover_local, String(raw.get("placement", {}).get("snap", "cell")), cell_size))
	var colour := Color(0.4, 0.9, 0.5, 0.4) if bool(result.get("ok", false)) else Color(1.0, 0.35, 0.3, 0.4)
	var label := ""
	if not bool(result.get("ok", false)):
		var d: Array = result.get("diagnostics", [])
		label = Tools.short_rule(String(d[0].get("rule", d[0].get("check", "")))) if not d.is_empty() and d[0] is Dictionary else "refused"
	else:
		var gv := ghost_verdict(id, _hover_local)
		if String(gv.get("severity", "")) == "fault":
			colour = Color(1.0, 0.35, 0.3, 0.4)
			label = String(gv.get("rule", ""))
		elif String(gv.get("severity", "")) == "advice":
			colour = Color(1.0, 0.75, 0.2, 0.4)
			label = String(gv.get("rule", ""))
		elif gv.is_empty() and _ghost_busy != "":
			label = "checking..."
	var footprint: Array = raw.get("geometry", {}).get("footprint", [])
	if footprint.is_empty():
		footprint = [[0, -1]] if is_zero_approx(fposmod(at.y, cell_size)) else [[0, 0]]
	var foot_cell := Vector2i(floori(at.x / cell_size), floori(at.y / cell_size))
	for offset in footprint:
		if offset is Array and offset.size() == 2:
			var c := foot_cell + Vector2i(int(offset[0]), int(offset[1]))
			_draw_rect(overlay, transform, Rect2(Vector2(c * cell_size), Vector2.ONE * cell_size), colour)
	var origin := transform * at
	if label != "":
		overlay.draw_string(ThemeDB.fallback_font, origin + Vector2(10, -10), label, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, colour.lightened(0.6))
	var direction := Vector2.DOWN
	match facing:
		"n": direction = Vector2.UP
		"e": direction = Vector2.RIGHT
		"w": direction = Vector2.LEFT
	var end := transform * (at + direction * cell_size)
	overlay.draw_line(origin, end, colour.lightened(0.4), 2.0)
	var tangent := direction.orthogonal() * 4.0
	overlay.draw_line(end, transform * (at + direction * (cell_size - 7) + tangent), colour.lightened(0.4), 2.0)
	overlay.draw_line(end, transform * (at + direction * (cell_size - 7) - tangent), colour.lightened(0.4), 2.0)
	for relation in raw.get("placement", {}).get("requires", []):
		var radius := float(relation.get("cells", 0))
		if radius > 0:
			var points := PackedVector2Array()
			for step in range(33):
				var angle := TAU * float(step) / 32.0
				points.append(transform * (at + Vector2(cos(angle), sin(angle)) * radius * cell_size))
			overlay.draw_polyline(points, Color(0.85, 0.8, 0.4, 0.7), 1.0)

## Tiers and flow have no picture of their own, so their brushes show them: each raised cell's
## tier as a number, each flow cell's direction as an arrow.
func _draw_height_and_flow(overlay: Control, transform: Transform2D, cell_size: int) -> void:
	if brush.begins_with("tier:"):
		for y in ground.grid_size.y:
			for x in ground.grid_size.x:
				var tier := ground.tier_at(Vector2i(x, y))
				if tier > 0:
					_draw_rect(overlay, transform, Rect2(Vector2(x, y) * cell_size, Vector2.ONE * cell_size), Color(1.0, 0.8, 0.3, 0.08 + 0.1 * tier))
					overlay.draw_string(ThemeDB.fallback_font, transform * (Vector2(x + 0.3, y + 0.75) * cell_size), str(tier), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(1, 0.95, 0.7))
		return
	var rows := operations.flow_rows()
	for y in rows.size():
		for x in rows[y].length():
			var direction: Vector2i = Tools.FLOW_DIRECTIONS.get(rows[y][x], Vector2i.ZERO)
			if direction == Vector2i.ZERO:
				continue
			var centre := (Vector2(x, y) + Vector2.ONE * 0.5) * cell_size
			var reach := Vector2(direction).normalized() * cell_size * 0.35
			var tip := centre + reach
			overlay.draw_line(transform * (centre - reach), transform * tip, Color(0.8, 0.95, 1.0, 0.95), 2.0)
			for side in [-1.0, 1.0]:
				overlay.draw_line(transform * tip, transform * (tip - reach.rotated(side * 0.6) * 0.6), Color(0.8, 0.95, 1.0, 0.95), 2.0)

func _draw_rect(overlay: Control, transform: Transform2D, rect: Rect2, colour: Color) -> void:
	var points := PackedVector2Array([transform * rect.position, transform * Vector2(rect.end.x, rect.position.y), transform * rect.end, transform * Vector2(rect.position.x, rect.end.y)])
	overlay.draw_colored_polygon(points, colour)
	points.append(points[0])
	overlay.draw_polyline(points, colour.lightened(0.2), 1.0)

func _say_result(result: Dictionary, success: String) -> void:
	if not is_instance_valid(dock):
		return
	if bool(result.get("ok", false)):
		dock.say(success)
	else:
		var findings: Array = result.get("diagnostics", [])
		var text := String(result.get("message", "The operation was refused."))
		if not findings.is_empty():
			text = "%s: %s" % [findings[0].get("check", findings[0].get("code", "rules")), findings[0].get("message", text)]
		dock.say(text)

## The bake runs as its own process beside the editor (bake_job.gd). start_bake returns at once;
## _process shows its progress on the dock and takes its result when it ends; cancel_bake stops it.
## Before 11 Nov the editor stood still for the whole bake (about 19 s a screen).
func start_bake() -> Dictionary:
	if _baking or bake_running() or EditorInterface.get_resource_filesystem().is_importing():
		return Rules.failure("editor.bake_busy", "Wait for the current bake or resource import to finish.")
	_baking = true
	var prepared := _bake_prepare()
	_baking = false
	if not bool(prepared.get("ok", false)):
		return prepared
	var job := BakeJob.new()
	var project := ProjectSettings.globalize_path("res://")
	var repo := project.trim_suffix("/").get_base_dir()
	var log := ProjectSettings.globalize_path("user://world_editor_bake_%d.log" % OS.get_process_id())
	if not job.start_module(Rules.python_binary(), repo, "scripts.art.kit.bake", PackedStringArray([String(prepared.zone_id)]), log, "Baking %s" % prepared.zone_id):
		return Rules.failure("editor.bake_failed", "The bake could not be started (is Python on the PATH?).")
	job.leftovers = PackedStringArray([ProjectSettings.globalize_path("res://zones/%s/ground_baked.png.tmp" % prepared.zone_id)])
	_bake_job = job
	_bake_zone_id = String(prepared.zone_id)
	_bake_ground = ground
	_bake_zone = zone
	_bake_key = Operations.bake_key(zone)
	return {"ok": true, "diagnostics": [], "running": true, "message": "Baking %s: the editor stays usable; press Cancel bake to stop it." % _bake_zone_id}

func bake_running() -> bool:
	return _bake_job != null

func cancel_bake() -> Dictionary:
	if _bake_job == null:
		return Rules.failure("editor.bake_idle", "No bake is running.")
	_bake_job.cancel()
	_bake_job = null
	var result := Rules.failure("editor.bake_cancelled", "Bake of %s cancelled; the zone keeps the ground it had." % _bake_zone_id)
	bake_finished.emit(result)
	if is_instance_valid(dock):
		dock.bake_done(result)
	return result

func _process(_delta: float) -> void:
	if _bake_job == null:
		return
	if _bake_job.running():
		if is_instance_valid(dock):
			dock.bake_progress(_bake_job.progress_text())
		return
	var result := _bake_finish()
	bake_finished.emit(result)
	if is_instance_valid(dock):
		dock.bake_done(result)

## The blocking form (the acceptance runs use it): the same job, waited for.
func bake_zone() -> Dictionary:
	var started := start_bake()
	if not bool(started.get("ok", false)):
		return started
	while _bake_job != null and _bake_job.running():
		OS.delay_msec(50)
	return _bake_finish()

## Everything before the painters run: the checks, the save and the plan the painters read.
func _bake_prepare() -> Dictionary:
	if not is_instance_valid(zone) or not is_instance_valid(ground):
		return Rules.failure("editor.zone_missing", "Select a kit zone first.")
	if zone != EditorInterface.get_edited_scene_root():
		return Rules.failure("editor.bake_scene", "Open the selected zone as its own scene before baking.")
	var snapshot := operations.export_plan()
	if not bool(snapshot.get("ok", false)):
		return snapshot
	# The current painter CLI consumes texels. Preserve W2's authored coordinate space
	# rather than silently baking cell positions as texels or rewriting its plan.
	if snapshot.plan.get("coordinate_space", "texels") != "texels":
		return Rules.failure("editor.bake_coordinates", "Baking cell-coordinate plans is not supported yet. Painting, placement and validation remain available.")
	var review := validate_zone()
	if not bool(review.get("ok", false)):
		return review
	var scene_path := String(zone.scene_file_path)
	var zone_id := String(zone.get("zone_id"))
	var id_pattern := RegEx.new()
	id_pattern.compile("^[A-Za-z0-9_-]+$")
	if scene_path.is_empty() or not scene_path.begins_with("res://") or id_pattern.search(zone_id) == null:
		return Rules.failure("editor.save_required", "Save this named zone scene before baking.")
	if EditorInterface.save_scene() != OK:
		return Rules.failure("editor.save_failed", "The scene could not be saved; no bake was run.")
	var exported := operations.export_plan_file("res://kit/zones/%s.json" % zone_id)
	if not bool(exported.get("ok", false)):
		return Rules.failure("editor.export_failed", "Plan export failed: %s" % exported.get("message", ""))
	return {"ok": true, "diagnostics": [], "zone_id": zone_id}

## The job has ended: take its picture in, or say why not.
func _bake_finish() -> Dictionary:
	var job := _bake_job
	_bake_job = null
	if job == null:
		return Rules.failure("editor.bake_idle", "No bake is running.")
	var zone_id := _bake_zone_id
	if job.exit_code() != 0:
		return Rules.failure("editor.bake_failed", "Ground bake failed (exit %d): %s" % [job.exit_code(), job.output().right(1200)])
	var png := "res://zones/%s/ground_baked.png" % zone_id
	# A zone's first bake writes a picture the editor has never seen: tell the file system about it
	# before asking for the import, or the import fails with "Can't find file" and the bake that
	# just succeeded is reported as having produced nothing.
	var files := EditorInterface.get_resource_filesystem()
	files.update_file(png)
	files.reimport_files(PackedStringArray([png]))
	if not ResourceLoader.exists(png):
		return Rules.failure("editor.bake_missing", "The bake did not produce its ground image.")
	if not is_instance_valid(_bake_ground):
		return Rules.failure("editor.bake_scene", "The zone was closed while it baked; its picture is on disk and binds at the next bake.")
	var texture := ResourceLoader.load(png, "Texture2D", ResourceLoader.CACHE_MODE_REPLACE) as Texture2D
	if not operations.bind_bake(_bake_zone, _bake_ground, texture, _bake_key):
		# the zone was edited while the painters ran: the picture is behind it. Nothing is saved over
		# the edit and walk.txt stays the export of the plan the painters read.
		operations.refresh_derived(_bake_ground)
		return Rules.failure("editor.bake_behind", "Baked %s, but the zone was edited during the bake: the picture is behind it and is not shown. Bake again." % zone_id)
	operations.refresh_derived(_bake_ground)
	if operations.write_walk_file(_bake_ground, "res://zones/%s/walk.txt" % zone_id) != OK:
		return Rules.failure("editor.walk_export_failed", "The ground was baked, but its walk mask could not be written.")
	# The scene was saved before the painters ran, so the file on disk does not hold the new
	# picture yet: save again, or the game would show the live tiles until the next save.
	var saved := _bake_zone == EditorInterface.get_edited_scene_root() and EditorInterface.save_scene() == OK
	return {"ok": true, "diagnostics": [], "message": "Baked %s in %d s%s" % [zone_id, int(job.seconds()), "" if saved else "; save the scene to keep it"]}

func _show_for_screenshot() -> void:
	EditorInterface.set_main_screen_editor("2D")
	var root := EditorInterface.get_edited_scene_root()
	if root != null:
		var target := root.get_node_or_null("Ground")
		EditorInterface.get_selection().clear()
		EditorInterface.get_selection().add_node(target if target != null else root)
	var node: Node = dock
	while node.get_parent() != null and not node.get_parent() is TabContainer:
		node = node.get_parent()
	var tabs := node.get_parent() as TabContainer
	if tabs != null:
		tabs.current_tab = node.get_index()

func _run_editor_smoke() -> void:
	var result: Dictionary = await Smoke.run(self)
	_finish_editor_smoke(result)

func _run_automatic_editor_smoke(show_requested: bool) -> void:
	var readiness: Dictionary = await Smoke.wait_for_editor_scene(self, "res://zones/kitlab/kitlab.tscn")
	var result: Dictionary
	if bool(readiness.get("ok", false)):
		if show_requested:
			_show_for_screenshot()
		result = await Smoke.run(self)
	else:
		result = {"ok": false, "failures": ["Editor startup scene readiness failed."]}
	result["startup_readiness"] = readiness
	_finish_editor_smoke(result)

func _show_when_ready() -> void:
	var readiness: Dictionary = await Smoke.wait_for_editor_scene(self, Smoke.requested_editor_scene())
	print("WORLD_EDITOR_STARTUP ", JSON.stringify(readiness))
	if bool(readiness.get("ok", false)):
		_show_for_screenshot()

func _finish_editor_smoke(result: Dictionary) -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--we-smoke-report="):
			var file := FileAccess.open(arg.substr(18), FileAccess.WRITE)
			if file != null:
				file.store_string(JSON.stringify(result, "  "))
				file.close()
	print("WORLD_EDITOR_SMOKE ", JSON.stringify(result))
	get_tree().quit(0 if bool(result.get("ok", false)) else 1)

func _run_editor_lifecycle() -> void:
	var result: Dictionary = await Smoke.run_lifecycle(self, true)
	print("WORLD_EDITOR_LIFECYCLE ", JSON.stringify(result))
	get_tree().quit(0 if bool(result.get("ok", false)) else 1)
