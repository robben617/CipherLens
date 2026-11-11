import logging
import re

from db import connect

logger = logging.getLogger("cipherlens.events")

# 已知事件类型：用于聚合时不必猜；白名单之外但格式合法的仍然入账并记一条 warning，
# 免得前端加个新类型就要改后端。
KNOWN_TYPES = frozenset(
    {
        "session",
        "step",
        "play",
        "pause",
        "jump",
        "direction",
        "ask",
        "tutor_ask",
        "step_revert",
        "tab",
    }
)
# 只收 [a-z0-9_]：中文、空格、表情这些拼错的东西不该污染 event_type 聚合
TYPE_RE = re.compile(r"^[a-z][a-z0-9_]{0,31}$")

MAX_STEP = 64
MAX_DWELL_MS = 10 * 60 * 1000


def record_events(client_id, items):
    """把一批事件写进 step_events，返回实际写入条数。

    `at` 用客户端时间戳（毫秒），用于算学习时长；`created_at` 由库填，
    两者一起才能在时钟漂移时看出问题。
    """
    rows = []
    skipped = 0
    unknown = set()
    for item in items:
        kind = item.type.strip().lower()
        if not TYPE_RE.match(kind):
            skipped += 1
            continue
        if kind not in KNOWN_TYPES:
            unknown.add(kind)

        step = item.step_index
        if step is not None and not (0 <= step <= MAX_STEP):
            step = None

        dwell = item.dwell_ms or 0
        dwell = max(0, min(int(dwell), MAX_DWELL_MS))

        rows.append((client_id, kind, step, dwell, item.at))

    if unknown:
        logger.warning("events unknown types=%s", sorted(unknown))

    if not rows:
        logger.info("events ignored client=%s skipped=%s", client_id, skipped)
        return 0

    with connect() as connection:
        connection.executemany(
            """
            INSERT INTO step_events (client_id, event_type, step_index, dwell_ms, at)
            VALUES (?, ?, ?, ?, ?)
            """,
            rows,
        )

    logger.info(
        "events stored client=%s count=%s skipped=%s", client_id, len(rows), skipped
    )
    return len(rows)
