"""AI 提问审计：每次调用写一条 `tutor_logs`。

单独立一个模块而不是在路由里顺手 INSERT，是为了让这件事**永远不影响回答**：
写失败只记 warn，不冒泡。教学过程留痕是加分项，不该成为新的故障点。
"""

import logging

from db import connect

logger = logging.getLogger("cipherlens.tutor")

QUESTION_LIMIT = 80


def record(
    trace_id,
    step_index,
    question,
    source,
    model,
    latency_ms,
    tokens=0,
    degraded=False,
    fabricated=0,
):
    text = (question or "").strip()
    if len(text) > QUESTION_LIMIT:
        text = text[:QUESTION_LIMIT] + "…"

    try:
        with connect() as connection:
            connection.execute(
                "INSERT INTO tutor_logs "
                "(trace_id, step_index, question, source, model, latency_ms, "
                " tokens, degraded, fabricated) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    trace_id,
                    int(step_index),
                    text,
                    source,
                    model,
                    max(0, int(latency_ms)),
                    max(0, int(tokens)),
                    1 if degraded else 0,
                    max(0, int(fabricated)),
                ),
            )
            connection.commit()
    except Exception:
        logger.warning("tutor log write failed trace_id=%s", trace_id, exc_info=True)
