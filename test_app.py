from http import HTTPStatus
from typing import Optional
from dataclasses import dataclass
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

@dataclass
class TestConfig:
    """テスト設定とフィクスチャを管理するクラス"""
    # 基本設定
    ALLOWED_ORIGIN: str = "http://localhost:3000"
    DISALLOWED_ORIGIN: str = "http://example.com"
    SPECIAL_ORIGINS: list[str] = (
        "null",  # null origin
        "file://localhost",  # ローカルファイル
        "data:",  # データURL
        f"{ALLOWED_ORIGIN}, {DISALLOWED_ORIGIN}"  # 複数Origin
    )
    TEST_PATH: str = "/test-status"
    
    # ヘッダー定数
    HEADERS = {
        "TYPE": "Content-Type",
        "AUTH": "Authorization",
        "ORIGIN": "Origin",
        # CORSヘッダー
        "AC_ORIGIN": "Access-Control-Allow-Origin",
        "AC_CRED": "Access-Control-Allow-Credentials",
        "AC_METHODS": "Access-Control-Allow-Methods",
        "AC_HEADERS": "Access-Control-Allow-Headers",
        # プリフライトリクエスト
        "REQ_METHOD": "Access-Control-Request-Method",
        "REQ_HEADERS": "Access-Control-Request-Headers"
    }

    # テスト用メソッド
    METHODS = {
        "POST": "POST",
        "GET": "GET",
        "OPTIONS": "OPTIONS"
    }

    @staticmethod
    def get_auth_headers(origin: str, include_type: bool = True) -> dict:
        """認証付きヘッダーを生成"""
        headers = {
            TestConfig.HEADERS["ORIGIN"]: origin,
            TestConfig.HEADERS["AUTH"]: "Bearer test-token"
        }
        if include_type:
            headers[TestConfig.HEADERS["TYPE"]] = "application/json"
        return headers

    @staticmethod
    def verify_cors_headers(headers: dict, methods: Optional[str] = None) -> None:
        """CORSヘッダーの検証（強化版）"""
        assert TestConfig.HEADERS["AC_ORIGIN"] in headers, "Access-Control-Allow-Origin header missing"
        assert headers[TestConfig.HEADERS["AC_ORIGIN"]] == TestConfig.ALLOWED_ORIGIN
        assert headers[TestConfig.HEADERS["AC_CRED"]] == "true"
        
        if methods:
            assert methods in headers[TestConfig.HEADERS["AC_METHODS"]], f"Method {methods} not allowed"
            assert TestConfig.HEADERS["TYPE"] in headers[TestConfig.HEADERS["AC_HEADERS"]]

# 基本的なCORSテスト
def test_cors_preflight_allowed_origin():
    """許可されたOriginからのプリフライトリクエスト検証"""
    headers = {
        TestConfig.HEADERS["ORIGIN"]: TestConfig.ALLOWED_ORIGIN,
        TestConfig.HEADERS["REQ_METHOD"]: TestConfig.METHODS["POST"],
        TestConfig.HEADERS["REQ_HEADERS"]: TestConfig.HEADERS["TYPE"]
    }
    response = client.options(TestConfig.TEST_PATH, headers=headers)
    assert response.status_code == HTTPStatus.OK
    TestConfig.verify_cors_headers(response.headers, TestConfig.METHODS["POST"])

def test_cors_preflight_disallowed_origin():
    """許可されていないOriginからのプリフライトリクエスト検証"""
    headers = {
        TestConfig.HEADERS["ORIGIN"]: TestConfig.DISALLOWED_ORIGIN,
        TestConfig.HEADERS["REQ_METHOD"]: TestConfig.METHODS["POST"],
        TestConfig.HEADERS["REQ_HEADERS"]: TestConfig.HEADERS["TYPE"]
    }
    response = client.options(TestConfig.TEST_PATH, headers=headers)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert TestConfig.HEADERS["AC_ORIGIN"] not in response.headers

# 新規追加: セキュリティテスト
def test_cors_special_origins():
    """特殊なOrigin値の検証"""
    for origin in TestConfig.SPECIAL_ORIGINS:
        headers = {
            TestConfig.HEADERS["ORIGIN"]: origin,
            TestConfig.HEADERS["REQ_METHOD"]: TestConfig.METHODS["POST"],
            TestConfig.HEADERS["REQ_HEADERS"]: TestConfig.HEADERS["TYPE"]
        }
        response = client.options(TestConfig.TEST_PATH, headers=headers)
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert TestConfig.HEADERS["AC_ORIGIN"] not in response.headers

# 新規追加: エラーケース
def test_cors_empty_post():
    """空のPOSTリクエスト検証"""
    headers = TestConfig.get_auth_headers(TestConfig.ALLOWED_ORIGIN)
    response = client.post(TestConfig.TEST_PATH, headers=headers)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json()["error"] == "Invalid JSON"
    TestConfig.verify_cors_headers(response.headers)

def test_cors_invalid_content_type():
    """不正なContent-Typeヘッダー検証"""
    headers = {
        TestConfig.HEADERS["ORIGIN"]: TestConfig.ALLOWED_ORIGIN,
        TestConfig.HEADERS["TYPE"]: "text/plain",
        TestConfig.HEADERS["AUTH"]: "Bearer test-token"
    }
    response = client.post(TestConfig.TEST_PATH, headers=headers, data="test")
    assert response.status_code == HTTPStatus.BAD_REQUEST
    TestConfig.verify_cors_headers(response.headers)

# 新規追加: ステータスコード境界値テスト
def test_cors_status_code_boundaries():
    """ステータスコード境界値の検証"""
    status_codes = [100, 200, 300, 400, 500]
    headers = TestConfig.get_auth_headers(TestConfig.ALLOWED_ORIGIN)
    
    for status in status_codes:
        response = client.post(
            TestConfig.TEST_PATH,
            headers=headers,
            json={"status": status}
        )
        assert response.status_code == status
        TestConfig.verify_cors_headers(response.headers)

def test_cors_success_response():
    """正常系レスポンスのCORSヘッダー検証"""
    headers = TestConfig.get_auth_headers(TestConfig.ALLOWED_ORIGIN)
    response = client.post(
        TestConfig.TEST_PATH,
        headers=headers,
        json={"status": HTTPStatus.OK}
    )
    assert response.status_code == HTTPStatus.OK
    TestConfig.verify_cors_headers(response.headers)

def test_cors_unauthorized_response():
    """認証エラー時のCORSヘッダー検証"""
    headers = {
        TestConfig.HEADERS["ORIGIN"]: TestConfig.ALLOWED_ORIGIN,
        TestConfig.HEADERS["TYPE"]: "application/json"
    }
    response = client.post(
        TestConfig.TEST_PATH,
        headers=headers,
        json={"status": HTTPStatus.OK}
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()["error"] == "Authentication required"
    TestConfig.verify_cors_headers(response.headers)

def test_cors_method_not_allowed():
    """不正なHTTPメソッド時のCORSヘッダー検証"""
    headers = TestConfig.get_auth_headers(TestConfig.ALLOWED_ORIGIN, include_type=False)
    response = client.get(TestConfig.TEST_PATH, headers=headers)
    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    TestConfig.verify_cors_headers(response.headers)
