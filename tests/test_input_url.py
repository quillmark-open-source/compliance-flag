import socket

import httpx
import pytest

from compliance_flag.input.url import (
    FETCH_HEADERS,
    MAX_PAGE_SIZE,
    _fetch_url_with_client,
    resolve_url_addresses,
)

EXAMPLE_IP = "93.184.216.34"


def example_resolver(host, port, **kwargs):
    assert host == "example.com"
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (EXAMPLE_IP, port or 80))]


def test_resolve_url_addresses_rejects_unsupported_scheme():
    with pytest.raises(ValueError, match="invalid URL"):
        resolve_url_addresses("file:///etc/passwd")


def test_resolve_url_addresses_returns_addresses():
    addresses = resolve_url_addresses(
        "http://example.com/page",
        resolver=example_resolver,
    )

    assert addresses == [EXAMPLE_IP]


def test_resolve_url_addresses_allows_loopback_ip_literal():
    addresses = resolve_url_addresses("http://127.0.0.1/private")

    assert "127.0.0.1" in addresses


def test_fetch_url_allows_redirect_to_loopback_host():
    requested_urls = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        if request.url.path == "/redirect":
            return httpx.Response(
                302,
                headers={"location": "http://127.0.0.1/private"},
                request=request,
            )
        return httpx.Response(200, text="INTERNAL_SECRET", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = _fetch_url_with_client(
            "http://example.com/redirect",
            client,
            resolver=example_resolver,
        )

    assert requested_urls == [
        f"http://{EXAMPLE_IP}/redirect",
        "http://127.0.0.1/private",
    ]
    assert result.document.content == "INTERNAL_SECRET"
    assert result.document.location == "http://127.0.0.1/private"


def test_fetch_url_pins_connection_to_validated_address():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["host_header"] = request.headers["host"]
        captured["sni"] = request.extensions.get("sni_hostname")
        return httpx.Response(
            200,
            text="<html><head><title>Example</title></head><body>ok</body></html>",
            request=request,
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = _fetch_url_with_client(
            "https://example.com/page",
            client,
            resolver=example_resolver,
        )

    assert captured["url"] == f"https://{EXAMPLE_IP}/page"
    assert captured["host_header"] == "example.com"
    assert captured["sni"] == "example.com"
    assert result.document.location == "https://example.com/page"


def test_fetch_url_stops_reading_when_response_exceeds_limit():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"x" * (MAX_PAGE_SIZE + 1),
            request=request,
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ValueError, match="page too large"):
            _fetch_url_with_client(
                "http://example.com/large",
                client,
                resolver=example_resolver,
            )


def test_fetch_url_allows_html_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text="<html><head><title>Example</title></head><body>ok</body></html>",
            request=request,
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = _fetch_url_with_client(
            "http://example.com/page",
            client,
            resolver=example_resolver,
        )

    assert result.status_code == 200
    assert result.document.location == "http://example.com/page"
    assert result.document.title == "Example"


def test_fetch_url_sends_generic_browser_headers():
    captured_headers = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_headers.update(request.headers)
        return httpx.Response(
            200,
            text="<html><head><title>Example</title></head><body>ok</body></html>",
            request=request,
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        _fetch_url_with_client(
            "http://example.com/page",
            client,
            resolver=example_resolver,
        )

    assert captured_headers["user-agent"] == FETCH_HEADERS["User-Agent"]
    assert "Compliance" not in captured_headers["user-agent"]
    assert "Codex" not in captured_headers["user-agent"]
    assert "text/html" in captured_headers["accept"]
    assert captured_headers["accept-language"] == "en-US,en;q=0.9"


def test_fetch_url_idna_encodes_international_hostnames():
    captured = {}

    def resolver(host, port, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (EXAMPLE_IP, port or 443))]

    def handler(request: httpx.Request) -> httpx.Response:
        captured["host_header"] = request.headers["host"]
        captured["sni"] = request.extensions.get("sni_hostname")
        return httpx.Response(200, text="<html></html>", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        _fetch_url_with_client(
            "https://bücher.example/page",
            client,
            resolver=resolver,
        )

    assert captured["host_header"] == "xn--bcher-kva.example"
    assert captured["sni"] == "xn--bcher-kva.example"


def test_fetch_url_skips_pinning_when_proxy_configured(monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.internal:3128")
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["sni"] = request.extensions.get("sni_hostname")
        return httpx.Response(200, text="<html></html>", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        _fetch_url_with_client(
            "https://example.com/page",
            client,
            resolver=example_resolver,
        )

    assert captured["url"] == "https://example.com/page"
    assert captured["sni"] is None


def test_fetch_url_falls_back_to_next_validated_address(monkeypatch):
    second_ip = "93.184.216.35"

    def resolver(host, port, **kwargs):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", (EXAMPLE_IP, port or 80)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", (second_ip, port or 80)),
        ]

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == EXAMPLE_IP:
            raise httpx.ConnectError("connection refused", request=request)
        return httpx.Response(200, text="<html></html>", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = _fetch_url_with_client(
            "http://example.com/page",
            client,
            resolver=resolver,
        )

    assert result.status_code == 200


def test_fetch_url_reports_http_errors_with_original_hostname():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="missing", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ValueError, match="404 fetching http://example.com/page"):
            _fetch_url_with_client(
                "http://example.com/page",
                client,
                resolver=example_resolver,
            )
