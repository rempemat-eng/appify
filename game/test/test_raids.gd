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
	assert_str(Raids.cycle_pad("pad_street_mouth")).is_equal("")
	assert_str(Raids.pad_kind("pad_street_mouth")).is_equal("")
	assert_str(Raids.cycle_pad("pad_street_mouth")).is_equal("hurdle_barricade")
	Raids.cycle_pad("pad_halt_street")
	assert_dict(Raids.rec().layout).is_equal({"pad_street_mouth": "hurdle_barricade", "pad_halt_street": ""})
	# without the forge there is no kind to choose, but the prefill stands
	SaveGame.data.village.restored.erase("forge")
	assert_array(Raids.kinds_owned()).is_empty()

func test_the_pads_and_the_lane_are_the_raids_own_data() -> void:
	var def: Dictionary = Raids.defs.first_night
	var lane := Raids.lane(def)
	assert_int(lane.size()).is_equal((def.lane_points as Array).size())
	# it starts where the plan's halt road does, at the zone's west edge
	assert_vector(lane[0]).is_equal(Vector2(0, 300))
	# both pads stand across the halt road (the one lane), in the street between the bakery and the
	# herbalist's (x 112 to 184), and each spans it wall to wall (y 288 to 336)
	var pads: Array = Raids.pads(def)
	assert_int(pads.size()).is_equal(2)
	for pad: Dictionary in pads:
		var at: Vector2 = pad.at
		assert_float(at.x).is_between(112.0 + 4.0, 184.0 - 4.0)
		assert_float(at.y - pad.span / 2.0).is_less_equal(288.0)
		assert_float(at.y + pad.span / 2.0).is_greater_equal(336.0)
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
	Raids.cycle_pad("pad_street_mouth")
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
	assert_bool(night.lantern.hurt()).is_false()          # unhurt: nothing is drawn over it
	var counts := []
	for w in 3:
		# the gap before the wave, then one creature a spawn_spacing
		for i in 30:     # wave 1 waits up to first_wave.or_after (the player is far from the square)
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
	# the lantern blocks only beside its plinth: at the lane's end, not from the well's side of the walk
	c.global_position = night.point_at(night.length())
	assert_object(night.blocker_ahead(c, night.length())).is_same(night.lantern)
	c.global_position = night.point_at(night.length() - 60.0)
	assert_object(night.blocker_ahead(c, night.length() - 60.0)).is_null()

func test_the_lantern_falls_the_night_is_lost_and_the_repairs_show_until_the_next_visit() -> void:
	var night := _into_town()
	Raids.ring()
	for i in 28:
		night._physics_process(1.0)
	assert_int(_creatures(night).size()).is_greater(0)
	night.lantern.batter(night.lantern.max_hp)
	assert_str(Raids.state()).is_equal("lost")
	assert_bool(night.is_over()).is_true()
	assert_int(_creatures(night).size()).is_equal(0)                  # they go back down the road
	assert_int(get_tree().get_nodes_in_group("raid_repair").size()).is_equal(2)
	assert_int(get_tree().get_nodes_in_group("raid_defence").size()).is_equal(0)   # the hurdles go with the night
	assert_object(night.lantern).is_null()                                          # and the lantern's lights
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
	screen._on_pad("pad_street_mouth")
	assert_str(Raids.pad_kind("pad_street_mouth")).is_equal("")
	screen._on_pad("pad_street_mouth")
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

# --- the audit of #483 ------------------------------------------------------------------------
## Crossroads loaded and in the tree after Home again, with the bell rung, and its solids in the physics space.
func _rung_town() -> RaidNight:
	var night := _into_town()
	Raids.ring()
	for i in 3:
		await get_tree().physics_frame
	return night

## B1: a hurdle closes the road. Across the lane at each hurdle, from the bakery's wall to the herbalist's,
## no creature-sized circle (r 12 texels, a creature's body) is free: nothing walks round it.
func test_no_creature_sized_gap_is_left_across_the_lane_at_either_hurdle() -> void:
	var night: RaidNight = await _rung_town()
	assert_int(night.barricades.size()).is_equal(2)
	var space := night.get_world_2d().direct_space_state
	var body := CircleShape2D.new()
	body.radius = 12.0
	var q := PhysicsShapeQueryParameters2D.new()
	q.shape = body
	q.collision_mask = 1
	for b: RaidBarricade in night.barricades:
		var free := []
		var y := (288.0 - 16.0) * 3.0
		while y <= (336.0 + 16.0) * 3.0:
			q.transform = Transform2D(0.0, Vector2(b.global_position.x, y))
			if space.intersect_shape(q, 1).is_empty():
				free.append(int(y / 3.0))
			y += 3.0
		assert_array(free).override_failure_message("%s: a creature fits at y %s (world px)" % [b.name, free]).is_empty()
	# broken, it opens the road
	var first: RaidBarricade = night.barricades[0]
	first.batter(first.hp)
	await get_tree().physics_frame
	q.transform = Transform2D(0.0, Vector2(first.global_position.x, 312.0 * 3.0))
	assert_bool(space.intersect_shape(q, 1).is_empty()).is_true()

## Matt, 13 Nov ("why does the lantern have a health bar?"): the lantern shows nothing until it is struck;
## then a row of lights, one for two health, in the HUD's meter style, and the same row in the tracker from
## the bell. A blow darkens its glass for FLICKER seconds: a flicker, or one steady dark under reduced motion.
func test_the_lantern_shows_its_health_only_once_struck_and_each_blow_shows_on_it() -> void:
	var night: RaidNight = await _rung_town()
	var lamp := night.lantern
	assert_bool(lamp.hurt()).is_false()
	assert_bool(lamp.is_processing()).is_false()                       # nothing runs while nothing happens
	assert_array(RaidLantern.lights(12, 12)).is_equal(["full", "full", "full", "full", "full", "full"])
	assert_array(RaidLantern.lights(11, 12)).is_equal(["full", "full", "full", "full", "full", "half"])
	assert_array(RaidLantern.lights(4, 12)).is_equal(["full", "full", "empty", "empty", "empty", "empty"])
	assert_array(RaidLantern.lights(0, 12)).is_equal(["empty", "empty", "empty", "empty", "empty", "empty"])
	# its lights are pictures that exist, as the hearts are
	for state: String in ["full", "half", "empty"]:
		assert_bool(ResourceLoader.exists("res://ui/art/shard_%s.png" % state)).is_true()
	lamp.batter(1)
	assert_bool(lamp.hurt()).is_true()
	assert_int(lamp.hp).is_equal(11)                                   # the number is the data's own
	assert_bool(lamp.is_processing()).is_true()
	# the blow: dark, back, dark, back; then nothing. Under reduced motion one steady dark, no flicker
	assert_float(RaidLantern.dim(RaidLantern.FLICKER, false)).is_equal(1.0)
	assert_float(RaidLantern.dim(RaidLantern.FLICKER * 0.6, false)).is_equal(0.0)
	assert_float(RaidLantern.dim(RaidLantern.FLICKER * 0.4, false)).is_equal(1.0)
	assert_float(RaidLantern.dim(RaidLantern.FLICKER * 0.1, false)).is_equal(0.0)
	assert_float(RaidLantern.dim(0.0, false)).is_equal(0.0)
	for left: float in [RaidLantern.FLICKER, RaidLantern.FLICKER * 0.6, RaidLantern.FLICKER * 0.1]:
		assert_float(RaidLantern.dim(left, true)).is_equal(1.0)
	assert_float(RaidLantern.dim(0.0, true)).is_equal(0.0)
	lamp._process(RaidLantern.FLICKER + RaidLantern.SWELL + 0.1)
	assert_bool(lamp.is_processing()).is_false()                       # finite: it stops by itself
	# each wave's coming swells its light once
	lamp.swell()
	assert_bool(lamp.is_processing()).is_true()
	lamp._process(RaidLantern.SWELL + 0.1)
	assert_bool(lamp.is_processing()).is_false()
	# the tracker names it and shows the same lights from the bell on
	assert_str(Raids.tracker_text()).contains("Hold the shard lantern")
	var hud: Control = auto_free(load("res://ui/hud.gd").new())
	add_child(hud)
	assert_str(hud.shown_text().lantern).is_equal("")                  # no raid's row until the HUD is told of one
	hud._show_lantern(lamp)
	assert_str(hud.shown_text().lantern).is_equal("11/12")
	hud._show_lantern(null)
	assert_str(hud.shown_text().lantern).is_equal("")
	# the glass the blow darkens lies inside the lit lantern's picture, over its housing
	var pic := load("res://zones/crossroads/art/lantern_lit.png") as Texture2D
	assert_float(-RaidLantern.GLASS.position.y).is_less(float(pic.get_height()))
	assert_float(RaidLantern.PIPS_ABOVE).is_greater(-RaidLantern.GLASS.position.y)

## Matt, 13 Nov ("what are those brown things on the track?"): the hurdles are pictures, one run from wall to
## wall, standing, battered from half health, then broken and flat on the road. No number of theirs changed.
func test_the_hurdles_are_drawn_from_their_pictures_in_three_states() -> void:
	var night: RaidNight = await _rung_town()
	var sheet := RaidBarricade.sheet()
	assert_int(int(sheet.span)).is_equal(48)
	for b: RaidBarricade in night.barricades:
		assert_bool(b.pictured()).is_true()
		assert_int(b.max_hp).is_equal(10)
		assert_vector((b.get_node("Shape") as CollisionShape2D).shape.size).is_equal(Vector2(18, 144))   # 6 x 48 world px
		assert_str(b.look()).is_equal("standing")
	for state: String in ["standing", "battered", "broken"]:
		var st: Dictionary = sheet.states[state]
		var tex := load(RaidBarricade.ART + String(st.png)) as Texture2D
		assert_object(tex).is_not_null()
		assert_vector(Vector2(tex.get_size())).is_equal(Vector2(float(sheet.frame[0]), float(sheet.frame[1])))
	var b0: RaidBarricade = night.barricades[0]
	# its ground line runs from wall to wall: the pad's whole span
	var ground: Array = sheet.states.standing.ground
	assert_float(float(ground[0][1])).is_equal(-72.0)
	assert_float(float(ground[ground.size() - 1][1])).is_equal(72.0)
	b0.batter(4)
	assert_str(b0.look()).is_equal("standing")
	b0.batter(1)
	assert_str(b0.look()).is_equal("battered")                      # from half its health down
	b0.batter(4)
	assert_str(b0.look()).is_equal("battered")
	b0.batter(1)
	assert_str(b0.look()).is_equal("broken")
	assert_int(b0.z_index).is_equal(-8)                              # the wreckage lies under everyone
	assert_bool(b0.z_as_relative).is_false()

## B2: the lane goes round the well, not through it: no point of it lies inside a solid, and its end stands
## beside the lantern's post, within the reach a raider strikes from.
func test_no_point_of_the_lane_lies_inside_a_solid_and_it_ends_beside_the_lantern() -> void:
	var night: RaidNight = await _rung_town()
	for b: RaidBarricade in night.barricades:
		b.batter(b.hp)                      # the hurdles stand on the lane by design; the rest must not
	await get_tree().physics_frame
	var space := night.get_world_2d().direct_space_state
	var q := PhysicsPointQueryParameters2D.new()
	q.collision_mask = 1
	var inside := []
	var s := 0.0
	while s <= night.length():
		q.position = night.point_at(s)
		for hit: Dictionary in space.intersect_point(q, 4):
			inside.append("%s at %s" % [(hit.collider as Node).name, (q.position / 3.0).round()])
		s += 3.0
	assert_array(inside).is_empty()
	var end := night.point_at(night.length())
	assert_float(night.lantern_distance(end)).is_less_equal(night.lantern_reach())
	assert_float(night.lantern_distance(end)).is_greater(0.0)

func test_a_night_lost_by_going_down_is_told_on_getting_up() -> void:
	var night := _into_town()
	Raids.ring()
	Raids.player_downed()
	assert_str(Raids.loss_untold).is_equal("down")
	assert_bool(Zones.go_to("crossroads", "start")).is_true()          # as game.gd does on getting up
	assert_str(Raids.loss_untold).is_equal("")
	assert_str(Raids.state()).is_equal("lost")
	assert_object(night).is_not_null()
	# a night lost at the lantern is told there and then, so nothing is left to tell on a reload
	Raids.loss_untold = ""
	assert_bool(Zones.go_to("crossroads", "start")).is_true()
	assert_str(Raids.loss_untold).is_equal("")

func test_a_won_night_clears_away_and_sets_out_the_bell_towers_mark() -> void:
	SaveGame.data.settings.reduced_motion = true
	var night := _into_town()
	Raids.ring()
	night.set_physics_process(false)
	for w in 3:
		for i in 30:     # wave 1 waits up to first_wave.or_after (the player is far from the square)
			night._physics_process(1.0)
		_free_all(night)
		await get_tree().process_frame
	night._physics_process(0.1)
	assert_str(Raids.state()).is_equal("won")
	await get_tree().process_frame
	assert_int(get_tree().get_nodes_in_group("raid_defence").size()).is_equal(0)
	assert_object(night.lantern).is_null()
	var site := Zones.current.get_node_or_null("Actors/BellTowerSite") as RestoreSite
	assert_object(site).is_not_null()
	assert_str(site.restore_id).is_equal("bell_tower")
	assert_bool(site.visible).is_true()
	# paid at the mark, as every restore: 50 Glint
	var before := int(SaveGame.data.glint)
	await site.interact()
	assert_bool(Village.is_restored("bell_tower")).is_true()
	assert_int(int(SaveGame.data.glint)).is_equal(before - 50)
	# not set out again once restored
	assert_bool(Zones.go_to("crossroads", "start")).is_true()
	assert_object(Zones.current.get_node_or_null("Actors/BellTowerSite")).is_null()

func test_an_unknown_raid_state_in_a_save_starts_afresh() -> void:
	var doc := {"raid": {"id": "first_night", "state": "bogus", "postponed": 1}}
	var out: Dictionary = SaveGame._migrate(doc)
	assert_str(String(out.raid.state)).is_equal("none")
	for st: String in Raids.STATES:
		assert_str(String(SaveGame._migrate({"raid": {"state": st}}).raid.state)).is_equal(st)
	assert_array(SaveGame.RAID_STATES).is_equal(Raids.STATES)

func test_the_screen_says_what_stands_on_the_pads() -> void:
	_after_home_again()
	Raids.arrive("crossroads", "woodland")
	var def := Raids.current()
	assert_str(RaidScreen._pads_sentence(def)).contains("both pads")
	Raids.cycle_pad("pad_street_mouth")
	assert_str(RaidScreen._pads_sentence(def)).contains("pad 2 is empty")
	Raids.cycle_pad("pad_halt_street")
	assert_str(RaidScreen._pads_sentence(def)).contains("Both pads are empty")
	# Hale's line before the night holds whatever the layout
	assert_str(" ".join(Dialogue.lines_for("hale"))).not_contains("on both pads")

func test_moss_never_talks_of_the_raid_while_one_of_her_quests_could_start() -> void:
	_after_home_again()
	Raids.arrive("crossroads", "woodland")
	Raids.postpone()
	assert_str(" ".join(Dialogue.lines_for("moss"))).contains("halt road")
	# the Frostline in the build: her brief for the Col hut, which starts on talking to her, comes first
	var entry: Dictionary = Dialogue.speakers.moss.entries[0]
	assert_array(entry.get("if", {}).get("not_flags", [])).contains(["zone_built:frostline"])

# --- the audit of #483, round 2 ------------------------------------------------------------------
## R2-2: wave 1 waits for the player to come near the square (or a while), so the hurdles can be held.
func test_the_first_wave_waits_for_the_player_at_the_square() -> void:
	var night := _into_town()
	var square := night.near_place()
	assert_bool(square.has_area()).is_true()
	var centre := square.get_center() * 3.0
	var far := Vector2(30, 70) * 3.0                                   # the garden walk, where the bell is rung
	var fw: Dictionary = Raids.defs.first_night.first_wave
	assert_bool(night.first_wave_due(float(fw.at_least) - 0.1, centre)).is_false()   # never at once
	assert_bool(night.first_wave_due(float(fw.at_least), centre)).is_true()
	assert_bool(night.first_wave_due(10.0, far)).is_false()
	assert_bool(night.first_wave_due(float(fw.or_after), far)).is_true()   # not for ever
	var within := float(fw.within)
	assert_bool(night.first_wave_due(5.0, (square.position + Vector2(-(within - 5.0), 20)) * 3.0)).is_true()
	assert_bool(night.first_wave_due(5.0, (square.position + Vector2(-(within + 5.0), 20)) * 3.0)).is_false()
	# in the scene: the bell rung on the garden walk, nothing comes until the player walks to the square
	Raids.ring()
	for i in 10:
		night._physics_process(1.0)
	assert_int(night.wave).is_equal(-1)
	assert_int(night.creatures().size()).is_equal(0)
	Zones.player.global_position = centre
	night._physics_process(0.1)
	assert_int(night.wave).is_equal(0)

## R2-1, the game's side: a real arrow, shot from the street as a player shoots it, frees a toad backed
## against the bakery's south wall (its body is a circle at its feet; the arrow's node flies on the ground).
func test_a_real_arrow_hits_a_toad_pressed_against_the_bakery_wall() -> void:
	var night: RaidNight = await _rung_town()
	for b: RaidBarricade in night.barricades:
		b.batter(b.hp)
	var toad := RaidCreature.new()
	toad.role = "shooter"
	toad.night = night
	toad.slots = night.slots
	toad.position = Vector2(135.0 * 3.0, 288.0 * 3.0 + 12.0)          # touching the bakery's wall face
	night.camp.add_child(toad)
	toad.set_physics_process(false)
	await get_tree().physics_frame
	var hp := toad.hp
	for from: Vector2 in [Vector2(135, 326) * 3.0, Vector2(160, 320) * 3.0, Vector2(110, 318) * 3.0]:
		var archer := Node2D.new()
		Zones.current.actors.add_child(archer)
		archer.global_position = from
		var arrow := Arrow.new()
		Zones.current.actors.add_child(arrow)
		# the player's own shot: from the bow at chest height, along the aim from the chest to the target's
		arrow.setup(from, 30.0, (toad.global_position + Vector2(0, -24)) - (from + Vector2(0, -24)), archer)
		for i in 30:
			await get_tree().physics_frame
		archer.queue_free()
	assert_int(toad.hp).override_failure_message("a toad against the wall took no arrow").is_less_equal(hp - 3)
	# and the line the pilot tests (feet to feet) is clear from there, where the old one (24 texels up) was not
	var space := night.get_world_2d().direct_space_state
	assert_bool(Arrow.walled_off(space, Vector2(135, 326) * 3.0, toad.global_position)).is_false()
	assert_bool(Arrow.walled_off(space, Vector2(135, 326) * 3.0, toad.global_position + Vector2(0, -24))).is_true()
	toad.queue_free()

## P1 and B2 together: a creature's whole body fits along the lane (not only its centre), from the halt road
## to the strike spot, which stands in front of the well's picture.
func test_a_creatures_body_fits_along_the_whole_lane() -> void:
	var night: RaidNight = await _rung_town()
	for b: RaidBarricade in night.barricades:
		b.batter(b.hp)
	await get_tree().physics_frame
	var space := night.get_world_2d().direct_space_state
	var body := CircleShape2D.new()
	body.radius = 12.0
	var q := PhysicsShapeQueryParameters2D.new()
	q.shape = body
	q.collision_mask = 1
	var blocked := []
	var s := RaidNight.SPAWN_IN * 3.0                                  # from where the creatures appear
	while s <= night.length():
		q.transform = Transform2D(0.0, night.point_at(s))
		for hit: Dictionary in space.intersect_shape(q, 4):
			blocked.append("%s at %s" % [(hit.collider as Node).name, (night.point_at(s) / 3.0).round()])
		s += 3.0
	assert_array(blocked).is_empty()
	# the strike spot sorts in front of the well and the lantern (both pictures' feet are at y 320), is clear
	# of the well's picture (x 269 to 307) and stands west of the lantern's plinth (x 344 to 360), so the
	# raider is seen whole from the square, never behind the well's frame or the lantern
	var end := night.point_at(night.length()) / 3.0
	var plinth := night.lantern_box()
	assert_float(end.y).is_greater(320.0)
	assert_float(end.y * 3.0).is_greater(plinth.end.y)
	assert_float(end.x).is_greater(307.0)
	assert_float(end.x * 3.0).is_less(plinth.position.x)
