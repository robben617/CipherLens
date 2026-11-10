import re

from db import connect

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

OP_LABELS = {
    "add_round_key": "轮密钥加",
    "mix_columns": "列混合",
    "sub_bytes": "字节代换",
    "shift_rows": "行移位",
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
    if result.get("input_mismatch") is not None:
        return

    first = result.get("first_diff")
    round_value = first["round"] if first else None
    step_value = first["step"] if first else None
    step_index_value = first["step_index"] if first else None
    byte_value = first["byte_index"] if first else None
    misconception = "unattributed" if first else None
    design_tag = result.get("design_tag")
    is_correct = 1 if first is None else 0

    with connect() as connection:
        connection.execute(
            """
            INSERT INTO practice_attempts
                (item_id, submitted, is_correct,
                 first_diff_round, first_diff_step, first_diff_step_index,
                 first_diff_byte, misconception, client_id, design_tag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.item_id,
                payload.answer_hex,
                is_correct,
                round_value,
                step_value,
                step_index_value,
                byte_value,
                misconception,
                client_id,
                design_tag,
            ),
        )


def _row_to_attempt(row):
    return {
        "id": row["id"],
        "item_id": row["item_id"],
        "submitted": row["submitted"],
        "is_correct": bool(row["is_correct"]),
        "first_diff_round": row["first_diff_round"],
        "first_diff_step": row["first_diff_step"],
        "first_diff_step_index": row["first_diff_step_index"],
        "first_diff_byte": row["first_diff_byte"],
        "misconception": row["misconception"],
        "client_id": row["client_id"] if "client_id" in row.keys() else LEGACY_CLIENT_ID,
        "design_tag": row["design_tag"] if "design_tag" in row.keys() else None,
        "created_at": row["created_at"],
    }


def summary(client_id=None, scope=None):
    with connect() as connection:
        rows = connection.execute(
            "SELECT * FROM practice_attempts ORDER BY id ASC"
        ).fetchall()

    attempts = [_row_to_attempt(row) for row in rows]
    if client_id:
        attempts = [item for item in attempts if item["client_id"] == client_id]
        scope_label = "client"
    elif scope == "legacy":
        attempts = [
            item for item in attempts if item["client_id"] == LEGACY_CLIENT_ID
        ]
        scope_label = "legacy"
    else:
        attempts = []
        scope_label = "none"
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
                    f"{OP_LABELS.get(step_value, step_value)} · 字节 {byte_value}"
                ),
            }

    trend = [
        {
            "index": index + 1,
            "is_correct": item["is_correct"],
            "created_at": item["created_at"],
        }
        for index, item in enumerate(attempts)
    ][-20:]

    return {
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total, 4) if total else None,
        "misconceptions": buckets,
        "design_tags": design_tags,
        "most_stuck": most_stuck,
        "trend": trend,
        "wrong": list(reversed(wrong))[:10],
        "sample_threshold": 3,
        "scope": scope_label,
    }