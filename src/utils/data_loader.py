"""
ADaM Data Loader
Loads ADSL, ADAE, ADLB from CSV files (Project 1 output) or generates
fresh synthetic data when no path is supplied.
"""

from __future__ import annotations
import random
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import date, timedelta


# ── Synthetic ADaM generator (self-contained, no Project 1 dependency) ────────

def _rand_date(start: date, end: date) -> str:
    return (start + timedelta(days=random.randint(0, (end - start).days))).isoformat()


def make_adsl(n: int = 80, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    random.seed(seed)
    rows = []
    for i in range(1, n + 1):
        site   = f"00{random.randint(1,4)}"
        arm    = random.choice(["A", "B"])
        bday   = date(1945, 1, 1) + timedelta(days=int(rng.integers(0, 365 * 45)))
        enroll = date(2022, 1, 1) + timedelta(days=int(rng.integers(0, 364)))
        age    = (enroll - bday).days // 365
        rows.append({
            "STUDYID":  "CDISCPILOT01",
            "USUBJID":  f"CDISCPILOT01-{site}-{i:04d}",
            "SUBJID":   f"{i:04d}",
            "SITEID":   site,
            "AGE":      age,
            "AGEU":     "YEARS",
            "AGEGR1":   "<65" if age < 65 else ">=65",
            "AGEGR1N":  1 if age < 65 else 2,
            "SEX":      random.choice(["M", "F"]),
            "SEXN":     1 if random.random() > 0.5 else 2,
            "RACE":     random.choices(
                            ["WHITE", "BLACK OR AFRICAN AMERICAN", "ASIAN", "OTHER"],
                            weights=[60, 20, 15, 5])[0],
            "ETHNIC":   random.choices(
                            ["HISPANIC OR LATINO", "NOT HISPANIC OR LATINO"],
                            weights=[20, 80])[0],
            "ARMCD":    arm,
            "ARM":      "Active Drug 100mg" if arm == "A" else "Placebo",
            "TRT01P":   "Active Drug 100mg" if arm == "A" else "Placebo",
            "TRT01PN":  1 if arm == "A" else 2,
            "TRT01A":   "Active Drug 100mg" if arm == "A" else "Placebo",
            "TRT01AN":  1 if arm == "A" else 2,
            "TRTSDT":   enroll.isoformat(),
            "TRTEDTC":  (enroll + timedelta(days=int(rng.integers(70, 84)))).isoformat(),
            "TRTDURD":  int(rng.integers(70, 84)),
            "SAFFL":    "Y",
            "EFFFL":    "Y",
            "ITTFL":    "Y",
            "BMIBL":    round(float(rng.normal(27, 4)), 1),
            "WEIGHTBL": round(float(rng.normal(80, 15)), 1),
            "HEIGHTBL": round(float(rng.normal(170, 10)), 1),
            "COUNTRY":  "USA",
        })
    return pd.DataFrame(rows)


def make_adae(adsl: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    rng  = np.random.default_rng(seed)
    random.seed(seed)
    ae_terms = [
        ("NAUSEA",        "Gastrointestinal disorders",  "MILD",     False),
        ("HEADACHE",      "Nervous system disorders",    "MILD",     False),
        ("FATIGUE",       "General disorders",           "MILD",     False),
        ("DIZZINESS",     "Nervous system disorders",    "MODERATE", False),
        ("HYPERTENSION",  "Vascular disorders",          "MODERATE", True),
        ("ALT INCREASED", "Investigations",              "MODERATE", True),
        ("RASH",          "Skin disorders",              "MILD",     False),
        ("DIARRHOEA",     "Gastrointestinal disorders",  "MILD",     False),
    ]
    rows = []
    seq  = 1
    for _, s in adsl.iterrows():
        trtsdt = date.fromisoformat(s["TRTSDT"])
        for _ in range(int(rng.poisson(2))):
            term, soc, sev, serious = random.choice(ae_terms)
            onset = trtsdt + timedelta(days=int(rng.integers(0, 180)))
            rows.append({
                "STUDYID":  s["STUDYID"],
                "USUBJID":  s["USUBJID"],
                "AESEQ":    seq,
                "TRT01A":   s["TRT01A"],
                "TRT01AN":  s["TRT01AN"],
                "SAFFL":    "Y",
                "AETERM":   term,
                "AEDECOD":  term,
                "AEBODSYS": soc,
                "AESEV":    sev,
                "AESEVN":   {"MILD": 1, "MODERATE": 2, "SEVERE": 3}[sev],
                "AESER":    "Y" if serious else "N",
                "AESERN":   1 if serious else 0,
                "AEREL":    random.choice(["Y", "N"]),
                "TRTEMFL":  "Y",
                "AESTDTC":  onset.isoformat(),
                "AEENDTC":  (onset + timedelta(days=int(rng.integers(1, 30)))).isoformat(),
                "AESTDY":   (onset - trtsdt).days + 1,
                "AEOUT":    "RECOVERED/RESOLVED",
                "AETOXGR":  str({"MILD": 1, "MODERATE": 2, "SEVERE": 3}[sev]),
                "AETOXGRN": {"MILD": 1, "MODERATE": 2, "SEVERE": 3}[sev],
                "AGEGR1":   s["AGEGR1"],
                "SEX":      s["SEX"],
                "RACE":     s["RACE"],
            })
            seq += 1
    return pd.DataFrame(rows)


def make_adlb(adsl: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    random.seed(seed)
    params = [
        ("ALT",   "Alanine Aminotransferase", "U/L",    1,  7,  56, 30, 8),
        ("AST",   "Aspartate Aminotransferase","U/L",   2, 10,  40, 25, 6),
        ("CREAT", "Creatinine",               "mg/dL",  3,  0.6, 1.2, 0.9, 0.15),
        ("HGB",   "Haemoglobin",              "g/dL",   4, 12,  17, 14, 1.2),
        ("GLUC",  "Glucose",                  "mg/dL",  5, 70, 110, 90, 12),
    ]
    visits = [
        ("SCREENING", -7,  1, "Y"),
        ("WEEK 4",    28,  2, ""),
        ("WEEK 12",   84,  3, ""),
    ]
    rows = []
    seq  = 1
    for _, s in adsl.iterrows():
        trtsdt = date.fromisoformat(s["TRTSDT"])
        baselines = {}
        for pcd, pnm, pu, pn, lo, hi, mn, sd in params:
            base_val = round(float(rng.normal(mn, sd)), 2)
            baselines[pcd] = base_val
            for visit, day, vnum, ablfl in visits:
                noise = round(float(rng.normal(0, sd * 0.3)), 2)
                aval  = round(base_val + noise, 2)
                base  = baselines[pcd]
                chg   = round(aval - base, 2) if ablfl != "Y" else 0.0
                pchg  = round(chg / base * 100, 2) if base != 0 and ablfl != "Y" else 0.0
                nrind = "LOW" if aval < lo else ("HIGH" if aval > hi else "NORMAL")
                rows.append({
                    "STUDYID":  s["STUDYID"],
                    "USUBJID":  s["USUBJID"],
                    "LBSEQ":    seq,
                    "TRT01A":   s["TRT01A"],
                    "TRT01AN":  s["TRT01AN"],
                    "SAFFL":    "Y",
                    "PARAMCD":  pcd,
                    "PARAM":    pnm,
                    "PARAMN":   pn,
                    "AVAL":     aval,
                    "AVALC":    str(aval),
                    "AVALU":    pu,
                    "BASE":     base,
                    "CHG":      chg,
                    "PCHG":     pchg,
                    "ANRLO":    lo,
                    "ANRHI":    hi,
                    "ANRIND":   nrind,
                    "BNRIND":   "NORMAL" if baselines[pcd] >= lo and baselines[pcd] <= hi else "HIGH",
                    "SHIFT1":   f"NORMAL→{nrind}",
                    "ABLFL":    ablfl,
                    "VISIT":    visit,
                    "VISITNUM": vnum,
                    "ADT":      (trtsdt + timedelta(days=day)).isoformat(),
                    "ADY":      day + 1 if day >= 0 else day,
                    "AGEGR1":   s["AGEGR1"],
                    "SEX":      s["SEX"],
                })
                seq += 1
    return pd.DataFrame(rows)


# ── Public loader ──────────────────────────────────────────────────────────────

def load_adam(adam_dir: str | None = None) -> dict[str, pd.DataFrame]:
    """
    Load ADaM datasets. If adam_dir points to Project 1 outputs, reads from
    CSV. Otherwise generates fresh synthetic data.
    """
    if adam_dir and Path(adam_dir).exists():
        adsl = pd.read_csv(Path(adam_dir) / "adsl.csv")
        adae = pd.read_csv(Path(adam_dir) / "adae.csv")
        adlb = pd.read_csv(Path(adam_dir) / "adlb.csv")
        print(f"[Data] Loaded from {adam_dir}")
    else:
        adsl = make_adsl()
        adae = make_adae(adsl)
        adlb = make_adlb(adsl)
        print("[Data] Generated synthetic ADaM datasets")
    return {"adsl": adsl, "adae": adae, "adlb": adlb}
