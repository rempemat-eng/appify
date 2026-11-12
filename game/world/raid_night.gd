class_name RaidNight
extends Node2D
## One raid played in its zone (core/raids.gd keeps its state in the save; data/raids/<id>.json holds its
## numbers). Raids adds one to the raid's zone on every load. It shows the brief repairs after a lost night,
## and while the night runs it stands the chosen defences on the pads (world/raid_barricade.gd), gives the
## shard lantern its health (world/raid_lantern.gd), sends the waves along the lane from the halt road
## (enemies/raid_creature.gd), and reports the outcome to Raids.
##
## Its creatures walk the lane towards the lantern, batter whatever stands on it, and turn on the player
## when the player comes near. Villagers are never a target: Hale and Moss stay where they are, unhurt.
## Its time is counted in physics steps (no clock, nothing while the tree is paused), and each wave comes
## when the one before is freed. Positions in the data are world px; here they are texels (x3).

const DENSITY := 3.0
const STOP := 40.0            ## texels: a marching creature stops this far short of a standing hurdle
const SPAWN_IN := 20.0        ## world px along the lane where a creature appears (inside the zone's edge)
const SPREAD := 16.0          ## texels: creatures of one wave appear this far either side of the lane
const CARD := 2.5             ## seconds the wave's card shows

signal ended(won: bool)

var def: Dictionary
var zone: Zone
var lane := PackedVector2Array()       ## texels
var _cum := PackedFloat32Array()       ## the lane's length up to each of its points
var barricades: Array[RaidBarricade] = []
var lantern: RaidLantern
var camp: Node2D
var slots: SliceAttackSlots
var repairs: Array[Node2D] = []
var wave := -1
var _queue: Array = []                 ## roles still to come in this wave
var _spawned := 0
var _spawn_t := 0.0
var _gap_t := 0.0
var _alive := 0
var _started := false
var _over := false

func _ready() -> void:
	zone = get_parent() as Zone
	for p: Vector2 in Raids.lane(def):
		lane.append(p * DENSITY)
	_cum.resize(lane.size())
	for i in lane.size():
		_cum[i] = 0.0 if i == 0 else _cum[i - 1] + lane[i - 1].distance_to(lane[i])
	Raids.changed.connect(_on_raids_changed)
	_show_repairs()
	if Raids.running():
		start()

func _on_raids_changed(st: String) -> void:
	_show_repairs()
	if st == "running" and not _started:
		start()

func actors() -> Node:
	return zone.actors if zone != null else get_parent()

# --- the lane -------------------------------------------------------------------------------
func length() -> float:
	return _cum[_cum.size() - 1] if _cum.size() > 0 else 0.0

## How far along the lane (texels) the point nearest `at` lies.
func progress(at: Vector2) -> float:
	var best := INF
	var out := 0.0
	for i in range(lane.size() - 1):
		var a := lane[i]
		var b := lane[i + 1]
		var ab := b - a
		var t := clampf((at - a).dot(ab) / maxf(ab.length_squared(), 0.0001), 0.0, 1.0)
		var d := at.distance_to(a + ab * t)
		if d < best:
			best = d
			out = _cum[i] + ab.length() * t
	return out

## The point `s` texels along the lane (clamped to its ends).
func point_at(s: float) -> Vector2:
	if lane.is_empty():
		return Vector2.ZERO
	s = clampf(s, 0.0, length())
	for i in range(lane.size() - 1):
		if s <= _cum[i + 1] or i == lane.size() - 2:
			var seg := _cum[i + 1] - _cum[i]
			return lane[i].lerp(lane[i + 1], 0.0 if seg <= 0.0 else (s - _cum[i]) / seg)
	return lane[lane.size() - 1]

func direction_at(s: float) -> Vector2:
	var a := point_at(s - 6.0)
	var b := point_at(s + 6.0)
	return a.direction_to(b) if a.distance_to(b) > 0.01 else Vector2.RIGHT

func march_speed() -> float:
	return float(def.get("march_speed", 30.0)) * DENSITY

func notice() -> float:
	return float(def.get("notice", 60.0)) * DENSITY

## What blocks a creature `s` texels along the lane: a standing hurdle just ahead of it (or one it is
## pressed against, off the lane), else the lantern once it is in reach; null when the way is open.
func blocker_ahead(creature: Node2D, s: float) -> Node2D:
	for b in barricades:
		if is_instance_valid(b) and b.standing():
			var on_lane := s >= b.lane_s - STOP and s <= b.lane_s + 12.0
			if on_lane or creature.global_position.distance_to(b.global_position) < STOP + 8.0:
				return b
	if is_instance_valid(lantern) and lantern.standing():
		var reach := float(def.get("lantern", {}).get("reach", 30.0)) * DENSITY
		if s >= length() - reach or creature.global_position.distance_to(lantern.global_position) < reach:
			return lantern
	return null

func batter_damage(role: String) -> int:
	var b: Dictionary = def.get("batter", {})
	return int(b.get("elite_damage", 2)) if role == "elite" else int(b.get("damage", 1))

# --- the night ------------------------------------------------------------------------------
func start() -> void:
	if _started:
		return
	_started = true
	_over = false
	wave = -1
	_alive = 0
	_queue = []
	_gap_t = float(def.get("first_wave_after", 2.0))
	slots = SliceAttackSlots.new()
	slots.name = "RaidSlots"
	add_child(slots)
	camp = Node2D.new()
	camp.name = "RaidCamp"
	camp.y_sort_enabled = true
	actors().add_child(camp)
	var dresser := CreatureDresser.new()
	dresser.name = "Dresser"
	dresser.with_den = false
	camp.add_child(dresser)
	_stand_defences()
	_light_the_lantern()

func _stand_defences() -> void:
	for pad: Dictionary in Raids.pads(def):
		var kind := Raids.pad_kind(String(pad.id), def)
		if kind == "":
			continue
		var b := RaidBarricade.new()
		b.name = "Raid_" + String(pad.id)
		b.pad_id = String(pad.id)
		b.kind = def.get("kinds", {}).get(kind, {})
		b.position = (pad.at as Vector2) * DENSITY
		b.lane_s = progress(b.position)
		b.across = direction_at(b.lane_s)
		actors().add_child(b)
		barricades.append(b)

func _light_the_lantern() -> void:
	# where the lantern's talk area stands in the scene, else the plan's thing, else the lane's end
	var at := point_at(length())
	for t: Dictionary in Village.plans.get(String(def.get("zone", "")), {}).get("things", []):
		if t.get("id", "") == "shard_lantern":
			at = Vector2(float(t.at[0]), float(t.at[1])) * DENSITY
	var node: Node2D = null
	if zone != null:
		node = zone.get_node_or_null("Actors/ShardLantern") as Node2D
	if node != null:
		at = node.global_position
	lantern = RaidLantern.new()
	lantern.name = "RaidLantern"
	lantern.max_hp = int(def.get("lantern", {}).get("hp", 12))
	lantern.position = at
	lantern.fell.connect(func() -> void: _end(false))
	actors().add_child(lantern)

func _physics_process(delta: float) -> void:
	if not _started or _over:
		return
	if not Raids.running():
		# lost elsewhere (the player went down): the zone reloads; nothing more happens here
		_over = true
		return
	if not _queue.is_empty():
		_spawn_t -= delta
		if _spawn_t <= 0.0:
			_spawn(String(_queue.pop_front()))
			_spawn_t = float(def.get("spawn_spacing", 1.0))
		return
	if _alive > 0:
		return
	var waves: Array = def.get("waves", [])
	if wave >= waves.size() - 1 and wave >= 0:
		_end(true)
		return
	_gap_t -= delta
	if _gap_t <= 0.0:
		_next_wave()

func _next_wave() -> void:
	wave += 1
	var waves: Array = def.get("waves", [])
	_queue = (waves[wave].get("creatures", []) as Array).duplicate()
	_spawned = 0
	_spawn_t = 0.0
	_gap_t = float(def.get("wave_gap", 3.0))
	Raids.wave_started(wave)
	_card(String(def.get("title", "")), "Wave %d of %d, down the halt road" % [wave + 1, waves.size()], "", CARD)

func _spawn(role: String) -> void:
	var c := RaidCreature.new()
	c.role = role
	c.night = self
	c.slots = slots
	c.name = "%s_%d_%d" % [role.capitalize(), wave + 1, _spawned + 1]
	var s := SPAWN_IN * DENSITY
	var side := direction_at(s).orthogonal() * SPREAD * (1.0 if _spawned % 2 == 0 else -1.0)
	c.position = point_at(s) + (side if _spawned > 0 else Vector2.ZERO) - camp.global_position
	_spawned += 1
	_alive += 1
	c.died.connect(_on_freed)
	camp.add_child(c)

func _on_freed() -> void:
	_alive = maxi(_alive - 1, 0)

## The creatures of this night still on their feet.
func creatures() -> Array:
	var out := []
	if is_instance_valid(camp):
		for c in camp.get_children():
			if c is RaidCreature and not c.dead:
				out.append(c)
	return out

func _end(won: bool) -> void:
	if _over:
		return
	_over = true
	_queue.clear()
	if won:
		var purse := Raids.win()
		_card(String(def.get("title", "")), "The lantern held", "Hale's hurdles did their part. The village's purse: %d Glint." % purse, 6.0)
	else:
		for c: RaidCreature in creatures():
			c.leave()
		Raids.lose()
		_card(String(def.get("title", "")), "The lantern went dark", "The shardstruck scatter back down the halt road. A few things need mending; the villagers will see to it.", 6.0)
	ended.emit(won)

func is_over() -> bool:
	return _over

func _card(title: String, sub: String, text: String, secs: float) -> void:
	var hud := get_tree().get_first_node_in_group("hud")
	if hud != null and hud.has_method("show_card"):
		hud.show_card(title, sub, text, secs)

# --- the brief repairs ------------------------------------------------------------------------
func _show_repairs() -> void:
	var want := bool(Raids.rec().get("repairs", false)) and String(Raids.rec().get("id", "")) == String(def.get("id", ""))
	if want == not repairs.is_empty():
		return
	for r in repairs:
		if is_instance_valid(r):
			r.queue_free()
	repairs.clear()
	if not want:
		return
	for spec: Dictionary in def.get("repairs", []):
		var r := RaidRepair.new()
		r.name = "Repair_" + String(spec.id)
		r.spec = spec
		var at: Array = spec.get("at", [0, 0])
		r.position = Vector2(float(at[0]), float(spec.get("foot", at[1]))) * DENSITY
		actors().add_child(r)
		repairs.append(r)
