import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from services.aes_impl import build_trace  # noqa: E402

PLAINTEXT = "00112233445566778899aabbccddeeff"

# (名称, 密钥, 密文) —— 加密用明文起步，解密用密文起步，两边都跑一遍
VECTORS = (
    (
        "C.1",
        "000102030405060708090a0b0c0d0e0f",
        "69c4e0d86a7b0430d8cdb78070b4c55a",
    ),
    (
        "C.2",
        "000102030405060708090a0b0c0d0e0f1011121314151617",
        "dda97ca4864cdfe06eaf70a0ec0d7191",
    ),
    (
        "C.3",
        "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f",
        "8ea2b7ca516745bfeafc49904b496089",
    ),
)

FIELDS = (
    "trace_id",
    "output",
    "ciphertext",
    "key_bits",
    "direction",
    "rounds",
    "step_count",
    "key_schedule",
)

STEP_FIELDS = (
    "index",
    "round",
    "op",
    "state_before",
    "state_after",
    "changed",
    "key_indices",
    "key_words",
    "label",
)

tool = BACKEND / "tools" / "dump_frontend_trace.mjs"
differences = []


def compare(name, plaintext, key, direction):
    """跑一组：前端 buildTrace 与后端 build_trace 逐字段比对。"""
    key_bits = len(key) * 4
    completed = subprocess.run(
        ["node", str(tool), plaintext, key, direction],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    frontend = json.loads(completed.stdout)
    backend = build_trace(plaintext, key, key_bits, direction)

    vector_differences = []
    for field in FIELDS:
        if frontend.get(field) != backend.get(field):
            vector_differences.append(
                f"{field}: frontend={frontend.get(field)!r} backend={backend.get(field)!r}"
            )

    if len(frontend["steps"]) != len(backend["steps"]):
        vector_differences.append(
            f"steps length: frontend={len(frontend['steps'])} "
            f"backend={len(backend['steps'])}"
        )

    for index, (left, right) in enumerate(zip(frontend["steps"], backend["steps"])):
        for field in STEP_FIELDS:
            if left[field] != right[field]:
                vector_differences.append(
                    f"steps[{index}].{field}: {left[field]!r} != {right[field]!r}"
                )

    print(f"{name} {direction}: key_bits={key_bits} steps={len(backend['steps'])}")
    print(f"  frontend_trace_id={frontend['trace_id']}")
    print(f"  backend_trace_id={backend['trace_id']}")
    print(f"  frontend_output={frontend['output']}")
    print(f"  backend_output={backend['output']}")

    if vector_differences:
        differences.extend(f"{name}/{direction} {item}" for item in vector_differences)


for name, key, ciphertext in VECTORS:
    compare(name, PLAINTEXT, key, "encrypt")
    compare(name, ciphertext, key, "decrypt")

if differences:
    print(f"differences={len(differences)}")
    for item in differences[:40]:
        print(f"  {item}")
    raise SystemExit(1)

print("differences=0")
