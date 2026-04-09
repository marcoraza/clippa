#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

APP_PATH="$(pwd)/dist/Clippa.app"
ZIP_PATH="$(pwd)/dist/Clippa-mac.zip"

if [ -z "${APPLE_SIGN_IDENTITY:-}" ]; then
    echo "Defina APPLE_SIGN_IDENTITY com o nome exato do certificado Developer ID Application."
    exit 1
fi

if [ -z "${APPLE_NOTARY_PROFILE:-}" ]; then
    echo "Defina APPLE_NOTARY_PROFILE com o perfil salvo no keychain via notarytool."
    exit 1
fi

./scripts/build-macos-app.sh

codesign --force --deep --options runtime --sign "$APPLE_SIGN_IDENTITY" "$APP_PATH"
codesign --verify --deep --strict --verbose=2 "$APP_PATH"

rm -f "$ZIP_PATH"
ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ZIP_PATH"

xcrun notarytool submit "$ZIP_PATH" --keychain-profile "$APPLE_NOTARY_PROFILE" --wait
xcrun stapler staple "$APP_PATH"
xcrun stapler validate "$APP_PATH"

rm -f "$ZIP_PATH"
ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ZIP_PATH"

echo ""
echo "Release pronto:"
echo "  app: $APP_PATH"
echo "  zip: $ZIP_PATH"
