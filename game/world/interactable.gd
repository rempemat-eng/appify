class_name Interactable
extends Area2D
## Something to talk to or read: a sign, a villager, a stone. When the player stands in its area the
## player's `focus` points here, the HUD shows the prompt and E (or Y) calls `interact()`, which runs
## the speaker's dialogue (data/dialogue) and then reports "talk:<speaker_id>" to the quests.
## While a quest waits on this speaker, a "!" floats above it (game-design.md 8.3: show, do not explain).
##
## No talk area is smaller than REACH (10 Nov: the areas were 30 texel circles the scenes drew one by
## one, and a walker who stopped a step short of Moss, the notice board or a restore mark got no
## prompt): every Interactable adds a circle of REACH texels round the node beside whatever shape the
## scene or a plan's `radius` gave it. The scene's own shape is left as it is (the world editor reads
## and writes it), so a larger one still reaches further. Where two areas overlap, the prompt goes to
## the one a quest is waiting on, then to the nearer.

const REACH := 60.0   ## texels (20 world px): the prompt shows about one body height away
const STALE_MARGIN := 20.0    ## beyond the reach by more than the player's body: no longer touching

@export var speaker_id := ""
@export var verb := "Talk"
@export var marker_height := 40.0  ## texels above the origin for the "!"

## The talk areas the player's body is inside right now.
static var _in_reach: Array[Interactable] = []

func _ready() -> void:
	collision_layer = 8  # interact
	collision_mask = 2   # player
	_use_the_shared_reach()
	body_entered.connect(_on_body.bind(true))
	body_exited.connect(_on_body.bind(false))
	tree_exiting.connect(func() -> void: _in_reach.erase(self))
	Quests.started.connect(func(_id: String) -> void: queue_redraw())
	Quests.advanced.connect(func(_id: String, _s: int) -> void: queue_redraw())
	Quests.completed.connect(func(_id: String) -> void: queue_redraw())
	set_physics_process(false)

## The shared reach: an internal circle of REACH texels (not a child the scene, the editor or a saved
## plan sees).
func _use_the_shared_reach() -> void:
	var reach := CollisionShape2D.new()
	reach.name = "Reach"
	var circle := CircleShape2D.new()
	circle.radius = REACH
	reach.shape = circle
	add_child(reach, false, Node.INTERNAL_MODE_BACK)

## How far the prompt reaches from the node: REACH, or the scene's own circle when that is larger.
func reach() -> float:
	var own := get_node_or_null("Shape") as CollisionShape2D
	if own != null and own.shape is CircleShape2D:
		return maxf(REACH, (own.shape as CircleShape2D).radius)
	return REACH

func _on_body(body: Node, entered: bool) -> void:
	if not body.is_in_group("player"):
		return
	if entered and not _in_reach.has(self):
		_in_reach.append(self)
	elif not entered:
		_in_reach.erase(self)
	set_physics_process(entered)
	refocus(body)

## While the player stands in this area, keep the focus on the best of the areas in reach: walking
## from one thing toward another moves the prompt without leaving either area.
func _physics_process(_delta: float) -> void:
	var player := get_tree().get_first_node_in_group("player")
	if player != null:
		refocus(player)

## True while this area can be used: in the tree, shown, and not switched off by a Conditional.
func usable() -> bool:
	return is_inside_tree() and can_process() and is_visible_in_tree()

## Points the player's focus at the best usable area in reach (or at nothing).
static func refocus(player: Node) -> void:
	var at: Vector2 = (player as Node2D).global_position
	var best: Interactable = null
	var best_wants := false
	var best_d := INF
	for i in range(_in_reach.size() - 1, -1, -1):
		var it := _in_reach[i]
		if not is_instance_valid(it) or not it.is_inside_tree():
			_in_reach.remove_at(i)
			continue
		var d := it.global_position.distance_squared_to(at)
		var far := it.reach() + STALE_MARGIN
		if d > far * far:
			# an area switched off by a Conditional reports no body_exited: the player has walked away
			_in_reach.remove_at(i)
			it.set_physics_process(false)
			continue
		if not it.usable():
			continue
		var wants := it.wants_talk()
		if best == null or (wants and not best_wants) or (wants == best_wants and d < best_d):
			best = it
			best_wants = wants
			best_d = d
	if player.get("focus") != best:
		player.set("focus", best)

func interact() -> void:
	Dialogue.talk(speaker_id)

## True when talking here would start or move on a quest (the quest's own conditions included: a
## quest that cannot start yet does not raise the "!").
func wants_talk() -> bool:
	return waits_on("talk:" + speaker_id)

func waits_on(event: String) -> bool:
	for id: String in Quests.defs:
		var st := Quests.state(id)
		if st == "none":
			var start: Dictionary = Quests.defs[id].get("start", {})
			if start.get("on", "") == event and Quests.check(start.get("if")):
				return true
		elif st == "active":
			var step := Quests.current_step(id)
			if step.get("on", "") == event and Quests.check(step.get("if")):
				return true
	return false

func _draw() -> void:
	if wants_talk():
		var c := Color(1.0, 0.86, 0.3)
		draw_rect(Rect2(-1.5, -marker_height - 12, 3, 8), c)
		draw_rect(Rect2(-1.5, -marker_height - 2, 3, 3), c)
