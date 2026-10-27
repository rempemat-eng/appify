@tool
class_name TerrainGround
extends Node2D
## A zone's ground from the terrain kit (docs/world-editor.md). The child TileMapLayer `Cells`
## (tile set: res://kit/terrain/materials.tres) holds one material per 24-texel cell and is what
## the editor paints; this node draws the picture with terrain.gdshader, live in the editor and in
## the game, and gives the validator and the walk mask the cells' metadata.

@export var grid_size := Vector2i(40, 23):  ## cells across and down (the zone's extent)
	set(v):
		grid_size = v
		_rebuild()
@export var lab := false  ## a lab or prototype zone: the dock may place pieces not yet through the library gate
@export var show_cells := false:  ## show the logical layer's swatches over the picture (editing aid)
	set(v):
		show_cells = v
		_apply_cells_visibility()

var kit: TerrainKit
var _cells_img: Image
var _cells_tex: ImageTexture
var _mat: ShaderMaterial
var _picture: Node2D     ## draws the ground with the shader; internal, never saved in the scene
var _ground := PackedInt32Array()   ## the derived ground: painted materials plus faces under raised tiers
var _tiers := PackedInt32Array()    ## the painted tiers
var _shadow_img: Image
var _shadow_tex: ImageTexture

func _ready() -> void:
	kit = TerrainKit.shared()
	var cells := get_cells_layer()
	if cells != null:
		cells.tile_set = kit.tileset
		if not cells.changed.is_connected(_rebuild):
			cells.changed.connect(_rebuild)
	var tl := get_tiers_layer()
	if tl != null:
		tl.tile_set = kit.tiers_tileset
		tl.self_modulate = Color(1, 1, 1, 0.0)
		if not tl.changed.is_connected(_rebuild):
			tl.changed.connect(_rebuild)
	if _picture == null:
		_picture = Node2D.new()
		_picture.name = "Picture"
		_picture.draw.connect(func() -> void:
			_picture.draw_rect(Rect2(Vector2.ZERO, Vector2(size_px())), Color.WHITE))
		add_child(_picture, false, Node.INTERNAL_MODE_FRONT)
	if _dressing() == null:
		var d := TerrainDressing.new()
		d.name = "Dressing"
		add_child(d, false, Node.INTERNAL_MODE_BACK)   # internal: rebuilt from the cells on every load, never saved
	_apply_cells_visibility()
	_rebuild()
	rebuild_shadows.call_deferred()
	if not Engine.is_editor_hint():
		_build_blocked.call_deferred()

func get_cells_layer() -> TileMapLayer:
	return get_node_or_null("Cells") as TileMapLayer

## The optional child TileMapLayer `Tiers` (tile set res://kit/terrain/tiers.tres): a height tier per
## cell; faces are derived under every south rim (ground-rules.md 1).
func get_tiers_layer() -> TileMapLayer:
	return get_node_or_null("Tiers") as TileMapLayer

## The painted tier of a cell (0 where none is painted).
func tier_at(c: Vector2i) -> int:
	var t := get_tiers_layer()
	if t == null or c.x < 0 or c.y < 0 or c.x >= grid_size.x or c.y >= grid_size.y:
		return 0
	var ac := t.get_cell_atlas_coords(c)
	return maxi(0, ac.x)

## The ground actually drawn at a cell: the painted material, or the face material where a face
## falls (compose.derive). 0 outside.
func ground_at(c: Vector2i) -> int:
	if c.x < 0 or c.y < 0 or c.x >= grid_size.x or c.y >= grid_size.y or _ground.is_empty():
		return 0
	return _ground[c.y * grid_size.x + c.x]

func ground_tier(c: Vector2i) -> int:
	if c.x < 0 or c.y < 0 or c.x >= grid_size.x or c.y >= grid_size.y or _tiers.is_empty():
		return 0
	return _tiers[c.y * grid_size.x + c.x]

func paint_tier(c: Vector2i, tier: int) -> void:
	var t := get_tiers_layer()
	if t == null:
		return
	if tier <= 0:
		t.erase_cell(c)
	else:
		t.set_cell(c, 0, Vector2i(tier, 0))

func _derive() -> void:
	var n := grid_size.x * grid_size.y
	_ground.resize(n)
	_tiers.resize(n)
	for y in grid_size.y:
		for x in grid_size.x:
			_ground[y * grid_size.x + x] = material_at(Vector2i(x, y))
			_tiers[y * grid_size.x + x] = tier_at(Vector2i(x, y))
	if kit.face_material == 0:
		return
	for x in grid_size.x:
		for y in grid_size.y - 1:
			var t0 := _tiers[y * grid_size.x + x]
			var t1 := _tiers[(y + 1) * grid_size.x + x]
			if t0 > t1:
				for k in range(1, kit.face_cells * (t0 - t1) + 1):
					if y + k < grid_size.y and _tiers[(y + k) * grid_size.x + x] < t0:
						_ground[(y + k) * grid_size.x + x] = kit.face_material

func _apply_cells_visibility() -> void:
	var cells := get_cells_layer()
	if cells != null:
		cells.self_modulate = Color(1, 1, 1, 0.45 if show_cells else 0.0)

## The material id at a cell (0 outside or unpainted).
func material_at(c: Vector2i) -> int:
	var cells := get_cells_layer()
	if cells == null or c.x < 0 or c.y < 0 or c.x >= grid_size.x or c.y >= grid_size.y:
		return 0
	# by the tile's atlas column (materials.tres lays one material per column, in manifest order):
	# set_cell is seen at once, where get_cell_tile_data waits for the layer's next update
	var ac := cells.get_cell_atlas_coords(c)
	var mats: Array = kit.manifest.materials
	return int(mats[ac.x].material_id) if ac.x >= 0 and ac.x < mats.size() else 0

## The cells as an array of rows of material ids (the JSON plan's form).
func cell_rows() -> Array:
	var rows := []
	for y in grid_size.y:
		var row := PackedInt32Array()
		row.resize(grid_size.x)
		for x in grid_size.x:
			row[x] = material_at(Vector2i(x, y))
		rows.append(row)
	return rows

## Paint a material on the logical layer by its piece id ("" erases).
func paint_cell(c: Vector2i, piece_id: String) -> void:
	var cells := get_cells_layer()
	if piece_id == "":
		cells.erase_cell(c)
	else:
		cells.set_cell(c, 0, kit.atlas_coords(piece_id))

func size_px() -> Vector2i:
	return grid_size * (kit.cell if kit != null else 24)

func _rebuild() -> void:
	if not is_inside_tree() or kit == null:
		return
	if _cells_img == null or _cells_img.get_size() != grid_size:
		_cells_img = Image.create_empty(maxi(1, grid_size.x), maxi(1, grid_size.y), false, Image.FORMAT_RGBA8)
		_cells_tex = null
	_derive()
	for y in grid_size.y:
		for x in grid_size.x:
			_cells_img.set_pixel(x, y, Color8(_ground[y * grid_size.x + x], _tiers[y * grid_size.x + x], 0, 255))
	if _cells_tex == null:
		_cells_tex = ImageTexture.create_from_image(_cells_img)
	else:
		_cells_tex.update(_cells_img)
	if _mat == null:
		_mat = ShaderMaterial.new()
		_mat.shader = preload("res://world/terrain/terrain.gdshader")
		_mat.set_shader_parameter("fills_tex", kit.fills_tex)
		_mat.set_shader_parameter("over_tex", kit.over_tex)
		_mat.set_shader_parameter("lut_tex", kit.lut_tex)
		_mat.set_shader_parameter("meta_tex", kit.meta_tex)
		_mat.set_shader_parameter("noise_tex", kit.noise_tex)
		_mat.set_shader_parameter("period", kit.period)
		_mat.set_shader_parameter("variants", kit.variants)
		_mat.set_shader_parameter("fill_cols", TerrainKit.FILL_COLS)
		_mat.set_shader_parameter("cell", kit.cell)
		_mat.set_shader_parameter("profiles", kit.profiles)
		_mat.set_shader_parameter("atlas_cols", kit.atlas_cols)
		_mat.set_shader_parameter("pair_rows", kit.pair_rows)
		_picture.material = _mat
	if _shadow_tex == null:
		_shadow_img = Image.create_empty(maxi(1, size_px().x), maxi(1, size_px().y), false, Image.FORMAT_R8)
		_shadow_tex = ImageTexture.create_from_image(_shadow_img)
		_mat.set_shader_parameter("shadow_tex", _shadow_tex)
	_mat.set_shader_parameter("cells_tex", _cells_tex)
	_mat.set_shader_parameter("grid", grid_size)
	_picture.queue_redraw()
	var dressing := _dressing() as TerrainDressing
	if dressing != null:
		dressing.ground = self
		dressing.queue_redraw()

## The pieces standing on this ground: every KitPiece under the zone (the ground's parent).
func pieces() -> Array:
	var out := []
	var stack: Array = [get_parent()] if get_parent() != null else []
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		if n is KitPiece:
			out.append(n)
		for c in n.get_children():
			stack.append(c)
	return out

## Cast shadows on the ground from the pieces' ellipses, as ramp steps the shader applies (the
## house shadow: core two tones down, its outer 2 world px one tone; scripts/art/kit/compose.py
## draws the same).
func rebuild_shadows() -> void:
	if _shadow_img == null:
		return
	_shadow_img.fill(Color(0, 0, 0, 1))
	var sz := size_px()
	for p in pieces():
		var sh: Dictionary = p.shadow()
		if sh.is_empty():
			continue
		if sh.has("mask"):
			var mk: Image = sh.mask
			var at: Vector2i = sh.at
			for my in mk.get_height():
				var y: int = at.y + my
				if y < 0 or y >= sz.y:
					continue
				for mx in mk.get_width():
					var x: int = at.x + mx
					if x < 0 or x >= sz.x:
						continue
					var v := mk.get_pixel(mx, my).r8
					if v > 0 and v > _shadow_img.get_pixel(x, y).r8:
						_shadow_img.set_pixel(x, y, Color8(v, 0, 0, 255))
			continue
		var c: Vector2 = sh.centre
		var r: Vector2 = sh.radii
		var rc := r - Vector2(6, 6)
		for y in range(maxi(0, int(floor(c.y - r.y))), mini(sz.y, int(ceil(c.y + r.y)) + 1)):
			for x in range(maxi(0, int(floor(c.x - r.x))), mini(sz.x, int(ceil(c.x + r.x)) + 1)):
				var dx := x + 0.5 - c.x
				var dy := y + 0.5 - c.y
				var q := (dx / r.x) * (dx / r.x) + (dy / r.y) * (dy / r.y)
				if q > 1.0:
					continue
				var v := 1
				if rc.x > 0 and rc.y > 0 and (dx / rc.x) * (dx / rc.x) + (dy / rc.y) * (dy / rc.y) <= 1.0:
					v = 2
				if v > _shadow_img.get_pixel(x, y).r8:
					_shadow_img.set_pixel(x, y, Color8(v, 0, 0, 255))
	_shadow_tex.update(_shadow_img)

## The walk mask from the cells: a cell whose material is not walkable is solid, merged into
## rectangles (rows of runs, joined downwards where they line up) on the walls layer.
func blocked_rects() -> Array:
	var rects := []
	var open := {}
	for y in grid_size.y:
		var runs := []
		var x := 0
		while x < grid_size.x:
			if _blocked_cell(Vector2i(x, y)):
				var x0 := x
				while x < grid_size.x and _blocked_cell(Vector2i(x, y)):
					x += 1
				runs.append(Vector2i(x0, x))
			else:
				x += 1
		var next := {}
		for r in runs:
			if open.has(r):
				var rr: Rect2i = open[r]
				rr.size.y += 1
				next[r] = rr
			else:
				next[r] = Rect2i(r.x, y, r.y - r.x, 1)
		for r in open:
			if not next.has(r):
				rects.append(open[r])
		open = next
	for r in open:
		rects.append(open[r])
	return rects

var _decks := {}   ## cells a piece's deck makes walkable (bridges, stairs), set by _build_blocked

func _blocked_cell(c: Vector2i) -> bool:
	if _decks.has(c):
		return false
	var mid := ground_at(c)
	return mid != 0 and not bool(kit.by_material[mid].walkable)

## Cells the pieces' decks cover (by at least a quarter, as kit_rules.deck_cells).
func deck_cells() -> Dictionary:
	var out := {}
	for p in pieces():
		var d = p.data().get("deck")
		if d == null:
			continue
		var x0: float = p.position.x + d[0]
		var y0: float = p.position.y + d[1]
		var x1: float = x0 + d[2]
		var y1: float = y0 + d[3]
		var c := kit.cell
		for cy in range(maxi(0, floori(y0 / c)), mini(grid_size.y, ceili(y1 / c))):
			for cx in range(maxi(0, floori(x0 / c)), mini(grid_size.x, ceili(x1 / c))):
				var ox := maxf(0.0, minf(x1, (cx + 1) * c) - maxf(x0, cx * c))
				var oy := maxf(0.0, minf(y1, (cy + 1) * c) - maxf(y0, cy * c))
				if ox * oy >= c * c * 0.25:
					out[Vector2i(cx, cy)] = true
	return out

func _build_blocked() -> void:
	_decks = deck_cells()
	var old := get_node_or_null("Blocked")
	if old != null:
		old.free()
	var body := StaticBody2D.new()
	body.name = "Blocked"
	body.collision_mask = 0
	add_child(body)
	for r in blocked_rects():
		var shape := RectangleShape2D.new()
		shape.size = Vector2(r.size * kit.cell)
		var cs := CollisionShape2D.new()
		cs.shape = shape
		cs.position = Vector2(r.position * kit.cell) + shape.size / 2.0
		body.add_child(cs)
	# a tier's edge is a wall where two walkable cells of different tiers meet (no deck between)
	for y in grid_size.y:
		for x in grid_size.x:
			var c := Vector2i(x, y)
			for nb in [Vector2i(x + 1, y), Vector2i(x, y + 1)]:
				if nb.x >= grid_size.x or nb.y >= grid_size.y or _blocked_cell(c) or _blocked_cell(nb):
					continue
				if ground_tier(c) == ground_tier(nb) or _decks.has(c) or _decks.has(nb):
					continue
				var shape := RectangleShape2D.new()
				var cs := CollisionShape2D.new()
				if nb.x > x:
					shape.size = Vector2(4, kit.cell)
					cs.position = Vector2((x + 1) * kit.cell, y * kit.cell + kit.cell / 2.0)
				else:
					shape.size = Vector2(kit.cell, 4)
					cs.position = Vector2(x * kit.cell + kit.cell / 2.0, (y + 1) * kit.cell)
				cs.shape = shape
				body.add_child(cs)



func _dressing() -> TerrainDressing:
	for c in get_children(true):
		if c is TerrainDressing:
			return c
	return null
