extends GdUnitTestSuite

var contacts: Array = []
var actor: Player
var driver: AbilityArenaDriver
var use_foreign := false

func _player() -> Player:
	var p: Player = auto_free(load("res://actors/player.tscn").instantiate())
	add_child(p)
	p.set_physics_process(false)
	p.input_enabled = false
	p.use_mouse_aim = false
	return p

func _sample(body: CastSprite, clip := "primary", facing := "E", index := 0, aim := "") -> Dictionary:
	var selected: Dictionary = body.manifest.clips[clip].facings[facing]
	if aim != "": selected = selected.aims[aim]
	return {"token": 1, "clip": clip, "facing": facing, "aim": aim, "index": index,
		"starts_at": 0.0, "frame": selected.frames[index].duplicate(true)}

func test_exact_four_facings_and_anchor_indices_without_mirroring_or_clock() -> void:
	var p := _player()
	for facing in ["S", "N", "E", "W"]:
		var sample := _sample(p.sprite, "primary", facing, 3)
		p.sprite.flip_h = true
		p.sprite.play()
		assert_bool(AbilitySpritePresenter.show_drawing(p.sprite, sample)).is_true()
		assert_str(p.sprite.animation).is_equal("primary_" + facing)
		assert_int(p.sprite.frame).is_equal(3)
		assert_int(p.sprite.frame_index).is_equal(3)
		assert_bool(p.sprite.is_playing()).is_false()
		assert_bool(p.sprite.flip_h).is_false()
		var anchor: Array = sample.frame.anchors.arrow_tip
		assert_vector(p.sprite.anchor("arrow_tip")).is_equal(Vector2(anchor[0], anchor[1]))

func test_missing_variant_invalid_index_and_forged_anchors_leave_body_unchanged() -> void:
	var p := _player()
	var valid := _sample(p.sprite)
	assert_bool(AbilitySpritePresenter.show_drawing(p.sprite, valid)).is_true()
	for change in [{"facing": "NE"}, {"aim": "missing"}, {"index": 0.5}, {"index": NAN},
		{"index": 999}, {"starts_at": -1.0}, {"frame": {"anchors": {"arrow_tip": [999, 999]}}}]:
		var bad := valid.duplicate(true)
		bad.merge(change, true)
		assert_bool(AbilitySpritePresenter.show_drawing(p.sprite, bad)).is_false()
		assert_str(p.sprite.animation).is_equal("primary_E")
		assert_int(p.sprite.frame).is_equal(0)

func test_exact_aim_sheet_and_missing_animation_fail_without_fallback() -> void:
	var p := _player()
	p.sprite.manifest = p.sprite.manifest.duplicate(true)
	p.sprite.sprite_frames = p.sprite.sprite_frames.duplicate(true)
	var frames: Array = p.sprite.manifest.clips.primary.facings.E.frames.duplicate(true)
	frames[1].anchors.arrow_tip = [31, -44]
	p.sprite.manifest.clips.primary.facings.E.aims = {"up22": {"frames": frames}}
	var sample := _sample(p.sprite, "primary", "E", 1, "up22")
	assert_bool(AbilitySpritePresenter.show_drawing(p.sprite, sample)).is_false()
	p.sprite.sprite_frames.add_animation("primary_E_up22")
	for i in frames.size():
		p.sprite.sprite_frames.add_frame("primary_E_up22", p.sprite.sprite_frames.get_frame_texture("primary_E", i))
	assert_bool(AbilitySpritePresenter.show_drawing(p.sprite, sample)).is_true()
	assert_str(p.sprite.animation).is_equal("primary_E_up22")
	assert_int(p.sprite.frame).is_equal(1)
	assert_vector(AbilityContactTrack.anchor(sample, "arrow_tip").offset).is_equal(Vector2(31, -44))

func _decode(value: Variant) -> Variant:
	if value is Dictionary:
		if value.size() == 1 and value.has("__f64le"):
			return str(value.__f64le).hex_decode().decode_double(0)
		var result := {}
		for key in value: result[key] = _decode(value[key])
		return result
	if value is Array: return value.map(_decode)
	return value

func _source() -> Dictionary:
	var bytes := FileAccess.get_file_as_bytes("res://test/combat/simulation-oracle.json.gz")
	var data: Dictionary = _decode(JSON.parse_string(bytes.decompress_dynamic(128 * 1024 * 1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8()))
	data.baseline.mode = "practice"
	return data.baseline

func _provide(snapshot: Dictionary, action: String) -> Dictionary:
	var info: Dictionary = actor.sprite.manifest.clips[action]
	var count: int = info.frame_count
	var release: int = info.release_frame
	var contact_at := AbilityPlayerPhase._release_time(snapshot.player)
	var remaining := float(snapshot.player.actionDuration) - contact_at
	var durations: Array = []
	for i in count:
		durations.append(contact_at / release if i < release else remaining / (count - release))
	var manifest := actor.sprite.manifest.duplicate(true)
	if use_foreign: manifest["foreign"] = true
	return {"manifest": manifest, "clip": action, "facing": "W", "durations": durations}

func _contact(sample: Dictionary) -> void:
	# This callback observes the real body's release drawing, before recovery can replace it.
	assert_str(actor.sprite.animation).is_equal("primary_W")
	assert_int(actor.sprite.frame).is_equal(int(sample.index))
	assert_int(actor.sprite.frame_index).is_equal(int(sample.index))
	assert_bool(actor.sprite.is_playing()).is_false()
	var anchor: Array = sample.frame.anchors.hand_R
	assert_vector(actor.sprite.anchor("hand_R")).is_equal(Vector2(anchor[0], anchor[1]))
	assert_dict(AbilityContactTrack.anchor(sample, "arrow_tip")).is_empty() # arrow already left
	contacts.append(sample.duplicate(true))

func _setup() -> void:
	contacts = []
	use_foreign = false
	actor = _player()
	driver = AbilityArenaDriver.new()
	driver.configure(_source(), Vector2.ZERO)
	actor.attach_action_driver(driver)

func _move(target: Vector2) -> Vector2:
	return target

func _tick() -> void:
	driver.tick({"active": true, "primary": true, "aim": Vector2.RIGHT},
		{"character": "bramble", "move_actor": _move}, 0.1)

func test_player_callback_shows_release_before_contact_without_legacy_arrow_or_state_mutation() -> void:
	_setup()
	var arrows := [0]
	actor.shot_released.connect(func(_node: Node, _frame: int) -> void: arrows[0] += 1)
	assert_bool(actor.bind_ability_presentation(_provide, _contact)).is_true()
	var expected := _source()
	for i in 3:
		_tick()
		expected = AbilitySimulation.step(expected, {"primary": true, "aimX": 186, "aimY": 98}, 0.1)
	assert_int(contacts.size()).is_equal(1)
	assert_dict(driver.snapshot()).is_equal(expected)
	assert_int(arrows[0]).is_equal(0)
	assert_str(actor.facing).is_equal("W")
	assert_str(actor.ability_presentation_error).is_empty()

func test_foreign_provider_manifest_never_draws_or_contacts() -> void:
	_setup()
	use_foreign = true
	assert_bool(actor.bind_ability_presentation(_provide, _contact)).is_true()
	for i in 3: _tick()
	assert_array(contacts).is_empty()
	assert_str(actor.sprite.animation).is_equal("idle_S")
	assert_str(actor.ability_presentation_error).is_equal("presentation manifest differs from loaded body")

func test_detached_driver_callback_cannot_draw_on_replacement_actor() -> void:
	_setup()
	var expected := driver
	actor.detach_action_driver()
	var replacement := AbilityArenaDriver.new()
	replacement.configure(_source(), Vector2.ZERO)
	actor.attach_action_driver(replacement)
	actor._present_ability_drawing(_sample(actor.sprite), expected)
	assert_str(actor.sprite.animation).is_equal("idle_S")
	actor._ability_contact(_sample(actor.sprite), _contact, expected)
	assert_array(contacts).is_empty()

func test_no_driver_or_non_arena_driver_cannot_bind_drawing_callbacks() -> void:
	actor = _player()
	assert_bool(actor.bind_ability_presentation(_provide, _contact)).is_false()
	actor.attach_action_driver(AbilityActionDriver.new())
	assert_bool(actor.bind_ability_presentation(_provide, _contact)).is_false()

func test_missing_sheet_at_release_suppresses_contact() -> void:
	_setup()
	assert_bool(actor.bind_ability_presentation(_provide, _contact)).is_true()
	_tick()
	actor.sprite.sprite_frames = actor.sprite.sprite_frames.duplicate(true)
	actor.sprite.sprite_frames.remove_animation("primary_W")
	for i in 2: _tick()
	assert_array(contacts).is_empty()
	assert_str(actor.ability_presentation_error).is_equal("missing or mismatched authored drawing")

func test_reset_restores_idle_even_when_legacy_state_was_already_idle() -> void:
	_setup()
	assert_bool(actor.bind_ability_presentation(_provide, _contact)).is_true()
	_tick()
	assert_str(actor.sprite.animation).is_equal("primary_W")
	assert_str(actor.state).is_equal("idle")
	actor.reset_motion()
	assert_str(actor.sprite.animation).is_equal("idle_W")
	assert_int(actor.sprite.frame).is_equal(0)
	for i in 2: _tick()
	assert_array(contacts).is_empty()
