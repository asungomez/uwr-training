/// <reference types="vite/client" />

interface ImportMetaEnv {
  // Optional override of the API base. Defaults to the same-origin "/api" proxy.
  readonly VITE_API_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
