class_name PlayerSounds
extends Node
## The player's cues, read from what the player already shows (game.gd adds one to the player): its
## signals (hurt, downed, a shot released, a hit landed) and its clip (the bow drawn, the roll, a foot
## coming down in the walk). It changes nothing in the player and asks nothing of it; with sound inactive
## (core/sound.gd) it does nothing at all.
##
##   bow_draw     the clip becomes `primary`           bow_release   `shot_released`
##   arrow_hit    `hit_landed` (the hit counted)       roll          the clip becomes `dodge`
##   hurt         `hurt` with hearts left              downed        `hurt` with none left
##   get_up       `downed`, when the fall has played and the player gets up at the zone's start (not
##                when that defeat lost a raid's night: the night's own cue is the moment's)
##   a footstep   the walk clip reaching a drawing where a foot is planted (two a cycle), while moving

const WALK := "walk"

var player: Player
var _state: StringName = &""
var _drawing := -1

func _ready() -> void:
	player = get_parent() as Player
	if player == null:
		set_physics_process(false)
		return
	_state = player.state
	player.hurt.connect(func(_amount: int) -> void: Sound.play(&"hurt" if player.hp > 0 else &"downed"))
	player.downed.connect(func() -> void: Sound.play(&"get_up", &"night_lost"))
	player.shot_released.connect(func(_arrow: Node, _frame: int) -> void: Sound.play(&"bow_release"))
	player.hit_landed.connect(func(_target: Node, _heavy: bool) -> void: Sound.play(&"arrow_hit"))

func _physics_process(_delta: float) -> void:
	if not Sound.active:
		return
	var state := player.state
	if state != _state:
		_state = state
		if state == &"primary":
			Sound.play(&"bow_draw")
		elif state == &"dodge":
			Sound.play(&"roll")
	var drawing := -1
	if state == &"walk" and player.sprite.playing == WALK and player.get_real_velocity().length() > 1.0:
		drawing = player.sprite.frame_index
		if footfall_between(_drawing, drawing, int(player.sprite.clip_info(WALK).frame_count)):
			Sound.step(player.global_position)
	_drawing = drawing

## True for the two drawings of a walk of `count` drawings on which a foot comes down: the first, and the
## one half a cycle on (Bramble's 12: drawings 0 and 6, where the manifest's foot anchors are lowest).
static func is_footfall(drawing: int, count: int) -> bool:
	return count >= 2 and drawing % maxi(count / 2, 1) == 0

## True when the walk went from drawing `from` to drawing `to` over a footfall (`to` included, `from` not).
## `from` -1 is a walk that has only just begun: its first drawing is where the foot already stands.
static func footfall_between(from: int, to: int, count: int) -> bool:
	if from < 0 or to < 0 or from == to or count < 2:
		return false
	var i := from
	while i != to:
		i = (i + 1) % count
		if is_footfall(i, count):
			return true
	return false
