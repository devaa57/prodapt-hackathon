import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Briefcase, FileCheck2, Sparkles, Users } from "lucide-react";
import { api } from "../api";
import type { Dashboard } from "../types";

export function DashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .dashboard()
      .then(setData)
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <p className="text-rose-600">{error}</p>;
  if (!data) return <p className="text-slate-500">Loading overview…</p>;

  const cards = [
    { label: "Open roles", value: data.jobs, icon: Briefcase },
    { label: "Candidates", value: data.candidates, icon: Users },
    { label: "Screened", value: data.screened, icon: FileCheck2 },
    { label: "Avg. match", value: `${data.avg_score}`, icon: Sparkles },
  ];

  const chart = Object.entries(data.score_buckets).map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-8">
      <div>
        <h2 className="font-display text-3xl">Hiring pulse</h2>
        <p className="mt-1 text-slate-500">A snapshot of screening volume, quality, and shortlists.</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <div key={card.label} className="rounded-2xl bg-white p-5 shadow-card">
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-500">{card.label}</p>
              <card.icon className="h-4 w-4 text-accent-500" />
            </div>
            <p className="mt-3 text-3xl font-semibold">{card.value}</p>
          </div>
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-5">
        <div className="rounded-2xl bg-white p-6 shadow-card lg:col-span-3">
          <h3 className="font-semibold">Score distribution</h3>
          <p className="mb-4 text-sm text-slate-500">How screened candidates cluster after matching.</p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chart}>
                <XAxis dataKey="name" axisLine={false} tickLine={false} />
                <YAxis allowDecimals={false} axisLine={false} tickLine={false} />
                <Tooltip />
                <Bar dataKey="value" fill="#14b8a6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="rounded-2xl bg-white p-6 shadow-card lg:col-span-2">
          <h3 className="font-semibold">Recent roles</h3>
          <div className="mt-4 space-y-3">
            {data.recent_jobs.length === 0 && <p className="text-sm text-slate-500">No roles yet. Create one to start screening.</p>}
            {data.recent_jobs.map((job) => (
              <Link
                key={job.id}
                to={`/jobs/${job.id}`}
                className="block rounded-xl border border-slate-100 p-3 hover:border-accent-400"
              >
                <p className="font-medium">{job.title}</p>
                <p className="text-xs text-slate-500">
                  {job.department || "General"} · {job.candidate_count} candidates · {job.screened_count} screened
                </p>
              </Link>
            ))}
          </div>
          <Link to="/jobs" className="mt-4 inline-block text-sm font-medium text-accent-600">
            Manage all roles →
          </Link>
        </div>
      </div>
    </div>
  );
}
