// Centralized Environment Configuration

export const API_BASE =
  (import.meta.env.VITE_API_BASE as string | undefined)?.replace(/\/$/, "") || "http://localhost:8000";

export const SAMPLE_USER_NAME =
  (import.meta.env.VITE_SAMPLE_USER_NAME as string | undefined)?.trim() || "Recruiter Demo";

/** Backend login uses "username" field (not email) */
export const SAMPLE_USER_USERNAME =
  (import.meta.env.VITE_SAMPLE_USER_USERNAME as string | undefined)?.trim() ||
  (import.meta.env.VITE_SAMPLE_USER_EMAIL as string | undefined)?.trim() || // legacy fallback
  "demo";

export const SAMPLE_USER_PASSWORD =
  (import.meta.env.VITE_SAMPLE_USER_PASSWORD as string | undefined)?.trim() || "password123";
