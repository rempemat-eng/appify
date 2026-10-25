#!/usr/bin/env bash
# The repo vendors LimboAI's editor (debug) libraries for Linux, Windows and macOS and both web builds
# (no threads); the desktop *release* libraries add about 12 MB and are needed only for release
# exports. This fetches the pinned release zip, checks it, and copies just those into
# game/addons/limboai/bin (they are git-ignored).
set -euo pipefail
VERSION=v1.8.1
URL="https://github.com/limbonaut/limboai/releases/download/${VERSION}/limboai%2B${VERSION}.gdextension-4.6.zip"
SHA256=0910411f8dbc0da8920f6c8bbbb6397c347cd9f2f193942468a702dfb11d5f0e
BIN=$(cd "$(dirname "${BASH_SOURCE[0]}")/../addons/limboai/bin" && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
curl -fsSL -o "$TMP/limboai.zip" "$URL"
echo "$SHA256  $TMP/limboai.zip" | sha256sum -c --quiet -
unzip -q "$TMP/limboai.zip" 'addons/limboai/bin/*template_release*' -d "$TMP"
SRC="$TMP/addons/limboai/bin"
cp "$SRC/liblimboai.linux.template_release.x86_64.so" "$SRC/liblimboai.windows.template_release.x86_64.dll" "$BIN/"
cp -r "$SRC/liblimboai.macos.template_release.framework" "$BIN/"
echo "LimboAI $VERSION release libraries in $BIN"
