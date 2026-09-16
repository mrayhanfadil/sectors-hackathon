# Copyright 2026 Sectors Hackathon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Stub agents - thin wrappers that delegate to agents/adk/ for single-ticker runs.

These stubs exist so other lanes (writer, backend, engines) can import
`agents.<name>` without depending on ADK. Each stub exposes a simple
async function that the lane owns; the orchestrator owns the graph.

For now each stub is a placeholder that re-exports the real ADK LlmAgent
factory for its lane. Lanes replace the body with real logic without
changing the orchestrator's import.
"""

from __future__ import annotations

STUB_AGENTS = [
    "collector",
    "news_harvester",
    "modeler",
    "analyst",
    "industry",
    "risk",
    "kpi",
    "writer",
    "visualizer",
    "sotp",
    "adversarial",
    "critic",
]

__all__ = ["STUB_AGENTS"]
