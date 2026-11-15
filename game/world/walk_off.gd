class_name WalkOff
extends Node
## Somebody sets off ahead of the player and is gone (15 Nov: Hale said she would be right behind
## Bramble and then stood by her tree until the next zone loaded). Added to an Interactable by its zone
## when a quest with `walks_off` starts (world/zone.gd, data/quests/road_to_crossroads.json): from that
## moment there is nothing to talk to here and her post no longer blocks the path. She walks toward
## `toward` at her own walking pace for LEAVE seconds (about 60 texels: gone in the open, before the
## path runs under the willow), fading out over the last FADE.
##
## She never walks through the player. If he stands within CLEAR texels of her lane she takes the
## nearest lane to the side away from him that is free of solids and comes no nearer to him than CLEAR
## (or than she already is, when he stands closer than that); with no such lane she fades where she
## stands. Under reduced motion she always fades where she stands, over STILL_FADE, with no movement.
## Finite either way. Looks and the talk area only: the quest's own flags say where she stands from the
## next zone load.

const WalkGrid := preload("res://tools/walk_grid.gd")

const LEAVE := 0.8
const FADE := 0.4
const STILL_FADE := 0.6          ## the fade in place: reduced motion, or no free lane
const CLEAR := 30.0              ## texels she keeps from the player's feet
## Lanes tried in order, as turns from the straight one in degrees; positive is the side away from the player.
const TURNS := [0.0, 35.0, 50.0, 70.0, 90.0, -35.0, -50.0, -70.0, -90.0, 120.0, -120.0, 180.0]

var who: Interactable
var toward := Vector2.ZERO           ## a point in the zone, in texels
var _dir := Vector2.ZERO             ## zero: fading where she stands
var _speed := 0.0
var _t := 0.0
var _life := LEAVE
var _fade := FADE
var _started := false

func _ready() -> void:
	if who == null:
		who = get_parent() as Interactable
	if who == null:
		queue_free()
		return
	who.leaving = true
	who.queue_redraw()                           # the "!" goes with her
	for c in who.get_children():
		if c is CollisionObject2D:               # her post: nothing to walk round once she has left it
			(c as CollisionObject2D).collision_layer = 0
	var player := get_tree().get_first_node_in_group("player") as Node2D
	if player != null:
		Interactable.refocus(player)
	var body := _body()
	_speed = body.walk_speed() if body != null else 0.0
	if _speed > 0.0 and not SaveGame.setting("reduced_motion", false):
		# the physics sees her post gone only after a step: choose the lane then
		await get_tree().physics_frame
		await get_tree().physics_frame
		if not is_instance_valid(who) or not who.is_inside_tree():
			return
		_dir = choose_lane(who.global_position, toward, player.global_position if player != null else Vector2.INF,
			reach(_speed), _grid())
	if _dir == Vector2.ZERO:
		_life = STILL_FADE
		_fade = STILL_FADE
	elif body != null:
		body.walking = _dir
	_started = true

func _grid() -> RefCounted:
	var zone := Zones.current
	if zone == null or not is_instance_valid(zone):
		return null
	return WalkGrid.new(who.get_world_2d(), zone.bounds)

func _body() -> Villager:
	for c in who.get_children():
		if c is Villager:
			return c
	return null

## How far she goes before she is gone, in texels (the tests hold this stretch free of solids).
static func reach(speed: float) -> float:
	return speed * LEAVE

## The nearest a point comes to the stretch from `a` to `b`.
static func distance_to_stretch(p: Vector2, a: Vector2, b: Vector2) -> float:
	return p.distance_to(Geometry2D.get_closest_point_to_segment(p, a, b))

## The direction she walks in from `from`: toward `toward` when that stretch of `length` texels stays
## clear of the player and of solids, else the first of TURNS that does. Zero: no lane, fade in place.
## `grid` (tools/walk_grid.gd) answers for the solids; null skips that check. `player` INF: nobody there.
static func choose_lane(from: Vector2, toward: Vector2, player: Vector2, length: float, grid: RefCounted) -> Vector2:
	var straight := (toward - from).normalized()
	if straight == Vector2.ZERO or length <= 0.0:
		return Vector2.ZERO
	var somebody := player.is_finite()
	# never nearer to him than CLEAR, or than she already stands when he is closer than that
	var keep := minf(CLEAR, from.distance_to(player) - 0.5) if somebody else 0.0
	var away := 1.0
	if somebody and straight.cross(player - from) > 0.0:
		away = -1.0
	for turn: float in TURNS:
		var dir := straight.rotated(deg_to_rad(turn) * away)
		var to := from + dir * length
		if somebody and distance_to_stretch(player, from, to) < keep:
			continue
		if grid != null and not grid.clear_line(from, to):
			continue
		return dir
	return Vector2.ZERO

func _process(delta: float) -> void:
	if not _started:
		return
	_t += delta
	if _t >= _life:
		_gone()
		return
	who.position += _dir * _speed * delta
	who.modulate.a = clampf((_life - _t) / _fade, 0.0, 1.0)

func _gone() -> void:
	who.visible = false
	who.modulate.a = 1.0
	var body := _body()
	if body != null:
		body.walking = Vector2.ZERO
	set_process(false)
	queue_free()
