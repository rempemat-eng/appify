class_name Enemy
extends CharacterBody2D
## A shardstruck mossling driven by a LimboAI hierarchical state machine (ported from the evaluation
## slice): idle -> chase -> windup (0.5 s ground telegraph) -> lunge -> recover -> chase, leashing home
## when dragged too far or when the target runs off. It dies at 0 hp and reports `died` to its Camp.
## Distances are in world px times DENSITY. The sprite is a placeholder until the cast lands.
##
## Home, health and waking (Matt, 10 Nov):
##   - It does not heal on the walk home. HOME_HEAL_TIME after it is home again it is at full health.
##   - A hit wakes it when the archer is within `wake_radius` (330), and its idle camp mates within its
##     aggro radius with it, if the archer stands on ground they keep to: the camp answers a shot together.
##     A hit on the walk home turns it round. Woken by a shot (or a mate's), it keeps coming for
##     PROVOKED_TIME even past its `lose_radius` (the arrow's knock pushed a mossling shot from 320 past
##     330, where it gave up, went home and was shot again asleep). Hurt by the player, it also keeps
##     coming across its leash for PROVOKED_TIME after the last hit (Claude A, 11 Nov; a glance does not
##     count), and the chase give-up below still applies in that time.
##     Woken that way it runs in at RUN_IN times its speed until its first wind-up (a proposal, 11 Nov:
##     no health or damage number changes; a fight begun by walking up to it is as before).
##   - Asleep, chasing or walking home it can only be hurt by someone it can come for (`can_come_for`):
##     standing within reach of the ground it keeps to and, while it is asleep or walking home, within
##     `wake_radius` of it. From anywhere else the arrow glances off (enemies/glance.gd) and it does not
##     react. While it winds up, lunges or recovers it can always be hurt: whoever it strikes at can
##     strike back (played 10 Nov: its lunge hit a player whose arrows glanced off it at 9 px).
##   - It steers round solids (enemies/steer.gd). If it still cannot get home in a fair time (twice the
##     straight walk plus LEASH_GIVE_UP) it gives up the walk and is put at home. A chase that gains no
##     ground on its target for CHASE_GIVE_UP is given up too: it walks home, and on that walk a shot
##     neither turns it round nor hurts it. Once it is home it answers a shot like any other.
##   - At most two enemies wind up or strike at once (SliceAttackSlots, shared with the Undercroft's
##     creatures; Claude A, 11 Nov: three mosslings lining up their tells downed a player in 0.5 s). A
##     mossling in reach that has no slot steps round its target until one is free.
##   - For ARRIVAL_GRACE after a zone becomes ready (a load, a door, getting up after a defeat) it does not
##     notice the player by nearness; a hit still wakes it.

signal state_changed(state: StringName)
signal died
signal glanced

const DENSITY := 3.0
const WINDUP_TIME := 0.5
const LUNGE_TIME := 0.16
const LUNGE_SPEED := 150.0 * DENSITY
const RECOVER_TIME := 0.55
const HOME_HEAL_TIME := 3.0     ## full health this long after it is home again
const LEASH_GIVE_UP := 3.0      ## seconds over twice the straight walk before it gives up walking home
const ARRIVAL_GRACE := 2.5      ## no noticing by nearness this long after the zone becomes ready
const RUN_IN := 1.6             ## woken by a shot it runs in this much faster, until its first wind-up
const CHASE_GIVE_UP := 2.5      ## a chase that gets no nearer its target for this long is given up
const GAIN := 12.0              ## "ground gained": this much nearer the target than it has been in this chase
const PROVOKED_TIME := 3.0      ## after a hit it does not give the archer up for being far, this long
const HOP_FADE := 0.3           ## it fades in at home after giving up the walk (not under reduced motion)

@export var aggro_radius := 55.0 * DENSITY
@export var lose_radius := 110.0 * DENSITY
@export var leash_radius := 100.0 * DENSITY  ## from home
@export var wake_radius := 110.0 * DENSITY   ## a hit wakes it when the archer is this near
@export var attack_range := 17.0 * DENSITY
@export var speed := 39.0 * DENSITY
@export var max_hp := 5          ## 3 until 11 Nov (Matt): a lone mossling now lives long enough to arrive

var home := Vector2.ZERO
var target: Node2D
var hp := 5
var state: StringName = &"idle"
var telegraph := 0.0
var attack_dir := Vector2.RIGHT
var hsm: LimboHSM
var dead := false
var _t := 0.0
var _struck := false
var _stagger := 0.0
var _flash := 0.0
var steer := EnemySteer.new()
var glance_t := 0.0
var _home_t := 0.0
var _leash_t := 0.0
var _leash_budget := 0.0
var _grace := 0.0
var _provoked := 0.0
var _pursue := 0.0             ## hurt by the player: it keeps coming across its leash this long (PROVOKED_TIME)
var _run_in := false
var _closest := INF
var _stuck_t := 0.0
var _gave_up := false           ## walking home from a chase it gave up: deaf to shots until it is home
var _fade := 0.0
var _slot := false              ## holds one of the shared attack slots (wind-up, lunge, recover)
var slots: SliceAttackSlots

@onready var sprite: Sprite2D = $Sprite

func _ready() -> void:
	add_to_group("enemy")
	hp = max_hp
	home = global_position
	wall_min_slide_angle = 0.0   # slide along a wall met at any angle (the default refuses under 15 degrees)
	slots = SliceAttackSlots.new()   # the reservations are shared by every pool (attack_slots.gd)
	slots.name = "AttackSlots"
	add_child(slots)
	Zones.zone_changed.connect(_on_zone_ready)
	_build_hsm()

func _on_zone_ready(_zone: Zone) -> void:
	_grace = ARRIVAL_GRACE

func _build_hsm() -> void:
	hsm = LimboHSM.new()
	hsm.name = "HSM"
	hsm.update_mode = LimboHSM.MANUAL
	add_child(hsm)
	var idle := LimboState.new().named("idle").call_on_enter(_idle_enter).call_on_update(_idle)
	var chase := LimboState.new().named("chase").call_on_enter(_chase_enter).call_on_update(_chase)
	var windup := LimboState.new().named("windup").call_on_enter(_windup_enter).call_on_update(_windup)
	var lunge := LimboState.new().named("lunge").call_on_enter(_lunge_enter).call_on_update(_lunge)
	var recover := LimboState.new().named("recover").call_on_enter(_reset_t).call_on_update(_recover)
	var leash := LimboState.new().named("leash").call_on_enter(_leash_enter).call_on_update(_leash)
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
	hsm.add_transition(leash, chase, &"aggro")   # hit on the walk home by someone it can come for
	hsm.initial_state = idle
	hsm.active_state_changed.connect(_on_state_changed)
	hsm.initialize(self)
	hsm.set_active(true)

func _on_state_changed(current: LimboState, _previous: LimboState) -> void:
	state = StringName(current.name)
	telegraph = 0.0
	if state != &"windup" and state != &"lunge" and state != &"recover":
		_free_slot()
	state_changed.emit(state)

func _physics_process(delta: float) -> void:
	if dead:
		return
	if target == null or not is_instance_valid(target):
		target = get_tree().get_first_node_in_group("player") as Node2D
	_flash = maxf(_flash - delta, 0.0)
	glance_t = maxf(glance_t - delta, 0.0)
	_fade = maxf(_fade - delta, 0.0)
	_grace = maxf(_grace - delta, 0.0)
	_provoked = maxf(_provoked - delta, 0.0)
	_pursue = maxf(_pursue - delta, 0.0)
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
	# hurt by the player, it keeps coming across its leash for PROVOKED_TIME (Claude A's call, 11 Nov: the
	# leash-line dance beat every enemy); the give-up in _chase still applies, and it never leaves the zone
	return (global_position.distance_to(home) > leash_radius and _pursue <= 0.0) \
		or (_target_dist() > lose_radius and _provoked <= 0.0)

## True when `at` is on the ground it keeps to: its leash lets it get within striking distance of it.
func on_its_ground(at: Vector2) -> bool:
	return home.distance_to(at) <= leash_radius + attack_range

## True when someone standing at `at` may hurt it. Always while it winds up, lunges or recovers. Otherwise
## when it can come for them: on its ground and, while it is asleep or walking home, near enough to notice
## a shot from; and not on the walk home from a chase it gave up for want of a way.
func can_come_for(at: Vector2) -> bool:
	if state == &"windup" or state == &"lunge" or state == &"recover":
		return true
	if _pursue > 0.0 and state == &"chase":
		return true                  # coming for the archer across its leash: they can strike back
	if (_gave_up and state == &"leash") or not on_its_ground(at):
		return false
	return (state != &"idle" and state != &"leash") or global_position.distance_to(at) <= wake_radius

func _idle_enter() -> void:
	_home_t = 0.0
	_gave_up = false             # at home it is never deaf
	_run_in = false

func _chase_enter() -> void:
	steer.reset()
	_gave_up = false
	_closest = INF
	_stuck_t = 0.0

func _idle(delta: float) -> void:
	velocity = Vector2.ZERO
	if hp < max_hp:
		_home_t += delta
		if _home_t >= HOME_HEAL_TIME:
			hp = max_hp
	if _grace > 0.0:
		return
	if target != null and _target_dist() < aggro_radius and home.distance_to(target.global_position) < leash_radius:
		hsm.dispatch(&"aggro")

func _chase(delta: float) -> void:
	if _should_leash():
		hsm.dispatch(&"leash")
		return
	if _target_dist() < attack_range:
		if EnemySteer.line_clear(self, target.global_position):
			if slots.acquire(self):
				_slot = true
				hsm.dispatch(&"in_range")
				return
			# two others are winding up or striking: it steps round its target and waits its turn
			_stuck_t = 0.0
			velocity = global_position.direction_to(target.global_position).orthogonal() * speed * 0.4
			return
		# a low solid between (arrows cross it, a bite does not): it walks round it (Matt, 11 Nov)
	# no ground gained on the target for too long (pushing at a solid, circling a pocket): go home
	if _target_dist() < _closest - GAIN:
		_closest = _target_dist()
		_stuck_t = 0.0
	else:
		_stuck_t += delta
		if _stuck_t >= CHASE_GIVE_UP:
			_gave_up = true
			hsm.dispatch(&"leash")
			return
	var pace := speed * (RUN_IN if _run_in else 1.0)
	velocity = steer.direction(self, global_position.direction_to(target.global_position), delta, target.global_position) * pace

func _reset_t() -> void:
	_t = 0.0

func _windup_enter() -> void:
	_t = 0.0
	_run_in = false
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

func _leash_enter() -> void:
	steer.reset()
	_pursue = 0.0
	_run_in = false
	_leash_t = 0.0
	_leash_budget = LEASH_GIVE_UP + 2.0 * global_position.distance_to(home) / (speed * 1.3)

## The walk home: no healing on the way (that waits until it has been home HOME_HEAL_TIME).
func _leash(delta: float) -> void:
	_leash_t += delta
	if global_position.distance_to(home) < 3.0:
		_arrive_home()
		return
	if _leash_t > _leash_budget:
		# it could not get round whatever is in the way: give the walk up cleanly
		if not SaveGame.setting("reduced_motion", false):
			_fade = HOP_FADE
		_arrive_home()
		return
	velocity = steer.direction(self, global_position.direction_to(home), delta, home) * speed * 1.3

func _arrive_home() -> void:
	global_position = home
	velocity = Vector2.ZERO
	hsm.dispatch(&"home")

# --- damage -------------------------------------------------------------
## Returns whether the hit counted (false when it glanced off).
func take_hit(amount: int, dir: Vector2, knockback: float = 200.0) -> bool:
	if dead:
		return false
	var archer := _archer()
	if archer != null and not can_come_for(archer.global_position):
		glance_t = Glance.TIME
		Glance.clink(global_position)
		glanced.emit()
		return false
	hp -= amount
	_flash = 0.12
	if archer != null:
		_provoked = PROVOKED_TIME
		_pursue = PROVOKED_TIME
		if hp > 0 and (state == &"idle" or state == &"leash"):
			_wake(archer.global_position)
	if state != &"windup" and state != &"lunge":
		_stagger = 0.14
		velocity = dir * knockback
	if hp <= 0:
		_die()
	return true

## Whoever hits it: the player (the only thing that shoots or swings at enemies).
func _archer() -> Node2D:
	return target if target != null and is_instance_valid(target) else null

## Woken by a hit: it comes for the archer, and so do its idle camp mates near enough to hear it.
func _wake(at: Vector2) -> void:
	_grace = 0.0
	_run_in = true
	hsm.dispatch(&"aggro")
	var camp := get_parent()
	if camp == null:
		return
	for mate in camp.get_children():
		if mate != self and mate.has_method("hear_alert") and global_position.distance_to((mate as Node2D).global_position) <= aggro_radius:
			mate.hear_alert(at)

## A camp mate was hit: wake too, when idle and the archer stands on ground it keeps to.
func hear_alert(at: Vector2) -> void:
	if dead or state != &"idle" or not on_its_ground(at):
		return
	_grace = 0.0
	_run_in = true
	_provoked = PROVOKED_TIME
	hsm.dispatch(&"aggro")

func _free_slot() -> void:
	if _slot and is_instance_valid(slots):
		slots.release(self)
	_slot = false

func _exit_tree() -> void:
	_free_slot()

func _die() -> void:
	dead = true
	_free_slot()
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
	if _fade > 0.0:
		sprite.modulate.a = 1.0 - _fade / HOP_FADE

func _draw() -> void:
	Glance.draw(self, Vector2(0, -42), glance_t)
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
