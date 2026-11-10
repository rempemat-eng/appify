extends GdUnitTestSuite
## The story played in every order. From a fresh save in the woodland, this walks every state a player
## can reach by doing what the three built zones offer, in any order: talk to whoever is there (the
## Conditionals decide who), clear a camp, step on the plate, pull the lever, pay at a restore mark, walk
## through an open door. What is "there" is asked of the zone scenes themselves, and whether it can be
## walked to of the real walls (tools/walk_grid.gd), so the Undercroft's sealed slab counts.
##
## It then checks that the story cannot be broken by the order of things:
##   - from every state the end of this build can still be reached (nothing strands the player);
##   - a quest that can start can also finish (nothing half-starts: on 10 Nov *Bread for the Col hut* and
##     *The torn roof* started in play and waited on a camp and a restore mark that did not exist);
##   - the HUD always has a line (a tracked quest or a lead), and Glint never goes below zero;
##   - every line written for the three zones' people can show, apart from those listed with a reason.
##
## The model mirrors the game's own code paths (Dialogue.talk, RestoreSite.interact, SealLever.interact,
## PressurePlate.press, Camp._on_died, Door and Zones.go_to); fights are assumed won, since losing
## changes nothing but where the player stands.

const WalkGrid := preload("res://tools/walk_grid.gd")
const ZONES := ["woodland", "crossroads", "undercroft"]
## What this build's story is made of: with all of these done the closing card shows.
const PLAYABLE := ["woodland_stones", "road_to_crossroads", "cold_forge", "under_the_stones", "home_again",
	"a1_the_choked_well", "a1_the_torn_roof"]
const SLICE_FILES := ["woodland", "crossroads", "undercroft"]
## Lines that are written but cannot show in this build, each with its reason.
const SILENT := {
	"restore_forge|The forge is lit.": "the mark goes when the forge is restored (kept for a later tier)",
	"restore_fern_cottage|The door is clear.": "the mark goes when the door is cleared",
	"restore_fern_cottage|Rubble blocks the Ferns' door. Clearing it needs 20 Glint of timber.":
		"the player always has the 20 Glint by then (Under the stones pays 60)",
	"moss|The Ferns are home, their beds are dug, and the stall has customers again. I'd forgotten the sound of that.":
		"Moss's fallback once act 1's own lines run out; act 1 always has a line for her in this build",
}
const ARROW_REACH := 330.0
const MAX_STATES := 60000

var _things := {}       ## zone id -> Array of things (Dictionaries)
var _conds := {}        ## zone id -> Array of every Conditional's only_if in the zone (parsed, distinct)
var _reach := {}        ## "zone|truth of each cond" -> Array[bool], one per thing
var _shown := {}        ## "speaker|first line" -> true, every dialogue entry the walk showed

func before_test() -> void:
	SaveGame.reset()

func after_test() -> void:
	SaveGame.reset()

# --- what the zones offer -----------------------------------------------------------------------
func _scan() -> void:
	for id: String in ZONES:
		var zone: Node = (load(Zones.table[id]) as PackedScene).instantiate()
		_things[id] = []
		_conds[id] = []
		_scan_node(zone, id, Vector2.ZERO, [])
		zone.free()

func _scan_node(n: Node, zone: String, origin: Vector2, conds: Array) -> void:
	var at := origin + ((n as Node2D).position if n is Node2D else Vector2.ZERO)
	if n is Conditional and (n as Conditional).only_if != "":
		var cond: Variant = JSON.parse_string((n as Conditional).only_if)
		conds = conds + [cond]
		if not _conds[zone].has(cond):
			_conds[zone].append(cond)
	var thing := {}
	if n is RestoreSite:
		thing = {"kind": "restore", "id": n.restore_id, "speaker": n.speaker_id if n.speaker_id != "" else "restore_" + n.restore_id}
	elif n is SealLever:
		thing = {"kind": "lever", "speaker": n.speaker_id, "needs": n.needs_flag, "flag": n.flag}
	elif n is Interactable:
		thing = {"kind": "talk", "speaker": n.speaker_id}
	elif n is PressurePlate:
		thing = {"kind": "plate", "flag": n.flag, "shape": (n.get_node("Shape") as CollisionShape2D).shape}
	elif n is Camp:
		var homes := []
		for c in n.get_children():
			if c is Node2D:
				homes.append(at + (c as Node2D).position)
		thing = {"kind": "camp", "id": n.camp_id, "homes": homes}
	elif n is Door:
		var cond: Variant = JSON.parse_string(n.only_if) if n.only_if != "" else null
		thing = {"kind": "door", "to": n.target_zone, "spawn": n.target_spawn, "if": cond,
			"shape": (n.get_node("Shape") as CollisionShape2D).shape}
	if not thing.is_empty():
		thing.merge({"name": String(n.name), "at": at, "conds": conds})
		_things[zone].append(thing)
	for c in n.get_children():
		_scan_node(c, zone, at, conds)

## Which of the zone's things a walker from `start` can use in the save's present state. The walls only
## change with the zone's Conditionals, so the answer is kept per combination of their conditions.
func _reachable(zone_id: String) -> Array:
	var key := zone_id + "|"
	for cond: Variant in _conds[zone_id]:
		key += "1" if Quests.check(cond) else "0"
	if _reach.has(key):
		return _reach[key]
	var zone: Zone = (load(Zones.table[zone_id]) as PackedScene).instantiate()
	add_child(zone)
	for i in 3:
		await get_tree().physics_frame
	var grid := WalkGrid.new(zone.get_world_2d(), zone.bounds, 0.0)
	var cells := grid.reachable(zone.spawn_position("start"))
	var out: Array = []
	for thing: Dictionary in _things[zone_id]:
		out.append(_can_use(thing, cells, grid))
	remove_child(zone)
	zone.free()
	await get_tree().physics_frame
	_reach[key] = out
	return out

func _can_use(thing: Dictionary, cells: Dictionary, grid: WalkGrid) -> bool:
	var at: Vector2 = thing.at
	match thing.kind:
		"camp":
			for home: Vector2 in thing.homes:
				var n := ceili(ARROW_REACH / WalkGrid.CELL)
				var c0 := WalkGrid.cell_of(home)
				for dy in range(-n, n + 1, 3):
					for dx in range(-n, n + 1, 3):
						var c := c0 + Vector2i(dx, dy)
						if cells.has(c) and WalkGrid.point_of(c).distance_to(home) <= ARROW_REACH \
								and grid.clear_line(WalkGrid.point_of(c), WalkGrid.point_of(grid.nearest_free(home, 30.0))):
							return true
			return false
		"door", "plate":
			var half := Vector2.ONE * (WalkGrid.BODY_RADIUS - 1.0)
			var shape: Shape2D = thing.shape
			if shape is RectangleShape2D:
				half += (shape as RectangleShape2D).size / 2.0
			elif shape is CircleShape2D:
				half += Vector2.ONE * (shape as CircleShape2D).radius
			for c: Vector2i in cells:
				var d := (WalkGrid.point_of(c) + WalkGrid.BODY_OFFSET - at).abs()
				if d.x < half.x and d.y < half.y:
					return true
			return false
		_:
			var r := Interactable.REACH + WalkGrid.BODY_RADIUS - 1.0
			var n := ceili(r / WalkGrid.CELL) + 1
			var c0 := WalkGrid.cell_of(at)
			for dy in range(-n, n + 1):
				for dx in range(-n, n + 1):
					var c := c0 + Vector2i(dx, dy)
					if cells.has(c) and (WalkGrid.point_of(c) + WalkGrid.BODY_OFFSET).distance_to(at) < r:
						return true
			return false

# --- what doing each thing does (the game's own code paths, without the scene) ---------------------
func _say(speaker: String) -> void:
	var lines := Dialogue.lines_for(speaker)
	if not lines.is_empty():
		_shown["%s|%s" % [speaker, lines[0]]] = true

func _do(thing: Dictionary) -> void:
	match thing.kind:
		"talk":
			_say(thing.speaker)
			Quests.notify("talk:" + thing.speaker)
		"restore":
			var could := Village.can_restore(thing.id)
			_say(thing.speaker)
			Quests.notify("talk:" + thing.speaker)
			if could:
				Village.restore(thing.id)
		"lever":
			var ready: bool = SaveGame.has_flag(thing.needs) and not SaveGame.has_flag(thing.flag)
			_say(thing.speaker)
			Quests.notify("talk:" + thing.speaker)
			if ready:
				SaveGame.set_flag(thing.flag)
		"plate":
			SaveGame.set_flag(thing.flag)
		"camp":
			if not SaveGame.has_flag("camp_cleared:" + thing.id):
				SaveGame.set_flag("camp_cleared:" + thing.id)
				Quests.notify("camp:" + thing.id)
		"door":
			if Quests.check(thing["if"]) and Zones.has_zone(thing.to):
				SaveGame.data.zone = thing.to
				SaveGame.data.spawn = thing.spawn
				SaveGame.set_flag("visited:" + thing.to)
				Quests.notify("enter:" + thing.to)

func _key(data: Dictionary) -> String:
	var d := data.duplicate(true)
	for ignored: String in ["spawn", "tracked", "player", "settings", "version"]:
		d.erase(ignored)
	return JSON.stringify(d, "", true)

func _label(thing: Dictionary) -> String:
	match thing.kind:
		"talk", "lever": return "talk to %s" % thing.name
		"restore": return "pay at %s" % thing.name
		"plate": return "step on %s" % thing.name
		"camp": return "clear camp %s" % thing.id
		_: return "walk through %s" % thing.name

func _route(key: String, parent: Dictionary) -> String:
	var steps := []
	while parent.has(key):
		steps.append(parent[key][1])
		key = parent[key][0]
	steps.reverse()
	return " > ".join(steps) if steps.size() > 0 else "(the start)"

func test_the_story_holds_in_every_order() -> void:
	_scan()
	# a fresh game: in the woodland at `start`, as game.gd begins it
	SaveGame.reset()
	SaveGame.set_flag("visited:woodland")
	Quests.notify("enter:woodland")
	var first := _key(SaveGame.data)
	var states := {first: SaveGame.data.duplicate(true)}
	var order: Array[String] = [first]
	var parent := {}                 ## key -> [key before, what was done]
	var back := {}                   ## key -> keys that lead to it
	var problems := []
	var negative_glint := ""
	var silent_hud := ""
	var i := 0
	while i < order.size() and order.size() < MAX_STATES:
		var key := order[i]
		i += 1
		SaveGame.data = states[key].duplicate(true)
		var zone: String = SaveGame.data.zone
		if silent_hud == "" and Quests.tracked_text() == "":
			silent_hud = key
		var can: Array = await _reachable(zone)
		for t in _things[zone].size():
			SaveGame.data = states[key].duplicate(true)
			var thing: Dictionary = _things[zone][t]
			if not can[t] or not thing.conds.all(func(c: Variant) -> bool: return Quests.check(c)):
				continue
			_do(thing)
			var next := _key(SaveGame.data)
			if next == key:
				continue
			if not states.has(next):
				states[next] = SaveGame.data.duplicate(true)
				order.append(next)
				parent[next] = [key, _label(thing)]
				if negative_glint == "" and int(SaveGame.data.glint) < 0:
					negative_glint = next
			if not back.has(next):
				back[next] = []
			back[next].append(key)
	assert_int(order.size()).override_failure_message("the walk did not finish within %d states" % MAX_STATES).is_less(MAX_STATES)

	# which states can still reach a state where `test` holds
	var can_reach := func(test: Callable) -> Dictionary:
		var seen := {}
		var todo: Array = []
		for key: String in order:
			SaveGame.data = states[key]
			if test.call():
				seen[key] = true
				todo.append(key)
		while not todo.is_empty():
			var k: String = todo.pop_back()
			for before: String in back.get(k, []):
				if not seen.has(before):
					seen[before] = true
					todo.append(before)
		return seen

	# 1. the end of this build can be reached from everywhere
	var to_end: Dictionary = can_reach.call(func() -> bool: return PLAYABLE.all(func(q: String) -> bool: return Quests.state(q) == "done"))
	if to_end.is_empty():
		problems.append("no order of play finishes this build's quests (%s)" % ", ".join(PLAYABLE))
	else:
		for key: String in order:
			if not to_end.has(key):
				problems.append("stranded: after [%s] the build's quests can no longer all be finished" % _route(key, parent))
				break
	# 2. whatever starts can finish, from every state where it is active
	var started := {}
	for key: String in order:
		SaveGame.data = states[key]
		for q: String in Quests.defs:
			if Quests.state(q) != "none":
				started[q] = true
	for q: String in started:
		var can_finish: Dictionary = can_reach.call(func() -> bool: return Quests.state(q) == "done")
		for key: String in order:
			SaveGame.data = states[key]
			if Quests.state(q) == "active" and not can_finish.has(key):
				var step: String = Quests.current_step(q).get("id", "")
				problems.append("%s can start and then never finish: stuck at step '%s' (waiting on %s) after [%s]" % [
					q, step, Quests.current_step(q).get("on", ""), _route(key, parent)])
				break
		if not PLAYABLE.has(q):
			problems.append("%s can start in this build but is not listed as playable" % q)
	for q: String in PLAYABLE:
		if not started.has(q):
			problems.append("%s is listed as playable but no order of play starts it" % q)
	# 3. the HUD always says something, and Glint is never owed
	if silent_hud != "":
		problems.append("the HUD has no quest and no lead after [%s]" % _route(silent_hud, parent))
	if negative_glint != "":
		problems.append("Glint goes below zero after [%s]" % _route(negative_glint, parent))
	# 4. every line written for the three zones can show
	var silent := []
	var placed := {}
	for zone: String in ZONES:
		for thing: Dictionary in _things[zone]:
			if thing.has("speaker"):
				placed[thing.speaker] = true
	for file: String in SLICE_FILES:
		var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/dialogue/%s.json" % file))
		for speaker: String in doc:
			for entry: Dictionary in doc[speaker].get("entries", []):
				var id := "%s|%s" % [speaker, entry.lines[0]]
				if _shown.has(id):
					continue
				var excused := SILENT.has(id)
				if not placed.has(speaker):
					silent.append("%s: nobody with these lines stands in any zone" % speaker)
				elif not excused:
					silent.append("%s never says \"%s\"" % [speaker, String(entry.lines[0]).left(70)])
	problems.append_array(silent)
	for known: String in SILENT:
		if _shown.has(known):
			problems.append("\"%s\" is listed as a line that cannot show, but it shows" % known)
	print("story model: %d states, %d quests can start (%s)" % [order.size(), started.size(), ", ".join(started.keys())])
	SaveGame.reset()
	assert_array(problems).is_empty()
