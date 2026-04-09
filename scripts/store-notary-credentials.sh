#!/bin/bash
set -euo pipefail

if [ -z "${APPLE_NOTARY_PROFILE:-}" ] || [ -z "${APPLE_ID:-}" ] || [ -z "${APPLE_TEAM_ID:-}" ] || [ -z "${APPLE_APP_PASSWORD:-}" ]; then
    echo "Defina APPLE_NOTARY_PROFILE, APPLE_ID, APPLE_TEAM_ID e APPLE_APP_PASSWORD antes de rodar."
    exit 1
fi

xcrun notarytool store-credentials "$APPLE_NOTARY_PROFILE" \
    --apple-id "$APPLE_ID" \
    --team-id "$APPLE_TEAM_ID" \
    --password "$APPLE_APP_PASSWORD"
