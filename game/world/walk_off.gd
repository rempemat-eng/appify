class_name WalkOff
extends Node
## Somebody sets off ahead of the player and is gone (15 Nov: Hale said she would be right behind
## Bramble and then stood by her tree until the next zone loaded). Added to an Interactable by its zone
## when a quest with `walks_off` starts (world/zone.gd, data/quests/road_to_crossroads.json): from that
## moment there is nothing to talk to here and her post no longer blocks the path. She walks toward
## `toward` at her own walking pace for LEAVE seconds (about 60 texels: gone in the open, before the
## path runs under the willow), fading out over the last FADE.
##
## She never walks through the player. If he stands within CLEAR texels of her lane she steps aside,
## away from him, by a few texels (SIDESTEPS) and walks on toward `toward` past him (audit of #491: a lane
## turned south took her off the road into the meadow), on two legs that are free of solids and come no
## nearer to him than CLEAR (or than she already is, when he stands closer than that). When no such
## two-leg path exists she takes the nearest single lane to the side away from him that keeps the same
## distance; with no such lane she fades where she stands. The walk takes LEAVE and fades over FADE
## whichever path she takes. Under reduced motion she always fades where she stands, over STILL_FADE,
## with no movement.
## Finite either way. Looks and the talk area only: the quest's own flags say where she stands from the
## next zone load.

const WalkGrid := preload("res://tools/walk_grid.gd")

const LEAVE := 0.8
const FADE := 0.4
const STILL_FADE := 0.6          ## the fade in place: reduced motion, or no free lane
const CLEAR := 30.0              ## texels she keeps from the player's feet
## Lanes tried in order, as turns from the straight one in degrees; positive is the side away from the player.
const TURNS := [0.0, 35.0, 50.0, 70.0, 90.0, -35.0, -50.0, -70.0, -90.0, 120.0, -120.0, 180.0]
## The step aside, tried after the straight lane and before the other TURNS. All turns are from the
## straight lane, to the side away from the player; the straightest leg on toward `toward` is tried first.
const SIDESTEPS := [12.0, 16.0, 20.0]      ## how far she steps aside, in texels
const STEP_TURNS := [70.0, 90.0]           ## the turn of the step aside
const ON_TURNS := [0.0, 10.0, 20.0, 30.0]  ## the turn of the leg on toward `toward` after it

var who: Interactable
var toward := Vector2.ZERO           ## a point in the zone, in texels
var _path := PackedVector2Array()   ## the corners she walks through, from where she stands; empty: fading in place
var _leg := -1                      ## the leg her body faces along
var _origin := Vector2.ZERO          ## her position where the path starts
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
		_path = choose_path(who.global_position, toward, player.global_position if player != null else Vector2.INF,
			reach(_speed), _grid())
	if _path.is_empty():
		_life = STILL_FADE
		_fade = STILL_FADE
	_origin = who.position
	_walk_to(0.0)
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

## The path from `from`: the straight lane when it is clear; else a step aside away from the player and on
## toward `toward` past him, both legs clear of solids and never within the keep distance of him; else
## the single lane choose_lane gives. Corners from `from`, `length` texels in all; empty: fade in place.
static func choose_path(from: Vector2, toward: Vector2, player: Vector2, length: float, grid: RefCounted) -> PackedVector2Array:
	var dir := choose_lane(from, toward, player, length, grid)
	var straight := (toward - from).normalized()
	if dir == Vector2.ZERO and (straight == Vector2.ZERO or length <= 0.0):
		return PackedVector2Array()
	if not dir.is_equal_approx(straight) and player.is_finite():
		var keep := minf(CLEAR, from.distance_to(player) - 0.5)
		var away := -1.0 if straight.cross(player - from) > 0.0 else 1.0
		for on: float in ON_TURNS:
			for side: float in SIDESTEPS:
				for step: float in STEP_TURNS:
					var mid := from + straight.rotated(deg_to_rad(step) * away) * side
					var to := mid + straight.rotated(deg_to_rad(on) * away) * (length - side)
					if distance_to_stretch(player, from, mid) < keep or distance_to_stretch(player, mid, to) < keep:
						continue
					if grid != null and not (grid.clear_line(from, mid) and grid.clear_line(mid, to)):
						continue
					return PackedVector2Array([from, mid, to])
	if dir == Vector2.ZERO:
		return PackedVector2Array()
	return PackedVector2Array([from, from + dir * length])

## Puts her `d` texels along her path and faces her body the way the leg she is on goes.
func _walk_to(d: float) -> void:
	var at := 0
	var p := Vector2.ZERO
	while at < _path.size() - 1:
		var leg := _path[at + 1] - _path[at]
		if d <= leg.length() or at == _path.size() - 2:
			p = _path[at] - _path[0] + leg.normalized() * minf(d, leg.length())
			break
		d -= leg.length()
		at += 1
	who.position = _origin + p
	if at != _leg and _path.size() > 1:
		_leg = at
		var body := _body()
		if body != null:
			body.walking = (_path[at + 1] - _path[at]).normalized()

func _process(delta: float) -> void:
	if not _started:
		return
	_t += delta
	if _t >= _life:
		_gone()
		return
	_walk_to(_speed * _t)
	who.modulate.a = clampf((_life - _t) / _fade, 0.0, 1.0)

func _gone() -> void:
	who.visible = false
	who.modulate.a = 1.0
	var body := _body()
	if body != null:
		body.walking = Vector2.ZERO
	set_process(false)
	queue_free()
