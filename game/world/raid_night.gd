class_name RaidNight
extends Node2D
## One raid played in its zone (core/raids.gd keeps its state in the save; data/raids/<id>.json holds its
## numbers). Raids adds one to the raid's zone on every load. It shows the brief repairs after a lost night,
## and while the night runs it stands the chosen defences on the pads (world/raid_barricade.gd), gives the
## shard lantern its health (world/raid_lantern.gd), sends the waves along the lane from the halt road
## (enemies/raid_creature.gd), and reports the outcome to Raids. When the night ends it clears the hurdles
## and the bar away and says how it went (a card); a night lost by going down says so on getting up. Once
## the raid is won it sets out the restore mark of the restore it offers (the bell tower) until it is paid.
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
var offer_site: RestoreSite
var wave := -1
var _queue: Array = []                 ## roles still to come in this wave
var _spawned := 0
var _spawn_t := 0.0
var _gap_t := 0.0
var _wait_t := 0.0                     ## seconds since the bell, until wave 1 comes
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
	_set_out_offer()
	if Raids.running():
		start()
	elif Raids.state() == "lost" and Raids.loss_untold == "down":
		# the night was lost by going down: the zone has just reloaded, so this is where it is told
		Raids.loss_untold = ""
		_card.call_deferred(String(def.get("title", "")), "The night is lost",
			"You went down, and the shardstruck scattered back down the halt road. A few things need mending; they will come again on your next walk into town.", 7.0)

func _on_raids_changed(st: String) -> void:
	_show_repairs()
	_set_out_offer()
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
## pressed against, off the lane), else the lantern when it stands beside the post (within `lantern.reach`
## world px of its solid, `lantern.box`); null when the way is open.
func blocker_ahead(creature: Node2D, s: float) -> Node2D:
	for b in barricades:
		if is_instance_valid(b) and b.standing():
			var on_lane := s >= b.lane_s - STOP and s <= b.lane_s + 12.0
			if on_lane or creature.global_position.distance_to(b.global_position) < STOP + 8.0:
				return b
	if is_instance_valid(lantern) and lantern.standing() and lantern_distance(creature.global_position) <= lantern_reach():
		return lantern
	return null

## The lantern's post in texels (the lit lantern's solid; data/raids/<id>.json lantern.box).
func lantern_box() -> Rect2:
	var b: Array = def.get("lantern", {}).get("box", [307, 290, 10, 22])
	return Rect2(Vector2(float(b[0]), float(b[1])) * DENSITY, Vector2(float(b[2]), float(b[3])) * DENSITY)

func lantern_reach() -> float:
	return float(def.get("lantern", {}).get("reach", 10.0)) * DENSITY

## How far `at` (texels) is from the lantern's post.
func lantern_distance(at: Vector2) -> float:
	var box := lantern_box()
	return at.distance_to(Vector2(clampf(at.x, box.position.x, box.end.x), clampf(at.y, box.position.y, box.end.y)))

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
	_wait_t = 0.0
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
		b.span = float(pad.get("span", 0.0))
		b.position = (pad.at as Vector2) * DENSITY
		b.lane_s = progress(b.position)
		b.across = direction_at(b.lane_s)
		actors().add_child(b)
		barricades.append(b)

func _light_the_lantern() -> void:
	# the bar hangs from the post's foot (data lantern.foot), else from the lane's end
	var foot: Variant = def.get("lantern", {}).get("foot")
	var at := Vector2(float(foot[0]), float(foot[1])) * DENSITY if foot is Array else point_at(length())
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
	if wave < 0:
		# wave 1 waits for the player to reach the square (or a while), so the hurdles can be held
		_wait_t += delta
		if first_wave_due(_wait_t, _player_at()):
			_next_wave()
		return
	var waves: Array = def.get("waves", [])
	if wave >= waves.size() - 1 and wave >= 0:
		_end(true)
		return
	_gap_t -= delta
	if _gap_t <= 0.0:
		_next_wave()

## True when wave 1 may come, `waited` seconds after the bell with the player at `at` (texels; INF: none):
## never before `first_wave.at_least`; then once the player is within `within` world px of the plan's place
## `near`, or after `or_after` seconds whatever happens.
func first_wave_due(waited: float, at: Vector2) -> bool:
	var fw: Dictionary = def.get("first_wave", {})
	if waited < float(fw.get("at_least", 2.0)):
		return false
	if waited >= float(fw.get("or_after", 25.0)):
		return true
	var place := near_place()
	if at == Vector2.INF or place.size == Vector2.ZERO:
		return false
	var p := at / DENSITY
	var nearest := Vector2(clampf(p.x, place.position.x, place.end.x), clampf(p.y, place.position.y, place.end.y))
	return p.distance_to(nearest) <= float(fw.get("within", 60.0))

## The plan's place wave 1 waits for the player to near (world px), or an empty Rect2.
func near_place() -> Rect2:
	var id := String(def.get("first_wave", {}).get("near", ""))
	for place: Dictionary in Village.plans.get(String(def.get("zone", "")), {}).get("places", []):
		if place.get("id", "") == id:
			var r: Array = place.rect
			return Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3]))
	return Rect2()

func _player_at() -> Vector2:
	if not is_inside_tree():
		return Vector2.INF
	var p := get_tree().get_first_node_in_group("player") as Node2D
	return p.global_position if p != null and p.is_inside_tree() else Vector2.INF

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
		_card(String(def.get("title", "")), "The lantern held", "The village's purse: %d Glint. Hale will want a word about the old bell." % purse, 6.0)
	else:
		for c: RaidCreature in creatures():
			c.leave()
		Raids.lose("lantern")
		Raids.loss_untold = ""
		_card(String(def.get("title", "")), "The shardstruck reached the lantern",
			"They scatter back down the halt road. A few things need mending; they will come again on your next walk into town.", 7.0)
	_clear_defences()
	ended.emit(won)

## The night is over: the hurdles (standing or broken) and the lantern's bar go. They fade unless reduced
## motion is on, when they go at once. Finite.
func _clear_defences() -> void:
	var gone: Array[Node2D] = []
	for b in barricades:
		if is_instance_valid(b):
			b.collision_layer = 0
			gone.append(b)
	if is_instance_valid(lantern):
		gone.append(lantern)
	barricades.clear()
	lantern = null
	for n in gone:
		n.remove_from_group("raid_defence")
		if SaveGame.setting("reduced_motion", false) or not n.is_inside_tree():
			n.queue_free()
		else:
			var t := n.create_tween()
			t.tween_property(n, "modulate:a", 0.0, 0.6)
			t.tween_callback(n.queue_free)

func is_over() -> bool:
	return _over

func _card(title: String, sub: String, text: String, secs: float) -> void:
	if not is_inside_tree():
		return                       # a deferred card whose zone has already gone
	var hud := get_tree().get_first_node_in_group("hud")
	if hud != null and hud.has_method("show_card"):
		hud.show_card(title, sub, text, secs)

# --- the restore a won raid offers --------------------------------------------------------------
## The mark of the offered restore (the bell tower before the library), while the raid is won, the offer is
## Raids' own (no plan site) and it is not restored yet. The mark is a RestoreSite like the plan's.
func _set_out_offer() -> void:
	var offer: Dictionary = def.get("reward", {}).get("offers", {})
	var want := not offer.is_empty() and offer.has("mark") and Raids.won(String(def.get("id", ""))) \
		and bool(Village.sites.get(offer.get("id", ""), {}).has("offered_by")) and not Village.is_restored(String(offer.id))
	if want == is_instance_valid(offer_site):
		return
	if not want:
		return                       # a paid mark stays until the zone reloads; its lines say the bell is back
	offer_site = RestoreSite.new()
	offer_site.name = "BellTowerSite" if offer.id == "bell_tower" else "OfferSite"
	offer_site.restore_id = String(offer.id)
	offer_site.verb = "Restore"
	offer_site.position = Vector2(float(offer.mark[0]), float(offer.mark[1])) * DENSITY
	actors().add_child(offer_site)

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
