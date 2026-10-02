"""OpenAI 兼容 /chat/completions 客户端（纯标准库，无 SDK 依赖）。

未配置 API 时 chat() 返回 None，调用方退回规则版。
"""
import json
import urllib.request

from . import config


def configured() -> bool:
    return bool(config.API_KEY and config.BASE_URL and config.MODEL)


def chat(prompt: str) -> str | None:
    if not configured():
        return None
    body = json.dumps({
        "model": config.MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": config.TEMPERATURE,
    }).encode()
    req = urllib.request.Request(
        config.BASE_URL.rstrip("/") + "/chat/completions",
        data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {config.API_KEY}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=config.LLM_TIMEOUT) as r:
            resp = json.loads(r.read().decode())
        return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"⚠️ LLM 调用失败（{e}），退回规则版。")
        return None
