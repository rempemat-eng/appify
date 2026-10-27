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

static func _valid_rows(rows: Array, width: int, height: int) -> bool:
	if rows.size() != height:
		return false
	for row in rows:
		if not row is String or row.length() != width:
			return false
	return true

## Returns an unattached scene, suitable for PackedScene.pack without entering a tree.
static func scene_from_plan(plan: Dictionary) -> Node2D:
	var kit := TerrainKit.shared()
	if not plan.get("zone") is String or not plan.get("legend") is Dictionary or not plan.get("rows") is Array:
		return null
	var rows: Array = plan.get("rows", [])
	if rows.is_empty() or not rows[0] is String or rows[0].is_empty():
		return null
	var size := Vector2i(rows[0].length(), rows.size())
	if not _valid_rows(rows, size.x, size.y):
		return null
	if plan.get("coordinate_space", "texels") not in ["texels", "cells"]:
		return null
	for field in ["tiers", "flow", "variants"]:
		if plan.has(field) and not _valid_rows(plan[field], size.x, size.y):
			return null
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
		var ps := load("res://kit/props/%s.tscn" % entry.piece) as PackedScene
		if ps == null:
			root.free()
			return null
		var inst := ps.instantiate() as KitPiece
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
		var packed := load(plan.gameplay_from) as PackedScene
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
						child.set_meta(&"kit_zone_inherited", _door_entry(child, {}, kit.cell))
				if name_ in ["Spawns", "Doors"]:
					inherited_ids[name_] = []
					for child in node.get_children():
						inherited_ids[name_].append(String(child.name))
					for id in plan.get("gameplay_removed", {}).get(name_, []):
						var removed := node.get_node_or_null(NodePath(String(id)))
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
		var marker := spawns.get_node_or_null(NodePath(String(id))) as Marker2D
		if marker == null:
			marker = Marker2D.new()
			marker.name = String(id).validate_node_name()
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
		var prior := doors.get_node_or_null(NodePath(String(entry.id).validate_node_name()))
		if prior != null:
			prior.free()
		var door = load("res://world/door.gd").new()
		door.name = String(entry.id).validate_node_name()
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
		var id = marker.get_meta(&"kit_zone_id", String(marker.name))
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
				if container == null or container.get_node_or_null(NodePath(id)) == null:
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
		entry["id"] = String(door.name)
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
	var root := scene_from_plan(_read(path))
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
	if out == "":
		out = fallback
	var file := FileAccess.open(out, FileAccess.WRITE)
	if file == null:
		root.free()
		return 1
	file.store_string(canonical(plan))
	file.close()
	root.free()
	print("kit_zone: wrote ", out)
	return 0
