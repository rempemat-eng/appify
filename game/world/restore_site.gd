class_name RestoreSite
extends Interactable
## A "restore here" mark on a broken building or lot (game-design.md 7.3). Interacting shows the site's
## lines (data/dialogue: speaker "restore_<restore_id>", chosen by condition, so the text can say whether
## the Glint is there) and then restores it through Village when it can. The "!" shows while a quest
## waits on "restore:<restore_id>".
##
## A mark is there once its restore's own condition holds (the plan's `restores[].if`, which Village
## also checks before taking the Glint): Crossroads' marks wait for their quest to ask, so nothing is
## repaired before the person it belongs to has spoken. Until then the mark is hidden and gives no prompt.

@export var restore_id := ""

func _ready() -> void:
	if speaker_id == "":
		speaker_id = "restore_" + restore_id
	super._ready()
	Village.changed.connect(func(_id: String) -> void: _refresh())
	Quests.started.connect(func(_id: String) -> void: _refresh())
	Quests.advanced.connect(func(_id: String, _s: int) -> void: _refresh())
	Quests.completed.connect(func(_id: String) -> void: _refresh())
	_refresh()

## True once the restore's own condition holds (no condition: always).
func asked() -> bool:
	return Quests.check(Village.sites.get(restore_id, {}).get("if"))

func _refresh() -> void:
	visible = asked()
	queue_redraw()

func interact() -> void:
	if Dialogue.busy or not asked():
		return
	var could := Village.can_restore(restore_id)
	await Dialogue.talk(speaker_id)
	if could:
		Village.restore(restore_id)

func wants_talk() -> bool:
	return not Village.is_restored(restore_id) and waits_on("restore:" + restore_id)
