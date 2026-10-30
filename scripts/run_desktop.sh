#!/usr/bin/env bash
set -euo pipefail
python3 -m desktop.main --host "${INGEST_HOST:-127.0.0.1}" --port "${INGEST_PORT:-8765}" "$@"
