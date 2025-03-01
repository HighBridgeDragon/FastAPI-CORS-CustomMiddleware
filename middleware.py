from fastapi import Request
from fastapi.responses import JSONResponse
import json
from typing import Callable, Awaitable

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
    
    # リクエストがあり、許可されたOriginからのリクエストの場合のみCORSヘッダーを付与
    if req and "Origin" in req.headers:
        origin = req.headers["Origin"]
        if origin in ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

async def custom_middleware(req: Request, call: Next) -> Res:
    """
    認証ミドルウェアの例
    - プリフライトリクエストはCORSミドルウェアに委ねる
    - その他のリクエストは認証チェック
    """
    try:
        # プリフライトリクエストはCORSミドルウェアに委ねる
        if req.method == "OPTIONS":
            return await call(req)

        # 認証チェック
        auth_header = req.headers.get("Authorization")
        if not auth_header:
            return error_response(401, "Authentication required", req)

        # POSTリクエストの処理
        if req.method == "POST":
            body_bytes = await req.body()
            if body_bytes:
                try:
                    body = json.loads(body_bytes)
                    if "status" in body:
                        req.state.status_code = body["status"]
                except json.JSONDecodeError:
                    return error_response(400, ERR_JSON, req)

        response = await call(req)
        if hasattr(req.state, "status_code"):
            response.status_code = req.state.status_code
        return response

    except Exception:
        return error_response(500, ERR_SYSTEM, req)
