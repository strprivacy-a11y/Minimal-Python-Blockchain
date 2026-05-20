#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$ROOT_DIR/.run"
PORTS=(8001 8002 8003)

mkdir -p "$PID_DIR"

for port in "${PORTS[@]}"; do
  pid_file="$PID_DIR/node-$port.pid"
  log_file="$PID_DIR/node-$port.log"

  if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
    echo "node on port $port is already running"
    continue
  fi

  nohup python3 -m uvicorn app.main:app --host 127.0.0.1 --port "$port" \
    >"$log_file" 2>&1 &
  echo $! >"$pid_file"
  echo "started node on port $port with pid $(cat "$pid_file")"
done

