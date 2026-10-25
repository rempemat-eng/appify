extends "res://world/camp.gd"
## Integration scene: instantiate under the zone's Actors. Uses the existing camp/quest protocol.
func _ready() -> void:
	var pool := SliceAttackSlots.new()
	pool.name = "AttackSlots"
	add_child(pool)
	var roles := ["rusher", "shooter", "shield", "elite"]
	var points := [Vector2(-75, 0), Vector2(60, -65), Vector2(75, 30), Vector2(-30, -90)]
	for i in roles.size():
		var enemy := SliceEnemy.new()
		enemy.name = roles[i].capitalize()
		enemy.role = roles[i]
		enemy.slots = pool
		enemy.position = points[i]
		add_child(enemy)
	super._ready()
