class_name SliceAttackSlots
extends Node
## Shared across pools so overlapping camps and isolated actors also respect the cap.
## Wind-up, contact and travelling shots retain their reservation.
static var _holders: Array[Node] = []
const LIMIT := 2

func acquire(actor: Node) -> bool:
	_prune()
	if actor in _holders:
		return true
	if _holders.size() >= LIMIT:
		return false
	_holders.append(actor)
	return true

func release(actor: Node) -> void:
	_holders.erase(actor)

func count() -> int:
	_prune()
	return _holders.size()

func _prune() -> void:
	for i in range(_holders.size() - 1, -1, -1):
		if not is_instance_valid(_holders[i]) or _holders[i].is_queued_for_deletion():
			_holders.remove_at(i)
