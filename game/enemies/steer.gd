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

var side := 0           ## 0 free; +1 or -1 the hand kept on the wall
var normal := Vector2.ZERO
var blocked_time := 0.0 ## seconds spent following walls since the last reset
var _free := 0.0

func reset() -> void:
	side = 0
	normal = Vector2.ZERO
	blocked_time = 0.0
	_free = 0.0

func following() -> bool:
	return side != 0

func _tangent() -> Vector2:
	return normal.orthogonal() * float(side)

## The unit direction to move in, given the unit direction wanted.
func direction(body: CharacterBody2D, want: Vector2, delta: float) -> Vector2:
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
		# the hand that keeps more of the wanted way; dead on, the same hand every time
		side = 1 if want.dot(normal.orthogonal()) >= -0.01 else -1
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
