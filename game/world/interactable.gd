class_name Interactable
extends Area2D
## Something to talk to or read: a sign, a villager, a stone. When the player stands in its area the
## player's `focus` points here, the HUD shows the prompt and E (or Y) calls `interact()`, which runs
## the speaker's dialogue (data/dialogue) and then reports "talk:<speaker_id>" to the quests.
## While a quest waits on this speaker, a "!" floats above it (game-design.md 8.3: show, do not explain).

@export var speaker_id := ""
@export var verb := "Talk"
@export var marker_height := 40.0  ## texels above the origin for the "!"

func _ready() -> void:
	collision_layer = 8  # interact
	collision_mask = 2   # player
	body_entered.connect(func(b: Node) -> void: if b.is_in_group("player"): b.set("focus", self))
	body_exited.connect(func(b: Node) -> void: if b.is_in_group("player") and b.get("focus") == self: b.set("focus", null))
	Quests.started.connect(func(_id: String) -> void: queue_redraw())
	Quests.advanced.connect(func(_id: String, _s: int) -> void: queue_redraw())
	Quests.completed.connect(func(_id: String) -> void: queue_redraw())

func interact() -> void:
	Dialogue.talk(speaker_id)

## True when talking here would start or move on a quest.
func wants_talk() -> bool:
	var event := "talk:" + speaker_id
	for id in Quests.defs:
		var st := Quests.state(id)
		if st == "none" and Quests.defs[id].get("start", {}).get("on", "") == event:
			return true
		if st == "active" and Quests.current_step(id).get("on", "") == event:
			return true
	return false

func _draw() -> void:
	if wants_talk():
		var c := Color(1.0, 0.86, 0.3)
		draw_rect(Rect2(-1.5, -marker_height - 12, 3, 8), c)
		draw_rect(Rect2(-1.5, -marker_height - 2, 3, 3), c)
