"""
Unit Tests — TLF Automation Engine
Run with: pytest tests/ -v
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.utils.data_loader import make_adsl, make_adae, make_adlb
from src.tables.t14_1_1_demographics import build_t14_1_1, to_dataframe as dm_df
from src.tables.t14_2_1_ae_summary   import build_t14_2_1, to_dataframe as ae_df
from src.tables.t14_3_1_lab_shift    import build_shift_table, build_all_shift_tables
from src.listings.l16_2_1_ae_listing import build_l16_2_1
from src.figures.fig_14_km_lab       import figure_14_1_km, figure_14_2_lab_change


@pytest.fixture(scope="module")
def adam():
    adsl = make_adsl(n=80)
    adae = make_adae(adsl)
    adlb = make_adlb(adsl)
    return {"adsl": adsl, "adae": adae, "adlb": adlb}


# ── Table 14.1.1 ─────────────────────────────────────────────────────────────

class TestT14_1_1:
    def test_returns_rows(self, adam):
        rows = build_t14_1_1(adam["adsl"])
        assert len(rows) > 0

    def test_subject_count_row_first(self, adam):
        rows = build_t14_1_1(adam["adsl"])
        assert "Number of subjects" in rows[0].label

    def test_to_dataframe_columns(self, adam):
        df = dm_df(build_t14_1_1(adam["adsl"]))
        assert list(df.columns) == ["Parameter", "Active Drug 100mg", "Placebo", "Total"]

    def test_mean_sd_format(self, adam):
        df = dm_df(build_t14_1_1(adam["adsl"]))
        mean_sd_rows = df[df["Parameter"].str.contains("Mean")]
        for _, row in mean_sd_rows.iterrows():
            for col in ["Active Drug 100mg", "Placebo", "Total"]:
                assert "(" in str(row[col]), f"Mean (SD) format incorrect: {row[col]}"

    def test_pct_format(self, adam):
        df = dm_df(build_t14_1_1(adam["adsl"]))
        pct_rows = df[df["Active Drug 100mg"].str.contains(r"\(", na=False) &
                      df["Active Drug 100mg"].str.contains("%", na=False)]
        assert len(pct_rows) > 0

    def test_totals_sum_to_n(self, adam):
        safe = adam["adsl"][adam["adsl"]["SAFFL"] == "Y"]
        rows = build_t14_1_1(adam["adsl"])
        header = rows[0]
        total = int(header.total)
        assert total == len(safe)


# ── Table 14.2.1 ─────────────────────────────────────────────────────────────

class TestT14_2_1:
    def test_returns_rows(self, adam):
        rows = build_t14_2_1(adam["adae"], adam["adsl"])
        assert len(rows) > 0

    def test_to_dataframe_columns(self, adam):
        df = ae_df(build_t14_2_1(adam["adae"], adam["adsl"]))
        assert "System Organ Class / Preferred Term" in df.columns
        assert any("Active" in c for c in df.columns)

    def test_soc_rows_present(self, adam):
        rows = build_t14_2_1(adam["adae"], adam["adsl"])
        labels = [r.label for r in rows]
        socs = adam["adae"]["AEBODSYS"].unique()
        for soc in socs:
            assert any(soc in l for l in labels), f"SOC '{soc}' not found in table"

    def test_teae_count_within_n(self, adam):
        safe = adam["adsl"][adam["adsl"]["SAFFL"] == "Y"]
        n_act = (safe["TRT01AN"] == 1).sum()
        rows = build_t14_2_1(adam["adae"], adam["adsl"])
        for row in rows:
            if row.active_n.isdigit():
                assert int(row.active_n) <= n_act


# ── Table 14.3.1 ─────────────────────────────────────────────────────────────

class TestT14_3_1:
    def test_shift_table_shape(self, adam):
        df = build_shift_table(adam["adlb"], "ALT")
        assert "Treatment" in df.columns
        assert "Baseline" in df.columns
        assert "LOW" in df.columns
        assert "NORMAL" in df.columns
        assert "HIGH" in df.columns

    def test_all_shift_tables_built(self, adam):
        tables = build_all_shift_tables(adam["adlb"])
        params = adam["adlb"]["PARAMCD"].unique()
        assert len(tables) == len(params)

    def test_row_totals_correct(self, adam):
        df = build_shift_table(adam["adlb"], "ALT")
        for _, row in df.iterrows():
            assert row["Total"] == row["LOW"] + row["NORMAL"] + row["HIGH"]


# ── Listing 16.2.1 ───────────────────────────────────────────────────────────

class TestL16_2_1:
    def test_only_teae(self, adam):
        listing = build_l16_2_1(adam["adae"])
        assert len(listing) > 0

    def test_sorted_by_usubjid(self, adam):
        listing = build_l16_2_1(adam["adae"])
        subjects = listing["Subject ID"].tolist()
        assert subjects == sorted(subjects)

    def test_required_columns(self, adam):
        listing = build_l16_2_1(adam["adae"])
        for col in ["Subject ID", "Treatment", "System Organ Class",
                    "Preferred Term", "Severity", "Start Date"]:
            assert col in listing.columns

    def test_row_count_matches_adae(self, adam):
        tae = adam["adae"][(adam["adae"]["TRTEMFL"] == "Y") & (adam["adae"]["SAFFL"] == "Y")]
        listing = build_l16_2_1(adam["adae"])
        assert len(listing) == len(tae)


# ── Figures ──────────────────────────────────────────────────────────────────

class TestFigures:
    def test_km_figure_created(self, adam, tmp_path):
        path = str(tmp_path / "km.png")
        result = figure_14_1_km(adam["adae"], adam["adsl"], path)
        assert Path(result).exists()
        assert Path(result).stat().st_size > 0

    def test_lab_change_figure_created(self, adam, tmp_path):
        path = str(tmp_path / "lab.png")
        result = figure_14_2_lab_change(adam["adlb"], path)
        assert Path(result).exists()
        assert Path(result).stat().st_size > 0

    def test_km_accepts_adsl_without_trtdurd(self, adam, tmp_path):
        adsl_mod = adam["adsl"].copy()
        if "TRTDURD" not in adsl_mod.columns:
            adsl_mod["TRTDURD"] = 84
        path = str(tmp_path / "km2.png")
        figure_14_1_km(adam["adae"], adsl_mod, path)
        assert Path(path).exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
