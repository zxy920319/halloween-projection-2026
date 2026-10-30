#!/usr/bin/env bash
# Install/refresh the Pi camera sender as a systemd service (auto-start on boot, auto-restart on crash).
# Usage: sudo bash deploy/pi/install_service.sh --server ws://DESKTOP_IP:8765/frames [--user pi] [--dir /path/to/repo]
set -euo pipefail

SERVER=""
SVC_USER="${SUDO_USER:-}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --server) SERVER="$2"; shift 2 ;;
    --user) SVC_USER="$2"; shift 2 ;;
    --dir) REPO_DIR="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

[[ $EUID -eq 0 ]] || { echo "run with sudo" >&2; exit 1; }
[[ -n "$SERVER" ]] || { echo "--server ws://DESKTOP_IP:8765/frames is required" >&2; exit 2; }
[[ -n "$SVC_USER" ]] && id "$SVC_USER" >/dev/null 2>&1 || { echo "user '$SVC_USER' does not exist; pass --user" >&2; exit 2; }
PY=""
for cand in "$REPO_DIR/.venv/bin/python" "$REPO_DIR/../.venv/bin/python"; do
  if [[ -x "$cand" ]] && "$cand" -c "import websockets" >/dev/null 2>&1; then PY="$(cd "$(dirname "$cand")" && pwd)/python"; break; fi
done
[[ -n "$PY" ]] || { echo "no venv with dependencies found (checked $REPO_DIR/.venv and $REPO_DIR/../.venv). Run: . <venv>/bin/activate && pip install -e $REPO_DIR" >&2; exit 2; }

usermod -aG video "$SVC_USER"

cat > /etc/systemd/system/halloween-pi.service <<EOF
[Unit]
Description=Halloween Projection Pi camera sender
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SVC_USER
Group=video
WorkingDirectory=$REPO_DIR
Environment=PYTHONUNBUFFERED=1
ExecStart=$PY -m pi_agent.main --server $SERVER --backend v4l2 --device auto --width 640 --height 480 --fps 30
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now halloween-pi.service
echo "Installed. Check: systemctl status halloween-pi   Logs: journalctl -u halloween-pi -f"
