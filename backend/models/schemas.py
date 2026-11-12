from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TraceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plaintext_hex: str = Field(min_length=32, max_length=32)
    key_hex: str = Field(min_length=32, max_length=64)
    key_bits: Literal[128, 192, 256]
    direction: Literal["encrypt", "decrypt"] = "encrypt"


class TraceStep(BaseModel):
    index: int
    round: int
    op: Literal["add_round_key", "sub_bytes", "shift_rows", "mix_columns"]
    state_before: list[int]
    state_after: list[int]
    changed: list[int]
    key_indices: list[int]
    key_words: list[int]
    label: str


class TraceResponse(BaseModel):
    trace_id: str
    # 加密=密文，解密=明文；ciphertext 是历史字段，值与 output 相同
    output: str = ""
    ciphertext: str
    key_bits: int
    direction: str
    rounds: int
    step_count: int
    key_schedule: list[list[int]]
    steps: list[TraceStep]
    meta: dict[str, str]

class TutorRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(min_length=1)
    step_index: int = Field(ge=0)
    question: str = Field(min_length=1, max_length=500)
    client: dict | None = None

class QuizRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str = Field(min_length=1)
    answer_hex: str = Field(min_length=32, max_length=32)
    plaintext_hex: str = Field(min_length=32, max_length=32)
    key_hex: str = Field(min_length=32, max_length=64)
    key_bits: Literal[128, 192, 256]


class EventItem(BaseModel):
    type: str = Field(min_length=1, max_length=32)
    step_index: int | None = None
    at: int | None = None
    dwell_ms: int | None = None
    payload: dict | None = None


class EventsRequest(BaseModel):
    # session_id 保留兼容旧调用（不落库：现在按 client_id 归属）
    session_id: str | None = None
    items: list[EventItem] = Field(min_length=1, max_length=200)

class AvalancheRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plaintext_hex: str = Field(min_length=32, max_length=32)
    key_hex: str = Field(min_length=32, max_length=64)
    # 改哪一块输入：明文（默认）或密钥
    target: Literal["plaintext", "key"] = "plaintext"
    byte_index: int = Field(default=0, ge=0, le=31)
    # 翻第几位：0 = 最低位（0x00 → 0x01），7 = 最高位
    bit_index: int = Field(default=0, ge=0, le=7)


class AvalancheSweepRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plaintext_hex: str = Field(min_length=32, max_length=32)
    key_hex: str = Field(min_length=32, max_length=64)
    target: Literal["plaintext", "key"] = "plaintext"
    bit_index: int = Field(default=0, ge=0, le=7)


class CipherSide(BaseModel):
    cipher_hex: str
    cells: list[int]


class AvalancheResponse(BaseModel):
    target: str
    byte_index: int
    bit_index: int
    key_bits: int
    input_before_hex: str
    input_after_hex: str
    input_byte_before: int
    input_byte_after: int
    before: CipherSide
    after: CipherSide
    changed_bits: int
    changed_bytes: int
    total_bits: int
    total_bytes: int
    ideal_bits: int
    rate: float
    # 128 个位，按十六进制顺序：字节 0 的 bit7 → bit0，再字节 1……
    bit_flags: list[bool]
    # 每个密文字节各变了几位（0–8），前端用来给格子分色阶
    byte_bits: list[int]


class SweepSample(BaseModel):
    byte_index: int
    byte_before: int
    byte_after: int
    changed_bits: int


class AvalancheSweepResponse(BaseModel):
    target: str
    bit_index: int
    key_bits: int
    trials: int
    total_bits: int
    ideal_bits: int
    mean: float
    min_bits: int
    max_bits: int
    samples: list[SweepSample]


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
