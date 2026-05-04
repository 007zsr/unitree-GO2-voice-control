#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
  echo "Project virtual environment .venv was not found."
  echo "Please run setup_ubuntu_venv.sh first."
  exit 1
fi

.venv/bin/python scripts/run/run_gui.py
