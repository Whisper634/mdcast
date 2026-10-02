"""markdown 定稿 → 小红书卡片图（封面 + 内页 + 结尾页）。

封面取第一个标题，hook 取第一段前 40 字；
内页按自然段分页，每页超过 CARD_MAX_CHARS 自动按句子折页；
结尾页文案由 config（MDCAST_CARD_*）自定义。

样式：改包内 data/card.html（配色、字号、页脚都在里面）。

依赖：playwright（pip install 'mdcast[cards]' && playwright install chromium）。
"""
import re
import sys
from pathlib import Path

from . import config

TEMPLATE = (Path(__file__).parent / "data" / "card.html").read_text(encoding="utf-8")


def strip_inline_md(s: str) -> str:
    s = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", s)
    s = re.sub(r"\*([^*]+)\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`([^`]*)`", r"\1", s)
    return s.strip()


def parse(md: str):
    lines = md.split("\n")
    title, paras, cur = None, [], []
    for ln in lines:
        if ln.startswith("# ") and title is None:
            title = ln.lstrip("# ").strip()
            continue
        if not ln.strip():
            if cur:
                paras.append(" ".join(cur))
                cur = []
        else:
            cur.append(ln.strip())
    if cur:
        paras.append(" ".join(cur))
    return title or "未命名", paras


def paginate(text: str, limit: int) -> list[str]:
    """每页不超过 limit 字；按句子打包，单句超长硬切。"""
    if len(text) <= limit:
        return [text]
    sentences = re.findall(r".*?(?:[。！？；，、]|$)", text)
    pages, buf = [], ""
    for s in sentences:
        if not s.strip():
            continue
        if len(s) > limit:
            if buf:
                pages.append(buf); buf = ""
            pages.extend(s[i:i + limit] for i in range(0, len(s), limit))
        elif len(buf + s) <= limit:
            buf += s
        else:
            pages.append(buf); buf = s
    if buf:
        pages.append(buf)
    return pages


def build_html(title: str, paras: list[str]) -> str:
    cards = []
    hook_src = re.sub(r"<[^>]+>", "", strip_inline_md(paras[0] if paras else ""))
    cut = max(hook_src.rfind(p, 0, 42) for p in "。！？；，")
    hook = hook_src[: cut + 1] if cut > 0 else hook_src[:40]
    cards.append(
        f'<div class="card cover"><div><div class="kicker">{config.CARD_KICKER}</div>'
        f"<h1>{strip_inline_md(title)}</h1>"
        f'<div class="hook">{hook}</div></div></div>'
    )
    n = 0
    for p in paras:
        for page in paginate(strip_inline_md(p), config.CARD_MAX_CHARS):
            n += 1
            cards.append(
                f'<div class="card page"><div class="body">{page}</div>'
                f'<div class="foot"><span>{strip_inline_md(title)[:14]}</span>'
                f'<span>{config.CARD_FOOTER}</span></div>'
                f'<div class="pgnum">{n}</div></div>'
            )
    end_sub = config.CARD_END_SUB + (f"<br>{config.CARD_FOOTER}" if config.CARD_FOOTER else "")
    cards.append(
        f'<div class="card end"><div><h2>{config.CARD_END_TITLE}</h2>'
        f"<p>{end_sub}</p></div></div>"
    )
    return TEMPLATE.replace("{{W}}", str(config.CARD_W)).replace(
        "{{H}}", str(config.CARD_H)).replace("{{CARDS}}", "\n".join(cards))


def render(md_path: str, out_dir: str):
    from playwright.sync_api import sync_playwright

    title, paras = parse(open(md_path, encoding="utf-8").read())
    html = build_html(title, paras)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tmp = (out / "_render.html").resolve()
    tmp.write_text(html, encoding="utf-8")

    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()  # playwright install chromium 后走这里
        except Exception:
            try:
                browser = pw.chromium.launch(channel="chrome")  # 系统已装 Chrome 的兜底
            except Exception:
                browser = pw.chromium.launch(executable_path="/usr/bin/chromium")  # Linux 兜底
        page = browser.new_page(viewport={"width": config.CARD_W, "height": config.CARD_H})
        page.goto(tmp.as_uri())
        cards = page.locator(".card")
        count = cards.count()
        names = ["cover"] + [f"page{i:02d}" for i in range(1, count - 1)] + ["end"]
        for i in range(count):
            cards.nth(i).screenshot(path=str(out / f"{names[i]}.png"))
        browser.close()
    tmp.unlink()
    print(f"已生成 {count} 张卡片 → {out}/（封面 cover.png + 内页 page*.png + 结尾 end.png）")


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("用法: mdcast cards 稿件.md [-o 输出目录]")
        sys.exit(1)
    out_dir = "cards_out"
    args = list(argv)
    if "-o" in args:
        i = args.index("-o")
        out_dir = args[i + 1]
        del args[i:i + 2]
    render(args[0], out_dir)


if __name__ == "__main__":
    main()
