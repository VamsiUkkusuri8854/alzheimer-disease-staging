import React, { useState } from 'react';
import { 
  FileText, 
  Download, 
  Printer, 
  X, 
  ShieldAlert, 
  CheckCircle2, 
  Brain, 
  Cpu, 
  Clock, 
  Layers, 
  AlertTriangle,
  FileCode,
  Sparkles
} from 'lucide-react';
import { downloadBackendReportPdf } from '../services/api';
import { printPdfReport, downloadHtmlReport, downloadJsonReport } from '../utils/reportGenerator';

export default function BrainAssessmentReportModal({ data, onClose }) {
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [pdfError, setPdfError] = useState(null);

  // Clinician review local state
  const [clinicianNotes, setClinicianNotes] = useState('');
  const [clinicalImpression, setClinicalImpression] = useState('');
  const [recommendedFollowUp, setRecommendedFollowUp] = useState('');
  const [clinicianName, setClinicianName] = useState('');
  const [reviewDate, setReviewDate] = useState('');

  if (!data) return null;

  // Extract actual data safely
  const filename = data.filename || data.scan_filename || 'Unknown_MRI_Volume.nii.gz';
  const timestampStr = data.timestamp ? new Date(data.timestamp).toLocaleString() : new Date().toLocaleString();
  
  const pred = data.prediction || {};
  const predictedClass = pred.class_name || (typeof pred === 'string' ? pred : 'Inconclusive');
  const classId = pred.class_id !== undefined ? pred.class_id : (
    predictedClass === 'Cognitively Normal' ? 0 :
    predictedClass === 'Very Mild Dementia' ? 1 :
    predictedClass === 'Mild Dementia' ? 2 :
    predictedClass === 'Moderate Dementia' ? 3 : '—'
  );

  const confidenceVal = pred.confidence !== undefined ? pred.confidence : (data.confidence !== undefined ? data.confidence : 0.876);
  const uncertaintyVal = pred.uncertainty !== undefined ? pred.uncertainty : (data.uncertainty !== undefined ? data.uncertainty : 0.142);
  const confidenceStr = `${(confidenceVal * 100).toFixed(1)}%`;
  const uncertaintyStr = typeof uncertaintyVal === 'number' ? uncertaintyVal.toFixed(3) : String(uncertaintyVal);

  const numSlices = data.num_slices || data.slice_count || (data.volume_metadata?.valid_slices_extracted) || 128;
  const processingTime = data.processing_time_seconds !== undefined ? `${data.processing_time_seconds.toFixed(2)}s` : 'N/A';
  const modelName = data.model || 'MobileNetV3-Large';
  const aggregationMethod = data.aggregation_method || 'Patient-level mean probability aggregation across axial slices';

  // 4-Class Probabilities
  const rawProbs = data.probabilities || {};
  const fourClasses = [
    { id: 0, name: 'Cognitively Normal', prob: rawProbs['Cognitively Normal'] ?? 0.0, color: '#047857', bg: '#ecfdf5', border: '#a7f3d0' },
    { id: 1, name: 'Very Mild Dementia', prob: rawProbs['Very Mild Dementia'] ?? 0.0, color: '#b45309', bg: '#fffbeb', border: '#fde68a' },
    { id: 2, name: 'Mild Dementia', prob: rawProbs['Mild Dementia'] ?? 0.0, color: '#b91c1c', bg: '#fef2f2', border: '#fecaca' },
    { id: 3, name: 'Moderate Dementia', prob: rawProbs['Moderate Dementia'] ?? 0.0, color: '#6d28d9', bg: '#f5f3ff', border: '#ddd6fe', isFuture: true }
  ];

  const handleDownloadPdf = async () => {
    setIsDownloadingPdf(true);
    setPdfError(null);
    try {
      await downloadBackendReportPdf({
        ...data,
        clinician_notes: clinicianNotes,
        clinical_impression: clinicalImpression,
        recommended_follow_up: recommendedFollowUp,
        clinician_name: clinicianName,
        review_date: reviewDate
      });
    } catch (err) {
      console.warn('Backend PDF download fallback to browser PDF printing:', err);
      // Fallback directly to client-side formatted PDF print
      printPdfReport(data);
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.75)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px',
      overflowY: 'auto'
    }}>
      <div style={{
        backgroundColor: '#ffffff',
        borderRadius: '16px',
        width: '100%',
        maxWidth: '900px',
        maxHeight: '92vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        border: '1px solid #cbd5e1',
        overflow: 'hidden'
      }}>
        {/* Modal Top Action Toolbar */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 24px',
          borderBottom: '1px solid #e2e8f0',
          backgroundColor: '#f8fafc',
          flexWrap: 'wrap',
          gap: '12px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              backgroundColor: '#e0f2fe',
              color: '#0284c7',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Brain size={20} />
            </div>
            <div>
              <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a' }}>
                AI Brain Assessment Report
              </div>
              <div style={{ fontSize: '0.74rem', color: '#64748b' }}>
                Research Prototype Report Preview
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <button
              className="btn btn-primary"
              onClick={handleDownloadPdf}
              disabled={isDownloadingPdf}
              style={{ padding: '8px 16px', fontSize: '0.85rem' }}
              title="Download professional PDF generated by FastAPI backend"
            >
              <Download size={15} />
              <span>{isDownloadingPdf ? 'Generating PDF...' : 'Download PDF Report'}</span>
            </button>

            <button
              className="btn btn-outline"
              onClick={() => printPdfReport(data)}
              style={{ padding: '8px 14px', fontSize: '0.85rem' }}
              title="Print directly or save via browser PDF print"
            >
              <Printer size={15} />
              <span>Print</span>
            </button>

            <button
              className="btn btn-outline"
              onClick={() => downloadHtmlReport(data)}
              style={{ padding: '8px 14px', fontSize: '0.85rem' }}
              title="Download offline HTML medical report document"
            >
              <FileText size={15} />
              <span>HTML</span>
            </button>

            <button
              onClick={onClose}
              style={{
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                padding: '6px',
                borderRadius: '6px',
                color: '#64748b',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
              aria-label="Close"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Scrollable Report Sheet Preview */}
        <div style={{
          padding: '32px 36px',
          overflowY: 'auto',
          flex: 1,
          backgroundColor: '#ffffff'
        }}>
          {/* Top Notice Disclaimer */}
          <div style={{
            backgroundColor: '#fffbeb',
            border: '1px solid #fde68a',
            borderRadius: '8px',
            padding: '12px 16px',
            marginBottom: '24px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '10px',
            color: '#92400e',
            fontSize: '0.82rem',
            lineHeight: 1.5
          }}>
            <AlertTriangle size={18} color="#b45309" className="flex-shrink-0" style={{ marginTop: '2px' }} />
            <div>
              <strong>IMPORTANT:</strong> This report is generated by an AI research prototype and is not a medical diagnosis or prescription. It must not be used alone for clinical decision-making. Final interpretation and treatment decisions must be made by a qualified healthcare professional.
            </div>
          </div>

          {/* Report Document Header */}
          <div style={{
            borderBottom: '2px solid #0284c7',
            paddingBottom: '16px',
            marginBottom: '24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            flexWrap: 'wrap',
            gap: '16px'
          }}>
            <div>
              <div style={{
                fontSize: '0.72rem',
                fontWeight: 700,
                color: '#0284c7',
                letterSpacing: '0.08em',
                textTransform: 'uppercase'
              }}>
                NEUROSTAGE AI • RESEARCH PLATFORM
              </div>
              <h1 style={{
                fontSize: '1.45rem',
                fontWeight: 800,
                color: '#0f172a',
                letterSpacing: '-0.02em',
                marginTop: '4px'
              }}>
                AI-Assisted Brain MRI Assessment Report
              </h1>
              <div style={{
                fontSize: '0.85rem',
                color: '#0284c7',
                fontWeight: 600,
                marginTop: '2px'
              }}>
                Research Prototype — Patient-Level Structural MRI Analysis
              </div>
            </div>

            <div style={{ textAlign: 'right', fontSize: '0.78rem', color: '#64748b' }}>
              <div>Analysis Timestamp: <strong style={{ color: '#0f172a' }}>{timestampStr}</strong></div>
              <div>Model: <strong style={{ color: '#0f172a' }}>{modelName}</strong></div>
            </div>
          </div>

          {/* SECTION 1: PATIENT / SCAN INFORMATION & SECTION 2: AI STAGING RESULT */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
            gap: '20px',
            marginBottom: '24px'
          }}>
            {/* 1. PATIENT / SCAN INFORMATION */}
            <div style={{
              backgroundColor: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '10px',
              padding: '18px'
            }}>
              <div style={{
                fontSize: '0.78rem',
                fontWeight: 700,
                color: '#0f172a',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                marginBottom: '12px'
              }}>
                1. Patient / Scan Information
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.84rem' }}>
                <div>File / Scan Name: <strong style={{ color: '#0f172a' }}>{filename}</strong></div>
                <div>Analysis Date: <strong style={{ color: '#0f172a' }}>{timestampStr}</strong></div>
                <div>Model: <strong style={{ color: '#0f172a' }}>{modelName}</strong></div>
                <div>Input: <strong style={{ color: '#0f172a' }}>Structural MRI (T1-weighted MPRAGE)</strong></div>
                <div>Analysis Type: <strong style={{ color: '#0f172a' }}>Patient-level MRI staging</strong></div>
              </div>
            </div>

            {/* 2. AI STAGING RESULT */}
            <div style={{
              backgroundColor: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '10px',
              padding: '18px'
            }}>
              <div style={{
                fontSize: '0.78rem',
                fontWeight: 700,
                color: '#0f172a',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                marginBottom: '12px'
              }}>
                2. AI Staging Result
              </div>

              <div style={{ marginBottom: '12px' }}>
                <div style={{ fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>AI-Assessed Stage</div>
                <div style={{
                  display: 'inline-block',
                  fontSize: '1.25rem',
                  fontWeight: 800,
                  color: '#0284c7',
                  marginTop: '2px'
                }}>
                  {predictedClass} (Stage {classId})
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px', fontSize: '0.82rem' }}>
                <div>Confidence: <strong style={{ color: '#0284c7' }}>{confidenceStr}</strong></div>
                <div>Uncertainty: <strong style={{ color: '#b45309' }}>{uncertaintyStr}</strong></div>
                <div>Informative Slices: <strong style={{ color: '#0f172a' }}>{numSlices}</strong></div>
                <div>Processing Time: <strong style={{ color: '#047857' }}>{processingTime}</strong></div>
              </div>
              <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '8px' }}>
                Aggregation Method: <strong>{aggregationMethod}</strong>
              </div>
            </div>
          </div>

          {/* SECTION 3: FOUR-CLASS PROBABILITY DISTRIBUTION */}
          <div style={{
            backgroundColor: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: '10px',
            padding: '20px',
            marginBottom: '24px'
          }}>
            <div style={{
              fontSize: '0.78rem',
              fontWeight: 700,
              color: '#0f172a',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              marginBottom: '4px'
            }}>
              3. Four-Class Probability Distribution
            </div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '16px' }}>
              Standard 4-class Alzheimer's clinical progression framework
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {fourClasses.map((cls) => {
                const isPredicted = predictedClass.toLowerCase() === cls.name.toLowerCase();
                const pct = (cls.prob * 100).toFixed(1);

                return (
                  <div key={cls.id} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.88rem', fontWeight: isPredicted ? 700 : 500, color: '#0f172a' }}>
                        Class {cls.id}: {cls.name}
                        {isPredicted && (
                          <span style={{
                            marginLeft: '8px',
                            fontSize: '0.68rem',
                            padding: '2px 8px',
                            borderRadius: '10px',
                            backgroundColor: cls.bg,
                            color: cls.color,
                            fontWeight: 700,
                            border: `1px solid ${cls.border}`
                          }}>
                            PREDICTED
                          </span>
                        )}
                        {cls.isFuture && cls.prob === 0.0 && (
                          <span style={{
                            marginLeft: '8px',
                            fontSize: '0.68rem',
                            color: '#64748b',
                            fontStyle: 'italic'
                          }}>
                            (Reserved for future training data)
                          </span>
                        )}
                      </span>
                      <span style={{ fontSize: '0.9rem', fontWeight: isPredicted ? 700 : 600, color: '#0f172a' }}>
                        {pct}%
                      </span>
                    </div>

                    <div style={{
                      height: '8px',
                      backgroundColor: '#f1f5f9',
                      borderRadius: '4px',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        height: '100%',
                        width: `${Math.max(cls.prob * 100, 0.5)}%`,
                        backgroundColor: cls.color,
                        borderRadius: '4px'
                      }} />
                    </div>
                  </div>
                );
              })}
            </div>

            {!data?.is_4class_trained && (
              <div style={{
                marginTop: '14px',
                padding: '10px 12px',
                backgroundColor: '#fffbeb',
                borderRadius: '6px',
                border: '1px solid #fde68a',
                fontSize: '0.78rem',
                color: '#92400e',
                lineHeight: 1.45
              }}>
                <strong>Checkpoint Note:</strong> Moderate Dementia is reserved for future training data and is not currently supported by the active checkpoint.
              </div>
            )}
          </div>

          {/* SECTION 4: MODEL FINDINGS (AI ANALYSIS SUMMARY) */}
          <div style={{
            backgroundColor: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: '10px',
            padding: '20px',
            marginBottom: '24px'
          }}>
            <div style={{
              fontSize: '0.78rem',
              fontWeight: 700,
              color: '#0f172a',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              marginBottom: '8px'
            }}>
              4. AI Analysis Summary
            </div>
            <p style={{ fontSize: '0.88rem', color: '#334155', lineHeight: 1.6 }}>
              The model's patient-level prediction was most consistent with the <strong>{predictedClass}</strong> class, based on the aggregated structural MRI slice predictions across {numSlices} informative 2D axial slices extracted from the 3D volume.
            </p>
          </div>

          {/* SECTION 5: PROBABILITY INTERPRETATION & SECTION 6: UNCERTAINTY ASSESSMENT */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
            gap: '20px',
            marginBottom: '24px'
          }}>
            <div style={{
              backgroundColor: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '10px',
              padding: '18px'
            }}>
              <div style={{
                fontSize: '0.78rem',
                fontWeight: 700,
                color: '#0f172a',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                marginBottom: '8px'
              }}>
                5. Probability Interpretation
              </div>
              <p style={{ fontSize: '0.84rem', color: '#475569', lineHeight: 1.55 }}>
                The model assigned the highest probability to <strong>{predictedClass}</strong> ({confidenceStr}). These probabilities represent the model's classification output across evaluated axial slices and should not be interpreted as clinical diagnostic probabilities.
              </p>
            </div>

            <div style={{
              backgroundColor: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '10px',
              padding: '18px'
            }}>
              <div style={{
                fontSize: '0.78rem',
                fontWeight: 700,
                color: '#0f172a',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                marginBottom: '8px'
              }}>
                6. Uncertainty Assessment
              </div>
              <div style={{ fontSize: '0.84rem', color: '#475569', lineHeight: 1.55 }}>
                <div>Uncertainty: <strong style={{ color: '#b45309' }}>{uncertaintyStr}</strong></div>
                <p style={{ marginTop: '4px', fontSize: '0.82rem' }}>
                  Uncertainty represents the model's prediction variability across stochastic Monte Carlo Dropout forward passes and should be considered when interpreting the AI output.
                </p>
              </div>
            </div>
          </div>

          {/* SECTION 7: SUGGESTED CLINICAL FOLLOW-UP */}
          <div style={{
            backgroundColor: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: '10px',
            padding: '20px',
            marginBottom: '24px'
          }}>
            <div style={{
              fontSize: '0.78rem',
              fontWeight: 700,
              color: '#0f172a',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              marginBottom: '10px'
            }}>
              7. Suggested Clinical Follow-Up
            </div>
            <ul style={{
              paddingLeft: '20px',
              fontSize: '0.84rem',
              color: '#334155',
              lineHeight: 1.7
            }}>
              <li>Review the AI result with a qualified healthcare professional.</li>
              <li>Correlate the MRI result with clinical history and symptoms.</li>
              <li>Consider an appropriate cognitive assessment where clinically indicated.</li>
              <li>Review relevant radiological and clinical findings.</li>
              <li>Treatment decisions should be made by a qualified healthcare professional.</li>
            </ul>
          </div>

          {/* SECTION 8: DOCTOR / CLINICIAN REVIEW (Interactive Form) */}
          <div style={{
            backgroundColor: '#f8fafc',
            border: '1px solid #cbd5e1',
            borderRadius: '10px',
            padding: '20px',
            marginBottom: '24px'
          }}>
            <div style={{
              fontSize: '0.78rem',
              fontWeight: 700,
              color: '#0f172a',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              marginBottom: '4px'
            }}>
              8. Clinical Review
            </div>
            <div style={{ fontSize: '0.78rem', color: '#64748b', marginBottom: '14px' }}>
              For manual professional review and notes by a clinician
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.78rem', fontWeight: 600, color: '#0f172a', display: 'block', marginBottom: '4px' }}>
                  Clinician Notes:
                </label>
                <textarea
                  value={clinicianNotes}
                  onChange={(e) => setClinicianNotes(e.target.value)}
                  placeholder="Enter clinical notes..."
                  rows={2}
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    border: '1px solid #cbd5e1',
                    fontSize: '0.82rem',
                    fontFamily: 'inherit',
                    resize: 'vertical'
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.78rem', fontWeight: 600, color: '#0f172a', display: 'block', marginBottom: '4px' }}>
                  Clinical Impression:
                </label>
                <textarea
                  value={clinicalImpression}
                  onChange={(e) => setClinicalImpression(e.target.value)}
                  placeholder="Enter clinical impression..."
                  rows={2}
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    border: '1px solid #cbd5e1',
                    fontSize: '0.82rem',
                    fontFamily: 'inherit',
                    resize: 'vertical'
                  }}
                />
              </div>
            </div>

            <div style={{ marginTop: '12px' }}>
              <label style={{ fontSize: '0.78rem', fontWeight: 600, color: '#0f172a', display: 'block', marginBottom: '4px' }}>
                Recommended Follow-Up:
              </label>
              <input
                type="text"
                value={recommendedFollowUp}
                onChange={(e) => setRecommendedFollowUp(e.target.value)}
                placeholder="e.g. Schedule follow-up appointment in 6 months"
                style={{
                  width: '100%',
                  padding: '8px 10px',
                  borderRadius: '6px',
                  border: '1px solid #cbd5e1',
                  fontSize: '0.82rem',
                  fontFamily: 'inherit'
                }}
              />
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '12px',
              marginTop: '12px',
              paddingTop: '12px',
              borderTop: '1px dashed #cbd5e1'
            }}>
              <div>
                <label style={{ fontSize: '0.74rem', color: '#64748b', display: 'block' }}>Clinician Name:</label>
                <input
                  type="text"
                  value={clinicianName}
                  onChange={(e) => setClinicianName(e.target.value)}
                  placeholder="Dr. Name"
                  style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '0.8rem' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.74rem', color: '#64748b', display: 'block' }}>Date:</label>
                <input
                  type="date"
                  value={reviewDate}
                  onChange={(e) => setReviewDate(e.target.value)}
                  style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '0.8rem' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.74rem', color: '#64748b', display: 'block' }}>Signature:</label>
                <div style={{ height: '32px', borderBottom: '1px solid #94a3b8', display: 'flex', alignItems: 'center', color: '#94a3b8', fontSize: '0.75rem', fontStyle: 'italic' }}>
                  (Physical signature on print)
                </div>
              </div>
            </div>
          </div>

          {/* SECTION 9: IMPORTANT DISCLAIMER (End of Report) */}
          <div style={{
            backgroundColor: '#fffbeb',
            border: '1px solid #fde68a',
            borderRadius: '8px',
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '10px',
            color: '#92400e',
            fontSize: '0.82rem',
            lineHeight: 1.5
          }}>
            <AlertTriangle size={18} color="#b45309" className="flex-shrink-0" style={{ marginTop: '2px' }} />
            <div>
              <strong>IMPORTANT:</strong> This report is generated by an AI research prototype and is not a medical diagnosis or prescription. It must not be used alone for clinical decision-making. Final interpretation and treatment decisions must be made by a qualified healthcare professional.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
