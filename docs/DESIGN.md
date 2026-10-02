# mdcast 设计思路

> 面向未来的协作者和未来的自己。读完这份再看代码。

## 一、定位

**「一文多发」命令行工具**：一篇 Markdown 定稿 → X 推文串 + 口播稿/srt 字幕 + 小红书卡片图。

目标用户：中文创作者（读书博主、知识区 up、 Newsletter 作者）——内容的核心资产是一篇认真写好的长文，但每个平台要吃不同形态。mdcast 把「形态转换」这一步自动化，人只做选题和定稿。

## 二、设计原则

1. **本地优先**：所有东西在本地跑完，产物是文件（txt/srt/png），发布动作永远留给人或显式命令。密钥只走环境变量/`.env`，不进代码、不进产物。
2. **LLM 是增强，不是依赖**：配了 OpenAI 兼容 API（Kimi/DeepSeek/Moonshot…），口播稿由 LLM 从书面稿改写；不配则规则降级照跑。核心功能零第三方依赖（纯标准库）。
3. **每个产物独立命令，也有一键入口**：`mdcast thread/script/cards/guard` 可单独跑，`mdcast build` 一键全出。
4. **红线前置**：`build` 在生成任何产物前先过 `guard` 红线扫描，硬命中即中止。
5. **产物是半成品，这是特性不是缺陷**：推文串要人审一眼再发；srt 导入剪映/CapCut 自动对轴后微调；卡片要人挑封面。工具替代的是重复劳动，不是判断力。

## 三、架构

```
mdcast 命令 (cli.py)
 ├── guard.py     红线扫描（词表可自定义，默认示例词表）
 ├── thread.py    Markdown → X 推文串（CJK 计权、断推、编号）
 ├── script.py    Markdown → 口播稿（LLM 改写 or 规则版）
 ├── subtitle.py  口播稿 → srt（按语速估算时长）
 ├── cards.py     Markdown → 小红书卡片图（playwright 渲染 HTML 模板截图）
 ├── xpost.py     X API 发布（OAuth 1.0a，纯标准库实现）
 ├── topics.py    选题台账（本地 JSON）
 └── llm.py       OpenAI 兼容客户端（urllib，无 SDK）
```

- 配置集中在 `config.py`：环境变量 > 当前目录 `.env`。
- 卡片样式在 `mdcast/data/card.html`，可整体替换。
- 台账（topics.json）、`.env`、`x_api.env` 都认**当前工作目录**，工具装到哪都能在自己项目里用。

## 四、公开边界（什么不进仓库）

- 不含任何个人素材、日记、批注、选矿结果。
- 不含个人红线词表——`guard_words.example.txt` 是占位示例，使用者复制改成自己的。
- 卡片结尾引导语文案通过环境变量配置，默认是中性文案。
- `mine.py`（个人档案选矿器）不进公开版：解析格式和词表都太私人。有通用化思路后再说。

## 五、明确不做

- **不自动发布国内平台**（抖音/B站/小红书）：风控强、合规风险高，前 N 条本来就该手动发。
- 不做 GUI、不做账号托管、不做「AI 全自动起号」——这个工具的立场是辅助认真做内容的人。

## 六、路线图

- **v0.1**（当前）：核心三件套 + guard + xpost + topics
- **v0.2**：真人录音流水线泛化版（停顿切分 → 响度统一 → 分段导出，当前在 private 仓库验证中）
- **v0.3**：更多平台 API（B站专栏已有草稿笔记，见 docs/notes-bilibili.md）

## 七、命名

`mdcast` = markdown → broadcast。发前想改名就改，README 里只出现这一处。
