"""
PDF Report Generator
Generates a downloadable PDF containing the complete eligibility & authorization report.
Uses ReportLab for PDF generation.
"""
from io import BytesIO # type: ignore
from datetime import datetime # type: ignore

try:
    from reportlab.lib.pagesizes import A4 # type: ignore
    from reportlab.lib import colors # type: ignore
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle # type: ignore
    from reportlab.lib.units import cm # type: ignore
    from reportlab.platypus import ( # type: ignore
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("[WARNING] reportlab not installed. PDF generation will use plain text fallback.")


def generate_pdf_report(session_data: dict) -> bytes:
    """
    Generate a PDF report from the full session data.
    Returns raw PDF bytes.
    """
    if not REPORTLAB_AVAILABLE:
        return _text_report_fallback(session_data).encode("utf-8")

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm,   bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    # Custom styles
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"],
        fontSize=20, textColor=colors.HexColor("#1e1b4b"), spaceAfter=6
    )
    h2_style = ParagraphStyle(
        "H2", parent=styles["Heading2"],
        fontSize=13, textColor=colors.HexColor("#4338ca"), spaceAfter=4, spaceBefore=12
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, textColor=colors.HexColor("#374151"), leading=15
    )
    label_style = ParagraphStyle(
        "Label", parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#6b7280"), leading=13
    )

    story = []

    # ── Header ───────────────────────────────────────────────────────────────
    story.append(Paragraph("Insurance Eligibility & Authorization Report", title_style))
    story.append(Paragraph(
        f"Generated: {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}",
        label_style
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#4338ca"), spaceAfter=14))

    # ── 1. Patient & Insurance Details ───────────────────────────────────────
    card_data = session_data.get("card_data") or {}
    story.append(Paragraph("1. Patient & Insurance Details", h2_style))
    info_data = [
        ["Field", "Value"],
        ["Member Name",   card_data.get("member_name", "Unknown")],
        ["Date of Birth", card_data.get("dob", "Unknown")],
        ["Member ID",     card_data.get("member_id", "Unknown")],
        ["Group Number",  card_data.get("group_number", "Unknown")],
        ["Policy Number", card_data.get("policy_number", "Unknown")],
        ["Payer / Insurer", card_data.get("payer_name", "Unknown")],
        ["Valid Through", card_data.get("valid_thru", "Unknown")],
    ]
    story.append(_make_table(info_data))
    story.append(Spacer(1, 10))

    # ── 2. Eligibility Results ────────────────────────────────────────────────
    benefits = session_data.get("benefits") or {}
    story.append(Paragraph("2. Eligibility & Benefits", h2_style))
    ben_data = [
        ["Field", "Value"],
        ["Coverage Status",        benefits.get("coverage_status", "Unknown")],
        ["Plan Type",              benefits.get("plan_type", "Unknown")],
        ["In Network",             "Yes" if benefits.get("in_network", True) else "No"],
        ["Copay",                  f"₹{benefits.get('copay', 0):,}"],
        ["Total Deductible",       f"₹{benefits.get('deductible_total', 0):,}"],
        ["Remaining Deductible",   f"₹{benefits.get('deductible_remaining', 0):,}"],
        ["Coinsurance",            f"{benefits.get('coinsurance', 0)}%"],
        ["Out-of-Pocket Max",      f"₹{benefits.get('out_of_pocket_max', 0):,}"],
    ]
    story.append(_make_table(ben_data))
    story.append(Spacer(1, 10))

    # ── 3. Financial Estimation ───────────────────────────────────────────────
    finance = session_data.get("financial_estimation") or {}
    if finance:
        story.append(Paragraph("3. Financial Responsibility Estimation", h2_style))
        fin_data = [
            ["Field", "Value"],
            ["Procedure Cost",       f"₹{finance.get('procedure_cost', 0):,}"],
            ["Patient Pays",         f"₹{finance.get('patient_pay', 0):,}"],
            ["Insurance Pays",       f"₹{finance.get('insurance_pay', 0):,}"],
            ["Deductible Applied",   f"₹{finance.get('deductible_applied', 0):,}"],
            ["Coinsurance Amount",   f"₹{finance.get('coinsurance_amount', 0):,}"],
            ["Copay Applied",        f"₹{finance.get('copay_applied', 0):,}"],
            ["Insurance Coverage",   f"{finance.get('coverage_pct', 0)}%"],
        ]
        story.append(_make_table(fin_data))
        story.append(Spacer(1, 10))

    # ── 4. Authorization Decision ─────────────────────────────────────────────
    auth = session_data.get("authorization") or {}
    if auth:
        story.append(Paragraph("4. Prior Authorization Decision", h2_style))
        status  = auth.get("authorization_status", "Unknown")
        conf    = auth.get("confidence_score", 0)
        reason  = auth.get("reason", "N/A")
        auth_data = [
            ["Field", "Value"],
            ["CPT Code",              auth.get("cpt_code", "N/A")],
            ["Authorization Status",  status],
            ["Confidence Score",      f"{int(conf * 100)}%"],
            ["AI Reason",             reason],
            ["Decision Source",       auth.get("source", "AI")],
        ]
        story.append(_make_table(auth_data))
        story.append(Spacer(1, 10))

    # ── 5. Denial Risk ────────────────────────────────────────────────────────
    risk = session_data.get("denial_risk") or {}
    if risk:
        story.append(Paragraph("5. Denial Risk Assessment", h2_style))
        risk_data = [
            ["Field", "Value"],
            ["Risk Score",  f"{risk.get('risk_score', 0)} / 100"],
            ["Risk Level",  risk.get("risk_level", "Unknown")],
            ["Summary",     risk.get("summary", "N/A")],
        ]
        story.append(_make_table(risk_data))

        # Show triggered rules
        rules = risk.get("rules_triggered", [])
        if isinstance(rules, list) and rules:
            story.append(Spacer(1, 6))
            story.append(Paragraph("Triggered Risk Rules:", label_style))
            rules_rows = [["Rule", "Points", "Detail"]] + [
                [r["rule"], str(r["points"]), r["detail"]] for r in rules
            ]
            story.append(_make_table(rules_rows, header_color=colors.HexColor("#fef3c7")))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e7eb")))
    story.append(Paragraph(
        "This report was automatically generated by the ZeroKost Insurance Verification & Authorization Automation Platform. "
        "For clinical decisions, always consult a licensed healthcare professional.",
        label_style
    ))

    doc.build(story)
    return buffer.getvalue()


def _make_table(data: list, header_color=None) -> Table:
    """Build a styled ReportLab table."""
    if header_color is None:
        header_color = colors.HexColor("#ede9fe")

    col_widths = [5.5*cm, 11*cm]
    t = Table(data, colWidths=col_widths)
    style = TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.HexColor("#1e1b4b")),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 9),
        ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",     (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
    ])
    t.setStyle(style)
    return t


def _text_report_fallback(session_data: dict) -> str:
    """Plain text fallback if reportlab is not installed."""
    lines = ["=" * 60, "INSURANCE ELIGIBILITY & AUTHORIZATION REPORT", "=" * 60, ""]

    card = session_data.get("card_data") or {}
    lines += [
        "PATIENT & INSURANCE DETAILS",
        f"  Member Name:   {card.get('member_name', 'N/A')}",
        f"  DOB:           {card.get('dob', 'N/A')}",
        f"  Member ID:     {card.get('member_id', 'N/A')}",
        f"  Payer:         {card.get('payer_name', 'N/A')}",
        f"  Valid Through: {card.get('valid_thru', 'N/A')}",
        "",
    ]

    ben = session_data.get("benefits") or {}
    if ben:
        lines += [
            "BENEFITS",
            f"  Coverage: {ben.get('coverage_status')}",
            f"  Copay: {ben.get('copay')}  |  Deductible Remaining: {ben.get('deductible_remaining')}",
            f"  Coinsurance: {ben.get('coinsurance')}%  |  OOP Max: {ben.get('out_of_pocket_max')}",
            "",
        ]

    fin = session_data.get("financial_estimation") or {}
    if fin:
        lines += [
            "FINANCIAL ESTIMATION",
            f"  Procedure Cost: {fin.get('procedure_cost')}",
            f"  Patient Pays:   {fin.get('patient_pay')}  |  Insurance Pays: {fin.get('insurance_pay')}",
            "",
        ]

    auth = session_data.get("authorization") or {}
    if auth:
        lines += [
            "AUTHORIZATION",
            f"  Status:     {auth.get('authorization_status')}",
            f"  Confidence: {auth.get('confidence_score')}",
            f"  Reason:     {auth.get('reason')}",
            "",
        ]

    risk = session_data.get("denial_risk") or {}
    if risk:
        lines += [
            "DENIAL RISK",
            f"  Score: {risk.get('risk_score')}/100  |  Level: {risk.get('risk_level')}",
            f"  {risk.get('summary')}",
        ]

    return "\n".join(lines)
