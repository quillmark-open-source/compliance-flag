import socket

import pytest

from compliance_flag.input.url import resolve_url_addresses


def internal_resolver(host, port, **kwargs):
    assert host == "example.com"
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.10", port or 80))]


def test_resolve_url_addresses_allows_loopback_ip_literal():
    addresses = resolve_url_addresses("http://127.0.0.1/page")

    assert "127.0.0.1" in addresses


def test_resolve_url_addresses_allows_internal_dns_result():
    addresses = resolve_url_addresses(
        "http://example.com/private",
        resolver=internal_resolver,
    )

    assert addresses == ["10.0.0.10"]


def test_resolve_url_addresses_rejects_non_http_scheme():
    with pytest.raises(ValueError, match="invalid URL"):
        resolve_url_addresses("file:///etc/passwd")
