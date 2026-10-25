extends Node2D
## The running game inside the 960 x 540 art grid: loads the save, makes the one player, hands both to
## the zone loader, drives the Phantom Camera (aim look-ahead, zone limits, hit shake) and autosaves when
## quests move, a building is restored or zones change.
##
## Command-line options (after `--`): --fresh (ignore the save), --zone=<id>, --spawn=<name>,
## --shot=<png path> (wait, save a 1:1 picture of the window, quit), --demo (a scripted walk in four
## directions with a bow shot after each, for screenshots and videos; --quit ends the run after it),
## --lineup (the whole cast in a row), --cycle (the player becomes each cast member in turn) and
## --character=<id> (start as that cast member), --stage=<id> (a zone plan's named state),
## --at=x,y (stand at a world point).
## See docs/godot.md.

const DENSITY := 3.0
const LOOK_MAX := 48.0 * DENSITY   ## 11.2: look-ahead up to 48 world px ...
const LOOK_DEAD := 16.0 * DENSITY  ## ... past a 16 px dead zone

var player: Player
var args := {}
var _shake := 0.0
var _look := Vector2.ZERO
var _cast_label: Label

@onready var zone_root: Node2D = $ZoneRoot
@onready var pcam: PhantomCamera2D = $PCam
@onready var hud: Control = $UI/HUD
@onready var paused_label: Label = $UI/Paused

func _ready() -> void:
	args = parse_args(OS.get_cmdline_user_args())
	if not args.has("fresh"):
		SaveGame.load_save()
	player = preload("res://actors/player.tscn").instantiate()
	player.hp = clampi(int(SaveGame.data.player.hp), 1, player.max_hp)
	hud.player = player
	Zones.attach(zone_root, player)
	Zones.zone_changed.connect(_on_zone)
	player.hit_landed.connect(func(_t: Node, heavy: bool) -> void: _shake = 0.16 if heavy else 0.1)
	player.hurt.connect(func(_a: int) -> void: _shake = 0.12)
	player.downed.connect(_on_downed)
	Quests.started.connect(func(_id: String) -> void: autosave())
	Quests.advanced.connect(func(_id: String, _s: int) -> void: autosave())
	Quests.completed.connect(func(_id: String) -> void: autosave())
	Village.changed.connect(func(_id: String) -> void: autosave())
	pcam.follow_target = player
	if args.has("stage"):
		apply_stage(String(args.get("zone", SaveGame.data.zone)), String(args.stage))
	var zone: String = args.get("zone", SaveGame.data.zone)
	if not Zones.go_to(zone, args.get("spawn", SaveGame.data.spawn)):
		Zones.go_to("woodland", "start")
	if args.has("shot"):
		_shot.call_deferred(args.shot)
	if args.has("demo"):
		_demo.call_deferred()
	if args.has("lineup"):
		_lineup.call_deferred()
	if args.has("at"):                           # --at=x,y: stand at a world point (screenshots)
		var xy := String(args.at).split(",")
		player.global_position = Vector2(float(xy[0]), float(xy[1])) * DENSITY
	if args.has("character"):
		select_character.call_deferred(String(args.character))
	if args.has("cycle"):
		_cycle.call_deferred()
	_cast_label = Label.new()
	_cast_label.position = Vector2(8, 520)
	_cast_label.add_theme_font_size_override("font_size", 8)
	$UI.add_child(_cast_label)
	_cast_label.text = "1-0, Shift+1-4: character"

static func parse_args(list: PackedStringArray) -> Dictionary:
	var out := {}
	for a in list:
		if a.begins_with("--"):
			var kv := a.substr(2).split("=", true, 1)
			out[kv[0]] = kv[1] if kv.size() > 1 else true
	return out

func autosave() -> void:
	SaveGame.data.player.hp = player.hp
	SaveGame.save()

func _on_zone(zone: Zone) -> void:
	var b := zone.bounds
	pcam.limit_left = int(b.position.x)
	pcam.limit_top = int(b.position.y)
	pcam.limit_right = int(b.end.x)
	pcam.limit_bottom = int(b.end.y)
	pcam.teleport_position()
	snap_camera()
	autosave()

## Puts the Camera2D on the phantom camera at once, so the first frame drawn in a new zone already shows the
## player (the host only moves the camera on its next physics step; a slow first frame showed the world's
## origin at the centre of the screen for that frame).
func snap_camera() -> void:
	var cam := $Camera2D as Camera2D
	cam.global_position = (player.global_position + pcam.follow_offset).round()
	cam.limit_left = pcam.limit_left
	cam.limit_top = pcam.limit_top
	cam.limit_right = pcam.limit_right
	cam.limit_bottom = pcam.limit_bottom
	cam.reset_smoothing()
	cam.force_update_scroll()

func _on_downed() -> void:
	# no naps at 0 HP (4): the player gets up at the zone's start with full health
	player.heal_full()
	Zones.go_to.call_deferred(SaveGame.data.zone, "start")

func _process(delta: float) -> void:
	if player == null or not player.is_inside_tree():
		return
	var want := Vector2.ZERO
	if player.use_mouse_aim:
		var lead := (get_global_mouse_position() - player.global_position) * 0.35
		want = lead.normalized() * clampf(lead.length() - LOOK_DEAD * 0.35, 0.0, LOOK_MAX)
	else:
		want = player.aim * LOOK_MAX * 0.66
	if Dialogue.busy:
		want = Vector2.ZERO
	_look = _look.lerp(want, 1.0 - exp(-4.0 * delta))
	var shake := Vector2.ZERO
	_shake = maxf(_shake - delta, 0.0)
	if _shake > 0.0 and not SaveGame.setting("reduced_motion", false):
		shake = Vector2(randf_range(-1, 1), randf_range(-1, 1)).round() * DENSITY  # 1 world px
	pcam.follow_offset = (_look + Vector2(0, -8.0 * DENSITY)).round() + shake

func _unhandled_input(event: InputEvent) -> void:
	# debug character select: 1 to 0 pick the first ten of Player.CAST, Shift+1 to 4 the rest
	if event is InputEventKey and event.pressed and not event.echo:
		var k: int = event.keycode
		if k >= KEY_0 and k <= KEY_9:
			var i := (k - KEY_1) if k != KEY_0 else 9
			if event.shift_pressed:
				i += 10
			if i < Player.CAST.size():
				select_character(Player.CAST[i])
				get_viewport().set_input_as_handled()
				return
	if event.is_action_pressed("menu"):
		get_tree().paused = not get_tree().paused
		paused_label.visible = get_tree().paused
		get_viewport().set_input_as_handled()

## --stage=<id>: put the save in one of a zone plan's named stages (its restores and flags), to see
## or test that state directly (e.g. --zone=crossroads --stage=homecoming).
static func apply_stage(zone: String, stage: String) -> void:
	var f := FileAccess.open("res://data/plans/%s.json" % zone, FileAccess.READ)
	if f == null:
		return
	var plan: Dictionary = JSON.parse_string(f.get_as_text())
	for st in plan.get("stages", []):
		if st.id != stage:
			continue
		var cond: Dictionary = st.get("if", {})
		for r in cond.get("restored", []):
			SaveGame.data.village.restored[r] = 1
		for fl in cond.get("flags", []):
			SaveGame.set_flag(fl)

func select_character(id: String) -> void:
	if player.set_character(id):
		_cast_label.text = "%s  (1-0, Shift+1-4: character)" % id.capitalize()

## --lineup: the whole cast standing in a row facing the camera, centred under the player.
func _lineup() -> void:
	await get_tree().process_frame
	await get_tree().create_timer(0.5).timeout
	var host := player.get_parent()
	var n := Player.CAST.size()
	var centre := get_viewport().get_camera_2d().get_screen_center_position()
	for i in n:
		var s := CastSprite.new()
		host.add_child(s)
		s.load_character(Player.CAST[i])
		s.global_position = Vector2(centre.x + 80.0 + (i - (n - 1) / 2.0) * 54.0, player.global_position.y + 34.0)
	player.visible = false

## --cycle: the player becomes each cast member in turn, walks a step, shoots and rolls.
func _cycle() -> void:
	player.use_mouse_aim = false
	await get_tree().create_timer(0.6).timeout
	for id in Player.CAST:
		select_character(id)
		player.aim = Vector2.RIGHT
		Input.action_press("move_right")
		await get_tree().create_timer(0.7).timeout
		Input.action_release("move_right")
		player.start_shot()
		await get_tree().create_timer(float(player.sprite.duration("primary")) + 0.15).timeout
		Input.action_press("move_left")
		await get_tree().create_timer(0.7).timeout
		Input.action_release("move_left")
		await get_tree().create_timer(0.2).timeout
	if args.has("quit"):
		get_tree().quit()

func _demo() -> void:
	player.use_mouse_aim = false
	await get_tree().create_timer(0.8).timeout
	for step in [["move_right", Vector2.RIGHT], ["move_down", Vector2.DOWN], ["move_left", Vector2.LEFT], ["move_up", Vector2.UP]]:
		Input.action_press(step[0])
		await get_tree().create_timer(1.3).timeout
		Input.action_release(step[0])
		await get_tree().create_timer(0.3).timeout
		player.aim = step[1]
		player.start_shot()
		await get_tree().create_timer(1.0).timeout
	if args.has("quit"):
		get_tree().quit()

func _shot(path: String) -> void:
	# wait in frames as well as seconds: a slow first frame (a big zone loading) can use up the whole wait,
	# and the picture would be the frame drawn before the camera ever moved
	await get_tree().create_timer(float(args.get("wait", "2.0")), true, false, true).timeout
	while Engine.get_process_frames() < SHOT_MIN_FRAMES:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var img := get_tree().root.get_texture().get_image()
	var ok := frame_covered(img)
	var err := img.save_png(path)
	print("SHOT %s %s %s%s" % [path, img.get_size(), error_string(err), "" if ok else " FAILED: the world does not cover the frame"])
	if not ok:
		push_error("shot %s: a quarter of the frame is black (the world does not cover it)" % path)
	get_tree().quit(0 if err == OK and ok else 1)

const SHOT_MIN_FRAMES := 30

## True when the world picture covers the whole frame: no quarter of it is almost all black. A camera
## left at the world's origin (the frame drawn before it followed anyone) leaves three quarters black.
static func frame_covered(img: Image, max_black := 0.9) -> bool:
	var w := img.get_width()
	var h := img.get_height()
	for q in 4:
		var x0 := (q % 2) * w / 2
		var y0 := (q / 2) * h / 2
		var black := 0
		var n := 0
		for y in range(y0, y0 + h / 2, 8):
			for x in range(x0, x0 + w / 2, 8):
				var c := img.get_pixel(x, y)
				n += 1
				if c.r + c.g + c.b < 0.06:
					black += 1
		if float(black) / float(maxi(n, 1)) > max_black:
			return false
	return true
