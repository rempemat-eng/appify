# Pinned Godot download cache

Y13 download-cache step, slot `ci-map`. The existing Godot workflow and getter remain the
entry points. C35's generator cache and verification runner are separate work in PR #185.

The Godot job caches only the Linux x86_64 release archive. Its exact key includes the
runner OS, architecture and the complete getter hash, so changing the pinned version,
SHA-512 or download logic creates a new key. There are no fallback restore keys.

`bash game/tools/get_godot.sh [binary_directory] [archive_directory]` retains the original
single-directory interface. With no second argument, the archive stays in the binary
directory. The pinned version and SHA-512 are unchanged.

Every invocation verifies the archive against that digest, including cache hits, then
extracts the named executable into a temporary directory and replaces the binary. An
existing executable is never accepted as evidence of an intact download. Missing archives
download to temporary files and become reusable only after verification. Failed downloads
and extractions clean up their temporary paths and print no binary path. A corrupt cached
archive fails closed; delete that exact Actions cache entry before retrying. The job cannot
replace an immutable corrupt cache under the same key.

The workflow first runs the getter's subprocess tests, then restores the archive and runs
the existing import, 300-frame main scene and full GdUnit suite. It never caches `.godot`,
test reports, user data or a successful check result. Cache hits cannot skip these checks.
The getter runs separately from the `GITHUB_ENV` write so a failed checksum stops the step.

Run the focused checks with:

```sh
python3 -m unittest discover -s game/tools -p test_get_godot.py -v
```

Tests use a deterministic synthetic archive and a temporary copy of the production getter
with only its pinned digest replaced by the fixture digest. Real SHA-512 verification and
unzip run against those bytes; a local curl stub records downloads. This exercises cache
reuse and failure behaviour without network access or an alternative production trust pin.

Archive reuse removes one engine download per warm runner. No hosted timing improvement,
device performance, visual approval or whole-Y13 completion is implied.
