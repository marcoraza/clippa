#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

ROOT_DIR="$(pwd)"
APP_PATH="$ROOT_DIR/dist/Clippa.app"
DMG_PATH="$ROOT_DIR/dist/Clippa-mac-unsigned.dmg"
STAGE_DIR="$ROOT_DIR/build/dmg"

if [ ! -d "$APP_PATH" ]; then
    ./scripts/build-macos-app.sh
fi

rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"

# The public DMG stays unsigned, so we strip extra macOS attributes
# and package a clean bundle for drag-and-drop install.
ditto --noextattr --noqtn "$APP_PATH" "$STAGE_DIR/Clippa.app"
ln -s /Applications "$STAGE_DIR/Applications"

rm -f "$DMG_PATH"
hdiutil create \
    -volname "Clippa" \
    -srcfolder "$STAGE_DIR" \
    -ov \
    -format UDZO \
    "$DMG_PATH"

echo ""
echo "DMG pronto:"
echo "  app: $APP_PATH"
echo "  dmg: $DMG_PATH"
