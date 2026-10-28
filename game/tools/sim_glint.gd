extends SceneTree
## Headless explicit-event Glint simulation, using the runtime ledger itself.
## godot --headless --path game -s res://tools/sim_glint.gd -- --scenario=/path/events.json [--out=/fresh/report.json]

const Ledger = preload("res://core/glint_economy.gd")
const REFUSALS := ["insufficient_funds", "not_eligible", "already_owned"]

static func _failure(message: String, location: String = "scenario") -> Dictionary:
	return {"schema_version": 1, "currency": "Glint", "settings_applied": false,
		"exit_code": 2, "error": message, "location": location, "trace": []}

## Godot replaces malformed UTF-8 and NUL with U+FFFD. Validate before decoding
## so transaction identities cannot silently change on the way into the ledger.
static func _utf8_error(bytes: PackedByteArray) -> String:
	var index: int = 0
	while index < bytes.size():
		var lead: int = bytes[index]
		if lead == 0:
			return "NUL is not valid JSON input (byte %d)" % index
		if lead < 128:
			index += 1
			continue
		var width: int = 0
		if lead >= 0xc2 and lead <= 0xdf:
			width = 2
		elif lead >= 0xe0 and lead <= 0xef:
			width = 3
		elif lead >= 0xf0 and lead <= 0xf4:
			width = 4
		if width == 0 or index + width > bytes.size():
			return "Invalid or truncated UTF-8 at byte %d" % index
		for offset: int in range(1, width):
			if bytes[index + offset] < 0x80 or bytes[index + offset] > 0xbf:
				return "Invalid UTF-8 continuation at byte %d" % (index + offset)
		var second: int = bytes[index + 1]
		if (lead == 0xe0 and second < 0xa0) or (lead == 0xed and second > 0x9f) or (lead == 0xf0 and second < 0x90) or (lead == 0xf4 and second > 0x8f):
			return "Overlong, surrogate or out-of-range UTF-8 at byte %d" % index
		index += width
	return ""

static func _hex4(raw: String, start: int) -> int:
	if start + 4 > raw.length():
		return -1
	var value: int = 0
	for index: int in range(start, start + 4):
		var digit: int = "0123456789abcdef".find(raw[index].to_lower())
		if digit < 0:
			return -1
		value = value * 16 + digit
	return value

static func _unicode_error(raw: String) -> String:
	var inside: bool = false
	var index: int = 0
	while index < raw.length():
		var code: int = raw.unicode_at(index)
		if code == 34: # Unescaped quote.
			inside = not inside
		elif inside and code == 92: # Backslash; skip escaped quotes/backslashes.
			if index + 1 < raw.length() and raw.unicode_at(index + 1) == 117:
				var unit: int = _hex4(raw, index + 2)
				if unit <= 0:
					return "Invalid Unicode escape or NUL at character %d" % index
				if unit >= 0xd800 and unit <= 0xdbff:
					if index + 12 > raw.length() or raw.unicode_at(index + 6) != 92 or raw.unicode_at(index + 7) != 117:
						return "Unpaired high surrogate at character %d" % index
					var low: int = _hex4(raw, index + 8)
					if low < 0xdc00 or low > 0xdfff:
						return "Unpaired high surrogate at character %d" % index
					index += 12
					continue
				if unit >= 0xdc00 and unit <= 0xdfff:
					return "Unpaired low surrogate at character %d" % index
				index += 6
				continue
			index += 2
			continue
		index += 1
	return ""

static func parse_document(bytes: PackedByteArray) -> Dictionary:
	var hash_context := HashingContext.new()
	hash_context.start(HashingContext.HASH_SHA256)
	hash_context.update(bytes)
	var digest: String = hash_context.finish().hex_encode()
	var error: String = _utf8_error(bytes)
	if not error.is_empty():
		return {"ok": false, "error": error, "sha256": digest}
	var raw: String = bytes.get_string_from_utf8()
	error = _unicode_error(raw)
	if not error.is_empty():
		return {"ok": false, "error": error, "sha256": digest}
	var json := JSON.new()
	if json.parse(raw) != OK:
		return {"ok": false, "error": "Invalid JSON at line %d: %s" % [json.get_error_line(), json.get_error_message()], "sha256": digest}
	return {"ok": true, "document": json.data, "sha256": digest}

## No clock, nap policy, earning frequency, prices or stock tiers are inferred.
## Valid but refused transactions leave state alone and are reported with exit 1.
static func simulate(value: Variant) -> Dictionary:
	if typeof(value) != TYPE_DICTIONARY:
		return _failure("Scenario must be an object")
	var document: Dictionary = value
	for key: Variant in document:
		if key not in ["schema_version", "currency", "opening_balance", "initial_owned", "events", "label", "assumptions", "source_status"]:
			return _failure("Unknown scenario field: %s" % str(key))
	if typeof(document.get("schema_version")) not in [TYPE_INT, TYPE_FLOAT] or document.get("schema_version") != 1 or document.get("currency") != "Glint":
		return _failure("Scenario requires schema_version 1 and explicit currency Glint")
	if typeof(document.get("events")) != TYPE_ARRAY:
		return _failure("events must be an ordered array")
	for key: String in ["label", "source_status"]:
		if document.has(key) and typeof(document[key]) != TYPE_STRING:
			return _failure("%s must be text when supplied" % key)
	var assumptions: Variant = document.get("assumptions", [])
	if typeof(assumptions) != TYPE_ARRAY:
		return _failure("assumptions must be an array of text")
	for assumption: Variant in assumptions:
		if typeof(assumption) != TYPE_STRING:
			return _failure("Every assumption must be text")
	var initial: Dictionary = Ledger.fresh(document.get("opening_balance"), document.get("initial_owned", []))
	if not initial.ok:
		return _failure(initial.error, "opening_balance/initial_owned")
	var state: Dictionary = initial.state
	var report: Dictionary = {"schema_version": 1, "currency": "Glint", "settings_applied": false,
		"model": "explicit ordered events; no earning-rate or balance claim", "exit_code": 0,
		"label": document.get("label", ""), "source_status": document.get("source_status", "explicit caller inputs"),
		"assumptions": assumptions.duplicate(), "opening_balance": state.balance, "trace": []}
	for index: int in document.events.size():
		var before: int = state.balance
		var result: Dictionary = Ledger.apply(state, document.events[index])
		var row: Dictionary = {"index": index, "before": before, "after": before, "ok": result.ok, "applied": false}
		if result.ok:
			state = result.state
			row.merge({"after": state.balance, "applied": result.applied, "receipt": result.receipt})
		else:
			row.merge({"code": result.code, "error": result.error})
			if result.code not in REFUSALS:
				report.exit_code = 2
				report.error = result.error
				report.location = "events[%d]" % index
			else:
				report.exit_code = 1
		report.trace.append(row)
		if report.exit_code == 2:
			break
	# This is a simulated prefix if input was malformed; exit 2 is never a
	# completed scenario. Refusals instead preserve the state and continue.
	report.state = state
	report.final_balance = state.balance
	return report

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var options: Dictionary = {}
	for argument: String in OS.get_cmdline_user_args():
		if argument == "--help":
			print("sim_glint: --scenario=/path/events.json [--out=/fresh/report.json]; exit 0 successful, 1 modeled refusals, 2 invalid input/output")
			quit(0)
			return
		var matched: bool = false
		for key: String in ["scenario", "out"]:
			var prefix: String = "--%s=" % key
			if argument.begins_with(prefix) and not argument.trim_prefix(prefix).is_empty() and not options.has(key):
				options[key] = argument.trim_prefix(prefix)
				matched = true
				break
		if not matched:
			_emit(_failure("Unknown, duplicate or empty argument: %s" % argument, "arguments"), "")
			return
	if not options.has("scenario"):
		_emit(_failure("--scenario is required; no default earning schedule is supplied", "arguments"), "")
		return
	var file: FileAccess = FileAccess.open(options.scenario, FileAccess.READ)
	if file == null:
		_emit(_failure("Cannot read scenario: %s" % options.scenario), "")
		return
	var bytes: PackedByteArray = file.get_buffer(file.get_length())
	file.close()
	var parsed: Dictionary = parse_document(bytes)
	var report: Dictionary = simulate(parsed.document) if parsed.ok else _failure(parsed.error)
	report.scenario_sha256 = parsed.sha256
	report.scenario_path = str(options.scenario)
	_emit(report, str(options.get("out", "")))

func _emit(report: Dictionary, output: String) -> void:
	var text: String = JSON.stringify(report, "\t", true) + "\n"
	if not output.is_empty():
		if FileAccess.file_exists(output) or DirAccess.dir_exists_absolute(output):
			printerr("sim_glint: existing output was preserved; choose a fresh file")
			quit(2)
			return
		var file: FileAccess = FileAccess.open(output, FileAccess.WRITE)
		if file == null:
			printerr("sim_glint: cannot create output: %s" % output)
			quit(2)
			return
		file.store_string(text)
		var write_error: Error = file.get_error()
		file.close()
		if write_error != OK:
			printerr("sim_glint: output write failed: %s" % error_string(write_error))
			quit(2)
			return
	else:
		print(text)
	quit(int(report.exit_code))
