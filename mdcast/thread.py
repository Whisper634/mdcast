"""markdown 定稿 → X 推文串（thread）。

断推原则：
- 按段落打包，尽量不打断段落；
- 单段超长时按句子边界切，句子还长再退到逗号；
- 每条末尾如果是半句话，自动补 "…" 表示未完，最后一条不补；
- 编号 "1/" "2/" … 便于读者知道进度。

X 计权规则：CJK 统一计 2，其余计 1。
"""
import re
import sys
from pathlib import Path

from .config import TWEET_WEIGHT_LIMIT, MAX_TWEETS_PER_THREAD


def char_weight(ch: str) -> int:
    return 2 if ord(ch) > 0x2E7F else 1


def text_weight(s: str) -> int:
    return sum(char_weight(c) for c in s)


def strip_md(md: str) -> str:
    s = re.sub(r"```.*?```", " ", md, flags=re.S)
    s = re.sub(r"`([^`]*)`", r"\1", s)
    s = re.sub(r"!\[.*?\]\(.*?\)", "", s)
    s = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", s)
    s = re.sub(r"^#{1,6}\s*", "", s, flags=re.M)
    s = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", s)
    s = re.sub(r"^\s*[-*+]\s+", "", s, flags=re.M)
    s = re.sub(r"^\s*\d+[.、]\s+", "", s, flags=re.M)
    s = re.sub(r"^>\s?", "", s, flags=re.M)
    s = re.sub(r"\n{2,}", "\n", s)
    return s.strip()


SENT_END = "。！？；!?;…"


def split_long_text(text: str) -> list[str]:
    """把超重的文本切成句子和逗号级别的碎片。"""
    parts = re.findall(r".*?(?:[" + SENT_END + r"]|$)", text)
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if text_weight(p) <= TWEET_WEIGHT_LIMIT:
            out.append(p)
        else:
            sub = re.findall(r".*?(?:，|,|：|:|$)", p)
            out.extend(x.strip() for x in sub if x.strip())
    return out


def pack_thread(plain: str) -> list[str]:
    """把纯文本打包成推文列表。"""
    paragraphs = [p.strip() for p in plain.split("\n") if p.strip()]
    fragments: list[str] = []
    for para in paragraphs:
        if text_weight(para) <= TWEET_WEIGHT_LIMIT:
            fragments.append(para)
        else:
            fragments.extend(split_long_text(para))

    tweets, buf, buf_w = [], "", 0
    for frag in fragments:
        w = text_weight(frag)
        need = w if not buf else w + 1  # 段间空行算 1
        if buf and buf_w + need > TWEET_WEIGHT_LIMIT:
            tweets.append(buf)
            buf, buf_w = frag, w
        else:
            buf = buf + "\n\n" + frag if buf else frag
            buf_w += need
    if buf:
        tweets.append(buf)

    total = len(tweets)
    numbered = []
    for i, t in enumerate(tweets, 1):
        if i < total and not t.endswith(tuple(SENT_END)):
            t += "…"
        numbered.append(f"{i}/{total}  {t}")
    return numbered


def md_to_thread(md_text: str) -> list[str]:
    return pack_thread(strip_md(md_text))


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("用法: mdcast thread 稿件.md [-o 输出.txt]（缺省打印到屏幕）")
        sys.exit(1)
    out_path = None
    args = list(argv)
    if "-o" in args:
        i = args.index("-o")
        out_path = args[i + 1]
        del args[i:i + 2]
    md = open(args[0], encoding="utf-8").read()
    tweets = md_to_thread(md)
    if len(tweets) > MAX_TWEETS_PER_THREAD:
        print(f"⚠️ 共 {len(tweets)} 条，超过 X 单串上限 {MAX_TWEETS_PER_THREAD}，建议拆成两篇发。",
              file=sys.stderr)
    out = "\n\n---\n\n".join(tweets)
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        open(out_path, "w", encoding="utf-8").write(out)
        print(f"已写出 {len(tweets)} 条推文 → {out_path}")
    else:
        print(out)


if __name__ == "__main__":
    main()
