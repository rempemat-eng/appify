extends GdUnitTestSuite
## The first night (core/raids.gd, world/raid_night.gd, enemies/raid_creature.gd, ui/raid_screen.gd;
## docs/vision/vertical-slice.md beat 8): the raid's state machine, its two postponements, the save's
## migration, and the win and the loss, in data and in the Crossroads scene. The scene tests step the
## night and its creatures by hand (no physics frames, no input): they hold the rules, not the feel.

const PATH := "user://test_raids_save.json"
const SLICE := ["woodland_stones", "road_to_crossroads", "cold_forge", "under_the_stones", "home_again"]

func before_test() -> void:
	SaveGame.reset()

func after_test() -> void:
	SaveGame.reset()
	Raids.offer_restores()          # no bell tower left in Village.sites for the suites after this one
	DirAccess.remove_absolute(ProjectSettings.globalize_path(PATH))
	Zones.current = null
	Zones.root = null

## The save as it stands once Home again is done: the lantern lit, the forge and the Ferns' door restored.
func _after_home_again() -> void:
	for q: String in SLICE:
		SaveGame.data.quests[q] = {"state": "done", "step": Quests.defs[q].steps.size()}
	for f: String in ["shard_home:woodland", "hale_walked_home", "visited:crossroads", "visited:woodland"]:
		SaveGame.set_flag(f)
	SaveGame.data.village.restored = {"forge": 1, "fern_cottage": 1}
	SaveGame.data.glint = 116

# --- the state machine -------------------------------------------------------------------------
func test_a_new_game_has_no_raid() -> void:
	assert_str(Raids.state()).is_equal("none")
	assert_dict(SaveGame.fresh().raid).is_equal({"id": "", "state": "none", "postponed": 0, "wave": 0, "layout": {}, "repairs": false})
	assert_bool(Raids.defs.has("first_night")).is_true()
	assert_bool(Raids.arrive("crossroads", "woodland")).is_false()
	assert_str(Raids.state()).is_equal("none")

func test_attention_comes_from_the_lit_lantern_and_waits_for_home_again() -> void:
	SaveGame.set_flag("shard_home:woodland")
	SaveGame.data.quests.home_again = {"state": "active", "step": 0}
	assert_bool(Raids.arrive("crossroads", "woodland")).is_false()
	assert_str(Raids.state()).is_equal("none")
	_after_home_again()
	SaveGame.set_flag("shard_home:woodland", false)
	assert_bool(Raids.arrive("crossroads", "woodland")).is_false()   # no attention without the lantern lit
	SaveGame.set_flag("shard_home:woodland")
	assert_bool(Raids.arrive("crossroads", "woodland")).is_true()
	assert_str(Raids.state()).is_equal("announced")
	assert_str(String(Raids.rec().id)).is_equal("first_night")
	assert_bool(SaveGame.has_flag("first_night_announced")).is_true()

func test_it_is_announced_on_a_walk_into_town_not_on_a_load_or_getting_up() -> void:
	_after_home_again()
	assert_bool(Raids.arrive("crossroads", "")).is_false()            # the game starts in town
	assert_bool(Raids.arrive("crossroads", "crossroads")).is_false()  # up again where the player fell
	assert_bool(Raids.arrive("woodland", "crossroads")).is_false()    # another zone
	assert_str(Raids.state()).is_equal("none")
	assert_bool(Raids.arrive("crossroads", "undercroft")).is_true()
	assert_str(Raids.state()).is_equal("announced")

func test_two_postponements_then_it_begins_on_the_next_walk_in() -> void:
	_after_home_again()
	Raids.arrive("crossroads", "woodland")
	assert_int(Raids.postpones_left()).is_equal(2)
	assert_bool(Raids.postpone()).is_true()
	assert_str(Raids.state()).is_equal("postponed")
	assert_bool(Raids.postpone()).is_false()                           # only from the screen
	assert_bool(Raids.ring()).is_false()
	assert_bool(Raids.arrive("crossroads", "crossroads")).is_false()  # getting up is not a return home
	assert_bool(Raids.arrive("crossroads", "woodland")).is_true()
	assert_int(Raids.postpones_left()).is_equal(1)
	assert_bool(Raids.postpone()).is_true()
	assert_str(Raids.state()).is_equal("pending")
	assert_int(Raids.postpones_left()).is_equal(0)
	assert_bool(Raids.arrive("crossroads", "woodland")).is_true()
	assert_str(Raids.state()).is_equal("announced")
	assert_bool(Raids.postpone()).is_false()                           # no third "not tonight"
	assert_str(Raids.state()).is_equal("announced")
	assert_bool(Raids.ring()).is_true()
	assert_str(Raids.state()).is_equal("running")
	assert_bool(SaveGame.has_flag("first_night_postponed")).is_false()

func test_a_screen_left_open_or_a_night_cut_short_comes_back_from_wave_one() -> void:
	_after_home_again()
	Raids.arrive("crossroads", "woodland")
	assert_bool(Raids.arrive("crossroads", "")).is_true()             # quit on the screen, start again
	assert_str(Raids.state()).is_equal("announced")
	Raids.ring()
	Raids.wave_started(2)
	assert_bool(Raids.arrive("crossroads", "")).is_true()             # quit mid-night, start again
	assert_str(Raids.state()).is_equal("announced")
	assert_int(int(Raids.rec().wave)).is_equal(0)

func test_a_win_pays_the_purse_once_and_offers_the_bell_tower() -> void:
	_after_home_again()
	Raids.arrive("crossroads", "woodland")
	assert_int(Raids.win()).is_equal(0)                                # not before the bell
	Raids.ring()
	var purse := int(GlintCache.balance().raids.first_night)
	assert_int(purse).is_greater(0)
	assert_int(Raids.win()).is_equal(purse)
	assert_int(int(SaveGame.data.glint)).is_equal(116 + purse)
	assert_str(Raids.state()).is_equal("won")
	assert_bool(SaveGame.has_flag("first_night_won")).is_true()
	assert_bool(Raids.won("first_night")).is_true()
	assert_int(Raids.win()).is_equal(0)                                # never twice
	assert_int(int(SaveGame.data.glint)).is_equal(116 + purse)
	# the bell tower is offered as a restore, at act 1's price, from the win on
	assert_bool(Village.sites.has("bell_tower")).is_true()
	assert_int(Village.cost("bell_tower")).is_equal(50)
	assert_bool(Village.can_restore("bell_tower")).is_true()
	SaveGame.set_flag("first_night_won", false)
	assert_bool(Village.can_restore("bell_tower")).is_false()
	Raids.offer_restores()
	assert_bool(Village.sites.has("bell_tower")).is_false()        # never offered before the win
	SaveGame.set_flag("first_night_won")
	Raids.offer_restores()
	assert_bool(Raids.arrive("crossroads", "woodland")).is_false()     # it does not come again
	assert_str(Raids.state()).is_equal("won")

func test_a_loss_costs_brief_repairs_cleared_on_the_next_visit_and_the_raid_comes_again() -> void:
	_after_home_again()
	Raids.arrive("crossroads", "woodland")
	Raids.postpone()
	Raids.arrive("crossroads", "woodland")
	Raids.ring()
	Raids.lose()
	assert_str(Raids.state()).is_equal("lost")
	assert_bool(bool(Raids.rec().repairs)).is_true()
	assert_int(int(SaveGame.data.glint)).is_equal(116)                 # nothing taken
	assert_dict(SaveGame.data.village.restored).is_equal({"forge": 1, "fern_cottage": 1})
	assert_bool(Raids.arrive("crossroads", "crossroads")).is_false()  # up again: the repairs still show
	assert_bool(bool(Raids.rec().repairs)).is_true()
	assert_bool(Raids.arrive("crossroads", "woodland")).is_true()
	assert_bool(bool(Raids.rec().repairs)).is_false()
	assert_str(Raids.state()).is_equal("announced")
	assert_int(Raids.postpones_left()).is_equal(2)                     # a lost night is offered again afresh

func test_going_down_loses_the_night_only_while_it_runs() -> void:
	_after_home_again()
	Raids.player_downed()
	assert_str(Raids.state()).is_equal("none")
	Raids.arrive("crossroads", "woodland")
	Raids.player_downed()
	assert_str(Raids.state()).is_equal("announced")
	Raids.ring()
	Raids.player_downed()
	assert_str(Raids.state()).is_equal("lost")

func test_every_pad_starts_with_hales_hurdle_and_a_tap_cycles_it() -> void:
	_after_home_again()
	Raids.arrive("crossroads", "woodland")
	var pads: Array = Raids.pads()
	assert_int(pads.size()).is_equal(2)
	for pad: Dictionary in pads:
		assert_str(Raids.pad_kind(pad.id)).is_equal("hurdle_barricade")
	assert_array(Raids.kinds_owned()).is_equal(["hurdle_barricade"])
	assert_str(Raids.cycle_pad("pad_halt_gate")).is_equal("")
	assert_str(Raids.pad_kind("pad_halt_gate")).is_equal("")
	assert_str(Raids.cycle_pad("pad_halt_gate")).is_equal("hurdle_barricade")
	Raids.cycle_pad("pad_halt_street")
	assert_dict(Raids.rec().layout).is_equal({"pad_halt_gate": "hurdle_barricade", "pad_halt_street": ""})
	# without the forge there is no kind to choose, but the prefill stands
	SaveGame.data.village.restored.erase("forge")
	assert_array(Raids.kinds_owned()).is_empty()

func test_the_pads_and_the_lane_come_from_the_plan() -> void:
	var lane := Raids.lane(Raids.defs.first_night)
	assert_int(lane.size()).is_equal(3)
	assert_vector(lane[0]).is_equal(Vector2(0, 300))
	var gate: Dictionary = Raids.pads(Raids.defs.first_night).filter(func(p: Dictionary) -> bool: return p.id == "pad_halt_gate")[0]
	assert_vector(gate.at).is_equal(Vector2(210, 300))
	# both pads stand on the halt road (the one lane), the street pad first
	for pad: Dictionary in Raids.pads(Raids.defs.first_night):
		assert_float(absf((pad.at as Vector2).y - 300.0)).is_less_equal(12.0)
	var def: Dictionary = Raids.defs.first_night
	assert_int((def.waves as Array).size()).is_equal(3)
	for w: Dictionary in def.waves:
		for role: String in w.creatures:
			assert_bool(role in ["rusher", "shooter", "shield", "elite"]).is_true()

# --- the save ----------------------------------------------------------------------------------
func _write(doc: Variant) -> void:
	var f := FileAccess.open(PATH, FileAccess.WRITE)
	f.store_string(JSON.stringify(doc))
	f.close()

func test_an_older_save_loads_with_no_raid_pending() -> void:
	for name: String in ["v1-village.json", "v1-foundation.json", "legacy-unversioned.json"]:
		var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://test/fixtures/saves/" + name))
		assert_bool(doc.has("raid")).is_false()
		_write(doc)
		assert_int(SaveGame.load_save(PATH)).is_equal(OK)
		assert_dict(SaveGame.data.raid).is_equal(SaveGame.fresh().raid)
	# a save made after the homecoming, before raids existed: nothing is sprung on load
	var after := {"version": 1, "zone": "crossroads", "flags": {"shard_home:woodland": true},
		"quests": {"home_again": {"state": "done", "step": 2}}}
	_write(after)
	assert_int(SaveGame.load_save(PATH)).is_equal(OK)
	assert_str(Raids.state()).is_equal("none")
	assert_bool(Raids.arrive("crossroads", "")).is_false()
	assert_str(Raids.state()).is_equal("none")
	# the next walk into town announces it, as for any save
	assert_bool(Raids.arrive("crossroads", "woodland")).is_true()

func test_the_raid_round_trips_through_the_save() -> void:
	_after_home_again()
	Raids.arrive("crossroads", "woodland")
	Raids.postpone()
	Raids.cycle_pad("pad_halt_gate")
	Raids.rec().repairs = true
	var before: Dictionary = SaveGame.data.raid.duplicate(true)
	assert_int(SaveGame.save(PATH)).is_equal(OK)
	SaveGame.reset()
	assert_int(SaveGame.load_save(PATH)).is_equal(OK)
	assert_dict(SaveGame.data.raid).is_equal(before)
	assert_int(typeof(SaveGame.data.raid.postponed)).is_equal(TYPE_INT)
	assert_str(Raids.state()).is_equal("postponed")

func test_a_malformed_raid_record_is_refused() -> void:
	for raid: Variant in [[], "none", {"state": 1}, {"postponed": -1}, {"postponed": 0.5}, {"wave": "1"},
			{"repairs": "yes"}, {"layout": []}, {"layout": {"pad": 1}}, {"id": null}]:
		assert_dict(SaveGame._migrate({"raid": raid})).is_empty()

# --- in the scene ------------------------------------------------------------------------------
func _attach() -> Player:
	var root: Node2D = auto_free(Node2D.new())
	add_child(root)
	var player: Player = auto_free(load("res://actors/player.tscn").instantiate())
	player.input_enabled = false
	Zones.current = null
	Zones.attach(root, player)
	return player

## Crossroads, walked into from the woodland after Home again: the raid announced, its night node there.
func _into_town() -> RaidNight:
	_after_home_again()
	_attach()
	assert_bool(Zones.go_to("woodland", "start")).is_true()
	assert_bool(Zones.go_to("crossroads", "woodland")).is_true()
	assert_str(Raids.state()).is_equal("announced")
	var night := Zones.current.get_node_or_null("RaidNight") as RaidNight
	assert_object(night).is_not_null()
	night.set_physics_process(false)
	return night

func _creatures(night: RaidNight) -> Array:
	return night.creatures()

func _free_all(night: RaidNight) -> int:
	var n := 0
	for c: RaidCreature in _creatures(night):
		c.set_physics_process(false)
		c.take_hit(99, Vector2.LEFT)
		n += 1
	return n

func test_the_night_stands_the_hurdles_and_three_waves_come_and_are_freed() -> void:
	var night := _into_town()
	assert_int(get_tree().get_nodes_in_group("raid_defence").size()).is_equal(0)   # nothing before the bell
	assert_bool(Raids.ring()).is_true()
	assert_int(night.barricades.size()).is_equal(2)
	for b: RaidBarricade in night.barricades:
		assert_bool(b.standing()).is_true()
		assert_int(b.collision_layer).is_equal(17)    # stops feet, not arrows
	assert_object(night.lantern).is_not_null()
	assert_int(night.lantern.hp).is_equal(12)
	var counts := []
	for w in 3:
		# the gap before the wave, then one creature a spawn_spacing
		for i in 12:
			night._physics_process(1.0)
		var wave := _creatures(night)
		counts.append(wave.size())
		assert_int(int(Raids.rec().wave)).is_equal(w)
		for c: RaidCreature in wave:
			assert_int(c.collision_mask).is_equal(1)
			assert_float(night.progress(c.global_position)).is_less(night.barricades[0].lane_s)
		assert_str(Raids.tracker_text()).contains("wave %d of 3" % (w + 1))
		var glint := int(SaveGame.data.glint)
		_free_all(night)
		assert_int(int(SaveGame.data.glint)).is_equal(glint)    # the creatures pay nothing; the purse does
		await get_tree().process_frame
	assert_array(counts).is_equal([2, 3, 3])
	night._physics_process(0.1)
	assert_str(Raids.state()).is_equal("won")
	assert_bool(night.is_over()).is_true()
	assert_int(int(SaveGame.data.glint)).is_equal(116 + int(GlintCache.balance().raids.first_night))
	# Hale offers the bell tower
	assert_str(" ".join(Dialogue.lines_for("hale"))).contains("bell")

func test_a_raider_marches_to_the_hurdle_and_batters_it_with_its_own_tell() -> void:
	var night := _into_town()
	Raids.ring()
	var hurdle: RaidBarricade = night.barricades[0]
	for b: RaidBarricade in night.barricades:
		if b.lane_s < hurdle.lane_s:
			hurdle = b
	var c: RaidCreature = auto_free(RaidCreature.new())
	c.role = "rusher"
	c.night = night
	c.slots = night.slots
	c.position = night.point_at(hurdle.lane_s - 200.0)
	night.camp.add_child(c)
	c.set_physics_process(false)
	c.step(0.05)                                                     # idle hands over to the march
	c.step(0.05)
	assert_str(c.state).is_equal("leash")                             # the march (the look walks in it)
	assert_float(c.velocity.x).is_greater(0.0)                       # east, towards the lantern
	c.global_position = night.point_at(hurdle.lane_s - 30.0)
	c.step(0.05)
	assert_str(c.state).is_equal("windup")
	assert_object(c.blocker).is_same(hurdle)
	c.step(c.windup_time() - 0.1)
	assert_int(hurdle.hp).is_equal(hurdle.max_hp)                    # nothing lands during the tell
	for i in 4:
		c.step(0.1)
	assert_int(hurdle.hp).is_equal(hurdle.max_hp - 1)
	# battered down: the body goes and the road is open
	hurdle.batter(hurdle.hp)
	assert_bool(hurdle.standing()).is_false()
	assert_int(hurdle.collision_layer).is_equal(0)
	for i in 10:
		c.step(0.1)
	assert_object(c.blocker).is_null()
	assert_str(c.state).is_equal("leash")
	# no villager is ever a target: only hurdles and the lantern block, and the player draws it off
	assert_bool(night.blocker_ahead(c, night.length()) == night.lantern).is_true()

func test_the_lantern_falls_the_night_is_lost_and_the_repairs_show_until_the_next_visit() -> void:
	var night := _into_town()
	Raids.ring()
	for i in 4:
		night._physics_process(1.0)
	assert_int(_creatures(night).size()).is_greater(0)
	night.lantern.batter(night.lantern.max_hp)
	assert_str(Raids.state()).is_equal("lost")
	assert_bool(night.is_over()).is_true()
	assert_int(_creatures(night).size()).is_equal(0)                  # they go back down the road
	assert_int(get_tree().get_nodes_in_group("raid_repair").size()).is_equal(2)
	assert_int(int(SaveGame.data.glint)).is_equal(116)
	# getting up in town keeps them; the next walk in clears them and offers the night again
	assert_bool(Zones.go_to("crossroads", "start")).is_true()
	await get_tree().process_frame
	assert_int(Zones.current.get_node("RaidNight").repairs.size()).is_equal(2)
	assert_bool(Zones.go_to("woodland", "crossroads")).is_true()
	assert_bool(Zones.go_to("crossroads", "woodland")).is_true()
	await get_tree().process_frame
	assert_int(Zones.current.get_node("RaidNight").repairs.size()).is_equal(0)
	assert_str(Raids.state()).is_equal("announced")

func test_walking_out_mid_night_leaves_it_pending() -> void:
	var night := _into_town()
	Raids.ring()
	night._physics_process(3.0)
	assert_bool(Zones.go_to("woodland", "crossroads")).is_true()
	assert_str(Raids.state()).is_equal("pending")
	assert_bool(Zones.go_to("crossroads", "woodland")).is_true()
	assert_str(Raids.state()).is_equal("announced")
	assert_int(Raids.postpones_left()).is_equal(2)

# --- the prepare screen ------------------------------------------------------------------------
func test_the_prepare_screen_is_untimed_touch_sized_and_rings_the_bell() -> void:
	_after_home_again()
	var player: Player = auto_free(load("res://actors/player.tscn").instantiate())
	add_child(player)
	var screen: RaidScreen = auto_free(RaidScreen.new())
	screen.player = player
	add_child(screen)
	screen.open()
	assert_bool(screen.is_open()).is_false()                          # nothing announced: nothing opens
	Raids.arrive("crossroads", "woodland")
	screen.open()
	await get_tree().process_frame
	assert_bool(screen.is_open()).is_true()
	assert_bool(player.input_enabled).is_false()                      # the player stands still behind it
	var targets := screen.targets()
	assert_int(targets.size()).is_equal(4)                            # ring, not tonight, two pads
	for b: Button in targets:
		var r := b.get_global_rect()
		assert_float(r.size.y).override_failure_message(b.name).is_greater_equal(UiStyle.TOUCH)
		assert_float(r.size.x).override_failure_message(b.name).is_greater_equal(UiStyle.TOUCH)
	# no timer: it is still waiting after a while
	for i in 10:
		await get_tree().process_frame
	assert_bool(screen.is_open()).is_true()
	assert_str(Raids.state()).is_equal("announced")
	# a pad tap cycles, and the first "not tonight" puts it off
	screen._on_pad("pad_halt_gate")
	assert_str(Raids.pad_kind("pad_halt_gate")).is_equal("")
	screen._on_pad("pad_halt_gate")
	screen._on_later()
	assert_bool(screen.is_open()).is_false()
	assert_bool(player.input_enabled).is_true()
	assert_str(Raids.state()).is_equal("postponed")
	# twice put off: no "not tonight" on the screen
	Raids.arrive("crossroads", "woodland")
	Raids.postpone()
	Raids.arrive("crossroads", "woodland")
	screen.open()
	await get_tree().process_frame
	assert_bool(screen._later.visible).is_false()
	screen._on_ring()
	assert_str(Raids.state()).is_equal("running")
	assert_bool(screen.is_open()).is_false()
