extends GdUnitTestSuite
## Free-kill spots that were faults of the world's solids, not of the combat rules (11 Nov, the
## combat audit of #468, findings 3 and 4; docs/physics.md, rules 4 and 5).
##   1. the Undercroft: a strip the player fits and a creature (r 12, 24 wide) does not. The corridor's
##      roots and the hall's rubble stood 24 texels off the south wall's foot, the seal room's rubble
##      box 24 off the doorway's wall: the shield and the rusher were shot for free from (816, 492).
##      The roots now stand 6 texels off the wall's foot and the rubble 4, closer than a body; the
##      seal rubble's box starts where its stones are drawn.
##   2. the woodland: the holly's and the bramble's boxes met in an inside corner at (610, 1570) that
##      faced the meadow camp, so mosslings chasing a player at (600, 1720) stood in it. The bramble now
##      stands clear of the holly, and a mossling's body passes all the way round each of them.

const SAVE := "user://test_world_pockets_save.json"
const PLAYER_R := 9.0       ## actors/player.tscn: a circle of r 9 ...
const PLAYER_UP := 4.0      ## ... its centre 4 texels above the feet
const CREATURE_R := 12.0    ## enemies/slice_enemy.gd: a circle of r 12 on the feet
const NEAR := 15.0          ## where the player stands, a creature can stand this near (texels)
const STEP := 6.0
const MOSSLING_R := 10.0     ## actors/enemy.tscn: a circle of r 10 ...
const MOSSLING_UP := 8.0     ## ... its centre 8 texels above the feet

var _holder: Node2D
var _player: Player

func before_test() -> void:
	SaveGame.reset()
	SaveGame.path = SAVE
	_holder = auto_free(Node2D.new())
	add_child(_holder)
	_player = auto_free(load("res://actors/player.tscn").instantiate())
	_player.input_enabled = false
	Zones.current = null
	Zones.attach(_holder, _player)

func after_test() -> void:
	SaveGame.path = SaveGame.DEFAULT_PATH
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SAVE))
	Zones.current = null
	Zones.root = null
	SaveGame.reset()

func _enter(zone: String, spawn := "start") -> Zone:
	assert_bool(Zones.go_to(zone, spawn)).is_true()
	return Zones.current

func _ticks(n: int) -> void:
	for i in n:
		await get_tree().physics_frame

## True when a circle of radius `r` centred at `at` overlaps no solid (layer 1, which low solids share).
func _fits(space: PhysicsDirectSpaceState2D, at: Vector2, r: float) -> bool:
	var circle := CircleShape2D.new()
	circle.radius = r
	var q := PhysicsShapeQueryParameters2D.new()
	q.shape = circle
	q.transform = Transform2D(0.0, at)
	q.collision_mask = 1
	q.collide_with_areas = false
	return space.intersect_shape(q, 1).is_empty()

# --- 1. the Undercroft --------------------------------------------------------------------------
func test_the_player_cannot_stand_in_the_strip_behind_the_corridor_roots() -> void:
	var zone := _enter("undercroft")
	await _ticks(2)
	var space := zone.get_world_2d().direct_space_state
	# the audit's spot (816, 492), and every place along and across the strip that was there (feet
	# 484 to 499 between the roots' old box and the wall's foot at 504): nobody's feet go there
	var fits: Array[Vector2] = []
	for x in range(786, 847, 6):
		for y in range(484, 500):
			var feet := Vector2(x, y)
			if _fits(space, feet + Vector2(0, -PLAYER_UP), PLAYER_R):
				fits.append(feet)
	assert_array(fits).override_failure_message(
		"the player fits at %s, between the corridor's roots and the south wall, where no creature can follow" % str(fits)).is_empty()

## True when a creature fits within NEAR of `feet`: on the coarse map, else searched on a 1 texel grid.
func _creature_near(space: PhysicsDirectSpaceState2D, coarse: Dictionary, feet: Vector2) -> bool:
	var c := Vector2i((feet / STEP).round())
	var reach := int(ceil(NEAR / STEP))
	for di in range(-reach, reach + 1):
		for dj in range(-reach, reach + 1):
			if coarse.has(c + Vector2i(di, dj)) and (Vector2(c + Vector2i(di, dj)) * STEP).distance_to(feet) <= NEAR:
				return true
	for dx in range(-int(NEAR), int(NEAR) + 1):
		for dy in range(-int(NEAR), int(NEAR) + 1):
			if Vector2(dx, dy).length() <= NEAR and _fits(space, feet + Vector2(dx, dy), CREATURE_R):
				return true
	return false

func test_wherever_the_player_stands_in_the_undercroft_rooms_a_creature_can_come_beside_it() -> void:
	# A place the player fits and a creature (r 12) cannot come near is a place to shoot the rooms'
	# creatures from for free. On a 6 texel grid over the hall, the corridor and the seal room (west of
	# the chamber's wall, x < 1680; the Thornback's chamber is its own fight): wherever the player's
	# body fits, a creature's fits within 15 texels of its feet (against a wall the two stand 3 apart).
	var zone := _enter("undercroft")
	await _ticks(2)
	var space := zone.get_world_2d().direct_space_state
	var east := _rect(zone.get_node("Walls/Wall_sep3_n")).position.x
	var ny := int((zone.get_node("Ground") as Sprite2D).texture.get_size().y / STEP)
	var nx := int(east / STEP)
	var coarse := {}
	for i in nx:
		for j in ny:
			if _fits(space, Vector2(i, j) * STEP, CREATURE_R):
				coarse[Vector2i(i, j)] = true
	var lonely: Array[Vector2] = []
	var stands := 0
	for i in nx:
		for j in ny:
			var feet := Vector2(i, j) * STEP
			if not _fits(space, feet + Vector2(0, -PLAYER_UP), PLAYER_R):
				continue
			stands += 1
			if not _creature_near(space, coarse, feet):
				lonely.append(feet)
	assert_int(stands).is_greater(2000)
	assert_array(lonely).override_failure_message(
		"the player stands at %s where no creature comes within %.0f texels" % [str(lonely), NEAR]).is_empty()

## The rectangle of a body's one rectangle shape, in the zone.
func _rect(node: Node) -> Rect2:
	var shape := node.get_node("Shape") as CollisionShape2D
	var size := (shape.shape as RectangleShape2D).size
	return Rect2(shape.global_position - size / 2.0, size)

# --- 2. the woodland ----------------------------------------------------------------------------
## The rectangle of the woodland object `id`'s solid (Walls or LowWalls, s_<id>).
func _solid(zone: Zone, id: String) -> Rect2:
	for parent in ["Base/Walls", "Base/LowWalls"]:
		var n := zone.get_node_or_null("%s/s_%s" % [parent, id]) as CollisionShape2D
		if n != null:
			var size := (n.shape as RectangleShape2D).size
			return Rect2(n.global_position - size / 2.0, size)
	assert_bool(false).override_failure_message("no solid s_%s" % id).is_true()
	return Rect2()

## The places round `box` where a mossling's body (r 10 at its feet less 8) just clears it, every
## 3 texels: its four sides and its four corners, the way a body following that solid goes round it.
func _ring(box: Rect2) -> Array[Vector2]:
	var g := MOSSLING_R + 1.0
	var outer := box.grow(g)
	var pts: Array[Vector2] = []
	var x := outer.position.x
	while x <= outer.end.x:
		pts.append(Vector2(x, outer.position.y))
		pts.append(Vector2(x, outer.end.y))
		x += 3.0
	var y := outer.position.y
	while y <= outer.end.y:
		pts.append(Vector2(outer.position.x, y))
		pts.append(Vector2(outer.end.x, y))
		y += 3.0
	return pts

func test_a_mossling_can_go_round_the_holly_and_the_bramble_south_of_the_meadow_camp() -> void:
	# The pocket at (610, 1570): the holly's box (wood-37) reached 7 texels past the bramble's (wood-38)
	# west end and 6 above it, an inside corner facing the camp. A mossling chasing a player south of the
	# bramble (600, 1720) followed the bramble's top edge west, as the short way round, met the holly and
	# stood in the corner. Each of the two is now a solid a body can walk all the way round: nothing
	# else stands where a mossling's body passes along its sides and round its corners.
	var zone := _enter("woodland")
	await _ticks(2)
	var space := zone.get_world_2d().direct_space_state
	for id: String in ["wood-37", "wood-38"]:
		var box := _solid(zone, id)
		var blocked: Array[Vector2] = []
		for centre in _ring(box):
			if not _fits(space, centre, MOSSLING_R):
				blocked.append(centre + Vector2(0, MOSSLING_UP))
		assert_array(blocked).override_failure_message(
			"a mossling cannot pass round %s %s: its feet do not fit at %s" % [id, box, str(blocked.slice(0, 6))]).is_empty()
	# and the audit's spot is no corner: from (610, 1562), against the holly's east end, a mossling's
	# body steps on south past it
	var feet := Vector2(610, 1580)
	assert_bool(_fits(space, feet - Vector2(0, MOSSLING_UP), MOSSLING_R)).override_failure_message(
		"a mossling's feet do not fit at %s, south of the corner at (610, 1562): the corner holds it" % feet).is_true()

