// ============================================================
// ALZHEIMER MRI STAGING - NAVBAR COMPONENT
// ============================================================

import React from 'react';
import { Activity, Cpu, BarChart3, Settings2, BrainCircuit } from 'lucide-react';

export default function Navbar({ serverStatus, onNavigate, selectedModel = 'mobilenet_v3' }) {
  const isOnline = serverStatus?.status === 'ok';
  const modelLoaded = serverStatus?.model_loaded;
  const modelDisplayName = selectedModel === 'mobilenet' ? 'MobileNetV2' : 'MobileNetV3-Large';
  const performanceDisplay = serverStatus?.accuracy_display || 'Evaluation pending';

  return (
    <header className="top-navbar">
      <div>
        <h1 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
          Alzheimer’s Disease Staging Portal
        </h1>
        <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px' }}>
          Uncertainty-Aware Patient-Level Analysis Using Lightweight Deep Learning
        </p>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
        {/* Selected Model Dropdown Selector */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => onNavigate && onNavigate('model-selection')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background: '#f8fafc',
              border: '1px solid #cbd5e1',
              borderRadius: '8px',
              padding: '6px 14px',
              fontSize: '0.80rem',
              color: '#334155',
              cursor: 'pointer',
              boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
              transition: 'all 0.15s ease'
            }}
            title="Click to select or switch AI model"
          >
            <div style={{
              width: '20px',
              height: '20px',
              borderRadius: '4px',
              backgroundColor: '#059669',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <BrainCircuit size={13} color="#ffffff" />
            </div>
            <span style={{ color: '#64748b' }}>Selected Model:</span>
            <strong style={{ color: '#0f172a', fontWeight: 600 }}>{modelDisplayName}</strong>
            <span style={{ fontSize: '0.65rem', color: '#94a3b8', marginLeft: '2px' }}>▼</span>
          </button>
        </div>

        {/* Device Badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          background: '#f0f9ff',
          border: '1px solid #bae6fd',
          borderRadius: '20px',
          padding: '6px 14px',
          fontSize: '0.78rem',
          color: '#0369a1',
          fontWeight: 600
        }}>
          <Cpu size={14} color="#0284c7" />
          <span>Device: <strong style={{ color: '#0284c7' }}>{serverStatus?.device?.toUpperCase() || 'CPU'}</strong></span>
        </div>

        {/* 4-Class Staging Pill */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          background: '#e0f2fe',
          border: '1px solid #bae6fd',
          borderRadius: '20px',
          padding: '6px 14px',
          fontSize: '0.78rem',
          color: '#0284c7',
          fontWeight: 700
        }}>
          <span>4-Class Staging</span>
        </div>
      </div>
    </header>
  );
}
