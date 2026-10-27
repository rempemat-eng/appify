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

## The piece's cast shadow on the ground: centre and radii in texels (zone space), or {} for none.
func shadow() -> Dictionary:
	var s = data().get("shadow")
	if s == null:
		return {}
	return {"centre": position + Vector2(s.dir[0], s.dir[1]), "radii": Vector2(s.size[0], s.size[1])}
