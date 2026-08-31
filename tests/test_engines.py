"""Unit tests for deterministic valuation engines (DCF, DDM, SOTP, Blended, Bands, GGM)."""

import unittest
from scripts.dcf_engine import wacc, dcf, ev_ebitda, index_target
from scripts.ddm_engine import ddm, dps_from_payout
from scripts.sotp_engine import sotp
from scripts.blended_engine import blended
from scripts.bands_engine import calc_bands, historical_bands
from scripts.ggm_engine import ggm, implied_coe, implied_roe, implied_g


class TestDeterministicEngines(unittest.TestCase):
    def test_ratu_dcf_replication(self):
        """Replicate RATU DCF 7,880 within +/- 2.0% tolerance."""
        res = dcf(
            fcf=[410.0, 432.0, 455.0],
            wacc=0.084,
            g_terminal=0.05,
            shares_out=2.71,
            cash=9219.9,
        )
        fv = res["fv_per_share"]
        ref = 7880.0
        err = abs(fv - ref) / ref * 100.0
        self.assertLessEqual(err, 2.0, f"RATU DCF error {err:.3f}% exceeds 2%")
        self.assertAlmostEqual(fv, 7879.88, places=1)

    def test_ratu_ev_ebitda_replication(self):
        """Replicate RATU EV/EBITDA 22.6x -> 6,960 within +/- 2.0% tolerance."""
        res = ev_ebitda(
            ebitda=585.0,
            multiple=22.6,
            shares_out=2.71,
            net_debt=-5640.6,
        )
        fv = res["fv_per_share"]
        ref = 6960.0
        err = abs(fv - ref) / ref * 100.0
        self.assertLessEqual(err, 2.0, f"RATU EV/EBITDA error {err:.3f}% exceeds 2%")
        self.assertEqual(fv, 6960.0)

    def test_cdia_ddm_replication(self):
        """Replicate CDIA DDM 810 within +/- 2.0% tolerance."""
        res = ddm(
            dividends=[35.6, 88.8],
            coe=0.14,
            g_terminal=0.04,
            per_share=True,
        )
        fv = res["fv_per_share"]
        ref = 810.0
        err = abs(fv - ref) / ref * 100.0
        self.assertLessEqual(err, 2.0, f"CDIA DDM error {err:.3f}% exceeds 2%")
        self.assertAlmostEqual(fv, 810.18, places=1)

    def test_cdia_sotp_replication(self):
        """Replicate CDIA SOTP 4 pillars within +/- 2.0% tolerance."""
        res = sotp(
            segments=[
                {"name": "Energi", "value": 7700.0, "method": "ev_ebitda"},
                {"name": "Logistik", "value": 4900.0, "method": "ev_ebitda"},
                {"name": "Air", "value": 1040.0, "method": "pe"},
                {"name": "Pelabuhan", "value": 780.0, "method": "ev_ebitda"},
            ],
            holdco_discount=0.15,
            shares_out=15.0,
        )
        fv = res["fv_per_share"]
        ref = 815.0
        err = abs(fv - ref) / ref * 100.0
        self.assertLessEqual(err, 2.0, f"CDIA SOTP error {err:.3f}% exceeds 2%")
        self.assertAlmostEqual(fv, 817.13, places=1)

    def test_mtel_blended_replication(self):
        """Replicate MTEL Blended 60% DCF + 40% EV/EBITDA -> 635 (MoS 15%) within +/- 2.0%."""
        res = blended(
            valuations={"DCF": 51556.0, "EV/EBITDA": 74513.0},
            weights={"DCF": 0.60, "EV/EBITDA": 0.40},
            margin_of_safety=0.15,
            shares_out=81.5,
        )
        tp = res["target_price"]
        ref = 635.0
        err = abs(tp - ref) / ref * 100.0
        self.assertLessEqual(err, 2.0, f"MTEL Blended error {err:.3f}% exceeds 2%")
        self.assertAlmostEqual(tp, 633.47, places=1)

    def test_bbca_ggm_replication(self):
        """Replicate BBCA GGM P/BV=3.30 (TP 9,600) within +/- 2.0%."""
        res = ggm(
            roe=0.197,
            coe=0.10848,
            g=0.07,
            bvps=2909.09,
        )
        pbv = res["pbv_implied"]
        ref_pbv = 3.30
        err_pbv = abs(pbv - ref_pbv) / ref_pbv * 100.0
        self.assertLessEqual(err_pbv, 2.0, f"BBCA GGM PBV error {err_pbv:.3f}% exceeds 2%")
        self.assertAlmostEqual(pbv, 3.30, places=2)
        self.assertAlmostEqual(res["fv_per_share"], 9601.21, places=0)

    def test_jpm_jci_replication(self):
        """Replicate JPM JCI 9,100 (8% EPS growth x 15x multiple) within +/- 2.0%."""
        res = index_target(
            current=8425.926,
            eps_growth=0.08,
            multiple=1.0,
        )
        target = res["index_target"]
        ref = 9100.0
        err = abs(target - ref) / ref * 100.0
        self.assertLessEqual(err, 2.0, f"JPM JCI error {err:.3f}% exceeds 2%")
        self.assertEqual(target, 9100.0)

    def test_bands_engine(self):
        """Test statistical bands calculation and positioning labels."""
        series = [10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 26.0, 28.0]
        res = calc_bands(series, current=13.0, metric_name="P/E")
        self.assertEqual(res["avg"], 19.0)
        self.assertIn("bands", res)
        self.assertEqual(res["current"]["label"], "-1SD TO -2SD")

    def test_ggm_solvers(self):
        """Test GGM inverse analytical solvers (implied CoE, ROE, g)."""
        coe_res = implied_coe(pbv=3.30, roe=0.197, g=0.07)
        self.assertAlmostEqual(coe_res["implied_coe"], 0.10848, places=4)
        roe_res = implied_roe(pbv=3.30, coe=0.10848, g=0.07)
        self.assertAlmostEqual(roe_res["implied_roe"], 0.197, places=3)
        g_res = implied_g(pbv=3.30, roe=0.197, coe=0.10848)
        self.assertAlmostEqual(g_res["implied_g"], 0.07, places=3)


if __name__ == "__main__":
    unittest.main()
