#!/usr/bin/env bash
# CipherLens 本地验证入口：单测 → 构建 → 三向量对账 → 后端探针。
# 用法：bash scripts/verify.sh [port] [--docker]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-8000}"
WITH_DOCKER="${2:-}"

echo "== frontend: npm test =="
(cd "$ROOT/frontend" && npm test)

echo "== frontend: npm run build =="
(cd "$ROOT/frontend" && npm run build)

echo "== backend: three-vector trace compare =="
(cd "$ROOT" && python backend/tools/compare_trace.py)

echo "== backend: start uvicorn on 127.0.0.1:$PORT =="
(cd "$ROOT/backend" && python -m uvicorn main:app --host 127.0.0.1 --port "$PORT" >"$ROOT/output/verify-backend.log" 2>&1) &
BACKEND_PID=$!

cleanup() {
  if kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
  if [ "$WITH_DOCKER" = "--docker" ]; then
    docker compose -f "$ROOT/docker-compose.yml" down >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

for _ in $(seq 1 30); do
  if python - "$PORT" <<'PY' >/dev/null 2>&1
import sys, urllib.request
urllib.request.urlopen(f"http://127.0.0.1:{sys.argv[1]}/openapi.json", timeout=1)
PY
  then
    break
  fi
  sleep 1
done

echo "== backend: quiz probe =="
python "$ROOT/backend/tools/quiz_probe.py" "$PORT"

echo "== backend: records probe (legacy scope) =="
python "$ROOT/backend/tools/records_probe.py" --summary

echo "== backend: tutor probe =="
python "$ROOT/backend/tools/tutor_probe.py" "$PORT"

if [ "$WITH_DOCKER" = "--docker" ]; then
  echo "== docker: compose up =="
  docker compose -f "$ROOT/docker-compose.yml" up -d --build
  sleep 8
  curl -fsS "http://127.0.0.1:8080/api/records/summary" >/dev/null
  echo "docker frontend/API reachable on 127.0.0.1:8080"
fi

echo "verify: OK"