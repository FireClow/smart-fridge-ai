import { useCallback, useEffect, useRef, useState } from "react";
import { cvAnalyze } from "../services/api.js";

const DEFAULT_INTERVAL = 1500;

function captureFrame(video, canvas) {
  const w = video.videoWidth;
  const h = video.videoHeight;
  if (!w || !h) return null;
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;
  ctx.drawImage(video, 0, 0, w, h);
  return new Promise((resolve) => {
    canvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.9);
  });
}

/**
 * Drives a camera frame loop into POST /api/cv/analyze for the CV page.
 * Returns refs to attach to <video>/<canvas>, the latest analysis result,
 * and controls. Optical flow + tracking rely on consecutive frames, so the
 * loop must keep sending frames from the same browser session.
 */
export function useCvAnalysis({ preprocessMode = "none", intervalMs = DEFAULT_INTERVAL } = {}) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const inFlightRef = useRef(false);
  const abortRef = useRef(null);
  const timerRef = useRef(null);
  const modeRef = useRef(preprocessMode);

  const [result, setResult] = useState(null);
  const [running, setRunning] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    modeRef.current = preprocessMode;
  }, [preprocessMode]);

  const analyzeOnce = useCallback(async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || inFlightRef.current) return;

    const blob = await captureFrame(video, canvas);
    if (!blob) return;

    inFlightRef.current = true;
    abortRef.current?.abort();
    abortRef.current = new AbortController();
    try {
      const file = new File([blob], "frame.jpg", { type: "image/jpeg" });
      const data = await cvAnalyze(file, modeRef.current, abortRef.current.signal);
      setResult(data);
      setError(null);
    } catch (e) {
      if (
        e?.name !== "CanceledError" &&
        e?.code !== "ERR_CANCELED" &&
        !e?.message?.includes("canceled")
      ) {
        setError(e?.message || "CV analysis failed");
      }
    } finally {
      inFlightRef.current = false;
    }
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
        setError(
          e?.name === "NotAllowedError"
            ? "Camera permission denied."
            : "Could not open camera.",
        );
      }
    })();

    return () => {
      cancelled = true;
      const s = streamRef.current;
      if (s) for (const t of s.getTracks()) t.stop();
      streamRef.current = null;
      abortRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    if (!running) {
      if (timerRef.current) clearInterval(timerRef.current);
      return undefined;
    }
    timerRef.current = setInterval(() => {
      if (document.visibilityState === "visible") void analyzeOnce();
    }, intervalMs);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [running, intervalMs, analyzeOnce]);

  return {
    videoRef,
    canvasRef,
    result,
    metrics: result?.metrics ?? null,
    running,
    error,
    setRunning,
    analyzeOnce,
  };
}
