import socket

import pytest

from compliance_flag.input.url import validate_public_url


def private_resolver(host, port, type=socket.SOCK_STREAM):
    assert host == "example.com"
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.10", port or 80))]


def test_validate_public_url_rejects_private_ip_literal():
    with pytest.raises(ValueError, match="non-public"):
        validate_public_url("http://127.0.0.1/private")


def test_validate_public_url_rejects_localhost():
    with pytest.raises(ValueError, match="not public"):
        validate_public_url("http://localhost/private")


def test_validate_public_url_rejects_private_dns_result():
    with pytest.raises(ValueError, match="non-public"):
        validate_public_url("http://example.com/private", resolver=private_resolver)
