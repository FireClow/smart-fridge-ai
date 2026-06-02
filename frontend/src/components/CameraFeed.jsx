import { useCallback, useEffect, useRef, useState } from "react";
import { postScanImage } from "../services/api.js";
import { useSettings } from "../context/SettingsContext.jsx";

const AUTO_MS = 3000;

function captureVideoFrame(video, canvas) {
  const w = video.videoWidth;
  const h = video.videoHeight;
  if (!w || !h) return null;
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;
  ctx.drawImage(video, 0, 0, w, h);
  return new Promise((resolve) => {
    canvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.92);
  });
}

export function CameraFeed({ onScanComplete, confidence: confidenceProp }) {
  const { confidence: settingsConf, defaultAutoScan, preprocessMode } = useSettings();
  const confidence = confidenceProp ?? settingsConf;

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const scanInFlightRef = useRef(false);
  const abortRef = useRef(null);
  const autoTimerRef = useRef(null);

  const [cameraError, setCameraError] = useState(null);
  const [scanError, setScanError] = useState(null);
  const [scanSuccess, setScanSuccess] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [autoScan, setAutoScan] = useState(defaultAutoScan);
  const [preview, setPreview] = useState(null);

  const stopStream = useCallback(() => {
    const s = streamRef.current;
    if (s) {
      for (const t of s.getTracks()) t.stop();
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment", width: { ideal: 1280 } },
          audio: false,
        });
        if (cancelled) {
          for (const t of stream.getTracks()) t.stop();
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play().catch(() => {});
        }
      } catch (e) {
        setCameraError(
          e?.name === "NotAllowedError"
            ? "Camera permission denied."
            : "Could not open camera.",
        );
      }
    })();

    return () => {
      cancelled = true;
      stopStream();
    };
  }, [stopStream]);

  const runScan = useCallback(
    async (blob) => {
      if (!blob) {
        setScanError("Camera not ready. Wait for video to load.");
        return null;
      }
      if (scanInFlightRef.current) return null;

      scanInFlightRef.current = true;
      abortRef.current?.abort();
      abortRef.current = new AbortController();

      setScanError(null);
      setScanSuccess(null);
      setScanning(true);

      try {
        const file =
          blob instanceof File ? blob : new File([blob], "scan.jpg", { type: "image/jpeg" });
        const data = await postScanImage(
          file,
          confidence,
          abortRef.current.signal,
          preprocessMode,
        );
        if (data?.annotated_image_base64) {
          setPreview(`data:image/jpeg;base64,${data.annotated_image_base64}`);
        } else {
          setPreview(null);
        }
        const count = data?.detected_count ?? data?.items?.length ?? 0;
        const fps = data?.fps;
        setScanSuccess(
          count > 0
            ? `Detected ${count} item${count === 1 ? "" : "s"}${fps ? ` · ${fps.toFixed(1)} FPS` : ""}`
            : "No items detected above confidence threshold.",
        );
        onScanComplete?.(data);
        return data;
      } catch (e) {
        if (
          e?.name === "CanceledError" ||
          e?.code === "ERR_CANCELED" ||
          e?.message?.includes("canceled")
        ) {
          return null;
        }
        setScanError(e?.message || "Scan failed");
        return null;
      } finally {
        scanInFlightRef.current = false;
        setScanning(false);
      }
    },
    [confidence, onScanComplete, preprocessMode],
  );

  const scanFromVideo = useCallback(async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return null;
    const blob = await captureVideoFrame(video, canvas);
    return runScan(blob);
  }, [runScan]);

  const scheduleAutoScan = useCallback(() => {
    if (autoTimerRef.current) clearTimeout(autoTimerRef.current);
    if (!autoScan || cameraError) return;

    autoTimerRef.current = setTimeout(async () => {
      if (document.visibilityState !== "visible") {
        scheduleAutoScan();
        return;
      }
      if (!scanInFlightRef.current) {
        await scanFromVideo();
      }
      scheduleAutoScan();
    }, AUTO_MS);
  }, [autoScan, cameraError, scanFromVideo]);

  useEffect(() => {
    scheduleAutoScan();
    return () => {
      if (autoTimerRef.current) clearTimeout(autoTimerRef.current);
      abortRef.current?.abort();
    };
  }, [scheduleAutoScan]);

  const onFileChange = (e) => {
    const f = e.target.files?.[0];
    e.target.value = "";
    if (f) void runScan(f);
  };

  return (
    <section className="relative flex w-full flex-col overflow-hidden rounded-2xl border border-gray-800 bg-gray-950 shadow-inner">
      <canvas ref={canvasRef} className="hidden" aria-hidden />

      <div className="relative aspect-video w-full bg-black">
        <video
          ref={videoRef}
          className="h-full w-full object-cover"
          playsInline
          muted
          autoPlay
        />
        {scanning ? (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-black/40">
            <span className="h-12 w-12 animate-pulse rounded-full border-2 border-cyan-400 border-t-transparent" />
          </div>
        ) : null}
        {preview && !scanning ? (
          <>
            <button
              type="button"
              className="absolute bottom-2 right-2 z-10 rounded-lg border border-gray-600 bg-gray-900/90 px-2 py-1 text-xs text-gray-300 hover:bg-gray-800"
              onClick={() => setPreview(null)}
            >
              Hide overlay
            </button>
            <img
              src={preview}
              alt="Last detection preview"
              className="pointer-events-none absolute inset-0 h-full w-full object-contain opacity-90"
            />
          </>
        ) : null}
      </div>

      <div className="relative z-10 flex flex-wrap items-center gap-2 border-t border-gray-800/80 bg-gray-900/50 px-3 py-3">
        <span className="rounded-full border border-cyan-500/40 bg-cyan-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-cyan-300">
          Vision stream
        </span>
        <button
          type="button"
          disabled={!!cameraError || scanning}
          onClick={() => void scanFromVideo()}
          className="rounded-lg border border-cyan-600/50 bg-cyan-600/20 px-3 py-1.5 text-xs font-semibold text-cyan-200 hover:bg-cyan-600/30 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {scanning ? "Scanning…" : "Scan now"}
        </button>
        <label className="cursor-pointer rounded-lg border border-gray-600 bg-gray-800/80 px-3 py-1.5 text-xs font-medium text-gray-200 hover:bg-gray-800 disabled:opacity-40">
          <input
            type="file"
            accept="image/jpeg,image/png,image/*"
            className="sr-only"
            disabled={scanning}
            onChange={onFileChange}
          />
          Upload photo
        </label>
        <label className="flex cursor-pointer items-center gap-2 text-xs text-gray-400">
          <input
            type="checkbox"
            checked={autoScan}
            disabled={!!cameraError}
            onChange={(e) => setAutoScan(e.target.checked)}
          />
          Auto-scan / 3s
        </label>
        {autoScan ? (
          <span className="text-xs text-cyan-500/80">Auto active</span>
        ) : null}
        <span className="ml-auto flex items-center gap-2 text-xs text-gray-500">
          <span
            className={`h-1.5 w-1.5 rounded-full ${scanning ? "animate-pulse bg-cyan-400" : "bg-gray-600"}`}
          />
          YOLOv8
        </span>
      </div>

      {cameraError ? (
        <p className="border-t border-gray-800/80 px-3 py-2 text-xs text-amber-400/90">{cameraError}</p>
      ) : null}
      {scanSuccess ? (
        <p className="border-t border-gray-800/80 px-3 py-2 text-xs text-emerald-400/90">{scanSuccess}</p>
      ) : null}
      {scanError ? (
        <p className="border-t border-gray-800/80 px-3 py-2 text-xs text-red-400/90">{scanError}</p>
      ) : null}
    </section>
  );
}
