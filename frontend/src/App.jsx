import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import DashboardTelemetry from './components/DashboardTelemetry';
import LiveCameraMonitoring from './components/LiveCameraMonitoring';
import RecordedVideoAnalysis from './components/RecordedVideoAnalysis';
import ModelEvaluationView from './components/ModelEvaluationView';
import ThresholdSettingsModal from './components/ThresholdSettingsModal';
import { api } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [health, setHealth] = useState(null);
  const [config, setConfig] = useState(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  useEffect(() => {
    fetchInitialData();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchInitialData = async () => {
    checkHealth();
    try {
      const cfg = await api.getThresholds();
      setConfig(cfg);
    } catch (err) {
      console.warn("Could not fetch initial config:", err);
    }
  };

  const checkHealth = async () => {
    try {
      const h = await api.getHealth();
      setHealth(h);
    } catch (err) {
      setHealth({ status: 'down', message: err.message });
    }
  };

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col font-sans">
      {/* Background industrial grid overlay */}
      <div 
        className="fixed inset-0 pointer-events-none opacity-[0.03] z-0"
        style={{
          backgroundImage: 'radial-gradient(circle at 1px 1px, #06b6d4 1px, transparent 0)',
          backgroundSize: '24px 24px'
        }}
      />

      {/* Main Header */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        health={health}
        config={config}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 z-10">
        {activeTab === 'dashboard' && (
          <DashboardTelemetry 
            config={config} 
            onOpenSettings={() => setIsSettingsOpen(true)}
          />
        )}

        {activeTab === 'mode_a' && (
          <LiveCameraMonitoring 
            config={config} 
            onReadingSaved={() => {}}
          />
        )}

        {activeTab === 'mode_b' && (
          <RecordedVideoAnalysis 
            config={config} 
          />
        )}

        {activeTab === 'dl_benchmark' && (
          <ModelEvaluationView />
        )}
      </main>

      {/* Settings Modal */}
      <ThresholdSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        config={config}
        onConfigSaved={(updated) => setConfig(updated)}
      />

      {/* Industrial SCADA Footer */}
      <footer className="border-t border-slate-900 bg-[#060a12] py-4 text-center text-xs font-mono text-slate-500 z-10">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>ApexMeter AI • Industrial Instrument Display Parameter Recognition System</span>
          <div className="flex items-center space-x-3">
            <span>PyTorch 2.14+</span>
            <span>•</span>
            <span>OpenCV 5.0+</span>
            <span>•</span>
            <span>FastAPI</span>
            <span>•</span>
            <span>React + Vite</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
