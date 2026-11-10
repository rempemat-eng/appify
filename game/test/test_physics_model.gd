extends GdUnitTestSuite
## The physics model of the three playable zones, as docs/physics.md states it: which layer and mask every
## body and area is on, that solids fit what is drawn, that the world is closed, and that every y-sorted
## picture sorts by its drawn feet. Regenerating a zone or adding a body kind must keep these true.

const ZONES := ["woodland", "crossroads", "undercroft"]
const WALLS := 1
const PLAYER := 2
const ENEMY := 4
const INTERACT := 8
const LOW := 16
## Pictures that sort where they do on purpose, with the reason (never a tolerance).
const SORT_EXEMPT := {
	"lintel-1": "lies across two standing stones: it sorts by their feet, not by its own underside",
}

var _table: Dictionary
var _holder: Node2D
var _player: Player

func before_test() -> void:
	SaveGame.reset()
	_table = Zones.table
	_holder = auto_free(Node2D.new())
	add_child(_holder)
	_player = auto_free(load("res://actors/player.tscn").instantiate())
	_player.input_enabled = false
	Zones.current = null
	Zones.attach(_holder, _player)

func after_test() -> void:
	SaveGame.reset()
	Zones.table = _table
	Zones.current = null
	Zones.root = null

func _enter(zone: String) -> Zone:
	assert_bool(Zones.go_to(zone, "start")).is_true()
	return Zones.current

func _all(node: Node, out: Array = []) -> Array:
	out.append(node)
	for c in node.get_children():
		_all(c, out)
	return out

func _where(n: Node) -> String:
	return "%s:%s" % [Zones.current.zone_id, Zones.current.get_path_to(n)]

# --- layers and masks -------------------------------------------------------------------------
func test_every_static_body_is_a_wall_or_a_low_wall() -> void:
	for id in ZONES:
		var zone := _enter(id)
		var bodies := 0
		for n in _all(zone):
			if not n is StaticBody2D:
				continue
			bodies += 1
			var b := n as StaticBody2D
			assert_bool(b.collision_layer == WALLS or b.collision_layer == (WALLS | LOW)) \
				.override_failure_message("%s is on layer %d: a solid is on 1, a low solid on 1 and 5 (17)" % [_where(b), b.collision_layer]).is_true()
			assert_int(b.collision_mask).override_failure_message("%s has a mask: solids detect nothing" % _where(b)).is_equal(0)
			var shapes := 0
			for c in b.get_children():
				if c is CollisionShape2D and c.shape != null:
					shapes += 1
			assert_int(shapes).override_failure_message("%s has no shape" % _where(b)).is_greater(0)
		assert_int(bodies).is_greater(1)

func test_what_must_stop_a_shot_is_never_low() -> void:
	# walls, wall faces, buildings, the zone's edges, the sealed slab and the posts of people and signs
	for id in ZONES:
		var zone := _enter(id)
		for n in _all(zone):
			if not n is StaticBody2D:
				continue
			var name_ := String(n.name)
			var tall := name_ == "Walls" or name_ == "Post" or name_ == "SealSlabBody"
			for prefix in ["Wall_", "Edge", "Face_", "Building_"]:
				tall = tall or name_.begins_with(prefix)
			if tall:
				assert_int(n.collision_layer).override_failure_message("%s must stop shots" % _where(n)).is_equal(WALLS)

func test_areas_and_actors_are_on_their_layers() -> void:
	for id in ZONES:
		var zone := _enter(id)
		await get_tree().physics_frame
		for n in _all(zone):
			if n is Door or n is PressurePlate:
				assert_int(n.collision_layer).override_failure_message(_where(n)).is_equal(0)
				assert_int(n.collision_mask).override_failure_message(_where(n)).is_equal(PLAYER)
			elif n is Interactable:
				assert_int(n.collision_layer).override_failure_message(_where(n)).is_equal(INTERACT)
				assert_int(n.collision_mask).override_failure_message(_where(n)).is_equal(PLAYER)
			elif n is Player:
				assert_int(n.collision_layer).is_equal(PLAYER)
				assert_int(n.collision_mask).is_equal(WALLS)
				var hitbox := n.get_node("Hitbox") as Area2D
				assert_int(hitbox.collision_layer).is_equal(0)
				assert_int(hitbox.collision_mask).is_equal(ENEMY)
			elif n is CharacterBody2D:
				assert_bool(n.is_in_group("enemy")).override_failure_message("%s: a moving body that is neither the player nor an enemy" % _where(n)).is_true()
				assert_int(n.collision_layer).override_failure_message(_where(n)).is_equal(ENEMY)
				assert_int(n.collision_mask).override_failure_message(_where(n)).is_equal(WALLS)
			elif n is Area2D and not n.get_parent() is Player:
				assert_bool(false).override_failure_message("%s: an area kind the model does not know (add it to docs/physics.md and here)" % _where(n)).is_true()

func test_an_arrow_meets_walls_and_enemies() -> void:
	var arrow: Arrow = auto_free(Arrow.new())
	add_child(arrow)
	assert_int(arrow.collision_layer).is_equal(0)
	assert_int(arrow.collision_mask).is_equal(WALLS | ENEMY)

# --- the world is closed and its solids fit ---------------------------------------------------
func _blocked(zone: Zone, at: Vector2) -> Array:
	var q := PhysicsPointQueryParameters2D.new()
	q.position = at
	q.collision_mask = WALLS
	return zone.get_world_2d().direct_space_state.intersect_point(q, 4)

func test_nobody_walks_off_a_zone() -> void:
	# a solid stands just outside every edge of the picture, all the way round
	for id in ZONES:
		var zone := _enter(id)
		await get_tree().physics_frame
		await get_tree().physics_frame
		var b := zone.bounds
		for i in 40:
			var t := (i + 0.5) / 40.0
			for at in [Vector2(b.position.x + b.size.x * t, b.position.y - 6), Vector2(b.position.x + b.size.x * t, b.end.y + 6),
					Vector2(b.position.x - 6, b.position.y + b.size.y * t), Vector2(b.end.x + 6, b.position.y + b.size.y * t)]:
				assert_bool(_blocked(zone, at).is_empty()).override_failure_message("%s: nothing stops a walker at %s, outside the zone" % [id, at]).is_false()

func test_the_woodland_is_split_into_walls_and_low_walls() -> void:
	var zone := _enter("woodland")
	await get_tree().physics_frame
	await get_tree().physics_frame
	var walls := zone.get_node("Base/Walls") as StaticBody2D
	var low := zone.get_node("Base/LowWalls") as StaticBody2D
	assert_int(walls.collision_layer).is_equal(WALLS)
	assert_int(low.collision_layer).is_equal(WALLS | LOW)
	# the stream and the pool are low (an arrow crosses water); the cliff face and the rock bank are walls
	for at in [Vector2(192, 400), Vector2(600, 900)]:
		var hit := _blocked(zone, at)
		assert_int(hit.size()).override_failure_message("water at %s blocks nobody" % at).is_greater(0)
		assert_object(hit[0].collider).is_same(low)
	for at in [Vector2(600, 800), Vector2(600, 20)]:
		var hit := _blocked(zone, at)
		assert_int(hit.size()).is_greater(0)
		assert_object(hit[0].collider).is_same(walls)
	# the bench, the stumps and the log are low; trunks and standing stones are walls
	assert_object(low.get_node_or_null("s_bench")).is_not_null()
	assert_object(low.get_node_or_null("s_stump-1")).is_not_null()
	assert_object(low.get_node_or_null("s_log-1")).is_not_null()
	assert_object(walls.get_node_or_null("s_willow")).is_not_null()
	assert_object(walls.get_node_or_null("s_stone-6")).is_not_null()

func test_every_woodland_thing_that_stands_tall_has_a_solid() -> void:
	# the six saplings (82 texels, taller than the player) had no box in the kit library and were walked
	# straight through. Whatever stands 64 texels or more above its foot blocks feet and stops shots.
	var zone := _enter("woodland")
	var walls := zone.get_node("Base/Walls")
	var tall := 0
	for sprite: Sprite2D in zone.get_node("Base/Objects").get_children():
		if SORT_EXEMPT.has(String(sprite.name)):
			continue                        # the lintel lies on two stones and stands on nothing itself
		var rise := sprite.texture.get_image().get_used_rect().size.y
		if rise < 64:
			continue
		tall += 1
		assert_object(walls.get_node_or_null("s_" + String(sprite.name))).override_failure_message(
			"%s stands %d texels tall and has no solid on the walls layer" % [sprite.name, rise]).is_not_null()
	assert_int(tall).is_greater(40)
	var stem := (walls.get_node("s_wood-14") as CollisionShape2D).shape as RectangleShape2D
	assert_vector(stem.size).is_equal(Vector2(12, 9))

func test_a_woodland_solid_is_no_wider_than_what_is_drawn() -> void:
	# the willow's solid was 180 px wide for a 30 px trunk, because the old walk mask blocked a picture's
	# whole width at its feet. A solid may not reach more than 8 px past the texels drawn in its rows.
	var zone := _enter("woodland")
	var checked := 0
	for body_name in ["Walls", "LowWalls"]:
		for shape: CollisionShape2D in zone.get_node("Base/" + body_name).get_children():
			if not String(shape.name).begins_with("s_"):
				continue
			var sprite := zone.get_node_or_null("Base/Objects/" + String(shape.name).substr(2)) as Sprite2D
			assert_object(sprite).override_failure_message("%s has no picture" % shape.name).is_not_null()
			var size: Vector2 = (shape.shape as RectangleShape2D).size
			var solid := Rect2(shape.global_position - size / 2.0, size)
			var img := sprite.texture.get_image()
			var top_left := sprite.global_position + sprite.offset
			var x0 := img.get_width()
			var x1 := -1
			for y in range(int(solid.position.y - top_left.y), mini(int(solid.end.y - top_left.y), img.get_height())):
				for x in img.get_width():
					if img.get_pixel(x, y).a >= 0.5:
						x0 = mini(x0, x)
						x1 = maxi(x1, x + 1)
			assert_int(x1).override_failure_message("%s: nothing is drawn where its solid stands" % shape.name).is_greater(0)
			var over_left := (top_left.x + x0) - solid.position.x
			var over_right := solid.end.x - (top_left.x + x1)
			assert_float(maxf(over_left, over_right)).override_failure_message(
				"%s: its solid reaches %d px left and %d px right of what is drawn" % [shape.name, over_left, over_right]).is_less_equal(8.0)
			assert_float(size.x).override_failure_message("%s: its solid is %d px wide, under a third of the %d px drawn" % [shape.name, size.x, x1 - x0]) \
				.is_greater_equal((x1 - x0) / 3.0)
			checked += 1
	assert_int(checked).is_greater(60)

func test_the_willow_blocks_only_its_trunk() -> void:
	var zone := _enter("woodland")
	await get_tree().physics_frame
	await get_tree().physics_frame
	var shape := zone.get_node("Base/Walls/s_willow") as CollisionShape2D
	assert_float((shape.shape as RectangleShape2D).size.x).is_less_equal(40.0)
	# the main path under the crown, 60 px either side of the trunk, is open ground
	assert_bool(_blocked(zone, Vector2(700, 1300)).is_empty()).is_true()
	assert_bool(_blocked(zone, Vector2(860, 1310)).is_empty()).is_true()

func test_crossroads_solids_follow_the_reviewed_boxes() -> void:
	# the kit library's boxes reviewed against the art (3 Nov) never reached the playable zone: the lantern's
	# solid ran 22 world px up its post, the hollow oak's was 24 px wide in a 66 px trunk
	var zone := _enter("crossroads")
	var oak := (zone.get_node("Walls/Solid_oak_6/Shape") as CollisionShape2D).shape as RectangleShape2D
	assert_vector(oak.size).is_equal(Vector2(66, 15))
	SaveGame.reset()
	var lantern := (zone.get_node("Props/If_lantern_dark/LanternDarkBody/Shape") as CollisionShape2D).shape as RectangleShape2D
	assert_vector(lantern.size).is_equal(Vector2(42, 15))
	# the notice board and the waystone block their drawn base, not only the 5 px post of their talk area
	var board := (zone.get_node("Walls/Solid_notice_board/Shape") as CollisionShape2D).shape as RectangleShape2D
	assert_vector(board.size).is_equal(Vector2(63, 12))
	var stone := (zone.get_node("Walls/Solid_waystone/Shape") as CollisionShape2D).shape as RectangleShape2D
	assert_vector(stone.size).is_equal(Vector2(56, 12))
	assert_int((zone.get_node("Walls/Solid_bench_28") as StaticBody2D).collision_layer).is_equal(WALLS | LOW)
	assert_int((zone.get_node("Walls/Solid_oak_6") as StaticBody2D).collision_layer).is_equal(WALLS)

# --- the y-sort -------------------------------------------------------------------------------
## The node the y-sort orders `node` by: itself or its nearest ancestor whose parent is y-sorted.
func _sort_item(zone: Zone, node: Node2D) -> Node2D:
	var k: Node = node
	while k != null and k != zone:
		var p := k.get_parent() as CanvasItem
		if p != null and p.y_sort_enabled:
			return k as Node2D
		k = p
	return null

func _z(zone: Zone, node: CanvasItem) -> int:
	var z := 0
	var k: Node = node
	while k is CanvasItem and k != zone.get_parent():
		z += (k as CanvasItem).z_index
		k = k.get_parent()
	return z

func test_every_sorted_picture_sorts_by_its_drawn_feet() -> void:
	for id in ZONES:
		var zone := _enter(id)
		var checked := 0
		for n in _all(zone):
			var s := n as Sprite2D
			if s == null or s.texture == null or s is LoopFx or s.hframes > 1 or _z(zone, s) != 0:
				continue                    # the ground layers, wall torches and effect strips are not sorted against people
			if s.get_parent() is CharacterBody2D or s.get_parent() == zone.occlusion:
				continue
			var item := _sort_item(zone, s)
			if item == null or SORT_EXEMPT.has(String(s.name)):
				continue
			if String(s.name).ends_with("Damage") or s.get_parent().name == "ThornbackAtRest":
				continue                    # an overlay sorts one texel in front of its building; the boss asleep is an actor
			var used := s.texture.get_image().get_used_rect()
			var feet := s.global_position.y + s.offset.y + used.end.y - (s.texture.get_height() / 2.0 if s.centered else 0.0)
			assert_float(absf(item.global_position.y - feet)).override_failure_message(
				"%s: its y-sort point is %d px from its drawn feet" % [_where(s), item.global_position.y - feet]).is_less_equal(2.0)
			checked += 1
		assert_int(checked).override_failure_message("%s: no sorted pictures were checked" % id).is_greater(5)

func test_flat_things_never_draw_over_people() -> void:
	# beds and debris lie on the ground and block nobody: y-sorted by their far edge they hid a walker whole
	var zone := _enter("crossroads")
	for path in ["Props/If_beds_scorched/BedsScorched", "Props/If_beds_dug/BedsDug", "Props/If_debris_a/DebrisA"]:
		var s := zone.get_node(path) as Sprite2D
		assert_int(_z(zone, s)).override_failure_message(path).is_less(0)
	_player.global_position = Vector2(1200, 300)       # in the middle of the beds
	assert_float(zone.occlusion.hidden_share(_player)).is_equal(0.0)

func test_no_villager_stands_hidden() -> void:
	# villagers get no faint copy (world/occlusion.gd follows the player and enemies): they stand still, so
	# one hidden behind a crown or a roof is a placement fault. Checked in every state a Conditional can show.
	for id in ZONES:
		var zone := _enter(id)
		var seen := 0
		for n in _all(zone):
			if not (n is Interactable):
				continue
			var body := n.get_node_or_null("Body") as AnimatedSprite2D
			if body == null:
				continue
			var holder := n.get_parent() as CanvasItem
			var was := holder.visible
			holder.visible = true                      # as when its Conditional holds
			var share := zone.occlusion.hidden_share(n)
			holder.visible = was
			assert_float(share).override_failure_message("%s is %d %% hidden behind scenery" % [_where(n), share * 100.0]) \
				.is_less(Occlusion.HIDDEN_SHARE)
			seen += 1
		if id != "undercroft":
			assert_int(seen).override_failure_message("%s: no villagers were checked" % id).is_greater(0)
