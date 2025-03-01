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
    """プリフライトリクエストのテスト - 認証不要"""
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
    """通常のリクエストでのCORSヘッダーのテスト - 認証必要"""
    # 認証なしの場合は401
    headers = {"Origin": ORIGIN, TYPE: "application/json"}
    data = {"status": 200}
    response = client.post(PATH, headers=headers, json=data)
    assert response.status_code == 401
    assert response.json()["error"] == "Authentication required"
    
    # 認証ありの場合は成功
    headers["Authorization"] = "Bearer test-token"
    response = client.post(PATH, headers=headers, json=data)
    assert response.status_code == 200

    # CORSヘッダーの検証（認証エラー時も付与される）
    headers = response.headers
    assert headers[AC_O] == ORIGIN
    assert headers[AC_C] == "true"


def test_custom_status_middleware():
    """カスタムステータスミドルウェアのテスト - 認証必要"""
    auth_headers = {
        "Authorization": "Bearer test-token",
        TYPE: "application/json"
    }

    # 正常なステータスコードのテスト
    response = client.post(PATH, headers=auth_headers, json={"status": 201})
    assert response.status_code == 201
    assert response.json() == {"message": "Status 201"}

    # 不正なJSONのテスト
    response = client.post(PATH, headers=auth_headers, data="invalid json")
    assert response.status_code == 400
    assert response.json()["error"] == "Invalid JSON"

    # エラーステータスコードのテスト
    response = client.post(PATH, headers=auth_headers, json={"status": 404})
    assert response.status_code == 404
    assert response.json() == {"message": "Status 404"}


def test_non_post_request():
    """POST以外のリクエストのテスト - 認証必要"""
    # 認証なしの場合は401
    response = client.get(PATH)
    assert response.status_code == 401
    assert response.json()["error"] == "Authentication required"

    # 認証ありの場合は405
    headers = {"Authorization": "Bearer test-token"}
    response = client.get(PATH, headers=headers)
    assert response.status_code == 405  # Method Not Allowed
