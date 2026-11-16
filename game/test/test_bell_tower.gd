extends GdUnitTestSuite
## The bell tower in the slice (Matt, 13 Nov, decision (d), docs/vision/decisions-2026-11-13.md: "the bell
## tower is optional, and its cupola is drawn, so that paying visibly changes the square"). The restore
## `bell_tower` is the Crossroads plan's (data/plans/crossroads.json `restores` and `restore_sites`), offered
## once the first night is won, at act 1's 50 Glint. Nothing in the slice waits on it. Paying hangs the bell
## in the library's cupola (Props/If_cupola_hung) in place of the empty one, takes the bell out of the street
## (Props/If_fallen_bell, its look line and its mark go with it), keeps across a save and a load, and is the
## event act 1's The wolf moon waits on.

const PATH := "user://test_bell_tower_save.json"
const SLICE := ["woodland_stones", "road_to_crossroads", "cold_forge", "under_the_stones", "home_again"]
## The quests this build plays to its closing card (test/story/test_story_model.gd PLAYABLE).
const PLAYABLE := ["woodland_stones", "road_to_crossroads", "cold_forge", "under_the_stones", "home_again",
	"a1_the_torn_roof"]

func before_test() -> void:
	SaveGame.reset()

func after_test() -> void:
	SaveGame.reset()
	Raids.offer_restores()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(PATH))
	Zones.current = null
	Zones.root = null

## The save once Home again is done and the first night is won: the lantern lit, the forge and the Ferns'
## door restored, the night's purse paid.
func _night_won(glint := 146) -> void:
	for q: String in SLICE:
		SaveGame.data.quests[q] = {"state": "done", "step": Quests.defs[q].steps.size()}
	for f: String in ["shard_home:woodland", "hale_walked_home", "visited:crossroads", "visited:woodland",
			"first_night_announced", "first_night_won"]:
		SaveGame.set_flag(f)
	SaveGame.data.village.restored = {"forge": 1, "fern_cottage": 1}
	SaveGame.data.raid = {"id": "first_night", "state": "won", "postponed": 2, "wave": 0, "layout": {}, "repairs": false}
	SaveGame.data.glint = glint
	Raids.offer_restores()

func _town() -> Zone:
	var root: Node2D = auto_free(Node2D.new())
	add_child(root)
	var player: Player = auto_free(load("res://actors/player.tscn").instantiate())
	player.input_enabled = false
	Zones.current = null
	Zones.attach(root, player)
	assert_bool(Zones.go_to("crossroads", "start")).is_true()
	return Zones.current

func _shown(zone: Node, path: String) -> bool:
	var n := zone.get_node_or_null(path) as CanvasItem
	assert_object(n).override_failure_message("the scene has no %s" % path).is_not_null()
	return n != null and n.is_visible_in_tree()

# --- offered ---------------------------------------------------------------------------------------------
func test_the_plan_offers_it_from_the_win_at_act_ones_price() -> void:
	var site: Dictionary = Village.sites.get("bell_tower", {})
	assert_str(String(site.get("plan", ""))).is_equal("crossroads")
	assert_bool(site.has("offered_by")).is_false()                 # the plan's own entry, not the raid's fallback
	assert_int(Village.cost("bell_tower")).is_equal(50)
	# the raid's offer says the same: its condition and price
	var offer: Dictionary = Raids.defs.first_night.reward.offers
	assert_str(String(offer.id)).is_equal("bell_tower")
	assert_int(int(offer.cost.glint)).is_equal(Village.cost("bell_tower"))
	assert_dict(offer.get("if")).is_equal(site.get("if"))
	assert_bool(offer.has("mark")).is_false()                       # the plan's site carries the mark now
	# not before the night is won, whatever the purse
	SaveGame.data.glint = 500
	assert_bool(Village.can_restore("bell_tower")).is_false()
	_night_won()
	assert_bool(Village.can_restore("bell_tower")).is_true()
	Raids.offer_restores()                                          # the fallback leaves the plan's entry alone
	assert_bool(Village.sites.bell_tower.has("offered_by")).is_false()

func test_its_mark_stands_by_the_library_door_only_after_the_win() -> void:
	var zone := _town()
	var site := zone.get_node_or_null("Actors/If_bell_tower_site/BellTowerSite") as RestoreSite
	assert_object(site).is_not_null()
	if site == null:
		return
	assert_str(site.restore_id).is_equal("bell_tower")
	assert_float(site.global_position.distance_to(Vector2(248, 214) * 3.0)).is_less(0.5)
	assert_bool(site.is_visible_in_tree()).is_false()               # a new game: no night won
	assert_object(zone.get_node_or_null("Actors/BellTowerSite")).is_null()   # no runtime mark from the raid
	_night_won()
	assert_bool(Zones.go_to("crossroads", "start")).is_true()
	zone = Zones.current
	assert_bool(_shown(zone, "Actors/If_bell_tower_site/BellTowerSite")).is_true()
	assert_object(zone.get_node_or_null("Actors/BellTowerSite")).is_null()

## The "!" the rule drew before 16 Nov: a quest waits on the restore and it is unpaid.
func _quest_mark(s: RestoreSite) -> bool:
	return not Village.is_restored(s.restore_id) and s.waits_on("restore:" + s.restore_id)

## Each restore mark in the scene: [drawn (shown and raising its "!"), shown at all].
func _marks(zone: Node) -> Dictionary:
	var out := {}
	for path: String in ["Actors/If_smithy_site/SmithySite", "Actors/If_fern_site/FernSite",
			"Actors/If_apothecary_site/ApothecarySite", "Actors/If_bell_tower_site/BellTowerSite"]:
		var s := zone.get_node_or_null(path) as RestoreSite
		assert_object(s).override_failure_message("the scene has no %s" % path).is_not_null()
		if s != null:
			out[s.restore_id] = [s.is_visible_in_tree() and s.wants_talk(), s.is_visible_in_tree()]
			if s.restore_id != "bell_tower":                            # the other marks keep the quest's rule
				assert_bool(s.wants_talk()).override_failure_message("%s's !" % s.restore_id) \
					.is_equal(_quest_mark(s))
	return out

func test_the_mark_raises_its_marker_while_offered_and_unpaid() -> void:
	# no quest of the slice waits on restore:bell_tower, so its mark shows the "!" because the night offers
	# it (Raids.offers); the forge, the Ferns' door and the apothecary keep the quest's rule (logic audit of
	# #499 at 95ef791e)
	var zone := _town()
	var m := _marks(zone)                                           # a new game
	assert_array(m.bell_tower).is_equal([false, false])
	assert_array(m.apothecary).is_equal([false, false])
	for q: String in SLICE:                                         # Home again done, the night not yet won
		SaveGame.data.quests[q] = {"state": "done", "step": Quests.defs[q].steps.size()}
	SaveGame.set_flag("shard_home:woodland")
	SaveGame.data.village.restored = {"forge": 1, "fern_cottage": 1}
	SaveGame.data.glint = 500
	assert_bool(Zones.go_to("crossroads", "start")).is_true()
	m = _marks(Zones.current)
	assert_array(m.bell_tower).is_equal([false, false])
	assert_array(m.apothecary).is_equal([false, false])              # not before The torn roof starts
	SaveGame.data.quests.a1_the_torn_roof = {"state": "active", "step": 0}
	assert_bool(Zones.go_to("crossroads", "start")).is_true()
	m = _marks(Zones.current)
	assert_bool(m.apothecary[1]).is_true()
	assert_array(m.bell_tower).is_equal([false, false])
	SaveGame.data.quests.erase("a1_the_torn_roof")
	_night_won()                                                    # won: the bell's mark raises its "!"
	assert_bool(Zones.go_to("crossroads", "start")).is_true()
	zone = Zones.current
	m = _marks(zone)
	assert_array(m.bell_tower).is_equal([true, true])
	assert_array(m.apothecary).is_equal([false, false])
	var site := zone.get_node("Actors/If_bell_tower_site/BellTowerSite") as RestoreSite
	await site.interact()                                           # paid: the mark and its "!" are gone
	assert_bool(Village.is_restored("bell_tower")).is_true()
	m = _marks(zone)
	assert_array(m.bell_tower).is_equal([false, false])

func test_the_win_tells_the_zone_at_once() -> void:
	# Raids.win() reports its reward flags as Village.changed, so a Conditional or a restore mark waiting on
	# first_night_won refreshes there and then, not on the next load (review of #499, round 1)
	SaveGame.reset()
	for q: String in SLICE:
		SaveGame.data.quests[q] = {"state": "done", "step": Quests.defs[q].steps.size()}
	SaveGame.set_flag("shard_home:woodland")
	SaveGame.data.glint = 116
	assert_bool(Raids.arrive("crossroads", "woodland")).is_true()
	Raids.ring()
	var told: Array[String] = []
	var hear := func(id: String) -> void: told.append(id)
	Village.changed.connect(hear)
	var mark := Conditional.new()
	mark.only_if = JSON.stringify({"flags": ["first_night_won"], "not_restored": ["bell_tower"]})
	add_child(auto_free(mark))
	assert_bool(mark.visible).is_false()
	assert_int(Raids.win()).is_greater(0)
	Village.changed.disconnect(hear)
	assert_array(told).contains(["first_night_won"])
	assert_str(Raids.state()).is_equal("won")
	assert_bool(mark.visible).is_true()

# --- not required -------------------------------------------------------------------------------------------
func test_nothing_in_the_slice_waits_on_it() -> void:
	for q: String in PLAYABLE:
		for step: Dictionary in Quests.defs[q].steps:
			assert_str(String(step.get("on", ""))).override_failure_message("%s waits on the bell tower" % q) \
				.is_not_equal("restore:bell_tower")
			assert_str(JSON.stringify(step.get("done_if", {}))).not_contains("bell_tower")
	# the closing card and the lead under it: no bell tower in their conditions
	var leads: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/leads.json"))
	for card: Dictionary in leads.cards:
		if String(card.get("id", "")) == "closing":
			assert_str(JSON.stringify(card.get("if", {}))).not_contains("bell_tower")
	for lead: Dictionary in leads.leads:
		assert_str(JSON.stringify(lead.get("if", {}))).not_contains("bell_tower")
	# the build's end is reached without it: every playable quest done, the night won, the tower not paid
	_night_won(106)
	SaveGame.data.quests.a1_the_torn_roof = {"state": "done", "step": Quests.defs.a1_the_torn_roof.steps.size()}
	SaveGame.data.village.restored.apothecary = 1
	assert_bool(Village.is_restored("bell_tower")).is_false()
	assert_str(String(Quests.due_card().get("id", ""))).is_equal("closing")

# --- pay, the picture, persistence -------------------------------------------------------------------------
func test_paying_hangs_the_bell_and_clears_the_street() -> void:
	_night_won()
	var zone := _town()
	assert_bool(_shown(zone, "Props/If_cupola_empty/CupolaEmpty")).is_true()
	assert_bool(_shown(zone, "Props/If_cupola_hung/CupolaHung")).is_false()
	assert_bool(_shown(zone, "Props/CupolaShadow")).is_true()
	assert_bool(_shown(zone, "Props/If_fallen_bell/FallenBell")).is_true()
	assert_bool(_shown(zone, "Actors/If_fallen_bell/FallenBell")).is_true()
	var site := zone.get_node_or_null("Actors/If_bell_tower_site/BellTowerSite") as RestoreSite
	assert_object(site).is_not_null()
	if site == null:
		return
	var before := int(SaveGame.data.glint)
	await site.interact()
	assert_bool(Village.is_restored("bell_tower")).is_true()
	assert_int(int(SaveGame.data.glint)).is_equal(before - 50)    # the 50 Glint and nothing more
	assert_bool(_shown(zone, "Props/If_cupola_hung/CupolaHung")).is_true()
	assert_bool(_shown(zone, "Props/If_cupola_empty/CupolaEmpty")).is_false()
	assert_bool(_shown(zone, "Props/CupolaShadow")).is_true()
	assert_bool(_shown(zone, "Props/If_fallen_bell/FallenBell")).is_false()
	assert_bool(_shown(zone, "Props/If_fallen_bell_shadow/FallenBellShadow")).is_false()
	assert_bool(_shown(zone, "Actors/If_fallen_bell/FallenBell")).is_false()
	assert_bool(_shown(zone, "Actors/If_bell_tower_site/BellTowerSite")).is_false()
	# the bell in the street blocked feet; once it is hung its body is off with it
	assert_object(zone.get_node_or_null("Props/If_fallen_bell/FallenBellBody")).is_not_null()
	var wrap := zone.get_node_or_null("Props/If_fallen_bell")
	assert_bool(wrap != null and not wrap.can_process()).is_true()
	# nothing else changed: no flag, quest or other restore came with it
	assert_dict(SaveGame.data.village.restored).is_equal({"forge": 1, "fern_cottage": 1, "bell_tower": 1})

func test_not_enough_glint_takes_nothing() -> void:
	_night_won(49)
	var zone := _town()
	var site := zone.get_node_or_null("Actors/If_bell_tower_site/BellTowerSite") as RestoreSite
	assert_object(site).is_not_null()
	if site == null:
		return
	await site.interact()
	assert_bool(Village.is_restored("bell_tower")).is_false()
	assert_int(int(SaveGame.data.glint)).is_equal(49)
	assert_bool(_shown(zone, "Props/If_cupola_empty/CupolaEmpty")).is_true()
	assert_bool(_shown(zone, "Props/If_fallen_bell/FallenBell")).is_true()

func test_the_hung_bell_keeps_across_a_save_and_a_load() -> void:
	_night_won()
	assert_bool(Village.restore("bell_tower")).is_true()
	assert_int(SaveGame.save(PATH)).is_equal(OK)
	SaveGame.reset()
	assert_bool(Village.is_restored("bell_tower")).is_false()
	assert_int(SaveGame.load_save(PATH)).is_equal(OK)
	assert_bool(Village.is_restored("bell_tower")).is_true()
	assert_int(int(SaveGame.data.glint)).is_equal(96)
	var zone := _town()
	assert_bool(_shown(zone, "Props/If_cupola_hung/CupolaHung")).is_true()
	assert_bool(_shown(zone, "Props/If_cupola_empty/CupolaEmpty")).is_false()
	assert_bool(_shown(zone, "Props/If_fallen_bell/FallenBell")).is_false()
	assert_bool(_shown(zone, "Actors/If_bell_tower_site/BellTowerSite")).is_false()

# --- the bell's look line -----------------------------------------------------------------------------------
func test_the_bell_names_the_mark_once_the_night_is_won() -> void:
	var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/dialogue/crossroads.json"))
	var entries: Array = doc.fallen_bell.entries
	assert_dict(entries[0].get("if", {})).is_equal({"flags": ["first_night_won"]})
	assert_str(String(entries[0].lines[0])).contains("The mark by the library door")
	assert_str(String(entries[1].lines[0])).not_contains("mark")
	assert_bool(entries[1].has("if")).is_false()
	for e: Dictionary in entries:                                  # no price, no reward on the look
		assert_str(String(e.lines[0])).not_contains("Glint")

# --- act 1 later -------------------------------------------------------------------------------------------
func test_the_wolf_moon_step_fires_on_the_restore() -> void:
	_night_won()
	SaveGame.data.quests.a1_the_wolf_moon = {"state": "active", "step": 0}
	assert_str(String(Quests.current_step("a1_the_wolf_moon").get("id", ""))).is_equal("bell")
	assert_bool(Village.restore("bell_tower")).is_true()
	assert_str(String(Quests.current_step("a1_the_wolf_moon").get("id", ""))).is_equal("ring")

func test_a_tower_paid_in_the_slice_still_counts_for_the_wolf_moon() -> void:
	_night_won()
	assert_bool(Village.restore("bell_tower")).is_true()
	SaveGame.data.quests.a1_the_circle_wakes = {"state": "done", "step": Quests.defs.a1_the_circle_wakes.steps.size()}
	Quests.notify("talk:hale")
	assert_str(Quests.state("a1_the_wolf_moon")).is_equal("active")
	assert_str(String(Quests.current_step("a1_the_wolf_moon").get("id", ""))).is_equal("ring")
