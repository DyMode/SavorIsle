"""Standard-library client for SavorIsle candidate preparation; no publication API."""
import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, urlencode, quote
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def settings():
    raw = os.environ.get("SAVORISLE_URL", "")
    secret = os.environ.get("SAVORISLE_TOOL_TOKEN", "")
    u = urlsplit(raw)
    local = u.hostname in ("localhost", "127.0.0.1", "::1")
    allow_http = local or os.environ.get("SAVORISLE_ALLOW_HTTP") == "1"
    if not u.hostname or u.username or u.password or u.query or u.fragment or (u.scheme != "https" and not (u.scheme == "http" and allow_http)):
        raise ValueError("SAVORISLE_URL 必须为 HTTPS 应用地址；本地测试可用 HTTP 回环地址，可信局域网需显式设置 SAVORISLE_ALLOW_HTTP=1")
    if not secret.startswith("si_tool_") or len(secret) > 193 or any(c.isspace() for c in secret):
        raise ValueError("请通过 SAVORISLE_TOOL_TOKEN 配置个人工具令牌")
    return urlunsplit((u.scheme, u.netloc, u.path.rstrip("/"), "", "")), secret


def request(base, secret, path, body=None):
    raw = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    if raw is not None and len(raw) > 64 * 1024 * 1024:
        raise ValueError("数据包超过 64 MiB，请分批提交")
    req = Request(base + "/api/tools/" + path, data=raw, headers={"Authorization": "Bearer " + secret, "Content-Type": "application/json"})
    try:
        with build_opener(NoRedirect()).open(req, timeout=30) as result:
            data = result.read(64 * 1024 * 1024 + 1)
        if len(data) > 64 * 1024 * 1024:
            raise ValueError("响应超过 64 MiB")
        return json.loads(data)
    except HTTPError as e:
        # Provider/proxy bodies are untrusted; do not print headers or credentials.
        raise ValueError("味屿请求失败（HTTP %s）；检查令牌、权限或数据包" % e.code) from None
    except URLError:
        raise ValueError("无法连接味屿，请检查地址；可用同一数据包重试") from None


def main():
    parser = argparse.ArgumentParser(description="将菜谱提交到味屿候选检查页")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("schema")
    sub.add_parser("example")
    catalog = sub.add_parser("catalog")
    catalog.add_argument("--query", default="")
    catalog.add_argument("--kind", choices=["ingredient", "food", "brand", "equipment", "tool", "mould"], default="ingredient")
    catalog.add_argument("--offset", type=int, default=0)
    sub.add_parser("prepare").add_argument("file")
    sub.add_parser("preview").add_argument("id")
    args = parser.parse_args()
    try:
        base, secret = settings()
        if args.action == "prepare":
            file = Path(args.file)
            if file.stat().st_size > 262144:
                raise ValueError("数据包超过 256 KiB，请分批提交")
            with file.open(encoding="utf-8-sig") as f:
                body = json.load(f)
            value = request(base, secret, "imports", body)
            value = {"import_id": value["id"], "review_url": base + "/imports/" + quote(value["id"], safe=""), "candidate_count": len(value["candidates"])}
        elif args.action == "preview":
            value = request(base, secret, "imports/" + quote(args.id, safe=""))
        elif args.action == "catalog":
            value = request(base, secret, "catalog?" + urlencode({"q": args.query, "kind": args.kind, "offset": args.offset}))
        else:
            value = request(base, secret, args.action)
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError) as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
