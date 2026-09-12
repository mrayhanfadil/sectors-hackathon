"""Abida's DCF engine, math modules only.

Files in this directory are copied verbatim from
https://github.com/abidamassi/dcf-valuation-tool so that the deck's valuation arithmetic is the
engine's arithmetic rather than a re-implementation of it. They import each other by bare module
name (`from config import ASSUMPTIONS`), which is how they run upstream, so this package puts its
own directory on `sys.path` and re-exports the entry points the report needs.

Anchoring note: the engine is a pure calculator. Which numbers go IN is the analyst's job and comes
from `data/assumptions/<ticker>.json` + the Sectors payload, never from a live fetch at render time.
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

__all__ = [
    "cost_of_equity",
    "cost_of_debt",
    "terminal_value",
    "check_tv_dependency",
    "discount_and_value",
    "bridge_table",
    "sensitivity_grid",
    "ENGINE_ASSUMPTIONS",
]
