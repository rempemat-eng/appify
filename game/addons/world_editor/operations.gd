@tool
class_name WorldEditorOperations
extends RefCounted
## Non-UI authoring transactions. Placement rules belong to W5/W6; their absence refuses
## placement/validation rather than falling back to a second relation implementation.

signal changed

const Tools := preload("res://addons/world_editor/tools.gd")
const ZonePlan := preload("res://tools/kit_zone.gd")
const PIECES := "res://kit/pieces"
const INDEX := "res://kit/props/index.json"

var last_changed_ground: TerrainGround
var _zone: Node
var _ground: TerrainGround
var _history: Object
var _options: Dictionary = {}
var _library: Dictionary = {}
var _index: Dictionary = {}
var _library_errors: Array[Dictionary] = []

func configure(zone: Node, ground: TerrainGround, history: Object, options: Dictionary = {}) -> void:
	_zone = zone
	_ground = ground
	_history = history
	_options = options.duplicate(true)
	_library_errors.clear()
	_library.clear()
	_index.clear()
	if options.has("library"):
		if options.library is Dictionary:
			_library = options.library.duplicate(true)
		else:
			_library_errors.append(_diagnostic("library.invalid", "The piece library must be a dictionary."))
	else:
		_read_library(PIECES)
	if options.has("index"):
		if options.index is Dictionary:
			_index = options.index.duplicate(true)
		else:
			_library_errors.append(_diagnostic("library.invalid", "The built piece index must be a dictionary."))
	else:
		var value = JSON.parse_string(FileAccess.get_file_as_string(INDEX))
		if value is Dictionary:
			_index = value
		else:
			_library_errors.append(_diagnostic("library.invalid", "The built piece index could not be read."))

func definition(piece_id: String) -> Dictionary:
	var value = _library.get(piece_id)
	return value.duplicate(true) if value is Dictionary else {}

func catalog() -> Dictionary:
	var materials: Array[Dictionary] = []
	var pieces: Array[Dictionary] = []
	var ids := _library.keys()
	ids.sort()
	for key in ids:
		var id := String(key)
		var raw := definition(id)
		if raw.is_empty() or not _approval(raw).ok:
			continue
		var entry: Dictionary = _index.get(id, {}).duplicate(true)
		if raw.get("kind") == "terrain" and is_instance_valid(_ground) and _ground.kit != null:
			entry.merge(_ground.kit.by_id.get(id, {}), true)
		entry.merge({"id": id, "name": raw.get("name", id), "approval": _state(raw), "definition": raw}, true)
		if raw.get("kind") == "terrain":
			entry["material_id"] = raw.get("terrain", {}).get("material_id", entry.get("material_id", 0))
			materials.append(entry)
		elif raw.get("kind") in ["prop", "structure", "decal"]:
			pieces.append(entry)
	return {"ok": _library_errors.is_empty(), "diagnostics": _library_errors.duplicate(true), "materials": materials, "pieces": pieces}

## A single brush/rectangle/route gesture is one action. An invalid member refuses the whole
## batch; duplicates are harmless. Empty material with a variant is a variant-only brush.
func paint_cells(cells: Array, material_id: String, variant: String = "") -> Dictionary:
	var context := _context(true)
	if not context.ok:
		return context
	var chosen: Array[Vector2i] = []
	for value in cells:
		if not (value is Vector2i or value is Vector2):
			return _failure("rules.cell", "A painted cell must have integer grid coordinates.")
		if value is Vector2 and not value.is_finite():
			return _failure("rules.cell", "A painted cell must have finite grid coordinates.")
		var cell := Vector2i(value)
		if value is Vector2 and Vector2(cell) != value:
			return _failure("rules.cell", "A painted cell must have integer grid coordinates.")
		if not _in_bounds(cell):
			return _failure("rules.bounds", "Cell %s lies outside the zone." % cell)
		if cell not in chosen:
			chosen.append(cell)
	var variant_only := material_id == "" and variant != ""
	if material_id != "":
		var raw := definition(material_id)
		if raw.is_empty() or raw.get("kind") != "terrain" or not _ground.kit.by_id.has(material_id):
			return _failure("rules.unknown_piece", "'%s' is not a built terrain material." % material_id)
		var gate := _approval(raw)
		if not gate.ok:
			return gate
	if variant != "" and not _known_variant(variant):
		return _failure("rules.variant", "Unknown surface variant '%s'." % variant)
	# A variant-only brush still uses its cells' current materials, so it cannot bypass approval.
	if variant_only:
		for cell in chosen:
			var current_id := _material_piece(cell)
			if current_id == "":
				return _failure("rules.variant", "An empty cell has no surface for a variant.")
			var gate := _approval(definition(current_id))
			if not gate.ok:
				return gate
	if variant != "":
		for cell in chosen:
			var surface_id := _material_piece(cell) if variant_only else material_id
			if not _variant_for_material(variant, surface_id):
				return _failure("rules.variant", "Surface '%s' has no variant '%s'." % [surface_id, variant])
	elif material_id != "":
		for cell in chosen:
			var retained := _ground.variant_at(cell)
			if not _variant_for_material(retained, material_id):
				return _failure("rules.variant", "The retained variant '%s' is invalid on '%s'; choose a compatible variant or auto." % [retained, material_id])
	var before := _paint_snapshot(chosen)
	var after := before.duplicate(true)
	if not variant_only:
		for cell in chosen:
			after.tiles[cell] = {"source": -1, "atlas": Vector2i(-1, -1), "alternative": 0} if material_id == "" else {"source": 0, "atlas": _ground.kit.atlas_coords(material_id), "alternative": 0}
	if variant != "":
		var rows: PackedStringArray = before.variants.duplicate()
		while rows.size() < _ground.grid_size.y:
			rows.append(".".repeat(_ground.grid_size.x))
		for cell in chosen:
			var row := rows[cell.y]
			if row.length() < _ground.grid_size.x:
				row += ".".repeat(_ground.grid_size.x - row.length())
			rows[cell.y] = row.substr(0, cell.x) + variant + row.substr(cell.x + 1)
		after.variants = rows
	if before.tiles == after.tiles and before.variants == after.variants:
		return {"ok": true, "diagnostics": [], "changed": false}
	after.baked_live = false
	_begin("Paint surface variant" if variant_only else "Paint terrain %s" % material_id)
	_do(Callable(self, "_apply_paint").bind(_ground, after))
	_undo(Callable(self, "_apply_paint").bind(_ground, before))
	_history.commit_action()
	return {"ok": true, "diagnostics": [], "changed": true, "cells": chosen}

func preview_piece(piece_id: String, at: Vector2, options: Dictionary = {}) -> Dictionary:
	var context := _context(false)
	if not context.ok:
		return context
	var raw := definition(piece_id)
	if raw.is_empty() or raw.get("kind") not in ["prop", "structure", "decal"]:
		return _failure("rules.unknown_piece", "Unknown placeable piece '%s'." % piece_id)
	var gate := _approval(raw)
	if not gate.ok:
		return gate
	if not at.is_finite():
		return _failure("rules.bounds", "The placement position must be finite.")
	var placement: Dictionary = raw.get("placement", {})
	var snapped := Tools.snap(at, String(placement.get("snap", "cell")), _ground.kit.cell)
	if snapped.x < 0 or snapped.y < 0 or snapped.x >= _ground.size_px().x or snapped.y >= _ground.size_px().y:
		return _failure("rules.bounds", "The piece's foot lies outside the zone.")
	var facing := String(options.get("facing", "s")).to_lower()
	if facing not in ["s", "w", "n", "e"]:
		return _failure("rules.facing", "Facing must be s, w, n or e.")
	var orientations: Array = placement.get("orientations", [])
	if not orientations.is_empty() and "any" not in orientations and facing not in orientations:
		return _failure("rules.facing", "This piece has no authored '%s' orientation." % facing)
	var stage := String(options.get("stage", ""))
	var stages: Array = placement.get("stages", [])
	if stage != "" and not stages.is_empty() and stage not in stages:
		return _failure("rules.stage", "This piece is not authored for stage '%s'." % stage)
	var variant := String(options.get("variant", ""))
	if variant != "" and not _piece_variant(raw, variant):
		return _failure("rules.variant", "Piece '%s' has no variant '%s'." % [piece_id, variant])
	var snapshot := export_plan()
	if not snapshot.ok:
		return snapshot
	var instance := options.duplicate(true)
	instance["piece"] = piece_id
	var unit := float(_ground.kit.cell) if String(snapshot.plan.get("coordinate_space", "texels")) == "cells" else 1.0
	instance["at"] = [snapped.x / unit, snapped.y / unit]
	instance["facing"] = facing
	var id := String(options.get("id", _free_id(piece_id, snapshot.plan.get("pieces", []))))
	if id == "" or id.validate_node_name() != id:
		return _failure("rules.instance_id", "The instance id must be a nonempty valid node name.")
	for other in snapshot.plan.get("pieces", []):
		if String(other.get("id", "")) == id:
			return _failure("rules.instance_id", "Instance id '%s' already exists." % id)
	var props := _zone.get_node_or_null("Props")
	if props != null:
		for child in props.get_children(true):
			if String(child.name) == id:
				return _failure("rules.instance_id", "Instance id '%s' already belongs to an authored Props child." % id)
	instance["id"] = id
	var evaluator = _options.get("relation_evaluator", Callable())
	if not evaluator is Callable or not evaluator.is_valid():
		return _failure("rules.provider_missing", "Placement is unavailable until the shared relation engine is installed.")
	var result := _provider_result(evaluator.call(snapshot.plan.duplicate(true), instance.duplicate(true), _library.duplicate(true)), "relation engine")
	result["at"] = snapped
	result["instance"] = instance
	return result

func place_piece(piece_id: String, at: Vector2, options: Dictionary = {}) -> Dictionary:
	var context := _context(true)
	if not context.ok:
		return context
	var preview := preview_piece(piece_id, at, options)
	if not preview.ok:
		return preview
	var props := _zone.get_node_or_null("Props") as Node2D
	if props == null:
		return _failure("editor.props_missing", "The zone needs its authored Props container before placing pieces.")
	var inst: Node
	var factory = _options.get("scene_factory", Callable())
	if factory is Callable and factory.is_valid():
		var created = factory.call(piece_id)
		if created is Node:
			inst = created
	else:
		var scene_path := String(_index.get(piece_id, {}).get("scene", "res://kit/props/%s.tscn" % piece_id))
		if not ResourceLoader.exists(scene_path):
			return _failure("library.scene_missing", "The built scene for '%s' is missing." % piece_id)
		var scene := load(scene_path) as PackedScene
		if scene != null:
			inst = scene.instantiate()
	if not inst is KitPiece or inst.get_parent() != null:
		if is_instance_valid(inst) and inst.get_parent() == null:
			inst.free()
		return _failure("library.scene_invalid", "The piece factory must return a detached KitPiece scene.")
	var piece := inst as KitPiece
	piece.name = preview.instance.id
	piece.piece_id = piece_id
	piece.variant = String(preview.instance.get("variant", ""))
	piece.set_meta("kit_zone_entry", preview.instance.duplicate(true))
	piece.set_meta("facing", preview.instance.facing)
	if preview.instance.has("stage"):
		piece.set_meta("stage", preview.instance.stage)
	if String(definition(piece_id).get("geometry", {}).get("z_sort", "foot")) == "ground":
		piece.z_index = -5
	var before := {"baked": _ground.baked, "baked_live": _ground.showing_baked()}
	_begin("Place %s" % piece_id)
	_do(Callable(self, "_apply_placement").bind(_zone, _ground, props, piece, preview.at, true, before))
	_undo(Callable(self, "_apply_placement").bind(_zone, _ground, props, piece, preview.at, false, before))
	_history.add_do_reference(piece)
	_history.commit_action()
	preview["node"] = piece
	preview["changed"] = true
	return preview

func validate() -> Dictionary:
	var snapshot := export_plan()
	if not snapshot.ok:
		return snapshot
	var approval_diagnostics := _scene_approval_diagnostics()
	if not approval_diagnostics.is_empty():
		return {"ok": false, "diagnostics": approval_diagnostics, "message": approval_diagnostics[0].message}
	var validator = _options.get("zone_validator", Callable())
	if not validator is Callable or not validator.is_valid():
		return _failure("rules.provider_missing", "Zone validation is unavailable until the shared validator is installed.")
	return _provider_result(validator.call(snapshot.plan.duplicate(true), _library.duplicate(true)), "zone validator")

func _scene_approval_diagnostics() -> Array[Dictionary]:
	var used := {}
	for y in _ground.grid_size.y:
		for x in _ground.grid_size.x:
			var id := _material_piece(Vector2i(x, y))
			if id != "":
				used[id] = true
	for piece in _ground.pieces():
		used[piece.piece_id] = true
	var diagnostics: Array[Dictionary] = []
	for id in used:
		var raw := definition(String(id))
		if raw.is_empty():
			diagnostics.append(_diagnostic("rules.unknown_piece", "Unknown piece '%s' in the scene." % id))
		else:
			var gate := _approval(raw)
			if not gate.ok:
				for diagnostic in gate.diagnostics:
					diagnostics.append(diagnostic)
	return diagnostics

## Export current authoring data, preserving the original plan's unknown fields. Gameplay
## ownership stays with its scene; no ordinary node is removed, replaced or reparented here.
func export_plan() -> Dictionary:
	var context := _context(false)
	if not context.ok:
		return context
	if not _zone is Node2D:
		return _failure("plan.zone", "The zone root must be a Node2D.")
	var fallback: Dictionary = {}
	if _options.has("plan"):
		if not _options.plan is Dictionary:
			return _failure("plan.seed", "The supplied plan template must be a dictionary.")
		fallback = _options.plan.duplicate(true)
	elif not _zone.has_meta(ZonePlan.PLAN_META):
		# Before W2, scenes stored no seed metadata. Match its CLI fallback without
		# interpreting an arbitrary zone id as a path or dropping the old author's notes.
		var zone_id = _zone.get("zone_id")
		if zone_id is String and zone_id != "" and zone_id not in [".", ".."] and zone_id.validate_filename() == zone_id:
			var path := "res://kit/zones/%s.json" % zone_id
			if FileAccess.file_exists(path):
				var seed = JSON.parse_string(FileAccess.get_file_as_string(path))
				if not seed is Dictionary:
					return _failure("plan.seed", "The legacy zone plan could not be read: %s." % path)
				fallback = seed
	var plan: Dictionary = ZonePlan.plan_from_scene(_zone as Node2D, fallback)
	if plan.is_empty():
		return _failure("plan.export", "The shared zone exporter could not snapshot this scene.")
	return {"ok": true, "diagnostics": [], "plan": plan}

func _context(needs_history: bool) -> Dictionary:
	if not is_instance_valid(_zone) or not is_instance_valid(_ground) or not _zone.is_ancestor_of(_ground):
		return _failure("editor.no_zone", "Select a zone with TerrainGround before editing.")
	if _ground.kit == null or _ground.get_cells_layer() == null:
		return _failure("editor.not_ready", "The terrain kit and its Cells layer are not ready.")
	if not _library_errors.is_empty():
		return {"ok": false, "diagnostics": _library_errors.duplicate(true), "message": _library_errors[0].message}
	if needs_history and not is_instance_valid(_history):
		return _failure("editor.no_history", "The editor undo history is unavailable.")
	if needs_history:
		for method in ["create_action", "commit_action", "add_do_method", "add_undo_method", "add_do_reference"]:
			if not _history.has_method(method):
				return _failure("editor.no_history", "The editor undo history is incompatible.")
	return {"ok": true, "diagnostics": []}

func _state(raw: Dictionary) -> String:
	var approval = raw.get("approval", {})
	return String(approval.get("state", "")) if approval is Dictionary else ""

func _approval(raw: Dictionary) -> Dictionary:
	var state := _state(raw)
	if state == "approved" or (is_instance_valid(_ground) and _ground.lab and state in ["candidate", "gated"]):
		return {"ok": true, "diagnostics": []}
	return _failure("rules.unapproved", "'%s' is %s; only approved pieces may be used outside a lab, and pre-art/rejected/retired pieces cannot be placed in any zone." % [raw.get("id", "unknown"), state if state != "" else "missing approval"])

func _known_variant(letter: String) -> bool:
	if letter == ".":
		return true
	if letter.length() != 1:
		return false
	for variants in _ground.kit.manifest.get("surface_variants", {}).values():
		if variants.has(letter):
			return true
	return false

func _variant_for_material(letter: String, id: String) -> bool:
	if letter == ".":
		return true
	var terrain: Dictionary = definition(id).get("terrain", {})
	var painter: Dictionary = terrain.get("paint", terrain.get("fill", {}))
	var family := String(painter.get("fn", ""))
	return _ground.kit.manifest.get("surface_variants", {}).get(family, {}).has(letter)

func _piece_variant(raw: Dictionary, id: String) -> bool:
	for value in raw.get("variants", []):
		if value is Dictionary and String(value.get("id", "")) == id:
			return true
	return false

func _in_bounds(cell: Vector2i) -> bool:
	return cell.x >= 0 and cell.y >= 0 and cell.x < _ground.grid_size.x and cell.y < _ground.grid_size.y

func _material_piece(cell: Vector2i) -> String:
	var ac := _ground.get_cells_layer().get_cell_atlas_coords(cell)
	var materials: Array = _ground.kit.manifest.materials
	return String(materials[ac.x].id) if ac.x >= 0 and ac.x < materials.size() else ""

func _paint_snapshot(cells: Array[Vector2i]) -> Dictionary:
	var tiles: Dictionary = {}
	var layer := _ground.get_cells_layer()
	for cell in cells:
		tiles[cell] = {"source": layer.get_cell_source_id(cell), "atlas": layer.get_cell_atlas_coords(cell), "alternative": layer.get_cell_alternative_tile(cell)}
	return {"tiles": tiles, "variants": _ground.variant_rows.duplicate(), "baked": _ground.baked, "baked_live": _ground.showing_baked()}

func _apply_paint(target: TerrainGround, state: Dictionary) -> void:
	if not is_instance_valid(target):
		return
	var layer := target.get_cells_layer()
	for cell in state.tiles:
		var tile: Dictionary = state.tiles[cell]
		if tile.source < 0:
			layer.erase_cell(cell)
		else:
			layer.set_cell(cell, tile.source, tile.atlas, tile.alternative)
	target.variant_rows = state.variants.duplicate()
	_restore_ground(target, state)

func _apply_placement(zone: Node, target: TerrainGround, props: Node2D, piece: KitPiece, at: Vector2, attach: bool, before: Dictionary) -> void:
	if not is_instance_valid(zone) or not is_instance_valid(target):
		return
	if attach:
		props.add_child(piece)
		piece.position = props.to_local(target.to_global(at)) if props.is_inside_tree() else at
		piece.owner = zone
		_restore_ground(target, {"baked": before.baked, "baked_live": false})
	else:
		if piece.get_parent() == props:
			props.remove_child(piece)
		_restore_ground(target, before)

func _restore_ground(target: TerrainGround, state: Dictionary) -> void:
	# Re-derive before restoring baked validity, so TileMapLayer's later changed notification
	# sees matching cells and cannot invalidate an otherwise exact undo snapshot.
	target.baked = state.baked
	target._rebuild()
	target._baked_live = bool(state.baked_live)
	target._rebuild()
	target.rebuild_shadows()
	last_changed_ground = target
	changed.emit()

func _begin(title: String) -> void:
	if _history is UndoRedo:
		_history.create_action(title)
	else:
		_history.create_action(title, UndoRedo.MERGE_DISABLE, _zone)

func _do(action: Callable) -> void:
	if _history is UndoRedo:
		_history.add_do_method(action)
	else:
		_history.callv("add_do_method", [action.get_object(), action.get_method()] + action.get_bound_arguments())

func _undo(action: Callable) -> void:
	if _history is UndoRedo:
		_history.add_undo_method(action)
	else:
		_history.callv("add_undo_method", [action.get_object(), action.get_method()] + action.get_bound_arguments())

func _provider_result(value: Variant, name: String) -> Dictionary:
	if not value is Dictionary or not value.get("ok") is bool or not value.get("diagnostics", []) is Array:
		return _failure("rules.provider_invalid", "The %s returned an invalid result." % name)
	for diagnostic in value.get("diagnostics", []):
		if not diagnostic is Dictionary or not diagnostic.get("message") is String:
			return _failure("rules.provider_invalid", "The %s returned invalid diagnostics." % name)
	var result: Dictionary = value.duplicate(true)
	if not result.has("diagnostics"):
		result["diagnostics"] = []
	if not result.ok and result.diagnostics.is_empty():
		result.diagnostics.append(_diagnostic("rules.refused", "The %s refused this operation." % name))
	if not result.has("message") and not result.diagnostics.is_empty():
		result["message"] = String(result.diagnostics[0].get("message", "Operation refused."))
	return result

func _read_library(path: String) -> void:
	var dir := DirAccess.open(path)
	if dir == null:
		_library_errors.append(_diagnostic("library.missing", "Cannot open piece definitions at %s." % path))
		return
	for folder in dir.get_directories():
		_read_library(path.path_join(folder))
	for file in dir.get_files():
		if not file.ends_with(".json"):
			continue
		var value = JSON.parse_string(FileAccess.get_file_as_string(path.path_join(file)))
		if not value is Dictionary or String(value.get("id", "")) == "" or _library.has(value.get("id")):
			_library_errors.append(_diagnostic("library.invalid", "Malformed or duplicate piece definition: %s." % path.path_join(file)))
			continue
		_library[value.id] = value

func _free_id(id: String, pieces: Array) -> String:
	var used := {}
	for piece in pieces:
		used[String(piece.get("id", ""))] = true
	var props := _zone.get_node_or_null("Props")
	if props != null:
		for child in props.get_children(true):
			used[String(child.name)] = true
	var candidate := id
	var suffix := 2
	while used.has(candidate):
		candidate = "%s_%s" % [id, suffix]
		suffix += 1
	return candidate

func _diagnostic(rule: String, message: String) -> Dictionary:
	return {"rule": rule, "code": rule, "message": message}

func _failure(rule: String, message: String) -> Dictionary:
	return {"ok": false, "diagnostics": [_diagnostic(rule, message)], "message": message}
