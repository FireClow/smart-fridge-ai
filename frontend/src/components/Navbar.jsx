import { StatusIndicator } from "./StatusIndicator.jsx";

export function Navbar({ online }) {
  return (
    <header className="mb-8 flex flex-col gap-4 border-b border-gray-800/80 pb-6 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-cyan-500/40 bg-gradient-to-br from-cyan-500/20 to-slate-900 shadow-glow-sm">
          <span className="text-2xl" aria-hidden>
            🧊
          </span>
        </div>
        <div>
          <p className="font-display text-xs font-semibold uppercase tracking-[0.35em] text-cyan-400/90">
            IoT Vision
          </p>
          <h1 className="font-display text-2xl font-bold tracking-tight text-white md:text-3xl">
            Smart Fridge{" "}
            <span className="text-glow bg-gradient-to-r from-cyan-300 to-blue-400 bg-clip-text text-transparent">
              AI
            </span>
          </h1>
          <p className="mt-1 max-w-xl text-sm text-gray-400">
            Real-time food inventory management using object detection
          </p>
        </div>
      </div>
      <StatusIndicator online={online} />
    </header>
  );
}
