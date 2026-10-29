import React from 'react';

const CLASS_COLORS = {
  'Cognitively Normal': { bar: '#059669', bg: '#ecfdf5', text: '#047857', border: '#a7f3d0' },
  'Very Mild Dementia': { bar: '#d97706', bg: '#fffbeb', text: '#b45309', border: '#fde68a' },
  'Mild Dementia': { bar: '#dc2626', bg: '#fef2f2', text: '#b91c1c', border: '#fecaca' },
  'Moderate Dementia': { bar: '#7c3aed', bg: '#f5f3ff', text: '#6d28d9', border: '#ddd6fe' },
};

export default function ProbabilityBarChart({ probabilities = {}, predictedClass = '' }) {
  const entries = Object.entries(probabilities);

  if (entries.length === 0) {
    return (
      <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', padding: '24px 0' }}>
        No probability distribution available.
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {entries.map(([className, rawProb]) => {
        const percent = Math.round(rawProb * 1000) / 10;
        const isPredicted = className === predictedClass;
        const colorConfig = CLASS_COLORS[className] || { bar: '#0284c7', bg: '#f0f9ff', text: '#0284c7', border: '#bae6fd' };

        return (
          <div key={className} style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{
                fontSize: '0.9rem',
                fontWeight: isPredicted ? 600 : 500,
                color: isPredicted ? 'var(--text-primary)' : 'var(--text-secondary)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <span style={{
                  width: '10px',
                  height: '10px',
                  borderRadius: '3px',
                  backgroundColor: colorConfig.bar
                }} />
                {className}
                {isPredicted && (
                  <span style={{
                    fontSize: '0.68rem',
                    padding: '2px 8px',
                    borderRadius: '10px',
                    backgroundColor: colorConfig.bg,
                    color: colorConfig.text,
                    border: `1px solid ${colorConfig.border}`,
                    fontWeight: 600,
                    textTransform: 'uppercase'
                  }}>
                    Predicted
                  </span>
                )}
              </span>

              <span style={{
                fontSize: '0.92rem',
                fontWeight: isPredicted ? 700 : 500,
                color: isPredicted ? colorConfig.text : 'var(--text-secondary)'
              }}>
                {percent.toFixed(1)}%
              </span>
            </div>

            {/* Visual Bar Track */}
            <div style={{
              height: '8px',
              backgroundColor: '#f1f5f9',
              borderRadius: '4px',
              overflow: 'hidden',
              position: 'relative',
              border: isPredicted ? `1px solid ${colorConfig.border}` : '1px solid #e2e8f0'
            }}>
              <div
                style={{
                  height: '100%',
                  width: `${Math.min(100, Math.max(percent, 0.5))}%`,
                  backgroundColor: colorConfig.bar,
                  borderRadius: '4px',
                  transition: 'width 0.8s cubic-bezier(0.16, 1, 0.3, 1)',
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
