import { useState } from "react";
import { cvHomography, cvMatch, uploadReferenceImage } from "../services/api.js";

/**
 * Course topics: Feature Matching (ORB + BFMatcher Hamming) and Homography
 * (findHomography + RANSAC) with perspective correction.
 *
 * Workflow: pick a food class, store a reference image, then match the current
 * capture against it and optionally estimate homography + warp to frontal view.
 */
export function MatchPanel({ classNames = [], captureFrame, onScore }) {
  const [className, setClassName] = useState("");
  const [matchResult, setMatchResult] = useState(null);
  const [homographyResult, setHomographyResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [info, setInfo] = useState(null);

  const typedClass = className.trim();

  async function getCurrentFile(fallbackFile) {
    if (fallbackFile) return fallbackFile;
    if (captureFrame) return captureFrame();
    return null;
  }

  const onUploadReference = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file || !typedClass) {
      setError("Choose a class name first, then a reference image.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await uploadReferenceImage(typedClass, file);
      setInfo(`Reference image stored for "${typedClass}".`);
    } catch (err) {
      setError(err?.message || "Reference upload failed.");
    } finally {
      setBusy(false);
    }
  };

  const runMatch = async (fallbackFile) => {
    if (!typedClass) {
      setError("Enter or select a food class first.");
      return;
    }
    const file = await getCurrentFile(fallbackFile);
    if (!file) {
      setError("No current image. Capture a frame or upload one.");
      return;
    }
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      const data = await cvMatch(file, typedClass);
      setMatchResult(data);
      setHomographyResult(null);
      onScore?.(data.match_score);
    } catch (err) {
      setError(err?.message || "Matching failed.");
    } finally {
      setBusy(false);
    }
  };

  const runHomography = async (fallbackFile) => {
    if (!typedClass) {
      setError("Enter or select a food class first.");
      return;
    }
    const file = await getCurrentFile(fallbackFile);
    if (!file) {
      setError("No current image. Capture a frame or upload one.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const data = await cvHomography(file, typedClass, true);
      setHomographyResult(data);
      onScore?.(data.match_score);
    } catch (err) {
      setError(err?.message || "Homography failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="rounded-2xl border border-gray-800 bg-gray-900/50 p-4">
      <h3 className="mb-3 font-display text-sm font-semibold text-white">
        Feature matching &amp; homography
      </h3>

      <div className="flex flex-wrap items-center gap-2">
        <input
          list="cv-class-list"
          value={className}
          onChange={(e) => setClassName(e.target.value)}
          placeholder="food class (e.g. apple)"
          className="rounded-lg border border-gray-700 bg-gray-950 px-3 py-1.5 text-sm text-white"
        />
        <datalist id="cv-class-list">
          {classNames.map((c) => (
            <option key={c} value={c} />
          ))}
        </datalist>

        <label className="cursor-pointer rounded-lg border border-gray-600 bg-gray-800/80 px-3 py-1.5 text-xs font-medium text-gray-200 hover:bg-gray-800">
          <input type="file" accept="image/*" className="sr-only" onChange={onUploadReference} />
          Set reference
        </label>

        <button
          type="button"
          disabled={busy}
          onClick={() => void runMatch()}
          className="rounded-lg border border-cyan-600/50 bg-cyan-600/20 px-3 py-1.5 text-xs font-semibold text-cyan-200 hover:bg-cyan-600/30 disabled:opacity-40"
        >
          {busy ? "Working…" : "Match current frame"}
        </button>

        <button
          type="button"
          disabled={busy}
          onClick={() => void runHomography()}
          className="rounded-lg border border-violet-600/50 bg-violet-600/20 px-3 py-1.5 text-xs font-semibold text-violet-200 hover:bg-violet-600/30 disabled:opacity-40"
        >
          Perspective correction
        </button>

        <label className="cursor-pointer rounded-lg border border-gray-600 bg-gray-800/80 px-3 py-1.5 text-xs font-medium text-gray-200 hover:bg-gray-800">
          <input
            type="file"
            accept="image/*"
            className="sr-only"
            onChange={(e) => {
              const f = e.target.files?.[0];
              e.target.value = "";
              if (f) void runMatch(f);
            }}
          />
          Match uploaded image
        </label>
      </div>

      {error ? <p className="mt-2 text-xs text-red-400">{error}</p> : null}
      {info ? <p className="mt-2 text-xs text-emerald-400">{info}</p> : null}

      {matchResult ? (
        <div className="mt-4">
          <div className="grid grid-cols-2 gap-3 text-center text-xs text-gray-400 sm:grid-cols-4">
            <Metric label="Matches" value={matchResult.match_count} />
            <Metric label="Score" value={matchResult.match_score} />
            <Metric label="Ref KP" value={matchResult.ref_keypoints} />
            <Metric label="Cur KP" value={matchResult.cur_keypoints} />
          </div>
          {matchResult.match_image_base64 ? (
            <figure className="mt-3">
              <img
                src={`data:image/jpeg;base64,${matchResult.match_image_base64}`}
                alt="Matched keypoints"
                className="w-full rounded-lg border border-gray-800 object-contain"
              />
              <figcaption className="mt-1 text-center text-xs text-gray-500">
                Reference (left) vs current (right) — matched keypoints
              </figcaption>
            </figure>
          ) : null}
        </div>
      ) : null}

      {homographyResult ? (
        <div className="mt-4">
          <div className="grid grid-cols-3 gap-3 text-center text-xs text-gray-400">
            <Metric label="Inliers" value={homographyResult.inliers} />
            <Metric label="Outliers" value={homographyResult.outliers} />
            <Metric label="Score" value={homographyResult.match_score} />
          </div>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {homographyResult.match_image_base64 ? (
              <figure>
                <img
                  src={`data:image/jpeg;base64,${homographyResult.match_image_base64}`}
                  alt="Inlier/outlier matches"
                  className="w-full rounded-lg border border-gray-800 object-contain"
                />
                <figcaption className="mt-1 text-center text-xs text-gray-500">
                  Inliers (green) vs outliers (red)
                </figcaption>
              </figure>
            ) : null}
            {homographyResult.warped_image_base64 ? (
              <figure>
                <img
                  src={`data:image/jpeg;base64,${homographyResult.warped_image_base64}`}
                  alt="Perspective-corrected view"
                  className="w-full rounded-lg border border-violet-800/50 object-contain"
                />
                <figcaption className="mt-1 text-center text-xs text-gray-500">
                  Warped to frontal view
                </figcaption>
              </figure>
            ) : (
              <div className="flex items-center justify-center rounded-lg border border-dashed border-gray-700 p-4 text-xs text-gray-500">
                Not enough matches to warp.
              </div>
            )}
          </div>
        </div>
      ) : null}
    </section>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-lg border border-gray-800 bg-gray-950/60 p-2">
      <p className="text-[10px] uppercase tracking-wider text-gray-500">{label}</p>
      <p className="mt-0.5 font-display text-lg font-bold text-white tabular-nums">
        {value ?? "—"}
      </p>
    </div>
  );
}
