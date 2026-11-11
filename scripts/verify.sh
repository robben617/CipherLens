#!/usr/bin/env bash
# CipherLens 本地验证入口：单测 → 构建 → 双向量对账 → 后端探针 → 接口文档。
# 用法：bash scripts/verify.sh [port] [--docker]
#
# 这一步对应大赛的「可复现」：在干净环境里只要 Python + Node，跑完这条命令
# 就能拿出证据，不依赖任何人肉点击。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-8000}"
WITH_DOCKER="${2:-}"
mkdir -p "$ROOT/output"

# 本机若注入了 http_proxy，127.0.0.1 的探测会被代理截走（返回 502）。
export NO_PROXY="127.0.0.1,localhost${NO_PROXY:+,$NO_PROXY}"
export no_proxy="$NO_PROXY"

# Windows 上 `python` 可能是不带依赖的另一个解释器（本机就是），
# 所以按「谁 import 得动 fastapi」来选，环境变量 PYTHON 可强制指定。
pick_python() {
  local candidate
  for candidate in ${PYTHON:-} python py python3; do
    if command -v "$candidate" >/dev/null 2>&1 \
      && "$candidate" -c "import fastapi, uvicorn, httpx" >/dev/null 2>&1; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}
PY="$(pick_python)" || {
  echo "找不到装了 fastapi / uvicorn / httpx 的解释器，试过：\$PYTHON python py python3" >&2
  echo "先跑：pip install -r backend/requirements.txt" >&2
  exit 1
}
echo "== python: $PY ($("$PY" --version 2>&1)) =="

echo "== frontend: npm test =="
(cd "$ROOT/frontend" && npm test)

echo "== frontend: npm run build =="
(cd "$ROOT/frontend" && npm run build)

echo "== backend: three-vector trace compare =="
(cd "$ROOT" && "$PY" backend/tools/compare_trace.py)

echo "== backend: start uvicorn on 127.0.0.1:$PORT =="
"$PY" -m uvicorn --app-dir "$ROOT/backend" main:app \
  --host 127.0.0.1 --port "$PORT" >"$ROOT/output/verify-backend.log" 2>&1 &
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

ready=0
for _ in $(seq 1 40); do
  if "$PY" - "$PORT" <<'PY' >/dev/null 2>&1
import sys, urllib.request
urllib.request.urlopen(f"http://127.0.0.1:{sys.argv[1]}/api/health", timeout=1)
PY
  then
    ready=1
    break
  fi
  sleep 1
done
[ "$ready" = "1" ] || { echo "后端 40 秒内没起来，见 output/verify-backend.log" >&2; exit 1; }

# 接口文档是 F13 的验收项：路径挂在 /api 下，且 spec 必须是合法 JSON、
# 五组业务路由齐全。这里不看 /docs 的 HTML，只看机器可读的那一份。
echo "== backend: openapi (docs at /api/docs) =="
"$PY" - "$PORT" <<'PY'
import json, sys, urllib.request

port = sys.argv[1]
for path in ("/api/openapi.json", "/api/docs"):
    resp = urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=5)
    if resp.status != 200:
        sys.exit(f"{path} -> {resp.status}")

spec = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/api/openapi.json", timeout=5))
paths = sorted(spec.get("paths", {}))
required = [
    "/api/aes/trace",
    "/api/tutor/ask",
    "/api/quiz/items",
    "/api/quiz/submit",
    "/api/records/summary",
    "/api/events",
    "/api/health",
]
missing = [item for item in required if item not in paths]
if missing:
    sys.exit(f"openapi 缺路由：{missing}")
print(f"openapi ok: {len(paths)} paths, {len(spec.get('components', {}).get('schemas', {}))} schemas")
PY

echo "== backend: quiz probe =="
"$PY" "$ROOT/backend/tools/quiz_probe.py" "$PORT"

echo "== backend: records probe (legacy scope) =="
"$PY" "$ROOT/backend/tools/records_probe.py" --summary

echo "== backend: tutor probe =="
"$PY" "$ROOT/backend/tools/tutor_probe.py" "$PORT"

if [ "$WITH_DOCKER" = "--docker" ]; then
  echo "== docker: compose up =="
  docker compose -f "$ROOT/docker-compose.yml" up -d --build
  for _ in $(seq 1 30); do
    if "$PY" - <<'PY' >/dev/null 2>&1
import urllib.request
urllib.request.urlopen("http://127.0.0.1:8080/api/health", timeout=2)
PY
    then
      break
    fi
    sleep 2
  done
  # 生产链路上真正要验的三条：首页、健康检查、接口文档
  "$PY" - <<'PY'
import json, sys, urllib.request

checks = {
    "/": "首页",
    "/api/health": "健康检查",
    "/api/openapi.json": "接口文档",
}
for path, label in checks.items():
    resp = urllib.request.urlopen(f"http://127.0.0.1:8080{path}", timeout=10)
    body = resp.read()
    if resp.status != 200 or not body:
        sys.exit(f"{label} {path} -> {resp.status}")
    if path.endswith("openapi.json"):
        paths = json.loads(body).get("paths", {})
        if "/api/aes/trace" not in paths:
            sys.exit("容器里的 openapi 缺 /api/aes/trace —— nginx 是否只代理了 /api/？")
        print(f"docker ok: {label} 200, {len(paths)} paths")
    else:
        print(f"docker ok: {label} 200, {len(body)} bytes")
PY
  echo "docker: 前端与 API 均可从 127.0.0.1:8080 访问"
fi

echo "verify: OK"
