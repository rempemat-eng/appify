class_name RestSpot
extends Interactable
## A place to rest (Matt, 10 Nov: the hut's door in Crossroads). Interacting gives full hearts, saves,
## shows the place's lines (data/dialogue, by `speaker_id`) and costs nothing: no Glint, no time, no
## reward. There is no rest during a fight (a living enemy within FIGHT_RANGE, or the player still
## flinching from a hit) or while a line is open: the spot then gives no prompt and E does nothing.
##
## Feedback is finite and quiet: the hearts fill, and the world dims a little and comes back
## (HUSH_IN + HUSH_OUT seconds, one CanvasModulate that frees itself). Under reduced motion the
## world does not dim; the hearts and the line say it.

signal rested

const FIGHT_RANGE := 480.0   ## texels: half the screen's width; a living enemy nearer than this is a fight
const HUSH := Color(0.62, 0.62, 0.72)   ## the world at the middle of the hush
const HUSH_IN := 0.25
const HUSH_OUT := 0.6

var _resting := false
var _hush: CanvasModulate

## No prompt while a fight is on: the HUD's verb must be something E will do.
func usable() -> bool:
	return super.usable() and not fight_near()

## True while a living enemy is within FIGHT_RANGE of this spot, or the player is still flinching.
func fight_near() -> bool:
	if not is_inside_tree():
		return false
	var player := get_tree().get_first_node_in_group("player")
	if player != null and player.has_method("is_invulnerable") and player.is_invulnerable():
		return true
	for e in get_tree().get_nodes_in_group("enemy"):
		var enemy := e as Node2D
		if enemy == null or not enemy.is_inside_tree() or not enemy.is_visible_in_tree():
			continue
		if bool(enemy.get("dead")) or int(enemy.get("hp")) <= 0:
			continue
		if enemy.global_position.distance_to(global_position) <= FIGHT_RANGE:
			return true
	return false

func interact() -> void:
	if _resting or Dialogue.busy or fight_near():
		return
	var player := get_tree().get_first_node_in_group("player")
	if player == null or not player.has_method("heal_full") or int(player.get("hp")) <= 0:
		return
	_resting = true
	player.heal_full()
	_save(player)
	_start_hush()
	rested.emit()
	await Dialogue.talk(speaker_id)
	_resting = false

## The game's own autosave when the game is running (it knows the picture modes that never save),
## the save itself otherwise.
func _save(player: Node) -> void:
	var game := get_tree().get_first_node_in_group("game")
	if game != null and game.has_method("autosave"):
		game.autosave()
		return
	SaveGame.data.player.hp = int(player.get("hp"))
	SaveGame.save()

func _start_hush() -> void:
	if SaveGame.setting("reduced_motion", false) or _hush != null:
		return
	_hush = CanvasModulate.new()
	_hush.name = "RestHush"
	_hush.color = Color.WHITE
	add_child(_hush)
	# bound to this node: it stops with the tree under the pause menu and goes with the zone
	var tween := create_tween()
	tween.tween_property(_hush, "color", HUSH, HUSH_IN)
	tween.tween_property(_hush, "color", Color.WHITE, HUSH_OUT)
	tween.tween_callback(_end_hush)

func _end_hush() -> void:
	if _hush != null:
		_hush.queue_free()
		_hush = null
