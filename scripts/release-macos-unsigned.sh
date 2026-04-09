#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

APP_PATH="$(pwd)/dist/Clippa.app"
ZIP_PATH="$(pwd)/dist/Clippa-mac-unsigned.zip"

./scripts/build-macos-app.sh

# Ad-hoc signing keeps the bundle internally consistent on macOS,
# but does not replace Developer ID signing/notarization.
codesign --force --deep --sign - "$APP_PATH"
codesign --verify --deep --strict --verbose=2 "$APP_PATH"

rm -f "$ZIP_PATH"
ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ZIP_PATH"

echo ""
echo "Release sem Apple Developer pronto:"
echo "  app: $APP_PATH"
echo "  zip: $ZIP_PATH"
