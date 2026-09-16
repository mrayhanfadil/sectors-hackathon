# Copyright 2026 Sectors Hackathon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Muse Spark 1.3 via OpenCode Go - OpenAI Responses-API adapter for ADK Python.

Why this exists: opencode-go (`https://opencode.ai/zen/go/v1`) lists
`muse-spark-1.3-contributor` on `/v1/models`, but serves it ONLY on the
Responses API (`POST /v1/responses`). The chat-completions endpoint
persistently returns `Internal server error` for this model (probed
2026-09-05). ADK's `LiteLlm` wrapper speaks chat-completions, so it can
never drive Muse - this `BaseLlm` subclass speaks Responses instead.

Wire format (OpenAI Responses API):
  in:  instructions + input[] (message | function_call | function_call_output)
       + tools[] ({type:function, name, description, parameters})
  out: output[] (message.output_text | function_call | reasoning[ignored])

Stateless per turn: the ADK runner owns the tool loop and re-sends full
history (including prior function_call/function_call_output items) each
turn, so no server-side state (`previous_response_id`) is needed.

Env:
  OPENCODE_GO_API_KEY - required (same key Hermes gateway uses).
  Resolution order: explicit arg → env → ~/.hermes/.env.
  NOTE: ~/.local/share/opencode/auth.json is deliberately NOT read -
  that CLI key 401s on inference (only good for /v1/models, probed
  2026-09-05). Fail fast instead of silently using a dead key.
  OPENCODE_GO_BASE_URL - default https://opencode.ai/zen/go/v1
  SPARK13_MODEL / SPARK13_MAX_TOKENS / SPARK13_TIMEOUT
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, AsyncGenerator

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from pydantic import Field

_OPENCODE_GO_DEFAULT_BASE = "https://opencode.ai/zen/go/v1"
_SPARK13_DEFAULT_MODEL = "muse-spark-1.3-contributor"
# Reasoning-effort-high models burn output budget on thinking tokens:
# the first live PONG needed >20 tokens for 17 reasoning tokens.
_SPARK13_DEFAULT_MAX_TOKENS = 8192


def _opencode_go_key(explicit: str | None = None) -> str | None:
    """Resolve the OpenCode Go key without ever printing it."""
    if explicit and explicit.strip():
        return explicit.strip().strip('"').strip("'")
    v = os.getenv("OPENCODE_GO_API_KEY")
    if v and v.strip() and not v.strip().startswith("#"):
        return v.strip().strip('"').strip("'")
    import pathlib

    p = pathlib.Path.home() / ".hermes" / ".env"
    if p.exists():
        try:
            m = re.search(r"^OPENCODE_GO_API_KEY\s*=\s*\"?([^\"\n]+)\"?", p.read_text(), re.M)
            if m and not m.group(1).strip().startswith("#"):
                key = m.group(1).strip().strip('"').strip("'")
                if key:
                    return key
        except Exception:
            pass
    return None


def _func_decl_to_responses_tool(fd: Any) -> dict[str, Any]:
    """FunctionDeclaration → Responses-API function tool dict.

    Reuses ADK's own OpenAI-spec converter when available so schema
    handling matches LiteLlm exactly; falls back to parameters_json_schema.
    """
    try:
        from google.adk.models.lite_llm import _function_declaration_to_tool_param

        spec = _function_declaration_to_tool_param(fd)["function"]
        return {
            "type": "function",
            "name": spec["name"],
            "description": spec.get("description") or "",
            "parameters": spec.get("parameters") or {"type": "object", "properties": {}},
        }
    except Exception:
        params = getattr(fd, "parameters_json_schema", None) or {
            "type": "object",
            "properties": {},
        }
        return {
            "type": "function",
            "name": getattr(fd, "name", "unknown_tool"),
            "description": getattr(fd, "description", None) or "",
            "parameters": params,
        }


def _contents_to_input_items(contents: list[Any]) -> list[dict[str, Any]]:
    """ADK contents → Responses `input` items (history replay)."""
    items: list[dict[str, Any]] = []
    for content in contents or []:
        role = getattr(content, "role", "") or ""
        for part in getattr(content, "parts", None) or []:
            t = getattr(part, "text", None)
            if t:
                if role == "model":
                    items.append({"role": "assistant", "content": t})
                else:
                    items.append({"role": "user", "content": t})
                continue
            fc = getattr(part, "function_call", None)
            if fc is not None:
                args = getattr(fc, "args", {}) or {}
                items.append(
                    {
                        "type": "function_call",
                        "call_id": getattr(fc, "id", None) or "",
                        "name": getattr(fc, "name", ""),
                        "arguments": json.dumps(args) if not isinstance(args, str) else args,
                    }
                )
                continue
            fr = getattr(part, "function_response", None)
            if fr is not None:
                resp = getattr(fr, "response", "")
                output = json.dumps(resp, ensure_ascii=False) if isinstance(resp, dict) else str(resp)
                items.append(
                    {
                        "type": "function_call_output",
                        "call_id": getattr(fr, "id", None) or "",
                        "output": output,
                    }
                )
                continue
    if not items:
        items.append({"role": "user", "content": ""})
    return items


def _parse_args(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


class OpenGoResponsesLlm(BaseLlm):
    """ADK model speaking OpenAI Responses API (opencode-go Muse Spark)."""

    api_key: str = Field(repr=False)
    api_base: str = _OPENCODE_GO_DEFAULT_BASE
    max_output_tokens: int = _SPARK13_DEFAULT_MAX_TOKENS
    timeout: int = 120
    max_retries: int = 2

    @property
    def capabilities(self):  # type: ignore[override]
        from google.adk.models._capabilities import LlmCapabilities

        return LlmCapabilities(output_schema_and_tools=True)

    def _payload(self, llm_request: LlmRequest) -> dict[str, Any]:
        try:
            from google.adk.models.interactions_utils import extract_system_instruction

            instructions = extract_system_instruction(llm_request.config) or ""
        except Exception:
            instructions = ""
        payload: dict[str, Any] = {
            "model": self.model,
            "max_output_tokens": self.max_output_tokens,
            "input": _contents_to_input_items(llm_request.contents),
        }
        if instructions:
            payload["instructions"] = instructions
        tools: list[dict[str, Any]] = []
        for tool in getattr(llm_request.config, "tools", None) or []:
            for fd in getattr(tool, "function_declarations", None) or []:
                tools.append(_func_decl_to_responses_tool(fd))
        if tools:
            payload["tools"] = tools
        return payload

    def _llm_response_from_output(self, data: dict[str, Any]) -> LlmResponse:
        parts: list[types.Part] = []
        for item in data.get("output") or []:
            itype = item.get("type", "")
            if itype == "message":
                texts = [
                    c.get("text", "")
                    for c in item.get("content", []) or []
                    if isinstance(c, dict) and c.get("type") in ("output_text", "text") and c.get("text")
                ]
                if texts:
                    parts.append(types.Part.from_text(text="".join(texts)))
            elif itype == "function_call":
                part = types.Part.from_function_call(
                    name=item.get("name", ""),
                    args=_parse_args(item.get("arguments", "")),
                )
                if part.function_call is not None:
                    part.function_call.id = item.get("call_id") or item.get("id")
                parts.append(part)
            # reasoning items carry encrypted_content only - nothing to surface.
        if not parts:
            raise RuntimeError(
                f"opencode-go responses returned no usable output (status={data.get('status')!r}, "
                f"incomplete={data.get('incomplete_details')!r})"
            )
        return LlmResponse(content=types.Content(role="model", parts=parts), partial=False)

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        import asyncio

        import httpx

        self._maybe_append_user_content(llm_request)
        url = self.api_base.rstrip("/") + "/responses"
        # Verified live 2026-09-05: plain Bearer + JSON is all this
        # endpoint needs. No extra headers (Referer/X-Title/session are
        # OpenRouter-isms - unneeded here, so not sent).
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = self._payload(llm_request)
        last_err: str = ""
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(url, headers=headers, json=payload)
            except Exception as e:
                last_err = f"request failed: {type(e).__name__}: {str(e)[:300]}"
            else:
                if resp.status_code == 200:
                    break
                last_err = f"HTTP {resp.status_code}: {resp.text[:500]}"
                if resp.status_code not in (429, 500, 502, 503, 504):
                    raise RuntimeError(f"opencode-go responses {last_err}")
            if attempt < self.max_retries:
                await asyncio.sleep(2**attempt)
        else:
            raise RuntimeError(f"opencode-go responses {last_err}")
        try:
            data = resp.json()
        except Exception:
            raise RuntimeError(f"opencode-go responses non-JSON reply: {resp.text[:300]}")
        if isinstance(data, dict) and data.get("type") == "error":
            raise RuntimeError(f"opencode-go responses error: {json.dumps(data)[:500]}")
        yield self._llm_response_from_output(data)


def spark13_model(
    model: str | None = None,
    api_key: str | None = None,
    api_base: str | None = None,
    max_output_tokens: int | None = None,
    timeout: int | None = None,
) -> OpenGoResponsesLlm:
    """Muse Spark 1.3-contributor via OpenCode Go Responses API (Hermes-style)."""
    key = _opencode_go_key(api_key)
    if not key:
        raise ValueError(
            "No OpenCode Go key - set OPENCODE_GO_API_KEY in env, "
            "project .env, or ~/.hermes/.env (same key Hermes gateway uses)"
        )
    return OpenGoResponsesLlm(
        model=model or os.getenv("SPARK13_MODEL") or _SPARK13_DEFAULT_MODEL,
        api_key=key,
        api_base=api_base or os.getenv("OPENCODE_GO_BASE_URL") or _OPENCODE_GO_DEFAULT_BASE,
        max_output_tokens=max_output_tokens or int(os.getenv("SPARK13_MAX_TOKENS", str(_SPARK13_DEFAULT_MAX_TOKENS))),
        timeout=timeout or int(os.getenv("SPARK13_TIMEOUT", "120")),
    )
