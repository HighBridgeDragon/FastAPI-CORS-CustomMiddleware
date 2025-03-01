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

def verify_cors_headers(headers, methods=None):
    """CORSヘッダーの検証"""
    assert headers[AC_O] == ORIGIN
    assert headers[AC_C] == "true"
    if methods:
        assert methods in headers[AC_M]
        assert TYPE in headers[AC_H]

def test_cors_preflight():
    """プリフライトリクエストのCORSヘッダー検証"""
    headers = {
        "Origin": ORIGIN,
        REQ_METHOD: METHOD,
        REQ_HEADERS: TYPE,
    }
    response = client.options(PATH, headers=headers)
    assert response.status_code == 200
    verify_cors_headers(response.headers, METHOD)

def test_cors_success_response():
    """正常系レスポンスのCORSヘッダー検証"""
    headers = {
        "Origin": ORIGIN,
        TYPE: "application/json",
        "Authorization": "Bearer test-token"
    }
    response = client.post(PATH, headers=headers, json={"status": 200})
    assert response.status_code == 200
    verify_cors_headers(response.headers)

def test_cors_unauthorized_response():
    """認証エラー時のCORSヘッダー検証"""
    headers = {
        "Origin": ORIGIN,
        TYPE: "application/json"
    }
    response = client.post(PATH, headers=headers, json={"status": 200})
    
    # レスポンスの検証
    assert response.status_code == 401
    assert response.json()["error"] == "Authentication required"
    
    # CORSヘッダーの検証
    verify_cors_headers(response.headers)

def test_cors_invalid_json_response():
    """不正なJSONリクエスト時のCORSヘッダー検証"""
    headers = {
        "Origin": ORIGIN,
        TYPE: "application/json",
        "Authorization": "Bearer test-token"
    }
    response = client.post(PATH, headers=headers, data="invalid json")
    
    # レスポンスの検証
    assert response.status_code == 400
    assert response.json()["error"] == "Invalid JSON"
    
    # CORSヘッダーの検証
    verify_cors_headers(response.headers)

def test_cors_method_not_allowed_response():
    """不正なHTTPメソッド時のCORSヘッダー検証"""
    headers = {
        "Origin": ORIGIN,
        "Authorization": "Bearer test-token"
    }
    response = client.get(PATH, headers=headers)
    
    # レスポンスの検証
    assert response.status_code == 405
    
    # CORSヘッダーの検証
    verify_cors_headers(response.headers)

def test_cors_custom_success_status():
    """カスタムステータスコード（成功）のCORSヘッダー検証"""
    headers = {
        "Origin": ORIGIN,
        "Authorization": "Bearer test-token",
        TYPE: "application/json"
    }
    response = client.post(PATH, headers=headers, json={"status": 201})
    
    # レスポンスの検証
    assert response.status_code == 201
    assert response.json() == {"message": "Status 201"}
    
    # CORSヘッダーの検証
    verify_cors_headers(response.headers)

def test_cors_custom_error_status():
    """カスタムステータスコード（エラー）のCORSヘッダー検証"""
    headers = {
        "Origin": ORIGIN,
        "Authorization": "Bearer test-token",
        TYPE: "application/json"
    }
    response = client.post(PATH, headers=headers, json={"status": 404})
    
    # レスポンスの検証
    assert response.status_code == 404
    assert response.json() == {"message": "Status 404"}
    
    # CORSヘッダーの検証
    verify_cors_headers(response.headers)
