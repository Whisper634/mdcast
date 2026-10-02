"""guard —— 出街前红线扫描。

用法：
    mdcast guard 稿件.md [更多.md ...] [--words 词表路径]   # 硬命中 exit 1
    build 命令内部调用 check_or_exit()                       # 生成产物前自动先扫

词表格式（见包内 data/guard_words.example.txt）：
@hard 段 = 真实姓名/学校/公司/地名等，命中即拒；
@warn 段 = 笔名/代称等身份词，打印警示放行（人工确认灰区）。
词表路径：MDCAST_GUARD_WORDS 环境变量，或 --words 参数，默认用包内示例。
"""
import sys
from pathlib import Path

from . import config


def load_words(path: str | None = None):
    words_file = Path(path or config.GUARD_WORDS)
    hard, warn, section = [], [], "hard"
    for ln in words_file.read_text(encoding="utf-8").split("\n"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        if ln == "@hard":
            section = "hard"
            continue
        if ln == "@warn":
            section = "warn"
            continue
        (hard if section == "hard" else warn).append(ln)
    return hard, warn


def scan(path: str, words_path: str | None = None):
    """返回 (hard_hits, warn_hits)，每个 hit = (行号, 词, 该行截断)。"""
    hard, warn = load_words(words_path)
    text = Path(path).read_text(encoding="utf-8")
    hard_hits, warn_hits = [], []
    for i, line in enumerate(text.split("\n"), 1):
        for w in hard:
            if w in line:
                hard_hits.append((i, w, line.strip()[:60]))
        for w in warn:
            if w in line:
                warn_hits.append((i, w, line.strip()[:60]))
    return hard_hits, warn_hits


def check_or_exit(path: str):
    """build 用：硬红线命中则打印并退出；警告级打印后放行。"""
    hard_hits, warn_hits = scan(path)
    if warn_hits:
        print("⚠️  身份词警示（确认不含可识别细节）：")
        for i, w, ctx in warn_hits[:10]:
            print(f"    第{i}行 [{w}] {ctx}")
    if hard_hits:
        print("🚫 命中硬红线，已中止：")
        for i, w, ctx in hard_hits[:10]:
            print(f"    第{i}行 [{w}] {ctx}")
        print(f"    共 {len(hard_hits)} 处。改稿或调整词表后重试。")
        sys.exit(1)


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    words_path = None
    args = list(argv)
    if "--words" in args:
        i = args.index("--words")
        words_path = args[i + 1]
        del args[i:i + 2]
    if not args:
        print("用法: mdcast guard 稿件.md [更多.md ...] [--words 词表路径]")
        sys.exit(1)
    bad = False
    for p in args:
        hard_hits, warn_hits = scan(p, words_path)
        print(f"— {p}")
        if warn_hits:
            print(f"  ⚠️ 警告 {len(warn_hits)} 处: " + ", ".join(f"第{i}行[{w}]" for i, w, _ in warn_hits[:8]))
        if hard_hits:
            bad = True
            print(f"  🚫 硬红线 {len(hard_hits)} 处: " + ", ".join(f"第{i}行[{w}]" for i, w, _ in hard_hits[:8]))
        if not warn_hits and not hard_hits:
            print("  ✅ 干净")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
