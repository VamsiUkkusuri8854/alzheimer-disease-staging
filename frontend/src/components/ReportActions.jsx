import React, { useState } from 'react';
import { Download, FileText, Printer, FileCode, ChevronDown, Brain } from 'lucide-react';
import { printPdfReport, downloadHtmlReport, downloadJsonReport } from '../utils/reportGenerator';
import { downloadBackendReportPdf } from '../services/api';

export default function ReportActions({ data, onOpenReportModal }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);

  if (!data) return null;

  const handleBackendPdf = async () => {
    setIsDownloadingPdf(true);
    setIsOpen(false);
    try {
      await downloadBackendReportPdf(data);
    } catch (err) {
      console.warn('Backend PDF failed, falling back to print dialog:', err);
      printPdfReport(data);
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          className="btn btn-outline"
          onClick={() => setIsOpen(!isOpen)}
          style={{
            padding: '9px 14px',
            fontSize: '0.88rem',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
          title="Export / Download Options"
        >
          <Download size={16} />
          <span>Export Report</span>
          <ChevronDown size={14} />
        </button>
      </div>

      {isOpen && (
        <>
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              zIndex: 90
            }}
            onClick={() => setIsOpen(false)}
          />
          <div style={{
            position: 'absolute',
            right: 0,
            marginTop: '6px',
            background: '#ffffff',
            border: '1px solid #cbd5e1',
            borderRadius: '8px',
            boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
            minWidth: '240px',
            zIndex: 100,
            padding: '6px 0',
            overflow: 'hidden'
          }}>
            {onOpenReportModal && (
              <button
                onClick={() => {
                  onOpenReportModal();
                  setIsOpen(false);
                }}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '10px 16px',
                  border: 'none',
                  background: 'transparent',
                  textAlign: 'left',
                  fontSize: '0.85rem',
                  color: 'var(--text-primary)',
                  cursor: 'pointer',
                  fontWeight: 600,
                  transition: 'background 0.15s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f0f9ff'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <Brain size={16} color="#0284c7" />
                <div>
                  <div>Preview Brain Report</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Interactive assessment & clinical review</div>
                </div>
              </button>
            )}

            <button
              onClick={handleBackendPdf}
              disabled={isDownloadingPdf}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '10px 16px',
                border: 'none',
                background: 'transparent',
                textAlign: 'left',
                fontSize: '0.85rem',
                color: 'var(--text-primary)',
                cursor: 'pointer',
                fontWeight: 500,
                borderTop: onOpenReportModal ? '1px solid #f1f5f9' : 'none',
                transition: 'background 0.15s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f1f5f9'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
            >
              <Download size={16} color="#0284c7" />
              <div>
                <div>Download PDF (FastAPI)</div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>ReportLab formatted medical PDF</div>
              </div>
            </button>

            <button
              onClick={() => {
                printPdfReport(data);
                setIsOpen(false);
              }}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '10px 16px',
                border: 'none',
                background: 'transparent',
                textAlign: 'left',
                fontSize: '0.85rem',
                color: 'var(--text-primary)',
                cursor: 'pointer',
                fontWeight: 500,
                borderTop: '1px solid #f1f5f9',
                transition: 'background 0.15s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f1f5f9'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
            >
              <Printer size={16} color="#475569" />
              <div>
                <div>Print / Browser PDF</div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Direct print dialog</div>
              </div>
            </button>

            <button
              onClick={() => {
                downloadHtmlReport(data);
                setIsOpen(false);
              }}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '10px 16px',
                border: 'none',
                background: 'transparent',
                textAlign: 'left',
                fontSize: '0.85rem',
                color: 'var(--text-primary)',
                cursor: 'pointer',
                fontWeight: 500,
                borderTop: '1px solid #f1f5f9',
                transition: 'background 0.15s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f1f5f9'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
            >
              <FileText size={16} color="#0284c7" />
              <div>
                <div>Download HTML Report</div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Self-contained research document</div>
              </div>
            </button>

            <button
              onClick={() => {
                downloadJsonReport(data);
                setIsOpen(false);
              }}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '10px 16px',
                border: 'none',
                background: 'transparent',
                textAlign: 'left',
                fontSize: '0.85rem',
                color: 'var(--text-primary)',
                cursor: 'pointer',
                fontWeight: 500,
                borderTop: '1px solid #f1f5f9',
                transition: 'background 0.15s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f1f5f9'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
            >
              <FileCode size={16} color="#059669" />
              <div>
                <div>Export Raw JSON Data</div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Probabilities & volume metadata</div>
              </div>
            </button>
          </div>
        </>
      )}
    </div>
  );
}
