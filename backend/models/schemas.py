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
    ciphertext: str
    key_bits: int
    direction: str
    rounds: int
    step_count: int
    key_schedule: list[list[int]]
    steps: list[TraceStep]
    meta: dict[str, str]