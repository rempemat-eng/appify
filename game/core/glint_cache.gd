class_name GlintCache
extends RefCounted
## Glint from fights, and the cache a downed player leaves (Matt, 10 Nov; data/balance/glint.json
## "fights" and "defeat"). Everything lives in the save, so a quit, a load, a door or getting up changes
## nothing:
##   - `SaveGame.data.paid` holds one key per creature that has paid ("<camp id>/<node name>"). A creature
##     pays once for the life of the save: a camp that comes back after a zone reload or a defeat pays
##     nothing the second time, so nobody farms Glint.
##   - `SaveGame.data.caches` is a list of {zone, x, y, glint}. Going down drops a share of the carried
##     Glint where the player fell. A cache stays until it is picked up; a second defeat adds a second
##     cache and never touches the first.
##   - No cache can strand the story: test/story/test_story_model.gd plays every order with the worst case
##     in it (going down wherever a camp stands until nothing more is taken, no cache ever recovered) and
##     every restore stays affordable. `floor_glint()` is the knob if that ever stops being true.
## world/camp.gd pays, game.gd drops and sets the pickups out (world/glint_cache_pickup.gd).

const BALANCE := "res://data/balance/glint.json"

static var _balance := {}

static func balance() -> Dictionary:
	if _balance.is_empty():
		var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string(BALANCE))
		_balance = doc if typeof(doc) == TYPE_DICTIONARY else {}
	return _balance

## Glint for freeing one creature of `kind` ("mossling", "creature", "boss").
static func fight_glint(kind: String) -> int:
	return int(balance().get("fights", {}).get(kind, 0))

## Pays for the creature `key` if it has not paid in this save. Returns what was paid (0 the second time).
static func pay_once(key: String, kind: String) -> int:
	var paid: Dictionary = SaveGame.data.paid
	var amount := fight_glint(kind)
	if key == "" or amount <= 0 or paid.has(key):
		return 0
	paid[key] = true
	SaveGame.add_glint(amount)
	return amount

## What a cache takes from a purse of `glint`: the share, rounded down. `keep` is a floor the purse is never
## taken below; the game passes `floor_glint()`.
static func amount_for(glint: int, keep: int) -> int:
	var share := float(balance().get("defeat", {}).get("cache_share_of_carried", 0.0))
	return clampi(mini(int(floor(float(glint) * share)), glint - keep), 0, maxi(glint, 0))

## The floor a cache leaves in the purse (data/balance/glint.json defeat.never_below, 0 today). The story
## model (test/story/test_story_model.gd) plays every order with the worst defeats in it and fails if any
## restore the story needs can no longer be paid; raise the floor if it ever does.
static func floor_glint() -> int:
	return int(balance().get("defeat", {}).get("never_below", 0))

## The player went down in `zone` at `at`: a cache is left there. Returns its Glint (0: none was left).
static func drop(zone: String, at: Vector2) -> int:
	var amount := amount_for(int(SaveGame.data.glint), floor_glint())
	if amount <= 0:
		return 0
	SaveGame.add_glint(-amount)
	(SaveGame.data.caches as Array).append({"zone": zone, "x": int(round(at.x)), "y": int(round(at.y)), "glint": amount})
	return amount

## The caches lying in `zone` (the save's own entries).
static func in_zone(zone: String) -> Array:
	return (SaveGame.data.caches as Array).filter(func(c: Dictionary) -> bool: return c.get("zone", "") == zone)

## Picks `cache` up: its Glint goes back to the purse and the entry leaves the save. Returns the Glint.
static func collect(cache: Dictionary) -> int:
	var list: Array = SaveGame.data.caches
	var i := list.find(cache)
	if i < 0:
		return 0
	list.remove_at(i)
	SaveGame.add_glint(int(cache.get("glint", 0)))
	return int(cache.get("glint", 0))
