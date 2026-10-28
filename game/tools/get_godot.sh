#!/usr/bin/env bash
# Downloads the pinned Godot (Linux x86_64) into $1. Optional $2 holds the reusable archive;
# otherwise it stays beside the binary. Every invocation checks the archive's official SHA-512
# and extracts a fresh binary, even when an executable already exists. Self-contained mode
# (a _sc_ file beside the binary) keeps editor settings out of ~/.config. Prints only its path:
#   export GODOT=$(bash game/tools/get_godot.sh)
set -euo pipefail
VERSION=4.7.2
ZIP=Godot_v${VERSION}-stable_linux.x86_64.zip
SHA512=9aa00f7a605200940bce3027a567b782f49bd8e940dd06ae9e987bd65aee1b1467edd56ed84fcdcbdd44354bf613bdbb4e5d2913e925850368e150c59ed54c65
DIR=${1:-${XDG_CACHE_HOME:-$HOME/.cache}/napattack-godot}
BIN="$DIR/Godot_v${VERSION}-stable_linux.x86_64"
ARCHIVES=${2:-$DIR}
ARCHIVE="$ARCHIVES/$ZIP"
DOWNLOAD=
STAGE=
cleanup() {
  if [ -n "$DOWNLOAD" ]; then rm -f -- "$DOWNLOAD"; fi
  if [ -n "$STAGE" ]; then rm -rf -- "$STAGE"; fi
}
trap cleanup EXIT
mkdir -p "$DIR" "$ARCHIVES"

SOURCE="$ARCHIVE"
if [ ! -f "$ARCHIVE" ]; then
  DOWNLOAD=$(mktemp "$ARCHIVES/.godot-download.XXXXXX")
  curl -fsSL -o "$DOWNLOAD" "https://github.com/godotengine/godot/releases/download/${VERSION}-stable/$ZIP"
  SOURCE="$DOWNLOAD"
fi
# Cache contents are untrusted. Refuse a corrupt hit before extraction or printing a binary path.
echo "$SHA512  $SOURCE" | sha512sum -c --quiet - >&2
if [ -n "$DOWNLOAD" ]; then
  mv -f -- "$DOWNLOAD" "$ARCHIVE"
  DOWNLOAD=
fi

STAGE=$(mktemp -d "$DIR/.godot-extract.XXXXXX")
unzip -q -o "$ARCHIVE" "${BIN##*/}" -d "$STAGE"
chmod +x "$STAGE/${BIN##*/}"
mv -f -- "$STAGE/${BIN##*/}" "$BIN"
touch "$DIR/_sc_"
echo "$BIN"
