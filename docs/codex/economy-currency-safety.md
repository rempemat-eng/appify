# C9, first slice: lossless raid currency

Base: `aeeceb1ecbae77549ef0aedd1815a17ee3b8e05c` (17 October 2026).
This is a bounded part of approved L2/C9, not the complete economy feature.
No artwork, visual component, backend schema or saved-data version is changed.

## What changes

- A lost attacking raid no longer subtracts 10 GRASS.
- A lost defence ignores the incoming raid's legacy `grass_amount`; it never
  subtracts a percentage of the wallet, including for staged pre-upgrade raids.
- Valid attacking wins keep the existing reward calculation: the lesser of the
  rival's balance and `max(10, floor(balance * 0.3))`. This is a reward credit,
  not a transfer from the rival. Successful defence still awards 20.
- Practice rewards, daily limits, cards, mission rewards, nap earnings, feed
  prices, level prices and hat prices remain unchanged. Mood and the existing
  recovery shield are unchanged pending C9's care model.
- New outgoing and simulated raid records carry `grass_amount: 0`. Before sync,
  `safeRaidTransport` copies even an old queued record with a zero wire debit.
  A failed upload keeps the original saved queue/history for a safe retry.
- No retrospective refunds, balance normalisation, ownership changes or data
  resets. Existing save migrations and unknown-field retention remain in use.

`lib/economy.ts` exports `attackingRaidReward`, `settleAttackingRaid`,
`settleDefendingRaid`, `safeRaidTransport` and `RAID_TRANSFER_GRASS`.
Settlements report the resulting balance, actual earned amount and zero
transferred GRASS. They never lower an existing numeric wallet or replace it
with infinity. Save recovery remains responsible for invalid saved data.

## Feedback for Claude: visual integration required

Please keep the PR draft until the old theft/loss presentation is aligned:

1. `components/game-battle.tsx`: replace `YOU STOLE ...` with a reward label;
   a defeat should say GRASS was kept, not show a negative amount (even `-0`).
2. `components/game-overlays.tsx`: replace the stolen-GRASS dialogue and the
   outgoing `GrassFlight` on a lost defence. Existing historical raid amounts
   are not evidence of a current wallet deduction.
3. The new wire `grass_amount` means transferred currency, always zero. Do not
   use it as an attacking reward display. The existing `raidGrass` export now
   returns the win reward or zero on defeat.

These are requested changes, not edits to Claude's visual lane. C9 is still
`taken`, not `complete`, even if this slice's engineering checks are green.

## Remaining C9 work

- Protected-hour earnings: Rest 2x, Focus 1.5x, with interval-aware settlement,
  saved launch context, hydration/edit races and repeated-wake tests. The current
  planner is stored separately and edited inside Claude's UI; merely loading it
  once must not make edits ineffective or retroactively boost an existing break.
- Persistent worn-out health, battle effects, nursing/medicine and small nap
  recovery; a daily well-kept gift connected to world health. The current plan
  does not specify the medicine price, recovery/wear values or gift amount and
  eligibility thresholds. This slice does not invent or ship those values.
- Wallet/care/earning-breakdown UI in Claude's lane.

No new mechanic or reward beyond the approved currency-safety change is added.

## Evidence and limits

`npm run check:economy` runs 2,110 deterministic pure assertions plus an actual
store sync test with substituted native/backend boundaries: failed legacy
upload, zero-debit retry, original record retained, legacy incoming loot ignored,
and duplicate defence delivery credited once. No real requests are made.

`check:game` includes real store tests for win/loss, repeated finish, reload,
unversioned balances, hats/cards/history/collection/chosen companion and unknown
save fields. Actual feed, level and hat purchase costs still lower the wallet
only on those chosen actions. The existing full save fixture suite remains.

Exact final commit, `npm run verify`, matching CI, screenshot artifact and
preview coverage are recorded in the PR. A mocked transport does not establish
live backend behaviour. Already-existing remote raid rows and older clients are
not migrated here; multiplayer remains deferred. No phone, native runtime,
device-use, audio, screen-reader, memory/FPS or full visual approval is claimed.
