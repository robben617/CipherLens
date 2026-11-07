from db import connect

MISCONCEPTIONS = (
    ("key_timing", "轮密钥时机", "轮密钥加的时机与顺序"),
    ("mix_coefficient", "列混合系数", "列混合系数与扩散方向"),
    ("key_schedule", "密钥扩展方向", "轮密钥的来源与扩展方向"),
)

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


def record_attempt(payload, result):
    if result.get("input_mismatch") is not None:
        return

    first = result.get("first_diff")
    round_value = first["round"] if first else None
    step_value = first["step"] if first else None
    step_index_value = first["step_index"] if first else None
    byte_value = first["byte_index"] if first else None
    misconception = misconception_for(step_value) if first else None
    is_correct = 1 if first is None else 0

    with connect() as connection:
        connection.execute(
            """
            INSERT INTO practice_attempts
                (item_id, submitted, is_correct,
                 first_diff_round, first_diff_step, first_diff_step_index,
                 first_diff_byte, misconception)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
        "created_at": row["created_at"],
    }


def summary():
    with connect() as connection:
        rows = connection.execute(
            "SELECT * FROM practice_attempts ORDER BY id ASC"
        ).fetchall()

    attempts = [_row_to_attempt(row) for row in rows]
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
        "most_stuck": most_stuck,
        "trend": trend,
        "wrong": list(reversed(wrong))[:10],
        "sample_threshold": 3,
    }