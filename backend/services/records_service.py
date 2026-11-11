import json
import logging
import re
from datetime import datetime, timezone

from db import connect
from services.glossary import OP_LABEL

logger = logging.getLogger("cipherlens.records")

CLIENT_ID_RE = re.compile(r"^c_[0-9a-f]{32}$")
LEGACY_CLIENT_ID = "legacy-default"

MISCONCEPTIONS = (
    ("key_timing", "轮密钥时机", "轮密钥加的时机与顺序"),
    ("mix_coefficient", "列混合系数", "列混合系数与扩散方向"),
    ("key_schedule", "密钥扩展方向", "轮密钥的来源与扩展方向"),
    ("unattributed", "未归类", "无法从最终密文可靠归因"),
)

DESIGN_TAGS = {
    "key_timing": "轮密钥时机",
    "mix_coefficient": "列混合系数",
    "key_schedule": "密钥扩展方向",
}


def misconception_for(step):
    if step == "add_round_key":
        return "key_timing"
    if step == "mix_columns":
        return "mix_coefficient"
    if step in ("sub_bytes", "shift_rows"):
        return "key_schedule"
    return None


def normalize_client_id(value):
    if value is None or value == "":
        return None
    if not CLIENT_ID_RE.fullmatch(value):
        raise ValueError("invalid_client_id")
    return value


def record_attempt(payload, result, client_id=LEGACY_CLIENT_ID):
    """判分结果落 `attempts`（按 client_id 隔离，题目走 quiz_items.id 外键）。"""
    if result.get("input_mismatch") is not None:
        return

    first = result.get("first_diff")
    is_correct = 1 if first is None else 0

    with connect() as connection:
        item = connection.execute(
            "SELECT id FROM quiz_items WHERE item_code = ?",
            (payload.item_id,),
        ).fetchone()
        if item is None:
            # 题库里没有这道题就不写 —— 落一行 item_id 悬空的记录没有意义
            logger.warning("attempt skipped unknown_item=%s", payload.item_id)
            return

        connection.execute(
            """
            INSERT INTO attempts
                (client_id, item_id, submitted, is_correct,
                 first_diff_round, first_diff_step, first_diff_step_index,
                 first_diff_byte, source_bytes, design_tag, misconception)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                client_id,
                item["id"],
                payload.answer_hex,
                is_correct,
                first["round"] if first else None,
                first["step"] if first else None,
                first["step_index"] if first else None,
                first["byte_index"] if first else None,
                json.dumps(result.get("source_bytes") or []),
                result.get("design_tag"),
                "unattributed" if first else None,
            ),
        )


def _attempt_from_new(row):
    raw = row["source_bytes"]
    try:
        source_bytes = json.loads(raw) if raw else []
    except (TypeError, ValueError):
        source_bytes = []

    return {
        "id": f"a{row['id']}",
        "item_id": row["item_code"] or "unknown",
        "submitted": row["submitted"],
        "is_correct": bool(row["is_correct"]),
        "first_diff_round": row["first_diff_round"],
        "first_diff_step": row["first_diff_step"],
        "first_diff_step_index": row["first_diff_step_index"],
        "first_diff_byte": row["first_diff_byte"],
        "misconception": row["misconception"],
        "design_tag": row["design_tag"],
        "source_bytes": source_bytes,
        "created_at": row["created_at"],
        "table": "attempts",
    }


def _attempt_from_legacy(row):
    return {
        "id": f"p{row['id']}",
        "item_id": row["item_id"],
        "submitted": row["submitted"],
        "is_correct": bool(row["is_correct"]),
        "first_diff_round": row["first_diff_round"],
        "first_diff_step": row["first_diff_step"],
        "first_diff_step_index": row["first_diff_step_index"],
        "first_diff_byte": row["first_diff_byte"],
        "misconception": row["misconception"],
        "design_tag": row["design_tag"] if "design_tag" in row.keys() else None,
        "source_bytes": [],
        "created_at": row["created_at"],
        "table": "practice_attempts",
    }


def _load_attempts(connection, client_id):
    """两个表取并集：`attempts` 是 F12 起的写入路径，`practice_attempts` 是历史记录。

    F12 之前所有记录都在 practice_attempts，直接换表等于让老用户的历史消失，
    所以这里读两处、按时间排序；写入只走 attempts，不会重复计一次。
    """
    new_rows = connection.execute(
        """
        SELECT a.id, q.item_code, a.submitted, a.is_correct,
               a.first_diff_round, a.first_diff_step, a.first_diff_step_index,
               a.first_diff_byte, a.misconception, a.design_tag,
               a.source_bytes, a.created_at
        FROM attempts a
        LEFT JOIN quiz_items q ON q.id = a.item_id
        WHERE a.client_id = ?
        ORDER BY a.id
        """,
        (client_id,),
    ).fetchall()

    legacy_rows = connection.execute(
        "SELECT * FROM practice_attempts WHERE client_id = ? ORDER BY id",
        (client_id,),
    ).fetchall()

    attempts = [_attempt_from_legacy(row) for row in legacy_rows]
    attempts.extend(_attempt_from_new(row) for row in new_rows)
    attempts.sort(key=lambda item: (item["created_at"], item["id"]))
    return attempts


def _study_ms(connection, client_id):
    """学习时长 = 本机事件的首末差；不到两条就返回 None，不假装有数据。"""
    rows = connection.execute(
        "SELECT at, dwell_ms, created_at FROM step_events "
        "WHERE client_id = ? ORDER BY id",
        (client_id,),
    ).fetchall()
    if len(rows) < 2:
        return None

    stamps = [row["at"] for row in rows if row["at"] is not None]
    if len(stamps) >= 2:
        span = max(stamps) - min(stamps)
        return max(0, int(span))

    parsed = []
    for row in rows:
        try:
            parsed.append(
                datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=timezone.utc
                )
            )
        except (TypeError, ValueError):
            continue
    if len(parsed) < 2:
        return None
    return int((max(parsed) - min(parsed)).total_seconds() * 1000)


def summary(client_id=None, scope=None):
    with connect() as connection:
        if client_id:
            attempts = _load_attempts(connection, client_id)
            scope_label = "client"
        elif scope == "legacy":
            rows = connection.execute(
                "SELECT * FROM practice_attempts WHERE client_id = ? ORDER BY id",
                (LEGACY_CLIENT_ID,),
            ).fetchall()
            attempts = [_attempt_from_legacy(row) for row in rows]
            attempts.sort(key=lambda item: (item["created_at"], item["id"]))
            scope_label = "legacy"
        else:
            attempts = []
            scope_label = "none"

        study_ms = _study_ms(connection, client_id) if client_id else None
        event_count = 0
        if client_id:
            event_count = connection.execute(
                "SELECT COUNT(*) FROM step_events WHERE client_id = ?",
                (client_id,),
            ).fetchone()[0]

    total = len(attempts)
    correct = sum(1 for item in attempts if item["is_correct"])
    wrong = [item for item in attempts if not item["is_correct"]]

    counts = {key: 0 for key, _label, _hint in MISCONCEPTIONS}
    for item in wrong:
        key = item["misconception"]
        if key in counts:
            counts[key] += 1

    buckets = [
        {"key": key, "label": label, "hint": hint, "count": counts[key]}
        for key, label, hint in MISCONCEPTIONS
    ]

    tag_counts = {}
    for item in attempts:
        tag = item.get("design_tag")
        if tag in DESIGN_TAGS:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    design_tags = [
        {"tag": tag, "label": label, "count": tag_counts[tag]}
        for tag, label in DESIGN_TAGS.items()
        if tag_counts.get(tag, 0) > 0
    ]

    most_stuck = None
    if wrong:
        groups = {}
        for item in wrong:
            key = (
                item["first_diff_round"],
                item["first_diff_step"],
                item["first_diff_byte"],
            )
            groups[key] = groups.get(key, 0) + 1
        (round_value, step_value, byte_value), count = max(
            groups.items(), key=lambda pair: pair[1]
        )
        if round_value is not None and step_value is not None:
            most_stuck = {
                "round": round_value,
                "step": step_value,
                "byte": byte_value,
                "count": count,
                "label": (
                    f"第 {round_value} 轮 "
                    f"{OP_LABEL.get(step_value, step_value)} · 字节 {byte_value}"
                ),
            }

    # 连续正确：从最近一次往前数
    streak = 0
    for item in reversed(attempts):
        if not item["is_correct"]:
            break
        streak += 1

    trend = [
        {
            "index": index + 1,
            "is_correct": item["is_correct"],
            "created_at": item["created_at"],
        }
        for index, item in enumerate(attempts)
    ][-20:]

    recent = [
        {
            "id": item["id"],
            "item_id": item["item_id"],
            "is_correct": item["is_correct"],
            "first_diff_byte": item["first_diff_byte"],
            "created_at": item["created_at"],
        }
        for item in reversed(attempts)
    ][:10]

    return {
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total, 4) if total else None,
        "streak": streak,
        "misconceptions": buckets,
        "design_tags": design_tags,
        "most_stuck": most_stuck,
        "trend": trend,
        "recent": recent,
        "wrong": list(reversed(wrong))[:10],
        "sample_threshold": 3,
        "scope": scope_label,
        "study_ms": study_ms,
        "event_count": event_count,
    }


def clear_records(client_id):
    """清空这个客户端自己的记录。`legacy-default` 是迁移前数据，不给清。"""
    if client_id == LEGACY_CLIENT_ID:
        raise ValueError("legacy_scope_readonly")

    with connect() as connection:
        attempts = connection.execute(
            "DELETE FROM attempts WHERE client_id = ?", (client_id,)
        ).rowcount
        legacy = connection.execute(
            "DELETE FROM practice_attempts WHERE client_id = ?", (client_id,)
        ).rowcount
        events = connection.execute(
            "DELETE FROM step_events WHERE client_id = ?", (client_id,)
        ).rowcount

    logger.info(
        "records cleared client=%s attempts=%s legacy=%s events=%s",
        client_id,
        attempts,
        legacy,
        events,
    )
    return {"attempts": attempts, "legacy_attempts": legacy, "events": events}
