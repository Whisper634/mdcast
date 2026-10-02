"""xpost —— X API 发布工具（OAuth 1.0a，纯标准库，无第三方依赖）。

凭据读取顺序：环境变量 > 当前目录 x_api.env。
支持代理：走 http_proxy / https_proxy 环境变量。

用法：
    mdcast xpost me                      # 验证凭据（GET users/me）
    mdcast xpost post "单条推文"          # 发一条
    mdcast xpost thread 稿件.thread.txt  # 发推文串（以 --- 分段）
    mdcast xpost delete <tweet_id>       # 删推
"""
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

KEYS_FILE = Path.cwd() / "x_api.env"
API = "https://api.x.com/2"


def load_creds():
    creds = {}
    for k in ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"):
        if os.environ.get(k):
            creds[k] = os.environ[k]
    if len(creds) < 4 and KEYS_FILE.exists():
        for ln in KEYS_FILE.read_text(encoding="utf-8").split("\n"):
            if "=" in ln:
                k, v = ln.split("=", 1)
                creds.setdefault(k.strip(), v.strip())
    missing = [k for k in ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET") if not creds.get(k)]
    if missing:
        sys.exit(f"缺凭据：{missing}（设置环境变量或填好 {KEYS_FILE}）")
    return creds


def oauth_header(method, url, creds, extra_params=None):
    """生成 OAuth 1.0a Authorization 头（HMAC-SHA1）。"""
    params = {
        "oauth_consumer_key": creds["X_API_KEY"],
        "oauth_nonce": secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": creds["X_ACCESS_TOKEN"],
        "oauth_version": "1.0",
    }
    if extra_params:
        params.update(extra_params)
    enc = lambda d: urllib.parse.urlencode(sorted(d.items()), quote_via=urllib.parse.quote)
    base = "&".join([method.upper(), urllib.parse.quote(url, safe=""), urllib.parse.quote(enc(params), safe="")])
    key = f'{urllib.parse.quote(creds["X_API_SECRET"], safe="")}&{urllib.parse.quote(creds["X_ACCESS_SECRET"], safe="")}'
    sig = base64.b64encode(hmac.new(key.encode(), base.encode(), hashlib.sha1).digest()).decode()
    params["oauth_signature"] = sig
    header = "OAuth " + ", ".join(f'{urllib.parse.quote(k, safe="")}="{urllib.parse.quote(v, safe="")}"'
                                  for k, v in sorted(params.items()))
    return header


def call(method, path, creds, json_body=None, params=None):
    url = API + path
    q = f"?{urllib.parse.urlencode(params)}" if params else ""
    body = json.dumps(json_body).encode() if json_body is not None else None
    header = oauth_header(method, url + (f"?{urllib.parse.urlencode(params)}" if params else ""), creds)
    req = urllib.request.Request(url + q, data=body, method=method,
                                 headers={"Authorization": header, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def cmd_me(creds):
    s, d = call("GET", "/users/me", creds)
    if s == 200:
        u = d["data"]
        print(f"✅ 凭据有效：@{u['username']} (id={u['id']})")
        return 0
    print(f"❌ {s}: {json.dumps(d, ensure_ascii=False)[:300]}")
    return 1


def cmd_post(creds, text):
    s, d = call("POST", "/tweets", creds, {"text": text})
    if s in (200, 201):
        print(f"✅ 已发：id={d['data']['id']}")
        return 0
    print(f"❌ {s}: {json.dumps(d, ensure_ascii=False)[:400]}")
    return 1


def cmd_thread(creds, path):
    text = Path(path).read_text(encoding="utf-8")
    parts = [re.sub(r"^\d+/\s*", "", p.strip()) for p in re.split(r"\n\s*---\s*\n", text) if p.strip()]
    if not parts:
        sys.exit("文件里没有可发的段落")
    prev, ok = None, True
    for i, p in enumerate(parts, 1):
        payload = {"text": p}
        if prev:
            payload["reply"] = {"in_reply_to_tweet_id": prev}
        s, d = call("POST", "/tweets", creds, payload)
        if s not in (200, 201):
            print(f"❌ 第{i}条失败 {s}: {json.dumps(d, ensure_ascii=False)[:300]}")
            ok = False
            break
        prev = d["data"]["id"]
        print(f"✅ {i}/{len(parts)} id={prev}")
        time.sleep(2)  # 防限流
    return 0 if ok else 1


def cmd_delete(creds, tid):
    s, d = call("DELETE", f"/tweets/{tid}", creds)
    if s == 200:
        print(f"✅ 已删 {tid}")
        return 0
    print(f"❌ {s}: {json.dumps(d, ensure_ascii=False)[:300]}")
    return 1


USAGE = __doc__


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(USAGE)
        sys.exit(1)
    c = load_creds()
    cmd = argv[0]
    if cmd == "me":
        sys.exit(cmd_me(c))
    if cmd == "post" and len(argv) > 1:
        sys.exit(cmd_post(c, argv[1]))
    if cmd == "thread" and len(argv) > 1:
        sys.exit(cmd_thread(c, argv[1]))
    if cmd == "delete" and len(argv) > 1:
        sys.exit(cmd_delete(c, argv[1]))
    print(USAGE)
    sys.exit(1)


if __name__ == "__main__":
    main()
