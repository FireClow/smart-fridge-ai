import { useCallback, useEffect, useRef, useState } from "react";
import { CornerPanel } from "../components/CornerPanel.jsx";
import { EventsPanel } from "../components/EventsPanel.jsx";
import { FilterComparison } from "../components/FilterComparison.jsx";
import { FlowPanel } from "../components/FlowPanel.jsx";
import { MatchPanel } from "../components/MatchPanel.jsx";
import { OrbPanel } from "../components/OrbPanel.jsx";
import { StatsCard } from "../components/StatsCard.jsx";
import { TrackingPanel } from "../components/TrackingPanel.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { PREPROCESS_MODES, useSettings } from "../context/SettingsContext.jsx";
import { useCvAnalysis } from "../hooks/useCvAnalysis.js";
import { ALLOWED_IMAGE_ACCEPT, validateImageFile } from "../lib/imageUpload.js";
import { cvDetectEvents, fetchCvEvents, fetchModelInfo } from "../services/api.js";
import { subscribeCvEvents, supabase } from "../services/supabase.js";

const PREPROCESS_LABELS = {
  none: "None",
  gaussian: "Gaussian",
  bilateral: "Bilateral",
  clahe: "CLAHE",
};

export function ComputerVisionAnalysis() {
  const { user } = useAuth();
  const { preprocessMode, setPreprocessMode } = useSettings();
  const { videoRef, canvasRef, result, metrics, running, error, setRunning, setError, analyzeFile } = useCvAnalysis({
    preprocessMode,
  });

  const [classNames, setClassNames] = useState([]);
  const [matchScore, setMatchScore] = useState(null);
  const [events, setEvents] = useState([]);
  const [detections, setDetections] = useState({});
  const [eventBusy, setEventBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadLabel, setUploadLabel] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");
  const [uploadPreview, setUploadPreview] = useState(null);
  const captureCanvasRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    void (async () => {
      try {
        const info = await fetchModelInfo();
        if (info?.classes) setClassNames(info.classes);
      } catch {
        /* ignore */
      }
    })();
  }, []);

  const loadEvents = useCallback(async () => {
    try {
      const rows = await fetchCvEvents(20);
      if (Array.isArray(rows)) setEvents(rows);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    void loadEvents();
    if (!supabase) return undefined;
    const unsub = subscribeCvEvents(() => void loadEvents(), user?.id ?? null);
    return unsub;
  }, [loadEvents, user?.id]);

  useEffect(() => {
    return () => {
      if (uploadPreview) URL.revokeObjectURL(uploadPreview);
    };
  }, [uploadPreview]);

  const captureFrame = useCallback(async () => {
    const video = videoRef.current;
    const canvas = captureCanvasRef.current;
    if (!video || !canvas) return null;
    const w = video.videoWidth;
    const h = video.videoHeight;
    if (!w || !h) return null;
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    ctx.drawImage(video, 0, 0, w, h);
    const blob = await new Promise((resolve) =>
      canvas.toBlob((b) => resolve(b), "image/jpeg", 0.9),
    );
    if (!blob) return null;
    return new File([blob], "frame.jpg", { type: "image/jpeg" });
  }, [videoRef]);

  const detectEvents = useCallback(async () => {
    setEventBusy(true);
    try {
      const file = await captureFrame();
      if (!file) return;
      const data = await cvDetectEvents(file);
      setDetections(data?.detections ?? {});
      if (data?.events?.length) {
        // Optimistically show; realtime/loadEvents will reconcile persisted rows.
        setEvents((prev) => [
          ...data.events.map((e) => ({ ...e, created_at: new Date().toISOString() })),
          ...prev,
        ].slice(0, 20));
      }
      void loadEvents();
    } catch {
      /* ignore */
    } finally {
      setEventBusy(false);
    }
  }, [captureFrame, loadEvents]);

  const onUploadAnalyze = useCallback(async (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;

    const validated = validateImageFile(file);
    if (!validated.ok) {
      setUploadSuccess("");
      setUploadLabel("");
      setUploadPreview(null);
      setError(validated.message);
      return;
    }

    setUploadSuccess("");
    setError(null);
    setRunning(false);
    setUploading(true);
    setUploadLabel(validated.file.name);
    setUploadPreview(URL.createObjectURL(validated.file));

    try {
      const analyzed = await analyzeFile(validated.file);
      if (analyzed) {
        setUploadSuccess(`Analysis complete for ${validated.file.name}.`);
      }
    } finally {
      setUploading(false);
    }
  }, [analyzeFile, setError, setRunning]);

  const openFilePicker = useCallback(() => {
    if (!uploading) fileInputRef.current?.click();
  }, [uploading]);

  const yoloCount = Object.values(detections).reduce((a, b) => a + Number(b || 0), 0);

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-bold text-white">Computer Vision Analysis</h1>
          <p className="mt-1 text-sm text-gray-500">
            Classical CV pipeline: filtering, corners, ORB, matching, homography, optical flow,
            and tracking.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-400">
            Filter
            <select
              value={preprocessMode}
              onChange={(e) => setPreprocessMode(e.target.value)}
              className="ml-2 rounded-lg border border-gray-700 bg-gray-950 px-2 py-1 text-sm text-white"
            >
              {PREPROCESS_MODES.map((m) => (
                <option key={m} value={m}>
                  {PREPROCESS_LABELS[m] ?? m}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            onClick={() => {
              setRunning((v) => {
                const next = !v;
                if (next) {
                  setUploadPreview(null);
                  setUploadLabel("");
                  setUploadSuccess("");
                }
                return next;
              });
            }}
            className="rounded-lg border border-cyan-600/50 bg-cyan-600/20 px-3 py-1.5 text-xs font-semibold text-cyan-200 hover:bg-cyan-600/30"
          >
            {running ? "Pause" : "Resume"}
          </button>
          <button
            type="button"
            disabled={uploading}
            onClick={openFilePicker}
            className="rounded-lg border border-violet-600/50 bg-violet-600/20 px-3 py-1.5 text-xs font-semibold text-violet-200 hover:bg-violet-600/30 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {uploading ? "Analyzing..." : "Upload image"}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept={ALLOWED_IMAGE_ACCEPT}
            className="sr-only"
            onChange={onUploadAnalyze}
            disabled={uploading}
          />
        </div>
      </div>

      {uploadLabel ? (
        <p className="text-xs text-violet-300/90">
          Showing uploaded analysis: <span className="font-medium">{uploadLabel}</span>
        </p>
      ) : null}

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

      {/* Metric cards (Phase 9) */}
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7">
        <StatsCard label="Harris corners" value={metrics?.harris_count ?? "—"} />
        <StatsCard label="Shi-Tomasi" value={metrics?.shi_tomasi_count ?? "—"} accent="blue" />
        <StatsCard label="ORB features" value={metrics?.orb_keypoints ?? "—"} accent="violet" />
        <StatsCard
          label="Match score"
          value={matchScore != null ? Number(matchScore).toFixed(2) : "—"}
        />
        <StatsCard label="Active tracks" value={metrics?.active_tracks ?? "—"} accent="blue" />
        <StatsCard
          label="Flow magnitude"
          value={metrics?.optical_flow_magnitude != null
            ? Number(metrics.optical_flow_magnitude).toFixed(2)
            : "—"}
          accent="violet"
        />
        <StatsCard label="YOLO detections" value={yoloCount || "—"} />
      </section>

      {/* Live camera */}
      <section className="grid gap-6 lg:grid-cols-2">
        <div className="overflow-hidden rounded-2xl border border-gray-800 bg-black">
          {uploadPreview && !running ? (
            <img
              src={uploadPreview}
              alt="Uploaded preview"
              className="h-full w-full object-cover"
            />
          ) : (
            <video
              ref={videoRef}
              className="h-full w-full object-cover"
              playsInline
              muted
              autoPlay
            />
          )}
          <canvas ref={canvasRef} className="hidden" aria-hidden />
          <canvas ref={captureCanvasRef} className="hidden" aria-hidden />
        </div>
        <FilterComparison
          original={result?.original_image_base64}
          filtered={result?.filtered_image_base64}
          mode={metrics?.preprocess_mode ?? preprocessMode}
        />
      </section>

      {/* Stage 1 visual panels */}
      <section className="grid gap-6 lg:grid-cols-2">
        <CornerPanel
          image={result?.corner_image_base64}
          harrisCount={metrics?.harris_count}
          shiTomasiCount={metrics?.shi_tomasi_count}
        />
        <OrbPanel
          image={result?.orb_image_base64}
          keypointCount={metrics?.orb_keypoints}
          descriptorCount={metrics?.orb_descriptors}
        />
        <FlowPanel
          image={result?.flow_image_base64}
          magnitude={metrics?.optical_flow_magnitude}
          pointCount={metrics?.flow_point_count}
        />
        <TrackingPanel
          image={result?.tracking_image_base64}
          activeTracks={metrics?.active_tracks}
        />
      </section>

      {/* Matching / homography + events */}
      <section className="grid gap-6 lg:grid-cols-2">
        <MatchPanel classNames={classNames} captureFrame={captureFrame} onScore={setMatchScore} />
        <EventsPanel events={events} busy={eventBusy} onDetect={() => void detectEvents()} />
      </section>
    </div>
  );
}
