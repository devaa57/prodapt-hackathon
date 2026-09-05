import { Laptop, Moon, Sun } from "lucide-react";
import { useAuth } from "../AuthContext";
import { useTheme, type Theme } from "../ThemeContext";

export function SettingsPage() {
  const { user } = useAuth();
  const { theme, setTheme } = useTheme();

  const themeOptions: { value: Theme; title: string; desc: string; icon: typeof Sun }[] = [
    { value: "light", title: "Light Mode", desc: "Clean bright contrast", icon: Sun },
    { value: "dark", title: "Dark Mode", desc: "Sleek low-light aesthetic", icon: Moon },
    { value: "system", title: "System Preference", desc: "Sync with OS theme settings", icon: Laptop },
  ];

  return (
    <div className="max-w-2xl space-y-6">
      <div className="rounded-2xl bg-white p-8 shadow-card">
        <h2 className="font-display text-3xl">Workspace settings</h2>
        <p className="mt-1 text-slate-500">Account details for this HireLens recruiter session.</p>
        <dl className="mt-8 grid gap-4">
          <div className="rounded-xl bg-slate-50 p-4">
            <dt className="text-xs uppercase tracking-wide text-slate-400">Name</dt>
            <dd className="mt-1 font-medium">{user?.name}</dd>
          </div>
          <div className="rounded-xl bg-slate-50 p-4">
            <dt className="text-xs uppercase tracking-wide text-slate-400">Email</dt>
            <dd className="mt-1 font-medium">{user?.email}</dd>
          </div>
          <div className="rounded-xl bg-slate-50 p-4">
            <dt className="text-xs uppercase tracking-wide text-slate-400">Role</dt>
            <dd className="mt-1 font-medium capitalize">{user?.role}</dd>
          </div>
        </dl>
      </div>

      <div className="rounded-2xl bg-white p-8 shadow-card">
        <h3 className="font-display text-2xl">Interface Theme</h3>
        <p className="mt-1 text-slate-500">Choose your preferred visual appearance across the recruiter workspace.</p>
        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          {themeOptions.map(({ value, title, desc, icon: Icon }) => (
            <button
              key={value}
              onClick={() => setTheme(value)}
              className={`flex flex-col items-start rounded-2xl border p-4 text-left transition ${
                theme === value
                  ? "border-accent-500 bg-accent-500/10 ring-2 ring-accent-400"
                  : "border-slate-200 bg-slate-50/50 hover:bg-slate-100/80"
              }`}
            >
              <div className={`rounded-xl p-2.5 ${theme === value ? "bg-accent-500 text-ink-950" : "bg-slate-200 text-slate-700"}`}>
                <Icon className="h-5 w-5" />
              </div>
              <p className="mt-3 font-semibold text-sm">{title}</p>
              <p className="mt-0.5 text-xs text-slate-500">{desc}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
