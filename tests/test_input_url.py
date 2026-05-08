import socket

import httpx
import pytest

from compliance_flag.input.url import (
    FETCH_HEADERS,
    MAX_PAGE_SIZE,
    _fetch_url_with_client,
    validate_public_url,
)


def public_resolver(host, port, type=socket.SOCK_STREAM):
    assert host == "example.com"
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port or 80))]


def test_validate_public_url_rejects_private_ip_literal():
    with pytest.raises(ValueError, match="non-public"):
        validate_public_url("http://127.0.0.1/private")


def test_fetch_url_rejects_redirect_to_private_host_before_requesting_it():
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
        with pytest.raises(ValueError, match="non-public"):
            _fetch_url_with_client(
                "http://example.com/redirect",
                client,
                resolver=public_resolver,
            )

    assert requested_urls == ["http://example.com/redirect"]


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
                resolver=public_resolver,
            )


def test_fetch_url_allows_public_html_response():
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
            resolver=public_resolver,
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
            resolver=public_resolver,
        )

    assert captured_headers["user-agent"] == FETCH_HEADERS["User-Agent"]
    assert "Compliance" not in captured_headers["user-agent"]
    assert "Codex" not in captured_headers["user-agent"]
    assert "text/html" in captured_headers["accept"]
    assert captured_headers["accept-language"] == "en-US,en;q=0.9"
