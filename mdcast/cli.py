"""mdcast 命令行入口。

    mdcast build 稿件.md      一键：红线扫描 → 推文串 → 口播稿+字幕（装了 playwright 再加卡片）
    mdcast thread 稿件.md     只出 X 推文串
    mdcast script 稿件.md     只出口播稿+srt 字幕
    mdcast cards  稿件.md     只出小红书卡片图
    mdcast guard  稿件.md …   红线扫描
    mdcast xpost  …           X API 发布（me/post/thread/delete）
    mdcast topics …           选题台账（add/list/next/done）
"""
import argparse
import re
import sys
from pathlib import Path

from . import cards, guard, script, subtitle, thread


def _base_of(md_path: str) -> str:
    return re.sub(r"\.md$", "", Path(md_path).name)


def cmd_build(args):
    if not Path(args.markdown).exists():
        sys.exit(f"找不到文件：{args.markdown}")
    guard.check_or_exit(args.markdown)  # 硬红线命中即中止
    text = Path(args.markdown).read_text(encoding="utf-8")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    base = _base_of(args.markdown)

    tweets = thread.md_to_thread(text)
    (out / f"{base}.thread.txt").write_text(
        "\n\n---\n\n".join(tweets), encoding="utf-8")
    print(f"① X 推文串 {len(tweets)} 条 → {out}/{base}.thread.txt")

    spoken = script.to_spoken(text)
    (out / f"{base}.script.txt").write_text(spoken, encoding="utf-8")
    (out / f"{base}.subtitle.srt").write_text(subtitle.text_to_srt(spoken), encoding="utf-8")
    print(f"② 口播稿（约 {script.minutes_of(spoken):.1f} 分钟）+ 字幕 → "
          f"{out}/{base}.script.txt / .subtitle.srt")

    try:
        cards.render(args.markdown, str(out / f"cards_{base}"))
    except ImportError:
        print("③ 跳过卡片（未装 playwright）：pip install 'mdcast[cards]' && playwright install chromium")
    print("完成。发布建议：先发 X 攒反馈，数据好的选题再做成视频。")


def cmd_thread(args):
    thread.main([args.markdown, "-o", str(Path(args.out) / f"{_base_of(args.markdown)}.thread.txt")]
                if args.out else [args.markdown])


def cmd_script(args):
    text = Path(args.markdown).read_text(encoding="utf-8")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    base = _base_of(args.markdown)
    spoken = script.to_spoken(text)
    (out / f"{base}.script.txt").write_text(spoken, encoding="utf-8")
    (out / f"{base}.subtitle.srt").write_text(subtitle.text_to_srt(spoken), encoding="utf-8")
    print(f"口播稿（约 {script.minutes_of(spoken):.1f} 分钟）→ {out}/{base}.script.txt")
    print(f"字幕文件 → {out}/{base}.subtitle.srt")


def main():
    ap = argparse.ArgumentParser(
        prog="mdcast",
        description="一篇 Markdown，多平台内容一键生成（X 推文串 / 口播稿+srt / 小红书卡片）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("build", help="一键产出全套（先过红线扫描）")
    p.add_argument("markdown")
    p.add_argument("-o", "--out", default="out")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("thread", help="只出 X 推文串")
    p.add_argument("markdown")
    p.add_argument("-o", "--out", default="out")
    p.set_defaults(func=cmd_thread)

    p = sub.add_parser("script", help="只出口播稿 + srt 字幕")
    p.add_argument("markdown")
    p.add_argument("-o", "--out", default="out")
    p.set_defaults(func=cmd_script)

    p = sub.add_parser("cards", help="只出小红书卡片图")
    p.add_argument("markdown")
    p.add_argument("-o", "--out", default="cards_out")
    p.set_defaults(func=lambda a: cards.main([a.markdown, "-o", a.out]))

    p = sub.add_parser("guard", help="红线扫描（硬命中 exit 1）")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p.set_defaults(func=lambda a: guard.main(a.args))

    p = sub.add_parser("xpost", help="X API 发布：me / post 文本 / thread 文件 / delete id")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p.set_defaults(func=lambda a: _xpost(a.args))

    p = sub.add_parser("topics", help="选题台账：add/list/next/done")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p.set_defaults(func=lambda a: _topics(a.args))

    args = ap.parse_args()
    args.func(args)


def _xpost(argv):
    from . import xpost
    xpost.main(argv)


def _topics(argv):
    from . import topics
    topics.main(argv)


if __name__ == "__main__":
    main()
