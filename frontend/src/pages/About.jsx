import React from 'react';
import { BookOpen, GraduationCap, ShieldCheck, Target, Brain, Award } from 'lucide-react';
import DisclaimerBanner from '../components/DisclaimerBanner';

export default function About() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '1000px' }}>
      <DisclaimerBanner />

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
          <GraduationCap size={14} />
          <span>Academic Research Prototype</span>
        </div>

        <h2 style={{ fontSize: '1.65rem', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em', lineHeight: 1.3 }}>
          Uncertainty-Aware Patient-Level Alzheimer’s Disease Staging Using Lightweight Deep Learning and Structural MRI
        </h2>
      </div>

      <div className="card">
        <div className="card-title">
          <Target size={18} color="#0284c7" />
          <span>Project Abstract & Core Objectives</span>
        </div>
        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.65, fontSize: '0.9rem' }}>
          This project implements a complete, rigorous machine learning and web application framework designed to stage Alzheimer's 
          disease progression across four clinical categories: <strong>Cognitively Normal (CDR 0.0)</strong>, <strong>Very Mild Dementia (CDR 0.5)</strong>, 
          <strong>Mild Dementia (CDR 1.0)</strong>, and <strong>Moderate Dementia (CDR 2.0)</strong>. 
          The neural network architecture and web application are 4-class ready, while 4-class model training is ethically halted 
          until real CDR 2.0 patient scans are available, strictly preventing data fabrication.
        </p>
        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.65, fontSize: '0.9rem', marginTop: '10px' }}>
          Unlike common slice-based approaches in literature that inadvertently cause severe data leakage by mixing slices from the 
          same patient between train, validation, and test splits, this project enforces <strong>strict 5-fold patient-wise splitting</strong>, 
          ensuring zero leakage and genuine clinical generalizability.
        </p>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-title">
            <Brain size={18} color="#0284c7" />
            <span>Key Methodological Highlights</span>
          </div>
          <ul style={{ paddingLeft: '20px', color: 'var(--text-secondary)', fontSize: '0.86rem', lineHeight: 1.75 }}>
            <li><strong>Lightweight Deep Learning:</strong> MobileNetV3-Large ensures rapid inference suitable for edge and web deployment without large GPU clusters.</li>
            <li><strong>Patient-Wise Aggregation:</strong> Individual slice predictions are pooled using mean probability aggregation across the axial volume for robust patient staging.</li>
            <li><strong>Uncertainty-Aware Inference:</strong> Monte Carlo Dropout stochastic passes estimate predictive entropy and variance, flagging ambiguous scans.</li>
            <li><strong>Balanced Class Weighting:</strong> Inverse frequency weights computed strictly from patient counts prevent majority class bias.</li>
          </ul>
        </div>

        <div className="card">
          <div className="card-title">
            <Award size={18} color="#0284c7" />
            <span>Academic & Technical Context</span>
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.86rem', lineHeight: 1.65 }}>
            <p><strong>Domain:</strong> Major Project in Computer Science & Medical AI.</p>
            <p style={{ marginTop: '6px' }}><strong>Data Source:</strong> OASIS-1 cross-sectional structural T1-weighted MPRAGE MRI collection.</p>
            <p style={{ marginTop: '6px' }}><strong>Frameworks:</strong> PyTorch, TorchVision, NiBabel, FastAPI, and React Vite.</p>
            <p style={{ marginTop: '6px' }}><strong>Model Checkpoint:</strong> MobileNetV3-Large with Adam optimizer and ReduceLROnPlateau scheduler.</p>
          </div>
        </div>
      </div>

      <div className="card" style={{ backgroundColor: '#fffbeb', borderColor: '#fde68a' }}>
        <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#78350f', marginBottom: '6px' }}>
          Official Medical Disclaimer
        </div>
        <p style={{ fontSize: '0.84rem', color: '#92400e', lineHeight: 1.55 }}>
          This software and neural network system are intended exclusively for academic research, education, and algorithmic demonstration. 
          It has not been evaluated or cleared by the FDA or any medical regulatory authority. Predictions generated by this system do not 
          constitute a clinical diagnosis, prognostic advice, or medical opinion.
        </p>
      </div>
    </div>
  );
}
