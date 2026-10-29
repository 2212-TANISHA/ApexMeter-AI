import React, { useState } from 'react';
import { X, Sliders, ShieldCheck, Cpu, AlertTriangle, AlertOctagon } from 'lucide-react';
import { api } from '../services/api';

export default function ThresholdSettingsModal({ isOpen, onClose, config, onConfigSaved }) {
  if (!isOpen) return null;

  const [formData, setFormData] = useState({
    machine_id: config?.machine_id || 'BOILER-TURBINE-01',
    parameter_name: config?.parameter_name || 'Steam Pressure',
    unit: config?.unit || 'PSI',
    min_critical: config?.min_critical ?? 5.0,
    min_warning: config?.min_warning ?? 15.0,
    max_warning: config?.max_warning ?? 75.0,
    max_critical: config?.max_critical ?? 90.0,
    active_model: config?.active_model || 'pytorch_cnn',
    confidence_threshold: config?.confidence_threshold ?? 0.65,
    sampling_interval_ms: config?.sampling_interval_ms ?? 1000
  });

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const updated = await api.updateThresholds(formData);
      onConfigSaved(updated);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to update configuration');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[#0b1320] border border-slate-800 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-[#101a2d]">
          <div className="flex items-center space-x-2">
            <Sliders className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-white font-mono uppercase">
              Industrial Monitoring Thresholds & Parameters
            </h3>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-rose-950/80 border border-rose-800 text-rose-300 text-xs font-mono">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3 text-xs font-mono">
            <div>
              <label className="block text-slate-400 mb-1">Machine Tag / ID</label>
              <input
                type="text"
                value={formData.machine_id}
                onChange={e => setFormData({ ...formData, machine_id: e.target.value })}
                className="w-full bg-[#101a2d] border border-slate-800 rounded px-2.5 py-1.5 text-slate-100 outline-none focus:border-cyan-500"
                required
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Parameter Name</label>
              <input
                type="text"
                value={formData.parameter_name}
                onChange={e => setFormData({ ...formData, parameter_name: e.target.value })}
                className="w-full bg-[#101a2d] border border-slate-800 rounded px-2.5 py-1.5 text-slate-100 outline-none focus:border-cyan-500"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs font-mono">
            <div>
              <label className="block text-slate-400 mb-1">Measurement Unit</label>
              <select
                value={formData.unit}
                onChange={e => setFormData({ ...formData, unit: e.target.value })}
                className="w-full bg-[#101a2d] border border-slate-800 rounded px-2.5 py-1.5 text-slate-100 outline-none focus:border-cyan-500"
              >
                <option value="PSI">PSI (Pounds per sq in)</option>
                <option value="bar">bar (Pressure)</option>
                <option value="°C">°C (Temperature)</option>
                <option value="°F">°F (Temperature)</option>
                <option value="RPM">RPM (Rotational Speed)</option>
                <option value="kW">kW (Power)</option>
                <option value="V">V (Voltage)</option>
                <option value="mA">mA (Current)</option>
                <option value="Hz">Hz (Frequency)</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Active Recognition Model</label>
              <select
                value={formData.active_model}
                onChange={e => setFormData({ ...formData, active_model: e.target.value })}
                className="w-full bg-[#101a2d] border border-slate-800 rounded px-2.5 py-1.5 text-slate-100 outline-none focus:border-cyan-500"
              >
                <option value="pytorch_cnn">PyTorch CNN (Recommended)</option>
                <option value="baseline_ocr">Conventional OCR Baseline</option>
              </select>
            </div>
          </div>

          {/* Thresholds Section */}
          <div className="pt-2 border-t border-slate-800 space-y-3">
            <span className="text-xs font-mono font-bold text-slate-300 block uppercase">
              Operational Safety Threshold Bands ({formData.unit})
            </span>

            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-2.5 bg-rose-950/20 border border-rose-900/60 rounded-lg">
                <label className="block text-rose-300 mb-1 flex items-center space-x-1">
                  <AlertOctagon className="w-3.5 h-3.5" />
                  <span>Lower Critical</span>
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.min_critical}
                  onChange={e => setFormData({ ...formData, min_critical: parseFloat(e.target.value) })}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-100 outline-none focus:border-rose-500"
                />
              </div>

              <div className="p-2.5 bg-amber-950/20 border border-amber-900/60 rounded-lg">
                <label className="block text-amber-300 mb-1 flex items-center space-x-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>Lower Warning</span>
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.min_warning}
                  onChange={e => setFormData({ ...formData, min_warning: parseFloat(e.target.value) })}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-100 outline-none focus:border-amber-500"
                />
              </div>

              <div className="p-2.5 bg-amber-950/20 border border-amber-900/60 rounded-lg">
                <label className="block text-amber-300 mb-1 flex items-center space-x-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>Upper Warning</span>
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.max_warning}
                  onChange={e => setFormData({ ...formData, max_warning: parseFloat(e.target.value) })}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-100 outline-none focus:border-amber-500"
                />
              </div>

              <div className="p-2.5 bg-rose-950/20 border border-rose-900/60 rounded-lg">
                <label className="block text-rose-300 mb-1 flex items-center space-x-1">
                  <AlertOctagon className="w-3.5 h-3.5" />
                  <span>Upper Critical</span>
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.max_critical}
                  onChange={e => setFormData({ ...formData, max_critical: parseFloat(e.target.value) })}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-100 outline-none focus:border-rose-500"
                />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs font-mono pt-2 border-t border-slate-800">
            <div>
              <label className="block text-slate-400 mb-1">
                Confidence Threshold: {Math.round(formData.confidence_threshold * 100)}%
              </label>
              <input
                type="range"
                min="0.4"
                max="0.9"
                step="0.05"
                value={formData.confidence_threshold}
                onChange={e => setFormData({ ...formData, confidence_threshold: parseFloat(e.target.value) })}
                className="w-full accent-cyan-400"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Sampling Interval (ms)</label>
              <input
                type="number"
                step="250"
                min="250"
                max="5000"
                value={formData.sampling_interval_ms}
                onChange={e => setFormData({ ...formData, sampling_interval_ms: parseInt(e.target.value) })}
                className="w-full bg-[#101a2d] border border-slate-800 rounded px-2.5 py-1 text-slate-100 outline-none focus:border-cyan-500"
              />
            </div>
          </div>

          {/* Footer buttons */}
          <div className="pt-4 border-t border-slate-800 flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-lg shadow-cyan-600/20 transition flex items-center space-x-1.5"
            >
              <span>{saving ? 'Saving...' : 'Save Configuration'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
