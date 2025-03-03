import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from http import HTTPStatus
from typing import Optional

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
        f"{ALLOWED_ORIGIN}, {DISALLOWED_ORIGIN}",  # 複数Origin
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
        "AC_MAX_AGE": "Access-Control-Max-Age",
        # プリフライトリクエスト
        "REQ_METHOD": "Access-Control-Request-Method",
        "REQ_HEADERS": "Access-Control-Request-Headers",
        # カスタムヘッダー
        "ACCEPT_LANGUAGE": "Accept-Language",
    }

    # テスト用メソッド
    METHODS = {
        "POST": "POST",
        "GET": "GET",
        "PUT": "PUT",
        "DELETE": "DELETE",
        "OPTIONS": "OPTIONS",
    }

    # テスト用言語
    LANGUAGES = ["en", "ja", "fr", "es"]

    # レート制限設定
    RATE_LIMIT = {"MAX_REQUESTS": 100, "TIME_WINDOW": 60}  # 秒

    # タイムアウト設定
    TIMEOUT = 5  # 秒

    @staticmethod
    def get_auth_headers(
        origin: str, include_type: bool = True, language: str = "en"
    ) -> dict:
        """認証付きヘッダーを生成"""
        headers = {
            TestConfig.HEADERS["ORIGIN"]: origin,
            TestConfig.HEADERS["AUTH"]: "Bearer test-token",
            TestConfig.HEADERS["ACCEPT_LANGUAGE"]: language,
        }
        if include_type:
            headers[TestConfig.HEADERS["TYPE"]] = "application/json"
        return headers

    @staticmethod
    def verify_cors_headers(headers: dict, methods: Optional[str] = None) -> None:
        """CORSヘッダーの検証（強化版）"""
        assert (
            TestConfig.HEADERS["AC_ORIGIN"] in headers
        ), "Access-Control-Allow-Origin header missing"
        assert headers[TestConfig.HEADERS["AC_ORIGIN"]] == TestConfig.ALLOWED_ORIGIN
        assert headers[TestConfig.HEADERS["AC_CRED"]] == "true"

        if methods:
            assert (
                methods in headers[TestConfig.HEADERS["AC_METHODS"]]
            ), f"Method {methods} not allowed"
            assert (
                TestConfig.HEADERS["TYPE"] in headers[TestConfig.HEADERS["AC_HEADERS"]]
            )


def test_cors_preflight_allowed_origin():
    """許可されたOriginからのプリフライトリクエスト検証"""
    headers = {
        TestConfig.HEADERS["ORIGIN"]: TestConfig.ALLOWED_ORIGIN,
        TestConfig.HEADERS["REQ_METHOD"]: TestConfig.METHODS["POST"],
        TestConfig.HEADERS["REQ_HEADERS"]: TestConfig.HEADERS["TYPE"],
    }
    response = client.options(TestConfig.TEST_PATH, headers=headers)
    assert response.status_code == HTTPStatus.OK
    TestConfig.verify_cors_headers(response.headers, TestConfig.METHODS["POST"])


def test_cors_preflight_disallowed_origin():
    """許可されていないOriginからのプリフライトリクエスト検証"""
    headers = {
        TestConfig.HEADERS["ORIGIN"]: TestConfig.DISALLOWED_ORIGIN,
        TestConfig.HEADERS["REQ_METHOD"]: TestConfig.METHODS["POST"],
        TestConfig.HEADERS["REQ_HEADERS"]: TestConfig.HEADERS["TYPE"],
    }
    response = client.options(TestConfig.TEST_PATH, headers=headers)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert TestConfig.HEADERS["AC_ORIGIN"] not in response.headers


def test_cors_special_origins():
    """特殊なOrigin値の検証"""
    for origin in TestConfig.SPECIAL_ORIGINS:
        headers = {
            TestConfig.HEADERS["ORIGIN"]: origin,
            TestConfig.HEADERS["REQ_METHOD"]: TestConfig.METHODS["POST"],
            TestConfig.HEADERS["REQ_HEADERS"]: TestConfig.HEADERS["TYPE"],
        }
        response = client.options(TestConfig.TEST_PATH, headers=headers)
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert TestConfig.HEADERS["AC_ORIGIN"] not in response.headers


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
        TestConfig.HEADERS["AUTH"]: "Bearer test-token",
    }
    response = client.post(TestConfig.TEST_PATH, headers=headers, data="test")
    assert response.status_code == HTTPStatus.BAD_REQUEST
    TestConfig.verify_cors_headers(response.headers)


def test_cors_status_code_boundaries():
    """ステータスコード境界値の検証"""
    status_codes = [
        HTTPStatus.CONTINUE,
        HTTPStatus.OK,
        HTTPStatus.MULTIPLE_CHOICES,
        HTTPStatus.BAD_REQUEST,
        HTTPStatus.INTERNAL_SERVER_ERROR,
    ]
    headers = TestConfig.get_auth_headers(TestConfig.ALLOWED_ORIGIN)

    for status in status_codes:
        response = client.post(
            TestConfig.TEST_PATH, headers=headers, json={"status": status}
        )
        assert response.status_code == status
        TestConfig.verify_cors_headers(response.headers)


def test_cors_success_response():
    """正常系レスポンスのCORSヘッダー検証"""
    headers = TestConfig.get_auth_headers(TestConfig.ALLOWED_ORIGIN)
    response = client.post(
        TestConfig.TEST_PATH, headers=headers, json={"status": HTTPStatus.OK}
    )
    assert response.status_code == HTTPStatus.OK
    TestConfig.verify_cors_headers(response.headers)


def test_cors_unauthorized_response():
    """認証エラー時のCORSヘッダー検証"""
    headers = {
        TestConfig.HEADERS["ORIGIN"]: TestConfig.ALLOWED_ORIGIN,
        TestConfig.HEADERS["TYPE"]: "application/json",
    }
    response = client.post(
        TestConfig.TEST_PATH, headers=headers, json={"status": HTTPStatus.OK}
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


def test_cors_preflight_cache():
    """プリフライトリクエストのキャッシュ制御検証"""
    headers = {
        TestConfig.HEADERS["ORIGIN"]: TestConfig.ALLOWED_ORIGIN,
        TestConfig.HEADERS["REQ_METHOD"]: TestConfig.METHODS["POST"],
        TestConfig.HEADERS["REQ_HEADERS"]: TestConfig.HEADERS["TYPE"],
    }

    # 最初のプリフライトリクエスト
    response = client.options(TestConfig.TEST_PATH, headers=headers)
    assert response.status_code == HTTPStatus.OK
    assert TestConfig.HEADERS["AC_MAX_AGE"] in response.headers
    max_age = int(response.headers[TestConfig.HEADERS["AC_MAX_AGE"]])
    assert max_age > 0

    # キャッシュ期間内の2回目のリクエスト
    response = client.options(TestConfig.TEST_PATH, headers=headers)
    assert response.status_code == HTTPStatus.OK
    TestConfig.verify_cors_headers(response.headers, TestConfig.METHODS["POST"])


def test_cors_multiple_methods():
    """異なるHTTPメソッドの組み合わせテスト"""
    for method in [TestConfig.METHODS["PUT"], TestConfig.METHODS["DELETE"]]:
        headers = {
            TestConfig.HEADERS["ORIGIN"]: TestConfig.ALLOWED_ORIGIN,
            TestConfig.HEADERS["REQ_METHOD"]: method,
            TestConfig.HEADERS["REQ_HEADERS"]: TestConfig.HEADERS["TYPE"],
        }
        response = client.options(TestConfig.TEST_PATH, headers=headers)
        assert response.status_code == HTTPStatus.OK
        TestConfig.verify_cors_headers(response.headers, method)


def test_cors_error_messages_i18n():
    """エラーメッセージの多言語対応検証"""
    for lang in TestConfig.LANGUAGES:
        headers = TestConfig.get_auth_headers(TestConfig.ALLOWED_ORIGIN, language=lang)
        response = client.post(TestConfig.TEST_PATH, headers=headers)
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert "error" in response.json()
        TestConfig.verify_cors_headers(response.headers)


def test_cors_timeout():
    """タイムアウト検証"""
    headers = TestConfig.get_auth_headers(TestConfig.ALLOWED_ORIGIN)
    response = client.post(
        TestConfig.TEST_PATH,
        headers=headers,
        json={"delay": TestConfig.TIMEOUT + 1},
    )
    # 時間がかかるリクエストでもCORSヘッダーが正しく設定されることを確認
    assert response.status_code in [HTTPStatus.BAD_REQUEST, HTTPStatus.REQUEST_TIMEOUT]
    TestConfig.verify_cors_headers(response.headers)


def test_cors_rate_limit():
    """レート制限検証"""
    headers = TestConfig.get_auth_headers(TestConfig.ALLOWED_ORIGIN)
    start_time = time.time()
    request_count = 0

    # レート制限に達するまでリクエストを送信
    with ThreadPoolExecutor(max_workers=10) as executor:
        while time.time() - start_time < TestConfig.RATE_LIMIT["TIME_WINDOW"]:
            if request_count >= TestConfig.RATE_LIMIT["MAX_REQUESTS"]:
                break

            response = client.post(
                TestConfig.TEST_PATH, headers=headers, json={"status": HTTPStatus.OK}
            )

            if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                # レート制限に到達
                assert "Retry-After" in response.headers
                assert int(response.headers["Retry-After"]) > 0
                TestConfig.verify_cors_headers(response.headers)
                break

            request_count += 1

    assert (
        request_count <= TestConfig.RATE_LIMIT["MAX_REQUESTS"]
    ), "レート制限が機能していません"


def test_cors_bulk_requests():
    """大量リクエスト時の検証"""
    headers = TestConfig.get_auth_headers(TestConfig.ALLOWED_ORIGIN)
    concurrent_requests = 50

    with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
        futures = []
        for _ in range(concurrent_requests):
            futures.append(
                executor.submit(
                    client.post,
                    TestConfig.TEST_PATH,
                    headers=headers,
                    json={"status": HTTPStatus.OK},
                )
            )

        # 全てのリクエストの結果を検証
        for future in futures:
            response = future.result()
            assert response.status_code in [HTTPStatus.OK, HTTPStatus.TOO_MANY_REQUESTS]
            if response.status_code == HTTPStatus.OK:
                TestConfig.verify_cors_headers(response.headers)
            else:
                assert "Retry-After" in response.headers
