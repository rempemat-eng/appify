extends GdUnitTestSuite
## The world fixes of 11 Nov, one rule each: the hut's rest, the seal plate off the walk to the lever,
## Crossroads' retaining faces in one line, the Undercroft's boxes on what is drawn and no body-wide
## slots, arrival spawns clear of their doors, the kit woodland in step with the woodland, layer 5's
## name, the forge's fire waiting for Hale, and arrivals looking into the zone.

const SAVE := "user://test_world_fixes_save.json"
const BODY := 18.0          ## the player's body: a circle of r 9
const BODY_UP := 4.0        ## its centre, texels above the feet

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

func _saved() -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(SAVE))

## The rectangle of a body's or an area's one rectangle shape, in the zone.
func _rect(node: Node) -> Rect2:
	var shape := node.get_node("Shape") as CollisionShape2D
	var size := (shape.shape as RectangleShape2D).size
	return Rect2(shape.global_position - size / 2.0, size)

## The gap between two rectangles along one axis when they overlap on the other; -1 when they do not face.
func _gap(a: Rect2, b: Rect2) -> float:
	var over_x := minf(a.end.x, b.end.x) - maxf(a.position.x, b.position.x)
	var over_y := minf(a.end.y, b.end.y) - maxf(a.position.y, b.position.y)
	if over_x > 0.0 and over_y <= 0.0:
		return -over_y
	if over_y > 0.0 and over_x <= 0.0:
		return -over_x
	return -1.0

func _dist_to_rect(p: Vector2, r: Rect2) -> float:
	return Vector2(maxf(maxf(r.position.x - p.x, p.x - r.end.x), 0.0), maxf(maxf(r.position.y - p.y, p.y - r.end.y), 0.0)).length()

# --- 1. the hut's rest ------------------------------------------------------------------------
func _at_the_hut() -> RestSpot:
	var zone := _enter("crossroads", "hut")
	var spot := zone.get_node("Actors/HutBed") as RestSpot
	assert_object(spot).is_not_null()
	await _ticks(3)
	return spot

func test_the_hut_door_gives_full_hearts_saves_and_costs_nothing() -> void:
	var spot: RestSpot = await _at_the_hut()
	assert_str(spot.verb).is_equal("Rest")
	assert_object(_player.focus).is_same(spot)     # arriving at the hut spawn, the prompt is the hut's
	SaveGame.data.glint = 37
	_player.hp = 2
	spot.interact()
	await _ticks(2)
	assert_int(_player.hp).is_equal(_player.max_hp)
	assert_int(int(SaveGame.data.glint)).is_equal(37)
	assert_int(int(_saved().player.hp)).is_equal(_player.max_hp)
	assert_int(int(_saved().glint)).is_equal(37)
	assert_str(str(_saved().zone)).is_equal("crossroads")
	# nothing else moved: no quest started, no reward, no flag but the visit
	assert_dict(SaveGame.data.quests).is_empty()
	# the lines say what happened and promise no bed behind a door that does not open
	var said := " ".join(Dialogue.lines_for("hut_door"))
	assert_str(said).contains("swollen shut")
	assert_str(said).not_contains("can wait")

func test_no_rest_during_a_fight_or_a_line() -> void:
	var spot: RestSpot = await _at_the_hut()
	_player.hp = 2
	# a living enemy on the terrace: no prompt, and E does nothing
	var enemy: Node2D = auto_free(load("res://actors/enemy.tscn").instantiate())
	enemy.position = spot.position + Vector2(200, 60)
	Zones.current.actors.add_child(enemy)
	await _ticks(3)
	assert_bool(spot.fight_near()).is_true()
	assert_bool(spot.usable()).is_false()
	assert_object(_player.focus).is_null()
	spot.interact()
	assert_int(_player.hp).is_equal(2)
	# freed, it is no fight any more
	enemy.set("dead", true)
	enemy.set("hp", 0)
	await _ticks(3)
	assert_bool(spot.fight_near()).is_false()
	assert_object(_player.focus).is_same(spot)
	# a line open: nothing
	Dialogue.busy = true
	spot.interact()
	assert_int(_player.hp).is_equal(2)
	Dialogue.busy = false
	spot.interact()
	assert_int(_player.hp).is_equal(_player.max_hp)

func test_the_rest_is_shown_quietly_and_ends() -> void:
	var spot: RestSpot = await _at_the_hut()
	_player.hp = 1
	spot.interact()
	await _ticks(2)
	var hush := spot.get_node_or_null("RestHush") as CanvasModulate
	assert_object(hush).is_not_null()
	await get_tree().create_timer(RestSpot.HUSH_IN + RestSpot.HUSH_OUT + 0.3).timeout
	assert_bool(is_instance_valid(hush) and hush.is_inside_tree()).is_false()   # finite: gone again
	# under reduced motion the world does not dim at all
	SaveGame.data.settings["reduced_motion"] = true
	_player.hp = 1
	spot.interact()
	await _ticks(2)
	assert_int(_player.hp).is_equal(_player.max_hp)
	assert_object(spot.get_node_or_null("RestHush")).is_null()

# --- 2. the seal plate ------------------------------------------------------------------------
func test_the_walk_from_the_doorway_to_the_lever_misses_the_plate() -> void:
	var zone := _enter("undercroft")
	var plate := _rect(zone.get_node("Actors/SealPlate"))
	var lever := (zone.get_node("Actors/SealLever") as Node2D).global_position
	# the doorway into the seal room: between the two blocks of the wall west of it
	var north := _rect(zone.get_node("Walls/Wall_sep2_n"))
	var south := _rect(zone.get_node("Walls/Wall_sep2_s"))
	var from := Vector2(north.end.x, (north.end.y + south.position.y) / 2.0)
	var to := lever + Vector2(0, Interactable.REACH * 0.5)      # where the Pull prompt is well in reach
	var nearest := INF
	for i in 201:
		var feet := from.lerp(to, i / 200.0)
		nearest = minf(nearest, _dist_to_rect(feet + Vector2(0, -BODY_UP), plate))
	assert_float(nearest).override_failure_message(
		"walking straight from the doorway to the lever passes %.1f texels from the plate: a body (r 9) presses it" % nearest) \
		.is_greater(BODY / 2.0 + 6.0)
	# nor does walking east along the doorway's own axis, to the slab
	var slab := Vector2(_rect(zone.get_node("Walls/Wall_sep3_n")).position.x, from.y)
	nearest = INF
	for i in 201:
		nearest = minf(nearest, _dist_to_rect(from.lerp(slab, i / 200.0) + Vector2(0, -BODY_UP), plate))
	assert_float(nearest).override_failure_message(
		"walking east along the doorway's axis passes %.1f texels from the plate" % nearest).is_greater(BODY / 2.0 + 6.0)
	# feet on the slab press it
	var on_it := (zone.get_node("Actors/SealPlate") as Node2D).global_position
	assert_float(_dist_to_rect(on_it + Vector2(0, -BODY_UP), plate)).is_less(BODY / 2.0)
	# and the plate still starts the channel: its picture reaches the channel's west end
	var channel := zone.get_node("Floor/If_channel_lit/ChannelLit") as Sprite2D
	var plate_pic := zone.get_node("Floor/If_plate_up/PlateUp") as Sprite2D
	var pic := Rect2(plate_pic.global_position + plate_pic.offset, plate_pic.texture.get_size())
	assert_bool(pic.grow(3.0).has_point(channel.global_position)).is_true()

# --- 3. Crossroads' retaining faces -----------------------------------------------------------
func test_the_garden_walk_and_the_terrace_share_one_wall_foot() -> void:
	var zone := _enter("crossroads")
	var lane := _rect(zone.get_node("Walls/Face_lane_face"))
	var terrace := _rect(zone.get_node("Walls/Face_terrace_face_w"))
	assert_float(lane.end.x).is_equal(terrace.position.x)            # they meet
	assert_float(lane.end.y).override_failure_message(
		"the garden walk's face ends at y %.0f and the terrace's at %.0f: one drawn wall, a step in its solid" % [lane.end.y, terrace.end.y]) \
		.is_equal(terrace.end.y)

# --- 4. the Undercroft's boxes ----------------------------------------------------------------
func test_no_undercroft_solid_leaves_a_body_wide_slot() -> void:
	# A gap a body just fits (18 texels) and cannot turn in is a place to get wedged: a prop stands
	# against its wall, closer than a body, or at least a body and a third clear of it.
	var zone := _enter("undercroft")
	var walls: Array[Rect2] = []
	var props := {}
	for n in zone.get_node("Walls").get_children():
		if String(n.name).begins_with("Solid_"):
			props[String(n.name)] = _rect(n)
		else:
			walls.append(_rect(n))
	assert_int(props.size()).is_greater(6)
	for name_: String in props:
		for w in walls:
			var gap := _gap(props[name_], w)
			assert_bool(gap < BODY or gap >= BODY + 6.0).override_failure_message(
				"%s stands %.0f texels from a wall: a slot one body wide" % [name_, gap]).is_true()

func test_the_undercroft_roots_and_pillars_block_what_is_drawn() -> void:
	var zone := _enter("undercroft")
	# box, then the picture's texels in the rows the box covers must fill it: no more than 8 texels of
	# plain floor inside the box on either side, and the box no narrower than three fifths of them (a
	# root that runs aslant and a plinth's scattered pebbles are wider than what stops a foot)
	for id: String in ["roots_hall", "stump_nw", "stump_se", "rubble_seal"]:
		var box := _rect(zone.get_node("Walls/Solid_" + id))
		var pic := zone.get_node("Props/" + id.to_pascal_case()) as Sprite2D
		var img := pic.texture.get_image()
		var origin := pic.global_position + pic.offset
		var lo := INF
		var hi := -INF
		for y in range(int(box.position.y), int(box.end.y)):
			var py := y - int(origin.y)
			if py < 0 or py >= img.get_height():
				continue
			for px in img.get_width():
				if img.get_pixel(px, py).a > 0.5:
					lo = minf(lo, origin.x + px)
					hi = maxf(hi, origin.x + px + 1.0)
		assert_float(lo - box.position.x).override_failure_message("%s: %.0f texels of bare floor inside its box on the west" % [id, lo - box.position.x]).is_less_equal(8.0)
		assert_float(box.end.x - hi).override_failure_message("%s: %.0f texels of bare floor inside its box on the east" % [id, box.end.x - hi]).is_less_equal(8.0)
		assert_float(box.size.x).override_failure_message("%s blocks %.0f of %.0f drawn texels" % [id, box.size.x, hi - lo]).is_greater_equal((hi - lo) * 0.6)

# --- 5. arrival spawns ------------------------------------------------------------------------
func test_arrivals_stand_clear_of_their_door_and_in_the_open() -> void:
	# A door arms 0.4 s after the zone loads and the walk covers 27 texels in that time: an arrival
	# stands further than that from the door it came through, a body clear of every solid and unhidden.
	for pair: Array in [["woodland", "crossroads"], ["woodland", "undercroft"], ["crossroads", "woodland"], ["undercroft", "start"]]:
		var zone := _enter(pair[0], pair[1])
		await _ticks(40)
		var feet := _player.global_position
		var nearest := INF
		for d in zone.get_node("Doors").get_children():
			nearest = minf(nearest, _dist_to_rect(feet + Vector2(0, -BODY_UP), _rect(d)) - BODY / 2.0)
		assert_float(nearest).override_failure_message("%s:%s stands %.0f texels from its door" % [pair[0], pair[1], nearest]).is_between(32.0, 90.0)
		var query := PhysicsShapeQueryParameters2D.new()
		var circle := CircleShape2D.new()
		circle.radius = BODY / 2.0 + BODY
		query.shape = circle
		query.transform = Transform2D(0.0, feet + Vector2(0, -BODY_UP))
		query.collision_mask = 1
		var hits := zone.get_world_2d().direct_space_state.intersect_shape(query, 4)
		# the Undercroft's stair is a slot in the west wall, and the hatch stands by the stones: named, not waved through
		if pair != ["undercroft", "start"]:
			assert_array(hits).override_failure_message("%s:%s is within a body of a solid" % [pair[0], pair[1]]).is_empty()
		assert_float(zone.occlusion.hidden_share(_player)).is_less(Occlusion.HIDDEN_SHARE)

# --- 6. the kit woodland ----------------------------------------------------------------------
func _gameplay(node: Node, root: Node, out: Dictionary) -> void:
	if node != root:
		var row := {"class": node.get_class()}
		if node is Node2D:
			row["position"] = (node as Node2D).position
		for key: String in ["only_if", "speaker_id", "verb", "camp_id", "target_zone", "target_spawn", "character", "facing_at_rest"]:
			if key in node:
				row[key] = node.get(key)
		out[String(root.get_path_to(node))] = row
	for c in node.get_children():
		if c.owner == null and node != root and not c is CollisionShape2D:
			continue                # nodes a script made at run time
		_gameplay(c, root, out)

func test_the_kit_woodland_has_the_woodland_s_people_spawns_and_doors() -> void:
	# woodland_kit takes its Actors, Spawns and Doors from the woodland (gameplay_from). They are not in
	# its plan, so only this holds the committed scene to its source (docs/world-editor.md, N2).
	var plan: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://kit/zones/woodland_kit.json"))
	var source := (load(String(plan.gameplay_from)) as PackedScene).instantiate()
	var kit := (load("res://zones/woodland_kit/woodland_kit.tscn") as PackedScene).instantiate()
	for group: String in ["Actors", "Spawns", "Doors"]:
		var want := {}
		var got := {}
		_gameplay(source.get_node(group), source.get_node(group), want)
		_gameplay(kit.get_node(group), kit.get_node(group), got)
		assert_int(want.size()).is_greater(0)
		for path: String in want:
			if group == "Spawns" and plan.get("spawns", {}).has(path):
				continue            # the plan names its own (start, where the kit zone's review begins)
			assert_bool(got.has(path)).override_failure_message("woodland_kit has no %s/%s" % [group, path]).is_true()
			if got.has(path):
				assert_dict(got[path]).override_failure_message(
					"woodland_kit %s/%s is %s, the woodland's is %s: rebuild the scene from its plan" % [group, path, got[path], want[path]]) \
					.is_equal(want[path])
		for path: String in got:
			if group == "Spawns" and plan.get("spawns", {}).has(path):
				continue
			assert_bool(want.has(path)).override_failure_message("woodland_kit has %s/%s, the woodland does not" % [group, path]).is_true()
	source.free()
	kit.free()

# --- 7. layer names ---------------------------------------------------------------------------
func test_the_low_layer_is_named() -> void:
	var names := ["walls", "player", "enemy", "interact", "low"]
	for i in names.size():
		assert_str(str(ProjectSettings.get_setting("layer_names/2d_physics/layer_%d" % (i + 1), ""))).is_equal(names[i])

# --- 8. the forge's fire ----------------------------------------------------------------------
func test_a_forge_paid_before_hale_is_home_has_no_flame_until_she_is() -> void:
	SaveGame.add_glint(30)
	var zone := _enter("crossroads")
	var fire := zone.get_node("Props/If_forge_fire") as Conditional
	var smoke := zone.get_node("Props/If_smithy_smoke") as Conditional
	assert_bool(fire.visible).is_false()
	# the mark says "under the ash in the hearth an ember is still alive": no flame, no smoke
	assert_str(" ".join(Dialogue.lines_for("restore_forge"))).contains("ember")
	assert_bool(Village.restore("forge")).is_true()
	await _ticks(2)
	assert_bool(fire.visible).override_failure_message("the forge burns at full flame with nobody home").is_false()
	assert_bool(smoke.visible).is_false()
	# she walks home with the next zone load, and her fire is lit
	Quests.notify("talk:hale")
	_enter("woodland", "crossroads")
	zone = _enter("crossroads", "woodland")
	assert_bool(SaveGame.has_flag("hale_walked_home")).is_true()
	assert_bool((zone.get_node("Props/If_forge_fire") as Conditional).visible).is_true()
	assert_bool((zone.get_node("Props/If_smithy_smoke") as Conditional).visible).is_true()
	assert_bool((zone.get_node("Actors/If_hale_forge") as Conditional).visible).is_true()

func test_a_forge_paid_with_hale_watching_lights_at_once() -> void:
	SaveGame.add_glint(30)
	SaveGame.set_flag("hale_walked_home")
	var zone := _enter("crossroads")
	assert_str(" ".join(Dialogue.lines_for("restore_forge"))).contains("Hale's fire takes")
	assert_bool(Village.restore("forge")).is_true()
	await _ticks(2)
	assert_bool((zone.get_node("Props/If_forge_fire") as Conditional).visible).is_true()

# --- 9. arriving ------------------------------------------------------------------------------
func test_an_arrival_looks_away_from_its_door() -> void:
	_player.use_mouse_aim = false
	for row: Array in [["undercroft", "start", "E"], ["woodland", "undercroft", "S"], ["woodland", "crossroads", "W"], ["crossroads", "woodland", "E"]]:
		_player.aim = Vector2.UP if row[2] != "N" else Vector2.DOWN
		_player.facing = "N"
		_enter(row[0], row[1])
		assert_str(_player.facing).override_failure_message("arriving at %s:%s the player faces %s" % [row[0], row[1], _player.facing]).is_equal(row[2])
		await _ticks(3)
		assert_str(_player.facing).is_equal(row[2])
	# a spawn that is no door's (the woodland's start) leaves the facing alone
	_player.aim = Vector2.LEFT
	_player.facing = "W"
	_enter("woodland", "start")
	assert_str(_player.facing).is_equal("W")

func test_the_undercroft_arrival_stands_inside_the_hall_in_front_of_the_stair() -> void:
	var zone := _enter("undercroft")
	var door := _rect(zone.get_node("Doors/ToWoodland"))
	var west := _rect(zone.get_node("Walls/Wall_west_n"))
	# east of the wall the stair comes through, level with the door, on the hall's floor
	assert_float(_player.global_position.x).is_greater(west.end.x + BODY)
	assert_float(_player.global_position.y).is_between(door.position.y, door.end.y)
	assert_float(door.end.x).is_less(west.end.x)        # the door's area is inside the stair's slot, not in the hall
