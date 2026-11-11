class_name EnemySteer
extends RefCounted
## Gets an enemy round a solid without a navigation mesh. Enemies walk straight at what they want (the
## player, or home). Met head on, a bench or a wall stopped them for good: a body pushing straight into a
## wall has nothing to slide along (M0 audit, M0-L3: a mossling hung on the bench for 30 s on its way home).
## `direction()` is asked once a physics step, before the body moves: while the last move met a solid that
## lies across the wanted way, it answers with the way along that solid instead (one side, kept until the
## way is free, so an inner corner is followed round and not bounced off), leaning a little into it so the
## contact is kept and the end of the solid is felt.

const INTO := 0.25      ## how far the followed way leans into the wall
const CLEAR := 0.18     ## seconds without contact before it heads straight again (clears its own width)
const ENTER := -0.2     ## the wall is "across the way" when wanted . normal is below this ...
const LEAVE := -0.05    ## ... and the way is free again above this

const LINE_SIDE := 6.0  ## texels: the line to the target is tested this wide on each side

## True when no solid at all (walls and low solids alike: a bench, a bramble, rubble) stands between the
## body and `to`. A melee enemy strikes only along such a line; otherwise it walks round.
## +1 or -1: the hand along the met solid that is the shorter way round to `goal`, found by feeling along
## the solid each way (a short ray into it every 8 texels) for where it ends; 0 without a goal or when
## neither end is found within 160 texels.
func _shorter_hand(body: Node2D, met: KinematicCollision2D, goal: Vector2) -> int:
	if met == null or goal == Vector2.INF or not body.is_inside_tree():
		return 0
	var space := body.get_world_2d().direct_space_state
	var centre := body.global_position
	for child in body.get_children():
		if child is CollisionShape2D:
			centre += (child as CollisionShape2D).position
			break
	var cost := [INF, INF]
	for k in 2:
		var t := normal.orthogonal() * (1.0 if k == 0 else -1.0)
		var d := 8.0
		while d <= 160.0:
			var p := centre + t * d
			var along := PhysicsRayQueryParameters2D.create(centre, p, 1)
			if not space.intersect_ray(along).is_empty():
				break                                    # another solid across that way
			var into := PhysicsRayQueryParameters2D.create(p, p - normal * 24.0, 1)
			if space.intersect_ray(into).is_empty():
				cost[k] = d + p.distance_to(goal)        # the solid ends here
				break
			d += 8.0
	if cost[0] == INF and cost[1] == INF:
		return 0
	return 1 if cost[0] <= cost[1] else -1

static func line_clear(body: Node2D, to: Vector2) -> bool:
	if not body.is_inside_tree():
		return true
	var space := body.get_world_2d().direct_space_state
	var from := body.global_position
	var side := (to - from).orthogonal().normalized() * LINE_SIDE if from.distance_to(to) > 0.01 else Vector2.ZERO
	for off: Vector2 in [Vector2.ZERO, side, -side]:
		var ray := PhysicsRayQueryParameters2D.create(from + off, to + off, 1)
		if not space.intersect_ray(ray).is_empty():
			return false
	return true

var side := 0           ## 0 free; +1 or -1 the hand kept on the wall
var normal := Vector2.ZERO
var blocked_time := 0.0 ## seconds spent following walls since the last reset
var flips := 0          ## times it has taken the other hand (see REPEAT)
var _free := 0.0
var _last_side := 0
var _since_follow := 99.0

## Back where the last wall was first met, soon after letting it go: the first hand leads round a pocket
## and back into it (a wall and a bramble meeting in a corner, 11 Nov: the mosslings circled there), so
## take the other hand. Away from that spot (the end of a bench) a new contact keeps the usual rule.
const REPEAT := 2.0
const BACK := 30.0
var _follow_start := Vector2.INF

func reset() -> void:
	side = 0
	normal = Vector2.ZERO
	blocked_time = 0.0
	flips = 0
	_free = 0.0
	_last_side = 0
	_since_follow = 99.0
	_follow_start = Vector2.INF

func following() -> bool:
	return side != 0

func _tangent() -> Vector2:
	return normal.orthogonal() * float(side)

## With a `goal` (the point it wants to reach; 11 Nov) it follows a wall until it is nearer the goal than
## where it met the wall (the "bug" rule), turning round a solid's corner instead of letting go of it: a
## mossling that met a bramble's top went west along it, lost it at its end, turned back into the corner
## it came from, and circled there. Without a goal (old callers) it lets go as soon as the way is free.
const CORNER_TIME := 0.9   ## seconds it keeps turning round a lost corner before it lets go
var _hit_dist := INF

## Free to head for the goal again: nearer than where it met the wall, or with nothing at all between.
func _nearer(body: Node2D, goal: Vector2) -> bool:
	return goal == Vector2.INF or body.global_position.distance_to(goal) < _hit_dist - 4.0 or line_clear(body, goal)

## The unit direction to move in, given the unit direction wanted.
func direction(body: CharacterBody2D, want: Vector2, delta: float, goal := Vector2.INF) -> Vector2:
	if want.length() < 0.01:
		return Vector2.ZERO
	want = want.normalized()
	var normals: Array[Vector2] = []
	var hits: Array[KinematicCollision2D] = []
	for i in body.get_slide_collision_count():
		hits.append(body.get_slide_collision(i))
		normals.append(hits[-1].get_normal())
	if side == 0:
		_since_follow += delta
		var worst := ENTER
		var met: KinematicCollision2D = null
		for i in normals.size():
			var d := want.dot(normals[i])
			if d < worst:
				worst = d
				normal = normals[i]
				met = hits[i]
		if worst >= ENTER:
			return want
		# the hand that keeps more of the wanted way; dead on, the same hand every time
		side = 1 if want.dot(normal.orthogonal()) >= -0.01 else -1
		# a box met with a goal in sight: the hand whose end of the box is the shorter way round (a bramble
		# met 5 px from its east end sent a mossling 80 px west, past its leash, 11 Nov)
		var by_box := _shorter_hand(body, met, goal)
		if by_box != 0:
			side = by_box
		if _last_side != 0 and _since_follow < REPEAT and body.global_position.distance_to(_follow_start) < BACK:
			side = -_last_side
			flips += 1
		_last_side = side
		_follow_start = body.global_position
		_hit_dist = body.global_position.distance_to(goal) if goal != Vector2.INF else INF
		_free = 0.0
	else:
		var touching := false
		var t := _tangent()
		for n in normals:
			if t.dot(n) < -0.5:          # an inner corner: the next wall, the same hand
				normal = n
				touching = true
				break
			if n.dot(normal) > 0.7:      # still on the followed wall (its normal may turn a little)
				normal = n
				touching = true
		if not touching and _free > 0.0 and goal != Vector2.INF:
			for n in normals:            # round an outer corner onto the next face: follow that one
				if n.dot(t) > 0.5:
					normal = n
					touching = true
					break
		if touching:
			_free = 0.0
			if want.dot(normal) > LEAVE and _nearer(body, goal):
				side = 0
				_since_follow = 0.0
				return want
		else:
			_free += delta
			if not _nearer(body, goal) and _free < CORNER_TIME:
				blocked_time += delta
				return (-normal - _tangent() * 0.3).normalized()   # round the corner: back towards the face it left
			if _free > CLEAR:
				side = 0
				_since_follow = 0.0
				return want
	blocked_time += delta
	return (_tangent() - normal * INTO).normalized()
