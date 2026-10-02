"""口播稿 → srt 字幕文件：按标点切成字幕条，时长按语速估算。

导入剪映/CapCut 后自动对轴，只需微调。语速在 config.CHARS_PER_SECOND。
"""
import re

from . import config


def text_to_srt(text: str) -> str:
    sentences = re.findall(r".*?(?:[。！？；，、!?…]|$)", text)
    cues, start = [], 0.0
    idx = 1
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        # 过长的句子按 18 字硬切
        chunks = [s[i:i + 18] for i in range(0, len(s), 18)] if len(s) > 18 else [s]
        for c in chunks:
            dur = len(c) / config.CHARS_PER_SECOND + 0.15
            end = start + dur
            cues.append((idx, start, end, c))
            start = end + 0.06  # 条间小停顿
            idx += 1

    def fmt(t: float) -> str:
        ms = int(round(t * 1000))
        h, ms = divmod(ms, 3600000)
        m, ms = divmod(ms, 60000)
        s2, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{s2:02d},{ms:03d}"

    return "\n".join(
        f"{i}\n{fmt(a)} --> {fmt(b)}\n{c}\n" for i, a, b, c in cues
    )
