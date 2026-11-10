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
##   key <Name>              tap a key (Escape, E, Space, Enter, Down, ...)
##   hold <left|right|up|down|upleft|...> <secs>
##   aim x y, click, roll    the mouse at a world point, a left click, Space
##   wait <secs>
##   shot <name>             save <out>/<name>.png (the window, 960 x 540)
##   st, en, info            log the state, the enemies, everything in the zone
##   expect <what> ...       fail unless it holds:
##       zone <id> | quest <id> <none|active|done> [step id] | flag <f> | noflag <f> | focus <Node|none>
##       prompt <verb|none> | hp <n> | glint <n> | restored <id> | notrestored <id> | enemies <n>
##       at x y <tol> | hud <text|none> | said <text> | banner <text|none> | paused <yes|no>
##       line <text|none> (the line on the dialogue box now)
##   restart                 close the window as a player would; the runner starts the game again from the
##                           save and the route carries on at the next line
##   end                     pass (the end of the file passes too)
## A line starting with `?` is tried and logged but never fails the run.

const WalkGrid := preload("res://tools/walk_grid.gd")
const STUCK_AFTER := 9
const MAX_DOWNS := 4

var route_path := ""
var out_dir := "user://playtest"
var follow := false

var _lines: PackedStringArray = []
var _next := 0
var _busy := false
var _done := false
var _step := ""
var _held := {}
var _t0 := 0.0
var _hurt := 0
var _downs := 0
var _hooked: Node = null
var _said: PackedStringArray = []
var _grid: WalkGrid
var _grid_zone: Node = null

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	out_dir = ProjectSettings.globalize_path(out_dir)
	DirAccess.make_dir_recursive_absolute(out_dir)
	_t0 = Time.get_ticks_msec() / 1000.0
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

func now() -> float:
	return Time.get_ticks_msec() / 1000.0 - _t0

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
		"glint":
			return "" if int(SaveGame.data.glint) == int(a[2]) else "Glint is %d" % int(SaveGame.data.glint)
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

## Fights whatever is near: aims the mouse at the nearest enemy and clicks, steps or rolls sideways out
## of the lane of a telegraphed attack, closes in when out of range or when a wall is in the way.
## Downed, it walks back to where the fight began and goes on (up to MAX_DOWNS times; the log counts
## them). Ends when no enemy that can be walked to is left in the zone, or after `limit` seconds (a failure).
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
	var left := n0
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
		aim_at(near.global_position + Vector2(0, -24))
		var threat := _threat(p)
		if threat != null and not p.is_rolling():
			# out of the lane, to the side the player is already on (or the one with room)
			var dir := _attack_dir(threat, p)
			var rel := p.global_position - threat.global_position
			var side := (rel - dir * rel.dot(dir))
			side = side.normalized() if side.length() > 2.0 else dir.orthogonal()
			if not g.is_free(WalkGrid.cell_of(p.global_position + side * 60.0)):
				side = -side
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
			hold(want - p.global_position)
			await _sleep(0.15)
			continue
		hold(Vector2.ZERO)
		if not p.is_shooting() and not p.is_rolling():
			await click()
			shots += 1
		await _sleep(0.05)
	hold(Vector2.ZERO)
	out("FIGHT %.1fs enemies %d -> %d shots=%d rolls=%d hurt=%d downs=%d  %s" % [now() - start, n0, enemies().size(), shots, rolls, _hurt - hurt0, _downs - downs0, status()])
	if SaveGame.data.zone != zone:
		return "the zone changed during the fight"
	if _downs - downs0 > MAX_DOWNS:
		return "downed %d times in one fight" % (_downs - downs0)
	if now() - start >= limit:
		return "%d enemies were still near after %.0fs" % [left, limit]
	return ""

## Walks to within a few steps of the nearest enemy and takes every hit, to see what being downed does.
func down(limit: float) -> String:
	var p := player()
	var start := now()
	var downs0 := _downs
	var noted := now()
	var g := grid()
	g.forget()
	while now() - start < limit and _downs == downs0:
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
		elif best < 105.0:
			# a few steps off, not at its feet: within 83 texels the Thornback only throws thorns, and a
			# player standing between their eight lines is never hit (found by this driver, 10 Nov)
			var away := near.global_position.direction_to(p.global_position)
			if not g.is_free(WalkGrid.cell_of(p.global_position + away * 30.0)):
				away = away.orthogonal()
			hold(away)
		else:
			hold(Vector2.ZERO)
		await _sleep(0.1)
	hold(Vector2.ZERO)
	if _downs == downs0:
		return "not downed after %.0fs (hp %d)" % [limit, p.hp]
	await _sleep(1.0)
	out("DOWN after %.1fs -> %s" % [now() - start, status()])
	return ""
