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
@export var show_cells := false:  ## show the logical layer's swatches over the picture (editing aid)
	set(v):
		show_cells = v
		_apply_cells_visibility()

var kit: TerrainKit
var _cells_img: Image
var _cells_tex: ImageTexture
var _mat: ShaderMaterial

func _ready() -> void:
	kit = TerrainKit.shared()
	var cells := get_cells_layer()
	if cells != null:
		cells.tile_set = kit.tileset
		if not cells.changed.is_connected(_rebuild):
			cells.changed.connect(_rebuild)
	_apply_cells_visibility()
	_rebuild()

func get_cells_layer() -> TileMapLayer:
	return get_node_or_null("Cells") as TileMapLayer

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
	for y in grid_size.y:
		for x in grid_size.x:
			_cells_img.set_pixel(x, y, Color8(material_at(Vector2i(x, y)), 0, 0, 255))
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
		_mat.set_shader_parameter("period", kit.period)
		_mat.set_shader_parameter("variants", kit.variants)
		_mat.set_shader_parameter("fill_cols", TerrainKit.FILL_COLS)
		_mat.set_shader_parameter("cell", kit.cell)
		_mat.set_shader_parameter("profiles", kit.profiles)
		_mat.set_shader_parameter("atlas_cols", kit.atlas_cols)
		_mat.set_shader_parameter("pair_rows", kit.pair_rows)
		material = _mat
	_mat.set_shader_parameter("cells_tex", _cells_tex)
	_mat.set_shader_parameter("grid", grid_size)
	queue_redraw()

func _draw() -> void:
	if kit != null:
		draw_rect(Rect2(Vector2.ZERO, Vector2(size_px())), Color.WHITE)
