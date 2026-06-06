"""
Table 14.3.1 — Laboratory Shift Table
Shift from baseline normal range category to post-baseline category.
Presented per parameter per treatment arm — Safety Population.
"""

from __future__ import annotations
import pandas as pd


CATEGORIES = ["LOW", "NORMAL", "HIGH"]


def build_shift_table(adlb: pd.DataFrame, paramcd: str) -> pd.DataFrame:
    """
    Build a 3×3 shift table (Baseline × Post-baseline) for a single lab parameter.
    Rows = Baseline category, Columns = Post-baseline category.
    Returns a DataFrame with MultiIndex columns (treatment arm × post-baseline category).
    """
    param = adlb[adlb["PARAMCD"] == paramcd].copy()
    baseline = param[param["ABLFL"] == "Y"][["USUBJID", "ANRIND", "TRT01A"]].rename(
        columns={"ANRIND": "BASE_CAT"}
    )
    post = param[param["ABLFL"] != "Y"][["USUBJID", "ANRIND"]].rename(
        columns={"ANRIND": "POST_CAT"}
    )
    merged = baseline.merge(post, on="USUBJID", how="inner")

    results = []
    for arm in sorted(merged["TRT01A"].unique()):
        arm_df = merged[merged["TRT01A"] == arm]
        for base_cat in CATEGORIES:
            base_sub = arm_df[arm_df["BASE_CAT"] == base_cat]
            row = {"Treatment": arm, "Baseline": base_cat}
            for post_cat in CATEGORIES:
                row[post_cat] = (base_sub["POST_CAT"] == post_cat).sum()
            row["Total"] = len(base_sub)
            results.append(row)

    return pd.DataFrame(results)


def build_all_shift_tables(adlb: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build shift tables for all parameters in ADLB."""
    tables = {}
    for pcd in adlb["PARAMCD"].unique():
        param_name = adlb[adlb["PARAMCD"] == pcd]["PARAM"].iloc[0]
        tables[f"{pcd} — {param_name}"] = build_shift_table(adlb, pcd)
    return tables


def to_display(shift_df: pd.DataFrame, param_label: str) -> pd.DataFrame:
    """Flatten shift table for clean display / export."""
    pivot = shift_df.pivot_table(
        index=["Treatment", "Baseline"],
        values=CATEGORIES + ["Total"],
        aggfunc="sum"
    ).reset_index()
    pivot.insert(0, "Parameter", param_label)
    return pivot[["Parameter", "Treatment", "Baseline"] + CATEGORIES + ["Total"]]
