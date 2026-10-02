"""markdown 定稿 → 口播稿。

优先路径：配了 LLM 时把书面稿改写成适合念出来的口播稿
（口语化、短句、保留理论专有名词不动、不新增观点）。
未配 LLM：退回规则版，直接用去 markdown 的原文——能跑，但念出来会偏书面。

输出（由 cli 落盘）：
    稿名.script.txt   口播稿（录音时照着念）
    稿名.subtitle.srt 字幕文件（导入剪映/CapCut 自动对轴）
"""
import re

from . import llm
from .thread import strip_md

LLM_PROMPT = """把下面这篇书面稿改写成口播稿。要求：
1. 短句为主，每句不超过 25 字，念起来顺口；
2. 保留所有理论专有名词和引用，不得新增观点、不得改变原意；
3. 全文控制在 {budget} 字以内；
4. 不要小标题、不要列表符号、不要 markdown 标记；
5. 开头 5 秒内必须出现核心问题钩子；
6. 只输出口播稿正文，不要任何解释。

【书面稿】
{draft}"""


def llm_rewrite(md: str) -> str | None:
    # 预算：按原文 0.8 倍估，给口语冗余留量
    budget = max(400, int(len(re.sub(r"\s", "", md)) * 0.8))
    return llm.chat(LLM_PROMPT.format(budget=budget, draft=md))


def rule_fallback(md: str) -> str:
    s = strip_md(md)
    # 去掉小标题行（短且没有句末标点的行），避免念出目录句
    kept = [ln for ln in s.split("\n")
            if not (len(ln.strip()) <= 14 and not re.search(r"[。！？；，、!?…]$", ln.strip()))]
    s = "\n".join(kept)
    s = re.sub(r"\n{2,}", "。", s)
    return s.replace("\n", "，")


def to_spoken(md: str) -> str:
    spoken = llm_rewrite(md) or rule_fallback(md)
    return re.sub(r"([。！？；…])[,，]", r"\1", spoken)  # 清理句号后多余的逗号


def minutes_of(spoken: str) -> float:
    return len(re.sub(r"\s", "", spoken)) / 270
