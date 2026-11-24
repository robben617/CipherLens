"""真实 LLM 接入 —— OpenAI 兼容的 /chat/completions 流式接口。

为什么不用各家 SDK：这条链路上唯一需要的东西是「一行一帧的 `data: {...}`」，
而 chat/completions 的流式协议早就统一了。装 SDK 等于把版本升级、代理配置、
异步客户端这些变量一起引进来，出问题时先要排查 SDK 而不是自己的代码。
httpx 只做三件事：POST 一个 JSON、读 SSE 行、超时。

降级是硬要求（答辩现场的网络不可控）：
    未配置 key            → 直接走本地模板，`source=local`
    首字前失败 / 超时 / 429 / 5xx → 重试一次（超时 ×1.5），仍失败再由调用方降级
    已经吐了一部分再断      → 不推倒重来，把断点告诉前端（retryable）
"""

from __future__ import annotations

import json
import logging
import os
import re
import time

import httpx

from services import agent_tools
from services.glossary import OP_LABEL

logger = logging.getLogger("cipherlens.llm")

TIMEOUT_DEFAULT = 20.0
RETRY_FACTOR = 1.5
MAX_TOKENS_DEFAULT = 400
QUESTION_LOG_LIMIT = 80


class LLMUnavailable(Exception):
    """模型不可用。`partial` 为真表示已经发出过内容，不能再从头重放。"""

    def __init__(self, code, message, *, retryable=True, partial=False):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.partial = partial
        self.audit = None


# ---------------------------------------------------------------- 配置

def _num_env(name, default, cast):
    raw = os.getenv(name, "")
    if not raw.strip():
        return default
    try:
        return cast(raw)
    except ValueError:
        logger.warning("bad env %s ignored", name)
        return default


def _override_text(override, name):
    """override 可能是 pydantic 模型或 dict；只取字符串，空值不回写。"""
    if override is None:
        return ""
    value = override.get(name) if isinstance(override, dict) else getattr(override, name, "")
    return value.strip() if isinstance(value, str) else ""


def config(override=None):
    """每次调用现读环境变量：测试和演示都要能在不重启的情况下切 key。

    override 只作用于当前请求：前端把「存在浏览器里的配置」随请求带来，
    后端不写进程状态、不落库、不记日志。
    """
    values = {
        "base_url": os.getenv("LLM_BASE_URL", "").strip().rstrip("/"),
        "api_key": os.getenv("LLM_API_KEY", "").strip(),
        "model": os.getenv("LLM_MODEL", "").strip(),
        "timeout": _num_env("LLM_TIMEOUT_S", TIMEOUT_DEFAULT, float),
        "max_tokens": _num_env("LLM_MAX_TOKENS", MAX_TOKENS_DEFAULT, int),
    }
    if override is not None:
        base_url = _override_text(override, "base_url")
        api_key = _override_text(override, "api_key")
        model = _override_text(override, "model")
        if base_url:
            values["base_url"] = base_url.rstrip("/")
        if api_key:
            values["api_key"] = api_key
        if model:
            values["model"] = model
    return values


def enabled():
    values = config()
    return bool(values["base_url"] and values["api_key"] and values["model"])


def public_status():
    """给 /api/health 用。**不含 base_url 与 key**。"""
    values = config()
    return {
        "enabled": bool(values["base_url"] and values["api_key"] and values["model"]),
        "model": values["model"] or None,
    }


# ---------------------------------------------------------------- 提示词

SYSTEM_PROMPT = """你是 AES 教学助手，面对刚学密码学的大学生。
学生正在看：{label}（整条链路的第 {index} 步，从 0 计），当前方向是{direction}。
规则：
1. 只讲当前这一步，不要扩展到整轮或整个算法。
2. 十六进制数值只能照抄给定的 before / after，禁止自己推算或编造。
3. 用中文口语，全文不超过 220 字。
4. 严格按下面的标题格式输出，标题单独占一行，不加粗、不用代码块：
【结论】
一句话说清这一步做了什么。
【为什么】
- 第一条
- 第二条
【下一步】
一句话说明下一步做什么。
5. 数据里看不出来的地方就说「这一步的数据里看不出」，不要猜。
6. 解密时方向是反的：行移位是循环右移、字节代换查逆 S 盒、列混合乘逆矩阵，
   轮密钥从最后一组往第 0 组倒着用。别把逆操作说成正操作。"""


def _hex(values):
    return " ".join(f"{value:02X}" for value in values)


def build_messages(trace, step_index, question):
    """只带当前步（和前后步的 op 名），不带全量 trace。

    全量 trace 有 40 步 × 16 字节，模型读不完也读不准，还费 token；
    讲这一步需要的全部信息就在这一步的 before / after / changed 里。
    """
    steps = trace["steps"]
    step = steps[step_index]
    prev_op = steps[step_index - 1]["op"] if step_index > 0 else None
    next_op = steps[step_index + 1]["op"] if step_index + 1 < len(steps) else None

    system = SYSTEM_PROMPT.format(
        label=step.get("label") or OP_LABEL.get(step["op"], step["op"]),
        index=step_index,
        direction="解密" if trace.get("direction") == "decrypt" else "加密",
    )
    user = {
        "direction": "decrypt" if trace.get("direction") == "decrypt" else "encrypt",
        "round": step["round"],
        "op": step["op"],
        "op_label": OP_LABEL.get(step["op"], step["op"]),
        "before": _hex(step["state_before"]),
        "after": _hex(step["state_after"]),
        "changed": list(step["changed"]),
        "prev_op": OP_LABEL.get(prev_op) if prev_op else None,
        "next_op": OP_LABEL.get(next_op) if next_op else None,
        "question": question,
    }
    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": json.dumps(user, ensure_ascii=False),
        },
    ]


# ---------------------------------------------------------------- 网络

async def _stream_once(messages, values, timeout):
    """一次请求，逐段吐 delta。错误一律翻译成 LLMUnavailable。"""
    url = f"{values['base_url']}/chat/completions"
    body = {
        "model": values["model"],
        "messages": messages,
        "stream": True,
        "temperature": 0.3,
        "max_tokens": values["max_tokens"],
    }
    headers = {
        "Authorization": f"Bearer {values['api_key']}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=min(5.0, timeout))
        ) as client:
            async with client.stream("POST", url, json=body, headers=headers) as response:
                if response.status_code != 200:
                    await response.aread()
                    status = response.status_code
                    raise LLMUnavailable(
                        f"llm_http_{status}",
                        f"模型服务返回 {status}",
                        retryable=status in (408, 429) or status >= 500,
                    )

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line.startswith("data:"):
                        continue
                    chunk = line[5:].strip()
                    if chunk == "[DONE]":
                        return
                    try:
                        payload = json.loads(chunk)
                    except json.JSONDecodeError:
                        # 心跳、注释、厂商自定义帧都会走到这里，跳过即可
                        continue
                    for choice in payload.get("choices") or []:
                        piece = (choice.get("delta") or {}).get("content")
                        if piece:
                            yield piece
    except httpx.TimeoutException as error:
        raise LLMUnavailable("llm_timeout", "模型服务超时", retryable=True) from error
    except httpx.HTTPError as error:
        raise LLMUnavailable("llm_network", "连不上模型服务", retryable=True) from error


# ---------------------------------------------------------------- 文本 → 四块

MARKERS = {"结论": "conclusion", "为什么": "why", "下一步": "next"}

_MARKER_LINE = re.compile(
    r"^[#>*_\s]*[【\[]?(结论|为什么|下一步)[】\]]?[*_]*[：:]?\s*(.*)$"
)
_BULLET = re.compile(r"^[-•·]\s")
_BULLET_PREFIX = re.compile(r"^(?:[-•·*]\s*|\d+[.、)]\s*)")
_HEX_VALUE = re.compile(r"0[xX]([0-9A-Fa-f]{2})(?![0-9A-Fa-f])")


class BlockAssembler:
    """把模型吐的纯文本增量拼成 F09 的四块事件。

    容错取向：**先等第一段文字到了再开「结论」块**，遇到标题再切换。
    模型不按格式来时正文全落在结论块里，一个字都不丢；模型一个字都不吐时，
    调用方还能干净地降级到本地模板（一个空块都没发出去）。
    """

    # 单行太长（模型不换行）时先吐一段，别让读者干等
    FLUSH_AT = 48
    FLUSH_KEEP = 16

    def __init__(self, changed, total):
        self.changed = list(changed)
        self.total = total
        self.buffer = ""
        self.current = None
        self.text = []

    @property
    def started(self):
        return self.current is not None

    def start(self):
        self.current = "conclusion"
        return [("block", {"type": "conclusion", "text": ""})]

    def feed(self, delta):
        self.buffer += delta
        return self._drain()

    def finish(self):
        events = self._drain(final=True)
        events.append(
            (
                "block",
                {
                    "type": "cite",
                    "bytes": self.changed[:3] if self.changed else [0, 1, 2],
                    "total": self.total,
                },
            )
        )
        return events

    # -- 内部

    def _drain(self, final=False):
        events = []
        while True:
            index = self.buffer.find("\n")
            if index < 0:
                break
            line = self.buffer[:index]
            self.buffer = self.buffer[index + 1 :]
            events.extend(self._line(line))
        if final:
            if self.buffer:
                events.extend(self._line(self.buffer))
                self.buffer = ""
            return events
        if len(self.buffer) >= self.FLUSH_AT:
            head = self.buffer[: -self.FLUSH_KEEP]
            self.buffer = self.buffer[-self.FLUSH_KEEP :]
            events.extend(self._text(head))
        return events

    def _line(self, line):
        stripped = line.strip()
        if not stripped:
            return []
        if not _BULLET.match(stripped):
            match = _MARKER_LINE.match(stripped)
            if match:
                return self._switch(MARKERS[match.group(1)], match.group(2).strip())
        if self.current == "why":
            item = _BULLET_PREFIX.sub("", stripped).strip()
            if not item:
                return []
            return self._new_item(item)
        return self._text(stripped if self.current == "conclusion" else line)

    def _switch(self, kind, rest):
        if kind == self.current:
            # 模型把同一个标题写了两遍：当正文续写，别开第二个块
            return self._text(rest) if rest else []
        self.current = kind
        if kind == "why":
            events = [("block", {"type": "why", "items": []})]
        elif kind == "next":
            events = [("block", {"type": "next", "text": ""})]
        else:
            events = [("block", {"type": "conclusion", "text": ""})]
        if rest:
            events.extend(self._text(rest))
        return events

    def _text(self, piece):
        if not piece:
            return []
        self.text.append(piece)
        return [("token", {"t": piece, "text": piece})]

    def _new_item(self, item):
        self.text.append(item)
        return [("token", {"t": item, "text": item, "item": True})]

    # -- 审计

    def hex_outside(self, allowed):
        """模型给出的、当前这一步数据里并不存在的十六进制值。

        不拦（中途打断会毁掉整段可读性），只记账：这是「编数值」的唯一可量化证据。
        """
        allowed = {int(value) for value in allowed}
        found = {int(match, 16) for match in _HEX_VALUE.findall(" ".join(self.text))}
        return sorted(found - allowed)


def allowed_hex(trace, step_index, question):
    """模型**被允许**引用的字节值：本步的 before / after，加上问题里问到的那个。

    刻意不含轮密钥：提示词没给它密钥，它真写出一个密钥字节就是自己算的。
    这条口径与验收「回答里的十六进制值逐个能在当前步 before/after 里找到」一致。
    """
    step = trace["steps"][step_index]
    values = set(step["state_before"]) | set(step["state_after"])
    for match in _HEX_VALUE.findall(question or ""):
        values.add(int(match, 16))
    return values


# ---------------------------------------------------------------- 对外

async def stream_answer(trace, step_index, question, override=None):
    """产出 (event, data)：与本地模板完全相同的 block / token 协议。

    最后额外产出一帧 `("audit", {...})`，只给调用方记账用，不发给前端。
    """
    values = config(override)
    if not (values["base_url"] and values["api_key"] and values["model"]):
        raise LLMUnavailable("llm_disabled", "未配置模型", retryable=False)

    messages = build_messages(trace, step_index, question)
    step = trace["steps"][step_index]
    assembler = BlockAssembler(step["changed"], len(step["changed"]))
    allowed = allowed_hex(trace, step_index, question)

    for attempt in (1, 2):
        timeout = values["timeout"] * (RETRY_FACTOR if attempt == 2 else 1.0)
        try:
            async for piece in _stream_once(messages, values, timeout):
                if not assembler.started:
                    for event in assembler.start():
                        yield event
                for event in assembler.feed(piece):
                    yield event
        except LLMUnavailable as error:
            if assembler.started:
                # 已经吐过字：补上依据块再抛，前端留着已生成的部分
                for event in assembler.finish():
                    yield event
                error.partial = True
                error.audit = {"hex_outside": assembler.hex_outside(allowed)}
                raise error
            if not error.retryable or attempt == 2:
                raise
            logger.warning("llm retry code=%s attempt=%s", error.code, attempt)
            continue

        if not assembler.started:
            raise LLMUnavailable("llm_empty", "模型没有返回内容", retryable=False)

        for event in assembler.finish():
            yield event
        yield "audit", {"hex_outside": assembler.hex_outside(allowed)}
        return

# ---------------------------------------------------------------- 页面问答

PAGE_LABEL = {"home": "首页", "sbox": "S 盒", "avalanche": "雪崩"}

PAGE_SYSTEM_PROMPT = """你是 CipherLens 的 AES 教学助手，面对刚学密码学的大学生。
当前页面：{page}。
规则：
1. 只回答与当前页面、AES 教学相关的问题；与这两个主题无关时，用一句中文说明你只负责讲解本站内容。
2. 页面上下文由用户端提供，只能引用其中出现的数值，禁止自己推算或编造十六进制值。
3. 用中文口语，全文不超过 220 字，不要输出 Markdown 标题、代码块或表格。
4. 数据里看不出来的地方就说「这一步的数据里看不出」，不要猜。"""


def build_page_messages(page, clean, question):
    system = PAGE_SYSTEM_PROMPT.format(page=PAGE_LABEL.get(page, page))
    user = {"page": page, "context": clean, "question": question}
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
    ]


async def stream_page_answer(page, clean, question, override=None):
    """页面级问答：产出纯文本增量，不套四块协议。

    与工作台单步讲解不同，页面问答没有 trace 步号可引用；前端只需要
    一段连续文字，因此这里不经过 BlockAssembler。
    """
    values = config(override)
    if not (values["base_url"] and values["api_key"] and values["model"]):
        raise LLMUnavailable("llm_disabled", "未配置模型", retryable=False)

    messages = build_page_messages(page, clean, question)
    produced = 0
    for attempt in (1, 2):
        timeout = values["timeout"] * (RETRY_FACTOR if attempt == 2 else 1.0)
        try:
            async for piece in _stream_once(messages, values, timeout):
                produced += 1
                yield piece
            if produced == 0:
                raise LLMUnavailable("llm_empty", "模型没有返回内容", retryable=False)
            return
        except LLMUnavailable as error:
            if produced:
                # 已经吐出内容：不重试、不重放，交给调用方保留已生成部分
                error.partial = True
                raise
            if not error.retryable or attempt == 2:
                raise
            logger.warning("llm page retry code=%s attempt=%s", error.code, attempt)


# ---------------------------------------------------------------- 连通性测试

PROBE_MESSAGES = [{"role": "user", "content": "ping"}]


def _probe_message(status):
    if status in (401, 403):
        return "API Key 无效或没有调用权限"
    if status == 404:
        return "地址或模型 ID 不正确"
    if status == 429:
        return "请求过于频繁，稍后再试"
    if status >= 500:
        return "服务商暂时不可用"
    return f"模型服务返回 {status}"


async def probe(base_url, api_key, model, timeout=12.0):
    """连通性测试：一次非流式最小请求。不记录 key，不保存任何内容。"""
    values = {
        "base_url": (base_url or "").strip().rstrip("/"),
        "api_key": (api_key or "").strip(),
        "model": (model or "").strip(),
    }
    if not (values["base_url"] and values["api_key"] and values["model"]):
        raise LLMUnavailable("llm_disabled", "配置不完整", retryable=False)

    url = f"{values['base_url']}/chat/completions"
    body = {
        "model": values["model"],
        "messages": PROBE_MESSAGES,
        "stream": False,
        "max_tokens": 1,
    }
    headers = {
        "Authorization": f"Bearer {values['api_key']}",
        "Content-Type": "application/json",
    }

    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=min(5.0, timeout))
        ) as client:
            response = await client.post(url, json=body, headers=headers)
    except httpx.TimeoutException as error:
        raise LLMUnavailable("llm_timeout", "连接超时", retryable=True) from error
    except httpx.HTTPError as error:
        raise LLMUnavailable("llm_network", "连不上模型服务", retryable=True) from error

    if response.status_code != 200:
        raise LLMUnavailable(
            f"llm_http_{response.status_code}",
            _probe_message(response.status_code),
            retryable=False,
        )
    return int((time.perf_counter() - started) * 1000)

# ---------------------------------------------------------------- 工具感知回答

TOOL_SYSTEM_PROMPT = """你可以调用注册表里的工具核验数值：查 S 盒、读当前轨迹、现场算雪崩、读轮密钥。
规则：
1. 回答里出现的十六进制值只能来自工具结果或当前步数据；工具没给的值不要写。
2. 工具失败就说明「这次没查到」，不要改用记忆里的近似值。
3. 练习场景只给分步提示，不返回判分结果或完整答案。
4. 仍然按【结论】【为什么】【下一步】的格式输出。"""

_SENTENCE_CUT = re.compile(r"[。！？!?]\s*|\n")


class HexSanitizer:
    """输出前审计：不在白名单里的 0xNN 替换为「（未核验）」，再交给四块拼装。"""

    def __init__(self, allowed):
        self.allowed = {int(value) for value in allowed}
        self.buffer = ""
        self.replaced = 0

    def _clean(self, text):
        def replace(match):
            value = int(match.group(1), 16)
            if value in self.allowed:
                return match.group(0)
            self.replaced += 1
            return "（未核验）"

        return _HEX_VALUE.sub(replace, text)

    def feed(self, piece):
        self.buffer += piece
        chunks = []
        while True:
            match = _SENTENCE_CUT.search(self.buffer)
            if match:
                cut = match.end()
            elif len(self.buffer) >= FLUSH_AT:
                cut = FLUSH_KEEP
            else:
                cut = -1
            if cut <= 0:
                break
            chunks.append(self._clean(self.buffer[:cut]))
            self.buffer = self.buffer[cut:]
        return chunks

    def flush(self):
        if not self.buffer:
            return []
        chunk = self._clean(self.buffer)
        self.buffer = ""
        return [chunk]


FLUSH_AT = 64
FLUSH_KEEP = 40
_CHUNK = 2


def _chunks(text):
    for start in range(0, len(text), _CHUNK):
        yield text[start : start + _CHUNK]


async def _chat_collect(messages, values, timeout, tools=None):
    """一次完整收集（工具轮不逐字下发），返回 (text, tool_calls)。"""
    url = f"{values['base_url']}/chat/completions"
    body = {
        "model": values["model"],
        "messages": messages,
        "stream": True,
        "temperature": 0.3,
        "max_tokens": values["max_tokens"],
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    headers = {
        "Authorization": f"Bearer {values['api_key']}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    text_parts = []
    calls = {}
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=min(5.0, timeout))
        ) as client:
            async with client.stream("POST", url, json=body, headers=headers) as response:
                if response.status_code != 200:
                    await response.aread()
                    status = response.status_code
                    if tools and status in (400, 422):
                        raise LLMUnavailable(
                            "llm_tools_unsupported",
                            "当前模型不支持工具调用",
                            retryable=False,
                        )
                    raise LLMUnavailable(
                        f"llm_http_{status}",
                        f"模型服务返回 {status}",
                        retryable=status in (408, 429) or status >= 500,
                    )

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line.startswith("data:"):
                        continue
                    chunk = line[5:].strip()
                    if chunk == "[DONE]":
                        break
                    try:
                        payload = json.loads(chunk)
                    except json.JSONDecodeError:
                        continue
                    for choice in payload.get("choices") or []:
                        delta = choice.get("delta") or {}
                        piece = delta.get("content")
                        if piece:
                            text_parts.append(piece)
                        for call in delta.get("tool_calls") or []:
                            index = call.get("index", 0)
                            entry = calls.setdefault(
                                index, {"id": "", "name": "", "arguments": ""}
                            )
                            if call.get("id"):
                                entry["id"] = call["id"]
                            function = call.get("function") or {}
                            if function.get("name"):
                                entry["name"] += function["name"]
                            if function.get("arguments"):
                                entry["arguments"] += function["arguments"]
    except httpx.TimeoutException as error:
        raise LLMUnavailable("llm_timeout", "模型服务超时", retryable=True) from error
    except httpx.HTTPError as error:
        raise LLMUnavailable("llm_network", "连不上模型服务", retryable=True) from error

    return "".join(text_parts), [calls[key] for key in sorted(calls)]


def _emit_blocks(blocks):
    """把四块结构切成 block/token 事件；与本地模板的节奏一致。"""
    for block in blocks:
        kind = block.get("type")
        if kind == "conclusion":
            yield "block", {"type": "conclusion", "text": ""}
            for piece in _chunks(block.get("text", "")):
                yield "token", {"t": piece, "text": piece}
        elif kind == "why":
            yield "block", {"type": "why", "items": []}
            for item in block.get("items", []):
                for index, piece in enumerate(_chunks(item)):
                    payload = {"t": piece, "text": piece}
                    if index == 0:
                        payload["item"] = True
                    yield "token", payload
        elif kind == "next":
            yield "block", {"type": "next", "text": "", "action": block.get("action")}
            if block.get("text"):
                for piece in _chunks(block["text"]):
                    yield "token", {"t": piece, "text": piece}
        elif kind == "cite":
            yield "block", dict(block)


def _tool_call_payload(call):
    return {
        "name": call.get("name", ""),
        "label": agent_tools.TOOL_LABELS.get(call.get("name", ""), call.get("name", "")),
        "params": call.get("arguments", {}),
    }


def _parse_arguments(call):
    raw = call.get("arguments") or "{}"
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        raise agent_tools.ToolError("invalid_arguments", "工具参数不是合法 JSON")
    if not isinstance(parsed, dict):
        raise agent_tools.ToolError("invalid_arguments", "工具参数必须是对象")
    return parsed


async def stream_agent_answer(trace, step_index, question, override=None):
    """工具感知回答：事件与 stream_answer 同协议，额外产出 tool_start/result/end。

    无 key / 断网：意图命中的工具仍先本地执行，再用本地模板成文；
    模型不可达时由调用方按既有降级链处理。
    """
    values = config(override)
    step = trace["steps"][step_index]
    allowed = set(allowed_hex(trace, step_index, question))
    tool_results = []
    tool_events = []

    def run_tool(call):
        name = call.get("name", "")
        events = [
            ("tool_start", _tool_call_payload(call)),
        ]
        started = time.perf_counter()
        try:
            arguments = _parse_arguments(call)
            result = agent_tools.execute_tool(name, arguments)
        except agent_tools.ToolError as error:
            events.append(
                (
                    "tool_result",
                    {"name": name, "ok": False, "code": error.code, "message": error.message},
                )
            )
            events.append(
                (
                    "tool_end",
                    {"name": name, "ok": False, "elapsed_ms": int((time.perf_counter() - started) * 1000)},
                )
            )
            return events, None
        allowed.update(result["hex_values"])
        events.append(
            (
                "tool_result",
                {
                    "name": name,
                    "ok": True,
                    "summary": result["summary"],
                    "data": result["result"],
                },
            )
        )
        events.append(
            (
                "tool_end",
                {"name": name, "ok": True, "elapsed_ms": int((time.perf_counter() - started) * 1000)},
            )
        )
        return events, result

    # 练习场景：只给分步提示，直接本地成文，不调模型
    if any(hint in question for hint in agent_tools.PRACTICE_HINTS):
        for event in _emit_blocks(agent_tools.practice_blocks(question)):
            yield event
        yield "audit", {"hex_outside": [], "sanitized": 0, "tools": []}
        return

    intent = agent_tools.detect_tool_call(question, trace, step_index)
    if intent is not None:
        events, result = run_tool(intent)
        for event in events:
            yield event
        if result is not None:
            tool_results.append(result)

    if not (values["base_url"] and values["api_key"] and values["model"]):
        if not tool_results:
            raise LLMUnavailable("llm_disabled", "未配置模型", retryable=False)
        for event in _emit_blocks(
            agent_tools.build_tool_local_blocks(tool_results[-1], trace, step_index, question)
        ):
            yield event
        yield "audit", {
            "hex_outside": [],
            "sanitized": 0,
            "tools": [result["name"] for result in tool_results],
        }
        return

    messages = build_messages(trace, step_index, question)
    messages.append({"role": "system", "content": TOOL_SYSTEM_PROMPT})
    if tool_results:
        messages.append(
            {
                "role": "user",
                "content": "已核验的工具结果："
                + json.dumps(
                    [result["result"] for result in tool_results], ensure_ascii=False
                ),
            }
        )

    tools = agent_tools.tool_definitions()
    final_text = ""
    try:
        for round_index in range(2):
            try:
                text, calls = await _chat_collect(
                    messages, values, values["timeout"], tools if tools else None
                )
            except LLMUnavailable as error:
                if error.code == "llm_tools_unsupported" and tools:
                    # 能力探测失败：同一轮不带 tools 再问一次，工具结果仍在上下文里
                    tools = None
                    logger.warning("llm tools unsupported, fallback without tools")
                    text, calls = await _chat_collect(messages, values, values["timeout"], None)
                else:
                    raise

            if calls and tools and round_index == 0:
                assistant_calls = []
                for call_index, call in enumerate(calls):
                    call_id = call.get("id") or f"call_{call_index}"
                    assistant_calls.append(
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": call.get("name", ""),
                                "arguments": call.get("arguments", "{}"),
                            },
                        }
                    )
                messages.append(
                    {"role": "assistant", "content": text or None, "tool_calls": assistant_calls}
                )
                for call_index, call in enumerate(calls):
                    events, result = run_tool(call)
                    for event in events:
                        yield event
                    if result is not None:
                        tool_results.append(result)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.get("id") or f"call_{call_index}",
                            "content": json.dumps(result["result"] if result else {"ok": False}, ensure_ascii=False),
                        }
                    )
                continue

            final_text = text
            break
    except LLMUnavailable as error:
        if not tool_results:
            raise
        # 工具结果已经拿到：模型不可达也先把确定性答案给出去
        for event in _emit_blocks(
            agent_tools.build_tool_local_blocks(tool_results[-1], trace, step_index, question)
        ):
            yield event
        yield "audit", {
            "hex_outside": [],
            "sanitized": 0,
            "tools": [result["name"] for result in tool_results],
            "degraded": True,
            "degrade_reason": error.code,
        }
        return

    if not final_text.strip():
        if tool_results:
            final_text = ""
            for event in _emit_blocks(
                agent_tools.build_tool_local_blocks(tool_results[-1], trace, step_index, question)
            ):
                yield event
            yield "audit", {
                "hex_outside": [],
                "sanitized": 0,
                "tools": [result["name"] for result in tool_results],
            }
            return
        raise LLMUnavailable("llm_empty", "模型没有返回内容", retryable=False)

    assembler = BlockAssembler(step["changed"], len(step["changed"]))
    sanitizer = HexSanitizer(allowed)
    for piece in final_text:
        for chunk in sanitizer.feed(piece):
            if not assembler.started:
                for event in assembler.start():
                    yield event
            for event in assembler.feed(chunk):
                yield event
    for chunk in sanitizer.flush():
        if not assembler.started:
            for event in assembler.start():
                yield event
        for event in assembler.feed(chunk):
            yield event

    if not assembler.started:
        raise LLMUnavailable("llm_empty", "模型没有返回内容", retryable=False)

    for event in assembler.finish():
        yield event
    yield "audit", {
        "hex_outside": assembler.hex_outside(allowed),
        "sanitized": sanitizer.replaced,
        "tools": [result["name"] for result in tool_results],
    }


async def stream_agent_page_answer(page, clean, question, override=None):
    """栏目页工具版：无 trace，只能查 S 盒与现算雪崩。"""
    values = config(override)
    allowed = {
        int(value, 16)
        for value in re.findall(r"0[xX]([0-9A-Fa-f]{2})(?![0-9A-Fa-f])", question)
    }
    tool_results = []

    def run_tool(call):
        name = call.get("name", "")
        yield ("tool_start", _tool_call_payload(call))
        started = time.perf_counter()
        try:
            arguments = _parse_arguments(call)
            result = agent_tools.execute_tool(name, arguments)
        except agent_tools.ToolError as error:
            yield ("tool_result", {"name": name, "ok": False, "code": error.code, "message": error.message})
            yield ("tool_end", {"name": name, "ok": False, "elapsed_ms": int((time.perf_counter() - started) * 1000)})
            return
        allowed.update(result["hex_values"])
        yield ("tool_result", {"name": name, "ok": True, "summary": result["summary"], "data": result["result"]})
        yield ("tool_end", {"name": name, "ok": True, "elapsed_ms": int((time.perf_counter() - started) * 1000)})
        tool_results.append(result)

    if any(hint in question for hint in agent_tools.PRACTICE_HINTS):
        for event in _emit_blocks(agent_tools.practice_blocks(question)):
            yield event
        yield "audit", {"hex_outside": [], "sanitized": 0, "tools": []}
        return

    intent = agent_tools.detect_tool_call(question, None, 0)
    if intent is not None:
        call = {
            "name": intent["name"],
            "arguments": json.dumps(intent["arguments"], ensure_ascii=False),
        }
        for event in run_tool(call):
            yield event

    if not (values["base_url"] and values["api_key"] and values["model"]):
        if not tool_results:
            raise LLMUnavailable("llm_disabled", "未配置模型", retryable=False)
        for event in _emit_blocks(
            agent_tools.build_tool_local_blocks(tool_results[-1], None, 0, question)
        ):
            yield event
        yield "audit", {
            "hex_outside": [],
            "sanitized": 0,
            "tools": [result["name"] for result in tool_results],
        }
        return

    messages = build_page_messages(page, clean, question)
    messages.append({"role": "system", "content": TOOL_SYSTEM_PROMPT})
    if tool_results:
        messages.append(
            {
                "role": "user",
                "content": "已核验的工具结果："
                + json.dumps([result["result"] for result in tool_results], ensure_ascii=False),
            }
        )

    tools = agent_tools.page_tool_definitions()
    final_text = ""
    try:
        for round_index in range(2):
            try:
                text, calls = await _chat_collect(messages, values, values["timeout"], tools)
            except LLMUnavailable as error:
                if error.code == "llm_tools_unsupported":
                    tools = None
                    text, calls = await _chat_collect(messages, values, values["timeout"], None)
                else:
                    raise

            if calls and tools and round_index == 0:
                assistant_calls = []
                for call_index, call in enumerate(calls):
                    assistant_calls.append(
                        {
                            "id": call.get("id") or f"call_{call_index}",
                            "type": "function",
                            "function": {
                                "name": call.get("name", ""),
                                "arguments": call.get("arguments", "{}"),
                            },
                        }
                    )
                messages.append(
                    {"role": "assistant", "content": text or None, "tool_calls": assistant_calls}
                )
                for call_index, call in enumerate(calls):
                    for event in run_tool(call):
                        yield event
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.get("id") or f"call_{call_index}",
                            "content": json.dumps(
                                tool_results[-1]["result"] if tool_results else {"ok": False},
                                ensure_ascii=False,
                            ),
                        }
                    )
                continue

            final_text = text
            break
    except LLMUnavailable as error:
        if not tool_results:
            raise
        for event in _emit_blocks(
            agent_tools.build_tool_local_blocks(tool_results[-1], None, 0, question)
        ):
            yield event
        yield "audit", {
            "hex_outside": [],
            "sanitized": 0,
            "tools": [result["name"] for result in tool_results],
            "degraded": True,
            "degrade_reason": error.code,
        }
        return

    if not final_text.strip():
        if tool_results:
            for event in _emit_blocks(
                agent_tools.build_tool_local_blocks(tool_results[-1], None, 0, question)
            ):
                yield event
            yield "audit", {
                "hex_outside": [],
                "sanitized": 0,
                "tools": [result["name"] for result in tool_results],
            }
            return
        raise LLMUnavailable("llm_empty", "模型没有返回内容", retryable=False)

    assembler = BlockAssembler([], 0)
    sanitizer = HexSanitizer(allowed)
    for piece in final_text:
        for chunk in sanitizer.feed(piece):
            if not assembler.started:
                for event in assembler.start():
                    yield event
            for event in assembler.feed(chunk):
                yield event
    for chunk in sanitizer.flush():
        if not assembler.started:
            for event in assembler.start():
                yield event
        for event in assembler.feed(chunk):
            yield event

    if not assembler.started:
        raise LLMUnavailable("llm_empty", "模型没有返回内容", retryable=False)

    for event in assembler.finish():
        yield event
    yield "audit", {
        "hex_outside": assembler.hex_outside(allowed),
        "sanitized": sanitizer.replaced,
        "tools": [result["name"] for result in tool_results],
    }
