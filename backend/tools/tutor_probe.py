import http.client
import json
import sys
import time

HOST = "127.0.0.1"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
PLAINTEXT = "00112233445566778899aabbccddeeff"
KEY = "000102030405060708090a0b0c0d0e0f"
STEP = 13
QUESTION = "这一步为什么这么做？"


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
    if response.status >= 400:
        raise RuntimeError(f"{path} HTTP {response.status}: {data}")
    return json.loads(data)


def stream_tutor(trace_id):
    connection = http.client.HTTPConnection(HOST, PORT, timeout=25)
    body = json.dumps(
        {
            "trace_id": trace_id,
            "step_index": STEP,
            "question": QUESTION,
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
    frames = []
    event = None
    tokens = []
    meta = None
    done = None

    while True:
        line = response.readline()
        if not line:
            break
        text = line.decode("utf-8").rstrip("\r\n")
        if text.startswith("event: "):
            event = text[7:]
        elif text.startswith("data: "):
            data = json.loads(text[6:])
            elapsed = round((time.perf_counter() - start) * 1000, 2)
            frames.append((event, data, elapsed))
            if event == "token":
                tokens.append(data.get("t", ""))
            elif event == "meta":
                meta = data
            elif event == "done":
                done = data
        elif text == "":
            event = None

    connection.close()
    return frames, "".join(tokens), meta, done


def first_token_ms(frames):
    for event, _data, elapsed in frames:
        if event == "token":
            return elapsed
    return None


trace = post_json(
    "/api/aes/trace",
    {
        "plaintext_hex": PLAINTEXT,
        "key_hex": KEY,
        "key_bits": 128,
        "direction": "encrypt",
    },
)
step = trace["steps"][STEP]

cold_frames, cold_text, cold_meta, cold_done = stream_tutor(trace["trace_id"])
warm_frames, warm_text, warm_meta, warm_done = stream_tutor(trace["trace_id"])

before = " ".join(f"{value:02X}" for value in step["state_before"])
after = " ".join(f"{value:02X}" for value in step["state_after"])

# F09 起回答不再 dump 整行十六进制，只举「一格」为例（整行堆数字对初学者等于没说）。
# 所以这里验的是「那一格真的被引用了」，而不是「整行都出现过」。
example = step["changed"][0] if step["changed"] else 0
example_before = f"0x{step['state_before'][example]:02X}"
example_after = f"0x{step['state_after'][example]:02X}"

print(f"trace_id={trace['trace_id']}")
print(f"step_index={STEP} label={step['label']}")
print(f"cold_meta_source={cold_meta['source']} model={cold_meta.get('model')}")
print(f"cold_meta_cache={cold_meta['cache']} warm_meta_cache={warm_meta['cache']}")
print(f"cold_first_token_ms={first_token_ms(cold_frames)}")
print(f"cold_total_ms={cold_frames[-1][2]}")
print(f"warm_first_token_ms={first_token_ms(warm_frames)}")
print(f"warm_total_ms={warm_frames[-1][2]}")
print(f"cold_tokens={len([f for f in cold_frames if f[0] == 'token'])}")
print(f"warm_tokens={len([f for f in warm_frames if f[0] == 'token'])}")
print(f"example_quoted_before={example_before in cold_text}")
print(f"example_quoted_after={example_after in cold_text}")
print(f"cold_done={cold_done}")
print(f"warm_done={warm_done}")
print("first_5_frames:")
for event, data, elapsed in cold_frames[:5]:
    print(f"  {elapsed:7.2f}ms {event} {json.dumps(data, ensure_ascii=False)}")

if not (example_before in cold_text or example_after in cold_text):
    raise SystemExit("example byte not quoted in tutor answer")
if not warm_meta["cache"]:
    raise SystemExit("second request did not hit cache")