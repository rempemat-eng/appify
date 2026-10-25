extends Node2D
## The running game inside the 960 x 540 art grid: loads the save, makes the one player, hands both to
## the zone loader, drives the Phantom Camera (aim look-ahead, zone limits, hit shake) and autosaves when
## quests move, a building is restored or zones change.
##
## Command-line options (after `--`): --fresh (ignore the save), --zone=<id>, --spawn=<name>,
## --shot=<png path> (wait, save a 1:1 picture of the window, quit). See docs/godot.md.

const DENSITY := 3.0
const LOOK_MAX := 48.0 * DENSITY   ## 11.2: look-ahead up to 48 world px ...
const LOOK_DEAD := 16.0 * DENSITY  ## ... past a 16 px dead zone

var player: Player
var args := {}
var _shake := 0.0
var _look := Vector2.ZERO

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
	var zone: String = args.get("zone", SaveGame.data.zone)
	if not Zones.go_to(zone, args.get("spawn", SaveGame.data.spawn)):
		Zones.go_to("woodland", "start")
	if args.has("shot"):
		_shot.call_deferred(args.shot)

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
	autosave()

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
	if event.is_action_pressed("menu"):
		get_tree().paused = not get_tree().paused
		paused_label.visible = get_tree().paused
		get_viewport().set_input_as_handled()

func _shot(path: String) -> void:
	await get_tree().create_timer(float(args.get("wait", "2.0")), true, false, true).timeout
	await RenderingServer.frame_post_draw
	var img := get_tree().root.get_texture().get_image()
	var err := img.save_png(path)
	print("SHOT %s %s %s" % [path, img.get_size(), error_string(err)])
	get_tree().quit(0 if err == OK else 1)
