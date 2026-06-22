import { browser, dev } from '$app/environment';

// App configuration constants following OpenWebUI format
export const APP_NAME = import.meta.env.VITE_APP_NAME || 'MOSPI';

export const REMOTE_BACKEND_HOST = import.meta.env.VITE_REMOTE_BACKEND_HOST || 'statsdoc.ai.mospi.gov.in';
export const LOCAL_BACKEND_HOST = import.meta.env.VITE_LOCAL_BACKEND_HOST || 'localhost:8000';

function isLocalBackendHost(host: string): boolean {
  return host.includes('localhost') || host.includes('127.0.0.1');
}

function resolveWebuiBaseUrl(): string {
  const host = REMOTE_BACKEND_HOST;
  const protocol = isLocalBackendHost(host) ? 'http' : 'https';
  return `${protocol}://${host}`;
}

function resolveWebuiWsUrl(): string {
  const host = REMOTE_BACKEND_HOST;
  if (isLocalBackendHost(host)) {
    return `ws://${host}`;
  }
  return `wss://${host}`;
}

export const WEBUI_HOSTNAME = REMOTE_BACKEND_HOST;
export const WEBUI_BASE_URL = resolveWebuiBaseUrl();
export const WEBUI_API_BASE_URL = `${WEBUI_BASE_URL}/api`;
export const WEBSOCKET_BASE_URL = resolveWebuiWsUrl();

export const WEBUI_VERSION = import.meta.env.VITE_APP_VERSION || '1.0.0';
export const WEBUI_DESCRIPTION = import.meta.env.VITE_APP_DESCRIPTION || 'Document Processing and Analysis Platform';

// Supported file types and extensions
export const SUPPORTED_FILE_TYPE = [
	'application/pdf',
	'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
	'application/msword',
	'application/vnd.openxmlformats-officedocument.presentationml.presentation',
	'application/vnd.ms-powerpoint',
	'text/plain',
	'text/csv',
	'text/html',
	'text/markdown'
];

export const SUPPORTED_FILE_EXTENSIONS = [
	'pdf',
	'docx',
	'doc',
	'pptx',
	'ppt',
	'txt',
	'csv',
	'html',
	'md'
];

// Themes following OpenWebUI pattern
export const THEMES = ['light', 'dark', 'system'] as const;
export type Theme = typeof THEMES[number];
