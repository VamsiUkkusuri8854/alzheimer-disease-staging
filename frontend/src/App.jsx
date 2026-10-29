// ============================================================
// ALZHEIMER MRI STAGING - ROOT APPLICATION
// ============================================================

import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import ModelSelection from './pages/ModelSelection';
import Analysis from './pages/Analysis';
import History from './pages/History';
import ModelInfo from './pages/ModelInfo';
import Evaluation from './pages/Evaluation';
import { checkHealth } from './services/api';

const HISTORY_STORAGE_KEY = 'neurostage_prediction_history';
const SELECTED_MODEL_KEY = 'neurostage_selected_model';
const LAST_RESULT_STORAGE_KEY = 'neurostage_last_analysis_result';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [serverStatus, setServerStatus] = useState(null);
  // Start with null so entering the MRI analysis page always displays a clean upload screen
  const [lastResult, setLastResult] = useState(null);

  // Clean up any previously stored results in localStorage
  useEffect(() => {
    try {
      localStorage.removeItem(LAST_RESULT_STORAGE_KEY);
    } catch (e) {
      // ignore
    }
  }, []);

  const handleUpdateLastResult = (result) => {
    setLastResult(result);
  };

  const handleNavigate = (tabId) => {
    if (tabId === 'analysis') {
      // Entering MRI analysis page fresh: clear old detection so it looks like a clean upload screen
      setLastResult(null);
    }
    setActiveTab(tabId);
  };
  
  // Model selection state with localStorage persistence
  const [selectedModel, setSelectedModel] = useState(() => {
    try {
      const saved = localStorage.getItem(SELECTED_MODEL_KEY);
      return saved || 'mobilenet_v3';
    } catch {
      return 'mobilenet_v3';
    }
  });

  const [history, setHistory] = useState(() => {
    try {
      const saved = localStorage.getItem(HISTORY_STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const pollHealth = async () => {
    const status = await checkHealth();
    setServerStatus(status);
  };

  useEffect(() => {
    pollHealth();
    const interval = setInterval(pollHealth, 10000); // Poll health every 10s
    return () => clearInterval(interval);
  }, []);

  const handleSelectModel = (modelId) => {
    setSelectedModel(modelId);
    try {
      localStorage.setItem(SELECTED_MODEL_KEY, modelId);
    } catch (e) {
      console.warn('Failed to save selected model to localStorage:', e);
    }
  };

  const handleConfirmModelSelection = (modelId) => {
    handleSelectModel(modelId);
    handleNavigate('analysis');
  };

  const handleSaveHistory = (entry) => {
    setHistory((prev) => {
      const updated = [entry, ...prev].slice(0, 50); // Store up to 50 recent records
      try {
        localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(updated));
      } catch (e) {
        console.warn('Failed to save to localStorage:', e);
      }
      return updated;
    });
  };

  const handleClearHistory = () => {
    localStorage.removeItem(HISTORY_STORAGE_KEY);
    setHistory([]);
  };

  return (
    <div className="app-layout">
      <Sidebar
        activeTab={activeTab}
        onSelectTab={handleNavigate}
        serverStatus={serverStatus}
        selectedModel={selectedModel}
      />

      <div className="main-wrapper">
        <Navbar 
          serverStatus={serverStatus} 
          onNavigate={handleNavigate}
          selectedModel={selectedModel}
        />

        <main className="page-container">
          <div style={{ display: activeTab === 'dashboard' ? 'block' : 'none' }}>
            <Dashboard
              serverStatus={serverStatus}
              onNavigate={handleNavigate}
              history={history}
              selectedModel={selectedModel}
            />
          </div>

          <div style={{ display: activeTab === 'model-selection' ? 'block' : 'none' }}>
            <ModelSelection
              selectedModel={selectedModel}
              onSelectModel={handleSelectModel}
              onConfirmSelection={handleConfirmModelSelection}
              onNavigate={setActiveTab}
              serverStatus={serverStatus}
            />
          </div>

          <div style={{ display: activeTab === 'analysis' ? 'block' : 'none' }}>
            <Analysis
              serverStatus={serverStatus}
              onSaveHistory={handleSaveHistory}
              lastResult={lastResult}
              setLastResult={handleUpdateLastResult}
              onNavigate={setActiveTab}
              selectedModel={selectedModel}
            />
          </div>

          <div style={{ display: activeTab === 'history' ? 'block' : 'none' }}>
            <History
              history={history}
              onClearHistory={handleClearHistory}
              onNavigate={setActiveTab}
            />
          </div>

          <div style={{ display: (activeTab === 'architecture' || activeTab === 'model-info') ? 'block' : 'none' }}>
            <ModelInfo 
              serverStatus={serverStatus} 
              onNavigate={setActiveTab}
              selectedModel={selectedModel}
            />
          </div>

          <div style={{ display: (activeTab === 'evaluation' || activeTab === 'framework') ? 'block' : 'none' }}>
            <Evaluation serverStatus={serverStatus} onNavigate={setActiveTab} />
          </div>
        </main>
      </div>
    </div>
  );
}
