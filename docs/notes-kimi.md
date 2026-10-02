# Kimi（Moonshot）API 接入实测笔记

> mdcast 在 Kimi API 上跑了多次真实任务后记录的一手坑。接入 Moonshot 模型前先看这个，能省几个小时。

## 模型选择

- **kimi-k2.6**：长文改写（>4K 字输入）稳定成功，约 240s 返回。日常主力推荐。
- **kimi-k3**：对 >4K 字的长输入会**挂起直到超时**，无报错。短输入正常。
- 改写类任务建议 `MDCAST_MODEL=kimi-k2.6`。

## 配置

```bash
MDCAST_API_KEY=sk-...                    # platform.moonshot.cn → API Key 管理
MDCAST_BASE_URL=https://api.moonshot.cn/v1   # OpenAI 兼容
MDCAST_MODEL=kimi-k2.6
```

## 非显然的坑

1. **超时要给足**：长文改写 240s+ 才返回，`MDCAST_LLM_TIMEOUT` 默认 180 不够就调大。很多"API 挂了"其实是没等够。
2. **temperature 锁 1.0**：k2.6/k3 传其他值直接 400。想控制随机性只能从 prompt 下手。
2. **查余额有官方接口**：`GET /v1/users/me/balance`（Bearer 鉴权），返回 `available_balance / voucher_balance / cash_balance`，不用爬控制台。
3. **代理环境**：走 clash 等系统代理时，命令行工具记得 `--noproxy '*'`（curl）或给 urllib 配 `no_proxy`，否则可能连不上或绕远路。
4. **k3 的 temperature 限制**：传非 1.0 的值会直接 400。mdcast 默认 1.0 就是这个原因；换 k2.6 后建议自己调低。

## 兼容性

- 接口形态是标准 OpenAI `/chat/completions`，mdcast 的 `llm.py` 用纯 urllib 实现，无 SDK 依赖。换 DeepSeek/通义等任何兼容服务只需改 `MDCAST_BASE_URL` 和 `MDCAST_MODEL`。
