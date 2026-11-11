"""练习题题库：题目定义只此一份。

前端不再内置题库（改由 `/api/quiz/items` 提供），正确答案也不写死在这里 ——
灌库时用当前引擎现算，所以「题库里的答案」和「引擎算出来的答案」不可能对不上。
题目 id 沿用 q_042…q_049：深链 `?item=q_046` 与既有 e2e 用例都靠它定位。
"""

QUIZ_BANK = (
    {
        "code": "q_042",
        "difficulty": "entry",
        "tag": "key_timing",
        "question": "轮密钥专项：使用给定明文与密钥，完成 AES-128 加密，填入 32 位十六进制密文。",
        "plaintext_hex": "00112233445566778899aabbccddeeff",
        "key_hex": "000102030405060708090a0b0c0d0e0f",
        "key_bits": 128,
        "explanation": "第 0 步就用 w[0..3]，之后每轮换下一组；错一位密钥第 1 轮就整块偏。",
    },
    {
        "code": "q_043",
        "difficulty": "basic",
        "tag": "mix_coefficient",
        "question": "列混合专项：使用给定明文与密钥，完成 AES-128 加密，填入 32 位十六进制密文。",
        "plaintext_hex": "3243f6a8885a308d313198a2e0370734",
        "key_hex": "2b7e151628aed2a6abf7158809cf4f3c",
        "key_bits": 128,
        "explanation": "列混合的系数是 2/3/1/1，乘 2 溢出要按 0x11B 约简，别用普通乘法。",
    },
    {
        "code": "q_044",
        "difficulty": "basic",
        "tag": None,
        "question": "使用给定明文与密钥，完成 AES-192 加密，填入 32 位十六进制密文。",
        "plaintext_hex": "00112233445566778899aabbccddeeff",
        "key_hex": "000102030405060708090a0b0c0d0e0f1011121314151617",
        "key_bits": 192,
        "explanation": "192 位是 12 轮，比 128 位多两轮；轮密钥共 52 个字。",
    },
    {
        "code": "q_045",
        "difficulty": "advanced",
        "tag": "mix_coefficient",
        "question": "列混合专项：使用给定明文与密钥，完成 AES-192 加密，填入 32 位十六进制密文。",
        "plaintext_hex": "3243f6a8885a308d313198a2e0370734",
        "key_hex": "8e73b0f7da0e6452c810f32b809079e562f8ead2522c6b7b",
        "key_bits": 192,
        "explanation": "末轮没有列混合，最后一步只做轮密钥加，别多算一次。",
    },
    {
        "code": "q_046",
        "difficulty": "challenge",
        "tag": "key_timing",
        "question": "轮密钥专项：使用给定明文与密钥，完成 AES-256 加密，填入 32 位十六进制密文。",
        "plaintext_hex": "00112233445566778899aabbccddeeff",
        "key_hex": (
            "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
        ),
        "key_bits": 256,
        "explanation": "256 位密钥 8 个字，前 8 组轮密钥直接来自输入，之后才做扩展。",
    },
    {
        "code": "q_047",
        "difficulty": "challenge",
        "tag": None,
        "question": "使用给定明文与密钥，完成 AES-256 加密，填入 32 位十六进制密文。",
        "plaintext_hex": "3243f6a8885a308d313198a2e0370734",
        "key_hex": (
            "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
        ),
        "key_bits": 256,
        "explanation": "14 轮里第 7 个字的扩展要额外做一次 SubWord，这是 256 位独有的。",
    },
    {
        "code": "q_048",
        "difficulty": "entry",
        "tag": "mix_coefficient",
        "question": "列混合专项：使用给定明文与密钥，完成 AES-128 加密，填入 32 位十六进制密文。",
        "plaintext_hex": "00112233445566778899aabbccddeeff",
        "key_hex": "2b7e151628aed2a6abf7158809cf4f3c",
        "key_bits": 128,
        "explanation": "FIPS-197 附录 B 的示例：第 1 轮列混合后应看到 58 4d ca f1… 这组数。",
    },
    {
        "code": "q_049",
        "difficulty": "advanced",
        "tag": None,
        "question": "使用给定明文与密钥，完成 AES-256 加密，填入 32 位十六进制密文。",
        "plaintext_hex": "ffeeddccbbaa99887766554433221100",
        "key_hex": (
            "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
        ),
        "key_bits": 256,
        "explanation": "明文是上一题的字节倒序，密文却完全不相关 —— 雪崩效应的直观例子。",
    },
)
