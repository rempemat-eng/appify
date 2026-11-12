class_name EnemySteer
extends RefCounted
## Gets an enemy round a solid without a navigation mesh. Enemies walk straight at what they want (the
## player, or home). Met head on, a bench or a wall stopped them for good: a body pushing straight into a
## wall has nothing to slide along (M0 audit, M0-L3: a mossling hung on the bench for 30 s on its way home).
## `direction()` is asked once a physics step, before the body moves: while the last move met a solid that
## lies across the wanted way, it answers with the way along that solid instead (one side, kept until the
## way is free, so an inner corner is followed round and not bounced off), leaning a little into it so the
## contact is kept and the end of the solid is felt.
##
## With a `goal` (the point it wants to reach; 11 Nov) it takes the hand whose end of the solid is the
## shorter way round: a mossling that met a bramble 5 px from its east end went 80 px west along it, out of
## its leash, and a camp behind the bramble at (600, 1600) was never reached.

const INTO := 0.25      ## how far the followed way leans into the wall
const CLEAR := 0.18     ## seconds without contact before it heads straight again (clears its own width)
const ENTER := -0.2     ## the wall is "across the way" when wanted . normal is below this ...
const LEAVE := -0.05    ## ... and the way is free again above this
const LINE_SIDE := 6.0  ## texels: the line to the target is tested this wide on each side
const FEEL_STEP := 8.0  ## texels between the rays that feel along a solid for its end
const FEEL_MAX := 160.0 ## how far along it feels each way

var side := 0           ## 0 free; +1 or -1 the hand kept on the wall
var normal := Vector2.ZERO
var blocked_time := 0.0 ## seconds spent following walls since the last reset
var _free := 0.0

## True when no solid at all (walls and low solids alike: a bench, a bramble, rubble) stands between the
## body and `to`. A melee enemy strikes only along such a line; otherwise it walks round (Matt, 11 Nov).
static func line_clear(body: Node2D, to: Vector2) -> bool:
	if not body.is_inside_tree():
		return true
	var space := body.get_world_2d().direct_space_state
	var from := body.global_position
	var side_off := (to - from).orthogonal().normalized() * LINE_SIDE if from.distance_to(to) > 0.01 else Vector2.ZERO
	for off: Vector2 in [Vector2.ZERO, side_off, -side_off]:
		var ray := PhysicsRayQueryParameters2D.create(from + off, to + off, 1)
		if not space.intersect_ray(ray).is_empty():
			return false
	return true

func reset() -> void:
	side = 0
	normal = Vector2.ZERO
	blocked_time = 0.0
	_free = 0.0

func following() -> bool:
	return side != 0

func _tangent() -> Vector2:
	return normal.orthogonal() * float(side)

## +1 or -1: the hand along the met solid that is the shorter way round to `goal`, found by feeling along
## the solid each way (a short ray into it every FEEL_STEP texels) for where it ends; 0 without a goal or
## when neither end is found within FEEL_MAX.
func _shorter_hand(body: Node2D, goal: Vector2) -> int:
	if goal == Vector2.INF or not body.is_inside_tree():
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
		var d := FEEL_STEP
		while d <= FEEL_MAX:
			var p := centre + t * d
			if not space.intersect_ray(PhysicsRayQueryParameters2D.create(centre, p, 1)).is_empty():
				break                                    # another solid across that way
			if space.intersect_ray(PhysicsRayQueryParameters2D.create(p, p - normal * 24.0, 1)).is_empty():
				cost[k] = d + p.distance_to(goal)        # the solid ends here
				break
			d += FEEL_STEP
	if cost[0] == INF and cost[1] == INF:
		return 0
	return 1 if cost[0] <= cost[1] else -1

## The unit direction to move in, given the unit direction wanted (and, optionally, the point it wants).
func direction(body: CharacterBody2D, want: Vector2, delta: float, goal := Vector2.INF) -> Vector2:
	if want.length() < 0.01:
		return Vector2.ZERO
	want = want.normalized()
	var normals: Array[Vector2] = []
	for i in body.get_slide_collision_count():
		normals.append(body.get_slide_collision(i).get_normal())
	if side == 0:
		var worst := ENTER
		for n in normals:
			var d := want.dot(n)
			if d < worst:
				worst = d
				normal = n
		if worst >= ENTER:
			return want
		# the hand that keeps more of the wanted way; dead on, the same hand every time; with a goal, the
		# shorter way round
		side = 1 if want.dot(normal.orthogonal()) >= -0.01 else -1
		var by_end := _shorter_hand(body, goal)
		if by_end != 0:
			side = by_end
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
		if touching:
			_free = 0.0
			if want.dot(normal) > LEAVE:
				side = 0
				return want
		else:
			_free += delta
			if _free > CLEAR:
				side = 0
				return want
	blocked_time += delta
	return (_tangent() - normal * INTO).normalized()
