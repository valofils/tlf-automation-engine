# TLF Automation Engine

> Automated generation of **Tables, Listings, and Figures (TLFs)** from CDISC ADaM datasets for Phase II/III regulatory submissions — producing a paginated PDF report, Excel workbook, and individual CSV/PNG outputs.

![CI](https://github.com/valofils/tlf-automation-engine/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue)
![CDISC](https://img.shields.io/badge/CDISC-ADaM%20BDS%20v1.3-orange)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Overview

This is **Project 2** in the Clinical/Pharma Data Science portfolio series. It consumes ADaM datasets (from [Project 1 — CDISC SDTM & ADaM Builder](https://github.com/valofils/cdisc-sdtm-adam-builder) or its own synthetic generator) and produces a complete regulatory TLF package.

| Deliverable | Content |
|---|---|
| Table 14.1.1 | Demographics and baseline characteristics |
| Table 14.2.1 | TEAE summary by SOC and Preferred Term |
| Table 14.3.1 | Lab shift tables (baseline → post-baseline NR category) |
| Listing 16.2.1 | Subject-level adverse event listing |
| Figure 14.1 | Kaplan-Meier — time to first TEAE by treatment arm |
| Figure 14.2 | Mean (±SD) change from baseline in lab parameters |
| PDF Report | All TLFs assembled in a paginated regulatory-style document |
| Excel Workbook | All tables and listing in a single `.xlsx` file |

---

## Project Structure

```
tlf-automation-engine/
├── pipeline.py                        # Main orchestrator
├── requirements.txt                   # Pinned dependencies
├── .github/workflows/ci.yml           # GitHub Actions CI
├── .gitignore
│
├── src/
│   ├── utils/
│   │   ├── data_loader.py             # Loads from Project 1 or generates synthetic ADaM
│   │   └── pdf_renderer.py            # ReportLab PDF assembler
│   ├── tables/
│   │   ├── t14_1_1_demographics.py    # Table 14.1.1
│   │   ├── t14_2_1_ae_summary.py      # Table 14.2.1
│   │   └── t14_3_1_lab_shift.py       # Table 14.3.1
│   ├── listings/
│   │   └── l16_2_1_ae_listing.py      # Listing 16.2.1
│   └── figures/
│       └── fig_14_km_lab.py           # Figure 14.1 (KM) + Figure 14.2 (lab)
│
├── tests/
│   └── test_pipeline.py               # 20 unit tests
│
└── outputs/                           # Generated on run — gitignored
    ├── t14_1_1_demographics.csv
    ├── t14_2_1_ae_summary.csv
    ├── t14_3_1_shift_*.csv
    ├── l16_2_1_ae_listing.csv
    ├── fig_14_1_km.png
    ├── fig_14_2_lab_change.png
    ├── tlf_tables.xlsx
    └── tlf_report_CDISCPILOT01.pdf
```

---

## Quick Start

```bash
git clone https://github.com/valofils/tlf-automation-engine.git
cd tlf-automation-engine

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1

pip install -r requirements.txt

# Run with built-in synthetic data
python pipeline.py

# Run using Project 1 ADaM datasets
python pipeline.py --adam-dir ../cdisc-sdtm-adam-builder/data/adam

pytest tests/ -v
```

---

## Tables

### Table 14.1.1 — Demographics and Baseline Characteristics
- Continuous variables: Mean (SD), Median (Min, Max)
- Categorical variables: n (%)
- Subgroups: Age group, Sex, Race, BMI, Weight
- Population: Safety (SAFFL=Y)

### Table 14.2.1 — Adverse Events Summary
- Overall TEAE counts by treatment arm
- Breakdown by maximum severity (Mild / Moderate / Severe)
- Hierarchy: System Organ Class → Preferred Term (MedDRA)
- Subjects counted once per SOC/PT at worst severity
- Filters: TRTEMFL=Y, SAFFL=Y

### Table 14.3.1 — Laboratory Shift Tables
- One table per parameter (ALT, AST, Creatinine, Haemoglobin, Glucose)
- Rows: Baseline normal range category (LOW / NORMAL / HIGH)
- Columns: Post-baseline category
- Separate sections per treatment arm

---

## Figures

### Figure 14.1 — Kaplan-Meier Curve
- Outcome: time to first TEAE (AESTDY)
- Subjects without TEAE censored at treatment duration
- Step function with 50% reference line

### Figure 14.2 — Lab Change from Baseline
- Mean ± SD change from baseline (CHG) per visit
- Panels per parameter, both arms overlaid
- Visits: Week 4, Week 12

---

## Listing

### Listing 16.2.1 — Subject-Level AE Listing
- All TEAEs (TRTEMFL=Y, SAFFL=Y)
- Sorted: USUBJID → System Organ Class → Preferred Term → Start Date
- Columns: Subject ID, Treatment, SOC, PT, Severity, Serious, Related, Start/End Date, Study Day, Outcome

---

## Regulatory Context

Output structure follows:
- **ICH E3** — Structure and Content of Clinical Study Reports (Section 11, 14, 16)
- **CDISC ADaM BDS v1.3** — input dataset structure
- **FDA Guidance for Industry** — Providing Regulatory Submissions in Electronic Format
- **MedDRA v26.0** — adverse event coding hierarchy

---

## Extending

| What to add | Where |
|---|---|
| New table (e.g. exposure summary) | `src/tables/` — follow `t14_1_1_demographics.py` pattern |
| New listing (e.g. lab listing) | `src/listings/` |
| New figure (e.g. forest plot) | `src/figures/` |
| Word/RTF output | Add `python-docx` renderer in `src/utils/` |

---

## Part of the Clinical Data Science Portfolio

| # | Project | Topics |
|---|---|---|
| 1 | [CDISC SDTM & ADaM Builder](https://github.com/valofils/cdisc-sdtm-adam-builder) | SDTM mapping, ADaM BDS, define.xml, Pinnacle 21 validation |
| 2 | **TLF Automation Engine** (this repo) | Tables, listings, figures, PDF report, KM curves, shift tables |
| 3 | Clinical Trial Statistical Analysis | MMRM, survival analysis, multiplicity, forest plots |
| 4 | Risk-Based Quality Management | KRIs, QTLs, SPC charts, monitoring dashboard |
| 5 | Predictive Modeling — Patient Outcomes | ML pipeline, SHAP, XGBoost, model card |
| 6 | Clinical Data Quality Dashboard | Streamlit, EDC metrics, query rates, enrollment tracker |

---

## License

MIT — all data is synthetic, no real patient information is used or stored.
