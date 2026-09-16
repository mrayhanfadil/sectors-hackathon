"""FCFF / DCF engine - the valuation arithmetic this repo runs.

A pure calculator: it fetches nothing and imports no network client, so a PDF render stays offline and
deterministic. Inputs come from `data/assumptions/<ticker>.json` and the Sectors payload.

Exposed entry points:
    cost_of_equity   CAPM cost of equity
    cost_of_debt     pre-tax cost of debt from the statements
    terminal_value   Gordon terminal value plus the implied exit multiple
    discount_and_value   discounting of the explicit period and the bridge to equity
    sensitivity_grid     WACC x terminal-growth grid
"""

import pathlib
import sys

_HERE = str(pathlib.Path(__file__).resolve().parent)
if _HERE not in sys.path:
    sys.path.append(_HERE)

from config import ASSUMPTIONS as ENGINE_ASSUMPTIONS  # noqa: E402
from s06_wacc import cost_of_debt, cost_of_equity  # noqa: E402
from s08_terminal import check_tv_dependency, terminal_value  # noqa: E402
from s09_valuation import bridge_table, discount_and_value  # noqa: E402
from s11_sensitivity import sensitivity_grid  # noqa: E402

__all__ = ["cost_of_equity", "cost_of_debt", "terminal_value", "check_tv_dependency",
           "discount_and_value", "bridge_table", "sensitivity_grid", "ENGINE_ASSUMPTIONS"]
