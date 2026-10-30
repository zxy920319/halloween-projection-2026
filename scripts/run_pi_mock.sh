#!/usr/bin/env bash
set -euo pipefail
python3 -m pi_agent.main --server "${SERVER_URL:-ws://127.0.0.1:8765/frames}" --backend mock
