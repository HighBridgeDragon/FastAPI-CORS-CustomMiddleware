from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from middleware import custom_middleware

app = FastAPI()

# FastAPIのCORSミドルウェアの適用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# カスタムミドルウェアの適用
app.middleware("http")(custom_middleware)


# テスト用エンドポイント
@app.post("/test-status")
async def test_status(request: Request):
    body = await request.json()
    return {"message": f"Status {body.get('status', 200)} requested"}
