// ============================================================
// ALZHEIMER MRI STAGING - CLINICAL REPORT GENERATOR (HTML & PRINT)
// ============================================================

export function generateReportHtml(data) {
  const timestamp = data.timestamp ? new Date(data.timestamp).toLocaleString() : new Date().toLocaleString();
  const reportId = `REP-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).substring(2, 6).toUpperCase()}`;
  const filename = data.filename || data.scan_filename || 'Unknown_MRI_Volume.nii.gz';
  const className = data.prediction?.class_name || 'Inconclusive';
  const classId = data.prediction?.class_id !== undefined ? data.prediction.class_id : '—';
  const confidence = data.prediction?.confidence !== undefined ? (data.prediction.confidence * 100).toFixed(1) : '—';
  const uncertainty = data.prediction?.uncertainty !== undefined ? data.prediction.uncertainty.toFixed(3) : '—';
  const numSlices = data.informative_slices || data.num_slices || data.volume_metadata?.valid_slices_extracted || '—';
  const processingTime = data.processing_time_seconds !== undefined ? `${data.processing_time_seconds.toFixed(2)}s` : '—';
  const modelName = data.model_name || data.model || 'MobileNetV3-Large';
  const modelArchitecture = data.model_architecture || modelName;
  const inputType = data.input_type || '3D T1-weighted MRI';
  const analysisLevel = data.analysis_level || 'Patient-level';
  const aggregationMethod = data.aggregation_method || 'Patient-level mean probability aggregation across axial slices';

  // Clinician fields
  const clinicianName = data.clinician_name || 'Not Specified';
  const clinicalImpression = data.clinical_impression || 'Pending clinical review';
  const clinicianNotes = data.clinician_notes || data.additional_notes || 'None entered';
  const reviewStatus = data.review_status || 'Not Reviewed';

  // Stage CDR mapping
  const cdrMapping = {
    'Cognitively Normal': 'CDR 0.0 (No Dementia)',
    'Very Mild Dementia': 'CDR 0.5 (Very Mild Cognitive Impairment)',
    'Mild Dementia': 'CDR 1.0 (Mild Alzheimer\'s Disease)',
    'Moderate Dementia': 'CDR 2.0 (Moderate Alzheimer\'s Disease)'
  };
  const cdrText = cdrMapping[className] || 'Experimental Staging Category';

  // 4-Class Probabilities rows
  const probs = data.probabilities || {};
  const fourClasses = [
    'Cognitively Normal',
    'Very Mild Dementia',
    'Mild Dementia',
    'Moderate Dementia'
  ];

  const probRows = fourClasses.map((cat) => {
    const val = probs[cat] ?? 0.0;
    const p = (val * 100).toFixed(1);
    const isSelected = cat === className;
    const isReserved = cat === 'Moderate Dementia' && val === 0.0 && !data.is_4class_trained;

    return `
      <tr style="${isSelected ? 'background-color: #f0fdf4; font-weight: 700;' : ''}">
        <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0;">
          ${cat} ${isSelected ? '<span style="color: #047857; margin-left: 6px;">[PREDICTED]</span>' : ''}
          ${isReserved ? '<span style="color: #64748b; font-size: 11px; margin-left: 6px;">(Reserved for future training data)</span>' : ''}
        </td>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; text-align: right; font-family: monospace; font-weight: 600;">${p}%</td>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; width: 35%;">
          <div style="background: #e2e8f0; height: 8px; border-radius: 4px; overflow: hidden;">
            <div style="background: ${isSelected ? '#059669' : '#0284c7'}; width: ${Math.max(p, 0.5)}%; height: 100%;"></div>
          </div>
        </td>
      </tr>
    `;
  }).join('');

  return `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Alzheimer MRI Staging Report - ${filename}</title>
  <style>
    body {
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      color: #0f172a;
      background: #ffffff;
      margin: 0;
      padding: 32px 40px;
      line-height: 1.5;
      font-size: 13.5px;
    }
    .report-card {
      max-width: 820px;
      margin: 0 auto;
      border: 1px solid #cbd5e1;
      padding: 32px 36px;
      border-radius: 12px;
      box-shadow: 0 4px 16px rgba(0,0,0,0.05);
    }
    .header-table {
      width: 100%;
      border-bottom: 2px solid #0284c7;
      padding-bottom: 14px;
      margin-bottom: 20px;
    }
    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
      margin-bottom: 20px;
    }
    .info-box {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      padding: 16px;
      border-radius: 8px;
    }
    .info-title {
      font-size: 11px;
      font-weight: 700;
      color: #0f172a;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 10px;
    }
    .disclaimer-box {
      background: #fffbeb;
      border: 1px solid #fde68a;
      padding: 12px 16px;
      border-radius: 8px;
      margin-bottom: 20px;
      font-size: 12px;
      color: #92400e;
      line-height: 1.5;
    }
    table {
      width: 100%;
      border-collapse: collapse;
    }
    @media print {
      body { padding: 0; }
      .report-card { border: none; box-shadow: none; padding: 0; }
    }
  </style>
</head>
<body>
  <div class="report-card">
    <!-- Top Disclaimer -->
    <div class="disclaimer-box">
      <strong>RESEARCH PROTOTYPE NOTICE:</strong> This AI assessment report is strictly intended for scientific evaluation and academic research. It does not constitute a clinical diagnosis, medical opinion, or prescription. All treatment decisions must be made by licensed medical practitioners.
    </div>

    <!-- Header -->
    <table class="header-table">
      <tr>
        <td>
          <div style="font-size: 12px; font-weight: 700; color: #0284c7; text-transform: uppercase;">NEUROSTAGE AI • RESEARCH PLATFORM</div>
          <h1 style="font-size: 20px; font-weight: 800; margin: 4px 0 2px; color: #0f172a;">AI-Assisted Brain MRI Assessment Report</h1>
          <div style="font-size: 12px; color: #64748b;">Uncertainty-Aware Patient-Level Alzheimer’s Disease Staging</div>
        </td>
        <td style="text-align: right; vertical-align: top; font-size: 12px; color: #64748b;">
          <div>Report ID: <strong>${reportId}</strong></div>
          <div>Date: <strong>${timestamp}</strong></div>
          <div>Model: <strong>${modelName}</strong></div>
        </td>
      </tr>
    </table>

    <!-- 1. Patient / Scan Info & 2. AI Staging Result -->
    <div class="grid-2">
      <div class="info-box">
        <div class="info-title">1. Analysis Information</div>
        <div style="display: flex; flex-direction: column; gap: 6px; font-size: 13px;">
          <div>Scan File: <strong>${filename}</strong></div>
          <div>Selected Model: <strong>${modelName}</strong></div>
          <div>Model Architecture: <strong>${modelArchitecture}</strong></div>
          <div>Input Type: <strong>${inputType}</strong></div>
          <div>Analysis Level: <strong>${analysisLevel}</strong></div>
        </div>
      </div>

      <div class="info-box">
        <div class="info-title">2. AI Prediction Result</div>
        <div style="margin-bottom: 8px;">
          <div style="font-size: 11px; color: #64748b; text-transform: uppercase;">AI Predicted Stage</div>
          <div style="font-size: 18px; font-weight: 800; color: #0284c7;">${className} (Stage ${classId})</div>
          <div style="font-size: 11px; color: #64748b;">${cdrText}</div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 12px; margin-top: 8px;">
          <div>Confidence: <strong>${confidence}%</strong></div>
          <div>Uncertainty: <strong>${uncertainty}</strong></div>
          <div>Slices Analyzed: <strong>${numSlices}</strong></div>
          <div>Processing Time: <strong>${processingTime}</strong></div>
        </div>
      </div>
    </div>

    <!-- 3. Four-Class Probability Distribution -->
    <div style="border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; margin-bottom: 20px;">
      <div style="background: #f8fafc; padding: 10px 14px; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em;">
        3. AI Prediction Probabilities (4-Class Staging)
      </div>
      <table>
        ${probRows}
      </table>
    </div>

    <!-- 4. AI Analysis Summary -->
    <div class="info-box" style="margin-bottom: 20px;">
      <div class="info-title">4. AI Analysis Summary</div>
      <div style="font-size: 13px; color: #334155; line-height: 1.6;">
        ${data.ai_analysis_summary || `The selected deep learning model (${modelName}) assigned the highest probability to ${className} (${confidence}% confidence). The patient-level prediction was obtained by aggregating predictions across ${numSlices} informative axial slices using mean probability pooling. The reported confidence and uncertainty reflect the model's output across stochastic forward passes.`}
      </div>
    </div>

    <!-- 5. Clinical Context & Follow-Up -->
    <div class="info-box" style="margin-bottom: 20px; background: #f0fdf4; border-color: #bbf7d0;">
      <div class="info-title" style="color: #166534;">5. Clinical Context & Follow-Up</div>
      <ul style="margin: 0; padding-left: 20px; font-size: 12.5px; color: #166534; line-height: 1.6;">
        <li>Review the MRI findings with a qualified radiologist or neurologist.</li>
        <li>Correlate the AI result with comprehensive clinical history, cognitive evaluations (MMSE, MoCA), and patient symptoms.</li>
        <li>Consider formal neurological evaluation when clinically appropriate.</li>
        <li>The AI result should not be used by itself to make treatment decisions.</li>
      </ul>
    </div>

    <!-- 6. Clinician Review -->
    <div class="info-box" style="margin-bottom: 20px;">
      <div class="info-title">6. Clinician Review</div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 12.5px;">
        <div>Clinician Name: <strong>${clinicianName}</strong></div>
        <div>Review Status: <strong>${reviewStatus}</strong></div>
        <div style="grid-column: 1 / -1;">Clinical Impression: <em>${clinicalImpression}</em></div>
        <div style="grid-column: 1 / -1;">Additional Notes: <em>${clinicianNotes}</em></div>
      </div>
    </div>

    <!-- Footer Disclaimer -->
    <div style="text-align: center; font-size: 11px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 12px;">
      NEUROSTAGE AI — Academic Research Prototype • Uncertainty-Aware Patient-Level Alzheimer's Staging
    </div>
  </div>
</body>
</html>
  `;
}

export function printPdfReport(data) {
  const htmlContent = generateReportHtml(data);
  const printWindow = window.open('', '_blank');
  if (printWindow) {
    printWindow.document.write(htmlContent);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
      printWindow.print();
    }, 400);
  }
}

export function downloadHtmlReport(data) {
  const htmlContent = generateReportHtml(data);
  const blob = new Blob([htmlContent], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  const filename = data.filename ? data.filename.replace('.nii.gz', '').replace('.nii', '') : 'mri_scan';
  a.href = url;
  a.download = `AI_Brain_Assessment_Report_${filename}.html`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function downloadJsonReport(data) {
  const jsonContent = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonContent], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  const filename = data.filename ? data.filename.replace('.nii.gz', '').replace('.nii', '') : 'mri_scan';
  a.href = url;
  a.download = `AI_Brain_Assessment_Data_${filename}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export default {
  generateReportHtml,
  printPdfReport,
  downloadHtmlReport,
  downloadJsonReport
};
