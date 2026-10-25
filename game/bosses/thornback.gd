class_name Thornback
extends CharacterBody2D
## The Thornback, the Undercroft's boss (docs/vision/vertical-slice.md beat 6): a boar turned wild by a
## splinter of the starfall shard in its bramble shell. Freed, never killed: at 0 strength the shell cracks
## and falls away and it lies down calm (`died` is the camp's "freed").
##
## Behaviour is a LimboAI state machine, stepped by `step(delta)` (also from the tests):
##   dormant  -> approach when the player is inside the arena
##   approach -> windup when an attack is chosen and the shared attack cap (SliceAttackSlots) allows it
##   windup   -> act after the attack's wind-up (never under MIN_WINDUP): the telegraph fills, no blinking
##   act      -> charge (a locked lane; hitting the arena's edge staggers it), volley (a ring of thorns),
##               slam (a ring around it); the attack holds its reservation until its thorns are gone
##   recover  -> approach;  stagger (the window: double damage) -> recover;  roar (the phase change) -> approach
##   freed    -> calm, for good
## Two phases: below PHASE2_AT strength it roars once, winds up faster (still at least MIN_WINDUP), adds the
## slam and throws more thorns. At most one attack at a time; it never leaves `arena` (texels, zone space)
## and goes back to sleep at home when the player leaves the arena. Placeholder numbers (vertical-slice.md).

signal died
signal phase_changed(phase: int)
signal telegraph_started(attack: String, seconds: float)
signal attack_released(attack: String)
signal staggered

const DENSITY := 3.0
const MAX_HP := 40
const PHASE2_AT := 20
const MIN_WINDUP := 0.5
const WINDUP := {"charge": [0.8, 0.6], "volley": [0.9, 0.7], "slam": [1.0, 0.75]}
const PHASE_ATTACKS := [["charge", "volley"], ["charge", "slam", "volley"]]
const MOVE_SPEED := 22.0 * DENSITY
const CHARGE_SPEED := 125.0 * DENSITY
const CHARGE_MAX := 1.2
const RECOVER := [0.8, 0.55]
const STAGGER_TIME := 1.6
const SLAM_STAGGER := 0.9
const ROAR_TIME := 1.1
const VOLLEY := [8, 12]
const SLAM_RADIUS := 34.0 * DENSITY
const BODY_RADIUS := 20.0 * DENSITY
const NEAR := 46.0 * DENSITY
const ART := "res://bosses/thornback/art/"

@export var arena := Rect2()   ## texels in the zone; empty = no limit (tests)

var hp := MAX_HP
var phase := 1
var state := "dormant"
var attack := ""
var elapsed := 0.0
var windup_time := 0.0
var aim := Vector2.RIGHT
var facing := "S"
var target: Node2D
var home := Vector2.ZERO
var freed := false
var thorns: Array[Node] = []
var hsm: LimboHSM
var sprite: AnimatedSprite2D
var slots: SliceAttackSlots
var manifest := {}
var marks: Node2D   ## the telegraphs, drawn on the floor under everyone


var _next := 0
var _struck := false
var _reserved := false
var _hold := 0.0
var _hurt_t := 0.0
var _roared := false
var _travel := 0.0

func _ready() -> void:
	add_to_group("enemy")
	add_to_group("thornback_live")
	home = global_position
	collision_layer = 4
	collision_mask = 1
	motion_mode = CharacterBody2D.MOTION_MODE_FLOATING
	var shape := CollisionShape2D.new()
	var c := CircleShape2D.new()
	c.radius = BODY_RADIUS
	shape.shape = c
	shape.position = Vector2(0, -6.0 * DENSITY)
	add_child(shape)
	slots = SliceAttackSlots.new()
	add_child(slots)
	marks = Node2D.new()
	marks.name = "Telegraph"
	marks.z_index = -5
	marks.draw.connect(_draw_telegraph)
	add_child(marks)
	_build_sprite()
	hsm = LimboHSM.new()
	hsm.update_mode = LimboHSM.MANUAL
	add_child(hsm)
	var states := {}
	for key in ["dormant", "approach", "windup", "act", "recover", "stagger", "roar", "freed"]:
		var st := LimboState.new().named(key).call_on_update(_update_state)
		hsm.add_child(st)
		states[key] = st
	for a in states:
		for b in states:
			if a != b:
				hsm.add_transition(states[a], states[b], StringName(b))
	hsm.initial_state = states.dormant
	hsm.active_state_changed.connect(_changed)
	hsm.initialize(self)
	hsm.set_active(true)
	_play("idle")

# --- the art ---------------------------------------------------------------------------------------
func _build_sprite() -> void:
	sprite = AnimatedSprite2D.new()
	sprite.name = "Sprite"
	add_child(sprite)
	var f := FileAccess.open(ART + "manifest.json", FileAccess.READ)
	if f == null:
		push_error("Thornback: no manifest")
		return
	manifest = JSON.parse_string(f.get_as_text())
	var frames := SpriteFrames.new()
	frames.remove_animation(&"default")
	var size: Array = manifest.frame_size
	for clip in manifest.clips:
		var info: Dictionary = manifest.clips[clip]
		for fc in manifest.directions:
			var anim := StringName("%s_%s" % [clip, fc])
			frames.add_animation(anim)
			frames.set_animation_loop(anim, bool(info.loop))
			frames.set_animation_speed(anim, 1.0)
			var tex: Texture2D = load(ART + "sheets/%s_%s.png" % [clip, fc])
			for i in int(info.frames):
				var at := AtlasTexture.new()
				at.atlas = tex
				at.region = Rect2(i * size[0], 0, size[0], size[1])
				frames.add_frame(anim, at, float(info.durations[i]))
	sprite.sprite_frames = frames
	sprite.centered = false
	var pivot: Array = manifest.foot_pivot
	sprite.offset = -Vector2(pivot[0], pivot[1])

func clip_length(clip: String) -> float:
	var total := 0.0
	for d in manifest.clips[clip].durations:
		total += float(d)
	return total

func _play(clip: String, seconds := 0.0) -> void:
	if sprite == null or sprite.sprite_frames == null:
		return
	var anim := StringName("%s_%s" % [clip, facing])
	if not sprite.sprite_frames.has_animation(anim):
		return
	sprite.speed_scale = clip_length(clip) / seconds if seconds > 0.0 else 1.0
	if sprite.animation != anim:
		sprite.play(anim)
	elif not sprite.is_playing():
		sprite.play(anim)

func _face(v: Vector2) -> void:
	var fc := CastSprite.facing_for(v, facing)
	if fc != facing and sprite != null and sprite.sprite_frames != null:
		facing = fc
		var clip := String(sprite.animation).rsplit("_", true, 1)[0]
		var anim := StringName("%s_%s" % [clip, facing])
		if sprite.sprite_frames.has_animation(anim):
			var fr := sprite.frame
			var prog := sprite.frame_progress
			sprite.play(anim)
			sprite.set_frame_and_progress(fr, prog)

# --- stepping --------------------------------------------------------------------------------------
func _physics_process(delta: float) -> void:
	if not is_instance_valid(target):
		target = get_tree().get_first_node_in_group("player") as Node2D
	step(delta)
	if state in ["approach", "act"]:
		move_and_slide()
		if state == "act" and attack == "charge" and get_slide_collision_count() > 0:
			_end_charge(true)
	_keep_in_arena()
	marks.queue_redraw()

## Deterministic advancement (the tests call it without physics).
func step(delta: float) -> void:
	_hurt_t = maxf(_hurt_t - delta, 0.0)
	var live: Array[Node] = []
	for n in thorns:
		if is_instance_valid(n) and not n.is_queued_for_deletion():
			live.append(n)
	thorns = live
	hsm.update(maxf(delta, 0.0))

func _changed(current: LimboState, _previous: LimboState) -> void:
	state = str(current.name)
	elapsed = 0.0
	velocity = Vector2.ZERO
	match state:
		"dormant": _play("idle")
		"approach": _play("move")
		"recover": _play("recover")
		"stagger": _play("stagger")
		"roar": _play("volley_windup", ROAR_TIME)
		"freed": _play("freed")

func player_in_arena() -> bool:
	if not is_instance_valid(target):
		return false
	return arena.size == Vector2.ZERO or arena.has_point(target.global_position - _zone_origin())

func _zone_origin() -> Vector2:
	var p := get_parent()
	while p != null and not (p is Zone):
		p = p.get_parent()
	return (p as Node2D).global_position if p is Node2D else Vector2.ZERO

func _keep_in_arena() -> void:
	if arena.size == Vector2.ZERO:
		return
	var o := _zone_origin()
	var r := arena.grow(-BODY_RADIUS * 0.6)
	var local := global_position - o
	var clamped := Vector2(clampf(local.x, r.position.x, r.end.x), clampf(local.y, r.position.y, r.end.y))
	if clamped != local:
		global_position = clamped + o
		if state == "act" and attack == "charge":
			_end_charge(true)

func _update_state(delta: float) -> void:
	elapsed += delta
	match state:
		"dormant":
			if global_position.distance_to(home) > 4.0:
				velocity = global_position.direction_to(home) * MOVE_SPEED
				global_position += velocity * delta
				_face(velocity)
			elif player_in_arena():
				hsm.dispatch(&"approach")
		"approach":
			if not player_in_arena():
				_release_slot()
				hsm.dispatch(&"dormant")
				return
			if not _roared and hp <= PHASE2_AT:
				_roared = true
				hsm.dispatch(&"roar")
				return
			var to := target.global_position - global_position
			_face(to)
			var choice := choose_attack(to.length())
			if elapsed >= 0.35 and attack_count() == 0 and slots.acquire(self):
				_reserved = true
				_start_windup(choice, to)
				return
			velocity = to.normalized() * MOVE_SPEED if to.length() > NEAR * 0.7 else Vector2.ZERO
			if _hurt_t > 0.0:
				_play("hurt")
			else:
				_play("move" if velocity != Vector2.ZERO else "idle")
		"windup":
			velocity = Vector2.ZERO
			if elapsed >= windup_time:
				_release()
		"act":
			match attack:
				"charge":
					velocity = aim * CHARGE_SPEED
					_travel += delta
					if not _struck and is_instance_valid(target) and target.global_position.distance_to(global_position) < BODY_RADIUS + 10.0 * DENSITY \
							and target.has_method("take_damage"):
						target.take_damage(2, aim)
						_struck = true
					if _travel >= CHARGE_MAX:
						_end_charge(false)
				"volley":
					if thorns.is_empty() and elapsed >= 0.3:
						_finish_attack(RECOVER[phase - 1])
				"slam":
					if elapsed >= clip_length("slam"):
						_finish_attack(0.0)
						_stagger(SLAM_STAGGER)
		"recover":
			velocity = Vector2.ZERO
			if elapsed >= _hold:
				hsm.dispatch(&"approach")
		"stagger":
			velocity = Vector2.ZERO
			if elapsed >= _hold:
				_hold = RECOVER[phase - 1] * 0.6
				hsm.dispatch(&"recover")
		"roar":
			velocity = Vector2.ZERO
			if elapsed >= ROAR_TIME:
				hsm.dispatch(&"approach")
		"freed":
			velocity = Vector2.ZERO
			if not sprite.is_playing() or elapsed >= clip_length("freed"):
				_play("calm")

## Which attack comes next: by phase, in turn, but a charge from far and a slam only when near.
func choose_attack(distance: float) -> String:
	var list: Array = PHASE_ATTACKS[phase - 1]
	var pick: String = list[_next % list.size()]
	if pick == "slam" and distance > NEAR * 1.4:
		pick = "charge"
	if pick == "charge" and distance < NEAR * 0.6:
		pick = "slam" if phase == 2 else "volley"
	return pick

func windup_for(name: String) -> float:
	return maxf(MIN_WINDUP, float(WINDUP[name][phase - 1]))

func _start_windup(name: String, to: Vector2) -> void:
	_next += 1
	attack = name
	aim = to.normalized() if to.length() > 0.01 else Vector2.RIGHT
	_face(aim)
	windup_time = windup_for(name)
	hsm.dispatch(&"windup")
	_play(name + "_windup", windup_time)
	telegraph_started.emit(name, windup_time)

func _release() -> void:
	_struck = false
	_travel = 0.0
	hsm.dispatch(&"act")
	attack_released.emit(attack)
	match attack:
		"charge":
			_play("charge")
		"volley":
			_play("volley")
			_throw_thorns(VOLLEY[phase - 1])
		"slam":
			_play("slam")
			if is_instance_valid(target) and target.global_position.distance_to(global_position) < SLAM_RADIUS \
					and target.has_method("take_damage"):
				target.take_damage(2, global_position.direction_to(target.global_position))

func _throw_thorns(n: int) -> void:
	var host := get_parent()
	for i in n:
		var a := TAU * float(i) / float(n) + (PI / float(n) if phase == 2 else 0.0)
		var th := ThornbackThorn.new()
		th.direction = Vector2.from_angle(a)
		th.arena = arena
		th.origin = _zone_origin()
		host.add_child(th)
		th.global_position = global_position + th.direction * BODY_RADIUS + Vector2(0, -4.0 * DENSITY)
		thorns.append(th)

func _end_charge(hit_wall: bool) -> void:
	if state != "act" or attack != "charge":
		return
	velocity = Vector2.ZERO
	if hit_wall:
		_finish_attack(0.0)
		_stagger(STAGGER_TIME)
	else:
		_finish_attack(RECOVER[phase - 1])

func _finish_attack(hold: float) -> void:
	attack = ""
	_release_slot()
	_hold = hold
	if hold > 0.0:
		hsm.dispatch(&"recover")

func _stagger(seconds: float) -> void:
	_hold = seconds
	hsm.dispatch(&"stagger")
	staggered.emit()

func _release_slot() -> void:
	if _reserved and is_instance_valid(slots):
		slots.release(self)
	_reserved = false

## An attack is live from its wind-up until its last thorn is gone.
func attack_count() -> int:
	return (1 if attack != "" else 0) + (1 if attack == "" and not thorns.is_empty() else 0)

func is_staggered() -> bool:
	return state == "stagger"

# --- being hit -------------------------------------------------------------------------------------
func take_hit(amount: int, _dir: Vector2, _knockback: float = 0.0) -> void:
	if freed or amount <= 0:
		return
	if state == "dormant":
		hsm.dispatch(&"approach")
	hp -= amount * (2 if is_staggered() else 1)
	_hurt_t = 0.2
	if hp <= 0:
		hp = 0
		_free()
	elif hp <= PHASE2_AT and phase == 1:
		phase = 2
		phase_changed.emit(2)
		if state in ["approach", "recover"]:
			_roared = true
			hsm.dispatch(&"roar")

func _free() -> void:
	freed = true
	attack = ""
	_release_slot()
	for th in thorns:
		if is_instance_valid(th):
			th.queue_free()
	thorns.clear()
	collision_layer = 0
	remove_from_group("enemy")
	hsm.dispatch(&"freed")
	died.emit()

func _exit_tree() -> void:
	_release_slot()

# --- the floor under it: its contact shadow, and the telegraphs as marks in the dust ---------------
## Colours from the house ramps: the dust (path 4), the scuffs (path 2), the lit edge (lamp 4), shadow (soot 0).
const DUST := Color("#c39771")
const SCUFF := Color("#885c4b")
const LIT := Color("#f5d49c")
const SHADOW := Color("#1c1426")

func _draw_telegraph() -> void:
	# the contact shadow: a soft-edged oval under the body, pushed a little down-right (light upper left)
	marks.draw_set_transform(Vector2(6, 3), 0.0, Vector2(1.0, 0.34))
	marks.draw_circle(Vector2.ZERO, BODY_RADIUS * 1.7, Color(SHADOW, 0.28))
	marks.draw_circle(Vector2.ZERO, BODY_RADIUS * 1.35, Color(SHADOW, 0.3))
	marks.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	if state != "windup":
		return
	var k := clampf(elapsed / maxf(windup_time, 0.01), 0.0, 1.0)
	match attack:
		"charge":
			var length := _lane_length()
			var side := aim.orthogonal()
			var half := BODY_RADIUS * 0.9
			# the whole lane, faint, so it reads from the first frame; scuffed furrows along both edges
			var far := aim * length
			marks.draw_colored_polygon(PackedVector2Array([side * half, far + side * half, far - side * half, -side * half]), Color(DUST, 0.14))
			var d := 6.0
			while d < length:
				for sgn: float in [-1.0, 1.0]:
					var p: Vector2 = aim * d + side * half * sgn
					marks.draw_line(_px(p), _px(p + aim * 9.0), Color(SCUFF, 0.75), 3.0)
				d += 15.0
			# the dust kicked up so far, and the lit edge that runs ahead of it
			var reach := length * k
			var i := 0
			d = 4.0
			while d < reach:
				var off := (float((i * 37) % 11) / 10.0 - 0.5) * half * 1.6
				marks.draw_rect(Rect2(_px(aim * d + side * off) - Vector2(3, 3), Vector2(6, 3)), Color(DUST, 0.55))
				i += 1
				d += 5.0
			marks.draw_line(_px(aim * reach + side * half), _px(aim * reach - side * half), Color(LIT, 0.95), 3.0)
		"volley":
			var n: int = VOLLEY[phase - 1]
			var full := 40.0 * DENSITY
			for j in n:
				var a := TAU * float(j) / float(n) + (PI / float(n) if phase == 2 else 0.0)
				var v := Vector2.from_angle(a)
				var d := BODY_RADIUS
				while d < BODY_RADIUS + full:
					marks.draw_line(_px(v * d), _px(v * (d + 6.0)), Color(SCUFF, 0.6), 3.0)
					d += 12.0
				var tip := v * (BODY_RADIUS + full * k)
				marks.draw_line(_px(v * BODY_RADIUS), _px(tip), Color(DUST, 0.5), 3.0)
				marks.draw_rect(Rect2(_px(tip) - Vector2(3, 3), Vector2(6, 6)), Color(LIT, 0.95))
		"slam":
			# a ring of cracks where the forefeet will land; the dust fills it, its lit edge runs outwards
			var pts := PackedVector2Array()
			for j in 37:
				var a := TAU * float(j) / 36.0
				var r := SLAM_RADIUS + (6.0 if j % 3 == 0 else -3.0)
				pts.append(_px(Vector2.from_angle(a) * r))
			marks.draw_polyline(pts, Color(SCUFF, 0.8), 3.0)
			for j in 8:
				var v := Vector2.from_angle(TAU * float(j) / 8.0 + 0.2)
				marks.draw_line(_px(v * SLAM_RADIUS * 0.55), _px(v * SLAM_RADIUS), Color(SCUFF, 0.6), 3.0)
			marks.draw_circle(Vector2.ZERO, SLAM_RADIUS * k, Color(DUST, 0.3))
			marks.draw_arc(Vector2.ZERO, SLAM_RADIUS * k, 0.0, TAU, 40, Color(LIT, 0.95), 3.0)

## Snaps a point to the 3-texel world pixel, so the marks sit on the art's grid.
func _px(p: Vector2) -> Vector2:
	return (p / DENSITY).round() * DENSITY

func _lane_length() -> float:
	if arena.size == Vector2.ZERO:
		return CHARGE_SPEED * CHARGE_MAX
	var o := _zone_origin()
	var p := global_position - o
	var r := arena.grow(-BODY_RADIUS * 0.6)
	var t := CHARGE_SPEED * CHARGE_MAX
	for axis in 2:
		var v := aim[axis]
		if absf(v) > 0.001:
			var edge := r.end[axis] if v > 0.0 else r.position[axis]
			t = minf(t, (edge - p[axis]) / v)
	return maxf(t, 0.0)
