extends GdUnitTestSuite
## Nothing in the three playable zones is out of the player's reach: from each zone's `start`, in every
## stage of the story, the walk grid (tools/walk_grid.gd: the player's body against the real walls)
## reaches every spawn, every open door and, with room to spare, a place where every talk area shows
## its prompt. The 10 Nov play-through found Moss, the notice board, the Ferns' restore mark and Cairn's
## statue with no prompt from where a walker could stand.

const WalkGrid := preload("res://tools/walk_grid.gd")
const ZONES := ["woodland", "crossroads", "undercroft"]
const MIN_CELLS := 150   ## 6 x 6 texel cells from which a talk area must be in reach (about 73 x 73 texels)
## The chamber behind the Undercroft's sealed slab: out of reach by design until the lever is pulled.
const BEHIND_THE_SEAL := ["CairnStatue", "CircleShard", "arena"]

## The story's stages, each as the flags and restores a save has by then.
const STAGES := {
	"fresh": {},
	"forge asked": {"flags": ["visited:crossroads"], "done": ["road_to_crossroads"], "active": ["cold_forge"]},
	"forge": {"restored": ["forge"], "flags": ["undercroft_open", "visited:crossroads"], "done": ["road_to_crossroads", "cold_forge"]},
	"seal open": {"restored": ["forge"], "flags": ["undercroft_open", "undercroft_plate", "undercroft_seal_open",
		"camp_cleared:undercroft_rooms"], "done": ["road_to_crossroads", "cold_forge"]},
	"homecoming": {"restored": ["forge"], "flags": ["undercroft_open", "undercroft_plate", "undercroft_seal_open",
		"camp_cleared:undercroft_rooms", "camp_cleared:thornback", "shard_taken:woodland", "shard_home:woodland"],
		"done": ["road_to_crossroads", "cold_forge", "under_the_stones"]},
	"ferns asked": {"restored": ["forge"], "flags": ["undercroft_open", "undercroft_plate", "undercroft_seal_open",
		"camp_cleared:undercroft_rooms", "camp_cleared:thornback", "shard_taken:woodland", "shard_home:woodland"],
		"done": ["road_to_crossroads", "cold_forge", "under_the_stones"], "active": ["home_again"]},
	"home again": {"restored": ["forge", "fern_cottage"], "flags": ["undercroft_open", "undercroft_plate",
		"undercroft_seal_open", "camp_cleared:undercroft_rooms", "camp_cleared:thornback", "shard_taken:woodland",
		"shard_home:woodland"], "done": ["road_to_crossroads", "cold_forge", "under_the_stones", "home_again"]},
	"mending": {"restored": ["forge", "fern_cottage"], "flags": ["undercroft_open", "undercroft_plate",
		"undercroft_seal_open", "camp_cleared:undercroft_rooms", "camp_cleared:thornback", "shard_taken:woodland",
		"shard_home:woodland"], "done": ["road_to_crossroads", "cold_forge", "under_the_stones", "home_again"],
		"active": ["a1_the_torn_roof"]},
}

func before_test() -> void:
	SaveGame.reset()

func after_test() -> void:
	SaveGame.reset()

func _apply(stage: Dictionary) -> void:
	SaveGame.reset()
	for r: String in stage.get("restored", []):
		SaveGame.data.village.restored[r] = 1
	for f: String in stage.get("flags", []):
		SaveGame.set_flag(f)
	for q: String in stage.get("done", []):
		SaveGame.data.quests[q] = {"state": "done", "step": Quests.defs[q].steps.size()}
	for q: String in stage.get("active", []):
		SaveGame.data.quests[q] = {"state": "active", "step": 0}

func _zone(id: String) -> Zone:
	var zone: Zone = (load(Zones.table[id]) as PackedScene).instantiate()
	add_child(zone)
	for i in 3:
		await get_tree().physics_frame
	return zone

func _enabled(n: Node) -> bool:
	return n.can_process() and (n as CanvasItem).is_visible_in_tree()

func _all(node: Node, out: Array) -> Array:
	out.append(node)
	for c in node.get_children():
		_all(c, out)
	return out

## How many reachable cells show the prompt of `area` (the player's body circle overlaps its shape),
## and the nearest a walker's feet get to its origin.
func _reach(area: Area2D, cells: Dictionary) -> Array:
	var count := 0
	var nearest := INF
	var shape := area.get_node("Shape") as CollisionShape2D
	var radius := (area as Interactable).reach() if area is Interactable else 0.0
	for c: Vector2i in cells:
		var feet := WalkGrid.point_of(c)
		nearest = minf(nearest, feet.distance_to(area.global_position))
		var body := feet + WalkGrid.BODY_OFFSET
		if area is Interactable:
			if body.distance_to(area.global_position) < radius + WalkGrid.BODY_RADIUS - 1.0:
				count += 1
		elif shape.shape is RectangleShape2D:
			var half := (shape.shape as RectangleShape2D).size / 2.0 + Vector2.ONE * (WalkGrid.BODY_RADIUS - 1.0)
			var d := (body - shape.global_position).abs()
			if d.x < half.x and d.y < half.y:
				count += 1
	return [count, nearest]

func test_every_talk_area_door_and_spawn_can_be_walked_to() -> void:
	var report := []
	var problems := []
	for stage: String in STAGES:
		for id: String in ZONES:
			_apply(STAGES[stage])
			var zone: Zone = await _zone(id)
			var grid := WalkGrid.new(zone.get_world_2d(), zone.bounds, 0.0)
			var cells := grid.reachable(zone.spawn_position("start"))
			for n: Node in _all(zone, []):
				if BEHIND_THE_SEAL.has(String(n.name)) and not SaveGame.has_flag("undercroft_seal_open"):
					continue
				var where := "%s, %s: %s" % [stage, id, n.name]
				if n is Marker2D and n.get_parent().name == "Spawns":
					if not cells.has(grid.nearest_free(n.global_position, 12.0)):
						problems.append("%s: the spawn is walled off from `start`" % where)
				elif n is Door and _enabled(n):
					if (n as Door).is_open() and _reach(n, cells)[0] == 0:
						problems.append("%s: the open door cannot be walked into" % where)
				elif n is Interactable and _enabled(n):
					var r := _reach(n, cells)
					report.append("%-11s %-10s %-14s cells in reach %4d, nearest feet %3d texels" % [stage, id, n.name, r[0], int(r[1])])
					if r[0] < MIN_CELLS:
						problems.append("%s: its prompt shows from %d reachable cells (at least %d wanted); the nearest a walker gets is %d texels" % [where, r[0], MIN_CELLS, int(r[1])])
			remove_child(zone)
			zone.free()
	print("\n".join(report))
	assert_array(problems).is_empty()

## Stands a player where the 10 Nov walker stood (a step short of each thing) and reads the focus the
## way the HUD does.
func _focus_at(zone: Zone, at: Vector2) -> String:
	var player: Player = preload("res://actors/player.tscn").instantiate()
	zone.actors.add_child(player)
	player.input_enabled = false
	player.global_position = at
	for i in 4:
		await get_tree().physics_frame
	var focus: Node = player.focus
	var found := String(focus.name) if focus != null else "none"
	zone.actors.remove_child(player)
	player.free()
	await get_tree().physics_frame
	return found

func test_the_prompt_shows_a_step_short_of_each_thing() -> void:
	# Crossroads with the Ferns' door still to clear: the notice board from (737, 709), Moss from 47 texels,
	# the Ferns' restore mark from 44
	_apply(STAGES["ferns asked"])
	var crossroads: Zone = await _zone("crossroads")
	assert_str(await _focus_at(crossroads, Vector2(737, 709))).is_equal("NoticeBoard")
	assert_str(await _focus_at(crossroads, Vector2(1152, 833))).is_equal("Moss")
	assert_str(await _focus_at(crossroads, Vector2(1440, 1352))).is_equal("FernSite")
	remove_child(crossroads)
	crossroads.free()
	# the Undercroft: Cairn's statue from 65 texels
	var undercroft: Zone = await _zone("undercroft")
	assert_str(await _focus_at(undercroft, Vector2(2160, 263))).is_equal("CairnStatue")
	remove_child(undercroft)
	undercroft.free()
	# the woodland: the sign and Hale from 47
	_apply(STAGES["fresh"])
	var woodland: Zone = await _zone("woodland")
	assert_str(await _focus_at(woodland, Vector2(372, 1151))).is_equal("StoneSign")
	assert_str(await _focus_at(woodland, Vector2(553, 1296))).is_equal("Hale")
	assert_str(await _focus_at(woodland, Vector2(405, 750))).is_equal("none")
	remove_child(woodland)
	woodland.free()

func test_no_talk_area_is_smaller_than_the_shared_reach() -> void:
	for id: String in ZONES:
		_apply(STAGES["home again"])
		var zone: Zone = await _zone(id)
		for n: Node in _all(zone, []):
			if n is Interactable:
				var it := n as Interactable
				var found: CollisionShape2D = null
				for c in it.get_children(true):
					if c is CollisionShape2D and c.name == "Reach":
						found = c
				assert_object(found).override_failure_message("%s has no shared reach" % it.name).is_not_null()
				assert_float((found.shape as CircleShape2D).radius).is_equal(Interactable.REACH)
				assert_float(it.reach()).override_failure_message("%s reaches %s" % [it.name, it.reach()]).is_greater_equal(Interactable.REACH)
				# the scene's own shape is left alone: the editor and the kit's seed pieces read it
				var own := (it.get_node("Shape") as CollisionShape2D).shape as CircleShape2D
				assert_float(own.radius).override_failure_message("%s: the scene's shape was changed" % it.name).is_less(Interactable.REACH)
		remove_child(zone)
		zone.free()
