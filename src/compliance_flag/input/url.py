from __future__ import annotations

import ipaddress
import socket
import urllib.request
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, urlunparse

import httpx
import idna
from bs4 import BeautifulSoup

from compliance_flag.console import log
from compliance_flag.input.file import SourceDocument
from compliance_flag.tokens import estimate_tokens

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


@dataclass(frozen=True)
class FetchResult:
    document: SourceDocument
    status_code: int
    content_type: str


@dataclass(frozen=True)
class _PageResponse:
    text: str
    content_type: str
    status_code: int


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    parsed = urlparse(url)
    if not parsed.netloc or not parsed.hostname:
        raise ValueError(f"invalid URL: {url}")
    return url


def resolve_url_addresses(
    url: str,
    *,
    resolver=socket.getaddrinfo,
) -> list[str]:
    """Validate URL shape and return resolved addresses for connection pinning."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"invalid URL: {url}")

    hostname = parsed.hostname.rstrip(".").lower()
    try:
        return [str(ipaddress.ip_address(hostname))]
    except ValueError:
        pass

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

    return addresses


def _ascii_hostname(hostname: str) -> str:
    """IDNA-encode an internationalized hostname for headers and SNI."""
    try:
        return idna.encode(hostname).decode("ascii")
    except (idna.IDNAError, UnicodeError):
        return hostname


def _proxy_in_use(url: str) -> bool:
    proxies = urllib.request.getproxies()
    return urlparse(url).scheme in proxies or "all" in proxies


def _pin_request_target(url: str, address: str) -> tuple[str, dict, dict]:
    """Rewrite the request to connect to a validated IP for the URL's host.

    The Host header and TLS SNI keep the original hostname so the request and
    certificate verification behave normally, while the TCP connection goes to
    the address that passed validation (closing the DNS-rebinding window
    between validation and connect).
    """
    parsed = urlparse(url)
    ip_netloc = f"[{address}]" if ":" in address else address
    hostname = _ascii_hostname(parsed.hostname or "")
    host_header = f"[{hostname}]" if ":" in hostname else hostname
    if parsed.port:
        ip_netloc = f"{ip_netloc}:{parsed.port}"
        host_header = f"{host_header}:{parsed.port}"

    pinned_url = urlunparse(parsed._replace(netloc=ip_netloc))
    headers = dict(FETCH_HEADERS)
    headers["Host"] = host_header
    # Without keep-alive, a later redirect hop to a different host that shares
    # this IP cannot reuse a TLS session verified for this hostname.
    headers["Connection"] = "close"
    extensions = {"sni_hostname": hostname} if parsed.scheme == "https" else {}
    return pinned_url, headers, extensions


def _request_targets(url: str, addresses: list[str]) -> list[tuple[str, dict, dict]]:
    if _proxy_in_use(url):
        # A proxy performs its own DNS resolution, so IP pinning cannot be
        # enforced (and the proxy CONNECT tunnel ignores the SNI override).
        # URL validation above still applies.
        return [(url, dict(FETCH_HEADERS), {})]
    return [_pin_request_target(url, address) for address in addresses]


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


def _request_once(
    client: httpx.Client,
    current_url: str,
    addresses: list[str],
) -> str | _PageResponse:
    """Issue one GET against a validated address.

    Returns the redirect target URL for redirect responses, otherwise the
    captured page. Tries the next validated address if a connection fails.
    """
    targets = _request_targets(current_url, addresses)
    last_error: httpx.ConnectError | None = None
    for request_url, headers, extensions in targets:
        try:
            with client.stream(
                "GET",
                request_url,
                headers=headers,
                extensions=extensions,
            ) as response:
                if response.is_redirect:
                    location = response.headers.get("location", "")
                    return urljoin(current_url, location)

                if response.status_code >= 400:
                    raise ValueError(
                        f"HTTP error {response.status_code} fetching {current_url}"
                    )
                body = _read_limited_response(response)
                encoding = response.encoding or "utf-8"
                return _PageResponse(
                    text=body.decode(encoding, errors="replace"),
                    content_type=response.headers.get("content-type", ""),
                    status_code=response.status_code,
                )
        except httpx.ConnectError as exc:
            last_error = exc

    assert last_error is not None
    raise last_error


def _fetch_url_with_client(
    url: str,
    client: httpx.Client,
    *,
    resolver=socket.getaddrinfo,
) -> FetchResult:
    current_url = url
    for _ in range(MAX_REDIRECTS + 1):
        addresses = resolve_url_addresses(current_url, resolver=resolver)
        result = _request_once(client, current_url, addresses)
        if isinstance(result, str):
            current_url = result
            continue
        page = result
        final_url = current_url
        break
    else:
        raise ValueError(f"too many redirects fetching URL (max: {MAX_REDIRECTS})")

    text = page.text
    soup = BeautifulSoup(text, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else final_url
    log(f"captured page content (~{estimate_tokens(text):,} tokens, estimated)")

    return FetchResult(
        document=SourceDocument(
            source_type="web",
            location=final_url,
            title=title,
            content=text,
        ),
        status_code=page.status_code,
        content_type=page.content_type,
    )


def fetch_url(url: str) -> FetchResult:
    """Fetch a URL and return captured content for analysis."""
    normalized = normalize_url(url)
    log(f"fetching {normalized}")
    with httpx.Client(timeout=FETCH_TIMEOUT, follow_redirects=False) as client:
        return _fetch_url_with_client(normalized, client)
