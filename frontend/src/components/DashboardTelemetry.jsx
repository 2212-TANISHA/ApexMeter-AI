import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  TrendingUp, 
  Clock, 
  CheckCircle, 
  AlertTriangle, 
  AlertOctagon, 
  Download, 
  Trash2, 
  Filter, 
  RefreshCw,
  Gauge,
  Sliders,
  Database
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid, 
  ReferenceLine 
} from 'recharts';
import { api } from '../services/api';

export default function DashboardTelemetry({ config, onOpenSettings }) {
  const [stats, setStats] = useState(null);
  const [readings, setReadings] = useState([]);
  const [sourceFilter, setSourceFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 3000);
    return () => clearInterval(interval);
  }, [sourceFilter, statusFilter]);

  const fetchTelemetry = async () => {
    try {
      const statsData = await api.getDashboardStats();
      setStats(statsData);

      const params = { limit: 100 };
      if (sourceFilter) params.source = sourceFilter;
      if (statusFilter) params.status = statusFilter;
      const history = await api.getReadings(params);
      setReadings(history);
    } catch (err) {
      console.error("Telemetry fetch error:", err);
    }
  };

  const handleClearReadings = async () => {
    if (window.confirm("Are you sure you want to clear telemetry readings history?")) {
      try {
        await api.clearReadings();
        fetchTelemetry();
      } catch (err) {
        alert("Failed to clear readings: " + err.message);
      }
    }
  };

  // Prepare chart data (chronological)
  const chartData = [...readings].reverse().map(r => ({
    time: new Date(r.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    value: r.numerical_value,
    confidence: Math.round((r.confidence || 0) * 100),
    status: r.status,
    source: r.source
  })).filter(d => d.value !== null && d.value !== undefined);

  const latestVal = stats?.latest_reading?.numerical_value;
  const unit = config?.unit || stats?.config?.unit || 'PSI';
  const paramName = config?.parameter_name || stats?.config?.parameter_name || 'Pressure';

  return (
    <div className="space-y-6">
      {/* 4 Primary SCADA KPI Telemetry Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Latest Valid Parameter Reading */}
        <div className="bg-[#0b1320] rounded-xl border border-slate-800 p-5 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span className="uppercase tracking-wider">Latest {paramName}</span>
            <Gauge className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="font-display text-4xl font-extrabold text-cyan-400 digital-glow-cyan">
              {latestVal !== undefined && latestVal !== null ? latestVal : '--'}
            </span>
            <span className="font-mono text-lg font-bold text-cyan-300">
              {unit}
            </span>
          </div>
          <div className="mt-2 text-[11px] font-mono text-slate-400 flex items-center justify-between">
            <span>Machine: {config?.machine_id}</span>
            <span className="text-slate-500">
              {stats?.latest_reading ? new Date(stats.latest_reading.timestamp).toLocaleTimeString() : 'No readings'}
            </span>
          </div>
          <div className="absolute -bottom-6 -right-6 w-24 h-24 bg-cyan-500/5 rounded-full blur-xl pointer-events-none" />
        </div>

        {/* Card 2: Total Processed Readings */}
        <div className="bg-[#0b1320] rounded-xl border border-slate-800 p-5 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span className="uppercase tracking-wider">Readings Processed</span>
            <Database className="w-4 h-4 text-blue-400" />
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="font-display text-4xl font-extrabold text-white">
              {stats?.total_readings ?? 0}
            </span>
            <span className="font-mono text-xs text-slate-400">
              samples
            </span>
          </div>
          <div className="mt-2 text-[11px] font-mono text-slate-400 flex items-center justify-between">
            <span>Valid: <strong className="text-emerald-400">{stats?.valid_readings_count ?? 0}</strong></span>
            <span>Recorded in SQLite</span>
          </div>
          <div className="absolute -bottom-6 -right-6 w-24 h-24 bg-blue-500/5 rounded-full blur-xl pointer-events-none" />
        </div>

        {/* Card 3: Recognition Success Rate */}
        <div className="bg-[#0b1320] rounded-xl border border-slate-800 p-5 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span className="uppercase tracking-wider">DL Recognition Rate</span>
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="font-display text-4xl font-extrabold text-emerald-400 digital-glow-green">
              {stats?.success_rate_percent !== undefined ? `${stats.success_rate_percent}%` : '--'}
            </span>
          </div>
          <div className="mt-2 text-[11px] font-mono text-slate-400 flex items-center justify-between">
            <span>Model: {config?.active_model === 'baseline_ocr' ? 'Baseline OCR' : 'PyTorch CNN'}</span>
            <span className="text-emerald-400 font-bold">ACTIVE</span>
          </div>
          <div className="absolute -bottom-6 -right-6 w-24 h-24 bg-emerald-500/5 rounded-full blur-xl pointer-events-none" />
        </div>

        {/* Card 4: Active Threshold Alerts */}
        <div className="bg-[#0b1320] rounded-xl border border-slate-800 p-5 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span className="uppercase tracking-wider">Threshold Alerts</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className={`font-display text-4xl font-extrabold ${
              (stats?.active_alerts_count || 0) > 0 ? 'text-rose-400 digital-glow-red animate-pulse' : 'text-slate-400'
            }`}>
              {stats?.active_alerts_count ?? 0}
            </span>
            <span className="font-mono text-xs text-slate-400">
              triggers
            </span>
          </div>
          <div className="mt-2 text-[11px] font-mono text-slate-400 flex items-center justify-between">
            <span>Status: <strong className={stats?.current_status === 'NORMAL' ? 'text-emerald-400' : 'text-rose-400'}>
              {stats?.current_status || 'NORMAL'}
            </strong></span>
            <button onClick={onOpenSettings} className="text-cyan-400 hover:underline">
              Limits
            </button>
          </div>
          <div className="absolute -bottom-6 -right-6 w-24 h-24 bg-rose-500/5 rounded-full blur-xl pointer-events-none" />
        </div>
      </div>

      {/* Main Telemetry Time-Series Chart */}
      <div className="bg-[#0b1320] rounded-xl border border-slate-800 p-5 space-y-4 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-cyan-400" />
              <span>Real-Time Telemetry Stream — {paramName} ({unit})</span>
            </h3>
            <p className="text-[11px] text-slate-400 font-mono mt-0.5">
              Live continuous time-series with automatic Upper & Lower Warning/Critical bands
            </p>
          </div>

          <div className="flex items-center space-x-4 text-xs font-mono">
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
              <span className="text-slate-300">Measured Value</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-0.5 bg-amber-400" />
              <span className="text-amber-300">Warn ({config?.max_warning})</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-0.5 bg-rose-500" />
              <span className="text-rose-300">Crit ({config?.max_critical})</span>
            </div>
          </div>
        </div>

        <div className="h-72 w-full">
          {chartData.length === 0 ? (
            <div className="h-full flex items-center justify-center text-xs text-slate-500 font-mono">
              No telemetry readings recorded yet. Start camera monitoring in Mode A or upload a video in Mode B.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="telemetryGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
                <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11, fill: '#94a3b8' }} domain={['auto', 'auto']} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0b1320', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                  labelStyle={{ color: '#06b6d4', fontWeight: 'bold' }}
                  formatter={(val) => [`${val} ${unit}`, paramName]}
                />
                {config?.max_critical && (
                  <ReferenceLine y={config.max_critical} stroke="#f43f5e" strokeDasharray="4 4" label={{ value: 'CRITICAL', fill: '#f43f5e', fontSize: 10 }} />
                )}
                {config?.max_warning && (
                  <ReferenceLine y={config.max_warning} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: 'WARNING', fill: '#f59e0b', fontSize: 10 }} />
                )}
                {config?.min_warning && (
                  <ReferenceLine y={config.min_warning} stroke="#f59e0b" strokeDasharray="3 3" />
                )}
                {config?.min_critical && (
                  <ReferenceLine y={config.min_critical} stroke="#f43f5e" strokeDasharray="4 4" />
                )}
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#06b6d4"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#telemetryGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Historical Telemetry Data Table & Filters */}
      <div className="bg-[#0b1320] rounded-xl border border-slate-800 p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <h3 className="text-xs font-mono font-bold uppercase text-slate-300">
              Reading History Log ({readings.length})
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
              SQLite DB
            </span>
          </div>

          {/* Action & Filter Controls */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Filter by Source */}
            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              className="bg-[#101a2d] border border-slate-800 text-slate-300 text-xs rounded px-2.5 py-1.5 outline-none font-mono focus:border-cyan-500"
            >
              <option value="">All Sources</option>
              <option value="camera">Live Camera</option>
              <option value="video">Recorded Video</option>
              <option value="simulated">Simulated</option>
            </select>

            {/* Filter by Status */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-[#101a2d] border border-slate-800 text-slate-300 text-xs rounded px-2.5 py-1.5 outline-none font-mono focus:border-cyan-500"
            >
              <option value="">All Statuses</option>
              <option value="VALID">VALID</option>
              <option value="WARNING">WARNING</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="UNCERTAIN">UNCERTAIN</option>
            </select>

            {/* CSV Export Button */}
            <a
              href={api.getExportCsvUrl(sourceFilter)}
              download
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-[#101a2d] hover:bg-slate-800 text-cyan-300 border border-slate-800 rounded-lg text-xs font-mono transition"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export CSV</span>
            </a>

            {/* Clear Database Button */}
            <button
              onClick={handleClearReadings}
              className="p-1.5 bg-[#101a2d] hover:bg-rose-950/60 text-slate-400 hover:text-rose-400 border border-slate-800 hover:border-rose-800 rounded-lg text-xs transition"
              title="Clear Readings History"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Scrollable Table */}
        <div className="overflow-x-auto max-h-96 overflow-y-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#101a2d] text-slate-400 uppercase text-[10px] sticky top-0">
              <tr>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Source</th>
                <th className="py-2.5 px-3">Raw Display</th>
                <th className="py-2.5 px-3">Numerical Value</th>
                <th className="py-2.5 px-3">Confidence</th>
                <th className="py-2.5 px-3">Model</th>
                <th className="py-2.5 px-3">Latency</th>
                <th className="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {readings.length === 0 ? (
                <tr>
                  <td colSpan="8" className="text-center py-6 text-slate-500">
                    No readings match the current filter.
                  </td>
                </tr>
              ) : (
                readings.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-800/40">
                    <td className="py-2 px-3 text-slate-400 whitespace-nowrap">
                      {new Date(r.timestamp).toLocaleString()}
                    </td>
                    <td className="py-2 px-3">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                        r.source === 'camera' ? 'bg-cyan-950 text-cyan-300 border border-cyan-800' :
                        r.source === 'video' ? 'bg-blue-950 text-blue-300 border border-blue-800' :
                        'bg-purple-950 text-purple-300 border border-purple-800'
                      }`}>
                        {r.source.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-2 px-3 font-display text-cyan-300 font-bold">
                      {r.raw_text || '--'}
                    </td>
                    <td className="py-2 px-3 font-bold text-white">
                      {r.numerical_value !== null ? `${r.numerical_value} ${r.unit}` : 'INVALID'}
                    </td>
                    <td className="py-2 px-3">
                      <span className={r.confidence >= 0.70 ? 'text-emerald-400' : 'text-amber-400'}>
                        {Math.round((r.confidence || 0) * 100)}%
                      </span>
                    </td>
                    <td className="py-2 px-3 text-slate-400 truncate max-w-[120px]">
                      {r.model_used}
                    </td>
                    <td className="py-2 px-3 text-slate-400">
                      {r.inference_time_ms ? `${r.inference_time_ms.toFixed(1)}ms` : '--'}
                    </td>
                    <td className="py-2 px-3">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        r.status === 'VALID' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
                        r.status === 'WARNING' ? 'bg-amber-950 text-amber-300 border border-amber-800' :
                        r.status === 'CRITICAL' ? 'bg-rose-950 text-rose-300 border border-rose-800' :
                        r.status === 'UNCERTAIN' ? 'bg-yellow-950 text-yellow-300 border border-yellow-800' :
                        'bg-slate-800 text-slate-400'
                      }`}>
                        {r.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
