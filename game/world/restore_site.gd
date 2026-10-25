class_name RestoreSite
extends Interactable
## A "restore here" mark on a broken building or lot (game-design.md 7.3). Interacting shows the site's
## lines (data/dialogue: speaker "restore_<restore_id>", chosen by condition, so the text can say whether
## the Glint is there) and then restores it through Village when it can. The "!" shows while a quest
## waits on "restore:<restore_id>".

@export var restore_id := ""

func _ready() -> void:
	if speaker_id == "":
		speaker_id = "restore_" + restore_id
	super._ready()
	Village.changed.connect(func(_id: String) -> void: queue_redraw())

func interact() -> void:
	if Dialogue.busy:
		return
	var could := Village.can_restore(restore_id)
	await Dialogue.talk(speaker_id)
	if could:
		Village.restore(restore_id)

func wants_talk() -> bool:
	if Village.is_restored(restore_id):
		return false
	for id in Quests.defs:
		if Quests.current_step(id).get("on", "") == "restore:" + restore_id:
			return true
	return false
