#!/usr/bin/env bash
# Downloads the pinned Godot (Linux x86_64) into $1 (default ~/.cache/napattack-godot), checks its
# SHA-512 against the official SHA512-SUMS, switches it to self-contained mode (a _sc_ file beside the
# binary keeps editor settings out of ~/.config) and prints the binary's path:
#   export GODOT=$(bash game/tools/get_godot.sh)
set -euo pipefail
VERSION=4.7.2
ZIP=Godot_v${VERSION}-stable_linux.x86_64.zip
SHA512=9aa00f7a605200940bce3027a567b782f49bd8e940dd06ae9e987bd65aee1b1467edd56ed84fcdcbdd44354bf613bdbb4e5d2913e925850368e150c59ed54c65
DIR=${1:-${XDG_CACHE_HOME:-$HOME/.cache}/napattack-godot}
BIN="$DIR/Godot_v${VERSION}-stable_linux.x86_64"
if [ ! -x "$BIN" ]; then
  mkdir -p "$DIR"
  curl -fsSL -o "$DIR/$ZIP" "https://github.com/godotengine/godot/releases/download/${VERSION}-stable/$ZIP"
  echo "$SHA512  $DIR/$ZIP" | sha512sum -c --quiet - >&2
  unzip -q -o "$DIR/$ZIP" -d "$DIR"
  rm "$DIR/$ZIP"
  chmod +x "$BIN"
fi
touch "$DIR/_sc_"
echo "$BIN"
