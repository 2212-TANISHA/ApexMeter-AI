import React, { useState, useRef, useEffect } from 'react';
import { 
  Camera, 
  VideoOff, 
  Play, 
  Square, 
  RefreshCw, 
  Sliders, 
  CheckCircle, 
  AlertTriangle, 
  AlertOctagon, 
  HelpCircle, 
  XCircle,
  Cpu,
  Layers,
  Sparkles,
  Zap
} from 'lucide-react';
import { api } from '../services/api';

export default function LiveCameraMonitoring({ config, onReadingSaved }) {
  const [stream, setStream] = useState(null);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [samplingIntervalMs, setSamplingIntervalMs] = useState(config?.sampling_interval_ms || 1000);
  const [cameraError, setCameraError] = useState(null);
  const [lastResult, setLastResult] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [stats, setStats] = useState({ captured: 0, valid: 0, uncertain: 0, alerts: 0 });
  const [useSimulatedMode, setUseSimulatedMode] = useState(false);
  const [roi, setRoi] = useState({ x: 0.15, y: 0.20, width: 0.70, height: 0.60 });

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const timerRef = useRef(null);

  // Start webcam
  const startCamera = async () => {
    setCameraError(null);
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'environment' },
        audio: false
      });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err) {
      console.warn("Webcam access error:", err);
      setCameraError(
        err.name === 'NotAllowedError'
          ? 'Camera permission denied. Please enable camera access in your browser or use the Simulated Stream below.'
          : `Could not access camera (${err.message}). Try the Simulated Machine Stream.`
      );
    }
  };

  // Stop webcam
  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    if (isMonitoring) {
      stopMonitoring();
    }
  };

  // Capture frame from video or simulation
  const captureAndRecognize = async () => {
    if (isProcessing) return;

    if (useSimulatedMode) {
      try {
        setIsProcessing(true);
        const resp = await api.simulateLiveFrame();
        handleRecognitionResponse(resp);
      } catch (err) {
        console.error("Simulation error:", err);
      } finally {
        setIsProcessing(false);
      }
      return;
    }

    if (!videoRef.current || !canvasRef.current || !stream) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (video.readyState < 2) return; // Not ready

    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const base64Data = canvas.toDataURL('image/jpeg', 0.85);

    try {
      setIsProcessing(true);
      const resp = await api.processLiveFrame({
        image_base64: base64Data,
        roi: roi,
        source: 'camera',
        save_reading: true
      });
      handleRecognitionResponse(resp);
    } catch (err) {
      console.error("Frame recognition error:", err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRecognitionResponse = (resp) => {
    setLastResult(resp);
    setStats(prev => ({
      captured: prev.captured + 1,
      valid: prev.valid + (resp.status === 'VALID' || resp.status === 'WARNING' || resp.status === 'CRITICAL' ? 1 : 0),
      uncertain: prev.uncertain + (resp.status === 'UNCERTAIN' ? 1 : 0),
      alerts: prev.alerts + (resp.status === 'WARNING' || resp.status === 'CRITICAL' ? 1 : 0)
    }));
    if (onReadingSaved) {
      onReadingSaved(resp);
    }
  };

  const startMonitoring = () => {
    setIsMonitoring(true);
    // Initial immediate frame capture
    captureAndRecognize();
    timerRef.current = setInterval(captureAndRecognize, samplingIntervalMs);
  };

  const stopMonitoring = () => {
    setIsMonitoring(false);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (stream) stream.getTracks().forEach(t => t.stop());
    };
  }, [stream]);

  // Handle sampling interval update while running
  useEffect(() => {
    if (isMonitoring) {
      if (timerRef.current) clearInterval(timerRef.current);
      timerRef.current = setInterval(captureAndRecognize, samplingIntervalMs);
    }
  }, [samplingIntervalMs]);

  // Status badge styling helper
  const getStatusBadge = (status) => {
    switch (status) {
      case 'VALID':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-emerald-950/80 border border-emerald-700 text-emerald-400 text-xs font-mono font-semibold">
            <CheckCircle className="w-3.5 h-3.5" />
            <span>NORMAL (VALID)</span>
          </span>
        );
      case 'WARNING':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-amber-950/80 border border-amber-700 text-amber-300 text-xs font-mono font-semibold animate-pulse">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>WARNING THRESHOLD</span>
          </span>
        );
      case 'CRITICAL':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-rose-950/90 border border-rose-600 text-rose-300 text-xs font-mono font-bold animate-bounce">
            <AlertOctagon className="w-3.5 h-3.5" />
            <span>CRITICAL ALERT</span>
          </span>
        );
      case 'UNCERTAIN':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-yellow-950/60 border border-yellow-800 text-yellow-400 text-xs font-mono">
            <HelpCircle className="w-3.5 h-3.5" />
            <span>LOW CONFIDENCE</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-slate-400 text-xs font-mono">
            <XCircle className="w-3.5 h-3.5" />
            <span>UNREADABLE / NO DIGITS</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Mode Description */}
      <div className="bg-[#0b1320] p-4 rounded-xl border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <Camera className="w-5 h-5 text-cyan-400" />
              <span>Mode A: Live Camera Monitoring</span>
            </h2>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
              REAL-TIME DL INFERENCE
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Streams video from your laptop camera or test feed, detects the digital instrument display ROI, and predicts numerical telemetry in real time.
          </p>
        </div>

        {/* Mode Switch: Webcam vs Simulated Stream */}
        <div className="flex items-center space-x-2 bg-[#101a2d] p-1 rounded-lg border border-slate-800 text-xs">
          <button
            onClick={() => { setUseSimulatedMode(false); if (!stream) startCamera(); }}
            className={`px-3 py-1.5 rounded-md font-medium transition ${
              !useSimulatedMode ? 'bg-cyan-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            Physical Camera
          </button>
          <button
            onClick={() => { setUseSimulatedMode(true); }}
            className={`px-3 py-1.5 rounded-md font-medium flex items-center space-x-1 transition ${
              useSimulatedMode ? 'bg-purple-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Simulated Stream</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Camera Viewfinder with ROI overlay (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-[#0b1320] rounded-xl border border-slate-800 p-4 relative overflow-hidden">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2 text-xs font-mono text-slate-300">
                <span className={`w-2.5 h-2.5 rounded-full ${isMonitoring ? 'bg-emerald-400 animate-ping' : 'bg-slate-600'}`} />
                <span>FEED: {useSimulatedMode ? 'SYNTHETIC INDUSTRIAL METER' : (stream ? 'LIVE WEBCAM' : 'STANDBY')}</span>
              </div>
              <div className="text-[11px] font-mono text-slate-400">
                Sampling: {samplingIntervalMs}ms
              </div>
            </div>

            {/* Viewfinder Display Box */}
            <div className="relative aspect-video bg-black rounded-lg overflow-hidden border border-slate-800 flex items-center justify-center">
              {!useSimulatedMode ? (
                <>
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className={`w-full h-full object-cover ${!stream ? 'hidden' : ''}`}
                  />
                  {!stream && (
                    <div className="text-center p-6 space-y-3">
                      <Camera className="w-12 h-12 text-slate-600 mx-auto" />
                      <p className="text-xs text-slate-400 max-w-sm">
                        {cameraError || 'Camera is currently stopped. Click "Start Camera" to initialize the webcam preview.'}
                      </p>
                      <button
                        onClick={startCamera}
                        className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium rounded-lg shadow-lg shadow-cyan-600/30 transition"
                      >
                        Start Camera
                      </button>
                    </div>
                  )}
                </>
              ) : (
                /* Simulated Stream Display */
                <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-slate-950 via-[#0a101f] to-slate-900 p-6">
                  {lastResult?.annotated_image_base64 ? (
                    <img 
                      src={`data:image/jpeg;base64,${lastResult.annotated_image_base64}`} 
                      alt="Simulated Meter Face" 
                      className="max-h-52 rounded border border-cyan-800/60 shadow-2xl"
                    />
                  ) : (
                    <div className="text-center space-y-2">
                      <Sparkles className="w-10 h-10 text-purple-400 mx-auto animate-pulse" />
                      <p className="text-xs text-slate-400">
                        Simulated industrial meter generator active. Click "Start Monitoring" to stream synthetic readings.
                      </p>
                    </div>
                  )}
                  <div className="mt-3 text-[10px] font-mono px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800">
                    SIMULATED INDUSTRIAL TELEMETRY
                  </div>
                </div>
              )}

              {/* Display ROI Bounding Box Guide Overlay (when stream is active and not simulated) */}
              {!useSimulatedMode && stream && (
                <div 
                  className="absolute border-2 border-cyan-400 bg-cyan-500/10 pointer-events-none rounded transition-all"
                  style={{
                    left: `${roi.x * 100}%`,
                    top: `${roi.y * 100}%`,
                    width: `${roi.width * 100}%`,
                    height: `${roi.height * 100}%`
                  }}
                >
                  <div className="absolute top-1 left-1.5 px-1.5 py-0.5 bg-cyan-950/90 text-[10px] font-mono text-cyan-300 rounded border border-cyan-700">
                    TARGET DISPLAY ROI
                  </div>
                  {/* Corner Target Marks */}
                  <div className="absolute top-0 left-0 w-3 h-3 border-t-2 border-l-2 border-cyan-300" />
                  <div className="absolute top-0 right-0 w-3 h-3 border-t-2 border-r-2 border-cyan-300" />
                  <div className="absolute bottom-0 left-0 w-3 h-3 border-b-2 border-l-2 border-cyan-300" />
                  <div className="absolute bottom-0 right-0 w-3 h-3 border-b-2 border-r-2 border-cyan-300" />
                </div>
              )}

              {/* Scanline Effect when monitoring */}
              {isMonitoring && (
                <div className="absolute inset-0 pointer-events-none bg-gradient-to-b from-transparent via-cyan-500/5 to-transparent h-12 w-full animate-bounce opacity-40" />
              )}
            </div>

            {/* Hidden canvas for frame extraction */}
            <canvas ref={canvasRef} className="hidden" />

            {/* Camera & Monitoring Controls Bar */}
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800">
              <div className="flex items-center space-x-2">
                {!isMonitoring ? (
                  <button
                    onClick={startMonitoring}
                    disabled={!useSimulatedMode && !stream}
                    className="flex items-center space-x-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-600 text-white text-xs font-semibold rounded-lg shadow-lg shadow-emerald-600/20 transition"
                  >
                    <Play className="w-4 h-4 fill-current" />
                    <span>Start Monitoring</span>
                  </button>
                ) : (
                  <button
                    onClick={stopMonitoring}
                    className="flex items-center space-x-2 px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-rose-600/20 transition"
                  >
                    <Square className="w-4 h-4 fill-current" />
                    <span>Stop Monitoring</span>
                  </button>
                )}

                {!useSimulatedMode && stream && (
                  <button
                    onClick={stopCamera}
                    className="flex items-center space-x-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg border border-slate-700 transition"
                  >
                    <VideoOff className="w-3.5 h-3.5" />
                    <span>Stop Camera</span>
                  </button>
                )}

                <button
                  onClick={captureAndRecognize}
                  disabled={isProcessing || (!useSimulatedMode && !stream)}
                  className="flex items-center space-x-1.5 px-3 py-2 bg-[#101a2d] hover:bg-slate-800 text-slate-300 text-xs rounded-lg border border-slate-800 transition disabled:opacity-50"
                  title="Capture single frame manually"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isProcessing ? 'animate-spin text-cyan-400' : ''}`} />
                  <span>Inspect Frame</span>
                </button>
              </div>

              {/* Sampling Rate Selector */}
              <div className="flex items-center space-x-2 text-xs font-mono text-slate-400">
                <Sliders className="w-3.5 h-3.5 text-cyan-400" />
                <span>Interval:</span>
                <select
                  value={samplingIntervalMs}
                  onChange={(e) => setSamplingIntervalMs(Number(e.target.value))}
                  className="bg-[#101a2d] border border-slate-800 text-slate-200 text-xs rounded px-2 py-1 outline-none focus:border-cyan-500"
                >
                  <option value={500}>500 ms (Fast)</option>
                  <option value={1000}>1000 ms (1s Standard)</option>
                  <option value={2000}>2000 ms (2s Low CPU)</option>
                </select>
              </div>
            </div>

            {/* ROI Adjustment Sliders (collapsible) */}
            {!useSimulatedMode && (
              <details className="mt-3 text-xs text-slate-400">
                <summary className="cursor-pointer hover:text-cyan-300 transition select-none flex items-center space-x-1 font-mono">
                  <span>📐 Adjust Target Display ROI Bounding Box</span>
                </summary>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-2 p-3 bg-[#101a2d] rounded-lg border border-slate-800 text-[11px] font-mono">
                  <div>
                    <label className="block mb-1 text-slate-400">X Offset: {Math.round(roi.x * 100)}%</label>
                    <input 
                      type="range" min="0" max="0.5" step="0.05" value={roi.x}
                      onChange={e => setRoi(prev => ({ ...prev, x: parseFloat(e.target.value) }))}
                      className="w-full accent-cyan-400"
                    />
                  </div>
                  <div>
                    <label className="block mb-1 text-slate-400">Y Offset: {Math.round(roi.y * 100)}%</label>
                    <input 
                      type="range" min="0" max="0.5" step="0.05" value={roi.y}
                      onChange={e => setRoi(prev => ({ ...prev, y: parseFloat(e.target.value) }))}
                      className="w-full accent-cyan-400"
                    />
                  </div>
                  <div>
                    <label className="block mb-1 text-slate-400">Width: {Math.round(roi.width * 100)}%</label>
                    <input 
                      type="range" min="0.3" max="1.0" step="0.05" value={roi.width}
                      onChange={e => setRoi(prev => ({ ...prev, width: parseFloat(e.target.value) }))}
                      className="w-full accent-cyan-400"
                    />
                  </div>
                  <div>
                    <label className="block mb-1 text-slate-400">Height: {Math.round(roi.height * 100)}%</label>
                    <input 
                      type="range" min="0.2" max="0.9" step="0.05" value={roi.height}
                      onChange={e => setRoi(prev => ({ ...prev, height: parseFloat(e.target.value) }))}
                      className="w-full accent-cyan-400"
                    />
                  </div>
                </div>
              </details>
            )}
          </div>
        </div>

        {/* Right Column: Real-Time HUD Recognition Panel (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          {/* Main Digital Reading Display Card */}
          <div className="bg-[#0b1320] rounded-xl border border-slate-800 p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
                {config?.parameter_name || 'PARAMETER'} READING
              </span>
              {getStatusBadge(lastResult?.status)}
            </div>

            {/* 7-Segment Digital Readout Box */}
            <div className="bg-black/90 p-5 rounded-xl border border-slate-800 text-center relative overflow-hidden">
              <div className="text-[11px] font-mono text-slate-500 absolute top-2 left-3">
                METER DIGITAL OUTPUT
              </div>
              
              <div className="my-2">
                <span className="font-display text-5xl font-black tracking-widest text-cyan-400 digital-glow-cyan">
                  {lastResult?.raw_text || '----'}
                </span>
                <span className="text-xl font-mono ml-3 text-cyan-300 font-bold">
                  {lastResult?.unit || config?.unit || 'PSI'}
                </span>
              </div>

              {/* Status details */}
              <div className="text-xs font-mono text-slate-400 flex items-center justify-center space-x-3 mt-1">
                <span>Value: {lastResult?.numerical_value !== null && lastResult?.numerical_value !== undefined ? lastResult.numerical_value : 'N/A'}</span>
                <span>•</span>
                <span>Machine: {config?.machine_id}</span>
              </div>
            </div>

            {/* Model Confidence & Latency Bar */}
            <div className="space-y-3 bg-[#101a2d] p-3.5 rounded-lg border border-slate-800">
              <div>
                <div className="flex justify-between text-xs font-mono mb-1">
                  <span className="text-slate-400">Recognition Confidence</span>
                  <span className={`font-semibold ${
                    (lastResult?.confidence || 0) >= 0.70 ? 'text-emerald-400' : 'text-amber-400'
                  }`}>
                    {lastResult?.confidence !== undefined ? `${Math.round(lastResult.confidence * 100)}%` : '0%'}
                  </span>
                </div>
                <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-300 ${
                      (lastResult?.confidence || 0) >= 0.70
                        ? 'bg-gradient-to-r from-emerald-500 to-cyan-500'
                        : 'bg-amber-500'
                    }`}
                    style={{ width: `${Math.min(100, (lastResult?.confidence || 0) * 100)}%` }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-1 text-slate-300">
                <div className="flex items-center space-x-1.5">
                  <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Latency:</span>
                  <span className="text-cyan-300 font-semibold">{lastResult?.inference_time_ms || 0} ms</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <Layers className="w-3.5 h-3.5 text-purple-400" />
                  <span>Model:</span>
                  <span className="text-purple-300 truncate">{lastResult?.model_used || config?.active_model || 'PyTorch CNN'}</span>
                </div>
              </div>
            </div>

            {/* Segmented Display Visual Preview (Annotated ROI crop) */}
            {lastResult?.annotated_image_base64 && (
              <div className="space-y-1.5">
                <span className="text-[11px] font-mono text-slate-400 flex items-center space-x-1">
                  <span>🔬 Display Element Segmentation (Crop & BBoxes)</span>
                </span>
                <div className="bg-black rounded-lg p-2 border border-slate-800 flex justify-center">
                  <img
                    src={`data:image/jpeg;base64,${lastResult.annotated_image_base64}`}
                    alt="Detected Display Elements"
                    className="max-h-28 rounded object-contain"
                  />
                </div>
              </div>
            )}

            {/* Session Summary Counter */}
            <div className="grid grid-cols-4 gap-2 text-center text-xs font-mono pt-2 border-t border-slate-800">
              <div className="p-2 bg-[#101a2d] rounded border border-slate-800/80">
                <div className="text-slate-400 text-[10px]">FRAMES</div>
                <div className="font-bold text-white text-sm">{stats.captured}</div>
              </div>
              <div className="p-2 bg-[#101a2d] rounded border border-slate-800/80">
                <div className="text-emerald-400 text-[10px]">VALID</div>
                <div className="font-bold text-emerald-400 text-sm">{stats.valid}</div>
              </div>
              <div className="p-2 bg-[#101a2d] rounded border border-slate-800/80">
                <div className="text-yellow-400 text-[10px]">UNCERTAIN</div>
                <div className="font-bold text-yellow-400 text-sm">{stats.uncertain}</div>
              </div>
              <div className="p-2 bg-[#101a2d] rounded border border-slate-800/80">
                <div className="text-rose-400 text-[10px]">ALERTS</div>
                <div className="font-bold text-rose-400 text-sm">{stats.alerts}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
