# T05 stub — see agents/stubs/__init__.py
# The real collector lives in agents/adk/app.py (LlmAgent "collector" + Sectors MCP).
# This stub keeps the import path stable for lane T01.
from agents.adk.tools.mcp_sectors import sectors_mcp_toolset, maybe_sectors_mcp_toolset, SECTORS_MCP_URL
__all__ = ["sectors_mcp_toolset", "maybe_sectors_mcp_toolset", "SECTORS_MCP_URL"]
