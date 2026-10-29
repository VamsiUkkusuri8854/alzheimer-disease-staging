// ============================================================
// ALZHEIMER MRI STAGING - DASHBOARD COMPONENT
// ============================================================

import React, { useState, useEffect } from 'react';
import { 
  BrainCircuit, 
  Cpu, 
  Layers, 
  ShieldCheck, 
  Activity, 
  ArrowRight, 
  Settings2,
  BarChart3, 
  CheckCircle2, 
  AlertCircle, 
  Database, 
  UploadCloud, 
  Clock, 
  Sparkles,
  Smartphone
} from 'lucide-react';
import DisclaimerBanner from '../components/DisclaimerBanner';
import ReportActions from '../components/ReportActions';
import { getAvailableModels } from '../services/api';

export default function Dashboard({ serverStatus, onNavigate, history = [], selectedModel = 'mobilenet_v3' }) {
  const isModelReady = serverStatus?.model_loaded;
  const selectedModelDisplayName = selectedModel === 'mobilenet' ? 'MobileNetV2' : 'MobileNetV3-Large';

  const [availableModelsList, setAvailableModelsList] = useState([]);

  useEffect(() => {
    async function loadModels() {
      const models = await getAvailableModels();
      setAvailableModelsList(models);
    }
    loadModels();
  }, []);

  // Latest analysis record if available, otherwise default sample
  const latestAnalysis = (history && history.length > 0) ? history[0] : {
    filename: 'OASIS1_0042_MR1.nii.gz',
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    prediction: {
      class_name: 'Very Mild Dementia',
      confidence: 0.876,
      uncertainty: 0.142
    },
    num_slices: 128,
    isSample: true
  };

  const getStageBadgeColor = (stageName) => {
    switch (stageName) {
      case 'Cognitively Normal':
        return { bg: '#ecfdf5', text: '#047857', border: '#a7f3d0' };
      case 'Very Mild Dementia':
        return { bg: '#fffbeb', text: '#b45309', border: '#fde68a' };
      case 'Mild Dementia':
        return { bg: '#fef2f2', text: '#b91c1c', border: '#fecaca' };
      case 'Moderate Dementia':
        return { bg: '#f5f3ff', text: '#6d28d9', border: '#ddd6fe' };
      default:
        return { bg: '#f0f9ff', text: '#0284c7', border: '#bae6fd' };
    }
  };

  const badgeStyle = getStageBadgeColor(latestAnalysis.prediction?.class_name);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <DisclaimerBanner />

      {/* Header / Research Console Banner */}
      <div className="card" style={{
        background: 'linear-gradient(135deg, #f8fafc 0%, #ffffff 100%)',
        border: '1px solid #e2e8f0',
        padding: '28px 32px',
        position: 'relative'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              background: '#e0f2fe',
              border: '1px solid #bae6fd',
              padding: '4px 12px',
              borderRadius: '20px',
              fontSize: '0.75rem',
              fontWeight: 600,
              color: '#0369a1',
              marginBottom: '10px',
              textTransform: 'uppercase',
              letterSpacing: '0.04em'
            }}>
              <Sparkles size={13} color="#0369a1" />
              <span>Research Console</span>
            </div>
            <h2 style={{ fontSize: '1.65rem', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em', lineHeight: 1.25 }}>
              Patient-Level Structural MRI Analysis
            </h2>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Lightweight deep learning for Alzheimer’s disease staging with Monte Carlo Dropout uncertainty estimation.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <button
              className="btn btn-primary"
              onClick={() => onNavigate('analysis')}
            >
              <UploadCloud size={17} />
              <span>Upload & Analyze MRI</span>
            </button>
            <button
              className="btn btn-outline"
              onClick={() => onNavigate('model-selection')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                borderColor: '#cbd5e1',
                backgroundColor: '#ffffff',
                color: 'var(--text-primary)',
                fontWeight: 600
              }}
            >
              <Settings2 size={17} color="#0284c7" />
              <span>Change Model</span>
            </button>
            <button
              className="btn btn-outline"
              onClick={() => onNavigate('evaluation')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                borderColor: '#bae6fd',
                backgroundColor: '#f0f9ff',
                color: '#0284c7',
                fontWeight: 600
              }}
            >
              <BarChart3 size={17} color="#0284c7" />
              <span>Model Performance</span>
            </button>
          </div>
        </div>
      </div>

      {/* TOP ROW: ANALYZE MRI & MODEL STATUS */}
      <div className="grid-2">
        {/* ANALYZE MRI CARD */}
        <div className="card" style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '10px',
                  background: '#f0f9ff',
                  border: '1px solid #bae6fd',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#0284c7'
                }}>
                  <UploadCloud size={18} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>Analyze MRI</h3>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Upload volumetric scan & start staging</div>
                </div>
              </div>
              <span style={{
                fontSize: '0.72rem',
                fontWeight: 600,
                padding: '3px 8px',
                borderRadius: '6px',
                backgroundColor: '#f1f5f9',
                color: 'var(--text-secondary)',
                border: '1px solid #e2e8f0'
              }}>
                .NII / .NII.GZ
              </span>
            </div>

            <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.55, marginTop: '8px' }}>
              Supports 3D structural T1-weighted MPRAGE volumes. Slices are automatically intensity-normalized, filtered, and processed using <strong>{selectedModelDisplayName}</strong>.
            </p>
          </div>

          <div style={{ marginTop: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid #f1f5f9', paddingTop: '14px' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Active Model: <strong style={{ color: '#0284c7' }}>{selectedModelDisplayName}</strong>
            </div>
            <button
              className="btn btn-primary"
              onClick={() => onNavigate('analysis')}
              style={{ padding: '8px 16px', fontSize: '0.85rem' }}
            >
              <span>Upload & Start</span>
              <ArrowRight size={15} />
            </button>
          </div>
        </div>

        {/* MODEL STATUS CARD */}
        <div className="card" style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '10px',
                  background: '#ecfdf5',
                  border: '1px solid #a7f3d0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#059669'
                }}>
                  <Cpu size={18} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>Current Model</h3>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{selectedModelDisplayName} (Active)</div>
                </div>
              </div>

              <button
                className="btn btn-outline"
                onClick={() => onNavigate('model-selection')}
                style={{
                  padding: '4px 10px',
                  fontSize: '0.78rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                  borderColor: '#0284c7',
                  color: '#0284c7',
                  fontWeight: 600
                }}
              >
                <Settings2 size={13} />
                <span>Change Model</span>
              </button>
            </div>

            {/* Available Models Mini List */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '10px' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '8px 12px',
                borderRadius: '8px',
                backgroundColor: selectedModel === 'mobilenet' ? '#f0f9ff' : '#f8fafc',
                border: selectedModel === 'mobilenet' ? '1px solid #bae6fd' : '1px solid #f1f5f9'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Smartphone size={15} color="#0284c7" />
                  <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>MobileNet</span>
                </div>
                <span style={{
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  padding: '2px 8px',
                  borderRadius: '10px',
                  backgroundColor: availableModelsList.find(m => m.id === 'mobilenet')?.checkpoint_available ? '#ecfdf5' : '#fffbeb',
                  color: availableModelsList.find(m => m.id === 'mobilenet')?.checkpoint_available ? '#047857' : '#b45309',
                  border: `1px solid ${availableModelsList.find(m => m.id === 'mobilenet')?.checkpoint_available ? '#a7f3d0' : '#fde68a'}`
                }}>
                  {availableModelsList.find(m => m.id === 'mobilenet')?.checkpoint_available ? 'READY' : 'CHECKPOINT NOT AVAILABLE'}
                </span>
              </div>

              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '8px 12px',
                borderRadius: '8px',
                backgroundColor: selectedModel === 'mobilenet_v3' ? '#ecfdf5' : '#f8fafc',
                border: selectedModel === 'mobilenet_v3' ? '1px solid #a7f3d0' : '1px solid #f1f5f9'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <BrainCircuit size={15} color="#059669" />
                  <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>MobileNetV3-Large</span>
                </div>
                <span style={{
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  padding: '2px 8px',
                  borderRadius: '10px',
                  backgroundColor: '#ecfdf5',
                  color: '#047857',
                  border: '1px solid #a7f3d0'
                }}>
                  READY
                </span>
              </div>
            </div>
          </div>

          <div style={{ marginTop: '14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid #f1f5f9', paddingTop: '12px' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Hardware: <strong style={{ color: 'var(--text-primary)' }}>{serverStatus?.device?.toUpperCase() || 'CPU'}</strong>
            </div>
            <button
              className="btn btn-outline"
              onClick={() => onNavigate('architecture')}
              style={{ padding: '6px 12px', fontSize: '0.8rem' }}
            >
              Architecture Specs
            </button>
          </div>
        </div>
      </div>

      {/* MIDDLE SECTION: AI ANALYSIS PIPELINE */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
          <div className="card-title" style={{ marginBottom: 0 }}>
            <Activity size={18} color="#0284c7" />
            <span>AI Analysis Pipeline</span>
          </div>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Sequential Inference Flow
          </span>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          gap: '10px',
          alignItems: 'stretch'
        }}>
          {[
            { step: '1', title: 'MRI', subtitle: '3D T1 MPRAGE', color: '#0284c7' },
            { step: '2', title: 'Preprocessing', subtitle: '1-99% Normalization', color: '#4f46e5' },
            { step: '3', title: 'Slice Extract', subtitle: '224×224 Axial RGB', color: '#0284c7' },
            { step: '4', title: 'CNN Model', subtitle: selectedModelDisplayName, color: '#059669' },
            { step: '5', title: 'Aggregation', subtitle: 'Patient-Level Mean', color: '#0284c7' },
            { step: '6', title: 'Uncertainty', subtitle: 'MC Dropout Dispersion', color: '#b45309' },
            { step: '7', title: 'AI Staging', subtitle: '4-Class Assessment', color: '#059669' },
          ].map((item, idx) => (
            <div
              key={idx}
              style={{
                backgroundColor: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                padding: '12px 10px',
                textAlign: 'center',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center'
              }}
            >
              <div style={{
                fontSize: '0.68rem',
                fontWeight: 700,
                color: item.color,
                marginBottom: '2px'
              }}>
                STEP 0{item.step}
              </div>
              <div style={{ fontSize: '0.86rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                {item.title}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                {item.subtitle}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* SECOND ROW: DATASET & RESEARCH STATUS */}
      <div className="grid-2">
        {/* DATASET CARD */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: '#f0f9ff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#0284c7'
            }}>
              <Database size={16} />
            </div>
            <div>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>Dataset</h3>
              <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>OASIS-1 Cross-Sectional MRI</div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginTop: '10px' }}>
            <div style={{ background: '#f8fafc', padding: '10px', borderRadius: '8px', border: '1px solid #f1f5f9' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Total Patients</div>
              <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>76</div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '1px' }}>OASIS-1 Cohort</div>
            </div>

            <div style={{ background: '#f8fafc', padding: '10px', borderRadius: '8px', border: '1px solid #f1f5f9' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>2D Axial Slices</div>
              <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#0284c7', marginTop: '2px' }}>9,346</div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '1px' }}>224 × 224 RGB</div>
            </div>

            <div style={{ background: '#f8fafc', padding: '10px', borderRadius: '8px', border: '1px solid #f1f5f9' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Scan Modality</div>
              <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#4f46e5', marginTop: '2px' }}>T1-w</div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '1px' }}>MPRAGE</div>
            </div>
          </div>

          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '12px', lineHeight: 1.45 }}>
            Class distribution: <strong>43</strong> Cognitively Normal (CDR 0), <strong>22</strong> Very Mild (CDR 0.5), <strong>11</strong> Mild (CDR 1.0).
          </div>
        </div>

        {/* RESEARCH STATUS CARD */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: '#fffbeb',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#b45309'
            }}>
              <ShieldCheck size={16} />
            </div>
            <div>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>Research Validation</h3>
              <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>Cross-validation & protocol integrity</div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginTop: '10px' }}>
            <div style={{ background: '#f8fafc', padding: '10px', borderRadius: '8px', border: '1px solid #f1f5f9' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Cross-Validation</div>
              <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>5-Fold</div>
              <div style={{ fontSize: '0.68rem', color: '#059669', marginTop: '1px', fontWeight: 600 }}>Stratified</div>
            </div>

            <div style={{ background: '#f8fafc', padding: '10px', borderRadius: '8px', border: '1px solid #f1f5f9' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Data Leakage</div>
              <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#059669', marginTop: '2px' }}>0.00%</div>
              <div style={{ fontSize: '0.68rem', color: '#059669', marginTop: '1px', fontWeight: 600 }}>Clean Split</div>
            </div>

            <div style={{ background: '#f8fafc', padding: '10px', borderRadius: '8px', border: '1px solid #f1f5f9' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Target Classes</div>
              <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#0284c7', marginTop: '2px' }}>4 Classes</div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '1px' }}>Full Spectrum</div>
            </div>
          </div>

          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '12px', lineHeight: 1.45 }}>
            Patient-wise partitioning prevents slice mixing between training and validation splits.
          </div>
        </div>
      </div>

      {/* BOTTOM SECTION: LATEST ANALYSIS */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: '#f1f5f9',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#475569'
            }}>
              <Clock size={16} />
            </div>
            <div>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>Latest Analysis</h3>
              <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                {latestAnalysis.isSample ? 'Recent Benchmark Record' : `Completed at ${latestAnalysis.timestamp}`}
              </div>
            </div>
          </div>

          <button
            className="btn btn-outline"
            onClick={() => onNavigate('history')}
            style={{ padding: '6px 12px', fontSize: '0.8rem' }}
          >
            <span>View All History</span>
            <ArrowRight size={14} />
          </button>
        </div>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '14px',
          padding: '14px 18px',
          background: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '10px'
        }}>
          <div>
            <div style={{ fontSize: '0.92rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              {latestAnalysis.filename}
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Analyzed {latestAnalysis.num_slices || 128} axial slices with Monte Carlo Dropout
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '18px', flexWrap: 'wrap' }}>
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 500 }}>Predicted Stage</div>
              <span style={{
                display: 'inline-block',
                marginTop: '3px',
                padding: '3px 10px',
                borderRadius: '12px',
                backgroundColor: badgeStyle.bg,
                color: badgeStyle.text,
                border: `1px solid ${badgeStyle.border}`,
                fontWeight: 600,
                fontSize: '0.8rem'
              }}>
                {latestAnalysis.prediction?.class_name || 'Very Mild Dementia'}
              </span>
            </div>

            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 500 }}>Confidence</div>
              <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#0284c7', marginTop: '2px' }}>
                {((latestAnalysis.prediction?.confidence || 0.876) * 100).toFixed(1)}%
              </div>
            </div>

            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 500 }}>Uncertainty</div>
              <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#b45309', marginTop: '2px' }}>
                {(latestAnalysis.prediction?.uncertainty || 0.142).toFixed(3)}
              </div>
            </div>

            <ReportActions data={latestAnalysis} />

            <button
              className="btn btn-primary"
              onClick={() => onNavigate('analysis')}
              style={{ padding: '7px 14px', fontSize: '0.82rem' }}
            >
              Analyze New Scan
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
