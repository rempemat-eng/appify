class_name RaidCreature
extends SliceEnemy
## A shardstruck raider (world/raid_night.gd): one of the woodland's creatures (rusher, shooter, shield,
## elite; dressed by CreatureDresser as the camps' are), drawn to the lit lantern. It adds a march to
## SliceEnemy and changes nothing in it:
##   - "leash" is its march (the state the look walks in): it walks the lane towards the lantern, steering
##     round solids (enemies/steer.gd). Idle hands straight over to it.
##   - A standing hurdle ahead, or the lantern once it is in reach, it batters with its own wind-up, so the
##     tell and the timing are the camps' (windup_time); the blow lands at the strike (RaidNight.batter_damage).
##   - The player near (RaidNight.notice), with nothing solid between, it turns on them with SliceEnemy's
##     own approach, wind-up and strike, under the shared cap of two (SliceAttackSlots). The toad looks over
##     low solids, as its spit flies (Arrow.walled_off), so it spits across a hurdle at the archer.
##   - Its "home" is where it left the lane, so the leash pulls it back to the road, not to the halt; a
##     chase given up, or a walk "home", sends it marching again at once.
##   - It came to town: it can always be hurt (no glancing for being out of a camp's reach).
## Freed, it plays the camps' freed look (CreatureLook, FreedCreature) and walks off: freed, not killed.
## It never targets a villager. It pays no fight Glint: the night's purse is the reward (core/raids.gd).

var night: RaidNight
var blocker: Node2D = null       ## the hurdle or the lantern it is battering
var lane_s := 0.0                ## how far along the lane it is (texels)
var _blow := false
var _leaving := false

func can_come_for(_at: Vector2) -> bool:
	return true

func _outside_leash() -> bool:
	if blocker != null:
		return false
	return super._outside_leash()

func _update_state(delta: float) -> void:
	if night == null or not is_instance_valid(night):
		super._update_state(delta)
		return
	match state:
		"idle":
			# a chase given up, the leash reached, a blow struck: back to the road, from wherever it stands
			# (the march starts on the next step: the state change zeroes the velocity after this returns)
			hsm.dispatch(&"leash")
		"leash":
			elapsed += delta
			_march(delta)
		"windup", "attack", "recover":
			if blocker != null:
				elapsed += delta
				_batter()
			else:
				super._update_state(delta)
		_:
			super._update_state(delta)

## True when it can see the player to come for them: nothing solid between for a striker, nothing that
## stops a shot for the toad.
func _sees(at: Vector2) -> bool:
	if role == "shooter":
		return not Arrow.walled_off(get_world_2d().direct_space_state, global_position, at)
	return EnemySteer.line_clear(self, at)

func _march(delta: float) -> void:
	home = global_position
	lane_s = night.progress(global_position)
	if night.is_over():
		velocity = Vector2.ZERO
		return
	if is_instance_valid(target) and _grace <= 0.0 and global_position.distance_to(target.global_position) < night.notice() \
			and _sees(target.global_position):
		hsm.dispatch(&"approach")
		return
	var block := night.blocker_ahead(self, lane_s)
	if block != null:
		blocker = block
		facing = global_position.direction_to(block.global_position) if global_position.distance_to(block.global_position) > 1.0 \
			else night.direction_at(lane_s)
		_blow = false
		hsm.dispatch(&"windup")
		return
	var goal := night.point_at(lane_s + 40.0 * DENSITY)
	var want := global_position.direction_to(goal)
	facing = want
	velocity = steer.direction(self, want, delta, goal) * night.march_speed()

func _batter() -> void:
	velocity = Vector2.ZERO
	if not is_instance_valid(blocker) or not blocker.call("standing"):
		blocker = null
		hsm.dispatch(&"leash")
		return
	match state:
		"windup":
			if elapsed >= windup_time():
				hsm.dispatch(&"attack")
		"attack":
			if not _blow:
				_blow = true
				blocker.call("batter", night.batter_damage(role), facing)
			if elapsed >= 0.18:
				hsm.dispatch(&"recover")
		"recover":
			if elapsed >= 0.65:
				blocker = null
				hsm.dispatch(&"leash")

## The night is lost: it stops, fades and goes (no freeing, no reward). Under reduced motion it goes at once.
func leave() -> void:
	if dead or _leaving:
		return
	_leaving = true
	dead = true
	_cancel_attack()
	hsm.set_active(false)
	collision_layer = 0
	velocity = Vector2.ZERO
	if SaveGame.setting("reduced_motion", false):
		queue_free()
		return
	var t := create_tween()
	t.tween_property(self, "modulate:a", 0.0, 0.5)
	t.tween_callback(queue_free)
