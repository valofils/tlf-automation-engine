"""
Table 14.2.1 — Summary of Adverse Events
Treatment-emergent adverse events by treatment arm — Safety Population.
Follows ICH E3 / CIOMS III reporting conventions.
"""

from __future__ import annotations
import pandas as pd
from dataclasses import dataclass


@dataclass
class AERow:
    label: str
    active_n: str
    active_pct: str
    placebo_n: str
    placebo_pct: str
    indent: int = 0


def _n_subj(df: pd.DataFrame) -> int:
    return df["USUBJID"].nunique()


def _subj_pct(ae_df: pd.DataFrame, arm_total: int, **filters) -> tuple[int, str]:
    sub = ae_df.copy()
    for col, val in filters.items():
        sub = sub[sub[col] == val]
    n = sub["USUBJID"].nunique()
    pct = f"{n/arm_total*100:.1f}" if arm_total else "0.0"
    return n, f"{n} ({pct}%)"


def build_t14_2_1(adae: pd.DataFrame, adsl: pd.DataFrame) -> list[AERow]:
    """
    Build Table 14.2.1 — Adverse Events Summary.
    Only treatment-emergent AEs (TRTEMFL=Y) in Safety Population (SAFFL=Y).
    """
    safe  = adsl[adsl["SAFFL"] == "Y"]
    n_act = (safe["TRT01AN"] == 1).sum()
    n_pbo = (safe["TRT01AN"] == 2).sum()

    tae = adae[(adae["TRTEMFL"] == "Y") & (adae["SAFFL"] == "Y")]
    act = tae[tae["TRT01AN"] == 1]
    pbo = tae[tae["TRT01AN"] == 2]

    rows: list[AERow] = []

    def row(label: str, a_df: pd.DataFrame, p_df: pd.DataFrame, indent: int = 0) -> AERow:
        an, ap = _subj_pct(a_df, n_act)
        pn, pp = _subj_pct(p_df, n_pbo)
        return AERow(label, str(an), ap, str(pn), pp, indent)

    # Overall summary
    rows.append(AERow("Subjects in safety population",
        str(n_act), f"{n_act} (100%)", str(n_pbo), f"{n_pbo} (100%)"))
    rows.append(row("Subjects with at least one TEAE", act, pbo))
    rows.append(row("  Subjects with at least one serious TEAE",
        act[act["AESER"] == "Y"], pbo[pbo["AESER"] == "Y"], indent=1))
    rows.append(row("  Subjects with at least one TEAE related to study drug",
        act[act["AEREL"] == "Y"], pbo[pbo["AEREL"] == "Y"], indent=1))
    rows.append(row("  Subjects with TEAE leading to discontinuation",
        act[act.get("AEACN", pd.Series()) == "DRUG WITHDRAWN"] if "AEACN" in act.columns
            else act.head(0),
        pbo[pbo.get("AEACN", pd.Series()) == "DRUG WITHDRAWN"] if "AEACN" in pbo.columns
            else pbo.head(0),
        indent=1))

    # By maximum severity
    rows.append(AERow("TEAEs by maximum severity", "", "", "", "", indent=0))
    for sev in ["MILD", "MODERATE", "SEVERE"]:
        # subjects whose worst AE is this severity
        def worst(df: pd.DataFrame, s: str) -> pd.DataFrame:
            mx = df.groupby("USUBJID")["AESEVN"].max().reset_index()
            sev_n = {"MILD": 1, "MODERATE": 2, "SEVERE": 3}[s]
            uids = mx[mx["AESEVN"] == sev_n]["USUBJID"]
            return df[df["USUBJID"].isin(uids)]
        rows.append(row(f"  {sev.capitalize()}", worst(act, sev), worst(pbo, sev), indent=1))

    # By SOC and PT
    rows.append(AERow("TEAEs by System Organ Class and Preferred Term",
        "", "", "", "", indent=0))
    for soc in sorted(tae["AEBODSYS"].unique()):
        a_soc = act[act["AEBODSYS"] == soc]
        p_soc = pbo[pbo["AEBODSYS"] == soc]
        rows.append(row(f"  {soc}", a_soc, p_soc, indent=1))
        for pt in sorted(tae[tae["AEBODSYS"] == soc]["AEDECOD"].unique()):
            rows.append(row(
                f"    {pt.capitalize()}",
                a_soc[a_soc["AEDECOD"] == pt],
                p_soc[p_soc["AEDECOD"] == pt],
                indent=2,
            ))

    return rows


def to_dataframe(rows: list[AERow]) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "System Organ Class / Preferred Term": r.label,
            "Active Drug 100mg\nn (%)": r.active_pct,
            "Placebo\nn (%)": r.placebo_pct,
        }
        for r in rows
    ])
