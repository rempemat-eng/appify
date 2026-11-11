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
		# walk over both
		for p: GlintCachePickup in pickups:
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
