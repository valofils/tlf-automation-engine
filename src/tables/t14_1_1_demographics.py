"""
Table 14.1.1 — Demographics and Baseline Characteristics
Summary statistics by treatment arm for the Safety Population.
ICH E3 Section 11.2 compliant structure.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from dataclasses import dataclass, field


@dataclass
class TableRow:
    label: str
    active: str
    placebo: str
    total: str
    indent: int = 0


def _n(df: pd.DataFrame) -> int:
    return len(df)


def _pct(num: int, den: int) -> str:
    if den == 0:
        return "0 (0.0%)"
    return f"{num} ({num/den*100:.1f}%)"


def _mean_sd(series: pd.Series) -> str:
    return f"{series.mean():.1f} ({series.std():.2f})"


def _median_range(series: pd.Series) -> str:
    return f"{series.median():.1f} ({series.min():.0f}, {series.max():.0f})"


def build_t14_1_1(adsl: pd.DataFrame) -> list[TableRow]:
    """
    Build Table 14.1.1 — Demographics and Baseline Characteristics.
    Returns a list of TableRow objects for rendering.
    """
    safe = adsl[adsl["SAFFL"] == "Y"].copy()
    act  = safe[safe["TRT01AN"] == 1]
    pbo  = safe[safe["TRT01AN"] == 2]

    rows: list[TableRow] = []

    # Header counts
    rows.append(TableRow(
        "Number of subjects",
        str(_n(act)), str(_n(pbo)), str(_n(safe))
    ))

    # ── Age ────────────────────────────────────────────────────────
    rows.append(TableRow("Age (years)", "", "", "", indent=0))
    rows.append(TableRow("  Mean (SD)",
        _mean_sd(act["AGE"]), _mean_sd(pbo["AGE"]), _mean_sd(safe["AGE"]), indent=1))
    rows.append(TableRow("  Median (Min, Max)",
        _median_range(act["AGE"]), _median_range(pbo["AGE"]), _median_range(safe["AGE"]), indent=1))

    # Age groups
    rows.append(TableRow("Age group, n (%)", "", "", "", indent=0))
    for grp in ["<65", ">=65"]:
        a = (act["AGEGR1"] == grp).sum()
        p = (pbo["AGEGR1"] == grp).sum()
        t = (safe["AGEGR1"] == grp).sum()
        rows.append(TableRow(f"  {grp}",
            _pct(a, _n(act)), _pct(p, _n(pbo)), _pct(t, _n(safe)), indent=1))

    # ── Sex ────────────────────────────────────────────────────────
    rows.append(TableRow("Sex, n (%)", "", "", "", indent=0))
    for sex, label in [("M", "Male"), ("F", "Female")]:
        a = (act["SEX"] == sex).sum()
        p = (pbo["SEX"] == sex).sum()
        t = (safe["SEX"] == sex).sum()
        rows.append(TableRow(f"  {label}",
            _pct(a, _n(act)), _pct(p, _n(pbo)), _pct(t, _n(safe)), indent=1))

    # ── Race ───────────────────────────────────────────────────────
    rows.append(TableRow("Race, n (%)", "", "", "", indent=0))
    for race in sorted(safe["RACE"].unique()):
        a = (act["RACE"] == race).sum()
        p = (pbo["RACE"] == race).sum()
        t = (safe["RACE"] == race).sum()
        rows.append(TableRow(f"  {race.title()}",
            _pct(a, _n(act)), _pct(p, _n(pbo)), _pct(t, _n(safe)), indent=1))

    # ── BMI ────────────────────────────────────────────────────────
    if "BMIBL" in safe.columns:
        rows.append(TableRow("BMI at baseline (kg/m²)", "", "", "", indent=0))
        rows.append(TableRow("  Mean (SD)",
            _mean_sd(act["BMIBL"]), _mean_sd(pbo["BMIBL"]), _mean_sd(safe["BMIBL"]), indent=1))
        rows.append(TableRow("  Median (Min, Max)",
            _median_range(act["BMIBL"]), _median_range(pbo["BMIBL"]), _median_range(safe["BMIBL"]), indent=1))

    # ── Weight ─────────────────────────────────────────────────────
    if "WEIGHTBL" in safe.columns:
        rows.append(TableRow("Weight at baseline (kg)", "", "", "", indent=0))
        rows.append(TableRow("  Mean (SD)",
            _mean_sd(act["WEIGHTBL"]), _mean_sd(pbo["WEIGHTBL"]), _mean_sd(safe["WEIGHTBL"]), indent=1))

    return rows


def to_dataframe(rows: list[TableRow]) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "Parameter": r.label,
            "Active Drug 100mg": r.active,
            "Placebo": r.placebo,
            "Total": r.total,
        }
        for r in rows
    ])
