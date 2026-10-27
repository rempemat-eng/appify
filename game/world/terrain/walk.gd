class_name KitWalk
extends Node
## W4: one 4-world-pixel mask for review exports and runtime collision.
## Add this node BELOW a TerrainGround, then call rebuild(), or set ground_path.
## It replaces only the prototype's generated Ground/Blocked and KitPiece/Solid
## collision layers while installed; removing it restores those original layers.
## No zone is opted in automatically. W2/W3 can install it after loading a plan.
## Coordinates below are density-3 texels: 24 per terrain cell, 12 per walk cell.

const STEP := 12
const OWNER_META := &"kit_walk_owner"
const BODY_OWNER_META := &"kit_walk_body_owner"
const BODY_LAYER_META := &"kit_walk_body_original_layer"

@export var ground_path: NodePath
## Nested prop children may omit metadata overrides when PackedScene packs the
## zone. Keep only scalar restore data on this owned node, never Node references.
@export_storage var saved_collision_layers: Dictionary = {}

var rows := PackedStringArray()
var source: TerrainGround
var _body: StaticBody2D
var _replaced: Dictionary = {}
var _queued := false
var _loaded_layers: Dictionary = {}

func _ready() -> void:
	_loaded_layers = saved_collision_layers.duplicate()
	if not ground_path.is_empty():
		source = get_node_or_null(ground_path) as TerrainGround
	elif get_parent() is TerrainGround:
		source = get_parent() as TerrainGround
	if source != null:
		# A child becomes ready before its TerrainGround parent. The parent defers
		# its prototype body, so install after that deferred initialization.
		await get_tree().process_frame
		if is_inside_tree():
			_queue_rebuild()

func _exit_tree() -> void:
	_disconnect_layers()
	if is_instance_valid(_body):
		_body.collision_layer = 0
		_body.queue_free()
	_restore_legacy()

func _queue_rebuild() -> void:
	if not _queued:
		_queued = true
		_rebuild_deferred.call_deferred()

func _rebuild_deferred() -> void:
	_queued = false
	if is_inside_tree() and is_instance_valid(source):
		rebuild(source)

## Rebuild after painting cells/tiers or moving/adding/removing a piece. Layer
## resource-change notifications also queue a refresh, but set_cell is batched by
## Godot, so authoring tools should call this explicitly at their edit boundary.
## Reject invalid geometry before replacing the existing collision.
func rebuild(ground: TerrainGround = null) -> bool:
	if ground == null:
		ground = source
	if ground == null or not ground.is_inside_tree():
		return false
	var owner := _ground_owner(ground)
	if owner != null and owner != self:
		return false
	var next := derive(ground)
	if next.is_empty():
		return false
	if source != ground:
		if source != null:
			_loaded_layers = {}
		_restore_legacy()
		if is_instance_valid(_body):
			_body.free()
		_body = null
		_disconnect_layers()
		source = ground
	source.set_meta(OWNER_META, get_instance_id())
	rows = next
	for layer in [source.get_cells_layer(), source.get_tiers_layer()]:
		if layer != null and not layer.changed.is_connected(_queue_rebuild):
			layer.changed.connect(_queue_rebuild)
	if not is_instance_valid(_body):
		_body = StaticBody2D.new()
		_body.name = "WalkBlocked"
		_body.collision_layer = 1
		_body.collision_mask = 0
		source.add_child(_body, false, Node.INTERNAL_MODE_BACK)
	for child in _body.get_children():
		child.free()
	for rect in merge_blocked(rows):
		var shape := RectangleShape2D.new()
		shape.size = Vector2(rect.size * STEP)
		var collider := CollisionShape2D.new()
		collider.shape = shape
		collider.position = Vector2(rect.position * STEP) + shape.size * 0.5
		_body.add_child(collider)
	var legacy := [source.get_node_or_null("Blocked")]
	for piece in source.pieces():
		legacy.append(piece.get_node_or_null("Solid"))
	for node in _replaced.keys():
		if not legacy.has(node):
			_release_legacy(node)
	for node in legacy:
		_disable_legacy(node)
	_snapshot_layers()
	_loaded_layers = {}
	return true

func _disconnect_layers() -> void:
	if not is_instance_valid(source):
		return
	for layer in [source.get_cells_layer(), source.get_tiers_layer()]:
		if layer != null and layer.changed.is_connected(_queue_rebuild):
			layer.changed.disconnect(_queue_rebuild)

static func _ground_owner(ground: TerrainGround) -> KitWalk:
	# Metadata is serialized by PackedScene: save only scalar runtime tokens.
	# A token from a saved scene cannot reserve its newly loaded copy, even if
	# the original owner is still alive, because the ground must also match.
	var token = ground.get_meta(OWNER_META, 0)
	if typeof(token) != TYPE_INT or token == 0 or not is_instance_id_valid(token):
		return null
	var candidate = instance_from_id(token)
	if candidate is KitWalk and is_instance_valid(candidate.source) and candidate.source == ground:
		return candidate
	return null

func _disable_legacy(node: Node) -> void:
	if node is StaticBody2D and node != _body:
		# A transferred body may already be disabled by another KitWalk. Keep its
		# true original layer on the body, independent of either rebuild order.
		if not node.has_meta(BODY_LAYER_META):
			var original = _loaded_layers.get(_layer_path(node), node.collision_layer)
			node.set_meta(BODY_LAYER_META, original if typeof(original) == TYPE_INT else node.collision_layer)
		_replaced[node] = node.get_meta(BODY_LAYER_META)
		node.set_meta(BODY_OWNER_META, get_instance_id())
		node.collision_layer = 0

func _layer_path(node: Node) -> String:
	return str(get_path_to(node)) if is_inside_tree() and node.is_inside_tree() else ""

func _snapshot_layers() -> void:
	saved_collision_layers = {}
	for node in _replaced:
		if is_instance_valid(node) and node.get_meta(BODY_OWNER_META, 0) == get_instance_id():
			var path := _layer_path(node)
			if not path.is_empty():
				saved_collision_layers[path] = _replaced[node]

func _release_legacy(node) -> void:
	# An earlier owner must not reactivate or overwrite the new owner's body.
	if is_instance_valid(node) and node.get_meta(BODY_OWNER_META, 0) == get_instance_id():
		node.collision_layer = _replaced[node]
		node.remove_meta(BODY_OWNER_META)
		node.remove_meta(BODY_LAYER_META)
	_replaced.erase(node)

func _restore_legacy() -> void:
	for node in _replaced.keys():
		_release_legacy(node)
	saved_collision_layers = {}
	if is_instance_valid(source) and source.get_meta(OWNER_META, 0) == get_instance_id():
		source.remove_meta(OWNER_META)

## Plain-text format consumed by gen_zone.py: rectangular . / # rows, final LF.
func walk_text() -> String:
	return "\n".join(rows) + "\n" if not rows.is_empty() else ""

func write_walk(path: String) -> Error:
	if rows.is_empty():
		return ERR_UNCONFIGURED
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return FileAccess.get_open_error()
	file.store_string(walk_text())
	file.close()
	return OK

## Read metadata, not sprite bounds. Empty Cells retain the prototype's walkable
## behaviour. A precise collision box takes precedence over the coarser footprint;
## footprint-only pieces are supported without inventing a collision from artwork.
static func derive(ground: TerrainGround) -> PackedStringArray:
	var out := PackedStringArray()
	var kit := ground.kit
	var cells := ground.get_cells_layer()
	if kit == null or cells == null or kit.cell <= 0 or kit.cell % STEP != 0:
		return out
	var size := ground.grid_size
	if size.x <= 0 or size.y <= 0:
		return out
	var factor := int(kit.cell / STEP)
	var fine_size := size * factor
	var blocked := PackedByteArray()
	blocked.resize(fine_size.x * fine_size.y)
	var tier := PackedInt32Array()
	tier.resize(size.x * size.y)
	# Tile custom data must reflect set_cell in this same authoring step.
	cells.update_internals()
	var has_walkable := cells.tile_set != null and cells.tile_set.get_custom_data_layer_by_name("walkable") >= 0
	for y in size.y:
		for x in size.x:
			var at := Vector2i(x, y)
			var mid := ground.material_at(at)
			tier[y * size.x + x] = ground.tier_at(at)
			var tile := cells.get_cell_tile_data(at)
			var walkable := true
			if tile != null and has_walkable:
				walkable = bool(tile.get_custom_data("walkable"))
			elif mid != 0:
				walkable = bool(kit.by_material.get(mid, {}).get("walkable", false))
			if not walkable:
				_fill(blocked, fine_size, Rect2(Vector2(at * kit.cell), Vector2.ONE * kit.cell), true)
	# South faces are derived from tier drops, as TerrainGround._derive / compose.
	if kit.face_material != 0 and not bool(kit.by_material.get(kit.face_material, {}).get("walkable", false)):
		for x in size.x:
			for y in size.y - 1:
				var top := tier[y * size.x + x]
				var below := tier[(y + 1) * size.x + x]
				if top > below:
					for dy in range(1, kit.face_cells * (top - below) + 1):
						if y + dy < size.y and tier[(y + dy) * size.x + x] < top:
							_fill(blocked, fine_size, Rect2(Vector2(x, y + dy) * kit.cell, Vector2.ONE * kit.cell), true)
	var decks := {}
	var pieces := ground.pieces()
	for piece in pieces:
		var data: Dictionary = piece.data()
		var deck = data.get("deck")
		if deck is Array and deck.size() == 4:
			var box := _piece_rect(ground, piece, Rect2(deck[0], deck[1], deck[2], deck[3]))
			for y in range(maxi(0, floori(box.position.y / kit.cell)), mini(size.y, ceili(box.end.y / kit.cell))):
				for x in range(maxi(0, floori(box.position.x / kit.cell)), mini(size.x, ceili(box.end.x / kit.cell))):
					var cell := Rect2(Vector2(x, y) * kit.cell, Vector2.ONE * kit.cell)
					if box.intersection(cell).get_area() >= kit.cell * kit.cell * 0.25:
						decks[Vector2i(x, y)] = true
						_fill(blocked, fine_size, cell, false)
	# A tier's side or back edge also needs a barrier unless a deck connects it.
	# Rasterise the prototype's thin edge wall to the same conservative walk grid.
	var terrain_mask := blocked.duplicate()
	for y in size.y:
		for x in size.x:
			var at := Vector2i(x, y)
			for nb in [at + Vector2i.RIGHT, at + Vector2i.DOWN]:
				if nb.x >= size.x or nb.y >= size.y or decks.has(at) or decks.has(nb):
					continue
				if tier[y * size.x + x] == tier[nb.y * size.x + nb.x]:
					continue
				if _terrain_blocked(terrain_mask, fine_size, at * factor) or _terrain_blocked(terrain_mask, fine_size, nb * factor):
					continue
				if nb.x > x:
					_fill(blocked, fine_size, Rect2((x + 1) * kit.cell - 2, y * kit.cell, 4, kit.cell), true)
				else:
					_fill(blocked, fine_size, Rect2(x * kit.cell, (y + 1) * kit.cell - 2, kit.cell, 4), true)
	# Solids are applied after deck exceptions, so a crate on a bridge remains solid.
	for piece in pieces:
		var data: Dictionary = piece.data()
		if not bool(data.get("blocks_move", false)):
			continue
		var collision = data.get("collision")
		if collision is Array and collision.size() == 4:
			_fill(blocked, fine_size, _piece_rect(ground, piece, Rect2(collision[0], collision[1], collision[2], collision[3])), true)
		else:
			for cell in data.get("footprint", []):
				_fill(blocked, fine_size, _piece_rect(ground, piece, Rect2(Vector2(cell[0], cell[1]) * kit.cell, Vector2.ONE * kit.cell)), true)
	for y in fine_size.y:
		var row := ""
		for x in fine_size.x:
			row += "#" if blocked[y * fine_size.x + x] else "."
		out.append(row)
	return out

static func _terrain_blocked(mask: PackedByteArray, size: Vector2i, at: Vector2i) -> bool:
	return bool(mask[at.y * size.x + at.x])

static func _piece_rect(ground: Node2D, piece: Node2D, rect: Rect2) -> Rect2:
	var transform := ground.global_transform.affine_inverse() * piece.global_transform
	return transform * rect

static func _fill(mask: PackedByteArray, size: Vector2i, rect: Rect2, value: bool) -> void:
	if rect.size.x <= 0 or rect.size.y <= 0:
		return
	for y in range(maxi(0, floori(rect.position.y / STEP)), mini(size.y, ceili(rect.end.y / STEP))):
		for x in range(maxi(0, floori(rect.position.x / STEP)), mini(size.x, ceili(rect.end.x / STEP))):
			mask[y * size.x + x] = int(value)

## gen_zone.py's merge: equal horizontal runs extend downward, ordered by y,x.
## The output partitions exactly the blocked cells; no rectangles overlap.
static func merge_blocked(mask: PackedStringArray) -> Array[Rect2i]:
	var rects: Array[Rect2i] = []
	var open := {}
	for y in mask.size() + 1:
		var row: String = mask[y] if y < mask.size() else ""
		var runs := {}
		var x := 0
		while x < row.length():
			if row[x] == "#":
				var start := x
				while x < row.length() and row[x] == "#":
					x += 1
				runs[Vector2i(start, x)] = true
			else:
				x += 1
		for run in open:
			if not runs.has(run):
				rects.append(Rect2i(run.x, open[run], run.y - run.x, y - open[run]))
		var next := {}
		for run in runs:
			next[run] = open.get(run, y)
		open = next
	rects.sort_custom(func(a: Rect2i, b: Rect2i) -> bool: return a.position.y < b.position.y or (a.position.y == b.position.y and a.position.x < b.position.x))
	return rects
