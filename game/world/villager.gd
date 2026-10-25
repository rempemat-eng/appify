class_name Villager
extends CastSprite
## A villager drawn from the cast (assets/characters/<id>): idles (or works, when `work` is set)
## facing `facing_at_rest`, and turns to the player and talks with a small gesture loop while the
## player stands within `talk_radius`. Only looks: the quest triggers stay on the parent
## Interactable.

@export var character := ""
@export var facing_at_rest := "S"
@export var work := false
@export var talk_radius := 40.0 * 3.0       ## world px times DENSITY

func _ready() -> void:
	if character == "" or not load_character(character):
		return
	play_clip(_rest_clip(), facing_at_rest, true)

func _rest_clip() -> String:
	return "work" if work and has_clip("work") else "idle"

func _process(delta: float) -> void:
	if manifest.is_empty():
		return
	var player := get_tree().get_first_node_in_group("player") as Node2D
	var near := player != null and player.global_position.distance_to(global_position) < talk_radius
	if near and has_clip("talk"):
		play_clip("talk", CastSprite.facing_for(player.global_position - global_position, facing))
	else:
		play_clip(_rest_clip(), facing_at_rest)
	advance(delta)
