"""Deterministic acceptance tests for T08 agents (no pytest dependency).

Run:  python tests/run_tests.py
Covers the task-brief invariants:
  1. Thesis: CDIA one-off 15.9 → net -72%
  2. Thesis: MTEL catalyst 3,000-3,500 tenants + 360-420bn by FY27-29
  3. SOTP: pillar pct sum == 100%, weights == 100%, holdco discount applied
  4. Visualizer: 8 mandated PNGs (9 incl. bands for infra), valid PNG magic
  5. templates/helpers.py exhibit fragments render without error
"""

from __future__ import annotations

import os
import sys
import traceback

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "agents"))
sys.path.insert(0, os.path.join(REPO_ROOT, "templates"))

import common  # noqa: E402,F401
import sotp as sotp_mod  # noqa: E402,F401
import visualizer as vis_mod  # noqa: E402,F401
import writer as writer_mod  # noqa: E402,F401
from helpers import normalization_exhibit, sotp_exhibit, thesis_exhibit  # noqa: E402,F401

PASS = 0
FAIL = 0
FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        msg = f"  FAIL  {name}" + (f"  ({detail})" if detail else "")
        FAILURES.append(msg)
        print(msg)


def png_ok(path: str) -> bool:
    if not path or not os.path.exists(path):
        return False
    with open(path, "rb") as fh:
        return fh.read(8) == b"\x89PNG\r\n\x1a\n"


def test_writer() -> None:
    print("[writer]")
    for tk in ("CDIA", "MTEL", "ADRO"):
        t = writer_mod.build_thesis(tk)
        check(f"{tk} thesis builds", bool(t["bull_case"]["headline"]))
        check(f"{tk} input fingerprint present", len(t["meta"]["input_fingerprint"]) == 12)

    c = writer_mod.build_thesis("CDIA")
    n = c["normalizations"]
    check("CDIA one-off gross == 15,900 mn", abs(n["gross_one_off_mn"] - 15900.0) < 1e-6, f"got {n['gross_one_off_mn']}")
    check("CDIA adjusted delta == -72.0%", abs(n["delta_pct"] - (-72.0)) < 0.05, f"got {n['delta_pct']}")
    check("CDIA adjusted net == 4,823 mn", abs(n["adjusted_net_income_mn"] - 4823.0) < 0.5, f"got {n['adjusted_net_income_mn']}")
    check("CDIA headline mentions one-off adj", "one-off" in c["bull_case"]["headline"] or "-72%" in c["bull_case"]["headline"])

    m = writer_mod.build_thesis("MTEL")
    cats = m["bull_case"]["catalysts"]
    q = next((c for c in cats if c["id"] == "MTEL-PST-UMT"), None)
    check("MTEL PST+UMT catalyst present", q is not None)
    if q:
        qs = q["quantified_struct"]
        check("MTEL tenants 3,000-3,500", qs["tenants_added_min"] == 3000 and qs["tenants_added_max"] == 3500)
        check("MTEL revenue 360,000-420,000 mn", qs["annualized_revenue_min_mn"] == 360000.0 and qs["annualized_revenue_max_mn"] == 420000.0)
        check("MTEL quantified string carries both", "3,000-3,500" in q["quantified"] and "360.0bn" in q["quantified"])
    kpi = m["kpi_highlights"]
    check("MTEL tenancy KPI 1.57x", any(k["kpi"] == "tenancy_ratio" and abs(k["value"] - 1.57) < 1e-9 for k in kpi))


def test_sotp() -> None:
    print("[sotp]")
    c = sotp_mod.build_sotp("CDIA")
    check("CDIA is conglomerate", c["conglomerate"])
    sc = c["sum_check"]
    check("CDIA pct sum == 100", abs(sc["pct_sum"] - 100.0) < 1e-6, f"got {sc['pct_sum']}")
    check("CDIA weight sum == 100", abs(sc["equity_weight_sum"] - 100.0) < 1e-6, f"got {sc['equity_weight_sum']}")
    check("CDIA sum_check.ok", sc["ok"])
    check("CDIA 4 pillars", c["pillar_count"] == 4)
    check("CDIA pre == post (no holdco)", abs(c["pre_discount_total_mn"] - c["post_discount_equity_mn"]) < 1e-6)
    check("CDIA discount 0%", c["holdco_discount_pct"] == 0.0)

    a = sotp_mod.build_sotp("ADRO")
    check("ADRO holdco discount 15%", abs(a["holdco_discount_pct"] - 0.15) < 1e-9, f"got {a['holdco_discount_pct']}")
    check("ADRO post = pre * 0.85", abs(a["post_discount_equity_mn"] - a["pre_discount_total_mn"] * 0.85) < 1e-6)
    check("ADRO sum_check.ok", a["sum_check"]["ok"])

    m = sotp_mod.build_sotp("MTEL")
    check("MTEL not conglomerate", not m["conglomerate"])


def test_visualizer() -> None:
    print("[visualizer]")
    MANDATED = {"revenue_mix", "trend", "margin", "leverage", "roe_roa", "vs_jci", "peer_multiples", "kpi"}
    for tk in ("CDIA", "MTEL", "ADRO"):
        manifest = vis_mod.run(tk)
        ids = {c["id"] for c in manifest["charts"]}
        missing = MANDATED - ids
        check(f"{tk} has all 8 mandated charts", not missing, f"missing: {missing}")
        check(f"{tk} chart count == 8 or 9", manifest["total"] in (8, 9), f"got {manifest['total']}")
        check(f"{tk} manifest has source per chart", all(c.get("source") for c in manifest["charts"]))
        charts_dir = os.path.join(common.ensure_out(tk), "charts")
        for c in manifest["charts"]:
            fname = c.get("file")
            if not fname:
                check(f"{tk} chart {c['id']} has file", False, "no file in manifest")
                continue
            full = os.path.join(charts_dir, os.path.basename(fname))
            check(f"{tk} chart {c['id']} exists", os.path.exists(full), full)
            check(f"{tk} {c['id']} is valid PNG", png_ok(full), full)
    mtel_ids = {c["id"] for c in vis_mod.run("MTEL")["charts"]}
    check("MTEL has bands chart (infra)", "bands" in mtel_ids)


def test_helpers() -> None:
    print("[helpers]")
    c = writer_mod.build_thesis("CDIA")
    frag = thesis_exhibit(c)
    check("thesis_exhibit renders", "Bull Case" in frag)
    frag2 = normalization_exhibit(c)
    check("normalization_exhibit renders -72%", "-72.0%" in frag2 and "4,823" in frag2)
    s = sotp_mod.build_sotp("CDIA")
    frag3 = sotp_exhibit(s)
    check("sotp_exhibit renders sum=100% badge", "sum = 100%" in frag3)
    check("sotp_exhibit has post-discount equity", "Post-discount equity" in frag3)


def main() -> None:
    print(f"T08 acceptance tests — repo {REPO_ROOT}\n")
    for fn in (test_writer, test_sotp, test_visualizer, test_helpers):
        try:
            fn()
        except Exception:
            global FAIL
            FAIL += 1
            print(f"  ERROR in {fn.__name__}:")
            traceback.print_exc()
    print(f"\n{'=' * 52}\nPASS {PASS}  FAIL {FAIL}")
    if FAILURES:
        print("\nFailures:")
        for f in FAILURES:
            print(f)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
