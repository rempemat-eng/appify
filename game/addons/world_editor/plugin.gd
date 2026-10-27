@tool
extends EditorPlugin
## The world editor's dock (docs/world-editor.md, "Zone authoring"; first prototype, Codex W3 grows
## it): paint a kit material on the selected zone's ground, place a library piece snapped to the
## soft grid, see a piece's size, rules, function and story, and be refused when a placement breaks
## its rules or the piece has not passed the library gate.

const Dock := preload("res://addons/world_editor/dock.gd")

var dock  ## the dock (dock.gd; untyped so its own methods resolve at run time)
var ground: TerrainGround
var zone: Node
var brush := ""        ## "material:<id>" or "piece:<id>"
var painting := false

func _enter_tree() -> void:
	dock = Dock.new()
	dock.plugin = self
	dock.name = "World"
	add_control_to_dock(DOCK_SLOT_RIGHT_UL, dock)
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--we-show="):
			# screenshots of the dock (docs/world-editor.md): the 2D view, the zone selected, the
			# dock's tab in front
			get_tree().create_timer(3.0).timeout.connect(_show_for_screenshot)

func _show_for_screenshot() -> void:
	EditorInterface.set_main_screen_editor("2D")
	var root := EditorInterface.get_edited_scene_root()
	if root != null:
		EditorInterface.get_selection().clear()
		EditorInterface.get_selection().add_node(root.get_node_or_null("Ground") if root.get_node_or_null("Ground") != null else root)
	var n: Node = dock
	while n.get_parent() != null and not (n.get_parent() is TabContainer):
		n = n.get_parent()
	var tc := n.get_parent() as TabContainer
	if tc != null:
		tc.current_tab = n.get_index()

func _exit_tree() -> void:
	if dock != null:
		remove_control_from_docks(dock)
		dock.queue_free()

func _handles(object: Object) -> bool:
	return _ground_of(object) != null

func _edit(object: Object) -> void:
	ground = _ground_of(object)
	zone = ground.get_parent() if ground != null else null
	if dock != null:
		dock.set_zone(zone, ground)

func _ground_of(object: Object) -> TerrainGround:
	if object is TerrainGround:
		return object
	if object is Node:
		var n: Node = object
		while n != null:
			var g := n.get_node_or_null("Ground") as TerrainGround
			if g != null:
				return g
			n = n.get_parent()
	return null

func _forward_canvas_gui_input(event: InputEvent) -> bool:
	if ground == null or brush == "":
		return false
	if event is InputEventMouse:
		var local: Vector2 = ground.get_global_transform_with_canvas().affine_inverse() * event.position
		var cell := Vector2i(floori(local.x / ground.kit.cell), floori(local.y / ground.kit.cell))
		if event is InputEventMouseMotion:
			dock.hover(cell, local)
			if painting and (brush.begins_with("material:") or brush.begins_with("variant:")):
				_paint(cell)
				return true
		if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
			painting = event.pressed
			if event.pressed:
				if brush.begins_with("material:") or brush.begins_with("variant:"):
					_paint(cell)
				else:
					_place(local)
				return true
	return false

func _paint(cell: Vector2i) -> void:
	if brush.begins_with("variant:"):
		var letter := brush.substr(8)
		var was := ground.variant_at(cell)
		var vr := get_undo_redo()
		vr.create_action("Paint variant %s" % letter, UndoRedo.MERGE_ENDS)
		vr.add_do_method(ground, "paint_variant", cell, letter)
		vr.add_undo_method(ground, "paint_variant", cell, was)
		vr.commit_action()
		return
	var id := brush.substr(9)
	var cells := ground.get_cells_layer()
	var before := cells.get_cell_atlas_coords(cell)
	var ur := get_undo_redo()
	ur.create_action("Paint %s" % id, UndoRedo.MERGE_ENDS)
	ur.add_do_method(ground, "paint_cell", cell, id)
	if before.x < 0:
		ur.add_undo_method(ground, "paint_cell", cell, "")
	else:
		ur.add_undo_method(ground, "paint_cell", cell, String(ground.kit.manifest.materials[before.x].id))
	ur.commit_action()

func _place(local: Vector2) -> void:
	var id := brush.substr(6)
	var e: Dictionary = KitPiece.index().get(id, {})
	var at := Dock.snap(local, String(e.get("snap", "cell")))
	var why: String = dock.refusal(id, at)
	if why != "":
		dock.say("Refused: " + why)
		return
	var props := zone.get_node_or_null("Props")
	var inst := (load("res://kit/props/%s.tscn" % id) as PackedScene).instantiate()
	inst.position = at
	var ur := get_undo_redo()
	ur.create_action("Place %s" % id)
	ur.add_do_method(props, "add_child", inst, true)
	ur.add_do_property(inst, "owner", zone)
	ur.add_do_reference(inst)
	ur.add_undo_method(props, "remove_child", inst)
	ur.commit_action()
	dock.say("Placed %s at %s" % [id, at])
	ground.rebuild_shadows.call_deferred()
