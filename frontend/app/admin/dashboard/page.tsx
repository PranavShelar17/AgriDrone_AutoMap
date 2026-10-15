"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import {
  UploadCloud,
  FolderUp,
  Sprout,
  Calendar,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  ArrowRight,
  Plus,
  Layers,
  Trash2,
  FileText,
  Database,
  MapPin,
  RefreshCw,
  X,
  ShieldCheck,
  Check,
} from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import { AlertBanner } from "@/components/AlertBanner";
import {
  api,
  FarmItem,
  FieldItem,
  SurveyItem,
  SurveyFileItem,
  DashboardStatsResponse,
  ApiClientError,
} from "@/lib/api";

export default function IngestionPage() {
  // Navigation & Upload mode
  const [uploadMode, setUploadMode] = useState<"raw_photos" | "geotiff">("raw_photos");

  // Core Entity State
  const [stats, setStats] = useState<DashboardStatsResponse | null>(null);
  const [farms, setFarms] = useState<FarmItem[]>([]);
  const [fields, setFields] = useState<FieldItem[]>([]);
  const [surveys, setSurveys] = useState<SurveyItem[]>([]);

  const [selectedFarmId, setSelectedFarmId] = useState<string>("");
  const [selectedFieldId, setSelectedFieldId] = useState<string>("");
  const [selectedSurveyId, setSelectedSurveyId] = useState<string>("");
  const [surveyFiles, setSurveyFiles] = useState<SurveyFileItem[]>([]);

  // Async UI State
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [lastValidation, setLastValidation] = useState<any | null>(null);

  // Modals
  const [isFarmModalOpen, setIsFarmModalOpen] = useState(false);
  const [newFarmName, setNewFarmName] = useState("");
  const [newFarmVillage, setNewFarmVillage] = useState("");
  const [newFarmDistrict, setNewFarmDistrict] = useState("");
  const [newFarmState, setNewFarmState] = useState("");

  const [isFieldModalOpen, setIsFieldModalOpen] = useState(false);
  const [newFieldName, setNewFieldName] = useState("");
  const [newFieldCrop, setNewFieldCrop] = useState("Sugarcane Co 86032");
  const [newFieldArea, setNewFieldArea] = useState(12.5);

  const [isSurveyModalOpen, setIsSurveyModalOpen] = useState(false);
  const [newSurveyDate, setNewSurveyDate] = useState(new Date().toISOString().split("T")[0]);
  const [newSurveyDrone, setNewSurveyDrone] = useState("DJI Mavic 3 Enterprise");
  const [newSurveySensor, setNewSurveySensor] = useState("RGB");
  const [newSurveyAltitude, setNewSurveyAltitude] = useState(80);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // 1. Fetch Dashboard Stats
  const loadStats = useCallback(async () => {
    try {
      const data = await api.getDashboardStats();
      setStats(data);
    } catch (err) {
      console.error("Failed to load dashboard statistics:", err);
    }
  }, []);

  // 2. Fetch Farms
  const loadFarms = useCallback(async () => {
    try {
      const res = await api.getFarms({ limit: 100 });
      setFarms(res.items);
      if (res.items.length > 0 && !selectedFarmId) {
        setSelectedFarmId(res.items[0].id);
      }
    } catch (err) {
      console.error("Failed to load farms:", err);
    }
  }, [selectedFarmId]);

  // Initial Load
  useEffect(() => {
    let mounted = true;
    const init = async () => {
      setIsLoading(true);
      await Promise.all([loadStats(), loadFarms()]);
      if (mounted) setIsLoading(false);
    };
    init();
    return () => {
      mounted = false;
    };
  }, [loadStats, loadFarms]);

  // 3. When Selected Farm changes, fetch its Fields
  useEffect(() => {
    if (!selectedFarmId) {
      setFields([]);
      setSelectedFieldId("");
      return;
    }
    const fetchFields = async () => {
      try {
        const data = await api.getFieldsForFarm(selectedFarmId);
        setFields(data);
        if (data.length > 0) {
          setSelectedFieldId(data[0].id);
        } else {
          setSelectedFieldId("");
        }
      } catch (err) {
        console.error("Failed to load fields for farm:", err);
      }
    };
    fetchFields();
  }, [selectedFarmId]);

  // 4. When Selected Field changes, fetch its Surveys
  useEffect(() => {
    if (!selectedFieldId) {
      setSurveys([]);
      setSelectedSurveyId("");
      return;
    }
    const fetchSurveys = async () => {
      try {
        const data = await api.getSurveys({ field_id: selectedFieldId, limit: 50 });
        setSurveys(data.items);
        if (data.items.length > 0) {
          setSelectedSurveyId(data.items[0].id);
        } else {
          setSelectedSurveyId("");
        }
      } catch (err) {
        console.error("Failed to load surveys for field:", err);
      }
    };
    fetchSurveys();
  }, [selectedFieldId]);

  // 5. When Selected Survey changes, fetch its Files
  const loadSurveyFiles = useCallback(async () => {
    if (!selectedSurveyId) {
      setSurveyFiles([]);
      return;
    }
    try {
      const data = await api.getSurveyFiles(selectedSurveyId);
      setSurveyFiles(data.items);
      if (data.items.length > 0) {
        const latestValid = data.items.find((f) => f.ingestion_status === "VALIDATED") || data.items[0];
        setLastValidation(latestValid);
      }
    } catch (err) {
      console.error("Failed to load survey files:", err);
    }
  }, [selectedSurveyId]);

  useEffect(() => {
    loadSurveyFiles();
  }, [loadSurveyFiles]);

  // Actions: Create Farm
  const handleCreateFarm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFarmName.trim()) return;
    try {
      const created = await api.createFarm({
        name: newFarmName.trim(),
        village: newFarmVillage.trim() || undefined,
        district: newFarmDistrict.trim() || undefined,
        state: newFarmState.trim() || undefined,
      });
      setFarms((prev) => [created, ...prev]);
      setSelectedFarmId(created.id);
      setIsFarmModalOpen(false);
      setNewFarmName("");
      setNewFarmVillage("");
      setNewFarmDistrict("");
      setNewFarmState("");
      setSuccessMessage(`Farm "${created.name}" registered successfully.`);
      loadStats();
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to create farm.");
    }
  };

  // Actions: Create Field
  const handleCreateField = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFarmId || !newFieldName.trim()) return;
    try {
      const created = await api.createField(selectedFarmId, {
        field_name: newFieldName.trim(),
        crop_type: newFieldCrop.trim() || undefined,
        area_hectares: Number(newFieldArea) || undefined,
      });
      setFields((prev) => [created, ...prev]);
      setSelectedFieldId(created.id);
      setIsFieldModalOpen(false);
      setNewFieldName("");
      setSuccessMessage(`Field "${created.field_name}" created successfully.`);
      loadStats();
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to create field.");
    }
  };

  // Actions: Create Survey
  const handleCreateSurvey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFieldId) return;
    try {
      const created = await api.createSurvey({
        field_id: selectedFieldId,
        flight_date: newSurveyDate,
        drone_model: newSurveyDrone,
        sensor_type: newSurveySensor,
        flight_altitude_m: Number(newSurveyAltitude),
      });
      setSurveys((prev) => [created, ...prev]);
      setSelectedSurveyId(created.id);
      setIsSurveyModalOpen(false);
      setSuccessMessage(`Survey mission "${created.survey_code}" created.`);
      loadStats();
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to create survey.");
    }
  };

  // Actions: Upload File
  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    if (!selectedSurveyId) {
      setErrorMessage("Please select or create a survey flight mission before uploading files.");
      return;
    }

    setIsUploading(true);
    setUploadProgress(20);
    setErrorMessage(null);
    setSuccessMessage(null);

    const file = files[0];
    try {
      setUploadProgress(45);
      const result = await api.uploadSurveyFile(selectedSurveyId, file, uploadMode);
      setUploadProgress(100);
      setLastValidation(result);

      if (result.ingestion_status === "VALIDATED") {
        setSuccessMessage(`File "${file.name}" validated and uploaded successfully! Route: ${result.workflow_route}`);
      } else {
        setErrorMessage(`File "${file.name}" rejected: ${result.validation_errors.join(", ")}`);
      }

      await loadSurveyFiles();
      await loadStats();
    } catch (err: any) {
      setErrorMessage(err.message || "Upload operation failed.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  // Actions: Delete File
  const handleDeleteFile = async (fileId: string, filename: string) => {
    if (!window.confirm(`Are you sure you want to delete file "${filename}"?`)) return;
    try {
      await api.deleteSurveyFile(fileId);
      setSuccessMessage(`File "${filename}" deleted.`);
      loadSurveyFiles();
      loadStats();
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to delete file.");
    }
  };

  const activeSurvey = surveys.find((s) => s.id === selectedSurveyId);
  const activeFarm = farms.find((f) => f.id === selectedFarmId);
  const activeField = fields.find((f) => f.id === selectedFieldId);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 mb-1">
            <span>Page 1 of 5</span>
            <span>&bull;</span>
            <span className="text-emerald-700 font-bold">Admin Dashboard</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Drone Image Ingestion & Survey Management
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Manage agricultural holdings, organize aerial survey flights, and ingest raw photography or GeoTIFF rasters.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              loadStats();
              loadFarms();
            }}
            className="btn-secondary text-xs flex items-center gap-1.5"
            title="Refresh database records"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
          <Link
            href="/admin/photogrammetry"
            className="btn-primary text-xs flex items-center gap-1.5"
          >
            <span>Proceed to WebODM</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Notifications */}
      {errorMessage && (
        <AlertBanner
          type="error"
          message={errorMessage}
          actionText="Dismiss"
          onAction={() => setErrorMessage(null)}
        />
      )}
      {successMessage && (
        <AlertBanner
          type="success"
          message={successMessage}
          actionText="Dismiss"
          onAction={() => setSuccessMessage(null)}
        />
      )}

      {/* Database KPI Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="card-base p-4">
          <span className="text-[11px] font-semibold text-slate-500 block">Registered Farms</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold text-slate-900">{stats?.total_farms ?? 0}</span>
            <span className="text-[10px] text-slate-400">estates</span>
          </div>
        </div>

        <div className="card-base p-4">
          <span className="text-[11px] font-semibold text-slate-500 block">Active Fields</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold text-slate-900">{stats?.total_fields ?? 0}</span>
            <span className="text-[10px] text-slate-400">parcels</span>
          </div>
        </div>

        <div className="card-base p-4">
          <span className="text-[11px] font-semibold text-slate-500 block">Surveys Logged</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold text-emerald-700">{stats?.total_surveys ?? 0}</span>
            <span className="text-[10px] text-slate-400">missions</span>
          </div>
        </div>

        <div className="card-base p-4">
          <span className="text-[11px] font-semibold text-slate-500 block">Total Datasets</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold text-slate-900">{stats?.total_datasets ?? 0}</span>
            <span className="text-[10px] text-slate-400">files</span>
          </div>
        </div>

        <div className="card-base p-4">
          <span className="text-[11px] font-semibold text-slate-500 block">Validated Datasets</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold text-emerald-600">{stats?.datasets_validated ?? 0}</span>
            <span className="text-[10px] text-emerald-600 font-medium">ready</span>
          </div>
        </div>

        <div className="card-base p-4">
          <span className="text-[11px] font-semibold text-slate-500 block">Failures / Rejected</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold text-rose-600">{stats?.datasets_rejected ?? 0}</span>
            <span className="text-[10px] text-rose-600 font-medium">attention</span>
          </div>
        </div>
      </div>

      {/* Row 1: Hierarchy Setup & Pre-Flight Validation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Card 1: Spatial Hierarchy & Flight Mission Setup */}
        <div className="card-base p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2 font-semibold text-sm text-slate-800">
              <Sprout className="w-4 h-4 text-emerald-600" />
              <span>Spatial Hierarchy &amp; Flight Setup</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setIsFarmModalOpen(true)}
                className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 flex items-center gap-1"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>New Farm</span>
              </button>
            </div>
          </div>

          <div className="space-y-3.5">
            {/* Target Farm */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-semibold text-slate-700">Target Farm</label>
                {activeFarm?.village && (
                  <span className="text-[11px] text-slate-400 flex items-center gap-1">
                    <MapPin className="w-3 h-3" />
                    {activeFarm.village}, {activeFarm.district || activeFarm.state}
                  </span>
                )}
              </div>
              <select
                value={selectedFarmId}
                onChange={(e) => setSelectedFarmId(e.target.value)}
                className="input-base w-full text-xs"
              >
                {farms.length === 0 ? (
                  <option value="">No farms registered — Click &apos;+ New Farm&apos; to add one</option>
                ) : (
                  farms.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.name} ({f.fields_count} fields, {f.surveys_count} surveys)
                    </option>
                  ))
                )}
              </select>
            </div>

            {/* Field Boundary */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-semibold text-slate-700">Field Boundary (PostGIS Polygon)</label>
                <button
                  type="button"
                  disabled={!selectedFarmId}
                  onClick={() => setIsFieldModalOpen(true)}
                  className="text-[11px] font-semibold text-emerald-700 hover:text-emerald-800 flex items-center gap-0.5 disabled:opacity-40"
                >
                  <Plus className="w-3 h-3" />
                  <span>New Field</span>
                </button>
              </div>
              <select
                value={selectedFieldId}
                onChange={(e) => setSelectedFieldId(e.target.value)}
                disabled={!selectedFarmId || fields.length === 0}
                className="input-base w-full text-xs disabled:bg-slate-50 disabled:text-slate-400"
              >
                {fields.length === 0 ? (
                  <option value="">No fields for this farm — Click &apos;+ New Field&apos; to create one</option>
                ) : (
                  fields.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.field_name} ({f.crop_type || "Unspecified Crop"}, {f.area_hectares ?? "--"} ha)
                    </option>
                  ))
                )}
              </select>
            </div>

            {/* Active Survey Mission Selector */}
            <div className="pt-2 border-t border-slate-100">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800">
                  <Calendar className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Flight Mission Association</span>
                </div>
                <button
                  type="button"
                  disabled={!selectedFieldId}
                  onClick={() => setIsSurveyModalOpen(true)}
                  className="text-[11px] font-semibold text-emerald-700 hover:text-emerald-800 flex items-center gap-0.5 disabled:opacity-40"
                >
                  <Plus className="w-3 h-3" />
                  <span>New Survey</span>
                </button>
              </div>

              <select
                value={selectedSurveyId}
                onChange={(e) => setSelectedSurveyId(e.target.value)}
                disabled={!selectedFieldId || surveys.length === 0}
                className="input-base w-full text-xs font-mono font-medium disabled:bg-slate-50 disabled:text-slate-400"
              >
                {surveys.length === 0 ? (
                  <option value="">No survey logged — Click &apos;+ New Survey&apos; to initialize one</option>
                ) : (
                  surveys.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.survey_code} &bull; {s.flight_date} &bull; {s.sensor_type} ({s.status})
                    </option>
                  ))
                )}
              </select>
            </div>

            {/* Active Survey Details Pill */}
            {activeSurvey && (
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
                <div className="flex items-center justify-between text-slate-700">
                  <span className="font-semibold">Survey Code:</span>
                  <span className="font-mono font-bold text-emerald-800">{activeSurvey.survey_code}</span>
                </div>
                <div className="flex items-center justify-between text-slate-600">
                  <span>Flight Drone / Sensor:</span>
                  <span>{activeSurvey.drone_model} &bull; {activeSurvey.sensor_type}</span>
                </div>
                <div className="flex items-center justify-between text-slate-600">
                  <span>Target Altitude:</span>
                  <span>{activeSurvey.flight_altitude_m ?? 80} m AGL</span>
                </div>
                <div className="flex items-center justify-between text-slate-600">
                  <span>Mission State:</span>
                  <StatusBadge status={activeSurvey.status} />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Card 2: Pre-Flight Metadata Extraction & Validation */}
        <div className="card-base p-6 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-3">
              <div className="flex items-center gap-2 font-semibold text-sm text-slate-800">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Server-Side Metadata Extraction &amp; Validation</span>
              </div>
              <span className="text-[11px] font-semibold text-slate-400 font-mono">Pillow &bull; ExifTags</span>
            </div>

            {lastValidation ? (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                    <span className="text-[11px] text-slate-500 font-medium block">Target CRS</span>
                    <strong className="text-xs text-slate-900 font-mono">
                      {lastValidation.validation_metadata?.crs_epsg || "EPSG:4326 (WGS84 Lat/Lon)"}
                    </strong>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                    <span className="text-[11px] text-slate-500 font-medium block">Resolution / Dimension</span>
                    <strong className="text-xs text-slate-900 font-mono">
                      {lastValidation.validation_metadata?.resolution_estimate ||
                        `${lastValidation.validation_metadata?.width ?? "--"} x ${lastValidation.validation_metadata?.height ?? "--"} px`}
                    </strong>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                    <span className="text-[11px] text-slate-500 font-medium block">Bands Detected</span>
                    <strong className="text-xs text-slate-900 font-mono">
                      {lastValidation.validation_metadata?.bands ?? 3} Channels ({lastValidation.validation_metadata?.color_mode || "RGB"})
                    </strong>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                    <span className="text-[11px] text-slate-500 font-medium block">Geotag Status</span>
                    <strong className="text-xs font-mono text-emerald-700">
                      {lastValidation.validation_metadata?.has_gps
                        ? `GPS Tagged (${lastValidation.validation_metadata?.gps_latitude}, ${lastValidation.validation_metadata?.gps_longitude})`
                        : "No GPS tags in file header"}
                    </strong>
                  </div>
                </div>

                {/* Eligibility Decision Badge */}
                <div
                  className={`p-3.5 rounded-lg border flex items-center justify-between ${
                    lastValidation.ingestion_status === "VALIDATED"
                      ? "bg-emerald-50 border-emerald-200"
                      : "bg-rose-50 border-rose-200"
                  }`}
                >
                  <div>
                    <span
                      className={`text-[10px] font-bold uppercase tracking-wider block ${
                        lastValidation.ingestion_status === "VALIDATED" ? "text-emerald-800" : "text-rose-800"
                      }`}
                    >
                      Ingestion Eligibility Decision
                    </span>
                    <span
                      className={`text-xs font-semibold ${
                        lastValidation.ingestion_status === "VALIDATED" ? "text-emerald-900" : "text-rose-900"
                      }`}
                    >
                      {lastValidation.workflow_route === "WEBODM_PHOTOGRAMMETRY"
                        ? "ELIGIBLE FOR WEBODM PHOTOGRAMMETRY (PAGE 2)"
                        : lastValidation.workflow_route === "DIRECT_ALGORITHM_GIS"
                        ? "ELIGIBLE FOR DIRECT ALGORITHM MULTI-MAP (PAGE 3)"
                        : `REJECTED: ${lastValidation.validation_errors?.[0] || "File validation failed"}`}
                    </span>
                  </div>
                  <StatusBadge status={lastValidation.ingestion_status} />
                </div>
              </div>
            ) : (
              <div className="h-44 flex flex-col items-center justify-center text-center p-4 border border-dashed border-slate-200 rounded-lg">
                <Database className="w-8 h-8 text-slate-300 mb-2" />
                <span className="text-xs font-semibold text-slate-700">No Image Ingested For Selected Survey</span>
                <span className="text-[11px] text-slate-400 mt-1 max-w-xs">
                  Upload raw drone photography or a GeoTIFF below to inspect projection, resolution, and EXIF coordinates.
                </span>
              </div>
            )}
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>
              Storage:{" "}
              <strong className="text-slate-700 font-mono">
                {stats?.storage_provider === "azure_blob"
                  ? "agridronestorage (Azure Private Container)"
                  : "local_dev (Local Storage Fallback)"}
              </strong>
            </span>
            <span className="flex items-center gap-1 text-emerald-700 font-medium">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Boundary Protected</span>
            </span>
          </div>
        </div>
      </div>

      {/* Row 2: Dual-Mode Upload Dropzone Card */}
      <div className="card-base p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <UploadCloud className="w-5 h-5 text-emerald-600" />
            <h2 className="text-sm font-bold text-slate-900">Upload Aerial Survey Data</h2>
          </div>
          {/* Mode Selector */}
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200">
            <button
              type="button"
              onClick={() => setUploadMode("raw_photos")}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                uploadMode === "raw_photos"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Mode A: Raw Drone Photos (Batch)
            </button>
            <button
              type="button"
              onClick={() => setUploadMode("geotiff")}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                uploadMode === "geotiff"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Mode B: Pre-Stitched GeoTIFF Raster
            </button>
          </div>
        </div>

        {/* Dropzone Container */}
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            handleFileUpload(e.dataTransfer.files);
          }}
          className="border-2 border-dashed border-slate-300 rounded-xl bg-slate-50/50 hover:bg-slate-50 p-8 text-center transition-colors"
        >
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            accept={uploadMode === "raw_photos" ? ".jpg,.jpeg,.tif,.tiff,.dng,.zip" : ".tif,.tiff"}
            onChange={(e) => handleFileUpload(e.target.files)}
          />

          <div className="max-w-md mx-auto space-y-3">
            <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-800">
                {uploadMode === "raw_photos"
                  ? "Drag and drop raw survey photography files here"
                  : "Drag and drop your pre-stitched orthomosaic GeoTIFF here"}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                {uploadMode === "raw_photos"
                  ? "Supported formats: .jpg, .jpeg, .tif, .tiff, .zip with EXIF GPS tags (Max 500 MB / upload)"
                  : "Supported formats: .tif, .tiff (GeoTIFF with EPSG CRS & ModelPixelScale tag, Max 500 MB)"}
              </p>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
              <button
                type="button"
                disabled={isUploading || !selectedSurveyId}
                onClick={() => fileInputRef.current?.click()}
                className="btn-primary text-xs disabled:opacity-50"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Uploading &amp; Validating ({uploadProgress}%)...</span>
                  </>
                ) : (
                  <>
                    <FolderUp className="w-3.5 h-3.5" />
                    <span>Browse &amp; Upload Flight Files</span>
                  </>
                )}
              </button>
            </div>

            {isUploading && (
              <div className="space-y-1.5 pt-4">
                <div className="flex justify-between text-xs font-medium text-slate-600">
                  <span>Streaming to Storage &amp; extracting metadata...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-emerald-600 h-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        <AlertBanner
          type="info"
          message="Notice: Pre-stitched GeoTIFF rasters with valid CRS and band mappings bypass WebODM photogrammetry (Page 2) and proceed directly to Algorithm Multi-Map Generation (Page 3)."
        />
      </div>

      {/* Row 3: Survey Ingestion & Eligibility Ledger */}
      <div className="card-base p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Survey Ingestion &amp; Eligibility Ledger</h2>
            <p className="text-xs text-slate-500">
              Live records of ingested datasets in database for {activeSurvey ? activeSurvey.survey_code : "all surveys"}.
            </p>
          </div>
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
            {surveyFiles.length} Records
          </span>
        </div>

        {surveyFiles.length === 0 ? (
          <div className="text-center py-12 border border-slate-100 rounded-lg bg-slate-50/50">
            <Layers className="w-8 h-8 text-slate-300 mx-auto mb-2" />
            <p className="text-xs font-semibold text-slate-700">No Datasets Uploaded For This Survey Mission</p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Select or drop an aerial survey file above to execute server validation.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border border-slate-200 rounded-lg overflow-hidden">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4">Filename</th>
                  <th className="py-2.5 px-4">File Type</th>
                  <th className="py-2.5 px-4">Size</th>
                  <th className="py-2.5 px-4">Ingestion Status</th>
                  <th className="py-2.5 px-4">Workflow Route</th>
                  <th className="py-2.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {surveyFiles.map((f) => (
                  <tr key={f.file_id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3 px-4 font-mono font-medium text-slate-900">{f.original_filename}</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded bg-slate-100 text-[10px] font-semibold text-slate-700">
                        {f.file_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono">
                      {(f.file_size_bytes / (1024 * 1024)).toFixed(2)} MB
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={f.ingestion_status} />
                    </td>
                    <td className="py-3 px-4">
                      {f.workflow_route === "WEBODM_PHOTOGRAMMETRY" ? (
                        <span className="text-[11px] font-semibold text-emerald-700">WebODM Photogrammetry</span>
                      ) : f.workflow_route === "DIRECT_ALGORITHM_GIS" ? (
                        <span className="text-[11px] font-semibold text-blue-700">Direct Algorithm GIS</span>
                      ) : (
                        <span className="text-[11px] text-rose-600">None (Rejected)</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {f.workflow_route === "WEBODM_PHOTOGRAMMETRY" && (
                          <Link
                            href="/admin/photogrammetry"
                            className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 hover:text-emerald-800"
                          >
                            <span>To WebODM</span>
                            <ArrowRight className="w-3.5 h-3.5" />
                          </Link>
                        )}
                        {f.workflow_route === "DIRECT_ALGORITHM_GIS" && (
                          <Link
                            href="/admin/algorithms"
                            className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 hover:text-blue-800"
                          >
                            <span>To Algorithms</span>
                            <ArrowRight className="w-3.5 h-3.5" />
                          </Link>
                        )}
                        <button
                          type="button"
                          onClick={() => handleDeleteFile(f.file_id, f.original_filename)}
                          className="text-slate-400 hover:text-rose-600 p-1"
                          title="Delete file"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* --- Modal 1: Register New Farm --- */}
      {isFarmModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4 border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Sprout className="w-4 h-4 text-emerald-600" />
                <span>Register Agricultural Farm</span>
              </h3>
              <button
                type="button"
                onClick={() => setIsFarmModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateFarm} className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Farm / Estate Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Baramati Precision Agronomy"
                  value={newFarmName}
                  onChange={(e) => setNewFarmName(e.target.value)}
                  className="input-base w-full text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">Village</label>
                  <input
                    type="text"
                    placeholder="e.g. Malegaon Kh"
                    value={newFarmVillage}
                    onChange={(e) => setNewFarmVillage(e.target.value)}
                    className="input-base w-full text-xs"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">District</label>
                  <input
                    type="text"
                    placeholder="e.g. Pune"
                    value={newFarmDistrict}
                    onChange={(e) => setNewFarmDistrict(e.target.value)}
                    className="input-base w-full text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">State / Region</label>
                <input
                  type="text"
                  placeholder="e.g. Maharashtra"
                  value={newFarmState}
                  onChange={(e) => setNewFarmState(e.target.value)}
                  className="input-base w-full text-xs"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsFarmModalOpen(false)}
                  className="btn-secondary text-xs"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary text-xs">
                  Save Farm
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- Modal 2: Create Field --- */}
      {isFieldModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4 border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Layers className="w-4 h-4 text-emerald-600" />
                <span>Add Field Parcel to {activeFarm?.name}</span>
              </h3>
              <button
                type="button"
                onClick={() => setIsFieldModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateField} className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Field Designation Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. North Pivot Sector 2"
                  value={newFieldName}
                  onChange={(e) => setNewFieldName(e.target.value)}
                  className="input-base w-full text-xs"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Planted Crop Species</label>
                <input
                  type="text"
                  placeholder="e.g. Sugarcane Co 86032 / Soybean"
                  value={newFieldCrop}
                  onChange={(e) => setNewFieldCrop(e.target.value)}
                  className="input-base w-full text-xs"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Field Area (Hectares) *</label>
                <input
                  type="number"
                  step="0.1"
                  required
                  value={newFieldArea}
                  onChange={(e) => setNewFieldArea(parseFloat(e.target.value) || 0)}
                  className="input-base w-full text-xs"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsFieldModalOpen(false)}
                  className="btn-secondary text-xs"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary text-xs">
                  Create Field
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- Modal 3: Create Survey --- */}
      {isSurveyModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4 border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-emerald-600" />
                <span>Initialize Drone Flight Mission</span>
              </h3>
              <button
                type="button"
                onClick={() => setIsSurveyModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateSurvey} className="space-y-3">
              <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-600">
                Target Field: <strong className="text-slate-900">{activeField?.field_name}</strong>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">Flight Date *</label>
                  <input
                    type="date"
                    required
                    value={newSurveyDate}
                    onChange={(e) => setNewSurveyDate(e.target.value)}
                    className="input-base w-full text-xs"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">Flight Altitude (m AGL)</label>
                  <input
                    type="number"
                    value={newSurveyAltitude}
                    onChange={(e) => setNewSurveyAltitude(Number(e.target.value))}
                    className="input-base w-full text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Drone Platform</label>
                <select
                  value={newSurveyDrone}
                  onChange={(e) => setNewSurveyDrone(e.target.value)}
                  className="input-base w-full text-xs"
                >
                  <option>DJI Mavic 3 Enterprise</option>
                  <option>DJI Phantom 4 Multispectral</option>
                  <option>MicaSense RedEdge-P (Matrice 300 RTK)</option>
                  <option>Sentera 6X Multispectral Sensor</option>
                  <option>SenseFly eBee X</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Sensor Configuration</label>
                <select
                  value={newSurveySensor}
                  onChange={(e) => setNewSurveySensor(e.target.value)}
                  className="input-base w-full text-xs"
                >
                  <option value="RGB">RGB (True Color 3-Band)</option>
                  <option value="MULTISPECTRAL">Multispectral (5-Band RedEdge / NIR / Green / Blue / Red)</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsSurveyModalOpen(false)}
                  className="btn-secondary text-xs"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary text-xs">
                  Initialize Survey
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
