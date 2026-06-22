/** Unified CV analysis source: uploaded file takes priority over webcam. */

export const ANALYSIS_SOURCE = {
  UPLOAD: "upload",
  WEBCAM: "webcam",
};

export function logAnalysisSource(source) {
  const label = source === ANALYSIS_SOURCE.UPLOAD ? "UPLOAD" : "WEBCAM";
  console.log("Analysis source:", label);
}
