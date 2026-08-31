"""Stub / re-export for QA Critic agent."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from critic import CriticEngine, audit_report, audit_ticker, evaluate_debate_turn  # noqa: F401

__all__ = ["CriticEngine", "audit_report", "audit_ticker", "evaluate_debate_turn"]
