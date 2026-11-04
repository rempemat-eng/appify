#!/usr/bin/env bash
# Headless check of the Godot project (npm run check:godot). Three steps, each failing on any
# "SCRIPT ERROR" or engine "ERROR:" line, because Godot keeps running and exits 0 after script errors:
#   1. import the project (fresh .godot cache on CI)
#   2. run the main scene for $FRAMES frames with a fresh save (-- --fresh)
#   3. run the GdUnit4 suites in game/test (reports in game/reports, git-ignored)
# GODOT must point at a Godot 4.7.2 binary (docs/godot.md); user data and editor settings go to a
# private executable-only copy with fresh per-child roots, including version probing.
set -uo pipefail
GAME=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
GODOT=${GODOT:-godot}
FRAMES=${FRAMES:-300}
if ! command -v "$GODOT" >/dev/null 2>&1; then
  echo "check:godot: no Godot binary. Set GODOT=/path/to/Godot_v4.7.2-stable (see docs/godot.md)." >&2
  exit 2
fi
# Resolve without invoking the original: portable markers beside it override XDG.
SELECTED=$(command -v "$GODOT")
isolation_error() {
  echo "check:godot: cannot isolate Godot executable" >&2
  exit 2
}
[ -f "$SELECTED" ] && [ -x "$SELECTED" ] || isolation_error
umask 077
TMP=$(mktemp -d) || isolation_error
trap 'rm -rf "$TMP"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
mkdir "$TMP/engine" || isolation_error
GODOT="$TMP/engine/godot"
# Copy only executable bytes, never sibling _sc_/editor_data/settings/profiles.
cp "$SELECTED" "$GODOT" && chmod u+x "$GODOT" || isolation_error
[ -f "$GODOT" ] && [ -x "$GODOT" ] && cmp -s "$SELECTED" "$GODOT" || isolation_error

run_engine() {
  local root
  root=$(mktemp -d "$TMP/phase.XXXXXX") || isolation_error
  mkdir "$root/home" "$root/data" "$root/config" "$root/cache" "$root/tmp" || isolation_error
  HOME="$root/home" XDG_DATA_HOME="$root/data" XDG_CONFIG_HOME="$root/config" \
    XDG_CACHE_HOME="$root/cache" TMPDIR="$root/tmp" "$GODOT" "$@"
}
# Version probing is an engine invocation too; establish containment first.
run_engine --version >"$TMP/version.log" 2>/dev/null
CODE=$?
VERSION=$(head -n1 "$TMP/version.log")
if [ "$CODE" -ne 0 ]; then
  echo "check:godot: could not read Godot version (exit $CODE)" >&2
  exit 2
fi
case "$VERSION" in
  4.7.2.*) ;;
  *) echo "check:godot: expected Godot 4.7.2, got '$VERSION'" >&2; exit 2 ;;
esac
FAILED=0

# Engine lines that are environment noise, not project errors (no sound card on CI and containers).
NOISE='ALSA|audio_driver_alsa|All audio drivers failed|init_output_device|pulseaudio|PulseAudio'

scan() { # $1 step name, $2 log file, $3 exit code
  local bad
  bad=$(grep -E 'SCRIPT ERROR|^ERROR:|Parse Error|Failed loading resource|Cannot open file' "$2" | grep -Ev "$NOISE" || true)
  if [ -n "$bad" ] || [ "$3" -ne 0 ]; then
    echo "FAIL $1 (exit $3)"
    grep -E -A6 'SCRIPT ERROR|^ERROR:|Parse Error|Failed loading' "$2" | grep -Ev "$NOISE" | head -60
    [ "$3" -ne 0 ] && tail -40 "$2"
    FAILED=1
  else
    echo "ok   $1"
  fi
}

run_engine --headless --path "$GAME" --import >"$TMP/import.log" 2>&1
scan "import" "$TMP/import.log" $?

run_engine --headless --audio-driver Dummy --path "$GAME" --quit-after "$FRAMES" -- --fresh >"$TMP/run.log" 2>&1
scan "run main scene for $FRAMES frames" "$TMP/run.log" $?

# no -d: with the debugger on, a parse error drops into Godot's interactive "debug>" prompt and hangs
run_engine --headless --audio-driver Dummy --path "$GAME" -s \
  res://addons/gdUnit4/bin/GdUnitCmdTool.gd --ignoreHeadlessMode -a res://test -rd reports -c >"$TMP/test.log" 2>&1
CODE=$?
grep -E 'Statistics|tests cases|failures|errors|Overall|PASSED|FAILED' "$TMP/test.log" | sed 's/\x1b\[[0-9;]*m//g' | tail -8
scan "GdUnit4 tests" "$TMP/test.log" $CODE
[ "$FAILED" -eq 0 ] && echo "check:godot passed" || echo "check:godot FAILED"
exit $FAILED
