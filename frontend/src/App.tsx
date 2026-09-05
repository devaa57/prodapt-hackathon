import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import { useAuth } from "./AuthContext";
import { AppShell } from "./components/AppShell";
import { CandidatePage } from "./pages/CandidatePage";
import { DashboardPage } from "./pages/DashboardPage";
import { JobWorkspacePage } from "./pages/JobWorkspacePage";
import { JobsPage } from "./pages/JobsPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { SettingsPage } from "./pages/SettingsPage";

function Protected() {
  const { user, loading } = useAuth();
  if (loading) return <div className="grid min-h-screen place-items-center text-slate-500">Loading workspace…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<Protected />}>
        <Route element={<AppShell />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/jobs" element={<JobsPage />} />
          <Route path="/jobs/:id" element={<JobWorkspacePage />} />
          <Route path="/candidates/:id" element={<CandidatePage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Route>
    </Routes>
  );
}
