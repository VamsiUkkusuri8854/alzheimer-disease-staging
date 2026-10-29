# ============================================================
# ALZHEIMER MRI STAGING - BACKEND PDF REPORT SERVICE
# ============================================================

import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


def generate_brain_assessment_pdf(data: dict) -> bytes:
    """
    Generate a professional, publication-quality PDF research report
    based on actual model outputs, selected model metadata, and clinician inputs.
    Does NOT fabricate clinical findings or prescriptions.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=32,
        bottomMargin=32
    )

    styles = getSampleStyleSheet()

    # Custom typography colors
    primary_color = colors.HexColor("#0f172a")     # Deep Slate
    accent_blue = colors.HexColor("#0284c7")       # Medical Cyan/Blue
    light_bg = colors.HexColor("#f8fafc")          # Soft background
    border_color = colors.HexColor("#cbd5e1")      # Slate border
    text_muted = colors.HexColor("#475569")        # Muted body

    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=primary_color,
        alignment=TA_LEFT
    )

    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=accent_blue,
        alignment=TA_LEFT
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=primary_color,
        spaceAfter=3,
        textTransform='uppercase'
    )

    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=primary_color,
        alignment=TA_LEFT
    )

    body_muted = ParagraphStyle(
        'ReportBodyMuted',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=text_muted,
        alignment=TA_LEFT
    )

    disclaimer_style = ParagraphStyle(
        'DisclaimerText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor("#78350f"),
        alignment=TA_LEFT
    )

    # Extract actual data safely
    filename = data.get("filename") or data.get("scan_filename") or "Uploaded_MRI_Scan.nii.gz"
    raw_timestamp = data.get("timestamp")
    if raw_timestamp:
        try:
            timestamp_str = datetime.fromisoformat(str(raw_timestamp).replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            timestamp_str = str(raw_timestamp)
    else:
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Prediction details
    pred = data.get("prediction", {})
    if isinstance(pred, dict):
        predicted_class = pred.get("class_name") or "Inconclusive"
        confidence_val = pred.get("confidence", 0.0)
        uncertainty_val = pred.get("uncertainty", 0.0)
    else:
        predicted_class = str(pred)
        confidence_val = data.get("confidence", 0.0)
        uncertainty_val = data.get("uncertainty", 0.0)

    confidence_str = f"{confidence_val * 100:.1f}%" if isinstance(confidence_val, (int, float)) else str(confidence_val)
    uncertainty_str = f"{uncertainty_val:.3f}" if isinstance(uncertainty_val, (int, float)) else str(uncertainty_val)

    num_slices = data.get("informative_slices") or data.get("num_slices") or data.get("slice_count") or (data.get("volume_metadata", {}).get("valid_slices_extracted")) or "128"
    processing_time = data.get("processing_time_seconds")
    proc_time_str = f"{processing_time:.2f} s" if processing_time is not None else "N/A"
    model_name = data.get("model_name") or data.get("model") or "MobileNetV3-Large"
    model_architecture = data.get("model_architecture") or model_name
    input_type = data.get("input_type") or "3D T1-weighted MRI"
    analysis_level = data.get("analysis_level") or "Patient-level"
    aggregation_method = data.get("aggregation_method") or "Patient-level mean probability aggregation across axial slices"
    device_name = data.get("device") or "CPU"

    # Clinician review inputs
    clinician_name = data.get("clinician_name") or "Not Specified"
    clinical_impression = data.get("clinical_impression") or "Pending clinical review"
    clinician_notes = data.get("clinician_notes") or data.get("additional_notes") or "None entered"
    review_status = data.get("review_status") or "Not Reviewed"

    # Probabilities handling (4-Class compliant)
    raw_probs = data.get("probabilities") or {}
    
    four_classes = [
        ("Class 0: Cognitively Normal", raw_probs.get("Cognitively Normal", 0.0)),
        ("Class 1: Very Mild Dementia", raw_probs.get("Very Mild Dementia", 0.0)),
        ("Class 2: Mild Dementia", raw_probs.get("Mild Dementia", 0.0)),
        ("Class 3: Moderate Dementia", raw_probs.get("Moderate Dementia", 0.0))
    ]

    elements = []

    # 1. Header with NEUROSTAGE AI Branding & Report Title
    header_data = [
        [
            Paragraph("<b>NEUROSTAGE AI</b>", ParagraphStyle('H1', fontName='Helvetica-Bold', fontSize=11, textColor=accent_blue)),
            Paragraph(f"<b>REPORT DATE:</b> {timestamp_str}", ParagraphStyle('H2', fontName='Helvetica', fontSize=8, alignment=TA_RIGHT, textColor=text_muted))
        ],
        [
            Paragraph("AI-Assisted Brain MRI Assessment Report", title_style),
            Paragraph("RESEARCH PROTOTYPE", ParagraphStyle('H3', fontName='Helvetica-Bold', fontSize=8.5, alignment=TA_RIGHT, textColor=accent_blue))
        ],
        [
            Paragraph("Uncertainty-Aware Patient-Level Alzheimer’s Disease Staging", subtitle_style),
            Paragraph(f"Selected Model: <b>{model_name}</b>", ParagraphStyle('H4', fontName='Helvetica', fontSize=8, alignment=TA_RIGHT, textColor=primary_color))
        ]
    ]
    header_table = Table(header_data, colWidths=[360, 180])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 4))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=accent_blue, spaceAfter=6, spaceBefore=2))

    # Top Notice Disclaimer Box
    disclaimer_text = (
        "<b>RESEARCH PROTOTYPE NOTICE:</b> This AI assessment report is generated for academic and scientific evaluation. "
        "It does not constitute a medical diagnosis, clinical finding, or treatment prescription. "
        "All diagnostic and therapeutic decisions must be made by licensed medical practitioners."
    )
    disc_table = Table([[Paragraph(disclaimer_text, disclaimer_style)]], colWidths=[540])
    disc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fffbeb")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#fde68a")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(disc_table)
    elements.append(Spacer(1, 8))

    # 1. SCAN INFORMATION & 2. AI STAGING RESULT (2-Column Table)
    scan_info_html = (
        f"<b>Scan / File Name:</b> {filename}<br/>"
        f"<b>Analysis Date:</b> {timestamp_str}<br/>"
        f"<b>Selected AI Model:</b> {model_name}<br/>"
        f"<b>Model Architecture:</b> {model_architecture}<br/>"
        f"<b>Input Type:</b> {input_type}<br/>"
        f"<b>Analysis Level:</b> {analysis_level}<br/>"
        f"<b>Execution Device:</b> {device_name}"
    )

    stage_result_html = (
        f"<b>AI Predicted Stage:</b> <font color='#0284c7' size='+1'><b>{predicted_class}</b></font><br/>"
        f"<b>Confidence:</b> <b>{confidence_str}</b> (Maximum class probability)<br/>"
        f"<b>Uncertainty:</b> <b>{uncertainty_str}</b> (MC Dropout dispersion)<br/>"
        f"<b>Informative Slices:</b> {num_slices} axial slices (224×224 RGB)<br/>"
        f"<b>Aggregation Method:</b> {aggregation_method}<br/>"
        f"<b>Measured Processing Time:</b> {proc_time_str}"
    )

    summary_grid = [
        [
            Paragraph("<b>1. ANALYSIS INFORMATION</b>", section_heading),
            Paragraph("<b>2. AI PREDICTION RESULT</b>", section_heading)
        ],
        [
            Paragraph(scan_info_html, body_style),
            Paragraph(stage_result_html, body_style)
        ]
    ]
    summary_table = Table(summary_grid, colWidths=[265, 275])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
        ('RIGHTPADDING', (0,0), (-1,-1), 7),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 8))

    # 3. FOUR-CLASS PROBABILITY DISTRIBUTION
    elements.append(Paragraph("<b>3. AI PREDICTION PROBABILITIES</b>", section_heading))
    
    prob_table_data = [
        [
            Paragraph("<b>Alzheimer's Staging Class</b>", ParagraphStyle('TH1', fontName='Helvetica-Bold', fontSize=8, textColor=primary_color)),
            Paragraph("<b>Probability</b>", ParagraphStyle('TH2', fontName='Helvetica-Bold', fontSize=8, alignment=TA_RIGHT, textColor=primary_color)),
            Paragraph("<b>Status & Representation</b>", ParagraphStyle('TH3', fontName='Helvetica-Bold', fontSize=8, textColor=primary_color))
        ]
    ]

    is_4class_trained = data.get("is_4class_trained", True)

    for c_name, c_prob in four_classes:
        is_pred = predicted_class.lower() in c_name.lower()
        
        # Check if class was trained in the active model checkpoint
        if "Moderate" in c_name and (not is_4class_trained or "Moderate Dementia" not in raw_probs):
            prob_val_str = "Unavailable"
            status_note = "Moderate Dementia is not trained in this 3-class checkpoint."
        elif is_pred:
            prob_val_str = f"{c_prob * 100:.1f}%"
            status_note = "<b>AI Predicted Stage (Highest Probability)</b>"
        else:
            prob_val_str = f"{c_prob * 100:.1f}%"
            status_note = "Aggregated across axial slices"

        prob_table_data.append([
            Paragraph(f"<b>{c_name}</b>" if is_pred else c_name, body_style),
            Paragraph(f"<b>{prob_val_str}</b>" if is_pred else prob_val_str, ParagraphStyle('TD2', fontName='Helvetica-Bold' if is_pred else 'Helvetica', fontSize=8.5, alignment=TA_RIGHT)),
            Paragraph(status_note, body_muted)
        ])

    prob_table = Table(prob_table_data, colWidths=[175, 85, 280])
    prob_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(prob_table)
    elements.append(Spacer(1, 8))

    # 4. AI ANALYSIS SUMMARY & UNCERTAINTY ASSESSMENT (2 Columns)
    ai_summary_text = data.get("ai_analysis_summary") or (
        f"The selected model ({model_name}) assigned the highest probability to {predicted_class} ({confidence_str} confidence). "
        f"The patient-level prediction was obtained by aggregating predictions across {num_slices} informative MRI slices. "
        "The reported confidence and uncertainty reflect the model's output across stochastic forward passes."
    )
    
    uncertainty_text = (
        f"<b>Calculated Uncertainty: {uncertainty_str}</b><br/>"
        "The uncertainty estimate reflects model variability across stochastic inference passes. "
        "Higher uncertainty indicates that the model is less consistent in its predictions across slice features."
    )

    assessment_grid = [
        [
            Paragraph("<b>4. AI ANALYSIS SUMMARY</b>", section_heading),
            Paragraph("<b>5. UNCERTAINTY ASSESSMENT</b>", section_heading)
        ],
        [
            Paragraph(ai_summary_text, body_style),
            Paragraph(uncertainty_text, body_style)
        ]
    ]
    assessment_table = Table(assessment_grid, colWidths=[265, 275])
    assessment_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
        ('RIGHTPADDING', (0,0), (-1,-1), 7),
    ]))
    elements.append(assessment_table)
    elements.append(Spacer(1, 8))

    # 6. CLINICAL CONTEXT & FOLLOW-UP
    elements.append(Paragraph("<b>6. CLINICAL CONTEXT & FOLLOW-UP</b>", section_heading))
    follow_up_html = (
        "<b>Research Prototype:</b> This AI system provides a research-oriented MRI staging prediction and should not be interpreted as a medical diagnosis.<br/>"
        "• Review the MRI findings with a qualified radiologist or clinician.<br/>"
        "• Correlate the AI result with clinical history and cognitive assessment (e.g. MMSE, MoCA, CDR).<br/>"
        "• Consider professional neurological evaluation when clinically appropriate.<br/>"
        "• The AI result should not be used by itself to make treatment decisions."
    )
    follow_up_table = Table([[Paragraph(follow_up_html, body_style)]], colWidths=[540])
    follow_up_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
        ('RIGHTPADDING', (0,0), (-1,-1), 7),
    ]))
    elements.append(follow_up_table)
    elements.append(Spacer(1, 8))

    # 7. CLINICIAN REVIEW SECTION
    elements.append(Paragraph("<b>7. CLINICIAN REVIEW</b>", section_heading))
    clinician_grid = [
        [
            Paragraph(f"<b>Clinician Name:</b> {clinician_name}", body_style),
            Paragraph(f"<b>Review Status:</b> <b>{review_status}</b>", body_style)
        ],
        [
            Paragraph(f"<b>Clinical Impression:</b> {clinical_impression}", body_style),
            Paragraph(f"<b>Additional Notes:</b> {clinician_notes}", body_style)
        ]
    ]
    clinician_table = Table(clinician_grid, colWidths=[265, 275])
    clinician_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(clinician_table)
    elements.append(Spacer(1, 6))

    # 8. FINAL DISCLAIMER & RESEARCH FOOTER
    final_disc = (
        "<b>RESEARCH DISCLAIMER:</b> NeuroStage AI is an academic research platform for automated MRI staging and uncertainty estimation. "
        "It does not provide medical diagnoses or prescribe medications. Research prototype only."
    )
    final_disc_table = Table([[Paragraph(final_disc, disclaimer_style)]], colWidths=[540])
    final_disc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fffbeb")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#fde68a")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(final_disc_table)

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
