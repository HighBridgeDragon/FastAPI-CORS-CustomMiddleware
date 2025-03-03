from http import HTTPStatus
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

# テスト用定数
ORIGIN = "http://localhost:3000"
DISALLOWED_ORIGIN = "http://example.com"
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

def test_cors_preflight_allowed_origin():
    """許可されたOriginからのプリフライトリクエストのCORSヘッダー検証"""
    headers = {
        "Origin": ORIGIN,
        REQ_METHOD: METHOD,
        REQ_HEADERS: TYPE
    }
    response = client.options(PATH, headers=headers)
    assert response.status_code == HTTPStatus.OK
    verify_cors_headers(response.headers, METHOD)

def test_cors_preflight_disallowed_origin():
    """許可されていないOriginからのプリフライトリクエストのCORSヘッダー検証"""
    headers = {
        "Origin": DISALLOWED_ORIGIN,
        REQ_METHOD: METHOD,
        REQ_HEADERS: TYPE
    }
    response = client.options(PATH, headers=headers)
    # プリフライトリクエストは許可されていないOriginからの場合はBAD_REQUEST
    assert response.status_code == HTTPStatus.BAD_REQUEST
    # CORSヘッダーは付与されない
    assert AC_O not in response.headers

def test_cors_success_response_allowed_origin():
    """許可されたOriginからの正常系レスポンスのCORSヘッダー検証"""
    headers = {
        "Origin": ORIGIN,
        TYPE: "application/json",
        "Authorization": "Bearer test-token"
    }
    response = client.post(PATH, headers=headers, json={"status": HTTPStatus.OK})
    assert response.status_code == HTTPStatus.OK
    verify_cors_headers(response.headers)

def test_cors_success_response_disallowed_origin():
    """許可されていないOriginからの正常系レスポンスのCORSヘッダー検証"""
    headers = {
        "Origin": DISALLOWED_ORIGIN,
        TYPE: "application/json",
        "Authorization": "Bearer test-token"
    }
    response = client.post(PATH, headers=headers, json={"status": HTTPStatus.OK})
    assert response.status_code == HTTPStatus.OK
    assert AC_O not in response.headers

def test_cors_unauthorized_response_allowed_origin():
    """許可されたOriginからの認証エラー時のCORSヘッダー検証"""
    headers = {
        "Origin": ORIGIN,
        TYPE: "application/json"
    }
    response = client.post(PATH, headers=headers, json={"status": HTTPStatus.OK})
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()["error"] == "Authentication required"
    verify_cors_headers(response.headers)

def test_cors_unauthorized_response_disallowed_origin():
    """許可されていないOriginからの認証エラー時のCORSヘッダー検証"""
    headers = {
        "Origin": DISALLOWED_ORIGIN,
        TYPE: "application/json"
    }
    response = client.post(PATH, headers=headers, json={"status": HTTPStatus.OK})
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()["error"] == "Authentication required"
    assert AC_O not in response.headers

def test_cors_invalid_json_response_allowed_origin():
    """許可されたOriginからの不正なJSONリクエスト時のCORSヘッダー検証"""
    headers = {
        "Origin": ORIGIN,
        TYPE: "application/json",
        "Authorization": "Bearer test-token"
    }
    response = client.post(PATH, headers=headers, data="invalid json")
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json()["error"] == "Invalid JSON"
    verify_cors_headers(response.headers)

def test_cors_invalid_json_response_disallowed_origin():
    """許可されていないOriginからの不正なJSONリクエスト時のCORSヘッダー検証"""
    headers = {
        "Origin": DISALLOWED_ORIGIN,
        TYPE: "application/json",
        "Authorization": "Bearer test-token"
    }
    response = client.post(PATH, headers=headers, data="invalid json")
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json()["error"] == "Invalid JSON"
    assert AC_O not in response.headers

def test_cors_method_not_allowed_response_allowed_origin():
    """許可されたOriginからの不正なHTTPメソッド時のCORSヘッダー検証"""
    headers = {
        "Origin": ORIGIN,
        "Authorization": "Bearer test-token"
    }
    response = client.get(PATH, headers=headers)
    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    verify_cors_headers(response.headers)

def test_cors_method_not_allowed_response_disallowed_origin():
    """許可されていないOriginからの不正なHTTPメソッド時のCORSヘッダー検証"""
    headers = {
        "Origin": DISALLOWED_ORIGIN,
        "Authorization": "Bearer test-token"
    }
    response = client.get(PATH, headers=headers)
    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    assert AC_O not in response.headers

def test_cors_custom_status_allowed_origin():
    """許可されたOriginからのカスタムステータスコードのCORSヘッダー検証"""
    headers = {
        "Origin": ORIGIN,
        "Authorization": "Bearer test-token",
        TYPE: "application/json"
    }
    # 成功ステータス (201)
    response = client.post(PATH, headers=headers, json={"status": HTTPStatus.CREATED})
    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {"message": "Status 201"}
    verify_cors_headers(response.headers)

    # エラーステータス (404)
    response = client.post(PATH, headers=headers, json={"status": HTTPStatus.NOT_FOUND})
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"message": "Status 404"}
    verify_cors_headers(response.headers)

def test_cors_custom_status_disallowed_origin():
    """許可されていないOriginからのカスタムステータスコードのCORSヘッダー検証"""
    headers = {
        "Origin": DISALLOWED_ORIGIN,
        "Authorization": "Bearer test-token",
        TYPE: "application/json"
    }
    # 成功ステータス (201)
    response = client.post(PATH, headers=headers, json={"status": HTTPStatus.CREATED})
    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {"message": "Status 201"}
    assert AC_O not in response.headers

    # エラーステータス (404)
    response = client.post(PATH, headers=headers, json={"status": HTTPStatus.NOT_FOUND})
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"message": "Status 404"}
    assert AC_O not in response.headers
