class_name Player
extends CharacterBody2D
## The player (game-design.md 4.2): WASD or the left stick to move, the mouse or right stick to aim,
## left click for a three-swing melee combo with hit-stop, Space to roll with invulnerability.
## Speeds and reaches are in world px and scaled by DENSITY, so they hold when the art density changes.
## The body is Bramble from the redrawn cast (assets/characters/bramble, actors/cast_sprite.gd): his
## facing (S, N, E, W) follows movement, or the aim when standing or shooting, and his state picks
## the clip: idle, walk, primary (left click: the bow shot, the arrow leaves at the drawing's
## arrow_tip on the manifest's release frame and flies along the aim), dodge (the roll), hit and
## defeat. He walks at the manifest's walk_speed, the speed that keeps his feet planted.
## The melee combo (start_swing) stays for the billhook and the tests; it is not bound for now.

signal hit_landed(target: Node, heavy: bool)
signal hurt(amount: int)
signal downed
signal shot_released(arrow: Node, frame: int)

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
const CHARACTER := "bramble"
## The redrawn cast in select order (game.gd: keys 1 to 0, then Shift+1 to 4). Bramble has his
## abilities wired (the arrow); the others play idle, walk, primary, dodge, hit and defeat until
## the ability runner lands.
const CAST := ["bramble", "iona", "pendle", "cairn", "morel", "velvet", "tam", "mirra", "brine", "ashe",
	"clack", "nix", "rook", "mote"]
const DEFEAT_HOLD := 0.5             ## the last defeat drawing holds this long before getting up

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
var state := &"idle"                 ## idle, walk, primary, dodge, hit, defeat (the clip shown)
var facing := "S"
var walk_speed := RUN_SPEED          ## replaced by the manifest's walk_speed in _ready
var character := CHARACTER
var _shot_dir := Vector2.RIGHT
var _defeat_t := 0.0
var action_driver: AbilityActionDriver = null
var ability_presentation_error := ""
var _ability_drawing: Dictionary = {}
## Explicit actor-texel support elevation; terrain integration supplies it, never inferred.
var ability_support_height := 0.0
var _ability_ground_body := Vector2.ZERO
var _ability_pose_driver: AbilityActionDriver = null

@onready var sprite: CastSprite = $Sprite
@onready var hitbox: Area2D = $Hitbox

func _ready() -> void:
	add_to_group("player")
	hp = max_hp
	hitbox.monitoring = false
	set_character(character)

func _exit_tree() -> void:
	# Scene removal/reparenting must not leave presentation callbacks on a departed actor.
	if action_driver != null:
		action_driver.cancel("actor_exited_tree")

## Swaps the body to another cast member (keeps position, HP and facing). False if unknown.
func set_character(id: String) -> bool:
	if hp <= 0 or is_rolling() or is_swinging() or is_shooting() or (action_driver != null and action_driver.is_busy()):
		return false
	if not sprite.load_character(id):
		return false
	character = id
	if action_driver != null:
		action_driver.character_changed(id)
	walk_speed = sprite.walk_speed() if sprite.walk_speed() > 0.0 else RUN_SPEED
	state = &"idle"
	sprite.play_clip("idle", facing, true)
	return true

## Optional C60 boundary. No driver is installed by default. Player retains input,
## facing, collision and movement; the driver owns action clocks and combat effects.
func attach_action_driver(driver: AbilityActionDriver) -> bool:
	if driver == null or action_driver != null or hp <= 0 or is_rolling() or is_swinging() or is_shooting():
		return false
	action_driver = driver
	action_driver.character_changed(character)
	return true

## Explicit optional binding: the provider must use this loaded body's exact manifest
## and supply approved canonical drawing clocks. No production schedule is inferred.
func bind_ability_presentation(provider: Callable, contact: Callable) -> bool:
	if not action_driver is AbilityArenaDriver or not provider.is_valid() or not contact.is_valid():
		return false
	var expected := action_driver
	var bound := (action_driver as AbilityArenaDriver).bind_presentation(
		_ability_contract.bind(provider, expected), _present_ability_drawing.bind(expected),
		_ability_contact.bind(contact, expected), _present_ability_pose.bind(expected))
	if bound:
		_ability_ground_body = sprite.position
		_ability_pose_driver = expected
		_ability_drawing = {}
		ability_presentation_error = ""
	return bound

## Only the body moves above its ground pivot. Colliders, actor, anchors and any
## sibling ground shadow stay put; no authored frame or canonical value is changed.
func _present_ability_pose(snapshot: Dictionary, expected: AbilityActionDriver) -> bool:
	if _ability_pose_driver != expected:
		return false
	if snapshot.is_empty():
		sprite.position = _ability_ground_body
		_ability_pose_driver = null
		return true
	if not _ability_actor_valid(expected):
		return false
	var height: Variant = snapshot.get("player", {}).get("vaultHeight")
	if not (height is int or height is float) or not is_finite(float(height)) or height < 0 or not is_finite(ability_support_height):
		ability_presentation_error = "invalid runner/support height"
		_ability_drawing = {}
		return false
	sprite.position = _ability_ground_body + Vector2.UP * (ability_support_height + float(height) * float(AbilityCatalogue.units().canonical_to_actor))
	return true

func _ability_contract(snapshot: Dictionary, action: String, provider: Callable, expected: AbilityActionDriver) -> Dictionary:
	if not _ability_actor_valid(expected):
		return {}
	var supplied: Variant = provider.call(snapshot, action)
	if not _ability_actor_valid(expected):
		return {} # the provider may have detached/replaced/reset the actor
	if not supplied is Dictionary or supplied.get("manifest") != sprite.manifest:
		ability_presentation_error = "presentation manifest differs from loaded body"
		return {}
	return supplied

func _ability_actor_valid(expected: AbilityActionDriver) -> bool:
	return action_driver == expected and is_inside_tree() and hp > 0 and not is_defeated()

func _present_ability_drawing(sample: Dictionary, expected: AbilityActionDriver) -> void:
	if not _ability_actor_valid(expected):
		return
	if not AbilitySpritePresenter.show_drawing(sprite, sample):
		_ability_drawing = {}
		ability_presentation_error = "missing or mismatched authored drawing"
		return
	_ability_drawing = sample.duplicate(true)
	ability_presentation_error = ""
	facing = str(sample.facing)

func _ability_contact(sample: Dictionary, contact: Callable, expected: AbilityActionDriver) -> void:
	if _ability_actor_valid(expected) and ability_presentation_error == "" and _ability_drawing == sample:
		contact.call(sample.duplicate(true)) # display callback only, never legacy _release

func detach_action_driver() -> void:
	if action_driver == null:
		return
	var old := action_driver
	action_driver = null
	old.cancel("detached")
	velocity = Vector2.ZERO
	_set_state(&"idle" if hp > 0 else &"defeat")

func _driver_request(action: String, direction: Vector2 = Vector2.ZERO) -> bool:
	if hp <= 0 or is_defeated():
		return false
	return action_driver.request(action, direction if direction.length() > 0.1 else aim)

func reset_motion() -> void:
	if action_driver != null:
		action_driver.cancel("reset_motion")
		_ability_drawing = {}
		_set_state(&"idle") # exact drawing callbacks do not change the legacy state field
	velocity = Vector2.ZERO
	_roll_t = 0.0
	_swing_t = 0.0
	focus = null
	if state != &"idle":
		_set_state(&"idle")

func is_invulnerable() -> bool:
	return _iframe_t > 0.0

func is_rolling() -> bool:
	return _roll_t > 0.0

func is_swinging() -> bool:
	return _swing_t > 0.0

func is_shooting() -> bool:
	return state == &"primary"

func is_defeated() -> bool:
	return state == &"defeat"

## The bow shot (Bramble's primary) at the aim: the body turns to the aim's facing, draws and
## looses; the arrow is spawned on the release frame (see _animate).
func start_shot() -> bool:
	if action_driver != null:
		return _driver_request("primary")
	if is_rolling() or is_shooting() or is_defeated() or not sprite.has_clip("primary"):
		return false
	_shot_dir = aim.normalized() if aim.length() > 0.1 else CastSprite.facing_vector(facing)
	facing = CastSprite.facing_for(_shot_dir, facing)
	_set_state(&"primary")
	velocity = Vector2.ZERO
	return true

## Rolls toward `dir` (or the aim when standing). Spends a charge; false when none is left.
func start_roll(dir: Vector2) -> bool:
	if action_driver != null:
		return _driver_request("dodge", dir)
	if roll_charges <= 0 or is_rolling() or is_defeated():
		return false
	roll_charges -= 1
	if _recharge_t <= 0.0:
		_recharge_t = ROLL_RECHARGE
	_roll_dir = dir.normalized() if dir.length() > 0.1 else aim
	_roll_t = ROLL_TIME
	_iframe_t = maxf(_iframe_t, ROLL_IFRAMES)
	_swing_t = 0.0
	hitbox.set_deferred("monitoring", false)
	facing = CastSprite.facing_for(_roll_dir, facing)
	_set_state(&"dodge")
	return true

## Swings at the aim; chains into the combo when pressed soon after the last swing.
func start_swing() -> bool:
	if action_driver != null:
		return _driver_request("primary")
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
		if action_driver != null:
			action_driver.cancel("defeated")
		_set_state(&"defeat")       # downed is emitted once the fall has played (_animate)
		_defeat_t = 0.0
	elif not is_rolling():
		_set_state(&"hit")
	return true

func heal_full() -> void:
	hp = max_hp

func _physics_process(delta: float) -> void:
	if not is_finite(delta) or delta <= 0.0:
		return
	if action_driver != null:
		_driver_physics(delta)
		return
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
	if input_enabled and not Dialogue.busy and not is_defeated():
		move = Input.get_vector("move_left", "move_right", "move_up", "move_down")
		_update_aim()
		if Input.is_action_just_pressed("dodge"):
			start_roll(move)
		if Input.is_action_just_pressed("attack"):
			start_shot()
		if Input.is_action_just_pressed("interact") and focus != null and is_instance_valid(focus):
			focus.interact()

	if is_rolling():
		var ease := 0.55 + 0.45 * (_roll_t / ROLL_TIME)  # fast start, settles at the end
		velocity = _roll_dir * ROLL_SPEED * ease
	elif is_defeated():
		velocity = Vector2.ZERO
	elif _hurt_t > 0.0 or is_swinging() or is_shooting():
		velocity = velocity.move_toward(Vector2.ZERO, 900.0 * delta)
	else:
		velocity = move * walk_speed
	move_and_slide()

	if is_swinging():
		_swing_t = maxf(_swing_t - delta, 0.0)
		_resolve_swing()
		if _swing_t <= 0.0:
			hitbox.monitoring = false
	_animate(move, delta)
	queue_redraw()

## Default drivers tick after Player movement. Planned drivers bypass that pass
## and resolve ordered targets through Player, never moving a second body copy.
func _driver_physics(delta: float) -> void:
	var active := input_enabled and not Dialogue.busy and hp > 0 and not is_defeated()
	var move := Vector2.ZERO
	if active:
		move = Input.get_vector("move_left", "move_right", "move_up", "move_down")
		_update_aim()
		facing = CastSprite.facing_for(move if move.length() > 0.1 else aim, facing)
		if Input.is_action_just_pressed("interact") and focus != null and is_instance_valid(focus):
			focus.interact()
	# Existing mercy/hurt timers stay with Player; legacy roll/recharge/swing clocks do not tick.
	_iframe_t = maxf(_iframe_t - delta, 0.0)
	_hurt_t = maxf(_hurt_t - delta, 0.0)
	if not action_driver.plans_movement():
		velocity = move * walk_speed if _hurt_t <= 0.0 else velocity.move_toward(Vector2.ZERO, 900.0 * delta)
		if not active:
			velocity = Vector2.ZERO
		move_and_slide()
	else:
		velocity = Vector2.ZERO
	var controls := {"active": active, "move": move, "aim": aim,
		"primary": active and Input.is_action_pressed("attack"),
		"secondary": active and Input.is_action_pressed("ranged"),
		"special": active and Input.is_action_pressed("special"),
		"guard": active and InputMap.has_action("guard") and Input.is_action_pressed("guard"),
		"dodge": active and Input.is_action_just_pressed("dodge")}
	action_driver.tick(controls, {"position": global_position, "velocity": velocity,
		"facing": facing, "character": character, "move_actor": _driver_move_actor}, delta)
	queue_redraw()

## The driver supplies an absolute actor-texel target; only Player applies it.
## Explicit displacement avoids move_and_slide using the outer frame duration for
## each canonical 1/60 substep. Resolve the remainder along a wall, at most once.
func _driver_move_actor(target: Vector2) -> Vector2:
	var displacement := target - global_position
	var collision := move_and_collide(displacement)
	if collision != null:
		move_and_collide(collision.get_remainder().slide(collision.get_normal()))
	velocity = (global_position - (target - displacement)) / AbilitySimulation.DT
	return global_position

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
	if action_driver != null:
		return
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

func _set_state(st: StringName) -> void:
	state = st
	var clip := String(st)
	if sprite.has_clip(clip):
		sprite.play_clip(clip, facing, true)

## Picks the facing and clip from the state, advances the drawings and fires the release.
func _animate(move: Vector2, delta: float) -> void:
	var moving := move.length() > 0.1
	match state:
		&"primary":
			_advance_action(delta)
			if sprite.finished:
				_set_state(&"walk" if moving else &"idle")
		&"dodge":
			sprite.advance(delta * sprite.duration("dodge") / ROLL_TIME)
			if not is_rolling():
				_set_state(&"walk" if moving else &"idle")
		&"hit":
			sprite.advance(delta)
			if sprite.finished or (moving and _hurt_t <= 0.0):
				_set_state(&"walk" if moving else &"idle")
		&"defeat":
			sprite.advance(delta)
			if sprite.finished:
				_defeat_t += delta
				if _defeat_t >= DEFEAT_HOLD and hp == 0:
					downed.emit()
			if hp > 0:              # healed and moved to the zone's start by the game
				_set_state(&"idle")
		_:
			facing = CastSprite.facing_for(move if moving else aim, facing)
			var want := &"walk" if moving else &"idle"
			state = want
			sprite.play_clip(String(want), facing)
			sprite.advance(delta)
	if is_invulnerable() and not is_rolling() and not is_defeated():
		sprite.modulate = Color(1, 1, 1, 0.45 if int(Time.get_ticks_msec() / 70) % 2 == 0 else 1.0)
	else:
		sprite.modulate = Color(1, 0.6, 0.6) if _hurt_t > 0.0 else Color.WHITE

func _advance_action(delta: float) -> void:
	var rel := sprite.release_frame()
	for i in sprite.advance(delta):
		if i == rel:
			_release(i)

## The arrow leaves the bow where the drawing's arrow tip is, on the release drawing.
func _release(frame: int) -> void:
	if action_driver != null:
		return
	if character != "bramble":      # the others' projectiles and effects come with the ability runner
		shot_released.emit(null, frame)
		return
	var a := sprite.anchor("arrow_tip", frame)
	if a == Vector2.ZERO:           # the arrow has left: the anchor of the drawing before
		a = sprite.anchor("arrow_tip", maxi(frame - 1, 0))
	var arrow := Arrow.new()
	var host := get_parent() if get_parent() != null else self
	host.add_child(arrow)
	arrow.setup(global_position + Vector2(a.x, 0.0), -a.y, _shot_dir)
	arrow.struck.connect(func(t: Node) -> void: hit_landed.emit(t, false))
	shot_released.emit(arrow, frame)

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
