import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  Briefcase,
  LayoutDashboard,
  LogOut,
  ScanSearch,
  Settings,
  Sparkles,
} from "lucide-react";
import { useAuth } from "../AuthContext";
import { ThemeToggle } from "./ThemeToggle";

const links = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/jobs", label: "Roles", icon: Briefcase },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#eef2f7] text-ink-900 dark:bg-[#08111e] dark:text-slate-100">
      <div className="flex min-h-screen">
        <aside className="sticky top-0 flex h-screen w-64 flex-col border-r border-slate-200 bg-white text-slate-800 transition-colors dark:border-slate-800/80 dark:bg-[#07111f] dark:text-slate-200">
          <div className="flex items-center gap-3 px-6 py-6 border-b border-slate-200 dark:border-slate-800/50">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-500 text-ink-950 shadow-md">
              <ScanSearch className="h-5 w-5" />
            </div>
            <div>
              <p className="font-semibold tracking-tight text-ink-900 dark:text-white">HireLens</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">AI screening assistant</p>
            </div>
          </div>
          <nav className="flex-1 space-y-1.5 px-3 py-4">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.to === "/"}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all ${
                    isActive
                      ? "bg-ink-900 text-white shadow-sm dark:bg-slate-800/90 dark:text-white"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800/50 dark:hover:text-white"
                  }`
                }
              >
                <link.icon className="h-4 w-4 text-accent-600 dark:text-accent-400" />
                {link.label}
              </NavLink>
            ))}
          </nav>
          <div className="m-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800/80 dark:bg-slate-900/60">
            <div className="mb-2 flex items-center gap-2 text-accent-600 dark:text-accent-300">
              <Sparkles className="h-4 w-4 text-accent-600 dark:text-accent-400" />
              <span className="text-xs font-semibold uppercase tracking-wider">Live matching</span>
            </div>
            <p className="text-xs leading-5 text-slate-500 dark:text-slate-400">
              Upload a requirement pack, drop resumes, and rank talent by skill, experience, and keyword fit.
            </p>
          </div>
          <button
            onClick={() => {
              logout();
              navigate("/login");
            }}
            className="m-3 flex items-center gap-2.5 rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm font-medium text-slate-600 hover:bg-rose-50 hover:text-rose-600 dark:border-slate-800/50 dark:text-slate-400 dark:hover:bg-rose-500/10 dark:hover:text-rose-400 transition"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </aside>
        <div className="min-w-0 flex-1">
          <header className="sticky top-0 z-20 flex items-center justify-between border-b border-slate-200/80 bg-white/80 px-8 py-4 backdrop-blur dark:border-slate-800 dark:bg-ink-950/80">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-400">Talent operations</p>
              <h1 className="text-lg font-semibold">Welcome back, {user?.name?.split(" ")[0]}</h1>
            </div>
            <div className="flex items-center gap-4">
              <ThemeToggle />
              <div className="text-right">
                <p className="text-sm font-medium">{user?.name}</p>
                <p className="text-xs capitalize text-slate-500">{user?.role}</p>
              </div>
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-ink-900 text-sm font-semibold text-accent-300">
                {user?.name?.slice(0, 1).toUpperCase()}
              </div>
            </div>
          </header>
          <main className="px-8 py-8">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}
