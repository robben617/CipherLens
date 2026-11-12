"""F16 探针：雪崩接口的数值、边界与「与 trace 同一份实现」。

用法：py tools/avalanche_probe.py [port]
只走 HTTP。断言的都是前端能拿到的字段 —— 数值错了，前端画得再对也没意义。
"""

import http.client
import json
import sys

HOST = "127.0.0.1"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
PLAINTEXT = "00112233445566778899aabbccddeeff"
KEY128 = "000102030405060708090a0b0c0d0e0f"
KEY192 = "000102030405060708090a0b0c0d0e0f1011121314151617"
KEY256 = "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
CIPHER128 = "69c4e0d86a7b0430d8cdb78070b4c55a"


def request(method, path, payload=None):
    connection = http.client.HTTPConnection(HOST, PORT, timeout=20)
    headers = {"Content-Type": "application/json; charset=utf-8"}
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload else None
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    raw = response.read().decode("utf-8")
    status = response.status
    connection.close()
    return status, (json.loads(raw) if raw else None)


def avalanche(**overrides):
    payload = {"plaintext_hex": PLAINTEXT, "key_hex": KEY128, "target": "plaintext", "byte_index": 0}
    payload.update(overrides)
    return request("POST", "/api/aes/avalanche", payload)


def sweep(**overrides):
    payload = {"plaintext_hex": PLAINTEXT, "key_hex": KEY128, "target": "plaintext"}
    payload.update(overrides)
    return request("POST", "/api/aes/avalanche/sweep", payload)


failures = []


def check(label, condition, detail=""):
    print(("PASS " if condition else "FAIL ") + label + ("" if condition else f"  <- {detail}"))
    if not condition:
        failures.append(label)


# ---- 单次：改明文 1 位 ----------------------------------------------------
status, body = avalanche()
check("plain_status", status == 200, status)
check("cipher_matches_fips", body["before"]["cipher_hex"] == CIPHER128, body["before"]["cipher_hex"])
check("cipher_after_differs", body["after"]["cipher_hex"] != body["before"]["cipher_hex"])
check("bit_flags_len", len(body["bit_flags"]) == 128, len(body["bit_flags"]))
check("bit_flags_sum", sum(body["bit_flags"]) == body["changed_bits"], body["changed_bits"])
check("byte_bits_len", len(body["byte_bits"]) == 16 and sum(1 for b in body["byte_bits"] if b) == body["changed_bytes"])
check("changed_bytes_all", body["changed_bytes"] == 16, body["changed_bytes"])
check("rate_is_half", 0.35 <= body["rate"] <= 0.65, body["rate"])
check("flip_is_one_bit", body["input_byte_before"] ^ body["input_byte_after"] == 1, body)
check("byte_index_echo", body["byte_index"] == 0)
check("key_bits_echo", body["key_bits"] == 128)
print("   changed_bits =", body["changed_bits"], "rate =", body["rate"], "per_byte =", body["byte_bits"])

# 换一个字节：结果必须不同，但不是「全都一样」
status, other = avalanche(byte_index=5)
check("other_byte_status", status == 200, status)
check("other_byte_changed", other["after"]["cipher_hex"] != body["after"]["cipher_hex"])
check("other_byte_in_range", 0.35 <= other["rate"] <= 0.65, other["rate"])

# ---- 单次：改密钥 1 位 ----------------------------------------------------
status, key_flip = avalanche(target="key")
check("key_status", status == 200, status)
check("key_flip_differs", key_flip["after"]["cipher_hex"] != CIPHER128)
check("key_flip_in_range", 0.35 <= key_flip["rate"] <= 0.65, key_flip["rate"])

# ---- 密钥长度 192 / 256 ---------------------------------------------------
for bits, key in ((192, KEY192), (256, KEY256)):
    status, result = avalanche(key_hex=key)
    check(f"aes{bits}_status", status == 200, status)
    check(f"aes{bits}_key_bits", result["key_bits"] == bits, result["key_bits"])
    status, wide = sweep(key_hex=key, target="key")
    check(f"aes{bits}_sweep_trials", status == 200 and wide["trials"] == bits // 8, wide.get("trials"))

# ---- 连做 ----------------------------------------------------------------
status, stats = sweep()
check("sweep_status", status == 200, status)
check("sweep_trials", stats["trials"] == 16, stats["trials"])
check("sweep_mean_near_half", 55 <= stats["mean"] <= 75, stats["mean"])
check("sweep_min_above_third", stats["min_bits"] > 32, stats["min_bits"])
check("sweep_samples_len", len(stats["samples"]) == 16)
print("   sweep mean =", stats["mean"], "min =", stats["min_bits"], "max =", stats["max_bits"])

status, key_stats = sweep(target="key")
check("key_sweep_status", status == 200, status)
check("key_sweep_mean", 55 <= key_stats["mean"] <= 75, key_stats["mean"])

# ---- 与 /api/aes/trace 同一份实现 ----------------------------------------
status, trace = request(
    "POST",
    "/api/aes/trace",
    {"plaintext_hex": PLAINTEXT, "key_hex": KEY128, "key_bits": 128},
)
check("trace_status", status == 200, status)
check("same_impl", trace["output"] == body["before"]["cipher_hex"], (trace["output"], body["before"]["cipher_hex"]))

# ---- 边界 ----------------------------------------------------------------
status, error = avalanche(byte_index=16)
check("byte_index_out_of_range", status == 400 and error["error"]["code"] == "invalid_byte_index", (status, error))
status, error = avalanche(key_hex=KEY128 + "00")  # 17 字节：过了 pydantic，该由引擎拒
check("bad_key_length_400", status == 400 and error["error"]["code"] == "invalid_key", (status, error))
status, error = avalanche(target="both")
check("bad_target_400", status == 400 and error["error"]["code"] == "validation_error", (status, error))
status, error = request("POST", "/api/aes/avalanche", {"plaintext_hex": "zz" * 16, "key_hex": KEY128})
check(
    "bad_hex_400",
    status == 400 and error["error"]["code"] in ("validation_error", "invalid_hex"),
    (status, error),
)

print()
print("FAILURES:", failures if failures else "none")
sys.exit(1 if failures else 0)
