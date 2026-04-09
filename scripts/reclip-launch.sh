#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"
export HOST="${HOST:-0.0.0.0}"
export PORT="${PORT:-8899}"

if [ ! -x "venv/bin/python" ]; then
    echo "Python virtualenv not found at $(pwd)/venv"
    echo "Run ./reclip.sh once in a terminal to install dependencies."
    exit 1
fi

exec ./venv/bin/python app.py
