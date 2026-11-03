import http.client
import json
import sys
import time

HOST = "127.0.0.1"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8021


def post_json(path, payload):
    connection = http.client.HTTPConnection(HOST, PORT, timeout=10)
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    connection.request(
        "POST",
        path,
        body=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    response = connection.getresponse()
    data = response.read().decode("utf-8")
    connection.close()
    return json.loads(data)


trace = post_json(
    "/api/aes/trace",
    {
        "plaintext_hex": "00112233445566778899aabbccddeeff",
        "key_hex": "000102030405060708090a0b0c0d0e0f",
        "key_bits": 128,
        "direction": "encrypt",
    },
)

connection = http.client.HTTPConnection(HOST, PORT, timeout=10)
body = json.dumps(
    {
        "trace_id": trace["trace_id"],
        "step_index": 13,
        "question": "断连测试",
    },
    ensure_ascii=False,
).encode("utf-8")
connection.request(
    "POST",
    "/api/tutor/ask",
    body=body,
    headers={
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "text/event-stream",
    },
)
response = connection.getresponse()
start = time.perf_counter()

for _ in range(4):
    line = response.readline()
    if not line:
        break

elapsed = (time.perf_counter() - start) * 1000
connection.close()
print(f"disconnected_after_ms={elapsed:.2f}")
time.sleep(1.0)