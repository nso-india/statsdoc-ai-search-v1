/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_NAME: string;
  readonly VITE_APP_VERSION: string;
  readonly VITE_APP_DESCRIPTION: string;
  readonly VITE_REMOTE_BACKEND_HOST: string;
  readonly VITE_LOCAL_BACKEND_HOST: string;
  readonly VITE_OPENAI_API_KEY: string;
  readonly VITE_OPENAI_API_URL: string;
  readonly VITE_GOOGLE_FONTS_URL: string;
  readonly VITE_GOOGLE_FONTS_STATIC_URL: string;
  // Add more env variables here as needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
