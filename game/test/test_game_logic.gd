extends GdUnitTestSuite
## The game's own logic round the save, the HUD's guidance and the talk areas (the 10 Nov logic pass):
## a loaded game keeps its hearts, the game scene never reads the save file, closing saves, the HUD
## always has a line and shows the title cards once, the tracker follows the quest that moved last, a
## "!" only stands where talking would move a quest, and overlapping talk areas share the prompt by rule.

const SAVE := "user://test_game_logic_save.json"

func before_test() -> void:
	SaveGame.reset()
	SaveGame.path = SAVE

func after_test() -> void:
	SaveGame.path = SaveGame.DEFAULT_PATH
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SAVE))
	Zones.current = null
	Zones.root = null
	SaveGame.reset()

func _game() -> Node2D:
	var g: Node2D = auto_free(load("res://game.tscn").instantiate())
	add_child(g)
	return g

func _ticks(n: int) -> void:
	for i in n:
		await get_tree().physics_frame

func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame

func _saved() -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(SAVE))

# --- the save ---------------------------------------------------------------------------------
func test_a_loaded_game_keeps_its_hearts() -> void:
	SaveGame.data.player.hp = 3
	var g := _game()
	await _ticks(3)
	assert_int(g.player.hp).is_equal(3)
	# the zone change at the start autosaves: it must write the 3 hearts, not a heal
	assert_int(int(_saved().player.hp)).is_equal(3)

func test_a_save_with_impossible_hearts_starts_whole() -> void:
	SaveGame.data.player.hp = 0
	var g := _game()
	await _ticks(2)
	assert_int(g.player.hp).is_equal(g.player.max_hp)

func test_the_game_scene_does_not_read_the_save_file() -> void:
	# a save an earlier test (or an earlier game) left on disk ...
	SaveGame.set_flag("left_by_an_earlier_test")
	SaveGame.data.glint = 77
	assert_int(SaveGame.save()).is_equal(OK)
	# ... and a test that starts from a clean state and makes the game
	SaveGame.reset()
	_game()
	assert_bool(SaveGame.has_flag("left_by_an_earlier_test")).is_false()
	assert_int(int(SaveGame.data.glint)).is_equal(0)

func test_closing_the_window_saves_what_moved_since_the_last_quest_step() -> void:
	var g := _game()
	await _ticks(2)
	g.player.hp = 2
	SaveGame.set_flag("camp_cleared:meadow")     # a camp cleared with no quest waiting on it
	assert_bool(_saved().flags.has("camp_cleared:meadow")).is_false()
	g.notification(Node.NOTIFICATION_WM_CLOSE_REQUEST)
	assert_bool(_saved().flags.has("camp_cleared:meadow")).is_true()
	assert_int(int(_saved().player.hp)).is_equal(2)

func test_a_save_made_while_downed_holds_full_hearts() -> void:
	var g := _game()
	await _ticks(2)
	g.player.hp = 0
	g.autosave()
	assert_int(int(_saved().player.hp)).is_equal(g.player.max_hp)

# --- the HUD's guidance ---------------------------------------------------------------------------
func test_a_new_game_shows_the_opening_card_once_and_a_lead() -> void:
	var g := _game()
	await _ticks(2)
	await _frames(3)
	var hud: Control = g.get_node("UI/HUD")
	assert_str(hud.shown_text().banner).is_equal("The Starfall")
	assert_str(hud.shown_text().quest_title).is_equal("The morning after")
	assert_str(hud.shown_text().quest_step).contains("stone circle")
	assert_bool(SaveGame.has_flag("seen:opening")).is_true()
	assert_bool(_saved().flags.has("seen:opening")).is_true()
	# the same save started again: no second card
	remove_child(g)
	g.free()
	Zones.current = null
	var again := _game()
	await _ticks(2)
	await _frames(3)
	assert_str((again.get_node("UI/HUD") as Control).shown_text().banner).is_equal("")

func test_no_card_and_no_lead_for_pictures() -> void:
	SaveGame.set_flag("seen:opening")
	var g := _game()
	var hud: Control = g.get_node("UI/HUD")
	hud.guidance = false          # as game.gd sets it for --shot, --demo and the other picture modes
	hud.show_card("Title", "", "text")
	await _frames(3)
	assert_str(hud.shown_text().banner).is_equal("")
	assert_str(hud.shown_text().quest_title).is_equal("")
	hud.guidance = true
	await _frames(2)
	assert_str(hud.shown_text().quest_title).is_equal("The morning after")

func test_the_closing_card_waits_for_the_last_quest() -> void:
	for q: String in ["woodland_stones", "road_to_crossroads", "cold_forge", "under_the_stones", "home_again", "a1_the_choked_well"]:
		SaveGame.data.quests[q] = {"state": "done", "step": Quests.defs[q].steps.size()}
	SaveGame.data.quests["a1_the_torn_roof"] = {"state": "active", "step": 1}
	SaveGame.set_flag("seen:opening")
	var g := _game()
	await _ticks(2)
	var hud: Control = g.get_node("UI/HUD")
	assert_str(hud.shown_text().banner).is_equal("")
	Quests.notify("talk:morel")
	await _frames(3)
	assert_str(Quests.state("a1_the_torn_roof")).is_equal("done")
	assert_str(hud.shown_text().banner).is_equal("The valley holds")
	assert_str(hud.shown_text().quest_title).is_equal("The valley holds")
	assert_bool(SaveGame.has_flag("seen:closing")).is_true()

func test_the_tracker_follows_the_quest_that_moved_last() -> void:
	Quests.notify("talk:stone_sign")
	assert_str(Quests.tracked_text()).starts_with("Thorns by the stones")
	Quests.notify("talk:hale")
	assert_str(Quests.tracked_text()).starts_with("The road home")
	Quests.notify("camp:meadow")
	assert_str(Quests.tracked_text()).is_equal("Thorns by the stones: Return to the sign by the stones")
	Quests.notify("talk:stone_sign")       # done: the tracker falls back to the other active quest
	assert_str(Quests.tracked_text()).starts_with("The road home")
	# and it is kept in the save
	assert_int(SaveGame.save()).is_equal(OK)
	assert_str(str(_saved().tracked)).is_equal("woodland_stones")

func test_the_hud_has_a_lead_between_quests() -> void:
	assert_str(Quests.tracked_text()).is_equal("The morning after: Follow the path south to the stone circle")
	assert_str(Quests.tracked_text(false)).is_equal("")
	SaveGame.set_flag("visited:crossroads")
	assert_str(Quests.tracked_text()).contains("Hale the smith is missing")
	SaveGame.data.quests["road_to_crossroads"] = {"state": "done", "step": 2}
	assert_str(Quests.tracked_text()).contains("Talk to Hale by her smithy")

# --- conditions -----------------------------------------------------------------------------------
func test_started_past_and_zone_built_conditions() -> void:
	assert_bool(Quests.check({"started": ["road_to_crossroads"]})).is_false()
	assert_bool(Quests.check({"not_past": ["road_to_crossroads", "go"]})).is_true()
	Quests.notify("talk:hale")
	assert_bool(Quests.check({"started": ["road_to_crossroads"]})).is_true()
	assert_bool(Quests.check({"past": ["road_to_crossroads", "go"]})).is_false()
	Quests.notify("enter:crossroads")
	assert_bool(Quests.check({"past": ["road_to_crossroads", "go"]})).is_true()
	assert_bool(Quests.check({"past": ["road_to_crossroads", "moss"]})).is_false()
	Quests.notify("talk:moss")
	assert_bool(Quests.check({"past": ["road_to_crossroads", "moss"], "started": ["road_to_crossroads"]})).is_true()
	# a zone in the build is a flag conditions can ask for; it is never written to the save
	assert_bool(Quests.check({"flags": ["zone_built:woodland"]})).is_true()
	assert_bool(Quests.check({"flags": ["zone_built:frostline"]})).is_false()
	assert_bool(Quests.check({"not_flags": ["zone_built:frostline"]})).is_true()
	assert_bool(SaveGame.data.flags.has("zone_built:woodland")).is_false()

func test_every_restore_marks_lines_quote_its_cost() -> void:
	for id: String in Village.sites:
		var entries: Array = Dialogue.speakers.get("restore_" + id, {}).get("entries", [])
		var quoted := -1
		for e: Dictionary in entries:
			if e.get("if", {}).has("glint_at_least"):
				quoted = int(e["if"].glint_at_least)
		assert_int(quoted).override_failure_message("restore_%s: its lines quote %d Glint, the plan costs %d" % [id, quoted, Village.cost(id)]).is_equal(Village.cost(id))

# --- talk areas -----------------------------------------------------------------------------------
func _zone_with_player(id: String) -> Array:
	var zone: Zone = auto_free((load(Zones.table[id]) as PackedScene).instantiate())
	add_child(zone)
	var player: Player = auto_free(preload("res://actors/player.tscn").instantiate())
	zone.actors.add_child(player)
	player.input_enabled = false
	return [zone, player]

func _stand(player: Player, at: Vector2) -> String:
	player.global_position = at
	await _ticks(4)
	return String(player.focus.name) if player.focus != null else "none"

func test_a_mark_only_stands_where_talking_moves_a_quest() -> void:
	var made := await _zone_with_player("crossroads")
	var zone: Zone = made[0]
	await _ticks(2)
	# a fresh save: Morel's roof, Moss's well and the lantern's circle cannot start yet
	for path: String in ["Actors/Morel", "Actors/Moss", "Actors/ShardLantern", "Actors/NoticeBoard"]:
		assert_bool((zone.get_node(path) as Interactable).wants_talk()).override_failure_message(path).is_false()
	# once Home again is done, Morel has something to say
	for q: String in ["road_to_crossroads", "cold_forge", "under_the_stones", "home_again"]:
		SaveGame.data.quests[q] = {"state": "done", "step": Quests.defs[q].steps.size()}
	assert_bool((zone.get_node("Actors/Morel") as Interactable).wants_talk()).is_true()
	assert_bool((zone.get_node("Actors/Moss") as Interactable).wants_talk()).is_true()

func test_overlapping_talk_areas_share_the_prompt_by_rule() -> void:
	# Home again, the Ferns' door still to clear: the restore mark (1440, 1308) and Ada (1500, 1296)
	# are 61 texels apart, so their areas overlap
	for q: String in ["road_to_crossroads", "cold_forge", "under_the_stones"]:
		SaveGame.data.quests[q] = {"state": "done", "step": Quests.defs[q].steps.size()}
	SaveGame.data.village.restored["forge"] = 1
	SaveGame.set_flag("shard_home:woodland")
	SaveGame.data.glint = 80
	Quests.notify("talk:moss")
	assert_str(Quests.current_step("home_again").get("id", "")).is_equal("clear")
	var made := await _zone_with_player("crossroads")
	var zone: Zone = made[0]
	var player: Player = made[1]
	# between the two, nearer to Ada: the quest waits on the mark, so the mark has the prompt
	assert_str(await _stand(player, Vector2(1480, 1345))).is_equal("FernSite")
	# the mark is paid: it goes, and the prompt passes to Ada without the player moving
	await (zone.get_node("Actors/If_fern_site/FernSite") as RestoreSite).interact()
	assert_bool(Village.is_restored("fern_cottage")).is_true()
	await _ticks(3)
	assert_str(String(player.focus.name) if player.focus != null else "none").is_equal("Ada")
	# walking away lets go
	assert_str(await _stand(player, Vector2(1480, 1480))).is_equal("none")
	# with no quest on either, the nearer of two overlapping areas has it: the lantern (936, 960) and
	# Hale's old spot are far apart, so use the lantern and the well's mark once Moss has asked
	Quests.notify("talk:ada_fern")
	Quests.notify("talk:moss")
	assert_str(Quests.current_step("a1_the_choked_well").get("id", "")).is_equal("well")
	await _ticks(3)
	assert_str(await _stand(player, Vector2(905, 1010))).is_equal("WellSite")
	SaveGame.data.glint = 80
	await (zone.get_node("Actors/If_well_site/WellSite") as RestoreSite).interact()
	await _ticks(3)
	assert_str(String(player.focus.name) if player.focus != null else "none").is_equal("ShardLantern")
