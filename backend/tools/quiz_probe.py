"""F12 探针：题库接口、判分、输入核对、事件落库、记录聚合、清空。

用法：py tools/quiz_probe.py [port]
只走 HTTP，不直接读库 —— 断言的就是「前端能拿到什么」。
"""

import http.client
import json
import sys

HOST = "127.0.0.1"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
CLIENT = "c_00000000000000000000000000000f12"
PLAINTEXT = "00112233445566778899aabbccddeeff"
KEY = "000102030405060708090a0b0c0d0e0f"
EXPECTED = "69c4e0d86a7b0430d8cdb78070b4c55a"


def request(method, path, payload=None, client=CLIENT):
    connection = http.client.HTTPConnection(HOST, PORT, timeout=15)
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if client:
        headers["X-Client-Id"] = client
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload else None
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    raw = response.read().decode("utf-8")
    status = response.status
    connection.close()
    return status, (json.loads(raw) if raw else None)


def submit(item_id, answer_hex, plaintext_hex=PLAINTEXT, key_hex=KEY, key_bits=128):
    return request(
        "POST",
        "/api/quiz/submit",
        {
            "item_id": item_id,
            "answer_hex": answer_hex,
            "plaintext_hex": plaintext_hex,
            "key_hex": key_hex,
            "key_bits": key_bits,
        },
    )


def summary():
    return request("GET", "/api/records/summary")[1]


status, items = request("GET", "/api/quiz/items")
codes = [item["id"] for item in items["items"]]
print("items_status=", status, "count=", items["count"], codes)
print("items_leak_answer=", any("answer" in item for item in items["items"]))
print(
    "bits_hist=",
    {bits: sum(1 for i in items["items"] if i["key_bits"] == bits) for bits in (128, 192, 256)},
)

before = summary()["total"]

status, correct = submit("q_042", EXPECTED)
print(
    "correct_status=",
    status,
    "wrong_count=",
    correct["summary"]["wrong_count"],
    "hint=",
    correct["design_tag_hint"],
)

wrong_answer = EXPECTED[:14] + "31" + EXPECTED[16:]
status, wrong = submit("q_042", wrong_answer)
print(
    "wrong_status=",
    status,
    "diff=",
    wrong["diff_bytes"],
    "source=",
    wrong["source_bytes"],
    "step=",
    wrong["source_step_index"],
)

status, item_mismatch = submit(
    "q_042", EXPECTED, plaintext_hex="ffeeddccbbaa99887766554433221100"
)
print(
    "item_mismatch_status=",
    status,
    "mismatch=",
    json.dumps(item_mismatch["input_mismatch"], ensure_ascii=False),
)

status, unknown = submit("q_999", EXPECTED)
print("unknown_item_status=", status, "code=", (unknown or {}).get("error", {}).get("code"))

after = summary()
print("attempts_written=", after["total"] - before, "(应等于 2：一正一错；后两种不落库)")

status, _ = request(
    "POST",
    "/api/events",
    {
        "items": [
            {"type": "session", "step_index": 0, "at": 1762000000000},
            {"type": "step", "step_index": 3, "at": 1762000012000, "dwell_ms": 12000},
            {"type": "step", "step_index": 9, "at": 1762000045000, "dwell_ms": 33000},
            {"type": "   ", "at": 1762000045000},
        ]
    },
)
print("events_status=", status, "(204 才算写入)")

events_no_client = request("POST", "/api/events", {"items": [{"type": "step"}]}, client=None)
print("events_without_client=", events_no_client[0])

record = summary()
print("study_ms=", record["study_ms"], "event_count=", record["event_count"])
print("recent=", [(item["item_id"], item["is_correct"]) for item in record["recent"]])

status, cleared = request("DELETE", "/api/records")
print("clear_status=", status, "removed=", cleared)
print("after_clear_total=", summary()["total"], "study_ms=", summary()["study_ms"])
