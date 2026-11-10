@tool
class_name WorldEditorOperations
extends RefCounted
## Non-UI authoring transactions. Placement rules belong to W5/W6; their absence refuses
## placement/validation rather than falling back to a second relation implementation.

signal changed

const Tools := preload("res://addons/world_editor/tools.gd")
const ZonePlan := preload("res://tools/kit_zone.gd")
const Walk := preload("res://world/terrain/walk.gd")
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
	_ghost_plans.clear()
	_ghost_verdicts.clear()
	_ghost_snapshot = {}
	_piece_signature = _pieces_now()
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
	var snapped := false
	if material_id != "":
		var raw := definition(material_id)
		if raw.is_empty() or raw.get("kind") != "terrain" or not _ground.kit.by_id.has(material_id):
			return _failure("rules.unknown_piece", "'%s' is not a built terrain material." % material_id)
		var gate := _approval(raw)
		if not gate.ok:
			return gate
		if bool(raw.get("terrain", {}).get("route", false)):
			var centred := _door_snap(chosen)
			snapped = centred != chosen
			chosen = centred
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
	return {"ok": true, "diagnostics": [], "changed": true, "cells": chosen, "snapped": snapped}

## Door paths: a route stroke that reaches the row before a placed door is centred on the door
## (Tools.door_path_cells), so the path leaves it centred and straight for a cell. Cells the snap
## would put outside the zone are dropped.
func _door_snap(cells: Array[Vector2i]) -> Array[Vector2i]:
	var out: Array[Vector2i] = cells.duplicate()
	for door in _doors():
		out = Tools.door_path_cells(out, door, _ground.kit.cell)
	var inside: Array[Vector2i] = []
	for c in out:
		if _in_bounds(c) and c not in inside:
			inside.append(c)
	return inside

## Every placed door facing south: its opening's x0 and x1 and its foot y, in ground texels
## (the pieces' geometry.doors).
func _doors() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	var props := _zone.get_node_or_null("Props") as Node2D
	if props == null:
		return out
	for child in props.get_children():
		if not child is KitPiece:
			continue
		var doors: Variant = definition(child.piece_id).get("geometry", {}).get("doors", [])
		if not doors is Array:
			continue
		var foot: Vector2 = _ground.to_local(props.to_global(child.position)) if props.is_inside_tree() else child.position
		for d in doors:
			if d is Dictionary and String(d.get("faces", "s")) == "s" and d.get("x") is Array and d.x.size() == 2:
				out.append({"x0": foot.x + float(d.x[0]), "x1": foot.x + float(d.x[1]), "y": foot.y})
	return out

## The centre (texels along the run) of the path crossing a fence run near a cell, or NAN: along x,
## route cells on both sides of the cell's south line; along y, route cells in the run's column and
## both columns beside it. The crossing nearest the cell, four cells either way.
func _crossing_path(at: Vector2i, along_x: bool, size: int) -> float:
	var runs: Array = []
	for i in range(-4, 5):
		var crosses := false
		if along_x:
			var c := at + Vector2i(i, 0)
			crosses = _is_route(c) and _is_route(c + Vector2i(0, 1))
		else:
			var c := at + Vector2i(0, i)
			crosses = _is_route(c) and _is_route(c + Vector2i(-1, 0)) and _is_route(c + Vector2i(1, 0))
		if crosses:
			if not runs.is_empty() and runs.back()[1] == i - 1:
				runs.back()[1] = i
			else:
				runs.append([i, i])
	if runs.is_empty():
		return NAN
	var best: Array = runs[0]
	for r in runs:
		if mini(absi(r[0]), absi(r[1])) < mini(absi(best[0]), absi(best[1])) or (r[0] <= 0 and r[1] >= 0):
			best = r
	var base := at.x if along_x else at.y
	return (base * 2 + best[0] + best[1] + 1) * size / 2.0

## Whether a ground cell's material is a route (a path, a road).
func _is_route(cell: Vector2i) -> bool:
	if not _in_bounds(cell):
		return false
	return bool(definition(_material_piece(cell)).get("terrain", {}).get("route", false))

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
	var twin := _twin(piece_id, snapped)
	if twin != "":
		return _failure("rules.duplicate", "'%s' (%s) already stands exactly here; a second one would hide under it." % [twin, piece_id])
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
	var made := _instantiate(piece_id)
	if not made.ok:
		return made
	var piece: KitPiece = made.node
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

## A fence run (round 3, 3 Nov): the cells a stroke crossed become fence cells of `style`, each
## piece chosen by its neighbours (fence_<style>_<joins>, scripts/art/kit/fences.py), and the
## existing cells of that style the run meets are re-joined to it; gates keep their place and the
## run's ends join them. One undo action; a refused cell refuses the whole run.
func place_fence_run(style: String, cells: Array, options: Dictionary = {}) -> Dictionary:
	var context := _context(true)
	if not context.ok:
		return context
	if not _history.has_method("add_undo_reference"):
		return _failure("editor.no_history", "The editor undo history is incompatible.")
	var props := _zone.get_node_or_null("Props") as Node2D
	if props == null:
		return _failure("editor.props_missing", "The zone needs its authored Props container before placing pieces.")
	var size := _ground.kit.cell
	var existing := {}
	var fixed := {}
	for child in props.get_children():
		if not child is KitPiece:
			continue
		var boundary: Variant = definition(child.piece_id).get("placement", {}).get("boundary")
		if not boundary is Dictionary or String(boundary.get("style", "")) != style:
			continue
		var foot: Vector2 = _ground.to_local(props.to_global(child.position)) if props.is_inside_tree() else child.position
		var at := Tools.fence_cell(foot, size)
		if bool(boundary.get("gate", false)):
			fixed.merge(Tools.gate_ends(at, boundary.get("joins", [])), true)
		elif bool(boundary.get("stile", false)):
			fixed[at] = boundary.get("joins", [])
		else:
			existing[at] = child
	var run: Array[Vector2i] = []
	for value in cells:
		var at := Vector2i(value)
		if not _in_bounds(at):
			return _failure("rules.bounds", "The fence run leaves the zone at %s." % at)
		if at not in run and not fixed.has(at):
			run.append(at)
	if run.size() + existing.size() < 2:
		return _failure("rules.fences", "A fence run needs two cells or more: drag along it.")
	var all_cells: Array = existing.keys()
	for at in run:
		if not existing.has(at):
			all_cells.append(at)
	var chosen := Tools.fence_pieces(style, all_cells + fixed.keys(), fixed)
	var removed: Array[KitPiece] = []
	var added: Array[KitPiece] = []
	var snapshot := export_plan()
	if not snapshot.ok:
		return snapshot
	var taken: Array = snapshot.plan.get("pieces", []).duplicate()
	var chosen_options := {}
	for key in ["facing", "stage", "variant"]:
		if String(options.get(key, "")) != "":
			chosen_options[key] = options[key]
	for at in all_cells:
		var id := String(chosen.get(at, ""))
		if id == "":
			_discard(added)
			return _failure("rules.fences", "The fence cell at %s joins nothing: a run must be continuous." % at)
		var raw := definition(id)
		if raw.is_empty():
			_discard(added)
			return _failure("rules.unknown_piece", "Unknown fence piece '%s'." % id)
		var gate := _approval(raw)
		if not gate.ok:
			_discard(added)
			return gate
		var old: KitPiece = existing.get(at)
		if old != null and old.piece_id == id:
			continue
		var foot := Tools.fence_foot(at, size)
		var entry := {}
		if old == null:
			var opts := chosen_options.duplicate()
			opts["id"] = _free_id(id, taken)
			if opts.has("variant") and not _piece_variant(raw, String(opts.variant)):
				opts.erase("variant")                            # a corner has no 'post': it takes its own
			var preview := preview_piece(id, foot, opts)
			if not preview.ok:
				_discard(added)
				return preview
			entry = preview.instance
			taken.append(entry)
		else:
			var kept: Variant = old.get_meta("kit_zone_entry", {})
			entry = kept.duplicate(true) if kept is Dictionary else {}
			entry["piece"] = id
			entry["id"] = String(old.name)
		var made := _instantiate(id)
		if not made.ok:
			_discard(added)
			return made
		var piece: KitPiece = made.node
		piece.name = String(entry.id)
		piece.piece_id = id
		_dress(piece, entry, old, chosen_options, "plain")
		piece.position = props.to_local(_ground.to_global(foot)) if props.is_inside_tree() else foot
		added.append(piece)
		if old != null:
			removed.append(old)
	if added.is_empty():
		return {"ok": true, "diagnostics": [], "changed": false, "message": "The fence already joins."}
	var before := {"baked": _ground.baked, "baked_live": _ground.showing_baked()}
	_begin("Fence run (%s, %d cells)" % [style, run.size()])
	_do(Callable(self, "_apply_swap").bind(_zone, _ground, props, removed, added, true, before))
	_undo(Callable(self, "_apply_swap").bind(_zone, _ground, props, removed, added, false, before))
	for node in added:
		_history.add_do_reference(node)
	for node in removed:
		_history.add_undo_reference(node)
	_history.commit_action()
	return {"ok": true, "diagnostics": [], "changed": true, "added": added.size() - removed.size(), "rejoined": removed.size(),
		"message": "Fence run: %d new cells, %d re-joined." % [added.size() - removed.size(), removed.size()]}

## What a fence run would place, without placing it (the canvas preview): {cell: piece id} for
## the run's cells and the existing cells it would re-join.
func preview_fence_run(style: String, cells: Array) -> Dictionary:
	var context := _context(false)
	if not context.ok:
		return {}
	var props := _zone.get_node_or_null("Props") as Node2D
	if props == null:
		return {}
	var existing := {}
	var fixed := {}
	for child in props.get_children():
		if not child is KitPiece:
			continue
		var boundary: Variant = definition(child.piece_id).get("placement", {}).get("boundary")
		if not boundary is Dictionary or String(boundary.get("style", "")) != style:
			continue
		var foot: Vector2 = _ground.to_local(props.to_global(child.position)) if props.is_inside_tree() else child.position
		var at := Tools.fence_cell(foot, _ground.kit.cell)
		if bool(boundary.get("gate", false)):
			fixed.merge(Tools.gate_ends(at, boundary.get("joins", [])), true)
		elif bool(boundary.get("stile", false)):
			fixed[at] = boundary.get("joins", [])
		else:
			existing[at] = child.piece_id
	var all_cells: Array = existing.keys()
	for value in cells:
		var at := Vector2i(value)
		if not existing.has(at) and not fixed.has(at) and at not in all_cells:
			all_cells.append(at)
	var chosen := Tools.fence_pieces(style, all_cells + fixed.keys(), fixed)
	var out := {}
	for at in chosen:
		if String(existing.get(at, "")) != String(chosen[at]):
			out[at] = chosen[at]
	return out

## Group copy (round 4): the given pieces as a clipboard, each entry's foot relative to a cell
## corner, so a pasted pen keeps its fences on their lines and what it holds inside them.
func copy_group(nodes: Array) -> Dictionary:
	var context := _context(false)
	if not context.ok:
		return context
	var props := _zone.get_node_or_null("Props") as Node2D
	var feet: Array = []
	for node in nodes:
		if node is KitPiece and node.get_parent() == props:
			var foot: Vector2 = _ground.to_local(props.to_global(node.position)) if props.is_inside_tree() else node.position
			feet.append([node, foot])
	if feet.is_empty():
		return _failure("editor.selection", "Select placed pieces to copy.")
	var size := float(_ground.kit.cell)
	var corner := Vector2(INF, INF)
	for pair in feet:
		corner = corner.min(pair[1])
	corner = (corner / size).floor() * size
	var group: Array = []
	for pair in feet:
		var node: KitPiece = pair[0]
		var kept: Variant = node.get_meta("kit_zone_entry", {})
		var entry := {"piece": node.piece_id, "offset": pair[1] - corner, "facing": String(node.get_meta("facing", "s")),
			"entry": kept.duplicate(true) if kept is Dictionary else {}, "meta": {}}
		for key in node.get_meta_list():
			if key != "kit_zone_entry":
				entry.meta[key] = node.get_meta(key)
		if node.variant != "":
			entry["variant"] = node.variant
		if node.has_meta("stage"):
			entry["stage"] = node.get_meta("stage")
		group.append(entry)
	return {"ok": true, "diagnostics": [], "group": group, "message": "Copied %d pieces." % group.size()}

## Paste a copied group with its cell corner at the cell under `at`: every piece is checked by the
## shared relation engine against the zone with the rest of the group in it (a hen needs the
## coop pasted with her), and all are placed in one undo action, or none.
func paste_group(group: Array, at: Vector2) -> Dictionary:
	var context := _context(true)
	if not context.ok:
		return context
	if group.is_empty():
		return _failure("editor.selection", "Copy a group of pieces first.")
	var props := _zone.get_node_or_null("Props") as Node2D
	if props == null:
		return _failure("editor.props_missing", "The zone needs its authored Props container before placing pieces.")
	var evaluator = _options.get("relation_evaluator", Callable())
	if not evaluator is Callable or not evaluator.is_valid():
		return _failure("rules.provider_missing", "Placement is unavailable until the shared relation engine is installed.")
	var size := float(_ground.kit.cell)
	var corner := (at / size).floor() * size
	var snapshot := export_plan()
	if not snapshot.ok:
		return snapshot
	var unit := size if String(snapshot.plan.get("coordinate_space", "texels")) == "cells" else 1.0
	var taken: Array = snapshot.plan.get("pieces", []).duplicate()
	var instances: Array = []
	for g in group:
		var id := String(g.get("piece", ""))
		var raw := definition(id)
		if raw.is_empty():
			return _failure("rules.unknown_piece", "Unknown piece '%s' in the group." % id)
		var gate := _approval(raw)
		if not gate.ok:
			return gate
		var foot: Vector2 = corner + Vector2(g.get("offset", Vector2.ZERO))
		if foot.x < 0 or foot.y < 0 or foot.x >= _ground.size_px().x or foot.y >= _ground.size_px().y:
			return _failure("rules.bounds", "The group does not fit in the zone here.")
		var twin := _twin(id, foot)
		if twin != "":
			return _failure("rules.duplicate", "'%s' (%s) already stands exactly where the group would put one; paste it elsewhere." % [twin, id])
		var instance: Dictionary = Dictionary(g.get("entry", {})).duplicate(true)
		instance.merge({"piece": id, "at": [foot.x / unit, foot.y / unit], "facing": String(g.get("facing", "s")),
			"id": _free_id(id, taken)}, true)
		for key in ["variant", "stage"]:
			if g.has(key):
				instance[key] = g[key]
		taken.append(instance)
		instances.append(instance)
	var whole: Dictionary = snapshot.plan.duplicate(true)
	for k in instances.size():
		var others: Array = snapshot.plan.get("pieces", []).duplicate(true)
		for j in instances.size():
			if j != k:
				others.append(instances[j].duplicate(true))
		whole["pieces"] = others
		var verdict := _provider_result(evaluator.call(whole.duplicate(true), instances[k].duplicate(true), _library.duplicate(true)), "relation engine")
		if not verdict.ok:
			return verdict
	var added: Array[KitPiece] = []
	for instance in instances:
		var made := _instantiate(String(instance.piece))
		if not made.ok:
			_discard(added)
			return made
		var piece: KitPiece = made.node
		piece.name = String(instance.id)
		piece.piece_id = String(instance.piece)
		piece.variant = String(instance.get("variant", ""))
		for key in Dictionary(group[instances.find(instance)].get("meta", {})):
			piece.set_meta(key, group[instances.find(instance)].meta[key])
		piece.set_meta("kit_zone_entry", instance.duplicate(true))
		piece.set_meta("facing", instance.facing)
		if instance.has("stage"):
			piece.set_meta("stage", instance.stage)
		var foot := Vector2(instance.at[0], instance.at[1]) * unit
		piece.position = props.to_local(_ground.to_global(foot)) if props.is_inside_tree() else foot
		added.append(piece)
	var before := {"baked": _ground.baked, "baked_live": _ground.showing_baked()}
	_begin("Paste group (%d pieces)" % added.size())
	_do(Callable(self, "_apply_swap").bind(_zone, _ground, props, [], added, true, before))
	_undo(Callable(self, "_apply_swap").bind(_zone, _ground, props, [], added, false, before))
	for node in added:
		_history.add_do_reference(node)
	_history.commit_action()
	return {"ok": true, "diagnostics": [], "changed": true, "nodes": added, "message": "Pasted %d pieces." % added.size()}

const CROSSING_STYLES := ["drystone", "rail"]
const GHOST_RADIUS := 8
var _ghost_plans: Dictionary = {}
var _ghost_verdicts: Dictionary = {}
var _ghost_snapshot: Dictionary = {}
var ghost_validations := 0

func _fence_nodes(style: String) -> Dictionary:
	var props := _zone.get_node_or_null("Props") as Node2D
	var out := {}
	if props == null:
		return out
	for child in props.get_children():
		if not child is KitPiece:
			continue
		var boundary: Variant = definition(child.piece_id).get("placement", {}).get("boundary")
		if not boundary is Dictionary or String(boundary.get("style", "")) != style or bool(boundary.get("gate", false)) or bool(boundary.get("stile", false)):
			continue
		var foot: Vector2 = _ground.to_local(props.to_global(child.position)) if props.is_inside_tree() else child.position
		out[Tools.fence_cell(foot, _ground.kit.cell)] = child
	return out

## Gates and stiles on runs (round 7): clicking a run with a gate or a stile replaces the straight
## cells it spans (a gate three, a stile one), snapping to the nearest straight span within two
## cells of the click. A stile goes only on a drystone or post-and-rail run, and (its relation)
## only where a path crosses. The cells either side keep their joins: they now meet the gate's or
## the stile's ends. One undo action.
func place_crossing(piece_id: String, at: Vector2, options: Dictionary = {}) -> Dictionary:
	var context := _context(true)
	if not context.ok:
		return context
	var raw := definition(piece_id)
	var boundary: Variant = raw.get("placement", {}).get("boundary")
	if not boundary is Dictionary or not (bool(boundary.get("gate", false)) or bool(boundary.get("stile", false))):
		return _failure("rules.crossing", "'%s' is not a gate or a stile." % piece_id)
	var gate_ok := _approval(raw)
	if not gate_ok.ok:
		return gate_ok
	var style := String(boundary.get("style", ""))
	var stile := bool(boundary.get("stile", false))
	if stile and style not in CROSSING_STYLES:
		return _failure("rules.crossing", "A stile crosses only a drystone or post-and-rail run, not %s." % style)
	var joins: Array = boundary.get("joins", [])
	var along_x := "e" in joins
	var span := int(boundary.get("span_cells", 1)) if not stile else 1
	var size := _ground.kit.cell
	var click := Vector2i(floori(at.x / size), floori(at.y / size))
	var cells := _fence_nodes(style)
	var step := Vector2i(1, 0) if along_x else Vector2i(0, 1)
	var straight := "_ew" if along_x else "_ns"
	var centre := Vector2i(-9999, -9999)
	var spans: Array[Vector2i] = []
	for d in [0, -1, 1, -2, 2]:
		var c: Vector2i = click + step * d
		var ok := true
		for k in range(-(span / 2), span / 2 + 1):
			var node = cells.get(c + step * k)
			if node == null or not String(node.piece_id).ends_with(straight):
				ok = false
				break
		if ok:
			spans.append(c)
	# of the spans it could take, the gate takes the one centred on the path that crosses the run
	var along: Array = []
	for c in spans:
		var foot := Tools.fence_foot(c, size)
		along.append(foot.x if along_x else foot.y)
	var pick := Tools.centred_span(along, _crossing_path(click, along_x, size))
	if pick >= 0:
		centre = spans[pick]
	if centre.x == -9999:
		return _failure("rules.crossing", "No straight %s run of %d cell%s here: a %s needs %s cell%s of a straight run along %s within two cells of the click." % [
			style, span, "s" if span > 1 else "", "stile" if stile else "gate", span, "s" if span > 1 else "", "x" if along_x else "y"])
	var removed: Array = []
	var names := {}
	for k in range(-(span / 2), span / 2 + 1):
		removed.append(cells[centre + step * k])
		names[String(cells[centre + step * k].name)] = true
	var snapshot := export_plan()
	if not snapshot.ok:
		return snapshot
	var others: Array = []
	for e in snapshot.plan.get("pieces", []):
		if not names.has(String(e.get("id", ""))):
			others.append(e)
	var plan: Dictionary = snapshot.plan.duplicate(true)
	plan["pieces"] = others
	var foot := Tools.fence_foot(centre, size)
	var unit := float(size) if String(plan.get("coordinate_space", "texels")) == "cells" else 1.0
	var instance := {"piece": piece_id, "at": [foot.x / unit, foot.y / unit], "facing": "s", "id": _free_id(piece_id, others)}
	var evaluator = _options.get("relation_evaluator", Callable())
	if not evaluator is Callable or not evaluator.is_valid():
		return _failure("rules.provider_missing", "Placement is unavailable until the shared relation engine is installed.")
	var verdict := _provider_result(evaluator.call(plan, instance.duplicate(true), _library.duplicate(true)), "relation engine")
	if not verdict.ok:
		return verdict
	var made := _instantiate(piece_id)
	if not made.ok:
		return made
	var props := _zone.get_node_or_null("Props") as Node2D
	var piece: KitPiece = made.node
	piece.name = String(instance.id)
	piece.piece_id = piece_id
	# the gate keeps what was authored on the cell at its middle (its stage, its notes)
	var centre_node: Node = cells[centre]
	var kept: Variant = centre_node.get_meta("kit_zone_entry", {})
	var entry: Dictionary = kept.duplicate(true) if kept is Dictionary else {}
	entry.merge(instance, true)
	_dress(piece, entry, centre_node, options)
	piece.position = props.to_local(_ground.to_global(foot)) if props.is_inside_tree() else foot
	var before := {"baked": _ground.baked, "baked_live": _ground.showing_baked()}
	_begin("Place %s on the run" % piece_id)
	_do(Callable(self, "_apply_swap").bind(_zone, _ground, props, removed, [piece], true, before))
	_undo(Callable(self, "_apply_swap").bind(_zone, _ground, props, removed, [piece], false, before))
	_history.add_do_reference(piece)
	for node in removed:
		_history.add_undo_reference(node)
	_history.commit_action()
	return {"ok": true, "diagnostics": [], "changed": true, "node": piece, "cell": centre, "replaced": removed.size(),
		"message": "%s placed on the run at %s, replacing %d cell%s." % [piece_id, centre, removed.size(), "s" if removed.size() > 1 else ""]}

## The live fault overlay (round 7), in two halves so the slow one can run off the main thread:
## ghost_plan (main thread) crops the zone's plan to the ghost's neighbourhood (GHOST_RADIUS cells
## round it) with the ghost in it, cached per revision; ghost_verdict runs the full validator (the
## same one Validate uses: kit_rules, relations, enclosures, check_plan) on that crop and keeps the
## findings about the ghost, cached per crop.
func ghost_plan(piece_id: String, at: Vector2, options: Dictionary = {}) -> Dictionary:
	var context := _context(false)
	if not context.ok:
		return {}
	var raw := definition(piece_id)
	if raw.is_empty():
		return {}
	var size := _ground.kit.cell
	var snapped := Tools.snap(at, String(raw.get("placement", {}).get("snap", "cell")), size)
	var key := [piece_id, snapped, String(options.get("facing", "s")), String(options.get("variant", "")), String(options.get("stage", ""))]
	var skey := str(key)
	if _ghost_plans.has(skey):
		return _ghost_plans[skey]
	if _ghost_snapshot.is_empty():
		var snap := export_plan()
		if not snap.ok:
			return {}
		_ghost_snapshot = snap.plan
	var plan: Dictionary = _ghost_snapshot
	var unit := float(size) if String(plan.get("coordinate_space", "texels")) == "cells" else 1.0
	var cell := Vector2i(floori(snapped.x / size), floori((snapped.y - 1) / size))
	var rows: Array = plan.get("rows", [])
	var y0 := maxi(0, cell.y - GHOST_RADIUS)
	var y1 := mini(rows.size(), cell.y + GHOST_RADIUS + 1)
	var x0 := maxi(0, cell.x - GHOST_RADIUS)
	var x1 := mini(String(rows[0]).length() if rows.size() > 0 else 0, cell.x + GHOST_RADIUS + 1)
	var crop_rows: Array = []
	for y in range(y0, y1):
		crop_rows.append(String(rows[y]).substr(x0, x1 - x0))
	var shift := Vector2(x0 * size, y0 * size)
	var pieces: Array = []
	for e in plan.get("pieces", []):
		var p := Vector2(e.at[0], e.at[1]) * unit - shift
		if p.x >= 0 and p.y >= 0 and p.x < (x1 - x0) * size and p.y <= (y1 - y0) * size:
			var c: Dictionary = e.duplicate(true)
			c["at"] = [p.x, p.y]
			pieces.append(c)
	var ghost := {"piece": piece_id, "at": [snapped.x - shift.x, snapped.y - shift.y], "facing": String(options.get("facing", "s")), "id": "ghost_" + piece_id}
	for k in ["variant", "stage"]:
		if String(options.get(k, "")) != "":
			ghost[k] = options[k]
	pieces.append(ghost)
	var crop := {"zone": String(plan.get("zone", "zone")) + "_ghost", "legend": plan.get("legend", {}), "rows": crop_rows, "pieces": pieces,
		"coordinate_space": "texels", "lab": plan.get("lab", false)}
	var out := {"key": skey, "plan": crop, "ghost": ghost.id, "at": Vector2(ghost.at[0], ghost.at[1])}
	_ghost_plans[skey] = out
	return out

func ghost_verdict(info: Dictionary) -> Dictionary:
	if info.is_empty():
		return {}
	if _ghost_verdicts.has(info.key):
		return _ghost_verdicts[info.key]
	var out := ghost_compute(info)
	_ghost_verdicts[info.key] = out
	return out

## The cached verdict for a crop, or {} while it is still being worked out.
func ghost_cached(info: Dictionary) -> Dictionary:
	return _ghost_verdicts.get(info.get("key", ""), {}) if not info.is_empty() else {}

func ghost_store(key: String, verdict: Dictionary) -> void:
	_ghost_verdicts[key] = verdict

## The slow half, safe off the main thread: it reads only the crop and the library.
func ghost_compute(info: Dictionary) -> Dictionary:
	var validator = _options.get("zone_validator", Callable())
	if not validator is Callable or not validator.is_valid():
		return {}
	ghost_validations += 1
	var result: Variant = validator.call(info.plan.duplicate(true), _library)
	var worst := ""
	var rule := ""
	var message := ""
	for f in (result.get("diagnostics", []) if result is Dictionary else []):
		if not f is Dictionary:
			continue
		var at_: Variant = f.get("at")
		var near := String(f.get("message", "")).begins_with(String(info.ghost) + ":")
		if at_ is Array and at_.size() == 2:
			near = near or Vector2(float(at_[0]), float(at_[1])).distance_to(info.at) <= 3.0 * _ground.kit.cell
		if not near:
			continue
		var sev := String(f.get("severity", "fault"))
		if worst != "fault" and (sev == "fault" or worst == ""):
			worst = sev
			rule = Tools.short_rule(String(f.get("check", f.get("rule", ""))))
			message = String(f.get("message", ""))
	return {"severity": worst, "rule": rule, "message": message}

func ghost_check(piece_id: String, at: Vector2, options: Dictionary = {}) -> Dictionary:
	return ghost_verdict(ghost_plan(piece_id, at, options))

## The scatter brush (round 7): small dressing (a piece no more than two cells either way, not a
## fence) over the cells of one stroke, each cell choosing by its own deterministic seed whether to
## take a piece (density) and which variant (by weight); a cell within a cell of another piece's
## foot is skipped (clearance) and every piece is checked by the shared relation engine against the
## zone with the stroke's earlier pieces in it (its forbids). One undo per stroke.
func scatter(piece_id: String, cells: Array, options: Dictionary = {}) -> Dictionary:
	var context := _context(true)
	if not context.ok:
		return context
	var raw := definition(piece_id)
	if raw.is_empty():
		return _failure("rules.unknown_piece", "Unknown piece '%s'." % piece_id)
	var gate := _approval(raw)
	if not gate.ok:
		return gate
	var cells_size: Array = raw.get("geometry", {}).get("size_cells", [9, 9])
	if raw.get("placement", {}).has("boundary") or int(cells_size[0]) > 2 or int(cells_size[1]) > 2:
		return _failure("rules.scatter", "Scatter takes small dressing only (two cells or less, not a fence): '%s' is %s cells." % [piece_id, cells_size])
	var props := _zone.get_node_or_null("Props") as Node2D
	if props == null:
		return _failure("editor.props_missing", "The zone needs its authored Props container before placing pieces.")
	var evaluator = _options.get("relation_evaluator", Callable())
	if not evaluator is Callable or not evaluator.is_valid():
		return _failure("rules.provider_missing", "Placement is unavailable until the shared relation engine is installed.")
	var density := float(options.get("density", 0.35))
	var seed := int(options.get("seed", 7))
	var size := _ground.kit.cell
	var snapshot := export_plan()
	if not snapshot.ok:
		return snapshot
	var plan: Dictionary = snapshot.plan.duplicate(true)
	if not plan.has("pieces"):
		plan["pieces"] = []
	var unit := float(size) if String(plan.get("coordinate_space", "texels")) == "cells" else 1.0
	var taken := {}
	for e in plan.get("pieces", []):
		var f := Vector2(e.at[0], e.at[1]) * unit
		taken[Vector2i(floori(f.x / size), floori((f.y - 1) / size))] = true
	var variants: Array = []
	var weights: Array = []
	for v in raw.get("variants", []):
		variants.append(String(v.get("id", "")))
		weights.append(float(v.get("weight", 1.0)))
	var sorted: Array = cells.duplicate()
	sorted.sort_custom(func(a: Vector2i, b: Vector2i) -> bool: return a.y < b.y or (a.y == b.y and a.x < b.x))
	var added: Array[KitPiece] = []
	var skipped := {"density": 0, "clearance": 0, "rules": 0}
	for value in sorted:
		var c := Vector2i(value)
		if not _in_bounds(c):
			continue
		if Tools.cell_hash(c, seed) >= density:
			skipped.density += 1
			continue
		var clear := true
		for dy in range(-1, 2):
			for dx in range(-1, 2):
				if taken.has(c + Vector2i(dx, dy)):
					clear = false
		if not clear:
			skipped.clearance += 1
			continue
		var variant := ""
		if variants.size() > 1:
			var total := 0.0
			for w in weights:
				total += w
			var pick := Tools.cell_hash(c, seed, 1) * total
			for i in variants.size():
				pick -= weights[i]
				if pick < 0:
					variant = variants[i]
					break
		var foot := Vector2(c.x * size + size / 2.0, (c.y + 1) * size)
		var instance := {"piece": piece_id, "at": [foot.x / unit, foot.y / unit], "facing": String(options.get("facing", "s")),
			"id": _free_id(piece_id, plan.get("pieces", []))}
		if variant != "":
			instance["variant"] = variant
		if String(options.get("stage", "")) != "":
			instance["stage"] = options.stage
		var verdict := _provider_result(evaluator.call(plan.duplicate(true), instance.duplicate(true), _library.duplicate(true)), "relation engine")
		if not verdict.ok:
			skipped.rules += 1
			continue
		var made := _instantiate(piece_id)
		if not made.ok:
			_discard(added)
			return made
		var piece: KitPiece = made.node
		piece.name = String(instance.id)
		piece.piece_id = piece_id
		piece.variant = variant
		piece.set_meta("kit_zone_entry", instance.duplicate(true))
		piece.set_meta("facing", instance.facing)
		if instance.has("stage"):
			piece.set_meta("stage", instance.stage)
		piece.position = props.to_local(_ground.to_global(foot)) if props.is_inside_tree() else foot
		added.append(piece)
		plan.pieces.append(instance)
		taken[c] = true
	if added.is_empty():
		return {"ok": true, "diagnostics": [], "changed": false, "nodes": [], "skipped": skipped, "message": "Scatter placed nothing here."}
	var before := {"baked": _ground.baked, "baked_live": _ground.showing_baked()}
	_begin("Scatter %s (%d)" % [piece_id, added.size()])
	_do(Callable(self, "_apply_swap").bind(_zone, _ground, props, [], added, true, before))
	_undo(Callable(self, "_apply_swap").bind(_zone, _ground, props, [], added, false, before))
	for node in added:
		_history.add_do_reference(node)
	_history.commit_action()
	return {"ok": true, "diagnostics": [], "changed": true, "nodes": added, "skipped": skipped,
		"message": "Scattered %d %s (%d cells left by density, %d for clearance, %d refused by the rules)." % [
			added.size(), piece_id, skipped.density, skipped.clearance, skipped.rules]}

func validate() -> Dictionary:
	# Export omits unchanged gameplay_from markers to preserve source ownership. Validation
	# must still check where every effective spawn stands in the current scene.
	var snapshot := export_plan(true)
	if not snapshot.ok:
		return snapshot
	var approval_diagnostics := _scene_approval_diagnostics()
	if not approval_diagnostics.is_empty():
		return {"ok": false, "diagnostics": approval_diagnostics, "message": approval_diagnostics[0].message}
	var validator = _options.get("zone_validator", Callable())
	if not validator is Callable or not validator.is_valid():
		return _failure("rules.provider_missing", "Zone validation is unavailable until the shared validator is installed.")
	var result := _provider_result(validator.call(snapshot.plan.duplicate(true), _library.duplicate(true)), "zone validator")
	# What the plan cannot hold is not a physical fault, but it is lost when the scene is rebuilt
	# from its plan: say so beside the validator's own findings.
	for lost in ZonePlan.unexported_actors(_zone):
		result.diagnostics.append({"check": "plan.actor_unexported", "severity": "advice", "message":
			"%s is not an actor kind the plan holds (interactable, villager, restore, camp or an actor scene); it stays in the scene only." % lost})
	return result

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

const GAMEPLAY_KINDS := ["spawn", "door", "interactable", "villager", "restore", "camp"]
var _piece_signature: Array = []

## The id of a placed piece of this kind whose foot is exactly here, or "": a second click on one
## spot must not stack a twin under the first (the picture would not show it).
func _twin(piece_id: String, foot: Vector2) -> String:
	var props := _zone.get_node_or_null("Props") as Node2D
	if props == null:
		return ""
	for child in props.get_children():
		if child is KitPiece and child.piece_id == piece_id:
			var at: Vector2 = _ground.to_local(props.to_global(child.position)) if props.is_inside_tree() else child.position
			if at.distance_to(foot) < 0.5:
				return String(child.name)
	return ""

func _pieces_now() -> Array:
	var out: Array = []
	var props := _zone.get_node_or_null("Props") if is_instance_valid(_zone) else null
	if props != null:
		for child in props.get_children():
			if child is KitPiece:
				out.append([child.get_instance_id(), child.piece_id, child.variant, child.position])
	return out

## What every change must bring up to date (the plugin calls this after each dock operation and
## after any of Godot's own actions on the zone): the pieces' cast shadows and the walk mask (W4's
## KitWalk, installed on first use and saved with the scene). KitWalk marks its ground with its
## instance id while it runs; that id means nothing in another process (a fresh game loading the
## saved scene logged an engine error looking it up), so it is never left on the ground to be saved.
func refresh_derived(target: TerrainGround = null) -> bool:
	if target == null:
		target = _ground
	if not is_instance_valid(target) or not target.is_inside_tree():
		return false
	target.rebuild_shadows()
	var walk := target.get_node_or_null("KitWalk") as KitWalk
	if walk == null:
		walk = Walk.new()
		walk.name = "KitWalk"
		target.add_child(walk)
		walk.owner = target.owner
	var rebuilt := walk.rebuild(target)
	if target.has_meta(Walk.OWNER_META):
		target.remove_meta(Walk.OWNER_META)
	return rebuilt

## Godot's own tools (dragging a piece, the inspector, deleting or duplicating in the scene tree)
## change the zone without the transactions above. When the placed pieces are no longer what the
## last operation left, the baked ground no longer matches them (its shadows and painted pieces),
## so the live tiles show, the caches of the live fault overlay are dropped and `changed` asks for
## the derived data again. True when something had changed.
func sync_native_edits() -> bool:
	if not _context(false).ok:
		return false
	var now := _pieces_now()
	if now == _piece_signature:
		return false
	_piece_signature = now
	_ghost_plans.clear()
	_ghost_verdicts.clear()
	_ghost_snapshot = {}
	if _ground.showing_baked():
		_ground._baked_live = false
		_ground._rebuild()
	last_changed_ground = _ground
	changed.emit()
	return true

## Spawns, doors and actors (10 Nov): one click places what a quest needs with sound defaults, as
## one undo action; its details (the speaker, the target zone, a camp's id) are then set in Godot's
## inspector, and the plan exports them from the nodes (kit_zone.gd, `actors`). Options: id, and per
## kind `to`/`spawn`/`size` (a door, size in cells), `speaker`/`verb` (an interactable),
## `speaker`/`character` (a villager), `restore`, `camp`/`count`/`scene`.
func place_gameplay(kind: String, at: Vector2, options: Dictionary = {}) -> Dictionary:
	var context := _context(true)
	if not context.ok:
		return context
	if kind not in GAMEPLAY_KINDS:
		return _failure("editor.gameplay_kind", "Gameplay kind must be one of %s." % ", ".join(GAMEPLAY_KINDS))
	if not at.is_finite():
		return _failure("rules.bounds", "The position must be finite.")
	var size := _ground.kit.cell
	var snapped := Tools.snap(at, "half", size)
	if snapped.x < 0 or snapped.y < 0 or snapped.x > _ground.size_px().x or snapped.y > _ground.size_px().y:
		return _failure("rules.bounds", "That point lies outside the zone.")
	var container_name: String = {"spawn": "Spawns", "door": "Doors"}.get(kind, "Actors")
	var container := _zone.get_node_or_null(container_name) as Node2D
	if container == null:
		return _failure("editor.container_missing", "The zone has no %s node to hold this." % container_name)
	var cell := Vector2i(floori(minf(snapped.x, _ground.size_px().x - 1) / size), floori(minf(snapped.y, _ground.size_px().y - 1) / size))
	if kind != "door":
		var material: Dictionary = _ground.kit.by_material.get(_ground.ground_at(cell), {})
		if not material.is_empty() and not bool(material.get("walkable", false)):
			return _failure("rules.walk", "Nobody can stand on %s: place the %s on walkable ground." % [material.get("id", "this ground"), kind])
	var used := {}
	for child in container.get_children():
		used[String(child.name)] = true
		used[ZonePlan._logical_id(child)] = true
		for inner in child.get_children():
			used[String(inner.name)] = true
	var wanted := String(options.get("id", ""))
	if wanted == "":
		wanted = {"spawn": "spawn", "door": "Door", "interactable": "Talk", "villager": "Villager", "restore": "Restore", "camp": "Camp"}[kind]
	if wanted.validate_node_name() != wanted or wanted in [".", ".."]:
		return _failure("rules.instance_id", "The name must be a valid node name.")
	var id := wanted
	var suffix := 2
	while used.has(id) or used.has("If_" + id):
		if options.has("id"):
			return _failure("rules.instance_id", "'%s' already exists under %s." % [id, container_name])
		id = "%s_%d" % [wanted, suffix]
		suffix += 1
	var unit := float(size) if String(_zone.get_meta(ZonePlan.PLAN_META, _options.get("plan", {})).get("coordinate_space", "texels")) == "cells" else 1.0
	var node: Node2D
	match kind:
		"spawn":
			var marker := Marker2D.new()
			marker.set_meta(&"kit_zone_id", id)
			marker.set_meta(ZonePlan.EXPLICIT_META, true)
			marker.position = snapped
			node = marker
		"door":
			var span: Array = options.get("size", [])
			if span.size() != 2:
				# an edge door lies along its edge, three cells wide; elsewhere one cell (a hatch)
				span = [1, 3] if cell.x == 0 or cell.x == _ground.grid_size.x - 1 else ([3, 1] if cell.y == 0 or cell.y == _ground.grid_size.y - 1 else [1, 1])
			var w := float(span[0])
			var h := float(span[1])
			if w <= 0 or h <= 0:
				return _failure("rules.bounds", "A door needs a positive size in cells.")
			var x0 := clampf(float(cell.x) - floorf((w - 1.0) / 2.0), 0.0, maxf(0.0, _ground.grid_size.x - w))
			var y0 := clampf(float(cell.y) - floorf((h - 1.0) / 2.0), 0.0, maxf(0.0, _ground.grid_size.y - h))
			var entry := {"id": id, "rect": [x0, y0, w, h], "to": String(options.get("to", ""))}
			if String(options.get("spawn", "start")) != "start":
				entry["spawn"] = String(options.spawn)
			node = ZonePlan.door_node(entry, size)
		_:
			var entry := {"id": id, "kind": kind, "at": [snapped.x / unit, snapped.y / unit]}
			match kind:
				"interactable":
					entry["speaker"] = String(options.get("speaker", id.to_snake_case()))
					if String(options.get("verb", "")) != "":
						entry["verb"] = String(options.verb)
				"villager":
					entry["character"] = String(options.get("character", ""))
					entry["speaker"] = String(options.get("speaker", entry.character))
				"restore":
					entry["restore"] = String(options.get("restore", id.to_snake_case()))
				"camp":
					entry["camp"] = String(options.get("camp", id.to_snake_case()))
					if String(options.get("scene", "")) != "":
						entry["scene"] = String(options.scene)
					# enemies stand in a loose ring round the camp's point, a cell and a half out
					var count := clampi(int(options.get("count", 3)), 1, 12)
					var spots := []
					for i in count:
						var spot := snapped + Vector2.from_angle(TAU * float(i) / float(count) - PI / 2.0) * size * 1.5
						spots.append([roundf(spot.x) / unit, roundf(spot.y) / unit])
					entry["enemies"] = spots
			var problem := ZonePlan.actor_error(entry, unit)
			if not problem.is_empty():
				return _failure("plan.actor", "The %s%s." % [kind, problem])
			node = ZonePlan.actor_node(entry, unit)
			if node == null:
				return _failure("plan.actor", "The %s's scene could not be instanced." % kind)
	node.name = id
	_begin("Place %s %s" % [kind, id])
	_do(Callable(self, "_apply_gameplay").bind(_zone, container, node, true))
	_undo(Callable(self, "_apply_gameplay").bind(_zone, container, node, false))
	_history.add_do_reference(node)
	_history.commit_action()
	return {"ok": true, "diagnostics": [], "changed": true, "node": node, "id": id, "at": snapped,
		"message": "Placed %s '%s'. Set its details in the inspector." % [kind, id]}

func _apply_gameplay(zone: Node, container: Node2D, node: Node2D, attach: bool) -> void:
	if not is_instance_valid(zone) or not is_instance_valid(container) or not is_instance_valid(node):
		return
	if attach:
		if node.get_parent() == null:
			container.add_child(node)
			ZonePlan._own_new(node, zone)
	elif node.get_parent() == container:
		container.remove_child(node)
	_ghost_plans.clear()
	_ghost_verdicts.clear()
	_ghost_snapshot = {}
	if is_instance_valid(_ground):
		last_changed_ground = _ground
	changed.emit()

## Write the zone's plan beside the others (game/kit/zones/<zone>.json): the compact form the
## Python checks, the bake and reviewers read. The scene and its plan are one document in two
## files; a guard test fails when a committed pair disagrees.
func export_plan_file(path: String = "") -> Dictionary:
	var snapshot := export_plan()
	if not snapshot.ok:
		return snapshot
	var zone_id := String(_zone.get("zone_id"))
	if path == "":
		if zone_id == "" or zone_id.validate_filename() != zone_id or zone_id in [".", ".."]:
			return _failure("plan.zone", "The zone needs an id before its plan can be written.")
		path = "res://kit/zones/%s.json" % zone_id
	var problem := ZonePlan.write_plan(snapshot.plan, path)
	if not problem.is_empty():
		return _failure("plan.export", "The plan was not written: %s." % problem)
	var lost := ZonePlan.unexported_actors(_zone)
	var note := "" if lost.is_empty() else " Not in the plan (scene only): %s." % ", ".join(lost)
	return {"ok": true, "diagnostics": [], "path": path, "unexported": lost, "message": "Wrote %s.%s" % [path, note]}

## Export current authoring data, preserving the original plan's unknown fields. Gameplay
## ownership stays with its scene; no ordinary node is removed, replaced or reparented here.
func export_plan(include_inherited_spawns: bool = false) -> Dictionary:
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
	var plan: Dictionary = ZonePlan.plan_from_scene(_zone as Node2D, fallback, include_inherited_spawns)
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

func _apply_swap(zone: Node, target: TerrainGround, props: Node2D, removed: Array, added: Array, forward: bool, before: Dictionary) -> void:
	if not is_instance_valid(zone) or not is_instance_valid(target):
		return
	var going: Array = removed if forward else added
	var coming: Array = added if forward else removed
	for node in going:
		if is_instance_valid(node) and node.get_parent() == props:
			props.remove_child(node)
	for node in coming:
		if is_instance_valid(node) and node.get_parent() == null:
			props.add_child(node)
			node.owner = zone
	_restore_ground(target, {"baked": before.baked, "baked_live": false} if forward else before)

## A new piece's authored data (the Codex lead's review of #430, P2): a piece that replaces one
## (a re-joined fence cell, a gate on a run) keeps the old node's metadata (stage, facing and any
## other meta) and entry fields, and takes the selected options only where the old one had none;
## a new piece takes the selected options. The variant is the old one, else the selected one,
## whichever this piece has, else `fallback`.
func _dress(piece: KitPiece, entry: Dictionary, old: Node, options: Dictionary, fallback: String = "") -> void:
	var raw := definition(piece.piece_id)
	if old != null:
		for key in old.get_meta_list():
			if key != "kit_zone_entry":
				piece.set_meta(key, old.get_meta(key))
	for key in ["facing", "stage"]:
		if not piece.has_meta(key) and String(options.get(key, "")) != "":
			piece.set_meta(key, options[key])
	if not piece.has_meta("facing"):
		piece.set_meta("facing", "s")
	entry["facing"] = piece.get_meta("facing")
	if piece.has_meta("stage"):
		entry["stage"] = piece.get_meta("stage")
	piece.variant = fallback
	for wanted in [String(old.variant) if old is KitPiece else "", String(options.get("variant", ""))]:
		if wanted != "" and _piece_variant(raw, wanted):
			piece.variant = wanted
			break
	if piece.variant != "" or entry.has("variant"):
		entry["variant"] = piece.variant
	piece.set_meta("kit_zone_entry", entry)

## Free pieces made for an operation that was then refused: nothing was attached or recorded, so
## the scene and the undo history stay as they were (the Codex lead's review of #430, P2).
func _discard(nodes: Array) -> void:
	for node in nodes:
		if is_instance_valid(node) and node.get_parent() == null:
			node.free()
	nodes.clear()

func _instantiate(piece_id: String) -> Dictionary:
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
	return {"ok": true, "diagnostics": [], "node": inst}

func _restore_ground(target: TerrainGround, state: Dictionary) -> void:
	# Re-derive before restoring baked validity, so TileMapLayer's later changed notification
	# sees matching cells and cannot invalidate an otherwise exact undo snapshot.
	target.baked = state.baked
	target._rebuild()
	target._baked_live = bool(state.baked_live)
	target._rebuild()
	target.rebuild_shadows()
	last_changed_ground = target
	_ghost_plans.clear()
	_ghost_verdicts.clear()
	_ghost_snapshot = {}
	if target == _ground:
		_piece_signature = _pieces_now()
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
