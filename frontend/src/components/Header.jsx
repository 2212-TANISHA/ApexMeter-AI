import React from 'react';
import { 
  Activity, 
  Video, 
  Camera, 
  BarChart3, 
  BrainCircuit, 
  Settings, 
  Wifi, 
  WifiOff, 
  Cpu,
  Sparkles
} from 'lucide-react';

export default function Header({ 
  activeTab, 
  setActiveTab, 
  health, 
  config, 
  onOpenSettings,
  onOpenDemoModal
}) {
  const isHealthy = health?.status === 'healthy';

  const navItems = [
    { id: 'dashboard', label: 'Telemetry Dashboard', icon: BarChart3 },
    { id: 'mode_a', label: 'Mode A: Live Camera', icon: Camera },
    { id: 'mode_b', label: 'Mode B: Video Analysis', icon: Video },
    { id: 'dl_benchmark', label: 'DL Model Benchmark', icon: BrainCircuit },
  ];

  return (
    <header className="bg-[#0b1320] border-b border-slate-800/80 sticky top-0 z-40 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Project Title */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 border border-cyan-400/30">
              <Activity className="w-5 h-5 text-white animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="font-display tracking-wider text-sm font-bold text-white uppercase">
                  ApexMeter <span className="text-cyan-400">AI</span>
                </h1>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                  DL CAPSTONE
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Industrial Instrument Parameter Monitoring
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="hidden md:flex space-x-1 bg-[#101a2d] p-1 rounded-lg border border-slate-800">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-cyan-500/20 to-blue-600/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right Status Indicators & Controls */}
          <div className="flex items-center space-x-3">
            {/* Active Model Pill */}
            <div className="hidden lg:flex items-center space-x-1.5 px-2.5 py-1 rounded bg-[#101a2d] border border-slate-800 text-[11px] font-mono text-slate-300">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" />
              <span>Model:</span>
              <span className="font-semibold text-cyan-300">
                {config?.active_model === 'baseline_ocr' ? 'Baseline OCR' : 'PyTorch CNN'}
              </span>
            </div>

            {/* Backend Connection Status */}
            <div 
              className={`flex items-center space-x-1.5 px-2.5 py-1 rounded text-[11px] font-mono border ${
                isHealthy
                  ? 'bg-emerald-950/60 border-emerald-800 text-emerald-400'
                  : 'bg-rose-950/60 border-rose-800 text-rose-400'
              }`}
              title={isHealthy ? `Backend Connected (${health?.torch_version})` : 'Backend Disconnected'}
            >
              {isHealthy ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
              <span className="hidden sm:inline">{isHealthy ? 'ONLINE' : 'OFFLINE'}</span>
            </div>

            {/* Threshold Settings Button */}
            <button
              onClick={onOpenSettings}
              className="p-2 rounded-lg bg-[#101a2d] hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white transition"
              title="Threshold & Alert Settings"
            >
              <Settings className="w-4 h-4 text-slate-400 hover:text-cyan-400" />
            </button>
          </div>
        </div>

        {/* Mobile Navigation bar */}
        <div className="md:hidden flex space-x-1 py-2 overflow-x-auto border-t border-slate-800/50">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-1.5 px-2.5 py-1 rounded text-xs whitespace-nowrap ${
                  isActive
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                    : 'text-slate-400 hover:bg-slate-800/40'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
}
