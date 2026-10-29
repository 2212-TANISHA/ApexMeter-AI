import React, { useState, useEffect, useRef } from 'react';
import { 
  Upload, 
  Video, 
  Play, 
  Pause, 
  FileText, 
  Download, 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  Layers, 
  Sparkles,
  BarChart, 
  Filter, 
  ChevronRight,
  TrendingUp,
  AlertTriangle,
  RefreshCw
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid, 
  ReferenceLine 
} from 'recharts';
import { api } from '../services/api';

export default function RecordedVideoAnalysis({ config }) {
  const [file, setFile] = useState(null);
  const [videoPreviewUrl, setVideoPreviewUrl] = useState(null);
  const [sampleIntervalSec, setSampleIntervalSec] = useState(1.0);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  // Video Job Tracking
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [jobReadings, setJobReadings] = useState([]);
  const [loadingJobDetails, setLoadingJobDetails] = useState(false);

  const videoElementRef = useRef(null);
  const pollIntervalRef = useRef(null);

  // Fetch jobs on mount
  useEffect(() => {
    loadJobs();
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  const loadJobs = async () => {
    try {
      const list = await api.getVideoJobs();
      setJobs(list);
      if (list.length > 0 && !selectedJob) {
        selectJob(list[0].id);
      }
    } catch (err) {
      console.error("Failed to load video jobs:", err);
    }
  };

  const selectJob = async (jobId) => {
    try {
      setLoadingJobDetails(true);
      const detail = await api.getVideoJob(jobId);
      setSelectedJob(detail);
      const readings = await api.getVideoJobReadings(jobId);
      setJobReadings(readings);
    } catch (err) {
      console.error("Error selecting video job:", err);
    } finally {
      setLoadingJobDetails(false);
    }
  };

  // Poll active jobs
  useEffect(() => {
    const hasActiveJobs = jobs.some(j => j.status === 'PROCESSING' || j.status === 'QUEUED');
    if (hasActiveJobs) {
      pollIntervalRef.current = setInterval(async () => {
        const updated = await api.getVideoJobs();
        setJobs(updated);
        if (selectedJob) {
          const cur = updated.find(j => j.id === selectedJob.id);
          if (cur) {
            setSelectedJob(cur);
            if (cur.status === 'COMPLETED' && selectedJob.status !== 'COMPLETED') {
              const readings = await api.getVideoJobReadings(cur.id);
              setJobReadings(readings);
            }
          }
        }
      }, 2000);
    } else {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    }
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [jobs, selectedJob]);

  // File selection
  const handleFileChange = (e) => {
    const selected = e.target.files?.[0];
    if (!selected) return;
    setUploadError(null);

    const ext = selected.name.split('.').pop()?.toLowerCase();
    if (!['mp4', 'avi', 'mov', 'mkv'].includes(ext)) {
      setUploadError("Invalid file type. Please upload an MP4 or AVI video.");
      return;
    }
    if (selected.size > 100 * 1024 * 1024) {
      setUploadError("File exceeds 100MB limit.");
      return;
    }

    setFile(selected);
    setVideoPreviewUrl(URL.createObjectURL(selected));
  };

  // Upload video
  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      const job = await api.uploadVideo(file, sampleIntervalSec);
      setJobs(prev => [job, ...prev]);
      setSelectedJob(job);
      setJobReadings([]);
      setFile(null);
      setVideoPreviewUrl(null);
    } catch (err) {
      setUploadError(err.message || "Failed to upload video");
    } finally {
      setUploading(false);
    }
  };

  // Generate demo video
  const handleGenerateDemo = async () => {
    setUploading(true);
    try {
      const demoJob = await api.generateDemoVideo(12);
      setJobs(prev => [demoJob, ...prev]);
      setSelectedJob(demoJob);
      setJobReadings([]);
    } catch (err) {
      setUploadError("Failed to generate demo video: " + err.message);
    } finally {
      setUploading(false);
    }
  };

  // Chart data
  const chartData = jobReadings.map(r => ({
    time: `${r.video_relative_time?.toFixed(1)}s`,
    rawTime: r.video_relative_time,
    value: r.numerical_value,
    confidence: Math.round((r.confidence || 0) * 100),
    status: r.status,
    isInferred: r.is_inferred === 1
  }));

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-[#0b1320] p-4 rounded-xl border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <Video className="w-5 h-5 text-cyan-400" />
              <span>Mode B: Recorded Video Analysis</span>
            </h2>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
              OFFLINE BATCH DL PIPELINE
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Upload MP4/AVI videos of industrial instruments, extract frames at specified intervals, filter duplicate readings, and produce a full time-series summary.
          </p>
        </div>

        {/* 1-Click Demo Video Button */}
        <button
          onClick={handleGenerateDemo}
          disabled={uploading}
          className="flex items-center space-x-2 px-3.5 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-purple-600/20 transition disabled:opacity-50"
        >
          <Sparkles className="w-4 h-4" />
          <span>Generate & Analyze Demo Video</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Video Uploader & Job List (4 cols) */}
        <div className="lg:col-span-4 space-y-5">
          {/* Upload Card */}
          <div className="bg-[#0b1320] rounded-xl border border-slate-800 p-4 space-y-4">
            <h3 className="text-xs font-mono font-bold uppercase text-slate-300 flex items-center space-x-2">
              <Upload className="w-4 h-4 text-cyan-400" />
              <span>Upload Video for Analysis</span>
            </h3>

            {/* Dropzone */}
            <div className="border-2 border-dashed border-slate-700 hover:border-cyan-500 rounded-lg p-5 text-center transition cursor-pointer relative bg-[#101a2d]">
              <input
                type="file"
                accept=".mp4,.avi,.mov,.mkv"
                onChange={handleFileChange}
                className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
              />
              <Video className="w-8 h-8 text-slate-400 mx-auto mb-2" />
              <p className="text-xs font-medium text-slate-200">
                {file ? file.name : 'Click or drag MP4 / AVI video here'}
              </p>
              <p className="text-[10px] text-slate-500 mt-1 font-mono">
                Max 100MB • MP4, AVI, MOV
              </p>
            </div>

            {/* Video Preview if selected */}
            {videoPreviewUrl && (
              <div className="rounded-lg overflow-hidden border border-slate-800 aspect-video bg-black">
                <video 
                  src={videoPreviewUrl} 
                  controls 
                  className="w-full h-full object-contain"
                />
              </div>
            )}

            {/* Upload Error */}
            {uploadError && (
              <div className="p-2.5 rounded bg-rose-950/80 border border-rose-800 text-rose-300 text-xs font-mono">
                {uploadError}
              </div>
            )}

            {/* Sampling Rate Configuration */}
            <div className="flex items-center justify-between text-xs font-mono bg-[#101a2d] p-2.5 rounded-lg border border-slate-800">
              <span className="text-slate-400">Frame Sampling:</span>
              <select
                value={sampleIntervalSec}
                onChange={(e) => setSampleIntervalSec(Number(e.target.value))}
                className="bg-slate-900 border border-slate-700 text-slate-200 rounded px-2 py-1 outline-none focus:border-cyan-500 text-xs"
              >
                <option value={0.5}>Every 0.5s (High density)</option>
                <option value={1.0}>Every 1.0s (Standard)</option>
                <option value={2.0}>Every 2.0s (Fast)</option>
              </select>
            </div>

            {/* Upload Button */}
            <button
              onClick={handleUpload}
              disabled={!file || uploading}
              className="w-full py-2.5 bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-800 disabled:text-slate-600 text-white text-xs font-semibold rounded-lg shadow-lg shadow-cyan-600/20 transition flex items-center justify-center space-x-2"
            >
              {uploading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Processing Video...</span>
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  <span>Start Video Pipeline</span>
                </>
              )}
            </button>
          </div>

          {/* Processed Videos History List */}
          <div className="bg-[#0b1320] rounded-xl border border-slate-800 p-4 space-y-3">
            <h3 className="text-xs font-mono font-bold uppercase text-slate-300 flex items-center justify-between">
              <span>Video Jobs ({jobs.length})</span>
              <button onClick={loadJobs} className="text-slate-400 hover:text-cyan-400">
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </h3>

            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {jobs.length === 0 ? (
                <div className="text-xs text-slate-500 font-mono text-center py-6">
                  No video jobs processed yet.
                </div>
              ) : (
                jobs.map(job => {
                  const isSelected = selectedJob?.id === job.id;
                  return (
                    <button
                      key={job.id}
                      onClick={() => selectJob(job.id)}
                      className={`w-full text-left p-2.5 rounded-lg border text-xs transition ${
                        isSelected
                          ? 'bg-cyan-950/40 border-cyan-500/60 shadow-sm'
                          : 'bg-[#101a2d] border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between font-mono">
                        <span className="font-semibold text-slate-200 truncate max-w-[180px]">
                          {job.original_name}
                        </span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                          job.status === 'COMPLETED' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
                          job.status === 'PROCESSING' ? 'bg-blue-950 text-blue-300 border border-blue-800 animate-pulse' :
                          job.status === 'FAILED' ? 'bg-rose-950 text-rose-400 border border-rose-800' :
                          'bg-slate-800 text-slate-400'
                        }`}>
                          {job.status}
                        </span>
                      </div>

                      {/* Progress bar for ongoing job */}
                      {job.status === 'PROCESSING' && (
                        <div className="mt-2 w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                          <div 
                            className="bg-cyan-400 h-full transition-all duration-300"
                            style={{ width: `${job.progress_percent}%` }}
                          />
                        </div>
                      )}

                      <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono mt-1">
                        <span>{job.duration_seconds ? `${job.duration_seconds}s` : 'Processing...'}</span>
                        <span>{new Date(job.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Selected Video Analysis Results & Summary (8 cols) */}
        <div className="lg:col-span-8 space-y-5">
          {!selectedJob ? (
            <div className="bg-[#0b1320] rounded-xl border border-slate-800 p-12 text-center text-slate-400">
              <Video className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-sm">Select a processed video or upload a new one to view analysis telemetry.</p>
            </div>
          ) : (
            <>
              {/* Job Summary Metrics Cards */}
              <div className="bg-[#0b1320] rounded-xl border border-slate-800 p-5 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                      <span>Analysis Report:</span>
                      <span className="text-cyan-400 font-mono">{selectedJob.original_name}</span>
                    </h3>
                    <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                      Duration: {selectedJob.duration_seconds}s • Extracted: {selectedJob.total_extracted_readings} frames @ {selectedJob.sample_interval_sec}s
                    </p>
                  </div>

                  {/* CSV Export Button for this specific video */}
                  <a
                    href={api.getVideoJobCsvUrl(selectedJob.id)}
                    download
                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-[#101a2d] hover:bg-slate-800 text-cyan-300 hover:text-cyan-200 border border-slate-700 rounded-lg text-xs font-mono transition"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Export CSV</span>
                  </a>
                </div>

                {/* 4 KPI Summary Cards */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center font-mono">
                  <div className="p-3 bg-[#101a2d] rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase">Average Reading</span>
                    <div className="text-xl font-bold text-cyan-400 font-display mt-0.5">
                      {selectedJob.avg_value !== null ? `${selectedJob.avg_value} ${config?.unit || 'PSI'}` : 'N/A'}
                    </div>
                  </div>
                  <div className="p-3 bg-[#101a2d] rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase">Min Reading</span>
                    <div className="text-xl font-bold text-emerald-400 font-display mt-0.5">
                      {selectedJob.min_value !== null ? `${selectedJob.min_value}` : 'N/A'}
                    </div>
                  </div>
                  <div className="p-3 bg-[#101a2d] rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase">Max Reading</span>
                    <div className="text-xl font-bold text-rose-400 font-display mt-0.5">
                      {selectedJob.max_value !== null ? `${selectedJob.max_value}` : 'N/A'}
                    </div>
                  </div>
                  <div className="p-3 bg-[#101a2d] rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase">Valid Readings</span>
                    <div className="text-xl font-bold text-white font-display mt-0.5">
                      {selectedJob.valid_readings_count} / {selectedJob.total_extracted_readings}
                    </div>
                  </div>
                </div>

                {/* Duplicates & Inferred Indicator */}
                <div className="flex flex-wrap items-center justify-between text-xs font-mono bg-slate-900/60 p-2.5 rounded-lg border border-slate-800 text-slate-400">
                  <div className="flex items-center space-x-2">
                    <Filter className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Deduplicated frames: <strong className="text-slate-200">{selectedJob.duplicate_filtered_count}</strong></span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                    <span>Invalid / Uncertain frames: <strong className="text-amber-400">{selectedJob.invalid_readings_count}</strong></span>
                  </div>
                </div>
              </div>

              {/* Time-Series Chart */}
              <div className="bg-[#0b1320] rounded-xl border border-slate-800 p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-mono font-bold uppercase text-slate-300 flex items-center space-x-2">
                    <TrendingUp className="w-4 h-4 text-cyan-400" />
                    <span>Video Relative Time-Series ({config?.unit || 'PSI'})</span>
                  </h4>
                  <div className="flex items-center space-x-3 text-[11px] font-mono text-slate-400">
                    <span className="flex items-center space-x-1">
                      <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
                      <span>Measured Value</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                      <span>Critical ({config?.max_critical})</span>
                    </span>
                  </div>
                </div>

                <div className="h-64 w-full">
                  {chartData.length === 0 ? (
                    <div className="h-full flex items-center justify-center text-xs text-slate-500 font-mono">
                      No readings available for this job yet.
                    </div>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
                        <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                        <YAxis stroke="#64748b" tick={{ fontSize: 11, fill: '#94a3b8' }} domain={['auto', 'auto']} />
                        <Tooltip
                          contentStyle={{ backgroundColor: '#0b1320', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                          labelStyle={{ color: '#06b6d4', fontWeight: 'bold' }}
                          formatter={(value, name) => [`${value} ${config?.unit || 'PSI'}`, 'Parameter']}
                        />
                        {config?.max_critical && (
                          <ReferenceLine y={config.max_critical} stroke="#f43f5e" strokeDasharray="4 4" label={{ value: 'CRITICAL', fill: '#f43f5e', fontSize: 10 }} />
                        )}
                        {config?.max_warning && (
                          <ReferenceLine y={config.max_warning} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: 'WARNING', fill: '#f59e0b', fontSize: 10 }} />
                        )}
                        <Line
                          type="monotone"
                          dataKey="value"
                          stroke="#06b6d4"
                          strokeWidth={2.5}
                          dot={{ r: 3, fill: '#06b6d4' }}
                          activeDot={{ r: 6, fill: '#22d3ee' }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </div>

              {/* Frame-by-Frame Inspector Table */}
              <div className="bg-[#0b1320] rounded-xl border border-slate-800 p-5 space-y-3">
                <h4 className="text-xs font-mono font-bold uppercase text-slate-300 flex items-center justify-between">
                  <span>Frame-by-Frame Extraction Log</span>
                  <span className="text-[11px] text-slate-400 font-normal">
                    Distinguishing Actual vs Inferred/Duplicate Readings
                  </span>
                </h4>

                <div className="overflow-x-auto max-h-80 overflow-y-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-[#101a2d] text-slate-400 uppercase text-[10px] sticky top-0">
                      <tr>
                        <th className="py-2 px-3">Video Time</th>
                        <th className="py-2 px-3">Predicted Value</th>
                        <th className="py-2 px-3">Raw Display</th>
                        <th className="py-2 px-3">Confidence</th>
                        <th className="py-2 px-3">Type</th>
                        <th className="py-2 px-3">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {jobReadings.map((r, i) => (
                        <tr key={r.id || i} className="hover:bg-slate-800/40">
                          <td className="py-2 px-3 text-slate-300 font-semibold">
                            {r.video_relative_time !== null ? `${r.video_relative_time.toFixed(2)}s` : 'N/A'}
                          </td>
                          <td className="py-2 px-3 font-bold text-white">
                            {r.numerical_value !== null ? `${r.numerical_value} ${r.unit}` : '--'}
                          </td>
                          <td className="py-2 px-3 text-cyan-300 font-display">
                            {r.raw_text || '--'}
                          </td>
                          <td className="py-2 px-3">
                            <span className={r.confidence >= 0.70 ? 'text-emerald-400' : 'text-amber-400'}>
                              {Math.round(r.confidence * 100)}%
                            </span>
                          </td>
                          <td className="py-2 px-3">
                            {r.is_inferred === 1 ? (
                              <span className="px-1.5 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800 text-[10px]">
                                INFERRED / DUP
                              </span>
                            ) : (
                              <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px]">
                                MEASURED
                              </span>
                            )}
                          </td>
                          <td className="py-2 px-3">
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                              r.status === 'VALID' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
                              r.status === 'WARNING' ? 'bg-amber-950 text-amber-300 border border-amber-800' :
                              r.status === 'CRITICAL' ? 'bg-rose-950 text-rose-300 border border-rose-800' :
                              'bg-slate-800 text-slate-400'
                            }`}>
                              {r.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
