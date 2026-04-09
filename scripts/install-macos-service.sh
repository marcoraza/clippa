#!/bin/bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_SOURCE="$REPO_DIR/deploy/macos/com.marko.clippa.plist"
PLIST_TARGET="$HOME/Library/LaunchAgents/com.marko.clippa.plist"
LABEL="com.marko.clippa"
GUI_DOMAIN="gui/$(id -u)"
LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"

mkdir -p "$HOME/Library/LaunchAgents" "$REPO_DIR/logs"
chmod +x "$REPO_DIR/scripts/reclip-launch.sh"
cp "$PLIST_SOURCE" "$PLIST_TARGET"

launchctl bootout "$GUI_DOMAIN" "$PLIST_TARGET" >/dev/null 2>&1 || true
launchctl bootstrap "$GUI_DOMAIN" "$PLIST_TARGET"

echo "Clippa service installed."
echo "Local: http://127.0.0.1:8899"
if [ -n "$LAN_IP" ]; then
    echo "LAN:   http://$LAN_IP:8899"
fi
echo "Label: $LABEL"
