# MyGame Godot import cache

This Y13 step extends PR327's verified archive cache. It does not cache check
results or replace Godot's import pass. CI restores only `game/.godot/imported`
and always runs the existing `game/tools/check.sh`: import, a fresh-userdata
300-frame main run, and every Godot test. A new cache entry is saved only after
that command succeeds. There are no fallback restore keys.

`python3 scripts/godot-import-cache.py --engine "$GODOT" --runner-os Linux
--runner-arch X64` prints one exact key. It hashes the executable bytes, runner
OS/architecture, each tracked game path/index mode/current file content, and
the workflow and both helper files. Fields are length-prefixed. Git commit
metadata, checkout paths and mtimes do not affect the key. Changing sources,
import sidecars/settings, project configuration, an asset, engine or workflow
invalidates it. A clean CI checkout is the intended caller; missing files,
untracked non-ignored game files, symlinks, unmerged/unsupported index entries,
missing project/engine/helpers and tracked generated imports fail with exit 2
and no stdout. Ignored generated imports and reports do not enter the key.

The existing getter still verifies its pinned SHA-512 on every archive reuse
and extracts a fresh executable. Version/digest pins and all 12 getter controls
are unchanged. C35's package/generator/check-runner ownership is separate.

Focused controls: `python3 scripts/godot-import-cache.test.py -v` uses actual
temporary Git repositories and subprocesses, including paths with spaces,
content/platform/engine changes, add/delete/rename/mode changes, invalid inputs,
ignored outputs and workflow ordering. Run the getter controls separately with
`python3 -m unittest discover -s game/tools -p test_get_godot.py -v`.

Acceptance still requires real cold/restored full-check equivalence, full
`npm run verify` with zero lint warnings and `npm run check:art-repro` on the
final exact source, followed by matching hosted CI. Until recorded in the PR,
those gates are pending. No rendered/device/gameplay/art approval follows from
a cache hit or a key test. A failed cache restore/check is never a pass.
