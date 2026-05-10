#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
LOG_DIR="$RUN_DIR/logs"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

mkdir -p "$LOG_DIR"

require_command() {
  local command_name="$1"
  local install_hint="$2"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Missing required command: $command_name"
    echo "$install_hint"
    exit 1
  fi
}

ensure_env_file() {
  if [[ -f "$ROOT_DIR/.env" ]]; then
    return
  fi

  echo "No .env file found."
  echo "Create one from .env.example and fill in LLM_* and EMBEDDING_* values before running analysis:"
  echo "  cp .env.example .env"
  echo
}

find_uv_python() {
  find "$ROOT_DIR/.uv-python" -type f \( -name "python3.11" -o -name "python.exe" \) 2>/dev/null | head -n 1
}

setup_backend() {
  require_command "uv" "Install uv first: https://docs.astral.sh/uv/getting-started/installation/"

  if [[ ! -d "$ROOT_DIR/.venv" ]]; then
    echo "Creating uv-managed Python environment..."
    (
      cd "$ROOT_DIR"
      uv --cache-dir .uv-cache python install --install-dir .uv-python 3.11
      local_python="$(find_uv_python)"
      if [[ -z "$local_python" ]]; then
        echo "Could not find uv-managed Python 3.11 under .uv-python."
        exit 1
      fi
      uv --cache-dir .uv-cache venv --python "$local_python" .venv
    )
  fi

  echo "Syncing backend dependencies..."
  (
    cd "$ROOT_DIR"
    uv --cache-dir .uv-cache sync
  )
}

setup_frontend() {
  require_command "npm" "Install Node.js 18+ first: https://nodejs.org/"

  if [[ ! -d "$ROOT_DIR/frontend/node_modules" ]]; then
    echo "Installing frontend dependencies..."
    (
      cd "$ROOT_DIR/frontend"
      npm install
    )
  fi
}

setup_all() {
  ensure_env_file
  setup_backend
  setup_frontend
  echo "Setup complete."
}

is_running() {
  local pid_file="$1"
  [[ -f "$pid_file" ]] || return 1
  local pid
  pid="$(cat "$pid_file")"
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

stop_pid() {
  local name="$1"
  local pid_file="$2"
  if ! is_running "$pid_file"; then
    rm -f "$pid_file"
    echo "$name is not running."
    return
  fi

  local pid
  pid="$(cat "$pid_file")"
  echo "Stopping $name (pid $pid)..."
  kill "$pid" 2>/dev/null || true

  for _ in {1..20}; do
    if ! kill -0 "$pid" 2>/dev/null; then
      rm -f "$pid_file"
      echo "$name stopped."
      return
    fi
    sleep 0.2
  done

  echo "$name did not stop gracefully; forcing shutdown."
  kill -9 "$pid" 2>/dev/null || true
  rm -f "$pid_file"
}

start_backend() {
  if is_running "$BACKEND_PID_FILE"; then
    echo "Backend is already running (pid $(cat "$BACKEND_PID_FILE"))."
    return
  fi

  echo "Starting backend on http://127.0.0.1:$BACKEND_PORT ..."
  (
    cd "$ROOT_DIR"
    uv --cache-dir .uv-cache run uvicorn app.main:app \
      --app-dir backend \
      --host 127.0.0.1 \
      --port "$BACKEND_PORT"
  ) >"$LOG_DIR/backend.log" 2>&1 &
  echo $! >"$BACKEND_PID_FILE"
}

start_frontend() {
  if is_running "$FRONTEND_PID_FILE"; then
    echo "Frontend is already running (pid $(cat "$FRONTEND_PID_FILE"))."
    return
  fi

  echo "Starting frontend on http://127.0.0.1:$FRONTEND_PORT ..."
  (
    cd "$ROOT_DIR/frontend"
    npm run dev -- --host 127.0.0.1 --port "$FRONTEND_PORT"
  ) >"$LOG_DIR/frontend.log" 2>&1 &
  echo $! >"$FRONTEND_PID_FILE"
}

start_all() {
  setup_all
  start_backend
  start_frontend
  echo
  echo "App is starting."
  echo "Frontend: http://127.0.0.1:$FRONTEND_PORT/"
  echo "Backend:  http://127.0.0.1:$BACKEND_PORT/"
  echo "Logs:     $LOG_DIR"
}

stop_all() {
  stop_pid "frontend" "$FRONTEND_PID_FILE"
  stop_pid "backend" "$BACKEND_PID_FILE"
}

status_all() {
  if is_running "$BACKEND_PID_FILE"; then
    echo "Backend:  running (pid $(cat "$BACKEND_PID_FILE"))"
  else
    echo "Backend:  stopped"
  fi

  if is_running "$FRONTEND_PID_FILE"; then
    echo "Frontend: running (pid $(cat "$FRONTEND_PID_FILE"))"
  else
    echo "Frontend: stopped"
  fi

  echo "Logs:     $LOG_DIR"
}

case "${1:-start}" in
  setup)
    setup_all
    ;;
  start)
    start_all
    ;;
  stop)
    stop_all
    ;;
  restart)
    stop_all
    start_all
    ;;
  status)
    status_all
    ;;
  logs)
    echo "Backend log:  $LOG_DIR/backend.log"
    echo "Frontend log: $LOG_DIR/frontend.log"
    ;;
  *)
    echo "Usage: $0 {setup|start|stop|restart|status|logs}"
    exit 2
    ;;
esac
