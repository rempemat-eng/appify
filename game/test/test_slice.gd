extends GdUnitTestSuite
## The vertical slice's village chain (docs/vision/vertical-slice.md): the quests advance in order, the
## restore step flips Crossroads' stage and the flip survives a save and a load, in data and in the scene.

const PATH := "user://test_slice_save.json"
const CHAIN := ["woodland_stones", "road_to_crossroads", "cold_forge", "under_the_stones", "home_again"]

func before_test() -> void:
	SaveGame.reset()

func after_test() -> void:
	DirAccess.remove_absolute(ProjectSettings.globalize_path(PATH))
	Zones.current = null
	Zones.root = null

func _step(q: String) -> String:
	return Quests.current_step(q).get("id", "")

func test_chain_advances_in_order() -> void:
	for q in CHAIN:
		assert_str(Quests.state(q)).is_equal("none")
	# the sign quest pays the Glint the forge needs
	Quests.notify("talk:stone_sign")
	Quests.notify("camp:meadow")
	Quests.notify("talk:stone_sign")
	assert_str(Quests.state("woodland_stones")).is_equal("done")
	# Hale in the woodland starts the road; talking to Moss before arriving does nothing
	Quests.notify("talk:hale")
	assert_str(_step("road_to_crossroads")).is_equal("go")
	Quests.notify("talk:moss")
	assert_str(_step("road_to_crossroads")).is_equal("go")
	Quests.notify("enter:crossroads")
	assert_str(_step("road_to_crossroads")).is_equal("moss")
	assert_str(Quests.state("cold_forge")).is_equal("none")
	Quests.notify("talk:moss")
	assert_str(Quests.state("road_to_crossroads")).is_equal("done")
	assert_int(SaveGame.data.glint).is_equal(50)
	# the forge
	assert_str(Village.stage("crossroads")).is_equal("broken")
	Quests.notify("talk:hale")
	assert_str(_step("cold_forge")).is_equal("restore")
	Quests.notify("talk:hale")  # talking again does not skip the repair
	assert_str(_step("cold_forge")).is_equal("restore")
	assert_bool(Village.restore("forge")).is_true()
	assert_int(SaveGame.data.glint).is_equal(20)
	assert_str(Village.stage("crossroads")).is_equal("forge")
	assert_str(_step("cold_forge")).is_equal("report")
	assert_str(Quests.state("under_the_stones")).is_equal("none")
	# reporting to Hale finishes the forge and starts the Undercroft in the same talk
	Quests.notify("talk:hale")
	assert_str(Quests.state("cold_forge")).is_equal("done")
	assert_bool(SaveGame.has_flag("undercroft_open")).is_true()
	assert_str(_step("under_the_stones")).is_equal("descend")
	# the Undercroft: rooms, then the Thornback, then the shard, then the lantern
	Quests.notify("camp:thornback")
	assert_str(_step("under_the_stones")).is_equal("descend")
	Quests.notify("enter:undercroft")
	assert_str(_step("under_the_stones")).is_equal("rooms")
	Quests.notify("talk:shard_lantern")
	assert_str(_step("under_the_stones")).is_equal("rooms")
	Quests.notify("camp:undercroft_rooms")
	Quests.notify("camp:thornback")
	assert_str(_step("under_the_stones")).is_equal("shard")
	Quests.notify("talk:circle_shard")
	assert_bool(SaveGame.has_flag("shard_taken:woodland")).is_true()
	assert_str(Quests.state("home_again")).is_equal("none")
	Quests.notify("talk:shard_lantern")
	assert_str(Quests.state("under_the_stones")).is_equal("done")
	assert_str(Village.stage("crossroads")).is_equal("homecoming")
	assert_int(SaveGame.data.glint).is_equal(80)
	# the homecoming: Moss starts it, the Ferns' door, then Ada
	Quests.notify("talk:ada_fern")
	assert_str(Quests.state("home_again")).is_equal("none")
	Quests.notify("talk:moss")
	assert_str(_step("home_again")).is_equal("clear")
	assert_bool(Village.restore("fern_cottage")).is_true()
	Quests.notify("talk:ada_fern")
	assert_str(Quests.state("home_again")).is_equal("done")
	assert_int(SaveGame.data.glint).is_equal(85)
	assert_bool(SaveGame.has_flag("seeds:valley")).is_true()

func test_entering_crossroads_first_still_counts() -> void:
	SaveGame.set_flag("visited:crossroads")
	Quests.notify("talk:hale")
	assert_str(_step("road_to_crossroads")).is_equal("moss")

func test_restore_needs_glint_and_its_condition() -> void:
	assert_bool(Village.can_restore("forge")).is_false()
	assert_bool(Village.restore("forge")).is_false()
	SaveGame.add_glint(29)
	assert_bool(Village.restore("forge")).is_false()
	SaveGame.add_glint(1)
	assert_bool(Village.restore("forge")).is_true()
	assert_int(SaveGame.data.glint).is_equal(0)
	assert_bool(Village.restore("forge")).is_false()  # once only
	SaveGame.add_glint(100)
	assert_bool(Village.can_restore("fern_cottage")).is_false()  # waits for the shard
	SaveGame.set_flag("shard_home:woodland")
	assert_bool(Village.can_restore("fern_cottage")).is_true()
	assert_bool(Village.can_restore("no_such_site")).is_false()

func test_restore_conditions() -> void:
	assert_bool(Quests.check({"restored": ["forge"]})).is_false()
	assert_bool(Quests.check({"not_restored": ["forge"]})).is_true()
	assert_bool(Quests.check({"glint_at_least": 1})).is_false()
	SaveGame.add_glint(30)
	assert_bool(Quests.check({"glint_at_least": 30})).is_true()
	Village.restore("forge")
	assert_bool(Quests.check({"restored": ["forge"], "not_restored": ["fern_cottage"]})).is_true()

func test_restore_persists_through_save_and_load() -> void:
	SaveGame.add_glint(30)
	Village.restore("forge")
	assert_int(SaveGame.save(PATH)).is_equal(OK)
	SaveGame.reset()
	assert_str(Village.stage("crossroads")).is_equal("broken")
	assert_int(SaveGame.load_save(PATH)).is_equal(OK)
	assert_bool(Village.is_restored("forge")).is_true()
	assert_int(typeof(SaveGame.data.village.restored.forge)).is_equal(TYPE_INT)
	assert_str(Village.stage("crossroads")).is_equal("forge")

func test_old_save_without_village_loads_broken() -> void:
	var f := FileAccess.open(PATH, FileAccess.WRITE)
	f.store_string(JSON.stringify({"version": 1, "glint": 3.0}))
	f.close()
	assert_int(SaveGame.load_save(PATH)).is_equal(OK)
	assert_str(Village.stage("crossroads")).is_equal("broken")

func _attach() -> Player:
	var root: Node2D = auto_free(Node2D.new())
	add_child(root)
	var player: Player = auto_free(load("res://actors/player.tscn").instantiate())
	player.input_enabled = false
	Zones.current = null
	Zones.attach(root, player)
	return player

func test_crossroads_scene_flips_and_keeps_the_flip() -> void:
	_attach()
	assert_bool(Zones.go_to("crossroads", "start")).is_true()
	var zone := Zones.current
	var rubble := zone.get_node("Props/If_smithy_rubble") as Conditional
	var fire := zone.get_node("Props/If_forge_fire") as Conditional
	var site := zone.get_node("Actors/If_smithy_site/SmithySite") as RestoreSite
	assert_bool(rubble.visible).is_true()
	assert_bool(fire.visible).is_false()
	assert_int(zone.get_node("RaidPads").get_child_count()).is_greater_equal(2)
	# not enough Glint: the site talks but nothing changes
	await site.interact()
	assert_bool(Village.is_restored("forge")).is_false()
	SaveGame.add_glint(30)
	await site.interact()
	assert_bool(Village.is_restored("forge")).is_true()
	assert_bool(rubble.visible).is_false()
	assert_int(rubble.process_mode).is_equal(Node.PROCESS_MODE_DISABLED)
	assert_bool(fire.visible).is_true()
	assert_bool((zone.get_node("Actors/If_hale_forge") as Conditional).visible).is_true()
	assert_bool((zone.get_node("Actors/If_hale_square") as Conditional).visible).is_false()
	# save, forget, load, and the zone comes back restored
	SaveGame.save(PATH)
	SaveGame.reset()
	SaveGame.load_save(PATH)
	assert_bool(Zones.go_to("crossroads", "start")).is_true()
	await get_tree().process_frame
	assert_bool((Zones.current.get_node("Props/If_smithy_rubble") as Conditional).visible).is_false()
	assert_bool((Zones.current.get_node("Props/If_forge_fire") as Conditional).visible).is_true()

func test_woodland_to_crossroads_and_back() -> void:
	var player := _attach()
	assert_bool(Zones.go_to("woodland", "start")).is_true()
	var woodland := Zones.current
	var to_town := woodland.get_node("Doors/ToCrossroads") as Door
	assert_str(to_town.target_zone).is_equal("crossroads")
	var hatch := woodland.get_node("Doors/ToUndercroft") as Door
	assert_bool(hatch.is_open()).is_false()
	assert_bool((woodland.get_node("Actors/HaleOnThePath") as Conditional).visible).is_true()
	assert_bool(Zones.go_to(to_town.target_zone, to_town.target_spawn)).is_true()
	assert_str(SaveGame.data.zone).is_equal("crossroads")
	assert_bool(SaveGame.has_flag("visited:crossroads")).is_true()
	assert_vector(player.global_position).is_equal(Zones.current.spawn_position("woodland"))
	var back := Zones.current.get_node("Doors/ToWoodland") as Door
	assert_bool(Zones.go_to(back.target_zone, back.target_spawn)).is_true()
	assert_vector(player.global_position).is_equal(Zones.current.spawn_position("crossroads"))
	SaveGame.set_flag("undercroft_open")
	assert_bool((Zones.current.get_node("Doors/ToUndercroft") as Door).is_open()).is_true()
	assert_bool(Zones.go_to("undercroft", "start")).is_true()
	assert_int(Zones.current.get_node("Actors/ThornbackCamp").get_child_count()).is_equal(1)
	var out := Zones.current.get_node("Doors/ToWoodland") as Door
	assert_bool(Zones.go_to(out.target_zone, out.target_spawn)).is_true()

func test_every_door_leads_somewhere_built() -> void:
	_attach()
	for zid in ["woodland", "crossroads", "undercroft"]:
		assert_bool(Zones.go_to(zid, "start")).is_true()
		for d in Zones.current.get_node("Doors").get_children():
			var door := d as Door
			if door.target_zone == "halt":
				continue  # Valley Halt waits for act 1
			assert_bool(Zones.has_zone(door.target_zone)).override_failure_message(door.name).is_true()
			var probe: Zone = load(Zones.table[door.target_zone]).instantiate()
			assert_bool(probe.has_node("Spawns/" + door.target_spawn)).override_failure_message(
				"%s -> %s:%s" % [door.name, door.target_zone, door.target_spawn]).is_true()
			probe.free()
