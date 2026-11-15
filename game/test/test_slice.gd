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

## The flag that moves Hale from the woodland to Crossroads (10 Nov: she stood in the woodland and on the
## square at once for a player who went to Crossroads first). `hale_walked_home` is set only by the next
## zone load after she has asked, never by the talk itself, so no moment has her in both zones. What
## the player sees on the path after the talk (she walks off and is gone) is held further down.
func test_hale_walked_home_is_set_only_by_the_next_zone_load_after_she_has_asked() -> void:
	var on_the_path := {"not_flags": ["hale_walked_home"]}
	assert_bool(Quests.check(on_the_path)).is_true()
	Quests.zone_loading()                      # a door before she has asked: she has not moved
	assert_bool(Quests.check(on_the_path)).is_true()
	assert_bool(SaveGame.has_flag("hale_walked_home")).is_false()
	Quests.notify("talk:hale")
	assert_bool(Quests.check(on_the_path)).is_true()
	assert_bool(SaveGame.has_flag("hale_walked_home")).is_false()
	Quests.zone_loading()
	assert_bool(Quests.check(on_the_path)).is_false()
	assert_bool(SaveGame.has_flag("hale_walked_home")).is_true()

func test_hale_is_in_one_place_in_the_scenes() -> void:
	_attach()
	# Crossroads before she has asked: not on the square, not at the anvil (even with the forge paid)
	SaveGame.add_glint(30)
	assert_bool(Zones.go_to("crossroads", "start")).is_true()
	assert_bool(Village.restore("forge")).is_true()
	assert_bool((Zones.current.get_node("Actors/If_hale_square") as Conditional).visible).is_false()
	assert_bool((Zones.current.get_node("Actors/If_hale_forge") as Conditional).visible).is_false()
	assert_bool(Zones.go_to("woodland", "crossroads")).is_true()
	var on_the_path := Zones.current.get_node("Actors/HaleOnThePath") as Conditional
	var hale := on_the_path.get_node("Hale") as Interactable
	assert_bool(on_the_path.visible).is_true()
	assert_bool(hale.usable()).is_true()
	Quests.notify("talk:hale")
	assert_str(_step("road_to_crossroads")).is_equal("moss")     # already visited: the first step is done
	assert_bool(on_the_path.visible).is_true()                    # the flag has not moved her to Crossroads yet
	assert_bool(SaveGame.has_flag("hale_walked_home")).is_false()
	# on the path itself there is nothing to talk to from this moment, and she is gone when her walk ends
	assert_bool(hale.usable()).is_false()
	await get_tree().create_timer(WalkOff.LEAVE + 0.4).timeout
	assert_bool(hale.is_visible_in_tree()).is_false()
	assert_bool(hale.usable()).is_false()
	assert_bool(SaveGame.has_flag("hale_walked_home")).is_false()
	assert_bool(Zones.go_to("crossroads", "woodland")).is_true()
	assert_bool((Zones.current.get_node("Actors/If_hale_forge") as Conditional).visible).is_true()
	assert_bool(Zones.go_to("woodland", "crossroads")).is_true()
	assert_bool((Zones.current.get_node("Actors/HaleOnThePath") as Conditional).visible).is_false()

## The forge paid before Hale asks (recorded: it can be), in both orders: before she is home, and with
## her standing on the square watching. The mark's line and her thanks must be true in each (11 Nov:
## she said "before I was even home" and spoke of an ember when she had watched her fire take).
func test_an_early_forge_is_told_truthfully_whether_hale_was_home_or_not() -> void:
	for was_home: bool in [false, true]:
		SaveGame.reset()
		SaveGame.add_glint(30)
		SaveGame.set_flag("hale_walked_home", was_home)
		var mark := " ".join(Dialogue.lines_for("restore_forge"))
		assert_bool(mark.contains("ember")).is_equal(not was_home)
		assert_bool(mark.contains("Hale's fire takes")).is_equal(was_home)
		Village.restore("forge")
		SaveGame.data.quests["road_to_crossroads"] = {"state": "done", "step": 2}
		SaveGame.set_flag("hale_walked_home")      # by now she is in Crossroads either way
		var thanks := " ".join(Dialogue.lines_for("hale"))
		assert_str(thanks).contains("cleared my door")
		for claim: String in ["home", "ember"]:    # each would be false in one of the two orders
			assert_bool(thanks.contains(claim)).override_failure_message(
				"Hale says \"%s\" (was home: %s): %s" % [claim, was_home, thanks]).is_false()

## --stage (and review:scene --stage) shows the town as it stands at that stage: from the forge on,
## Hale is home (11 Nov: the stages set no hale_walked_home, so every stage picture had lost her).
func test_every_stage_after_the_first_shows_hale_in_crossroads() -> void:
	var plan: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/plans/crossroads.json"))
	_attach()
	for i in plan.stages.size():
		SaveGame.reset()
		load("res://game.gd").apply_stage("crossroads", plan.stages[i].id)
		assert_str(Village.stage("crossroads")).is_equal(plan.stages[i].id)
		assert_bool(Zones.go_to("crossroads", "start")).is_true()
		var shown := 0
		for n: String in ["Actors/If_hale_square", "Actors/If_hale_forge"]:
			shown += int((Zones.current.get_node(n) as Conditional).visible)
		assert_int(shown).override_failure_message("stage %s shows Hale %d times" % [plan.stages[i].id, shown]).is_equal(int(i > 0))

## The apothecary's mark waits for Morel to ask (its 40 Glint, paid early, could leave the forge or the
## Ferns' door out of reach); the forge and the Ferns' door can be paid before their quests, as recorded.
func test_the_apothecary_mark_waits_for_its_quest() -> void:
	SaveGame.add_glint(100)
	assert_bool(Village.can_restore("forge")).is_true()
	assert_bool(Village.can_restore("apothecary")).is_false()
	for q: String in CHAIN:
		SaveGame.data.quests[q] = {"state": "done", "step": Quests.defs[q].steps.size()}
	assert_bool(Village.can_restore("apothecary")).is_false()
	_attach()
	assert_bool(Zones.go_to("crossroads", "start")).is_true()
	var mark := Zones.current.get_node("Actors/If_apothecary_site/ApothecarySite") as RestoreSite
	assert_bool(mark.usable()).is_false()
	await mark.interact()
	assert_bool(Village.is_restored("apothecary")).is_false()
	Quests.notify("talk:morel")
	assert_bool(mark.usable()).is_true()
	await mark.interact()
	assert_bool(Village.is_restored("apothecary")).is_true()
	assert_int(SaveGame.data.glint).is_equal(60)

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
	SaveGame.set_flag("hale_walked_home")      # Hale has walked home (The road home)
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

## One scene-consumer run of the reachable slice. It uses the authored interactables, doors,
## Camp damage/death path and restore sites, without granting flags, Glint or quest records.
## The pilot supplies lethal hits and area-entry signals; this is not movement/combat balance,
## UI, visual or phone acceptance. The absent shard routes still gate the full circle waking.
func test_reachable_slice_through_home_again_uses_scene_consumers() -> void:
	assert_bool(Dialogue.opened.get_connections().is_empty()).is_true()
	var player := _attach()
	assert_bool(Zones.go_to("woodland", "start")).is_true()
	for q in CHAIN:
		assert_str(Quests.state(q)).is_equal("none")
	assert_int(SaveGame.data.glint).is_equal(0)
	assert_bool((Zones.current.get_node("Doors/ToUndercroft") as Door).is_open()).is_false()

	await _slice_talk("Actors/StoneSign")
	assert_str(_step("woodland_stones")).is_equal("clear_camp")
	await _slice_free_camp("Actors/MeadowCamp", 3)
	await _slice_talk("Actors/StoneSign")
	assert_str(Quests.state("woodland_stones")).is_equal("done")
	assert_int(SaveGame.data.glint).is_equal(46)      # the sign's 40 and 2 for each of the three mosslings
	await _slice_talk("Actors/HaleOnThePath/Hale")
	assert_str(_step("road_to_crossroads")).is_equal("go")
	await _slice_door("Doors/ToCrossroads", player, "crossroads")

	await _slice_talk("Actors/Moss")
	assert_str(Quests.state("road_to_crossroads")).is_equal("done")
	assert_int(SaveGame.data.glint).is_equal(56)
	await _slice_talk("Actors/If_hale_square/HaleSquare")
	assert_str(_step("cold_forge")).is_equal("restore")
	await _slice_talk("Actors/If_smithy_site/SmithySite")
	assert_bool(Village.is_restored("forge")).is_true()
	assert_int(SaveGame.data.glint).is_equal(26)
	await _slice_talk("Actors/If_hale_forge/HaleForge")
	assert_str(Quests.state("cold_forge")).is_equal("done")
	assert_str(_step("under_the_stones")).is_equal("descend")
	await _slice_door("Doors/ToWoodland", player, "woodland")
	await _slice_door("Doors/ToUndercroft", player, "undercroft")
	assert_str(_step("under_the_stones")).is_equal("rooms")

	# The real plate and lever consumers open the existing seal; the pilot does not write flags.
	var lever := Zones.current.get_node("Actors/SealLever") as SealLever
	await _slice_talk("Actors/SealLever")
	assert_bool(SaveGame.has_flag("undercroft_seal_open")).is_false()
	var plate := Zones.current.get_node("Actors/SealPlate") as PressurePlate
	plate.body_entered.emit(player)
	assert_bool(plate.is_pressed()).is_true()
	await _slice_talk("Actors/SealLever")
	assert_bool(SaveGame.has_flag(lever.flag)).is_true()
	await _slice_free_camp("Actors/UndercroftRoomsCamp", 5)
	assert_str(_step("under_the_stones")).is_equal("thornback")
	await _slice_free_camp("Actors/ThornbackCamp", 1)
	assert_str(_step("under_the_stones")).is_equal("shard")
	assert_bool((Zones.current.get_node("Actors/If_circle_shard") as Conditional).visible).is_true()
	await _slice_talk("Actors/If_circle_shard/CircleShard")
	assert_bool(SaveGame.has_flag("shard_taken:woodland")).is_true()
	assert_str(Dialogue.lines_for("cairn_statue")[0]).contains("glow")
	await _slice_talk("Actors/CairnStatue")
	assert_bool(SaveGame.has_flag("folk:cairn")).is_false()
	await _slice_door("Doors/ToWoodland", player, "woodland")
	await _slice_door("Doors/ToCrossroads", player, "crossroads")

	await _slice_talk("Actors/ShardLantern")
	assert_str(Quests.state("under_the_stones")).is_equal("done")
	assert_bool(SaveGame.has_flag("shard_home:woodland")).is_true()
	assert_str(Village.stage("crossroads")).is_equal("homecoming")
	await _slice_talk("Actors/Moss")
	assert_str(_step("home_again")).is_equal("clear")
	await _slice_talk("Actors/If_fern_site/FernSite")
	assert_bool(Village.is_restored("fern_cottage")).is_true()
	await _slice_talk("Actors/If_ada/Ada")
	for q in CHAIN:
		assert_str(Quests.state(q)).is_equal("done")
	assert_int(SaveGame.data.glint).is_equal(116)     # 85 from the quests and restores, 31 from the nine creatures
	assert_bool(SaveGame.has_flag("seeds:valley")).is_true()
	assert_bool(SaveGame.has_flag("shard_home:frostline")).is_false()
	assert_bool(SaveGame.has_flag("shard_home:brackens")).is_false()
	assert_str(Quests.state("a1_the_circle_wakes")).is_equal("none")
	assert_bool(SaveGame.has_flag("circle_awake")).is_false()

func _slice_talk(path: String) -> void:
	var target := Zones.current.get_node(path) as Interactable
	assert_bool(target.is_visible_in_tree()).is_true()
	assert_bool(Dialogue.busy).is_false()
	target.interact()
	await get_tree().process_frame
	assert_bool(Dialogue.busy).is_false()

func _slice_door(path: String, player: Player, destination: String) -> void:
	var door := Zones.current.get_node(path) as Door
	assert_bool(door.is_open()).is_true()
	assert_str(door.target_zone).is_equal(destination)
	await get_tree().create_timer(0.41).timeout
	door.body_entered.emit(player)
	await get_tree().process_frame
	await get_tree().process_frame
	assert_str(SaveGame.data.zone).is_equal(destination)
	assert_str(Zones.current.zone_id).is_equal(destination)

func _slice_free_camp(path: String, expected_enemies: int) -> void:
	var camp := Zones.current.get_node(path) as Camp
	var enemies: Array[Node] = []
	for child in camp.get_children():
		if child.has_method("take_hit") and child.has_signal("died"):
			enemies.append(child)
	assert_int(enemies.size()).is_equal(expected_enemies)
	assert_bool(camp.is_cleared()).is_false()
	for enemy in enemies:
		# The hit comes from beside the creature: an enemy cannot be hurt by someone it cannot come for
		# (out of range, or outside the Thornback's arena), so the player stands where a fight would be.
		if Zones.player != null:
			Zones.player.global_position = (enemy as Node2D).global_position + Vector2(48, 0)
		# Twice current strength covers the existing shield reduction; no quest/flag shortcut.
		enemy.call("take_hit", int(enemy.get("hp")) * 2, Vector2.RIGHT, 0.0)
	await get_tree().create_timer(0.3).timeout
	assert_bool(camp.is_cleared()).is_true()

# --- Hale goes ahead (15 Nov) ------------------------------------------------------------------
const WalkGrid := preload("res://tools/walk_grid.gd")

func _hale_on_the_path() -> Interactable:
	return Zones.current.get_node("Actors/HaleOnThePath/Hale") as Interactable

## She said "I'll be right behind you" and then stood by her tree. Now her words say she goes ahead, and
## she does: when the talk closes she walks off east along the path and is gone, there is nothing left to
## talk to, and she is at her post in Crossroads when the player arrives.
func test_hale_walks_off_ahead_when_her_talk_closes_and_is_in_crossroads_on_arrival() -> void:
	var player := _attach()
	assert_bool(Zones.go_to("woodland", "start")).is_true()
	await get_tree().physics_frame
	var hale := _hale_on_the_path()
	var from := hale.global_position
	assert_bool(hale.usable()).is_true()
	assert_str(" ".join(Dialogue.lines_for("hale"))).contains("I'll go on ahead")
	await _slice_talk("Actors/HaleOnThePath/Hale")
	assert_str(_step("road_to_crossroads")).is_equal("go")
	# at once: nothing to talk to, no "!" and no post in the way
	assert_bool(hale.leaving).is_true()
	assert_bool(hale.usable()).is_false()
	assert_int((hale.get_node("Post") as StaticBody2D).collision_layer).is_equal(0)
	player.global_position = from + Vector2(-40, 0)
	Interactable.refocus(player)
	assert_object(player.focus).is_null()
	assert_bool(hale.is_visible_in_tree()).is_true()          # she does not vanish as her line closes
	await get_tree().create_timer(0.5).timeout
	assert_bool(hale.is_visible_in_tree()).is_true()
	assert_float(hale.global_position.x).is_greater(from.x + 20.0)       # east, toward the door
	assert_str((hale.get_node("Body") as Villager).clip).is_equal("walk")
	assert_str((hale.get_node("Body") as Villager).facing).is_equal("E")
	await get_tree().create_timer(WalkOff.LEAVE).timeout
	assert_bool(hale.is_visible_in_tree()).is_false()         # gone, after a finite walk
	assert_object(hale.get_node_or_null("WalkOff")).is_null()
	var went := hale.global_position.distance_to(from)
	var speed := (hale.get_node("Body") as Villager).walk_speed()
	assert_float(went).is_between(WalkOff.reach(speed) * 0.8, WalkOff.reach(speed) * 1.1)
	# nothing new is saved, and the flag that places her is still the quest's own, set by the next zone load
	assert_bool(SaveGame.has_flag("hale_walked_home")).is_false()
	await _slice_door("Doors/ToCrossroads", player, "crossroads")
	assert_bool(SaveGame.has_flag("hale_walked_home")).is_true()
	assert_bool((Zones.current.get_node("Actors/If_hale_square") as Conditional).visible).is_true()
	assert_str(" ".join(Dialogue.lines_for("hale"))).contains("Talk to Moss at the stall first")
	assert_str(" ".join(Dialogue.lines_for("moss"))).contains("come in ahead of you")
	# and back in the woodland she is not on the path
	await _slice_door("Doors/ToWoodland", player, "woodland")
	assert_bool(_hale_on_the_path().is_visible_in_tree()).is_false()

## The stretch she walks is free of solids for a whole body (the player's, with her own post gone).
func test_the_stretch_hale_walks_is_clear_of_solids() -> void:
	_attach()
	assert_bool(Zones.go_to("woodland", "start")).is_true()
	var hale := _hale_on_the_path()
	var off: Dictionary = Quests.defs["road_to_crossroads"].walks_off
	assert_str(String(off.speaker)).is_equal(hale.speaker_id)
	assert_str(String(off.zone)).is_equal("woodland")
	var toward := Vector2(float(off.toward[0]), float(off.toward[1]))
	assert_vector(toward).is_equal((Zones.current.get_node("Doors/ToCrossroads") as Node2D).global_position)
	(hale.get_node("Post") as StaticBody2D).collision_layer = 0
	await get_tree().physics_frame
	await get_tree().physics_frame
	var from := hale.global_position
	var speed := (hale.get_node("Body") as Villager).walk_speed()
	assert_float(speed).is_greater(30.0)
	var to := from + (toward - from).normalized() * WalkOff.reach(speed)
	assert_float(from.distance_to(to)).is_less(from.distance_to(toward))      # she is gone before the door
	var grid := WalkGrid.new(get_viewport().get_world_2d(), Zones.current.bounds)
	assert_bool(grid.clear_line(from, to)).override_failure_message("something solid stands between %s and %s" % [from, to]).is_true()

func test_under_reduced_motion_hale_fades_where_she_stands_and_does_not_move() -> void:
	SaveGame.data.settings["reduced_motion"] = true
	_attach()
	assert_bool(Zones.go_to("woodland", "start")).is_true()
	var hale := _hale_on_the_path()
	var from := hale.global_position
	await _slice_talk("Actors/HaleOnThePath/Hale")
	assert_bool(hale.usable()).is_false()
	assert_bool(hale.is_visible_in_tree()).is_true()          # no pop as the line closes
	await get_tree().create_timer(WalkOff.STILL_FADE * 0.5).timeout
	assert_bool(hale.is_visible_in_tree()).is_true()
	assert_float(hale.modulate.a).is_between(0.2, 0.8)
	assert_vector(hale.global_position).is_equal(from)
	assert_str((hale.get_node("Body") as Villager).clip).is_not_equal("walk")
	await get_tree().create_timer(WalkOff.STILL_FADE * 0.5 + 0.2).timeout
	assert_bool(hale.is_visible_in_tree()).is_false()
	assert_vector(hale.global_position).is_equal(from)
	assert_float(hale.modulate.a).is_equal(1.0)
	assert_object(hale.get_node_or_null("WalkOff")).is_null()

## Crossroads first, then Hale: the road's first step is already done, and she still goes ahead.
## Another quest starting in the woodland sends nobody anywhere.
func test_hale_goes_ahead_in_the_other_order_and_only_for_her_own_quest() -> void:
	SaveGame.set_flag("visited:crossroads")
	_attach()
	assert_bool(Zones.go_to("woodland", "start")).is_true()
	var hale := _hale_on_the_path()
	Quests.notify("talk:stone_sign")
	assert_str(Quests.state("woodland_stones")).is_equal("active")
	assert_bool(hale.leaving).is_false()
	assert_bool(hale.usable()).is_true()
	await _slice_talk("Actors/HaleOnThePath/Hale")
	assert_str(_step("road_to_crossroads")).is_equal("moss")
	assert_bool(hale.leaving).is_true()

## Her words: nobody says she walks with Bramble or behind, and nothing is left that only a Hale still
## standing on the path could say.
func test_hale_s_words_say_she_goes_ahead() -> void:
	var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/dialogue/crossroads.json"))
	for speaker: String in ["hale", "moss"]:
		for entry: Dictionary in doc[speaker].entries:
			for line: String in entry.lines:
				for wrong: String in ["right behind you", "Walk back with me", "Hale with you"]:
					assert_bool(line.contains(wrong)).override_failure_message("%s: %s" % [speaker, line]).is_false()
	assert_str(String(Quests.defs["road_to_crossroads"].summary)).contains("goes ahead of you")

## The audit of #491: with the player standing east of her, on her way, she walked straight through him.
## She takes a lane to the side away from him, free of solids, and never comes within WalkOff.CLEAR
## texels of his feet (or nearer than she stood, when he is closer than that).
func test_hale_never_walks_through_a_player_who_stands_in_her_way() -> void:
	# on her straight line 52, 36, 20 and 80 texels out; and (audit 1 of #495) where the route
	# crossroads_first talks from, about (58, 13) east and south of her, and (45, -10)
	for spot: Vector2 in [Vector2(52, 0), Vector2(36, 0), Vector2(20, 0), Vector2(80, 0), Vector2(58, 13), Vector2(45, -10)]:
		SaveGame.reset()
		var player := _attach()
		assert_bool(Zones.go_to("woodland", "start")).is_true()
		await get_tree().physics_frame
		var hale := _hale_on_the_path()
		var from := hale.global_position
		var toward: Vector2 = (Zones.current.get_node("Doors/ToCrossroads") as Node2D).global_position
		var on_line := spot.y == 0.0
		player.global_position = from + ((toward - from).normalized() * spot.x if on_line else spot)
		var stood := player.global_position
		var east := stood.x - from.x
		await _slice_talk("Actors/HaleOnThePath/Hale")
		var nearest := INF
		var moved := 0.0
		var shown := 0
		var last := from
		var keep := minf(WalkOff.CLEAR, from.distance_to(stood) - 0.5)
		var grid := WalkGrid.new(get_viewport().get_world_2d(), Zones.current.bounds)
		var occ: Occlusion = Zones.current.occlusion
		# his drawn box as he stands; hers as drawn at each frame, and (where they overlap from the start)
		# her walking box for the way she walks (all frames of that facing and its turns), so that her
		# movement is measured and not her gestures
		var his := WalkOff.drawn_box(player)
		var first := WalkOff.box_overlap(from, WalkOff.drawn_box(hale), stood, his)
		var body := hale.get_node("Body") as Villager
		var walk_boxes := WalkOff.walk_boxes(body)
		var overlap := INF
		while is_instance_valid(hale.get_node_or_null("WalkOff")):
			await get_tree().process_frame
			player.global_position = stood
			if hale.is_visible_in_tree():
				shown += 1
				var d := hale.global_position.distance_to(stood)
				assert_float(d).override_failure_message(      # at every frame, not only the nearest
					"%s: frame %d at %.1f texels" % [spot, shown, d]).is_greater_equal(keep - 0.01)
				nearest = minf(nearest, d)
				moved = maxf(moved, hale.global_position.distance_to(from))
				last = hale.global_position
				assert_bool(grid.is_free(WalkGrid.cell_of(last))).override_failure_message(
					"%s: Hale on a solid cell at %s" % [spot, last]).is_true()
				assert_float(occ.hidden_share(hale)).override_failure_message(      # not under the willow
					"%s: Hale hidden at %s" % [spot, last]).is_less(Occlusion.HIDDEN_SHARE)
				# her drawn body off his while she can be seen: none, or never more than she started with
				var now := WalkOff.box_overlap(last, WalkOff.drawn_box(hale), stood, his)
				if hale.modulate.a > WalkOff.MIN_ALPHA:
					if first == 0.0:
						assert_float(now).override_failure_message("%s: frame %d alpha %.2f, boxes overlap %.0f" % [
							spot, shown, hale.modulate.a, now]).is_equal(0.0)
					elif body.walking != Vector2.ZERO:
						var moved_over := WalkOff.box_overlap(last, WalkOff.box_facing(walk_boxes, body.walking), stood, his)
						assert_float(moved_over).override_failure_message("%s: frame %d alpha %.2f, overlap grew to %.0f from %.0f" % [
							spot, shown, hale.modulate.a, moved_over, overlap]).is_less_equal(overlap + 0.01)
						overlap = moved_over
		assert_float(nearest).override_failure_message(
			"%s: Hale came within %.1f texels of him" % [spot, nearest]).is_greater_equal(keep - 0.01)
		# a step aside and on toward town: where she is last seen is east of where she stood (audit of #491:
		# at 20 and 36 east she turned south, off the road into the meadow); when her body already covers
		# his, she steps off him, away from him
		if first == 0.0:
			assert_float(last.x).override_failure_message("%s: last seen at %s" % [spot, last]).is_greater(from.x)
		else:
			assert_float(last.distance_to(stood)).override_failure_message("%s: last seen at %s" % [spot, last]).is_greater(from.distance_to(stood))
		assert_int(shown).is_greater(10)                           # she is seen going, not popped
		assert_bool(hale.is_visible_in_tree()).is_false()
		assert_bool(hale.usable()).is_false()
		# she walks (audit 1 of #495: no longer 30 texels, since her drawn body may not cross his while she
		# is seen, and 60 texels do not take it past him)
		if east < 60.0:
			assert_float(moved).override_failure_message("%s: she did not walk (%.1f)" % [spot, moved]).is_greater_equal(WalkOff.MIN_WALK)
		player.remove_from_group("player")      # the next round's player is the only one she looks for

## Her path is chosen once, as her talk closes; if he then walks up to her (within the keep distance
## less a texel) she stops where she is and fades out from the alpha she has, at the in-place rate.
func test_when_the_player_walks_up_to_hale_mid_walk_she_stops_and_fades() -> void:
	var player := _attach()
	assert_bool(Zones.go_to("woodland", "start")).is_true()
	await get_tree().physics_frame
	var hale := _hale_on_the_path()
	var from := hale.global_position
	player.global_position = from + Vector2(-40, 0)
	await _slice_talk("Actors/HaleOnThePath/Hale")
	while hale.global_position.distance_to(from) < 12.0:
		await get_tree().process_frame
	assert_float(hale.modulate.a).is_equal(1.0)
	player.global_position = hale.global_position + Vector2(10, 0)       # right up to her
	await get_tree().process_frame
	await get_tree().process_frame
	var stopped := hale.global_position
	var alpha := hale.modulate.a
	assert_float(alpha).is_greater(0.9)
	assert_vector((hale.get_node("Body") as Villager).walking).is_equal(Vector2.ZERO)
	var start := Time.get_ticks_msec()
	while is_instance_valid(hale.get_node_or_null("WalkOff")):
		player.global_position = stopped + Vector2(10, 0)
		await get_tree().process_frame
		if hale.is_visible_in_tree():
			assert_vector(hale.global_position).is_equal(stopped)       # she walks no further
			assert_float(hale.modulate.a).is_less_equal(alpha)         # and only fades
			alpha = hale.modulate.a
	var took := (Time.get_ticks_msec() - start) / 1000.0
	assert_float(took).is_less(WalkOff.STILL_FADE + 0.2)
	assert_float(took).is_greater(WalkOff.STILL_FADE * 0.7)
	assert_bool(hale.is_visible_in_tree()).is_false()

class NoLane extends RefCounted:
	func clear_line(_a: Vector2, _b: Vector2) -> bool:
		return false

class NoStepAside extends RefCounted:
	func clear_line(a: Vector2, b: Vector2) -> bool:
		return a.distance_to(b) > 30.0

class EastOnly extends RefCounted:
	func clear_line(a: Vector2, b: Vector2) -> bool:
		return absf((b - a).normalized().y) < 0.2 and b.x > a.x

func test_the_lane_hale_takes() -> void:
	var from := Vector2(600, 1296)
	var toward := Vector2(951, 1356)
	var straight := (toward - from).normalized()
	# nobody near: straight at the door
	assert_vector(WalkOff.choose_lane(from, toward, Vector2.INF, 61.0, null)).is_equal_approx(straight, Vector2(0.001, 0.001))
	assert_vector(WalkOff.choose_lane(from, toward, from + Vector2(-40, 0), 61.0, null)).is_equal_approx(straight, Vector2(0.001, 0.001))
	# the player on her line: a lane turned away from him that keeps CLEAR
	for side: float in [-1.0, 0.0, 1.0]:
		var player := from + straight * 52.0 + straight.orthogonal() * 6.0 * side
		var dir := WalkOff.choose_lane(from, toward, player, 61.0, null)
		assert_bool(dir != Vector2.ZERO and not dir.is_equal_approx(straight)).is_true()
		assert_float(WalkOff.distance_to_stretch(player, from, from + dir * 61.0)).is_greater_equal(WalkOff.CLEAR)
		if side != 0.0:      # to the side he is not on
			assert_float(signf(straight.cross(dir))).is_equal(-signf(straight.cross(player - from)))
	# a lane with something solid in it is passed over; with none free she stays (and fades in place)
	assert_vector(WalkOff.choose_lane(from, toward, Vector2.INF, 61.0, NoLane.new())).is_equal(Vector2.ZERO)
	assert_vector(WalkOff.choose_lane(from, toward, from + straight * 52.0, 61.0, NoLane.new())).is_equal(Vector2.ZERO)
	var only := WalkOff.choose_lane(from, toward, Vector2.INF, 61.0, EastOnly.new())
	assert_bool(only != Vector2.ZERO).is_true()
	assert_float(absf(only.y)).is_less(0.2)

## The path she takes round a player close east (audit of #491): a short step aside, away from him, and on
## toward the door past him, both legs never within the keep distance of him; when no two-leg path keeps
## it, the single lane choose_lane gives, and with neither she fades in place.
func test_the_path_hale_takes_round_a_player_close_east() -> void:
	var from := Vector2(600, 1296)
	var toward := Vector2(951, 1356)
	var straight := (toward - from).normalized()
	# nobody in the way: the straight lane, one leg
	var free := WalkOff.choose_path(from, toward, Vector2.INF, 61.0, null)
	assert_int(free.size()).is_equal(2)
	assert_vector(free[1]).is_equal_approx(from + straight * 61.0, Vector2(0.001, 0.001))
	for east: float in [20.0, 22.0, 36.0, 40.0, 52.0, 80.0]:
		for side: float in [-1.0, 0.0, 1.0]:
			var player := from + straight * east + straight.orthogonal() * 4.0 * side
			var keep := minf(WalkOff.CLEAR, from.distance_to(player) - 0.5)
			var path := WalkOff.choose_path(from, toward, player, 61.0, null)
			var what := "player %d east, side %d: %s" % [east, side, path]
			assert_int(path.size()).override_failure_message(what).is_equal(3)
			assert_vector(path[0]).is_equal(from)
			var step := path[1] - from
			assert_float(step.length()).override_failure_message(what).is_between(11.99, 20.01)
			assert_float(absf(straight.dot(step.normalized()))).override_failure_message(what).is_less(0.35)     # aside, not along
			if side != 0.0:      # to the side he is not on
				assert_float(signf(straight.cross(step))).override_failure_message(what).is_equal(-signf(straight.cross(player - from)))
			assert_float(step.length() + path[1].distance_to(path[2])).is_equal_approx(61.0, 0.01)      # same length, same time
			assert_float(WalkOff.distance_to_stretch(player, from, path[1])).override_failure_message(what).is_greater_equal(keep)
			assert_float(WalkOff.distance_to_stretch(player, path[1], path[2])).override_failure_message(what).is_greater_equal(keep)
			assert_float(path[2].x).override_failure_message(what).is_greater(from.x + 30.0)       # on toward town
	# something solid in every step aside but a whole lane free: the single lane, as before
	var close := from + straight * 22.0
	var only := WalkOff.choose_path(from, toward, close, 61.0, NoStepAside.new())
	assert_int(only.size()).is_equal(2)
	var lane := WalkOff.choose_lane(from, toward, close, 61.0, NoStepAside.new())
	assert_bool(lane != Vector2.ZERO).is_true()
	assert_vector(only[1]).is_equal_approx(from + lane * 61.0, Vector2(0.001, 0.001))
	# nothing free: fade in place
	assert_int(WalkOff.choose_path(from, toward, from + straight * 22.0, 61.0, NoLane.new()).size()).is_equal(0)
	assert_int(WalkOff.choose_path(from, from, Vector2.INF, 61.0, null).size()).is_equal(0)

func test_with_no_free_lane_hale_fades_where_she_stands() -> void:
	var player := _attach()
	assert_bool(Zones.go_to("woodland", "start")).is_true()
	await get_tree().physics_frame
	var hale := _hale_on_the_path()
	var from := hale.global_position
	player.global_position = from + Vector2(-40, 0)
	var walk := WalkOff.new()
	walk.who = hale
	walk.toward = from                 # nowhere to go: no lane at all
	hale.add_child(walk)
	await get_tree().create_timer(WalkOff.STILL_FADE * 0.5).timeout
	assert_bool(hale.is_visible_in_tree()).is_true()
	assert_vector(hale.global_position).is_equal(from)
	await get_tree().create_timer(WalkOff.STILL_FADE * 0.5 + 0.3).timeout
	assert_bool(hale.is_visible_in_tree()).is_false()
