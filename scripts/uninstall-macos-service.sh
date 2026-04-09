#!/bin/bash
set -euo pipefail

PLIST_TARGET="$HOME/Library/LaunchAgents/com.marko.clippa.plist"
GUI_DOMAIN="gui/$(id -u)"

if [ -f "$PLIST_TARGET" ]; then
    launchctl bootout "$GUI_DOMAIN" "$PLIST_TARGET" >/dev/null 2>&1 || true
    rm -f "$PLIST_TARGET"
fi

echo "Clippa service removed."
