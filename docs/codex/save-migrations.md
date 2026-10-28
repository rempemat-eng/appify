# Godot save compatibility (Y6)

The runtime remains `game/core/save_game.gd`, with one JSON document and VERSION 1.
There is no new gameplay state or balance change. Expo saves use a separate engine
and are not Godot save documents; this task does not convert them.

## Audited history

- `c21814f1`: the Godot foundation introduced VERSION 1, zone/spawn, Glint,
  flags, quests, player health and settings. Its loader also accepted versionless
  and explicit version-0 partial documents.
- `49981c81`: village restoration was added without changing VERSION. Missing
  village state therefore needs defaults even in a version-1 document.
- Base `1e8ce2d8`: these are the only authored Godot save shapes in repository
  history. The four JSON fixtures in `game/test/fixtures/saves/` are representative
  examples built from these contracts, not recovered user saves.

## Contract

Migration validates structure before indexing it, copies recursively, advances
version 0 to 1 explicitly, then fills missing defaults recursively. Existing and
unknown fields are preserved, including retired quest records, settings and
village extensions. Accepted documents do not share nested containers with their
input or with other migrated documents. Migrating again gives the same result.

Missing files retain the existing fresh-game behaviour. Invalid JSON/non-objects
return ERR_PARSE_ERROR; malformed known fields return ERR_INVALID_DATA; a future
version returns ERR_UNAVAILABLE. Refused loads emit no loaded signal, retain the
running state, and leave the source bytes untouched. Loading never writes a file.
A subsequent save also refuses to replace an existing future-version target,
including an autosave after a failed load. Recovering that slot requires deliberately
moving that newer file or using the compatible game build.

Known persisted integer fields must be finite, whole and exactly representable by
Godot's JSON-number parser, within plus or minus 9,007,199,254,740,991. Numeric strings,
booleans, fractions and overflow are refused rather than silently coerced. Negative
legacy values are preserved: validation does not impose economy or combat rules.
Unknown fields retain their JSON values and are not interpreted as new game rules.
Quest IDs/states and location IDs are not rewritten or checked against current content.
Missing quest steps retain the existing default of zero.

Saving validates a detached document before opening the temporary file. It checks
write/flush errors, renames only after a successful write, removes a failed temporary
file, and emits saved/updates the live version only after successful publication.
The existing temp-and-rename design remains; this is not a power-loss durability,
filesystem locking or multi-process transaction guarantee.

## Verification

`game/test/test_save.gd` covers all historical shapes, normalisation/idempotence,
unknown-field retention, nested alias isolation, invalid/future data, exact numeric
boundaries, real disk round trips, source-byte and live-state preservation,
write/rename failures, default-path use and success/failure signals. It runs through
the existing `npm run check:godot`; no package/check registration changes are needed.
The original four save tests remain.

The frozen base reproduction accepts a future version as version 1 and changes its
caller's nested player/settings dictionaries. Final gate results and exact source
head/tree belong in the PR handoff. Runtime UI error presentation, actual crash or
power-loss injection, cloud saves, native phones, future schema versions and a combined
W1-W7/Y-system integration are outside this task.
