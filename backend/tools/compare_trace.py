import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from services.aes_impl import build_trace  # noqa: E402

PLAINTEXT = "00112233445566778899aabbccddeeff"
KEY = "000102030405060708090a0b0c0d0e0f"

tool = BACKEND / "tools" / "dump_frontend_trace.mjs"
completed = subprocess.run(
    ["node", str(tool), PLAINTEXT, KEY],
    cwd=ROOT,
    capture_output=True,
    text=True,
    encoding="utf-8",
    check=True,
)
frontend = json.loads(completed.stdout)
backend = build_trace(PLAINTEXT, KEY, 128, "encrypt")

differences = []

for field in (
    "trace_id",
    "ciphertext",
    "key_bits",
    "direction",
    "rounds",
    "step_count",
    "key_schedule",
):
    if frontend[field] != backend[field]:
        differences.append(f"{field}: frontend={frontend[field]!r} backend={backend[field]!r}")

if len(frontend["steps"]) != len(backend["steps"]):
    differences.append(
        f"steps length: frontend={len(frontend['steps'])} backend={len(backend['steps'])}"
    )

for index, (left, right) in enumerate(zip(frontend["steps"], backend["steps"])):
    for field in (
        "index",
        "round",
        "op",
        "state_before",
        "state_after",
        "changed",
        "key_indices",
        "key_words",
        "label",
    ):
        if left[field] != right[field]:
            differences.append(f"steps[{index}].{field}: {left[field]!r} != {right[field]!r}")

print(f"frontend_steps={len(frontend['steps'])}")
print(f"backend_steps={len(backend['steps'])}")
print(f"frontend_ciphertext={frontend['ciphertext']}")
print(f"backend_ciphertext={backend['ciphertext']}")
print(f"frontend_trace_id={frontend['trace_id']}")
print(f"backend_trace_id={backend['trace_id']}")

if differences:
    print(f"differences={len(differences)}")
    for item in differences[:20]:
        print(f"  {item}")
    raise SystemExit(1)

print("differences=0")