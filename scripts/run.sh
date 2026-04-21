#!/usr/bin/env bash
# broll-dispatch skill entry point
# Usage: bash run.sh "<用户消息>"

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

MESSAGE="${1:-}"
exec python3 "$SCRIPT_DIR/main.py" "$MESSAGE"
