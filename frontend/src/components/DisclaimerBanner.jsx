import React from 'react';
import { AlertTriangle } from 'lucide-react';

export default function DisclaimerBanner({ className = '' }) {
  return (
    <div className={`disclaimer-banner ${className}`}>
      <AlertTriangle size={18} className="flex-shrink-0" style={{ marginTop: '2px', color: '#b45309' }} />
      <div>
        <strong>IMPORTANT MEDICAL RESEARCH DISCLAIMER:</strong>{' '}
        Research prototype only. This prediction is not a medical diagnosis and must not be used for clinical decision-making.
      </div>
    </div>
  );
}
