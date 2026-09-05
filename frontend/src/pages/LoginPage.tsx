import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { ScanSearch } from "lucide-react";
import { useAuth } from "../AuthContext";
import { SAMPLE_USER_USERNAME, SAMPLE_USER_PASSWORD } from "../config";

export function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  function handleFillSample() {
    setUsername(SAMPLE_USER_USERNAME);
    setPassword(SAMPLE_USER_PASSWORD);
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(username, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in");
    } finally {
      setBusy(false);
    }
  }

  async function onDemoLogin() {
    setBusy(true);
    setError("");
    try {
      await login(SAMPLE_USER_USERNAME, SAMPLE_USER_PASSWORD);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-grid grid min-h-screen lg:grid-cols-2">
      <div className="hidden flex-col justify-between p-12 text-white lg:flex">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-accent-500 text-ink-950">
            <ScanSearch className="h-5 w-5" />
          </div>
          <span className="text-lg font-semibold">HireLens</span>
        </div>
        <div className="max-w-lg">
          <p className="font-display text-5xl leading-tight">Screen talent with the precision of a hiring desk.</p>
          <p className="mt-6 text-lg text-slate-300">
            Parse requirement packs, ingest candidate resumes, and rank every profile against skills, tenure, and role language.
          </p>
        </div>
        <p className="text-sm text-slate-500">Prodapt Hackathon 2026 · AI Resume Screening Assistant</p>
      </div>
      <div className="flex items-center justify-center p-6">
        <form onSubmit={onSubmit} className="w-full max-w-md rounded-3xl bg-white p-8 shadow-card dark:bg-ink-950">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-semibold text-ink-900 dark:text-white">Sign in</h2>
            <button
              type="button"
              onClick={handleFillSample}
              className="text-xs font-medium text-accent-600 hover:underline"
            >
              Fill Sample Demo
            </button>
          </div>
          <p className="mt-1 text-sm text-slate-500">Use your workspace credentials to sign in.</p>
          {error && <p className="mt-4 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
          <label className="mt-6 block text-sm font-medium">
            Username
            <input
              id="login-username"
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder={SAMPLE_USER_USERNAME}
              autoComplete="username"
              className="mt-1.5 w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none ring-accent-400 focus:ring-2 dark:border-slate-800 dark:bg-slate-900"
            />
          </label>
          <label className="mt-4 block text-sm font-medium">
            Password
            <input
              id="login-password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
              className="mt-1.5 w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none ring-accent-400 focus:ring-2 dark:border-slate-800 dark:bg-slate-900"
            />
          </label>
          <button
            id="login-submit"
            disabled={busy}
            className="mt-6 w-full rounded-xl bg-ink-900 py-3 text-sm font-semibold text-white hover:bg-ink-800 disabled:opacity-60"
          >
            {busy ? "Signing in…" : "Continue"}
          </button>

          <div className="relative my-6 flex items-center justify-center border-t border-slate-200 dark:border-slate-800">
            <span className="bg-white px-3 text-xs uppercase tracking-wider text-slate-400 dark:bg-ink-950">Or</span>
          </div>

          <button
            id="login-demo"
            type="button"
            onClick={onDemoLogin}
            disabled={busy}
            className="w-full rounded-xl border border-accent-500/50 bg-accent-500/10 py-3 text-sm font-semibold text-accent-600 hover:bg-accent-500/20 disabled:opacity-60 dark:text-accent-400"
          >
            Sign in with Demo Account ({SAMPLE_USER_USERNAME})
          </button>

          <p className="mt-5 text-center text-sm text-slate-500">
            New to HireLens?{" "}
            <Link to="/register" className="font-medium text-accent-600">
              Learn more
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
