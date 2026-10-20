#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN=python
fi

if [ ! -x .venv/bin/python ]; then
  "$PYTHON_BIN" -m venv .venv
fi

.venv/bin/python -m pip install --disable-pip-version-check --upgrade -r requirements.txt
printf '\nMeaw Loader is starting. Open http://127.0.0.1:8080 in your browser.\n'
printf 'Keep this terminal open while using the downloader. Press Ctrl+C to stop it.\n\n'
exec .venv/bin/python server.py
