extends Sprite2D
## A wall torch drawn by the undercroft kit: its bracket and four drawings of the flame in one strip
## (hframes). The flame flickers only while the torch is on screen (it stops when the screen moves on or
## the zone is left) and holds its first drawing under reduced motion. Decorative: nothing reads it.

const FRAME_SEC := 0.13
const ORDER := [0, 1, 0, 2, 3, 2]   ## lean, lift, settle: never the same step twice in a row

var _t := 0.0

func _ready() -> void:
	frame = 0
	_t = fmod(position.x * 0.0137, 1.0)   # torches out of step with each other, the same every run
	var notifier := VisibleOnScreenNotifier2D.new()
	notifier.rect = get_rect()
	add_child(notifier)
	notifier.screen_entered.connect(func() -> void: set_process(true))
	notifier.screen_exited.connect(func() -> void: set_process(false))
	set_process(false)

func _process(delta: float) -> void:
	if SaveGame.setting("reduced_motion", false):
		frame = 0
		return
	_t += delta
	frame = ORDER[int(_t / FRAME_SEC) % ORDER.size()] % hframes
