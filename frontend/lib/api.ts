import { config } from './config';

export interface HealthResponse {
  status: 'ok' | 'degraded' | 'down';
  version: string;
  environment: string;
  timestamp: string;
}

export interface ComponentStatus {
  status: 'healthy' | 'unhealthy' | 'disabled';
  latency_ms: number;
  details: string;
}

export interface ReadinessResponse {
  status: 'ready' | 'not_ready';
  components: Record<string, ComponentStatus>;
  timestamp: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: unknown;
  status: number;
}

export class ApiClientError extends Error {
  public code: string;
  public status: number;
  public details?: unknown;

  constructor(error: ApiError) {
    super(error.message);
    this.name = 'ApiClientError';
    this.code = error.code;
    this.status = error.status;
    this.details = error.details;
  }
}

// --- Phase 5 Types ---

export interface FieldItem {
  id: string;
  farm_id: string;
  field_name: string;
  crop_type?: string;
  area_hectares?: number;
  boundary_geojson?: any;
  surveys_count: number;
  created_at: string;
}

export interface FarmItem {
  id: string;
  owner_id: string;
  name: string;
  village?: string;
  district?: string;
  state?: string;
  boundary_geojson?: any;
  fields_count: number;
  surveys_count: number;
  created_at: string;
  fields?: FieldItem[];
}

export interface FarmListResponse {
  items: FarmItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface SurveyItem {
  id: string;
  field_id: string;
  farm_name?: string;
  field_name?: string;
  survey_code: string;
  flight_date: string;
  drone_model?: string;
  sensor_type: string;
  flight_altitude_m?: number;
  status: string;
  coverage_geojson?: any;
  created_at: string;
  files_count: number;
  total_bytes: number;
}

export interface SurveyListResponse {
  items: SurveyItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface SurveyFileItem {
  file_id: string;
  survey_id: string;
  original_filename: string;
  file_type: string;
  file_size_bytes: number;
  mime_type: string;
  blob_uri: string;
  md5_checksum?: string;
  ingestion_status: string;
  workflow_route: string;
  validation_metadata?: any;
  validation_errors: string[];
  created_at: string;
}

export interface SurveyFileListResponse {
  survey_id: string;
  items: SurveyFileItem[];
  total_files: number;
  total_bytes: number;
  validated_count: number;
  rejected_count: number;
}

// --- Phase 6 Photogrammetry Types ---

export interface ClusterStatusResponse {
  cluster_status: 'ONLINE' | 'OFFLINE';
  is_connected: boolean;
  api_url: string;
  engine: string;
  active_nodes: number;
  total_nodes: number;
  available_ram_gb?: number;
  details: string;
  error_message?: string;
  timestamp: string;
}

export interface EligibleDatasetItem {
  file_id: string;
  survey_id: string;
  survey_code: string;
  farm_name?: string;
  field_name?: string;
  original_filename: string;
  file_type: string;
  file_size_bytes: number;
  ingestion_status: string;
  workflow_route: string;
  is_eligible: boolean;
  ineligibility_reason?: string;
  photo_count_estimate?: number;
  camera_model?: string;
  created_at: string;
}

export interface EligibleDatasetsResponse {
  items: EligibleDatasetItem[];
  total: number;
  eligible_count: number;
  ineligible_count: number;
}

export interface PhotogrammetryProjectItem {
  id: string;
  name: string;
  description?: string;
  farm_id?: string;
  farm_name?: string;
  field_id?: string;
  field_name?: string;
  survey_id?: string;
  survey_code?: string;
  webodm_project_id?: number;
  tags?: string[];
  tasks_count: number;
  latest_task_status?: string;
  available_outputs_count: number;
  created_at: string;
  updated_at: string;
}

export interface PhotogrammetryProjectListResponse {
  items: PhotogrammetryProjectItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface PhotogrammetryProjectCreate {
  name: string;
  description?: string;
  farm_id?: string;
  field_id?: string;
  survey_id?: string;
  tags?: string[];
}

export interface PhotogrammetryProjectUpdate {
  name?: string;
  description?: string;
  farm_id?: string;
  field_id?: string;
  survey_id?: string;
  tags?: string[];
}

export interface GCPPointItem {
  line: number;
  point_id: string;
  easting_x: number;
  northing_y: number;
  elevation_z: number;
  pixel_x?: number;
  pixel_y?: number;
  image_name?: string;
}

export interface GCPValidateRequest {
  content: string;
  filename?: string;
}

export interface GCPValidateResponse {
  valid: boolean;
  crs?: string;
  point_count: number;
  distinct_count: number;
  points: GCPPointItem[];
  errors: string[];
  warnings: string[];
}

export interface ClusterNodeItem {
  id: number;
  name: string;
  hostname: string;
  port: number;
  engine: string;
  version?: string;
  online: boolean;
  task_queue_count: number;
  available_memory_bytes?: number;
  available_memory_gb?: number;
  last_checked: string;
}

export interface ClusterNodesResponse {
  nodes: ClusterNodeItem[];
  total: number;
  active_count: number;
}

export interface DiagnosticsResponse {
  timestamp: string;
  webodm_status: string;
  webodm_url: string;
  webodm_latency_ms?: number;
  authenticated: boolean;
  active_nodes: number;
  total_nodes: number;
  storage_status: string;
  storage_provider: string;
  database_status: string;
  redis_status: string;
  issues: string[];
  recommendations: string[];
}

export interface PhotogrammetryAdminConfigResponse {
  api_url: string;
  username: string;
  default_project_id?: number;
  timeout_seconds: number;
  poll_interval_seconds: number;
  max_retries: number;
  storage_provider: string;
  supported_presets: string[];
}

export interface PhotogrammetryTaskCreate {
  survey_id: string;
  source_file_id?: string;
  project_id?: string;
  gcp_file_id?: string;
  resolution_preset?: 'FAST' | 'HIGH_RES' | 'MULTISPECTRAL' | 'CUSTOM';
  custom_resolution_cm?: number;
  generate_dsm?: boolean;
  generate_dtm?: boolean;
  radiometric_calibration?: boolean;
  feature_quality?: string;
  pc_quality?: string;
}

export interface PhotogrammetryTaskItem {
  task_id: string;
  survey_id: string;
  survey_code?: string;
  project_id?: string;
  project_name?: string;
  source_file_id?: string;
  source_filename?: string;
  gcp_file_id?: string;
  gcp_applied?: boolean;
  webodm_task_uuid?: string;
  resolution_preset: string;
  generate_dsm: boolean;
  generate_dtm: boolean;
  radiometric_calibration: boolean;
  options?: any;
  status: string;
  progress_percent: number;
  current_stage?: string;
  error_message?: string;
  retry_count: number;
  started_at?: string;
  completed_at?: string;
  generated_products_count: number;
}

export interface PhotogrammetryTaskListResponse {
  items: PhotogrammetryTaskItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface TaskLogItem {
  id: number;
  task_id: string;
  log_level: string;
  message: string;
  logged_at: string;
}

export interface TaskLogsResponse {
  task_id: string;
  logs: TaskLogItem[];
  total_lines: number;
}

export interface ArtifactItem {
  product_id: string;
  survey_id: string;
  source_task_id?: string;
  product_type: string;
  original_filename: string;
  blob_uri: string;
  is_cog: boolean;
  band_count: number;
  crs_epsg: string;
  resolution_cm_px?: number;
  created_at: string;
}

export interface ArtifactListResponse {
  task_id: string;
  survey_id: string;
  items: ArtifactItem[];
  total: number;
}

export interface DashboardStatsResponse {
  total_farms: number;
  total_fields: number;
  total_surveys: number;
  total_datasets: number;
  datasets_awaiting_validation: number;
  datasets_validated: number;
  datasets_rejected: number;
  storage_provider: string;
  recent_surveys: Array<{
    survey_id: string;
    survey_code: string;
    farm_name: string;
    field_name: string;
    flight_date: string;
    sensor_type: string;
    status: string;
    files_count: number;
    total_bytes: number;
    created_at: string;
  }>;
  recent_uploads: Array<{
    file_id: string;
    survey_id: string;
    survey_code: string;
    original_filename: string;
    file_type: string;
    file_size_bytes: number;
    ingestion_status: string;
    workflow_route: string;
    created_at: string;
  }>;
  recent_failures: Array<{
    file_id: string;
    survey_id: string;
    survey_code: string;
    original_filename: string;
    file_size_bytes: number;
    validation_errors: string[];
    created_at: string;
  }>;
}

// --- Phase 7 Algorithm & Raster Analytics Types ---

export interface AlgorithmSpec {
  code: string;
  display_name: string;
  required_sensor: string;
  formula: string;
  required_bands: string[];
  expected_range: [number, number];
  description: string;
  parameters?: Record<string, any>;
}

export interface BandSummary {
  band_index: number;
  data_type: string;
  nodata_value?: number | null;
  min_value: number;
  max_value: number;
  mean_value: number;
  std_value: number;
  description?: string;
}

export interface RasterInspection {
  source_id: string;
  source_type: 'MAP_PRODUCT' | 'SURVEY_FILE';
  survey_id: string;
  survey_code?: string;
  farm_name?: string;
  field_name?: string;
  width: number;
  height: number;
  band_count: number;
  crs_epsg?: string;
  bounds: [number, number, number, number];
  gsd_cm: number;
  detected_sensor: string;
  radiometric_type: string;
  calibration_notes: string[];
  suggested_band_mapping: Record<string, number>;
  supported_algorithms: string[];
  bands: BandSummary[];
}

export interface EligibleRasterItem {
  source_id: string;
  source_type: 'MAP_PRODUCT' | 'SURVEY_FILE';
  survey_id: string;
  survey_code: string;
  farm_name?: string;
  field_name?: string;
  filename: string;
  product_type: string;
  band_count: number;
  crs_epsg: string;
  resolution_cm_px?: number;
  detected_sensor: string;
  is_eligible: boolean;
  ineligibility_reason?: string;
  created_at: string;
}

export interface EligibleRastersResponse {
  items: EligibleRasterItem[];
  total: number;
  eligible_count: number;
  ineligible_count: number;
}

export interface BandMappingValidateRequest {
  band_count: number;
  mapping: Record<string, number>;
  algorithm_codes: string[];
}

export interface BandMappingValidateResponse {
  is_valid: boolean;
  per_algorithm_status: Record<string, { is_valid: boolean; error_message?: string }>;
  overall_message?: string;
}

export interface AlgorithmJobItem {
  job_id: string;
  batch_id?: string;
  algorithm_code: string;
  algorithm_name?: string;
  input_product_id: string;
  status: string;
  current_stage?: string;
  progress_percent: number;
  error_message?: string;
  parameters?: Record<string, any>;
  output_product_id?: string;
  started_at?: string;
  completed_at?: string;
}

export interface AlgorithmBatchResponse {
  batch_id: string;
  survey_id: string;
  input_product_id: string;
  total_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  in_progress_jobs: number;
  status: string;
  jobs: AlgorithmJobItem[];
}

export interface ZonalStatItem {
  zone_name: string;
  min_val: number;
  max_val: number;
  area_hectares: number;
  area_percentage: number;
}

export interface MapProductDetail {
  product_id: string;
  survey_id: string;
  source_job_id?: string;
  product_type: string;
  blob_uri: string;
  access_url: string;
  is_cog: boolean;
  band_count: number;
  crs_epsg: string;
  resolution_cm_px?: number;
  statistical_summary?: Record<string, any>;
  zonal_statistics: ZonalStatItem[];
  created_at: string;
}

// --- Phase 8 GIS Maps, Multi-Layer & Diagnostics Types ---

export interface FieldBoundaryGeoJSON {
  type: string;
  id: string;
  geometry: {
    type: string;
    coordinates: any;
  };
  properties: {
    field_id: string;
    field_name: string;
    crop_type?: string;
    area_hectares?: number;
    farm_id: string;
    farm_name: string;
  };
  bbox?: [number, number, number, number];
  centroid?: [number, number];
}

export interface LegendStop {
  value: number;
  color: string;
  label: string;
}

export interface MapLegend {
  title: string;
  unit: string;
  colormap_type: string;
  min_value: number;
  max_value: number;
  nodata_color: string;
  stops: LegendStop[];
}

export interface MapLayerVisualization {
  product_id: string;
  product_type: string;
  survey_id: string;
  field_id?: string;
  farm_id?: string;
  crs_epsg: string;
  is_cog: boolean;
  bounds: [number, number, number, number]; // [minLon, minLat, maxLon, maxLat]
  center: [number, number]; // [lon, lat]
  tile_url_template: string;
  legend: MapLegend;
  statistical_summary?: Record<string, any>;
}

export interface MapProductListItem {
  id: string;
  survey_id: string;
  survey_code: string;
  farm_name: string;
  field_name: string;
  product_type: string;
  display_name: string;
  band_count: number;
  crs_epsg: string;
  resolution_cm_px?: number;
  is_cog: boolean;
  is_published: boolean;
  created_at: string;
  has_raster_file: boolean;
}

export interface PointProbeResponse {
  product_id: string;
  lat: number;
  lon: number;
  value?: number;
  unit: string;
  is_valid: boolean;
  description: string;
}

export interface ZonalDistributionItem {
  zone_name: string;
  min_val: number;
  max_val: number;
  area_hectares: number;
  area_percentage: number;
  color: string;
}

export interface DiagnosticSummaryResponse {
  product_id: string;
  product_type: string;
  display_name: string;
  survey_id: string;
  survey_code: string;
  field_name: string;
  farm_name: string;
  crop_type?: string;
  crs_epsg: string;
  resolution_cm_px?: number;
  valid_pixel_count: number;
  nodata_pixel_count: number;
  total_pixel_count: number;
  valid_percentage: number;
  covered_area_hectares: number;
  min_value?: number;
  max_value?: number;
  mean_value?: number;
  std_value?: number;
  median_value?: number;
  unit: string;
  zonal_distribution: ZonalDistributionItem[];
  scientific_warnings: string[];
  analytical_limitations: string[];
}

export interface ComparisonCompatibilityResponse {
  product_a_id: string;
  product_b_id: string;
  is_compatible: boolean;
  spatial_overlap_percentage: number;
  reason: string;
  recommendation: string;
}

// --- Phase 9 Authentication & Farmer Portal Types ---

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: 'ADMIN' | 'AGRONOMIST' | 'FARMER';
  is_active: boolean;
  assigned_farm_ids: string[];
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserProfile;
}

export interface ReportItem {
  id: string;
  survey_id: string;
  generated_by_user_id: string;
  report_number: string;
  report_title: string;
  blob_uri: string;
  file_size_bytes: number;
  status: string;
  report_parameters?: any;
  created_at: string;
  download_url?: string;
}

export interface ReportListResponse {
  reports: ReportItem[];
  total: number;
}

/**
 * Base fetch client with timeout, JSON parsing, credentials, and token management.
 */
async function fetchWithTimeout(url: string, options: RequestInit = {}, timeoutMs = 15000): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const isFormData = options.body instanceof FormData;
    const defaultHeaders: Record<string, string> = {
      Accept: 'application/json',
    };
    if (!isFormData) {
      defaultHeaders['Content-Type'] = 'application/json';
    }

    if (typeof window !== 'undefined') {
      const storedToken = localStorage.getItem('agridrone_token');
      if (storedToken && !(options.headers && 'Authorization' in options.headers)) {
        defaultHeaders['Authorization'] = `Bearer ${storedToken}`;
      }
    }

    const response = await fetch(url, {
      ...options,
      credentials: 'include',
      signal: controller.signal,
      headers: {
        ...defaultHeaders,
        ...(options.headers || {}),
      },
    });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    if (error instanceof Error && error.name === 'AbortError') {
      throw new ApiClientError({
        code: 'TIMEOUT',
        message: `API request timed out after ${timeoutMs}ms`,
        status: 408,
      });
    }
    throw new ApiClientError({
      code: 'NETWORK_ERROR',
      message: error instanceof Error ? error.message : 'Network request failed',
      status: 0,
    });
  }
}

/**
 * AgriDrone AutoMap API Client
 */
export const api = {
  /**
   * Check API liveness probe.
   */
  async checkHealth(): Promise<HealthResponse> {
    const url = `${config.apiBaseUrl}/health`;
    const response = await fetchWithTimeout(url, { method: 'GET' });
    if (!response.ok) {
      throw new ApiClientError({
        code: 'HEALTH_CHECK_FAILED',
        message: `Health check returned HTTP ${response.status}`,
        status: response.status,
      });
    }
    return (await response.json()) as HealthResponse;
  },

  /**
   * Check API readiness probe (verifies database and redis connectivity).
   */
  async checkReadiness(): Promise<ReadinessResponse> {
    const url = `${config.apiBaseUrl}/health/readiness`;
    const response = await fetchWithTimeout(url, { method: 'GET' });
    const data = (await response.json()) as ReadinessResponse;
    if (!response.ok && response.status !== 503) {
      throw new ApiClientError({
        code: 'READINESS_CHECK_FAILED',
        message: `Readiness check returned HTTP ${response.status}`,
        status: response.status,
        details: data,
      });
    }
    return data;
  },

  /**
   * Get real dashboard statistics.
   */
  async getDashboardStats(): Promise<DashboardStatsResponse> {
    return this.get<DashboardStatsResponse>('/dashboard/stats');
  },

  /**
   * Farms & Fields endpoints.
   */
  async getFarms(params: { search?: string; skip?: number; limit?: number } = {}): Promise<FarmListResponse> {
    const query = new URLSearchParams();
    if (params.search) query.set('search', params.search);
    if (params.skip !== undefined) query.set('skip', String(params.skip));
    if (params.limit !== undefined) query.set('limit', String(params.limit));
    const qs = query.toString();
    return this.get<FarmListResponse>(`/farms${qs ? `?${qs}` : ''}`);
  },

  async createFarm(data: { name: string; village?: string; district?: string; state?: string; boundary_geojson?: any }): Promise<FarmItem> {
    return this.post<FarmItem>('/farms', data);
  },

  async getFarm(farmId: string): Promise<FarmItem> {
    return this.get<FarmItem>(`/farms/${farmId}`);
  },

  async deleteFarm(farmId: string): Promise<void> {
    const url = `${config.apiBaseUrl}/farms/${farmId}`;
    const response = await fetchWithTimeout(url, { method: 'DELETE' });
    if (!response.ok) {
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: 'Failed to delete farm',
        status: response.status,
      });
    }
  },

  async getFieldsForFarm(farmId: string): Promise<FieldItem[]> {
    return this.get<FieldItem[]>(`/farms/${farmId}/fields`);
  },

  async createField(farmId: string, data: { field_name: string; crop_type?: string; area_hectares?: number; boundary_geojson?: any }): Promise<FieldItem> {
    return this.post<FieldItem>(`/farms/${farmId}/fields`, data);
  },

  /**
   * Surveys endpoints.
   */
  async getSurveys(params: { field_id?: string; farm_id?: string; status?: string; skip?: number; limit?: number } = {}): Promise<SurveyListResponse> {
    const query = new URLSearchParams();
    if (params.field_id) query.set('field_id', params.field_id);
    if (params.farm_id) query.set('farm_id', params.farm_id);
    if (params.status) query.set('status', params.status);
    if (params.skip !== undefined) query.set('skip', String(params.skip));
    if (params.limit !== undefined) query.set('limit', String(params.limit));
    const qs = query.toString();
    return this.get<SurveyListResponse>(`/surveys${qs ? `?${qs}` : ''}`);
  },

  async createSurvey(data: {
    field_id: string;
    flight_date: string;
    drone_model?: string;
    sensor_type?: string;
    flight_altitude_m?: number;
    survey_code?: string;
  }): Promise<SurveyItem> {
    return this.post<SurveyItem>('/surveys', data);
  },

  async getSurvey(surveyId: string): Promise<SurveyItem & { files?: SurveyFileItem[] }> {
    return this.get<SurveyItem & { files?: SurveyFileItem[] }>(`/surveys/${surveyId}`);
  },

  /**
   * Drone Ingestion endpoints.
   */
  async uploadSurveyFile(
    surveyId: string,
    file: File,
    workflowMode: 'raw_photos' | 'geotiff' = 'raw_photos'
  ): Promise<SurveyFileItem> {
    const url = `${config.apiBaseUrl}/ingestion/upload/${surveyId}`;
    const formData = new FormData();
    formData.append('file', file);
    formData.append('workflow_mode', workflowMode);

    const response = await fetchWithTimeout(url, {
      method: 'POST',
      body: formData,
    }, 60000); // 60s timeout for large uploads

    if (!response.ok) {
      let errorBody: any;
      try {
        errorBody = await response.json();
      } catch {
        errorBody = await response.text();
      }
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: errorBody?.detail || 'File upload failed',
        status: response.status,
        details: errorBody,
      });
    }

    return (await response.json()) as SurveyFileItem;
  },

  async getSurveyFiles(surveyId: string): Promise<SurveyFileListResponse> {
    return this.get<SurveyFileListResponse>(`/ingestion/surveys/${surveyId}/files`);
  },

  async deleteSurveyFile(fileId: string): Promise<void> {
    const url = `${config.apiBaseUrl}/ingestion/files/${fileId}`;
    const response = await fetchWithTimeout(url, { method: 'DELETE' });
    if (!response.ok) {
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: 'Failed to delete file',
        status: response.status,
      });
    }
  },

  /**
   * Phase 6: WebODM Photogrammetry endpoints
   */
  async getClusterStatus(): Promise<ClusterStatusResponse> {
    return this.get<ClusterStatusResponse>('/photogrammetry/cluster-status');
  },

  async getEligibleDatasets(surveyId?: string): Promise<EligibleDatasetsResponse> {
    const qs = surveyId ? `?survey_id=${encodeURIComponent(surveyId)}` : '';
    return this.get<EligibleDatasetsResponse>(`/photogrammetry/eligible-datasets${qs}`);
  },

  async createPhotogrammetryTask(data: PhotogrammetryTaskCreate): Promise<PhotogrammetryTaskItem> {
    return this.post<PhotogrammetryTaskItem>('/photogrammetry/tasks', data);
  },

  async getPhotogrammetryTasks(params: {
    survey_id?: string;
    status?: string;
    skip?: number;
    limit?: number;
  } = {}): Promise<PhotogrammetryTaskListResponse> {
    const query = new URLSearchParams();
    if (params.survey_id) query.set('survey_id', params.survey_id);
    if (params.status) query.set('status', params.status);
    if (params.skip !== undefined) query.set('skip', String(params.skip));
    if (params.limit !== undefined) query.set('limit', String(params.limit));
    const qs = query.toString();
    return this.get<PhotogrammetryTaskListResponse>(`/photogrammetry/tasks${qs ? `?${qs}` : ''}`);
  },

  async getPhotogrammetryTask(taskId: string): Promise<PhotogrammetryTaskItem> {
    return this.get<PhotogrammetryTaskItem>(`/photogrammetry/tasks/${taskId}`);
  },

  async getPhotogrammetryLogs(taskId: string, limit: number = 500): Promise<TaskLogsResponse> {
    return this.get<TaskLogsResponse>(`/photogrammetry/tasks/${taskId}/logs?limit=${limit}`);
  },

  async getPhotogrammetryArtifacts(taskId: string): Promise<ArtifactListResponse> {
    return this.get<ArtifactListResponse>(`/photogrammetry/tasks/${taskId}/artifacts`);
  },

  async cancelPhotogrammetryTask(taskId: string): Promise<{ task_id: string; status: string; message: string }> {
    const url = `${config.apiBaseUrl}/photogrammetry/tasks/${taskId}/cancel`;
    const response = await fetchWithTimeout(url, { method: 'POST' });
    if (!response.ok) {
      let errorBody: any;
      try {
        errorBody = await response.json();
      } catch {
        errorBody = await response.text();
      }
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: errorBody?.detail || 'Failed to cancel task',
        status: response.status,
        details: errorBody,
      });
    }
    return (await response.json()) as { task_id: string; status: string; message: string };
  },

  async retryPhotogrammetryTask(taskId: string): Promise<PhotogrammetryTaskItem> {
    const url = `${config.apiBaseUrl}/photogrammetry/tasks/${taskId}/retry`;
    const response = await fetchWithTimeout(url, { method: 'POST' });
    if (!response.ok) {
      let errorBody: any;
      try {
        errorBody = await response.json();
      } catch {
        errorBody = await response.text();
      }
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: errorBody?.detail || 'Failed to retry task',
        status: response.status,
        details: errorBody,
      });
    }
    return (await response.json()) as PhotogrammetryTaskItem;
  },

  // --- WebODM Integration & Projects Workspace ---

  async getPhotogrammetryProjects(params: {
    farm_id?: string;
    field_id?: string;
    search?: string;
    skip?: number;
    limit?: number;
  } = {}): Promise<PhotogrammetryProjectListResponse> {
    const query = new URLSearchParams();
    if (params.farm_id) query.set('farm_id', params.farm_id);
    if (params.field_id) query.set('field_id', params.field_id);
    if (params.search) query.set('search', params.search);
    if (params.skip !== undefined) query.set('skip', String(params.skip));
    if (params.limit !== undefined) query.set('limit', String(params.limit));
    const qs = query.toString();
    return this.get<PhotogrammetryProjectListResponse>(`/photogrammetry/projects${qs ? `?${qs}` : ''}`);
  },

  async getPhotogrammetryProject(projectId: string): Promise<PhotogrammetryProjectItem> {
    return this.get<PhotogrammetryProjectItem>(`/photogrammetry/projects/${projectId}`);
  },

  async createPhotogrammetryProject(data: PhotogrammetryProjectCreate): Promise<PhotogrammetryProjectItem> {
    return this.post<PhotogrammetryProjectItem>('/photogrammetry/projects', data);
  },

  async updatePhotogrammetryProject(projectId: string, data: PhotogrammetryProjectUpdate): Promise<PhotogrammetryProjectItem> {
    return this.patch<PhotogrammetryProjectItem>(`/photogrammetry/projects/${projectId}`, data);
  },

  async deletePhotogrammetryProject(projectId: string): Promise<{ task_id: string; status: string; message: string }> {
    return this.delete<{ task_id: string; status: string; message: string }>(`/photogrammetry/projects/${projectId}`);
  },

  async validateGcp(data: GCPValidateRequest): Promise<GCPValidateResponse> {
    return this.post<GCPValidateResponse>('/photogrammetry/gcp/validate', data);
  },

  async getProcessingNodes(): Promise<ClusterNodesResponse> {
    return this.get<ClusterNodesResponse>('/photogrammetry/nodes');
  },

  async getPhotogrammetryDiagnostics(): Promise<DiagnosticsResponse> {
    return this.get<DiagnosticsResponse>('/photogrammetry/diagnostics');
  },

  async getPhotogrammetryAdminConfig(): Promise<PhotogrammetryAdminConfigResponse> {
    return this.get<PhotogrammetryAdminConfigResponse>('/photogrammetry/admin/config');
  },

  // --- Phase 7 Algorithms & Raster Analytics ---

  async getSupportedAlgorithms(): Promise<AlgorithmSpec[]> {
    const url = `${config.apiBaseUrl}/algorithms/supported`;
    const response = await fetchWithTimeout(url);
    if (!response.ok) {
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: 'Failed to fetch supported algorithms',
        status: response.status,
      });
    }
    return (await response.json()) as AlgorithmSpec[];
  },

  async getEligibleRasters(surveyId?: string): Promise<EligibleRastersResponse> {
    const query = surveyId ? `?survey_id=${encodeURIComponent(surveyId)}` : '';
    const url = `${config.apiBaseUrl}/algorithms/eligible-rasters${query}`;
    const response = await fetchWithTimeout(url);
    if (!response.ok) {
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: 'Failed to fetch eligible rasters',
        status: response.status,
      });
    }
    return (await response.json()) as EligibleRastersResponse;
  },

  async inspectRaster(sourceId: string, sourceType: string = 'MAP_PRODUCT'): Promise<RasterInspection> {
    const url = `${config.apiBaseUrl}/algorithms/inspect/${encodeURIComponent(sourceId)}?source_type=${encodeURIComponent(sourceType)}`;
    const response = await fetchWithTimeout(url);
    if (!response.ok) {
      let errorBody: any;
      try {
        errorBody = await response.json();
      } catch {
        errorBody = await response.text();
      }
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: errorBody?.detail || 'Raster inspection failed',
        status: response.status,
        details: errorBody,
      });
    }
    return (await response.json()) as RasterInspection;
  },

  async validateBandMapping(payload: BandMappingValidateRequest): Promise<BandMappingValidateResponse> {
    const url = `${config.apiBaseUrl}/algorithms/validate-mapping`;
    const response = await fetchWithTimeout(url, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: 'Failed to validate band mapping',
        status: response.status,
      });
    }
    return (await response.json()) as BandMappingValidateResponse;
  },

  async submitAlgorithmBatch(payload: {
    source_id: string;
    source_type?: string;
    band_mapping: Record<string, number>;
    algorithms: Array<{ algorithm_code: string; parameters?: Record<string, any> }>;
  }): Promise<AlgorithmBatchResponse> {
    const url = `${config.apiBaseUrl}/algorithms/jobs`;
    const response = await fetchWithTimeout(url, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      let errorBody: any;
      try {
        errorBody = await response.json();
      } catch {
        errorBody = await response.text();
      }
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: errorBody?.detail || 'Failed to submit algorithm batch',
        status: response.status,
        details: errorBody,
      });
    }
    return (await response.json()) as AlgorithmBatchResponse;
  },

  async getAlgorithmBatch(batchId: string): Promise<AlgorithmBatchResponse> {
    const url = `${config.apiBaseUrl}/algorithms/batches/${encodeURIComponent(batchId)}`;
    const response = await fetchWithTimeout(url);
    if (!response.ok) {
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: 'Failed to fetch algorithm batch status',
        status: response.status,
      });
    }
    return (await response.json()) as AlgorithmBatchResponse;
  },

  async listAlgorithmJobs(surveyId?: string, status?: string): Promise<AlgorithmJobItem[]> {
    const params = new URLSearchParams();
    if (surveyId) params.append('survey_id', surveyId);
    if (status) params.append('status', status);
    const query = params.toString() ? `?${params.toString()}` : '';
    const url = `${config.apiBaseUrl}/algorithms/jobs${query}`;
    const response = await fetchWithTimeout(url);
    if (!response.ok) {
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: 'Failed to list algorithm jobs',
        status: response.status,
      });
    }
    return (await response.json()) as AlgorithmJobItem[];
  },

  async getAlgorithmJob(jobId: string): Promise<AlgorithmJobItem> {
    const url = `${config.apiBaseUrl}/algorithms/jobs/${encodeURIComponent(jobId)}`;
    const response = await fetchWithTimeout(url);
    if (!response.ok) {
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: 'Failed to fetch algorithm job',
        status: response.status,
      });
    }
    return (await response.json()) as AlgorithmJobItem;
  },

  async retryAlgorithmJob(jobId: string): Promise<AlgorithmJobItem> {
    const url = `${config.apiBaseUrl}/algorithms/jobs/${encodeURIComponent(jobId)}/retry`;
    const response = await fetchWithTimeout(url, { method: 'POST' });
    if (!response.ok) {
      let errorBody: any;
      try {
        errorBody = await response.json();
      } catch {
        errorBody = await response.text();
      }
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: errorBody?.detail || 'Failed to retry algorithm job',
        status: response.status,
        details: errorBody,
      });
    }
    return (await response.json()) as AlgorithmJobItem;
  },

  async getMapProductDetail(productId: string): Promise<MapProductDetail> {
    const url = `${config.apiBaseUrl}/algorithms/products/${encodeURIComponent(productId)}`;
    const response = await fetchWithTimeout(url);
    if (!response.ok) {
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: 'Failed to fetch map product details',
        status: response.status,
      });
    }
    return (await response.json()) as MapProductDetail;
  },

  // --- Phase 8 GIS Maps & Diagnostics API Client ---

  async getFieldBoundary(fieldId: string): Promise<FieldBoundaryGeoJSON> {
    const url = `${config.apiBaseUrl}/maps/fields/${encodeURIComponent(fieldId)}/boundary`;
    const response = await fetchWithTimeout(url);
    if (!response.ok) {
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: 'Failed to fetch field boundary geometry',
        status: response.status,
      });
    }
    return (await response.json()) as FieldBoundaryGeoJSON;
  },

  async getSurveyCoverage(surveyId: string): Promise<any> {
    const url = `${config.apiBaseUrl}/maps/surveys/${encodeURIComponent(surveyId)}/coverage`;
    const response = await fetchWithTimeout(url);
    if (!response.ok) {
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: 'Failed to fetch survey coverage geometry',
        status: response.status,
      });
    }
    return await response.json();
  },

  async getSurveyProducts(surveyId: string): Promise<MapProductListItem[]> {
    const url = `${config.apiBaseUrl}/maps/surveys/${encodeURIComponent(surveyId)}/products`;
    const response = await fetchWithTimeout(url);
    if (!response.ok) {
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: 'Failed to fetch survey raster products',
        status: response.status,
      });
    }
    return (await response.json()) as MapProductListItem[];
  },

  async getLayerVisualization(productId: string): Promise<MapLayerVisualization> {
    const url = `${config.apiBaseUrl}/maps/layers/${encodeURIComponent(productId)}/visualization`;
    const response = await fetchWithTimeout(url);
    if (!response.ok) {
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: 'Failed to fetch layer visualization metadata',
        status: response.status,
      });
    }
    return (await response.json()) as MapLayerVisualization;
  },

  getMapTileUrlTemplate(productId: string): string {
    return `${config.apiBaseUrl}/maps/tiles/${encodeURIComponent(productId)}/{z}/{x}/{y}.png`;
  },

  async probeMapPoint(productId: string, lat: number, lon: number): Promise<PointProbeResponse> {
    const url = `${config.apiBaseUrl}/maps/products/${encodeURIComponent(productId)}/probe?lat=${lat}&lon=${lon}`;
    const response = await fetchWithTimeout(url);
    if (!response.ok) {
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: 'Failed to probe raster point',
        status: response.status,
      });
    }
    return (await response.json()) as PointProbeResponse;
  },

  async getProductDiagnostics(productId: string): Promise<DiagnosticSummaryResponse> {
    const url = `${config.apiBaseUrl}/maps/products/${encodeURIComponent(productId)}/diagnostics`;
    const response = await fetchWithTimeout(url);
    if (!response.ok) {
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: 'Failed to fetch raster diagnostics summary',
        status: response.status,
      });
    }
    return (await response.json()) as DiagnosticSummaryResponse;
  },

  async checkComparisonCompatibility(productA: string, productB: string): Promise<ComparisonCompatibilityResponse> {
    const url = `${config.apiBaseUrl}/maps/compare-compatibility?product_a=${encodeURIComponent(productA)}&product_b=${encodeURIComponent(productB)}`;
    const response = await fetchWithTimeout(url);
    if (!response.ok) {
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: 'Failed to evaluate raster comparison compatibility',
        status: response.status,
      });
    }
    return (await response.json()) as ComparisonCompatibilityResponse;
  },

  /**
   * Generic GET helper.
   */
  async get<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${config.apiBaseUrl}${cleanEndpoint}`;
    const response = await fetchWithTimeout(url, { ...options, method: 'GET' });
    if (!response.ok) {
      let errorBody: any;
      try {
        errorBody = await response.json();
      } catch {
        errorBody = await response.text();
      }
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: errorBody?.detail || `Request failed with status ${response.status}`,
        status: response.status,
        details: errorBody,
      });
    }
    return (await response.json()) as T;
  },

  /**
   * Generic POST helper.
   */
  async post<T>(endpoint: string, data: unknown, options: RequestInit = {}): Promise<T> {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${config.apiBaseUrl}${cleanEndpoint}`;
    const response = await fetchWithTimeout(url, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      let errorBody: any;
      try {
        errorBody = await response.json();
      } catch {
        errorBody = await response.text();
      }
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: errorBody?.detail || `Request failed with status ${response.status}`,
        status: response.status,
        details: errorBody,
      });
    }
    return (await response.json()) as T;
  },

  /**
   * Generic PATCH helper.
   */
  async patch<T>(endpoint: string, data: unknown, options: RequestInit = {}): Promise<T> {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${config.apiBaseUrl}${cleanEndpoint}`;
    const response = await fetchWithTimeout(url, {
      ...options,
      method: 'PATCH',
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      let errorBody: any;
      try {
        errorBody = await response.json();
      } catch {
        errorBody = await response.text();
      }
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: errorBody?.detail || `Request failed with status ${response.status}`,
        status: response.status,
        details: errorBody,
      });
    }
    return (await response.json()) as T;
  },

  /**
   * Generic DELETE helper.
   */
  async delete<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${config.apiBaseUrl}${cleanEndpoint}`;
    const response = await fetchWithTimeout(url, {
      ...options,
      method: 'DELETE',
    });
    if (!response.ok) {
      let errorBody: any;
      try {
        errorBody = await response.json();
      } catch {
        errorBody = await response.text();
      }
      throw new ApiClientError({
        code: `HTTP_${response.status}`,
        message: errorBody?.detail || `Request failed with status ${response.status}`,
        status: response.status,
        details: errorBody,
      });
    }
    return (await response.json()) as T;
  },

  /**
   * Phase 9 Authentication API Methods
   */
  auth: {
    async login(email: string, password: string): Promise<TokenResponse> {
      const url = `${config.apiBaseUrl}/auth/login`;
      const response = await fetchWithTimeout(url, {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      if (!response.ok) {
        let errorBody: any;
        try {
          errorBody = await response.json();
        } catch {
          errorBody = await response.text();
        }
        throw new ApiClientError({
          code: `HTTP_${response.status}`,
          message: errorBody?.detail || 'Invalid email or password.',
          status: response.status,
          details: errorBody,
        });
      }
      const data = (await response.json()) as TokenResponse;
      if (typeof window !== 'undefined' && data.access_token) {
        localStorage.setItem('agridrone_token', data.access_token);
        localStorage.setItem('agridrone_user', JSON.stringify(data.user));
      }
      return data;
    },

    async logout(): Promise<{ message: string }> {
      try {
        const url = `${config.apiBaseUrl}/auth/logout`;
        await fetchWithTimeout(url, { method: 'POST' });
      } catch {
        // Continue even if network fails to ensure client-side state is cleared
      } finally {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('agridrone_token');
          localStorage.removeItem('agridrone_user');
        }
      }
      return { message: 'Successfully logged out.' };
    },

    async getMe(): Promise<UserProfile> {
      const url = `${config.apiBaseUrl}/auth/me`;
      const response = await fetchWithTimeout(url, { method: 'GET' });
      if (!response.ok) {
        if (response.status === 401 && typeof window !== 'undefined') {
          localStorage.removeItem('agridrone_token');
          localStorage.removeItem('agridrone_user');
        }
        let errorBody: any;
        try {
          errorBody = await response.json();
        } catch {
          errorBody = await response.text();
        }
        throw new ApiClientError({
          code: `HTTP_${response.status}`,
          message: errorBody?.detail || 'Unauthenticated session.',
          status: response.status,
          details: errorBody,
        });
      }
      const user = (await response.json()) as UserProfile;
      if (typeof window !== 'undefined') {
        localStorage.setItem('agridrone_user', JSON.stringify(user));
      }
      return user;
    },

    async registerFarmer(payload: { email: string; full_name: string; password?: string; farm_id?: string }): Promise<UserProfile> {
      const url = `${config.apiBaseUrl}/auth/register-farmer`;
      const response = await fetchWithTimeout(url, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        let errorBody: any;
        try {
          errorBody = await response.json();
        } catch {
          errorBody = await response.text();
        }
        throw new ApiClientError({
          code: `HTTP_${response.status}`,
          message: errorBody?.detail || 'Failed to create farmer account.',
          status: response.status,
          details: errorBody,
        });
      }
      return (await response.json()) as UserProfile;
    },

    async assignFarm(payload: { farmer_id: string; farm_id: string }): Promise<{ message: string; farmer: UserProfile }> {
      const url = `${config.apiBaseUrl}/auth/assign-farm`;
      const response = await fetchWithTimeout(url, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        let errorBody: any;
        try {
          errorBody = await response.json();
        } catch {
          errorBody = await response.text();
        }
        throw new ApiClientError({
          code: `HTTP_${response.status}`,
          message: errorBody?.detail || 'Failed to assign farm to farmer.',
          status: response.status,
          details: errorBody,
        });
      }
      return (await response.json()) as { message: string; farmer: UserProfile };
    },
  },

  /**
   * Phase 9 Reports API Methods
   */
  reports: {
    async list(surveyId?: string): Promise<ReportListResponse> {
      let url = `${config.apiBaseUrl}/reports`;
      if (surveyId) {
        url += `?survey_id=${encodeURIComponent(surveyId)}`;
      }
      const response = await fetchWithTimeout(url, { method: 'GET' });
      if (!response.ok) {
        let errorBody: any;
        try {
          errorBody = await response.json();
        } catch {
          errorBody = await response.text();
        }
        throw new ApiClientError({
          code: `HTTP_${response.status}`,
          message: errorBody?.detail || 'Failed to fetch reports list.',
          status: response.status,
          details: errorBody,
        });
      }
      return (await response.json()) as ReportListResponse;
    },

    async get(reportId: string): Promise<ReportItem> {
      const url = `${config.apiBaseUrl}/reports/${encodeURIComponent(reportId)}`;
      const response = await fetchWithTimeout(url, { method: 'GET' });
      if (!response.ok) {
        let errorBody: any;
        try {
          errorBody = await response.json();
        } catch {
          errorBody = await response.text();
        }
        throw new ApiClientError({
          code: `HTTP_${response.status}`,
          message: errorBody?.detail || 'Report not found.',
          status: response.status,
          details: errorBody,
        });
      }
      return (await response.json()) as ReportItem;
    },

    getDownloadUrl(reportId: string): string {
      return `${config.apiBaseUrl}/reports/${encodeURIComponent(reportId)}/download`;
    },
  },
};

export const apiClient = api;
