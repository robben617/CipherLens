# CipherLens 部署文档 v1.0

> 面向：换一台机器、交给评审环境、或答辩现场临时起服务。
> 对应改造项 **F13**（工程与文档收尾），验收口径见 `CipherLens-分功能改造设计方案-v1.0.md` §F13。

---

## 1. 拓扑

```
浏览器 ──▶ frontend 容器（nginx :80，宿主 :8080）
              ├─ /            静态 SPA（try_files 回退 index.html）
              └─ /api/*       proxy_pass → backend:8000
                                 └─ FastAPI + SQLite（卷 cipherlens-data:/app/data）
```

只有 **8080** 对外；后端 8000 只在 compose 内部网络可见（`expose`，不是 `ports`）。
所以宿主机访问 `/api/docs` 必须走 8080，直连 8000 拿不到。

| 项 | 值 | 位置 |
|---|---|---|
| 宿主端口 | `8080`（改这里：`docker-compose.yml` 的 `ports`） | `docker-compose.yml` |
| 容器端口 | frontend `80` / backend `8000` | 同上 |
| 数据卷 | `cipherlens-data` → `/app/data` | 同上 `volumes` |
| 数据库文件 | `/app/data/cipherlens.db` | `backend/db.py` 的 `DB_PATH` |
| 镜像 | 无 registry，本地 build | `docker/frontend.Dockerfile`、`backend/Dockerfile` |

---

## 2. 首次部署

```bash
git clone <repo> && cd CipherLens
cp .env.example .env          # 不填 LLM_* 也能跑，AI 区自动降级本地讲解
docker compose up -d --build
docker compose ps             # 两个服务都要 healthy
```

验收四条（缺一条就是没部署好）：

```bash
curl -fsS http://localhost:8080/ | head -1                      # 200，HTML
curl -fsS http://localhost:8080/api/health                      # {"status":"ok",...}
curl -fsS http://localhost:8080/api/openapi.json | head -c 80   # {"openapi":"3.1.0"...
curl -fsS http://localhost:8080/api/quiz/items | head -c 80     # {"count":8,...
```

浏览器打开 `http://localhost:8080/api/docs` 应看到 Swagger，分组为
**AES 轨迹 / AI 辅导 / 练习与判分 / 行为事件 / 学习记录 / 术语表 / 健康检查**。

> F13 之前这里 404：FastAPI 默认把文档挂在 `/docs`、`/openapi.json`，而 nginx 只反代 `/api/`。
> 现在 `main.py` 显式指定 `openapi_url="/api/openapi.json"`，并手写 `/api/docs` 路由。

### 2.1 文档页不依赖 CDN（离线可用）

Swagger UI 的 css/js/favicon 默认从 `cdn.jsdelivr.net` 拉。实测在受限网络里 CSS 会被
`ERR_CONNECTION_RESET`，页面退化成一页裸 HTML——接口列表还在，样式全丢，评委看到的就是这个。
所以三个文件随镜像走：

| 文件 | 路径 | 体积 |
|---|---|---|
| `swagger-ui-bundle.js` | `backend/static/swagger/` | 1.7 MB |
| `swagger-ui.css` | 同上 | 184 KB |
| `favicon-32x32.png` | 同上 | 628 B |

由 `app.mount("/api/static", StaticFiles(...))` 提供，`/api/docs` 用
`get_swagger_ui_html(swagger_js_url=...)` 指过去。

**坑**：`swagger_js_url` / `swagger_css_url` 是 `get_swagger_ui_html()` 的参数，
不是 `FastAPI()` 的构造参数。写进构造函数不会报错——它被 `**extra` 吞掉，页面仍指 CDN。
`docs_url` 必须设成 `None`，否则内置路由会先注册，手写的 `/api/docs` 不生效。

升级 Swagger UI 时（`npm pack swagger-ui-dist@<ver>` 后替换两个文件即可），无需改代码。

---

## 3. 健康检查怎么设计的

| 位置 | 探针 | 间隔 / 超时 / 重试 | 为什么探这个 |
|---|---|---|---|
| `backend/Dockerfile` `HEALTHCHECK` | `GET /api/health` | 10s / 3s / 5 | 只读状态，不碰数据库、不调模型，空库也立刻 200 |
| `docker-compose.yml` backend | 同上 | 10s / 5s / 6 | compose 会覆盖 Dockerfile 里的定义 |
| `docker-compose.yml` frontend | `wget -qO- http://127.0.0.1/` | 10s / 5s / 6 | 验 nginx 起来且 `index.html` 拿得到 |

`frontend` 用 `depends_on: backend: condition: service_healthy`，所以**前端不会先于后端对外服务**，
首屏不会出现「接口一片红」。启动顺序：backend 健康 → frontend 起来。

不要去探 `/api/records/summary` 当健康检查：它要读库，库锁住时会误判后端已死。

---

## 4. 环境变量

`.env` 放在**仓库根**（compose 自动读），backend 容器里由 compose 注入。本机裸跑时后端也会读
`backend/.env`（`backend/env_file.py`），且**不覆盖已存在的环境变量**——CI 里用 `-e` 传的值优先。

| 变量 | 默认 | 说明 |
|---|---|---|
| `LLM_BASE_URL` | 空 | OpenAI 兼容根路径，末尾不带 `/chat/completions`，例 `https://api.deepseek.com/v1` |
| `LLM_API_KEY` | 空 | 只从环境读；不进代码、不进日志、不落库、不回显 |
| `LLM_MODEL` | 空 | 例 `deepseek-chat` |
| `LLM_TIMEOUT_S` | `20` | 单次超时；失败重试一次按 ×1.5 |
| `LLM_MAX_TOKENS` | `400` | 教学场景一段话够用 |
| `VITE_BASE` | `/` | 前端部署在子路径时改（例 `/cipherlens/`） |
| `VITE_BUILD_TARGET` | 空 | 需要兼容旧浏览器时填（例 `es2019`） |
| `CIPHERLENS_DB_PATH` | 空 | **预留**：`db.py` 目前固定 `backend/data/cipherlens.db`，改这里暂不生效 |

三个 `LLM_*` 任意一个为空 → `llm.enabled=false` → E 区状态点显示「本地」，走本地模板讲解。
这是设计内行为，不是故障。

> `VITE_BASE` 是**构建期**变量：改了必须 `docker compose build --no-cache frontend`，
> 只 `restart` 不生效。

---

## 5. nginx 的两个关键点（改错就出 SSE 故障）

`docker/nginx.conf` 的 `/api/` location：

```nginx
proxy_buffering off;   # 关掉响应缓冲
proxy_cache off;
proxy_read_timeout 60s;
gzip off;              # 本 location 禁用 gzip
proxy_http_version 1.1;
proxy_set_header Connection "";
```

- **`proxy_buffering off` 是 SSE 的生死线。** 开着的话 nginx 会先攒一块（默认 4k/8k）再吐，
  AI 讲解就变成「转半天 → 一次性蹦出全文」，F09 做的逐字流式全白费。
- **`gzip off` 同理。** gzip 需要攒够数据才能压缩，等于又加一层缓冲。注意 `gzip on` 是写在
  `server` 层的，必须在 location 里显式关掉才能覆盖。
- `proxy_read_timeout 60s` > `LLM_TIMEOUT_S × 1.5`（最长约 30s），不会在后端还在等模型时被 nginx 掐断。
- `proxy_http_version 1.1` + 空 `Connection`：SSE 长连接默认走 1.0 会被关掉。

自建反代（学校服务器 / 云主机前置 nginx）时，这四行必须照抄，否则现象和代码 bug 长得一模一样。

另外给文档资源单独开一个 location（`/api/` 那个把 gzip 关了，1.7 MB 的 js 不压缩很难受）：

```nginx
location /api/static/ {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_read_timeout 30s;
    expires 7d;
}
```

前缀匹配里 `/api/static/` 比 `/api/` 长，会优先命中，因此继承 server 层的 `gzip on`。

---

## 6. 数据：备份、迁移、重置

**备份（在线可做）**

```bash
docker run --rm -v cipherlens-data:/data -v "$PWD":/backup alpine \
  tar czf /backup/cipherlens-data-$(date +%Y%m%d).tar.gz -C /data .
```

**迁移**：后端启动时读 `PRAGMA user_version`，低于目标版本就在**事务内**逐步迁移
（`BEGIN IMMEDIATE` → 建表/改表 → `PRAGMA user_version = N`），失败整体回滚并在日志里报
`step=xxx`。当前目标版本 **3**。迁移前自动备份成 `cipherlens.db.bak-v0-<时间戳>`，只保留最近 2 份
（`db.py` 的 `BACKUP_KEEP`）。

**重置**（答辩前清成干净状态，推荐）

```bash
docker compose down -v        # 连卷一起删，下次起是全新库
docker compose up -d
```

启动时 `seed_items()` 会用 `quiz_bank.py` 重灌 8 道题，答案由引擎现算，不需要手工造数据。

**只清学习记录、不删题目**：前端记录页的「清空记录」，或
`curl -X DELETE -H "X-Client-Id: c_<32位十六进制>" http://localhost:8080/api/records`。

---

## 7. 离线 / 内网部署

评审机器不能联网时，走「有网机器构建 → 导出镜像 → 内网导入」：

```bash
# 有网机器
docker compose build
docker save -o cipherlens-images.tar $(docker compose images -q | sort -u)
docker compose images                # 记下两个镜像名

# 内网机器（把 tar 和仓库一起带过去）
docker load -i cipherlens-images.tar
docker compose up -d --no-build
```

注意三点：

1. `--no-build` 必须有，否则 compose 会尝试联网拉基础镜像。
2. 内网起容器后不会自动有数据，`seed_items()` 在启动时灌题库，8 道题开箱可用。
3. LLM 若也在内网，把 `LLM_BASE_URL` 指向内网 OpenAI 兼容服务即可；不通就降级本地讲解，不影响验收。

无法用 Docker 时的裸跑部署：`pip install -r backend/requirements.txt` →
`python -m uvicorn --app-dir backend main:app --host 0.0.0.0 --port 8000`，
再把 `frontend/dist` 交给任意静态服务器，反代 `/api/` 到 8000（反代规则见 §5）。

---

## 8. 故障排查

| 现象 | 先看哪里 | 处理 |
|---|---|---|
| `docker compose ps` 里 backend 一直 `starting`/`unhealthy` | `docker compose logs backend` | 多半是 `.env` 里 key 填了占位符导致启动异常；先清空 `LLM_*` 验证基线 |
| 8080 打不开 | `docker compose ps` 端口映射、宿主 8080 是否被占 | 改 `ports: "8081:80"`，或停掉占用进程（Windows：`netstat -ano` 里找 `:8080` 的 PID） |
| 页面 404 / 白屏，但 `/api/health` 正常 | 浏览器控制台、`VITE_BASE` | 子路径部署时 `VITE_BASE` 没设或没重新构建 |
| `/api/docs` 404 | 镜像是否最新 | `docker compose up -d --build`；确认 nginx 有 `location /api/` 反代 |
| AI 内容一次性出现 | `docker/nginx.conf` | 见 §5，`proxy_buffering off` + `gzip off` |
| AI 一直转圈最后报错 | `/api/health` 的 `llm.enabled` | `true` 则是模型服务不通（网络/key/模型名）；`false` 是没配，本就会降级 |
| 记录页一直空 | 浏览器 `localStorage` 是否有 `cl_client_id` | 隐私模式会拦；或后端 `step_events` 无数据（没播放过） |
| 起服务报 `database is locked` | 是否有第二个进程写了同一个 db | 只跑一个后端实例；SQLite 单写，不要多副本 |
| 时区导致「今天」统计不对 | 容器默认 UTC | `cipherlens.db` 里时间用 `CURRENT_TIMESTAMP`（UTC），前端按本地时区渲染 |

---

## 9. 安全边界（答辩会被问，先写清）

- **没有账号体系。** 数据按浏览器生成的匿名 `client_id`（`c_<32 hex>`）隔离；同一台机器换浏览器就是另一个人。
- **接口是公开的。** `/api/health` 只报「有没有配模型」，不回显 `base_url`、`key`、任何一段密钥。
- **答案不下发。** `GET /api/quiz/items` 不含 `answer` / `explanation`，判分只在后端做。
- **题面明文与密钥是教学材料**，不是真实密钥，写在题库里是刻意的；真实 LLM key 只走环境变量。
- **CORS 白名单**只开 `localhost:5173 / 127.0.0.1:5173 / :4173`，生产环境走同源反代，不需要放宽。
- **对外暴露前必须加**：HTTPS、访问认证、`/api/events` 与 `/api/records` 的速率限制。当前形态是**课程演示级**，不是公网服务。

---

## 10. 验收清单（F13）

| # | 项 | 命令 / 动作 | 期望 |
|---|---|---|---|
| 1 | Swagger 可打开 | 浏览器 `:8080/api/docs` | 200，7 个分组齐全 |
| 2 | schema 合法 | `curl -fsS :8080/api/openapi.json` | 200，JSON 合法，9 条路径 |
| 3 | 三容器链路 | `docker compose ps` | backend healthy，frontend healthy |
| 4 | 一键回归 | `bash scripts/verify.sh 8000 --docker` | 结尾打印 `verify: OK` |
| 5 | 冷启动可复现 | 新机器按 §2 四步 | 10 分钟内可访问 |
| 6 | 离线包可用 | §7 的 `save/load` 流程 | `--no-build` 起得来 |
| 7 | 断网可用 | 断外网后开 `:8080/api/docs` | 样式完整，控制台无 CDN 请求 |
