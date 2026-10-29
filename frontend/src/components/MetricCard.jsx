import React from 'react';

export default function MetricCard({ title, value, subtitle, icon: Icon, color = '#0284c7' }) {
  return (
    <div className="card" style={{ display: 'flex', alignItems: 'flex-start', gap: '14px', padding: '18px' }}>
      {Icon && (
        <div style={{
          width: '42px',
          height: '42px',
          borderRadius: '10px',
          backgroundColor: '#f0f9ff',
          border: '1px solid #bae6fd',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0
        }}>
          <Icon size={20} color={color} />
        </div>
      )}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.03em' }}>
          {title}
        </div>
        <div style={{ fontSize: '1.45rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px', letterSpacing: '-0.01em' }}>
          {value}
        </div>
        {subtitle && (
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            {subtitle}
          </div>
        )}
      </div>
    </div>
  );
}
