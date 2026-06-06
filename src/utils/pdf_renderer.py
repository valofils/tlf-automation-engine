"""
PDF Report Renderer
Assembles all Tables, Listings, and Figures into a single paginated PDF
using ReportLab — mimicking a regulatory submission appendix.
"""

from __future__ import annotations
import pandas as pd
from pathlib import Path
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak, Image, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


STUDY_ID  = "CDISCPILOT01"
COMPANY   = "Pharmaceutical Co., Ltd."
FONT_BODY = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_MONO = "Courier"

HEADER_BLUE  = colors.HexColor("#1f4e79")
ALT_ROW      = colors.HexColor("#f2f7fc")
BORDER_COLOR = colors.HexColor("#bdd7ee")


def _styles():
    base = getSampleStyleSheet()
    return {
        "title":   ParagraphStyle("title",   fontName=FONT_BOLD,  fontSize=11,
                                  textColor=HEADER_BLUE, spaceAfter=4, alignment=TA_CENTER),
        "subtitle":ParagraphStyle("subtitle",fontName=FONT_BODY,  fontSize=9,
                                  textColor=colors.gray, spaceAfter=2, alignment=TA_CENTER),
        "footnote":ParagraphStyle("footnote",fontName=FONT_BODY,  fontSize=7,
                                  textColor=colors.gray, spaceBefore=4),
        "body":    ParagraphStyle("body",    fontName=FONT_BODY,  fontSize=9),
        "header":  ParagraphStyle("header",  fontName=FONT_BOLD,  fontSize=9,
                                  textColor=colors.white),
    }


def _table_style(n_rows: int, n_cols: int, header_rows: int = 1) -> TableStyle:
    cmds = [
        ("BACKGROUND",  (0, 0),          (-1, header_rows - 1), HEADER_BLUE),
        ("TEXTCOLOR",   (0, 0),          (-1, header_rows - 1), colors.white),
        ("FONTNAME",    (0, 0),          (-1, header_rows - 1), FONT_BOLD),
        ("FONTSIZE",    (0, 0),          (-1, -1),               8),
        ("ROWBACKGROUNDS", (0, header_rows), (-1, -1), [colors.white, ALT_ROW]),
        ("GRID",        (0, 0),          (-1, -1),               0.25, BORDER_COLOR),
        ("VALIGN",      (0, 0),          (-1, -1),               "MIDDLE"),
        ("TOPPADDING",  (0, 0),          (-1, -1),               3),
        ("BOTTOMPADDING",(0, 0),         (-1, -1),               3),
        ("LEFTPADDING", (0, 0),          (-1, -1),               5),
        ("RIGHTPADDING",(0, 0),          (-1, -1),               5),
    ]
    return TableStyle(cmds)


def _page_header_footer(canvas, doc):
    canvas.saveState()
    w, h = doc.pagesize
    # Header line
    canvas.setStrokeColor(HEADER_BLUE)
    canvas.setLineWidth(1)
    canvas.line(doc.leftMargin, h - doc.topMargin + 10, w - doc.rightMargin, h - doc.topMargin + 10)
    canvas.setFont(FONT_BOLD, 8)
    canvas.setFillColor(HEADER_BLUE)
    canvas.drawString(doc.leftMargin, h - doc.topMargin + 13, STUDY_ID)
    canvas.setFont(FONT_BODY, 7)
    canvas.setFillColor(colors.gray)
    canvas.drawRightString(w - doc.rightMargin, h - doc.topMargin + 13, COMPANY)
    # Footer
    canvas.setFont(FONT_BODY, 7)
    canvas.setFillColor(colors.gray)
    canvas.drawString(doc.leftMargin, doc.bottomMargin - 10,
                      f"CONFIDENTIAL — {date.today().isoformat()} — {STUDY_ID}")
    canvas.drawRightString(w - doc.rightMargin, doc.bottomMargin - 10,
                           f"Page {doc.page}")
    canvas.restoreState()


def _df_to_rl_table(df: pd.DataFrame, col_widths=None) -> Table:
    styles = _styles()
    headers = [[Paragraph(str(c), styles["header"]) for c in df.columns]]
    data_rows = [
        [Paragraph(str(v), styles["body"]) for v in row]
        for row in df.values
    ]
    all_rows = headers + data_rows
    tbl = Table(all_rows, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(_table_style(len(all_rows), len(df.columns)))
    return tbl


def build_pdf(
    t14_1_1: pd.DataFrame,
    t14_2_1: pd.DataFrame,
    t14_3_1: dict[str, pd.DataFrame],
    l16_2_1: pd.DataFrame,
    fig_14_1_path: str,
    fig_14_2_path: str,
    output_path: str,
) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    S = _styles()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.8*cm,  bottomMargin=1.5*cm,
    )
    story = []

    def section_title(text: str) -> list:
        return [
            Spacer(1, 0.3*cm),
            Paragraph(text, S["title"]),
            HRFlowable(width="100%", thickness=0.5, color=HEADER_BLUE),
            Spacer(1, 0.2*cm),
        ]

    def footnote(text: str) -> Paragraph:
        return Paragraph(f"<i>{text}</i>", S["footnote"])

    # ── Cover ──────────────────────────────────────────────────────
    story += [
        Spacer(1, 2*cm),
        Paragraph(COMPANY, S["subtitle"]),
        Spacer(1, 0.5*cm),
        Paragraph(f"Study {STUDY_ID}", S["title"]),
        Paragraph("Tables, Listings, and Figures", S["title"]),
        Spacer(1, 0.3*cm),
        Paragraph("Phase II Randomised, Double-Blind, Placebo-Controlled Study", S["subtitle"]),
        Paragraph(f"Generated: {date.today().isoformat()}", S["subtitle"]),
        Spacer(1, 0.5*cm),
        HRFlowable(width="60%", thickness=1, color=HEADER_BLUE, hAlign="CENTER"),
        PageBreak(),
    ]

    # ── Table 14.1.1 ───────────────────────────────────────────────
    story += section_title("Table 14.1.1 — Demographics and Baseline Characteristics\nSafety Population")
    story.append(_df_to_rl_table(t14_1_1, col_widths=[9*cm, 5*cm, 5*cm, 4*cm]))
    story.append(footnote(
        "SD = Standard Deviation. BMI = Body Mass Index. "
        "Safety Population: all subjects who received at least one dose of study drug."
    ))
    story.append(PageBreak())

    # ── Table 14.2.1 ───────────────────────────────────────────────
    story += section_title("Table 14.2.1 — Summary of Treatment-Emergent Adverse Events\nSafety Population")
    story.append(_df_to_rl_table(t14_2_1, col_widths=[12*cm, 5*cm, 5*cm]))
    story.append(footnote(
        "TEAE = Treatment-Emergent Adverse Event. n = number of subjects with event. "
        "Subjects counted once per category at the highest level of severity. "
        "MedDRA version 26.0."
    ))
    story.append(PageBreak())

    # ── Table 14.3.1 — Lab shifts ──────────────────────────────────
    story += section_title("Table 14.3.1 — Laboratory Shift Tables (Baseline to Post-Baseline)\nSafety Population")
    for param_label, shift_df in list(t14_3_1.items())[:3]:
        story.append(Paragraph(param_label, S["body"]))
        story.append(Spacer(1, 0.1*cm))
        story.append(_df_to_rl_table(
            shift_df,
            col_widths=[6*cm, 4*cm, 3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm, 3*cm],
        ))
        story.append(Spacer(1, 0.3*cm))
    story.append(footnote(
        "LOW = below lower limit of normal. NORMAL = within reference range. "
        "HIGH = above upper limit of normal. Baseline = last value before first dose."
    ))
    story.append(PageBreak())

    # ── Figure 14.1 ────────────────────────────────────────────────
    story += section_title("Figure 14.1 — Kaplan-Meier Estimate of Time to First TEAE\nSafety Population")
    if Path(fig_14_1_path).exists():
        story.append(Image(fig_14_1_path, width=20*cm, height=12*cm))
    story.append(PageBreak())

    # ── Figure 14.2 ────────────────────────────────────────────────
    story += section_title("Figure 14.2 — Mean (±SD) Change from Baseline in Laboratory Parameters\nSafety Population")
    if Path(fig_14_2_path).exists():
        story.append(Image(fig_14_2_path, width=24*cm, height=14*cm))
    story.append(PageBreak())

    # ── Listing 16.2.1 ─────────────────────────────────────────────
    story += section_title("Listing 16.2.1 — Subject-Level Adverse Event Listing\nSafety Population (TRTEMFL=Y)")
    listing_cols = l16_2_1.reset_index()
    col_widths_l = [1.2*cm, 4.5*cm, 3*cm, 4*cm, 3*cm, 2*cm, 2*cm, 2.5*cm, 2.5*cm, 2*cm, 4*cm]
    story.append(_df_to_rl_table(listing_cols, col_widths=col_widths_l))
    story.append(footnote(
        "TEAE = Treatment-Emergent Adverse Event. Listing sorted by Subject ID, "
        "System Organ Class, Preferred Term, and Start Date. MedDRA version 26.0."
    ))

    doc.build(story, onFirstPage=_page_header_footer, onLaterPages=_page_header_footer)
    print(f"[OK] PDF report → {output_path}")
    return output_path
