extends Sprite2D
## Cycles a zone's moving-water frames (packed hframes x vframes), as the Expo app does.
## Holds the first frame under reduced motion.

const FRAME_SEC := 0.16

var _t := 0.0

func _process(delta: float) -> void:
	if SaveGame.setting("reduced_motion", false):
		frame = 0
		return
	_t += delta
	frame = int(_t / FRAME_SEC) % (hframes * vframes)
