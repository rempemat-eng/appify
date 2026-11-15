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
	assert_int(Raids.win()).is_equal(0)                                # not before the anvil
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

func test_a_loss_costs_brief_repairs_that_stay_while_the_lantern_is_dark_and_the_raid_comes_again() -> void:
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
	assert_bool(bool(Raids.rec().repairs)).is_true()                   # the square looks worse until a night is held
	assert_str(Raids.state()).is_equal("announced")
	assert_int(Raids.postpones_left()).is_equal(2)                     # a lost night is offered again afresh
	# a raid with no stake of its own keeps the older rule: mended on the next walk in
	SaveGame.set_flag("shard_lantern_dark", false)
	Raids.postpone()
	assert_bool(Raids.arrive("crossroads", "woodland")).is_true()
	assert_bool(bool(Raids.rec().repairs)).is_false()

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
	assert_int(get_tree().get_nodes_in_group("raid_defence").size()).is_equal(0)   # nothing before the anvil
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
	# Hale says it was the one night (Matt, 13 Nov: a one-off): no next lot, no bell
	var says := " ".join(Dialogue.lines_for("hale"))
	assert_str(says).contains("the one night")
	assert_str(says).contains("not come for it again")
	assert_str(says.to_lower()).not_contains("bell")
	assert_str(says.to_lower()).not_contains("next")

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

func test_the_lantern_falls_the_night_is_lost_and_the_repairs_show_until_a_night_is_held() -> void:
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
	await get_tree().process_frame
	assert_bool(_handcart_shown()).is_false()                                       # its wreck lies on the square instead
	assert_int(get_tree().get_nodes_in_group("raid_defence").size()).is_equal(0)   # the hurdles go with the night
	assert_object(night.lantern).is_null()                                          # and the lantern's lights
	assert_int(int(SaveGame.data.glint)).is_equal(116)
	# getting up in town keeps them; the next walk in offers the night again, and they stay: the square looks
	# worse for as long as the lantern is dark (Matt, 13 Nov)
	assert_bool(Zones.go_to("crossroads", "start")).is_true()
	await get_tree().process_frame
	assert_int(Zones.current.get_node("RaidNight").repairs.size()).is_equal(2)
	assert_bool(Zones.go_to("woodland", "crossroads")).is_true()
	assert_bool(Zones.go_to("crossroads", "woodland")).is_true()
	await get_tree().process_frame
	assert_int(Zones.current.get_node("RaidNight").repairs.size()).is_equal(2)
	assert_bool(_handcart_shown()).is_false()
	assert_bool(bool(Raids.rec().repairs)).is_true()
	assert_str(Raids.state()).is_equal("announced")
	# the boards on the wall have no body; the overturned cart's bed is solid where the data says
	# (test_with_the_repairs_showing_the_lane_and_every_walk_stay_open holds that nothing is shut by it)
	for r: Node2D in Zones.current.get_node("RaidNight").repairs:
		var bodies := r.find_children("*", "CollisionObject2D", true, false)
		assert_bool(r is CollisionObject2D).is_false()
		assert_int(bodies.size()).is_equal(1 if (r as RaidRepair).spec.has("solid") else 0)
	# a night held mends them, at once and for good
	night = Zones.current.get_node("RaidNight") as RaidNight
	assert_bool(Raids.ring()).is_true()
	assert_int(night.repairs.size()).is_equal(2)                                    # through the second night
	await _hold_the_night(night)
	assert_str(Raids.state()).is_equal("won")
	assert_bool(bool(Raids.rec().repairs)).is_false()
	await get_tree().process_frame
	assert_int(get_tree().get_nodes_in_group("raid_repair").filter(func(n: Node) -> bool: return not n.is_queued_for_deletion()).size()).is_equal(0)
	await get_tree().process_frame
	assert_bool(_handcart_shown()).is_true()                                        # the handcart is back with the mending
	assert_bool(Zones.go_to("crossroads", "start")).is_true()
	await get_tree().process_frame
	assert_int(Zones.current.get_node("RaidNight").repairs.size()).is_equal(0)
	assert_bool(_handcart_shown()).is_true()

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
func test_the_prepare_screen_is_untimed_touch_sized_and_sounds_the_anvil() -> void:
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
	assert_int(targets.size()).is_equal(4)                            # the anvil, not tonight, two pads
	# night one is called by Hale's anvil (Matt, 13 Nov): no word on the screen says bell
	assert_str(screen._ring.text).is_equal("Sound the anvil")
	assert_str(screen._text.text).contains("Hale strikes her anvil")
	for word: String in [screen._ring.text, screen._text.text, screen._sub.text, screen._later.text]:
		assert_str(word.to_lower()).not_contains("bell")
	assert_str(screen._text.text).contains("stays dark until a night is held")   # the stake, said before the night
	assert_str(screen._text.text).not_contains("has been dark")                  # and nothing of a loss before one
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
	# opened again in the same session, the pads' buttons keep their names (the play driver presses them by name)
	var names := screen.targets().map(func(b: Button) -> String: return String(b.name))
	assert_array(names).contains(["Pad_pad_halt_street", "Pad_pad_street_mouth", "SoundTheAnvil"])
	screen._on_ring()
	assert_str(Raids.state()).is_equal("running")
	assert_bool(screen.is_open()).is_false()

# --- the audit of #483 ------------------------------------------------------------------------
## Crossroads loaded and in the tree after Home again, with the anvil sounded, and its solids in the physics space.
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
## the anvil. A blow darkens its glass for FLICKER seconds: a flicker, or one steady dark under reduced motion.
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
	# each wave's coming pools its light once on the setts: rings from the foot outwards, then gone the
	# same way, in whole steps; under reduced motion the whole pool, still, for as long
	lamp.swell()
	assert_bool(lamp.is_processing()).is_true()
	var outer := RaidLantern.POOL.size() - 1
	assert_array(RaidLantern.rings(RaidLantern.SWELL, false)).is_equal([outer])
	assert_array(RaidLantern.rings(RaidLantern.SWELL * 0.5, false)).is_equal([0, 1, 2])
	assert_array(RaidLantern.rings(RaidLantern.SWELL * 0.05, false)).is_equal([0])
	assert_array(RaidLantern.rings(0.0, false)).is_empty()
	assert_array(RaidLantern.rings(RaidLantern.SWELL * 0.5, true)).is_equal([0, 1, 2])
	assert_array(RaidLantern.rings(RaidLantern.SWELL * 0.05, true)).is_equal([0, 1, 2])
	assert_array(RaidLantern.rings(0.0, true)).is_empty()
	lamp._process(RaidLantern.SWELL + 0.1)
	assert_bool(lamp.is_processing()).is_false()
	# the tracker names it and shows the same lights from the anvil on
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
	# ... and follows the arched head: full height under the crown, ARCH texels lower at the posts, so the
	# dark never lies over the iron of the head's corners
	var shape := RaidLantern.pane()
	var mid := RaidLantern.GLASS.get_center().x
	assert_bool(Geometry2D.is_point_in_polygon(Vector2(mid - 0.5, RaidLantern.GLASS.position.y + 1.5), shape)).is_true()
	for side: float in [RaidLantern.GLASS.position.x + 0.5, RaidLantern.GLASS.end.x - 0.5]:
		assert_bool(Geometry2D.is_point_in_polygon(Vector2(side, RaidLantern.GLASS.position.y + RaidLantern.ARCH - 1.5), shape)).is_false()
		assert_bool(Geometry2D.is_point_in_polygon(Vector2(side, RaidLantern.GLASS.position.y + RaidLantern.ARCH + 1.5), shape)).is_true()
		assert_bool(Geometry2D.is_point_in_polygon(Vector2(side, RaidLantern.GLASS.end.y - 0.5), shape)).is_true()
	assert_bool(Geometry2D.triangulate_polygon(shape).is_empty()).is_false()      # a shape Godot can fill
	# the dark pane has a canvas item of its own, under the lights and over the lantern's picture: the lights
	# are textures, and a texture drawn after a polygon by one item comes out blank in the real game
	var glass := lamp.get_node("Glass") as Node2D
	assert_object(glass).is_not_null()
	assert_bool(glass.show_behind_parent).is_true()
	assert_bool(glass.z_as_relative).is_true()
	assert_int(glass.z_index).is_equal(0)

## One light is two health, not two blows: with the data's own damage (first_night.json: a raider's blow 1,
## the elite's 2) the elite's blow empties one whole light, and a raider's blow after it leaves a half light.
func test_the_elites_blow_empties_a_whole_light_and_a_raiders_half_of_one() -> void:
	var night: RaidNight = await _rung_town()
	var lamp := night.lantern
	assert_int(lamp.max_hp).is_equal(12)                               # the data's own numbers, unchanged
	assert_int(night.batter_damage("rusher")).is_equal(1)
	assert_int(night.batter_damage("elite")).is_equal(2)
	assert_int(RaidLantern.lights(lamp.hp, lamp.max_hp).size()).is_equal(6)
	lamp.batter(night.batter_damage("elite"))
	assert_int(lamp.hp).is_equal(10)
	assert_array(RaidLantern.lights(lamp.hp, lamp.max_hp)).is_equal(["full", "full", "full", "full", "full", "empty"])
	lamp.batter(night.batter_damage("rusher"))
	assert_int(lamp.hp).is_equal(9)
	assert_array(RaidLantern.lights(lamp.hp, lamp.max_hp)).is_equal(["full", "full", "full", "full", "half", "empty"])
	# the tracker's row is the same row
	var hud: Control = auto_free(load("res://ui/hud.gd").new())
	add_child(hud)
	hud._show_lantern(lamp)
	assert_str(hud.shown_text().lantern).is_equal("9/12")

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
		# the picture is a child sprite over the node's own shadow drawing (drawn in _draw after the shadow's
		# polygons it came out a blank white frame in the real game), its foot on the pad
		var pic := b.get_node("Picture") as Sprite2D
		assert_object(pic).is_not_null()
		assert_bool(pic.centered).is_false()
		assert_vector(pic.position).is_equal(-Vector2(float(sheet.foot[0]), float(sheet.foot[1])))
		assert_bool(pic.show_behind_parent).is_false()
		assert_int(pic.z_index).is_equal(0)
		assert_bool(pic.z_as_relative).is_true()                      # it sorts and sinks with its hurdle
		assert_str(pic.texture.resource_path).is_equal(RaidBarricade.ART + String(sheet.states.standing.png))
	for state: String in ["standing", "battered", "broken"]:
		var st: Dictionary = sheet.states[state]
		var tex := load(RaidBarricade.ART + String(st.png)) as Texture2D
		assert_object(tex).is_not_null()
		assert_vector(Vector2(tex.get_size())).is_equal(Vector2(float(sheet.frame[0]), float(sheet.frame[1])))
	var b0: RaidBarricade = night.barricades[0]
	var pic0 := b0.get_node("Picture") as Sprite2D
	# its ground line runs from wall to wall: the pad's whole span
	var ground: Array = sheet.states.standing.ground
	assert_float(float(ground[0][1])).is_equal(-72.0)
	assert_float(float(ground[ground.size() - 1][1])).is_equal(72.0)
	b0.batter(4)
	assert_str(b0.look()).is_equal("standing")
	assert_str(pic0.texture.resource_path).is_equal(RaidBarricade.ART + String(sheet.states.standing.png))
	assert_object(pic0.modulate).is_equal(RaidBarricade.HIT_LIT)    # struck: a step lit, a colour and no movement
	b0._process(RaidBarricade.HIT_TINT + 0.01)
	assert_object(pic0.modulate).is_equal(Color.WHITE)
	b0.batter(1)
	assert_str(b0.look()).is_equal("battered")                      # from half its health down
	assert_str(pic0.texture.resource_path).is_equal(RaidBarricade.ART + String(sheet.states.battered.png))
	b0.batter(4)
	assert_str(b0.look()).is_equal("battered")
	b0.batter(1)
	assert_str(b0.look()).is_equal("broken")
	assert_str(pic0.texture.resource_path).is_equal(RaidBarricade.ART + String(sheet.states.broken.png))
	assert_int(b0.z_index).is_equal(-8)                              # the wreckage lies under everyone
	assert_bool(b0.z_as_relative).is_false()

## The night's lantern is gone from the raid the moment the night ends, as the hurdles are, even while its
## lights fade (0.6 s without reduced motion): nothing that asks for the raid's lantern finds a fading one.
func test_the_lantern_is_no_longer_the_raids_once_the_night_ends_while_it_fades() -> void:
	SaveGame.data.settings.reduced_motion = false
	var night: RaidNight = await _rung_town()
	var lamp := night.lantern
	assert_object(get_tree().get_first_node_in_group("raid_lantern")).is_same(lamp)
	night._end(true)
	assert_str(Raids.state()).is_equal("won")
	assert_bool(is_instance_valid(lamp) and lamp.is_inside_tree()).is_true()   # still fading out
	assert_object(get_tree().get_first_node_in_group("raid_lantern")).is_null()
	assert_int(get_tree().get_nodes_in_group("raid_defence").size()).is_equal(0)
	assert_object(night.lantern).is_null()

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
	var far := Vector2(30, 70) * 3.0                                   # the garden walk, where the anvil is sounded
	var fw: Dictionary = Raids.defs.first_night.first_wave
	assert_bool(night.first_wave_due(float(fw.at_least) - 0.1, centre)).is_false()   # never at once
	assert_bool(night.first_wave_due(float(fw.at_least), centre)).is_true()
	assert_bool(night.first_wave_due(10.0, far)).is_false()
	assert_bool(night.first_wave_due(float(fw.or_after), far)).is_true()   # not for ever
	var within := float(fw.within)
	assert_bool(night.first_wave_due(5.0, (square.position + Vector2(-(within - 5.0), 20)) * 3.0)).is_true()
	assert_bool(night.first_wave_due(5.0, (square.position + Vector2(-(within + 5.0), 20)) * 3.0)).is_false()
	# in the scene: the anvil sounded on the garden walk, nothing comes until the player walks to the square
	Raids.ring()
	for i in 10:
		night._physics_process(1.0)
	assert_int(night.wave).is_equal(-1)
	assert_int(night.creatures().size()).is_equal(0)
	# the tracker does not count a wave that has not come (#483 polish): it says they are coming
	assert_str(Raids.tracker_text()).contains("the shardstruck are coming")
	assert_str(Raids.tracker_text()).not_contains("wave 1")
	Zones.player.global_position = centre
	night._physics_process(0.1)
	assert_int(night.wave).is_equal(0)
	assert_str(Raids.tracker_text()).contains("wave 1 of 3")

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

## The square's upright handcart (its picture, its shadow and its body, in the zone's Conditionals): hidden for
## exactly as long as its wreck, the repair `cart_on_its_side`, shows.
func _handcart_shown() -> bool:
	var cart := Zones.current.get_node("Props/If_handcart") as Conditional
	var shade := Zones.current.get_node("Props/If_handcart_shadow") as Conditional
	assert_bool(cart.visible).is_equal(shade.visible)
	assert_object(cart.find_child("*Body*", true, false)).is_not_null()
	return cart.visible and cart.process_mode != Node.PROCESS_MODE_DISABLED

## The drawn repairs after a lost night (world/raid_repair.gd, the pictures from scripts/art/native/town.py):
## each shows its picture where kit.json puts it; the boards on the smithy's wall have no body; the
## wrecked cart's bed is a solid on the walls' layer (it stands above LOW_RISE, so by the zone's own rule it
## stops shots as well as feet), its rectangle the data's `solid`. With them showing a creature's whole body still fits along the lane, and every talk
## area, open door and spawn of the square can still be walked to from `start` (test_reach.gd's bar).
func test_with_the_repairs_showing_the_lane_and_every_walk_stay_open() -> void:
	_after_home_again()
	SaveGame.set_flag("shard_lantern_dark")
	SaveGame.data.raid = {"id": "first_night", "state": "lost", "postponed": 0, "wave": 0, "layout": {}, "repairs": true}
	_attach()
	assert_bool(Zones.go_to("crossroads", "start")).is_true()
	await get_tree().process_frame
	var night := Zones.current.get_node("RaidNight") as RaidNight
	night.set_physics_process(false)
	assert_int(night.repairs.size()).is_equal(2)
	await get_tree().process_frame
	assert_bool(_handcart_shown()).is_false()
	for r: Node2D in night.repairs:
		var spec: Dictionary = (r as RaidRepair).spec
		var pic := r.get_node("Picture") as Sprite2D
		assert_str(pic.texture.resource_path).is_equal(String(spec.picture))
		var bodies := r.find_children("*", "StaticBody2D", true, false)
		if not spec.has("solid"):
			assert_array(bodies).is_empty()
			assert_object(r.get_node_or_null("Shadow")).is_null()
			continue
		assert_object(r.get_node_or_null("Shadow")).is_not_null()
		assert_int(bodies.size()).is_equal(1)
		var body := bodies[0] as StaticBody2D
		# the wreck's raised bed and shafts stand above LOW_RISE (tools/gen_physics.py): its bed stops shots too
		var stands := int(RaidRepair.kit_entry(String(spec.picture), String(spec.id)).stands)
		assert_int(stands).is_greater_equal(RaidRepair.LOW_RISE)
		assert_int(body.collision_layer).is_equal(1)
		var cs := body.get_child(0) as CollisionShape2D
		var half := (cs.shape as RectangleShape2D).size / 2.0
		var solid: Array = spec.solid
		assert_vector((cs.global_position - half) / 3.0).is_equal_approx(Vector2(solid[0], solid[1]), Vector2(0.01, 0.01))
		assert_vector(half * 2.0 / 3.0).is_equal_approx(Vector2(solid[2], solid[3]), Vector2(0.01, 0.01))
	await get_tree().physics_frame
	await get_tree().physics_frame
	# the lane, a creature's whole body along it
	var space := night.get_world_2d().direct_space_state
	var q := PhysicsShapeQueryParameters2D.new()
	var round_body := CircleShape2D.new()
	round_body.radius = 12.0
	q.shape = round_body
	q.collision_mask = 1
	var blocked := []
	var s := RaidNight.SPAWN_IN * 3.0
	while s <= night.length():
		q.transform = Transform2D(0.0, night.point_at(s))
		for hit: Dictionary in space.intersect_shape(q, 4):
			blocked.append("%s at %s" % [(hit.collider as Node).name, (night.point_at(s) / 3.0).round()])
		s += 3.0
	assert_array(blocked).is_empty()
	# every walk: the spawns, the open doors and the talk areas from `start`
	const WalkGrid := preload("res://tools/walk_grid.gd")
	var zone: Zone = Zones.current
	var grid := WalkGrid.new(zone.get_world_2d(), zone.bounds, 0.0)
	var cells: Dictionary = grid.reachable(zone.spawn_position("start"))
	var problems := []
	for n: Node in zone.find_children("*", "", true, false):
		if not (n is Marker2D or n is Area2D) or not n.can_process() or not (n as CanvasItem).is_visible_in_tree():
			continue
		if n is Marker2D and n.get_parent().name == "Spawns":
			if not cells.has(grid.nearest_free((n as Node2D).global_position, 12.0)):
				problems.append("%s: the spawn is walled off from `start`" % n.name)
		elif (n is Door and (n as Door).is_open()) or n is Interactable:
			var area := n as Area2D
			var shape := area.get_node("Shape") as CollisionShape2D
			var radius := (area as Interactable).reach() if area is Interactable else 0.0
			var count := 0
			for c: Vector2i in cells:
				var at: Vector2 = WalkGrid.point_of(c) + WalkGrid.BODY_OFFSET
				if area is Interactable:
					count += int(at.distance_to(area.global_position) < radius + WalkGrid.BODY_RADIUS - 1.0)
				elif shape.shape is RectangleShape2D:
					var h := (shape.shape as RectangleShape2D).size / 2.0 + Vector2.ONE * (WalkGrid.BODY_RADIUS - 1.0)
					var d := (at - shape.global_position).abs()
					count += int(d.x < h.x and d.y < h.y)
			if count < (150 if area is Interactable else 1):
				problems.append("%s: in reach from %d walkable cells" % [n.name, count])
	assert_array(problems).is_empty()

# --- Matt's decisions of 13 Nov: the stake, the anvil, a one-off ---------------------------------
## What a loss must leave alone: the Glint, the quests, the restores and every flag but the stake's own.
func _kept() -> Dictionary:
	var flags: Dictionary = SaveGame.data.flags.duplicate(true)
	flags.erase("shard_lantern_dark")
	return {"glint": int(SaveGame.data.glint), "quests": SaveGame.data.quests.duplicate(true),
		"restored": SaveGame.data.village.restored.duplicate(true), "flags": flags}

func _dimmed() -> Node2D:
	return Zones.current.get_node_or_null("Props/If_lantern_lit/LanternLit/Dimmed") as Node2D

## The night's waves come and are freed, to the win.
func _hold_the_night(night: RaidNight) -> void:
	night.set_physics_process(false)
	for w in 3:
		for i in 30:
			night._physics_process(1.0)
		_free_all(night)
		await get_tree().process_frame
	night._physics_process(0.1)

## "Shard dims until held": a lost night leaves the shard lantern dark, through a zone reload, a save and a
## load, the next announcement and the next night, until a night is won. Nothing else is taken.
func test_a_lost_night_leaves_the_lantern_dark_until_a_night_is_held() -> void:
	SaveGame.data.settings.reduced_motion = true
	var night := _into_town()
	assert_bool(Raids.lantern_dark()).is_false()
	assert_object(_dimmed()).is_null()                                 # lit, as it has been since the shard came home
	Raids.ring()
	var kept := _kept()
	for i in 28:
		night._physics_process(1.0)
	night.lantern.batter(night.lantern.max_hp)
	assert_str(Raids.state()).is_equal("lost")
	assert_bool(SaveGame.has_flag("shard_lantern_dark")).is_true()
	assert_bool(Raids.lantern_dark()).is_true()
	assert_dict(_kept()).is_equal(kept)                                # no Glint, quest, restore or other flag
	# the square shows it at once: the dark pane over the lit lantern's glass, a child of its picture
	var pane := _dimmed()
	assert_object(pane).is_not_null()
	assert_bool(pane.is_visible_in_tree()).is_true()
	assert_object(pane.get_parent()).is_same(night.lantern_picture())
	assert_vector(pane.global_position).is_equal(Vector2(352, 320) * 3.0)   # the plinth's foot (data lantern.foot)
	assert_float(RaidLantern.DIM.a).is_greater(RaidLantern.DARK.a)     # darker than a blow's flicker
	assert_int(night.repairs.size()).is_equal(2)                       # and the square looks worse
	assert_str(" ".join(Dialogue.lines_for("shard_lantern"))).contains("gone dark")
	# Hale says how it comes back, in the lead's words; talking to her starts nothing and she does not say so
	var hale := " ".join(Dialogue.lines_for("hale"))
	assert_str(hale).contains("stays dark until we hold a night")
	assert_str(hale).contains("the next time you walk into Crossroads")
	assert_str(hale).not_contains("Give me the word")
	assert_str(Raids.state()).is_equal("lost")
	Quests.notify("talk:hale")
	assert_str(Raids.state()).is_equal("lost")
	assert_str(" ".join(Dialogue.lines_for("notice_board"))).contains("THE LANTERN IS DARK")
	# a zone reload (getting up in town), and a save and a load: still dark
	assert_bool(Zones.go_to("crossroads", "start")).is_true()
	await get_tree().process_frame
	assert_object(_dimmed()).is_not_null()
	assert_int(SaveGame.save(PATH)).is_equal(OK)
	SaveGame.reset()
	assert_bool(Raids.lantern_dark()).is_false()
	assert_int(SaveGame.load_save(PATH)).is_equal(OK)
	assert_bool(Raids.lantern_dark()).is_true()
	assert_dict(_kept()).is_equal(kept)
	assert_bool(Zones.go_to("crossroads", "start")).is_true()
	await get_tree().process_frame
	assert_object(_dimmed()).is_not_null()
	# the next walk into town offers the night again (as before), and the lantern is still dark
	assert_bool(Zones.go_to("woodland", "crossroads")).is_true()
	assert_bool(Zones.go_to("crossroads", "woodland")).is_true()
	await get_tree().process_frame
	assert_str(Raids.state()).is_equal("announced")
	assert_int(Raids.postpones_left()).is_equal(2)
	assert_bool(Raids.lantern_dark()).is_true()
	assert_object(_dimmed()).is_not_null()
	assert_int((Zones.current.get_node("RaidNight") as RaidNight).repairs.size()).is_equal(2)
	# putting it off does not light it
	assert_bool(Raids.postpone()).is_true()
	assert_bool(Raids.lantern_dark()).is_true()
	assert_bool(Zones.go_to("woodland", "crossroads")).is_true()
	assert_bool(Zones.go_to("crossroads", "woodland")).is_true()
	await get_tree().process_frame
	# the second night: a dark lantern pools no light when a wave comes, and the tracker is the night's
	night = Zones.current.get_node("RaidNight") as RaidNight
	assert_bool(Raids.ring()).is_true()
	assert_bool(night.lantern.dark).is_true()
	night.lantern.swell()
	assert_bool(night.lantern.is_processing()).is_false()
	assert_object(_dimmed()).is_not_null()                             # dark through the night, until it is held
	# held: lit at once, and it stays lit
	var glint := int(SaveGame.data.glint)
	await _hold_the_night(night)
	assert_str(Raids.state()).is_equal("won")
	assert_bool(SaveGame.has_flag("shard_lantern_dark")).is_false()
	assert_int(int(SaveGame.data.glint)).is_equal(glint + int(GlintCache.balance().raids.first_night))
	await get_tree().process_frame
	assert_object(_dimmed()).is_null()
	assert_str(" ".join(Dialogue.lines_for("shard_lantern"))).not_contains("dark")
	assert_str(" ".join(Dialogue.lines_for("notice_board"))).contains("THE LANTERN IS LIT")
	assert_bool(Zones.go_to("crossroads", "start")).is_true()
	await get_tree().process_frame
	assert_object(_dimmed()).is_null()

## Going down loses the night too, so it dims the lantern too, and the card on getting up says so. The
## record only: the real fall, through the game scene, is test_going_down_in_a_night_costs_no_glint.
func test_going_down_dims_the_lantern_and_the_card_claims_only_what_happened() -> void:
	_into_town()
	var hud: Control = auto_free(load("res://ui/hud.gd").new())
	add_child(hud)
	Raids.ring()
	Raids.player_downed()
	assert_bool(Raids.lantern_dark()).is_true()
	assert_bool(Raids.downed_in_a_night()).is_true()
	assert_bool(Raids.lost_while_dark).is_false()
	assert_bool(Zones.go_to("crossroads", "start")).is_true()          # as game.gd does on getting up
	await get_tree().process_frame
	await get_tree().process_frame
	assert_bool(Raids.downed_in_a_night()).is_false()                  # told: the next defeat is an ordinary one
	assert_object(_dimmed()).is_not_null()
	assert_str(hud.shown_text().banner_text).is_equal(RaidNight.LOST_DOWN)
	# no raider reaches the lantern when the player goes down, and the card does not say one did
	for card: String in [RaidNight.LOST_DOWN, RaidNight.LOST_DOWN_AGAIN]:
		assert_str(card).not_contains("reached")
	for card: String in [RaidNight.LOST_DOWN, RaidNight.LOST_LANTERN, RaidNight.LOST_DOWN_AGAIN, RaidNight.LOST_LANTERN_AGAIN]:
		assert_str(card).contains("until a night is held")
		assert_str(card).contains("Nothing else is lost")
		assert_str(card).contains("they will come again on your next walk into town")

## A lantern already dark cannot go out again: a second lost night says it stays dark, either way it is lost.
func test_a_second_lost_night_says_the_lantern_stays_dark() -> void:
	assert_array(RaidNight.loss_card("lantern", false)).is_equal(["The shardstruck broke the shard lantern", RaidNight.LOST_LANTERN])
	assert_array(RaidNight.loss_card("lantern", true)).is_equal(["The shardstruck reached the shard lantern", RaidNight.LOST_LANTERN_AGAIN])
	assert_array(RaidNight.loss_card("down", false)).is_equal(["The night is lost", RaidNight.LOST_DOWN])
	assert_array(RaidNight.loss_card("down", true)).is_equal(["The night is lost", RaidNight.LOST_DOWN_AGAIN])
	for again: String in [RaidNight.LOST_LANTERN_AGAIN, RaidNight.LOST_DOWN_AGAIN]:
		assert_str(again).contains("stays dark")
		assert_str(again).not_contains("goes out")
		assert_str(again).not_contains("went out")
	# in the scene: the first night lost at the lantern, the second at the lantern again
	SaveGame.data.settings.reduced_motion = true
	var night := _into_town()
	var hud: Control = auto_free(load("res://ui/hud.gd").new())
	add_child(hud)
	Raids.ring()
	night.lantern.batter(night.lantern.max_hp)
	assert_str(hud.shown_text().banner_text).is_equal(RaidNight.LOST_LANTERN)
	assert_bool(Zones.go_to("woodland", "crossroads")).is_true()
	assert_bool(Zones.go_to("crossroads", "woodland")).is_true()
	await get_tree().process_frame
	night = Zones.current.get_node("RaidNight") as RaidNight
	Raids.ring()
	night.lantern.batter(night.lantern.max_hp)
	assert_bool(Raids.lost_while_dark).is_true()
	assert_str(hud.shown_text().banner_text).is_equal(RaidNight.LOST_LANTERN_AGAIN)
	# and the third by going down
	assert_bool(Zones.go_to("woodland", "crossroads")).is_true()
	assert_bool(Zones.go_to("crossroads", "woodland")).is_true()
	await get_tree().process_frame
	Raids.ring()
	Raids.player_downed()
	assert_bool(Zones.go_to("crossroads", "start")).is_true()
	await get_tree().process_frame
	await get_tree().process_frame
	assert_str(hud.shown_text().banner_text).is_equal(RaidNight.LOST_DOWN_AGAIN)

## "No progress or Glint lost" (Matt, 13 Nov), through the path the game takes: the player's own `downed`
## in the game scene, which game.gd answers with Raids.player_downed and then its own _on_downed. While a
## night runs the purse is untouched and no cache lies anywhere; the defeat after it is an ordinary one and
## leaves its cache as before.
func test_going_down_in_a_night_costs_no_glint() -> void:
	const GAME_SAVE := "user://test_raids_game_save.json"
	SaveGame.path = GAME_SAVE
	_after_home_again()
	SaveGame.data.zone = "woodland"
	var g: Node2D = load("res://game.tscn").instantiate()
	add_child(g)
	for i in 3:
		await get_tree().physics_frame
	assert_bool(Zones.go_to("crossroads", "woodland")).is_true()
	for i in 3:
		await get_tree().physics_frame
	assert_str(Raids.state()).is_equal("announced")
	assert_bool(Raids.ring()).is_true()
	var player: Player = g.player
	var kept := _kept()
	assert_int(int(kept.glint)).is_equal(116)
	player.global_position = Vector2(640, 930)
	player.downed.emit()                                               # what the fall's last drawing sends
	for i in 4:
		await get_tree().physics_frame
	assert_str(Raids.state()).is_equal("lost")
	assert_bool(Raids.lantern_dark()).is_true()
	assert_dict(_kept()).is_equal(kept)                                # the purse, the quests, the restores
	assert_array(SaveGame.data.caches).is_empty()
	assert_int(Zones.current.actors.get_children().filter(func(n: Node) -> bool: return n is GlintCachePickup).size()).is_equal(0)
	assert_int(player.hp).is_equal(player.max_hp)
	assert_vector(player.global_position).is_equal(Zones.current.spawn_position("start"))
	var saved: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(GAME_SAVE))
	assert_int(int(saved.glint)).is_equal(116)
	assert_array(saved.caches).is_empty()
	assert_bool(bool(saved.flags.get("shard_lantern_dark", false))).is_true()
	# the next defeat, with no night running, keeps the cache rule: a fifth of the purse stays where they fell
	player.global_position = Vector2(640, 930)
	player.downed.emit()
	for i in 4:
		await get_tree().physics_frame
	assert_int(int(SaveGame.data.glint)).is_equal(116 - GlintCache.amount_for(116, GlintCache.floor_glint()))
	assert_int((SaveGame.data.caches as Array).size()).is_equal(1)
	g.queue_free()
	await get_tree().process_frame
	SaveGame.path = SaveGame.DEFAULT_PATH
	DirAccess.remove_absolute(ProjectSettings.globalize_path(GAME_SAVE))

## A save made before the stake existed whose raid is `lost`: the lantern is dark from the load on. Any
## other state says nothing of an old loss and stays lit.
func test_a_save_lost_before_the_stake_existed_loads_dark() -> void:
	_after_home_again()
	Raids.arrive("crossroads", "woodland")
	Raids.ring()
	Raids.lose("lantern")
	SaveGame.set_flag("shard_lantern_dark", false)                    # as such a save was written
	assert_int(SaveGame.save(PATH)).is_equal(OK)
	SaveGame.reset()
	assert_int(SaveGame.load_save(PATH)).is_equal(OK)
	assert_str(Raids.state()).is_equal("lost")
	assert_bool(SaveGame.has_flag("shard_lantern_dark")).is_true()
	SaveGame.reset()
	_after_home_again()
	Raids.arrive("crossroads", "woodland")
	assert_int(SaveGame.save(PATH)).is_equal(OK)
	SaveGame.reset()
	assert_int(SaveGame.load_save(PATH)).is_equal(OK)
	assert_bool(SaveGame.has_flag("shard_lantern_dark")).is_false()

## The HUD says the lantern is dark, and how the night comes again, exactly where the first night's lead
## stands: it hides no other lead (Morel's, while his roof is owed) and no active quest.
func test_the_hud_says_the_lantern_is_dark_only_where_the_first_nights_lead_stands() -> void:
	_after_home_again()
	var player := _attach()
	var hud: Control = auto_free(load("res://ui/hud.gd").new())
	hud.player = player
	add_child(hud)
	SaveGame.set_flag("first_night_announced")
	SaveGame.set_flag("shard_lantern_dark")
	# the torn roof still owed: Morel's lead keeps the tracker, dark lantern or not
	hud._process(0.0)
	var other: String = hud.shown_text().quest_title + ": " + hud.shown_text().quest_step
	assert_str(other).not_contains("dark")
	SaveGame.set_flag("shard_lantern_dark", false)
	hud._process(0.0)
	assert_str(hud.shown_text().quest_title + ": " + hud.shown_text().quest_step).is_equal(other)
	# the roof on: the first night's lead, and its dark wording while the lantern is dark
	SaveGame.data.quests["a1_the_torn_roof"] = {"state": "done", "step": Quests.defs["a1_the_torn_roof"].steps.size()}
	hud._process(0.0)
	assert_str(hud.shown_text().quest_title).is_equal("The first night")
	assert_str(hud.shown_text().quest_step).is_equal("The shardstruck are camped on the halt road. They come the next time you walk into Crossroads")
	SaveGame.set_flag("shard_lantern_dark")
	hud._process(0.0)
	assert_str(hud.shown_text().quest_title).is_equal("The first night")
	assert_str(hud.shown_text().quest_step).is_equal("The shard lantern is dark until a night is held. They come the next time you walk into Crossroads")
	assert_str(hud.shown_text().lantern).is_equal("")                  # no lights row: no night runs
	# an active quest keeps the tracker
	SaveGame.data.quests["home_again"] = {"state": "active", "step": 0}
	hud._process(0.0)
	assert_str(hud.shown_text().quest_title).is_not_equal("The first night")

## Under the dark pane the lit picture's light on the iron is gone too: every pixel where the lit and the
## unlit lantern pictures differ lies under the pane or under one of the unlit picture's parts.
func test_no_lit_pixel_is_left_round_the_dark_glass() -> void:
	var night := _into_town()
	Raids.ring()
	night.lantern.batter(night.lantern.max_hp)
	var pane := _dimmed()
	assert_object(pane.get_node_or_null("Unlit")).is_not_null()
	var lamp: Dictionary = night.def.lantern
	var lit := (load("res://zones/crossroads/art/lantern_lit.png") as Texture2D).get_image()
	var unlit := (load(String(lamp.unlit)) as Texture2D).get_image()
	assert_vector(Vector2(unlit.get_size())).is_equal(Vector2(lit.get_size()))
	var pic := night.lantern_picture() as Sprite2D
	var glass := Rect2(RaidLantern.GLASS.position - pic.offset, RaidLantern.GLASS.size)   # in picture px
	var parts: Array[Rect2] = []
	for part: Array in lamp.unlit_parts:
		parts.append(Rect2(float(part[0]), float(part[1]), float(part[2]), float(part[3])))
		assert_bool(Rect2(Vector2.ZERO, Vector2(lit.get_size())).encloses(parts[parts.size() - 1])).is_true()
	var left := []
	for y in lit.get_height():
		for x in lit.get_width():
			if lit.get_pixel(x, y) == unlit.get_pixel(x, y):
				continue
			var at := Vector2(x + 0.5, y + 0.5)
			if glass.has_point(at) or parts.any(func(r: Rect2) -> bool: return r.has_point(at)):
				continue
			left.append(Vector2i(x, y))
	assert_array(left).is_empty()

## A raid already won is never offered, begun, paid or dark again, whatever its record or flags say (a
## hand-edited or older save).
func test_a_won_raid_stays_won_lit_and_unpaid_whatever_the_record_says() -> void:
	_after_home_again()
	SaveGame.set_flag("first_night_won")
	SaveGame.set_flag("shard_lantern_dark")
	SaveGame.data.raid = {"id": "", "state": "none", "postponed": 0, "wave": 0, "layout": {}, "repairs": false}
	assert_int(SaveGame.save(PATH)).is_equal(OK)
	SaveGame.reset()
	assert_int(SaveGame.load_save(PATH)).is_equal(OK)
	assert_bool(SaveGame.has_flag("shard_lantern_dark")).is_false()    # won: lit, from the load on
	assert_bool(Raids.earned(Raids.defs.first_night)).is_false()
	for st: String in ["none", "postponed", "pending", "lost", "announced", "running"]:
		SaveGame.data.raid.state = st
		SaveGame.data.raid.id = "first_night"
		assert_bool(Raids.arrive("crossroads", "woodland")).override_failure_message(st).is_false()
		assert_str(Raids.state()).is_equal(st)
	assert_int(int(SaveGame.data.glint)).is_equal(116)

## "Hale's anvil signals": when the word is given a card says who calls the night, and each of the cue's
## three blows throws a spark off the anvil at the forge. Finite, and still under reduced motion.
func test_the_night_is_called_from_hales_anvil() -> void:
	var night := _into_town()
	var hud: Control = auto_free(load("res://ui/hud.gd").new())
	add_child(hud)
	assert_object(night.anvil_call).is_null()
	assert_bool(Raids.ring()).is_true()                               # the cue: test_sound.gd, the anvil and never the bell
	assert_str(hud.shown_text().banner).is_equal("The first night")
	assert_str(hud.shown_text().banner_text).is_equal("Three blows from the forge: the night has begun.")
	var call := night.anvil_call
	assert_object(call).is_not_null()
	# on the anvil's face, inside its picture, west of where Hale stands at the forge
	var anvil := Zones.current.get_node("Props/If_anvil/Anvil") as Sprite2D
	var pic := Rect2(anvil.global_position + anvil.offset, anvil.texture.get_size())
	assert_bool(pic.has_point(call.global_position)).is_true()
	var hale := Zones.current.get_node("Actors/If_hale_forge/HaleForge") as Node2D
	assert_bool(hale.is_visible_in_tree()).is_true()
	assert_float(call.global_position.x).is_less(hale.global_position.x)
	assert_float(call.global_position.distance_to(hale.global_position)).is_less(60.0)
	# three blows, as the cue's; each spark lasts the glance's time and then it is over
	assert_array(RaidSignal.BLOWS).is_equal([0.0, 0.5, 1.0])
	assert_float(RaidSignal.left(0.0, 0.0)).is_equal(Glance.TIME)
	assert_float(RaidSignal.left(0.4, 0.5)).is_equal(0.0)                # the second blow has not fallen yet
	assert_float(RaidSignal.left(0.5 + Glance.TIME, 0.5)).is_equal_approx(0.0, 0.0001)
	assert_bool(RaidSignal.over(1.0 + Glance.TIME - 0.01)).is_false()
	assert_bool(RaidSignal.over(1.0 + Glance.TIME)).is_true()
	assert_float(float(Glance.parts(Glance.TIME, true).ray)).is_equal(Glance.RAY)   # reduced motion: still, full size
	call._process(1.0 + Glance.TIME)
	assert_bool(call.is_queued_for_deletion()).is_true()
	assert_bool(call.is_processing()).is_false()

## Without the forge's anvil in the zone there is nothing to strike sparks from: the cue and the card only.
func test_no_spark_is_thrown_where_no_anvil_stands() -> void:
	var night := _into_town()
	SaveGame.data.village.restored.erase("forge")
	Village.changed.emit("forge")
	assert_bool((Zones.current.get_node("Props/If_anvil") as CanvasItem).is_visible_in_tree()).is_false()
	assert_bool(Raids.ring()).is_true()
	assert_object(night.anvil_call).is_null()

## "One-off, Hale says so": once won, no walk into town, load or quit offers the night again, and no line
## of Hale's, the lantern's or the HUD's speaks of a next one.
func test_a_won_night_is_never_offered_again() -> void:
	var night := _into_town()
	Raids.ring()
	await _hold_the_night(night)
	assert_str(Raids.state()).is_equal("won")
	assert_bool(Raids.won("first_night")).is_true()
	for from: String in ["woodland", "", "crossroads"]:
		assert_bool(Raids.arrive("crossroads", from)).is_false()
		assert_str(Raids.state()).is_equal("won")
	assert_bool(Raids.ring()).is_false()
	assert_bool(Raids.postpone()).is_false()
	assert_int(SaveGame.save(PATH)).is_equal(OK)
	SaveGame.reset()
	assert_int(SaveGame.load_save(PATH)).is_equal(OK)
	assert_bool(Raids.arrive("crossroads", "woodland")).is_false()
	assert_str(Raids.state()).is_equal("won")
	assert_dict(Raids.current()).is_equal(Raids.defs.first_night)      # no other raid waits behind it
	assert_str(Raids.tracker_text()).is_equal("")
	for who: String in ["hale", "shard_lantern", "moss"]:
		var says := " ".join(Dialogue.lines_for(who)).to_lower()
		for word: String in ["next lot", "come again", "another night", "bell"]:
			assert_str(says).override_failure_message("%s says '%s'" % [who, word]).not_contains(word)
