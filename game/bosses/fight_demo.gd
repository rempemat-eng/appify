class_name BossFightDemo
extends Node
## --bossfight (docs/godot.md): a scripted fight with the Thornback for screenshots and videos. The rooms'
## camp counts as cleared and the seal as open, the player starts at the arena's door and is healed whenever it runs low, then a simple pilot keeps its distance, sidesteps telegraphs (a roll across a charge's lane, away
## from a slam), and looses arrows while the boss recovers or staggers. --telegraph_shot=<png> saves the
## window halfway through the first wind-up and quits; --quit ends the run a few seconds after the freeing.

var game: Node
var player: Player
var boss: Thornback
var shot_path := ""
var quit_after := false
var _cool := 0.0
var _rolled_for := -1
var _freed_t := -1.0
var _windups := 0

static func prepare() -> void:
	SaveGame.set_flag("camp_cleared:undercroft_rooms")
	SaveGame.set_flag("undercroft_seal_open")
	SaveGame.set_flag("undercroft_plate")

func _physics_process(delta: float) -> void:
	if player == null or not is_instance_valid(player):
		return
	if boss == null or not is_instance_valid(boss):
		boss = get_tree().get_first_node_in_group("thornback_live") as Thornback
		if boss == null:
			return
		boss.telegraph_started.connect(func(_a: String, _s: float) -> void: _windups += 1)
	if player.hp < 3:
		player.heal_full()           # a demo, not a test of the pilot: it never goes down
	player.use_mouse_aim = false
	_cool = maxf(_cool - delta, 0.0)
	var to := boss.global_position - player.global_position
	var dist := to.length()
	player.aim = to.normalized()
	if shot_path != "" and boss.state == "windup" and boss.elapsed >= boss.windup_time * 0.55:
		_save_shot()
		return
	if boss.freed:
		_press(Vector2.ZERO)
		if _freed_t < 0.0:
			_freed_t = 0.0
			print("FREED after %d wind-ups" % _windups)
		_freed_t += delta
		if quit_after and _freed_t > 3.5:
			get_tree().quit()
		return
	var want := Vector2.ZERO
	var keep := 72.0 * 3.0
	if dist < keep * 0.8:
		want = -to.normalized()
	elif dist > keep * 1.3:
		want = to.normalized()
	else:
		want = to.normalized().orthogonal() * 0.8
	if boss.state == "windup":
		var k := boss.elapsed / boss.windup_time
		if boss.attack == "charge":
			want = boss.aim.orthogonal() * signf(boss.aim.orthogonal().dot(-to) + 0.001)
			if k > 0.7 and _rolled_for != _windups:
				_rolled_for = _windups
				player.start_roll(want)
		elif boss.attack == "slam":
			want = -to.normalized()
			if k > 0.75 and _rolled_for != _windups and dist < Thornback.SLAM_RADIUS * 1.2:
				_rolled_for = _windups
				player.start_roll(want)
	var centre := boss.arena.get_center() + boss._zone_origin() if boss.arena.size != Vector2.ZERO else player.global_position
	var off := player.global_position - centre
	if absf(off.x) > boss.arena.size.x * 0.4 or absf(off.y) > boss.arena.size.y * 0.38:
		want = (want - off.normalized() * 1.2).normalized()
	_press(want)
	if boss.state in ["recover", "stagger", "approach", "act"] and _cool <= 0.0 and not player.is_rolling():
		if boss.state != "act":
			if player.start_shot():
				_cool = 0.55

func _press(v: Vector2) -> void:
	for pair in [["move_right", v.x > 0.35], ["move_left", v.x < -0.35], ["move_down", v.y > 0.35], ["move_up", v.y < -0.35]]:
		if pair[1]:
			Input.action_press(pair[0])
		else:
			Input.action_release(pair[0])

func _save_shot() -> void:
	set_physics_process(false)
	await RenderingServer.frame_post_draw
	var img := get_tree().root.get_texture().get_image()
	if not game.frame_covered(img):
		push_error("telegraph shot: the world does not cover the frame")
		get_tree().quit(1)
		return
	var err := img.save_png(shot_path)
	print("SHOT %s %s %s (%s, %.2f of %.2f s)" % [shot_path, img.get_size(), error_string(err), boss.attack, boss.elapsed, boss.windup_time])
	get_tree().quit(0 if err == OK else 1)
