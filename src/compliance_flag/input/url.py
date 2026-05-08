from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from compliance_flag.input.file import SourceDocument
from compliance_flag.logging import log
from compliance_flag.tokens import count_tokens

FETCH_TIMEOUT = 30
MAX_PAGE_SIZE = 512 * 1024
MAX_REDIRECTS = 10
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.6 Safari/605.1.15"
)
FETCH_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
_BLOCKED_HOSTNAMES = {"localhost"}


@dataclass(frozen=True)
class FetchResult:
    document: SourceDocument
    status_code: int
    content_type: str


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    parsed = urlparse(url)
    if not parsed.netloc or not parsed.hostname:
        raise ValueError(f"invalid URL: {url}")
    return url


def _is_blocked_ip(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    return any(
        [
            not ip.is_global,
            ip.is_private,
            ip.is_loopback,
            ip.is_link_local,
            ip.is_multicast,
            ip.is_reserved,
            ip.is_unspecified,
        ]
    )


def validate_public_url(
    url: str,
    *,
    resolver=socket.getaddrinfo,
) -> None:
    """Reject URLs that resolve to local or otherwise non-public networks."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"invalid URL: {url}")

    hostname = parsed.hostname.rstrip(".").lower()
    if hostname in _BLOCKED_HOSTNAMES or hostname.endswith(".localhost"):
        raise ValueError(f"URL host is not public: {hostname}")

    try:
        addresses = [str(ipaddress.ip_address(hostname))]
    except ValueError:
        try:
            results = resolver(
                hostname,
                parsed.port,
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as exc:
            raise ValueError(f"could not resolve URL host: {hostname}") from exc
        addresses = [result[4][0] for result in results]

    if not addresses:
        raise ValueError(f"could not resolve URL host: {hostname}")

    for address in addresses:
        if _is_blocked_ip(address):
            raise ValueError(f"URL host resolves to a non-public address: {address}")


def _read_limited_response(response: httpx.Response) -> bytes:
    content_length = response.headers.get("content-length")
    if content_length and int(content_length) > MAX_PAGE_SIZE:
        raise ValueError(
            f"page too large ({int(content_length):,} bytes). Max: {MAX_PAGE_SIZE:,}"
        )

    body = bytearray()
    for chunk in response.iter_bytes():
        body.extend(chunk)
        if len(body) > MAX_PAGE_SIZE:
            raise ValueError(
                f"page too large ({len(body):,} bytes). Max: {MAX_PAGE_SIZE:,}"
            )
    return bytes(body)


def _fetch_url_with_client(
    url: str,
    client: httpx.Client,
    *,
    resolver=socket.getaddrinfo,
) -> FetchResult:
    current_url = url
    for _ in range(MAX_REDIRECTS + 1):
        validate_public_url(current_url, resolver=resolver)
        with client.stream(
            "GET",
            current_url,
            headers=FETCH_HEADERS,
        ) as response:
            if response.is_redirect:
                location = response.headers.get("location")
                if not location:
                    response.raise_for_status()
                current_url = urljoin(str(response.url), location)
                continue

            response.raise_for_status()
            body = _read_limited_response(response)
            content_type = response.headers.get("content-type", "")
            encoding = response.encoding or "utf-8"
            text = body.decode(encoding, errors="replace")
            final_url = str(response.url)
            status_code = response.status_code
            break
    else:
        raise ValueError(f"too many redirects fetching URL (max: {MAX_REDIRECTS})")

    validate_public_url(final_url, resolver=resolver)
    soup = BeautifulSoup(text, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else final_url
    tokens, method = count_tokens(text)
    log(f"captured page content ({tokens:,} tokens, {method})")

    return FetchResult(
        document=SourceDocument(
            source_type="web",
            location=final_url,
            title=title,
            content=text,
        ),
        status_code=status_code,
        content_type=content_type,
    )


def fetch_url(url: str) -> FetchResult:
    """Fetch a public page and return captured content for analysis."""
    normalized = normalize_url(url)
    log(f"fetching {normalized}")
    with httpx.Client(timeout=FETCH_TIMEOUT, follow_redirects=False) as client:
        return _fetch_url_with_client(normalized, client)
