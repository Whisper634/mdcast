# mdcast

一篇 Markdown 定稿，一条命令产出多平台内容：**X 推文串 / 口播稿 + srt 字幕 / 小红书卡片图**。

适合认真写长文、但要给每个平台喂不同形态的中文创作者：内容的核心资产是一篇 markdown，剩下的重复劳动交给工具。

## 特点

- **零依赖核心**：纯 Python 标准库，clone 即用；卡片渲染是唯一的可选依赖（playwright）
- **LLM 是增强不是依赖**：配了 OpenAI 兼容 API（Kimi/DeepSeek/任何兼容服务），口播稿由 LLM 从书面稿改写；不配则规则降级照跑
- **红线前置**：`build` 生成任何产物前先扫描红线词表（真实姓名/学校等），硬命中即中止
- **产物是半成品**：推文串复制即发、srt 导入剪映自动对轴、卡片挑一张就能当封面——工具替代重复劳动，判断留给人
- 附赠 **xpost**：纯标准库实现的 X API 发布（OAuth 1.0a），发推文串不用装任何 SDK

## 安装

```bash
git clone https://github.com/<you>/mdcast.git
cd mdcast
pip install -e .                    # 核心零依赖
pip install -e '.[cards]'           # 要出小红书卡片再装这个
playwright install chromium
```

也可以不安装，直接用 `python3 -m mdcast ...`（仓库根目录下）。

## 配置（可选但建议）

复制 `.env.example` 为 `.env`：

```
MDCAST_API_KEY=你的密钥              # platform.moonshot.cn 或任何 OpenAI 兼容服务
MDCAST_BASE_URL=https://api.moonshot.cn/v1
MDCAST_MODEL=kimi-k2.6
```

卡片文案和红线词表也都走环境变量，见 `.env.example`。

> 用 Kimi API 的话先看 [docs/notes-kimi.md](docs/notes-kimi.md)——里面是我们实测踩出来的坑（模型选择、超时、temperature 限制），能省几个小时。

## 用法

```bash
mdcast build 稿件.md        # 一键：红线扫描 → 推文串 → 口播稿+srt → 卡片图
mdcast thread 稿件.md       # 只出 X 推文串（CJK 计权断推、自动编号）
mdcast script 稿件.md       # 只出口播稿 + srt 字幕
mdcast cards  稿件.md       # 只出小红书卡片图
mdcast guard  稿件.md       # 红线扫描（也可 --words 指定自己的词表）
mdcast xpost me             # X 发布：me 验证 / post 单条 / thread 串 / delete 删除
mdcast topics next          # 选题台账：add / list / next / done
```

产物在 `out/`：

| 文件 | 用途 |
|---|---|
| `稿名.thread.txt` | X 推文串，编号 1/ 2/ …，以 `---` 分段 |
| `稿名.script.txt` | 口播稿，录音时照着念 |
| `稿名.subtitle.srt` | 字幕，导入剪映/CapCut 自动对轴后微调 |
| `cards_稿名/*.png` | 小红书卡片：cover 封面 + page01.. 内页 + end 结尾 |

## 自定义

- 卡片样式：改 `mdcast/data/card.html`（配色、字号、版式全在里面）
- 推文长度、卡片尺寸、语速：改 `mdcast/config.py` 顶部的常量
- 红线词表：复制 `mdcast/data/guard_words.example.txt` 改成自己的，用 `MDCAST_GUARD_WORDS` 指向它

## 工作流建议

1. 长文定稿（markdown）
2. `mdcast build 稿件.md`
3. 先发 X 攒反馈，数据好的选题再做成短视频（口播稿+srt 就是干这个的）和小红书图文

## 明确不做

- 不自动发布国内平台（抖音/B站/小红书）——风控强、合规风险高，前 N 条本来就该手动发
- 不做 GUI / 账号托管 /「全自动起号」

## License

MIT
