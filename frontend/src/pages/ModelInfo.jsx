// ============================================================
// ALZHEIMER MRI STAGING - MODEL ARCHITECTURE & PIPELINE PAGE
// ============================================================

import React, { useEffect, useState } from 'react';
import { 
  Cpu, 
  Database, 
  Layers, 
  ArrowDown, 
  CheckCircle, 
  AlertTriangle, 
  BrainCircuit, 
  Smartphone, 
  Settings2,
  Sparkles,
  ShieldCheck,
  Activity
} from 'lucide-react';
import { getModelInfo, getAvailableModels } from '../services/api';
import DisclaimerBanner from '../components/DisclaimerBanner';

export default function ModelInfo({ serverStatus, onNavigate, selectedModel = 'mobilenet_v3' }) {
  const [modelDetails, setModelDetails] = useState(null);
  const [modelsList, setModelsList] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchInfo() {
      try {
        const [info, models] = await Promise.all([
          getModelInfo(selectedModel),
          getAvailableModels()
        ]);
        setModelDetails(info);
        setModelsList(models);
      } catch (e) {
        console.warn('Could not fetch dynamic model info:', e);
      } finally {
        setLoading(false);
      }
    }
    fetchInfo();
  }, [selectedModel]);

  const is4ClassTrained = serverStatus?.is_4class_trained;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <DisclaimerBanner />

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
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
            textTransform: 'uppercase'
          }}>
            <Cpu size={14} />
            <span>NEUROSTAGE AI • Model Specifications</span>
          </div>

          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Model & Architecture
          </h1>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Detailed scientific parameters of the supported lightweight deep learning models and sequential inference pipeline.
          </p>
        </div>

        <button
          className="btn btn-primary"
          onClick={() => onNavigate && onNavigate('model-selection')}
          style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <Settings2 size={16} />
          <span>Change Model</span>
        </button>
      </div>

      {/* TWO SUPPORTED MODELS COMPARISON */}
      <div className="grid-2">
        {/* MODEL 1: MobileNet */}
        <div className="card" style={{
          border: selectedModel === 'mobilenet' ? '2px solid #0284c7' : '1px solid #e2e8f0',
          backgroundColor: '#ffffff'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{
                width: '42px',
                height: '42px',
                borderRadius: '10px',
                backgroundColor: '#e0f2fe',
                color: '#0284c7',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Smartphone size={22} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)' }}>MobileNet</h3>
                <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>MobileNet-V2 Inverted Residuals</div>
              </div>
            </div>

            <span style={{
              fontSize: '0.72rem',
              fontWeight: 600,
              padding: '3px 10px',
              borderRadius: '12px',
              backgroundColor: '#fffbeb',
              color: '#b45309',
              border: '1px solid #fde68a'
            }}>
              CHECKPOINT PENDING
            </span>
          </div>

          <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '16px' }}>
            Lightweight convolutional neural network with depthwise separable convolutions and linear bottleneck inverted residuals.
          </p>

          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            fontSize: '0.8rem',
            backgroundColor: '#f8fafc',
            padding: '14px',
            borderRadius: '8px',
            border: '1px solid #e2e8f0'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Backbone:</span>
              <strong style={{ color: 'var(--text-primary)' }}>torchvision.models.mobilenet_v2</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Input Resolution:</span>
              <strong style={{ color: 'var(--text-primary)' }}>224 × 224 × 3 (RGB)</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Target Classes:</span>
              <strong style={{ color: 'var(--text-primary)' }}>4 Classes (CN, VMCI, MCI, Moderate)</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Status:</span>
              <strong style={{ color: '#b45309' }}>Checkpoint not available yet</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Accuracy:</span>
              <strong style={{ color: '#b45309' }}>Evaluation pending</strong>
            </div>
          </div>
        </div>

        {/* MODEL 2: MobileNetV3-Large */}
        <div className="card" style={{
          border: selectedModel === 'mobilenet_v3' ? '2px solid #059669' : '1px solid #e2e8f0',
          backgroundColor: '#ffffff'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{
                width: '42px',
                height: '42px',
                borderRadius: '10px',
                backgroundColor: '#ecfdf5',
                color: '#059669',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <BrainCircuit size={22} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)' }}>MobileNetV3-Large</h3>
                <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>Hard-Swish + Squeeze-and-Excitation</div>
              </div>
            </div>

            <span style={{
              fontSize: '0.72rem',
              fontWeight: 600,
              padding: '3px 10px',
              borderRadius: '12px',
              backgroundColor: '#ecfdf5',
              color: '#047857',
              border: '1px solid #a7f3d0'
            }}>
              READY
            </span>
          </div>

          <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '16px' }}>
            Modern lightweight CNN optimized for edge deployment using hard-swish activation functions and squeeze-and-excitation attention.
          </p>

          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            fontSize: '0.8rem',
            backgroundColor: '#f8fafc',
            padding: '14px',
            borderRadius: '8px',
            border: '1px solid #e2e8f0'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Backbone:</span>
              <strong style={{ color: 'var(--text-primary)' }}>torchvision.models.mobilenet_v3_large</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Input Resolution:</span>
              <strong style={{ color: 'var(--text-primary)' }}>224 × 224 × 3 (RGB)</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Target Classes:</span>
              <strong style={{ color: 'var(--text-primary)' }}>4 Classes (CN, VMCI, MCI, Moderate)</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Status:</span>
              <strong style={{ color: '#047857' }}>Loaded & Cached in Memory</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Accuracy:</span>
              <strong style={{ color: '#047857' }}>Evaluation pending</strong>
            </div>
          </div>
        </div>
      </div>

      {/* COMMON INFERENCE PIPELINE (STEP-BY-STEP) */}
      <div className="card">
        <div className="card-title">
          <Layers size={18} color="#0284c7" />
          <span>End-to-End Inference Pipeline</span>
        </div>
        <div className="card-subtitle">
          Sequential execution flow from raw 3D NIfTI structural MRI to uncertainty-aware patient staging
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '12px',
          marginTop: '16px'
        }}>
          {[
            {
              step: '01',
              title: 'MRI Volume Input',
              desc: '3D T1-weighted MPRAGE structural MRI volume (.nii or .nii.gz).'
            },
            {
              step: '02',
              title: 'Preprocessing',
              desc: '1st–99th percentile non-zero intensity clipping & background noise filtering.'
            },
            {
              step: '03',
              title: 'Informative Slice Extraction',
              desc: 'Extract 224×224 RGB axial slices spanning representative brain anatomy.'
            },
            {
              step: '04',
              title: 'CNN Model',
              desc: 'Forward pass through selected lightweight model (MobileNet or MobileNetV3).'
            },
            {
              step: '05',
              title: 'Slice-Level Prediction',
              desc: 'Compute Softmax class logits and probability distributions per 2D slice.'
            },
            {
              step: '06',
              title: 'Patient-Level Aggregation',
              desc: 'Mean probability pooling across all valid axial slices.'
            },
            {
              step: '07',
              title: 'Uncertainty Estimation',
              desc: 'Monte Carlo Dropout stochastic passes computing predictive entropy and slice variance.'
            },
            {
              step: '08',
              title: 'AI Predicted Stage',
              desc: 'Structured report output with confidence, uncertainty, and 4-class distribution.'
            }
          ].map((item, idx) => (
            <div
              key={idx}
              style={{
                backgroundColor: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '10px',
                padding: '16px 14px',
                display: 'flex',
                flexDirection: 'column',
                gap: '4px'
              }}
            >
              <span style={{ fontSize: '0.7rem', fontWeight: 800, color: '#0284c7' }}>
                STEP {item.step}
              </span>
              <strong style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                {item.title}
              </strong>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: '4px 0 0', lineHeight: 1.45 }}>
                {item.desc}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* 4-Class Framework Reference */}
      <div className="card">
        <div className="card-title">
          <Database size={18} color="#0284c7" />
          <span>Four-Class Disease Staging Framework</span>
        </div>
        <div className="card-subtitle">
          Standardized clinical mapping across all models
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '12px',
          marginTop: '14px'
        }}>
          {[
            { id: 0, name: 'Cognitively Normal', cdr: 'CDR 0.0', desc: 'No dementia symptoms; normal memory and reasoning functions', color: '#047857', bg: '#ecfdf5', border: '#a7f3d0' },
            { id: 1, name: 'Very Mild Dementia', cdr: 'CDR 0.5', desc: 'Very mild cognitive impairment; subtle memory lapses', color: '#b45309', bg: '#fffbeb', border: '#fde68a' },
            { id: 2, name: 'Mild Dementia', cdr: 'CDR 1.0', desc: 'Mild Alzheimer’s disease; moderate memory and judgment difficulties', color: '#b91c1c', bg: '#fef2f2', border: '#fecaca' },
            { id: 3, name: 'Moderate Dementia', cdr: 'CDR 2.0', desc: 'Moderate Alzheimer’s disease; severe memory loss, requiring daily assistance', color: '#6d28d9', bg: '#f5f3ff', border: '#ddd6fe' },
          ].map((cls) => (
            <div
              key={cls.id}
              style={{
                backgroundColor: cls.bg,
                border: `1px solid ${cls.border}`,
                borderRadius: '10px',
                padding: '14px 16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '4px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.74rem', fontWeight: 700, color: cls.color }}>CLASS {cls.id}</span>
                <span style={{ fontSize: '0.74rem', fontWeight: 600, color: cls.color, backgroundColor: '#ffffff', padding: '1px 6px', borderRadius: '4px' }}>
                  {cls.cdr}
                </span>
              </div>
              <strong style={{ fontSize: '0.95rem', color: '#0f172a' }}>{cls.name}</strong>
              <span style={{ fontSize: '0.78rem', color: '#475569', marginTop: '2px', lineHeight: 1.4 }}>
                {cls.desc}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
