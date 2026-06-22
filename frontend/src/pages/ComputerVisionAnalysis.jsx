import { useCallback, useEffect, useRef, useState } from "react";
import { CornerPanel } from "../components/CornerPanel.jsx";
import { FlowPanel } from "../components/FlowPanel.jsx";
import { OrbPanel } from "../components/OrbPanel.jsx";
import { StatsCard } from "../components/StatsCard.jsx";
import { TrackingPanel } from "../components/TrackingPanel.jsx";
import { PREPROCESS_MODES, useSettings } from "../context/SettingsContext.jsx";
import { useCvAnalysis } from "../hooks/useCvAnalysis.js";
import { ALLOWED_IMAGE_ACCEPT, validateImageFile } from "../lib/imageUpload.js";

const PREPROCESS_LABELS = {
  none: "None",
  gaussian: "Gaussian",
  bilateral: "Bilateral",
  clahe: "CLAHE",
};

export function ComputerVisionAnalysis() {
  const { preprocessMode, setPreprocessMode } = useSettings();
  const {
    result,
    metrics,
    error,
    setError,
    analyzing,
    panelLoading,
    hasImage,
    analyzeFile,
    clearImage,
  } = useCvAnalysis({ preprocessMode });

  const [uploadLabel, setUploadLabel] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");
  const [uploadPreview, setUploadPreview] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    return () => {
      if (uploadPreview) URL.revokeObjectURL(uploadPreview);
    };
  }, [uploadPreview]);

  const onUploadAnalyze = useCallback(
    async (e) => {
      const file = e.target.files?.[0];
      e.target.value = "";
      if (!file) return;

      const validated = validateImageFile(file);
      if (!validated.ok) {
        setUploadSuccess("");
        setUploadLabel("");
        if (uploadPreview) URL.revokeObjectURL(uploadPreview);
        setUploadPreview(null);
        setError(validated.message);
        return;
      }

      setUploadSuccess("");
      setError(null);
      setUploadLabel(validated.file.name);
      if (uploadPreview) URL.revokeObjectURL(uploadPreview);
      setUploadPreview(URL.createObjectURL(validated.file));

      const analyzed = await analyzeFile(validated.file);
      if (analyzed) {
        setUploadSuccess(`Analysis complete for ${validated.file.name}.`);
      }
    },
    [analyzeFile, setError, uploadPreview],
  );

  const openFilePicker = useCallback(() => {
    if (!analyzing) fileInputRef.current?.click();
  }, [analyzing]);

  const onClearImage = useCallback(() => {
    if (uploadPreview) URL.revokeObjectURL(uploadPreview);
    setUploadPreview(null);
    setUploadLabel("");
    setUploadSuccess("");
    clearImage();
  }, [clearImage, uploadPreview]);

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-bold text-white">Computer Vision Analysis</h1>
          <p className="mt-1 text-sm text-gray-500">
            Upload a photo to run filtering, corners, ORB, optical flow, and feature tracking.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-400">
            Filter
            <select
              value={preprocessMode}
              onChange={(e) => setPreprocessMode(e.target.value)}
              disabled={!hasImage || analyzing}
              className="ml-2 rounded-lg border border-gray-700 bg-gray-950 px-2 py-1 text-sm text-white disabled:opacity-50"
            >
              {PREPROCESS_MODES.map((m) => (
                <option key={m} value={m}>
                  {PREPROCESS_LABELS[m] ?? m}
                </option>
              ))}
            </select>
          </label>
          {hasImage ? (
            <button
              type="button"
              disabled={analyzing}
              onClick={onClearImage}
              className="rounded-lg border border-gray-600 bg-gray-800/80 px-3 py-1.5 text-xs font-semibold text-gray-200 hover:bg-gray-800 disabled:opacity-50"
            >
              Clear image
            </button>
          ) : null}
          <button
            type="button"
            disabled={analyzing}
            onClick={openFilePicker}
            className="rounded-lg border border-violet-600/50 bg-violet-600/20 px-3 py-1.5 text-xs font-semibold text-violet-200 hover:bg-violet-600/30 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {analyzing ? "Analyzing…" : hasImage ? "Upload another" : "Upload image"}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept={ALLOWED_IMAGE_ACCEPT}
            className="sr-only"
            onChange={onUploadAnalyze}
            disabled={analyzing}
          />
        </div>
      </div>

      {!hasImage ? (
        <button
          type="button"
          onClick={openFilePicker}
          className="flex w-full flex-col items-center justify-center rounded-2xl border-2 border-dashed border-gray-700 bg-gray-900/30 py-16 text-center transition hover:border-violet-600/50 hover:bg-violet-950/20"
        >
          <span className="text-lg font-semibold text-white">Upload an image to start</span>
          <span className="mt-2 text-sm text-gray-500">JPG, PNG, or WEBP — max 5 MB</span>
        </button>
      ) : (
        <p className="text-xs text-violet-300/90">
          Analysis source: <span className="font-semibold">UPLOAD</span>
          {analyzing ? " (analyzing…)" : ""} — <span className="font-medium">{uploadLabel}</span>
        </p>
      )}

      {uploadSuccess ? (
        <p className="rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-300">
          {uploadSuccess}
        </p>
      ) : null}

      {error ? (
        <p className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-300">
          {error}
        </p>
      ) : null}

      {hasImage ? (
        <>
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <StatsCard label="Harris corners" value={metrics?.harris_count ?? "—"} />
            <StatsCard label="Shi-Tomasi" value={metrics?.shi_tomasi_count ?? "—"} accent="blue" />
            <StatsCard label="ORB features" value={metrics?.orb_keypoints ?? "—"} accent="violet" />
            <StatsCard
              label="Active tracks"
              value={metrics?.active_tracks ?? "—"}
              accent="blue"
            />
            <StatsCard
              label="Flow magnitude"
              value={
                metrics?.optical_flow_magnitude != null
                  ? Number(metrics.optical_flow_magnitude).toFixed(2)
                  : "—"
              }
              accent="violet"
            />
          </section>

          <div className="overflow-hidden rounded-2xl border border-gray-800 bg-black">
            {uploadPreview ? (
              <img
                src={uploadPreview}
                alt="Uploaded preview"
                className="max-h-[480px] w-full object-contain"
              />
            ) : null}
          </div>

          <section className="grid gap-6 lg:grid-cols-2">
            <CornerPanel
              image={result?.corner_image_base64}
              harrisCount={metrics?.harris_count}
              shiTomasiCount={metrics?.shi_tomasi_count}
              loading={panelLoading}
            />
            <OrbPanel
              image={result?.orb_image_base64}
              keypointCount={metrics?.orb_keypoints}
              descriptorCount={metrics?.orb_descriptors}
              loading={panelLoading}
            />
            <FlowPanel
              image={result?.flow_image_base64}
              magnitude={metrics?.optical_flow_magnitude}
              pointCount={metrics?.flow_point_count}
              loading={panelLoading}
              unavailable={result?.flow_unavailable}
              message={result?.flow_message}
            />
            <TrackingPanel
              image={result?.tracking_image_base64}
              activeTracks={metrics?.active_tracks}
              loading={panelLoading}
              unavailable={result?.tracking_unavailable}
              message={result?.tracking_message}
            />
          </section>
        </>
      ) : null}
    </div>
  );
}
