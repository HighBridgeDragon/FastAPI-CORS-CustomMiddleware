from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from middleware import custom_middleware
import json

app = FastAPI()


# FastAPIのCORSミドルウェアを最初に適用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# カスタムミドルウェア（認証など）を後に適用
app.middleware("http")(custom_middleware)


# テスト用エンドポイント
@app.post("/test-status")
async def test_status(request: Request):
    try:
        body = await request.json()
        status = getattr(request.state, "status_code", 200)
        return {"message": f"Status {status}"}
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON"}
        )
