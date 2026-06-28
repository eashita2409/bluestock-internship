"""
recommender.py
==============
Bluestock Mutual Fund Capstone – D6 Advanced Analytics
Rule-based Mutual Fund Recommendation Engine

Author  : Bluestock Internship Team
Created : 2026
Version : 1.0

Usage
-----
from scripts.recommender import MutualFundRecommender
rec = MutualFundRecommender()
results = rec.recommend(risk_appetite='Moderate', horizon=5, preferred_category='Large Cap')
print(results)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Path Setup
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUT_CSV = DATA_PROCESSED / "recommendations.csv"


# ---------------------------------------------------------------------------
# Constants & Configuration
# ---------------------------------------------------------------------------

# Risk appetite → allowed risk grades
RISK_ALLOWED: dict[str, list[str]] = {
    "Conservative": ["Low"],
    "Moderate":     ["Low", "Moderate", "Moderately High"],
    "Aggressive":   ["Low", "Moderate", "Moderately High", "High", "Very High"],
}

# Risk appetite → scoring weights for [Sharpe, CAGR, Volatility, MaxDrawdown]
# MaxDrawdown and Volatility are *inverted* (lower = better)
SCORING_WEIGHTS: dict[str, dict[str, float]] = {
    "Conservative": {
        "sharpe_ratio":     0.40,
        "return_3yr_pct":   0.25,
        "std_dev_ann_pct":  0.20,   # inverted
        "max_drawdown_pct": 0.15,   # inverted (less negative = better)
    },
    "Moderate": {
        "sharpe_ratio":     0.30,
        "return_3yr_pct":   0.35,
        "std_dev_ann_pct":  0.15,   # inverted
        "max_drawdown_pct": 0.20,   # inverted
    },
    "Aggressive": {
        "sharpe_ratio":     0.20,
        "return_3yr_pct":   0.45,
        "std_dev_ann_pct":  0.10,   # inverted
        "max_drawdown_pct": 0.25,   # inverted
    },
}

# Minimum horizon (years) required per category
MIN_HORIZON: dict[str, int] = {
    "Liquid":         0,
    "Gilt":           1,
    "Short Duration": 1,
    "Index":          3,
    "Index/ETF":      3,
    "Large Cap":      3,
    "Flexi Cap":      3,
    "Large & Mid Cap": 4,
    "Mid Cap":        5,
    "Value":          5,
    "ELSS":           3,
    "Small Cap":      7,
}

# Risk appetite → recommended horizons for explanation
HORIZON_LABELS: dict[str, str] = {
    "Conservative": "1–3 years",
    "Moderate":     "3–7 years",
    "Aggressive":   "7+ years",
}


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _minmax_scale(series: pd.Series) -> pd.Series:
    """Min-max normalise a series to [0, 1]. Returns 0.5 if constant."""
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series(0.5, index=series.index)
    return (series - lo) / (hi - lo)


def _load_performance_data() -> pd.DataFrame:
    """Load scheme performance data from the processed CSV."""
    perf_path = DATA_PROCESSED / "07_scheme_performance.csv"
    if not perf_path.exists():
        raise FileNotFoundError(f"Performance data not found: {perf_path}")
    df = pd.read_csv(perf_path)
    return df


def _load_fund_master() -> pd.DataFrame:
    """Load fund master data from the processed CSV."""
    master_path = DATA_PROCESSED / "01_fund_master.csv"
    if not master_path.exists():
        raise FileNotFoundError(f"Fund master data not found: {master_path}")
    df = pd.read_csv(master_path)
    return df


# ---------------------------------------------------------------------------
# MutualFundRecommender Class
# ---------------------------------------------------------------------------

class MutualFundRecommender:
    """
    Rule-based Mutual Fund Recommender.

    Scoring Methodology
    -------------------
    Each scheme receives a composite score in [0, 100] computed as a
    weighted sum of min-max normalised metrics:

        Score = Σ  weight_i × normalised_metric_i

    For risk metrics (Volatility, Max Drawdown), the *inverted* normalised
    value is used so that lower risk → higher score.

    The weights vary by risk appetite:
      - Conservative  : Sharpe 40% | CAGR 25% | Volatility 20% | MaxDD 15%
      - Moderate      : Sharpe 30% | CAGR 35% | Volatility 15% | MaxDD 20%
      - Aggressive    : Sharpe 20% | CAGR 45% | Volatility 10% | MaxDD 25%
    """

    def __init__(self) -> None:
        self._perf_df = _load_performance_data()
        self._master_df = _load_fund_master()
        # Merge launch_date from master for cohort context
        self._df = self._perf_df.merge(
            self._master_df[["amfi_code", "launch_date", "fund_manager",
                              "min_sip_amount", "min_lumpsum_amount"]],
            on="amfi_code",
            how="left",
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def recommend(
        self,
        risk_appetite: Literal["Conservative", "Moderate", "Aggressive"] = "Moderate",
        horizon: int = 5,
        preferred_category: str | None = None,
        plan: Literal["Regular", "Direct", "Both"] = "Both",
        top_n: int = 5,
    ) -> pd.DataFrame:
        """
        Generate top-N fund recommendations.

        Parameters
        ----------
        risk_appetite       : 'Conservative' | 'Moderate' | 'Aggressive'
        horizon             : Investment horizon in years (≥ 0)
        preferred_category  : Fund category string or None (all categories)
        plan                : 'Regular' | 'Direct' | 'Both'
        top_n               : Number of recommendations to return

        Returns
        -------
        pd.DataFrame with columns:
            rank, scheme_name, fund_house, category, plan, return_3yr_pct,
            sharpe_ratio, std_dev_ann_pct, max_drawdown_pct, morningstar_rating,
            recommendation_score, explanation
        """
        if risk_appetite not in RISK_ALLOWED:
            raise ValueError(f"risk_appetite must be one of {list(RISK_ALLOWED.keys())}")

        df = self._df.copy()

        # ── 1. Filter by plan ──────────────────────────────────────────
        if plan != "Both":
            df = df[df["plan"] == plan]

        # ── 2. Filter by risk grade ────────────────────────────────────
        allowed_risks = RISK_ALLOWED[risk_appetite]
        df = df[df["risk_grade"].isin(allowed_risks)]

        # ── 3. Filter by investment horizon ───────────────────────────
        def _horizon_ok(cat: str) -> bool:
            return horizon >= MIN_HORIZON.get(cat, 3)

        df = df[df["category"].apply(_horizon_ok)]

        # ── 4. Filter by preferred category ───────────────────────────
        if preferred_category and preferred_category.lower() not in ("all", "any", ""):
            df = df[df["category"].str.lower() == preferred_category.lower()]

        if df.empty:
            return pd.DataFrame(columns=["rank", "scheme_name", "recommendation_score",
                                         "explanation"])

        # ── 5. Score schemes ───────────────────────────────────────────
        weights = SCORING_WEIGHTS[risk_appetite]

        # Normalise each metric; invert risk metrics
        sharpe_norm   = _minmax_scale(df["sharpe_ratio"])
        cagr_norm     = _minmax_scale(df["return_3yr_pct"])
        vol_norm      = 1 - _minmax_scale(df["std_dev_ann_pct"])      # inverted
        maxdd_norm    = 1 - _minmax_scale(df["max_drawdown_pct"].abs()) # inverted

        score = (
            weights["sharpe_ratio"]     * sharpe_norm  +
            weights["return_3yr_pct"]   * cagr_norm    +
            weights["std_dev_ann_pct"]  * vol_norm      +
            weights["max_drawdown_pct"] * maxdd_norm
        ) * 100.0

        df = df.copy()
        df["recommendation_score"] = score.round(2)

        # ── 6. Rank and select top-N ───────────────────────────────────
        df = df.sort_values("recommendation_score", ascending=False).head(top_n)
        df["rank"] = range(1, len(df) + 1)

        # ── 7. Build human-readable explanation ────────────────────────
        df["explanation"] = df.apply(
            lambda row: self._build_explanation(row, risk_appetite, horizon, weights),
            axis=1,
        )

        # ── 8. Select output columns ───────────────────────────────────
        output_cols = [
            "rank", "amfi_code", "scheme_name", "fund_house", "category",
            "plan", "return_3yr_pct", "sharpe_ratio", "std_dev_ann_pct",
            "max_drawdown_pct", "morningstar_rating", "aum_crore",
            "recommendation_score", "explanation",
        ]
        result = df[output_cols].reset_index(drop=True)
        return result

    def batch_recommend(
        self,
        profiles: list[dict],
        save_csv: bool = True,
    ) -> pd.DataFrame:
        """
        Run recommendations for multiple investor profiles and optionally
        save all results to data/processed/recommendations.csv.

        Parameters
        ----------
        profiles : list of dicts, each with keys:
            investor_id, risk_appetite, horizon, preferred_category
        save_csv : whether to persist results

        Returns
        -------
        Combined pd.DataFrame of all recommendations.
        """
        all_results: list[pd.DataFrame] = []

        for profile in profiles:
            investor_id      = profile.get("investor_id", "Unknown")
            risk_appetite    = profile.get("risk_appetite", "Moderate")
            horizon          = profile.get("horizon", 5)
            preferred_cat    = profile.get("preferred_category", None)
            plan             = profile.get("plan", "Both")
            top_n            = profile.get("top_n", 5)

            recs = self.recommend(
                risk_appetite=risk_appetite,
                horizon=horizon,
                preferred_category=preferred_cat,
                plan=plan,
                top_n=top_n,
            )
            if not recs.empty:
                recs.insert(0, "investor_id", investor_id)
                recs.insert(1, "risk_appetite", risk_appetite)
                recs.insert(2, "horizon_years", horizon)
                recs.insert(3, "preferred_category", preferred_cat or "All")
                all_results.append(recs)

        if not all_results:
            return pd.DataFrame()

        combined = pd.concat(all_results, ignore_index=True)

        if save_csv:
            OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
            combined.to_csv(OUTPUT_CSV, index=False)
            print(f"[Recommender] Saved {len(combined)} recommendations → {OUTPUT_CSV}")

        return combined

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_explanation(
        row: pd.Series,
        risk_appetite: str,
        horizon: int,
        weights: dict[str, float],
    ) -> str:
        """Generate a natural-language explanation for a recommendation."""
        parts: list[str] = []

        # Risk alignment
        parts.append(
            f"Suitable for a {risk_appetite.lower()} investor with a "
            f"{horizon}-year horizon ({HORIZON_LABELS[risk_appetite]} recommended)."
        )

        # Return performance
        cagr = row.get("return_3yr_pct", float("nan"))
        if not np.isnan(cagr):
            parts.append(f"3-year CAGR of {cagr:.1f}% (weight: {weights['return_3yr_pct']*100:.0f}%).")

        # Risk-adjusted performance
        sharpe = row.get("sharpe_ratio", float("nan"))
        if not np.isnan(sharpe):
            quality = "excellent" if sharpe >= 1.0 else ("good" if sharpe >= 0.7 else "moderate")
            parts.append(
                f"Sharpe ratio of {sharpe:.2f} indicates {quality} risk-adjusted returns "
                f"(weight: {weights['sharpe_ratio']*100:.0f}%)."
            )

        # Volatility
        vol = row.get("std_dev_ann_pct", float("nan"))
        if not np.isnan(vol):
            vol_desc = "low" if vol <= 8 else ("moderate" if vol <= 16 else "high")
            parts.append(
                f"Annualised volatility of {vol:.1f}% ({vol_desc}; "
                f"weight: {weights['std_dev_ann_pct']*100:.0f}%)."
            )

        # Drawdown
        mdd = row.get("max_drawdown_pct", float("nan"))
        if not np.isnan(mdd):
            parts.append(
                f"Maximum drawdown of {mdd:.1f}% "
                f"(weight: {weights['max_drawdown_pct']*100:.0f}%)."
            )

        # Star rating
        rating = row.get("morningstar_rating", None)
        if rating and not np.isnan(float(rating)):
            parts.append(f"Morningstar rating: {'★' * int(rating)}.")

        # AUM
        aum = row.get("aum_crore", float("nan"))
        if not np.isnan(aum):
            parts.append(f"AUM: ₹{aum:,.0f} Cr.")

        return " ".join(parts)


# ---------------------------------------------------------------------------
# CLI Entry-Point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Quick demonstration: generate recommendations for three investor profiles
    and save results to data/processed/recommendations.csv.
    """
    recommender = MutualFundRecommender()

    profiles = [
        {
            "investor_id":        "INV-001",
            "risk_appetite":      "Conservative",
            "horizon":            2,
            "preferred_category": "Gilt",
            "plan":               "Regular",
            "top_n":              5,
        },
        {
            "investor_id":        "INV-002",
            "risk_appetite":      "Moderate",
            "horizon":            5,
            "preferred_category": "Large Cap",
            "plan":               "Both",
            "top_n":              5,
        },
        {
            "investor_id":        "INV-003",
            "risk_appetite":      "Aggressive",
            "horizon":            10,
            "preferred_category": "Small Cap",
            "plan":               "Regular",
            "top_n":              5,
        },
        {
            "investor_id":        "INV-004",
            "risk_appetite":      "Moderate",
            "horizon":            7,
            "preferred_category": None,   # All categories
            "plan":               "Both",
            "top_n":              10,
        },
        {
            "investor_id":        "INV-005",
            "risk_appetite":      "Aggressive",
            "horizon":            8,
            "preferred_category": "Mid Cap",
            "plan":               "Regular",
            "top_n":              5,
        },
    ]

    combined = recommender.batch_recommend(profiles, save_csv=True)
    print(combined[["investor_id", "risk_appetite", "rank", "scheme_name",
                     "recommendation_score"]].to_string(index=False))


if __name__ == "__main__":
    main()
