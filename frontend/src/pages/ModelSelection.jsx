// ============================================================
// ALZHEIMER MRI STAGING - MODEL SELECTION PAGE
// ============================================================

import React, { useState, useEffect } from 'react';
import { 
  BrainCircuit, 
  Smartphone, 
  Cpu, 
  Layers, 
  Check, 
  CheckCircle2, 
  AlertCircle, 
  ArrowRight, 
  ArrowLeft, 
  Sparkles,
  Zap,
  ShieldCheck,
  Activity
} from 'lucide-react';
import DisclaimerBanner from '../components/DisclaimerBanner';
import { getAvailableModels } from '../services/api';

export default function ModelSelection({ 
  selectedModel, 
  onSelectModel, 
  onConfirmSelection, 
  onNavigate,
  serverStatus 
}) {
  const [models, setModels] = useState([]);
  const [currentChoice, setCurrentChoice] = useState(selectedModel || 'mobilenet_v3');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchModels() {
      try {
        setLoading(true);
        const data = await getAvailableModels();
        setModels(data);
      } catch (err) {
        console.error('Failed to load models list:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchModels();
  }, []);

  const handleCardClick = (modelId) => {
    setCurrentChoice(modelId);
  };

  const handleConfirm = () => {
    onSelectModel(currentChoice);
    if (onConfirmSelection) {
      onConfirmSelection(currentChoice);
    } else if (onNavigate) {
      onNavigate('analysis');
    }
  };

  // Find model details from backend or fallbacks
  const mobilenetInfo = models.find(m => m.id === 'mobilenet') || {
    id: 'mobilenet',
    name: 'MobileNet',
    display_name: 'MobileNet',
    description: 'Lightweight convolutional neural network designed for efficient image classification.',
    architecture_details: 'MobileNet-V2 inverted residual blocks with linear bottlenecks',
    input_resolution: '224 × 224 × 3',
    badges: ['Lightweight', 'Fast', 'Efficient'],
    checkpoint_available: false,
    status: 'CHECKPOINT NOT AVAILABLE',
    accuracy_display: 'Evaluation pending'
  };

  const mobilenetV3Info = models.find(m => m.id === 'mobilenet_v3') || {
    id: 'mobilenet_v3',
    name: 'MobileNetV3-Large',
    display_name: 'MobileNetV3-Large',
    description: 'Lightweight modern CNN architecture optimized for efficient feature extraction and image classification.',
    architecture_details: 'MobileNetV3-Large with Hard-Swish and Squeeze-and-Excitation attention',
    input_resolution: '224 × 224 × 3',
    badges: ['Lightweight', 'Advanced', 'Efficient'],
    checkpoint_available: true,
    status: 'READY',
    accuracy_display: 'Evaluation pending'
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px', maxWidth: '1080px', margin: '0 auto', width: '100%' }}>
      <DisclaimerBanner />

      {/* Header Banner */}
      <div style={{ textAlign: 'center', padding: '16px 0 8px' }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          background: '#e0f2fe',
          border: '1px solid #bae6fd',
          padding: '6px 16px',
          borderRadius: '24px',
          fontSize: '0.8rem',
          fontWeight: 600,
          color: '#0369a1',
          marginBottom: '14px',
          textTransform: 'uppercase',
          letterSpacing: '0.04em'
        }}>
          <BrainCircuit size={16} color="#0284c7" />
          <span>NEUROSTAGE AI • Model Selection</span>
        </div>

        <h1 style={{ 
          fontSize: '2.1rem', 
          fontWeight: 800, 
          color: 'var(--text-primary)', 
          letterSpacing: '-0.025em',
          marginBottom: '8px'
        }}>
          Select AI Model
        </h1>

        <p style={{ 
          fontSize: '1rem', 
          color: 'var(--text-secondary)', 
          maxWidth: '640px', 
          margin: '0 auto',
          lineHeight: 1.5
        }}>
          Choose the deep learning model for Alzheimer’s MRI analysis. Both architectures provide lightweight patient-level staging.
        </p>
      </div>

      {/* Two Model Cards Side-by-Side */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
        gap: '24px',
        alignItems: 'stretch'
      }}>
        {/* CARD 1: MobileNet */}
        <div 
          onClick={() => handleCardClick('mobilenet')}
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '16px',
            border: currentChoice === 'mobilenet' ? '2.5px solid #0284c7' : '1px solid #e2e8f0',
            boxShadow: currentChoice === 'mobilenet' 
              ? '0 12px 28px -6px rgba(2, 132, 199, 0.25), 0 0 0 1px #0284c7' 
              : '0 4px 12px rgba(0, 0, 0, 0.04)',
            padding: '32px 28px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            cursor: 'pointer',
            transition: 'all 0.25s ease',
            position: 'relative',
            background: currentChoice === 'mobilenet' 
              ? 'linear-gradient(180deg, #f0f9ff 0%, #ffffff 40%)' 
              : '#ffffff'
          }}
        >
          {/* Selected Floating Badge */}
          {currentChoice === 'mobilenet' && (
            <div style={{
              position: 'absolute',
              top: '-12px',
              right: '24px',
              backgroundColor: '#0284c7',
              color: '#ffffff',
              padding: '4px 14px',
              borderRadius: '20px',
              fontSize: '0.74rem',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              boxShadow: '0 4px 10px rgba(2, 132, 199, 0.35)',
              textTransform: 'uppercase',
              letterSpacing: '0.04em'
            }}>
              <Check size={13} strokeWidth={3} />
              <span>Selected</span>
            </div>
          )}

          <div>
            {/* Top Icon Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
              <div style={{
                width: '58px',
                height: '58px',
                borderRadius: '14px',
                backgroundColor: currentChoice === 'mobilenet' ? '#0284c7' : '#e0f2fe',
                color: currentChoice === 'mobilenet' ? '#ffffff' : '#0284c7',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s ease',
                boxShadow: currentChoice === 'mobilenet' ? '0 6px 14px rgba(2, 132, 199, 0.3)' : 'none'
              }}>
                <Smartphone size={28} />
              </div>

              {/* Status Badge */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '5px 12px',
                borderRadius: '20px',
                fontSize: '0.74rem',
                fontWeight: 600,
                backgroundColor: mobilenetInfo.checkpoint_available ? '#ecfdf5' : '#fffbeb',
                color: mobilenetInfo.checkpoint_available ? '#047857' : '#b45309',
                border: `1px solid ${mobilenetInfo.checkpoint_available ? '#a7f3d0' : '#fde68a'}`
              }}>
                <span style={{
                  width: '7px',
                  height: '7px',
                  borderRadius: '50%',
                  backgroundColor: mobilenetInfo.checkpoint_available ? '#059669' : '#d97706'
                }} />
                <span>{mobilenetInfo.checkpoint_available ? 'READY' : 'CHECKPOINT NOT AVAILABLE'}</span>
              </div>
            </div>

            {/* Model Name & Description */}
            <h2 style={{ 
              fontSize: '1.5rem', 
              fontWeight: 800, 
              color: 'var(--text-primary)',
              letterSpacing: '-0.02em',
              marginBottom: '8px'
            }}>
              {mobilenetInfo.display_name || 'MobileNetV2'}
            </h2>

            <p style={{ 
              fontSize: '0.88rem', 
              color: 'var(--text-secondary)', 
              lineHeight: 1.55,
              marginBottom: '20px'
            }}>
              {mobilenetInfo.description || 'Lightweight convolutional neural network designed for efficient image classification.'}
            </p>

            {/* Badges */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '24px' }}>
              <span style={{
                backgroundColor: '#f1f5f9',
                color: '#334155',
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '0.74rem',
                fontWeight: 600,
                border: '1px solid #e2e8f0'
              }}>
                Lightweight
              </span>
              <span style={{
                backgroundColor: '#f1f5f9',
                color: '#334155',
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '0.74rem',
                fontWeight: 600,
                border: '1px solid #e2e8f0'
              }}>
                Fast
              </span>
              <span style={{
                backgroundColor: '#f1f5f9',
                color: '#334155',
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '0.74rem',
                fontWeight: 600,
                border: '1px solid #e2e8f0'
              }}>
                Efficient
              </span>
            </div>

            {/* Architecture Details Grid */}
            <div style={{
              backgroundColor: currentChoice === 'mobilenet' ? '#ffffff' : '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '10px',
              padding: '14px 16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
              fontSize: '0.8rem',
              marginBottom: '24px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Architecture:</span>
                <strong style={{ color: 'var(--text-primary)' }}>MobileNet-V2 Inverted Residuals</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Input Resolution:</span>
                <strong style={{ color: 'var(--text-primary)' }}>224 × 224 × 3</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Target Classes:</span>
                <strong style={{ color: 'var(--text-primary)' }}>4 Classes (CN, VMCI, MCI, Moderate)</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Accuracy:</span>
                <strong style={{ color: mobilenetInfo.accuracy_display && mobilenetInfo.accuracy_display !== 'Evaluation pending' ? '#047857' : '#b45309' }}>
                  {mobilenetInfo.accuracy_display || 'Evaluation pending'}
                </strong>
              </div>
            </div>

            {/* Warning if checkpoint not yet available */}
            {!mobilenetInfo.checkpoint_available && (
              <div style={{
                backgroundColor: '#fffbeb',
                border: '1px solid #fde68a',
                borderRadius: '8px',
                padding: '10px 14px',
                fontSize: '0.76rem',
                color: '#92400e',
                lineHeight: 1.4,
                marginBottom: '20px',
                display: 'flex',
                gap: '8px',
                alignItems: 'center'
              }}>
                <AlertCircle size={16} className="flex-shrink-0" />
                <span>Model selected, but trained checkpoint is not available yet.</span>
              </div>
            )}
          </div>

          {/* Select Button */}
          <button
            type="button"
            className={currentChoice === 'mobilenet' ? 'btn btn-primary' : 'btn btn-outline'}
            style={{
              width: '100%',
              padding: '11px',
              fontSize: '0.9rem',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}
            onClick={(e) => {
              e.stopPropagation();
              handleCardClick('mobilenet');
            }}
          >
            {currentChoice === 'mobilenet' ? (
              <>
                <CheckCircle2 size={17} />
                <span>Selected</span>
              </>
            ) : (
              <span>Select MobileNet</span>
            )}
          </button>
        </div>

        {/* CARD 2: MobileNetV3-Large */}
        <div 
          onClick={() => handleCardClick('mobilenet_v3')}
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '16px',
            border: currentChoice === 'mobilenet_v3' ? '2.5px solid #059669' : '1px solid #e2e8f0',
            boxShadow: currentChoice === 'mobilenet_v3' 
              ? '0 12px 28px -6px rgba(5, 150, 105, 0.25), 0 0 0 1px #059669' 
              : '0 4px 12px rgba(0, 0, 0, 0.04)',
            padding: '32px 28px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            cursor: 'pointer',
            transition: 'all 0.25s ease',
            position: 'relative',
            background: currentChoice === 'mobilenet_v3' 
              ? 'linear-gradient(180deg, #ecfdf5 0%, #ffffff 40%)' 
              : '#ffffff'
          }}
        >
          {/* Selected Floating Badge */}
          {currentChoice === 'mobilenet_v3' && (
            <div style={{
              position: 'absolute',
              top: '-12px',
              right: '24px',
              backgroundColor: '#059669',
              color: '#ffffff',
              padding: '4px 14px',
              borderRadius: '20px',
              fontSize: '0.74rem',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              boxShadow: '0 4px 10px rgba(5, 150, 105, 0.35)',
              textTransform: 'uppercase',
              letterSpacing: '0.04em'
            }}>
              <Check size={13} strokeWidth={3} />
              <span>Selected (Active Checkpoint)</span>
            </div>
          )}

          <div>
            {/* Top Icon Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
              <div style={{
                width: '58px',
                height: '58px',
                borderRadius: '14px',
                backgroundColor: currentChoice === 'mobilenet_v3' ? '#059669' : '#ecfdf5',
                color: currentChoice === 'mobilenet_v3' ? '#ffffff' : '#059669',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s ease',
                boxShadow: currentChoice === 'mobilenet_v3' ? '0 6px 14px rgba(5, 150, 105, 0.3)' : 'none'
              }}>
                <BrainCircuit size={28} />
              </div>

              {/* Status Badge */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '5px 12px',
                borderRadius: '20px',
                fontSize: '0.74rem',
                fontWeight: 600,
                backgroundColor: '#ecfdf5',
                color: '#047857',
                border: '1px solid #a7f3d0'
              }}>
                <span style={{
                  width: '7px',
                  height: '7px',
                  borderRadius: '50%',
                  backgroundColor: '#059669'
                }} />
                <span>READY</span>
              </div>
            </div>

            {/* Model Name & Description */}
            <h2 style={{ 
              fontSize: '1.5rem', 
              fontWeight: 800, 
              color: 'var(--text-primary)',
              letterSpacing: '-0.02em',
              marginBottom: '8px'
            }}>
              MobileNetV3-Large
            </h2>

            <p style={{ 
              fontSize: '0.88rem', 
              color: 'var(--text-secondary)', 
              lineHeight: 1.55,
              marginBottom: '20px'
            }}>
              Lightweight modern CNN architecture optimized for efficient feature extraction and image classification.
            </p>

            {/* Badges */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '24px' }}>
              <span style={{
                backgroundColor: '#f1f5f9',
                color: '#334155',
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '0.74rem',
                fontWeight: 600,
                border: '1px solid #e2e8f0'
              }}>
                Lightweight
              </span>
              <span style={{
                backgroundColor: '#f1f5f9',
                color: '#334155',
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '0.74rem',
                fontWeight: 600,
                border: '1px solid #e2e8f0'
              }}>
                Advanced
              </span>
              <span style={{
                backgroundColor: '#f1f5f9',
                color: '#334155',
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '0.74rem',
                fontWeight: 600,
                border: '1px solid #e2e8f0'
              }}>
                Efficient
              </span>
            </div>

            {/* Architecture Details Grid */}
            <div style={{
              backgroundColor: currentChoice === 'mobilenet_v3' ? '#ffffff' : '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '10px',
              padding: '14px 16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
              fontSize: '0.8rem',
              marginBottom: '24px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Architecture:</span>
                <strong style={{ color: 'var(--text-primary)' }}>Hard-Swish + Squeeze & Excitation</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Input Resolution:</span>
                <strong style={{ color: 'var(--text-primary)' }}>224 × 224 × 3</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Target Classes:</span>
                <strong style={{ color: 'var(--text-primary)' }}>4 Classes (CN, VMCI, MCI, Moderate)</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Accuracy:</span>
                <strong style={{ color: mobilenetV3Info.accuracy_display && mobilenetV3Info.accuracy_display !== 'Evaluation pending' ? '#047857' : '#b45309' }}>
                  {mobilenetV3Info.accuracy_display || 'Evaluation pending'}
                </strong>
              </div>
            </div>

            {/* Checkpoint verified notice */}
            <div style={{
              backgroundColor: '#ecfdf5',
              border: '1px solid #a7f3d0',
              borderRadius: '8px',
              padding: '10px 14px',
              fontSize: '0.76rem',
              color: '#065f46',
              lineHeight: 1.4,
              marginBottom: '20px',
              display: 'flex',
              gap: '8px',
              alignItems: 'center'
            }}>
              <ShieldCheck size={16} color="#059669" className="flex-shrink-0" />
              <span>Trained checkpoint loaded and active in memory cache.</span>
            </div>
          </div>

          {/* Select Button */}
          <button
            type="button"
            className={currentChoice === 'mobilenet_v3' ? 'btn btn-primary' : 'btn btn-outline'}
            style={{
              width: '100%',
              padding: '11px',
              fontSize: '0.9rem',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              backgroundColor: currentChoice === 'mobilenet_v3' ? '#059669' : undefined,
              borderColor: currentChoice === 'mobilenet_v3' ? '#059669' : undefined
            }}
            onClick={(e) => {
              e.stopPropagation();
              handleCardClick('mobilenet_v3');
            }}
          >
            {currentChoice === 'mobilenet_v3' ? (
              <>
                <CheckCircle2 size={17} />
                <span>Selected</span>
              </>
            ) : (
              <span>Select MobileNetV3-Large</span>
            )}
          </button>
        </div>
      </div>

      {/* Action Footer Buttons */}
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        gap: '16px',
        padding: '20px 0',
        borderTop: '1px solid #e2e8f0',
        flexWrap: 'wrap'
      }}>
        <button
          className="btn btn-outline"
          onClick={() => onNavigate && onNavigate('analysis')}
          style={{
            padding: '12px 24px',
            fontSize: '0.92rem',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <ArrowLeft size={16} />
          <span>Back to Analysis</span>
        </button>

        <button
          className="btn btn-primary"
          onClick={handleConfirm}
          style={{
            padding: '12px 32px',
            fontSize: '0.95rem',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            boxShadow: '0 4px 14px rgba(2, 132, 199, 0.3)'
          }}
          id="confirm-model-selection-btn"
        >
          <Check size={18} strokeWidth={2.5} />
          <span>Confirm Selection</span>
          <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
}
