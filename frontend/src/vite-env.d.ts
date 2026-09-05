/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE?: string;
  readonly VITE_SAMPLE_USER_NAME?: string;
  readonly VITE_SAMPLE_USER_EMAIL?: string;
  readonly VITE_SAMPLE_USER_PASSWORD?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
