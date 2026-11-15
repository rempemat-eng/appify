class_name RaidRepair
extends Node2D
## A brief repair after a lost raid (docs/vision/vertical-slice.md beat 8: boards on a window, a cart on
## its side), shown while the shard lantern is dark: from the lost night until a night is held (Matt,
## 13 Nov: the square looks worse until then; core/raids.gd keeps `repairs`). Nothing is destroyed and
## nothing costs anything. The node stands at the thing's foot, so it sorts with the building or the
## actors in front of it.
##
## Drawn with the zone (scripts/art/native/town.py, from the raid's `repairs`): `spec.picture` is the
## picture, and the zone's kit.json `repairs` holds where it and its shadow go from the foot. The shadow
## lies on the ground under everyone (z -9, as a conditional prop's shadow in the zone scene). A repair
## with a `solid` (the overturned cart) has a body there, on the walls' layer, and on the low layer too
## when its picture stands under LOW_RISE texels, so feet stop at it and arrows fly over it (the rule
## tools/gen_physics.py applies to the zone's own props). A repair without one (the boards on the wall)
## has no body: it blocks no path, door or lane. Still; it never moves.

const DENSITY := 3.0
const WALLS := 1
const LOW := 16
const LOW_RISE := 64                 ## texels: tools/gen_physics.py LOW_RISE
## The blockout's look, kept only for a repair with no picture yet
const PLANK := Color("#806850")
const DARK := Color("#5a4632")

static var _kits := {}

var spec: Dictionary = {}

func _ready() -> void:
	add_to_group("raid_repair")
	var pic := String(spec.get("picture", ""))
	var entry := RaidRepair.kit_entry(pic, String(spec.get("id", "")))
	if entry.is_empty():
		return
	if entry.has("shadow"):
		var sh := Sprite2D.new()
		sh.name = "Shadow"
		sh.texture = load(pic.get_base_dir().path_join(String(entry.shadow.png))) as Texture2D
		sh.centered = false
		sh.offset = Vector2(entry.shadow.offset[0], entry.shadow.offset[1])
		sh.z_index = -9
		add_child(sh)
	var s := Sprite2D.new()
	s.name = "Picture"
	s.texture = load(pic) as Texture2D
	s.centered = false
	s.offset = Vector2(entry.offset[0], entry.offset[1])
	add_child(s)
	var solid: Variant = spec.get("solid")
	if solid is Array and (solid as Array).size() == 4:
		var body := StaticBody2D.new()
		body.name = "Body"
		body.collision_layer = WALLS | (LOW if int(entry.get("stands", 0)) < LOW_RISE else 0)
		body.collision_mask = 0
		var shape := CollisionShape2D.new()
		var rect := RectangleShape2D.new()
		rect.size = Vector2(float(solid[2]), float(solid[3])) * DENSITY
		shape.shape = rect
		# the solid is in world px; the node stands at the foot
		shape.position = (Vector2(float(solid[0]) + float(solid[2]) / 2.0, float(solid[1]) + float(solid[3]) / 2.0)) * DENSITY - position
		body.add_child(shape)
		add_child(body)

## The zone kit.json's `repairs` entry for repair `id` drawn as `picture` (res://zones/<zone>/art/<name>.png),
## or {} when there is none.
static func kit_entry(picture: String, id: String) -> Dictionary:
	if picture == "":
		return {}
	var path := picture.get_base_dir().get_base_dir().path_join("kit.json")
	if not _kits.has(path):
		var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
		var by_id := {}
		if doc is Dictionary:
			for e: Variant in (doc as Dictionary).get("repairs", []):
				if e is Dictionary:
					by_id[String(e.get("id", ""))] = e
		_kits[path] = by_id
	var e: Variant = (_kits[path] as Dictionary).get(id, {})
	if not e is Dictionary or (e as Dictionary).is_empty():
		return {}
	if picture.get_file() != String((e as Dictionary).get("png", "")):
		return {}
	return e

func _draw() -> void:
	if get_child_count() > 0:
		return
	# no picture: the blockout's flat planks, in the size the data gives
	var at: Array = spec.get("at", [0, 0])
	var size: Array = spec.get("size", [12, 12])
	var foot := float(spec.get("foot", at[1]))
	var s := Vector2(float(size[0]), float(size[1])) * DENSITY
	var r := Rect2(Vector2(0.0, (float(at[1]) - foot) * DENSITY) - s / 2.0, s)
	draw_rect(r, PLANK)
	draw_rect(Rect2(r.position, Vector2(s.x, 5)), DARK)
