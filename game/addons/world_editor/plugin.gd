@tool
extends EditorPlugin
## W3 input/editor integration. Operations own transactions; W5/W6 own rules.
const Dock := preload("res://addons/world_editor/dock.gd")
const Operations := preload("res://addons/world_editor/operations.gd")
const Tools := preload("res://addons/world_editor/tools.gd")
const Rules := preload("res://addons/world_editor/rules_adapter.gd")
const Walk := preload("res://world/terrain/walk.gd")
const Smoke := preload("res://addons/world_editor/smoke.gd")

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

func _enter_tree() -> void:
	operations.changed.connect(_operations_changed)
	dock = Dock.new()
	dock.plugin = self
	dock.name = "World"
	add_control_to_dock(DOCK_SLOT_RIGHT_UL, dock)
	# Separate opt-in lifecycle: never schedule the old smoke alongside it.
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--we-lifecycle="):
			get_tree().create_timer(4.0).timeout.connect(_run_editor_lifecycle)
			return
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--we-show="):
			get_tree().create_timer(3.0).timeout.connect(_show_for_screenshot)
		if arg.begins_with("--we-smoke-report="):
			get_tree().create_timer(4.0).timeout.connect(_run_editor_smoke)

func _exit_tree() -> void:
	_cancel_stroke()
	if operations.changed.is_connected(_operations_changed):
		operations.changed.disconnect(_operations_changed)
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
	ground = _ground_of(object)
	zone = ground.get_parent() if ground != null else null
	operations.configure(zone, ground, get_undo_redo(), {
		"relation_evaluator": Callable(Rules, "placement"),
		"zone_validator": Callable(Rules, "validate_plan"),
	})
	_revision += 1
	_preview_key.clear()
	if is_instance_valid(dock):
		dock.set_zone(zone, ground)

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
			_cancel_stroke()
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
			if brush.begins_with("piece:"):
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
			var material := brush.substr(9) if brush.begins_with("material:") else ""
			var variant := brush.substr(8) if brush.begins_with("variant:") else ""
			_say_result(paint_cells(cells, material, variant), "Painted %d cells" % cells.size())
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
	var target: TerrainGround = operations.last_changed_ground
	if is_instance_valid(target):
		target.rebuild_shadows()
		var walk := target.get_node_or_null("KitWalk") as KitWalk
		if walk == null:
			walk = Walk.new()
			walk.name = "KitWalk"
			target.add_child(walk)
			walk.owner = target.owner
		walk.rebuild(target)
	update_overlays()

func _forward_canvas_draw_over_viewport(overlay: Control) -> void:
	if not is_instance_valid(ground) or ground.kit == null or not _has_hover:
		return
	var transform := ground.get_global_transform_with_canvas()
	var cell_size := ground.kit.cell
	if not brush.begins_with("piece:"):
		var cell := Vector2i(floori(_hover_local.x / cell_size), floori(_hover_local.y / cell_size))
		var cells := _stroke_cells if painting else Tools.brush_cells(cell, brush_size)
		for target in _bounded_cells(cells):
			_draw_rect(overlay, transform, Rect2(Vector2(target * cell_size), Vector2.ONE * cell_size), Color(0.55, 0.8, 1.0, 0.22))
		return
	var id := brush.substr(6)
	var result := preview_piece(id, _hover_local)
	var raw := operations.definition(id)
	var at: Vector2 = result.get("at", Tools.snap(_hover_local, String(raw.get("placement", {}).get("snap", "cell")), cell_size))
	var colour := Color(0.4, 0.9, 0.5, 0.4) if bool(result.get("ok", false)) else Color(1.0, 0.35, 0.3, 0.4)
	var footprint: Array = raw.get("geometry", {}).get("footprint", [])
	if footprint.is_empty():
		footprint = [[0, -1]] if is_zero_approx(fposmod(at.y, cell_size)) else [[0, 0]]
	var foot_cell := Vector2i(floori(at.x / cell_size), floori(at.y / cell_size))
	for offset in footprint:
		if offset is Array and offset.size() == 2:
			var c := foot_cell + Vector2i(int(offset[0]), int(offset[1]))
			_draw_rect(overlay, transform, Rect2(Vector2(c * cell_size), Vector2.ONE * cell_size), colour)
	var origin := transform * at
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

func bake_zone() -> Dictionary:
	if _baking or EditorInterface.get_resource_filesystem().is_importing():
		return Rules.failure("editor.bake_busy", "Wait for the current bake or resource import to finish.")
	_baking = true
	var result := _bake_zone()
	_baking = false
	return result

func _bake_zone() -> Dictionary:
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
	var plan_path := "res://kit/zones/%s.json" % zone_id
	var output: Array = []
	var project := ProjectSettings.globalize_path("res://")
	var code := OS.execute(OS.get_executable_path(), ["--headless", "--path", project, "-s", "res://tools/kit_zone.gd", "--", "--export=" + scene_path, "--out=" + plan_path], output, true)
	if code != 0:
		return Rules.failure("editor.export_failed", "Plan export failed: %s" % "".join(output))
	output.clear()
	var python := Rules.python_binary()
	var repo := project.trim_suffix("/").get_base_dir()
	const BAKE := "import os,runpy,sys; os.chdir(sys.argv[1]); sys.path.insert(0,sys.argv[1]); sys.argv=['scripts.art.kit.bake',sys.argv[2]]; runpy.run_module('scripts.art.kit.bake',run_name='__main__')"
	code = OS.execute(python, ["-c", BAKE, repo, zone_id], output, true)
	if code != 0:
		return Rules.failure("editor.bake_failed", "Ground bake failed: %s" % "".join(output))
	var png := "res://zones/%s/ground_baked.png" % zone_id
	EditorInterface.get_resource_filesystem().reimport_files(PackedStringArray([png]))
	if not ResourceLoader.exists(png):
		return Rules.failure("editor.bake_missing", "The bake did not produce its ground image.")
	ground.baked = ResourceLoader.load(png, "Texture2D", ResourceLoader.CACHE_MODE_REPLACE) as Texture2D
	var walk := ground.get_node_or_null("KitWalk") as KitWalk
	if walk != null and walk.write_walk("res://zones/%s/walk.txt" % zone_id) != OK:
		return Rules.failure("editor.walk_export_failed", "The ground was baked, but its walk mask could not be written.")
	return {"ok": true, "diagnostics": [], "message": "Baked %s" % zone_id}

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
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--we-smoke-report="):
			var file := FileAccess.open(arg.substr(18), FileAccess.WRITE)
			if file != null:
				file.store_string(JSON.stringify(result, "  "))
				file.close()
	print("WORLD_EDITOR_SMOKE ", JSON.stringify(result))
	get_tree().quit(0 if bool(result.get("ok", false)) else 1)

func _run_editor_lifecycle() -> void:
	var result: Dictionary = await Smoke.run_lifecycle(self)
	print("WORLD_EDITOR_LIFECYCLE ", JSON.stringify(result))
	get_tree().quit(0 if bool(result.get("ok", false)) else 1)
