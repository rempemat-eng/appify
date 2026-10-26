class_name SealLever
extends Interactable
## The Undercroft puzzle's second step: pull the lever. It only moves once the plate is down
## (`needs_flag`); then it sets `flag`, which sinks the sealed slab (its picture and collision sit in a
## Conditional) and draws the lever pulled. Its lines come from data/dialogue (speaker "seal_lever"),
## chosen by the same flags, so the player is told why it will not move.

signal opened

@export var needs_flag := "undercroft_plate"
@export var flag := "undercroft_seal_open"

func interact() -> void:
	var ready_to_open := SaveGame.has_flag(needs_flag) and not SaveGame.has_flag(flag)
	super.interact()
	if ready_to_open:
		pull()

## True when the pull opened the seal.
func pull() -> bool:
	if not SaveGame.has_flag(needs_flag) or SaveGame.has_flag(flag):
		return false
	SaveGame.set_flag(flag)
	Village.changed.emit(flag)
	opened.emit()
	return true
