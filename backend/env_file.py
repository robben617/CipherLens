"""极简 `.env` 读取 —— 不引第三方库，只做「一行一个 KEY=VALUE」。

三条自律：
1. **不覆盖**已存在的环境变量。容器/CI 里注入的真实值，不该被仓库旁边
   一个 `.env` 悄悄改掉。
2. 不做变量展开、不解析引号里的转义 —— 解析器越聪明，出错时越难猜。
3. 只报告读到了几个键，**永不打印值**。key 一旦进日志就等于泄露。
"""

import os
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent / ".env"


def load_env_file(path=None) -> int:
    """读 `backend/.env`（可选）。返回注入的键数，0 表示没有或没读懂。"""
    target = Path(path) if path else ENV_PATH
    if not target.is_file():
        return 0

    loaded = 0
    for raw in target.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        name = name.strip()
        value = value.strip().strip('"').strip("'")
        if not name or name in os.environ:
            continue
        os.environ[name] = value
        loaded += 1
    return loaded
