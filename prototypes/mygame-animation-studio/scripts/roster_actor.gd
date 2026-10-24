class_name RosterStudyActor
extends CharacterBody2D
## An authored east-view animation actor. Physics and draw pivots stay separate.

signal action_released(character_id: String, clip: String, origin: Vector2, direction: Vector2)
signal action_finished(character_id: String, clip: String)
signal action_cancelled(character_id: String, clip: String)
signal footfall(point: Vector2)
signal landed(point: Vector2, surface: String)
signal void_fall

const CLIPS := ["idle", "walk", "primary", "secondary", "special", "guard", "hit", "defeat", "jump", "stair_up", "stair_down", "dodge", "powered_idle", "powered_walk", "powered_primary", "powered_guard", "powered_exit"]
const ACTIONS := ["primary", "secondary", "special"]
const SPEED := 92.0
const PIVOT := Vector2(96, 172)
const BUFFER_SECONDS := 0.15
var character_id := ""
var manifest: Dictionary = {}
var foot_pivot := PIVOT
var sprite: AnimatedSprite2D
var held_stone: Sprite2D
var available := false
var clip := "idle"
var clock := 0.0
var action := ""
var event_count := 0
var released := false
var phase := "REST"
var study_mode := true
var study_loop := true
var pose_paused := false
var suspended := false
var guarded := false
var guard_override := false
var demo_move := Vector2.ZERO
var use_demo_move := false
var queued_action := ""
var queue_time := 0.0
var speed_scale := 1.0
var foot_clock := 0.0
var dash_time := 0.0
var dash_velocity := Vector2.ZERO
var vault_time := 0.0
var vault_duration := 0.5
var finished := false
var render_height := 0.0
var ground_height := 0.0
var jump_height := 0.0
var absolute_height := 0.0
var vertical_velocity := 0.0
var traversal_state := ""
var traversal_clock := 0.0
var traversal_clip := "jump"
var traversal_is_ability := false
var traversal_direction := Vector2.RIGHT
var traversal_motion_speed := 0.0
var landing_count := 0
var surface := "stone"
var floor_sampler: Callable
var last_safe_position := Vector2.ZERO
var blocked_step := false
var activation_origin := Vector2.ZERO
var powered_mode := false
const JUMP_LOAD := 0.13
const JUMP_GRAVITY := 780.0
const JUMP_SPEED := 260.0
const LAND_RECOVERY := 0.21

func grounded() -> bool:
	return traversal_state.is_empty() or traversal_state == "dodge" or traversal_state == "land" or traversal_state == "load"

func visual_foot() -> Vector2:
	return global_position - Vector2(0, render_height)

func shadow_lift() -> float:
	if vault_time>0.0:return maxf(jump_height,sin((1.0-vault_time/vault_duration)*PI)*30.0)
	return jump_height

func _sample_floor(point: Vector2) -> Dictionary:
	if floor_sampler.is_valid():
		return floor_sampler.call(point)
	return {"height":0.0,"support":true,"surface":"stone","stairs":false}

func animation_clips() -> Array:
	var result:Array = CLIPS.duplicate()
	if character_id=="pendle":result.append("reload")
	return result

func start_reload() -> bool:
	if character_id!="pendle" or not available or not action.is_empty() or powered_mode or guarded or not traversal_state.is_empty() or study_mode:return false
	action="reload"
	clip="reload"
	clock=0.0
	released=false
	phase="RELOAD"
	_update_pose()
	return true

func reset_traversal() -> void:
	traversal_state = ""
	traversal_clock = 0.0
	traversal_clip = "jump"
	traversal_is_ability = false
	traversal_motion_speed = 0.0
	jump_height = 0.0
	vertical_velocity = 0.0
	var floor:Dictionary = _sample_floor(global_position)
	ground_height = float(floor.height)
	absolute_height = ground_height
	surface = str(floor.surface)
	render_height = ground_height
	last_safe_position = global_position

func start_jump() -> bool:
	if not available or suspended or pose_paused or not action.is_empty() or guarded or powered_mode or not traversal_state.is_empty():return false
	study_mode = false
	queued_action = ""
	traversal_state = "load"
	traversal_clip = "jump"
	traversal_is_ability = false
	traversal_clock = 0.0
	absolute_height = ground_height
	clip = "jump"
	clock = 0.0
	phase = "JUMP LOAD"
	_update_pose()
	return true

func start_dodge() -> bool:
	if not available or suspended or pose_paused or not action.is_empty() or guarded or powered_mode or not traversal_state.is_empty():return false
	study_mode = false
	queued_action = ""
	traversal_state = "dodge"
	traversal_clock = 0.0
	clip = "dodge"
	clock = 0.0
	var movement := demo_move if use_demo_move else Input.get_vector("r_left", "r_right", "r_up", "r_down")
	dash_velocity = (movement.normalized() if movement.length_squared()>0.01 else Vector2.RIGHT) * 190.0
	phase = "DODGE"
	_update_pose()
	return true


func _ready() -> void:
	sprite = AnimatedSprite2D.new()
	sprite.name = "Sprite"
	sprite.centered = false
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	sprite.position = -PIVOT
	add_child(sprite)
	held_stone=Sprite2D.new()
	held_stone.name="HeldBoulder"
	held_stone.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	if ResourceLoader.exists("res://assets/cairn/boulder.png"):
		held_stone.texture=load("res://assets/cairn/boulder.png")
	held_stone.visible=false
	add_child(held_stone)
	var collision := CollisionShape2D.new()
	var footprint := RectangleShape2D.new()
	footprint.size = Vector2(30, 16)
	collision.position = Vector2(0, -5)
	collision.shape = footprint
	add_child(collision)
	collision_layer = 2
	collision_mask = 1


func load_character(value: String) -> bool:
	clear_controls()
	character_id = value
	available = false
	held_stone.visible=false
	manifest = {}
	var resource_path := "res://assets/animated/%s/frames.tres" % value
	var metadata_path := "res://assets/animated/%s/manifest.json" % value
	if not ResourceLoader.exists(resource_path) or not FileAccess.file_exists(metadata_path):
		sprite.visible = false
		return false
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(metadata_path))
	if not parsed is Dictionary:
		sprite.visible = false
		return false
	manifest = parsed
	var pivot_data:Array=manifest.get("foot_pivot",[96,172])
	foot_pivot=Vector2(float(pivot_data[0]),float(pivot_data[1]))
	sprite.sprite_frames = load(resource_path) as SpriteFrames
	if sprite.sprite_frames == null:
		return false
	for required in animation_clips():
		if not sprite.sprite_frames.has_animation(required) or sprite.sprite_frames.get_frame_count(required) == 0:
			sprite.visible = false
			return false
		for index in sprite.sprite_frames.get_frame_count(required):
			var texture:=sprite.sprite_frames.get_frame_texture(required,index)
			if texture==null or texture.get_width()<1 or texture.get_height()<1:
				sprite.visible=false
				return false
	available = true
	sprite.visible = true
	sprite.flip_h = false
	event_count = 0
	landing_count = 0
	powered_mode = false
	dash_time = 0.0
	vault_time = 0.0
	reset_traversal()
	play_study("idle")
	return true


func duration(name: String = "") -> float:
	var key := clip if name.is_empty() else name
	if not available:
		return 0.0
	var total := 0.0
	for index in range(sprite.sprite_frames.get_frame_count(key)):
		total += frame_duration(key, index)
	return total


func frame_duration(name: String, index: int) -> float:
	return sprite.sprite_frames.get_frame_duration(name, index) / maxf(0.001, sprite.sprite_frames.get_animation_speed(name))


func release_time(name: String) -> float:
	if manifest.has("clips") and manifest.clips.has(name):
		var information: Dictionary = manifest.clips[name]
		if information.has("release_time") and information.release_time != null:
			return float(information.release_time)
	var frame := 8 if character_id == "cairn" and sprite.sprite_frames.get_frame_count(name) == 16 else 4
	if manifest.has("clips") and manifest.clips.has(name):
		var information: Dictionary = manifest.clips[name]
		if information.has("release_frame") and information.release_frame != null:
			frame = int(information.release_frame)
	var total := 0.0
	for index in range(mini(frame, sprite.sprite_frames.get_frame_count(name))):
		total += frame_duration(name, index)
	return total


func guard_hold_frame() -> int:
	var key := "powered_guard" if clip=="powered_guard" else "guard"
	if manifest.has("clips") and manifest.clips.has(key) and manifest.clips[key].has("hold_frame") and manifest.clips[key].hold_frame != null:
		return int(manifest.clips[key].hold_frame)
	return 3 if character_id == "cairn" and key=="guard" else 4


func play_study(name: String) -> void:
	if not available or name not in animation_clips():
		return
	clear_controls()
	reset_traversal()
	study_mode = true
	powered_mode = false
	clip = name
	action = ""
	clock = 0.0
	released = false
	finished = false
	phase = "STUDY"
	_update_pose()


func enter_practice() -> void:
	if not available:
		return
	study_mode = false
	action = ""
	clock = 0.0
	clip = "idle"
	finished = false
	pose_paused = false
	powered_mode = false
	reset_traversal()
	_update_pose()


func start_action(name: String) -> bool:
	if not available or name not in ACTIONS or not action.is_empty() or guarded or suspended or pose_paused or not traversal_state.is_empty():
		return false
	if powered_mode and name == "secondary":return false
	if name=="special" and not powered_mode and bool(_sample_floor(global_position).get("terrain",false)):return false
	study_mode = false
	action = "powered_exit" if powered_mode and name == "special" else name
	clip = "powered_primary" if powered_mode and name == "primary" else action
	clock = 0.0
	released = false
	finished = false
	phase = "PREPARE"
	activation_origin = visual_foot()
	_update_pose()
	return true


func queue_action(name: String) -> void:
	if name not in ACTIONS or suspended or pose_paused or not traversal_state.is_empty():
		return
	if action.is_empty() and not guarded:
		start_action(name)
	else:
		queued_action = name
		queue_time = BUFFER_SECONDS


func _physics_process(delta: float) -> void:
	step(delta)


func step(delta: float) -> void:
	if not available or suspended or pose_paused:
		velocity = Vector2.ZERO
		return
	var dt := delta * speed_scale
	if study_mode:
		clock += dt
		if clock >= duration():
			if study_loop:
				clock = fmod(clock, maxf(0.001, duration()))
			else:
				clock = duration()
				finished = true
		_update_pose()
		return
	queue_time = maxf(0.0, queue_time - dt)
	if queue_time <= 0.0:
		queued_action = ""
	var movement := demo_move if use_demo_move else Input.get_vector("r_left", "r_right", "r_up", "r_down")
	if not traversal_state.is_empty():
		_step_traversal(dt, movement)
		_update_pose()
		return
	var dash_started_before_frame := dash_time>0.0
	var effect_delta := dt
	var wants_guard := guard_override or Input.is_action_pressed("r_guard")
	if action in ["special","powered_exit","reload"]:wants_guard = false
	if wants_guard and not action.is_empty():
		var cancelled := action
		action = ""
		released = false
		queued_action = ""
		dash_time=0.0
		dash_velocity=Vector2.ZERO
		action_cancelled.emit(character_id,cancelled)
	guarded = wants_guard
	if action.is_empty() and not guarded and not queued_action.is_empty():
		var next := queued_action
		queued_action = ""
		start_action(next)
	if not action.is_empty():
		clock += dt
		var release := release_time(clip)
		if action not in ["powered_exit","reload"] and not released and clock >= release:
			released = true
			event_count += 1
			action_released.emit(character_id, action, visual_foot(), Vector2.RIGHT)
			if not dash_started_before_frame and dash_time>0.0:effect_delta=clampf(clock-release,0.0,dt)
			if traversal_is_ability and not traversal_state.is_empty():
				_step_traversal(clampf(clock-release,0.0,dt),movement)
				_update_pose()
				return
		phase = "RELOAD" if action=="reload" else ("PREPARE" if clock < release else ("CONTACT" if clock < release + 0.09 else "RECOVER"))
		if clock >= duration(clip):
			var previous := action
			if previous == "special":powered_mode = true
			if previous == "powered_exit":powered_mode = false
			action = ""
			clock = 0.0
			clip = "powered_idle" if powered_mode else "idle"
			action_finished.emit(character_id, previous)
	else:
		var floor:Dictionary = _sample_floor(global_position)
		var next_clip := "guard" if guarded else ("walk" if movement.length_squared() > 0.01 else "idle")
		if powered_mode:next_clip = "powered_" + next_clip
		if next_clip == "walk" and bool(floor.get("stairs", false)) and absf(movement.x)>0.01:
			var ahead:Dictionary = _sample_floor(global_position + Vector2(signf(movement.x)*2, 0))
			var rise:float = float(ahead.height)-float(floor.height)
			if absf(rise)>0.001:next_clip = "stair_up" if rise>0 else "stair_down"
		if next_clip != clip:
			clip = next_clip
			clock = 0.0
		clock += dt
		if not guarded:
			clock = fmod(clock, maxf(0.001, duration()))
		phase = "BRACED" if guarded else (clip.to_upper() if clip in ["walk","stair_up","stair_down","powered_walk"] else "REST")
	var dash_step := minf(dash_time,effect_delta)
	if vault_time > 0.0:
		vault_time = maxf(0.0, vault_time - effect_delta)
		# Rook's authored secondary already contains the airborne height.
		render_height = ground_height + (0.0 if character_id=="rook" else sin((1.0 - vault_time / vault_duration) * PI) * 30.0)
	else:
		render_height = ground_height
	velocity = movement.limit_length(1.0) * SPEED * (0.0 if guarded or not action.is_empty() else 1.0)
	if clip in ["stair_up","stair_down"]:velocity *= 0.72
	if dash_time > 0.0:
		velocity = dash_velocity
	var position_before_move := global_position
	_integrate_move(velocity * (dash_step if dash_time>0.0 else dt))
	var moved_distance := global_position.distance_to(position_before_move)
	dash_time = maxf(0.0,dash_time-dash_step)
	var floor:Dictionary = _sample_floor(global_position)
	if bool(floor.support) and ground_height-float(floor.height)>6.0:
		traversal_state = "fall"
		traversal_clock = 0.0
		vertical_velocity = 0.0
		ground_height = float(floor.height)
		jump_height = maxf(0.0,absolute_height-ground_height)
		render_height = absolute_height
		guarded = false
		action = ""
		queued_action = ""
	elif bool(floor.support):
		ground_height = float(floor.height)
		absolute_height = ground_height
		surface = str(floor.surface)
		render_height = ground_height
		last_safe_position = global_position
	else:
		traversal_state = "fall"
		traversal_clock = 0.0
		vertical_velocity = 0.0
		guarded = false
		action = ""
		queued_action = ""
	if moved_distance>0.001 and vault_time <= 0.0 and traversal_state.is_empty():
		foot_clock += dt
		var interval:float = duration(clip)*0.5 if clip in ["walk","stair_up","stair_down","powered_walk"] else 0.36
		if foot_clock >= interval:
			foot_clock = fmod(foot_clock, maxf(interval,0.01))
			footfall.emit(visual_foot())
	else:
		foot_clock = 0.0
		if clip in ["walk","stair_up","stair_down","powered_walk"] and movement.length_squared()>0.01 and moved_distance<=0.001:
			clock=maxf(0.0,clock-dt)
			phase="BLOCKED"
	_update_pose()


func _integrate_move(displacement: Vector2) -> void:
	var before := global_position
	blocked_step = false
	var collision := move_and_collide(displacement)
	if collision != null:
		move_and_collide(collision.get_remainder().slide(collision.get_normal()))
	var floor:Dictionary = _sample_floor(global_position)
	# A stair tread is a continuous walkable profile. A tall side face is solid.
	var max_height := absolute_height + (0.5 if traversal_state in ["air","fall"] else 6.0)
	var obstacle_height:float = float(floor.height) if bool(floor.support) else -INF
	for offset in [Vector2(-10,-5),Vector2(10,-5),Vector2(-10,5),Vector2(10,5)]:
		if displacement.dot(offset)<=0.0:continue
		var corner:Dictionary = _sample_floor(global_position+offset)
		if bool(corner.support):obstacle_height=maxf(obstacle_height,float(corner.height))
	if obstacle_height>max_height:
		global_position = before
		blocked_step = true


func _pose_clock_at(index: int, fraction: float = 0.0) -> float:
	var result := 0.0
	for i in range(index):result += frame_duration(clip,i)
	return result + frame_duration(clip,index)*clampf(fraction,0.0,0.999)


func _step_traversal(dt: float, movement: Vector2) -> void:
	guarded = false
	queued_action = ""
	var remaining := dt
	while remaining>0.000001 and not traversal_state.is_empty():
		var slice := minf(remaining,1.0/120.0)
		remaining -= slice
		traversal_clock += slice
		if traversal_state == "dodge":
			clip = "dodge"
			clock = minf(traversal_clock,duration("dodge"))
			phase = "DODGE"
			_integrate_move(dash_velocity * slice)
			var floor:Dictionary = _sample_floor(global_position)
			if bool(floor.support) and ground_height-float(floor.height)>6.0:
				traversal_state = "fall"
				traversal_clock = 0.0
				vertical_velocity = 0.0
				ground_height = float(floor.height)
			elif bool(floor.support):
				ground_height = float(floor.height)
				absolute_height = ground_height
				surface = str(floor.surface)
				last_safe_position = global_position
			else:
				traversal_state = "fall"
				traversal_clock = 0.0
				vertical_velocity = 0.0
			if traversal_state == "dodge" and traversal_clock>=duration("dodge"):
				traversal_state = ""
				clip = "idle"
				clock = 0.0
			continue
		clip = traversal_clip
		if traversal_state == "load":
			phase = "JUMP LOAD"
			clock = _pose_clock_at(0 if traversal_clock<JUMP_LOAD*0.5 else 1, fmod(traversal_clock/(JUMP_LOAD*0.5),1.0))
			if traversal_clock>=JUMP_LOAD:
				traversal_state = "air"
				traversal_clock = 0.0
				vertical_velocity = JUMP_SPEED * (0.9 if character_id=="cairn" else 1.0)
		elif traversal_state in ["air","fall"]:
			phase = ("VAULT DESCEND" if vertical_velocity<0 else "VAULT RISE") if traversal_is_ability else ("FALL" if vertical_velocity<0 else "JUMP RISE")
			vertical_velocity -= JUMP_GRAVITY*slice
			absolute_height += vertical_velocity*slice
			velocity = traversal_direction*traversal_motion_speed if traversal_is_ability else movement.limit_length(1.0)*SPEED
			_integrate_move(velocity*slice)
			var floor:Dictionary = _sample_floor(global_position)
			var floor_height:float = float(floor.height)
			if bool(floor.support) and absolute_height<=floor_height and vertical_velocity<=0:
				ground_height = floor_height
				absolute_height = floor_height
				jump_height = 0.0
				vertical_velocity = 0.0
				surface = str(floor.surface)
				traversal_state = "land"
				traversal_clock = 0.0
				landing_count += 1
				last_safe_position = global_position
				render_height = absolute_height
				landed.emit(global_position-Vector2(0,ground_height),surface)
			elif not bool(floor.support) and absolute_height < -42.0:
				void_fall.emit()
				return
			else:
				ground_height = floor_height if bool(floor.support) else 0.0
				jump_height = maxf(0.0,absolute_height-ground_height)
				# Source5 is contact compression; it may only appear after physical support.
				var index := (3 if vertical_velocity>65 else (4 if vertical_velocity>-65 else 5)) if traversal_is_ability else (2 if vertical_velocity>65 else (3 if vertical_velocity>-65 else 4))
				clock = _pose_clock_at(index)
		elif traversal_state == "land":
			phase = "VAULT LAND" if traversal_is_ability else "LAND RECOVERY"
			var contact_count:=2 if traversal_is_ability else 3
			var first_contact:=6 if traversal_is_ability else 5
			var contact_index:=mini(7,first_contact+int(traversal_clock/(LAND_RECOVERY/float(contact_count))))
			clock = _pose_clock_at(contact_index, fmod(traversal_clock/(LAND_RECOVERY/float(contact_count)),1.0))
			if traversal_clock>=LAND_RECOVERY:
				traversal_state = ""
				clip = "idle"
				clock = 0.0
				if traversal_is_ability:
					action=""
					traversal_is_ability=false
					traversal_clip="jump"
					action_finished.emit(character_id,"secondary")
	jump_height = maxf(0.0,absolute_height-ground_height)
	render_height = absolute_height


func dash(speed: float, seconds: float, vault: bool = false) -> void:
	if vault:
		traversal_state="air"
		traversal_clip="secondary"
		traversal_is_ability=true
		traversal_direction=Vector2.RIGHT
		traversal_motion_speed=speed
		traversal_clock=0.0
		absolute_height=ground_height
		vertical_velocity=JUMP_GRAVITY*seconds*0.5
		dash_time=0.0
		vault_time=0.0
		return
	dash_velocity = Vector2(speed, 0)
	dash_time = seconds


func step_pose(direction: int) -> void:
	if not available:
		return
	pose_paused = true
	study_mode = true
	action = ""
	var count := sprite.sprite_frames.get_frame_count(clip)
	var next := posmod(sprite.frame + direction, count)
	clock = 0.0
	for index in range(next):
		clock += frame_duration(clip, index)
	clock += 0.00001
	_update_pose()


func _update_pose() -> void:
	if not available:
		return
	sprite.animation = clip
	var remaining := clock
	var index := 0
	var count := sprite.sprite_frames.get_frame_count(clip)
	for candidate in range(count):
		index = candidate
		if remaining < frame_duration(clip, candidate):
			break
		remaining -= frame_duration(clip, candidate)
	if guarded and not study_mode:
		index = mini(index, guard_hold_frame())
	sprite.frame = clampi(index, 0, count - 1)
	sprite.pause()
	sprite.flip_h = false
	sprite.position = -foot_pivot + visual_foot().round() - global_position
	held_stone.visible=character_id=="cairn" and clip=="secondary" and sprite.frame>=2 and sprite.frame<=7
	if held_stone.visible:
		var anchors:={2:Vector2(18,-22),3:Vector2(24,-54),4:Vector2(15,-80),5:Vector2(-5,-104),6:Vector2(-15,-120),7:Vector2(-15,-126)}
		held_stone.position=Vector2(anchors[sprite.frame])+visual_foot().round()-global_position


func clear_controls() -> void:
	guarded = false
	guard_override = false
	queued_action = ""
	queue_time = 0.0
	demo_move = Vector2.ZERO
	velocity = Vector2.ZERO
	for binding in ["r_left", "r_right", "r_up", "r_down", "r_guard"]:
		if InputMap.has_action(binding):
			Input.action_release(binding)


func reset_pose() -> void:
	clear_controls()
	clock = 0.0
	action = ""
	clip = "idle"
	event_count = 0
	landing_count = 0
	released = false
	pose_paused = false
	dash_time = 0.0
	vault_time = 0.0
	render_height = 0.0
	finished = false
	study_mode = true
	powered_mode = false
	reset_traversal()
	_update_pose()
