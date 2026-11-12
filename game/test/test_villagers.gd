extends GdUnitTestSuite
## The village folk (Hale, Moss, Ada Fern) drawn from the cast: they load, rest in their work loop
## or idle, turn to the player to talk, and the forge's looping effects hold still under reduced
## motion.

func before_test() -> void:
	SaveGame.reset()

func _villager(id: String, work: bool, fc := "S") -> Villager:
	var v := Villager.new()
	v.character = id
	v.work = work
	v.facing_at_rest = fc
	add_child(v)
	auto_free(v)
	return v

func test_each_villager_loads_with_talk_and_work() -> void:
	for id in ["hale", "moss", "ada"]:
		var v := _villager(id, true, "W")
		assert_bool(v.manifest.is_empty()).is_false()
		for clip in ["idle", "walk", "talk", "work"]:
			assert_bool(v.has_clip(clip)).is_true()
		assert_str(v.animation).is_equal("work_W")

func test_turns_to_talk_when_the_player_is_near() -> void:
	var p: Player = auto_free(load("res://actors/player.tscn").instantiate())
	add_child(p)
	p.input_enabled = false
	var v := _villager("moss", false)
	v.global_position = Vector2(500, 500)
	p.global_position = Vector2(560, 500)          # to her east, within the talk radius
	await get_tree().process_frame
	await get_tree().process_frame
	assert_str(v.animation).is_equal("talk_E")
	p.global_position = Vector2(1500, 500)
	await get_tree().process_frame
	await get_tree().process_frame
	assert_str(v.shown_facing).is_equal("S")
	for i in 30:                                # past the turn in-between (contract V2.9: idle_SE for a beat)
		if v.animation == &"idle_S":
			break
		await get_tree().process_frame
	assert_str(v.animation).is_equal("idle_S")

func test_loop_fx_holds_still_under_reduced_motion() -> void:
	SaveGame.data.settings["reduced_motion"] = true
	var fx := LoopFx.new()
	fx.texture = load("res://zones/crossroads/art/fx/forge_fire_8.png")
	fx.hframes = 8
	add_child(fx)
	auto_free(fx)
	for i in 10:
		await get_tree().process_frame
	assert_int(fx.frame).is_equal(0)
	SaveGame.data.settings["reduced_motion"] = false

func test_a_forge_paid_before_hale_is_home_shows_the_banked_ember() -> void:
	# Matt, 11 Nov: a dark hearth until she arrives. The scene holds the fire (restored and Hale home)
	# and the banked ash with its ember (restored, Hale not yet home) as two exclusive conditions.
	var scene: Node = auto_free(load("res://zones/crossroads/crossroads.tscn").instantiate())
	var fire: Node = scene.get_node("Props/If_forge_fire")
	var banked: Node = scene.get_node("Props/If_forge_fire_banked")
	var fire_if: Dictionary = JSON.parse_string(fire.only_if)
	var banked_if: Dictionary = JSON.parse_string(banked.only_if)
	assert_array(fire_if["restored"]).contains(["forge"])
	assert_array(fire_if["flags"]).contains(["hale_walked_home"])
	assert_array(banked_if["restored"]).contains(["forge"])
	assert_array(banked_if["not_flags"]).contains(["hale_walked_home"])
	var ember: Sprite2D = banked.get_node("ForgeFireBanked")
	assert_str(ember.texture.resource_path).is_equal("res://zones/crossroads/art/fx/forge_ember_8.png")
	assert_int(ember.hframes).is_equal(8)
