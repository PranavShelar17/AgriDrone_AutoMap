"use client";

import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";
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
  Plus,
  Search,
  Filter,
  Trash2,
  Edit3,
  MapPin,
  Eye,
  Download,
  ExternalLink,
  ShieldCheck,
  Activity,
  HardDrive,
  Zap,
  Database,
  UploadCloud,
  X,
  FileText,
  ChevronRight,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
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
  PhotogrammetryProjectItem,
  PhotogrammetryProjectCreate,
  GCPValidateResponse,
  ClusterNodeItem,
  DiagnosticsResponse,
  PhotogrammetryAdminConfigResponse,
  ApiClientError,
  FarmItem,
} from "@/lib/api";

type WorkspaceTab =
  | "projects"
  | "ingest"
  | "tasks"
  | "presets"
  | "map"
  | "nodes"
  | "diagnostics"
  | "admin";

export default function WebODMPhotogrammetryWorkspace() {
  const { user, isAdmin, isFarmer } = useAuth();

  // Active Tab
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("projects");

  // Core Data
  const [projects, setProjects] = useState<PhotogrammetryProjectItem[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [loadingProjects, setLoadingProjects] = useState<boolean>(true);

  const [surveys, setSurveys] = useState<SurveyItem[]>([]);
  const [selectedSurveyId, setSelectedSurveyId] = useState<string>("");
  const [loadingSurveys, setLoadingSurveys] = useState<boolean>(true);

  const [farms, setFarms] = useState<FarmItem[]>([]);

  // Cluster Status
  const [clusterStatus, setClusterStatus] = useState<ClusterStatusResponse | null>(null);
  const [checkingCluster, setCheckingCluster] = useState<boolean>(true);

  // Eligible Ingested Datasets
  const [datasets, setDatasets] = useState<EligibleDatasetItem[]>([]);
  const [selectedFileId, setSelectedFileId] = useState<string>("");
  const [loadingDatasets, setLoadingDatasets] = useState<boolean>(false);

  // Active Task & History
  const [activeTask, setActiveTask] = useState<PhotogrammetryTaskItem | null>(null);
  const [taskHistory, setTaskHistory] = useState<PhotogrammetryTaskItem[]>([]);
  const [logs, setLogs] = useState<TaskLogItem[]>([]);
  const [artifacts, setArtifacts] = useState<ArtifactItem[]>([]);
  const [selectedArtifact, setSelectedArtifact] = useState<ArtifactItem | null>(null);
  const [submittingTask, setSubmittingTask] = useState<boolean>(false);
  const [actionLoading, setActionLoading] = useState<boolean>(false);

  // Preset & Configuration
  const [preset, setPreset] = useState<"fast" | "precision" | "multispectral" | "custom">("precision");
  const [targetGsd, setTargetGsd] = useState<number>(2.5);
  const [generateDsm, setGenerateDsm] = useState<boolean>(true);
  const [generateDtm, setGenerateDtm] = useState<boolean>(true);
  const [radiometricCal, setRadiometricCal] = useState<boolean>(false);
  const [featureQuality, setFeatureQuality] = useState<string>("high");
  const [pcQuality, setPcQuality] = useState<string>("medium");

  // GCP Ingestion State
  const [gcpContent, setGcpContent] = useState<string>("");
  const [validatingGcp, setValidatingGcp] = useState<boolean>(false);
  const [gcpResult, setGcpResult] = useState<GCPValidateResponse | null>(null);
  const [gcpAttached, setGcpAttached] = useState<boolean>(false);

  // Raw Photos Upload State
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isDragOver, setIsDragOver] = useState<boolean>(false);

  // Nodes & Diagnostics Telemetry
  const [nodes, setNodes] = useState<ClusterNodeItem[]>([]);
  const [loadingNodes, setLoadingNodes] = useState<boolean>(false);
  const [diagnostics, setDiagnostics] = useState<DiagnosticsResponse | null>(null);
  const [loadingDiagnostics, setLoadingDiagnostics] = useState<boolean>(false);
  const [adminConfig, setAdminConfig] = useState<PhotogrammetryAdminConfigResponse | null>(null);

  // UI Modals & Filters
  const [showAddProjectModal, setShowAddProjectModal] = useState<boolean>(false);
  const [newProjectName, setNewProjectName] = useState<string>("");
  const [newProjectDesc, setNewProjectDesc] = useState<string>("");
  const [newProjectFarmId, setNewProjectFarmId] = useState<string>("");
  const [newProjectFieldId, setNewProjectFieldId] = useState<string>("");
  const [creatingProject, setCreatingProject] = useState<boolean>(false);

  const [projectSearchQuery, setProjectSearchQuery] = useState<string>("");
  const [projectSortBy, setProjectSortBy] = useState<"newest" | "name" | "tasks">("newest");
  const [taskStatusFilter, setTaskStatusFilter] = useState<string>("ALL");

  const [showLogDrawer, setShowLogDrawer] = useState<boolean>(false);
  const [autoScrollLogs, setAutoScrollLogs] = useState<boolean>(true);

  // Feedback Messages
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const logTerminalRef = useRef<HTMLDivElement>(null);

  // 1. Initial Data Fetch: Projects, Surveys, Farms, and Cluster Health
  const loadInitialWorkspaceData = useCallback(async () => {
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
        details: err?.message || "WebODM / NodeODM cluster offline",
        timestamp: new Date().toISOString(),
      });
    } finally {
      setCheckingCluster(false);
    }

    try {
      setLoadingProjects(true);
      const [projRes, survRes, farmRes] = await Promise.all([
        api.getPhotogrammetryProjects({ limit: 100 }),
        api.getSurveys({ limit: 100 }),
        api.getFarms({ limit: 50 }),
      ]);
      setProjects(projRes.items);
      setSurveys(survRes.items);
      setFarms(farmRes.items);

      if (projRes.items.length > 0 && !selectedProjectId) {
        setSelectedProjectId(projRes.items[0].id);
      }
      if (survRes.items.length > 0 && !selectedSurveyId) {
        setSelectedSurveyId(survRes.items[0].id);
      }
    } catch (err: any) {
      setErrorMessage("Failed to load initial workspace data: " + (err?.message || ""));
    } finally {
      setLoadingProjects(false);
      setLoadingSurveys(false);
    }
  }, [selectedProjectId, selectedSurveyId]);

  useEffect(() => {
    loadInitialWorkspaceData();
  }, [loadInitialWorkspaceData]);

  // 2. Fetch Tasks & Datasets for Selected Survey / Project
  const loadSurveyContext = useCallback(async (surveyId: string) => {
    if (!surveyId) return;
    try {
      setLoadingDatasets(true);
      const [dsRes, taskRes] = await Promise.all([
        api.getEligibleDatasets(surveyId),
        api.getPhotogrammetryTasks({ survey_id: surveyId, limit: 20 }),
      ]);
      setDatasets(dsRes.items);
      setTaskHistory(taskRes.items);

      const firstEligible = dsRes.items.find((d) => d.is_eligible);
      if (firstEligible) {
        setSelectedFileId(firstEligible.file_id);
      } else {
        setSelectedFileId("");
      }

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
      setErrorMessage("Error fetching survey photogrammetry context: " + (err?.message || ""));
    } finally {
      setLoadingDatasets(false);
    }
  }, []);

  useEffect(() => {
    if (selectedSurveyId) {
      loadSurveyContext(selectedSurveyId);
    }
  }, [selectedSurveyId, loadSurveyContext]);

  // 3. Polling for Active Task Progress & Logs
  useEffect(() => {
    if (!activeTask) return;
    const isRunning = [
      "SUBMITTED",
      "QUEUED",
      "PREPARING",
      "UPLOADING",
      "RUNNING",
      "FINALIZING",
      "CANCEL_REQUESTED",
    ].includes(activeTask.status);

    const fetchDetails = async () => {
      try {
        const [updatedTask, logsRes, artRes] = await Promise.all([
          api.getPhotogrammetryTask(activeTask.task_id),
          api.getPhotogrammetryLogs(activeTask.task_id, 200),
          api.getPhotogrammetryArtifacts(activeTask.task_id),
        ]);
        setActiveTask(updatedTask);
        setLogs(logsRes.logs);
        setArtifacts(artRes.items);
        if (artRes.items.length > 0 && !selectedArtifact) {
          setSelectedArtifact(artRes.items[0]);
        }
      } catch {
        // Silently tolerate temporary polling network blips
      }
    };

    fetchDetails();
    if (!isRunning) return;

    const interval = setInterval(fetchDetails, 3000);
    return () => clearInterval(interval);
  }, [activeTask?.task_id, activeTask?.status, selectedArtifact]);

  // Auto-scroll logs
  useEffect(() => {
    if (autoScrollLogs && logTerminalRef.current) {
      logTerminalRef.current.scrollTop = logTerminalRef.current.scrollHeight;
    }
  }, [logs, autoScrollLogs]);

  // 4. Fetch Nodes, Diagnostics, and Admin Config on Tab Switch
  useEffect(() => {
    if (activeTab === "nodes" && isAdmin) {
      setLoadingNodes(true);
      api
        .getProcessingNodes()
        .then((res) => setNodes(res.nodes))
        .catch((err) => console.warn("Failed to fetch nodes:", err))
        .finally(() => setLoadingNodes(false));
    } else if (activeTab === "diagnostics" && isAdmin) {
      setLoadingDiagnostics(true);
      api
        .getPhotogrammetryDiagnostics()
        .then((res) => setDiagnostics(res))
        .catch((err) => console.warn("Failed to fetch diagnostics:", err))
        .finally(() => setLoadingDiagnostics(false));
    } else if (activeTab === "admin" && isAdmin) {
      api
        .getPhotogrammetryAdminConfig()
        .then((res) => setAdminConfig(res))
        .catch((err) => console.warn("Failed to fetch admin config:", err));
    }
  }, [activeTab, isAdmin]);

  // Filtered & Sorted Projects
  const filteredProjects = useMemo(() => {
    let list = [...projects];
    if (projectSearchQuery.trim()) {
      const q = projectSearchQuery.toLowerCase();
      list = list.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.description?.toLowerCase().includes(q) ||
          p.farm_name?.toLowerCase().includes(q) ||
          p.survey_code?.toLowerCase().includes(q)
      );
    }
    if (projectSortBy === "name") {
      list.sort((a, b) => a.name.localeCompare(b.name));
    } else if (projectSortBy === "tasks") {
      list.sort((a, b) => b.tasks_count - a.tasks_count);
    } else {
      list.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    }
    return list;
  }, [projects, projectSearchQuery, projectSortBy]);

  // Filtered Tasks
  const filteredTasks = useMemo(() => {
    if (taskStatusFilter === "ALL") return taskHistory;
    return taskHistory.filter((t) => t.status === taskStatusFilter);
  }, [taskHistory, taskStatusFilter]);

  // 5. Actions: Create Project
  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) {
      setErrorMessage("Project name is required.");
      return;
    }
    try {
      setCreatingProject(true);
      setErrorMessage(null);
      const payload: PhotogrammetryProjectCreate = {
        name: newProjectName.trim(),
        description: newProjectDesc.trim() || undefined,
        farm_id: newProjectFarmId || undefined,
        field_id: newProjectFieldId || undefined,
        survey_id: selectedSurveyId || undefined,
      };
      const created = await api.createPhotogrammetryProject(payload);
      setProjects((prev) => [created, ...prev]);
      setSelectedProjectId(created.id);
      setSuccessMessage(`Project "${created.name}" created successfully.`);
      setShowAddProjectModal(false);
      setNewProjectName("");
      setNewProjectDesc("");
    } catch (err: any) {
      setErrorMessage("Failed to create project: " + (err?.message || ""));
    } finally {
      setCreatingProject(false);
    }
  };

  // 6. Actions: Delete Project
  const handleDeleteProject = async (projId: string, projName: string) => {
    if (!confirm(`Are you sure you want to delete project "${projName}"? Associated task records will be unlinked.`)) {
      return;
    }
    try {
      setActionLoading(true);
      await api.deletePhotogrammetryProject(projId);
      setProjects((prev) => prev.filter((p) => p.id !== projId));
      if (selectedProjectId === projId) {
        setSelectedProjectId(projects.find((p) => p.id !== projId)?.id || "");
      }
      setSuccessMessage(`Project "${projName}" deleted successfully.`);
    } catch (err: any) {
      setErrorMessage("Failed to delete project: " + (err?.message || ""));
    } finally {
      setActionLoading(false);
    }
  };

  // 7. Actions: Validate GCP
  const handleValidateGcp = async () => {
    if (!gcpContent.trim()) {
      setErrorMessage("Please paste or load GCP coordinate data first.");
      return;
    }
    try {
      setValidatingGcp(true);
      setErrorMessage(null);
      const res = await api.validateGcp({ content: gcpContent });
      setGcpResult(res);
      if (res.valid) {
        setGcpAttached(true);
        setSuccessMessage(`GCP verified! Identified ${res.point_count} points in CRS: ${res.crs}`);
      } else {
        setGcpAttached(false);
        setErrorMessage("GCP verification failed. Check errors below.");
      }
    } catch (err: any) {
      setErrorMessage("Error verifying GCP: " + (err?.message || ""));
    } finally {
      setValidatingGcp(false);
    }
  };

  // 8. Actions: Handle File Drop & Ingest Photos
  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const dropped = Array.from(e.dataTransfer.files);
      const valid = dropped.filter((f) => /\.(jpe?g|png|tif|tiff)$/i.test(f.name));
      if (valid.length !== dropped.length) {
        setErrorMessage("Some files were skipped: Only JPG, PNG, and TIF photographs are supported.");
      }
      setSelectedFiles((prev) => [...prev, ...valid]);
    }
  };

  const handleUploadPhotos = async () => {
    if (!selectedSurveyId) {
      setErrorMessage("Please select a target flight survey first.");
      return;
    }
    if (selectedFiles.length === 0) {
      setErrorMessage("Please select at least one photograph to upload.");
      return;
    }
    try {
      setIsUploading(true);
      setUploadProgress(10);
      setErrorMessage(null);

      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        const formData = new FormData();
        formData.append("file", file);
        formData.append("workflow_mode", "raw_photos");

        const token = typeof window !== "undefined" ? localStorage.getItem("agridrone_token") : null;
        const res = await fetch(`/api/v1/ingestion/upload/${selectedSurveyId}`, {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          body: formData,
        });

        if (!res.ok) {
          throw new Error(`Upload failed for ${file.name} (HTTP ${res.status})`);
        }
        setUploadProgress(Math.round(((i + 1) / selectedFiles.length) * 100));
      }

      setSuccessMessage(`Successfully uploaded ${selectedFiles.length} photographs.`);
      setSelectedFiles([]);
      loadSurveyContext(selectedSurveyId);
    } catch (err: any) {
      setErrorMessage("Upload error: " + (err?.message || ""));
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  // 9. Actions: Launch Task with Preset
  const handleLaunchTask = async (overridePreset?: "fast" | "precision" | "multispectral" | "custom") => {
    if (!selectedSurveyId) {
      setErrorMessage("Please select a valid survey first.");
      return;
    }
    const chosenPreset = overridePreset || preset;
    let resolutionPreset: "FAST" | "HIGH_RES" | "MULTISPECTRAL" | "CUSTOM" = "HIGH_RES";
    let dsm = generateDsm;
    let dtm = generateDtm;
    let cal = radiometricCal;
    let fq = featureQuality;
    let pq = pcQuality;
    let gsd = targetGsd;

    if (chosenPreset === "fast") {
      resolutionPreset = "FAST";
      dsm = false;
      dtm = false;
      fq = "medium";
      pq = "low";
      gsd = 5.0;
    } else if (chosenPreset === "multispectral") {
      resolutionPreset = "MULTISPECTRAL";
      cal = true;
      dsm = true;
      dtm = true;
      fq = "high";
      pq = "high";
      gsd = 2.0;
    } else if (chosenPreset === "precision") {
      resolutionPreset = "HIGH_RES";
      dsm = true;
      dtm = true;
      fq = "high";
      pq = "medium";
      gsd = 2.5;
    } else {
      resolutionPreset = "CUSTOM";
    }

    try {
      setSubmittingTask(true);
      setErrorMessage(null);
      const payload = {
        survey_id: selectedSurveyId,
        source_file_id: selectedFileId || undefined,
        project_id: selectedProjectId || undefined,
        resolution_preset: resolutionPreset,
        custom_resolution_cm: gsd,
        generate_dsm: dsm,
        generate_dtm: dtm,
        radiometric_calibration: cal,
        feature_quality: fq,
        pc_quality: pq,
      };

      const task = await api.createPhotogrammetryTask(payload);
      setActiveTask(task);
      setTaskHistory((prev) => [task, ...prev]);
      setSuccessMessage(`Photogrammetry task #${task.task_id.substring(0, 8)} submitted to cluster.`);
      setActiveTab("tasks");
    } catch (err: any) {
      setErrorMessage("Failed to start photogrammetry task: " + (err?.message || ""));
    } finally {
      setSubmittingTask(false);
    }
  };

  // 10. Actions: Cancel Task
  const handleCancelTask = async (taskId: string) => {
    try {
      setActionLoading(true);
      await api.cancelPhotogrammetryTask(taskId);
      setSuccessMessage("Task cancellation requested.");
      const updated = await api.getPhotogrammetryTask(taskId);
      setActiveTask(updated);
      setTaskHistory((prev) => prev.map((t) => (t.task_id === taskId ? updated : t)));
    } catch (err: any) {
      setErrorMessage("Failed to cancel task: " + (err?.message || ""));
    } finally {
      setActionLoading(false);
    }
  };

  // 11. Actions: Retry Task
  const handleRetryTask = async (taskId: string) => {
    try {
      setActionLoading(true);
      const retried = await api.retryPhotogrammetryTask(taskId);
      setActiveTask(retried);
      setTaskHistory((prev) => [retried, ...prev.filter((t) => t.task_id !== taskId)]);
      setSuccessMessage("Task restarted successfully.");
    } catch (err: any) {
      setErrorMessage("Failed to retry task: " + (err?.message || ""));
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#06140c] text-slate-100 flex flex-col selection:bg-emerald-600 selection:text-white">
      {/* Top Banner / Breadcrumb Bar */}
      <div className="bg-[#0a1f13] border-b border-emerald-900/50 px-4 sm:px-6 lg:px-8 py-3">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-emerald-400">
            <Layers className="w-4 h-4 text-emerald-400" />
            <span className="font-semibold uppercase tracking-wider text-emerald-400">Page 2</span>
            <ChevronRight className="w-3 h-3 text-emerald-700" />
            <span className="text-slate-300">WebODM Photogrammetry Processing Workspace</span>
          </div>

          {/* Quick cluster health pill */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-[#040e08] border border-emerald-900/60 rounded-full px-3 py-1">
              <span
                className={`w-2 h-2 rounded-full ${
                  clusterStatus?.cluster_status === "ONLINE"
                    ? "bg-emerald-400 animate-pulse"
                    : "bg-rose-500"
                }`}
              />
              <span className="text-[11px] font-medium text-slate-300">
                WebODM Cluster:{" "}
                <span
                  className={
                    clusterStatus?.cluster_status === "ONLINE"
                      ? "text-emerald-400 font-bold"
                      : "text-rose-400 font-bold"
                  }
                >
                  {clusterStatus?.cluster_status || "CHECKING"}
                </span>
              </span>
              <span className="text-[10px] text-slate-500">
                ({clusterStatus?.engine || "NodeODM"})
              </span>
            </div>

            <button
              onClick={loadInitialWorkspaceData}
              disabled={checkingCluster}
              className="p-1 hover:bg-emerald-900/40 rounded text-slate-400 hover:text-emerald-300 transition"
              title="Refresh cluster status"
            >
              <RotateCw className={`w-3.5 h-3.5 ${checkingCluster ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Main Header Area */}
      <div className="bg-gradient-to-b from-[#0a1f13] to-[#06140c] border-b border-emerald-900/40 px-4 sm:px-6 lg:px-8 py-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
              <span>WebODM Photogrammetry Workspace</span>
              <span className="text-xs font-semibold uppercase px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                Production Node
              </span>
            </h1>
            <p className="text-sm text-emerald-300/80 mt-1 max-w-2xl">
              Manage drone surveys, configure photogrammetry, monitor processing, and explore generated map products.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={() => setShowAddProjectModal(true)}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium text-sm flex items-center gap-2 shadow-lg shadow-emerald-900/40 transition active:scale-95"
            >
              <Plus className="w-4 h-4" />
              <span>Add Project</span>
            </button>

            <button
              onClick={() => handleLaunchTask()}
              disabled={submittingTask || !selectedSurveyId}
              className="px-4 py-2 bg-[#0d2a1a] hover:bg-[#123824] border border-emerald-700/60 text-emerald-300 rounded-lg font-medium text-sm flex items-center gap-2 transition disabled:opacity-50"
            >
              <Play className="w-4 h-4 text-emerald-400" />
              <span>{submittingTask ? "Submitting..." : "Start Processing"}</span>
            </button>
          </div>
        </div>

        {/* Workspace Tab Bar */}
        <div className="max-w-7xl mx-auto mt-6 flex items-center gap-1 overflow-x-auto pb-1 scrollbar-thin border-b border-emerald-900/40">
          <button
            onClick={() => setActiveTab("projects")}
            className={`px-4 py-2.5 text-xs sm:text-sm font-semibold rounded-t-lg transition flex items-center gap-2 shrink-0 ${
              activeTab === "projects"
                ? "bg-[#0d2417] text-emerald-300 border-t-2 border-emerald-500 border-x border-emerald-900/50"
                : "text-slate-400 hover:text-slate-200 hover:bg-emerald-950/20"
            }`}
          >
            <FolderOpen className="w-4 h-4 text-emerald-400" />
            <span>1. Projects Dashboard</span>
            <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800">
              {projects.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab("ingest")}
            className={`px-4 py-2.5 text-xs sm:text-sm font-semibold rounded-t-lg transition flex items-center gap-2 shrink-0 ${
              activeTab === "ingest"
                ? "bg-[#0d2417] text-emerald-300 border-t-2 border-emerald-500 border-x border-emerald-900/50"
                : "text-slate-400 hover:text-slate-200 hover:bg-emerald-950/20"
            }`}
          >
            <UploadCloud className="w-4 h-4 text-emerald-400" />
            <span>2. Select Images & GCP</span>
            {gcpAttached && (
              <span className="w-2 h-2 rounded-full bg-emerald-400" title="GCP Attached" />
            )}
          </button>

          <button
            onClick={() => setActiveTab("tasks")}
            className={`px-4 py-2.5 text-xs sm:text-sm font-semibold rounded-t-lg transition flex items-center gap-2 shrink-0 ${
              activeTab === "tasks"
                ? "bg-[#0d2417] text-emerald-300 border-t-2 border-emerald-500 border-x border-emerald-900/50"
                : "text-slate-400 hover:text-slate-200 hover:bg-emerald-950/20"
            }`}
          >
            <Activity className="w-4 h-4 text-emerald-400" />
            <span>3. Processing Tasks</span>
            {activeTask && (
              <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] bg-amber-950 text-amber-300 border border-amber-800 animate-pulse">
                Active
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab("presets")}
            className={`px-4 py-2.5 text-xs sm:text-sm font-semibold rounded-t-lg transition flex items-center gap-2 shrink-0 ${
              activeTab === "presets"
                ? "bg-[#0d2417] text-emerald-300 border-t-2 border-emerald-500 border-x border-emerald-900/50"
                : "text-slate-400 hover:text-slate-200 hover:bg-emerald-950/20"
            }`}
          >
            <Sliders className="w-4 h-4 text-emerald-400" />
            <span>4. Presets & Options</span>
          </button>

          <button
            onClick={() => setActiveTab("map")}
            className={`px-4 py-2.5 text-xs sm:text-sm font-semibold rounded-t-lg transition flex items-center gap-2 shrink-0 ${
              activeTab === "map"
                ? "bg-[#0d2417] text-emerald-300 border-t-2 border-emerald-500 border-x border-emerald-900/50"
                : "text-slate-400 hover:text-slate-200 hover:bg-emerald-950/20"
            }`}
          >
            <MapPin className="w-4 h-4 text-emerald-400" />
            <span>5. View Map & Outputs</span>
            {artifacts.length > 0 && (
              <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] bg-emerald-950 text-emerald-300 border border-emerald-800">
                {artifacts.length}
              </span>
            )}
          </button>

          {/* Admin Tabs */}
          {isAdmin && (
            <>
              <button
                onClick={() => setActiveTab("nodes")}
                className={`px-4 py-2.5 text-xs sm:text-sm font-semibold rounded-t-lg transition flex items-center gap-2 shrink-0 ${
                  activeTab === "nodes"
                    ? "bg-[#0d2417] text-emerald-300 border-t-2 border-emerald-500 border-x border-emerald-900/50"
                    : "text-slate-400 hover:text-slate-200 hover:bg-emerald-950/20"
                }`}
              >
                <Cpu className="w-4 h-4 text-emerald-400" />
                <span>6. Processing Nodes</span>
              </button>

              <button
                onClick={() => setActiveTab("diagnostics")}
                className={`px-4 py-2.5 text-xs sm:text-sm font-semibold rounded-t-lg transition flex items-center gap-2 shrink-0 ${
                  activeTab === "diagnostics"
                    ? "bg-[#0d2417] text-emerald-300 border-t-2 border-emerald-500 border-x border-emerald-900/50"
                    : "text-slate-400 hover:text-slate-200 hover:bg-emerald-950/20"
                }`}
              >
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <span>7. Diagnostics</span>
              </button>

              <button
                onClick={() => setActiveTab("admin")}
                className={`px-4 py-2.5 text-xs sm:text-sm font-semibold rounded-t-lg transition flex items-center gap-2 shrink-0 ${
                  activeTab === "admin"
                    ? "bg-[#0d2417] text-emerald-300 border-t-2 border-emerald-500 border-x border-emerald-900/50"
                    : "text-slate-400 hover:text-slate-200 hover:bg-emerald-950/20"
                }`}
              >
                <Zap className="w-4 h-4 text-amber-300" />
                <span>8. Administration & Lightning</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Notifications Bar */}
      <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 mt-4">
        {errorMessage && (
          <div className="p-3 mb-3 bg-rose-950/80 border border-rose-800/80 text-rose-200 rounded-lg text-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{errorMessage}</span>
            </div>
            <button onClick={() => setErrorMessage(null)} className="text-rose-400 hover:text-rose-200">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {successMessage && (
          <div className="p-3 mb-3 bg-emerald-950/80 border border-emerald-800/80 text-emerald-200 rounded-lg text-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>{successMessage}</span>
            </div>
            <button onClick={() => setSuccessMessage(null)} className="text-emerald-400 hover:text-emerald-200">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Content Area */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6">
        {/* ===================================================================
            TAB 1: PROJECTS DASHBOARD
        =================================================================== */}
        {activeTab === "projects" && (
          <div className="space-y-6">
            {/* Project Filters & Search Toolbar */}
            <div className="bg-[#0b2115] border border-emerald-900/50 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="relative flex-1 w-full">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-emerald-500/70" />
                <input
                  type="text"
                  placeholder="Search projects by name, description, farm, or survey code..."
                  value={projectSearchQuery}
                  onChange={(e) => setProjectSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 bg-[#040e08] border border-emerald-900/60 rounded-lg text-sm text-slate-100 placeholder-emerald-700/60 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center gap-3 w-full md:w-auto">
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <Filter className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Sort:</span>
                </div>
                <select
                  value={projectSortBy}
                  onChange={(e: any) => setProjectSortBy(e.target.value)}
                  className="bg-[#040e08] border border-emerald-900/60 text-slate-200 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"
                >
                  <option value="newest">Newest First</option>
                  <option value="name">Name (A-Z)</option>
                  <option value="tasks">Most Tasks</option>
                </select>

                <button
                  onClick={() => setShowAddProjectModal(true)}
                  className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition shrink-0"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Project</span>
                </button>
              </div>
            </div>

            {/* Projects Grid */}
            {loadingProjects ? (
              <div className="py-20 text-center text-slate-400 flex flex-col items-center justify-center gap-3">
                <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
                <span>Loading photogrammetry projects...</span>
              </div>
            ) : filteredProjects.length === 0 ? (
              <div className="bg-[#0b2115] border border-emerald-900/40 rounded-xl p-12 text-center">
                <div className="w-12 h-12 bg-emerald-950/80 rounded-full flex items-center justify-center mx-auto text-emerald-400 mb-4 border border-emerald-800">
                  <FolderOpen className="w-6 h-6" />
                </div>
                <h3 className="text-base font-bold text-white">No Photogrammetry Projects Found</h3>
                <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
                  {projectSearchQuery
                    ? `No projects matching "${projectSearchQuery}". Try adjusting your search query.`
                    : "Create your first photogrammetry project to organize drone surveys, GCPs, and orthophoto generation."}
                </p>
                <button
                  onClick={() => setShowAddProjectModal(true)}
                  className="mt-4 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold inline-flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  <span>Create Project</span>
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredProjects.map((p) => {
                  const isSelected = selectedProjectId === p.id;
                  return (
                    <div
                      key={p.id}
                      className={`bg-[#0b2115] border rounded-xl p-5 flex flex-col justify-between transition relative overflow-hidden group ${
                        isSelected
                          ? "border-emerald-500 ring-1 ring-emerald-500/40 shadow-lg shadow-emerald-950/60"
                          : "border-emerald-900/50 hover:border-emerald-700/60"
                      }`}
                    >
                      {/* Card Header */}
                      <div>
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <span className="text-[10px] font-mono text-emerald-400 block uppercase tracking-wider">
                              {p.survey_code || "Drone Project"}
                            </span>
                            <h3 className="text-base font-bold text-white group-hover:text-emerald-300 transition mt-0.5">
                              {p.name}
                            </h3>
                          </div>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                              p.latest_task_status === "COMPLETED"
                                ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                                : p.latest_task_status === "RUNNING"
                                ? "bg-amber-950 text-amber-300 border border-amber-800 animate-pulse"
                                : "bg-slate-900 text-slate-400 border border-slate-800"
                            }`}
                          >
                            {p.latest_task_status || "IDLE"}
                          </span>
                        </div>

                        {p.description && (
                          <p className="text-xs text-slate-300 mt-2 line-clamp-2">{p.description}</p>
                        )}

                        {/* Metadata Details */}
                        <div className="mt-4 pt-3 border-t border-emerald-900/40 space-y-1.5 text-xs text-slate-400">
                          {p.farm_name && (
                            <div className="flex items-center justify-between">
                              <span className="text-slate-500">Farm:</span>
                              <span className="text-slate-200 font-medium">{p.farm_name}</span>
                            </div>
                          )}
                          {p.field_name && (
                            <div className="flex items-center justify-between">
                              <span className="text-slate-500">Field:</span>
                              <span className="text-slate-200 font-medium">{p.field_name}</span>
                            </div>
                          )}
                          <div className="flex items-center justify-between">
                            <span className="text-slate-500">Tasks:</span>
                            <span className="text-emerald-400 font-semibold">{p.tasks_count} processed</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-slate-500">Created:</span>
                            <span>{new Date(p.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      </div>

                      {/* Card Actions */}
                      <div className="mt-5 pt-3 border-t border-emerald-900/40 flex items-center justify-between gap-2">
                        <button
                          onClick={() => {
                            setSelectedProjectId(p.id);
                            if (p.survey_id) setSelectedSurveyId(p.survey_id);
                            setActiveTab("tasks");
                          }}
                          className="px-3 py-1.5 bg-[#040e08] hover:bg-emerald-900/40 border border-emerald-800/60 text-emerald-300 rounded text-xs font-semibold flex items-center gap-1.5 transition"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>View Tasks</span>
                        </button>

                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => {
                              setSelectedProjectId(p.id);
                              if (p.survey_id) setSelectedSurveyId(p.survey_id);
                              setActiveTab("ingest");
                            }}
                            className="p-1.5 hover:bg-emerald-900/40 text-slate-400 hover:text-emerald-300 rounded transition"
                            title="Select Images and GCP"
                          >
                            <UploadCloud className="w-3.5 h-3.5" />
                          </button>

                          <button
                            onClick={() => handleDeleteProject(p.id, p.name)}
                            disabled={actionLoading}
                            className="p-1.5 hover:bg-rose-950/60 text-slate-400 hover:text-rose-400 rounded transition"
                            title="Delete Project"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ===================================================================
            TAB 2: SELECT IMAGES AND GCP
        =================================================================== */}
        {activeTab === "ingest" && (
          <div className="space-y-6">
            {/* Target Survey & Project Selection Header */}
            <div className="bg-[#0b2115] border border-emerald-900/50 rounded-xl p-5">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <UploadCloud className="w-5 h-5 text-emerald-400" />
                <span>Select Images & Ground Control Points (GCP)</span>
              </h2>
              <p className="text-xs text-slate-300 mt-1">
                Upload raw drone imagery and ingest surveyor GCP coordinate files formatted for OpenDroneMap.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div>
                  <label className="text-xs font-medium text-emerald-400 block mb-1">Target Flight Survey</label>
                  <select
                    value={selectedSurveyId}
                    onChange={(e) => setSelectedSurveyId(e.target.value)}
                    className="w-full bg-[#040e08] border border-emerald-900/60 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
                  >
                    <option value="">-- Choose Flight Survey --</option>
                    {surveys.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.survey_code} — {s.farm_name || "Farm"} ({s.sensor_type}, {s.files_count} files)
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-xs font-medium text-emerald-400 block mb-1">Associated WebODM Project</label>
                  <select
                    value={selectedProjectId}
                    onChange={(e) => setSelectedProjectId(e.target.value)}
                    className="w-full bg-[#040e08] border border-emerald-900/60 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
                  >
                    <option value="">-- Select Project (Optional) --</option>
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Split Ingestion: Raw Photos Drag & Drop vs GCP Ingestion */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Left Column: Raw Photographs Drag & Drop */}
              <div className="bg-[#0b2115] border border-emerald-900/50 rounded-xl p-5 flex flex-col justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <FileCheck className="w-4 h-4 text-emerald-400" />
                    <span>Raw Drone Photographs (JPEG / TIFF)</span>
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Select geotagged raw aerial photos captured during the flight.
                  </p>

                  {/* Dropzone */}
                  <div
                    onDragOver={(e) => {
                      e.preventDefault();
                      setIsDragOver(true);
                    }}
                    onDragLeave={() => setIsDragOver(false)}
                    onDrop={handleFileDrop}
                    className={`mt-4 border-2 border-dashed rounded-xl p-6 text-center transition cursor-pointer ${
                      isDragOver
                        ? "border-emerald-400 bg-emerald-950/40"
                        : "border-emerald-900/60 hover:border-emerald-700 bg-[#040e08]/60"
                    }`}
                    onClick={() => document.getElementById("photo-input")?.click()}
                  >
                    <input
                      id="photo-input"
                      type="file"
                      multiple
                      accept="image/jpeg,image/png,image/tiff"
                      className="hidden"
                      onChange={(e) => {
                        if (e.target.files) {
                          setSelectedFiles((prev) => [...prev, ...Array.from(e.target.files!)]);
                        }
                      }}
                    />
                    <UploadCloud className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-80" />
                    <span className="text-xs font-semibold text-slate-200 block">
                      Click to browse or drag & drop photographs
                    </span>
                    <span className="text-[11px] text-slate-500 mt-1 block">
                      Supported: JPG, JPEG, TIF, TIFF (Max 50MB per file)
                    </span>
                  </div>

                  {/* Selected Files Preview */}
                  {selectedFiles.length > 0 && (
                    <div className="mt-4">
                      <div className="flex items-center justify-between text-xs text-emerald-400 mb-2">
                        <span className="font-semibold">{selectedFiles.length} photos staged</span>
                        <button
                          onClick={() => setSelectedFiles([])}
                          className="text-slate-400 hover:text-rose-400"
                        >
                          Clear All
                        </button>
                      </div>
                      <div className="max-h-40 overflow-y-auto space-y-1 pr-1 scrollbar-thin">
                        {selectedFiles.map((f, i) => (
                          <div
                            key={i}
                            className="bg-[#040e08] px-3 py-1.5 rounded flex items-center justify-between text-xs text-slate-300 border border-emerald-950"
                          >
                            <span className="truncate max-w-[200px]">{f.name}</span>
                            <span className="text-[10px] text-slate-500">
                              {(f.size / (1024 * 1024)).toFixed(1)} MB
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Progress Bar */}
                  {isUploading && (
                    <div className="mt-4">
                      <div className="w-full bg-[#040e08] rounded-full h-2 overflow-hidden border border-emerald-950">
                        <div
                          className="bg-emerald-500 h-2 transition-all duration-300"
                          style={{ width: `${uploadProgress}%` }}
                        />
                      </div>
                      <span className="text-[11px] text-emerald-400 mt-1 block text-right">
                        Uploading: {uploadProgress}%
                      </span>
                    </div>
                  )}
                </div>

                <button
                  onClick={handleUploadPhotos}
                  disabled={isUploading || selectedFiles.length === 0}
                  className="mt-6 w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-semibold text-xs transition disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Ingesting Drone Imagery...</span>
                    </>
                  ) : (
                    <>
                      <UploadCloud className="w-4 h-4" />
                      <span>Upload {selectedFiles.length > 0 ? `(${selectedFiles.length}) Photos` : "Imagery"}</span>
                    </>
                  )}
                </button>
              </div>

              {/* Right Column: Ground Control Points (GCP) */}
              <div className="bg-[#0b2115] border border-emerald-900/50 rounded-xl p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-white flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-emerald-400" />
                        <span>Ground Control Points (GCP Interface)</span>
                      </h3>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Import surveyor RTK/GNSS reference points for millimeter georeferencing.
                      </p>
                    </div>

                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                        gcpAttached
                          ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                          : "bg-slate-900 text-slate-500 border border-slate-800"
                      }`}
                    >
                      {gcpAttached ? "GCP Ready" : "No GCP"}
                    </span>
                  </div>

                  {/* Format Notice */}
                  <div className="mt-3 p-2.5 bg-[#040e08] border border-emerald-950 rounded-lg text-[11px] text-slate-400">
                    <span className="text-emerald-400 font-semibold block mb-0.5">OpenDroneMap GCP Format:</span>
                    Line 1: CRS string (e.g. <code className="text-emerald-300">+proj=utm +zone=43 +datum=WGS84</code>)
                    <br />
                    Subsequent Lines: <code className="text-slate-300">X Y Z pixel_x pixel_y image_name</code>
                  </div>

                  {/* GCP Content Editor */}
                  <div className="mt-3">
                    <textarea
                      rows={6}
                      placeholder={`+proj=utm +zone=43 +datum=WGS84 +units=m +no_defs\n385200.12 2011400.45 540.23 1250 820 DJI_0001.JPG\n385220.89 2011410.60 541.02 1400 950 DJI_0002.JPG\n385240.34 2011430.12 540.88 1650 1100 DJI_0003.JPG`}
                      value={gcpContent}
                      onChange={(e) => setGcpContent(e.target.value)}
                      className="w-full p-2.5 bg-[#040e08] border border-emerald-900/60 rounded-lg text-xs font-mono text-emerald-300 placeholder-slate-600 focus:outline-none focus:border-emerald-500"
                    />
                  </div>

                  {/* GCP Validation Result Preview */}
                  {gcpResult && (
                    <div
                      className={`mt-3 p-3 rounded-lg border text-xs ${
                        gcpResult.valid
                          ? "bg-emerald-950/40 border-emerald-800/80 text-emerald-300"
                          : "bg-rose-950/40 border-rose-800/80 text-rose-300"
                      }`}
                    >
                      <div className="flex items-center justify-between font-semibold">
                        <span>{gcpResult.valid ? "✓ Valid GCP Format" : "⚠ GCP Errors Detected"}</span>
                        <span>{gcpResult.point_count} Points</span>
                      </div>
                      {gcpResult.crs && <div className="text-[11px] mt-1 text-slate-300 font-mono">CRS: {gcpResult.crs}</div>}
                      {gcpResult.errors.length > 0 && (
                        <ul className="mt-1.5 list-disc list-inside text-rose-300 text-[11px]">
                          {gcpResult.errors.map((err, i) => (
                            <li key={i}>{err}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}
                </div>

                <div className="mt-6 flex items-center gap-3">
                  <button
                    onClick={handleValidateGcp}
                    disabled={validatingGcp || !gcpContent.trim()}
                    className="flex-1 py-2.5 bg-[#040e08] hover:bg-[#071a10] border border-emerald-700/60 text-emerald-300 rounded-lg font-semibold text-xs transition disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {validatingGcp ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                    <span>Verify & Validate GCP</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ===================================================================
            TAB 3: PROCESSING TASKS & REAL-TIME MONITORING
        =================================================================== */}
        {activeTab === "tasks" && (
          <div className="space-y-6">
            {/* Active Task Hero Card */}
            {activeTask && (
              <div className="bg-gradient-to-r from-[#0a2315] to-[#06180e] border border-emerald-700/60 rounded-xl p-5 shadow-xl">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-emerald-400">
                        Task #{activeTask.task_id.substring(0, 8)}
                      </span>
                      <StatusBadge status={activeTask.status} />
                      <span className="text-xs text-slate-400">
                        Preset: <strong className="text-emerald-300">{activeTask.resolution_preset}</strong>
                      </span>
                    </div>
                    <h2 className="text-lg font-bold text-white mt-1">
                      {activeTask.current_stage || "Processing Stage"}
                    </h2>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setShowLogDrawer(true)}
                      className="px-3 py-1.5 bg-[#040e08] hover:bg-emerald-950/60 border border-emerald-800 text-emerald-300 rounded text-xs font-semibold flex items-center gap-1.5 transition"
                    >
                      <Terminal className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Live Console ({logs.length})</span>
                    </button>

                    {["RUNNING", "PREPARING", "UPLOADING", "QUEUED"].includes(activeTask.status) && (
                      <button
                        onClick={() => handleCancelTask(activeTask.task_id)}
                        disabled={actionLoading}
                        className="px-3 py-1.5 bg-rose-950/60 hover:bg-rose-900 border border-rose-800 text-rose-200 rounded text-xs font-semibold flex items-center gap-1.5 transition"
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        <span>Cancel Task</span>
                      </button>
                    )}

                    {["FAILED", "CANCELLED"].includes(activeTask.status) && (
                      <button
                        onClick={() => handleRetryTask(activeTask.task_id)}
                        disabled={actionLoading}
                        className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold flex items-center gap-1.5 transition"
                      >
                        <RotateCw className="w-3.5 h-3.5" />
                        <span>Retry Task</span>
                      </button>
                    )}

                    {activeTask.status === "COMPLETED" && (
                      <button
                        onClick={() => setActiveTab("map")}
                        className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold flex items-center gap-1.5 transition"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>View Map</span>
                      </button>
                    )}
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="mt-4">
                  <div className="flex justify-between text-xs text-slate-300 mb-1">
                    <span>Reconstruction Progress</span>
                    <span className="font-bold text-emerald-400">{activeTask.progress_percent}%</span>
                  </div>
                  <div className="w-full bg-[#040e08] rounded-full h-2.5 overflow-hidden border border-emerald-950">
                    <div
                      className="bg-emerald-500 h-2.5 transition-all duration-500 ease-out"
                      style={{ width: `${activeTask.progress_percent}%` }}
                    />
                  </div>
                </div>

                {/* Stages Indicator */}
                <div className="mt-4 pt-3 border-t border-emerald-900/40 grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] text-slate-400">
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Photos & GCP Load</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2
                      className={`w-3.5 h-3.5 ${activeTask.progress_percent >= 30 ? "text-emerald-400" : "text-slate-600"}`}
                    />
                    <span>Structure from Motion</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2
                      className={`w-3.5 h-3.5 ${activeTask.progress_percent >= 65 ? "text-emerald-400" : "text-slate-600"}`}
                    />
                    <span>DEM / DSM Elevation</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2
                      className={`w-3.5 h-3.5 ${activeTask.progress_percent >= 90 ? "text-emerald-400" : "text-slate-600"}`}
                    />
                    <span>Orthophoto Stitch</span>
                  </div>
                </div>
              </div>
            )}

            {/* Tasks History Table */}
            <div className="bg-[#0b2115] border border-emerald-900/50 rounded-xl overflow-hidden">
              <div className="p-4 border-b border-emerald-900/50 flex flex-wrap items-center justify-between gap-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Activity className="w-4 h-4 text-emerald-400" />
                  <span>Task History & Queue</span>
                </h3>

                <div className="flex items-center gap-2 text-xs">
                  <span className="text-slate-400">Filter Status:</span>
                  <select
                    value={taskStatusFilter}
                    onChange={(e) => setTaskStatusFilter(e.target.value)}
                    className="bg-[#040e08] border border-emerald-900/60 rounded px-2.5 py-1 text-slate-200 text-xs focus:outline-none focus:border-emerald-500"
                  >
                    <option value="ALL">All Statuses</option>
                    <option value="COMPLETED">Completed</option>
                    <option value="RUNNING">Running</option>
                    <option value="FAILED">Failed</option>
                    <option value="CANCELLED">Cancelled</option>
                  </select>
                </div>
              </div>

              {filteredTasks.length === 0 ? (
                <div className="p-10 text-center text-slate-400 text-xs">
                  No photogrammetry tasks recorded for this survey.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-[#07180e] text-emerald-400 border-b border-emerald-900/50 uppercase tracking-wider text-[10px]">
                      <tr>
                        <th className="py-3 px-4">Task ID</th>
                        <th className="py-3 px-4">Preset</th>
                        <th className="py-3 px-4">Status</th>
                        <th className="py-3 px-4">Progress</th>
                        <th className="py-3 px-4">Artifacts</th>
                        <th className="py-3 px-4">Created</th>
                        <th className="py-3 px-4 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-emerald-950 text-slate-300">
                      {filteredTasks.map((t) => (
                        <tr
                          key={t.task_id}
                          onClick={() => setActiveTask(t)}
                          className={`hover:bg-emerald-950/30 cursor-pointer transition ${
                            activeTask?.task_id === t.task_id ? "bg-emerald-950/50" : ""
                          }`}
                        >
                          <td className="py-3 px-4 font-mono text-emerald-300 font-medium">
                            #{t.task_id.substring(0, 8)}
                          </td>
                          <td className="py-3 px-4 font-medium">{t.resolution_preset}</td>
                          <td className="py-3 px-4">
                            <StatusBadge status={t.status} />
                          </td>
                          <td className="py-3 px-4">
                            <span className="font-semibold text-white">{t.progress_percent}%</span>
                          </td>
                          <td className="py-3 px-4">
                            <span className="px-1.5 py-0.5 rounded bg-[#040e08] border border-emerald-900 text-emerald-400">
                              {t.generated_products_count} maps
                            </span>
                          </td>
                          <td className="py-3 px-4 text-slate-400">
                            {t.started_at ? new Date(t.started_at).toLocaleTimeString() : "Pending"}
                          </td>
                          <td className="py-3 px-4 text-right space-x-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setActiveTask(t);
                                setShowLogDrawer(true);
                              }}
                              className="text-emerald-400 hover:text-emerald-200"
                              title="View Terminal Logs"
                            >
                              Logs
                            </button>
                            {t.status === "COMPLETED" && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setActiveTask(t);
                                  setActiveTab("map");
                                }}
                                className="text-emerald-300 hover:underline font-semibold"
                              >
                                View Map
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Collapsible Console Log Drawer */}
            {showLogDrawer && (
              <div className="bg-[#030d07] border border-emerald-900/80 rounded-xl overflow-hidden shadow-2xl">
                <div className="bg-[#07180e] px-4 py-2.5 border-b border-emerald-900/60 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs font-mono font-semibold text-emerald-300">
                      ODM Execution Console — Task #{activeTask?.task_id.substring(0, 8)}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 text-xs">
                    <label className="flex items-center gap-1.5 text-slate-400 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={autoScrollLogs}
                        onChange={(e) => setAutoScrollLogs(e.target.checked)}
                        className="rounded border-emerald-800 text-emerald-500 focus:ring-0"
                      />
                      <span>Auto-scroll</span>
                    </label>

                    <button
                      onClick={() => setShowLogDrawer(false)}
                      className="text-slate-400 hover:text-slate-200"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div
                  ref={logTerminalRef}
                  className="p-4 h-72 overflow-y-auto font-mono text-[11px] leading-relaxed space-y-1 text-slate-300 scrollbar-thin"
                >
                  {logs.length === 0 ? (
                    <div className="text-slate-600 italic">No execution console records received yet.</div>
                  ) : (
                    logs.map((log) => (
                      <div key={log.id} className="flex items-start gap-2">
                        <span className="text-slate-600 select-none">
                          {new Date(log.logged_at).toLocaleTimeString()}
                        </span>
                        <span
                          className={`font-bold select-none ${
                            log.log_level === "ERROR"
                              ? "text-rose-400"
                              : log.log_level === "WARNING"
                              ? "text-amber-400"
                              : "text-emerald-500"
                          }`}
                        >
                          [{log.log_level}]
                        </span>
                        <span className="text-slate-200">{log.message}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ===================================================================
            TAB 4: PROCESSING PRESETS & OPTIONS
        =================================================================== */}
        {activeTab === "presets" && (
          <div className="space-y-6">
            <div className="bg-[#0b2115] border border-emerald-900/50 rounded-xl p-5">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Sliders className="w-5 h-5 text-emerald-400" />
                <span>Agricultural Photogrammetry Presets</span>
              </h2>
              <p className="text-xs text-slate-300 mt-1">
                Select an optimized pipeline preset tuned for agricultural drone surveys, canopy heights, and multispectral analysis.
              </p>

              {/* 4 Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-5">
                {/* 1. Fast Orthophoto */}
                <div
                  onClick={() => setPreset("fast")}
                  className={`bg-[#040e08] border rounded-xl p-4 cursor-pointer transition flex flex-col justify-between ${
                    preset === "fast"
                      ? "border-emerald-400 ring-1 ring-emerald-400 bg-emerald-950/20"
                      : "border-emerald-950 hover:border-emerald-800"
                  }`}
                >
                  <div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-900 text-slate-300 border border-slate-800">
                      Fast 2D Preview
                    </span>
                    <h3 className="text-sm font-bold text-white mt-2">Fast Orthophoto</h3>
                    <p className="text-xs text-slate-400 mt-1">
                      Rapid 2D boundary inspection. Skips dense DSM to deliver orthomosaics in under 10 minutes.
                    </p>
                    <div className="mt-3 text-[11px] text-emerald-400 space-y-1">
                      <div>• Target GSD: ~5.0 cm/px</div>
                      <div>• DEM: Disabled</div>
                      <div>• Runtime: ~5-10 mins</div>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleLaunchTask("fast");
                    }}
                    className="mt-4 w-full py-2 bg-emerald-700 hover:bg-emerald-600 text-white rounded text-xs font-semibold"
                  >
                    Run Fast Preset
                  </button>
                </div>

                {/* 2. Precision High-Res */}
                <div
                  onClick={() => setPreset("precision")}
                  className={`bg-[#040e08] border rounded-xl p-4 cursor-pointer transition flex flex-col justify-between ${
                    preset === "precision"
                      ? "border-emerald-400 ring-1 ring-emerald-400 bg-emerald-950/20"
                      : "border-emerald-950 hover:border-emerald-800"
                  }`}
                >
                  <div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-950 text-emerald-300 border border-emerald-800">
                      Recommended
                    </span>
                    <h3 className="text-sm font-bold text-white mt-2">Field Precision (High-Res)</h3>
                    <p className="text-xs text-slate-400 mt-1">
                      Standard agricultural survey. Produces high-resolution orthophoto, DSM canopy models, and DTM terrain.
                    </p>
                    <div className="mt-3 text-[11px] text-emerald-400 space-y-1">
                      <div>• Target GSD: ~2.5 cm/px</div>
                      <div>• DEM: DSM + DTM Enabled</div>
                      <div>• Point Cloud: Medium Density</div>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleLaunchTask("precision");
                    }}
                    className="mt-4 w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold"
                  >
                    Run Precision Preset
                  </button>
                </div>

                {/* 3. Multispectral */}
                <div
                  onClick={() => setPreset("multispectral")}
                  className={`bg-[#040e08] border rounded-xl p-4 cursor-pointer transition flex flex-col justify-between ${
                    preset === "multispectral"
                      ? "border-emerald-400 ring-1 ring-emerald-400 bg-emerald-950/20"
                      : "border-emerald-950 hover:border-emerald-800"
                  }`}
                >
                  <div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-purple-950 text-purple-300 border border-purple-800">
                      Multispectral
                    </span>
                    <h3 className="text-sm font-bold text-white mt-2">Multispectral Index</h3>
                    <p className="text-xs text-slate-400 mt-1">
                      Calibrated reflectance mapping for DJI Mavic 3M, RedEdge, or Sequoia sensors with sun sensor normalization.
                    </p>
                    <div className="mt-3 text-[11px] text-emerald-400 space-y-1">
                      <div>• Radiometric Cal: Active</div>
                      <div>• Band Alignment: Rigorous</div>
                      <div>• Ready for: NDVI, NDRE, SAVI</div>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleLaunchTask("multispectral");
                    }}
                    className="mt-4 w-full py-2 bg-purple-700 hover:bg-purple-600 text-white rounded text-xs font-semibold"
                  >
                    Run Multispectral
                  </button>
                </div>

                {/* 4. Custom GSD */}
                <div
                  onClick={() => setPreset("custom")}
                  className={`bg-[#040e08] border rounded-xl p-4 cursor-pointer transition flex flex-col justify-between ${
                    preset === "custom"
                      ? "border-emerald-400 ring-1 ring-emerald-400 bg-emerald-950/20"
                      : "border-emerald-950 hover:border-emerald-800"
                  }`}
                >
                  <div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-950 text-amber-300 border border-amber-800">
                      Advanced
                    </span>
                    <h3 className="text-sm font-bold text-white mt-2">Custom Configuration</h3>
                    <p className="text-xs text-slate-400 mt-1">
                      Fine-tune ground sampling resolution, feature matching algorithms, and elevation interpolation parameters.
                    </p>
                    <div className="mt-3 text-[11px] text-emerald-400 space-y-1">
                      <div>• Custom GSD Slider</div>
                      <div>• Quality Toggles</div>
                      <div>• Full Parameter Control</div>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setPreset("custom");
                    }}
                    className="mt-4 w-full py-2 bg-amber-700 hover:bg-amber-600 text-white rounded text-xs font-semibold"
                  >
                    Configure Custom
                  </button>
                </div>
              </div>

              {/* Custom Parameter Adjuster (Visible if preset === "custom") */}
              {preset === "custom" && (
                <div className="mt-6 p-4 bg-[#040e08] border border-emerald-900/80 rounded-xl space-y-4">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                    Advanced Parameter Tuning
                  </h4>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="text-xs text-slate-300 block mb-1">
                        Target GSD (cm/pixel): <strong className="text-emerald-400">{targetGsd} cm</strong>
                      </label>
                      <input
                        type="range"
                        min="1.0"
                        max="10.0"
                        step="0.5"
                        value={targetGsd}
                        onChange={(e) => setTargetGsd(parseFloat(e.target.value))}
                        className="w-full accent-emerald-500"
                      />
                    </div>

                    <div>
                      <label className="text-xs text-slate-300 block mb-1">Feature Matching Quality</label>
                      <select
                        value={featureQuality}
                        onChange={(e) => setFeatureQuality(e.target.value)}
                        className="w-full bg-[#0a2315] border border-emerald-900 rounded p-2 text-xs text-slate-200"
                      >
                        <option value="ultra">Ultra (Sub-pixel, Slower)</option>
                        <option value="high">High (Recommended)</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low (Fast)</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-xs text-slate-300 block mb-1">Point Cloud Density</label>
                      <select
                        value={pcQuality}
                        onChange={(e) => setPcQuality(e.target.value)}
                        className="w-full bg-[#0a2315] border border-emerald-900 rounded p-2 text-xs text-slate-200"
                      >
                        <option value="ultra">Ultra Dense</option>
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                      </select>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-6 pt-2 text-xs text-slate-300">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={generateDsm}
                        onChange={(e) => setGenerateDsm(e.target.checked)}
                        className="rounded border-emerald-800 text-emerald-500"
                      />
                      <span>Generate Digital Surface Model (DSM)</span>
                    </label>

                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={generateDtm}
                        onChange={(e) => setGenerateDtm(e.target.checked)}
                        className="rounded border-emerald-800 text-emerald-500"
                      />
                      <span>Generate Digital Terrain Model (DTM)</span>
                    </label>

                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={radiometricCal}
                        onChange={(e) => setRadiometricCal(e.target.checked)}
                        className="rounded border-emerald-800 text-emerald-500"
                      />
                      <span>Radiometric Reflectance Calibration</span>
                    </label>
                  </div>

                  <div className="pt-2">
                    <button
                      onClick={() => handleLaunchTask("custom")}
                      className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold"
                    >
                      Submit Custom Task
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ===================================================================
            TAB 5: VIEW MAP & OUTPUTS
        =================================================================== */}
        {activeTab === "map" && (
          <div className="space-y-6">
            <div className="bg-[#0b2115] border border-emerald-900/50 rounded-xl p-5">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                <div>
                  <h2 className="text-base font-bold text-white flex items-center gap-2">
                    <MapPin className="w-5 h-5 text-emerald-400" />
                    <span>View Map — Photogrammetry Reconstruction Outputs</span>
                  </h2>
                  <p className="text-xs text-slate-300 mt-1">
                    Explore Cloud-Optimized GeoTIFF (COG) orthophoto and digital elevation models rendered with MapLibre GL JS.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <Link
                    href="/portal/surveys"
                    className="px-3 py-1.5 bg-[#040e08] hover:bg-emerald-950/60 border border-emerald-800 text-emerald-300 rounded text-xs font-semibold flex items-center gap-1.5 transition"
                  >
                    <span>Full Map Portal</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>

              {/* Artifacts Deliverables List */}
              {artifacts.length === 0 ? (
                <div className="mt-6 p-10 bg-[#040e08] border border-emerald-950 rounded-xl text-center">
                  <div className="w-10 h-10 bg-emerald-950 rounded-full flex items-center justify-center mx-auto text-emerald-500 mb-2 border border-emerald-900">
                    <Layers className="w-5 h-5" />
                  </div>
                  <h4 className="text-sm font-semibold text-white">No Map Products Generated Yet</h4>
                  <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                    Submit and complete a photogrammetry task to generate orthophoto, DSM, and point cloud deliverables.
                  </p>
                </div>
              ) : (
                <div className="mt-5 space-y-4">
                  {/* Layer Tabs */}
                  <div className="flex items-center gap-2 border-b border-emerald-900/60 pb-2">
                    {artifacts.map((a) => (
                      <button
                        key={a.product_id}
                        onClick={() => setSelectedArtifact(a)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                          selectedArtifact?.product_id === a.product_id
                            ? "bg-emerald-600 text-white"
                            : "bg-[#040e08] text-slate-300 hover:text-emerald-300"
                        }`}
                      >
                        {a.product_type} ({a.crs_epsg})
                      </button>
                    ))}
                  </div>

                  {/* Active Artifact Metadata & Download Controls */}
                  {selectedArtifact && (
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3 bg-[#040e08] border border-emerald-950 p-4 rounded-xl text-xs">
                      <div>
                        <span className="text-slate-500 block">Product Type</span>
                        <span className="font-bold text-emerald-300">{selectedArtifact.product_type}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">CRS & Projection</span>
                        <span className="font-mono text-slate-200">{selectedArtifact.crs_epsg}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">Resolution</span>
                        <span className="text-slate-200">
                          {selectedArtifact.resolution_cm_px ? `${selectedArtifact.resolution_cm_px} cm/px` : "N/A"}
                        </span>
                      </div>
                      <div className="flex items-center md:justify-end">
                        <a
                          href={`/api/v1/maps/products/${selectedArtifact.product_id}/download`}
                          target="_blank"
                          rel="noreferrer"
                          className="px-3 py-1.5 bg-emerald-700 hover:bg-emerald-600 text-white rounded text-xs font-semibold flex items-center gap-1.5"
                        >
                          <Download className="w-3.5 h-3.5" />
                          <span>Download GeoTIFF</span>
                        </a>
                      </div>
                    </div>
                  )}

                  {/* Map Preview Simulation Frame */}
                  <div className="relative w-full h-96 bg-[#030d07] rounded-xl border border-emerald-900 overflow-hidden flex items-center justify-center">
                    <div className="absolute inset-0 bg-cover bg-center opacity-30 pointer-events-none" style={{ backgroundImage: "radial-gradient(#059669 1px, transparent 1px)", backgroundSize: "24px 24px" }} />
                    <div className="text-center z-10 p-6 bg-[#06140c]/90 border border-emerald-800/80 rounded-xl max-w-md shadow-2xl backdrop-blur-md">
                      <Sparkles className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
                      <h4 className="text-sm font-bold text-white">Interactive GeoTIFF Render Ready</h4>
                      <p className="text-xs text-slate-300 mt-1">
                        Displaying product: <strong className="text-emerald-300">{selectedArtifact?.product_type}</strong> ({selectedArtifact?.original_filename})
                      </p>
                      <div className="mt-4 flex items-center justify-center gap-2">
                        <Link
                          href="/portal/surveys"
                          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold"
                        >
                          Open in Precision MapLibre Viewer
                        </Link>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ===================================================================
            TAB 6: PROCESSING NODES (ADMIN)
        =================================================================== */}
        {activeTab === "nodes" && isAdmin && (
          <div className="space-y-6">
            <div className="bg-[#0b2115] border border-emerald-900/50 rounded-xl p-5">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold text-white flex items-center gap-2">
                    <Cpu className="w-5 h-5 text-emerald-400" />
                    <span>Processing Nodes & Cluster Capacity</span>
                  </h2>
                  <p className="text-xs text-slate-300 mt-1">
                    Live telemetry from connected WebODM / NodeODM worker instances executing photogrammetry pipelines.
                  </p>
                </div>

                <button
                  onClick={() => {
                    setLoadingNodes(true);
                    api
                      .getProcessingNodes()
                      .then((res) => setNodes(res.nodes))
                      .finally(() => setLoadingNodes(false));
                  }}
                  className="px-3 py-1.5 bg-[#040e08] hover:bg-emerald-950/60 border border-emerald-800 text-emerald-300 rounded text-xs font-semibold flex items-center gap-1.5 transition"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loadingNodes ? "animate-spin" : ""}`} />
                  <span>Refresh Telemetry</span>
                </button>
              </div>

              {loadingNodes ? (
                <div className="py-16 text-center text-slate-400 flex flex-col items-center justify-center gap-2">
                  <Loader2 className="w-6 h-6 text-emerald-400 animate-spin" />
                  <span>Probing processing node status...</span>
                </div>
              ) : nodes.length === 0 ? (
                <div className="mt-6 p-8 bg-[#040e08] border border-emerald-950 rounded-xl text-center">
                  <p className="text-xs text-slate-400">
                    No remote cluster nodes reported. NodeODM is configured to execute on primary server host:{" "}
                    <code className="text-emerald-400">http://localhost:3001</code>
                  </p>
                </div>
              ) : (
                <div className="mt-5 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {nodes.map((node) => (
                    <div
                      key={node.id}
                      className="bg-[#040e08] border border-emerald-950 rounded-xl p-4 space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-white">{node.name}</span>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            node.online
                              ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                              : "bg-rose-950 text-rose-300 border border-rose-800"
                          }`}
                        >
                          {node.online ? "Online" : "Offline"}
                        </span>
                      </div>

                      <div className="space-y-1.5 text-xs text-slate-400">
                        <div className="flex justify-between">
                          <span>Endpoint:</span>
                          <span className="font-mono text-slate-300">
                            {node.hostname}:{node.port}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Task Queue:</span>
                          <span className="font-bold text-emerald-400">{node.task_queue_count} queued</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Available RAM:</span>
                          <span className="text-slate-200">
                            {node.available_memory_gb ? `${node.available_memory_gb} GB` : "N/A"}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Engine:</span>
                          <span>{node.engine} {node.version || ""}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ===================================================================
            TAB 7: DIAGNOSTICS (ADMIN)
        =================================================================== */}
        {activeTab === "diagnostics" && isAdmin && (
          <div className="space-y-6">
            <div className="bg-[#0b2115] border border-emerald-900/50 rounded-xl p-5">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold text-white flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-amber-400" />
                    <span>System Photogrammetry Diagnostics Probe</span>
                  </h2>
                  <p className="text-xs text-slate-300 mt-1">
                    End-to-end connectivity verification across WebODM cluster, storage engine, PostgreSQL/PostGIS, and Redis Celery queues.
                  </p>
                </div>

                <button
                  onClick={() => {
                    setLoadingDiagnostics(true);
                    api
                      .getPhotogrammetryDiagnostics()
                      .then((res) => setDiagnostics(res))
                      .finally(() => setLoadingDiagnostics(false));
                  }}
                  className="px-3 py-1.5 bg-[#040e08] hover:bg-emerald-950/60 border border-emerald-800 text-emerald-300 rounded text-xs font-semibold flex items-center gap-1.5 transition"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loadingDiagnostics ? "animate-spin" : ""}`} />
                  <span>Execute Health Probe</span>
                </button>
              </div>

              {loadingDiagnostics ? (
                <div className="py-16 text-center text-slate-400 flex flex-col items-center justify-center gap-2">
                  <Loader2 className="w-6 h-6 text-amber-400 animate-spin" />
                  <span>Executing comprehensive diagnostic probe...</span>
                </div>
              ) : diagnostics ? (
                <div className="mt-5 space-y-6">
                  {/* Status Matrix */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-[#040e08] border border-emerald-950 p-4 rounded-xl">
                      <span className="text-[11px] text-slate-500 uppercase tracking-wider block">WebODM Engine</span>
                      <span
                        className={`text-base font-bold mt-1 block ${
                          diagnostics.webodm_status === "HEALTHY" ? "text-emerald-400" : "text-rose-400"
                        }`}
                      >
                        {diagnostics.webodm_status}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono mt-1 block">
                        Latency: {diagnostics.webodm_latency_ms ? `${diagnostics.webodm_latency_ms} ms` : "Offline"}
                      </span>
                    </div>

                    <div className="bg-[#040e08] border border-emerald-950 p-4 rounded-xl">
                      <span className="text-[11px] text-slate-500 uppercase tracking-wider block">Storage Provider</span>
                      <span className="text-base font-bold text-emerald-400 mt-1 block">
                        {diagnostics.storage_status}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono mt-1 block">
                        Provider: {diagnostics.storage_provider}
                      </span>
                    </div>

                    <div className="bg-[#040e08] border border-emerald-950 p-4 rounded-xl">
                      <span className="text-[11px] text-slate-500 uppercase tracking-wider block">PostgreSQL / PostGIS</span>
                      <span className="text-base font-bold text-emerald-400 mt-1 block">
                        {diagnostics.database_status}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono mt-1 block">Port 5434 / PostGIS 3.4</span>
                    </div>

                    <div className="bg-[#040e08] border border-emerald-950 p-4 rounded-xl">
                      <span className="text-[11px] text-slate-500 uppercase tracking-wider block">Redis / Celery</span>
                      <span className="text-base font-bold text-emerald-400 mt-1 block">
                        {diagnostics.redis_status}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono mt-1 block">Port 6380 / Worker Broker</span>
                    </div>
                  </div>

                  {/* Issues and Recommendations */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-[#040e08] border border-rose-950/60 p-4 rounded-xl">
                      <h4 className="text-xs font-bold text-rose-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
                        <span>Identified Issues ({diagnostics.issues.length})</span>
                      </h4>
                      {diagnostics.issues.length === 0 ? (
                        <div className="text-xs text-emerald-400">No active system issues identified.</div>
                      ) : (
                        <ul className="space-y-1.5 text-xs text-rose-200/90 list-disc list-inside">
                          {diagnostics.issues.map((iss, i) => (
                            <li key={i}>{iss}</li>
                          ))}
                        </ul>
                      )}
                    </div>

                    <div className="bg-[#040e08] border border-emerald-950 p-4 rounded-xl">
                      <h4 className="text-xs font-bold text-emerald-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Operational Runbook Recommendations</span>
                      </h4>
                      {diagnostics.recommendations.length === 0 ? (
                        <div className="text-xs text-slate-400">All systems operating within normal parameters.</div>
                      ) : (
                        <ul className="space-y-1.5 text-xs text-emerald-300/90 list-disc list-inside">
                          {diagnostics.recommendations.map((rec, i) => (
                            <li key={i}>{rec}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        )}

        {/* ===================================================================
            TAB 8: ADMINISTRATION & WEBODM LIGHTNING (ADMIN)
        =================================================================== */}
        {activeTab === "admin" && isAdmin && (
          <div className="space-y-6">
            {/* Administration Config Card */}
            <div className="bg-[#0b2115] border border-emerald-900/50 rounded-xl p-5">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <span>WebODM Administration & Server Configuration</span>
              </h2>
              <p className="text-xs text-slate-300 mt-1">
                Backend parameters governing OpenDroneMap tasks, retry thresholds, and worker limits.
              </p>

              {adminConfig && (
                <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
                  <div className="bg-[#040e08] p-3 rounded border border-emerald-950">
                    <span className="text-slate-500 block">WebODM Host API</span>
                    <span className="font-mono text-emerald-300">{adminConfig.api_url}</span>
                  </div>
                  <div className="bg-[#040e08] p-3 rounded border border-emerald-950">
                    <span className="text-slate-500 block">Default Timeout</span>
                    <span className="font-mono text-slate-200">{adminConfig.timeout_seconds} seconds</span>
                  </div>
                  <div className="bg-[#040e08] p-3 rounded border border-emerald-950">
                    <span className="text-slate-500 block">Max Retries</span>
                    <span className="font-mono text-slate-200">{adminConfig.max_retries} attempts</span>
                  </div>
                  <div className="bg-[#040e08] p-3 rounded border border-emerald-950">
                    <span className="text-slate-500 block">Storage Engine</span>
                    <span className="font-mono text-emerald-300">{adminConfig.storage_provider}</span>
                  </div>
                  <div className="bg-[#040e08] p-3 rounded border border-emerald-950">
                    <span className="text-slate-500 block">Poll Interval</span>
                    <span className="font-mono text-slate-200">{adminConfig.poll_interval_seconds} seconds</span>
                  </div>
                  <div className="bg-[#040e08] p-3 rounded border border-emerald-950">
                    <span className="text-slate-500 block">Supported Presets</span>
                    <span className="text-slate-200">{adminConfig.supported_presets.join(", ")}</span>
                  </div>
                </div>
              )}
            </div>

            {/* WebODM Lightning Investigation Card */}
            <div className="bg-gradient-to-br from-[#0c2617] to-[#041109] border border-amber-600/40 rounded-xl p-6 shadow-xl">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-300 shrink-0">
                  <Zap className="w-6 h-6" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-amber-400">
                      Technical Investigation & Architecture Notice
                    </span>
                    <span className="px-2 py-0.2 rounded text-[10px] font-semibold bg-amber-950 text-amber-300 border border-amber-800">
                      Feature Analysis
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-white mt-1">WebODM Lightning Cloud Service</h3>
                  <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                    The <strong>Lightning</strong> feature visible on the native WebODM desktop interface is OpenDroneMap's commercial cloud GPU acceleration subscription (hosted at <code className="text-amber-300">cloud.webodm.net</code>). It enables users to pay per-megapixel or subscription credits to offload processing to public cloud GPU nodes.
                  </p>

                  <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div className="bg-[#030d07] p-3 rounded-lg border border-emerald-950">
                      <span className="font-bold text-emerald-300 block mb-1">AgriDrone AutoMap Architecture:</span>
                      By default, AgriDrone AutoMap connects to self-hosted, private <strong>NodeODM</strong> instances. This ensures farmer imagery remains strictly on-premise, satisfies Indian data sovereignty guidelines, and incurs <strong>zero third-party credit costs</strong>.
                    </div>
                    <div className="bg-[#030d07] p-3 rounded-lg border border-amber-950">
                      <span className="font-bold text-amber-300 block mb-1">Optional Lightning Offloading:</span>
                      If cloud GPU bursting is required during peak sugarcane harvest surveys, administrators can input a WebODM Lightning API key into the cluster node manager to seamlessly offload tasks to cloud GPUs.
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Add Project Modal */}
      {showAddProjectModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0a1e13] border border-emerald-700/60 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
            <div className="flex items-center justify-between pb-3 border-b border-emerald-900/60">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <FolderOpen className="w-5 h-5 text-emerald-400" />
                <span>Create Photogrammetry Project</span>
              </h3>
              <button
                onClick={() => setShowAddProjectModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateProject} className="mt-4 space-y-4">
              <div>
                <label className="text-xs font-semibold text-emerald-400 block mb-1">Project Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Baramati Sugarcane Survey 2026"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  className="w-full bg-[#040e08] border border-emerald-900/60 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-emerald-400 block mb-1">Description (Optional)</label>
                <textarea
                  rows={3}
                  placeholder="Notes on survey flight parameters, crop stages, or camera sensor..."
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  className="w-full bg-[#040e08] border border-emerald-900/60 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-emerald-400 block mb-1">Associate Farm</label>
                  <select
                    value={newProjectFarmId}
                    onChange={(e) => setNewProjectFarmId(e.target.value)}
                    className="w-full bg-[#040e08] border border-emerald-900/60 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                  >
                    <option value="">-- No Farm --</option>
                    {farms.map((f) => (
                      <option key={f.id} value={f.id}>
                        {f.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-emerald-400 block mb-1">Associate Flight</label>
                  <select
                    value={selectedSurveyId}
                    onChange={(e) => setSelectedSurveyId(e.target.value)}
                    className="w-full bg-[#040e08] border border-emerald-900/60 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                  >
                    <option value="">-- Select Flight --</option>
                    {surveys.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.survey_code}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="pt-3 border-t border-emerald-900/60 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowAddProjectModal(false)}
                  className="px-4 py-2 bg-[#040e08] hover:bg-emerald-950/60 text-slate-300 rounded-lg text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingProject}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition disabled:opacity-50"
                >
                  {creatingProject ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
                  <span>{creatingProject ? "Creating..." : "Create Project"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
