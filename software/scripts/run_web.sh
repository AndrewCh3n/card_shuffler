#!/usr/bin/env bash
# Launch the Card Shuffler Web UI & Live Vision Studio on port 8000.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOFTWARE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SOFTWARE_DIR"

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

IP_ADDR="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
echo "============================================================"
echo " Card Shuffler Web UI & Live Vision Studio"
echo "   Local:   http://localhost:8000"
if [ -n "${IP_ADDR:-}" ]; then
  echo "   Phone:   http://${IP_ADDR}:8000"
fi
echo "   Tab 3 -> 'Vision / Camera' to calibrate & identify cards!"
echo "============================================================"

exec uvicorn shuffler.web_app:app --host 0.0.0.0 --port 8000
