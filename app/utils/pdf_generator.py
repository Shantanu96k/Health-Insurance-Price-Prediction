                            
   

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from datetime import datetime


                                                                         
CLR_PRIMARY   = colors.HexColor("#3b82f6")
CLR_HIGH      = colors.HexColor("#ef4444")
CLR_MEDIUM    = colors.HexColor("#f97316")
CLR_LOW       = colors.HexColor("#10b981")
CLR_DARK      = colors.HexColor("#0f172a")
CLR_SURFACE   = colors.HexColor("#f8fafc")
CLR_BORDER    = colors.HexColor("#e2e8f0")
CLR_TEXT_2    = colors.HexColor("#64748b")


                                                                         
def _risk_color(risk: str) -> colors.Color:
    return {"high": CLR_HIGH, "medium": CLR_MEDIUM, "low": CLR_LOW}.get(risk, CLR_TEXT_2)


def generate_health_report_pdf(
    patient_name: str,
    prediction: dict,
    ai_tips: dict,
    health_score: dict,
    insurance_plan: dict | None = None,
) -> bytes:
       
    buffer = BytesIO()
    doc    = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()

                                                                         
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"],
        fontSize=24, textColor=CLR_DARK, spaceAfter=4,
        fontName="Helvetica-Bold", alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontSize=10, textColor=CLR_TEXT_2, alignment=TA_CENTER,
        spaceAfter=12,
    )
    section_style = ParagraphStyle(
        "Section", parent=styles["Heading2"],
        fontSize=12, textColor=CLR_PRIMARY, spaceBefore=16, spaceAfter=6,
        fontName="Helvetica-Bold", borderPadding=(0, 0, 4, 0),
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, textColor=CLR_DARK, leading=16, spaceAfter=4,
    )
    tip_style = ParagraphStyle(
        "Tip", parent=styles["Normal"],
        fontSize=9, textColor=CLR_DARK, leading=14,
        leftIndent=12, spaceAfter=3,
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer", parent=styles["Normal"],
        fontSize=8, textColor=CLR_TEXT_2, leading=12,
        borderPadding=(8, 8, 8, 8), alignment=TA_CENTER,
    )

    story = []

                                                                         
    story.append(Paragraph("✦ MedPredict", title_style))
    story.append(Paragraph("AI Health Intelligence — Personalised Health Report", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=CLR_PRIMARY))
    story.append(Spacer(1, 0.4*cm))

                                                                         
    report_date = datetime.now().strftime("%d %B %Y, %I:%M %p")
    created_at  = prediction.get("created_at", "")[:10] if prediction.get("created_at") else report_date
    info_data = [
        ["Patient Name:", patient_name,        "Report Date:", report_date],
        ["Assessment Date:", created_at,       "Risk Level:", prediction.get("risk_level", "—").upper()],
    ]
    risk_color = _risk_color(prediction.get("risk_level", "low"))
    info_table = Table(info_data, colWidths=[3.5*cm, 6.5*cm, 3.5*cm, 3.5*cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME",    (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",    (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("TEXTCOLOR",   (0, 0), (-1, -1), CLR_DARK),
        ("TEXTCOLOR",   (3, 1), (3, 1), risk_color),
        ("FONTNAME",    (3, 1), (3, 1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [CLR_SURFACE, colors.white]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5*cm))

                                                                         
    story.append(Paragraph("🩺 Prediction Summary", section_style))
    pred_disease    = prediction.get("predicted_disease", "—")
    confidence      = prediction.get("confidence_score", 0)
    mri_consistency = prediction.get("mri_consistency", "no_mri")
    honesty_flag    = prediction.get("honesty_flag", "trusted")
    model_used      = prediction.get("model_used", "Ensemble ML")

    pred_data = [
        ["Predicted Condition", pred_disease],
        ["Confidence Score",    f"{confidence}%"],
        ["Risk Level",          prediction.get("risk_level", "—").upper()],
        ["MRI Consistency",     mri_consistency.replace("_", " ").title()],
        ["Data Integrity",      "✓ Trusted" if honesty_flag == "trusted" else "⚠ Review Needed"],
        ["Model Used",          "Ensemble (Random Forest + Gradient Boosting + Naive Bayes)"],
    ]
    pred_table = Table(pred_data, colWidths=[6*cm, 11*cm])
    pred_table.setStyle(TableStyle([
        ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",    (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR",   (0, 0), (-1, -1), CLR_DARK),
        ("TEXTCOLOR",   (1, 2), (1, 2), risk_color),
        ("FONTNAME",    (1, 2), (1, 2), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [CLR_SURFACE, colors.white]),
        ("GRID",        (0, 0), (-1, -1), 0.5, CLR_BORDER),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING",  (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(pred_table)
    story.append(Spacer(1, 0.4*cm))

                                                                         
    if health_score:
        story.append(Paragraph("📊 Wellness Score (0–100)", section_style))
        hs_score = health_score.get("score", 0)
        hs_grade = health_score.get("grade", "—")
        hs_label = health_score.get("label", "—")
        bd = health_score.get("breakdown", {})
        hs_data = [
            ["Overall Health Score", f"{hs_score} / 100  (Grade {hs_grade} — {hs_label})"],
            ["Disease Component",    f"{bd.get('disease', 0)} / 100"],
            ["Lifestyle Component",  f"{bd.get('lifestyle', 0)} / 100"],
            ["Family History",       f"{bd.get('family', 0)} / 100"],
        ]
        hs_table = Table(hs_data, colWidths=[6*cm, 11*cm])
        hs_table.setStyle(TableStyle([
            ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME",    (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE",    (0, 0), (-1, -1), 9.5),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [CLR_SURFACE, colors.white]),
            ("GRID",        (0, 0), (-1, -1), 0.5, CLR_BORDER),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING",  (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("FONTNAME",    (0, 0), (0, 0), "Helvetica-Bold"),
            ("FONTSIZE",    (1, 0), (1, 0), 10),
        ]))
        story.append(hs_table)
        story.append(Spacer(1, 0.4*cm))

                                                                         
    def _tips_section(title: str, tips: list, bullet: str = "•"):
        if not tips:
            return
        story.append(Paragraph(title, section_style))
        for tip in tips:
            story.append(Paragraph(f"{bullet}  {tip}", tip_style))
        story.append(Spacer(1, 0.2*cm))

    if ai_tips:
        _tips_section("✅ What You Should DO",         ai_tips.get("do", []),       "→")
        _tips_section("🚫 What You Should NOT Do",     ai_tips.get("dont", []),     "✕")
        _tips_section("📈 How To Improve",             ai_tips.get("improve", []),  "◆")
        _tips_section("🥗 Diet Recommendations",       ai_tips.get("diet", []),     "●")
        _tips_section("🏃 Exercise Plan",              ai_tips.get("exercise", []), "▸")

                                                                         
    if insurance_plan:
        story.append(Paragraph("🛡️ Recommended Insurance Plan", section_style))
        ins_data = [
            ["Plan Name",    insurance_plan.get("plan_name", "—")],
            ["Plan Type",    insurance_plan.get("plan_type", "—").title()],
            ["Monthly Cost", f"₹{insurance_plan.get('monthly_cost', '—')}"],
        ]
        ins_table = Table(ins_data, colWidths=[6*cm, 11*cm])
        ins_table.setStyle(TableStyle([
            ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME",    (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE",    (0, 0), (-1, -1), 9.5),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [CLR_SURFACE, colors.white]),
            ("GRID",        (0, 0), (-1, -1), 0.5, CLR_BORDER),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING",  (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(ins_table)
        story.append(Spacer(1, 0.4*cm))

                                                                         
    story.append(HRFlowable(width="100%", thickness=0.5, color=CLR_BORDER))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "⚕ Medical Disclaimer: This report is generated by an AI ensemble model for educational purposes only. "
        "It is NOT a substitute for professional medical diagnosis. Always consult a licensed physician for "
        "any health concerns. | MedPredict v2.0 — MCA Major Project",
        disclaimer_style
    ))

    doc.build(story)
    return buffer.getvalue()
