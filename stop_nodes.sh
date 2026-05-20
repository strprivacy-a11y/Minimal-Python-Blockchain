#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$ROOT_DIR/.run"
PORTS=(8001 8002 8003)

for port in "${PORTS[@]}"; do
  pid_file="$PID_DIR/node-$port.pid"

  if [[ ! -f "$pid_file" ]]; then
    echo "node on port $port is not tracked"
    continue
  fi

  pid="$(cat "$pid_file")"
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid"
    echo "stopped node on port $port"
  else
    echo "node on port $port is not running"
  fi

  rm -f "$pid_file"
done
