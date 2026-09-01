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
# Minimax DIRECT (like hermes custom_providers minimax-v1) — hermes config has
# custom_providers: name minimax-v1, base https://api.minimax.io/v1, key MINIMAX_API_KEY, model MiniMax-M3.
# We use the same direct endpoint so the full 11-agent graph doesn't hop through
# the overloaded CommandCode free tier (minimax-m3-free @ api.commandcode.ai 503'd).
_MINIMAX_DIRECT_MODEL = "MiniMax-M3"
_MINIMAX_DIRECT_BASE = "https://api.minimax.io/v1"
# Legacy CommandCode free tier (kept as fallback if MINIMAX_API_KEY missing)
_MINIMAX_FREE_MODEL = "minimax/minimax-m3-free"
_MINIMAX_FREE_BASE = "https://api.commandcode.ai/provider/v1"
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


def _minimax_api_key() -> str | None:
    """Read MINIMAX_API_KEY from env or local .env or ~/.hermes/.env (same as hermes minimax-v1)."""
    v = os.getenv("MINIMAX_API_KEY")
    if v and not v.strip().startswith("#"):
        return v.strip().strip('"').strip("'")
    import pathlib, re as _re
    search_paths = (
        pathlib.Path(".env"),
        pathlib.Path("sectors-hackathon/.env"),
        pathlib.Path(__file__).resolve().parents[3] / ".env",
        pathlib.Path.home() / ".hermes/.env",
        pathlib.Path.home() / ".env",
    )
    for pp in search_paths:
        if pp.exists():
            try:
                mm = _re.search(r'^MINIMAX_API_KEY\s*=\s*"?([^"\n]+)"?', pp.read_text(), re.M)
                if mm and not mm.group(1).strip().startswith("#"):
                    key = mm.group(1).strip().strip('"').strip("'")
                    if key and key != "your_minimax_api_key_here":
                        return key
            except Exception:
                pass
    return None


def minimax_model(
    model: str | None = None,
    api_key: str | None = None,
    api_base: str | None = None,
    num_retries: int | None = None,
) -> BaseLlm:
    """Return a LiteLlm BaseLlm for MiniMax — DIRECT, like hermes custom_providers minimax-v1.

    Direct: MiniMax-M3 @ https://api.minimax.io/v1 with MINIMAX_API_KEY from
    ~/.hermes/.env (same key hermes uses for minimax-v1). Proven: tool calling
    works (calc_wacc tool_call verified) and content works via minimax/MiniMax-M3.

    Fallback: if MINIMAX_API_KEY missing, uses CommandCode minimax-m3-free
    @ https://api.commandcode.ai/provider/v1 with COMMANDCODE_API_KEY.

    num_retries: default 2 for direct (stable), 3 for CommandCode free (503-prone).
    """
    if not _litellm_available():
        raise ImportError("litellm not installed — pip install litellm or google-adk[extensions]")
    from google.adk.models.lite_llm import LiteLlm
    import pathlib, re as _re

    # Prefer direct MiniMax (hermes style) — stable, tool calling verified
    direct_key = api_key or _minimax_api_key()
    if direct_key:
        model_id = model or os.getenv("MINIMAX_MODEL") or _MINIMAX_DIRECT_MODEL
        base = api_base or os.getenv("MINIMAX_BASE_URL") or _MINIMAX_DIRECT_BASE
        retries = num_retries if num_retries is not None else int(os.getenv("MINIMAX_NUM_RETRIES", "2"))
        try:
            import litellm as _l
            _l.num_retries = max(_l.num_retries or 0, retries)
        except Exception:
            pass
        return LiteLlm(
            model=f"minimax/{model_id}",
            api_base=base,
            api_key=direct_key,
            max_tokens=4096,
            num_retries=retries,
            timeout=int(os.getenv("MINIMAX_TIMEOUT", "90")),
        )
    # Fallback: CommandCode free tier
    key = os.getenv("COMMANDCODE_API_KEY") or ""
    if not key:
        p = pathlib.Path.home()/".config"/"commandcode-bridge"/"env"
        if p.exists():
            try:
                txt2 = p.read_text()
                m = _re.search(r'COMMANDCODE_API_KEY="([^"]+)"', txt2)
                if m:
                    key = m.group(1).strip()
            except Exception:
                pass
    if not key:
        raise ValueError("No MiniMax key — set MINIMAX_API_KEY in ~/.hermes/.env (preferred, like hermes minimax-v1) or COMMANDCODE_API_KEY")
    model_id = model or os.getenv("MINIMAX_MODEL") or _MINIMAX_FREE_MODEL
    base = api_base or os.getenv("MINIMAX_API_BASE") or _MINIMAX_FREE_BASE
    retries = num_retries if num_retries is not None else int(os.getenv("MINIMAX_NUM_RETRIES", "3"))
    try:
        import litellm as _l
        _l.num_retries = max(_l.num_retries or 0, retries)
    except Exception:
        pass
    return LiteLlm(
        model=f"openai/{model_id}",
        api_base=base,
        api_key=key,
        max_tokens=4096,
        num_retries=retries,
        timeout=int(os.getenv("MINIMAX_TIMEOUT", "120")),
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
    if name in ("minimax", "minimax-m3", "minimax-m3-free", "minimax/minimax-m3-free", "minimax-free", "minimax_m3_free"):
        return minimax_model(**kw)
    if name in ("deepseek", "deepseek-chat", "deepseek-reasoner", "deepseek-v3", "deepseek-r1"):
        # normalize model aliases
        model = kw.pop("model", None)
        if name not in ("deepseek",):
            model = name if "/" not in name else model
        return deepseek_model(model=model, **kw)
    if name in ("gemini", "google", "gemini-2.0-flash", "gemini-flash", "gemini-2.5-flash"):
        return gemini_model(**kw)
    raise ValueError(f"Unknown provider {name!r} — expected 'spark'|'deepseek'|'gemini'")
