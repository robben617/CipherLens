import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from services.aes_impl import build_trace  # noqa: E402

PLAINTEXT = "00112233445566778899aabbccddeeff"

VECTORS = (
    (
        "C.1",
        PLAINTEXT,
        "000102030405060708090a0b0c0d0e0f",
    ),
    (
        "C.2",
        PLAINTEXT,
        "000102030405060708090a0b0c0d0e0f1011121314151617",
    ),
    (
        "C.3",
        PLAINTEXT,
        "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f",
    ),
)

FIELDS = (
    "trace_id",
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

for name, plaintext, key in VECTORS:
    key_bits = len(key) * 4
    completed = subprocess.run(
        ["node", str(tool), plaintext, key],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    frontend = json.loads(completed.stdout)
    backend = build_trace(plaintext, key, key_bits, "encrypt")

    vector_differences = []
    for field in FIELDS:
        if frontend[field] != backend[field]:
            vector_differences.append(
                f"{field}: frontend={frontend[field]!r} backend={backend[field]!r}"
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

    print(f"{name}: key_bits={key_bits} steps={len(backend['steps'])}")
    print(f"  frontend_trace_id={frontend['trace_id']}")
    print(f"  backend_trace_id={backend['trace_id']}")
    print(f"  frontend_ciphertext={frontend['ciphertext']}")
    print(f"  backend_ciphertext={backend['ciphertext']}")

    if vector_differences:
        differences.extend(
            f"{name} {item}" for item in vector_differences
        )

if differences:
    print(f"differences={len(differences)}")
    for item in differences[:40]:
        print(f"  {item}")
    raise SystemExit(1)

print("differences=0")