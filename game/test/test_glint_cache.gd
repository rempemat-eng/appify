extends GdUnitTestSuite
## Glint from fights and the downed player's cache (core/glint_cache.gd, Matt 10 Nov): 2 a mossling, 3 an
## Undercroft creature, 10 the Thornback, each paid once for the life of the save; going down leaves a
## fifth of the carried Glint where the player fell, kept until picked up, through a second defeat and
## through quit and load.

const SAVE := "user://test_glint_cache_save.json"

func before_test() -> void:
	SaveGame.reset()
	SaveGame.path = SAVE

func after_test() -> void:
	SaveGame.path = SaveGame.DEFAULT_PATH
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SAVE))
	Zones.current = null
	Zones.root = null
	SaveGame.reset()

func _ticks(n: int) -> void:
	for i in n:
		await get_tree().physics_frame

func _zone(id: String) -> Player:
	var root: Node2D = auto_free(Node2D.new())
	add_child(root)
	var player: Player = auto_free(load("res://actors/player.tscn").instantiate())
	player.input_enabled = false
	Zones.current = null
	Zones.attach(root, player)
	assert_bool(Zones.go_to(id, "start")).is_true()
	return player

func _free_one(camp: Node, name: String, player: Player) -> void:
	var e := camp.get_node(name) as Node2D
	player.global_position = e.global_position + Vector2(48, 0)
	e.call("take_hit", 99, Vector2.LEFT, 0.0)

func test_the_numbers_are_two_three_and_ten_and_a_fifth() -> void:
	assert_int(GlintCache.fight_glint("mossling")).is_equal(2)
	assert_int(GlintCache.fight_glint("creature")).is_equal(3)
	assert_int(GlintCache.fight_glint("boss")).is_equal(10)
	assert_int(GlintCache.amount_for(100, 0)).is_equal(20)
	assert_int(GlintCache.amount_for(26, 0)).is_equal(5)        # rounded down
	assert_int(GlintCache.amount_for(4, 0)).is_equal(0)
	assert_int(GlintCache.amount_for(100, 90)).is_equal(10)     # never below the floor
	assert_int(GlintCache.amount_for(50, 90)).is_equal(0)

## Today's build pays 31 Glint in all, counted from the zone scenes themselves.
func test_the_three_zones_hold_thirty_one_glint_of_fights() -> void:
	var total := 0
	var keys := {}
	for id: String in ["woodland", "crossroads", "undercroft"]:
		var zone: Node = (load(Zones.table[id]) as PackedScene).instantiate()
		for camp in zone.find_children("*", "Node2D", true, false):
			if camp is Camp:
				for c in camp.get_children():
					if c.has_signal("died"):
						total += GlintCache.fight_glint(Camp.kind_of(c))
						keys["%s/%s" % [(camp as Camp).camp_id, c.name]] = true
		zone.free()
	assert_int(total).is_equal(31)
	assert_int(keys.size()).is_equal(9)                         # nine creatures, nine different keys

## Nobody farms Glint: clear part of the camp, leave, come back to a whole camp, clear it: every creature
## has paid once.
func test_a_creature_pays_once_however_often_its_camp_comes_back() -> void:
	var player := _zone("woodland")
	await _ticks(2)
	var camp := Zones.current.get_node("Actors/MeadowCamp")
	_free_one(camp, "Mossling1", player)
	_free_one(camp, "Mossling2", player)
	assert_int(int(SaveGame.data.glint)).is_equal(4)
	assert_bool(SaveGame.has_flag("camp_cleared:meadow")).is_false()
	# a door and back, or getting up after a defeat: the zone loads again and the camp is whole
	assert_bool(Zones.go_to("woodland", "start")).is_true()
	await _ticks(2)
	camp = Zones.current.get_node("Actors/MeadowCamp")
	assert_int(camp.get_child_count()).is_equal(3)
	for name: String in ["Mossling1", "Mossling2", "Mossling3"]:
		_free_one(camp, name, player)
	assert_int(int(SaveGame.data.glint)).is_equal(6)            # 2 more for the third, nothing for the first two again
	assert_bool(SaveGame.has_flag("camp_cleared:meadow")).is_true()
	# and through quit and load
	assert_int(SaveGame.save()).is_equal(OK)
	SaveGame.reset()
	assert_int(SaveGame.load_save()).is_equal(OK)
	assert_int(GlintCache.pay_once("meadow/Mossling3", "mossling")).is_equal(0)
	assert_int(int(SaveGame.data.glint)).is_equal(6)

func test_the_undercroft_pays_three_a_creature_and_ten_for_the_thornback() -> void:
	SaveGame.set_flag("undercroft_seal_open")
	var player := _zone("undercroft")
	await _ticks(2)
	var rooms := Zones.current.get_node("Actors/UndercroftRoomsCamp")
	for name: String in ["Rusher1", "Shooter2", "Shield3", "Rusher4", "Elite5"]:
		_free_one(rooms, name, player)
	assert_int(int(SaveGame.data.glint)).is_equal(15)
	_free_one(Zones.current.get_node("Actors/ThornbackCamp"), "Thornback", player)
	assert_int(int(SaveGame.data.glint)).is_equal(25)

func test_going_down_leaves_a_fifth_where_the_player_fell_and_a_second_defeat_keeps_the_first() -> void:
	SaveGame.data.glint = 50
	assert_int(GlintCache.drop("undercroft", Vector2(300.4, 400.6))).is_equal(10)
	assert_int(int(SaveGame.data.glint)).is_equal(40)
	assert_array(SaveGame.data.caches).is_equal([{"zone": "undercroft", "x": 300, "y": 401, "glint": 10}])
	assert_int(GlintCache.drop("woodland", Vector2(700, 1500))).is_equal(8)
	assert_int(int(SaveGame.data.glint)).is_equal(32)
	assert_int((SaveGame.data.caches as Array).size()).is_equal(2)
	assert_int(int(SaveGame.data.caches[0].glint)).is_equal(10)   # the first is untouched
	assert_int(GlintCache.in_zone("undercroft").size()).is_equal(1)
	# nothing is ever lost: purse and caches together are what was carried
	assert_int(int(SaveGame.data.glint) + 10 + 8).is_equal(50)
	# a purse too small to share leaves no cache
	SaveGame.data.glint = 4
	assert_int(GlintCache.drop("woodland", Vector2.ZERO)).is_equal(0)
	assert_int((SaveGame.data.caches as Array).size()).is_equal(2)
	assert_int(GlintCache.collect(SaveGame.data.caches[0])).is_equal(10)
	assert_int(int(SaveGame.data.glint)).is_equal(14)
	assert_int((SaveGame.data.caches as Array).size()).is_equal(1)

func test_caches_and_payments_survive_quit_and_load_and_a_save_from_main_loads() -> void:
	SaveGame.data.glint = 50
	GlintCache.drop("undercroft", Vector2(300, 400))
	GlintCache.pay_once("meadow/Mossling1", "mossling")
	assert_int(SaveGame.save()).is_equal(OK)
	SaveGame.reset()
	assert_int(SaveGame.load_save()).is_equal(OK)
	assert_int(int(SaveGame.data.glint)).is_equal(42)
	assert_array(SaveGame.data.caches).is_equal([{"zone": "undercroft", "x": 300, "y": 400, "glint": 10}])
	assert_bool(SaveGame.data.paid.has("meadow/Mossling1")).is_true()
	assert_int(typeof(SaveGame.data.caches[0].glint)).is_equal(TYPE_INT)
	# a save written before these fields existed (main at 5098b37d): it loads, with nothing paid and no cache
	var old := SaveGame.fresh()
	old.erase("paid")
	old.erase("caches")
	old.glint = 26
	var f := FileAccess.open(SAVE, FileAccess.WRITE)
	f.store_string(JSON.stringify(old))
	f.close()
	assert_int(SaveGame.load_save()).is_equal(OK)
	assert_int(int(SaveGame.data.glint)).is_equal(26)
	assert_dict(SaveGame.data.paid).is_empty()
	assert_array(SaveGame.data.caches).is_empty()
	assert_int(int(SaveGame.data.version)).is_equal(SaveGame.VERSION)
	# a damaged cache list is refused, not half read
	old["caches"] = [{"zone": "woodland", "x": "here", "y": 2, "glint": 5}]
	f = FileAccess.open(SAVE, FileAccess.WRITE)
	f.store_string(JSON.stringify(old))
	f.close()
	assert_int(SaveGame.load_save()).is_equal(ERR_INVALID_DATA)

## The whole of it in the game scene: down in the Undercroft with 26 Glint, up at the stair with 21, the
## cache lying where the player fell after the zone loads again, picked up by walking over it.
func test_in_the_game_a_downed_player_finds_the_cache_where_they_fell() -> void:
	for reduced: bool in [true, false]:
		SaveGame.reset()
		SaveGame.data.settings.reduced_motion = reduced
		SaveGame.data.zone = "undercroft"
		SaveGame.data.glint = 26
		var g: Node2D = load("res://game.tscn").instantiate()
		add_child(g)
		await _ticks(3)
		var player: Player = g.player
		var fell := Vector2(150, 380)
		player.global_position = fell
		player.downed.emit()                                  # what the fall's last drawing sends
		await _ticks(4)
		assert_int(int(SaveGame.data.glint)).is_equal(21)
		assert_int(player.hp).is_equal(player.max_hp)
		assert_vector(player.global_position).is_equal(Zones.current.spawn_position("start"))
		var pickups := Zones.current.actors.get_children().filter(func(n: Node) -> bool: return n is GlintCachePickup)
		assert_int(pickups.size()).is_equal(1)
		var pickup := pickups[0] as GlintCachePickup
		assert_vector(pickup.global_position).is_equal(fell)
		# the autosave after getting up holds it
		var saved: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(SAVE))
		assert_int(int(saved.glint)).is_equal(21)
		assert_int(int(saved.caches[0].glint)).is_equal(5)
		# a second defeat elsewhere: a second cache, the first still there
		player.global_position = Vector2(200, 420)
		player.downed.emit()
		await _ticks(4)
		assert_int(int(SaveGame.data.glint)).is_equal(17)
		pickups = Zones.current.actors.get_children().filter(func(n: Node) -> bool: return n is GlintCachePickup)
		assert_int(pickups.size()).is_equal(2)
		# the physics server may still hold the body where it fell for a step after the zone loaded: a body
		# that is not really here takes nothing (played: every cache was taken back as the player got up)
		(pickups[0] as GlintCachePickup).body_entered.emit(player)
		assert_int(int(SaveGame.data.glint)).is_equal(17)
		# walk over both
		for p: GlintCachePickup in pickups:
			player.global_position = p.global_position + Vector2(6, 0)
			p.body_entered.emit(player)
		assert_int(int(SaveGame.data.glint)).is_equal(26)
		assert_array(SaveGame.data.caches).is_empty()
		saved = JSON.parse_string(FileAccess.get_file_as_string(SAVE))
		assert_int(int(saved.glint)).is_equal(26)
		await _ticks(2)
		var left := pickups.filter(func(p: Variant) -> bool: return is_instance_valid(p) and not (p as Node).is_queued_for_deletion())
		if reduced:
			assert_int(left.size()).is_equal(0)                 # gone at once under reduced motion
		else:
			assert_int(left.size()).is_equal(2)                 # rising and fading ...
			await _ticks(int(GlintCachePickup.RISE * 60.0) + 6)
			await get_tree().process_frame
			left = pickups.filter(func(p: Variant) -> bool: return is_instance_valid(p) and not (p as Node).is_queued_for_deletion())
			assert_int(left.size()).is_equal(0)                 # ... and finite
		g.free()
		Zones.current = null
		Zones.root = null
		await _ticks(1)

func test_the_hud_count_flashes_on_a_change_and_only_changes_under_reduced_motion() -> void:
	var hud: Control = auto_free(load("res://ui/hud.gd").new())
	add_child(hud)
	hud._glint_changed(10, 12)
	assert_bool(hud._glint.modulate == Color.WHITE).is_false()
	await get_tree().create_timer(hud.GLINT_FLASH + 0.2).timeout
	assert_bool(hud._glint.modulate == Color.WHITE).is_true()    # finite
	SaveGame.data.settings.reduced_motion = true
	hud._glint_changed(12, 10)
	assert_bool(hud._glint.modulate == Color.WHITE).is_true()

# --- one camp for each room of the Undercroft (15 Nov) -----------------------------------------
func _rooms_camp() -> Camp:
	return Zones.current.get_node("Actors/UndercroftRoomsCamp") as Camp

func _creatures(camp: Node) -> Array:
	var out := []
	for c in camp.get_children():
		if c.has_signal("died") and not c.is_queued_for_deletion():
			out.append(String(c.name))
	out.sort()
	return out

## The mechanics review, 14 Nov: the five creatures were one camp, so going down in room 3 brought
## rooms 1 and 2 back. Each room is a camp of its own now: cleared, it stays cleared through getting up
## (the zone loads again), a door and back, and quit and load. Roles, numbers and Glint are as they were.
func test_a_cleared_room_of_the_undercroft_stays_cleared_when_the_zone_loads_again() -> void:
	var player := _zone("undercroft")
	await _ticks(2)
	assert_array(_creatures(_rooms_camp())).is_equal(["Elite5", "Rusher1", "Rusher4", "Shield3", "Shooter2"])
	# one of the stair hall's two freed, then down: the hall is not cleared, so it is whole again
	_free_one(_rooms_camp(), "Rusher1", player)
	assert_int(int(SaveGame.data.glint)).is_equal(3)
	assert_bool(SaveGame.has_flag("camp_cleared:undercroft_stair_hall")).is_false()
	assert_bool(Zones.go_to("undercroft", "start")).is_true()        # as game.gd does on getting up
	await _ticks(2)
	assert_int(_creatures(_rooms_camp()).size()).is_equal(5)
	# the stair hall cleared, and the corridor's shield bearer freed; then down in the corridor
	for name: String in ["Rusher1", "Shooter2", "Shield3"]:
		_free_one(_rooms_camp(), name, player)
	assert_int(int(SaveGame.data.glint)).is_equal(9)               # Rusher1 paid once: 3 + 3 + 3
	assert_bool(SaveGame.has_flag("camp_cleared:undercroft_stair_hall")).is_true()
	assert_bool(_rooms_camp().room_cleared("undercroft_stair_hall")).is_true()
	assert_bool(SaveGame.has_flag("camp_cleared:undercroft_root_corridor")).is_false()
	assert_bool(SaveGame.has_flag("camp_cleared:undercroft_rooms")).is_false()
	assert_bool(Zones.go_to("undercroft", "start")).is_true()
	await _ticks(2)
	assert_array(_creatures(_rooms_camp())).is_equal(["Elite5", "Rusher4", "Shield3"])
	# through quit and load too
	assert_int(SaveGame.save()).is_equal(OK)
	SaveGame.reset()
	assert_int(SaveGame.load_save()).is_equal(OK)
	assert_bool(Zones.go_to("undercroft", "start")).is_true()
	await _ticks(2)
	assert_array(_creatures(_rooms_camp())).is_equal(["Elite5", "Rusher4", "Shield3"])
	# the rest: the quest's event and the whole camp's flag come with the last room, and nobody pays twice
	Quests.start_quest("under_the_stones")
	Quests.notify("enter:undercroft")
	assert_str(String(Quests.current_step("under_the_stones").id)).is_equal("rooms")
	for name: String in ["Shield3", "Rusher4"]:
		_free_one(_rooms_camp(), name, player)
	assert_bool(SaveGame.has_flag("camp_cleared:undercroft_root_corridor")).is_true()
	assert_bool(SaveGame.has_flag("camp_cleared:undercroft_rooms")).is_false()
	assert_str(String(Quests.current_step("under_the_stones").id)).is_equal("rooms")
	_free_one(_rooms_camp(), "Elite5", player)
	assert_bool(SaveGame.has_flag("camp_cleared:undercroft_seal_room")).is_true()
	assert_bool(SaveGame.has_flag("camp_cleared:undercroft_rooms")).is_true()
	assert_bool(_rooms_camp().is_cleared()).is_true()
	assert_str(String(Quests.current_step("under_the_stones").id)).is_equal("thornback")
	assert_int(int(SaveGame.data.glint)).is_equal(15)              # five creatures, 3 each, each once
	assert_int((SaveGame.data.paid as Dictionary).size()).is_equal(5)
	for name: String in ["Rusher1", "Shooter2", "Shield3", "Rusher4", "Elite5"]:
		assert_bool((SaveGame.data.paid as Dictionary).has("undercroft_rooms/" + name)).is_true()

## A save from main knows nothing of room camps. One with the rooms cleared has only the whole camp's
## flag: every room is empty. One made in the middle of the rooms has creatures paid and no flag: the
## camp is whole, as it was on main, and the creatures already paid pay nothing again.
func test_saves_from_before_the_room_camps_load_as_they_were() -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://tools/routes/first_night.save.json"))
	assert_bool(bool(fixture.flags.get("camp_cleared:undercroft_rooms", false))).is_true()
	for room: Dictionary in Camp.rooms_of("undercroft_rooms"):
		assert_bool(fixture.flags.has("camp_cleared:" + String(room.id))).is_false()
	SaveGame.set_flag("camp_cleared:undercroft_rooms")
	_zone("undercroft")
	await _ticks(2)
	assert_array(_creatures(_rooms_camp())).is_empty()
	for room: Dictionary in Camp.rooms_of("undercroft_rooms"):
		assert_bool(_rooms_camp().room_cleared(String(room.id))).is_true()
	# a save from the middle of the rooms on main: two paid, nothing cleared
	SaveGame.reset()
	SaveGame.data.paid = {"undercroft_rooms/Rusher1": true, "undercroft_rooms/Shooter2": true}
	SaveGame.data.glint = 6
	var player := _zone("undercroft")
	await _ticks(2)
	assert_int(_creatures(_rooms_camp()).size()).is_equal(5)
	for name: String in ["Rusher1", "Shooter2"]:
		_free_one(_rooms_camp(), name, player)
	assert_int(int(SaveGame.data.glint)).is_equal(6)
	assert_bool(SaveGame.has_flag("camp_cleared:undercroft_stair_hall")).is_true()

## data/camps.json against the scene and the plan: every creature of the camp is in exactly one room
## camp, and stands inside that room of the plan.
func test_every_undercroft_creature_is_in_the_camp_of_the_room_it_stands_in() -> void:
	_zone("undercroft")
	await _ticks(2)
	var plan: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/plans/undercroft.json"))
	var rects := {}
	for room: Dictionary in plan.rooms:
		rects[room.id] = Rect2(room.rect[0], room.rect[1], room.rect[2], room.rect[3])
	var named := []
	var rooms := Camp.rooms_of("undercroft_rooms")
	assert_int(rooms.size()).is_equal(3)
	for room: Dictionary in rooms:
		assert_bool(rects.has(room.room)).is_true()
		assert_str(String(room.id)).is_not_equal("undercroft_rooms")
		for creature: String in room.creatures:
			named.append(creature)
			var node := _rooms_camp().get_node_or_null(creature) as Node2D
			assert_object(node).override_failure_message("no creature %s in the rooms' camp" % creature).is_not_null()
			var at := node.global_position / 3.0          # texels to the plan's world px
			assert_bool((rects[room.room] as Rect2).has_point(at)).override_failure_message(
				"%s stands at %s, outside %s %s" % [creature, at, room.room, rects[room.room]]).is_true()
	named.sort()
	assert_array(named).is_equal(_creatures(_rooms_camp()))
	assert_array(Camp.rooms_of("meadow")).is_empty()
	assert_array(Camp.rooms_of("thornback")).is_empty()
