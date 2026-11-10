extends SceneTree
## Lossless kit plan <-> scene authoring (W2, docs/world-editor.md).
## --plan=<json> [--out=<tscn>] or --export=<tscn> [--out=<json>], or
## --new=<zone> [--size=40x23] [--ground=lawn] [--lab=1] [--note=<text>] for an empty plan and its scene.
## Legacy piece `at` and spawns are Godot texels. Explicit coordinate_space="cells"
## uses logical terrain cells for those fields; no guessing from their magnitudes.
## Door `rect` is always in cells, with existing plan keys id/to/spawn/if.
## Flow is a hidden logical TileMapLayer with a `flow` custom-data glyph per cell.
## Facing/stage are authored metadata; no new facing art, flow animation or rules ship.
## The source template is saved IN the scene, so export needs no input/output sidecar.
## Actors (10 Nov): `actors` holds what a quest needs in the zone, each {id, kind, at, ...}:
## an interactable (speaker, verb, radius, marker_height), a villager (an interactable with a
## cast body: character, facing, work), a restore site (restore), a camp (camp, enemies as
## positions, scene) and any actor scene (scene, with `set` property overrides). `if` wraps the
## actor in a Conditional. `at` and enemy positions use the plan's coordinate space; a radius is
## always texels. Nodes under Actors that are none of these cannot be held by a plan:
## unexported_actors() lists them, and the dock's Validate reports them.

const PLAN_META := &"kit_zone_plan"
const ENTRY_META := &"kit_zone_entry"
const EXPLICIT_META := &"kit_zone_explicit"
const GAMEPLAY_IDS_META := &"kit_zone_gameplay_ids"
const ACTOR_KINDS := ["interactable", "villager", "restore", "camp", "scene"]
const INTERACTABLE := "res://world/interactable.gd"
const RESTORE := "res://world/restore_site.gd"
const CAMP := "res://world/camp.gd"
const CONDITIONAL := "res://world/conditional.gd"
const VILLAGER := "res://world/villager.gd"
const ENEMY := "res://actors/enemy.tscn"
const TALK_RADIUS := 30.0
const MARKER_HEIGHT := 40.0

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2, a.find("=") - 2)] = a.substr(a.find("=") + 1)
	if args.has("editor-lifecycle-runtime"):
		var report: Dictionary = await _lifecycle_runtime(args)
		print("WORLD_EDITOR_LIFECYCLE_RUNTIME ", JSON.stringify(report))
		quit(0 if bool(report.get("ok", false)) else 1)
		return
	var code := 1
	if args.has("new"):
		code = _new(args)
	elif args.has("plan"):
		code = _build(args.plan, args.get("out", ""))
	elif args.has("export"):
		code = _export(args.export, args.get("out", ""))
	else:
		printerr("kit_zone: --plan=<json>, --export=<tscn> or --new=<zone>")
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

## Own a newly built branch without flattening instanced scenes: an instance's own children stay
## with their scene, so the zone stores the instance and its overrides, not copies.
static func _own_new(node: Node, root: Node) -> void:
	node.owner = root
	if not String(node.scene_file_path).is_empty():
		return
	for child in node.get_children():
		_own_new(child, root)

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
	if not plan.get("actors", []) is Array:
		return "actors must be an array"
	var actor_ids := {}
	for i in plan.get("actors", []).size():
		var actor_problem := actor_error(plan.actors[i], unit)
		if not actor_problem.is_empty():
			return "actors[%s]%s" % [i, actor_problem]
		if actor_ids.has(plan.actors[i].id):
			return "actors[%s].id repeats '%s'" % [i, plan.actors[i].id]
		actor_ids[plan.actors[i].id] = true
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

## An instance that stays an instance when the zone is saved. A plain instantiate() forgets which
## values came from the instanced scene, so the zone file stored them all again as its own (an
## enemy's script, layers and motion mode, a piece's script and id) and would keep those copies
## when the instanced scene later changed.
static func instance(packed: PackedScene) -> Node:
	return packed.instantiate(PackedScene.GEN_EDIT_STATE_INSTANCE)

## What is wrong with one `actors` entry ("" when sound), as a suffix for its path.
static func actor_error(entry: Variant, unit: float = 1.0) -> String:
	if not entry is Dictionary:
		return " must be an object"
	if not entry.get("id") is String or entry.id.is_empty() or entry.id.validate_node_name() != entry.id or entry.id in [".", ".."]:
		return ".id must be a nonempty valid node name"
	if not entry.get("kind") is String or entry.kind not in ACTOR_KINDS:
		return ".kind must be one of %s" % ", ".join(ACTOR_KINDS)
	if not _numbers(entry.get("at"), 2, unit):
		return ".at must contain two finite coordinates"
	var needs := {"interactable": ["speaker"], "villager": ["speaker", "character"], "restore": ["restore"], "camp": ["camp"], "scene": ["scene"]}
	for key in needs[entry.kind]:
		if not entry.get(key) is String or entry[key].is_empty():
			return ".%s must be a nonempty string" % key
	for key in ["speaker", "verb", "facing", "scene"]:
		if entry.has(key) and not entry[key] is String:
			return ".%s must be a string" % key
	for key in ["radius", "marker_height"]:
		if entry.has(key) and (typeof(entry[key]) not in [TYPE_INT, TYPE_FLOAT] or not is_finite(float(entry[key])) or float(entry[key]) <= 0.0):
			return ".%s must be a positive number" % key
	if entry.has("work") and not entry.work is bool:
		return ".work must be a boolean"
	if entry.has("if") and not entry["if"] is Dictionary:
		return ".if must be a condition object"
	if entry.has("set") and not entry["set"] is Dictionary:
		return ".set must be an object of property values"
	if entry.kind == "camp":
		if not entry.get("enemies") is Array or entry.enemies.is_empty():
			return ".enemies must be a nonempty array of positions"
		for spot in entry.enemies:
			if not _numbers(spot, 2, unit):
				return ".enemies must contain finite coordinate pairs"
	if entry.kind in ["camp", "scene"] and entry.has("scene") and not ResourceLoader.exists(entry.scene, "PackedScene"):
		return ".scene is not a scene in the project: %s" % entry.scene
	return ""

## One actor from its plan entry, unattached (null when its scene cannot be instanced). Its
## entry is kept on it so an unchanged actor exports byte for byte.
static func actor_node(entry: Dictionary, unit: float = 1.0) -> Node2D:
	var at := Vector2(entry.at[0], entry.at[1]) * unit
	var node: Node2D
	match String(entry.kind):
		"camp":
			var packed := load(String(entry.get("scene", ENEMY))) as PackedScene
			if packed == null:
				return null
			node = Node2D.new()
			node.set_script(load(CAMP))
			node.set("camp_id", entry.camp)
			var count := 1
			for spot in entry.enemies:
				var enemy := instance(packed) as Node2D
				if enemy == null:
					node.free()
					return null
				enemy.name = "Enemy%d" % count
				count += 1
				enemy.position = Vector2(spot[0], spot[1]) * unit - at
				node.add_child(enemy)
		"scene":
			var packed := load(String(entry.scene)) as PackedScene
			node = instance(packed) as Node2D if packed != null else null
			if node == null:
				return null
			var overrides: Dictionary = entry.get("set", {})
			for key in overrides:
				node.set(key, overrides[key])
		_:
			var area := Area2D.new()
			area.set_script(load(RESTORE if entry.kind == "restore" else INTERACTABLE))
			if entry.kind == "restore":
				area.set("restore_id", entry.restore)
			if entry.has("speaker"):
				area.set("speaker_id", entry.speaker)
			if entry.has("verb"):
				area.set("verb", entry.verb)
			if entry.has("marker_height"):
				area.set("marker_height", float(entry.marker_height))
			var shape := CollisionShape2D.new()
			shape.name = "Shape"
			var circle := CircleShape2D.new()
			circle.radius = float(entry.get("radius", TALK_RADIUS))
			shape.shape = circle
			area.add_child(shape)
			if entry.kind == "villager":
				var body := AnimatedSprite2D.new()
				body.name = "Body"
				body.centered = false
				body.offset = Vector2(-80, -136)       # the cast's foot pivot (docs/godot.md, "The cast")
				body.set_script(load(VILLAGER))
				body.set("character", entry.character)
				if entry.has("facing"):
					body.set("facing_at_rest", entry.facing)
				if entry.has("work"):
					body.set("work", entry.work)
				area.add_child(body)
				var post := StaticBody2D.new()
				post.name = "Post"
				post.collision_mask = 0
				var post_shape := CollisionShape2D.new()
				post_shape.name = "Shape"
				var post_circle := CircleShape2D.new()
				post_circle.radius = 5.0
				post_shape.shape = post_circle
				post.add_child(post_shape)
				area.add_child(post)
			node = area
	node.name = entry.id
	node.position = at
	node.set_meta(ENTRY_META, entry.duplicate(true))
	return node

## An actor with its `if` condition stands inside a Conditional (world/conditional.gd).
static func actor_holder(entry: Dictionary, unit: float = 1.0) -> Node2D:
	var node := actor_node(entry, unit)
	if node == null or not entry.has("if"):
		return node
	var holder := Node2D.new()
	holder.name = "If_" + String(entry.id)
	holder.set_script(load(CONDITIONAL))
	holder.set("only_if", JSON.stringify(entry["if"]))
	holder.add_child(node)
	return holder

static func _script_path(node: Node) -> String:
	var script := node.get_script() as Script
	return script.resource_path if script != null else ""

## The plan entry of one node under Actors, or {} when it is not a kind a plan can hold.
static func actor_entry(node: Node, unit: float = 1.0, offset: Vector2 = Vector2.ZERO) -> Dictionary:
	if not node is Node2D:
		return {}
	var kept: Variant = node.get_meta(ENTRY_META, {})
	var entry: Dictionary = kept.duplicate(true) if kept is Dictionary else {}
	var path := _script_path(node)
	var kind := ""
	if path == RESTORE:
		kind = "restore"
	elif path == INTERACTABLE:
		kind = "interactable"
		var cast := node.get_node_or_null("Body")
		if cast != null and _script_path(cast) == VILLAGER:
			kind = "villager"
	elif path == CAMP:
		kind = "camp"
	elif not String(node.scene_file_path).is_empty():
		kind = "scene"
	if kind.is_empty():
		return {}
	entry["id"] = String(node.name)
	entry["kind"] = kind
	entry["at"] = _position_value(node.position + offset, entry.get("at", []) if entry.get("at") is Array else [], unit)
	match kind:
		"camp":
			entry["camp"] = node.get("camp_id")
			var scenes := {}
			var spots := []
			var old: Array = entry.get("enemies", []) if entry.get("enemies") is Array else []
			for child in node.get_children():
				if not child is Node2D or String(child.scene_file_path).is_empty():
					return {}
				scenes[String(child.scene_file_path)] = true
				var before: Array = old[spots.size()] if spots.size() < old.size() and old[spots.size()] is Array else []
				spots.append(_position_value(child.position + node.position + offset, before, unit))
			if scenes.size() != 1:
				return {}                           # an empty camp or mixed enemies: not this simple form
			entry["enemies"] = spots
			if entry.has("scene") or scenes.keys()[0] != ENEMY:
				entry["scene"] = scenes.keys()[0]
		"scene":
			entry["scene"] = String(node.scene_file_path)
			if entry.get("set") is Dictionary:
				for key in entry["set"]:
					entry["set"][key] = node.get(key)
		_:
			if kind == "restore":
				entry["restore"] = node.get("restore_id")
				# RestoreSite fills an empty speaker in at run time: that default is not authored
				if entry.has("speaker") or String(node.get("speaker_id")) not in ["", "restore_" + String(node.get("restore_id"))]:
					entry["speaker"] = node.get("speaker_id")
			else:
				entry["speaker"] = node.get("speaker_id")
			if entry.has("verb") or String(node.get("verb")) != "Talk":
				entry["verb"] = node.get("verb")
			if entry.has("marker_height") or not is_equal_approx(float(node.get("marker_height")), MARKER_HEIGHT):
				entry["marker_height"] = _number_value(float(node.get("marker_height")), entry.get("marker_height"))
			var shape := node.get_node_or_null("Shape") as CollisionShape2D
			if shape != null and shape.shape is CircleShape2D and (entry.has("radius") or not is_equal_approx(shape.shape.radius, TALK_RADIUS)):
				entry["radius"] = _number_value(shape.shape.radius, entry.get("radius"))
			if kind == "villager":
				var cast := node.get_node("Body")
				entry["character"] = cast.get("character")
				if entry.has("facing") or String(cast.get("facing_at_rest")) != "S":
					entry["facing"] = cast.get("facing_at_rest")
				if entry.has("work") or bool(cast.get("work")):
					entry["work"] = cast.get("work")
			else:
				for key in ["character", "facing", "work"]:
					entry.erase(key)
	return entry

## Keep an unchanged JSON number as it was written.
static func _number_value(now: float, original: Variant) -> Variant:
	if typeof(original) in [TYPE_INT, TYPE_FLOAT] and is_equal_approx(float(original), now):
		return original
	return now

## Every authored actor as [entry, ...] and, in `skipped`, the paths of the Actors children no
## plan entry can hold (they would be lost when the scene is rebuilt from its plan). Nodes copied
## in by gameplay_from stay with their source scene, as inherited spawns and doors do.
static func _actor_entries(root: Node, unit: float, skipped: Array) -> Array:
	var out := []
	var actors := root.get_node_or_null("Actors")
	for child in actors.get_children() if actors != null else []:
		if not bool(child.get_meta(EXPLICIT_META, true)):
			continue
		if _script_path(child) == CONDITIONAL and child is Node2D:
			var condition: Variant = JSON.parse_string(String(child.get("only_if")))
			if child.get_child_count() == 0 or not condition is Dictionary:
				skipped.append(String(root.get_path_to(child)))
				continue
			for inner in child.get_children():
				var inner_entry := actor_entry(inner, unit, child.position)
				if inner_entry.is_empty():
					skipped.append(String(root.get_path_to(inner)))
				else:
					inner_entry["if"] = condition
					out.append(inner_entry)
			continue
		var entry := actor_entry(child, unit)
		if entry.is_empty():
			skipped.append(String(root.get_path_to(child)))
		else:
			entry.erase("if")
			out.append(entry)
	return out

static func unexported_actors(root: Node) -> Array:
	var skipped := []
	_actor_entries(root, 1.0, skipped)
	return skipped

## A door from its plan entry (rect in cells), unattached.
static func door_node(entry: Dictionary, cell: int) -> Area2D:
	var door: Area2D = load("res://world/door.gd").new()
	var r: Array = entry.rect
	door.position = Vector2(r[0] + r[2] / 2.0, r[1] + r[3] / 2.0) * cell
	door.set("target_zone", entry.get("to", entry.get("target_zone", "")))
	door.set("target_spawn", entry.get("spawn", entry.get("target_spawn", "start")))
	if entry.has("if"):
		door.set("only_if", JSON.stringify(entry["if"]))
	door.set_meta(ENTRY_META, entry.duplicate(true))
	door.set_meta(EXPLICIT_META, true)
	var shape := CollisionShape2D.new()
	shape.name = "Shape"
	var rectangle := RectangleShape2D.new()
	rectangle.size = Vector2(r[2], r[3]) * cell
	shape.shape = rectangle
	door.add_child(shape)
	return door

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
		var node := instance(ps)
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
	var actors := _container(root, "Actors")
	actors.y_sort_enabled = true
	for entry in plan.get("actors", []):
		var holder := actor_holder(entry, unit)
		if holder == null:
			root.free()
			return null
		for stale in [_child_with_id(actors, entry.id), _child_with_id(actors, "If_" + String(entry.id))]:
			if stale != null:
				stale.free()                       # an explicit actor replaces the inherited one of its name
		actors.add_child(holder)
		_own_new(holder, root)
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
		var door := door_node(entry, kit.cell)
		door.name = _storage_name(doors, entry.id)
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

static func plan_from_scene(root: Node2D, fallback: Dictionary = {}, include_inherited_spawns: bool = false) -> Dictionary:
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
	var actor_entries := _actor_entries(root, unit, [])
	if plan.has("actors") or not actor_entries.is_empty():
		plan["actors"] = actor_entries
	var spawns := {}
	var spawn_node := root.get_node_or_null("Spawns")
	for marker in spawn_node.get_children() if spawn_node != null else []:
		if not marker is Marker2D:
			continue
		if not include_inherited_spawns and not bool(marker.get_meta(EXPLICIT_META, true)) and marker.position == marker.get_meta(&"kit_zone_inherited", marker.position):
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

## Write a plan as canonical JSON, staged beside its destination and promoted only when the whole
## document is on disk. Returns "" or what went wrong; a failed stage stays for inspection.
static func write_plan(plan: Dictionary, out: String) -> String:
	var problem := plan_error(plan)
	if not problem.is_empty():
		return "invalid plan: " + problem
	# Keep the previous document intact until a complete candidate is closed and checked.
	var directory := DirAccess.open(out.get_base_dir() if out.get_base_dir() != "" else ".")
	if directory == null:
		return "cannot open the folder of %s" % out
	var staged := out + ".tmp"
	var document := canonical(plan)
	var file := FileAccess.open(staged, FileAccess.WRITE)
	if file == null:
		return "cannot write %s" % staged
	file.store_string(document)
	file.flush()
	var err := file.get_error()
	file.close()
	if err != OK:
		return "failed staged write %s: %s" % [staged, error_string(err)]
	# Reopen after close to catch incomplete output, including delayed write failures.
	# Failed stages remain beside the destination for inspection/recovery.
	var candidate := FileAccess.open(staged, FileAccess.READ)
	if candidate == null:
		return "cannot reopen %s" % staged
	var encoded := document.to_utf8_buffer()
	var complete := candidate.get_length() == encoded.size() and candidate.get_buffer(encoded.size()) == encoded
	err = candidate.get_error()
	candidate.close()
	if not complete or err not in [OK, ERR_FILE_EOF]:
		return "incomplete staged export %s" % staged
	err = directory.rename(staged.get_file(), out.get_file())
	if err != OK:
		return "failed export promotion %s: %s" % [out, error_string(err)]
	return ""

func _export(path: String, out: String) -> int:
	var scene := load(path) as PackedScene
	if scene == null:
		return 1
	var root := scene.instantiate() as Node2D
	var fallback := "res://kit/zones/%s.json" % root.get("zone_id")
	var plan := plan_from_scene(root, _read(fallback) if not root.has_meta(PLAN_META) and FileAccess.file_exists(fallback) else {})
	for lost in unexported_actors(root):
		printerr("kit_zone: warning: ", lost, " is not a kind the plan holds; it is not exported")
	root.free()
	if out == "":
		out = fallback
	var problem := write_plan(plan, out)
	if not problem.is_empty():
		printerr("kit_zone: ", path, ": ", problem)
		return 1
	print("kit_zone: wrote ", out)
	return 0

## An empty zone to start authoring in: a plan of one ground material and its scene. Refuses to
## replace an existing plan or scene.
func _new(args: Dictionary) -> int:
	var zone := String(args["new"])
	var pattern := RegEx.new()
	pattern.compile("^[a-z][a-z0-9_]*$")
	if pattern.search(zone) == null:
		printerr("kit_zone: --new needs a zone id of lower-case letters, digits and underscores")
		return 1
	var size := String(args.get("size", "40x23")).split("x")
	if size.size() != 2 or not size[0].is_valid_int() or not size[1].is_valid_int() or int(size[0]) < 1 or int(size[1]) < 1 or int(size[0]) > 400 or int(size[1]) > 400:
		printerr("kit_zone: --size is <cells across>x<cells down>, 1 to 400 each")
		return 1
	var ground := String(args.get("ground", "lawn"))
	if TerrainKit.shared().atlas_coords(ground).x < 0:
		printerr("kit_zone: --ground '%s' is not a built terrain material" % ground)
		return 1
	var plan_path := "res://kit/zones/%s.json" % zone
	var scene_path := String(args.get("out", "res://zones/%s/%s.tscn" % [zone, zone]))
	if FileAccess.file_exists(plan_path) or FileAccess.file_exists(scene_path):
		printerr("kit_zone: %s or %s exists already" % [plan_path, scene_path])
		return 1
	var rows := []
	for y in int(size[1]):
		rows.append(".".repeat(int(size[0])))
	var plan := {"zone": zone, "legend": {".": ground}, "rows": rows}
	if String(args.get("lab", "0")) in ["1", "true"]:
		plan["lab"] = true
	if args.has("note"):
		plan["note"] = String(args.note)
	var problem := write_plan(plan, plan_path)
	if not problem.is_empty():
		printerr("kit_zone: ", problem)
		return 1
	print("kit_zone: wrote ", plan_path)
	return _build(plan_path, scene_path)


# Optional private acceptance contract. These checks do not prove physical path
# isolation: the enclosing receiver must verify the disposable project, original
# source, private user roots, exact inputs and owned output paths before launch.
# Bootstrap with existing --plan/--out CLI using lifecycle_probe_plan()'s data;
# it creates the NEW named scene below in the disposable project only.
const LIFECYCLE_ZONE := "editor_lifecycle_probe"
const LIFECYCLE_SCENE := "res://zones/editor_lifecycle_probe/editor_lifecycle_probe.tscn"
const LIFECYCLE_PLAN := "res://kit/zones/editor_lifecycle_probe.json"
const LIFECYCLE_PNG := "res://zones/editor_lifecycle_probe/ground_baked.png"
const LIFECYCLE_SIDECAR := "res://zones/editor_lifecycle_probe/ground_baked.json"
const LIFECYCLE_WALK := "res://zones/editor_lifecycle_probe/walk.txt"

static func lifecycle_context(phase: String) -> Dictionary:
	var duty := OS.get_environment("MYGAME_EDITOR_LIFECYCLE_ROOT").simplify_path().trim_suffix("/")
	var declared := OS.get_environment("MYGAME_EDITOR_LIFECYCLE_PROJECT").simplify_path().trim_suffix("/")
	var original := OS.get_environment("MYGAME_EDITOR_LIFECYCLE_SOURCE").simplify_path().trim_suffix("/")
	var source_sha := OS.get_environment("MYGAME_EDITOR_LIFECYCLE_SHA")
	var case_id := OS.get_environment("MYGAME_EDITOR_LIFECYCLE_CASE")
	var project := ProjectSettings.globalize_path("res://").simplify_path().trim_suffix("/")
	var userdata := ProjectSettings.globalize_path("user://").simplify_path().trim_suffix("/")
	var sha_pattern := RegEx.new()
	sha_pattern.compile("^[0-9a-f]{40}$")
	var case_pattern := RegEx.new()
	case_pattern.compile("^[0-9a-f]{32}$")
	if phase not in ["author", "reopen", "runtime"] or OS.get_environment("MYGAME_EDITOR_LIFECYCLE") != "1":
		return {"ok": false, "message": "Explicit private lifecycle context is required."}
	if not duty.is_absolute_path() or duty in ["", "/"] or not original.is_absolute_path() or original in ["", "/"] or sha_pattern.search(source_sha) == null or case_pattern.search(case_id) == null:
		return {"ok": false, "message": "Owned duty, original source and exact source SHA are required."}
	if project != declared or not project.begins_with(duty + "/") or not userdata.begins_with(duty + "/") or duty == original or duty.begins_with(original + "/") or project == original or project.begins_with(original + "/"):
		return {"ok": false, "message": "Lifecycle must run in the declared disposable project/private user roots outside original source."}
	var evidence := duty.path_join("evidence/editor_lifecycle")
	var report := evidence.path_join(phase + ".json")
	if FileAccess.file_exists(report) or DirAccess.make_dir_recursive_absolute(evidence) != OK:
		return {"ok": false, "message": "Fresh writable lifecycle evidence is required; old receipts are never overwritten."}
	return {"ok": true, "phase": phase, "duty": duty, "project": project, "userdata": userdata,
		"source_sha": source_sha, "case_id": case_id, "evidence": evidence, "report": report,
		"owned_outputs": [evidence, ProjectSettings.globalize_path(LIFECYCLE_SCENE),
			ProjectSettings.globalize_path(LIFECYCLE_PLAN), ProjectSettings.globalize_path(LIFECYCLE_PNG),
			ProjectSettings.globalize_path(LIFECYCLE_SIDECAR), ProjectSettings.globalize_path(LIFECYCLE_WALK)],
		"generated_private_only": [project.path_join(".godot"), ProjectSettings.globalize_path(LIFECYCLE_PNG + ".import")]}

static func lifecycle_probe_plan() -> Dictionary:
	var plan := _read("res://test/fixtures/editor_persistence.json").duplicate(true)
	if plan.is_empty(): return {}
	plan["zone"] = LIFECYCLE_ZONE
	plan["lab"] = true
	plan["bake"] = true
	plan["coordinate_space"] = "texels"
	return plan

static func lifecycle_read(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null: return {}
	if file.get_length() > 262144:
		file.close()
		return {}
	var parser := JSON.new()
	var code := parser.parse(file.get_as_text())
	file.close()
	return parser.data if code == OK and parser.data is Dictionary else {}

static func lifecycle_write(path: String, value: Dictionary) -> bool:
	var text := canonical(value)
	if FileAccess.file_exists(path) or text.to_utf8_buffer().size() > 262144: return false
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null: return false
	file.store_string(text)
	file.flush()
	var code := file.get_error()
	file.close()
	return code == OK

static func lifecycle_finish(context: Dictionary, result: Dictionary) -> Dictionary:
	var failures: Array = result.get("failures", [])
	result["ok"] = failures.is_empty()
	result["pid"] = OS.get_process_id()
	result["finished_unix"] = Time.get_unix_time_from_system()
	result["scope"] = "Private candidate-lab functional evidence; no approved kit, actual biome, art or gameplay acceptance."
	if not bool(context.get("ok", false)):
		result["ok"] = false
		return result
	result["phase"] = context.phase
	result["source_sha"] = context.source_sha
	result["context"] = context
	if not lifecycle_write(context.report, result):
		failures.append("Lifecycle report could not be written to its fresh owned path.")
		result["ok"] = false
	return result

static func lifecycle_prior(context: Dictionary, phase: String) -> Dictionary:
	var prior := lifecycle_read(String(context.evidence).path_join(phase + ".json"))
	if not bool(prior.get("ok", false)) or prior.get("phase") != phase or prior.get("source_sha") != context.source_sha or int(prior.get("pid", 0)) in [0, OS.get_process_id()]:
		return {}
	var previous_context: Dictionary = prior.get("context", {})
	for key in ["duty", "project", "source_sha", "case_id"]:
		if previous_context.get(key) != context.get(key): return {}
	return prior

func _lifecycle_runtime(args: Dictionary) -> Dictionary:
	var context := lifecycle_context("runtime")
	var result := {"ok": false, "failures": [], "started_unix": Time.get_unix_time_from_system()}
	var failures: Array = result.failures
	if not bool(context.get("ok", false)):
		failures.append(context.get("message", "Invalid lifecycle context."))
		return lifecycle_finish(context, result)
	if args.size() != 1 or args.get("editor-lifecycle-runtime") != "1" or Engine.is_editor_hint():
		failures.append("Runtime verification requires its sole explicit flag and a fresh non-editor process.")
		return lifecycle_finish(context, result)
	var author := lifecycle_prior(context, "author")
	var reopened := lifecycle_prior(context, "reopen")
	var expected_path := String(context.evidence).path_join("expected-plan.json")
	var expected := lifecycle_read(expected_path)
	if author.is_empty() or reopened.is_empty() or expected.is_empty() or int(author.pid) == int(reopened.pid) or reopened.get("author_pid") != author.pid or FileAccess.get_sha256(expected_path) != author.get("expected_plan_sha256"):
		failures.append("Successful distinct-process author/reopen receipts and exact expected plan are required.")
		return lifecycle_finish(context, result)
	if reopened.get("author_report_sha256") != FileAccess.get_sha256(String(context.evidence).path_join("author.json")) or reopened.get("expected_plan_sha256") != author.get("expected_plan_sha256"):
		failures.append("Prior receipt/expected-plan hash chain changed.")
		return lifecycle_finish(context, result)
	for key in ["scene", "png", "sidecar", "walk", "export"]:
		var paths := {"scene": LIFECYCLE_SCENE, "png": LIFECYCLE_PNG, "sidecar": LIFECYCLE_SIDECAR, "walk": LIFECYCLE_WALK, "export": LIFECYCLE_PLAN}
		if not FileAccess.file_exists(paths[key]) or FileAccess.get_sha256(paths[key]) != reopened.get(key + "_sha256"):
			failures.append("Reopened bake artifact changed or is absent: " + key)
	if not failures.is_empty(): return lifecycle_finish(context, result)
	var packed := ResourceLoader.load(LIFECYCLE_SCENE, "PackedScene", ResourceLoader.CACHE_MODE_IGNORE) as PackedScene
	if packed == null:
		failures.append("Saved named scene could not be loaded from disk.")
		return lifecycle_finish(context, result)
	var scene := packed.instantiate() as Node2D
	if scene == null:
		failures.append("The saved probe did not instantiate as Node2D.")
		return lifecycle_finish(context, result)
	var ground := scene.get_node_or_null("Ground") as TerrainGround
	# Inspect SERIALIZED binding before tree-ready callbacks or any rebuild/repair.
	if ground == null or ground.baked == null or ground.baked.resource_path != LIFECYCLE_PNG:
		failures.append("Fresh saved scene has no matching baked texture binding; bake was not persisted.")
		scene.free()
		return lifecycle_finish(context, result)
	if not ground.lab or canonical(plan_from_scene(scene)) != canonical(expected):
		failures.append("Fresh runtime scene changed lab/authoring data.")
		scene.free()
		return lifecycle_finish(context, result)
	root.add_child(scene)
	await process_frame
	await physics_frame
	await physics_frame
	await process_frame
	var walk := ground.get_node_or_null("KitWalk") as KitWalk
	if walk == null or walk.rows.is_empty() or walk.walk_text() != FileAccess.get_file_as_string(LIFECYCLE_WALK) or not ground.showing_baked():
		failures.append("Persisted walk node/rows or baked presentation did not restore without repair.")
	else:
		var player_scene := load("res://actors/player.tscn") as PackedScene
		if player_scene == null:
			failures.append("Existing Player scene is unavailable.")
			scene.queue_free()
			await process_frame
			return lifecycle_finish(context, result)
		# Builtin typing keeps the CLI script load independent of autoload-dependent Player.
		var player := player_scene.instantiate() as CharacterBody2D
		if player == null or player.get_script() != load("res://actors/player.gd"):
			failures.append("Existing Player could not be instantiated with its exact script.")
			if player != null: player.free()
			scene.queue_free()
			await process_frame
			return lifecycle_finish(context, result)
		player.set("input_enabled", false)
		if player.get("input_enabled") != false:
			failures.append("Existing Player input was not disabled before tree insertion.")
			player.free()
			scene.queue_free()
			await process_frame
			return lifecycle_finish(context, result)
		player.position = Vector2(108, 156)
		scene.add_child(player)
		await physics_frame
		await physics_frame
		var blocked := player.move_and_collide(Vector2(0, -72))
		var blocked_collider: Node = null
		if blocked != null: blocked_collider = blocked.get_collider() as Node
		result["blocked_probe"] = {"collision": blocked != null, "position": [player.position.x, player.position.y],
			"collider": String(blocked_collider.get_path()) if blocked_collider != null else ""}
		if blocked == null or player.position.y <= 84: failures.append("Existing Player crossed the saved bench collision.")
		player.position = Vector2(24, 156)
		var clear := player.move_and_collide(Vector2(0, -72))
		result["clear_probe"] = {"collision": clear != null, "position": [player.position.x, player.position.y]}
		result["player_layers"] = {"layer": player.collision_layer, "mask": player.collision_mask, "input_enabled": player.get("input_enabled")}
		if clear != null or not player.position.is_equal_approx(Vector2(24, 84)): failures.append("Existing Player could not traverse the saved clear lane.")
		result["walk_rows"] = walk.rows
		result["baked_binding"] = ground.baked.resource_path
		result["collision_authority"] = "Existing compiled KitPiece index and packed Solid; raw bench collision metadata remains unclassified."
	scene.queue_free()
	await process_frame
	return lifecycle_finish(context, result)
