"""
PDF Generation Helper - Converts Markdown reports to branded PDF using fpdf2.
"""

import re
from datetime import date


def markdown_to_pdf(title: str, subtitle: str, markdown_content: str) -> bytes:
    """Convert a Markdown report to a branded Rappi PDF.

    Args:
        title: Report title (shown in the header).
        subtitle: Subtitle / date line under the title.
        markdown_content: Full Markdown text of the report.

    Returns:
        PDF as bytes (ready for st.download_button).
    """
    from fpdf import FPDF

    ORANGE = (255, 68, 31)
    DARK = (30, 30, 46)
    GRAY = (107, 114, 128)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(left=15, top=15, right=15)
    pdf.add_page()

    # ── Header bar ──────────────────────────────────────────────────
    pdf.set_fill_color(*ORANGE)
    pdf.rect(0, 0, 210, 24, "F")
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(15, 6)
    pdf.cell(0, 9, _safe(title))
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(15, 15)
    pdf.cell(0, 6, _safe(subtitle))

    # ── Body ────────────────────────────────────────────────────────
    pdf.set_xy(15, 30)
    pdf.set_text_color(*DARK)

    for line in markdown_content.split("\n"):
        if line.startswith("# "):
            # H1: skip — already in header
            continue

        elif line.startswith("## "):
            pdf.ln(4)
            pdf.set_fill_color(*ORANGE)
            pdf.rect(15, pdf.get_y(), 3, 7, "F")
            pdf.set_x(20)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(*ORANGE)
            pdf.cell(0, 7, _safe(line[3:]), ln=True)
            pdf.set_text_color(*DARK)
            pdf.ln(1)

        elif line.startswith("### "):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*DARK)
            pdf.set_x(15)
            pdf.cell(0, 6, _safe(line[4:]), ln=True)

        elif line.startswith("- ") or line.startswith("* "):
            content = line[2:]
            content = _strip_bold(content)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*DARK)
            pdf.set_x(20)
            pdf.multi_cell(0, 5, f"  -  {_safe(content)}")

        elif re.match(r"^\d+\.\s", line):
            # Numbered list item
            content = re.sub(r"^\d+\.\s", "", line)
            content = _strip_bold(content)
            num = line.split(".")[0]
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*DARK)
            pdf.set_x(20)
            pdf.multi_cell(0, 5, f"{num}. {_safe(content)}")

        elif line.startswith("---") or line.startswith("***"):
            # Horizontal rule
            pdf.ln(3)
            pdf.set_draw_color(*GRAY)
            y = pdf.get_y()
            pdf.line(15, y, 195, y)
            pdf.ln(3)

        elif line.startswith("**") and line.endswith("**") and len(line) > 4:
            # Bold-only line (label)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_x(15)
            pdf.cell(0, 5, _safe(_strip_bold(line)), ln=True)

        elif line.strip():
            # Regular paragraph text
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*DARK)
            pdf.set_x(15)
            pdf.multi_cell(0, 5, _safe(_strip_bold(line)))

        else:
            pdf.ln(2)

    # ── Footer ──────────────────────────────────────────────────────
    pdf.set_y(-15)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 10, f"Rappi AI Intelligence Engine  |  {date.today().isoformat()}  |  Confidencial", align="C")

    return bytes(pdf.output())


def _strip_bold(text: str) -> str:
    """Remove **bold** and *italic* markdown markers."""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    return text


def _safe(text: str) -> str:
    """Replace non-latin1 characters for fpdf2 compatibility."""
    return text.encode("latin-1", errors="replace").decode("latin-1")
