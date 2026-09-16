# server/scripts stub - re-export engines for T02 orchestrator import boundary
# T02 writes scripts/{dcf,ddm,sotp,blended,bands,ggm,news,adversarial,social}.py
# Server imports via scripts/* when present, else falls back to server/engines.
# This shim keeps the import path stable regardless of T02 landing order.
try:
    from server.engines import wacc, dcf, ddm, ev_ebitda, ggm, sotp, blended, historical_bands, ratios  # noqa
except Exception:
    pass
