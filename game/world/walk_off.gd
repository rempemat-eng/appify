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
## whichever path she takes.
##
## Feet are not bodies (audit 1 of #495): a path alongside him at CLEAR still drew her inside his sprite.
## So no path is taken on which her drawn box meets his while she is still more than MIN_ALPHA visible
## (or, when the boxes already overlap where she stands, on which the overlap grows). When every path
## would, she takes the one that stays clear longest as far as it stays clear, stops there and fades out
## on the same clock (stopping rather than walking slower: a slowed walk slides her feet). And if he
## walks up to within CLEAR - 1 of her during her walk she stops and fades out from where she is.
## Under reduced motion she always fades where she stands, over STILL_FADE, with no movement.
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
const STEP_TURNS := [70.0, 90.0, 110.0]    ## the turn of the step aside (past 90: a little back)
const ON_TURNS := [0.0, 10.0, 20.0, 30.0]  ## the turn of the leg on toward `toward` after it
const MIN_ALPHA := 0.1                     ## fainter than this, her box may meet his
const MIN_WALK := 12.0                     ## a cut path shorter than this: she fades in place instead

var who: Interactable
var toward := Vector2.ZERO           ## a point in the zone, in texels
var _path := PackedVector2Array()   ## the corners she walks through, from where she stands; empty: fading in place
var _leg := -1                      ## the leg her body faces along
var _origin := Vector2.ZERO          ## her position where the path starts
var _player: Node2D = null
var _keep := 0.0                     ## nearer than this less one texel, and she stops and fades
var _still := false                  ## stopped by the player coming up to her: fading in place
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
		var at: Vector2 = player.global_position if player != null else Vector2.INF
		_path = choose_path(who.global_position, toward, at, reach(_speed), _grid(),
			walk_boxes(_body()), drawn_box(player) if player != null else Rect2())
		if player != null:
			_player = player
			_keep = minf(CLEAR, who.global_position.distance_to(at) - 0.5)
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

## The path from `from`, as corners, `length` texels in all; empty: fade in place. Tried in order: the
## straight lane; a step aside away from the player and on toward `toward` past him; the single lane
## choose_lane gives. The first that is clear of solids and stays clear of him all the way (path_clear)
## is taken whole; with none, the one that stays clear longest is cut where it stops being clear, when
## that is at least MIN_WALK. `her` and `his` are the drawn boxes about the feet (drawn_box); empty
## boxes leave only the keep distance to check. `her` holds her walking boxes by facing (walk_boxes).
static func choose_path(from: Vector2, toward: Vector2, player: Vector2, length: float, grid: RefCounted,
		her := {}, his := Rect2()) -> PackedVector2Array:
	var straight := (toward - from).normalized()
	if straight == Vector2.ZERO or length <= 0.0:
		return PackedVector2Array()
	var paths: Array[PackedVector2Array] = [PackedVector2Array([from, from + straight * length])]
	if player.is_finite():
		# away from him across her lane; when he stands on it, the side away from his body (north of a
		# player south of her feet), since a step that way uncovers him soonest
		var across := straight.cross(player - from)
		if absf(across) < 1.0:
			across = (player - from).y * signf(straight.x if straight.x != 0.0 else 1.0)
		var away := -1.0 if across > 0.0 else 1.0
		for on: float in ON_TURNS:
			for side: float in SIDESTEPS:
				for step: float in STEP_TURNS:
					var mid := from + straight.rotated(deg_to_rad(step) * away) * side
					paths.append(PackedVector2Array([from, mid, mid + straight.rotated(deg_to_rad(on) * away) * (length - side)]))
	var dir := choose_lane(from, toward, player, length, grid)
	if dir != Vector2.ZERO and not dir.is_equal_approx(straight):
		paths.append(PackedVector2Array([from, from + dir * length]))
	var best := PackedVector2Array()
	var best_clear := 0.0
	for path in paths:
		var clear := path_clear(path, player, her, his, length * (1.0 - MIN_ALPHA * FADE / LEAVE))
		if clear <= best_clear and clear < INF:
			continue
		var walked := path if clear == INF else cut(path, clear)
		if not _clear_of_solids(walked, grid):
			continue
		if clear == INF:
			return path
		best = walked
		best_clear = clear
	return best if best_clear >= MIN_WALK else PackedVector2Array()

static func _clear_of_solids(path: PackedVector2Array, grid: RefCounted) -> bool:
	if grid == null:
		return true
	for i in path.size() - 1:
		if not grid.clear_line(path[i], path[i + 1]):
			return false
	return true

## How far along `path` she stays clear of the player at `player`: never nearer to his feet than CLEAR
## (or than she starts, less half a texel, when that is nearer), and, while she has walked less than
## `seen` (the stretch on which she is more than MIN_ALPHA visible), her box never meeting his when it
## starts clear and never covering more of it when it starts overlapping. INF: the whole path. Checked
## every half texel.
static func path_clear(path: PackedVector2Array, player: Vector2, her: Dictionary, his: Rect2, seen: float) -> float:
	if not player.is_finite():
		return INF
	var keep := minf(CLEAR, path[0].distance_to(player) - 0.5)
	var boxes := not her.is_empty() and his.has_area()
	var first := box_overlap(path[0], box_facing(her, path[1] - path[0]), player, his) if boxes else 0.0
	var last := first
	var total := 0.0
	for i in path.size() - 1:
		total += path[i].distance_to(path[i + 1])
	var d := 0.0
	while d <= total:
		var p := point_on(path, d)
		if p.distance_to(player) < keep:
			return maxf(d - 0.5, 0.0)
		if boxes and d <= seen:
			var now := box_overlap(p, box_facing(her, leg_on(path, d)), player, his)
			if (first == 0.0 and now > 0.0) or now > last + 0.01:
				return maxf(d - 0.5, 0.0)
			last = now
		d += 0.5
	return INF

## An actor's drawn box about its feet: the opaque part of the frame its first sprite shows now, in
## texels relative to the actor's position. Empty when nothing is drawn.
static func drawn_box(actor: Node2D) -> Rect2:
	if actor == null:
		return Rect2()
	for c in actor.get_children():
		var anim := c as AnimatedSprite2D
		if anim != null and anim.sprite_frames != null and anim.sprite_frames.has_animation(anim.animation):
			return _opaque(anim, anim.sprite_frames.get_frame_texture(anim.animation, anim.frame))
	return Rect2()

## The union of the opaque parts of every frame of one of a sprite's animations, about its feet.
static func frames_box(anim: AnimatedSprite2D, name: String) -> Rect2:
	var box := Rect2()
	if anim.sprite_frames == null or not anim.sprite_frames.has_animation(name):
		return box
	for i in anim.sprite_frames.get_frame_count(name):
		var part := _opaque(anim, anim.sprite_frames.get_frame_texture(name, i))
		box = part if not box.has_area() else box.merge(part)
	return box

static func _opaque(anim: AnimatedSprite2D, tex: Texture2D) -> Rect2:
	if tex == null:
		return Rect2()
	var used := Rect2i(Vector2i.ZERO, Vector2i(tex.get_size()))
	var img := tex.get_image()
	if img != null and not img.is_empty():
		if img.is_compressed():
			img.decompress()
		if img.get_used_rect().has_area():
			used = img.get_used_rect()
	var origin := anim.offset - (tex.get_size() / 2.0 if anim.centered else Vector2.ZERO)
	return Rect2(anim.position + (origin + Vector2(used.position)) * anim.scale, Vector2(used.size) * anim.scale)

## How much her box (at feet `a`) and his (at feet `b`) cover each other, in square texels.
static func box_overlap(a: Vector2, her: Rect2, b: Vector2, his: Rect2) -> float:
	var mine := Rect2(her.position + a, her.size)
	var yours := Rect2(his.position + b, his.size)
	return mine.intersection(yours).get_area() if mine.intersects(yours) else 0.0

## The point `d` texels along a path of corners (its end, past that).
static func point_on(path: PackedVector2Array, d: float) -> Vector2:
	for i in path.size() - 1:
		var leg := path[i + 1] - path[i]
		if d <= leg.length():
			return path[i] + leg.normalized() * d
		d -= leg.length()
	return path[path.size() - 1]

## The direction of the leg `d` texels along a path of corners (the last leg, past its end).
static func leg_on(path: PackedVector2Array, d: float) -> Vector2:
	for i in path.size() - 1:
		var leg := path[i + 1] - path[i]
		if d <= leg.length() or i == path.size() - 2:
			return leg
		d -= leg.length()
	return Vector2.ZERO

## Her boxes while she walks, by the facing her walk shows for a direction (CastSprite.facing_for):
## each the union of every frame of the walk in that facing and in the two diagonals beside it, the
## in-betweens she shows while she turns into it.
static func walk_boxes(body: AnimatedSprite2D) -> Dictionary:
	var out := {}
	if body == null:
		return out
	for fc: String in ["E", "N", "W", "S"]:
		var box := Rect2()
		for name: String in ["walk_" + fc, "walk_" + _beside(fc, -1), "walk_" + _beside(fc, 1)]:
			var part := frames_box(body, name)
			box = part if not box.has_area() else (box.merge(part) if part.has_area() else box)
		if box.has_area():
			out[fc] = box
	return out

static func _beside(fc: String, side: int) -> String:
	var ring := ["E", "SE", "S", "SW", "W", "NW", "N", "NE"]
	return ring[(ring.find(fc) + side + ring.size()) % ring.size()]

## Her box for walking in direction `v`; the union of them all when none is kept for its facing.
static func box_facing(her: Dictionary, v: Vector2) -> Rect2:
	var fc := CastSprite.facing_for(v)
	if her.has(fc):
		return her[fc]
	var all := Rect2()
	for box: Rect2 in her.values():
		all = box if not all.has_area() else all.merge(box)
	return all

## The first `d` texels of a path of corners.
static func cut(path: PackedVector2Array, d: float) -> PackedVector2Array:
	var out := PackedVector2Array([path[0]])
	for i in path.size() - 1:
		var leg := path[i + 1] - path[i]
		if d <= leg.length():
			out.append(path[i] + leg.normalized() * d)
			return out
		d -= leg.length()
		out.append(path[i + 1])
	return out

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
	var leg_now := at if _path.size() > 1 and d < (_path[at + 1] - _path[at]).length() else -2      # -2: at the end, standing
	if leg_now != _leg:
		_leg = leg_now
		var body := _body()
		if body != null:
			body.walking = (_path[at + 1] - _path[at]).normalized() if leg_now >= 0 else Vector2.ZERO

func _process(delta: float) -> void:
	if not _started:
		return
	_t += delta
	if _t >= _life:
		_gone()
		return
	if not _still and _player != null and is_instance_valid(_player) and not _path.is_empty() \
			and who.global_position.distance_to(_player.global_position) < _keep - 1.0:
		_stop_and_fade()
	if not _still:
		_walk_to(_speed * _t)
	who.modulate.a = clampf((_life - _t) / _fade, 0.0, 1.0)

## He came up to her while she walked: she stops where she is and fades out from the alpha she has, at
## the in-place rate (STILL_FADE for a whole fade).
func _stop_and_fade() -> void:
	var alpha := clampf((_life - _t) / _fade, 0.0, 1.0)
	_still = true
	_path = PackedVector2Array()
	_t = 0.0
	_fade = STILL_FADE
	_life = alpha * STILL_FADE
	var body := _body()
	if body != null:
		body.walking = Vector2.ZERO

func _gone() -> void:
	who.visible = false
	who.modulate.a = 1.0
	var body := _body()
	if body != null:
		body.walking = Vector2.ZERO
	set_process(false)
	queue_free()
