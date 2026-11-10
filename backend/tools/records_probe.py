"""F20 记录页验收探针：直接读写 practice_attempts，模拟 0/2/10 条记录。

seed 数据用于记录页三态与三类误解分布的界面验收，不代表真实答题结果。
真实答题记录由 POST /api/quiz/submit 写入。
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from db import connect  # noqa: E402
from services.records_service import misconception_for, summary  # noqa: E402

STEPS = ("add_round_key", "add_round_key", "mix_columns", "sub_bytes")
ROUNDS = (10, 10, 4, 2)
STEP_INDEXES = (39, 39, 15, 5)
BYTES = (7, 7, 7, 3)


def clear():
    with connect() as connection:
        connection.execute("DELETE FROM practice_attempts")
        connection.execute(
            "DELETE FROM sqlite_sequence WHERE name = 'practice_attempts'"
        )


def seed(count):
    clear()
    with connect() as connection:
        for index in range(count):
            is_correct = 1 if index % 3 == 0 else 0
            step = STEPS[index % len(STEPS)] if not is_correct else None
            round_value = ROUNDS[index % len(ROUNDS)] if not is_correct else None
            step_index_value = STEP_INDEXES[index % len(STEP_INDEXES)] if not is_correct else None
            byte_value = BYTES[index % len(BYTES)] if not is_correct else None
            connection.execute(
                """
                INSERT INTO practice_attempts
                    (item_id, submitted, is_correct,
                     first_diff_round, first_diff_step, first_diff_step_index,
                     first_diff_byte, misconception)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "q_042",
                    f"seed-{index + 1:02d}",
                    is_correct,
                    round_value,
                    step,
                    step_index_value,
                    byte_value,
                    misconception_for(step) if step else None,
                ),
            )


def sql_rows():
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT id, item_id, is_correct,
                   first_diff_round, first_diff_step, first_diff_step_index,
                   first_diff_byte,
                   misconception, created_at
            FROM practice_attempts
            ORDER BY id
            """
        ).fetchall()
    return [dict(row) for row in rows]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--clear", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--sql", action="store_true")
    args = parser.parse_args()

    if args.clear and args.seed is None:
        clear()
    if args.seed is not None:
        seed(args.seed)
    if args.sql:
        print(json.dumps(sql_rows(), ensure_ascii=False, indent=2))
    if args.summary:
        print(json.dumps(summary(scope="legacy"), ensure_ascii=False, indent=2))
    if not (args.clear or args.seed is not None or args.summary or args.sql):
        parser.print_help()


if __name__ == "__main__":
    main()