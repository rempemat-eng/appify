@tool
class_name KitPiece
extends Node2D
## A placed piece from the library (game/kit/props/<id>.tscn, written by scripts/art/kit/props.py).
## Its origin is its foot on the soft grid; `variant` picks another of the piece's pictures. The
## ground's shadow pass, the validator and the dock read the piece's data from index.json.

const INDEX := "res://kit/props/index.json"

static var _index: Dictionary

@export var piece_id := ""
@export var variant := "":
	set(v):
		variant = v
		_apply_variant()

static func index() -> Dictionary:
	if _index.is_empty():
		_index = JSON.parse_string(FileAccess.get_file_as_string(INDEX))
	return _index

func data() -> Dictionary:
	return index().get(piece_id, {})

func _enter_tree() -> void:
	set_notify_local_transform(true)
	_notify_ground()

func _exit_tree() -> void:
	_notify_ground(true)

func _notification(what: int) -> void:
	if what == NOTIFICATION_LOCAL_TRANSFORM_CHANGED:
		_notify_ground()

## Native edits bypass the dock's operations; notify the same ground on membership
## and local-position changes, using the index's existing painted-piece authority.
func _notify_ground(exiting: bool = false) -> void:
	if not is_inside_tree() or not bool(data().get("painted", false)):
		return
	var props := get_parent()
	var zone := props.get_parent() if props != null else null
	if zone == null or zone.get_node_or_null("Props") != props:
		return
	var ground := zone.get_node_or_null("Ground")
	if ground != null and ground.is_inside_tree() and ground.is_node_ready() and ground.has_method("_rebuild"):
		ground.call("_rebuild", self if exiting else null)

func _ready() -> void:
	add_to_group("kit_piece")
	_apply_variant()

func _apply_variant() -> void:
	if variant == "" or not is_inside_tree():
		return
	var d := data()
	var vs: Dictionary = d.get("variants", {})
	if not vs.has(variant):
		push_warning("KitPiece %s: no variant '%s'" % [piece_id, variant])
		return
	var sprite := get_node_or_null("Sprite") as Sprite2D
	if sprite != null:
		sprite.texture = load(vs[variant].png)
		sprite.offset = -Vector2(vs[variant].foot[0], vs[variant].foot[1])

## A piece painted into a baked ground (a fall, log steps) hides its picture there: the bake drew it.
func set_ground_baked(on: bool) -> void:
	var sprite := get_node_or_null("Sprite") as Sprite2D
	if sprite != null and bool(data().get("painted", false)):
		sprite.visible = not on

static var _masks := {}

## The piece's cast shadow on the ground, or {} for none: an ellipse ("centre", "radii", texels in
## zone space) or a mask from the crown ("mask": Image of ramp steps, "at": its top left).
func shadow() -> Dictionary:
	var s = data().get("shadow")
	if s == null:
		return {}
	if s.has("mask"):
		var png: String = s.mask.png
		if not _masks.has(png):
			var img := (load(png) as Texture2D).get_image()
			if img.is_compressed():
				img.decompress()
			img.convert(Image.FORMAT_L8)
			_masks[png] = img
		return {"mask": _masks[png], "at": Vector2i(int(position.x) + int(s.mask.offset[0]), int(position.y) + int(s.mask.offset[1]))}
	return {"centre": position + Vector2(s.dir[0], s.dir[1]), "radii": Vector2(s.size[0], s.size[1])}
