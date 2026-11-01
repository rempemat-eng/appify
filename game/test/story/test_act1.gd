extends GdUnitTestSuite
## Act 1 after the slice (docs/story/act1.md): the Frostline, the Brackens, Morel, Velvet, Cairn waking,
## the wolf moon and the Millrace landslip, as quest and dialogue data. Drives the chain with
## Quests.notify, checks who says what at the key beats, and checks the data against itself: every
## talk step has someone to talk to, every restore step has a mark's lines, and act 1's lines for the
## slice's people come before the slice's own (Dialogue's entry priority).

const SLICE := ["woodland_stones", "road_to_crossroads", "cold_forge", "under_the_stones", "home_again"]

func before_test() -> void:
	SaveGame.reset()

func _step(q: String) -> String:
	return Quests.current_step(q).get("id", "")

func _restore(id: String) -> void:
	# The restore marks for act 1 are Claude A's to place in crossroads.json; here the save stands in.
	SaveGame.data.village.restored[id] = 1
	Quests.notify("restore:" + id)

func _first_line(speaker: String) -> String:
	var lines := Dialogue.lines_for(speaker)
	return lines[0] if lines.size() > 0 else ""

func _finish_slice() -> void:
	for q in SLICE:
		SaveGame.data.quests[q] = {"state": "done", "step": Quests.defs[q].steps.size()}
	SaveGame.set_flag("shard_home:woodland")

func _act1_ids() -> Array:
	return Quests.defs.keys().filter(func(id: String) -> bool: return id.begins_with("a1_"))

func test_act1_data_is_whole() -> void:
	var ids := _act1_ids()
	assert_int(ids.size()).is_equal(15)
	for id in ids:
		var def: Dictionary = Quests.defs[id]
		assert_str(def.get("title", "")).is_not_empty()
		for ev in [def.start.on] + def.steps.map(func(s: Dictionary) -> String: return s.on):
			var kind: String = ev.get_slice(":", 0)
			var what: String = ev.get_slice(":", 1)
			assert_array(["talk", "camp", "enter", "restore"]).contains([kind])
			if kind == "talk":
				assert_bool(Dialogue.speakers.has(what)).override_failure_message("%s: nobody to talk to: %s" % [id, what]).is_true()
			if kind == "restore":
				assert_bool(Dialogue.speakers.has("restore_" + what)).override_failure_message("%s: no lines for the mark %s" % [id, what]).is_true()
		for cond_q in def.get("start", {}).get("if", {}).get("done", []):
			assert_bool(Quests.defs.has(cond_q)).is_true()

func test_layers_put_act1_first_and_keep_the_slice() -> void:
	# Before the slice is done, Moss still speaks the slice's lines; after it, act 1's offer.
	assert_str(_first_line("moss")).is_equal("Stall's open. It's the only thing on the square that is.")
	_finish_slice()
	assert_str(_first_line("moss")).starts_with("Before the storm the hut warden came down")
	assert_str(Dialogue.speakers.moss.name).is_equal("Moss")
	# Hale's slice line still shows when act 1 has nothing for her yet
	assert_str(_first_line("hale")).is_equal("Two chimneys smoking on the square. It almost looks like a town again.")

func test_the_frostline() -> void:
	_finish_slice()
	Quests.notify("talk:moss")
	assert_str(_step("a1_bread_for_the_bothy")).is_equal("col")
	Quests.notify("enter:frostline")
	assert_str(_step("a1_bread_for_the_bothy")).is_equal("col")
	Quests.notify("camp:col_crows")
	assert_bool(SaveGame.has_flag("way_open:W2")).is_true()
	Quests.notify("enter:frostline")
	assert_str(_first_line("hut_warden")).starts_with("Bread!")
	Quests.notify("talk:hut_warden")
	assert_str(Quests.state("a1_bread_for_the_bothy")).is_equal("done")
	assert_str(_step("a1_the_ring_is_shut")).is_equal("fells")
	Quests.notify("camp:fells_ibex")
	Quests.notify("talk:hut_warden")
	assert_str(Quests.state("a1_the_ring_is_shut")).is_equal("done")
	assert_str(_step("a1_under_the_snout")).is_equal("cutter")
	Quests.notify("talk:ice_cutter")
	Quests.notify("enter:ice_caves")
	Quests.notify("camp:ice_caves_rooms")
	Quests.notify("talk:tam")  # Tam waits until the wyrm is freed
	assert_str(_step("a1_under_the_snout")).is_equal("wyrm")
	Quests.notify("camp:rime_wyrm")
	assert_str(_first_line("tam")).starts_with("You came in.")
	Quests.notify("talk:tam")
	Quests.notify("talk:frost_shard")
	assert_bool(SaveGame.has_flag("shard_taken:frostline")).is_true()
	Quests.notify("talk:shard_lantern")
	assert_bool(SaveGame.has_flag("shard_home:frostline")).is_true()
	assert_str(Quests.state("a1_under_the_snout")).is_equal("done")
	# Tam joins at the bothy, then the warden sends the town a ring
	Quests.notify("talk:hut_warden")
	assert_str(_step("a1_a_cup_by_the_stove")).is_equal("tam")
	Quests.notify("talk:tam")
	assert_bool(SaveGame.has_flag("folk:tam")).is_true()
	Quests.notify("talk:hut_warden")
	assert_str(_step("a1_the_training_yard")).is_equal("yard")
	_restore("training_yard")
	Quests.notify("talk:hale")
	assert_bool(SaveGame.has_flag("training_yard_open")).is_true()

func test_the_brackens() -> void:
	_finish_slice()
	Quests.notify("talk:drover")
	assert_str(_step("a1_the_scattered_flock")).is_equal("flock")
	Quests.notify("camp:gap_flock")
	Quests.notify("talk:drover")
	assert_str(_step("a1_the_cut_rope")).is_equal("well")
	Quests.notify("talk:drove_well")
	Quests.notify("enter:the_barrow")
	Quests.notify("camp:barrow_rooms")
	Quests.notify("camp:old_fang")
	Quests.notify("talk:barrow_shard")
	Quests.notify("talk:shard_lantern")
	assert_bool(SaveGame.has_flag("shard_home:brackens")).is_true()
	Quests.notify("talk:drover")
	Quests.notify("camp:spur_tor")
	assert_str(_first_line("iona")).starts_with("The ram's down?")
	Quests.notify("talk:iona")
	assert_bool(SaveGame.has_flag("folk:iona")).is_true()
	# the shepherd's side quest stands on its own, and clearing the dog first still counts
	SaveGame.set_flag("camp_cleared:stray_dog")
	Quests.notify("talk:shepherd")
	assert_str(_step("a1_the_shepherds_dog")).is_equal("home")

func test_the_valley_and_the_end_of_act1() -> void:
	_finish_slice()
	# Morel and Velvet, the other two starters
	Quests.notify("talk:morel")
	_restore("apothecary")
	assert_str(_first_line("morel")).starts_with("A roof!")
	Quests.notify("talk:morel")
	assert_bool(SaveGame.has_flag("folk:morel")).is_true()
	Quests.notify("talk:velvet")
	Quests.notify("enter:driftwood")
	Quests.notify("camp:driftwood_quay")
	Quests.notify("talk:lighthouse_lamp")
	Quests.notify("talk:velvet")
	assert_bool(SaveGame.has_flag("folk:velvet")).is_true()
	# the circle wakes only once all three great shards are home
	Quests.notify("talk:shard_lantern")
	assert_str(Quests.state("a1_the_circle_wakes")).is_equal("none")
	SaveGame.set_flag("shard_home:frostline")
	SaveGame.set_flag("shard_home:brackens")
	Quests.notify("talk:shard_lantern")
	assert_str(_step("a1_the_circle_wakes")).is_equal("stones")
	Quests.notify("talk:circle_stones")
	Quests.notify("camp:circle_trial")
	Quests.notify("talk:cairn")
	assert_bool(SaveGame.has_flag("folk:cairn")).is_true()
	# the wolf moon, then the landslip opens the line to Cogsworth
	Quests.notify("talk:hale")
	Quests.notify("talk:bell_tower")  # no bell to ring before the cupola is rebuilt
	assert_str(_step("a1_the_wolf_moon")).is_equal("bell")
	_restore("bell_tower")
	Quests.notify("talk:bell_tower")
	Quests.notify("camp:wolf_moon")
	Quests.notify("talk:hale")
	assert_str(Quests.state("a1_the_wolf_moon")).is_equal("done")
	Quests.notify("talk:moss")
	_restore("halt")
	Quests.notify("camp:millrace_slip")
	assert_bool(SaveGame.has_flag("way_open:W3")).is_true()
	Quests.notify("talk:moss")
	assert_bool(SaveGame.has_flag("act1_done")).is_true()
	for f in ["folk:morel", "folk:velvet", "folk:cairn"]:
		assert_bool(SaveGame.has_flag(f)).is_true()

func test_priority_orders_entries_across_files() -> void:
	var d: Node = Dialogue
	var before: Dictionary = d.speakers.duplicate(true)
	d.add_doc({"probe": {"name": "First", "entries": [{"lines": ["base"]}]}})
	d.add_doc({"probe": {"name": "Second", "entries": [{"priority": 5, "lines": ["over"]}, {"lines": ["tail"]}]}})
	assert_str(d.speakers.probe.name).is_equal("First")
	var got: Array = d.speakers.probe.entries.map(func(e: Dictionary) -> String: return e.lines[0])
	assert_array(got).is_equal(["over", "base", "tail"])
	d.speakers = before
