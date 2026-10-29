const API_BASE = '/api';

export const api = {
  // Health
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },

  // Telemetry & Stats
  async getDashboardStats() {
    const res = await fetch(`${API_BASE}/readings/stats`);
    if (!res.ok) throw new Error('Failed to fetch dashboard telemetry stats');
    return res.json();
  },

  async getReadings(params = {}) {
    const query = new URLSearchParams(params).toString();
    const res = await fetch(`${API_BASE}/readings?${query}`);
    if (!res.ok) throw new Error('Failed to fetch readings');
    return res.json();
  },

  async getLatestReading() {
    const res = await fetch(`${API_BASE}/readings/latest`);
    if (!res.ok) throw new Error('Failed to fetch latest reading');
    return res.json();
  },

  async clearReadings() {
    const res = await fetch(`${API_BASE}/readings/clear`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to clear readings');
    return res.json();
  },

  getExportCsvUrl(source = '') {
    return `${API_BASE}/readings/export-csv${source ? `?source=${source}` : ''}`;
  },

  // Configuration & Thresholds
  async getThresholds() {
    const res = await fetch(`${API_BASE}/config/thresholds`);
    if (!res.ok) throw new Error('Failed to fetch thresholds');
    return res.json();
  },

  async updateThresholds(config) {
    const res = await fetch(`${API_BASE}/config/thresholds`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to update thresholds');
    }
    return res.json();
  },

  // Live Camera Monitoring (Mode A)
  async processLiveFrame(data) {
    const res = await fetch(`${API_BASE}/monitoring/process-frame`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Frame processing error');
    }
    return res.json();
  },

  async simulateLiveFrame(targetValue = null) {
    const url = targetValue !== null 
      ? `${API_BASE}/monitoring/simulate-frame?target_value=${targetValue}`
      : `${API_BASE}/monitoring/simulate-frame`;
    const res = await fetch(url, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to simulate live frame');
    return res.json();
  },

  // Mode B: Video Analysis
  async uploadVideo(file, sampleIntervalSec = 1.0, roi = null) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('sample_interval_sec', sampleIntervalSec);
    if (roi) {
      formData.append('roi_x', roi.x);
      formData.append('roi_y', roi.y);
      formData.append('roi_w', roi.width);
      formData.append('roi_h', roi.height);
    }
    const res = await fetch(`${API_BASE}/video/upload`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to upload video');
    }
    return res.json();
  },

  async getVideoJobs() {
    const res = await fetch(`${API_BASE}/video/jobs`);
    if (!res.ok) throw new Error('Failed to list video jobs');
    return res.json();
  },

  async getVideoJob(jobId) {
    const res = await fetch(`${API_BASE}/video/jobs/${jobId}`);
    if (!res.ok) throw new Error('Failed to fetch video job');
    return res.json();
  },

  async getVideoJobReadings(jobId) {
    const res = await fetch(`${API_BASE}/video/jobs/${jobId}/readings`);
    if (!res.ok) throw new Error('Failed to fetch video job readings');
    return res.json();
  },

  getVideoJobCsvUrl(jobId) {
    return `${API_BASE}/video/jobs/${jobId}/csv`;
  },

  async generateDemoVideo(duration = 10) {
    const res = await fetch(`${API_BASE}/video/generate-demo?duration_seconds=${duration}`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Failed to generate demo video');
    return res.json();
  },

  // Deep Learning Models & Benchmark
  async getModelsInfo() {
    const res = await fetch(`${API_BASE}/models/info`);
    if (!res.ok) throw new Error('Failed to fetch model info');
    return res.json();
  },

  async getEvaluationReport() {
    const res = await fetch(`${API_BASE}/models/evaluation`);
    if (!res.ok) throw new Error('Failed to fetch evaluation report');
    return res.json();
  },

  async runEvaluation(numSamples = 50) {
    const res = await fetch(`${API_BASE}/models/run-evaluation?num_samples=${numSamples}`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Failed to trigger benchmark evaluation');
    return res.json();
  }
};
