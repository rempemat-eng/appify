extends GdUnitTestSuite

func _enemy(role: String, pool: SliceAttackSlots, target: Node2D) -> SliceEnemy:
	var enemy: SliceEnemy = auto_free(SliceEnemy.new())
	enemy.role = role
	enemy.slots = pool
	add_child(enemy)
	enemy.set_physics_process(false)
	enemy.target = target
	enemy.step(0.01) # idle -> approach
	enemy.step(0.01) # approach -> windup
	return enemy

func test_every_role_waits_its_full_telegraph() -> void:
	for role in ["rusher", "shooter", "shield", "elite"]:
		var pool: SliceAttackSlots = auto_free(SliceAttackSlots.new())
		add_child(pool)
		var target: Node2D = auto_free(Node2D.new())
		add_child(target)
		target.position = Vector2(35, 0)
		var enemy := _enemy(role, pool, target)
		assert_str(enemy.state).is_equal("windup")
		assert_float(enemy.windup_time()).is_greater_equal(0.5)
		enemy.step(enemy.windup_time() - 0.001)
		assert_str(enemy.state).is_equal("windup")
		enemy.step(0.002)
		assert_str(enemy.state).is_equal("attack")
		enemy._cancel_attack()

func test_pack_caps_commitments_and_releases_on_loss_of_target() -> void:
	var pool: SliceAttackSlots = auto_free(SliceAttackSlots.new())
	add_child(pool)
	var target: Node2D = auto_free(Node2D.new())
	add_child(target)
	target.position = Vector2(30, 0)
	var first := _enemy("rusher", pool, target)
	var second := _enemy("shield", pool, target)
	var third := _enemy("elite", pool, target)
	assert_int(pool.count()).is_equal(2)
	assert_str(third.state).is_equal("approach")
	first.target = null
	first.step(0.01)
	assert_int(pool.count()).is_equal(1)
	third.step(0.01)
	assert_str(third.state).is_equal("windup")
	assert_int(pool.count()).is_equal(2)
	second._cancel_attack()

func test_leash_cancels_tell_and_never_releases_a_hit() -> void:
	var pool: SliceAttackSlots = auto_free(SliceAttackSlots.new())
	add_child(pool)
	var target: Node2D = auto_free(Node2D.new())
	add_child(target)
	target.position = Vector2(30, 0)
	var enemy := _enemy("rusher", pool, target)
	var attacks := [0]
	enemy.released.connect(func() -> void: attacks[0] += 1)
	enemy.position = Vector2(200, 0)
	target.position = Vector2(SliceEnemy.LEASH + 1.0, 0)
	enemy.step(1.0)
	assert_str(enemy.state).is_equal("leash")
	assert_int(pool.count()).is_equal(0)
	assert_int(attacks[0]).is_equal(0)
	enemy.position = enemy.home
	enemy.step(0.01)
	assert_str(enemy.state).is_equal("idle")

func test_shield_front_halves_damage_and_back_is_open() -> void:
	var pool: SliceAttackSlots = auto_free(SliceAttackSlots.new())
	add_child(pool)
	var target: Node2D = auto_free(Node2D.new())
	add_child(target)
	target.position = Vector2(30, 0)
	var enemy := _enemy("shield", pool, target)
	enemy.take_hit(4, Vector2.LEFT)
	assert_int(enemy.hp).is_equal(6)
	enemy.take_hit(4, Vector2.RIGHT)
	assert_int(enemy.hp).is_equal(2)

func test_camp_spawns_four_roles_sharing_one_pool() -> void:
	SaveGame.reset()
	var camp: Node2D = auto_free(load("res://enemies/woodland_camp.tscn").instantiate())
	add_child(camp)
	var pool: SliceAttackSlots = camp.get_node("AttackSlots")
	var roles: Array[String] = []
	for child in camp.get_children():
		if child is SliceEnemy:
			child.set_physics_process(false)
			roles.append(child.role)
			assert_object(child.slots).is_same(pool)
	assert_int(roles.size()).is_equal(4)

func test_shot_keeps_slot_until_it_finishes_and_recovers() -> void:
	var pool: SliceAttackSlots = auto_free(SliceAttackSlots.new())
	add_child(pool)
	var target: Node2D = auto_free(Node2D.new())
	add_child(target)
	target.position = Vector2(90, 0)
	var enemy := _enemy("shooter", pool, target)
	enemy.step(enemy.windup_time())
	assert_object(enemy.shot).is_not_null()
	enemy.shot.set_physics_process(false)
	enemy.step(2.0)
	assert_str(enemy.state).is_equal("attack")
	assert_int(pool.count()).is_equal(1)
	enemy.shot.finish()
	enemy.step(0.01)
	assert_str(enemy.state).is_equal("recover")
	enemy.step(0.66)
	assert_int(pool.count()).is_equal(0)

func test_freed_enemy_returns_its_attack_slot() -> void:
	var pool: SliceAttackSlots = auto_free(SliceAttackSlots.new())
	add_child(pool)
	var target: Node2D = auto_free(Node2D.new())
	add_child(target)
	target.position = Vector2(30, 0)
	var enemy := _enemy("rusher", pool, target)
	enemy.take_hit(99, Vector2.LEFT)
	assert_bool(enemy.dead).is_true()
	assert_int(pool.count()).is_equal(0)

func test_overlapping_camps_cannot_exceed_the_global_cap() -> void:
	var first: SliceAttackSlots = auto_free(SliceAttackSlots.new())
	var second: SliceAttackSlots = auto_free(SliceAttackSlots.new())
	add_child(first)
	add_child(second)
	var a: Node = auto_free(Node.new())
	var b: Node = auto_free(Node.new())
	var c: Node = auto_free(Node.new())
	assert_bool(first.acquire(a)).is_true()
	assert_bool(second.acquire(b)).is_true()
	assert_bool(second.acquire(c)).is_false()
	first.release(a)
	assert_bool(second.acquire(c)).is_true()
	second.release(b)
	second.release(c)

class DamageTarget extends Node2D:
	var hits := 0
	func take_damage(_amount: int, _direction: Vector2) -> bool:
		hits += 1
		return true

func test_locked_lunge_misses_behind_and_hits_only_once_in_front() -> void:
	var pool: SliceAttackSlots = auto_free(SliceAttackSlots.new())
	add_child(pool)
	var target: DamageTarget = auto_free(DamageTarget.new())
	add_child(target)
	target.position = Vector2(20, 0)
	var enemy := _enemy("rusher", pool, target)
	enemy.step(enemy.windup_time())
	target.position = Vector2(-20, 0)
	enemy.step(0.01)
	assert_int(target.hits).is_equal(0)
	target.position = Vector2(20, 0)
	enemy.step(0.01)
	enemy.step(0.01)
	assert_int(target.hits).is_equal(1)

func test_shooter_cancels_if_it_leaves_the_view_during_its_tell() -> void:
	var pool: SliceAttackSlots = auto_free(SliceAttackSlots.new())
	add_child(pool)
	var target: Node2D = auto_free(Node2D.new())
	add_child(target)
	target.position = Vector2(90, 0)
	var enemy := _enemy("shooter", pool, target)
	var attacks := [0]
	enemy.released.connect(func() -> void: attacks[0] += 1)
	enemy.position = Vector2(-2000, 0)
	enemy.home = enemy.position
	target.position = enemy.position + Vector2(90, 0)
	enemy.step(enemy.windup_time())
	assert_str(enemy.state).is_equal("recover")
	assert_int(attacks[0]).is_equal(0)
	assert_int(pool.count()).is_equal(0)
	assert_object(enemy.shot).is_null()
