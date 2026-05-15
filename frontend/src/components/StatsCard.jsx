export function StatsCard({ label, value, sub, accent = "cyan" }) {
  const ring =
    accent === "blue"
      ? "from-blue-500/30 to-transparent"
      : accent === "violet"
        ? "from-violet-500/30 to-transparent"
        : "from-cyan-500/30 to-transparent";

  return (
    <div
      className={`group relative overflow-hidden rounded-2xl border border-gray-800 bg-gray-900/60 p-5 shadow-lg transition duration-300 hover:border-cyan-500/40 hover:shadow-glow`}
    >
      <div
        className={`pointer-events-none absolute -right-6 -top-6 h-24 w-24 rounded-full bg-gradient-to-br ${ring} blur-2xl`}
      />
      <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">
        {label}
      </p>
      <p className="mt-2 font-display text-3xl font-bold text-white tabular-nums">
        {value}
      </p>
      {sub ? (
        <p className="mt-1 text-xs text-gray-500 transition group-hover:text-gray-400">
          {sub}
        </p>
      ) : null}
    </div>
  );
}
