import http.client
import json
import sys

HOST = "127.0.0.1"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
PLAINTEXT = "00112233445566778899aabbccddeeff"
KEY = "000102030405060708090a0b0c0d0e0f"
EXPECTED = "69c4e0d86a7b0430d8cdb78070b4c55a"


def post(path, payload):
    connection = http.client.HTTPConnection(HOST, PORT, timeout=10)
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    connection.request(
        "POST",
        path,
        body=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    response = connection.getresponse()
    raw = response.read().decode("utf-8")
    status = response.status
    connection.close()
    return status, raw


def submit(answer_hex, plaintext_hex=PLAINTEXT, key_hex=KEY):
    status, raw = post(
        "/api/quiz/submit",
        {
            "item_id": "q_042",
            "answer_hex": answer_hex,
            "plaintext_hex": plaintext_hex,
            "key_hex": key_hex,
            "key_bits": 128,
        },
    )
    return status, json.loads(raw) if raw else None


status, correct = submit(EXPECTED)
print("correct_status=", status)
print("correct=", json.dumps(correct, ensure_ascii=False))

wrong_answer = EXPECTED[:14] + "31" + EXPECTED[16:]
status, wrong = submit(wrong_answer)
print("wrong_status=", status)
print("wrong=", json.dumps(wrong, ensure_ascii=False))

status, bad_plaintext = submit(
    EXPECTED,
    plaintext_hex="001122G3445566778899aabbccddeeff",
)
print("bad_plaintext_status=", status)
print("bad_plaintext=", json.dumps(bad_plaintext, ensure_ascii=False))

status, bad_key = submit(
    EXPECTED,
    key_hex="000102030405060708090a0b0c0d0e0G",
)
print("bad_key_status=", status)
print("bad_key=", json.dumps(bad_key, ensure_ascii=False))

status, raw = post(
    "/api/events",
    {
        "session_id": "s_9c21",
        "items": [
            {"type": "step_revert", "step_index": 11, "at": 1762012345678},
            {
                "type": "tutor_ask",
                "step_index": 13,
                "at": 1762012355120,
                "payload": {"cached": False},
            },
        ],
    },
)
print("events_status=", status)
print("events_body=", raw)