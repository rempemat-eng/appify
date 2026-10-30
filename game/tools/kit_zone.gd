extends SceneTree
## Lossless kit plan <-> scene authoring (W2, docs/world-editor.md).
## --plan=<json> [--out=<tscn>] or --export=<tscn> [--out=<json>].
## Legacy piece `at` and spawns are Godot texels. Explicit coordinate_space="cells"
## uses logical terrain cells for those fields; no guessing from their magnitudes.
## Door `rect` is always in cells, with existing plan keys id/to/spawn/if.
## Flow is a hidden logical TileMapLayer with a `flow` custom-data glyph per cell.
## Facing/stage are authored metadata; no new facing art, flow animation or rules ship.
## The source template is saved IN the scene, so export needs no input/output sidecar.

const PLAN_META := &"kit_zone_plan"
const ENTRY_META := &"kit_zone_entry"
const EXPLICIT_META := &"kit_zone_explicit"
const GAMEPLAY_IDS_META := &"kit_zone_gameplay_ids"

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2, a.find("=") - 2)] = a.substr(a.find("=") + 1)
	var code := 1
	if args.has("plan"):
		code = _build(args.plan, args.get("out", ""))
	elif args.has("export"):
		code = _export(args.export, args.get("out", ""))
	else:
		printerr("kit_zone: --plan=<json> or --export=<tscn>")
	quit(code)

static func _read(path: String) -> Dictionary:
	var value = JSON.parse_string(FileAccess.get_file_as_string(path))
	return value if value is Dictionary else {}

## Canonical JSON: recursive key ordering; arrays keep author order.
static func canonical(plan: Dictionary) -> String:
	return JSON.stringify(_canonical_value(plan), " ", true) + "\n"

static func _canonical_value(value: Variant) -> Variant:
	if value is Dictionary:
		var out := {}
		for key in value:
			out[key] = _canonical_value(value[key])
		return out
	if value is Array:
		var out := []
		for item in value:
			out.append(_canonical_value(item))
		return out
	if value is float and is_finite(value) and abs(value) < 9.0e18 and value == float(int(value)):
		return int(value)
	return value

static func _unown(node: Node, source: Node) -> void:
	for child in node.get_children():
		_unown(child, source)
	if node.owner == source:
		node.owner = null

static func _units(plan: Dictionary, cell: int) -> float:
	return float(cell) if plan.get("coordinate_space", "texels") == "cells" else 1.0

static func _own(node: Node, root: Node) -> void:
	if node.owner == null:
		node.owner = root
	for child in node.get_children():
		_own(child, root)

static func _container(root: Node, name_: String) -> Node2D:
	var node := root.get_node_or_null(NodePath(name_)) as Node2D
	if node == null:
		node = Node2D.new()
		node.name = name_
		root.add_child(node)
		node.owner = root
	return node

## Authored IDs are literal data. Node names are only collision-safe storage names;
## never interpret an ID as a NodePath or discard its persisted logical identity.
static func _logical_id(node: Node) -> String:
	if node.has_meta(&"kit_zone_id"):
		return String(node.get_meta(&"kit_zone_id"))
	var entry = node.get_meta(ENTRY_META, {})
	if entry is Dictionary and entry.get("id") is String and not entry.id.is_empty():
		return entry.id
	return String(node.name)

static func _child_with_id(parent: Node, id: String) -> Node:
	if parent != null:
		for child in parent.get_children():
			if _logical_id(child) == id:
				return child
	return null

static func _storage_name(parent: Node, id: String) -> String:
	var base := id.validate_node_name()
	if base in ["", ".", ".."]:
		base = "Entry"
	var used := {}
	for child in parent.get_children():
		used[String(child.name)] = true
	var candidate := base
	var suffix := 1
	while used.has(candidate):
		candidate = "%s_%s" % [base, suffix]
		suffix += 1
	return candidate

static func _valid_rows(rows: Variant, width: int, height: int) -> bool:
	if not rows is Array or rows.size() != height:
		return false
	for row in rows:
		if not row is String or row.length() != width:
			return false
	return true

static func _numbers(value: Variant, count: int, unit: float = 1.0) -> bool:
	if not value is Array or value.size() != count:
		return false
	for number in value:
		if typeof(number) not in [TYPE_INT, TYPE_FLOAT] or not is_finite(float(number)):
			return false
		# Vector2 stores float32 components, including when JSON numbers are doubles.
		if absf(float(number) * unit) > 3.402823466e38:
			return false
	return true

## Structural errors are rejected before constructing any scene nodes. Unknown
## extension fields stay in the template; placement and approvals belong to W5/W6.
static func plan_error(plan: Dictionary) -> String:
	if not plan.get("zone") is String or plan.zone.is_empty():
		return "zone must be a nonempty string"
	if plan.zone.capitalize().replace(" ", "").is_empty():
		return "zone must produce a nonempty scene name"
	if not plan.get("legend") is Dictionary:
		return "legend must be an object of string material IDs"
	for key in plan.legend:
		if not key is String or not plan.legend[key] is String:
			return "legend keys and material IDs must be strings"
	var rows = plan.get("rows")
	if not rows is Array or rows.is_empty() or not rows[0] is String or rows[0].is_empty():
		return "rows must be a nonempty array of nonempty equal-width strings"
	var width: int = rows[0].length()
	if not _valid_rows(rows, width, rows.size()):
		return "rows must contain equal-width strings"
	if plan.get("coordinate_space", "texels") not in ["texels", "cells"]:
		return "coordinate_space must be texels or cells"
	if plan.has("lab") and not plan.lab is bool:
		return "lab must be a boolean"
	for field in ["tiers", "flow", "variants"]:
		if plan.has(field) and not _valid_rows(plan[field], width, rows.size()):
			return "%s must be an array of strings matching rows" % field
	if plan.has("tiers"):
		for row in plan.tiers:
			for glyph in row:
				if glyph < "0" or glyph > "9":
					return "tiers must contain digit glyphs"
	if plan.has("flow"):
		for row in plan.flow:
			for glyph in row:
				if glyph not in [".", " ", "^", ">", "v", "<", "↑", "→", "↓", "←", "↗", "↘", "↙", "↖"]:
					return "flow contains an unsupported glyph"
	var kit := TerrainKit.shared()
	var unit := _units(plan, kit.cell)
	for field in ["pieces", "doors"]:
		if not plan.get(field, []) is Array:
			return "%s must be an array" % field
		for i in plan.get(field, []).size():
			var entry = plan[field][i]
			var path := "%s[%s]" % [field, i]
			if not entry is Dictionary:
				return "%s must be an object" % path
			var name_field := "piece" if field == "pieces" else "id"
			if not entry.get(name_field) is String or entry[name_field].is_empty():
				return "%s.%s must be a nonempty string" % [path, name_field]
			if field == "pieces":
				if not _numbers(entry.get("at"), 2, unit):
					return "%s.at must contain two finite coordinates" % path
				for key in ["id", "variant", "facing", "stage"]:
					if entry.has(key) and not entry[key] is String:
						return "%s.%s must be a string" % [path, key]
				if entry.has("id") and entry.id.is_empty():
					return "%s.id must be a nonempty string" % path
			else:
				if not _numbers(entry.get("rect"), 4, kit.cell):
					return "%s.rect must contain four finite coordinates" % path
				if entry.rect[2] <= 0 or entry.rect[3] <= 0:
					return "%s.rect width and height must be positive" % path
				if not _numbers([entry.rect[0] + entry.rect[2] / 2.0, entry.rect[1] + entry.rect[3] / 2.0], 2, kit.cell):
					return "%s.rect centre must contain finite coordinates" % path
				for key in ["to", "target_zone", "spawn", "target_spawn"]:
					if entry.has(key) and not entry[key] is String:
						return "%s.%s must be a string" % [path, key]
				if (entry.has("to") and entry.has("target_zone") and entry.to != entry.target_zone) or (entry.has("spawn") and entry.has("target_spawn") and entry.spawn != entry.target_spawn):
					return "%s target aliases disagree" % path
	if not plan.get("spawns", {}) is Dictionary:
		return "spawns must be an object of coordinate pairs"
	for id in plan.get("spawns", {}):
		if not id is String or id.is_empty() or not _numbers(plan.spawns[id], 2, unit):
			return "spawns must map nonempty string IDs to two finite coordinates"
	if plan.has("gameplay_from") and not plan.gameplay_from is String:
		return "gameplay_from must be a scene path string"
	if not plan.get("gameplay_removed", {}) is Dictionary:
		return "gameplay_removed must be an object"
	for field in ["Spawns", "Doors"]:
		var removed = plan.get("gameplay_removed", {}).get(field, [])
		if not removed is Array:
			return "gameplay_removed.%s must be an array of string IDs" % field
		for id in removed:
			if not id is String or id.is_empty():
				return "gameplay_removed.%s must contain nonempty string IDs" % field
	return ""

## Returns an unattached scene, suitable for PackedScene.pack without entering a tree.
static func scene_from_plan(plan: Dictionary) -> Node2D:
	if not plan_error(plan).is_empty():
		return null
	var kit := TerrainKit.shared()
	var rows: Array = plan.get("rows", [])
	var size := Vector2i(rows[0].length(), rows.size())
	var root := Node2D.new()
	root.name = String(plan.zone).capitalize().replace(" ", "")
	root.set_script(load("res://world/zone.gd"))
	root.set("zone_id", plan.zone)
	root.set("bounds", Rect2(Vector2.ZERO, Vector2(size * kit.cell)))
	root.set_meta(PLAN_META, plan.duplicate(true))
	root.y_sort_enabled = true
	var ground := TerrainGround.new()
	ground.name = "Ground"
	ground.grid_size = size
	ground.z_index = -10
	ground.lab = bool(plan.get("lab", false))
	var baked_png := "res://zones/%s/ground_baked.png" % plan.zone
	if ResourceLoader.exists(baked_png):
		ground.baked = load(baked_png)
	if plan.has("variants"):
		ground.variant_rows = PackedStringArray(plan.variants)
	root.add_child(ground)
	ground.owner = root
	var cells := TileMapLayer.new()
	cells.name = "Cells"
	cells.tile_set = kit.tileset
	ground.add_child(cells)
	cells.owner = root
	var legend: Dictionary = plan.legend
	for y in size.y:
		for x in size.x:
			var id: String = legend.get(rows[y][x], "")
			if id == "":
				continue
			var ac := kit.atlas_coords(id)
			if ac.x < 0:
				root.free()
				return null
			cells.set_cell(Vector2i(x, y), 0, ac)
	if plan.has("tiers"):
		var tiers := TileMapLayer.new()
		tiers.name = "Tiers"
		tiers.tile_set = kit.tiers_tileset
		ground.add_child(tiers)
		tiers.owner = root
		for y in size.y:
			for x in size.x:
				var ch: String = plan.tiers[y][x]
				if ch < "0" or ch > "9":
					root.free()
					return null
				if not kit.tiers_tileset.get_source(0).has_tile(Vector2i(int(ch), 0)):
					root.free()
					return null
				if int(ch) > 0:
					tiers.set_cell(Vector2i(x, y), 0, Vector2i(int(ch), 0))
	if plan.has("flow"):
		for row in plan.flow:
			for ch in row:
				if ch not in [".", " ", "^", ">", "v", "<", "↑", "→", "↓", "←", "↗", "↘", "↙", "↖"]:
					root.free()
					return null
		var flow := _flow_layer(plan.flow, kit.cell)
		ground.add_child(flow)
		flow.owner = root
	var props := _container(root, "Props")
	props.y_sort_enabled = true
	var unit := _units(plan, kit.cell)
	for entry in plan.get("pieces", []):
		var piece_path := "res://kit/props/%s.tscn" % entry.piece
		var ps := load(piece_path) as PackedScene if ResourceLoader.exists(piece_path) else null
		if ps == null:
			root.free()
			return null
		var node := ps.instantiate()
		if not node is KitPiece:
			node.free()
			root.free()
			return null
		var inst := node as KitPiece
		inst.name = String(entry.get("id", entry.piece)).validate_node_name()
		inst.position = Vector2(entry.at[0], entry.at[1]) * unit
		inst.set_meta(ENTRY_META, entry.duplicate(true))
		for field in ["facing", "stage"]:
			if entry.has(field):
				inst.set_meta(field, entry[field])
		if entry.has("variant"):
			inst.variant = entry.variant
		if String(KitPiece.index().get(entry.piece, {}).get("z_sort", "foot")) == "ground":
			inst.z_index = -5
		props.add_child(inst)
		# Keep the library instance's children owned by that scene, not flattened copies.
		inst.owner = root
	if plan.has("gameplay_from"):
		var packed := load(plan.gameplay_from) as PackedScene if ResourceLoader.exists(plan.gameplay_from) else null
		if packed == null:
			root.free()
			return null
		var src := packed.instantiate()
		var inherited_ids := {}
		for name_ in ["Actors", "Spawns", "Doors"]:
			var node := src.get_node_or_null(NodePath(name_))
			if node != null:
				_unown(node, src)
				src.remove_child(node)
				root.add_child(node)
				_own(node, root)
				for child in node.get_children():
					child.set_meta(EXPLICIT_META, false)
					if name_ == "Spawns" and child is Marker2D:
						child.set_meta(&"kit_zone_inherited", child.position)
					elif name_ == "Doors" and child is Area2D:
						child.set_meta(&"kit_zone_inherited", _door_entry(child, child.get_meta(ENTRY_META, {}), kit.cell))
				if name_ in ["Spawns", "Doors"]:
					inherited_ids[name_] = []
					for child in node.get_children():
						inherited_ids[name_].append(_logical_id(child))
					for id in plan.get("gameplay_removed", {}).get(name_, []):
						var removed := _child_with_id(node, id)
						if removed != null:
							removed.free()
		root.set_meta(GAMEPLAY_IDS_META, inherited_ids)
		src.free()
	_container(root, "Actors").y_sort_enabled = true
	var spawns := _container(root, "Spawns")
	var specified: Dictionary = plan.get("spawns", {})
	if specified.is_empty() and spawns.get_child_count() == 0 and not "start" in plan.get("gameplay_removed", {}).get("Spawns", []):
		var fallback := Marker2D.new()
		fallback.name = "start"
		fallback.position = Vector2(size * kit.cell) / 2.0
		fallback.set_meta(EXPLICIT_META, false)
		fallback.set_meta(&"kit_zone_inherited", fallback.position)
		spawns.add_child(fallback)
		fallback.owner = root
	for id in specified:
		var marker := _child_with_id(spawns, id) as Marker2D
		if marker == null:
			marker = Marker2D.new()
			marker.name = _storage_name(spawns, id)
			spawns.add_child(marker)
			marker.owner = root
		marker.set_meta(&"kit_zone_id", id)
		marker.set_meta(EXPLICIT_META, true)
		marker.position = Vector2(specified[id][0], specified[id][1]) * unit
	var doors := _container(root, "Doors")
	for entry in plan.get("doors", []):
		if (entry.has("to") and entry.has("target_zone") and entry.to != entry.target_zone) or (entry.has("spawn") and entry.has("target_spawn") and entry.spawn != entry.target_spawn):
			root.free()
			return null
		var prior := _child_with_id(doors, entry.id)
		if prior != null:
			prior.free()
		var door = load("res://world/door.gd").new()
		door.name = _storage_name(doors, entry.id)
		var r: Array = entry.rect
		door.position = Vector2(r[0] + r[2] / 2.0, r[1] + r[3] / 2.0) * kit.cell
		door.target_zone = entry.get("to", entry.get("target_zone", ""))
		door.target_spawn = entry.get("spawn", entry.get("target_spawn", "start"))
		if entry.has("if"):
			door.only_if = JSON.stringify(entry["if"])
		door.set_meta(ENTRY_META, entry.duplicate(true))
		door.set_meta(EXPLICIT_META, true)
		var shape := CollisionShape2D.new()
		shape.name = "Shape"
		var rectangle := RectangleShape2D.new()
		rectangle.size = Vector2(r[2], r[3]) * kit.cell
		shape.shape = rectangle
		door.add_child(shape)
		doors.add_child(door)
		_own(door, root)
	return root

static func _flow_layer(rows: Array, cell: int) -> TileMapLayer:
	var glyphs := []
	for row in rows:
		for ch in row:
			if ch != "." and ch != " " and ch not in glyphs:
				glyphs.append(ch)
	glyphs.sort()
	var flow := TileMapLayer.new()
	flow.name = "Flow"
	flow.self_modulate.a = 0.0
	flow.set_meta(&"glyphs", glyphs)
	var tiles := TileSet.new()
	tiles.tile_size = Vector2i(cell, cell)
	tiles.add_custom_data_layer()
	tiles.set_custom_data_layer_name(0, "flow")
	tiles.set_custom_data_layer_type(0, TYPE_STRING)
	var atlas := TileSetAtlasSource.new()
	var texture := GradientTexture2D.new()
	texture.width = maxi(1, glyphs.size()) * cell
	texture.height = cell
	texture.gradient = Gradient.new()
	atlas.texture = texture
	atlas.texture_region_size = Vector2i(cell, cell)
	tiles.add_source(atlas, 0)
	for i in glyphs.size():
		atlas.create_tile(Vector2i(i, 0))
		atlas.get_tile_data(Vector2i(i, 0), 0).set_custom_data("flow", glyphs[i])
	flow.tile_set = tiles
	for y in rows.size():
		for x in rows[y].length():
			var i := glyphs.find(rows[y][x])
			if i >= 0:
				flow.set_cell(Vector2i(x, y), 0, Vector2i(i, 0))
	return flow

static func plan_from_scene(root: Node2D, fallback: Dictionary = {}) -> Dictionary:
	var plan: Dictionary = root.get_meta(PLAN_META, fallback).duplicate(true)
	var ground := root.get_node("Ground") as TerrainGround
	var kit := TerrainKit.shared()
	plan["zone"] = root.get("zone_id")
	var legend: Dictionary = plan.get("legend", {}).duplicate()
	var back := {}
	for key in legend:
		if not back.has(legend[key]):
			back[legend[key]] = key
	var rows := []
	for y in ground.grid_size.y:
		var row := ""
		for x in ground.grid_size.x:
			var ac := ground.get_cells_layer().get_cell_atlas_coords(Vector2i(x, y))
			var mats: Array = kit.manifest.materials
			var id := "" if ac.x < 0 or ac.x >= mats.size() else String(mats[ac.x].id)
			var original := ""
			if y < plan.get("rows", []).size() and x < plan.rows[y].length():
				original = plan.rows[y][x]
			if legend.get(original, "") == id:
				row += original
			elif id == "":
				row += " "
			else:
				if not back.has(id):
					for ch in "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ":
						if not legend.has(ch):
							legend[ch] = id
							back[id] = ch
							break
				row += back.get(id, " ")
		rows.append(row)
	plan["legend"] = legend
	plan["rows"] = rows
	if plan.has("lab") or ground.lab:
		plan["lab"] = ground.lab
	var tiers := ground.get_tiers_layer()
	if tiers != null:
		var out := []
		for y in ground.grid_size.y:
			var row := ""
			for x in ground.grid_size.x:
				row += str(maxi(0, tiers.get_cell_atlas_coords(Vector2i(x, y)).x))
			out.append(row)
		plan["tiers"] = out
	else:
		plan.erase("tiers")
	var flow := ground.get_node_or_null("Flow") as TileMapLayer
	if flow != null:
		var out := []
		var glyphs: Array = flow.get_meta(&"glyphs", [])
		for y in ground.grid_size.y:
			var row := ""
			for x in ground.grid_size.x:
				var ac := flow.get_cell_atlas_coords(Vector2i(x, y))
				var old := "."
				if y < plan.get("flow", []).size() and x < plan.flow[y].length():
					old = plan.flow[y][x]
				row += String(glyphs[ac.x]) if ac.x >= 0 and ac.x < glyphs.size() else (old if old in [".", " "] else ".")
			out.append(row)
		plan["flow"] = out
	else:
		plan.erase("flow")
	if not ground.variant_rows.is_empty():
		plan["variants"] = Array(ground.variant_rows)
	else:
		plan.erase("variants")
	var pieces := []
	var props := root.get_node_or_null("Props")
	var unit := _units(plan, kit.cell)
	if props != null:
		for child in props.get_children():
			if not child is KitPiece:
				continue
			var entry: Dictionary = child.get_meta(ENTRY_META, {}).duplicate(true)
			if entry.is_empty():
				entry["id"] = String(child.name)
			entry["piece"] = child.piece_id
			entry["at"] = _position_value(child.position, entry.get("at", []), unit)
			if child.variant != "" or entry.has("variant"):
				entry["variant"] = child.variant
			for field in ["facing", "stage"]:
				if child.has_meta(field):
					entry[field] = child.get_meta(field)
				else:
					entry.erase(field)
			pieces.append(entry)
	if plan.has("pieces") or not pieces.is_empty():
		plan["pieces"] = pieces
	var spawns := {}
	var spawn_node := root.get_node_or_null("Spawns")
	for marker in spawn_node.get_children() if spawn_node != null else []:
		if not marker is Marker2D:
			continue
		if not bool(marker.get_meta(EXPLICIT_META, true)) and marker.position == marker.get_meta(&"kit_zone_inherited", marker.position):
			continue
		var id := _logical_id(marker)
		spawns[id] = _position_value(marker.position, plan.get("spawns", {}).get(id, []), unit)
	if plan.has("spawns") or not spawns.is_empty():
		plan["spawns"] = spawns
	var doors := []
	var door_node := root.get_node_or_null("Doors")
	for door in door_node.get_children() if door_node != null else []:
		if not door is Area2D or door.get_script() != load("res://world/door.gd"):
			continue
		var entry: Dictionary = _door_entry(door, door.get_meta(ENTRY_META, {}), kit.cell)
		if not bool(door.get_meta(EXPLICIT_META, true)) and entry == door.get_meta(&"kit_zone_inherited", entry):
			continue
		doors.append(entry)
	if plan.has("doors") or not doors.is_empty():
		plan["doors"] = doors
	# A missing inherited node needs a tombstone; omission alone would copy it
	# again from gameplay_from on the next build. Explicit overrides can revive it.
	if root.has_meta(GAMEPLAY_IDS_META):
		var removed: Dictionary = plan.get("gameplay_removed", {}).duplicate(true)
		var inherited_ids: Dictionary = root.get_meta(GAMEPLAY_IDS_META)
		for name_ in ["Spawns", "Doors"]:
			var missing := []
			var container := root.get_node_or_null(NodePath(name_))
			for id in inherited_ids.get(name_, []):
				if _child_with_id(container, id) == null:
					missing.append(id)
			if removed.has(name_) or not missing.is_empty():
				removed[name_] = missing
		if plan.has("gameplay_removed") or not removed.is_empty():
			plan["gameplay_removed"] = removed
	return plan

## Retain unchanged JSON numbers before Vector2's float32 conversion can round them.
static func _position_value(position: Vector2, original: Array, unit: float) -> Array:
	if original.size() == 2 and position == Vector2(original[0], original[1]) * unit:
		return original.duplicate()
	return [position.x / unit, position.y / unit]

static func _door_entry(door: Node2D, template: Dictionary, cell: int) -> Dictionary:
	var entry := template.duplicate(true)
	if entry.is_empty():
		entry["id"] = _logical_id(door)
	var shape := door.get_node_or_null("Shape") as CollisionShape2D
	if shape == null or not shape.shape is RectangleShape2D:
		return entry
	var rect := shape.shape as RectangleShape2D
	var start: Vector2 = door.position + shape.position - rect.size / 2.0
	var old: Array = entry.get("rect", [])
	if old.size() != 4 or rect.size != Vector2(old[2], old[3]) * cell or door.position + shape.position != Vector2(old[0] + old[2] / 2.0, old[1] + old[3] / 2.0) * cell:
		entry["rect"] = [start.x / cell, start.y / cell, rect.size.x / cell, rect.size.y / cell]
	entry["target_zone" if entry.has("target_zone") else "to"] = door.get("target_zone")
	if entry.has("to") and entry.has("target_zone"):
		entry["to"] = door.get("target_zone")
	if entry.has("spawn") or entry.has("target_spawn") or door.get("target_spawn") != "start":
		entry["target_spawn" if entry.has("target_spawn") else "spawn"] = door.get("target_spawn")
	if entry.has("spawn") and entry.has("target_spawn"):
		entry["spawn"] = door.get("target_spawn")
	var condition: String = door.get("only_if")
	if condition != "":
		entry["if"] = JSON.parse_string(condition)
	else:
		entry.erase("if")
	return entry

func _build(path: String, out: String) -> int:
	var plan := _read(path)
	var problem := plan_error(plan)
	if not problem.is_empty():
		printerr("kit_zone: invalid plan ", path, ": ", problem)
		return 1
	var root := scene_from_plan(plan)
	if root == null:
		printerr("kit_zone: invalid plan ", path)
		return 1
	var scene := PackedScene.new()
	var err := scene.pack(root)
	if out == "":
		out = "res://zones/%s/%s.tscn" % [root.get("zone_id"), root.get("zone_id")]
	if err == OK:
		DirAccess.make_dir_recursive_absolute(out.get_base_dir())
		err = ResourceSaver.save(scene, out)
	root.free()
	print("kit_zone: wrote ", out)
	return 0 if err == OK else 1

func _export(path: String, out: String) -> int:
	var scene := load(path) as PackedScene
	if scene == null:
		return 1
	var root := scene.instantiate() as Node2D
	var fallback := "res://kit/zones/%s.json" % root.get("zone_id")
	var plan := plan_from_scene(root, _read(fallback) if not root.has_meta(PLAN_META) and FileAccess.file_exists(fallback) else {})
	var problem := plan_error(plan)
	if not problem.is_empty():
		printerr("kit_zone: invalid plan ", path, ": ", problem)
		root.free()
		return 1
	if out == "":
		out = fallback
	# Keep the previous document intact until a complete candidate is closed and checked.
	var directory := DirAccess.open(out.get_base_dir() if out.get_base_dir() != "" else ".")
	if directory == null:
		root.free()
		return 1
	var staged := out + ".tmp"
	var document := canonical(plan)
	var file := FileAccess.open(staged, FileAccess.WRITE)
	if file == null:
		root.free()
		return 1
	file.store_string(document)
	file.flush()
	var err := file.get_error()
	file.close()
	if err != OK:
		printerr("kit_zone: failed staged write ", staged, ": ", error_string(err))
		root.free()
		return 1
	# Reopen after close to catch incomplete output, including delayed write failures.
	# Failed stages remain beside the destination for inspection/recovery.
	var candidate := FileAccess.open(staged, FileAccess.READ)
	if candidate == null:
		root.free()
		return 1
	var encoded := document.to_utf8_buffer()
	var complete := candidate.get_length() == encoded.size() and candidate.get_buffer(encoded.size()) == encoded
	err = candidate.get_error()
	candidate.close()
	if not complete or err not in [OK, ERR_FILE_EOF]:
		printerr("kit_zone: incomplete staged export ", staged)
		root.free()
		return 1
	err = directory.rename(staged.get_file(), out.get_file())
	if err != OK:
		printerr("kit_zone: failed export promotion ", out, ": ", error_string(err))
		root.free()
		return 1
	root.free()
	print("kit_zone: wrote ", out)
	return 0
