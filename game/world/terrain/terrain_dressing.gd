@tool
class_name TerrainDressing
extends Node2D
## Edge dressing over a TerrainGround (scripts/art/kit/dressing.py, the same placement): at most one
## decal (a tuft, hanging blades, a pebble) per cell edge between two materials whose transition is
## dressed, chosen and placed by a hash of the cell edge and seated on its lumped outline.

var ground: TerrainGround

func _ready() -> void:
	ground = get_parent() as TerrainGround

static func mul32(a: int, b: int) -> int:
	# (a * b) mod 2^32 for a, b < 2^32 without overflowing a 64-bit int
	return (a * (b & 0xFFFF) + (((a * (b >> 16)) & 0xFFFF) << 16)) & 0xFFFFFFFF

static func profile(a: int, b: int, c: int, m: int, n: int) -> int:
	var h := mul32(a, 0x9E3779B1) ^ mul32(b, 0x85EBCA77) ^ mul32(c, 0xC2B2AE3D) ^ mul32(m, 0x27D4EB2F)
	h = h ^ (h >> 16)
	h = mul32(h, 0x7FEB352D)
	h = h ^ (h >> 15)
	return h % n

static func dress_hash(a: int, b: int, c: int, m: int) -> int:
	var h := mul32(a, 0x1B873593) ^ mul32(b, 0xCC9E2D51) ^ mul32(c, 0x38B34AE5) ^ mul32(m, 0xA1C9B2F7)
	h = h ^ (h >> 16)
	h = mul32(h, 0x85EBCA6B)
	h = h ^ (h >> 13)
	h = mul32(h, 0xC2B2AE35)
	h = h ^ (h >> 16)
	return h

## Every decal: [decal id, Vector2i anchor position in texels], in draw order.
func placements() -> Array:
	var out := []
	if ground == null or ground.kit == null:
		return out
	var kit := ground.kit
	var cell := kit.cell
	var half := cell / 2
	var gs := ground.grid_size
	for cy in gs.y:
		for cx in gs.x:
			var a := ground.ground_at(Vector2i(cx, cy))
			var ta := ground.ground_tier(Vector2i(cx, cy))
			for horiz in [true, false]:
				var nb := Vector2i(cx, cy + 1) if horiz else Vector2i(cx + 1, cy)
				if nb.x >= gs.x or nb.y >= gs.y:
					continue
				var b := ground.ground_at(nb)
				var tb := ground.ground_tier(nb)
				if (a == b and ta == tb) or a == 0 or b == 0:
					continue
				var ea := ta * 256 + kit.priority(a)
				var eb := tb * 256 + kit.priority(b)
				var up := a if ea > eb else b
				var lo := b if ea > eb else a
				var tu := ta if ea > eb else tb
				var pair := kit.pair_for(up, lo, ta != tb)
				if pair == "" or kit.dressing.get(pair) == null:
					continue
				var dr: Dictionary = kit.dressing[pair]
				var key := Vector3i(cx, cy + 1, 1) if horiz else Vector3i(cx + 1, cy, 0)
				var mk := up + 64 * tu
				var h := dress_hash(key.x, key.y, key.z, mk)
				if h % 1000 >= int(float(dr.density) * 1000.0):
					continue
				var t := ((h >> 10) % 17) - 8
				var p := profile(key.x, key.y, key.z, mk, kit.profiles)
				var disp := float(kit.curves[p][t + half])
				var side := ""
				var pos := Vector2i.ZERO
				if horiz:
					var line := (cy + 1) * cell
					var south := b == up and tb == tu
					side = "south" if south else "north"
					var bound := line + disp if south else line - disp
					pos = Vector2i(cx * cell + half + t, int(floor(bound + 0.5)))
				else:
					var line := (cx + 1) * cell
					var east := b == up and tb == tu
					side = "side"
					var bound := line + disp if east else line - disp
					pos = Vector2i(int(floor(bound + 0.5)), cy * cell + half + t)
				var choices: Array = dr.get(side, [])
				if choices.is_empty():
					continue
				out.append([choices[(h >> 20) % choices.size()], pos])
	return out

func _draw() -> void:
	if ground == null or ground.kit == null:
		return
	for pl in placements():
		var d: Dictionary = ground.kit.decals[pl[0]]
		draw_texture(d.tex, Vector2(pl[1] - d.anchor))
