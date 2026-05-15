export function StatusIndicator({ online }) {
  return (
    <div className="flex items-center gap-2 rounded-full border border-gray-700 bg-gray-900/80 px-3 py-1.5">
      <span
        className={`relative flex h-2.5 w-2.5 ${
          online ? "animate-pulse" : ""
        }`}
      >
        <span
          className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${
            online ? "animate-ping bg-emerald-400" : "bg-red-500"
          }`}
        />
        <span
          className={`relative inline-flex h-2.5 w-2.5 rounded-full ${
            online ? "bg-emerald-400" : "bg-red-500"
          }`}
        />
      </span>
      <span className="text-xs font-medium tracking-wide text-gray-300">
        {online ? "System Online" : "Offline / Demo data"}
      </span>
    </div>
  );
}
