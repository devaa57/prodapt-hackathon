import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { MapPin, Plus, Sparkles, Trash2 } from "lucide-react";
import { api } from "../api";
import type { Job } from "../types";

export function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    title: "",
    department: "",
    location: "",
    employment_type: "Full-time",
    description: "",
  });

  async function load() {
    setJobs(await api.jobs());
  }

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api.createJob(form);
      setOpen(false);
      setForm({ title: "", department: "", location: "", employment_type: "Full-time", description: "" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create role");
    }
  }

  async function onSeedSample() {
    setBusy(true);
    setError("");
    try {
      await api.seedSampleJob();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not seed sample role");
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(id: number | string) {
    if (!confirm("Delete this role and its candidates?")) return;
    await api.deleteJob(id);
    await load();
  }

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="font-display text-3xl">Open roles</h2>
          <p className="mt-1 text-slate-500">Each role holds a requirement document and a candidate pipeline.</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={onSeedSample}
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60"
          >
            <Sparkles className="h-4 w-4 text-accent-600" />
            {busy ? "Seeding sample..." : "Load Sample Demo Role"}
          </button>
          <button
            onClick={() => setOpen(true)}
            className="inline-flex items-center gap-2 rounded-xl bg-ink-900 px-4 py-2.5 text-sm font-semibold text-white"
          >
            <Plus className="h-4 w-4" />
            New role
          </button>
        </div>
      </div>
      {error && <p className="mt-4 text-sm text-rose-600">{error}</p>}
      <div className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {jobs.map((job) => (
          <article key={job.id} className="rounded-2xl bg-white p-5 shadow-card">
            <div className="flex items-start justify-between gap-3">
              <div>
                <Link to={`/jobs/${job.id}`} className="text-lg font-semibold hover:text-accent-600">
                  {job.title}
                </Link>
                <p className="mt-1 text-sm text-slate-500">{job.department || "Unassigned department"}</p>
              </div>
              <button onClick={() => onDelete(job.id)} className="rounded-lg p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600">
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
            <p className="mt-4 flex items-center gap-1 text-sm text-slate-500">
              <MapPin className="h-4 w-4" />
              {job.location || "Remote / unspecified"} · {job.employment_type}
            </p>
            <div className="mt-5 grid grid-cols-3 gap-2 text-center">
              <div className="rounded-xl bg-slate-50 py-2">
                <p className="text-lg font-semibold">{job.candidate_count}</p>
                <p className="text-[11px] uppercase tracking-wide text-slate-400">Resumes</p>
              </div>
              <div className="rounded-xl bg-slate-50 py-2">
                <p className="text-lg font-semibold">{job.screened_count}</p>
                <p className="text-[11px] uppercase tracking-wide text-slate-400">Screened</p>
              </div>
              <div className="rounded-xl bg-slate-50 py-2">
                <p className="text-lg font-semibold">{job.has_requirement ? "Yes" : "No"}</p>
                <p className="text-[11px] uppercase tracking-wide text-slate-400">JD file</p>
              </div>
            </div>
          </article>
        ))}
        {jobs.length === 0 && (
          <div className="rounded-2xl border border-dashed border-slate-300 p-10 text-center text-slate-500 md:col-span-2">
            <p className="text-base font-medium text-slate-700">No roles found yet.</p>
            <p className="mt-1 text-sm">Create a custom role or load a pre-built sample role with candidate resumes.</p>
            <div className="mt-6 flex justify-center gap-3">
              <button
                onClick={onSeedSample}
                disabled={busy}
                className="inline-flex items-center gap-2 rounded-xl bg-accent-500 px-4 py-2.5 text-sm font-semibold text-ink-950 hover:bg-accent-400 disabled:opacity-60"
              >
                <Sparkles className="h-4 w-4" />
                Load Sample Demo Role
              </button>
              <button
                onClick={() => setOpen(true)}
                className="inline-flex items-center gap-2 rounded-xl bg-ink-900 px-4 py-2.5 text-sm font-semibold text-white"
              >
                <Plus className="h-4 w-4" />
                Create custom role
              </button>
            </div>
          </div>
        )}
      </div>

      {open && (
        <div className="fixed inset-0 z-30 flex items-center justify-center bg-ink-950/50 p-4">
          <form onSubmit={onCreate} className="w-full max-w-lg rounded-3xl bg-white p-6 shadow-card">
            <h3 className="text-xl font-semibold">Create role</h3>
            <div className="mt-4 grid gap-3">
              <input
                required
                placeholder="Role title"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                className="rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:ring-2 focus:ring-accent-400"
              />
              <div className="grid gap-3 sm:grid-cols-2">
                <input
                  placeholder="Department"
                  value={form.department}
                  onChange={(e) => setForm({ ...form, department: e.target.value })}
                  className="rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:ring-2 focus:ring-accent-400"
                />
                <input
                  placeholder="Location"
                  value={form.location}
                  onChange={(e) => setForm({ ...form, location: e.target.value })}
                  className="rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:ring-2 focus:ring-accent-400"
                />
              </div>
              <select
                value={form.employment_type}
                onChange={(e) => setForm({ ...form, employment_type: e.target.value })}
                className="rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:ring-2 focus:ring-accent-400"
              >
                <option>Full-time</option>
                <option>Contract</option>
                <option>Internship</option>
              </select>
              <textarea
                rows={4}
                placeholder="Optional notes (the uploaded requirement document is the source of truth)"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                className="rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:ring-2 focus:ring-accent-400"
              />
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <button type="button" onClick={() => setOpen(false)} className="rounded-xl px-4 py-2 text-sm text-slate-500">
                Cancel
              </button>
              <button className="rounded-xl bg-ink-900 px-4 py-2 text-sm font-semibold text-white">Save role</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
