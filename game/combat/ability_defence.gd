class_name AbilityDefence
extends RefCounted
## Original P/$ and interrupted X on canonical snapshots; no actor-HP conversion.

static func damage(source: Dictionary, amount: float, from_x: float, from_y: float,
		kind := "projectile") -> Dictionary:
	var state := source.duplicate(true)
	var player: Dictionary = state.player
	if player.hp <= 0:
		return state
	if player.airborne and kind in ["melee", "field"]:
		AbilityImpacts._fx(state, "ground-miss", player.x, player.y, 9, 0.2)
		return state
	var dx := from_x - float(player.x)
	var dy := from_y - float(player.y)
	var length := sqrt(dx * dx + dy * dy)
	var nx := dx / length if length > 1.0e-8 else 1.0
	var ny := dy / length if length > 1.0e-8 else 0.0
	var frontal: bool = nx * player.dirX + ny * player.dirY >= 0.25
	var remaining := amount
	if player.blocking and frontal and player.guardBroken <= 1.0e-8:
		var absorbed := minf(amount, player.guard / 1.5)
		player.guard -= 1.5 * absorbed
		player.guardRecovery = 0.8
		remaining -= absorbed
		state.statistics.guarded += absorbed
		AbilityImpacts._fx(state, "shield", player.x + 9 * player.dirX,
			player.y + 9 * player.dirY, 12, 0.25)
		_event(state, "guard", "Guard absorbed %d" % floori(absorbed + 0.5), absorbed)
		if player.id == "velvet" and AbilityImpacts._powered(state):
			player.counterRemaining = 2
		if player.guard <= 1.0e-8:
			_break_guard(state)
	if remaining <= 1.0e-8:
		return state
	var taken := minf(player.hp, remaining)
	player.hp -= taken
	player.lastHitAt = state.time
	state.statistics.damageTaken += taken
	player.action = "defeat" if player.hp <= 0 else "hit"
	player.actionElapsed = 0
	player.actionDuration = 0.8 if player.hp <= 0 else 0.25
	player.actionReleased = true
	player.blocking = false
	state.queuedAction = null
	state.queueRemaining = 0
	AbilityImpacts._fx(state, "player-hit", player.x, player.y, 12, 0.3)
	_event(state, "hit", "Received %d" % floori(taken + 0.5), taken)
	if player.hp <= 0:
		state.status = "defeat"
		if AbilityImpacts._powered(state):
			player.specialRemaining = 0
			if player.id == "rook":
				state.turrets = []
				player.designatedId = null
			_event(state, "special-end", "Form interrupted")
		player.vaultRemaining = 0
		player.vaultHeight = 0
		player.airborne = false
		state.projectiles = []
		state.fields = []
		state.turrets = []
		_event(state, "defeat", "Defeated — restart the practice wave")
	return state

static func _break_guard(state: Dictionary) -> void:
	var player: Dictionary = state.player
	player.blocking = false
	player.guard = 0
	player.guardBroken = 1.15
	player.guardRecovery = 1.15
	player.action = "hit"
	player.actionElapsed = 0
	player.actionDuration = 0.4
	player.actionReleased = true
	AbilityImpacts._fx(state, "guard-break", player.x, player.y, 20, 0.4)
	_event(state, "guard-break", "Guard broken — recover before raising it again")

static func _event(state: Dictionary, kind: String, text: String, amount: Variant = null) -> void:
	var event := {"time": state.time, "type": kind, "text": text}
	if amount != null:
		event.amount = amount
	state.events.append(event)
	if state.events.size() > 80:
		state.events.pop_front()
