extends GdUnitTestSuite
## The redrawn cast in play: Bramble's facing follows movement or aim, the bow shot releases its
## arrow on the manifest's release frame at that drawing's arrow_tip, and he walks at the
## manifest's walk_speed.

func before_test() -> void:
	SaveGame.reset()

func _player() -> Player:
	var p: Player = auto_free(load("res://actors/player.tscn").instantiate())
	add_child(p)
	p.input_enabled = false
	p.use_mouse_aim = false
	return p

func _manifest() -> Dictionary:
	var f := FileAccess.open("res://assets/characters/bramble/manifest.json", FileAccess.READ)
	return JSON.parse_string(f.get_as_text())

func test_facing_selection() -> void:
	assert_str(CastSprite.facing_for(Vector2(1, 0.2))).is_equal("E")
	assert_str(CastSprite.facing_for(Vector2(-1, 0.4))).is_equal("W")
	assert_str(CastSprite.facing_for(Vector2(0.3, 1))).is_equal("S")
	assert_str(CastSprite.facing_for(Vector2(-0.2, -1))).is_equal("N")
	assert_str(CastSprite.facing_for(Vector2(1, 1))).is_equal("S")       # a tie faces S or N
	assert_str(CastSprite.facing_for(Vector2.ZERO, "W")).is_equal("W")   # no direction keeps it
	# hysteresis: 50 degrees below east stays E when already facing E, but is S from elsewhere
	var v := Vector2.from_angle(deg_to_rad(50.0))
	assert_str(CastSprite.facing_for(v, "E")).is_equal("E")
	assert_str(CastSprite.facing_for(v, "N")).is_equal("S")
	assert_str(CastSprite.facing_for(Vector2.from_angle(deg_to_rad(60.0)), "E")).is_equal("S")

func test_bow_aims_within_the_facing() -> void:
	var p := _player()
	var m := _manifest()
	assert_bool(m.aim_clips.has("primary")).is_true()
	# 16 directions: facing by quarter, aim by 22.5 degrees within it
	var cases := [[0.0, "E", "0"], [22.5, "E", "p22"], [-45.0, "E", "m45"], [112.5, "S", "p22"],
		[180.0, "W", "0"], [-67.5, "N", "p22"], [157.5, "W", "m22"]]
	for c in cases:
		var dir := Vector2.from_angle(deg_to_rad(float(c[0])))
		p.aim = dir
		await get_tree().physics_frame
		await get_tree().physics_frame
		p.state = &"idle"
		assert_bool(p.start_shot()).is_true()
		assert_str(p.facing).is_equal(c[1])
		assert_str(p.sprite.animation).is_equal("primary_%s_%s" % [c[1], c[2]])
		p._set_state(&"idle")
func test_idle_fidget_plays_and_returns() -> void:
	var s: CastSprite = auto_free(CastSprite.new())
	add_child(s)
	assert_bool(s.load_character("bramble")).is_true()
	var cfg: Dictionary = s.manifest.idle_fidgets
	assert_int(cfg.clips.size()).is_greater_equal(2)
	var seen := false
	for i in int((float(cfg.after) + 3.0) * 60.0):
		s.advance(1.0 / 60.0)
		if s.is_fidgeting():
			seen = true
			assert_bool(String(s.animation).begins_with("fidget_")).is_true()
			break
	assert_bool(seen).is_true()
	for i in 600:
		s.advance(1.0 / 60.0)
		if not s.is_fidgeting():
			break
	assert_bool(s.is_fidgeting()).is_false()
	assert_str(s.animation).is_equal("idle_S")
	# any other clip cancels it at once
	s._next_fidget = 0.0
	for i in 200:
		s.advance(1.0 / 60.0)
		if s.is_fidgeting():
			break
	s.play_clip("walk", "S")
	assert_str(s.animation).is_equal("walk_S")
	assert_bool(s.is_fidgeting()).is_false()

func test_standing_faces_the_aim() -> void:
	var p := _player()
	for want in [["E", Vector2.RIGHT], ["N", Vector2.UP], ["W", Vector2.LEFT], ["S", Vector2.DOWN]]:
		p.aim = want[1]
		await get_tree().physics_frame     # emitted before the nodes' own physics step ...
		await get_tree().physics_frame     # ... so wait one more
		assert_str(p.facing).is_equal(want[0])
		assert_str(p.sprite.animation).is_equal("idle_" + want[0])

func test_shot_releases_on_the_release_frame() -> void:
	var m := _manifest()
	var clip: Dictionary = m.clips.primary
	var rel := int(clip.release_frame)
	for dir in [Vector2.RIGHT, Vector2.UP, Vector2.LEFT, Vector2.DOWN, Vector2(1, 1).normalized(),
			Vector2(-1, -1).normalized(), Vector2.from_angle(deg_to_rad(200.0))]:   # any angle: from the nearest facing
		var p := _player()
		p.global_position = Vector2(300, 300)
		p.aim = dir
		await get_tree().physics_frame
		var got := []
		p.shot_released.connect(func(a: Node, fr: int) -> void: got.append([a, fr, p.sprite.clip_time]))
		assert_bool(p.start_shot()).is_true()
		var fc := CastSprite.facing_for(dir)
		var tag := p.sprite.aim_tag_for("primary", fc, dir)
		assert_str(p.sprite.animation).is_equal("primary_%s_%s" % [fc, tag])
		for i in 60:
			await get_tree().physics_frame
			if got.size() > 0:
				break
		assert_int(got.size()).is_equal(1)
		assert_int(got[0][1]).is_equal(rel)
		# released within one physics step of the manifest's release time
		assert_float(got[0][2]).is_between(float(clip.release_time), float(clip.release_time) + 1.0 / 60.0 + 0.001)
		# from the arrow tip of the drawing before the release (the arrow has left on it)
		var frames: Array = clip.facings[fc].aims[tag].frames
		var tip = frames[rel].anchors.get("arrow_tip", frames[rel - 1].anchors.get("arrow_tip"))
		var arrow: Arrow = got[0][0]
		assert_vector(arrow.dir).is_equal_approx(dir, Vector2(0.001, 0.001))
		assert_float(arrow.height).is_equal_approx(-float(tip[1]), 0.01)
		var off: Vector2 = arrow.global_position - Vector2(300.0 + float(tip[0]), 300.0)
		assert_float(off.dot(dir)).is_between(-0.5, Arrow.SPEED / 60.0 + 0.5)   # at most one step flown
		assert_float(absf(off.cross(dir))).is_less(0.5)
		arrow.queue_free()

func test_walks_at_the_manifest_speed() -> void:
	var p := _player()
	assert_float(p.walk_speed).is_equal_approx(float(_manifest().walk_speed), 0.001)

func test_dodge_and_hit_clips() -> void:
	var p := _player()
	p.start_roll(Vector2.LEFT)
	assert_str(p.sprite.animation).is_equal("dodge_W")
	await get_tree().create_timer(0.6).timeout
	assert_str(p.state).is_equal("idle")
	assert_bool(p.take_damage(1, Vector2.RIGHT)).is_true()
	assert_bool(String(p.sprite.animation).begins_with("hit_")).is_true()

func test_defeat_plays_before_downed() -> void:
	var p := _player()
	var downed := [false]
	p.downed.connect(func() -> void: downed[0] = true)
	p.hp = 1
	p.take_damage(1)
	assert_str(p.state).is_equal("defeat")
	await get_tree().physics_frame
	assert_bool(downed[0]).is_false()
	await get_tree().create_timer(2.0).timeout
	assert_bool(downed[0]).is_true()

func test_every_cast_member_loads_and_switches() -> void:
	var p := _player()
	for id in Player.CAST:
		assert_bool(p.set_character(id)).is_true()
		assert_str(p.character).is_equal(id)
		var f := FileAccess.open("res://assets/characters/%s/manifest.json" % id, FileAccess.READ)
		var m: Dictionary = JSON.parse_string(f.get_as_text())
		assert_float(p.walk_speed).is_equal_approx(float(m.walk_speed), 0.001)
		for clip in ["idle", "walk", "primary", "dodge", "hit", "defeat"]:
			for fc in m.get("directions", CastSprite.FACINGS):
				assert_bool(p.sprite.sprite_frames.has_animation("%s_%s" % [clip, fc])).is_true()
	assert_bool(p.set_character("bramble")).is_true()
	assert_bool(p.start_shot()).is_true()
