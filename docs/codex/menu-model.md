# Y7: menu view model

`game/core/menu_model.gd` is a non-visual, caller-owned `RefCounted` model. It extends
the existing pause/settings menu and quest/save services without replacing them.
There is no autoload, input binding, save field, item grant or gameplay action.

## Existing contracts audited

- `game/ui/pause_menu.gd` owns pause, settings, focus and Resume/Quit. It remains unchanged.
- `game/core/quests.gd` owns quest definitions, state transitions, rewards and HUD tracking.
  A saved quest record is `{state, step}`; active steps are zero-based, and completed
  records use the number of steps. The journal consumes this exact contract.
- `game/core/save_game.gd` owns persistence. Main has no Godot inventory store or item
  instance schema. This change neither adds one nor imports a speculative save shape.
- The 27 October development plan authorises Y7 menu/inventory/journal logic without
  new art. `docs/vision/interface.md` describes the existing Godot pause controls.
  `docs/vision/progression.md` and the older game-design proposal disagree on weapon
  slots. This view model makes no equipment/capacity/salvage decision from that older proposal.

## API

Create the model with `preload("res://core/menu_model.gd").new()`.

1. `configure(["inventory", "journal", "settings"])` sets an ordered list of unique,
   nonblank tab IDs. These IDs are an example supplied by the caller, not a final
   menu specification. Configuration closes the menu and clears its transient rows.
2. `set_rows(tab, records)` supplies detached view records with unique string `id`s.
   The caller chooses labels, grouping and order. Unknown fields survive unchanged.
3. `open(tab)`, `select_tab`, `move_tab`, `select_row`, `move_row`, `show_detail`,
   `back` and `close` manipulate view state. Tab movement wraps; row movement stops
   at the ends. Direction arguments use their sign, including for repeated input.
4. `snapshot()` and `changed(view)` expose detached dictionaries. Retaining or
   editing these values cannot edit the model's nested data.

The model has two open levels: tab/list and selected-row detail. Back closes detail
first, then the menu; Back while closed returns false. Closed navigation is inert.
Changing tabs closes detail and keeps each tab's selected ID. A refreshed list keeps
the selection by ID, even when reordered. If that ID disappears, it closes stale
detail and selects the nearest surviving index, or no item when empty.

Invalid configuration/row replacement returns false atomically. No save is repaired,
truncated or reset. A renderer should retain its previous view and show the input error.
Projection failures return `{ok: false, rows: [], error: ...}`. An empty successful
result is distinct from malformed data and must not conceal a failed projection.

## Inventory and journal projections

`inventory(records, query)` projects an array of caller-owned item-instance records.
Each needs a unique nonblank string `id`; optional `name` must be a string. Filtering
is case-insensitive over ID/name, preserves source order and validates every record,
including filtered-out rows. Other fields are opaque and copied. There is no sorting
by guessed value, stacking, comparison formula, equip, salvage, purchase, capacity,
drop roll or mutation of an inventory. Those belong to the eventual item/economy owner.

`journal(Quests.defs, SaveGame.data.quests)` projects only started/completed quests.
It hides absent/`none` quests, orders active before done and uses IDs for stable order
within each group. It exposes title/kind, actual state/step, step count and the active
step text. Completed rows have no current-step text. It does not evaluate conditions,
advance quests, choose HUD tracking, disclose future steps or claim rewards.

Unknown saved quest IDs, malformed records and inconsistent/out-of-bounds progress
produce explicit failures. Whole JSON floats are accepted as step indices. The
projection does not change authored definitions, unknown save metadata or live state.
Content migration/removal decisions stay with the quest/save owners.

## Integration and acceptance limits

Claude A wires this model into the existing menu and its input/focus lifecycle after
review. The caller still owns pausing/resuming, swallowing handled Back input,
refreshing rows when underlying state changes and displaying projection errors.
Inventory actions/persistence require their authoritative contract; this API does
not authorise a second item store. The model is useful without those actions as a
read-only inventory and quest journal with deterministic navigation.

Tests cover all twenty real quest definitions and each active step, completed and
unstarted states, one live quest transition, malformed/unknown saved data, item search,
nested alias isolation, empty lists, refresh/removal, tab focus memory and Back.
`npm run check:godot` discovers the suite automatically; no package script change.

Not covered by source/engine tests: rendered tabs, keyboard/gamepad event dispatch,
screen-reader focus, mouse/touch hit targets, native phones, final art, live item
actions/persistence, or acceptance of the combined W/Y slice. No device or whole-menu
UI completion claim follows from this isolated logic step.
