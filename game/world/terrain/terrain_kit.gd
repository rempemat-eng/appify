@tool
class_name TerrainKit
extends RefCounted
## The built terrain kit (game/kit/terrain/manifest.json, written by scripts/art/kit/build.py) as
## the textures terrain.gdshader reads: the fills in a grid, the transitions stacked, the palette
## and a small table of priorities and pairs. Loaded once and shared (`TerrainKit.shared()`).

const MANIFEST := "res://kit/terrain/manifest.json"
const DIR := "res://kit/terrain/"
const FILL_COLS := 4
const MAX_MATERIALS := 64

static var _shared: TerrainKit

var manifest: Dictionary
var cell := 24
var period := 768
var variants := 4
var profiles := 3
var atlas_cols := 64
var pair_rows := 1
var fills_tex: ImageTexture
var over_tex: ImageTexture
var lut_tex: Texture2D
var meta_tex: ImageTexture
var tileset: TileSet
var curves: Array = []         ## per profile, the outline's displacement at the 24 texels of a cell edge
var decals := {}               ## decal id -> {"tex": ImageTexture, "anchor": Vector2i}
var dressing := {}             ## transition id -> its dressing block
var pairs := {}                ## Vector2i(upper material id, lower material id or 0 for any) -> transition id
var by_id := {}          ## piece id -> material entry
var by_material := {}    ## material id -> material entry

static func shared() -> TerrainKit:
	if _shared == null:
		_shared = TerrainKit.new()
		_shared._load()
	return _shared

static func reload() -> TerrainKit:
	_shared = null
	return shared()

func _image(name: String) -> Image:
	var tex := load(DIR + name) as Texture2D
	assert(tex != null, "terrain kit: missing " + name)
	var img := tex.get_image()
	if img.is_compressed():
		img.decompress()
	img.convert(Image.FORMAT_RGBA8)
	return img

func _load() -> void:
	manifest = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
	cell = int(manifest.cell)
	period = int(manifest.period)
	variants = int(manifest.variants)
	profiles = int(manifest.profiles)
	atlas_cols = int(manifest.atlas_cols)
	var mats: Array = manifest.materials
	var rows := maxi(1, int(ceil(float(mats.size()) / FILL_COLS)))
	var fills := Image.create_empty(FILL_COLS * period, rows * period, false, Image.FORMAT_RGBA8)
	var meta := Image.create_empty(MAX_MATERIALS, MAX_MATERIALS + 1, false, Image.FORMAT_RGBA8)
	meta.fill(Color(0, 0, 0, 1))
	for slot in mats.size():
		var m: Dictionary = mats[slot]
		var mid := int(m.material_id)
		assert(mid > 0 and mid < MAX_MATERIALS, "terrain kit: material id out of range")
		by_id[m.id] = m
		by_material[mid] = m
		var f := _image(m.fill)
		fills.blit_rect(f, Rect2i(Vector2i.ZERO, f.get_size()), Vector2i((slot % FILL_COLS) * period, (slot / FILL_COLS) * period))
		meta.set_pixel(mid, 0, Color8(int(m.priority), slot, 1, 255))
	var trs: Array = manifest.transitions
	for t in trs:
		pair_rows = maxi(pair_rows, _image(t.png).get_height() / cell)
	var over := Image.create_empty(atlas_cols * cell, maxi(1, trs.size()) * pair_rows * cell, false, Image.FORMAT_RGBA8)
	for k in trs.size():
		var t: Dictionary = trs[k]
		var o := _image(t.png)
		over.blit_rect(o, Rect2i(Vector2i.ZERO, o.get_size()), Vector2i(0, k * pair_rows * cell))
		var upper := int(by_id[t.upper].material_id)
		var lower := 0 if t.lower == "*" else int(by_id[t.lower].material_id)
		meta.set_pixel(lower, 1 + upper, Color8(k + 1, 0, 0, 255))
	curves = manifest.get("curves", [])
	var lut_img := _image(manifest.lut)
	for did in manifest.get("decals", {}):
		var d: Dictionary = manifest.decals[did]
		var src := _image(d.png)
		var rgba := Image.create_empty(src.get_width(), src.get_height(), false, Image.FORMAT_RGBA8)
		for y in src.get_height():
			for x in src.get_width():
				var c := src.get_pixel(x, y)
				if c.a8 > 0:
					var col := lut_img.get_pixel(c.r8 + 256 * c.g8, 0)
					col.a = 1.0
					rgba.set_pixel(x, y, col)
		decals[did] = {"tex": ImageTexture.create_from_image(rgba), "anchor": Vector2i(int(d.anchor[0]), int(d.anchor[1]))}
	for t in trs:
		dressing[t.id] = t.get("dressing")
		var lo := 0 if t.lower == "*" else int(by_id[t.lower].material_id)
		pairs[Vector2i(int(by_id[t.upper].material_id), lo)] = t.id
	fills_tex = ImageTexture.create_from_image(fills)
	over_tex = ImageTexture.create_from_image(over)
	meta_tex = ImageTexture.create_from_image(meta)
	lut_tex = ImageTexture.create_from_image(_image(manifest.lut))
	tileset = load(DIR + str(manifest.tileset)) as TileSet

## The atlas coordinates of a material's tile in materials.tres (for painting the Cells layer).
func atlas_coords(piece_id: String) -> Vector2i:
	var mats: Array = manifest.materials
	for i in mats.size():
		if mats[i].id == piece_id:
			return Vector2i(i, 0)
	return Vector2i(-1, -1)

## The transition laid where `upper` meets `lower` (material ids), or "" when none is drawn.
func pair_for(upper: int, lower: int) -> String:
	return pairs.get(Vector2i(upper, lower), pairs.get(Vector2i(upper, 0), ""))

func priority(mid: int) -> int:
	return int(by_material[mid].priority) if by_material.has(mid) else 0

func material_id(piece_id: String) -> int:
	return int(by_id[piece_id].material_id) if by_id.has(piece_id) else 0
