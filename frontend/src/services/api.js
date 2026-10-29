// ============================================================
// ALZHEIMER MRI STAGING - API SERVICE CLIENT
// ============================================================

import axios from 'axios';

// Dynamic base URL: automatically connects to backend on current host IP/domain
const getBaseUrl = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  if (typeof window !== 'undefined' && window.location && window.location.hostname) {
    return `http://${window.location.hostname}:8000`;
  }
  return 'http://127.0.0.1:8000';
};

const BASE_URL = getBaseUrl();

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 180000, // 3 minutes timeout for large MRI processing
});

export const checkHealth = async () => {
  try {
    const response = await client.get('/health');
    return response.data;
  } catch (error) {
    return {
      status: 'offline',
      model_loaded: false,
      error: error.response?.data?.detail || error.message || 'Cannot connect to backend server.',
    };
  }
};

export const getAvailableModels = async () => {
  try {
    const response = await client.get('/models');
    return response.data?.models || [];
  } catch (error) {
    console.warn('Failed to fetch available models from backend:', error);
    // Return fallback list matching registry
    return [
      {
        id: 'mobilenet',
        name: 'MobileNet',
        display_name: 'MobileNet',
        description: 'Lightweight convolutional neural network designed for efficient image classification.',
        architecture_details: 'MobileNet-V2 inverted residual blocks with linear bottlenecks',
        input_resolution: '224 × 224 × 3',
        badges: ['Lightweight', 'Fast', 'Efficient'],
        checkpoint_available: false,
        is_loaded: false,
        status: 'CHECKPOINT NOT AVAILABLE',
        status_message: 'Model selected, but trained checkpoint is not available yet.',
        accuracy_display: 'Evaluation pending'
      },
      {
        id: 'mobilenet_v3',
        name: 'MobileNetV3-Large',
        display_name: 'MobileNetV3-Large',
        description: 'Lightweight modern CNN architecture optimized for efficient feature extraction and image classification.',
        architecture_details: 'MobileNetV3-Large with Hard-Swish and Squeeze-and-Excitation attention',
        input_resolution: '224 × 224 × 3',
        badges: ['Lightweight', 'Advanced', 'Efficient'],
        checkpoint_available: true,
        is_loaded: true,
        status: 'READY',
        status_message: '4-Class Alzheimer\'s Disease Staging model loaded and ready.',
        accuracy_display: 'Evaluation pending'
      }
    ];
  }
};

export const getModelInfo = async (modelName) => {
  try {
    const params = modelName ? { model_name: modelName } : {};
    const response = await client.get('/model-info', { params });
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || error.message || 'Failed to retrieve model info.');
  }
};

export const predictMri = async (file, modelName = 'mobilenet_v3', onProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('model_name', modelName);

  try {
    const response = await client.post('/predict', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percentCompleted);
        }
      },
    });
    return response.data;
  } catch (error) {
    const errorMsg = error.response?.data?.detail || error.message || 'MRI analysis failed.';
    throw new Error(errorMsg);
  }
};

export const getSampleMriAnalysis = async () => {
  try {
    const response = await client.get('/sample-mri');
    return response.data;
  } catch (error) {
    console.warn('Backend /sample-mri not reachable, using offline sample:', error);
    return null;
  }
};

export const downloadBackendReportPdf = async (reportData) => {
  try {
    const response = await client.post('/generate-report-pdf', reportData, {
      responseType: 'blob',
    });
    
    const blob = new Blob([response.data], { type: 'application/pdf' });
    const rawFilename = reportData.filename || reportData.scan_filename || 'MRI_Scan';
    const cleanFilename = rawFilename.replace('.nii.gz', '').replace('.nii', '').replace(/\s+/g, '_');
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `AI_Brain_Assessment_Report_${cleanFilename}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
    return true;
  } catch (error) {
    const errorMsg = error.response?.data?.detail || error.message || 'Failed to download PDF report.';
    throw new Error(errorMsg);
  }
};

export const sendChatMessage = async (message, history = [], mriContext = null) => {
  try {
    const response = await client.post('/api/chat', {
      message,
      history,
      mri_context: mriContext,
    });
    return response.data;
  } catch (error) {
    const errorMsg = error.response?.data?.detail || error.message || 'Failed to connect to medical assistant.';
    throw new Error(errorMsg);
  }
};

export default {
  checkHealth,
  getAvailableModels,
  getModelInfo,
  predictMri,
  downloadBackendReportPdf,
  sendChatMessage,
};
