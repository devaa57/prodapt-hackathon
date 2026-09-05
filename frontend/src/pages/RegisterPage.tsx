import { Link, Navigate } from "react-router-dom";
import { Info, ScanSearch } from "lucide-react";
import { useAuth } from "../AuthContext";
import { SAMPLE_USER_USERNAME, SAMPLE_USER_PASSWORD } from "../config";

export function RegisterPage() {
  const { user, login } = useAuth();

  if (user) return <Navigate to="/" replace />;

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
          <p className="font-display text-5xl leading-tight">Stand up a screening desk in minutes.</p>
          <p className="mt-6 text-lg text-slate-300">
            Create roles, attach requirement documents, and let the assistant surface interview-ready candidates.
          </p>
        </div>
        <p className="text-sm text-slate-500">Secure JWT authentication · AI-powered resume analysis</p>
      </div>
      <div className="flex items-center justify-center p-6">
        <div className="w-full max-w-md rounded-3xl bg-white p-8 shadow-card dark:bg-ink-950">
          <h2 className="text-2xl font-semibold text-ink-900 dark:text-white">Account access</h2>
          <p className="mt-1 text-sm text-slate-500">
            HireLens accounts are managed by your workspace administrator.
          </p>

          <div className="mt-6 rounded-xl border border-blue-200 bg-blue-50 p-4 dark:border-blue-900/40 dark:bg-blue-950/30">
            <div className="flex gap-3">
              <Info className="mt-0.5 h-4 w-4 shrink-0 text-blue-600 dark:text-blue-400" />
              <div className="text-sm text-blue-800 dark:text-blue-300">
                <p className="font-semibold">No self-registration</p>
                <p className="mt-1">
                  User accounts are provisioned by the backend administrator via environment variables. Contact your
                  admin to get access credentials.
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 rounded-xl border border-slate-200 p-4 dark:border-slate-800">
            <p className="text-sm font-medium text-ink-900 dark:text-white">Try the demo account</p>
            <p className="mt-1 text-sm text-slate-500">
              Username: <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs dark:bg-slate-800">{SAMPLE_USER_USERNAME}</code>
            </p>
            <button
              id="register-demo-login"
              onClick={() => login(SAMPLE_USER_USERNAME, SAMPLE_USER_PASSWORD)}
              className="mt-3 w-full rounded-xl border border-accent-500/50 bg-accent-500/10 py-2.5 text-sm font-semibold text-accent-600 hover:bg-accent-500/20 dark:text-accent-400"
            >
              Sign in with Demo Account
            </button>
          </div>

          <p className="mt-5 text-center text-sm text-slate-500">
            Already have credentials?{" "}
            <Link to="/login" className="font-medium text-accent-600">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
