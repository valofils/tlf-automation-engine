"""
TLF Automation Engine — Main Pipeline
======================================
Generates Tables, Listings, and Figures for a Phase II clinical trial
and assembles them into a regulatory-style PDF report.

Usage:
    python pipeline.py
    python pipeline.py --adam-dir ../cdisc-sdtm-adam-builder/data/adam
"""

import argparse
import os
from pathlib import Path

from src.utils.data_loader import load_adam
from src.tables.t14_1_1_demographics import build_t14_1_1, to_dataframe as dm_df
from src.tables.t14_2_1_ae_summary   import build_t14_2_1, to_dataframe as ae_df
from src.tables.t14_3_1_lab_shift    import build_all_shift_tables, to_display
from src.listings.l16_2_1_ae_listing import build_l16_2_1
from src.figures.fig_14_km_lab       import figure_14_1_km, figure_14_2_lab_change
from src.utils.pdf_renderer          import build_pdf


def run_pipeline(adam_dir: str | None = None, output_dir: str = "outputs") -> None:
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  TLF Automation Engine — Pipeline Start")
    print("=" * 60)

    # ── Data ───────────────────────────────────────────────────────
    print("\n[1/6] Loading ADaM datasets ...")
    adam = load_adam(adam_dir)
    adsl, adae, adlb = adam["adsl"], adam["adae"], adam["adlb"]

    # ── Tables ─────────────────────────────────────────────────────
    print("\n[2/6] Building tables ...")

    t14_1_1_rows = build_t14_1_1(adsl)
    t14_1_1 = dm_df(t14_1_1_rows)
    t14_1_1.to_csv(f"{output_dir}/t14_1_1_demographics.csv", index=False)
    print(f"    Table 14.1.1  {len(t14_1_1):>3} rows  → {output_dir}/t14_1_1_demographics.csv")

    t14_2_1_rows = build_t14_2_1(adae, adsl)
    t14_2_1 = ae_df(t14_2_1_rows)
    t14_2_1.to_csv(f"{output_dir}/t14_2_1_ae_summary.csv", index=False)
    print(f"    Table 14.2.1  {len(t14_2_1):>3} rows  → {output_dir}/t14_2_1_ae_summary.csv")

    shift_tables_raw = build_all_shift_tables(adlb)
    shift_tables_display = {
        label: to_display(df, label) for label, df in shift_tables_raw.items()
    }
    for label, df in shift_tables_display.items():
        fname = label.split("—")[0].strip().lower()
        df.to_csv(f"{output_dir}/t14_3_1_shift_{fname}.csv", index=False)
    print(f"    Table 14.3.1  {len(shift_tables_display)} shift tables → {output_dir}/")

    # ── Listing ────────────────────────────────────────────────────
    print("\n[3/6] Building listings ...")
    l16_2_1 = build_l16_2_1(adae)
    l16_2_1.to_csv(f"{output_dir}/l16_2_1_ae_listing.csv")
    print(f"    Listing 16.2.1  {len(l16_2_1):>3} rows  → {output_dir}/l16_2_1_ae_listing.csv")

    # ── Figures ────────────────────────────────────────────────────
    print("\n[4/6] Generating figures ...")
    fig1_path = f"{output_dir}/fig_14_1_km.png"
    fig2_path = f"{output_dir}/fig_14_2_lab_change.png"
    figure_14_1_km(adae, adsl, fig1_path)
    figure_14_2_lab_change(adlb, fig2_path)

    # ── Excel workbook ─────────────────────────────────────────────
    print("\n[5/6] Exporting Excel workbook ...")
    xl_path = f"{output_dir}/tlf_tables.xlsx"
    with __import__("pandas").ExcelWriter(xl_path, engine="openpyxl") as writer:
        t14_1_1.to_excel(writer, sheet_name="T14.1.1 Demographics", index=False)
        t14_2_1.to_excel(writer, sheet_name="T14.2.1 AE Summary",   index=False)
        l16_2_1.reset_index().to_excel(writer, sheet_name="L16.2.1 AE Listing", index=False)
        for label, df in list(shift_tables_display.items())[:3]:
            sheet = label.split("—")[0].strip()[:28]
            df.to_excel(writer, sheet_name=f"Shift {sheet}", index=False)
    print(f"    Excel workbook → {xl_path}")

    # ── PDF ────────────────────────────────────────────────────────
    print("\n[6/6] Assembling PDF report ...")
    pdf_path = f"{output_dir}/tlf_report_{adsl['STUDYID'].iloc[0]}.pdf"
    build_pdf(
        t14_1_1, t14_2_1, shift_tables_display,
        l16_2_1, fig1_path, fig2_path, pdf_path,
    )

    # ── Summary ────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Pipeline Complete — Outputs")
    print("=" * 60)
    for f in sorted(Path(output_dir).iterdir()):
        size = f.stat().st_size
        unit = "KB" if size < 1_000_000 else "MB"
        val  = size // 1024 if size < 1_000_000 else size // (1024 * 1024)
        print(f"  {f.name:<45} {val:>4} {unit}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TLF Automation Engine")
    parser.add_argument("--adam-dir",    default=None,      help="Path to ADaM CSVs (Project 1 output)")
    parser.add_argument("--output-dir",  default="outputs",  help="Output directory")
    args = parser.parse_args()
    run_pipeline(args.adam_dir, args.output_dir)
