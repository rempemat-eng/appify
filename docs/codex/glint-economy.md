# Glint ledger and simulation (Y3/r1)

[`GlintEconomy`](../../game/core/glint_economy.gd) is an isolated, explicit-event transaction API. [`sim_glint.gd`](../../game/tools/sim_glint.gd) uses that same GDScript implementation to simulate ordered earnings and spending. It follows the project's existing practice of reproducible economy inputs and reports, without changing the older Dream Dust [C33 simulation](economy-sim.md) or [PR #211](https://github.com/rempemat-eng/appify/pull/211). Glint is a separate currency; there is no conversion, daily income, nap reward, default schedule or inferred earning frequency.

## API and transaction schema

All methods are static and return a dictionary with `ok`. A failure has `code` and `error` and leaves supplied values unchanged.

| Method | Result on success |
| --- | --- |
| `fresh(opening_balance = 0, initial_owned = [])` | Detached schema-version-1 Glint `state`, with opening/current balance, initial/current cosmetic ownership and an empty ordered receipt array. |
| `validate(snapshot)` | Replays the entire receipt history and returns a detached `state`; claimed closing balance and ordered ownership must match. |
| `apply(snapshot, event)` | Validated detached `state`, `receipt` and `applied`; the input snapshot/event is never modified. |
| `quote_cosmetic(folk, item_id, price, eligible)` | A proposal `offer` plus provenance, without charging money or applying effects. |
| `quote_respec(policy, uses, context)` | A proposal `offer` using the supplied policy/use count/context, without charging money or resetting points. |

An event has only these fields:

| Field | Contract |
| --- | --- |
| `id`, `source` | Required nonblank strings without NUL. `id` identifies one transaction within this ledger; `source` records caller-supplied provenance. |
| `kind` | `earn` or `spend`. |
| `amount` | Whole, nonnegative Glint in `0..9007199254740991`, the exact JSON interchange range rather than a gameplay cap. Integral JSON floats are accepted; booleans, fractions, nonfinite values and overflow are refused. |
| `source_status` | Optional nonblank provenance/status text; proposal labels are retained rather than promoted to approved settings. |
| `category`, `item`, `eligible` | Required only for `spend`: supported category, nonblank item identity and an explicit boolean eligibility decision. Earnings must omit all three. |

Earnings must be positive. Spending must be positive except an explicitly supplied zero-price `respec`. Supported spending categories are `restoration`, `forge`, `shop`, `cosmetic`, `respec` and `map_service`; Glint cannot buy levels, XP or skill points. Unknown fields/categories are rejected rather than reinterpreted.

Insufficient funds, `eligible=false` and an already-owned cosmetic are atomic refusals. Cosmetic ownership uses the exact supplied identity, for example `bramble/acorn_whistle`; other categories do not grant ownership or enforce one-time purchases. The caller must establish access, stock, prices and eligibility. A source string or validated receipt history proves internal consistency, not entitlement or trusted provenance.

Reapplying an identical normalised payload with the same ID succeeds with `applied=false`, without another receipt or charge/reward. Reusing the ID for a different payload returns `duplicate_conflict`. Snapshots reject duplicate receipt IDs, malformed entries, impossible spending, tampered balances/ownership and other currencies. Returned state/receipts are detached from caller inputs; callers must persist the returned state themselves.

## Authored inputs and proposal boundaries

The current vertical-slice ordering can be expressed without choosing new earning rates. Starting at zero, these authored values total **85 Glint**:

| Event | Change | Balance | Source |
| --- | ---: | ---: | --- |
| `woodland_stones` reward | +40 | 40 | [Quest](../../game/data/quests/woodland_stones.json) |
| `road_to_crossroads` reward | +10 | 50 | [Quest](../../game/data/quests/road_to_crossroads.json) |
| Restore `forge` | −30 | 20 | [Crossroads restores](../../game/data/plans/crossroads.json) |
| `under_the_stones` reward | +60 | 80 | [Quest](../../game/data/quests/under_the_stones.json) |
| Restore `fern_cottage` | −20 | 60 | [Crossroads restores](../../game/data/plans/crossroads.json) |
| `home_again` reward | +25 | 85 | [Quest](../../game/data/quests/home_again.json) |

These are the existing quest/plan amounts used by [`Quests`](../../game/core/quests.gd) and [`Village`](../../game/core/village.gd), including the plan's explicit placeholder labels. The ledger does not replace them with the larger first-value incomes/building budgets in [`balance/glint.json`](../../game/data/balance/glint.json), whose status remains “first values for the sim, not settings”. This arithmetic models the supplied order; it does not complete quests, satisfy restoration conditions or play the slice.

`quote_cosmetic` resolves a Glint-unlock item from the supplied folk's `outfits`/`accessories`, returns its `folk/item` identity, authored unlock event/note and unchanged folk `status`. The current [progression catalogue](../../game/data/progression/catalogue.json) references 14 folk documents containing 19 such identities. Price and eligibility are **explicit caller inputs**: numbers and stall tiers in prose notes are not parsed into authoritative prices or stock. Unknown stock/access remains the receiving owner's decision. The offer has `price_source="caller_explicit"`; the result is `proposal=true`, `effects_applied=false` even when eligibility is true.

`quote_respec` reads only the supplied policy's `sinks.respec.first` and `after`, retaining its `status`. The current balance proposal says first use **0**, subsequent uses **50** Glint, consistent with the [progression proposal](../vision/progression.md). The caller supplies a whole nonnegative `uses` count and every boolean context flag: `at_hut_bed`, `in_fight`, `in_siege`, `in_dungeon`, `allow_proposal`. Eligibility requires the hut bed and explicit proposal permission, with no fight/siege/dungeon. The caller must define whether the use count is per folk, account or another approved scope; this API makes no choice. The result remains `proposal=true`, `effects_applied=false`, `price_source="provided_policy"`.

To apply a quote to a simulated ledger, copy `result.offer`, add a unique `id`, then call `apply`. Quote metadata stays outside the event. This records only the explicit fee and cosmetic ledger identity where relevant. It does not reset Y1 points, grant outfits/perks, set live stock, emit unlock events, write SaveGame or wire the owned UI. Those effects and any atomic payment/effect integration remain receiving-system work for Claude A's review.

## Headless explicit-event simulation

Write a scenario JSON object with required `schema_version: 1`, `currency: "Glint"`, `opening_balance` and ordered `events`. Optional fields are `initial_owned` (unique identities), `label`, `source_status` and `assumptions` (an array of text). Unknown fields are invalid. For example, this models the existing Road to Crossroads reward once, then an identical replay:

```json
{
  "schema_version": 1,
  "currency": "Glint",
  "opening_balance": 0,
  "label": "One authored reward and its retry",
  "assumptions": ["The caller has established quest completion"],
  "events": [
    {"id": "quest:road_to_crossroads", "kind": "earn", "amount": 10, "source": "game/data/quests/road_to_crossroads.json"},
    {"id": "quest:road_to_crossroads", "kind": "earn", "amount": 10, "source": "game/data/quests/road_to_crossroads.json"}
  ]
}
```

Use the project's Godot binary ([setup](../godot.md)), with a readable scenario path and an existing parent directory for a **fresh** output file:

```sh
"$GODOT" --headless --audio-driver Dummy --path game \
  -s res://tools/sim_glint.gd -- \
  --scenario=/absolute/path/events.json --out=/absolute/path/fresh-report.json
```

Prefer `--out` for machine-readable JSON; Godot's stdout may also contain its engine banner. Existing output files/directories are preserved, not overwritten. `--help` prints the short usage. The report retains input assumptions/status, exact scenario byte SHA256/path (including a UTF-8 BOM), per-event before/after balances, receipts/refusals, final ledger state and `settings_applied=false`.

`parse_document(bytes)` validates UTF-8 before decoding and checks Unicode escapes before Godot's JSON parser. Invalid UTF-8, raw/escaped NUL and unpaired surrogates are refused instead of silently replacing transaction identities. Valid Unicode, paired surrogates and literal escaped backslash text remain valid. It returns `ok`, `sha256` and either `document` or `error`; the CLI writes an invalid-input report when a usable fresh `--out` was supplied.

| Exit | Meaning |
| --- | --- |
| `0` | Every event succeeded, including identical retries with `applied=false`. |
| `1` | Valid modelled refusals (`insufficient_funds`, `not_eligible`, `already_owned`) occurred; each leaves state unchanged and simulation continues. |
| `2` | Invalid arguments/JSON/schema/event/snapshot, conflicting transaction ID, overflow or output failure. An event error stops at that event; any returned closing state is only the successful prefix, not a completed scenario. |

No timestamps, real-time schedule, currency conversion, default prices, earning rates, stock tiers, live progression or physical/gameplay effects are inferred. Reports can compare explicit caller assumptions; they do not establish balance, player behaviour, live wiring or native/device acceptance.

## Checks

```sh
"$GODOT" --headless --audio-driver Dummy --path game --import
"$GODOT" --headless --audio-driver Dummy --path game \
  -s res://addons/gdUnit4/bin/GdUnitCmdTool.gd --ignoreHeadlessMode \
  -a res://test/test_glint_economy.gd -rd reports -c
npm run check:godot
npm run verify
npm run check:art-repro
```

The focused suite exercises the ledger, real authored rewards/restores and proposal quotes, and calls the same simulator implementation. Retain actual final-head command results and CLI limitations in the PR handoff; this document does not assert a completed validation run or approve design, art or balance changes.
