#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install -U pip
.venv/bin/python -m pip install -r requirements-ubuntu.txt

echo "Project .venv is ready."
echo "Run: bash run_gui_ubuntu.sh"
