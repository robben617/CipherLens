"""题库落库：灌库、读列表、取题目的判分元信息。

三个职责刻意分开：
- `seed_items()`   启动时跑，题库以 `quiz_bank.py` 为准，答案用引擎现算；
- `list_items()`   给 `/api/quiz/items`，**不含 answer / explanation**，否则打开
  浏览器就能看到答案；
- `meta_for()`     判分时取这道题的 design_tag、明文、密钥，用来核对提交的输入。
"""

import logging

from db import connect
from services.aes_impl import AesInputError, build_trace
from services.quiz_bank import QUIZ_BANK

logger = logging.getLogger("cipherlens.quiz")

DESIGN_TAG_LABELS = {
    "key_timing": "轮密钥时机",
    "mix_coefficient": "列混合系数",
    "key_schedule": "密钥扩展方向",
}

# 四级梯度：入门 → 基础 → 进阶 → 挑战。题目按这个顺序出，别按 id 排。
DIFFICULTY_ORDER = ("entry", "basic", "advanced", "challenge")
DIFFICULTY_LABELS = {
    "entry": "入门",
    "basic": "基础",
    "advanced": "进阶",
    "challenge": "挑战",
}

# 判分页给一句人话解释，别让人对着「列混合系数」四个字猜
DESIGN_TAG_HINTS = {
    "key_timing": "轮密钥该用哪一组、在哪一步加，这里最容易错位。",
    "mix_coefficient": "列混合的 2/3/1/1 系数用错，整列都会跟着偏。",
    "key_schedule": "轮密钥是从上一个字推出来的，扩错了后面全错。",
}

UNTAGGED_HINT = "综合题：四步里任意一步错，都会体现在这 16 个字节上。"


def _expected_answer(plaintext_hex, key_hex, key_bits):
    trace = build_trace(plaintext_hex, key_hex, key_bits, "encrypt")
    return trace["output"]


def seed_items():
    """幂等灌库：缺则插、内容不一致则更新。

    题面与答案是同一份事实的两个投影，必须一起同步：改了题却留着旧答案，
    用户怎么做都是错的。答案每次由引擎重算，也就不存在「人写常量写错了」——
    F07 的 S 盒常量就是靠现算比对才发现的。
    """
    inserted = 0
    updated = 0
    with connect() as connection:
        seeded_ids = {}
        for item in QUIZ_BANK:
            answer = _expected_answer(
                item["plaintext_hex"], item["key_hex"], item["key_bits"]
            )
            row = connection.execute(
                "SELECT id FROM quiz_items WHERE item_code = ?",
                (item["code"],),
            ).fetchone()

            if row is None:
                cursor = connection.execute(
                    """
                    INSERT INTO quiz_items
                        (item_code, type, difficulty, misconception_tag, question,
                         answer, explanation, plaintext_hex, key_hex, key_bits)
                    VALUES (?, 'ciphertext', ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item["code"],
                        item["difficulty"],
                        item["tag"],
                        item["question"],
                        answer,
                        item["explanation"],
                        item["plaintext_hex"],
                        item["key_hex"],
                        item["key_bits"],
                    ),
                )
                seeded_ids[item["code"]] = cursor.lastrowid
                inserted += 1
                continue

            seeded_ids[item["code"]] = row["id"]
            current = connection.execute(
                """
                SELECT answer, difficulty, misconception_tag, question,
                       explanation, plaintext_hex, key_hex, key_bits
                FROM quiz_items WHERE id = ?
                """,
                (row["id"],),
            ).fetchone()
            expected = {
                "answer": answer,
                "difficulty": item["difficulty"],
                "misconception_tag": item["tag"],
                "question": item["question"],
                "explanation": item["explanation"],
                "plaintext_hex": item["plaintext_hex"],
                "key_hex": item["key_hex"],
                "key_bits": item["key_bits"],
            }
            if any(current[field] != value for field, value in expected.items()):
                connection.execute(
                    """
                    UPDATE quiz_items
                    SET answer = ?, difficulty = ?, misconception_tag = ?,
                        question = ?, explanation = ?, plaintext_hex = ?,
                        key_hex = ?, key_bits = ?
                    WHERE id = ?
                    """,
                    (
                        answer,
                        item["difficulty"],
                        item["tag"],
                        item["question"],
                        item["explanation"],
                        item["plaintext_hex"],
                        item["key_hex"],
                        item["key_bits"],
                        row["id"],
                    ),
                )
                updated += 1

    if inserted or updated:
        logger.info("quiz items seeded inserted=%s updated=%s", inserted, updated)
    return {"inserted": inserted, "updated": updated}


def item_ids():
    """题目代号 → quiz_items.id（attempts 用整数外键指向题库行）"""
    with connect() as connection:
        rows = connection.execute(
            "SELECT item_code, id FROM quiz_items"
        ).fetchall()
    return {row["item_code"]: row["id"] for row in rows}


def list_items():
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT item_code, difficulty, misconception_tag, question,
                   plaintext_hex, key_hex, key_bits
            FROM quiz_items
            WHERE item_code IS NOT NULL
            """
        ).fetchall()

    def rank(row):
        level = row["difficulty"] or "entry"
        order = (
            DIFFICULTY_ORDER.index(level)
            if level in DIFFICULTY_ORDER
            else len(DIFFICULTY_ORDER)
        )
        return (order, row["item_code"])

    return [
        {
            "id": row["item_code"],
            "difficulty": row["difficulty"],
            "difficulty_label": DIFFICULTY_LABELS.get(row["difficulty"] or "", "未分级"),
            "design_tag": row["misconception_tag"],
            "tag_label": DESIGN_TAG_LABELS.get(row["misconception_tag"] or ""),
            "question": row["question"],
            "plaintext_hex": row["plaintext_hex"],
            "key_hex": row["key_hex"],
            "key_bits": row["key_bits"],
        }
        for row in sorted(rows, key=rank)
    ]


def meta_for(item_code):
    """判分要用的题目信息。题目不存在就报错，不再静默给 None。

    以前 `QUIZ_ITEM_META` 用 `.get(..., (None, None))` 兜底，随手编一个
    `item_id` 也能判分并入库，等于把输入校验让给了调用方。
    """
    with connect() as connection:
        row = connection.execute(
            """
            SELECT id, misconception_tag, plaintext_hex, key_hex, key_bits
            FROM quiz_items WHERE item_code = ?
            """,
            (item_code,),
        ).fetchone()

    if row is None:
        raise AesInputError(
            "unknown_item",
            f"题目 {item_code} 不存在",
            "item_id",
        )

    tag = row["misconception_tag"]
    return {
        "id": row["id"],
        "item_code": item_code,
        "design_tag": tag,
        "design_tag_label": DESIGN_TAG_LABELS.get(tag or ""),
        "design_tag_hint": DESIGN_TAG_HINTS.get(tag or "", UNTAGGED_HINT),
        "plaintext_hex": row["plaintext_hex"] or "",
        "key_hex": row["key_hex"] or "",
        "key_bits": row["key_bits"],
    }
