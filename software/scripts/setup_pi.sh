#!/usr/bin/env bash
# One-command setup for Raspberry Pi 4 Model B (Raspberry Pi OS 64-bit / Debian / Ubuntu)
# Installs precompiled OpenCV + NumPy + PySerial via apt (fast!) and FastAPI/Uvicorn in .venv.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOFTWARE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "==> Installing system packages (OpenCV, NumPy, PySerial, venv)..."
sudo apt-get update
sudo apt-get install -y \
  python3-venv \
  python3-pip \
  python3-opencv \
  python3-numpy \
  python3-serial \
  v4l-utils

echo "==> Creating Python virtual environment (reusing fast system OpenCV)..."
cd "$SOFTWARE_DIR"
python3 -m venv --system-site-packages .venv
source .venv/bin/activate

echo "==> Installing web server packages (FastAPI + Uvicorn)..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "==> Checking detected USB webcams:"
v4l2-ctl --list-devices || true

echo ""
echo "Setup complete! Start the Web UI + Live Vision Studio with:"
echo "  bash software/scripts/run_web.sh"
