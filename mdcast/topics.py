"""topics —— 选题台账：把素材矿变成可开采的选题清单。

用法：
    mdcast topics add "选题名" --src "日记 p.213" --theory "拉康/欲望" --form all --due 2026-10-08
    mdcast topics list            # 全部
    mdcast topics next            # 看下一步该做什么（按 due 排序的待办）
    mdcast topics done <id>       # 标记完成

台账存当前目录 topics.json（已在 .gitignore 里），字段：
    title 选题名 | src 素材来源 | theory 涉及理论 | form 适用形态
    (thread/script/cards/all) | due 计划发布日 | status: todo/done
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

DB = Path.cwd() / "topics.json"


def load() -> list[dict]:
    if DB.exists():
        return json.loads(DB.read_text(encoding="utf-8"))
    return []


def save(items: list[dict]):
    DB.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    ap = argparse.ArgumentParser(prog="mdcast topics")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_add = sub.add_parser("add")
    p_add.add_argument("title")
    p_add.add_argument("--src", default="")
    p_add.add_argument("--theory", default="")
    p_add.add_argument("--form", default="all", choices=["thread", "script", "cards", "all"])
    p_add.add_argument("--due", default=str(date.today()))
    p_done = sub.add_parser("done")
    p_done.add_argument("id", type=int)
    sub.add_parser("list")
    sub.add_parser("next")
    a = ap.parse_args(argv)

    items = load()
    if a.cmd == "add":
        items.append({"id": (max([x["id"] for x in items], default=0) + 1),
                      "title": a.title, "src": a.src, "theory": a.theory,
                      "form": a.form, "due": a.due, "status": "todo"})
        save(items)
        print(f"已登记 #{items[-1]['id']}：{a.title}")
    elif a.cmd == "list":
        for x in items:
            mark = "✅" if x["status"] == "done" else "⬜"
            print(f"{mark} #{x['id']} [{x['due']}] {x['title']}  ({x['form']}|{x['theory']}|{x['src']})")
    elif a.cmd == "next":
        todo = sorted((x for x in items if x["status"] == "todo"), key=lambda x: x["due"])
        if not todo:
            print("台账已清空。")
        for x in todo[:10]:
            print(f"⬜ #{x['id']} [{x['due']}] {x['title']}")
    elif a.cmd == "done":
        for x in items:
            if x["id"] == a.id:
                x["status"] = "done"
                save(items)
                print(f"#{a.id} 已完成：{x['title']}")
                return
        print(f"找不到 #{a.id}", file=sys.stderr)


if __name__ == "__main__":
    main()
