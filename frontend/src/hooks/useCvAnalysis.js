import { useCallback, useEffect, useRef, useState } from "react";
import { ANALYSIS_SOURCE, logAnalysisSource } from "../lib/cvAnalysisSource.js";
import { cvAnalyze } from "../services/api.js";

/**
 * Upload-only CV analysis — no webcam or realtime loop.
 */
export function useCvAnalysis({ preprocessMode = "none" } = {}) {
  const uploadedFileRef = useRef(null);
  const requestGenRef = useRef(0);
  const abortRef = useRef(null);
  const modeRef = useRef(preprocessMode);
  const lastPreprocessRef = useRef(null);

  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [hasImage, setHasImage] = useState(false);

  useEffect(() => {
    modeRef.current = preprocessMode;
  }, [preprocessMode]);

  const runAnalysis = useCallback(async (file) => {
    const reqId = ++requestGenRef.current;
    setAnalyzing(true);
    setError(null);
    abortRef.current?.abort();
    abortRef.current = new AbortController();
    try {
      logAnalysisSource(ANALYSIS_SOURCE.UPLOAD);
      const data = await cvAnalyze(
        file,
        modeRef.current,
        abortRef.current.signal,
        ANALYSIS_SOURCE.UPLOAD,
      );
      if (reqId !== requestGenRef.current) return null;
      setResult(data);
      setError(null);
      return data;
    } catch (e) {
      if (reqId !== requestGenRef.current) return null;
      if (
        e?.name !== "CanceledError" &&
        e?.code !== "ERR_CANCELED" &&
        !e?.message?.includes("canceled")
      ) {
        setError(e?.message || "CV analysis failed");
        setResult(null);
      }
      return null;
    } finally {
      if (reqId === requestGenRef.current) setAnalyzing(false);
    }
  }, []);

  const analyzeFile = useCallback(
    async (file) => {
      if (!file) return null;
      uploadedFileRef.current = file;
      setHasImage(true);
      setResult(null);
      return runAnalysis(file);
    },
    [runAnalysis],
  );

  const clearImage = useCallback(() => {
    uploadedFileRef.current = null;
    setHasImage(false);
    setResult(null);
    setError(null);
    lastPreprocessRef.current = null;
    requestGenRef.current += 1;
    abortRef.current?.abort();
  }, []);

  const getAnalysisSourceFile = useCallback(async () => {
    if (!uploadedFileRef.current) return null;
    logAnalysisSource(ANALYSIS_SOURCE.UPLOAD);
    return uploadedFileRef.current;
  }, []);

  useEffect(() => {
    if (!hasImage || !uploadedFileRef.current) {
      lastPreprocessRef.current = null;
      return;
    }
    if (lastPreprocessRef.current === null) {
      lastPreprocessRef.current = preprocessMode;
      return;
    }
    if (lastPreprocessRef.current === preprocessMode) return;
    lastPreprocessRef.current = preprocessMode;
    void runAnalysis(uploadedFileRef.current);
  }, [preprocessMode, hasImage, runAnalysis]);

  const panelLoading = analyzing || (hasImage && !result && !error);

  return {
    result,
    metrics: result?.metrics ?? null,
    error,
    setError,
    analyzing,
    panelLoading,
    hasImage,
    analyzeFile,
    clearImage,
    getAnalysisSourceFile,
  };
}
