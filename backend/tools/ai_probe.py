"""通用 AI 端点探针。

阶段 0 只做 `--self-test`（纯函数）；阶段 1 扩展 HTTP 全场景。
"""

import http.client
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.ai_service import (  # noqa: E402
    ai_cache_key,
    build_local_blocks,
    context_fingerprint,
    get_cached,
    iter_ai_events,
    normalize_question,
    put_cached,
    quotes_values,
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

    home_blocks = build_local_blocks("home", {"page": "home"}, "AES 是什么？")
    home_text = json.dumps(home_blocks, ensure_ascii=False)
    check("home_no_concrete_byte", re.search(r"0x[0-9A-Fa-f]{2}", home_text) is None)
    check("home_quotes_false", quotes_values("home", {"page": "home"}) is False)
    sbox_text = json.dumps(build_local_blocks("sbox", clean, "为什么？"), ensure_ascii=False)
    check("sbox_local_values", "0x53" in sbox_text and "0xED" in sbox_text and quotes_values("sbox", clean) is True)
    avalanche_text = json.dumps(build_local_blocks("avalanche", avalanche, "为什么？"), ensure_ascii=False)
    check("avalanche_local_values", "62/128" in avalanche_text and "48.4%" in avalanche_text)
    no_result = sanitize_context("avalanche", {"target": "plaintext", "byte_index": 0, "bit_index": 7, "key_bits": 128})[0]
    no_result_text = json.dumps(build_local_blocks("avalanche", no_result, "为什么？"), ensure_ascii=False)
    check("avalanche_no_result_hint", "先跑一次实验" in no_result_text)
    check("avalanche_no_result_quotes_false", quotes_values("avalanche", no_result) is False)

    events = list(iter_ai_events("home", {"page": "home"}, "AES 是什么？"))
    check(
        "event_iteration",
        events[0][0] == "block"
        and events[0][1]["type"] == "conclusion"
        and any(kind == "token" for kind, _ in events)
        and events[-1][0] == "block"
        and events[-1][1]["type"] == "cite",
    )

    key = ai_cache_key("sbox", first, normalize_question("为什么？"))
    other_key = ai_cache_key("avalanche", other, normalize_question("为什么？"))
    check("cache_key_cross_page_after_blocks", key != other_key)
    check("cache_miss_then_hit", get_cached(key) is None)
    put_cached(key, build_local_blocks("sbox", clean, "为什么？"))
    check("cache_hit", get_cached(key) is not None)

    failed = [name for name, passed in checks if not passed]
    for name, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    print(f"selfcheck: {len(checks) - len(failed)}/{len(checks)} passed")
    return 1 if failed else 0


def _post_sse(port: int, payload: dict):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
    started = time.perf_counter()
    try:
        connection.request(
            "POST",
            "/api/ai/ask",
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        )
        response = connection.getresponse()
        status = response.status
        if status != 200:
            body = response.read().decode("utf-8", errors="replace")
            return status, [], body, (time.perf_counter() - started) * 1000

        frames = []
        event = ""
        data_lines = []
        for raw_line in response:
            line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
            if line == "":
                if event:
                    frames.append((event, json.loads("\n".join(data_lines) or "{}")))
                    event = ""
                    data_lines = []
            elif line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].lstrip())
        if event:
            frames.append((event, json.loads("\n".join(data_lines) or "{}")))
        return status, frames, "", (time.perf_counter() - started) * 1000
    finally:
        connection.close()


def _frames_text(frames) -> str:
    parts = []
    buffer = ""
    for event, data in frames:
        if event == "token":
            buffer += str(data.get("text", data.get("t", "")))
        elif event == "block":
            if buffer:
                parts.append(buffer)
                buffer = ""
            if data.get("text"):
                parts.append(str(data["text"]))
            if isinstance(data.get("items"), list):
                parts.extend(str(item) for item in data["items"])
            for ref in data.get("refs", []):
                parts.append(f"{ref.get('label', '')} {ref.get('value', '')}")
    if buffer:
        parts.append(buffer)
    return " ".join(parts)


def _meta(frames) -> dict:
    for event, data in frames:
        if event == "meta":
            return data
    return {}


def _logs_count():
    path = Path(__file__).resolve().parents[1] / "data" / "cipherlens.db"
    if not path.exists():
        return None
    connection = sqlite3.connect(path)
    try:
        return connection.execute("SELECT COUNT(*) FROM tutor_logs").fetchone()[0]
    except sqlite3.Error:
        return None
    finally:
        connection.close()


def httpcheck(port: int) -> int:
    local_checks = []
    tag = str(int(time.time() * 1000))

    def check(name, condition):
        local_checks.append((name, bool(condition)))

    status, frames, body, elapsed = _post_sse(port, {
        "page": "home", "question": f"AES 是什么？{tag}",
        "context": {"page": "home"}, "conversation_id": "conv_t09_home",
    })
    text = _frames_text(frames)
    meta = _meta(frames)
    check("home_200", status == 200)
    check("home_meta_local", meta.get("source") == "local" and meta.get("quotes_values") is False)
    check("home_no_concrete_byte", re.search(r"0x[0-9A-Fa-f]{2}", text) is None)
    check("home_done", any(event == "done" for event, _ in frames))

    status, frames, body, _ = _post_sse(port, {
        "page": "sbox", "question": f"0x53 为什么查表得到 0xED？{tag}",
        "context": {"page": "sbox", "mode": "forward", "input": 0x53, "output": 0xED, "selected_hex": "0x53"},
        "conversation_id": "conv_t09_sbox",
    })
    text = _frames_text(frames)
    meta = _meta(frames)
    check("sbox_200", status == 200)
    check("sbox_values", "0x53" in text and "0xED" in text and meta.get("quotes_values") is True)

    status, frames, body, _ = _post_sse(port, {
        "page": "sbox", "question": f"这一格为什么这样？{tag}",
        "context": {"page": "sbox"}, "conversation_id": "conv_t09_sbox_empty",
    })
    text = _frames_text(frames)
    check("sbox_no_context_200", status == 200 and "先在" in text)

    status, frames, body, _ = _post_sse(port, {
        "page": "avalanche", "question": f"为什么改 1 位变这么多？{tag}",
        "context": {"page": "avalanche", "target": "plaintext", "byte_index": 0, "bit_index": 7, "key_bits": 128, "changed_bits": 62, "total_bits": 128, "rate": 0.484375},
        "conversation_id": "conv_t09_avalanche",
    })
    text = _frames_text(frames)
    meta = _meta(frames)
    check("avalanche_200", status == 200)
    check("avalanche_values", "62/128" in text and "48.4%" in text and meta.get("quotes_values") is True)

    status, frames, body, _ = _post_sse(port, {
        "page": "avalanche", "question": f"还没有结果怎么说？{tag}",
        "context": {"page": "avalanche", "target": "plaintext", "byte_index": 0, "bit_index": 7, "key_bits": 128},
        "conversation_id": "conv_t09_avalanche_empty",
    })
    text = _frames_text(frames)
    meta = _meta(frames)
    check("avalanche_no_result", status == 200 and "先跑一次实验" in text and meta.get("quotes_values") is False)

    cache_payload = {
        "page": "home", "question": f"cache probe {tag}",
        "context": {"page": "home"}, "conversation_id": "conv_t09_cache",
    }
    status1, frames1, _, _ = _post_sse(port, cache_payload)
    status2, frames2, _, elapsed2 = _post_sse(port, cache_payload)
    meta2 = _meta(frames2)
    token2 = [event for event, _ in frames2 if event == "token"]
    check("cache_200", status1 == 200 and status2 == 200)
    check("cache_meta", meta2.get("cache") is True)
    check("cache_no_tokens", len(token2) == 0)
    check("cache_under_100ms", elapsed2 < 100)

    status, frames, body, _ = _post_sse(port, {
        "page": "sbox", "question": f"不要泄露上下文 {tag}",
        "context": {"page": "sbox", "mode": "forward", "input": 0x53, "output": 0xED, "plaintext_hex": "SECRET_PLAINTEXT", "key_hex": "SECRET_KEY"},
        "conversation_id": "conv_t09_whitelist",
    })
    text = _frames_text(frames)
    meta = _meta(frames)
    check("whitelist_200", status == 200 and "SECRET_PLAINTEXT" not in text and "SECRET_KEY" not in text)
    check("whitelist_ignored", set(meta.get("context_ignored", [])) == {"plaintext_hex", "key_hex"})

    status, frames, body, _ = _post_sse(port, {
        "page": "home", "question": "unknown top level", "context": {"page": "home"},
        "conversation_id": "conv_t09_extra", "unexpected": 1,
    })
    check("top_level_extra_ignored", status == 200)

    status, _, body, _ = _post_sse(port, {
        "page": "practice", "question": "x", "context": {}, "conversation_id": "conv_t09_bad_page",
    })
    check("invalid_page_400", status == 400)

    status, _, _, _ = _post_sse(port, {
        "page": "home", "question": "x" * 501, "context": {}, "conversation_id": "conv_t09_long",
    })
    check("long_question_400", status == 400)
    status, _, _, _ = _post_sse(port, {
        "page": "home", "question": "   ", "context": {}, "conversation_id": "conv_t09_blank",
    })
    check("blank_question_400", status == 400)

    before = _logs_count()
    status, _, _, _ = _post_sse(port, {
        "page": "home", "question": f"audit probe {tag}", "context": {"page": "home"},
        "conversation_id": "conv_t09_log",
    })
    after = _logs_count()
    if before is None or after is None:
        print("SKIP tutor_logs database unavailable")
    else:
        check("tutor_logs_unchanged", before == after)

    for name, passed in local_checks:
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    failed = [name for name, passed in local_checks if not passed]
    print(f"httpcheck: {len(local_checks) - len(failed)}/{len(local_checks)} passed")
    return 1 if failed else 0


def main(argv: list[str]) -> int:
    if len(argv) <= 1 or argv[1] == "--self-test":
        return selfcheck()
    if argv[1].isdigit():
        return httpcheck(int(argv[1]))
    print("用法：ai_probe.py --self-test | ai_probe.py <port>")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))