"""统一配置：环境变量 > 当前目录 .env。

LLM（OpenAI 兼容接口，Kimi/DeepSeek/Moonshot 皆可）：
    MDCAST_API_KEY / MDCAST_BASE_URL / MDCAST_MODEL
    MDCAST_TEMPERATURE   默认 1.0——Moonshot 当前模型实测只接受 1.0，传其他值会 400
    MDCAST_LLM_TIMEOUT   秒，默认 180（长文改写要给足时间）

卡片文案自定义：
    MDCAST_CARD_KICKER / MDCAST_CARD_END_TITLE / MDCAST_CARD_END_SUB / MDCAST_CARD_FOOTER

红线词表：
    MDCAST_GUARD_WORDS   词表文件路径（默认包内示例，务必换成自己的）
"""
import os
from pathlib import Path


def _load_dotenv():
    p = Path.cwd() / ".env"
    if not p.exists():
        return
    for ln in p.read_text(encoding="utf-8").split("\n"):
        ln = ln.strip()
        if ln and not ln.startswith("#") and "=" in ln:
            k, v = ln.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip("'\""))


_load_dotenv()

API_KEY = os.getenv("MDCAST_API_KEY", "")
BASE_URL = os.getenv("MDCAST_BASE_URL", "")
MODEL = os.getenv("MDCAST_MODEL", "")
TEMPERATURE = float(os.getenv("MDCAST_TEMPERATURE", "1.0"))
LLM_TIMEOUT = int(os.getenv("MDCAST_LLM_TIMEOUT", "180"))

# X 推文：CJK 字符按 2 计重，上限留余量给编号 "n/"
TWEET_WEIGHT_LIMIT = 250
MAX_TWEETS_PER_THREAD = 25

# 小红书卡片：3:4 竖版
CARD_W, CARD_H = 1242, 1660
CARD_MAX_CHARS = 110
CARD_KICKER = os.getenv("MDCAST_CARD_KICKER", "读书笔记")
CARD_END_TITLE = os.getenv("MDCAST_CARD_END_TITLE", "你在想什么？")
CARD_END_SUB = os.getenv("MDCAST_CARD_END_SUB", "评论区聊聊你的看法")
CARD_FOOTER = os.getenv("MDCAST_CARD_FOOTER", "")

GUARD_WORDS = os.getenv(
    "MDCAST_GUARD_WORDS",
    str(Path(__file__).parent / "data" / "guard_words.example.txt"))

# 口播语速：每秒约 4.5 个汉字（偏慢，清晰向）
CHARS_PER_SECOND = 4.5
