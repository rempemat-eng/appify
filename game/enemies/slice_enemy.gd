class_name SliceEnemy
extends CharacterBody2D
## C61 independent actor: LimboAI HSM, shared attack reservations, no save/reward writes.
signal died
signal committed
signal released
const DENSITY := 3.0
const LEASH := 140.0 * DENSITY
@export_enum("rusher", "shooter", "shield", "elite") var role := "rusher"
var slots: SliceAttackSlots
var target: Node2D
var home := Vector2.ZERO
var hp := 4
var dead := false
var state := "idle"
var elapsed := 0.0
var facing := Vector2.DOWN
var hsm: LimboHSM
var shot: SliceEnemyShot
var _struck := false
var _reserved := false

func windup_time() -> float:
	return 0.65 if role == "elite" else 0.95

func reach() -> float:
	return 85.0 * DENSITY if role == "shooter" else 22.0 * DENSITY

func _ready() -> void:
	add_to_group("enemy")
	home = global_position
	hp = 12 if role == "elite" else (8 if role == "shield" else 4)
	collision_layer = 4
	collision_mask = 1
	motion_mode = CharacterBody2D.MOTION_MODE_FLOATING
	var shape := CollisionShape2D.new()
	var circle := CircleShape2D.new()
	circle.radius = 12.0
	shape.shape = circle
	add_child(shape)
	if slots == null:
		# Safe isolated preview; production encounter supplies a shared pool.
		slots = SliceAttackSlots.new()
		add_child(slots)
	hsm = LimboHSM.new()
	hsm.update_mode = LimboHSM.MANUAL
	add_child(hsm)
	var states := {}
	for key in ["idle", "approach", "windup", "attack", "recover", "leash"]:
		var s := LimboState.new().named(key).call_on_update(_update_state)
		hsm.add_child(s)
		states[key] = s
	for key in states:
		for dest in states:
			if key != dest:
				hsm.add_transition(states[key], states[dest], StringName(dest))
	hsm.initial_state = states.idle
	hsm.active_state_changed.connect(_changed)
	hsm.initialize(self)
	hsm.set_active(true)

func _changed(current: LimboState, _previous: LimboState) -> void:
	state = str(current.name)
	elapsed = 0.0
	velocity = Vector2.ZERO
	queue_redraw()

func _physics_process(delta: float) -> void:
	if not is_instance_valid(target):
		target = get_tree().get_first_node_in_group("player") as Node2D
	step(delta)
	move_and_slide()

## Deterministic state advancement is also used by GdUnit fixtures.
func step(delta: float) -> void:
	if dead:
		return
	if state != "idle" and state != "leash" and _outside_leash():
		_cancel_attack()
		hsm.dispatch(&"leash")
	hsm.update(maxf(delta, 0.0))
	queue_redraw()

func _outside_leash() -> bool:
	return not is_instance_valid(target) or global_position.distance_to(home) > LEASH or home.distance_to(target.global_position) > LEASH

func _update_state(delta: float) -> void:
	elapsed += delta
	match state:
		"idle":
			if is_instance_valid(target) and not _outside_leash() and global_position.distance_to(target.global_position) < 100.0 * DENSITY:
				hsm.dispatch(&"approach")
		"approach":
			var distance := global_position.distance_to(target.global_position)
			facing = global_position.direction_to(target.global_position)
			if distance <= reach() and _can_commit() and slots.acquire(self):
				_reserved = true
				committed.emit()
				hsm.dispatch(&"windup")
			elif role == "shooter" and distance < 45.0 * DENSITY:
				velocity = -facing * 30.0 * DENSITY
			else:
				velocity = facing * 34.0 * DENSITY if distance > reach() else facing.orthogonal() * 16.0 * DENSITY
		"windup":
			velocity = Vector2.ZERO  # direction locks at commitment; no tracking during tell
			if elapsed >= windup_time():
				_struck = false
				hsm.dispatch(&"attack")
				if role == "shooter":
					shot = SliceEnemyShot.new()
					shot.direction = facing
					shot.source = self
					get_parent().add_child(shot)
					shot.global_position = global_position + facing * 18.0
				released.emit()
		"attack":
			if role == "shooter":
				if not is_instance_valid(shot) or shot.finished:
					hsm.dispatch(&"recover")
			else:
				velocity = facing * (125.0 if role != "shield" else 45.0) * DENSITY
				if not _struck and is_instance_valid(target) and global_position.distance_to(target.global_position) < 28.0 and facing.dot(global_position.direction_to(target.global_position)) >= 0.3 and target.has_method("take_damage"):
					_struck = true
					target.take_damage(2 if role == "elite" else 1, facing)
				if elapsed >= 0.18:
					hsm.dispatch(&"recover")
		"recover":
			velocity = Vector2.ZERO
			if elapsed >= 0.65:
				_cancel_attack()
				hsm.dispatch(&"approach")
		"leash":
			if global_position.distance_to(home) <= 4.0:
				global_position = home
				hsm.dispatch(&"idle")
			else:
				velocity = global_position.direction_to(home) * 48.0 * DENSITY

func _can_commit() -> bool:
	if role != "shooter":
		return true
	# Prevent off-screen fire, including when the scene is placed on a large map.
	var screen := get_viewport_rect()
	var point := get_global_transform_with_canvas().origin
	if not screen.has_point(point):
		return false
	var query := PhysicsRayQueryParameters2D.create(global_position, target.global_position, 1)
	return get_world_2d().direct_space_state.intersect_ray(query).is_empty()

func take_hit(amount: int, dir: Vector2, _knockback: float = 200.0) -> void:
	if dead or amount <= 0:
		return
	# Incoming travel direction opposes the shield's facing on a frontal hit.
	var guarded := role == "shield" and dir.normalized().dot(facing) < -0.5 and state != "recover"
	hp -= maxi(1, ceili(float(amount) * (0.5 if guarded else 1.0)))
	if hp <= 0:
		dead = true
		_cancel_attack()
		hsm.set_active(false)
		collision_layer = 0
		velocity = Vector2.ZERO
		died.emit()
		# Placeholder freedom animation: creature shrinks out; no loot/reward authority.
		var tween := create_tween()
		tween.tween_property(self, "scale", Vector2(0.1, 0.1), 0.25)
		tween.tween_callback(queue_free)

func _cancel_attack() -> void:
	if is_instance_valid(shot):
		shot.finish()
	if _reserved and is_instance_valid(slots):
		slots.release(self)
	_reserved = false

func _exit_tree() -> void:
	_cancel_attack()

func _draw() -> void:
	# Distinct temporary silhouettes, all using the same telegraph colour.
	var ink := Color(0.4, 0.65, 0.35)
	match role:
		"rusher": draw_colored_polygon(PackedVector2Array([Vector2(-16, 7), Vector2(0, -30), Vector2(16, 7)]), ink)
		"shooter":
			draw_circle(Vector2(0, -12), 13.0, ink)
			draw_line(Vector2(0, -12), facing * 30.0 + Vector2(0, -12), ink, 8.0)
		"shield":
			draw_rect(Rect2(-20, -29, 40, 36), ink)
			draw_line(facing * 23.0 + facing.orthogonal() * 22.0, facing * 23.0 - facing.orthogonal() * 22.0, Color(0.8, 0.8, 0.65), 8.0)
		"elite":
			draw_circle(Vector2(0, -15), 23.0, ink)
			draw_line(Vector2(-24, -28), Vector2(-12, -45), ink, 9.0)
			draw_line(Vector2(24, -28), Vector2(12, -45), ink, 9.0)
	if state == "windup":
		var colour := Color(1.0, 0.65, 0.15, 0.85)
		if role == "shooter":
			draw_line(Vector2.ZERO, facing * reach(), colour, 4.0)
		elif role == "shield":
			draw_arc(Vector2.ZERO, reach(), 0, TAU, 32, colour, 3.0)
		else:
			var tip := facing * reach()
			draw_line(Vector2.ZERO, tip + facing.orthogonal() * 18.0, colour, 3.0)
			draw_line(Vector2.ZERO, tip - facing.orthogonal() * 18.0, colour, 3.0)
		# Continuous fill, no blinking/strobe.
		draw_circle(Vector2(0, -45), 3.0 + 5.0 * clampf(elapsed / windup_time(), 0.0, 1.0), colour)
