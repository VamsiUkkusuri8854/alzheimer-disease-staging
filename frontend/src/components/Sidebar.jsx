// ============================================================
// ALZHEIMER MRI STAGING - SIDEBAR COMPONENT
// ============================================================

import React from 'react';
import { 
  LayoutDashboard, 
  BrainCircuit, 
  History, 
  Cpu, 
  BarChart3, 
  Sliders, 
  Layers,
  Database
} from 'lucide-react';

export default function Sidebar({ activeTab, onSelectTab, serverStatus, selectedModel = 'mobilenet_v3' }) {
  const modelDisplayName = selectedModel === 'mobilenet' ? 'MobileNetV2' : 'MobileNetV3-Large';

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'model-selection', label: 'Select AI Model', icon: Sliders },
    { id: 'analysis', label: 'MRI Analysis', icon: BrainCircuit, tag: 'Core', tagColor: 'blue' },
    { id: 'history', label: 'Prediction History', icon: History },
    { id: 'architecture', label: 'Architecture', icon: Cpu },
    { id: 'evaluation', label: 'Model Performance', icon: BarChart3 },
    { id: 'framework', label: 'Four-Class Framework', icon: Layers },
  ];

  const handleNavClick = (id) => {
    onSelectTab(id);
  };

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div className="sidebar-header" style={{ padding: '20px 18px', borderBottom: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '10px',
          backgroundColor: '#e0f2fe',
          border: '1.5px solid #bae6fd',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#0284c7',
          flexShrink: 0
        }}>
          <BrainCircuit size={24} color="#0284c7" />
        </div>
        <div>
          <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em', lineHeight: 1.2 }}>
            NeuroStage AI
          </div>
          <div style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 500, marginTop: '2px' }}>
            Alzheimer's Disease Staging
          </div>
        </div>
      </div>

      {/* Navigation Items */}
      <nav className="sidebar-nav" style={{ padding: '14px 10px', display: 'flex', flexDirection: 'column', gap: '4px', flex: 1 }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id || 
            (item.id === 'architecture' && activeTab === 'model-info') ||
            (item.id === 'framework' && activeTab === 'framework');

          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => handleNavClick(item.id)}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                width: '100%',
                padding: '9px 12px',
                borderRadius: '8px',
                fontSize: '0.84rem',
                fontWeight: isActive ? 600 : 500,
                color: isActive ? '#0284c7' : '#475569',
                backgroundColor: isActive ? '#e0f2fe' : 'transparent',
                border: 'none',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.15s ease'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Icon size={17} color={isActive ? '#0284c7' : '#64748b'} />
                <span>{item.label}</span>
              </div>

              {item.tag && (
                <span style={{
                  fontSize: '0.64rem',
                  fontWeight: 700,
                  backgroundColor: item.tagColor === 'green' ? '#ecfdf5' : '#e0f2fe',
                  color: item.tagColor === 'green' ? '#047857' : '#0284c7',
                  padding: '2px 7px',
                  borderRadius: '10px',
                  border: `1px solid ${item.tagColor === 'green' ? '#a7f3d0' : '#bae6fd'}`,
                  textTransform: 'uppercase',
                  letterSpacing: '0.02em'
                }}>
                  {item.tag}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer OASIS Benchmark Card */}
      <div className="sidebar-footer" style={{ padding: '14px 14px 18px', borderTop: '1px solid #f1f5f9' }}>
        <div style={{
          backgroundColor: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '10px',
          padding: '12px',
          marginBottom: '12px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '7px', fontSize: '0.78rem', fontWeight: 700, color: '#0f172a' }}>
            <Database size={14} color="#0284c7" />
            <span>OASIS Benchmark</span>
          </div>
          <div style={{ fontSize: '0.70rem', color: '#64748b', marginTop: '4px', lineHeight: 1.4 }}>
            76 Subjects • 9,346 Slices
          </div>
          <div style={{ fontSize: '0.68rem', color: '#0284c7', marginTop: '2px', fontWeight: 600 }}>
            4-Class Architecture
          </div>
        </div>

        <div style={{ textAlign: 'center', fontSize: '0.70rem', color: '#94a3b8', lineHeight: 1.4 }}>
          <strong style={{ color: '#64748b', display: 'block' }}>NeuroStage AI</strong>
          <div>Research Prototype v1.0</div>
        </div>
      </div>
    </aside>
  );
}
