class_name Player
extends CharacterBody2D
## The player (game-design.md 4.2): WASD or the left stick to move, the mouse or right stick to aim,
## left click for a three-swing melee combo with hit-stop, Space to roll with invulnerability.
## Speeds and reaches are in world px and scaled by DENSITY, so they hold when the art density changes.
## The sprite is a placeholder sheet (four facings) until the redrawn cast lands.

signal hit_landed(target: Node, heavy: bool)
signal hurt(amount: int)
signal downed

const DENSITY := 3.0                 ## texels per world px (the art grid)
const RUN_SPEED := 50.0 * DENSITY    ## 4.2: the prototype's run, 50 world px a second
const ROLL_TIME := 0.42              ## 4.2: a 0.42 s roll ...
const ROLL_IFRAMES := 0.26           ## ... invulnerable for its first 0.26 s
const ROLL_SPEED := 100.0 * DENSITY  ## about 40 world px per roll
const ROLL_CHARGES := 2              ## two charges ...
const ROLL_RECHARGE := 1.2           ## ... each back after 1.2 s
const SWING_TIME := 0.18
const COMBO_WINDOW := 0.45           ## press again within this after a swing to chain
const COMBO_RESET := 0.6
const SWING_REACH := 9.0 * DENSITY
const SWING_STEP := 30.0 * DENSITY   ## each swing steps a little toward the aim
const HITSTOP_FRAMES := [4, 4, 7]    ## 4.2: 3 to 8 frames by weight; the finisher holds longest
const KNOCKBACK := [70.0 * DENSITY, 70.0 * DENSITY, 130.0 * DENSITY]
const MERCY_TIME := 0.6              ## invulnerable after taking a hit

@export var max_hp := 5

var hp := 5
var aim := Vector2.DOWN
var input_enabled := true
var use_mouse_aim := true
var focus: Node = null               ## the Interactable the player stands at, if any
var combo := 0                       ## swings so far in the current chain (1..3 while swinging)
var roll_charges := ROLL_CHARGES

var _roll_t := 0.0
var _iframe_t := 0.0
var _recharge_t := 0.0
var _roll_dir := Vector2.DOWN
var _swing_t := 0.0
var _since_swing := 99.0
var _swing_hits := {}
var _hurt_t := 0.0
var _facing := 0                     ## 0 S, 1 E, 2 N, 3 W (the sheet's columns)

@onready var sprite: Sprite2D = $Sprite
@onready var hitbox: Area2D = $Hitbox

func _ready() -> void:
	add_to_group("player")
	hp = max_hp
	hitbox.monitoring = false

func reset_motion() -> void:
	velocity = Vector2.ZERO
	_roll_t = 0.0
	_swing_t = 0.0
	focus = null

func is_invulnerable() -> bool:
	return _iframe_t > 0.0

func is_rolling() -> bool:
	return _roll_t > 0.0

func is_swinging() -> bool:
	return _swing_t > 0.0

## Rolls toward `dir` (or the aim when standing). Spends a charge; false when none is left.
func start_roll(dir: Vector2) -> bool:
	if roll_charges <= 0 or is_rolling():
		return false
	roll_charges -= 1
	if _recharge_t <= 0.0:
		_recharge_t = ROLL_RECHARGE
	_roll_dir = dir.normalized() if dir.length() > 0.1 else aim
	_roll_t = ROLL_TIME
	_iframe_t = maxf(_iframe_t, ROLL_IFRAMES)
	_swing_t = 0.0
	hitbox.set_deferred("monitoring", false)
	return true

## Swings at the aim; chains into the combo when pressed soon after the last swing.
func start_swing() -> bool:
	if is_rolling() or is_swinging():
		return false
	combo = combo + 1 if (_since_swing < COMBO_WINDOW and combo < 3) else 1
	_swing_t = SWING_TIME
	_since_swing = 0.0
	_swing_hits.clear()
	hitbox.position = aim * SWING_REACH + Vector2(0, -8)
	hitbox.monitoring = true
	velocity = aim * SWING_STEP
	return true

## Returns true when the hit landed (false while invulnerable).
func take_damage(amount: int, from_dir: Vector2 = Vector2.ZERO) -> bool:
	if is_invulnerable() or hp <= 0:
		return false
	hp = maxi(hp - amount, 0)
	_hurt_t = 0.25
	_iframe_t = MERCY_TIME
	velocity = from_dir * 60.0 * DENSITY
	hurt.emit(amount)
	if hp == 0:
		downed.emit()
	return true

func heal_full() -> void:
	hp = max_hp

func _physics_process(delta: float) -> void:
	_roll_t = maxf(_roll_t - delta, 0.0)
	_iframe_t = maxf(_iframe_t - delta, 0.0)
	_hurt_t = maxf(_hurt_t - delta, 0.0)
	_since_swing += delta
	if _since_swing > COMBO_RESET and not is_swinging():
		combo = 0
	if roll_charges < ROLL_CHARGES:
		_recharge_t -= delta
		if _recharge_t <= 0.0:
			roll_charges += 1
			_recharge_t = ROLL_RECHARGE if roll_charges < ROLL_CHARGES else 0.0

	var move := Vector2.ZERO
	if input_enabled and not Dialogue.busy:
		move = Input.get_vector("move_left", "move_right", "move_up", "move_down")
		_update_aim()
		if Input.is_action_just_pressed("dodge"):
			start_roll(move)
		if Input.is_action_just_pressed("attack"):
			start_swing()
		if Input.is_action_just_pressed("interact") and focus != null and is_instance_valid(focus):
			focus.interact()

	if is_rolling():
		var ease := 0.55 + 0.45 * (_roll_t / ROLL_TIME)  # fast start, settles at the end
		velocity = _roll_dir * ROLL_SPEED * ease
	elif _hurt_t > 0.0 or is_swinging():
		velocity = velocity.move_toward(Vector2.ZERO, 900.0 * delta)
	else:
		velocity = move * RUN_SPEED
	move_and_slide()

	if is_swinging():
		_swing_t = maxf(_swing_t - delta, 0.0)
		_resolve_swing()
		if _swing_t <= 0.0:
			hitbox.monitoring = false
	_animate(move)
	queue_redraw()

func _update_aim() -> void:
	var stick := Inputs.stick_aim()
	if stick != Vector2.ZERO:
		aim = stick
		use_mouse_aim = false
	elif use_mouse_aim and is_inside_tree():
		var to_mouse := get_global_mouse_position() - (global_position + Vector2(0, -8 * DENSITY))
		if to_mouse.length() > 4.0:
			aim = to_mouse.normalized()

func _input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		use_mouse_aim = true

func _resolve_swing() -> void:
	var heavy := combo >= 3
	for body in hitbox.get_overlapping_bodies():
		if body.is_in_group("enemy") and not _swing_hits.has(body) and body.has_method("take_hit"):
			_swing_hits[body] = true
			body.take_hit(2 if heavy else 1, aim, KNOCKBACK[combo - 1])
			hit_landed.emit(body, heavy)
			_hitstop(HITSTOP_FRAMES[combo - 1])

func _hitstop(frames: int) -> void:
	if SaveGame.setting("reduced_motion", false):
		frames = int(frames / 2.0)
	if frames <= 0 or not is_inside_tree():
		return
	Engine.time_scale = 0.05
	await get_tree().create_timer(frames / 60.0, true, false, true).timeout
	Engine.time_scale = 1.0

func _animate(move: Vector2) -> void:
	var look := aim if (is_swinging() or move.length() < 0.1) else move
	if absf(look.x) > absf(look.y):
		_facing = 1 if look.x > 0 else 3
	else:
		_facing = 0 if look.y > 0 else 2
	sprite.frame = _facing
	# a two-texel bob while walking stands in for the walk cycle
	var bob := 0.0
	if move.length() > 0.1 and not is_rolling():
		bob = -3.0 if int(Time.get_ticks_msec() / 140) % 2 == 0 else 0.0
	sprite.position.y = bob
	sprite.rotation = (TAU * (1.0 - _roll_t / ROLL_TIME)) * signf(_roll_dir.x + 0.01) if is_rolling() else 0.0
	if is_invulnerable() and not is_rolling():
		sprite.modulate = Color(1, 1, 1, 0.45 if int(Time.get_ticks_msec() / 70) % 2 == 0 else 1.0)
	elif is_rolling():
		sprite.modulate = Color(0.8, 0.92, 1.0, 0.85)
	else:
		sprite.modulate = Color(1, 0.6, 0.6) if _hurt_t > 0.0 else Color.WHITE

func _draw() -> void:
	if is_swinging():
		# the swing: an arc of 3x3 texel cells (one world px each) in front of the aim
		var t := 1.0 - _swing_t / SWING_TIME
		var r := SWING_REACH + (4.0 if combo >= 3 else 0.0) * DENSITY
		var c := Color(1, 1, 0.85, 0.9 - 0.6 * t)
		var steps := 9
		for i in steps:
			var a := aim.angle() + lerpf(-1.1, 1.1, float(i) / (steps - 1)) * (0.5 + t)
			var p := (Vector2(cos(a), sin(a)) * r + Vector2(0, -8)).snapped(Vector2(3, 3))
			draw_rect(Rect2(p, Vector2(3, 3)), c)
