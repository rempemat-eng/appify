# Godot name and save-directory migration

Z1, Caliper, under [ASSIGN6913435709](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6913435709).
The app/window name and custom user directory in `game/project.godot` are `MyGame`.
The save document remains version 2. Export presets, bundle identifiers, kit/schema IDs,
game rules and player files are unchanged.

On an ordinary boot of the default save slot, `SaveGame` derives the old desktop custom
directory from the parent of `OS.get_user_data_dir()` and looks for `napattack/save_0.json`.
This follows Godot's [custom-directory locations](https://docs.godotengine.org/en/stable/tutorials/io/data_paths.html).
It copies the original bytes through a separate temporary file into the new slot, then
uses the existing loader. It does not rewrite, rename or delete the old save.
An existing destination, including a damaged/future file or a directory, takes precedence.
The destination is checked again immediately before publishing the copy.

If reading, writing or publishing the import fails, default autosave is refused for that
target so a fresh save cannot hide the old progress on the next boot. The next ordinary
boot retries. An explicitly different save target remains usable. `--fresh` skips this
lookup, and a custom save path never searches the real old directory.
Damaged/future documents retain the existing loader's policy: damaged bytes are copied
to the new slot's `.broken` file before a fresh autosave; future versions are not overwritten.
In each case the original old-folder file is still retained.

Eight new cases in `game/test/test_save.gd` cover the rich v2 fixture, exact copied bytes,
known progress and opaque nested fields, later stable save/load, existing destination
precedence, fresh/custom-path isolation, missing legacy data, an obstructed write with
autosave refusal and retry, damaged/future documents and an occupied destination directory.
They use detached save nodes and disposable test paths, not live saves.

Validation at source handoff is limited to GDScript grammar parsing with gdtoolkit 4.5.0,
JSON fixture parsing and source/tree isolation checks. Godot compilation, these eight
regressions, routes, full gates and hosted Ready checks have not run; the lead must allocate
the single final chain. Grammar parsing is not Godot type checking or runtime acceptance.
Desktop/macOS/Windows launches, mobile/web storage and simultaneous first launches have
not been exercised. The destination recheck is not an atomic cross-process lock.

Integration remains open: the Z4-owned `game/tools/playtest.sh` still seeds the old folder.
It must be reconciled by its owner/lead before claiming all routes on the combined source.
Other technical name matches are reported in the PR; no claim that only kit/fixture names
remain is made. A failed authenticated Git transport check prevented a local whole-repo
grep; the handoff instead records a scan of 1,400 selected game text files at the pinned base,
with the candidate's changed files substituted. Binary assets are outside that text scan.
