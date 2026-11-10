#!/usr/bin/env bash
# Plays the game with real input from a fresh save and fails at the first step that does not work
# (npm run playtest:godot). tools/play_driver.gd presses the keys and moves the mouse; this script gives
# it a display, a private profile and the routes, and starts the game again wherever a route says
# `restart`, so quitting and loading are part of the play.
#
#   bash game/tools/playtest.sh                      every route in game/tools/routes/*.txt
#   bash game/tools/playtest.sh path/to/route.txt    one route (or several)
#
# GODOT must point at a Godot 4.7.2 binary (docs/godot.md). With DISPLAY set the game opens there;
# without it this starts its own Xvfb (PLAYTEST_DISPLAY, default :97) and stops it afterwards.
# Results go to PLAYTEST_OUT (default game/reports/playtest, git-ignored): per route a log.txt, the
# engine's godot.log, result.txt and the pictures the route took (fail.png at a failure).
# PLAYTEST_TIMEOUT caps one game session in seconds (default 900).
# A real-time play of the whole route takes about a quarter of an hour; it is not part of check:godot.
set -uo pipefail
GAME=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
GODOT=${GODOT:-godot}
OUT=${PLAYTEST_OUT:-$GAME/reports/playtest}
LIMIT=${PLAYTEST_TIMEOUT:-900}
if ! command -v "$GODOT" >/dev/null 2>&1; then
  echo "playtest: no Godot binary. Set GODOT=/path/to/Godot_v4.7.2-stable (see docs/godot.md)." >&2
  exit 2
fi
SELECTED=$(command -v "$GODOT")
umask 077
TMP=$(mktemp -d) || exit 2
XVFB_PID=""
cleanup() {
  [ -n "$XVFB_PID" ] && kill "$XVFB_PID" 2>/dev/null
  rm -rf "$TMP"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
# A private copy of the executable only (no portable markers), as check.sh does.
mkdir "$TMP/engine" && cp "$SELECTED" "$TMP/engine/godot" && chmod u+x "$TMP/engine/godot" || exit 2
GODOT="$TMP/engine/godot"

if [ -z "${DISPLAY:-}" ]; then
  if ! command -v Xvfb >/dev/null 2>&1; then
    echo "playtest: no DISPLAY and no Xvfb. The driver sends real key and mouse events and needs a window." >&2
    exit 2
  fi
  export DISPLAY=${PLAYTEST_DISPLAY:-:97}
  Xvfb "$DISPLAY" -screen 0 960x540x24 -nolisten tcp >"$TMP/xvfb.log" 2>&1 &
  XVFB_PID=$!
  sleep 1
  if ! kill -0 "$XVFB_PID" 2>/dev/null; then
    echo "playtest: Xvfb did not start on $DISPLAY (set PLAYTEST_DISPLAY to a free display)" >&2
    cat "$TMP/xvfb.log" >&2
    exit 2
  fi
fi

if [ "$#" -gt 0 ]; then
  ROUTES=("$@")
else
  ROUTES=("$GAME"/tools/routes/*.txt)
fi

run_engine() { # $1 profile root, then engine arguments
  local root=$1
  shift
  HOME="$root/home" XDG_DATA_HOME="$root/data" XDG_CONFIG_HOME="$root/config" XDG_CACHE_HOME="$root/cache" \
    "$GODOT" "$@"
}

if [ ! -d "$GAME/.godot/imported" ]; then
  mkdir -p "$TMP/import"/{home,data,config,cache}
  echo "playtest: importing the project (first run)"
  run_engine "$TMP/import" --headless --path "$GAME" --import >"$TMP/import.log" 2>&1 || { tail -20 "$TMP/import.log"; exit 2; }
fi

NOISE='ALSA|audio_driver_alsa|All audio drivers failed|init_output_device|pulseaudio|PulseAudio'
FAILED=0
for ROUTE in "${ROUTES[@]}"; do
  NAME=$(basename "$ROUTE" .txt)
  if [ ! -f "$ROUTE" ]; then
    echo "FAIL $NAME: no route file at $ROUTE"
    FAILED=1
    continue
  fi
  ROUTE=$(cd "$(dirname "$ROUTE")" && pwd)/$(basename "$ROUTE")
  DIR="$OUT/$NAME"
  rm -rf "$DIR"
  mkdir -p "$DIR"
  # one profile for the whole route: a restart loads the save the session before it wrote
  PROFILE="$TMP/profile-$NAME"
  mkdir -p "$PROFILE"/{home,data,config,cache}
  FRESH=--fresh
  SESSIONS=0
  START=$(date +%s)
  while true; do
    SESSIONS=$((SESSIONS + 1))
    rm -f "$DIR/result.txt"
    run_engine "$PROFILE" --path "$GAME" --audio-driver Dummy --resolution 960x540 --position 0,0 -- \
      $FRESH --play="$ROUTE" --play-out="$DIR" >>"$DIR/godot.log" 2>&1 &
    PID=$!
    ( sleep "$LIMIT"; touch "$DIR/timed-out"; kill -9 "$PID" 2>/dev/null ) &
    WATCH=$!
    wait "$PID"
    CODE=$?
    kill "$WATCH" 2>/dev/null
    wait "$WATCH" 2>/dev/null
    FRESH=
    [ -f "$DIR/resume.txt" ] && [ "$CODE" -eq 0 ] && continue
    break
  done
  SECS=$(( $(date +%s) - START ))
  BAD=$(grep -E 'SCRIPT ERROR|^ERROR:|Parse Error|Failed loading resource' "$DIR/godot.log" | grep -Ev "$NOISE" | sort | uniq -c | head -20 || true)
  RESULT=$(cat "$DIR/result.txt" 2>/dev/null || true)
  if [ "$CODE" -eq 0 ] && [ -z "$BAD" ] && [ "${RESULT:0:4}" = "PASS" ]; then
    echo "ok   $NAME (${SECS}s, $SESSIONS game sessions)"
  else
    FAILED=1
    echo "FAIL $NAME (${SECS}s, $SESSIONS game sessions, exit $CODE)"
    if [ -n "$RESULT" ]; then
      echo "  $RESULT"
    elif [ -f "$DIR/timed-out" ]; then
      echo "  the game was stopped after ${LIMIT}s (PLAYTEST_TIMEOUT)"
    elif [ "$CODE" -ge 128 ]; then
      echo "  the game was killed by signal $((CODE - 128)) (9 is usually the machine running out of memory)"
    else
      echo "  the game ended without a result (a crash, or the driver did not start)"
    fi
    [ -n "$BAD" ] && echo "  engine errors:" && echo "$BAD"
    echo "  last steps:"
    tail -6 "$DIR/log.txt" 2>/dev/null | cut -c1-240 | sed 's/^/    /'
    echo "  see $DIR (log.txt, godot.log, fail.png)"
  fi
done
[ "$FAILED" -eq 0 ] && echo "playtest passed" || echo "playtest FAILED"
exit $FAILED
