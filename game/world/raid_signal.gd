class_name RaidSignal
extends Node2D
## Hale's anvil calling the first night (Matt, 13 Nov: "Hale's anvil signals"; the bell is rebuilt later,
## for the wolf moon). A node at the anvil's face that only draws: each of the cue's three blows
## (`raid_anvil`, scripts/audio/game_sounds.py: at 0, 0.5 and 1 s) throws the spark an arrow throws when it
## glances off iron (enemies/glance.gd, word and all), for the glance's own time. No new art and no sound of
## its own: Raids.ring plays the cue. Under reduced motion each spark stands still at its full size
## (Glance.parts). Finite: after the last spark it frees itself, and it goes with its zone before that.

const BLOWS: Array[float] = [0.0, 0.5, 1.0]      ## seconds from the call: the cue's three strikes

var _t := 0.0

func _ready() -> void:
	z_index = 1                        # over the anvil's own picture, as the lantern's lights are over it

## Seconds the spark of the blow at `blow` still shows, `t` seconds into the call (0 or less: none).
static func left(t: float, blow: float) -> float:
	return Glance.TIME - (t - blow) if t >= blow else 0.0

## True once the last blow's spark is over.
static func over(t: float) -> bool:
	return t >= BLOWS[BLOWS.size() - 1] + Glance.TIME

func _process(delta: float) -> void:
	_t += delta
	queue_redraw()
	if over(_t):
		set_process(false)
		queue_free()

func _draw() -> void:
	for blow: float in BLOWS:
		Glance.draw(self, Vector2.ZERO, left(_t, blow))
