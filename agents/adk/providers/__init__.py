# Copyright 2026 Sectors Hackathon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""DeepSeek + Gemini + CommandCode Spark provider adapter for ADK Python.

DeepSeek (deepseek-chat / deepseek-reasoner) is OpenAI-compatible.
We route it via LiteLlm so ADK's BaseLlm plumbing handles tools/prompts.
Muse Spark via CommandCode bridge (127.0.0.1:9992) is PREFERRED when available.

Gemini is native (google-genai) — used for search-grounded sub-agents
where GoogleSearchTool requires a Gemini model.

Env:
  COMMANDCODE_BRIDGE_KEY / BRIDGE_API_KEY — CommandCode bridge bearer (preferred)
  DEEPSEEK_API_KEY  — required for DeepSeek fallback
  GOOGLE_API_KEY    — required for Gemini search sub-agent (also GEMINI_API_KEY)
  DEEPSEEK_MODEL    — default deepseek-chat (also supports deepseek-reasoner)
  GEMINI_MODEL      — default gemini-2.0-flash
  SPARK_MODEL       — default meta/muse-spark-1.2-contributor
  SPARK_API_BASE    — default http://127.0.0.1:9992/v1
"""

from __future__ import annotations

import os

# Prevent litellm from auto-loading ~/.env at import time (would pick up stale GOOGLE_API_KEY from /home/fadil/.env)
os.environ.setdefault("LITELLM_MODE", "PRODUCTION")

import re

from google.adk.models.base_llm import BaseLlm

# LiteLlm is only available when google-adk[extensions] or litellm is installed.
# Import is deferred so `agents.adk` imports without litellm in tests.
_LITELLM_AVAILABLE: bool | None = None

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)

# CommandCode bridge defaults
_SPARK_DEFAULT_MODEL = "meta/muse-spark-1.2-contributor"
_SPARK_DEFAULT_BASE = "http://127.0.0.1:9992/v1"


def _bridge_key() -> str | None:
    """Read CommandCode bridge key from env or ~/.config/commandcode-bridge/env."""
    for k in ("BRIDGE_API_KEY", "COMMANDCODE_BRIDGE_KEY"):
        v = os.getenv(k)
        if v:
            return v.strip().strip('"').strip("'")
    # fallback: read bridge env file
    import pathlib

    p = pathlib.Path.home() / ".config" / "commandcode-bridge" / "env"
    if p.exists():
        try:
            txt = p.read_text()
            import re as _re

            m = _re.search(r'BRIDGE_API_KEY="([^"]+)"', txt)
            if m:
                return m.group(1).strip()
            m = _re.search(r"BRIDGE_API_KEY=([^\s]+)", txt)
            if m:
                return m.group(1).strip().strip('"').strip("'")
        except Exception:
            pass
    return None


def _litellm_available() -> bool:
    global _LITELLM_AVAILABLE
    if _LITELLM_AVAILABLE is not None:
        return _LITELLM_AVAILABLE
    try:
        import litellm  # noqa: F401

        _LITELLM_AVAILABLE = True
    except ImportError:
        _LITELLM_AVAILABLE = False
    return _LITELLM_AVAILABLE


def deepseek_model(
    model: str | None = None,
    api_key: str | None = None,
) -> BaseLlm:
    """Return a LiteLlm BaseLlm bound to DeepSeek OpenAI-compat endpoint.

    LiteLlm expects model strings like ``openai/deepseek-chat`` for
    OpenAI-compat routing; we use the ``openai/`` prefix so LiteLLM picks
    the OpenAI provider and respects api_base/api_key.
    """
    if not _litellm_available():
        raise ImportError("litellm not installed — pip install litellm or google-adk[extensions]")
    from google.adk.models.lite_llm import LiteLlm

    api_key = (api_key if api_key is not None else os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY") or "")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY (or OPENAI_API_KEY) is not set")
    model_id = model or os.getenv("DEEPSEEK_MODEL") or "deepseek-chat"
    # LiteLLM OpenAI-compat: api_base overrides the default OpenAI base URL.
    return LiteLlm(
        model=f"openai/{model_id}",
        api_base="https://api.deepseek.com/v1",
        api_key=api_key,
    )


def spark_model(
    model: str | None = None,
    api_key: str | None = None,
    api_base: str | None = None,
) -> BaseLlm:
    """Return a LiteLlm BaseLlm bound to CommandCode bridge (Muse Spark).

    Preferred provider for ADK — uses Muse Spark 1M context via local bridge.
    Falls back to reading BRIDGE_API_KEY from env or ~/.config/commandcode-bridge/env.
    """
    if not _litellm_available():
        raise ImportError("litellm not installed — pip install litellm or google-adk[extensions]")
    from google.adk.models.lite_llm import LiteLlm

    key = api_key or _bridge_key() or os.getenv("DEEPSEEK_API_KEY") or ""
    if not key:
        raise ValueError("No bridge key — set BRIDGE_API_KEY or check ~/.config/commandcode-bridge/env")
    model_id = model or os.getenv("SPARK_MODEL") or _SPARK_DEFAULT_MODEL
    base = api_base or os.getenv("SPARK_API_BASE") or _SPARK_DEFAULT_BASE
    return LiteLlm(
        model=f"openai/{model_id}",
        api_base=base,
        api_key=key,
        max_tokens=4096,  # Spark reasoning needs ≥256 visible; 4096 safe for tools
    )


def gemini_model(
    model: str | None = None,
    api_key: str | None = None,
) -> BaseLlm:
    """Return a native Gemini BaseLlm (google-genai)."""
    from google.adk.models.google_llm import Gemini

    key = api_key if api_key is not None else os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
    if not key:
        raise ValueError("GOOGLE_API_KEY (or GEMINI_API_KEY) is not set")
    # Gemini reads GOOGLE_API_KEY from env inside the SDK; ensure it's set.
    os.environ.setdefault("GOOGLE_API_KEY", key)
    model_id = model or os.getenv("GEMINI_MODEL") or "gemini-2.0-flash"
    return Gemini(model=model_id)


def strip_thinking_tags(text: str) -> str:
    """Strip DeepSeek <think>...</think> blocks."""
    return _THINK_RE.sub("", text).strip()


# Convenience: pick provider by name
def provider_model(name: str = "deepseek", **kw) -> BaseLlm:
    name = name.lower().strip()
    if name in ("spark", "muse", "muse-spark", "meta/muse-spark-1.2-contributor", "commandcode", "cc"):
        return spark_model(**kw)
    if name in ("deepseek", "deepseek-chat", "deepseek-reasoner", "deepseek-v3", "deepseek-r1"):
        # normalize model aliases
        model = kw.pop("model", None)
        if name not in ("deepseek",):
            model = name if "/" not in name else model
        return deepseek_model(model=model, **kw)
    if name in ("gemini", "google", "gemini-2.0-flash", "gemini-flash", "gemini-2.5-flash"):
        return gemini_model(**kw)
    raise ValueError(f"Unknown provider {name!r} — expected 'spark'|'deepseek'|'gemini'")
