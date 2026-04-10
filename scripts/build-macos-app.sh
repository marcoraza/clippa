#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -x "venv/bin/python" ]; then
    echo "Virtualenv nao encontrado em $(pwd)/venv"
    echo "Rode ./reclip.sh uma vez para criar o ambiente."
    exit 1
fi

FFMPEG_BIN="$(command -v ffmpeg || true)"
FFPROBE_BIN="$(command -v ffprobe || true)"

if [ -z "$FFMPEG_BIN" ] || [ -z "$FFPROBE_BIN" ]; then
    echo "ffmpeg e ffprobe precisam estar instalados para gerar o app completo."
    echo "No macOS com Homebrew: brew install ffmpeg"
    exit 1
fi

if ! venv/bin/python -c "import webview; import PyInstaller" 2>/dev/null; then
    echo "Instalando dependencias desktop..."
    venv/bin/python -m pip install -r requirements-desktop.txt
fi

venv/bin/python -m PyInstaller \
    --noconfirm \
    --clean \
    --windowed \
    --name Clippa \
    --icon assets/Clippa.icns \
    --osx-bundle-identifier com.marko.clippa.desktop \
    --add-data "templates:templates" \
    --add-data "static:static" \
    --add-data "assets:assets" \
    --add-binary "${FFMPEG_BIN}:bin" \
    --add-binary "${FFPROBE_BIN}:bin" \
    --hidden-import webview.platforms.cocoa \
    desktop.py

echo ""
echo "Build finalizado:"
echo "  $(pwd)/dist/Clippa.app"
