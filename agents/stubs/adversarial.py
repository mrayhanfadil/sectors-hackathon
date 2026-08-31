"""Stub / re-export for Adversarial Red Team agent."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from adversarial import AdversarialRedTeam, challenge, run_duel  # noqa: F401

__all__ = ["AdversarialRedTeam", "challenge", "run_duel"]
