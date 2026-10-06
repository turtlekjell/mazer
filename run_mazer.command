#!/bin/bash
set -e
cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo "Python 3 was not found. Install Python 3, then try again."
  read -r -p "Press Return to close..."
  exit 1
fi

exec "$PYTHON" webapp.py
