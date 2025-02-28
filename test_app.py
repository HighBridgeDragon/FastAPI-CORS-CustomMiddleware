from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

# テスト用定数
ORIGIN = "http://localhost:3000"
TYPE = "Content-Type"
METHOD = "POST"
PATH = "/test-status"

# CORSヘッダー定数
AC_O = "Access-Control-Allow-Origin"
AC_C = "Access-Control-Allow-Credentials"
AC_M = "Access-Control-Allow-Methods"
AC_H = "Access-Control-Allow-Headers"

# リクエストヘッダー定数
REQ_METHOD = "Access-Control-Request-Method"
REQ_HEADERS = "Access-Control-Request-Headers"


def test_cors_preflight():
    """プリフライトリクエストのテスト"""
    headers = {
        "Origin": ORIGIN,
        REQ_METHOD: METHOD,
        REQ_HEADERS: TYPE,
    }
    response = client.options(PATH, headers=headers)
    assert response.status_code == 200

    # CORSヘッダーの検証
    headers = response.headers
    assert headers[AC_O] == ORIGIN
    assert headers[AC_C] == "true"
    assert METHOD in headers[AC_M]
    assert TYPE in headers[AC_H]


def test_cors_actual_request():
    """通常のリクエストでのCORSヘッダーのテスト"""
    headers = {"Origin": ORIGIN, TYPE: "application/json"}
    data = {"status": 200}
    response = client.post(PATH, headers=headers, json=data)
    assert response.status_code == 200

    # CORSヘッダーの検証
    headers = response.headers
    assert headers[AC_O] == ORIGIN
    assert headers[AC_C] == "true"


def test_custom_status_middleware():
    """カスタムステータスミドルウェアのテスト"""
    # 正常なステータスコードのテスト
    response = client.post(PATH, json={"status": 201})
    assert response.status_code == 201
    assert response.json() == {"message": "Status 201"}

    # 不正なJSONのテスト
    response = client.post(PATH, data="invalid json")
    assert response.status_code == 400
    assert response.json()["error"] == "Invalid JSON"

    # エラーステータスコードのテスト
    response = client.post(PATH, json={"status": 404})
    assert response.status_code == 404
    assert response.json() == {"message": "Status 404"}


def test_non_post_request():
    """POST以外のリクエストのテスト"""
    response = client.get(PATH)
    assert response.status_code == 405  # Method Not Allowed
