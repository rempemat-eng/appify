extends GdUnitTestSuite
## The sample quest in the woodland moves on events, pays its Glint once, and its dialogue follows it.

const Q := "woodland_stones"

func before_test() -> void:
	SaveGame.reset()

func test_quest_runs_start_to_finish() -> void:
	assert_str(Quests.state(Q)).is_equal("none")
	assert_bool(Quests.notify("camp:meadow")).is_false()  # nothing listens before the quest starts
	Quests.notify("talk:stone_sign")
	assert_str(Quests.state(Q)).is_equal("active")
	assert_str(Quests.current_step(Q).id).is_equal("clear_camp")
	Quests.notify("talk:stone_sign")  # talking again does not skip the fight
	assert_str(Quests.current_step(Q).id).is_equal("clear_camp")
	SaveGame.set_flag("camp_cleared:meadow")
	Quests.notify("camp:meadow")
	assert_str(Quests.current_step(Q).id).is_equal("return")
	Quests.notify("talk:stone_sign")
	assert_str(Quests.state(Q)).is_equal("done")
	assert_int(SaveGame.data.glint).is_equal(40)
	assert_bool(SaveGame.has_flag("woodland_stones_done")).is_true()
	Quests.notify("talk:stone_sign")  # rewards are paid once
	assert_int(SaveGame.data.glint).is_equal(40)

func test_camp_cleared_first_still_counts() -> void:
	SaveGame.set_flag("camp_cleared:meadow")
	Quests.notify("talk:stone_sign")
	assert_str(Quests.current_step(Q).id).is_equal("return")

func test_dialogue_follows_the_quest() -> void:
	var intro := Dialogue.lines_for("stone_sign")
	assert_str(intro[0]).starts_with("TO WHOEVER")
	Quests.start_quest(Q)
	assert_str(Dialogue.lines_for("stone_sign")[0]).starts_with("Mosslings")
	Quests.notify("camp:meadow")
	assert_str(Dialogue.lines_for("stone_sign")[0]).contains("gone")
	Quests.notify("talk:stone_sign")
	assert_str(Dialogue.lines_for("stone_sign")[0]).contains("quiet")

func test_talk_reports_to_quests() -> void:
	await Dialogue.talk("stone_sign")  # no box listens in tests, so it closes at once
	assert_str(Quests.state(Q)).is_equal("active")

func test_conditions() -> void:
	assert_bool(Quests.check(null)).is_true()
	assert_bool(Quests.check({"flags": ["x"]})).is_false()
	SaveGame.set_flag("x")
	assert_bool(Quests.check({"flags": ["x"], "not_started": [Q]})).is_true()
	assert_bool(Quests.check({"not_flags": ["x"]})).is_false()

func test_camp_clears_when_its_last_enemy_dies() -> void:
	Quests.start_quest(Q)
	var camp := Camp.new()
	camp.camp_id = "meadow"
	for i in 2:
		var e: Enemy = load("res://actors/enemy.tscn").instantiate()
		e.position = Vector2(200 + 80 * i, 200)
		camp.add_child(e)
	add_child(auto_free(camp))
	var enemies := camp.get_children()
	for e in enemies:
		e.take_hit(99, Vector2.RIGHT)
	assert_bool(SaveGame.has_flag("camp_cleared:meadow")).is_true()
	assert_str(Quests.current_step(Q).id).is_equal("return")

func test_sample_quest_in_the_woodland_scene() -> void:
	var root: Node2D = auto_free(Node2D.new())
	add_child(root)
	var player: Player = auto_free(load("res://actors/player.tscn").instantiate())
	player.input_enabled = false
	Zones.current = null
	Zones.attach(root, player)
	assert_bool(Zones.go_to("woodland", "start")).is_true()
	var zone := Zones.current
	var sign := zone.get_node("Actors/StoneSign") as Interactable
	assert_bool(sign.wants_talk()).is_true()
	await sign.interact()
	assert_str(Quests.current_step(Q).id).is_equal("clear_camp")
	assert_bool(sign.wants_talk()).is_false()
	var camp := zone.get_node("Actors/MeadowCamp") as Camp
	var enemies := camp.get_children()
	assert_int(enemies.size()).is_equal(3)
	for e in enemies:
		e.take_hit(99, Vector2.RIGHT)
	assert_bool(camp.is_cleared()).is_true()
	assert_bool(sign.wants_talk()).is_true()
	await sign.interact()
	assert_str(Quests.state(Q)).is_equal("done")
	assert_int(SaveGame.data.glint).is_equal(40)
	# the camp stays cleared when the zone loads again
	assert_bool(Zones.go_to("woodland", "start")).is_true()
	await get_tree().process_frame
	assert_int(Zones.current.get_node("Actors/MeadowCamp").get_child_count()).is_equal(0)
	Zones.current = null
	Zones.root = null
