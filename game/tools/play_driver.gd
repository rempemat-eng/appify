extends Node
## The play driver: plays the game through real input events (key presses to move, interact and roll,
## mouse motion and clicks to aim and shoot) from a route file, checks what it expects after each step
## and logs what it sees. game.gd adds it when the game is started with `-- --play=<route file>`:
##
##   --play=<file>       the route: one command a line (below), `#` starts a comment
##   --play-out=<dir>    where log.txt, result.txt, resume.txt and the pictures go (default user://playtest)
##   --play-follow       keep reading lines appended to the file instead of ending at its last line
##                       (steer a session by hand from a second terminal)
##
## It needs a display (Xvfb will do): headless Godot has no window to send the mouse to.
## tools/playtest.sh runs a route from a fresh save and restarts the game where the route says so.
##
## Commands (positions are global positions in texels, as the zone scenes have them):
##   step <text>             names what follows; a failure reports it
##   goto x y [tol]          walk there round the walls (fails when it does not arrive)
##   door x y <zone>         walk at a door until the zone changes to <zone>
##   talk [Node]             press E at the thing in reach and through its lines (fails with nothing
##                           in reach, or when the focus is not the named node)
##   fight [secs]            aim with the mouse, shoot, roll out of wind-ups, until no enemy that can be
##                           walked to is left in the zone
##   down [secs]             stand a few steps from the nearest enemy until downed, then get up
##   hurt [secs]             the same, but only until the first hit lands (hearts missing, not downed)
##   button <name or text>   move the mouse onto a visible on-screen button (its node name, or the start of
##                           its text) and click it, as a player would (the raid's prepare screen)
##   defend [secs] [x y [x2 y2]]  defend a raid's night from a station (default: here; the second once both
##                           hurdles are down) until it is over: shoots the raider nearest the lantern over the
##                           hurdles, walks out only for one it cannot hit
##   waitfor <secs> <what>   wait, standing, until `expect <what>` holds (fails after <secs>)
##   key <Name>              tap a key (Escape, E, Space, Enter, Down, ...)
##   hold <left|right|up|down|upleft|...> <secs>
##   aim x y, click, roll    the mouse at a world point, a left click, Space
##   wait <secs>
##   shot <name>             save <out>/<name>.png (the window, 960 x 540)
##   st, en, info            log the state, the enemies, everything in the zone
##   expect <what> ...       fail unless it holds:
##       zone <id> | quest <id> <none|active|done> [step id] | flag <f> | noflag <f> | focus <Node|none>
##       prompt <verb|none> | hp <n> | hurt (hearts missing) | glint <n> | restored <id> | notrestored <id> | enemies <n>
##       at x y <tol> | hud <text|none> | said <text> | banner <text|none> | paused <yes|no>
##       line <text|none> (the line on the dialogue box now)
##       raid <state> (core/raids.gd: none, announced, postponed, pending, running, won, lost) | raidscreen <yes|no>
##       defences <n> (hurdles standing) | repairs <yes|no> (the brief repairs after a lost night)
##       battering (a raider is battering a hurdle) | wave <n> (the night's wave under way, from 1)
##   restart                 close the window as a player would; the runner starts the game again from the
##                           save and the route carries on at the next line
##   end                     pass (the end of the file passes too)
## A line starting with `?` is tried and logged but never fails the run.

const WalkGrid := preload("res://tools/walk_grid.gd")
const STUCK_AFTER := 9
const MAX_DOWNS := 4
const DOOR_MARGIN := 36.0   # texels the fight pilot keeps between the player and an open door's trigger
const DODGE_REACH := 140.0  # how far a dodge may carry the player: a roll (about 100 texels) and the steps after it

var route_path := ""
var out_dir := "user://playtest"
var follow := false

var _lines: PackedStringArray = []
var _next := 0
var _busy := false
var _done := false
var _step := ""
var _held := {}
var _f0 := 0
var _hurt := 0
var _downs := 0
var _landed_t := 0.0            # game time of the player's last arrow that counted (hit_landed)
var _hooked: Node = null
var _said: PackedStringArray = []
var _grid: WalkGrid
var _grid_zone: Node = null
var _boss_attacks := 0          # the Thornback pilot (`_boss_turn`): wind-ups seen, the one last rolled for
var _boss_rolled_for := -1
var _boss_last := ""
var _doors: Array = []          # the current zone's Door nodes (`_door_rects`), found once per zone
var _doors_zone: Node = null
var _fighting := false         # while `fight` runs, `_process` keeps the nearest the player came to a door
var _fight_gap := 1e9
var _door_turns := 0           # how often `_door_safe` turned the pilot from a door (the FIGHT line logs it)

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	out_dir = ProjectSettings.globalize_path(out_dir)
	DirAccess.make_dir_recursive_absolute(out_dir)
	_f0 = Engine.get_physics_frames()
	Dialogue.opened.connect(func(speaker: String, lines: PackedStringArray) -> void:
		_said.append("%s: %s" % [speaker, " / ".join(lines)]))
	_read_route()
	var resume := out_dir.path_join("resume.txt")
	if FileAccess.file_exists(resume):
		var parts := FileAccess.get_file_as_string(resume).strip_edges().split("\t")
		_next = int(parts[0])
		_step = parts[1] if parts.size() > 1 else ""
		DirAccess.remove_absolute(resume)
		out("DRIVER resumed at line %d (%s)" % [_next + 1, _step])
	else:
		out("DRIVER ready: %s" % route_path)

func _read_route() -> void:
	if FileAccess.file_exists(route_path):
		_lines = FileAccess.get_file_as_string(route_path).split("\n")
	else:
		_finish(false, "no route file at '%s'" % route_path)

## Seconds of game time since the driver started, counted in physics steps and not on the wall clock:
## on a loaded machine the game runs slow, and a walk's limit must not run out because of that.
func now() -> float:
	return float(Engine.get_physics_frames() - _f0) / float(Engine.physics_ticks_per_second)

func out(s: String) -> void:
	var path := out_dir.path_join("log.txt")
	var f := FileAccess.open(path, FileAccess.READ_WRITE) if FileAccess.file_exists(path) else FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		return
	f.seek_end()
	f.store_line("[%7.1f] %s" % [now(), s])
	f.close()
	print("[play %7.1f] %s" % [now(), s])

func player() -> Player:
	return get_tree().get_first_node_in_group("player") as Player

func _sleep(secs: float) -> void:
	await get_tree().create_timer(secs, true).timeout

func _process(_d: float) -> void:
	if _done:
		return
	var p := player()
	if p != null and p != _hooked:
		_hooked = p
		p.hurt.connect(func(a: int) -> void:
			_hurt += a
			out("  HURT %d hp=%d" % [a, p.hp]))
		p.downed.connect(func() -> void:
			_downs += 1
			out("  DOWNED"))
		p.hit_landed.connect(func(_t: Node, _heavy: bool) -> void: _landed_t = now())
	if _fighting and p != null and p.is_inside_tree():
		_fight_gap = minf(_fight_gap, _door_gap(p.global_position))
	if _busy or p == null:
		return
	if follow:
		_read_route()
	while _next < _lines.size():
		var line := _lines[_next].strip_edges()
		_next += 1
		if line == "" or line.begins_with("#"):
			continue
		_busy = true
		await _run_line(line)
		_busy = false
		return
	if not follow:
		_finish(true, "route finished")

func _run_line(line: String) -> void:
	var soft := line.begins_with("?")
	if soft:
		line = line.substr(1).strip_edges()
	var problem: String = await run(line)
	if problem == "":
		return
	if soft:
		out("  WARN (not fatal) line %d `%s`: %s" % [_next, line, problem])
		return
	await shot("fail")
	_finish(false, "line %d `%s`%s: %s\n    %s" % [_next, line, (" in step \"%s\"" % _step) if _step != "" else "", problem, status()])

func _finish(ok: bool, why: String) -> void:
	if _done:
		return
	_done = true
	hold(Vector2.ZERO)
	out(("PASS " if ok else "FAIL ") + why)
	_write("result.txt", ("PASS " if ok else "FAIL ") + why + "\n")
	get_tree().quit(0 if ok else 1)

func _write(name: String, text: String) -> void:
	var f := FileAccess.open(out_dir.path_join(name), FileAccess.WRITE)
	if f != null:
		f.store_string(text)
		f.close()

# --- input ------------------------------------------------------------------------------------
func key(code: int, down: bool) -> void:
	var e := InputEventKey.new()
	e.keycode = code as Key
	e.physical_keycode = code as Key
	e.pressed = down
	Input.parse_input_event(e)

func tap(code: int) -> void:
	key(code, true)
	await _sleep(0.08)
	key(code, false)

## Holds the movement keys for a direction (zero lets go). Far away the direction is cut into eight;
## within a few texels the keys follow whichever axis is still off, so the walk can end on a point.
func hold(dir: Vector2, exact := false) -> void:
	var x := dir.x
	var y := dir.y
	var cut := 2.0
	if not exact and dir.length() > 0.001:
		var n := dir.normalized()
		x = n.x
		y = n.y
		cut = 0.38
	var want := {KEY_A: x < -cut, KEY_D: x > cut, KEY_W: y < -cut, KEY_S: y > cut}
	for k: int in want:
		if want[k] != _held.get(k, false):
			key(k, want[k])
			_held[k] = want[k]

func aim_at(world: Vector2) -> void:
	var p := player()
	var sv: Vector2 = p.get_viewport().get_canvas_transform() * world
	var main := get_tree().current_scene
	var screen: Vector2 = sv
	if main != null and main.get("screen") != null:
		screen = main.screen.position + sv * main.scale_k
	var e := InputEventMouseMotion.new()
	e.position = screen
	e.global_position = screen
	Input.parse_input_event(e)
	Input.warp_mouse(screen)

func click() -> void:
	var at := get_viewport().get_mouse_position()
	for down: bool in [true, false]:
		var e := InputEventMouseButton.new()
		e.button_index = MOUSE_BUTTON_LEFT
		e.pressed = down
		e.position = at
		e.global_position = at
		Input.parse_input_event(e)
		await _sleep(0.06)

# --- what it sees -----------------------------------------------------------------------------
func enemies() -> Array:
	var a := []
	for e in get_tree().get_nodes_in_group("enemy"):
		if is_instance_valid(e) and not e.get("dead") and e.is_inside_tree() and str(e.get("state")) != "freed":
			a.append(e)
	return a

func hud() -> Dictionary:
	var h := get_tree().get_first_node_in_group("hud")
	return h.shown_text() if h != null and h.has_method("shown_text") else {}

func focus_name() -> String:
	var p := player()
	return str(p.focus.name) if p != null and p.focus != null and is_instance_valid(p.focus) else "none"

func status() -> String:
	var p := player()
	var q := []
	for id: String in Quests.defs:
		var st: String = Quests.state(id)
		if st != "none":
			q.append("%s=%s%s" % [id, st, (":" + str(Quests.current_step(id).get("id", ""))) if st == "active" else ""])
	return "zone=%s pos=%s hp=%d glint=%s focus=%s enemies=%d quests=[%s] hud=%s" % [
		SaveGame.data.zone, p.global_position.round(), p.hp, SaveGame.data.get("glint", "?"),
		focus_name(), enemies().size(), ", ".join(q), JSON.stringify(hud())]

func _walk_tree(node: Node, depth: int, lines: Array) -> void:
	var p := player()
	if node is Area2D or node.is_in_group("enemy") or node is Marker2D:
		var kind := ""
		if node is Door:
			kind = "DOOR->%s/%s open=%s" % [node.target_zone, node.target_spawn, node.is_open()]
		elif node is RestoreSite:
			kind = "RESTORE %s cost=%d wants=%s" % [node.restore_id, Village.cost(node.restore_id), node.wants_talk()]
		elif node is Interactable:
			kind = "TALK %s verb=%s wants=%s" % [node.speaker_id, node.verb, node.wants_talk()]
		elif node.is_in_group("enemy"):
			kind = "ENEMY hp=%s role=%s" % [node.get("hp"), node.get("role")]
		elif node is Marker2D:
			kind = "MARK"
		elif node.get_script() != null:
			kind = "AREA " + String(node.get_script().resource_path).get_file()
		if kind != "":
			var g: Vector2 = node.global_position
			var hidden := "" if (node as CanvasItem).is_visible_in_tree() else " (hidden)"
			lines.append("%-28s %-48s at %s d=%d%s" % [node.name, kind, g.round(), int(g.distance_to(p.global_position)), hidden])
	for c in node.get_children():
		if depth < 7:
			_walk_tree(c, depth + 1, lines)

func shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_tree().root.get_texture().get_image()
	if img.get_width() > 960:
		img.resize(960, 540, Image.INTERPOLATE_BILINEAR)
	img.save_png(out_dir.path_join(name + ".png"))

func grid() -> WalkGrid:
	if _grid == null or _grid_zone != Zones.current:
		_grid_zone = Zones.current
		_grid = WalkGrid.new(player().get_world_2d(), Zones.current.bounds)
	return _grid

# --- commands ---------------------------------------------------------------------------------
## Runs one command; returns "" or what went wrong.
func run(c: String) -> String:
	var a := c.split(" ", false)
	var p := player()
	match a[0]:
		"step":
			_step = c.substr(5).strip_edges()
			out("STEP " + _step)
		"info":
			var lines := []
			_walk_tree(Zones.current, 0, lines)
			out("INFO " + status() + " bounds=%s\n    %s" % [Zones.current.bounds, "\n    ".join(lines)])
		"st":
			out("ST " + status())
		"en":
			var l := []
			for e: Node2D in enemies():
				l.append("%s hp=%s state=%s at %s d=%d" % [e.name, e.get("hp"), e.get("state"), e.global_position.round(), int(e.global_position.distance_to(p.global_position))])
			out("EN " + " | ".join(l))
		"wait":
			await _sleep(float(a[1]))
		"key":
			var code := OS.find_keycode_from_string(a[1])
			if code == KEY_NONE:
				return "no key named '%s'" % a[1]
			await tap(code)
			await _sleep(0.15)
			out("KEY %s" % a[1])
		"hold":
			var dirs := {"left": Vector2.LEFT, "right": Vector2.RIGHT, "up": Vector2.UP, "down": Vector2.DOWN,
				"upleft": Vector2(-1, -1), "upright": Vector2(1, -1), "downleft": Vector2(-1, 1), "downright": Vector2(1, 1)}
			if not dirs.has(a[1]):
				return "no direction '%s'" % a[1]
			var from := p.global_position
			hold(dirs[a[1]])
			await _sleep(float(a[2]))
			hold(Vector2.ZERO)
			out("HOLD %s %ss moved %s  %s" % [a[1], a[2], (p.global_position - from).round(), status()])
		"roll":
			await tap(KEY_SPACE)
			out("ROLL rolling=%s charges=%d" % [p.is_rolling(), p.roll_charges])
		"shot":
			await shot(a[1])
			out("SHOT %s  %s" % [a[1], status()])
		"goto":
			return await goto(Vector2(float(a[1]), float(a[2])), float(a[3]) if a.size() > 3 else 12.0)
		"door":
			return await goto(Vector2(float(a[1]), float(a[2])), 12.0, a[3])
		"talk":
			return await talk(a[1] if a.size() > 1 else "")
		"aim":
			aim_at(Vector2(float(a[1]), float(a[2])))
			await _sleep(0.15)
			out("AIM -> player.aim=%s" % p.aim)
		"click":
			await click()
			await _sleep(0.1)
			out("CLICK state=%s" % p.state)
		"fight":
			return await fight(float(a[1]) if a.size() > 1 else 90.0)
		"down":
			return await down(float(a[1]) if a.size() > 1 else 40.0)
		"caches":
			# walks over every cache of Glint lying in this zone (where the player went down: core/glint_cache.gd)
			for i in 8:
				var lying := GlintCache.in_zone(SaveGame.data.zone)
				if lying.is_empty():
					break
				var problem := await goto(Vector2(float(lying[0].x), float(lying[0].y)), 10.0)
				await get_tree().create_timer(0.3, true).timeout
				if problem != "" and not GlintCache.in_zone(SaveGame.data.zone).is_empty():
					return "the cache at (%d, %d): %s" % [int(lying[0].x), int(lying[0].y), problem]
			if not GlintCache.in_zone(SaveGame.data.zone).is_empty():
				return "a cache is still lying here"
			out("CACHES picked up; Glint %d" % int(SaveGame.data.glint))
		"hurt":
			return await down(float(a[1]) if a.size() > 1 else 40.0, true)
		"button":
			return await press_button(c.substr(7).strip_edges())
		"waitfor":
			var t0 := now()
			var want := PackedStringArray(["expect"]) + a.slice(2)
			while expect(want) != "":
				if now() - t0 > float(a[1]):
					return "after %ss: %s" % [a[1], expect(want)]
				await _sleep(0.1)
			out("WAITFOR %s held after %.1fs  %s" % [" ".join(a.slice(2)), now() - t0, status()])
		"defend":
			var at := Vector2(float(a[2]), float(a[3])) if a.size() > 3 else Vector2.INF
			var back := Vector2(float(a[4]), float(a[5])) if a.size() > 5 else Vector2.INF
			return await defend(float(a[1]) if a.size() > 1 else 300.0, at, back)
		"expect":
			var problem := expect(a)
			out(("  ok   %s" % c) if problem == "" else ("  MISS %s: %s" % [c, problem]))
			return problem
		"restart":
			_done = true
			hold(Vector2.ZERO)
			_write("resume.txt", "%d\t%s" % [_next, _step])
			out("RESTART (closing the window; the route carries on at line %d)" % (_next + 1))
			get_tree().root.propagate_notification(NOTIFICATION_WM_CLOSE_REQUEST)
			get_tree().quit(0)
		"end":
			_finish(true, "route finished")
		_:
			return "unknown command"
	return ""

func expect(a: PackedStringArray) -> String:
	var p := player()
	var rest := " ".join(a.slice(2))
	match a[1]:
		"zone":
			return "" if SaveGame.data.zone == a[2] and Zones.current != null and Zones.current.zone_id == a[2] else "the zone is %s" % SaveGame.data.zone
		"quest":
			var st: String = Quests.state(a[2])
			if st != a[3]:
				return "%s is %s" % [a[2], st]
			if a.size() > 4 and Quests.current_step(a[2]).get("id", "") != a[4]:
				return "%s is at step '%s'" % [a[2], Quests.current_step(a[2]).get("id", "")]
		"flag":
			return "" if SaveGame.has_flag(a[2]) else "the flag is not set"
		"noflag":
			return "the flag is set" if SaveGame.has_flag(a[2]) else ""
		"focus":
			return "" if focus_name() == a[2] else "the focus is %s" % focus_name()
		"prompt":
			var shown := str(hud().get("prompt", ""))
			return "" if (shown == "" and a[2] == "none") or shown == rest else "the HUD prompt shows '%s'" % shown
		"hp":
			return "" if p.hp == int(a[2]) else "hp is %d" % p.hp
		"hurt":
			return "" if p.hp > 0 and p.hp < p.max_hp else "hp is %d of %d" % [p.hp, p.max_hp]
		"glint":
			return "" if int(SaveGame.data.glint) == int(a[2]) else "Glint is %d" % int(SaveGame.data.glint)
		"cached":
			# the Glint lying in caches, everywhere (`expect cached 5`)
			var lying := 0
			for cache: Dictionary in SaveGame.data.caches:
				lying += int(cache.glint)
			return "" if lying == int(a[2]) else "%d Glint lies in %d caches" % [lying, (SaveGame.data.caches as Array).size()]
		"restored":
			return "" if Village.is_restored(a[2]) else "it is not restored"
		"notrestored":
			return "it is restored" if Village.is_restored(a[2]) else ""
		"enemies":
			return "" if enemies().size() == int(a[2]) else "%d enemies are up" % enemies().size()
		"at":
			var d := p.global_position.distance_to(Vector2(float(a[2]), float(a[3])))
			return "" if d <= float(a[4]) else "the player is %d texels from there, at %s" % [int(d), p.global_position.round()]
		"hud":
			var text := "%s: %s" % [hud().get("quest_title", ""), hud().get("quest_step", "")]
			if rest == "none":
				return "" if str(hud().get("quest_title", "")) == "" else "the HUD tracks '%s'" % text
			return "" if text.to_lower().contains(rest.to_lower()) else "the HUD tracks '%s'" % text
		"banner":
			var banner := str(hud().get("banner", ""))
			if rest == "none":
				return "" if banner == "" else "the banner shows '%s'" % banner
			return "" if banner.to_lower().contains(rest.to_lower()) else "the banner shows '%s'" % banner
		"said":
			var all := "\n".join(_said).to_lower()
			return "" if all.contains(rest.to_lower()) else "the last lines were: %s" % (" | ".join(_said) if _said.size() > 0 else "(nothing)")
		"paused":
			return "" if get_tree().paused == (a[2] == "yes") else "paused is %s" % get_tree().paused
		"raid":
			return "" if Raids.state() == a[2] else "the raid is %s" % Raids.state()
		"raidscreen":
			var screen := get_tree().get_first_node_in_group("raid_screen") as Control
			var up := screen != null and screen.is_visible_in_tree()
			return "" if up == (a[2] == "yes") else "the prepare screen is %s" % ("up" if up else "not up")
		"defences":
			var standing := 0
			for b in get_tree().get_nodes_in_group("raid_defence"):
				if b.has_method("standing") and b.standing():
					standing += 1
			return "" if standing == int(a[2]) else "%d hurdles stand" % standing
		"lantern":
			# the shard lantern during a raid: "unhurt" (and showing no lights), "hurt" (its lights up) or "gone"
			var lamp := get_tree().get_first_node_in_group("raid_lantern") as RaidLantern
			var is_now := "gone" if lamp == null else ("hurt" if lamp.hurt() else "unhurt")
			return "" if is_now == a[2] else "the lantern is %s" % is_now
		"battering":
			for c2 in get_tree().get_nodes_in_group("enemy"):
				if c2 is RaidCreature and not c2.dead and c2.blocker is RaidBarricade:
					return ""
			return "no raider is battering a hurdle"
		"wave":
			return "" if Raids.running() and int(Raids.rec().wave) + 1 == int(a[2]) else "the raid is %s at wave %d" % [Raids.state(), int(Raids.rec().wave) + 1]
		"repairs":
			var shown := not get_tree().get_nodes_in_group("raid_repair").filter(func(n: Node) -> bool: return not n.is_queued_for_deletion()).is_empty()
			return "" if shown == (a[2] == "yes") else "the repairs are %s" % ("shown" if shown else "not shown")
		"line":
			var box := get_tree().get_first_node_in_group("dialogue_box")
			var line: String = box.shown_line() if box != null else ""
			if rest == "none":
				return "" if line == "" else "the dialogue box shows '%s'" % line
			return "" if line.to_lower().contains(rest.to_lower()) else "the dialogue box shows '%s'" % line
		_:
			return "unknown expectation '%s'" % a[1]
	return ""

## Walks to `target` round the walls: plans on the walk grid, steers at the furthest point of the plan
## it can see, and plans again as it goes. With `until_zone` it walks until a door takes it there.
func goto(target: Vector2, tol: float, until_zone := "") -> String:
	var p := player()
	var start := now()
	var zone: String = SaveGame.data.zone
	var from := p.global_position
	var limit := 25.0 + from.distance_to(target) / 30.0
	var g := grid()
	g.forget()
	var plan := PackedVector2Array()
	var plan_t := -99.0
	var last := from
	var last_t := now()
	var stuck := 0
	var no_path := false
	var slack := 0.0
	while now() - start < limit:
		if SaveGame.data.zone != zone:
			break
		if not p.is_inside_tree() or Dialogue.busy or get_tree().paused:
			hold(Vector2.ZERO)
			await _sleep(0.1)
			continue
		var pos := p.global_position
		if until_zone == "" and pos.distance_to(target) <= tol:
			break
		if now() - plan_t > 0.5:
			plan = g.path(pos, target, maxf(tol - 5.0, 5.0))
			plan_t = now()
			if plan.is_empty():
				no_path = true
				break
		var want := target
		if not plan.is_empty():
			want = plan[0]
			for i in range(mini(plan.size(), 90) - 1, -1, -1):
				if g.clear_line(pos, plan[i]):
					want = plan[i]
					break
			if until_zone == "" and want == plan[plan.size() - 1] and pos.distance_to(want) < 3.0:
				slack = WalkGrid.CELL   # as near as the walk grid gets: a cell's width of grace
				break
			if want == plan[plan.size() - 1] and g.clear_line(pos, target):
				want = target
		var to := want - pos
		hold(to, to.length() < 9.0)
		await _sleep(0.05)
		if now() - last_t > 1.0:
			if p.global_position.distance_to(last) < 5.0 and not Dialogue.busy and not p.is_defeated():
				stuck += 1
				if stuck > STUCK_AFTER:
					break
				var side := Vector2(-to.y, to.x).normalized() * (1.0 if stuck % 2 == 1 else -1.0)
				hold(side)
				await _sleep(0.2 + 0.1 * stuck)
			last = p.global_position
			last_t = now()
	hold(Vector2.ZERO)
	var changed: bool = SaveGame.data.zone != zone
	var dist := p.global_position.distance_to(target)
	var ok: bool = (changed and SaveGame.data.zone == until_zone) if until_zone != "" else (not changed and dist <= tol + slack)
	var how := "ok" if ok else ("ZONE-CHANGED" if changed else ("NO-PATH" if no_path else "FAILED"))
	out("%s %s %s in %.1fs walked=%d sidesteps=%d  %s" % ["DOOR" if until_zone != "" else "GOTO", target, how, now() - start, int(from.distance_to(p.global_position)), stuck, status()])
	if ok:
		if changed:
			await _sleep(0.6)   # the new zone's first frames; its doors arm after 0.4 s
		return ""
	if until_zone != "":
		return "walked at the door for %.0fs and the zone is still %s" % [now() - start, SaveGame.data.zone] if not changed else "the door led to %s" % SaveGame.data.zone
	if changed:
		return "a door took the player to %s on the way" % SaveGame.data.zone
	return "%s: stopped %d texels short at %s" % ["the walk grid has no way there" if no_path else "did not arrive", int(dist), p.global_position.round()]

## The visible button named `what` (its node name, or the start of its text, either case), or null.
func _find_button(node: Node, what: String) -> BaseButton:
	if node is BaseButton and (node as CanvasItem).is_visible_in_tree():
		var b := node as BaseButton
		var text := String(b.get("text")) if b.get("text") != null else ""
		if String(b.name) == what or (text != "" and text.to_lower().begins_with(what.to_lower())):
			return b
	for c in node.get_children():
		var found := _find_button(c, what)
		if found != null:
			return found
	return null

## Moves the mouse onto a button and clicks it with real mouse events, through the pixel screen's scale.
func press_button(what: String) -> String:
	var b := _find_button(get_tree().root, what)
	if b == null:
		return "no visible button '%s'" % what
	var centre := b.get_global_rect().get_center()      # in the game's 960 x 540 art grid
	var main := get_tree().current_scene
	var screen := centre
	if main != null and main.get("screen") != null:
		screen = main.screen.position + centre * main.scale_k
	var move := InputEventMouseMotion.new()
	move.position = screen
	move.global_position = screen
	Input.parse_input_event(move)
	Input.warp_mouse(screen)
	await _sleep(0.1)
	for down: bool in [true, false]:
		var e := InputEventMouseButton.new()
		e.button_index = MOUSE_BUTTON_LEFT
		e.pressed = down
		e.position = screen
		e.global_position = screen
		Input.parse_input_event(e)
		await _sleep(0.08)
	await _sleep(0.2)
	out("BUTTON %s  raid=%s  %s" % [what, Raids.state(), status()])
	return ""

## Defends a raid's night until it is over (won or lost) or `limit` seconds pass, as a player at the lantern
## would: it holds `station` (default where it stands) and shoots the raider nearest the lantern whenever an
## arrow can reach it (Arrow.walled_off: arrows fly over the hurdles, which are low solids), so it hits them
## where they batter a hurdle it cannot walk through. It walks out only for a raider it cannot hit from where
## it stands, and steps or rolls out of the lane of a telegraphed attack as `fight` does.
## The line of fire is tested feet to feet, where the arrow flies and hits (actors/arrow.gd: the arrow's node
## runs on the ground under the drawn shaft, parallel to the aim from the archer's chest to the target's), so
## a raider backed against a wall is shot like any other.
## With `fallback` given, it holds `station` while a hurdle stands and `fallback` once both are down (a player
## falls back to what they defend). It never chases off after the nearest raider, as `fight` does: the lantern
## falls in seconds once raiders reach it. Point blank it shoots only the toad, which spits from where it stands.
## A raider coming for it within COMING is shot first, nearest first; otherwise the raider nearest the lantern.
## It never gives ground (backing off, bounded or not, let the raiders take the lantern). Its dodges and walks
## keep clear of open doors (`_door_safe`, as `fight`'s). Each hurt is logged with the raiders near it.
## It fails, saying so, when raiders are up and no arrow has counted for STALL seconds.
const STALL := 30.0
const BESIDE := 60.0
const COMING := 200.0               ## a raider coming for the archer this near is shot first

func defend(limit: float, station := Vector2.INF, fallback := Vector2.INF) -> String:
	var p := player()
	var start := now()
	if station == Vector2.INF:
		station = p.global_position
	var shots := 0
	var rolls := 0
	var hurt0 := _hurt
	var g := grid()
	var held := station
	var hurt_seen := _hurt
	_landed_t = now()
	while now() - start < limit and Raids.running():
		if not p.is_inside_tree() or p.is_defeated():
			hold(Vector2.ZERO)
			await _sleep(0.2)
			continue
		var es := enemies()
		if es.is_empty():
			_landed_t = now()                          # between waves nothing is there to hit
			if p.global_position.distance_to(station) > 30.0:
				await goto(station, 20.0)
			else:
				hold(Vector2.ZERO)
				await _sleep(0.2)
			continue
		var lantern := get_tree().get_first_node_in_group("raid_lantern") as Node2D
		var guard := lantern.global_position if lantern != null else station
		# the target: a raider coming for the archer, nearest first (a player shoots what is about to hit them);
		# else the raider nearest the lantern
		var target: Node2D = null
		for e: Node2D in es:
			if str(e.get("state")) in ["approach", "windup", "attack"] and e.global_position.distance_to(p.global_position) < COMING \
					and (target == null or e.global_position.distance_to(p.global_position) < target.global_position.distance_to(p.global_position)):
				target = e
		if target == null:
			target = es[0]
			for e: Node2D in es:
				if e.global_position.distance_to(guard) < target.global_position.distance_to(guard):
					target = e
		var threat := _threat(p)
		if threat != null and not p.is_rolling():
			var dir := _attack_dir(threat, p)
			var rel := p.global_position - threat.global_position
			var side := rel - dir * rel.dot(dir)
			side = side.normalized() if side.length() > 2.0 else dir.orthogonal()
			if not g.is_free(WalkGrid.cell_of(p.global_position + side * 60.0)):
				side = -side
			side = _door_safe(p.global_position, side, DODGE_REACH)   # never dodge towards a door (as fight)
			hold(side)
			if p.roll_charges > 0:
				await _sleep(0.03)
				await tap(KEY_SPACE)
				rolls += 1
				await _sleep(0.28)
			else:
				await _sleep(0.12)
			continue
		# the station: by the street's mouth while a hurdle stands; once both are down, beside the lantern, where
		# the lane's last leg and the strike spot are in sight
		var night := Zones.current.get_node_or_null("RaidNight") as RaidNight
		var standing := false
		if night != null:
			for b: RaidBarricade in night.barricades:
				if is_instance_valid(b) and b.standing():
					standing = true
		station = held if standing or fallback == Vector2.INF else fallback
		# hurt: say by whom, so a lost night can be read from the log
		if _hurt != hurt_seen:
			hurt_seen = _hurt
			var near := []
			for e: Node2D in es:
				if e.global_position.distance_to(p.global_position) < 200.0:
					near.append("%s %s %d" % [e.name, e.get("state"), int(e.global_position.distance_to(p.global_position))])
			out("  defend: hurt at %s by one of [%s]" % [p.global_position.round(), ", ".join(near)])
		if now() - _landed_t > STALL:
			hold(Vector2.ZERO)
			return "no arrow has counted for %.0fs with %d raiders up: %s %s at %s, the archer at %s" % [
				STALL, es.size(), target.name, target.get("state"), target.global_position.round(), p.global_position.round()]
		var space := p.get_world_2d().direct_space_state
		var aim := target.global_position + Vector2(0, -24)
		var d := p.global_position.distance_to(target.global_position)
		var point_blank := d <= BESIDE and str(target.get("role")) == "shooter"
		if point_blank or (d <= 320.0 and not Arrow.walled_off(space, p.global_position, target.global_position)):
			hold(Vector2.ZERO)
			aim_at(aim)
			if not p.is_shooting() and not p.is_rolling():
				await click()
				shots += 1
			await _sleep(0.05)
			continue
		# out of reach from here: to whichever station it can be hit from (this one first), else after it
		var goal := target.global_position
		for st: Vector2 in [station, held, fallback]:
			if st != Vector2.INF and st.distance_to(target.global_position) <= 320.0 \
					and not Arrow.walled_off(space, st, target.global_position):
				goal = st
				break
		if goal != target.global_position and p.global_position.distance_to(goal) > 30.0:
			# to that station with the routes' own walker (plans round the well, sidesteps when stuck)
			await goto(goal, 24.0)
			continue
		var plan := g.path(p.global_position, goal, 30.0)
		var want := goal
		for i in range(mini(plan.size(), 60) - 1, -1, -1):
			if g.clear_line(p.global_position, plan[i]):
				want = plan[i]
				break
		hold(_door_safe(p.global_position, want - p.global_position, 40.0))
		await _sleep(0.15)
	hold(Vector2.ZERO)
	out("DEFEND %.1fs raid=%s shots=%d rolls=%d hurt=%d  %s" % [now() - start, Raids.state(), shots, rolls, _hurt - hurt0, status()])
	if Raids.running():
		return "the night was still on after %.0fs" % limit
	return ""

## Presses E at the focus and on through every line. Fails when nothing is in reach.
func talk(expected: String) -> String:
	var p := player()
	if p.focus == null or not is_instance_valid(p.focus):
		out("TALK no focus  " + status())
		return "nothing is in reach (no prompt)"
	var who := focus_name()
	if expected != "" and who != expected:
		return "the thing in reach is %s" % who
	var presses := 0
	var start := now()
	_said.clear()
	await tap(KEY_E)
	presses += 1
	await _sleep(0.4)
	while Dialogue.busy and presses < 80:
		await tap(KEY_E)
		presses += 1
		await _sleep(0.3)
	await _sleep(0.25)
	out("TALK %s presses=%d %.1fs\n    %s\n    -> %s" % [who, presses, now() - start, "\n    ".join(_said), status()])
	if Dialogue.busy:
		return "the dialogue did not close after %d presses" % presses
	return ""

## The direction an enemy's telegraphed attack will go: mosslings lock `attack_dir` when they wind up,
## the Undercroft's creatures lock `facing`; anything else is taken to come straight at the player.
func _attack_dir(e: Node2D, p: Node2D) -> Vector2:
	for prop: String in ["attack_dir", "facing"]:
		var v: Variant = e.get(prop)
		if v is Vector2 and (v as Vector2).length() > 0.1:
			return (v as Vector2).normalized()
	return e.global_position.direction_to(p.global_position)

## The enemy about to hit the player, if any: winding up or striking, with the player in its lane.
func _threat(p: Node2D) -> Node2D:
	var worst: Node2D = null
	var worst_d := 1e9
	for e: Node2D in enemies():
		var st := str(e.get("state"))
		if st != "windup" and st != "lunge" and st != "attack" and st != "act":
			continue
		var boss := e.get("arena") != null
		var rel := p.global_position - e.global_position
		var dir := _attack_dir(e, p)
		var along := rel.dot(dir)
		var across := absf(rel.cross(dir))
		var d := rel.length()
		var in_lane := along > -24.0 and along < (460.0 if boss else (360.0 if str(e.get("role")) == "shooter" else 150.0)) \
			and across < (70.0 if boss else 44.0)
		if (in_lane or (boss and d < 150.0)) and d < worst_d:
			worst = e
			worst_d = d
	return worst

## The triggers of the zone's open doors, made global and grown by DOOR_MARGIN. A door takes whoever enters
## it (world/door.gd), mid-fight too, as it should: a player may leave a fight that way. The fight pilot must
## not do it by accident, and its dodges did: the meadow camp is some 200 texels from the door to Crossroads,
## and a roll and the steps after it carry the player about 140 (12 Nov).
func _door_rects() -> Array[Rect2]:
	if _doors_zone != Zones.current:
		_doors_zone = Zones.current
		_doors = []
		var todo: Array[Node] = []
		if Zones.current != null:
			todo.append(Zones.current)
		while not todo.is_empty():
			var n: Node = todo.pop_back()
			if n is Door:
				_doors.append(n)
			todo.append_array(n.get_children())
	var rects: Array[Rect2] = []
	for d in _doors:
		if not is_instance_valid(d) or not (d as Door).is_open():
			continue
		for s in (d as Node).get_children():
			var cs := s as CollisionShape2D
			if cs != null and cs.shape != null and not cs.disabled:
				rects.append((cs.global_transform * cs.shape.get_rect()).grow(DOOR_MARGIN))
	return rects

## Whether going `reach` texels from `from` along `dir` comes near a door. A door the player already stands
## near only counts when `dir` leads closer to it.
func _door_on_way(from: Vector2, dir: Vector2, reach: float, rects: Array[Rect2]) -> bool:
	if dir.length() < 0.001:
		return false
	var n := dir.normalized()
	for r: Rect2 in rects:
		if r.has_point(from):
			if n.dot(from - r.get_center()) <= 0.0:
				return true
			continue
		var t := 0.0
		while t <= reach:
			if r.has_point(from + n * t):
				return true
			t += 6.0
	return false

## `dir` when going that way for `reach` texels keeps clear of the doors; otherwise the nearest turn of it
## that does and is open ground; otherwise straight away from the nearest door.
func _door_safe(from: Vector2, dir: Vector2, reach: float) -> Vector2:
	var rects := _door_rects()
	if rects.is_empty() or not _door_on_way(from, dir, reach, rects):
		return dir
	_door_turns += 1
	var g := grid()
	for turn: float in [PI / 4.0, -PI / 4.0, PI / 2.0, -PI / 2.0, 3.0 * PI / 4.0, -3.0 * PI / 4.0, PI]:
		var d := dir.normalized().rotated(turn)
		if not _door_on_way(from, d, reach, rects) and g.is_free(WalkGrid.cell_of(from + d * minf(reach, 60.0))):
			return d
	return _away_from_doors(from, rects)

## Texels from `at` to the nearest open door's trigger (its own rect, without the margin); 1e9 with none.
func _door_gap(at: Vector2) -> float:
	var gap := 1e9
	for r: Rect2 in _door_rects():
		var raw := r.grow(-DOOR_MARGIN)
		gap = minf(gap, at.distance_to(at.clamp(raw.position, raw.end)))
	return gap

func _away_from_doors(from: Vector2, rects: Array) -> Vector2:
	var best := Vector2.ZERO
	var best_d := 1e9
	for r: Rect2 in rects:
		var d := from.distance_to(r.get_center())
		if d < best_d:
			best_d = d
			best = r.get_center().direction_to(from)
	return best

## Fights whatever is near: aims the mouse at the nearest enemy and clicks, steps or rolls sideways out
## of the lane of a telegraphed attack, closes in when out of range or when a wall is in the way.
## Downed, it walks back to where the fight began and goes on (up to MAX_DOWNS times; the log counts
## them). It never dodges or closes in towards a door, and steps out of DOOR_MARGIN of one first.
## Ends when no enemy that can be walked to is left in the zone, or after `limit` seconds (a failure).
func fight(limit: float) -> String:
	var p := player()
	var start := now()
	var hurt0 := _hurt
	var downs0 := _downs
	var seen_downs := _downs
	var n0 := enemies().size()
	var shots := 0
	var rolls := 0
	var zone: String = SaveGame.data.zone
	var anchor := p.global_position
	var g := grid()
	g.forget()
	var ground := g.reachable(p.global_position)   # enemies behind a closed wall are not this fight's
	_boss_attacks = 0
	_boss_rolled_for = -1
	_boss_last = ""
	var left := n0
	var turns0 := _door_turns
	_fight_gap = 1e9
	_fighting = true
	while now() - start < limit and SaveGame.data.zone == zone:
		if _downs != seen_downs:
			seen_downs = _downs
			if _downs - downs0 > MAX_DOWNS:
				break
			hold(Vector2.ZERO)
			await _sleep(1.2)
			out("  fight: downed (%d), walking back to %s" % [_downs - downs0, anchor.round()])
			await goto(anchor, 30.0)
			g.forget()
			continue
		if not p.is_inside_tree() or p.is_defeated():
			hold(Vector2.ZERO)
			await _sleep(0.2)
			continue
		var near: Node2D = null
		var best := 1e9
		left = 0
		for e: Node2D in enemies():
			var d: float = e.global_position.distance_to(p.global_position)
			if not ground.has(g.nearest_free(e.global_position, 40.0)):
				continue
			left += 1
			if d < best:
				best = d
				near = e
		if near == null:
			break
		if near is Thornback:
			rolls += await _boss_turn(p, near as Thornback)
			continue
		aim_at(near.global_position + Vector2(0, -24))
		var out_of_door := _away_from_doors(p.global_position, _door_rects().filter(
			func(r: Rect2) -> bool: return r.has_point(p.global_position)))
		if out_of_door != Vector2.ZERO and not p.is_rolling():
			_door_turns += 1
			hold(out_of_door)   # too near a door: out of its margin before anything else
			await _sleep(0.12)
			continue
		var threat := _threat(p)
		if threat != null and not p.is_rolling():
			# out of the lane, to the side the player is already on (or the one with room)
			var dir := _attack_dir(threat, p)
			var rel := p.global_position - threat.global_position
			var side := (rel - dir * rel.dot(dir))
			side = side.normalized() if side.length() > 2.0 else dir.orthogonal()
			if not g.is_free(WalkGrid.cell_of(p.global_position + side * 60.0)):
				side = -side
			side = _door_safe(p.global_position, side, DODGE_REACH)
			hold(side)
			if p.roll_charges > 0 and (p.is_shooting() or str(threat.get("state")) != "windup" or threat.get("arena") != null or p.roll_charges == Player.ROLL_CHARGES):
				await _sleep(0.03)
				await tap(KEY_SPACE)
				rolls += 1
				await _sleep(0.28)
			else:
				await _sleep(0.12)
			continue
		var sight := g.clear_line(p.global_position, near.global_position) or best < 40.0
		if best > 330.0 or not sight:
			var plan := g.path(p.global_position, near.global_position, 40.0)
			var want := near.global_position
			for i in range(mini(plan.size(), 60) - 1, -1, -1):
				if g.clear_line(p.global_position, plan[i]):
					want = plan[i]
					break
			hold(_door_safe(p.global_position, want - p.global_position, 40.0))
			await _sleep(0.15)
			continue
		hold(Vector2.ZERO)
		if not p.is_shooting() and not p.is_rolling():
			await click()
			shots += 1
		await _sleep(0.05)
	hold(Vector2.ZERO)
	_fighting = false
	var gap := _fight_gap
	out("FIGHT %.1fs enemies %d -> %d shots=%d rolls=%d hurt=%d downs=%d door_turns=%d nearest_door=%s  %s" % [now() - start, n0, enemies().size(), shots, rolls, _hurt - hurt0, _downs - downs0, _door_turns - turns0, ("%d" % gap) if gap < 1e8 else "none", status()])
	if SaveGame.data.zone != zone:
		return "the zone changed during the fight"
	if _downs - downs0 > MAX_DOWNS:
		return "downed %d times in one fight" % (_downs - downs0)
	if now() - start >= limit:
		return "%d enemies were still near after %.0fs" % [left, limit]
	return ""

## One turn of the fight against the Thornback (bosses/thornback.gd), which the general pilot above loses:
## it now charges a player who stays close and heals 3 s after the player has left its arena. Rolls across
## a charge as it commits or arrives, away from a slam, across a thorn; keeps 170 to 320 texels off and
## inside the arena (outside it its arrows glance); shoots when it is standing still. Returns the rolls.
func _boss_turn(p: Node2D, b: Thornback) -> int:
	var st := b.state
	if st == "windup" and _boss_last != "windup":
		_boss_attacks += 1
	_boss_last = st
	var to := p.global_position - b.global_position
	var d := to.length()
	var want := Vector2.ZERO
	if st == "windup" and b.attack == "charge" and d < 150.0 and b.elapsed >= b.windup_time - 0.12:
		want = to.normalized().rotated(1.4)
	elif st == "act" and b.attack == "charge" and d < 135.0:
		want = b.aim.rotated(1.5708 if b.aim.cross(to) > 0.0 else -1.5708)
	elif st == "windup" and b.attack == "slam" and d < 130.0 and b.elapsed >= b.windup_time - 0.3:
		want = to.normalized()
	else:
		for th: Node in b.thorns:
			if is_instance_valid(th):
				var rel: Vector2 = p.global_position + Vector2(0, -4) - (th as Node2D).global_position
				var dir: Vector2 = th.get("direction")
				if rel.length() < 55.0 and rel.dot(dir) > 0.0 and absf(dir.cross(rel)) < 24.0:
					want = dir.rotated(1.5708 if dir.cross(rel) > 0.0 else -1.5708)
	var arena := Rect2(b.arena.position + b._zone_origin(), b.arena.size)   # texels in the zone, made global
	var centre := arena.get_center() if arena.size != Vector2.ZERO else b.global_position
	if want != Vector2.ZERO and _boss_attacks != _boss_rolled_for and p.roll_charges > 0 and not p.is_rolling():
		want = _door_safe(p.global_position, want, DODGE_REACH)   # never towards a door; the arena still wins
		if arena.size != Vector2.ZERO and not arena.grow(-20.0).has_point(p.global_position + want * 100.0):
			want = -want if arena.grow(-20.0).has_point(p.global_position - want * 100.0) else (centre - p.global_position).normalized()
		if b.attack != "volley":
			_boss_rolled_for = _boss_attacks
		hold(want)
		await _sleep(0.03)
		await tap(KEY_SPACE)
		await _sleep(0.3)
		hold(Vector2.ZERO)
		return 1
	aim_at(b.global_position + Vector2(0, -24))
	var move := Vector2.ZERO
	var safe := arena.grow(-45.0)
	if arena.size != Vector2.ZERO and (not safe.has_point(p.global_position) or not b.player_in_arena()):
		move = (centre - p.global_position).normalized()      # never leave the arena: walk back in
	elif d < 170.0 and st != "stagger":
		move = to.normalized()
		if arena.size != Vector2.ZERO and not safe.has_point(p.global_position + move * 30.0):
			# cornered: slip along the wall, towards the roomier side
			var l := move.rotated(1.5708)
			var r := move.rotated(-1.5708)
			move = l if (centre - p.global_position).dot(l) > 0.0 else r
	elif d > 320.0:
		move = -to.normalized()
	if move != Vector2.ZERO:
		move = _door_safe(p.global_position, move, 40.0)
	hold(move)
	if move == Vector2.ZERO and not p.is_shooting() and not p.is_rolling():
		await click()
	await _sleep(0.04)
	return 0

func _near_a_door(at: Vector2) -> bool:
	var doors := Zones.current.get_node_or_null("Doors")
	if doors != null:
		for d in doors.get_children():
			if d is Node2D and (d as Node2D).global_position.distance_to(at) < 110.0:
				return true
	return false

## Walks to within a few steps of the nearest enemy and takes every hit, to see what being downed does.
func down(limit: float, first_hit_only := false) -> String:
	var p := player()
	var start := now()
	var downs0 := _downs
	var noted := now()
	var g := grid()
	g.forget()
	var zone: String = SaveGame.data.zone
	while now() - start < limit and _downs == downs0:
		if first_hit_only and p.hp < p.max_hp:
			break
		if SaveGame.data.zone != zone:
			hold(Vector2.ZERO)
			return "walked out of %s while waiting to be downed" % zone
		var near: Node2D = null
		var best := 1e9
		for e: Node2D in enemies():
			var d: float = e.global_position.distance_to(p.global_position)
			if d < best:
				best = d
				near = e
		if near == null:
			hold(Vector2.ZERO)
			return "no enemy is left to be downed by"
		if now() - noted > 5.0:
			noted = now()
			out("  down: %s is %d texels away, %s; hp %d" % [near.name, int(best), near.get("state"), p.hp])
		if not p.is_inside_tree() or p.is_defeated():
			hold(Vector2.ZERO)
		elif best > 170.0:
			var plan := g.path(p.global_position, near.global_position, 130.0)
			var want := near.global_position
			for i in range(mini(plan.size(), 60) - 1, -1, -1):
				if g.clear_line(p.global_position, plan[i]):
					want = plan[i]
					break
			hold(want - p.global_position)
		elif best < 105.0 and near.get("arena") != null:
			# a few steps off, not at its feet: within 83 texels the Thornback only throws thorns, and a
			# player standing between their eight lines is never hit (found by this driver, 10 Nov)
			var away := near.global_position.direction_to(p.global_position)
			for turn: float in [0.0, PI / 2.0, -PI / 2.0, PI]:
				var to := p.global_position + away.rotated(turn) * 30.0
				if g.is_free(WalkGrid.cell_of(to)) and not _near_a_door(to):
					away = away.rotated(turn)
					break
			hold(away)
		else:
			hold(Vector2.ZERO)
		await _sleep(0.1)
	hold(Vector2.ZERO)
	if first_hit_only:
		out("HURT after %.1fs -> %s" % [now() - start, status()])
		return "" if p.hp < p.max_hp and _downs == downs0 else "not hurt after %.0fs (hp %d, downed %d times)" % [limit, p.hp, _downs - downs0]
	if _downs == downs0:
		return "not downed after %.0fs (hp %d)" % [limit, p.hp]
	await _sleep(1.0)
	out("DOWN after %.1fs -> %s" % [now() - start, status()])
	return ""
