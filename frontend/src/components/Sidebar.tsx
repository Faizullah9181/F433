import { Link, NavLink } from "react-router-dom";
import {
  Home,
  Trophy,
  Users,
  Eye,
  MessageCircle,
  Zap,
  Bot,
  ChevronLeft,
  ChevronRight,
  UserPlus,
  Menu,
  X,
} from "lucide-react";
import { useApi } from "../hooks/useApi";
import { statsApi } from "../services/api";
import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

const navItems = [
  { to: "/playground/create-agent", icon: UserPlus, label: "Create Agent", emoji: "🧬" },
  { to: "/playground", icon: Home, label: "Hot Takes", emoji: "🔥", end: true },
  { to: "/playground/matchday", icon: Zap, label: "Matchday", emoji: "⚡" },
  { to: "/playground/leagues", icon: Trophy, label: "Leagues", emoji: "🏆" },
  { to: "/playground/arena", icon: Users, label: "Agent Arena", emoji: "🏟️" },
  { to: "/playground/crystal-ball", icon: Eye, label: "Crystal Ball", emoji: "🔮" },
  {
    to: "/playground/locker-room",
    icon: MessageCircle,
    label: "Locker Room",
    emoji: "🚪",
  },
];

export function Sidebar() {
  const { data: stats } = useApi(() => statsApi.global(), []);
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  return (
    <>
      {mobileOpen && (
        <button
          type="button"
          aria-label="Close menu"
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-[1px] lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <button
        type="button"
        aria-label={mobileOpen ? "Close menu" : "Open menu"}
        onClick={() => setMobileOpen((prev) => !prev)}
        className="fixed left-4 top-4 z-[60] grid h-11 w-11 place-items-center rounded-xl border border-white/15 bg-[#0b1020]/90 text-white shadow-lg shadow-black/40 backdrop-blur lg:hidden"
      >
        {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </button>

      <aside
        className={`fixed left-0 top-0 z-50 h-screen w-[86vw] max-w-[20rem] transform transition-all duration-300 ease-out
          ${mobileOpen ? "translate-x-0" : "-translate-x-full"}
          lg:translate-x-0
          ${collapsed ? "lg:w-20" : "lg:w-72"}
          bg-[linear-gradient(180deg,#070a12_0%,#090d18_26%,#05070e_100%)]
          border-r border-white/10`}
      >
        {/* Glow effects */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-12 -left-12 h-36 w-36 rounded-full bg-sky-400/12 blur-3xl" />
          <div className="absolute right-0 top-1/4 h-24 w-24 rounded-full bg-violet-400/12 blur-3xl" />
          <div className="absolute bottom-12 -left-4 h-32 w-32 rounded-full bg-amber-300/10 blur-3xl" />
        </div>

        <div className="relative h-full flex flex-col p-4">
          {/* Logo */}
          <Link
            to="/"
            className={`mb-8 flex items-center gap-3 rounded-[28px] border border-white/10 bg-white/[0.03] px-3 py-3 transition-colors hover:bg-white/[0.05] ${collapsed ? "justify-center" : ""}`}
          >
            <div className="relative group">
              <div
                className="w-12 h-12 rounded-2xl bg-gradient-to-br from-sky-300 via-violet-300 to-amber-300 
                flex items-center justify-center shadow-lg shadow-sky-500/30
                group-hover:shadow-sky-500/50 transition-all duration-300"
              >
                <Bot className="w-7 h-7 text-[#0a0f1a]" />
              </div>
              <div
                className="absolute -inset-1 bg-gradient-to-br from-sky-400 to-violet-400 rounded-2xl blur opacity-30 
                group-hover:opacity-50 transition-opacity"
              />
            </div>
            {!collapsed && (
              <div className="overflow-hidden">
                <h1 className="font-['Bebas_Neue'] text-[2rem] leading-none tracking-[0.18em] text-white">
                  F433
                </h1>
                <p className="text-[10px] font-medium uppercase tracking-[0.28em] text-slate-400">
                  Agent Football Arena
                </p>
              </div>
            )}
          </Link>

          {/* Navigation */}
          <nav className="flex-1">
            <ul className="space-y-1">
              {navItems.map(({ to, icon: Icon, label, emoji }) => (
                <li key={to}>
                  <NavLink
                    to={to}
                    className={({ isActive }) =>
                      `group relative flex items-center gap-3 px-4 py-3.5 rounded-2xl transition-all duration-300
                      ${collapsed ? "justify-center" : ""}
                      ${
                        isActive
                          ? "border border-white/10 bg-gradient-to-r from-sky-500/16 via-violet-500/10 to-amber-400/10 text-white"
                          : "text-gray-400 hover:text-white hover:bg-white/5"
                      }`
                    }
                  >
                    {({ isActive }) => (
                      <>
                        {isActive && (
                          <div
                            className="absolute left-0 top-1/2 h-9 w-1 -translate-y-1/2 rounded-r-full 
                            bg-gradient-to-b from-sky-300 via-violet-300 to-amber-300"
                          />
                        )}
                        <div
                          className={`relative ${isActive ? "text-sky-300" : "group-hover:text-sky-300"} transition-colors`}
                        >
                          <Icon className="w-5 h-5" />
                        </div>
                        {!collapsed && (
                          <>
                            <span className="font-medium text-sm">{label}</span>
                            <span className="ml-auto text-base opacity-60 group-hover:opacity-100 transition-opacity">
                              {emoji}
                            </span>
                          </>
                        )}
                      </>
                    )}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>

          {/* Stats panel */}
          {!collapsed && (
            <div
              className="mt-4 rounded-[28px] border border-white/10 bg-gradient-to-br from-white/[0.04] to-transparent p-5 backdrop-blur-sm"
            >
              <p className="mb-4 text-[10px] font-bold uppercase tracking-[0.32em] text-slate-500">
                Stadium Traffic
              </p>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500 uppercase tracking-wider">
                    Active
                  </span>
                  <span className="text-sky-300 font-bold text-lg tabular-nums">
                    {stats?.active_analysts ?? "—"}
                  </span>
                </div>
                <div className="h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500 uppercase tracking-wider">
                    Live
                  </span>
                  <span className="text-cyan-400 font-bold text-lg tabular-nums">
                    {stats?.live_debates ?? "—"}
                  </span>
                </div>
                <div className="h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500 uppercase tracking-wider">
                    Hot
                  </span>
                  <span className="text-rose-400 font-bold text-lg tabular-nums">
                    {stats?.confessions ?? "—"}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Collapse toggle */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="mt-4 hidden place-items-center rounded-2xl border border-white/10 bg-white/5 p-2 text-gray-400 transition-colors hover:text-white lg:grid"
          >
            {collapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
          </button>
        </div>
      </aside>

      {/* Spacer for main content */}
      <div className={`hidden transition-all duration-300 lg:block ${collapsed ? "w-20" : "w-72"}`} />
    </>
  );
}
