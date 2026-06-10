import sys
import types
from types import SimpleNamespace

import httpx
import pytest

from compliance_flag.providers.anthropic import DEFAULT_MODEL, AnthropicProvider


def _final_message(text="{}", stop_reason="end_turn"):
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        usage=SimpleNamespace(input_tokens=11, output_tokens=22),
        stop_reason=stop_reason,
    )


class FakeStream:
    def __init__(self, *, fail_with=None, message=None):
        self.fail_with = fail_with
        self.message = message or _final_message()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def __iter__(self):
        yield SimpleNamespace(
            type="content_block_start",
            content_block=SimpleNamespace(type="text"),
        )
        if self.fail_with is not None:
            raise self.fail_with

    def get_final_message(self):
        return self.message


class FakeAnthropicClient:
    requests: list = []
    streams: list = []

    def __init__(self, *args, **kwargs):
        self.messages = self

    def stream(self, **kwargs):
        FakeAnthropicClient.requests.append(kwargs)
        return FakeAnthropicClient.streams.pop(0)


class FakeAPIStatusError(Exception):
    def __init__(self, status_code: int):
        super().__init__(f"API error {status_code}")
        self.status_code = status_code


@pytest.fixture
def fake_anthropic(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr("time.sleep", lambda seconds: None)
    module = types.ModuleType("anthropic")
    module.Anthropic = FakeAnthropicClient
    module.APIStatusError = FakeAPIStatusError
    monkeypatch.setitem(sys.modules, "anthropic", module)
    FakeAnthropicClient.requests = []
    FakeAnthropicClient.streams = []
    return FakeAnthropicClient


def test_provider_requires_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        AnthropicProvider()


def test_provider_sends_model_thinking_and_output_schema(fake_anthropic):
    fake_anthropic.streams = [FakeStream(message=_final_message('{"ok": true}'))]
    schema = {"type": "object", "additionalProperties": False}

    response = AnthropicProvider().complete(
        system="system",
        user="user",
        output_schema=schema,
    )

    request = fake_anthropic.requests[0]
    assert request["model"] == DEFAULT_MODEL
    assert request["max_tokens"] == 64000
    assert request["thinking"] == {"type": "adaptive"}
    assert request["output_config"] == {
        "format": {"type": "json_schema", "schema": schema}
    }
    assert response.text == '{"ok": true}'
    assert response.stop_reason == "end_turn"
    assert response.usage.input_tokens == 11
    assert response.usage.output_tokens == 22


def test_provider_omits_output_config_without_schema(fake_anthropic):
    fake_anthropic.streams = [FakeStream()]

    AnthropicProvider().complete(system="system", user="user")

    assert "output_config" not in fake_anthropic.requests[0]


def test_provider_retries_mid_stream_transport_errors(fake_anthropic):
    fake_anthropic.streams = [
        FakeStream(fail_with=httpx.ReadTimeout("stalled")),
        FakeStream(fail_with=httpx.RemoteProtocolError("dropped")),
        FakeStream(message=_final_message('{"ok": true}')),
    ]

    response = AnthropicProvider().complete(system="system", user="user")

    assert len(fake_anthropic.requests) == 3
    assert response.text == '{"ok": true}'


def test_provider_gives_up_after_three_transport_failures(fake_anthropic):
    fake_anthropic.streams = [
        FakeStream(fail_with=httpx.ReadTimeout("stalled")) for _ in range(3)
    ]

    with pytest.raises(httpx.ReadTimeout):
        AnthropicProvider().complete(system="system", user="user")

    assert len(fake_anthropic.requests) == 3


def test_provider_retries_mid_stream_server_errors(fake_anthropic):
    fake_anthropic.streams = [
        FakeStream(fail_with=FakeAPIStatusError(529)),
        FakeStream(message=_final_message('{"ok": true}')),
    ]

    response = AnthropicProvider().complete(system="system", user="user")

    assert len(fake_anthropic.requests) == 2
    assert response.text == '{"ok": true}'


def test_provider_does_not_retry_client_errors(fake_anthropic):
    fake_anthropic.streams = [FakeStream(fail_with=FakeAPIStatusError(400))]

    with pytest.raises(FakeAPIStatusError):
        AnthropicProvider().complete(system="system", user="user")

    assert len(fake_anthropic.requests) == 1
