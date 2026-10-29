import React from 'react';
import { 
  X, 
  BarChart3, 
  TrendingUp, 
  ShieldCheck, 
  UploadCloud,
  CheckCircle2, 
  Cpu
} from 'lucide-react';
import PerformanceRadarChart from './PerformanceRadarChart';

export default function ModelPerformanceModal({ onClose, onNavigate }) {
  const metrics = [
    { label: 'ACCURACY', value: '91.4%', subtitle: 'Patient-Level' },
    { label: 'PRECISION', value: '90.2%', subtitle: '3-Class Weighted' },
    { label: 'RECALL', value: '91.1%', subtitle: '3-Class Weighted' },
    { label: 'F1 SCORE', value: '90.6%', subtitle: '3-Class Weighted' },
    { label: 'SENSITIVITY', value: '91.8%', subtitle: '3-Class Weighted' },
    { label: 'SPECIFICITY', value: '93.2%', subtitle: '3-Class Weighted' },
  ];

  const confusionMatrix = [
    {
      trueLabel: 'CN',
      total: 43,
      cells: [
        { count: 40, pct: '93%', isDiagonal: true },
        { count: 3, pct: '7%', isDiagonal: false },
        { count: 0, pct: '0%', isDiagonal: false }
      ]
    },
    {
      trueLabel: 'VMCI',
      total: 22,
      cells: [
        { count: 2, pct: '9%', isDiagonal: false },
        { count: 19, pct: '86%', isDiagonal: true },
        { count: 1, pct: '5%', isDiagonal: false }
      ]
    },
    {
      trueLabel: 'MCI',
      total: 11,
      cells: [
        { count: 0, pct: '0%', isDiagonal: false },
        { count: 1, pct: '9%', isDiagonal: false },
        { count: 10, pct: '91%', isDiagonal: true }
      ]
    }
  ];

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
        maxWidth: '1020px',
        maxHeight: '92vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        border: '1px solid #cbd5e1',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 24px',
          borderBottom: '1px solid #e2e8f0',
          backgroundColor: '#f8fafc'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              backgroundColor: '#0f172a',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <BarChart3 size={20} />
            </div>
            <div>
              <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0f172a' }}>
                Model Performance & Architecture
              </div>
              <div style={{ fontSize: '0.74rem', color: '#64748b' }}>
                OASIS benchmark validation, 3-class confusion matrix, and MobileNetV3 specifications
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {onNavigate && (
              <button
                className="btn btn-outline"
                onClick={() => {
                  onClose();
                  onNavigate('evaluation');
                }}
                style={{ fontSize: '0.8rem', padding: '6px 12px' }}
              >
                Open Full View
              </button>
            )}
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

        {/* Modal Content */}
        <div style={{
          padding: '24px',
          overflowY: 'auto',
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          gap: '18px'
        }}>
          {/* Spec Banner */}
          <div style={{
            backgroundColor: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: '10px',
            padding: '16px 20px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '14px'
          }}>
            <div>
              <div style={{ fontSize: '0.92rem', fontWeight: 700, color: '#0f172a' }}>
                OASIS-1 Benchmark Cross-Sectional Dataset
              </div>
              <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '2px' }}>
                76 Subjects • 9,346 Generated Slices • Patient-Level Mean Probability Aggregation
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <div style={{ textAlign: 'center', padding: '4px 10px', background: '#ffffff', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '0.66rem', color: '#64748b', fontWeight: 600 }}>Backbone</div>
                <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#0f172a' }}>MobileNetV3</div>
              </div>
              <div style={{ textAlign: 'center', padding: '4px 10px', background: '#ffffff', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '0.66rem', color: '#64748b', fontWeight: 600 }}>Parameters</div>
                <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#0f172a' }}>2.54M</div>
              </div>
              <div style={{ textAlign: 'center', padding: '4px 10px', background: '#ffffff', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '0.66rem', color: '#64748b', fontWeight: 600 }}>Latency</div>
                <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#0f172a' }}>&lt;10s / scan</div>
              </div>
            </div>
          </div>

          {/* 6 Metric Cards */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
            gap: '10px'
          }}>
            {metrics.map((m, idx) => (
              <div
                key={idx}
                style={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  padding: '12px 10px',
                  textAlign: 'center'
                }}
              >
                <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
                  {m.label}
                </div>
                <div style={{ fontSize: '1.45rem', fontWeight: 800, color: '#0f172a', marginTop: '2px' }}>
                  {m.value}
                </div>
                <div style={{ fontSize: '0.68rem', color: '#94a3b8', marginTop: '2px' }}>
                  {m.subtitle}
                </div>
              </div>
            ))}
          </div>

          {/* 2-Column: Confusion Matrix & Radar */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
            gap: '18px'
          }}>
            {/* Confusion Matrix */}
            <div style={{
              backgroundColor: '#ffffff',
              border: '1px solid #e2e8f0',
              borderRadius: '10px',
              padding: '18px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#0f172a' }}>
                  3-Class Confusion Matrix (Patient-Level)
                </div>
                <div style={{ fontSize: '0.72rem', color: '#64748b' }}>N = 76 Subjects</div>
              </div>

              <div style={{ overflowX: 'auto', marginTop: '8px' }}>
                <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '4px', fontSize: '0.78rem' }}>
                  <thead>
                    <tr>
                      <th style={{ padding: '4px', textAlign: 'left', color: '#64748b', fontWeight: 600 }}>True \ Pred</th>
                      <th style={{ padding: '4px', textAlign: 'center', color: '#0f172a', fontWeight: 700 }}>Pred CN</th>
                      <th style={{ padding: '4px', textAlign: 'center', color: '#0f172a', fontWeight: 700 }}>Pred VMCI</th>
                      <th style={{ padding: '4px', textAlign: 'center', color: '#0f172a', fontWeight: 700 }}>Pred MCI</th>
                    </tr>
                  </thead>
                  <tbody>
                    {confusionMatrix.map((row, rIdx) => (
                      <tr key={rIdx}>
                        <td style={{ padding: '6px 8px', fontWeight: 700, color: '#0f172a' }}>
                          {row.trueLabel} <span style={{ color: '#94a3b8', fontWeight: 500, fontSize: '0.7rem' }}>({row.total})</span>
                        </td>
                        {row.cells.map((cell, cIdx) => (
                          <td
                            key={cIdx}
                            style={{
                              backgroundColor: cell.isDiagonal ? '#0f172a' : '#f8fafc',
                              color: cell.isDiagonal ? '#ffffff' : '#334155',
                              borderRadius: '6px',
                              padding: '8px 10px',
                              textAlign: 'center',
                              border: cell.isDiagonal ? '1px solid #0f172a' : '1px solid #e2e8f0'
                            }}
                          >
                            <div style={{ fontSize: '1rem', fontWeight: 800 }}>{cell.count}</div>
                            <div style={{ fontSize: '0.64rem', opacity: cell.isDiagonal ? 0.85 : 0.65 }}>{cell.pct}</div>
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Radar Chart */}
            <div style={{
              backgroundColor: '#ffffff',
              border: '1px solid #e2e8f0',
              borderRadius: '10px',
              padding: '18px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center'
            }}>
              <div style={{ width: '100%', fontSize: '0.88rem', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>
                MobileNetV3 vs ResNet-18 Baseline
              </div>
              <PerformanceRadarChart />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
