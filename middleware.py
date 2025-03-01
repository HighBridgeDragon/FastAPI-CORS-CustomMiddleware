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


def error_response(code: int, msg: str, **extra) -> Res:
    """エラーレスポンスを生成"""
    content = {"error": msg}
    if extra:
        content.update(extra)
    return JSONResponse(status_code=code, content=content)


async def custom_middleware(req: Request, call: Next) -> Res:
    """
    認証ミドルウェアの例
    - プリフライトリクエスト（OPTIONS）は常に許可
    - その他のリクエストは認証チェック
    """
    # プリフライトリクエストは常に許可（CORSミドルウェアに処理を委ねる）
    if req.method == "OPTIONS":
        return await call(req)

    # 認証チェックの例（CORSミドルウェアが先に実行されているため、
    # エラーレスポンスにもCORSヘッダーが付与される）
    auth_header = req.headers.get("Authorization")
    if not auth_header:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"}
        )

    try:
        if req.method == "POST":
            body_bytes = await req.body()
            if body_bytes:
                try:
                    body = json.loads(body_bytes)
                    if "status" in body:
                        req.state.status_code = body["status"]
                except json.JSONDecodeError:
                    return error_response(400, ERR_JSON)

        response = await call(req)
        if hasattr(req.state, "status_code"):
            response.status_code = req.state.status_code
        return response

    except Exception:
        return error_response(500, ERR_SYSTEM)
