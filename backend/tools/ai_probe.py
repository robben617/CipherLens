"""通用 AI 端点探针。

阶段 0 只做 `--self-test`（纯函数）；阶段 1 扩展 HTTP 全场景。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.ai_service import (  # noqa: E402
    ai_cache_key,
    context_fingerprint,
    normalize_question,
    sanitize_context,
)

checks: list[tuple[str, bool]] = []


def check(name: str, condition: bool) -> None:
    checks.append((name, bool(condition)))


def selfcheck() -> int:
    clean, missing, ignored = sanitize_context(
        "sbox",
        {
            "mode": "forward",
            "input": 0x53,
            "output": 0xED,
            "selected_hex": "0x53",
            "plaintext_hex": "3243f6a8885a308d313198a2e0370734",
            "key_hex": "2b7e151628aed2a6abf7158809cf4f3c",
        },
    )
    check("sbox_whitelist", clean == {
        "page": "sbox",
        "mode": "forward",
        "input": 0x53,
        "output": 0xED,
        "selected_hex": "0x53",
    })
    check("sbox_ignore_secret_keys", set(ignored) == {"key_hex", "plaintext_hex"})
    check("sbox_missing_pair", sanitize_context("sbox", {"input": 0x53})[1] == ["output"])
    check(
        "sbox_out_of_range",
        sanitize_context("sbox", {"input": 0x153, "output": 0xED})[1] == ["input"],
    )

    home, home_missing, home_ignored = sanitize_context(
        "home", {"page": "home", "byte_index": 1}
    )
    check("home_only_page", home == {"page": "home"} and home_missing == [])
    check("home_ignored_extra", home_ignored == ["byte_index"])

    avalanche, avalanche_missing, avalanche_ignored = sanitize_context(
        "avalanche",
        {
            "target": "plaintext",
            "byte_index": 0,
            "bit_index": 7,
            "key_bits": 128,
            "changed_bits": 62,
            "total_bits": 128,
            "rate": 0.484375,
            "plaintext_hex": "3243f6a8885a308d313198a2e0370734",
        },
    )
    check(
        "avalanche_result",
        avalanche["changed_bits"] == 62
        and avalanche["total_bits"] == 128
        and avalanche["rate"] == 0.484375,
    )
    check("avalanche_ignore_secret", avalanche_ignored == ["plaintext_hex"])
    check(
        "avalanche_invalid",
        sanitize_context(
            "avalanche",
            {"target": "x", "byte_index": 32, "bit_index": 8, "key_bits": 200},
        )[1]
        == ["target", "byte_index", "bit_index", "key_bits"],
    )

    first = context_fingerprint(
        "sbox",
        {
            "page": "sbox",
            "mode": "forward",
            "input": 0x53,
            "output": 0xED,
            "selected_hex": "0x53",
        },
    )
    second = context_fingerprint(
        "sbox",
        {
            "selected_hex": "0x53",
            "output": 0xED,
            "input": 0x53,
            "mode": "forward",
            "page": "sbox",
        },
    )
    other = context_fingerprint(
        "avalanche",
        {
            "page": "avalanche",
            "target": "plaintext",
            "byte_index": 0,
            "bit_index": 7,
            "key_bits": 128,
        },
    )
    check("fingerprint_stable", first == second and len(first) == 16)
    check("fingerprint_cross_page", first != other)
    check(
        "cache_key_cross_page",
        ai_cache_key("sbox", first, "为什么？")
        != ai_cache_key("avalanche", other, "为什么？"),
    )
    check("normalize_nfkc", normalize_question("  ＡＥＳ\t是什么？\n") == "AES 是什么?")

    failed = [name for name, passed in checks if not passed]
    for name, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    print(f"selfcheck: {len(checks) - len(failed)}/{len(checks)} passed")
    return 1 if failed else 0


def main(argv: list[str]) -> int:
    if len(argv) <= 1 or argv[1] == "--self-test":
        return selfcheck()
    print("阶段 1 才会加入 HTTP 模式")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))