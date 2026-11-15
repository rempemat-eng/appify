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
	get_tree().paused = false
	Input.action_release("ui_advance")
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

func test_a_damaged_save_is_kept_aside_and_the_game_says_so() -> void:
	var file := ProjectSettings.globalize_path(SAVE)
	var f := FileAccess.open(SAVE, FileAccess.WRITE)
	f.store_string("{ this is not a save")
	f.close()
	assert_int(SaveGame.boot()).is_equal(ERR_PARSE_ERROR)
	assert_bool(FileAccess.file_exists(file + ".broken")).is_true()
	assert_str(FileAccess.get_file_as_string(file + ".broken")).is_equal("{ this is not a save")
	var g := _game()
	await _ticks(2)
	await _frames(3)
	var hud: Control = g.get_node("UI/HUD")
	assert_str(hud.shown_text().banner).is_equal("A new game")
	assert_str(hud.shown_text().banner_text).contains(".broken")
	DirAccess.remove_absolute(file + ".broken")
	SaveGame.boot_error = OK

func test_a_newer_games_save_is_left_alone_and_the_game_says_so() -> void:
	var f := FileAccess.open(SAVE, FileAccess.WRITE)
	f.store_string(JSON.stringify({"version": SaveGame.VERSION + 1, "glint": 500}))
	f.close()
	assert_int(SaveGame.boot()).is_equal(ERR_UNAVAILABLE)
	var g := _game()
	await _ticks(2)
	await _frames(3)
	assert_str((g.get_node("UI/HUD") as Control).shown_text().banner_text).contains("will not be saved over the newer one")
	assert_int(int(_saved().glint)).is_equal(500)      # the autosaves since were refused
	assert_bool(FileAccess.file_exists(ProjectSettings.globalize_path(SAVE) + ".broken")).is_false()
	SaveGame.boot_error = OK

func test_fresh_start_does_not_read_the_save() -> void:
	SaveGame.set_flag("on_disk")
	assert_int(SaveGame.save()).is_equal(OK)
	SaveGame.reset()
	assert_int(SaveGame.boot(true)).is_equal(OK)
	assert_bool(SaveGame.has_flag("on_disk")).is_false()
	assert_int(SaveGame.boot(false)).is_equal(OK)
	assert_bool(SaveGame.has_flag("on_disk")).is_true()

func test_a_lab_zone_is_never_where_the_game_resumes() -> void:
	# The audit of #471: one start of the Brackens lab made it the save's zone, so every later plain
	# start opened inside it, with no door out, under the woodland's banner and quest.
	var g := _game()
	await _ticks(2)
	await _frames(3)
	assert_str(Zones.current.zone_id).is_equal("woodland")
	assert_bool(Zones.go_to("brackens_lab", "west")).is_true()
	await _frames(2)
	assert_bool(Zones.in_lab()).is_true()
	# closing the window, and a settings change in the pause menu, both save: neither names the lab
	g.autosave()
	g.notification(Window.NOTIFICATION_WM_CLOSE_REQUEST)
	assert_int(SaveGame.save()).is_equal(OK)
	assert_str(String(_saved().zone)).is_equal("woodland")
	assert_str(String(_saved().spawn)).is_equal("start")
	assert_bool(_saved().flags.has("visited:brackens_lab")).is_false()
	# in the game it is still the lab (the play driver and the HUD read this)
	assert_str(SaveGame.data.zone).is_equal("brackens_lab")
	# the HUD shows no quest and no lead in a lab
	var hud: Control = g.get_node("UI/HUD")
	assert_str(hud.shown_text().quest_title).is_equal("")
	# leaving the lab makes the save follow the player again
	assert_bool(Zones.go_to("crossroads", "start")).is_true()
	assert_int(SaveGame.save()).is_equal(OK)
	assert_str(String(_saved().zone)).is_equal("crossroads")

func test_a_save_already_inside_a_lab_resumes_at_the_start() -> void:
	# Two sessions, no save by hand. A save made before the lab rule names the Brackens lab; the
	# first start still opens there, and the next plain start must open in the woodland.
	SaveGame.data.zone = "brackens_lab"
	SaveGame.data.spawn = "west"
	SaveGame.data.glint = 12
	assert_int(SaveGame.save()).is_equal(OK)
	SaveGame.reset()
	assert_int(SaveGame.boot()).is_equal(OK)
	var first := _game()
	await _ticks(2)
	await _frames(3)
	assert_str(Zones.current.zone_id).is_equal("brackens_lab")
	var hud: Control = first.get_node("UI/HUD")
	assert_str(hud.shown_text().banner).is_equal("")                # no opening card in a lab
	assert_bool(SaveGame.has_flag("seen:opening")).is_false()
	assert_str(String(_saved().zone)).is_equal("woodland")         # written once, at the start
	assert_int(int(_saved().glint)).is_equal(12)
	first.notification(Window.NOTIFICATION_WM_CLOSE_REQUEST)       # the window closed as a player would
	remove_child(first)
	first.free()
	Zones.current = null
	# the second session: a plain start from the file
	SaveGame.reset()
	assert_int(SaveGame.boot()).is_equal(OK)
	var second := _game()
	await _ticks(2)
	await _frames(3)
	assert_str(Zones.current.zone_id).is_equal("woodland")
	assert_bool(second.player.global_position.is_finite()).is_true()

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

## --shot, --demo and the other picture modes look at a save and never write one (11 Nov: a picture
## taken with --fresh replaced the player's save with a new game).
func test_the_picture_modes_leave_the_save_file_as_it_is() -> void:
	SaveGame.add_glint(85)
	SaveGame.set_flag("visited:crossroads")
	SaveGame.save()
	var g := _game()
	await _ticks(2)
	g.hud.guidance = false        # as game.gd sets it for --shot, --demo and the other picture modes
	var before := FileAccess.get_file_as_bytes(SAVE)
	assert_int(before.size()).is_greater(0)
	SaveGame.add_glint(-50)
	Quests.notify("talk:stone_sign")          # a quest starts: a played game saves here
	assert_str(Quests.state("woodland_stones")).is_equal("active")
	assert_bool(Zones.go_to("crossroads", "start")).is_true()     # and on a zone change
	g.notification(Node.NOTIFICATION_WM_CLOSE_REQUEST)            # and on closing the window
	assert_array(FileAccess.get_file_as_bytes(SAVE)).is_equal(before)
	g.hud.guidance = true
	g.autosave()
	assert_array(FileAccess.get_file_as_bytes(SAVE)).is_not_equal(before)

## A save made before the Frostline gate can hold Moss's loaf as an active quest. This build cannot
## finish it, so loading puts it back to not started and the tracker moves on (11 Nov).
func test_loading_shelves_an_active_quest_whose_zone_is_not_built() -> void:
	SaveGame.data.quests["home_again"] = {"state": "done", "step": 1}
	SaveGame.data.quests["a1_bread_for_the_bothy"] = {"state": "active", "step": 0}
	SaveGame.data.quests["a1_the_torn_roof"] = {"state": "active", "step": 0}
	SaveGame.data.tracked = "a1_bread_for_the_bothy"
	SaveGame.save()
	SaveGame.reset()
	assert_int(SaveGame.load_save()).is_equal(OK)
	assert_str(Quests.state("a1_bread_for_the_bothy")).is_equal("none")
	assert_str(Quests.state("a1_the_torn_roof")).is_equal("active")       # a quest this build can finish stays
	assert_str(Quests.tracked_id()).is_equal("a1_the_torn_roof")
	assert_str(Quests.tracked_text()).contains("The torn roof")

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
	for q: String in ["woodland_stones", "road_to_crossroads", "cold_forge", "under_the_stones", "home_again"]:
		SaveGame.data.quests[q] = {"state": "done", "step": Quests.defs[q].steps.size()}
	SaveGame.data.quests["a1_the_torn_roof"] = {"state": "active", "step": 1}
	SaveGame.set_flag("seen:opening")
	SaveGame.set_flag("first_night_won")      # the night held first (15 Nov: the card waits for it too, below)
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
	assert_str(Quests.tracked_text()).contains("Moss at the stall may know")
	SaveGame.data.quests["road_to_crossroads"] = {"state": "done", "step": 2}
	assert_str(Quests.tracked_text()).contains("Talk to Hale by her smithy")

# --- the dialogue box under the pause menu -------------------------------------------------------------
func _press_advance() -> void:
	Input.action_press("ui_advance")
	await _frames(2)
	Input.action_release("ui_advance")
	await _frames(2)

func test_the_pause_menu_owns_the_keys_over_an_open_line() -> void:
	var box: PanelContainer = auto_free(preload("res://ui/dialogue_box.gd").new())
	box.process_mode = Node.PROCESS_MODE_ALWAYS      # as game.tscn sets it: the box runs under the pause
	add_child(box)
	SaveGame.data.settings.reduced_motion = true     # whole lines at once: one press is one page
	Dialogue.talk("stone_sign")
	await _frames(2)
	assert_str(box.shown_line()).starts_with("TO WHOEVER READS THIS")
	get_tree().paused = true
	await _press_advance()
	await _press_advance()
	assert_str(box.shown_line()).starts_with("TO WHOEVER READS THIS")
	get_tree().paused = false
	await _frames(3)
	await _press_advance()
	assert_str(box.shown_line()).starts_with("Drive them off")
	await _press_advance()
	assert_str(box.shown_line()).is_equal("")
	await get_tree().create_timer(0.3).timeout      # Dialogue stays busy a moment after the box closes

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
	# Moss's loaf waits for the Frostline to be built, and her well for the loaf: no mark over her
	assert_bool((zone.get_node("Actors/Moss") as Interactable).wants_talk()).is_false()

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

func test_of_two_plain_neighbours_the_nearer_has_the_prompt() -> void:
	# Hale on the square (1290, 900) and the smithy's mark (1410, 912), neither with a quest waiting
	# (The road home is at "find Moss"): their areas overlap between them
	SaveGame.set_flag("hale_walked_home")
	SaveGame.set_flag("visited:crossroads")
	SaveGame.data.quests["road_to_crossroads"] = {"state": "active", "step": 1}
	var made := await _zone_with_player("crossroads")
	var player: Player = made[1]
	assert_str(await _stand(player, Vector2(1345, 925))).is_equal("HaleSquare")
	assert_str(await _stand(player, Vector2(1352, 925))).is_equal("SmithySite")
	assert_str(await _stand(player, Vector2(1345, 925))).is_equal("HaleSquare")

## The number keys swap the playable character only when the game was started with --debug-controls
## (15 Nov: they did in every build, and every cast member but Bramble has no bow to shoot yet).
func test_the_number_keys_swap_the_character_only_with_debug_controls() -> void:
	SaveGame.set_flag("seen:opening")
	var g := _game()
	await _ticks(2)
	g.args.erase("debug-controls")
	var was := String(g.player.character)
	for shift: bool in [false, true]:
		for code: int in [KEY_1, KEY_2, KEY_5, KEY_0]:
			var key := InputEventKey.new()
			key.keycode = code as Key
			key.shift_pressed = shift
			key.pressed = true
			g._unhandled_input(key)
			assert_str(String(g.player.character)).override_failure_message(
				"key %s (shift %s) swapped the character without --debug-controls" % [OS.get_keycode_string(code), shift]).is_equal(was)
	assert_bool(g.debug_controls()).is_false()
	# with the flag the same key picks the second of the cast, as before
	g.args["debug-controls"] = true
	var two := InputEventKey.new()
	two.keycode = KEY_2
	two.pressed = true
	g._unhandled_input(two)
	assert_str(String(g.player.character)).is_equal(String(Player.CAST[1]))
	assert_str(String(g.player.character)).is_not_equal(was)

# --- the beat when the meadow camp is cleared (15 Nov) ---------------------------------------
func _free_the_meadow(g: Node2D) -> Camp:
	var camp := Zones.current.get_node("Actors/MeadowCamp") as Camp
	for c in camp.get_children():
		if c.has_signal("died"):
			g.player.global_position = (c as Node2D).global_position + Vector2(48, 0)
			c.call("take_hit", 99, Vector2.LEFT, 0.0)
	return camp

## When the last mossling of the meadow goes, the HUD says the meadow is quiet for a few seconds and
## motes lift off the ground where the camp stood, once and then gone.
func test_the_meadow_cleared_gets_a_short_card_and_a_settle_effect_that_ends() -> void:
	SaveGame.set_flag("seen:opening")
	var g := _game()
	await _ticks(2)
	var hud: Control = g.get_node("UI/HUD")
	assert_str(Zones.current.zone_id).is_equal("woodland")
	assert_str(hud.shown_text().banner).is_equal("")
	Quests.notify("talk:stone_sign")
	var camp := _free_the_meadow(g)
	await _frames(2)
	assert_bool(camp.is_cleared()).is_true()
	assert_str(hud.shown_text().banner).is_equal("The meadow is quiet")
	assert_str(hud.shown_text().banner_text).is_equal("")
	assert_str(hud.shown_text().quest_step).is_equal("Return to the sign by the stones")
	var settle := Zones.current.get_node_or_null("Actors/CampSettle") as CampSettle
	assert_object(settle).is_not_null()
	# over the meadow: within the three mosslings' places (735 to 765, 1476 to 1525 texels)
	assert_bool(Rect2(700, 1450, 100, 100).has_point(settle.global_position)).override_failure_message(str(settle.global_position)).is_true()
	await get_tree().create_timer(CampSettle.LIFE + 0.3).timeout
	assert_bool(is_instance_valid(settle)).override_failure_message("the settle effect is still there after its life").is_false()
	# the card goes too, on its own clock
	assert_float(float(Quests.beat("camp:meadow").seconds)).is_less_equal(5.0)
	await get_tree().create_timer(float(Quests.beat("camp:meadow").seconds) - CampSettle.LIFE + 0.2).timeout
	assert_str(hud.shown_text().banner).is_equal("")
	# nothing of it is saved, and a load into the cleared meadow says nothing
	assert_bool(SaveGame.data.flags.keys().any(func(f: String) -> bool: return f.contains("beat") or f.contains("settle"))).is_false()
	Zones.go_to("woodland", "start")
	await _frames(3)
	assert_str(hud.shown_text().banner).is_equal("")
	assert_object(Zones.current.get_node_or_null("Actors/CampSettle")).is_null()

func test_the_settle_effect_is_finite_and_static_under_reduced_motion() -> void:
	assert_array(CampSettle.parts(CampSettle.LIFE, false)).is_empty()
	assert_array(CampSettle.parts(CampSettle.LIFE, true)).is_empty()
	assert_array(CampSettle.parts(CampSettle.LIFE + 5.0, false)).is_empty()
	# moving: the motes rise and fade
	var early := CampSettle.parts(0.5, false)
	var late := CampSettle.parts(1.4, false)
	assert_int(late.size()).is_equal(CampSettle.MOTES.size())
	assert_float(float(late[0].at.y)).is_less(float(early[0].at.y))
	assert_float(float(late[0].alpha)).is_less(float(early[0].alpha))
	for p: Dictionary in late:           # on the world's grid, never between texels
		assert_vector(p.at).is_equal((p.at / CampSettle.TEXEL).round() * CampSettle.TEXEL)
	# reduced motion: the same still picture from the first frame to the last
	var still := CampSettle.parts(0.0, true)
	assert_int(still.size()).is_equal(CampSettle.MOTES.size())
	for t: float in [0.3, 0.8, 1.2, CampSettle.LIFE - 0.01]:
		assert_array(CampSettle.parts(t, true)).is_equal(still)
	# only the meadow has a beat: the Undercroft's camps and the Thornback's say nothing
	for id: String in ["undercroft_rooms", "undercroft_stair_hall", "thornback"]:
		assert_dict(Quests.beat("camp:" + id)).is_empty()
	# and with the picture modes' guidance off there is no card and no effect
	SaveGame.set_flag("seen:opening")
	var g := _game()
	await _ticks(2)
	var hud: Control = g.get_node("UI/HUD")
	hud.guidance = false
	_free_the_meadow(g)
	await _frames(2)
	assert_str(hud.shown_text().banner).is_equal("")
	assert_object(Zones.current.get_node_or_null("Actors/CampSettle")).is_null()

# --- the end of the slice waits for the first night (15 Nov) -----------------------------------
func _slice_quests_done() -> void:
	for q: String in ["woodland_stones", "road_to_crossroads", "cold_forge", "under_the_stones", "home_again", "a1_the_torn_roof"]:
		SaveGame.data.quests[q] = {"state": "done", "step": Quests.defs[q].steps.size()}
	for f: String in ["seen:opening", "shard_home:woodland", "hale_walked_home", "visited:crossroads", "visited:woodland"]:
		SaveGame.set_flag(f)
	SaveGame.data.village.restored["forge"] = 1

## "Here the story rests" came with Home again and The torn roof done, before the first night had been
## played. It waits for the night now, and while the night is owed the tracker names it.
func test_the_closing_card_waits_for_the_first_night_and_the_tracker_names_it_meanwhile() -> void:
	_slice_quests_done()
	SaveGame.data.zone = "crossroads"
	var g := _game()
	await _ticks(2)
	await _frames(3)
	var hud: Control = g.get_node("UI/HUD")
	# every quest done, the night not yet announced (a load is not a walk into town): no card, and a lead for it
	assert_str(Raids.state()).is_equal("none")
	assert_str(hud.shown_text().banner).is_equal("")
	assert_bool(SaveGame.has_flag("seen:closing")).is_false()
	assert_str(hud.shown_text().quest_title).is_equal("The lit lantern")
	assert_str(hud.shown_text().quest_step).contains("when you next walk into Crossroads")
	# announced and put off, once and twice: the tracker names the night, still no card
	for left: int in [1, 0]:
		assert_bool(Raids.arrive("crossroads", "woodland")).is_true()
		assert_bool(Raids.postpone()).is_true()
		assert_int(Raids.postpones_left()).is_equal(left)
		await _frames(2)
		assert_str(hud.shown_text().quest_title).is_equal("The first night")
		assert_str(hud.shown_text().quest_step).contains("the next time you walk into Crossroads")
		assert_dict(Quests.due_card()).is_empty()
	# the bell: the raid's own line takes the tracker
	assert_bool(Raids.arrive("crossroads", "woodland")).is_true()
	assert_bool(Raids.ring()).is_true()
	await _frames(2)
	assert_str(hud.shown_text().quest_step).contains("Hold the")
	# lost: owed again, named again, no card
	Raids.lose("lantern")
	await _frames(2)
	assert_str(hud.shown_text().quest_title).is_equal("The first night")
	assert_dict(Quests.due_card()).is_empty()
	assert_bool(SaveGame.has_flag("seen:closing")).is_false()
	# won: the closing card, after the night's own card has gone, and the closing lead
	assert_bool(Raids.arrive("crossroads", "woodland")).is_true()
	assert_bool(Raids.ring()).is_true()
	hud.show_card("The first night", "The lantern held", "", 1.0)      # as world/raid_night.gd does on the win
	assert_int(Raids.win()).is_greater(0)
	await _frames(2)
	assert_str(hud.shown_text().banner).is_equal("The first night")
	assert_bool(SaveGame.has_flag("seen:closing")).is_false()
	await get_tree().create_timer(2.2).timeout
	assert_str(hud.shown_text().banner).is_equal("The valley holds")
	assert_str(hud.shown_text().quest_title).is_equal("The valley holds")
	assert_bool(SaveGame.has_flag("seen:closing")).is_true()

## The other order: the night won before The torn roof (routes/first_night.txt plays it from a save
## made just after Home again). The card comes with the roof, as before.
func test_the_closing_card_comes_with_the_last_quest_when_the_night_was_won_first() -> void:
	_slice_quests_done()
	SaveGame.data.quests["a1_the_torn_roof"] = {"state": "active", "step": 1}
	SaveGame.set_flag("first_night_announced")
	SaveGame.set_flag("first_night_won")
	var g := _game()
	await _ticks(2)
	var hud: Control = g.get_node("UI/HUD")
	assert_str(hud.shown_text().banner).is_equal("")
	Quests.notify("talk:morel")
	await _frames(3)
	assert_str(hud.shown_text().banner).is_equal("The valley holds")

## A save from main that already saw the closing card (seen:closing) with the night unplayed: the card
## is not shown twice, and the tracker names the night it still owes.
func test_a_save_that_saw_the_closing_card_before_the_night_is_not_shown_it_again() -> void:
	_slice_quests_done()
	SaveGame.set_flag("seen:closing")
	var g := _game()
	await _ticks(2)
	await _frames(3)
	var hud: Control = g.get_node("UI/HUD")
	assert_str(hud.shown_text().quest_title).is_equal("The lit lantern")
	SaveGame.set_flag("first_night_announced")
	SaveGame.set_flag("first_night_won")
	await _frames(2)
	assert_dict(Quests.due_card()).is_empty()
	assert_str(hud.shown_text().quest_title).is_equal("The valley holds")
