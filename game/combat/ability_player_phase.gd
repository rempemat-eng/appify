class_name AbilityPlayerPhase
extends RefCounted
## Original v prefix through action commitment. Fixed canonical 1/60, before movement.
## Inputs are already normalised by the dispatcher. No previous-input update or world adapter.

const DT := 1.0 / 60.0
const EPS := 1.0e-8

static func tick(source: Dictionary, input: Dictionary) -> Dictionary:
	var state := source.duplicate(true)
	var p: Dictionary = state.player
	state.time += DT
	state.tick += 1
	p.aimX = clampf(input.aimX, 0, state.width)
	p.aimY = clampf(input.aimY, 0, state.height)
	var direction := _normal(float(p.aimX) - float(p.x), float(p.aimY) - float(p.y))
	p.dirX = direction.x
	p.dirY = direction.y
	p.facing = ("E" if p.dirX > 0 else "W") if absf(p.dirX) > absf(p.dirY) else ("S" if p.dirY > 0 else "N")
	for action in ["primary", "secondary", "block", "special"]:
		p.cooldowns[action] = maxf(0, p.cooldowns[action] - DT)
	p.guardBroken = maxf(0, p.guardBroken - DT)
	p.guardRecovery = maxf(0, p.guardRecovery - DT)
	state.queueRemaining = maxf(0, state.queueRemaining - DT)
	if state.queueRemaining <= EPS:
		state.queuedAction = null
	if input.special and not state.previous.special and p.cooldowns.special <= EPS:
		state.queuedAction = "special"
		state.queueRemaining = 0.7
	elif input.secondary and not state.previous.secondary and p.cooldowns.secondary <= EPS:
		state.queuedAction = "secondary"
		state.queueRemaining = 0.7
	p.counterRemaining = maxf(0, p.counterRemaining - DT)
	p.designationRemaining = maxf(0, p.designationRemaining - DT)
	if p.designationRemaining <= EPS:
		p.designatedId = null
	p.tetherRemaining = maxf(0, p.tetherRemaining - DT)
	var live_tether := false
	for enemy in state.enemies:
		if enemy.id == p.tetherId and enemy.hp > 0:
			live_tether = true
	if p.tetherRemaining <= EPS or not live_tether:
		p.tetherId = null
	if p.reload > 0:
		p.reload = maxf(0, p.reload - DT)
		if p.reload <= EPS:
			p.ammo = p.maxAmmo
			AbilityDefence._event(state, "reload", "Reload complete")
	if p.id == "nix":
		p.heat = maxf(0, p.heat - DT * (4 if p.action == "primary" else (7 if AbilityImpacts._powered(state) else 15)))
	if AbilityImpacts._powered(state):
		p.specialRemaining = maxf(0, p.specialRemaining - DT)
		if p.specialRemaining <= EPS:
			state = AbilityFormExit.finish(state)
			p = state.player
	p.blocking = input.block and p.guardBroken <= EPS and p.guard > 0.1
	if p.blocking:
		state.queuedAction = null
		state.queueRemaining = 0
		if p.action != "block":
			p.action = "block"
			p.actionElapsed = 0
			p.actionDuration = 0.18
			p.actionReleased = true
			if not state.previous.block:
				state.statistics.actions.block += 1
				AbilityDefence._event(state, "action", "Guard raised")
		p.guard = maxf(0, p.guard - 1.0 / 30.0)
		if p.guard <= EPS:
			AbilityDefence._break_guard(state)
	elif p.action == "block":
		p.action = "idle"
		p.actionElapsed = 0
	if not p.blocking and p.guardRecovery <= EPS and p.guardBroken <= EPS:
		p.guard = minf(p.maxGuard, p.guard + 11.0 / 30.0)
	p.actionElapsed += DT
	if p.action in ["primary", "secondary", "special"] and not p.actionReleased and p.actionElapsed + EPS >= _release_time(p):
		p.actionReleased = true
		if p.action == "special":
			state = AbilitySpecial.activate(state)
		elif p.action == "secondary":
			state = AbilitySecondary.release(state)
		else:
			state = AbilityPrimary.release(state)
		p = state.player
	if p.action not in ["block", "idle", "walk"] and p.actionElapsed + EPS >= p.actionDuration:
		p.action = "idle"
		p.actionElapsed = 0
	var available: bool = p.action in ["idle", "walk"] or (p.id == "rook" and p.vaultRemaining > 0 and p.action == "secondary" and p.actionReleased)
	if not p.blocking and available:
		if state.queuedAction == "special" and p.cooldowns.special <= EPS:
			_commit(state, "special")
			state.queuedAction = null
		elif state.queuedAction == "secondary" and p.cooldowns.secondary <= EPS:
			var mx := float(input.moveX)
			var my := float(input.moveY)
			var vault := _normal(mx, my) if sqrt(mx * mx + my * my) > 0.1 else direction
			p.vaultDirX = vault.x
			p.vaultDirY = vault.y
			_commit(state, "secondary")
			state.queuedAction = null
		elif input.primary and p.cooldowns.primary <= EPS:
			_commit(state, "primary")
	return state

static func _normal(x: float, y: float) -> Dictionary:
	var length := sqrt(x * x + y * y)
	return {"x": x / length, "y": y / length} if length > EPS else {"x": 1.0, "y": 0.0}

static func _release_time(p: Dictionary) -> float:
	if p.action == "special":
		return 0.28
	if p.action == "secondary" and p.id in ["rook", "nix"]:
		return 0.05
	return p.actionDuration * (0.48 if p.id in ["cairn", "clack"] else 0.38)

static func _commit(state: Dictionary, action: String) -> void:
	var p: Dictionary = state.player
	if action == "primary" and p.id == "nix" and p.heat >= 92:
		return
	if (action == "primary" or (action == "secondary" and p.id == "pendle")) and p.maxAmmo != 0 and not (p.id == "pendle" and AbilityImpacts._powered(state)) and (p.reload > EPS or p.ammo <= 0):
		return
	p.action = action
	p.actionElapsed = 0
	# R uses strictly positive power, including a positive sub-epsilon remnant.
	# Keep timings/cooldowns in the audited character data rather than a second table.
	var spec := AbilityCatalogue.action(str(p.id), action, p.specialRemaining > 0)
	p.actionDuration = spec.duration_seconds
	p.actionReleased = false
	p.actionDirX = p.dirX
	p.actionDirY = p.dirY
	p.actionOriginX = p.x
	p.actionOriginY = p.y
	p.cooldowns[action] = spec.cooldown_seconds
	state.statistics.actions[action] += 1
	AbilityDefence._event(state, "action", action.capitalize() + " committed")
