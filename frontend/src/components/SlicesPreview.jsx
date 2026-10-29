import React from 'react';
import { Layers } from 'lucide-react';

export default function SlicesPreview({ thumbnails = [], totalSlices = 0 }) {
  if (!thumbnails || thumbnails.length === 0) return null;

  return (
    <div style={{ marginTop: '20px' }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '12px'
      }}>
        <div style={{
          fontSize: '0.85rem',
          fontWeight: 600,
          color: 'var(--text-secondary)',
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}>
          <Layers size={16} color="#0284c7" />
          <span>Extracted Axial Slices ({totalSlices} informative slices sampled)</span>
        </div>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          224 × 224 RGB
        </span>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(90px, 1fr))',
        gap: '10px'
      }}>
        {thumbnails.map((src, idx) => (
          <div
            key={idx}
            style={{
              aspectRatio: '1/1',
              borderRadius: '8px',
              overflow: 'hidden',
              border: '1px solid #e2e8f0',
              backgroundColor: '#000000',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
              position: 'relative'
            }}
          >
            <img
              src={src}
              alt={`Extracted slice ${idx + 1}`}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                display: 'block'
              }}
            />
            <span style={{
              position: 'absolute',
              bottom: '4px',
              right: '4px',
              background: 'rgba(0, 0, 0, 0.75)',
              color: '#f8fafc',
              fontSize: '0.65rem',
              padding: '1px 5px',
              borderRadius: '4px',
              fontFamily: 'var(--font-mono)'
            }}>
              #{idx + 1}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
