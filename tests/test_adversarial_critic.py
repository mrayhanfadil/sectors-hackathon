"""
Unit and Acceptance Tests for T09: Adversarial Red Team + Critic Arbiter.

Run:  python -m unittest tests/test_adversarial_critic.py
      or python tests/run_tests.py

Covers:
  1. QA Critic Numbers == Table Audit (Cover TP vs Valuation FV, upside math, one-off -72%)
  2. QA Critic Weights == 100% Audit (Blended 60/40, SOTP pillars, segment mix, rejection on != 100%)
  3. QA Critic Source per Exhibit Audit (Rejection on missing/null/empty exhibit source)
  4. QA Critic DDM Payout Math Audit (CoE > g, Payout * EPS == DPS)
  5. QA Critic KPI Tenancy Ratio Formula Audit (Tenancy == Tenants / Towers)
  6. QA Critic Anti-Sycophancy Gate (REJECT agree-without-evidence, accept verified defenses/corrections)
  7. Adversarial Red Team 2-Round Duel (RATU, CDIA, MTEL, BBCA, ADRO)
  8. Adversarial Red Team Interactive User Challenge (WACC, Tenancy, One-offs, Anti-Sycophancy)
  9. File Output Verification (debate.json, critic_audit.json, debate_user.json)
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "agents"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from critic import CriticEngine, audit_report, audit_ticker, evaluate_debate_turn
from adversarial import AdversarialRedTeam, challenge, run_duel


class TestCriticArbiter(unittest.TestCase):
    def setUp(self):
        self.critic = CriticEngine()

    def test_numbers_tp_match(self):
        """Cover TP matching valuation DCF / Blended FV passes."""
        report = {
            "ticker": "RATU",
            "cover": {"rating_box": {"tp": 7880, "price": 6200, "upside_pct": 27.1}},
            "valuation": {"methods": [{"method": "DCF", "fv": 7880, "source": "DCF Engine"}]},
            "source": "IDX",
        }
        res = self.critic.audit_numbers(report)
        tp_check = next((c for c in res if c.name == "target_price_consistency"), None)
        self.assertIsNotNone(tp_check)
        self.assertTrue(tp_check.passed)

    def test_numbers_tp_mismatch_rejected(self):
        """Cover TP not matching valuation FV is flagged."""
        report = {
            "ticker": "RATU",
            "cover": {"rating_box": {"tp": 9999, "price": 6200, "upside_pct": 27.1}},
            "valuation": {"methods": [{"method": "DCF", "fv": 7880, "source": "DCF Engine"}]},
            "source": "IDX",
        }
        res = self.critic.audit_numbers(report)
        tp_check = next((c for c in res if c.name == "target_price_consistency"), None)
        self.assertIsNotNone(tp_check)
        self.assertFalse(tp_check.passed)

    def test_one_off_normalization_delta(self):
        """CDIA one-off normalization invariant (15.9mn -> net -72%)."""
        report = {
            "ticker": "CDIA",
            "one_offs": {
                "reported_net_income_mn": 17225.0,
                "tax_rate": 0.22,
                "items": [{"label": "Asset sale & FX one-off", "amount_mn": 15900.0}],
                "delta_pct": -72.0,
            },
            "source": "BCA Sekuritas",
        }
        res = self.critic.audit_numbers(report)
        one_off_check = next((c for c in res if c.name == "one_off_normalization_math"), None)
        self.assertIsNotNone(one_off_check)
        self.assertTrue(one_off_check.passed)

    def test_weights_sum_blended_100(self):
        """Blended weights summing to 1.0 (60% + 40%) passes."""
        report = {
            "ticker": "MTEL",
            "valuation": {
                "blended": {
                    "weights": {"DCF": 0.60, "EV/EBITDA": 0.40},
                    "target_price": 635,
                }
            },
            "source": "KSI Research",
        }
        res = self.critic.audit_weights(report)
        w_check = next((c for c in res if c.name == "blended_weights_sum_100"), None)
        self.assertIsNotNone(w_check)
        self.assertTrue(w_check.passed)

    def test_weights_sum_blended_mismatch_rejected(self):
        """Blended weights not summing to 1.0 (60% + 30% = 90%) is rejected."""
        report = {
            "ticker": "MTEL",
            "valuation": {
                "blended": {
                    "weights": {"DCF": 0.60, "EV/EBITDA": 0.30},
                    "target_price": 635,
                }
            },
            "source": "KSI Research",
        }
        res = self.critic.audit_weights(report)
        w_check = next((c for c in res if c.name == "blended_weights_sum_100"), None)
        self.assertIsNotNone(w_check)
        self.assertFalse(w_check.passed)

    def test_sotp_pillars_sum_100(self):
        """SOTP pillars summing to 100% passes."""
        report = {
            "ticker": "CDIA",
            "sotp": {
                "pillars": [
                    {"name": "Energy", "pct": 55.0},
                    {"name": "Logistics", "pct": 34.0},
                    {"name": "Water", "pct": 6.0},
                    {"name": "Port", "pct": 5.0},
                ]
            },
            "source": "BCA Sekuritas",
        }
        res = self.critic.audit_weights(report)
        sotp_check = next((c for c in res if c.name == "sotp_pillars_sum_100"), None)
        self.assertIsNotNone(sotp_check)
        self.assertTrue(sotp_check.passed)

    def test_sources_missing_rejected(self):
        """Exhibits with missing source are strictly rejected."""
        report = {
            "ticker": "TEST",
            "risks": [
                {"bucket": "Risk 1", "detail": "Detail", "source": "IDX"},
                {"bucket": "Risk 2", "detail": "Detail", "source": None},  # missing
            ],
            "source": None,
        }
        res = self.critic.audit_sources(report)
        src_check = next((c for c in res if c.name == "source_per_exhibit_audit"), None)
        self.assertIsNotNone(src_check)
        self.assertFalse(src_check.passed)

    def test_ddm_math_and_discount(self):
        """DDM CoE > g and Payout * EPS == DPS verified."""
        report = {
            "ticker": "BANK",
            "valuation": {
                "ddm": {
                    "coe": 0.10,
                    "g_terminal": 0.03,
                    "payout_ratio": 0.40,
                    "eps": 500.0,
                    "dps": 200.0,
                    "fv": 810,
                }
            },
            "source": "Bank model",
        }
        res = self.critic.audit_ddm(report)
        disc_check = next((c for c in res if c.name == "ddm_discount_rate_sanity"), None)
        dps_check = next((c for c in res if c.name == "ddm_payout_eps_dps_math"), None)
        self.assertTrue(disc_check.passed)
        self.assertTrue(dps_check.passed)

    def test_kpi_tenancy_ratio_formula(self):
        """Tenancy ratio = Tenants / Towers formula verified."""
        report = {
            "ticker": "MTEL",
            "kpi": {
                "towers": 40563,
                "tenants": 63866,
                "tenancy_ratio": 1.57,
            },
            "source": "KSI Research",
        }
        res = self.critic.audit_kpis(report)
        kpi_check = next((c for c in res if c.name == "kpi_tenancy_ratio_formula"), None)
        self.assertIsNotNone(kpi_check)
        self.assertTrue(kpi_check.passed)

    def test_kpi_tenancy_ratio_mismatch_rejected(self):
        """Tenancy ratio mismatch with raw towers/tenants is rejected."""
        report = {
            "ticker": "MTEL",
            "kpi": {
                "towers": 40563,
                "tenants": 63866,
                "tenancy_ratio": 1.95,  # wrong ratio
            },
            "source": "KSI Research",
        }
        res = self.critic.audit_kpis(report)
        kpi_check = next((c for c in res if c.name == "kpi_tenancy_ratio_formula"), None)
        self.assertIsNotNone(kpi_check)
        self.assertFalse(kpi_check.passed)

    def test_anti_sycophancy_agree_without_evidence_rejected(self):
        """Critic REJECTS 'agree without evidence' when defender blindly concedes."""
        turn_verdict = evaluate_debate_turn(
            round_idx=1,
            challenger="Red Team",
            claim="WACC 8.4% is wrong, should be 15%",
            defense_type="concede",
            evidence="I agree with you, 8.4% is probably wrong.",  # sycophancy without calc/source
        )
        self.assertEqual(turn_verdict["status"], "REJECT")
        self.assertEqual(turn_verdict["verdict"], "REJECT_AGREE_WITHOUT_EVIDENCE")

    def test_anti_sycophancy_verified_defense_accepted(self):
        """Critic accepts defense with concrete calc and verified source."""
        turn_verdict = evaluate_debate_turn(
            round_idx=1,
            challenger="Red Team",
            claim="WACC 8.4% is too low vs MTEL 10.1%",
            defense_type="defend",
            evidence={
                "argument": "WACC is 8.4% due to We 85%, CoE 10.0%, Wd 15%, CoD 3.5% * (1-0.22).",
                "calc": {"wacc": 8.4, "coe": 10.0, "rf": 6.2, "beta": 0.70, "erp": 6.9},
                "source": "HP Sekuritas RATU Initiation p.6; Exhibit 3",
            },
        )
        self.assertEqual(turn_verdict["status"], "PASS")
        self.assertEqual(turn_verdict["verdict"], "DEFENDED")


class TestAdversarialRedTeam(unittest.TestCase):
    def setUp(self):
        self.red_team = AdversarialRedTeam(max_rounds=2)

    def test_internal_duel_ratu(self):
        """RATU 2-round duel passes and writes debate.json."""
        res = self.red_team.run_duel("RATU", max_rounds=2)
        self.assertEqual(res.ticker, "RATU")
        self.assertEqual(res.rounds_count, 2)
        self.assertTrue(res.passed_audit)
        self.assertEqual(res.final_verdict, "DEFENDED")
        self.assertTrue(os.path.exists(os.path.join(REPO_ROOT, "out", "RATU", "debate.json")))

    def test_internal_duel_cdia(self):
        """CDIA 2-round duel passes with one-off and SOTP defense."""
        res = self.red_team.run_duel("CDIA", max_rounds=2)
        self.assertEqual(res.ticker, "CDIA")
        self.assertEqual(res.rounds_count, 2)
        self.assertTrue(res.passed_audit)
        self.assertEqual(res.final_verdict, "DEFENDED")

    def test_internal_duel_mtel(self):
        """MTEL 2-round duel passes with tenancy KPI and blended valuation defense."""
        res = self.red_team.run_duel("MTEL", max_rounds=2)
        self.assertEqual(res.ticker, "MTEL")
        self.assertEqual(res.rounds_count, 2)
        self.assertTrue(res.passed_audit)
        self.assertEqual(res.final_verdict, "DEFENDED")

    def test_internal_duel_adro(self):
        """ADRO 2-round duel passes with holdco discount SOTP defense."""
        res = self.red_team.run_duel("ADRO", max_rounds=2)
        self.assertEqual(res.ticker, "ADRO")
        self.assertEqual(res.rounds_count, 2)
        self.assertTrue(res.passed_audit)

    def test_internal_duel_bbca(self):
        """BBCA 2-round duel passes with GGM P/BV defense."""
        res = self.red_team.run_duel("BBCA", max_rounds=2)
        self.assertEqual(res.ticker, "BBCA")
        self.assertEqual(res.rounds_count, 2)
        self.assertTrue(res.passed_audit)

    def test_interactive_user_challenge_wacc(self):
        """Interactive challenge on WACC returns grounded defense with exact formula."""
        res = asyncio.run(challenge("RATU", "Is WACC 8.4% too low vs MTEL 10.1%?"))
        self.assertEqual(res["verdict"], "defend")
        self.assertEqual(res["critic_verdict"], "PASS")
        self.assertIn("8.4", res["evidence"])
        self.assertIn("CoE", res["evidence"])
        self.assertIsNotNone(res["calc"])
        self.assertIsNotNone(res["source"])

    def test_interactive_user_challenge_tenancy(self):
        """Interactive challenge on Tenancy returns exact calculation."""
        res = asyncio.run(challenge("MTEL", "Tenancy ratio 1.57x is impossible with 40k towers"))
        self.assertEqual(res["verdict"], "defend")
        self.assertEqual(res["critic_verdict"], "PASS")
        self.assertIn("63,866", res["evidence"])
        self.assertIn("40,563", res["evidence"])

    def test_interactive_user_challenge_one_off(self):
        """Interactive challenge on One-off returns exact -72.0% math."""
        res = asyncio.run(challenge("CDIA", "Why normalize one-off 15.9mn?"))
        self.assertEqual(res["verdict"], "defend")
        self.assertEqual(res["critic_verdict"], "PASS")
        self.assertIn("-72.0%", res["evidence"])
        self.assertIn("4,823", res["evidence"])


if __name__ == "__main__":
    unittest.main()
