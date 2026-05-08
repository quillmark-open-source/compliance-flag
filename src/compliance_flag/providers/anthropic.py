from __future__ import annotations

import os
import time
from dataclasses import dataclass

import httpx

from compliance_flag.logging import log

DEFAULT_MODEL = "claude-opus-4-6"


@dataclass(frozen=True)
class ModelUsage:
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class ModelResponse:
    text: str
    usage: ModelUsage
    stop_reason: str | None


class AnthropicProvider:
    """Anthropic Messages API provider."""

    def __init__(self, *, model: str = DEFAULT_MODEL, max_tokens: int = 32000):
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set")
        self.model = model
        self.max_tokens = max_tokens

    def complete(self, *, system: str, user: str) -> ModelResponse:
        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError("anthropic package is not installed") from exc

        client = anthropic.Anthropic()
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            start = time.time()
            try:
                log(f"model: {self.model}")
                log("sending streaming request to Anthropic API")
                with client.messages.stream(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                ) as stream:
                    for event in stream:
                        self._log_stream_event(event)
                    response = stream.get_final_message()

                elapsed = time.time() - start
                log(f"response received ({elapsed:.1f}s)")
                text_parts = [
                    block.text
                    for block in response.content
                    if hasattr(block, "text") and block.text is not None
                ]
                usage = ModelUsage(
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                )
                return ModelResponse(
                    text="\n".join(text_parts),
                    usage=usage,
                    stop_reason=response.stop_reason,
                )
            except (httpx.RemoteProtocolError, httpx.ReadError) as exc:
                if attempt == max_retries:
                    raise
                wait = 5 * attempt
                log(f"connection lost: {exc}")
                log(f"retrying in {wait}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)

        raise RuntimeError("model request failed")

    @staticmethod
    def _log_stream_event(event) -> None:
        """Emit concise progress logs for Anthropic stream events."""
        event_type = getattr(event, "type", None)
        if event_type != "content_block_start":
            return

        block = getattr(event, "content_block", None)
        block_type = getattr(block, "type", None)
        if block_type == "thinking":
            log("thinking")
        elif block_type == "text":
            log("generating report")
        elif block_type == "server_tool_use":
            log("using server tool")
        elif block_type:
            log(f"received {block_type} block")
