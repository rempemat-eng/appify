class_name SliceEnemy
extends CharacterBody2D
## C61 independent actor: LimboAI HSM, shared attack reservations, no save/reward writes.
##
## Home, health and waking (Matt, 10 Nov; the same rules as the mossling, actors/enemy.gd):
##   - No healing on the walk home; HOME_HEAL_TIME after it is home again it is at full health.
##   - A hit wakes it when the archer is within WAKE of it and inside its leash, and its idle camp mates
##     within ALERT of it with it, if the archer is inside their leash. A hit on the walk home turns it round.
##     A rusher woken that way runs in at RUN_IN times its speed until its first wind-up (a proposal).
##   - It can only be hurt by someone it can come for (`can_come_for`). From anywhere else the arrow
##     glances off (enemies/glance.gd). (Stepping in and out over its leash line still beats it: it turns
##     for home the step the player is outside, and wakes again on the next hit from inside.)
##   - It steers round solids (enemies/steer.gd), gives up a walk home that takes too long (it is put at
##     home, no fade) and an approach that gains no ground for CHASE_GIVE_UP (it walks home and for
##     NO_WAY_TIME neither wakes to a shot nor is hurt by one).
##   - For ARRIVAL_GRACE after a zone becomes ready it does not notice the player by nearness (the
##     Undercroft's first rusher reached the start 1.8 s after every load and every time the player got up).
signal died
signal committed
signal released
signal glanced
const DENSITY := 3.0
const LEASH := 140.0 * DENSITY
const NOTICE := 100.0 * DENSITY     ## it notices the player this near
const WAKE := 110.0 * DENSITY       ## a hit wakes it when the archer is this near
const ALERT := NOTICE               ## idle camp mates this near wake with it
const HOME_HEAL_TIME := 3.0
const LEASH_GIVE_UP := 3.0
const LEASH_SPEED := 48.0 * DENSITY
const ARRIVAL_GRACE := 2.5
const RUN_IN := 1.6
const CHASE_GIVE_UP := 2.5
const GAIN := 12.0
const NO_WAY_TIME := 6.0
@export_enum("rusher", "shooter", "shield", "elite") var role := "rusher"
var slots: SliceAttackSlots
var target: Node2D
var home := Vector2.ZERO
var hp := 4
var max_hp := 4
var dead := false
var state := "idle"
var elapsed := 0.0
var facing := Vector2.DOWN
var hsm: LimboHSM
var shot: SliceEnemyShot
var _struck := false
var _reserved := false
var steer := EnemySteer.new()
var glance_t := 0.0
var _home_t := 0.0
var _leash_t := 0.0
var _leash_budget := 0.0
var _grace := 0.0
var _run_in := false
var _closest := INF
var _stuck_t := 0.0
var _no_way_t := 0.0

func windup_time() -> float:
	return 0.65 if role == "elite" else 0.95

func reach() -> float:
	return 85.0 * DENSITY if role == "shooter" else 22.0 * DENSITY

func _ready() -> void:
	add_to_group("enemy")
	home = global_position
	max_hp = 12 if role == "elite" else (8 if role == "shield" else 4)
	hp = max_hp
	wall_min_slide_angle = 0.0   # slide along a wall met at any angle
	Zones.zone_changed.connect(_on_zone_ready)
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

func _on_zone_ready(_zone: Zone) -> void:
	_grace = ARRIVAL_GRACE

func _changed(current: LimboState, _previous: LimboState) -> void:
	state = str(current.name)
	elapsed = 0.0
	velocity = Vector2.ZERO
	steer.reset()
	_closest = INF
	_stuck_t = 0.0
	if state != "approach":
		_run_in = false
	if state == "idle":
		_home_t = 0.0
	elif state == "leash":
		_leash_t = 0.0
		_leash_budget = LEASH_GIVE_UP + 2.0 * global_position.distance_to(home) / LEASH_SPEED
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
	glance_t = maxf(glance_t - delta, 0.0)
	_grace = maxf(_grace - delta, 0.0)
	_no_way_t = maxf(_no_way_t - delta, 0.0)
	if state != "idle" and state != "leash" and _outside_leash():
		_cancel_attack()
		hsm.dispatch(&"leash")
	hsm.update(maxf(delta, 0.0))
	queue_redraw()

func _outside_leash() -> bool:
	return not is_instance_valid(target) or global_position.distance_to(home) > LEASH or home.distance_to(target.global_position) > LEASH

## True when it can come for someone standing at `at`: inside its leash, and, while it is idle or walking
## home, near enough to notice a shot from.
func can_come_for(at: Vector2) -> bool:
	if _no_way_t > 0.0 or home.distance_to(at) > LEASH or global_position.distance_to(home) > LEASH:
		return false
	return (state != "idle" and state != "leash") or global_position.distance_to(at) <= WAKE

func _update_state(delta: float) -> void:
	elapsed += delta
	match state:
		"idle":
			if hp < max_hp:
				_home_t += delta
				if _home_t >= HOME_HEAL_TIME:
					hp = max_hp
			if _grace <= 0.0 and _no_way_t <= 0.0 and is_instance_valid(target) and not _outside_leash() and global_position.distance_to(target.global_position) < NOTICE:
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
			elif distance > reach():
				# no ground gained for too long (circling a pocket, pushing at a solid): go home
				if distance < _closest - GAIN:
					_closest = distance
					_stuck_t = 0.0
				else:
					_stuck_t += delta
					if _stuck_t >= CHASE_GIVE_UP:
						_no_way_t = NO_WAY_TIME
						hsm.dispatch(&"leash")
						return
				velocity = steer.direction(self, facing, delta) * 34.0 * DENSITY * (RUN_IN if _run_in else 1.0)
			else:
				velocity = facing.orthogonal() * 16.0 * DENSITY
		"windup":
			velocity = Vector2.ZERO  # direction locks at commitment; no tracking during tell
			if elapsed >= windup_time():
				if role == "shooter" and not _can_commit():
					_cancel_attack()
					hsm.dispatch(&"recover")
					return
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
			# no healing on the way; a walk that cannot get round what is in the way is given up cleanly
			_leash_t += delta
			if global_position.distance_to(home) <= 4.0 or _leash_t > _leash_budget:
				global_position = home
				hsm.dispatch(&"idle")
			else:
				velocity = steer.direction(self, global_position.direction_to(home), delta) * LEASH_SPEED

func _can_commit() -> bool:
	if role != "shooter":
		return true
	# Prevent off-screen fire, including when the scene is placed on a large map.
	var screen := get_viewport_rect()
	var point := get_global_transform_with_canvas().origin
	if not screen.has_point(point):
		return false
	# the same sight the player's arrow has: low solids (a bench, a stump, water) do not block it
	return not Arrow.walled_off(get_world_2d().direct_space_state, global_position, target.global_position)

## Returns whether the hit counted (false when it glanced off).
func take_hit(amount: int, dir: Vector2, _knockback: float = 200.0) -> bool:
	if dead or amount <= 0:
		return false
	var archer: Node2D = target if is_instance_valid(target) else null
	if archer != null and not can_come_for(archer.global_position):
		glance_t = Glance.TIME
		glanced.emit()
		queue_redraw()
		return false
	if archer != null and (state == "idle" or state == "leash"):
		_wake(archer.global_position)
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
	return true

## Woken by a hit: it comes for the archer, and so do its idle camp mates near enough to hear it.
func _wake(at: Vector2) -> void:
	_grace = 0.0
	_run_in = role == "rusher"
	hsm.dispatch(&"approach")
	var camp := get_parent()
	if camp == null:
		return
	for mate in camp.get_children():
		if mate != self and mate.has_method("hear_alert") and global_position.distance_to((mate as Node2D).global_position) <= ALERT:
			mate.hear_alert(at)

## A camp mate was hit: wake too, when idle and the archer is inside its leash.
func hear_alert(at: Vector2) -> void:
	if dead or state != "idle" or _no_way_t > 0.0 or home.distance_to(at) > LEASH:
		return
	_grace = 0.0
	_run_in = role == "rusher"
	hsm.dispatch(&"approach")

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
	Glance.draw(self, Vector2(0, -54), glance_t)
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
