"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  MapPin,
  Calendar,
  Layers,
  Download,
  Info,
  CheckCircle2,
  Sliders,
  AlertTriangle,
  ArrowRight,
  Shield,
  FileText,
  Lock,
  Columns,
  Loader2,
  RefreshCw,
  Eye,
  Maximize2,
} from "lucide-react";
import {
  api,
  FarmItem,
  FieldItem,
  SurveyItem,
  MapProductListItem,
  FieldBoundaryGeoJSON,
  MapLayerVisualization,
  PointProbeResponse,
} from "@/lib/api";
import { MapLibreViewer } from "@/components/MapLibreViewer";
import { MapComparisonViewer } from "@/components/MapComparisonViewer";
import { StatusBadge } from "@/components/StatusBadge";
import { AlertBanner } from "@/components/AlertBanner";

export default function FarmerPortalPage() {
  // Navigation & Entity Selection State
  const [farms, setFarms] = useState<FarmItem[]>([]);
  const [selectedFarmId, setSelectedFarmId] = useState<string>("");
  const [fields, setFields] = useState<FieldItem[]>([]);
  const [selectedFieldId, setSelectedFieldId] = useState<string>("");
  const [surveys, setSurveys] = useState<SurveyItem[]>([]);
  const [selectedSurveyId, setSelectedSurveyId] = useState<string>("");

  // Spatial & Layer State
  const [fieldBoundary, setFieldBoundary] = useState<FieldBoundaryGeoJSON | null>(null);
  const [products, setProducts] = useState<MapProductListItem[]>([]);
  const [activeProductId, setActiveProductId] = useState<string | null>(null);
  const [activeVisualization, setActiveVisualization] = useState<MapLayerVisualization | null>(null);
  const [opacity, setOpacity] = useState<number>(0.85);

  // Comparison Mode State
  const [isComparisonMode, setIsComparisonMode] = useState<boolean>(false);
  const [compareProductBId, setCompareProductBId] = useState<string | null>(null);
  const [compareVisB, setCompareVisB] = useState<MapLayerVisualization | null>(null);

  // Loading & Error States
  const [isLoadingEntities, setIsLoadingEntities] = useState<boolean>(true);
  const [isLoadingLayer, setIsLoadingLayer] = useState<boolean>(false);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);

  // Probing State
  const [probedPoint, setProbedPoint] = useState<PointProbeResponse | null>(null);

  // Download simulation
  const [downloadingReport, setDownloadingReport] = useState<boolean>(false);
  const [downloadSuccess, setDownloadSuccess] = useState<boolean>(false);

  // Tenant Guard simulation toggle (from Phase 2 design review)
  const [simulateDenied, setSimulateDenied] = useState<boolean>(false);

  // 1. Initial Load: Fetch Farms and Surveys
  useEffect(() => {
    let isMounted = true;
    setIsLoadingEntities(true);

    Promise.all([api.getFarms({ limit: 50 }), api.getSurveys({ limit: 50 })])
      .then(([farmsRes, surveysRes]) => {
        if (!isMounted) return;

        const farmList = farmsRes.items || [];
        const surveyList = surveysRes.items || [];

        setFarms(farmList);
        setSurveys(surveyList);

        if (farmList.length > 0) {
          const firstFarm = farmList[0];
          setSelectedFarmId(firstFarm.id);
          const farmFields = firstFarm.fields || [];
          setFields(farmFields);

          if (farmFields.length > 0) {
            setSelectedFieldId(farmFields[0].id);
          }
        }

        // Set initial survey if matches
        if (surveyList.length > 0) {
          setSelectedSurveyId(surveyList[0].id);
        }
      })
      .catch((err) => {
        if (!isMounted) return;
        console.error("Failed to fetch initial portal entities:", err);
        setErrorBanner("Could not load farm or survey records. Please verify backend connectivity.");
      })
      .finally(() => {
        if (isMounted) setIsLoadingEntities(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // 2. When Farm changes, update Fields
  const handleFarmChange = (farmId: string) => {
    setSelectedFarmId(farmId);
    const farm = farms.find((f) => f.id === farmId);
    const farmFields = farm?.fields || [];
    setFields(farmFields);
    if (farmFields.length > 0) {
      setSelectedFieldId(farmFields[0].id);
    } else {
      setSelectedFieldId("");
      setFieldBoundary(null);
    }
  };

  // 3. When Field changes, update Boundary and filter Surveys
  useEffect(() => {
    if (!selectedFieldId) {
      setFieldBoundary(null);
      return;
    }

    let isMounted = true;
    api
      .getFieldBoundary(selectedFieldId)
      .then((boundary) => {
        if (isMounted) setFieldBoundary(boundary);
      })
      .catch((err) => {
        if (isMounted) {
          console.warn("Field boundary not found or empty:", err);
          setFieldBoundary(null);
        }
      });

    // Update selected survey to one belonging to this field if possible
    const fieldSurveys = surveys.filter((s) => s.field_id === selectedFieldId);
    if (fieldSurveys.length > 0) {
      setSelectedSurveyId(fieldSurveys[0].id);
    }

    return () => {
      isMounted = false;
    };
  }, [selectedFieldId, surveys]);

  // 4. When Survey changes, fetch its Map Products
  useEffect(() => {
    if (!selectedSurveyId) {
      setProducts([]);
      setActiveProductId(null);
      setActiveVisualization(null);
      return;
    }

    let isMounted = true;
    setIsLoadingLayer(true);

    api
      .getSurveyProducts(selectedSurveyId)
      .then((prods) => {
        if (!isMounted) return;
        setProducts(prods);

        // Pick initial active product (prioritize INDEX_NDVI, then ORTHOPHOTO, then first available)
        if (prods.length > 0) {
          const ndviProd = prods.find((p) => p.product_type === "INDEX_NDVI" && p.has_raster_file);
          const orthoProd = prods.find((p) => p.product_type === "ORTHOPHOTO" && p.has_raster_file);
          const defaultProd = ndviProd || orthoProd || prods[0];

          setActiveProductId(defaultProd.id);

          // For comparison mode, select second product
          const secondProd = prods.find((p) => p.id !== defaultProd.id && p.has_raster_file);
          if (secondProd) {
            setCompareProductBId(secondProd.id);
          }
        } else {
          setActiveProductId(null);
          setActiveVisualization(null);
        }
      })
      .catch((err) => {
        if (!isMounted) return;
        console.warn("Failed to fetch products for survey:", err);
        setProducts([]);
        setActiveProductId(null);
        setActiveVisualization(null);
      })
      .finally(() => {
        if (isMounted) setIsLoadingLayer(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedSurveyId]);

  // 5. When activeProductId changes, fetch visualization metadata
  useEffect(() => {
    if (!activeProductId) {
      setActiveVisualization(null);
      return;
    }

    let isMounted = true;
    api
      .getLayerVisualization(activeProductId)
      .then((vis) => {
        if (isMounted) setActiveVisualization(vis);
      })
      .catch((err) => {
        if (isMounted) {
          console.warn("Failed to fetch layer visualization:", err);
          setActiveVisualization(null);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [activeProductId]);

  // 6. When compareProductBId changes, fetch visualization metadata B
  useEffect(() => {
    if (!compareProductBId) {
      setCompareVisB(null);
      return;
    }

    let isMounted = true;
    api
      .getLayerVisualization(compareProductBId)
      .then((vis) => {
        if (isMounted) setCompareVisB(vis);
      })
      .catch((err) => {
        if (isMounted) {
          console.warn("Failed to fetch compare layer B visualization:", err);
          setCompareVisB(null);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [compareProductBId]);

  const handleSimulateDownload = () => {
    setDownloadingReport(true);
    setDownloadSuccess(false);
    setTimeout(() => {
      setDownloadingReport(false);
      setDownloadSuccess(true);
    }, 1200);
  };

  const selectedFieldObj = fields.find((f) => f.id === selectedFieldId);
  const selectedSurveyObj = surveys.find((s) => s.id === selectedSurveyId);
  const selectedProductObj = products.find((p) => p.id === activeProductId);

  if (simulateDenied) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center space-y-4">
        <div className="w-16 h-16 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto">
          <Lock className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-slate-900">Access Denied: Cross-Tenant Guard Triggered</h2>
        <p className="text-sm text-slate-600 max-w-md mx-auto">
          You do not have authorized permission to view survey rasters for this farm entity. Survey data is strictly
          partitioned by tenant ownership.
        </p>
        <button onClick={() => setSimulateDenied(false)} className="btn-primary text-xs">
          Return to Authorized Field
        </button>
      </div>
    );
  }

  if (!isLoadingEntities && farms.length === 0) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center space-y-4">
        <div className="w-16 h-16 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center mx-auto">
          <MapPin className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-slate-900">No Maps or Fields Available Yet</h2>
        <p className="text-sm text-slate-600 max-w-md mx-auto">
          No farms or fields are currently assigned to your account. When your agricultural administrator registers and maps your fields, your survey rasters and diagnostics will appear here automatically.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 mb-1">
            <span>Page 4 of 5</span>
            <span>&bull;</span>
            <span className="text-emerald-700 font-bold">Interactive GIS Maps</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Interactive GIS Maps &amp; Multi-Layer Visualization
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Explore validated drone rasters, PostGIS field boundaries, continuous spectral indices, and side-by-side product comparisons.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setIsComparisonMode(!isComparisonMode)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 border transition ${
              isComparisonMode
                ? "bg-blue-50 text-blue-800 border-blue-300 font-semibold"
                : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
            }`}
          >
            <Columns className="w-3.5 h-3.5" />
            <span>{isComparisonMode ? "Exit Comparison" : "Compare Layers"}</span>
          </button>

          <button
            onClick={() => setSimulateDenied(true)}
            className="btn-secondary text-xs text-slate-600"
            title="Preview how unauthorized tenant requests are safely rejected"
          >
            <Shield className="w-3.5 h-3.5 text-slate-400" />
            <span>Tenant Guard</span>
          </button>

          {activeProductId && (
            <Link
              href={`/portal/diagnostics?product_id=${encodeURIComponent(activeProductId)}`}
              className="btn-primary text-xs flex items-center gap-1.5"
            >
              <span>View Diagnostics (Page 5)</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          )}
        </div>
      </div>

      {errorBanner && (
        <AlertBanner type="error" title="Geospatial Data Error" message={errorBanner} />
      )}

      {/* Row 1: Farm, Field & Survey Selectors */}
      <div className="card-base p-4 bg-white flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-4 text-xs">
          <div>
            <span className="font-semibold text-slate-500 block mb-1">Assigned Farm</span>
            <select
              value={selectedFarmId}
              onChange={(e) => handleFarmChange(e.target.value)}
              className="input-base text-xs font-semibold text-slate-900 min-w-[180px]"
              disabled={isLoadingEntities || farms.length === 0}
            >
              {farms.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <span className="font-semibold text-slate-500 block mb-1">Select Field</span>
            <select
              value={selectedFieldId}
              onChange={(e) => setSelectedFieldId(e.target.value)}
              className="input-base text-xs font-semibold text-slate-900 min-w-[200px]"
              disabled={isLoadingEntities || fields.length === 0}
            >
              {fields.map((fld) => (
                <option key={fld.id} value={fld.id}>
                  {fld.field_name} {fld.crop_type ? `(${fld.crop_type})` : ""}
                </option>
              ))}
            </select>
          </div>

          <div>
            <span className="font-semibold text-slate-500 block mb-1">Survey Flight Date</span>
            <select
              value={selectedSurveyId}
              onChange={(e) => setSelectedSurveyId(e.target.value)}
              className="input-base text-xs font-semibold text-emerald-800 bg-emerald-50/50 border-emerald-200 min-w-[210px]"
              disabled={isLoadingEntities || surveys.length === 0}
            >
              {surveys
                .filter((s) => !selectedFieldId || s.field_id === selectedFieldId)
                .map((srv) => (
                  <option key={srv.id} value={srv.id}>
                    {srv.flight_date} — {srv.survey_code} ({srv.sensor_type})
                  </option>
                ))}
            </select>
          </div>
        </div>

        {/* Selected Field Metadata Pill */}
        <div className="flex items-center gap-2">
          {selectedFieldObj && (
            <div className="text-right text-[11px] text-slate-600 bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5">
              <span className="font-semibold text-slate-800">{selectedFieldObj.field_name}</span>
              <span className="text-slate-400 mx-1.5">&bull;</span>
              <span>{selectedFieldObj.crop_type || "Mixed Crop"}</span>
              <span className="text-slate-400 mx-1.5">&bull;</span>
              <span className="font-mono font-medium text-emerald-700">
                {selectedFieldObj.area_hectares ? `${selectedFieldObj.area_hectares} ha` : "Boundary Active"}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Row 2: Map Viewer Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Main Map Viewer Canvas (3 cols) */}
        <div className="lg:col-span-3 space-y-3">
          {isComparisonMode ? (
            /* Comparison Dual Synchronized MapLibre View */
            <MapComparisonViewer
              boundaryGeoJson={fieldBoundary}
              productAId={activeProductId}
              productBId={compareProductBId}
              metaA={activeVisualization}
              metaB={compareVisB}
            />
          ) : (
            /* Single Layer Interactive MapLibre View */
            <MapLibreViewer
              boundaryGeoJson={fieldBoundary}
              activeProductId={activeProductId}
              visualizationMeta={activeVisualization}
              opacity={opacity}
              onOpacityChange={setOpacity}
              onProbe={setProbedPoint}
            />
          )}

          {/* Quick Probed Value Banner */}
          {probedPoint && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-xs flex items-center justify-between text-emerald-900">
              <div className="flex items-center gap-2">
                <span className="font-semibold">Last Probed Pixel:</span>
                <span className="font-mono bg-white px-2 py-0.5 rounded border border-emerald-300 font-bold">
                  {probedPoint.is_valid ? `${probedPoint.value} ${probedPoint.unit}` : "NoData / Masked"}
                </span>
                <span className="text-emerald-700 text-[11px]">
                  ({probedPoint.lat.toFixed(5)}, {probedPoint.lon.toFixed(5)})
                </span>
              </div>
              <span className="text-[11px] text-emerald-600 italic">
                {probedPoint.description}
              </span>
            </div>
          )}
        </div>

        {/* Sidebar Controls & Product Selector (1 col) */}
        <div className="card-base p-5 space-y-5 flex flex-col justify-between">
          <div className="space-y-4">
            {/* Layer Selection */}
            <div className="border-b border-slate-100 pb-3">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  {isComparisonMode ? "Primary Layer (Left)" : "Validated Map Products"}
                </h2>
                <span className="text-[10px] text-slate-400 font-mono">
                  {products.length} Available
                </span>
              </div>

              {isLoadingLayer ? (
                <div className="flex items-center justify-center py-6 text-xs text-slate-400 gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-emerald-600" />
                  <span>Loading products...</span>
                </div>
              ) : products.length === 0 ? (
                <div className="p-3 bg-slate-50 rounded-lg text-xs text-slate-500 border border-dashed border-slate-200 text-center">
                  No validated raster products for this survey yet.
                </div>
              ) : (
                <div className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
                  {products.map((prod) => {
                    const isSelected = prod.id === activeProductId;
                    return (
                      <label
                        key={prod.id}
                        className={`flex items-start gap-2.5 text-xs p-2.5 rounded-lg border cursor-pointer transition ${
                          isSelected
                            ? "bg-emerald-50/70 border-emerald-300 shadow-xs"
                            : "bg-white border-slate-200 hover:bg-slate-50"
                        }`}
                      >
                        <input
                          type="radio"
                          name="product-radio"
                          checked={isSelected}
                          onChange={() => setActiveProductId(prod.id)}
                          className="mt-0.5 text-emerald-600 focus:ring-emerald-500"
                        />
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center justify-between gap-1">
                            <span
                              className={`font-bold truncate ${
                                isSelected ? "text-emerald-900" : "text-slate-800"
                              }`}
                            >
                              {prod.display_name}
                            </span>
                            {prod.has_raster_file ? (
                              <span className="text-[9px] font-mono bg-emerald-100 text-emerald-800 px-1 py-0.2 rounded shrink-0">
                                GeoTIFF
                              </span>
                            ) : (
                              <span className="text-[9px] font-mono bg-slate-100 text-slate-500 px-1 py-0.2 rounded shrink-0">
                                Metadata Only
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-1.5 text-[10px] text-slate-500 mt-0.5">
                            <span>{prod.crs_epsg}</span>
                            <span>&bull;</span>
                            <span>{prod.band_count} Band{prod.band_count > 1 ? "s" : ""}</span>
                            {prod.resolution_cm_px && (
                              <>
                                <span>&bull;</span>
                                <span>{prod.resolution_cm_px} cm/px</span>
                              </>
                            )}
                          </div>
                        </div>
                      </label>
                    );
                  })}
                </div>
              )}
            </div>

            {/* If Comparison Mode: Secondary Layer Selector */}
            {isComparisonMode && (
              <div className="border-b border-slate-100 pb-3">
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                  Secondary Layer (Right)
                </h2>
                <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                  {products.map((prod) => {
                    const isSelected = prod.id === compareProductBId;
                    return (
                      <label
                        key={`cmp-${prod.id}`}
                        className={`flex items-start gap-2.5 text-xs p-2 rounded-lg border cursor-pointer transition ${
                          isSelected
                            ? "bg-blue-50/70 border-blue-300 shadow-xs"
                            : "bg-white border-slate-200 hover:bg-slate-50"
                        }`}
                      >
                        <input
                          type="radio"
                          name="compare-radio"
                          checked={isSelected}
                          onChange={() => setCompareProductBId(prod.id)}
                          className="mt-0.5 text-blue-600 focus:ring-blue-500"
                        />
                        <div className="min-w-0 flex-1">
                          <span
                            className={`font-semibold text-xs truncate block ${
                              isSelected ? "text-blue-900" : "text-slate-800"
                            }`}
                          >
                            {prod.display_name}
                          </span>
                          <span className="text-[10px] text-slate-500 font-mono">
                            {prod.product_type}
                          </span>
                        </div>
                      </label>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Opacity Control */}
            <div className="space-y-1.5 border-b border-slate-100 pb-4">
              <div className="flex justify-between text-xs font-semibold text-slate-700">
                <span>Overlay Opacity</span>
                <span className="font-mono text-emerald-700">{Math.round(opacity * 100)}%</span>
              </div>
              <input
                type="range"
                min={0.1}
                max={1.0}
                step={0.05}
                value={opacity}
                onChange={(e) => setOpacity(parseFloat(e.target.value))}
                className="w-full accent-emerald-600 cursor-pointer"
              />
            </div>

            {/* Spatial Metadata Card */}
            <div className="bg-slate-50 rounded-lg p-3 space-y-1.5 text-xs border border-slate-200">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Survey Spatial Context
              </span>
              <div className="flex justify-between text-slate-600">
                <span>Field:</span>
                <span className="font-medium text-slate-800">
                  {selectedFieldObj?.field_name || "N/A"}
                </span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Crop:</span>
                <span className="font-medium text-slate-800">
                  {selectedFieldObj?.crop_type || "N/A"}
                </span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Flight Date:</span>
                <span className="font-mono font-medium text-slate-800">
                  {selectedSurveyObj?.flight_date || "N/A"}
                </span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Sensor:</span>
                <span className="font-medium text-slate-800">
                  {selectedSurveyObj?.sensor_type || "N/A"}
                </span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Boundary:</span>
                <span
                  className={`font-semibold ${
                    fieldBoundary ? "text-emerald-700" : "text-amber-600"
                  }`}
                >
                  {fieldBoundary ? "PostGIS Validated" : "No Geometry"}
                </span>
              </div>
            </div>
          </div>

          {/* Secure Deliverables */}
          <div className="pt-4 border-t border-slate-100 space-y-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
              Deliverables &amp; Diagnostics
            </span>
            {activeProductId && (
              <Link
                href={`/portal/diagnostics?product_id=${encodeURIComponent(activeProductId)}`}
                className="btn-primary w-full text-xs py-2.5 flex items-center justify-center gap-1.5"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Open Detailed Diagnostics</span>
              </Link>
            )}

            <button
              onClick={handleSimulateDownload}
              disabled={downloadingReport}
              className="btn-secondary w-full text-xs py-2 flex items-center justify-center gap-1.5"
            >
              <Download className="w-3.5 h-3.5" />
              <span>
                {downloadingReport ? "Generating Signed SAS URL..." : "Download PDF Report"}
              </span>
            </button>

            {downloadSuccess && (
              <p className="text-[11px] text-emerald-700 bg-emerald-50 border border-emerald-200 p-2 rounded-lg font-medium flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                <span>Signed Azure SAS URL ready (valid 15m)</span>
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
