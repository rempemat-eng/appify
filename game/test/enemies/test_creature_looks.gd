extends GdUnitTestSuite
## The drawn creatures over Codex's SliceEnemy: looks only, behaviour untouched.

func _setup(role: String) -> Array:
	var host: Node2D = auto_free(Node2D.new())
	add_child(host)
	var pool := SliceAttackSlots.new()
	host.add_child(pool)
	var target := Node2D.new()
	host.add_child(target)
	target.position = Vector2(35, 0)
	var enemy := SliceEnemy.new()
	enemy.role = role
	enemy.slots = pool
	host.add_child(enemy)
	enemy.set_physics_process(false)
	enemy.target = target
	var look := CreatureLook.new()
	enemy.add_child(look)
	look.set_process(false)
	return [host, enemy, look]

func test_every_role_has_its_creature_and_hides_the_placeholder() -> void:
	var want := {"rusher": "boarlet", "shooter": "toad", "shield": "tortoise", "elite": "thornback"}
	for role in want:
		var s := _setup(role)
		var enemy: SliceEnemy = s[1]
		var look: CreatureLook = s[2]
		assert_str(look.character).is_equal(want[role])
		assert_object(look.sprite).is_not_null()
		assert_float(enemy.self_modulate.a).is_equal(0.0)
		for clip in ["idle", "move", "telegraph", "attack", "hurt", "stagger", "freed", "freed_move"]:
			assert_bool(look.sprite.has_clip(clip)).override_failure_message("%s lacks %s" % [want[role], clip]).is_true()
		enemy._cancel_attack()

func test_states_map_to_clips_and_the_tell_spans_the_windup() -> void:
	var s := _setup("rusher")
	var enemy: SliceEnemy = s[1]
	var look: CreatureLook = s[2]
	assert_str(look.clip_for_state()[0]).is_equal("idle")
	enemy.step(0.01)   # approach
	enemy.step(0.01)   # windup
	assert_str(enemy.state).is_equal("windup")
	look._process(0.01)
	assert_str(look.sprite.clip).is_equal("telegraph")
	# the telegraph clip is stretched to the wind-up: it finishes when the tell does, not before
	look._process(enemy.windup_time() * 0.9)
	assert_bool(look.sprite.finished).is_false()
	enemy.step(enemy.windup_time())
	look._process(0.01)
	assert_str(look.sprite.clip).is_equal("attack")
	enemy.step(0.2)
	look._process(0.01)
	assert_str(enemy.state).is_equal("recover")
	assert_str(look.sprite.clip).is_equal("stagger")
	enemy._cancel_attack()

func test_a_hit_during_the_tell_flashes_without_cutting_it() -> void:
	var s := _setup("shield")
	var enemy: SliceEnemy = s[1]
	var look: CreatureLook = s[2]
	enemy.step(0.01)
	enemy.step(0.01)
	look._process(0.01)
	enemy.take_hit(1, Vector2.LEFT)
	look._process(0.01)
	assert_str(look.sprite.clip).is_equal("telegraph")
	enemy._cancel_attack()

func test_the_shot_becomes_a_seed() -> void:
	var s := _setup("shooter")
	var enemy: SliceEnemy = s[1]
	var look: CreatureLook = s[2]
	var shot := SliceEnemyShot.new()
	shot.direction = Vector2.RIGHT
	enemy.get_parent().add_child(shot)
	enemy.shot = shot
	look._on_released()
	assert_float(shot.self_modulate.a).is_equal(0.0)
	assert_int(shot.get_child_count()).is_equal(1)
	shot.finish()

func test_freed_creature_calms_and_leaves() -> void:
	var s := _setup("rusher")
	var host: Node2D = s[0]
	var enemy: SliceEnemy = s[1]
	enemy.take_hit(10, Vector2.LEFT)
	await get_tree().process_frame
	var freed: FreedCreature = null
	for c in host.get_children():
		if c is FreedCreature:
			freed = c
	assert_object(freed).is_not_null()
	assert_str(freed.sprite.clip).is_equal("freed")
	freed._process(freed.sprite.duration("freed") + 0.01)
	assert_bool(freed.sprite.clip in ["freed_move", "idle"]).is_true()
	freed._process(FreedCreature.LEAVE + 0.1)
	assert_bool(freed.is_queued_for_deletion()).is_true()

func test_the_tell_is_in_the_world_and_glints_at_the_commit() -> void:
	# no lane or ring: the body winds up (squats, leans back), and one glint at the commit
	var s := _setup("rusher")
	var enemy: SliceEnemy = s[1]
	var look: CreatureLook = s[2]
	enemy.step(0.01)
	enemy.step(0.01)
	assert_str(enemy.state).is_equal("windup")
	look._process(0.01)
	enemy.step(enemy.windup_time() * 0.8)
	look._process(0.01)
	assert_float(look.sprite.scale.y).is_less(1.0)
	assert_float(look._glint).is_equal(0.0)
	enemy.step(enemy.windup_time())
	look._process(0.01)
	assert_str(enemy.state).is_equal("attack")
	assert_float(look._glint).is_greater(0.0)
	assert_float(look.sprite.scale.y).is_equal(1.0)
	enemy._cancel_attack()

func test_the_tell_holds_still_under_reduced_motion() -> void:
	SaveGame.data.settings["reduced_motion"] = true
	var s := _setup("shooter")
	var enemy: SliceEnemy = s[1]
	var look: CreatureLook = s[2]
	enemy.target.position = Vector2(150, 40)
	enemy.step(0.01)
	enemy.step(0.01)
	enemy.step(enemy.windup_time() * 0.6)
	look._process(0.01)
	assert_float(look.sprite.scale.y).is_equal(1.0)
	assert_float(look.sprite.rotation).is_equal(0.0)
	SaveGame.data.settings["reduced_motion"] = false
	enemy._cancel_attack()
