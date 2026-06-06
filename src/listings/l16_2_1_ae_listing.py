"""
Listing 16.2.1 — Subject-Level Adverse Event Listing
All TEAEs sorted by USUBJID, AEBODSYS, AEDECOD — Safety Population.
"""

from __future__ import annotations
import pandas as pd


COLUMNS = [
    ("USUBJID",  "Subject ID"),
    ("TRT01A",   "Treatment"),
    ("AEBODSYS", "System Organ Class"),
    ("AEDECOD",  "Preferred Term"),
    ("AESEV",    "Severity"),
    ("AESER",    "Serious"),
    ("AEREL",    "Related"),
    ("AESTDTC",  "Start Date"),
    ("AEENDTC",  "End Date"),
    ("AESTDY",   "Study Day"),
    ("AEOUT",    "Outcome"),
]


def build_l16_2_1(adae: pd.DataFrame) -> pd.DataFrame:
    """
    Build Listing 16.2.1 — All TEAEs.
    Filters TRTEMFL=Y and SAFFL=Y, sorts per CDISC listing conventions.
    """
    tae = adae[
        (adae["TRTEMFL"] == "Y") & (adae["SAFFL"] == "Y")
    ].copy()

    available = [c for c, _ in COLUMNS if c in tae.columns]
    labels    = {c: lbl for c, lbl in COLUMNS if c in tae.columns}

    listing = (
        tae[available]
        .sort_values(["USUBJID", "AEBODSYS", "AEDECOD", "AESTDTC"])
        .rename(columns=labels)
        .reset_index(drop=True)
    )
    listing.index += 1
    listing.index.name = "Row"
    return listing
