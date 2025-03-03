import json
from typing import Awaitable, Callable

from fastapi import Request
from fastapi.responses import JSONResponse

# 型エイリアス
Res = JSONResponse
Awt = Awaitable[Res]
Next = Callable[[Request], Awt]

# エラーメッセージ
ERR_JSON = "Invalid JSON"
ERR_SYSTEM = "System error"

# 許可するOrigin
ALLOWED_ORIGINS = ["http://localhost:3000"]


def error_response(code: int, msg: str, req: Request = None, **extra) -> Res:
    """エラーレスポンスを生成"""
    content = {"error": msg}
    if extra:
        content.update(extra)
    response = JSONResponse(status_code=code, content=content)

    if req and "Origin" in req.headers:
        origin = req.headers["Origin"]
        if origin in ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


async def _handle_post_request(req: Request) -> None:
    """POSTリクエストの処理"""
    body_bytes = await req.body()
    if not body_bytes:
        return

    try:
        body = json.loads(body_bytes)
        if "status" in body:
            req.state.status_code = body["status"]
    except json.JSONDecodeError:
        raise ValueError(ERR_JSON)


async def custom_middleware(req: Request, call: Next) -> Res:
    """
    認証ミドルウェアの例
    - プリフライトリクエストはCORSミドルウェアに委ねる
    - その他のリクエストは認証チェック
    """
    try:
        if req.method == "OPTIONS":
            return await call(req)

        auth_header = req.headers.get("Authorization")
        if not auth_header:
            return error_response(401, "Authentication required", req)

        if req.method == "POST":
            try:
                await _handle_post_request(req)
            except ValueError as e:
                return error_response(400, str(e), req)

        response = await call(req)
        if hasattr(req.state, "status_code"):
            response.status_code = req.state.status_code
        return response

    except Exception:
        return error_response(500, ERR_SYSTEM, req)
