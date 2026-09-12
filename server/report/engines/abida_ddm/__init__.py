"""Abida's DDM engine, math modules only (github.com/abidamassi/ddm_tool).

Copied verbatim so the dividend branch of deck slide 4 uses the engine's arithmetic rather than a
re-implementation. Same rule as the DCF vendor: the math is taken, the fetch layer is not.
"""

import pathlib
import sys

_HERE = str(pathlib.Path(__file__).resolve().parent)
if _HERE not in sys.path:
    sys.path.append(_HERE)

from ddm_config import DDM_ASSUMPTIONS as ENGINE_ASSUMPTIONS  # noqa: E402
from d05_terminal import terminal_value  # noqa: E402
from d06_valuation import discount_dividends, value_bridge_table  # noqa: E402
from d07_crosscheck import compare_methods, fair_pbv, residual_income  # noqa: E402
from d08_sensitivity import sensitivity_grid  # noqa: E402

__all__ = ["terminal_value", "discount_dividends", "value_bridge_table", "fair_pbv",
           "residual_income", "compare_methods", "sensitivity_grid", "ENGINE_ASSUMPTIONS"]
