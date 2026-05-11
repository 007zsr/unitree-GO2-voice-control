#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

.venv/bin/python project_cli.py gui \
  --robot-mode go2 \
  --enable-real-robot \
  --interface enx4cea41674695 \
  --real-demo \
  --allowed-real-actions stand_up,sit_down,stop,move_forward,move_backward,turn_left,turn_right
