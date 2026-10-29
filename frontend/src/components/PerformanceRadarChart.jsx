import React, { useState, useRef } from 'react';

export default function PerformanceRadarChart({
  metrics = {
    accuracy: 91.4,
    precision: 90.2,
    recall: 91.1,
    f1: 90.6,
    sensitivity: 91.8,
    specificity: 93.2
  },
  baseline = {
    accuracy: 85.8,
    precision: 84.1,
    recall: 85.0,
    f1: 84.5,
    sensitivity: 86.2,
    specificity: 87.5
  }
}) {
  const axes = [
    { label: 'Accuracy', key: 'accuracy' },
    { label: 'Precision', key: 'precision' },
    { label: 'Recall', key: 'recall' },
    { label: 'F1 Score', key: 'f1' },
    { label: 'Sensitivity', key: 'sensitivity' },
    { label: 'Specificity', key: 'specificity' },
  ];

  const svgRef = useRef(null);
  const [hoveredAxis, setHoveredAxis] = useState(0); // Default to Accuracy (axis 0)
  const [isInteracting, setIsInteracting] = useState(false);
  const [mouseCoord, setMouseCoord] = useState({ x: 160, y: 55 });
  const [isDragging, setIsDragging] = useState(false);

  const size = 340;
  const center = size / 2;
  const radius = 100;
  const totalAxes = axes.length;

  // Grid levels (60%, 70%, 80%, 90%, 100%)
  const gridLevels = [0.6, 0.7, 0.8, 0.9, 1.0];

  const getCoordinates = (index, valuePercent) => {
    // Normalise from 50%..100% to radius
    const minVal = 50;
    const maxVal = 100;
    const norm = Math.max(0, Math.min(1, (valuePercent - minVal) / (maxVal - minVal)));
    const r = norm * radius;
    const angle = (Math.PI * 2 / totalAxes) * index - Math.PI / 2;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle)
    };
  };

  const getLabelCoordinates = (index) => {
    const r = radius + 32;
    const angle = (Math.PI * 2 / totalAxes) * index - Math.PI / 2;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle)
    };
  };

  // Handle pointer / mouse movement anywhere across the SVG figure
  const handlePointerMove = (e) => {
    if (!svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const clientX = e.clientX || (e.touches && e.touches[0]?.clientX) || 0;
    const clientY = e.clientY || (e.touches && e.touches[0]?.clientY) || 0;
    
    const x = ((clientX - rect.left) / rect.width) * size;
    const y = ((clientY - rect.top) / rect.height) * size;

    setMouseCoord({ x, y });
    setIsInteracting(true);

    const dx = x - center;
    const dy = y - center;

    // Angle in radians from top (-PI/2)
    let angle = Math.atan2(dy, dx) + Math.PI / 2;
    if (angle < 0) angle += Math.PI * 2;

    // Closest axis (0 to 5)
    const step = (Math.PI * 2) / totalAxes;
    const nearestIndex = Math.round(angle / step) % totalAxes;
    setHoveredAxis(nearestIndex);
  };

  const handlePointerLeave = () => {
    setIsDragging(false);
    setIsInteracting(false);
  };

  const modelPoints = axes.map((axis, i) => {
    const pt = getCoordinates(i, metrics[axis.key]);
    return `${pt.x},${pt.y}`;
  }).join(' ');

  const baselinePoints = axes.map((axis, i) => {
    const pt = getCoordinates(i, baseline[axis.key]);
    return `${pt.x},${pt.y}`;
  }).join(' ');

  const activeAxis = axes[hoveredAxis];
  const activeModelVal = metrics[activeAxis.key];
  const activeBaseVal = baseline[activeAxis.key];
  const activePt = getCoordinates(hoveredAxis, activeModelVal);
  const activeBasePt = getCoordinates(hoveredAxis, activeBaseVal);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      width: '100%',
      userSelect: 'none'
    }}>
      {/* Dynamic Top Live Status Bar */}
      <div style={{
        width: '100%',
        backgroundColor: '#0f172a',
        borderRadius: '10px',
        padding: '10px 16px',
        marginBottom: '10px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '10px',
        color: '#ffffff',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: '#38bdf8',
            boxShadow: '0 0 8px #38bdf8'
          }} />
          <span style={{ fontSize: '0.9rem', fontWeight: 800, color: '#38bdf8' }}>
            {activeAxis.label}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '0.82rem' }}>
          <div>
            <span style={{ color: '#94a3b8', fontSize: '0.72rem' }}>MobileNetV3: </span>
            <strong style={{ color: '#ffffff', fontSize: '1rem' }}>{activeModelVal}%</strong>
          </div>
          <div>
            <span style={{ color: '#94a3b8', fontSize: '0.72rem' }}>ResNet-18: </span>
            <strong style={{ color: '#cbd5e1' }}>{activeBaseVal}%</strong>
          </div>
          <div style={{
            backgroundColor: '#047857',
            color: '#a7f3d0',
            padding: '2px 8px',
            borderRadius: '12px',
            fontWeight: 800,
            fontSize: '0.74rem'
          }}>
            +{(activeModelVal - activeBaseVal).toFixed(1)}% Gain
          </div>
        </div>
      </div>

      {/* SVG Canvas with Full Drag and Mouse Tracking */}
      <div
        style={{
          position: 'relative',
          width: '100%',
          maxWidth: `${size}px`,
          touchAction: 'none'
        }}
      >
        <svg
          ref={svgRef}
          width="100%"
          height="100%"
          viewBox={`0 0 ${size} ${size}`}
          style={{ overflow: 'visible', cursor: isDragging ? 'grabbing' : 'crosshair' }}
          onMouseMove={handlePointerMove}
          onTouchMove={handlePointerMove}
          onMouseDown={(e) => {
            setIsDragging(true);
            handlePointerMove(e);
          }}
          onTouchStart={(e) => {
            setIsDragging(true);
            handlePointerMove(e);
          }}
          onMouseUp={() => setIsDragging(false)}
          onTouchEnd={() => setIsDragging(false)}
          onMouseLeave={handlePointerLeave}
        >
          {/* Subtle Background Radial Gradient */}
          <defs>
            <radialGradient id="radarGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#0284c7" stopOpacity="0.12" />
              <stop offset="100%" stopColor="#0284c7" stopOpacity="0.0" />
            </radialGradient>
          </defs>

          {/* Concentric Grid Polygons & Percentage Ring Markers */}
          {gridLevels.map((lvl, lvlIdx) => {
            const pts = axes.map((_, i) => {
              const angle = (Math.PI * 2 / totalAxes) * i - Math.PI / 2;
              const norm = (lvl * 100 - 50) / 50;
              const r = norm * radius;
              return `${center + r * Math.cos(angle)},${center + r * Math.sin(angle)}`;
            }).join(' ');

            return (
              <g key={lvlIdx}>
                <polygon
                  points={pts}
                  fill={lvlIdx === gridLevels.length - 1 ? 'url(#radarGlow)' : 'none'}
                  stroke="#e2e8f0"
                  strokeWidth="1"
                />
                <text
                  x={center + 3}
                  y={center - ((lvl * 100 - 50) / 50) * radius + 3}
                  fill="#94a3b8"
                  fontSize="9"
                  fontFamily="inherit"
                  fontWeight="500"
                >
                  {Math.round(lvl * 100)}%
                </text>
              </g>
            );
          })}

          {/* Active Radial Guide Line Following Drag / Mouse Angle */}
          <line
            x1={center}
            y1={center}
            x2={activePt.x}
            y2={activePt.y}
            stroke="#0284c7"
            strokeWidth="2"
            strokeDasharray="2 2"
          />

          {/* Axis Radial Lines */}
          {axes.map((axis, i) => {
            const pt = getCoordinates(i, 100);
            const isCurrent = hoveredAxis === i;

            return (
              <line
                key={`line-${i}`}
                x1={center}
                y1={center}
                x2={pt.x}
                y2={pt.y}
                stroke={isCurrent ? '#0284c7' : '#e2e8f0'}
                strokeWidth={isCurrent ? 2 : 1}
              />
            );
          })}

          {/* ResNet-18 Baseline Polygon (Dashed Gray) */}
          <polygon
            points={baselinePoints}
            fill="none"
            stroke="#94a3b8"
            strokeWidth="1.6"
            strokeDasharray="4 3"
          />

          {/* MobileNetV3 Polygon (Vivid Blue Fill) */}
          <polygon
            points={modelPoints}
            fill="rgba(2, 132, 199, 0.2)"
            stroke="#0284c7"
            strokeWidth="2.8"
          />

          {/* ResNet-18 Data Points */}
          {axes.map((axis, i) => {
            const pt = getCoordinates(i, baseline[axis.key]);
            const isCurrent = hoveredAxis === i;

            return (
              <circle
                key={`base-${i}`}
                cx={pt.x}
                cy={pt.y}
                r={isCurrent ? 4.5 : 2.5}
                fill="#94a3b8"
                stroke="#ffffff"
                strokeWidth="1.2"
              />
            );
          })}

          {/* MobileNetV3 Data Points & Permanent Value Badges */}
          {axes.map((axis, i) => {
            const pt = getCoordinates(i, metrics[axis.key]);
            const lblPt = getLabelCoordinates(i);
            const isCurrent = hoveredAxis === i;
            const val = metrics[axis.key];

            let textAnchor = 'middle';
            if (lblPt.x < center - 20) textAnchor = 'end';
            else if (lblPt.x > center + 20) textAnchor = 'start';

            return (
              <g key={`point-${i}`}>
                {/* Outer Vertex Point */}
                {isCurrent && (
                  <circle
                    cx={pt.x}
                    cy={pt.y}
                    r="9"
                    fill="rgba(2, 132, 199, 0.25)"
                  />
                )}

                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r={isCurrent ? 6 : 4}
                  fill={isCurrent ? '#0284c7' : '#0284c7'}
                  stroke="#ffffff"
                  strokeWidth={isCurrent ? 2.5 : 1.5}
                />

                {/* Permanent Value Tag on Each Vertex */}
                <g transform={`translate(${lblPt.x}, ${lblPt.y})`}>
                  <text
                    x="0"
                    y={i === 0 ? -12 : i === 3 ? 18 : 0}
                    textAnchor={textAnchor}
                    fill={isCurrent ? '#0284c7' : '#0f172a'}
                    fontSize={isCurrent ? '12' : '11'}
                    fontWeight={isCurrent ? '800' : '700'}
                    fontFamily="inherit"
                  >
                    {axis.label}
                  </text>
                  <text
                    x="0"
                    y={i === 0 ? 0 : i === 3 ? 30 : 12}
                    textAnchor={textAnchor}
                    fill={isCurrent ? '#0284c7' : '#64748b'}
                    fontSize={isCurrent ? '11' : '10'}
                    fontWeight="800"
                    fontFamily="inherit"
                  >
                    {val}%
                  </text>
                </g>
              </g>
            );
          })}

          {/* Floating Crosshair Indicator at Mouse Position when Dragging */}
          {isInteracting && (
            <g transform={`translate(${mouseCoord.x}, ${mouseCoord.y})`}>
              <circle
                r="18"
                fill="none"
                stroke="#0284c7"
                strokeWidth="1.5"
                strokeDasharray="3 3"
                opacity="0.75"
              />
              <circle
                r="3"
                fill="#0284c7"
              />
            </g>
          )}
        </svg>
      </div>

      {/* Drag Instruction Banner */}
      <div style={{
        marginTop: '6px',
        fontSize: '0.74rem',
        color: '#64748b',
        display: 'flex',
        alignItems: 'center',
        gap: '6px'
      }}>
        <span>🖱️ <strong>Drag or move mouse across the radar figure</strong> to dynamically inspect metric values.</span>
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', gap: '20px', marginTop: '10px', fontSize: '0.8rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '12px', height: '3px', backgroundColor: '#0284c7', display: 'inline-block', borderRadius: '2px' }} />
          <strong style={{ color: '#0284c7' }}>MobileNetV3 (91.4% Avg)</strong>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '12px', height: '0px', borderTop: '2px dashed #94a3b8', display: 'inline-block' }} />
          <span style={{ color: '#64748b' }}>ResNet-18 Baseline (85.8%)</span>
        </div>
      </div>
    </div>
  );
}
