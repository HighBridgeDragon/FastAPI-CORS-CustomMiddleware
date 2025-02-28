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


async def handle_body(body: dict) -> Res | None:
    """リクエストボディを処理"""
    if "status" in body:
        status = body["status"]
        msg = f"Status {status}"
        return JSONResponse(status_code=status, content={"message": msg})
    return None


async def custom_middleware(req: Request, call: Next) -> Res:
    try:
        if req.method == "POST":
            body_bytes = await req.body()
            if body_bytes:
                body = json.loads(body_bytes)
                resp = await handle_body(body)
                if resp:
                    return resp

        return await call(req)

    except json.JSONDecodeError:
        return error_response(400, ERR_JSON)
    except Exception as e:
        return error_response(500, ERR_SYSTEM, detail=str(e))
