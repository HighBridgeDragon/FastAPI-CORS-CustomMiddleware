# FastAPI CORS Custom Middleware

FastAPIでのエラーレスポンスを伴うカスタムミドルウェアとCORSMidllewareの処理の検討

## 環境構築

```bash
rye sync
```
or
```bash
pip install -r requirements-dev.txt
```

## 機能詳細

### CORSヘッダー制御

- `Access-Control-Allow-Origin`
- `Access-Control-Allow-Credentials`
- `Access-Control-Allow-Methods`
- `Access-Control-Allow-Headers`
- `Access-Control-Max-Age`

### エラーレスポンス

```json
{
    "error": "エラーメッセージ",
    "detail": "追加情報（オプション）"
}
```

### 認証チェック

`Authorization`ヘッダーを使用した認証制御：

```python
headers = {
    "Authorization": "Bearer your-token",
    "Content-Type": "application/json"
}
```

## テスト

テストの実行：

```bash
pytest test_app.py
```
