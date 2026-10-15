"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import {
  Layers,
  Play,
  RotateCw,
  XCircle,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Terminal,
  Cpu,
  ArrowRight,
  Sliders,
  FileCheck,
  Check,
  AlertCircle,
  RefreshCw,
  FolderOpen,
  Info,
} from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import { AlertBanner } from "@/components/AlertBanner";
import {
  api,
  SurveyItem,
  EligibleDatasetItem,
  PhotogrammetryTaskItem,
  TaskLogItem,
  ArtifactItem,
  ClusterStatusResponse,
  ApiClientError,
} from "@/lib/api";

export default function PhotogrammetryPage() {
  // Navigation / Selection State
  const [surveys, setSurveys] = useState<SurveyItem[]>([]);
  const [selectedSurveyId, setSelectedSurveyId] = useState<string>("");
  const [loadingSurveys, setLoadingSurveys] = useState<boolean>(true);

  // Cluster Health State
  const [clusterStatus, setClusterStatus] = useState<ClusterStatusResponse | null>(null);
  const [checkingCluster, setCheckingCluster] = useState<boolean>(true);

  // Eligible Datasets State
  const [datasets, setDatasets] = useState<EligibleDatasetItem[]>([]);
  const [selectedFileId, setSelectedFileId] = useState<string>("");
  const [loadingDatasets, setLoadingDatasets] = useState<boolean>(false);

  // Task Configuration State
  const [preset, setPreset] = useState<"fast" | "precision" | "custom">("precision");
  const [targetGsd, setTargetGsd] = useState<number>(2.5);
  const [generateDsm, setGenerateDsm] = useState<boolean>(true);
  const [generateDtm, setGenerateDtm] = useState<boolean>(true);
  const [radiometricCal, setRadiometricCal] = useState<boolean>(false);
  const [featureQuality, setFeatureQuality] = useState<string>("high");
  const [pcQuality, setPcQuality] = useState<string>("medium");

  // Active Job & History State
  const [activeTask, setActiveTask] = useState<PhotogrammetryTaskItem | null>(null);
  const [taskHistory, setTaskHistory] = useState<PhotogrammetryTaskItem[]>([]);
  const [logs, setLogs] = useState<TaskLogItem[]>([]);
  const [artifacts, setArtifacts] = useState<ArtifactItem[]>([]);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Auto-scroll ref for terminal
  const logTerminalRef = useRef<HTMLDivElement>(null);

  // 1. Initial Load: Cluster Health & Surveys
  const loadInitialData = useCallback(async () => {
    try {
      setCheckingCluster(true);
      const health = await api.getClusterStatus();
      setClusterStatus(health);
    } catch (err: any) {
      setClusterStatus({
        cluster_status: "OFFLINE",
        is_connected: false,
        api_url: "http://localhost:3001",
        engine: "WebODM",
        active_nodes: 0,
        total_nodes: 0,
        details: err?.message || "WebODM service unreachable",
        timestamp: new Date().toISOString(),
      });
    } finally {
      setCheckingCluster(false);
    }

    try {
      setLoadingSurveys(true);
      const res = await api.getSurveys({ limit: 100 });
      setSurveys(res.items);
      if (res.items.length > 0 && !selectedSurveyId) {
        setSelectedSurveyId(res.items[0].id);
      }
    } catch (err: any) {
      setErrorMessage("Failed to load flight surveys from backend: " + (err?.message || ""));
    } finally {
      setLoadingSurveys(false);
    }
  }, [selectedSurveyId]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // 2. When selected survey changes: fetch eligible datasets & existing tasks
  const loadSurveyDetails = useCallback(async (surveyId: string) => {
    if (!surveyId) return;
    try {
      setLoadingDatasets(true);
      setErrorMessage(null);

      // Fetch datasets
      const dsRes = await api.getEligibleDatasets(surveyId);
      setDatasets(dsRes.items);

      // Auto-select first eligible dataset
      const firstEligible = dsRes.items.find((d) => d.is_eligible);
      if (firstEligible) {
        setSelectedFileId(firstEligible.file_id);
      } else {
        setSelectedFileId("");
      }

      // Fetch task history for this survey
      const taskRes = await api.getPhotogrammetryTasks({ survey_id: surveyId, limit: 10 });
      setTaskHistory(taskRes.items);

      // Set active task (first active or most recent)
      if (taskRes.items.length > 0) {
        const running = taskRes.items.find((t) =>
          ["SUBMITTED", "QUEUED", "PREPARING", "UPLOADING", "RUNNING", "FINALIZING"].includes(t.status)
        );
        const target = running || taskRes.items[0];
        setActiveTask(target);
      } else {
        setActiveTask(null);
        setLogs([]);
        setArtifacts([]);
      }
    } catch (err: any) {
      setErrorMessage("Error fetching survey photogrammetry records: " + (err?.message || ""));
    } finally {
      setLoadingDatasets(false);
    }
  }, []);

  useEffect(() => {
    if (selectedSurveyId) {
      loadSurveyDetails(selectedSurveyId);
    }
  }, [selectedSurveyId, loadSurveyDetails]);

  // 3. Polling for Active Task Progress & Logs
  useEffect(() => {
    if (!activeTask) return;

    const isActive = ["SUBMITTED", "QUEUED", "PREPARING", "UPLOADING", "RUNNING", "FINALIZING", "CANCEL_REQUESTED"].includes(
      activeTask.status
    );

    // Initial fetch of logs & artifacts
    const fetchTaskDetails = async () => {
      try {
        const [updatedTask, logsRes, artRes] = await Promise.all([
          api.getPhotogrammetryTask(activeTask.task_id),
          api.getPhotogrammetryLogs(activeTask.task_id),
          api.getPhotogrammetryArtifacts(activeTask.task_id),
        ]);
        setActiveTask(updatedTask);
        setLogs(logsRes.logs);
        setArtifacts(artRes.items);
      } catch (err) {
        // Silently catch polling glitches
      }
    };

    fetchTaskDetails();

    if (!isActive) return;

    // Set polling interval
    const interval = setInterval(fetchTaskDetails, 3000);
    return () => clearInterval(interval);
  }, [activeTask?.task_id, activeTask?.status]);

  // Auto-scroll terminal to bottom when new logs arrive
  useEffect(() => {
    if (logTerminalRef.current) {
      logTerminalRef.current.scrollTop = logTerminalRef.current.scrollHeight;
    }
  }, [logs]);

  // Handle Preset Selection
  const handlePresetChange = (selected: "fast" | "precision" | "custom") => {
    setPreset(selected);
    if (selected === "fast") {
      setTargetGsd(5.0);
      setGenerateDsm(true);
      setGenerateDtm(false);
      setFeatureQuality("low");
      setPcQuality("low");
    } else if (selected === "precision") {
      setTargetGsd(2.5);
      setGenerateDsm(true);
      setGenerateDtm(true);
      setFeatureQuality("high");
      setPcQuality("medium");
    }
  };

  // 4. Submit New Task
  const handleStartReconstruction = async () => {
    if (!selectedSurveyId) {
      setErrorMessage("Please select a target flight survey.");
      return;
    }

    if (clusterStatus && !clusterStatus.is_connected) {
      setErrorMessage("Cannot dispatch job: WebODM photogrammetry cluster is currently offline.");
      return;
    }

    setSubmitting(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const presetName = preset === "fast" ? "FAST" : preset === "precision" ? "HIGH_RES" : "CUSTOM";
      const task = await api.createPhotogrammetryTask({
        survey_id: selectedSurveyId,
        source_file_id: selectedFileId || undefined,
        resolution_preset: presetName,
        custom_resolution_cm: targetGsd,
        generate_dsm: generateDsm,
        generate_dtm: generateDtm,
        radiometric_calibration: radiometricCal,
        feature_quality: featureQuality,
        pc_quality: pcQuality,
      });

      setSuccessMessage(`Photogrammetry reconstruction job dispatched! Task ID: ${task.task_id.slice(0, 8)}`);
      setActiveTask(task);
      setTaskHistory((prev) => [task, ...prev]);
      setLogs([]);
      setArtifacts([]);
    } catch (err: any) {
      if (err instanceof ApiClientError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Failed to initiate photogrammetry task: " + (err?.message || "Unknown error"));
      }
    } finally {
      setSubmitting(false);
    }
  };

  // 5. Cancel Active Task
  const handleCancelTask = async () => {
    if (!activeTask) return;
    setActionLoading(true);
    setErrorMessage(null);
    try {
      await api.cancelPhotogrammetryTask(activeTask.task_id);
      const updated = await api.getPhotogrammetryTask(activeTask.task_id);
      setActiveTask(updated);
      setSuccessMessage("Task cancellation requested.");
    } catch (err: any) {
      setErrorMessage("Failed to cancel task: " + (err?.message || ""));
    } finally {
      setActionLoading(false);
    }
  };

  // 6. Retry Failed Task
  const handleRetryTask = async () => {
    if (!activeTask) return;
    setActionLoading(true);
    setErrorMessage(null);
    try {
      const retried = await api.retryPhotogrammetryTask(activeTask.task_id);
      setActiveTask(retried);
      setSuccessMessage(`Task retry #${retried.retry_count} queued successfully.`);
    } catch (err: any) {
      setErrorMessage("Failed to retry task: " + (err?.message || ""));
    } finally {
      setActionLoading(false);
    }
  };

  const selectedSurvey = surveys.find((s) => s.id === selectedSurveyId);
  const eligibleDatasets = datasets.filter((d) => d.is_eligible);
  const ineligibleDatasets = datasets.filter((d) => !d.is_eligible);
  const isClusterOnline = clusterStatus?.is_connected === true;
  const isTaskRunning = Boolean(
    activeTask &&
      ["SUBMITTED", "QUEUED", "PREPARING", "UPLOADING", "RUNNING", "FINALIZING"].includes(activeTask.status)
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 mb-1">
            <span>Page 2 of 5</span>
            <span>&bull;</span>
            <span className="text-emerald-700 font-bold">Photogrammetry Engine</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            WebODM Photogrammetry Processing
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Submit validated raw aerial survey photos to WebODM, configure photogrammetry options, and track live reconstruction.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/admin/algorithms"
            className="btn-primary text-xs"
          >
            <span>Proceed to Algorithms</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Global Banners */}
      {errorMessage && (
        <AlertBanner
          type="error"
          message={errorMessage}
          onClose={() => setErrorMessage(null)}
        />
      )}
      {successMessage && (
        <AlertBanner
          type="info"
          message={successMessage}
          onClose={() => setSuccessMessage(null)}
        />
      )}

      {/* Row 1: Pipeline Configuration & Cluster Health */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Card 1: Configuration Panel (2 cols) */}
        <div className="card-base p-6 lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2 font-semibold text-sm text-slate-800">
              <Sliders className="w-4 h-4 text-emerald-600" />
              <span>Photogrammetry Pipeline Configuration</span>
            </div>
            <span
              className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${
                isClusterOnline
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : "bg-rose-50 text-rose-700 border-rose-200"
              }`}
            >
              {checkingCluster ? "Checking Node..." : isClusterOnline ? "Cluster Online" : "WebODM Offline"}
            </span>
          </div>

          <div className="space-y-4">
            {/* Survey Selector */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-semibold text-slate-700 block">Target Flight Survey</label>
                {loadingSurveys && <span className="text-[11px] text-slate-400">Loading surveys...</span>}
              </div>
              <select
                value={selectedSurveyId}
                onChange={(e) => setSelectedSurveyId(e.target.value)}
                className="input-base w-full text-xs"
                disabled={loadingSurveys || isTaskRunning}
              >
                {surveys.length === 0 ? (
                  <option value="">No flight surveys found</option>
                ) : (
                  surveys.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.survey_code} ({s.farm_name || "Farm"} &bull; {s.field_name || "Field"} &bull; {s.files_count} files)
                    </option>
                  ))
                )}
              </select>
            </div>

            {/* Eligible Datasets Ledger */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-slate-700 block">
                  Source Drone Photo Dataset
                </label>
                <span className="text-[11px] text-slate-500 font-mono">
                  {eligibleDatasets.length} Eligible | {ineligibleDatasets.length} Ineligible
                </span>
              </div>

              {loadingDatasets ? (
                <div className="p-4 border border-slate-200 rounded-xl text-center text-xs text-slate-500 flex items-center justify-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-emerald-600" />
                  <span>Inspecting dataset eligibility...</span>
                </div>
              ) : datasets.length === 0 ? (
                <div className="p-4 border border-dashed border-slate-200 rounded-xl text-center text-xs text-slate-500 space-y-1">
                  <p>No files uploaded for this survey yet.</p>
                  <Link href="/admin/dashboard" className="text-emerald-600 underline font-semibold">
                    Upload drone photos in Page 1
                  </Link>
                </div>
              ) : (
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {datasets.map((ds) => (
                    <div
                      key={ds.file_id}
                      onClick={() => ds.is_eligible && !isTaskRunning && setSelectedFileId(ds.file_id)}
                      className={`p-2.5 rounded-xl border text-xs flex items-center justify-between transition-all ${
                        !ds.is_eligible
                          ? "bg-slate-50/70 border-slate-200 opacity-70 cursor-not-allowed"
                          : selectedFileId === ds.file_id
                          ? "border-emerald-600 bg-emerald-50/60 shadow-xs cursor-pointer"
                          : "border-slate-200 hover:border-slate-300 bg-white cursor-pointer"
                      }`}
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <div
                          className={`w-3.5 h-3.5 rounded-full border flex items-center justify-center ${
                            selectedFileId === ds.file_id
                              ? "border-emerald-600 bg-emerald-600 text-white"
                              : "border-slate-300"
                          }`}
                        >
                          {selectedFileId === ds.file_id && <Check className="w-2.5 h-2.5 stroke-[3]" />}
                        </div>
                        <div className="truncate">
                          <p className="font-semibold text-slate-900 truncate">{ds.original_filename}</p>
                          <p className="text-[11px] text-slate-500">
                            {ds.file_type} &bull; {(ds.file_size_bytes / (1024 * 1024)).toFixed(1)} MB
                            {ds.photo_count_estimate ? ` &bull; ~${ds.photo_count_estimate} photos` : ""}
                          </p>
                          {!ds.is_eligible && ds.ineligibility_reason && (
                            <p className="text-[10px] text-rose-600 font-medium mt-0.5">
                              {ds.ineligibility_reason}
                            </p>
                          )}
                        </div>
                      </div>

                      <div className="shrink-0 ml-2">
                        {ds.is_eligible ? (
                          <span className="badge-done text-[10px] py-0.5">Eligible</span>
                        ) : (
                          <span className="badge-failed text-[10px] py-0.5">Ineligible</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Presets */}
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-2">Processing Presets</label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <button
                  type="button"
                  disabled={isTaskRunning}
                  onClick={() => handlePresetChange("fast")}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    preset === "fast"
                      ? "border-emerald-600 bg-emerald-50/50 shadow-xs"
                      : "border-slate-200 hover:border-slate-300 bg-white"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-xs text-slate-900">Agricultural Fast</span>
                    {preset === "fast" && <Check className="w-3.5 h-3.5 text-emerald-600" />}
                  </div>
                  <p className="text-[11px] text-slate-500">Rapid 2D orthomosaic generation (~15-30 min, 5cm GSD).</p>
                </button>

                <button
                  type="button"
                  disabled={isTaskRunning}
                  onClick={() => handlePresetChange("precision")}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    preset === "precision"
                      ? "border-emerald-600 bg-emerald-50/50 shadow-xs"
                      : "border-slate-200 hover:border-slate-300 bg-white"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-xs text-slate-900">High Precision</span>
                    {preset === "precision" && <Check className="w-3.5 h-3.5 text-emerald-600" />}
                  </div>
                  <p className="text-[11px] text-slate-500">Full point-cloud densification, 2.5cm orthomosaic &amp; elevation DSM/DTM.</p>
                </button>

                <button
                  type="button"
                  disabled={isTaskRunning}
                  onClick={() => handlePresetChange("custom")}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    preset === "custom"
                      ? "border-emerald-600 bg-emerald-50/50 shadow-xs"
                      : "border-slate-200 hover:border-slate-300 bg-white"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-xs text-slate-900">Custom Options</span>
                    {preset === "custom" && <Check className="w-3.5 h-3.5 text-emerald-600" />}
                  </div>
                  <p className="text-[11px] text-slate-500">Specify manual GSD, feature extraction quality and camera flags.</p>
                </button>
              </div>
            </div>

            {/* Custom Sliders & Toggles */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Target GSD (cm/pixel)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0.5"
                  max="50"
                  disabled={preset !== "custom" || isTaskRunning}
                  value={targetGsd}
                  onChange={(e) => setTargetGsd(Number(e.target.value))}
                  className="input-base w-full text-xs disabled:bg-slate-100 disabled:text-slate-400"
                />
              </div>

              <div className="flex items-center gap-2 pt-6">
                <input
                  type="checkbox"
                  id="dsm-toggle"
                  disabled={isTaskRunning}
                  checked={generateDsm}
                  onChange={(e) => setGenerateDsm(e.target.checked)}
                  className="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500"
                />
                <label htmlFor="dsm-toggle" className="text-xs font-semibold text-slate-700 cursor-pointer">
                  Generate Elevation Model (DSM)
                </label>
              </div>

              <div className="flex items-center gap-2 pt-6">
                <input
                  type="checkbox"
                  id="dtm-toggle"
                  disabled={isTaskRunning}
                  checked={generateDtm}
                  onChange={(e) => setGenerateDtm(e.target.checked)}
                  className="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500"
                />
                <label htmlFor="dtm-toggle" className="text-xs font-semibold text-slate-700 cursor-pointer">
                  Generate Terrain Model (DTM)
                </label>
              </div>
            </div>

            {/* Quality options when Custom is active */}
            {preset === "custom" && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-3 bg-slate-50 rounded-xl border border-slate-200">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Feature Extraction Quality
                  </label>
                  <select
                    value={featureQuality}
                    disabled={isTaskRunning}
                    onChange={(e) => setFeatureQuality(e.target.value)}
                    className="input-base w-full text-xs"
                  >
                    <option value="lowest">Lowest (fastest)</option>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High (recommended)</option>
                    <option value="ultra">Ultra (high RAM required)</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Point Cloud Densification
                  </label>
                  <select
                    value={pcQuality}
                    disabled={isTaskRunning}
                    onChange={(e) => setPcQuality(e.target.value)}
                    className="input-base w-full text-xs"
                  >
                    <option value="lowest">Lowest</option>
                    <option value="low">Low</option>
                    <option value="medium">Medium (standard)</option>
                    <option value="high">High</option>
                    <option value="ultra">Ultra (very high compute)</option>
                  </select>
                </div>
              </div>
            )}

            {/* Submission Action */}
            <div className="pt-2 flex items-center justify-between">
              <button
                type="button"
                onClick={handleStartReconstruction}
                disabled={submitting || isTaskRunning || !selectedSurveyId || eligibleDatasets.length === 0}
                className="btn-primary text-xs disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Dispatching Reconstruction...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Start Photogrammetry Reconstruction</span>
                  </>
                )}
              </button>

              {isTaskRunning && (
                <span className="text-xs text-amber-600 font-semibold flex items-center gap-1.5 animate-pulse">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Active task in progress
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Card 2: Cluster Node Health (1 col) */}
        <div className="card-base p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2 font-semibold text-sm text-slate-800">
              <Cpu className="w-4 h-4 text-emerald-600" />
              <span>WebODM Compute Cluster</span>
            </div>
            <button
              onClick={loadInitialData}
              disabled={checkingCluster}
              className="text-slate-400 hover:text-slate-600 transition-colors p-1"
              title="Refresh Cluster Status"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${checkingCluster ? "animate-spin" : ""}`} />
            </button>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500">Service Status</span>
              {checkingCluster ? (
                <span className="text-slate-400">Probing...</span>
              ) : isClusterOnline ? (
                <span className="font-semibold text-emerald-700 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  Online &amp; Responsive
                </span>
              ) : (
                <span className="font-semibold text-rose-600 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-rose-500" />
                  Cluster Offline
                </span>
              )}
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500">Photogrammetry Engine</span>
              <strong className="text-slate-900 font-mono">
                {clusterStatus?.engine || "WebODM / NodeODM"}
              </strong>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500">Active Compute Nodes</span>
              <strong className="text-slate-900 font-mono">
                {clusterStatus?.active_nodes ?? 0} / {clusterStatus?.total_nodes ?? 0}
              </strong>
            </div>

            {clusterStatus?.available_ram_gb !== undefined && clusterStatus.available_ram_gb !== null && (
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                <span className="text-slate-500">Available Node RAM</span>
                <strong className="text-slate-900 font-mono">
                  {clusterStatus.available_ram_gb} GB
                </strong>
              </div>
            )}

            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500">Target API Endpoint</span>
              <strong className="text-slate-700 font-mono text-[10px] truncate max-w-[150px]">
                {clusterStatus?.api_url || "http://localhost:3001"}
              </strong>
            </div>
          </div>

          {!isClusterOnline ? (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs space-y-1.5 text-amber-900">
              <div className="flex items-center gap-1.5 font-bold text-amber-800">
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                <span>WebODM Not Detected on Port 3001</span>
              </div>
              <p className="text-[11px] leading-relaxed text-amber-800">
                To run real photogrammetric reconstructions locally:
              </p>
              <code className="block bg-amber-100/80 p-2 rounded text-[11px] font-mono text-amber-950 overflow-x-auto">
                docker run -p 3001:3000 opendronemap/nodeodm
              </code>
              <p className="text-[11px] text-amber-700">
                Or start a full WebODM cluster using the documentation in <code className="font-mono">docs/phase-6/</code>.
              </p>
            </div>
          ) : (
            <AlertBanner
              type="info"
              message="Dedicated Celery queue (photogrammetry) prevents heavy reconstructions from blocking GIS raster operations."
            />
          )}
        </div>
      </div>

      {/* Row 2: Live Task Progress & Terminal */}
      {activeTask && (
        <div className="card-base p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-slate-900">
                  Task: {activeTask.task_id.slice(0, 8)}...
                </span>
                {activeTask.webodm_task_uuid && (
                  <span className="text-[11px] font-mono text-slate-500">
                    (WebODM: {activeTask.webodm_task_uuid.slice(0, 8)}...)
                  </span>
                )}
                <StatusBadge status={activeTask.status} />
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Stage: <strong className="text-slate-700">{activeTask.current_stage || "Initializing"}</strong>
                {activeTask.source_filename && ` &bull; Source: ${activeTask.source_filename}`}
              </p>
            </div>

            <div className="flex items-center gap-2">
              {isTaskRunning && (
                <button
                  type="button"
                  onClick={handleCancelTask}
                  disabled={actionLoading}
                  className="btn-secondary text-xs text-rose-600 border-rose-200 hover:bg-rose-50"
                >
                  <XCircle className="w-3.5 h-3.5 text-rose-500" />
                  <span>Cancel Job</span>
                </button>
              )}

              {(activeTask.status === "FAILED" || activeTask.status === "CANCELLED") && (
                <button
                  type="button"
                  onClick={handleRetryTask}
                  disabled={actionLoading}
                  className="btn-secondary text-xs text-emerald-700 border-emerald-200 hover:bg-emerald-50"
                >
                  <RotateCw className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Retry Task</span>
                </button>
              )}
            </div>
          </div>

          {/* Progress Bar */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-medium text-slate-600">
              <span>Overall Task Progress</span>
              <span>
                {activeTask.progress_percent}%
                {activeTask.started_at && ` (Started: ${new Date(activeTask.started_at).toLocaleTimeString()})`}
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden">
              <div
                className={`h-full transition-all duration-500 ${
                  activeTask.status === "FAILED"
                    ? "bg-rose-600"
                    : activeTask.status === "COMPLETED"
                    ? "bg-emerald-600"
                    : "bg-blue-600 animate-pulse"
                }`}
                style={{ width: `${Math.max(activeTask.progress_percent, 5)}%` }}
              />
            </div>
          </div>

          {/* Failure Alert if Failed */}
          {activeTask.status === "FAILED" && activeTask.error_message && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 space-y-1">
              <div className="flex items-center gap-1.5 font-bold">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>Photogrammetry Failure Diagnostic</span>
              </div>
              <p className="font-mono text-[11px] break-words">{activeTask.error_message}</p>
            </div>
          )}

          {/* Monospace Log Terminal */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
              <span className="flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5 text-slate-500" />
                <span>Diagnostic Log Feed</span>
              </span>
              <span className="text-[11px] font-mono text-slate-400">
                {logs.length} lines logged
              </span>
            </div>
            <div
              ref={logTerminalRef}
              className="bg-slate-900 text-slate-200 p-4 rounded-xl font-mono text-xs h-64 overflow-y-auto space-y-1 shadow-inner border border-slate-800"
            >
              {logs.length === 0 ? (
                <div className="text-slate-500 italic p-2">Waiting for console output from worker...</div>
              ) : (
                logs.map((log) => (
                  <div
                    key={log.id}
                    className="leading-relaxed hover:bg-slate-800/50 px-1 rounded transition-colors text-[11px]"
                  >
                    <span className="text-slate-500">[{new Date(log.logged_at).toLocaleTimeString()}] </span>
                    <span
                      className={`font-semibold mr-1.5 ${
                        log.log_level === "ERROR"
                          ? "text-rose-400"
                          : log.log_level === "WARNING"
                          ? "text-amber-400"
                          : "text-emerald-400"
                      }`}
                    >
                      {log.log_level}:
                    </span>
                    <span className="text-slate-300">{log.message}</span>
                  </div>
                ))
              )}
              {isTaskRunning && (
                <div className="flex items-center gap-2 text-emerald-400 pt-2 font-bold animate-pulse text-[11px]">
                  <span>&gt; Task actively processing...</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Row 3: Generated Artifacts Ledger */}
      <div className="card-base p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Generated Photogrammetry Deliverables</h2>
            <p className="text-xs text-slate-500">
              Stitched orthomosaics, surface models (DSM) and terrain models (DTM) verified on storage backend.
            </p>
          </div>
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
            {artifacts.length} Deliverables Ready
          </span>
        </div>

        {artifacts.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500 space-y-2 border border-dashed border-slate-200 rounded-xl">
            <FolderOpen className="w-8 h-8 text-slate-300 mx-auto" />
            <p className="font-semibold text-slate-700">No output deliverables generated yet</p>
            <p className="text-slate-400 max-w-sm mx-auto">
              Deliverables appear here automatically once WebODM completes point-cloud densification and raster orthorectification.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border border-slate-200 rounded-lg overflow-hidden">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4">Artifact Name</th>
                  <th className="py-2.5 px-4">Type</th>
                  <th className="py-2.5 px-4">Spatial CRS</th>
                  <th className="py-2.5 px-4">Resolution (GSD)</th>
                  <th className="py-2.5 px-4">Storage URI</th>
                  <th className="py-2.5 px-4 text-right">Phase 7 Handoff</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {artifacts.map((art) => (
                  <tr key={art.product_id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3 px-4 font-bold text-slate-900 flex items-center gap-2">
                      <FileCheck className="w-4 h-4 text-emerald-600" />
                      <span>{art.original_filename}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="badge-queued text-[10px] py-0.5">{art.product_type}</span>
                    </td>
                    <td className="py-3 px-4 font-mono">{art.crs_epsg}</td>
                    <td className="py-3 px-4 font-mono">
                      {art.resolution_cm_px ? `${art.resolution_cm_px} cm/px` : "N/A"}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-500 truncate max-w-xs" title={art.blob_uri}>
                      {art.blob_uri}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {art.product_type === "ORTHOPHOTO" ? (
                        <Link
                          href="/admin/algorithms"
                          className="btn-primary text-xs py-1 px-3"
                        >
                          <span>Open in Algorithms</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      ) : (
                        <span className="badge-done text-[10px] py-0.5">Archived</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Row 4: Task History */}
      {taskHistory.length > 1 && (
        <div className="card-base p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Survey Reconstruction History</h2>
              <p className="text-xs text-slate-500">Previous photogrammetry execution attempts for this flight survey.</p>
            </div>
            <span className="text-xs text-slate-500 font-mono">{taskHistory.length} Total Runs</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border border-slate-200 rounded-lg overflow-hidden">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4">Task ID</th>
                  <th className="py-2.5 px-4">Preset</th>
                  <th className="py-2.5 px-4">Status</th>
                  <th className="py-2.5 px-4">Progress</th>
                  <th className="py-2.5 px-4">Started</th>
                  <th className="py-2.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {taskHistory.map((t) => (
                  <tr
                    key={t.task_id}
                    className={`hover:bg-slate-50/60 transition-colors ${
                      activeTask?.task_id === t.task_id ? "bg-emerald-50/40" : ""
                    }`}
                  >
                    <td className="py-2.5 px-4 font-mono font-semibold text-slate-900">
                      {t.task_id.slice(0, 8)}...
                    </td>
                    <td className="py-2.5 px-4 font-mono">{t.resolution_preset}</td>
                    <td className="py-2.5 px-4">
                      <StatusBadge status={t.status} />
                    </td>
                    <td className="py-2.5 px-4 font-mono">{t.progress_percent}%</td>
                    <td className="py-2.5 px-4 text-slate-500">
                      {t.started_at ? new Date(t.started_at).toLocaleString() : "N/A"}
                    </td>
                    <td className="py-2.5 px-4 text-right">
                      <button
                        type="button"
                        onClick={() => setActiveTask(t)}
                        className="text-emerald-700 font-semibold hover:underline text-xs"
                      >
                        Inspect Run
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
