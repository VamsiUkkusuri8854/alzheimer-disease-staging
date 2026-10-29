import React, { useState } from 'react';
import { History as HistoryIcon, Trash2, Calendar, FileText, ArrowRight, ArrowLeft, Clock, Cpu, Layers, Sparkles, AlertTriangle, Timer } from 'lucide-react';
import DisclaimerBanner from '../components/DisclaimerBanner';
import ProbabilityBarChart from '../components/ProbabilityBarChart';
import ReportActions from '../components/ReportActions';
import BrainAssessmentReportModal from '../components/BrainAssessmentReportModal';

export default function History({ history = [], onClearHistory, onNavigate }) {
  const [confirmClear, setConfirmClear] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(null);
  const [reportModalData, setReportModalData] = useState(null);

  const getStageBadgeClass = (className) => {
    if (className === 'Cognitively Normal') return 'badge-cn';
    if (className === 'Very Mild Dementia') return 'badge-very-mild';
    if (className === 'Mild Dementia') return 'badge-mild';
    return 'badge-moderate';
  };

  const handleClearClick = () => {
    setConfirmClear(true);
  };

  const handleConfirmClear = () => {
    onClearHistory();
    setConfirmClear(false);
    setSelectedIndex(null);
  };

  const handleCancelClear = () => {
    setConfirmClear(false);
  };

  if (selectedIndex !== null && history[selectedIndex]) {
    const item = history[selectedIndex];
    const dateStr = new Date(item.timestamp).toLocaleString();

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <DisclaimerBanner />

        <button
          className="btn btn-outline"
          onClick={() => setSelectedIndex(null)}
          style={{ alignSelf: 'flex-start' }}
        >
          <ArrowLeft size={15} />
          <span>Back to History</span>
        </button>

        {/* Result Banner */}
        <div className="card" style={{
          background: 'linear-gradient(135deg, #f0f9ff 0%, #ffffff 100%)',
          border: '1px solid #bae6fd',
          padding: '24px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
            <div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Predicted Patient Stage
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '4px' }}>
                <h3 style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
                  {item.prediction?.class_name}
                </h3>
                <span className={`badge ${getStageBadgeClass(item.prediction?.class_name)}`}>
                  Stage {item.prediction?.class_id}
                </span>
              </div>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Source scan: <strong style={{ color: 'var(--text-secondary)' }}>{item.filename}</strong>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
              <button
                className="btn btn-primary"
                onClick={() => setReportModalData(item)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '9px 18px',
                  fontSize: '0.88rem',
                  fontWeight: 600,
                  boxShadow: '0 2px 4px rgba(2, 132, 199, 0.2)'
                }}
              >
                <FileText size={16} />
                <span>Generate AI Brain Report</span>
              </button>
              <ReportActions data={item} onOpenReportModal={() => setReportModalData(item)} />
            </div>
          </div>

          {/* Quick Metrics Bar */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
            gap: '14px',
            marginTop: '20px',
            paddingTop: '18px',
            borderTop: '1px solid #e2e8f0'
          }}>
            <div>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: 600 }}>Confidence</div>
              <div style={{ fontSize: '1.45rem', fontWeight: 700, color: '#0284c7' }}>
                {(item.confidence * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Maximum probability</div>
            </div>

            <div>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: 600 }}>Uncertainty</div>
              <div style={{ fontSize: '1.45rem', fontWeight: 700, color: '#b45309' }}>
                {item.uncertainty?.toFixed(3)}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Stochastic MC dispersion</div>
            </div>

            <div>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: 600 }}>Slices Analyzed</div>
              <div style={{ fontSize: '1.45rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                {item.num_slices}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>224×224 RGB axial slices</div>
            </div>

            <div>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: 600 }}>Inference Model</div>
              <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
                {item.model || 'MobileNetV3-Large'}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Mean probability aggregation</div>
            </div>

            {item.processing_time_seconds != null && (
              <div>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: 600 }}>Processing Time</div>
                <div style={{ fontSize: '1.45rem', fontWeight: 700, color: '#047857' }}>
                  {item.processing_time_seconds.toFixed(1)}s
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>End-to-end measured</div>
              </div>
            )}
          </div>
        </div>

        {/* Probability Chart */}
        {item.probabilities && (
          <div className="card">
            <div className="card-title">
              <Sparkles size={18} color="#0284c7" />
              <span>Class Probability Distribution</span>
            </div>
            <div className="card-subtitle">
              Patient-level aggregated probability across all axial brain slices
            </div>
            <ProbabilityBarChart
              probabilities={item.probabilities}
              predictedClass={item.prediction?.class_name}
            />
          </div>
        )}

        {/* Additional Metadata */}
        <div className="card">
          <div className="card-title">
            <FileText size={18} color="#0284c7" />
            <span>Analysis Metadata</span>
          </div>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '10px',
            marginTop: '10px',
            fontSize: '0.82rem',
            color: 'var(--text-secondary)'
          }}>
            <div>Filename: <strong style={{ color: 'var(--text-primary)' }}>{item.filename}</strong></div>
            <div>Timestamp: <strong style={{ color: 'var(--text-primary)' }}>{dateStr}</strong></div>
            <div>Model: <strong style={{ color: 'var(--text-primary)' }}>{item.model || 'MobileNetV3-Large'}</strong></div>
            {item.num_slices != null && (
              <div>Informative Slices: <strong style={{ color: 'var(--text-primary)' }}>{item.num_slices}</strong></div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <DisclaimerBanner />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <h2 style={{ fontSize: '1.65rem', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Prediction History
          </h2>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Local session history stored securely in your browser's localStorage.
          </p>
        </div>

        {history.length > 0 && (
          <button
            className="btn btn-outline"
            onClick={handleClearClick}
            style={{ color: '#b91c1c', borderColor: '#fecaca', background: '#fef2f2' }}
          >
            <Trash2 size={15} color="#b91c1c" />
            <span>Clear History</span>
          </button>
        )}
      </div>

      {/* Confirmation Dialog */}
      {confirmClear && (
        <div className="card" style={{
          background: '#fef2f2',
          border: '1px solid #fecaca',
          padding: '18px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '14px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <AlertTriangle size={20} color="#b91c1c" />
            <div>
              <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#991b1b' }}>
                Clear all analysis history?
              </div>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                This action cannot be undone. All saved prediction results will be permanently removed.
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="btn btn-outline" onClick={handleCancelClear}>
              Cancel
            </button>
            <button
              className="btn btn-primary"
              onClick={handleConfirmClear}
              style={{ background: '#dc2626' }}
            >
              <Trash2 size={15} />
              <span>Confirm Clear</span>
            </button>
          </div>
        </div>
      )}

      {history.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '50px 20px' }}>
          <div style={{
            width: '50px',
            height: '50px',
            borderRadius: '50%',
            backgroundColor: '#f1f5f9',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 14px',
            color: 'var(--text-muted)'
          }}>
            <HistoryIcon size={24} />
          </div>
          <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            No Analysis History Found
          </div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px', maxWidth: '400px', margin: '4px auto 18px' }}>
            Uploaded scans and their model staging predictions will be saved here automatically.
          </div>
          <button
            className="btn btn-primary"
            onClick={() => onNavigate('analysis')}
          >
            Start First Analysis
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {history.map((item, index) => {
            const dateStr = new Date(item.timestamp).toLocaleString();
            return (
              <div
                key={item.id || index}
                className="card"
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '16px 20px',
                  flexWrap: 'wrap',
                  gap: '14px',
                  cursor: 'pointer',
                  background: '#ffffff'
                }}
                onClick={() => setSelectedIndex(index)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                  <div style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '10px',
                    backgroundColor: '#f0f9ff',
                    border: '1px solid #bae6fd',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#0284c7'
                  }}>
                    <FileText size={20} />
                  </div>
                  <div>
                    <div style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {item.filename}
                    </div>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      fontSize: '0.78rem',
                      color: 'var(--text-muted)',
                      marginTop: '2px'
                    }}>
                      <Calendar size={13} />
                      <span>{dateStr}</span>
                      <span>•</span>
                      <span>{item.num_slices} slices</span>
                      {item.processing_time_seconds != null && (
                        <>
                          <span>•</span>
                          <Timer size={13} />
                          <span>{item.processing_time_seconds.toFixed(1)}s</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 500 }}>
                      Confidence
                    </div>
                    <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#0284c7' }}>
                      {(item.confidence * 100).toFixed(1)}%
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 500 }}>
                      Uncertainty
                    </div>
                    <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#b45309' }}>
                      {item.uncertainty?.toFixed(3)}
                    </div>
                  </div>

                  <span className={`badge ${getStageBadgeClass(item.prediction?.class_name)}`}>
                    {item.prediction?.class_name}
                  </span>

                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }} onClick={(e) => e.stopPropagation()}>
                    <button
                      className="btn btn-outline"
                      onClick={() => setSelectedIndex(index)}
                      style={{ padding: '6px 12px', fontSize: '0.8rem' }}
                      title="View complete analysis details"
                    >
                      View Result
                    </button>

                    <button
                      className="btn btn-primary"
                      onClick={() => setReportModalData(item)}
                      style={{
                        padding: '6px 14px',
                        fontSize: '0.8rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}
                      title="Generate and preview AI Brain Assessment Report"
                    >
                      <FileText size={14} />
                      <span>Generate Report</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Brain Assessment Report Modal */}
      {reportModalData && (
        <BrainAssessmentReportModal
          data={reportModalData}
          onClose={() => setReportModalData(null)}
        />
      )}
    </div>
  );
}
