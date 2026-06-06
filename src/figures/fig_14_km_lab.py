"""
Figures for regulatory submission:
  Figure 14.1 — Kaplan-Meier time-to-first-TEAE curve by treatment arm
  Figure 14.2 — Mean change from baseline in lab parameters over time
"""

from __future__ import annotations
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path


COLORS = {"Active Drug 100mg": "#1f4e79", "Placebo": "#c55a11"}
STYLE  = {
    "font.family":       "DejaVu Sans",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.labelsize":    10,
    "axes.titlesize":    11,
    "xtick.labelsize":   9,
    "ytick.labelsize":   9,
    "legend.fontsize":   9,
    "figure.dpi":        150,
}


def _km_curve(times: pd.Series, events: pd.Series) -> tuple[list, list]:
    """Simple Kaplan-Meier estimator (no ties correction)."""
    df = pd.DataFrame({"t": times, "e": events}).sort_values("t")
    n  = len(df)
    s  = 1.0
    curve_t = [0]
    curve_s = [1.0]
    for i, (_, row) in enumerate(df.iterrows()):
        if row["e"] == 1:
            s *= (n - i - 1) / (n - i) if (n - i) > 0 else s
        curve_t.append(row["t"])
        curve_s.append(s)
    return curve_t, curve_s


def figure_14_1_km(adae: pd.DataFrame, adsl: pd.DataFrame,
                   output_path: str) -> str:
    """
    Figure 14.1 — Kaplan-Meier curve: time to first TEAE by treatment arm.
    Uses AESTDY as time variable; subjects without a TEAE are censored at TRTDURD.
    """
    safe = adsl[adsl["SAFFL"] == "Y"][["USUBJID", "TRT01A", "TRTDURD"]].copy()
    tae  = adae[(adae["TRTEMFL"] == "Y") & (adae["SAFFL"] == "Y")]
    first_ae = (
        tae.groupby("USUBJID")["AESTDY"].min().reset_index()
           .rename(columns={"AESTDY": "TIME"})
    )
    first_ae["EVENT"] = 1

    merged = safe.merge(first_ae, on="USUBJID", how="left")
    merged["EVENT"] = merged["EVENT"].fillna(0).astype(int)
    merged["TIME"]  = merged["TIME"].fillna(merged["TRTDURD"])

    plt.rcParams.update(STYLE)
    fig, ax = plt.subplots(figsize=(7, 4.5))

    for arm, grp in merged.groupby("TRT01A"):
        t, s = _km_curve(grp["TIME"], grp["EVENT"])
        ax.step(t, s, where="post", label=f"{arm} (n={len(grp)})",
                color=COLORS.get(arm, "gray"), linewidth=1.8)

    ax.set_xlabel("Study Day")
    ax.set_ylabel("Probability of being TEAE-free")
    ax.set_title("Figure 14.1  Kaplan-Meier Estimate of Time to First TEAE\nSafety Population")
    ax.set_ylim(0, 1.05)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
    ax.legend(loc="lower left", frameon=False)
    ax.axhline(0.5, color="gray", linestyle=":", linewidth=0.8, alpha=0.6)

    note = ("TEAE = Treatment-Emergent Adverse Event. "
            "Subjects without a TEAE are censored at end of treatment.")
    fig.text(0.01, -0.03, note, fontsize=7, color="gray", wrap=True)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] Figure 14.1 → {output_path}")
    return output_path


def figure_14_2_lab_change(adlb: pd.DataFrame, output_path: str,
                            params: list[str] | None = None) -> str:
    """
    Figure 14.2 — Mean (±SD) change from baseline in lab parameters by visit.
    One subplot per parameter.
    """
    if params is None:
        params = adlb["PARAMCD"].unique().tolist()[:4]  # max 4 subplots

    post = adlb[(adlb["ABLFL"] != "Y") & adlb["CHG"].notna()].copy()

    visit_order = post.groupby("VISIT")["ADY"].mean().sort_values().index.tolist()

    plt.rcParams.update(STYLE)
    n_plots = len(params)
    ncols = 2
    nrows = (n_plots + 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(11, 4 * nrows), sharey=False)
    axes = axes.flatten() if n_plots > 1 else [axes]

    for ax, pcd in zip(axes, params):
        param_df   = post[post["PARAMCD"] == pcd]
        param_name = param_df["PARAM"].iloc[0] if len(param_df) else pcd
        unit       = param_df["AVALU"].iloc[0] if "AVALU" in param_df.columns and len(param_df) else ""

        for arm, grp in param_df.groupby("TRT01A"):
            stats = (
                grp.groupby("VISIT")["CHG"]
                   .agg(["mean", "std", "count"])
                   .reindex(visit_order)
                   .dropna()
            )
            x = range(len(stats))
            ax.errorbar(
                x, stats["mean"], yerr=stats["std"],
                label=arm, color=COLORS.get(arm, "gray"),
                marker="o", markersize=5, linewidth=1.5,
                capsize=4, capthick=1,
            )

        ax.axhline(0, color="gray", linestyle="--", linewidth=0.8)
        ax.set_xticks(range(len(visit_order)))
        ax.set_xticklabels(visit_order, rotation=15, ha="right")
        ax.set_title(param_name, fontsize=10)
        ax.set_ylabel(f"Change from Baseline ({unit})", fontsize=8)
        if ax == axes[0]:
            ax.legend(frameon=False)

    # hide empty subplots
    for ax in axes[n_plots:]:
        ax.set_visible(False)

    fig.suptitle("Figure 14.2  Mean (±SD) Change from Baseline in Laboratory Parameters\nSafety Population",
                 fontsize=11, y=1.01)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] Figure 14.2 → {output_path}")
    return output_path
