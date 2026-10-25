class_name Enemy
extends CharacterBody2D
## A shardstruck mossling driven by a LimboAI hierarchical state machine (ported from the evaluation
## slice): idle -> chase -> windup (0.5 s ground telegraph) -> lunge -> recover -> chase, leashing home
## when dragged too far or when the target runs off. It dies at 0 hp and reports `died` to its Camp.
## Distances are in world px times DENSITY. The sprite is a placeholder until the cast lands.

signal state_changed(state: StringName)
signal died

const DENSITY := 3.0
const WINDUP_TIME := 0.5
const LUNGE_TIME := 0.16
const LUNGE_SPEED := 150.0 * DENSITY
const RECOVER_TIME := 0.55

@export var aggro_radius := 55.0 * DENSITY
@export var lose_radius := 110.0 * DENSITY
@export var leash_radius := 100.0 * DENSITY  ## from home
@export var attack_range := 17.0 * DENSITY
@export var speed := 39.0 * DENSITY
@export var max_hp := 3

var home := Vector2.ZERO
var target: Node2D
var hp := 3
var state: StringName = &"idle"
var telegraph := 0.0
var attack_dir := Vector2.RIGHT
var hsm: LimboHSM
var dead := false
var _t := 0.0
var _struck := false
var _stagger := 0.0
var _flash := 0.0

@onready var sprite: Sprite2D = $Sprite

func _ready() -> void:
	add_to_group("enemy")
	hp = max_hp
	home = global_position
	_build_hsm()

func _build_hsm() -> void:
	hsm = LimboHSM.new()
	hsm.name = "HSM"
	hsm.update_mode = LimboHSM.MANUAL
	add_child(hsm)
	var idle := LimboState.new().named("idle").call_on_update(_idle)
	var chase := LimboState.new().named("chase").call_on_update(_chase)
	var windup := LimboState.new().named("windup").call_on_enter(_windup_enter).call_on_update(_windup)
	var lunge := LimboState.new().named("lunge").call_on_enter(_lunge_enter).call_on_update(_lunge)
	var recover := LimboState.new().named("recover").call_on_enter(_reset_t).call_on_update(_recover)
	var leash := LimboState.new().named("leash").call_on_update(_leash)
	for s in [idle, chase, windup, lunge, recover, leash]:
		hsm.add_child(s)
	hsm.add_transition(idle, chase, &"aggro")
	hsm.add_transition(chase, windup, &"in_range")
	hsm.add_transition(windup, lunge, &"strike")
	hsm.add_transition(lunge, recover, &"done")
	hsm.add_transition(recover, chase, &"done")
	hsm.add_transition(chase, leash, &"leash")
	hsm.add_transition(recover, leash, &"leash")
	hsm.add_transition(leash, idle, &"home")
	hsm.initial_state = idle
	hsm.active_state_changed.connect(_on_state_changed)
	hsm.initialize(self)
	hsm.set_active(true)

func _on_state_changed(current: LimboState, _previous: LimboState) -> void:
	state = StringName(current.name)
	telegraph = 0.0
	state_changed.emit(state)

func _physics_process(delta: float) -> void:
	if dead:
		return
	if target == null or not is_instance_valid(target):
		target = get_tree().get_first_node_in_group("player") as Node2D
	_flash = maxf(_flash - delta, 0.0)
	if _stagger > 0.0:
		_stagger -= delta
		velocity = velocity.move_toward(Vector2.ZERO, 1800.0 * delta)
	else:
		hsm.update(delta)
	move_and_slide()
	_animate()
	queue_redraw()

# --- states -------------------------------------------------------------
func _target_dist() -> float:
	return INF if target == null else global_position.distance_to(target.global_position)

func _should_leash() -> bool:
	return global_position.distance_to(home) > leash_radius or _target_dist() > lose_radius

func _idle(_delta: float) -> void:
	velocity = Vector2.ZERO
	if target != null and _target_dist() < aggro_radius and home.distance_to(target.global_position) < leash_radius:
		hsm.dispatch(&"aggro")

func _chase(_delta: float) -> void:
	if _should_leash():
		hsm.dispatch(&"leash")
		return
	if _target_dist() < attack_range:
		hsm.dispatch(&"in_range")
		return
	velocity = global_position.direction_to(target.global_position) * speed

func _reset_t() -> void:
	_t = 0.0

func _windup_enter() -> void:
	_t = 0.0
	attack_dir = global_position.direction_to(target.global_position)

func _windup(delta: float) -> void:
	velocity = Vector2.ZERO
	_t += delta
	telegraph = clampf(_t / WINDUP_TIME, 0.0, 1.0)
	if _t >= WINDUP_TIME:
		hsm.dispatch(&"strike")

func _lunge_enter() -> void:
	_t = 0.0
	_struck = false

func _lunge(delta: float) -> void:
	_t += delta
	velocity = attack_dir * LUNGE_SPEED
	if not _struck and target != null and _target_dist() < 9.0 * DENSITY and target.has_method("take_damage"):
		_struck = true
		target.take_damage(1, attack_dir)
	if _t >= LUNGE_TIME:
		hsm.dispatch(&"done")

func _recover(delta: float) -> void:
	velocity = Vector2.ZERO
	_t += delta
	if _t >= RECOVER_TIME:
		hsm.dispatch(&"leash" if _should_leash() else &"done")

func _leash(_delta: float) -> void:
	if Engine.get_physics_frames() % 30 == 0:
		hp = mini(hp + 1, max_hp)
	if global_position.distance_to(home) < 3.0:
		global_position = home
		velocity = Vector2.ZERO
		hsm.dispatch(&"home")
		return
	velocity = global_position.direction_to(home) * speed * 1.3

# --- damage -------------------------------------------------------------
func take_hit(amount: int, dir: Vector2, knockback: float = 200.0) -> void:
	if dead:
		return
	hp -= amount
	_flash = 0.12
	if state != &"windup" and state != &"lunge":
		_stagger = 0.14
		velocity = dir * knockback
	if hp <= 0:
		_die()

func _die() -> void:
	dead = true
	hsm.set_active(false)
	collision_layer = 0
	velocity = Vector2.ZERO
	died.emit()
	var tw := create_tween()
	tw.tween_property(sprite, "scale", Vector2(1.3, 0.6), 0.08)
	tw.tween_property(sprite, "modulate:a", 0.0, 0.18)
	tw.tween_callback(queue_free)

# --- look ---------------------------------------------------------------
func _animate() -> void:
	var dir := velocity if velocity.length() > 1.0 else attack_dir
	if absf(dir.x) > absf(dir.y):
		sprite.frame = 1 if dir.x > 0 else 3
	else:
		sprite.frame = 0 if dir.y > 0 else 2
	if _flash > 0.0:
		sprite.modulate = Color(3, 3, 3)
	elif state == &"windup":
		var on := int(telegraph * telegraph * 14.0) % 2 == 0  # blinks faster as the strike nears
		sprite.modulate = Color(1.8, 0.7, 0.6) if on else Color(1, 0.8, 0.75)
	else:
		sprite.modulate = Color.WHITE

func _draw() -> void:
	if state != &"windup" or dead:
		return
	# ground telegraph: a wedge of 3x3 texel cells (one world px); the outline shows the full reach,
	# the fill grows toward it over the wind-up
	var reach := attack_range + 4.0 * DENSITY
	var half := 0.55
	var fill := 9.0 + (reach - 9.0) * telegraph
	var cell := DENSITY
	for gy in range(-int(reach), int(reach) + 1, int(cell)):
		for gx in range(-int(reach), int(reach) + 1, int(cell)):
			var v := Vector2(gx, gy)
			var r := v.length()
			if r < 9.0 or r > reach:
				continue
			var off := absf(wrapf(v.angle() - attack_dir.angle(), -PI, PI))
			if off > half:
				continue
			if r > reach - cell * 1.2 or off > half - cell * 1.2 / r:
				draw_rect(Rect2(v, Vector2(cell, cell)), Color(1.0, 0.35, 0.25, 0.85))
			elif r <= fill:
				draw_rect(Rect2(v, Vector2(cell, cell)), Color(0.95, 0.2, 0.15, 0.3 + 0.3 * telegraph))
	draw_rect(Rect2(Vector2(-1.5, -48), Vector2(3, 9)), Color(1, 0.9, 0.3))
	draw_rect(Rect2(Vector2(-1.5, -36), Vector2(3, 3)), Color(1, 0.9, 0.3))
