/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the FastAPI backend in production builds. */
  readonly VITE_API_URL?: string;
  /** "true" serves the generated demo dataset instead of calling the backend. */
  readonly VITE_DEMO_MODE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
