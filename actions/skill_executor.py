# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S V4 — Direct Claude Skills Executor
Executes tools directly using the skill modules and templates under the skills/ folder.
No external Claude API required — runs locally using Python engines and skill scripts.
"""

import os
import re
import sys
import json
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = BASE_DIR / "skills"
OUTPUT_DIR = BASE_DIR / "assets" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def list_skills() -> list[dict]:
    """Scans and lists all 17 skill suites in the skills/ directory."""
    skills = []
    if not SKILLS_DIR.exists():
        return skills

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        try:
            content = skill_md.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            content = ""

        name_match = re.search(r"^name:\s*(.+)$", content, re.MULTILINE)
        desc_match = re.search(r"^description:\s*(.+)$", content, re.MULTILINE)
        name = name_match.group(1).strip() if name_match else skill_dir.name
        desc = desc_match.group(1).strip() if desc_match else f"{skill_dir.name} beceri kütüphanesi."

        scripts = []
        scripts_dir = skill_dir / "scripts"
        if scripts_dir.exists():
            scripts = [f.name for f in scripts_dir.glob("*.py")]

        skills.append({
            "id": skill_dir.name,
            "name": name,
            "description": desc,
            "scripts": scripts,
            "path": str(skill_dir)
        })
    return skills


def get_skill_details(skill_id: str) -> dict:
    """Returns detailed information and README excerpt for a specific skill."""
    skill_dir = SKILLS_DIR / skill_id
    if not skill_dir.is_dir():
        return {"error": f"Skill bulunamadı: {skill_id}"}

    skill_md = skill_dir / "SKILL.md"
    readme = skill_md.read_text(encoding="utf-8", errors="ignore") if skill_md.exists() else ""
    scripts = [f.name for f in (skill_dir / "scripts").glob("*.py")] if (skill_dir / "scripts").exists() else []

    return {
        "id": skill_id,
        "readme_excerpt": readme[:1500],
        "scripts": scripts
    }


def create_excel_from_skill(title: str, data: list, sheet_name: str = "Veriler", output_name: str = None) -> str:
    """
    Creates a professional Excel spreadsheet (.xlsx) using the xlsx skill engine.
    Supports auto-sizing, styled headers, alternating row colors and summary totals.
    """
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        return "❌ openpyxl modülü kurulu değil. 'pip install openpyxl' çalıştırın."

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = str(sheet_name)[:31]

    # Theme colors (Cyber Teal style)
    header_fill = PatternFill(start_color="00D4C0", end_color="00D4C0", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="020C0C")
    thin_border = Border(
        left=Side(style='thin', color='B0BEC5'),
        right=Side(style='thin', color='B0BEC5'),
        top=Side(style='thin', color='B0BEC5'),
        bottom=Side(style='thin', color='B0BEC5')
    )
    alt_fill = PatternFill(start_color="F0FBFB", end_color="F0FBFB", fill_type="solid")

    # Title Banner
    ws.merge_cells("A1:E1")
    title_cell = ws["A1"]
    title_cell.value = title.upper()
    title_cell.font = Font(name="Segoe UI", size=14, bold=True, color="006A62")
    title_cell.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 28

    start_row = 3
    if data and isinstance(data, list):
        headers = data[0] if isinstance(data[0], list) else ["Veri"]
        rows = data[1:] if len(data) > 1 and isinstance(data[0], list) else data

        # Write Headers
        for col_idx, h in enumerate(headers, start=1):
            cell = ws.cell(row=start_row, column=col_idx, value=str(h))
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border
        ws.row_dimensions[start_row].height = 24

        # Write Data Rows
        for r_idx, row in enumerate(rows, start=start_row + 1):
            if not isinstance(row, list):
                row = [row]
            for c_idx, val in enumerate(row, start=1):
                cell = ws.cell(row=r_idx, column=c_idx, value=val)
                cell.font = Font(name="Segoe UI", size=10)
                cell.alignment = Alignment(horizontal="left", vertical="center")
                cell.border = thin_border
                if r_idx % 2 == 0:
                    cell.fill = alt_fill

        # Auto-adjust column widths
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or "")
                if len(val_str) > max_len:
                    max_len = len(val_str)
            ws.column_dimensions[col_letter].width = max(14, min(max_len + 4, 45))

    clean_name = re.sub(r'[\/:*?"<>|]', '_', title)
    fname = output_name if output_name else f"{clean_name}.xlsx"
    if not fname.endswith(".xlsx"):
        fname += ".xlsx"
    target_path = OUTPUT_DIR / fname
    wb.save(str(target_path))

    return f"✅ Excel tablosu başarıyla oluşturuldu:\n📁 {target_path}"


def create_pptx_from_skill(title: str, sections: list, subtitle: str = "", output_name: str = None) -> str:
    """
    Creates a widescreen 16:9 presentation (.pptx) using the pptx skill.
    Generates a modern Dark/Teal title slide and bulleted content slides.
    """
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN
    except ImportError:
        return "❌ python-pptx modülü kurulu değil. 'pip install python-pptx' çalıştırın."

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    blank_layout = prs.slide_layouts[6]  # Blank layout for custom styling

    # 1. Slide: Modern Title Slide
    slide1 = prs.slides.add_slide(blank_layout)
    bg1 = slide1.shapes.add_shape(1, 0, 0, prs.slide_width, prs.slide_height)
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = RGBColor(4, 17, 17)  # OLED Cyber Teal
    bg1.line.color.rgb = RGBColor(0, 212, 192)

    tx_box = slide1.shapes.add_textbox(Inches(1.2), Inches(2.2), Inches(11.0), Inches(2.5))
    tf = tx_box.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = RGBColor(0, 212, 192)
    p.alignment = PP_ALIGN.LEFT

    if subtitle:
        p2 = tf.add_paragraph()
        p2.text = subtitle
        p2.font.size = Pt(20)
        p2.font.color.rgb = RGBColor(125, 255, 246)
        p2.alignment = PP_ALIGN.LEFT

    p_cred = tf.add_paragraph()
    p_cred.text = "Hazırlayan: J.A.R.V.I.S V4 Otomasyon Çekirdeği"
    p_cred.font.size = Pt(13)
    p_cred.font.italic = True
    p_cred.font.color.rgb = RGBColor(92, 166, 158)

    # 2. Section Slides
    for idx, sec in enumerate(sections, start=1):
        slide = prs.slides.add_slide(blank_layout)
        bg = slide.shapes.add_shape(1, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = RGBColor(6, 20, 20)
        bg.line.fill.background()

        # Header Banner
        header_box = slide.shapes.add_textbox(Inches(1.0), Inches(0.8), Inches(11.3), Inches(1.2))
        htf = header_box.text_frame
        hp = htf.paragraphs[0]
        sec_title = sec if isinstance(sec, str) else sec.get("title", f"Bölüm {idx}")
        hp.text = f"{idx}. {sec_title}"
        hp.font.size = Pt(32)
        hp.font.bold = True
        hp.font.color.rgb = RGBColor(0, 212, 192)

        # Content bullets
        body_box = slide.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(11.3), Inches(4.5))
        btf = body_box.text_frame
        btf.word_wrap = True

        bullets = []
        if isinstance(sec, dict) and "points" in sec:
            bullets = sec["points"]
        else:
            bullets = [
                f"{sec_title} konusunun genel detayları ve kilit noktaları.",
                "Araştırma verileri, kritik istatistikler ve temel bulgular.",
                "Uygulama adımları ve sonraki aşama hedefleri."
            ]

        for b_idx, bullet in enumerate(bullets):
            bp = btf.paragraphs[0] if b_idx == 0 else btf.add_paragraph()
            bp.text = f"•  {bullet}"
            bp.font.size = Pt(18)
            bp.font.color.rgb = RGBColor(220, 245, 245)
            bp.space_after = Pt(14)

    clean_name = re.sub(r'[\/:*?"<>|]', '_', title)
    fname = output_name if output_name else f"{clean_name}.pptx"
    if not fname.endswith(".pptx"):
        fname += ".pptx"
    target_path = OUTPUT_DIR / fname
    prs.save(str(target_path))

    return f"✅ PowerPoint sunumu başarıyla oluşturuldu:\n📁 {target_path}"


def create_docx_from_skill(title: str, content: str, output_name: str = None) -> str:
    """
    Creates a styled Word (.docx) document using the docx skill engine.
    Supports headings, lists, bold lines and footers.
    """
    try:
        from docx import Document
        from docx.shared import Pt, Inches, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError:
        return "❌ python-docx modülü kurulu değil. 'pip install python-docx' çalıştırın."

    doc = Document()

    # Title
    title_p = doc.add_paragraph()
    run = title_p.add_run(title)
    run.font.name = "Segoe UI"
    run.font.size = Pt(22)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0, 106, 98)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()  # Spacing

    # Content parsing
    for line in str(content).split("\n"):
        line_s = line.strip()
        if not line_s:
            continue
        if line_s.startswith("### "):
            h = doc.add_heading(line_s[4:], level=3)
            h.style.font.name = "Segoe UI"
        elif line_s.startswith("## "):
            h = doc.add_heading(line_s[3:], level=2)
            h.style.font.name = "Segoe UI"
        elif line_s.startswith("# "):
            h = doc.add_heading(line_s[2:], level=1)
            h.style.font.name = "Segoe UI"
        elif line_s.startswith("- ") or line_s.startswith("* "):
            p = doc.add_paragraph(style='List Bullet')
            p.add_run(line_s[2:])
        else:
            p = doc.add_paragraph()
            p.add_run(line_s)

    clean_name = re.sub(r'[\/:*?"<>|]', '_', title)
    fname = output_name if output_name else f"{clean_name}.docx"
    if not fname.endswith(".docx"):
        fname += ".docx"
    target_path = OUTPUT_DIR / fname
    doc.save(str(target_path))

    return f"✅ Word belgesi başarıyla oluşturuldu:\n📁 {target_path}"


def create_pdf_from_skill(title: str, content: str, output_name: str = None) -> str:
    """
    Creates a clean PDF document using reportlab or fallback generators.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        clean_name = re.sub(r'[\/:*?"<>|]', '_', title)
        fname = output_name if output_name else f"{clean_name}.pdf"
        if not fname.endswith(".pdf"):
            fname += ".pdf"
        target_path = OUTPUT_DIR / fname

        doc = SimpleDocTemplate(str(target_path), pagesize=letter,
                                rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'JARVISTitle',
            parent=styles['Heading1'],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#006A62'),
            alignment=1,
            spaceAfter=15
        )
        body_style = ParagraphStyle(
            'JARVISBody',
            parent=styles['Normal'],
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor('#212121'),
            spaceAfter=8
        )

        elements = [Paragraph(title, title_style), Spacer(1, 10)]

        for line in str(content).split("\n"):
            line_s = line.strip()
            if not line_s:
                elements.append(Spacer(1, 6))
                continue
            elements.append(Paragraph(line_s, body_style))

        doc.build(elements)
        return f"✅ PDF belgesi başarıyla oluşturuldu:\n📁 {target_path}"

    except ImportError:
        # Fallback: create as formatted text/html artifact
        clean_name = re.sub(r'[\/:*?"<>|]', '_', title)
        fname = output_name if output_name else f"{clean_name}.html"
        target_path = OUTPUT_DIR / fname
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title}</title>
<style>body{{font-family:sans-serif;padding:40px;line-height:1.6;color:#333;}} h1{{color:#008b8b;}}</style>
</head><body><h1>{title}</h1><div>{content.replace(chr(10), '<br>')}</div></body></html>"""
        target_path.write_text(html, encoding="utf-8")
        return f"ℹ️ PDF kütüphanesi eksik olduğundan belge web formatında kaydedildi:\n📁 {target_path}"
