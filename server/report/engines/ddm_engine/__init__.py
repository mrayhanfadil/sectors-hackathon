"""Dividend-discount engine - the equity-side arithmetic this repo runs.

Same contract as the FCFF engine next to it: pure calculation, no fetching, inputs from the assumptions
file and the Sectors payload.

Exposed entry points:
    terminal_value        Gordon terminal value with the stable-phase payout test
    discount_dividends    discounting of DPS and the value per share
    fair_pbv              fair P/BV, used for the inverse cost-of-equity cross-check
    residual_income       residual income cross-check
    sensitivity_grid      cost of equity x long-term growth grid
"""

import pathlib
import sys

_HERE = str(pathlib.Path(__file__).resolve().parent)
if _HERE not in sys.path:
    sys.path.append(_HERE)

from d05_terminal import terminal_value  # noqa: E402
from d06_valuation import discount_dividends, value_bridge_table  # noqa: E402
from d07_crosscheck import compare_methods, fair_pbv, residual_income  # noqa: E402
from ddm_config import DDM_ASSUMPTIONS as ENGINE_ASSUMPTIONS  # noqa: E402
from d08_sensitivity import sensitivity_grid  # noqa: E402

__all__ = ["terminal_value", "discount_dividends", "value_bridge_table", "fair_pbv",
           "residual_income", "compare_methods", "sensitivity_grid", "ENGINE_ASSUMPTIONS"]
