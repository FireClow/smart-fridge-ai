import { NavLink } from "react-router-dom";
import { StatusIndicator } from "./StatusIndicator.jsx";

const links = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/inventory", label: "Inventory" },
  { to: "/history", label: "History" },
  { to: "/notifications", label: "Notifications" },
  { to: "/settings", label: "Settings" },
];

export function AppNav({ online, yoloLoaded, apiDown }) {
  return (
    <header className="border-b border-gray-800/80 bg-gray-950/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-cyan-500/40 bg-gradient-to-br from-cyan-500/20 to-slate-900">
            <span className="text-xl" aria-hidden>
              🧊
            </span>
          </div>
          <div>
            <p className="font-display text-xs font-semibold uppercase tracking-[0.3em] text-cyan-400/90">
              Smart Fridge AI
            </p>
            <p className="text-xs text-gray-500">
              {yoloLoaded === false ? "Model offline" : "Vision pipeline ready"}
            </p>
          </div>
        </div>
        <nav className="flex flex-wrap gap-1">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              className={({ isActive }) =>
                `rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                  isActive
                    ? "bg-cyan-600/20 text-cyan-200"
                    : "text-gray-400 hover:bg-gray-800/80 hover:text-gray-200"
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
        <StatusIndicator online={online} apiDown={apiDown} />
      </div>
    </header>
  );
}
