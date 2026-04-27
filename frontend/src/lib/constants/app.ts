import { browser, dev } from '$app/environment';

// App configuration constants following OpenWebUI format
export const APP_NAME = import.meta.env.VITE_APP_NAME || 'MOSPI';

// Force use of remote backend
const isLocalhost = false; // Always use remote backend

// CONNECT TO REMOTE BACKEND FOR PRODUCTION
export const REMOTE_BACKEND_HOST = import.meta.env.VITE_REMOTE_BACKEND_HOST || 'statsdoc.ai.mospi.gov.in';
export const LOCAL_BACKEND_HOST = import.meta.env.VITE_LOCAL_BACKEND_HOST || 'localhost:8000';

export const WEBUI_HOSTNAME = browser 
  ? REMOTE_BACKEND_HOST
  : 'web:8000';

export const WEBUI_BASE_URL = browser 
  ? `https://${REMOTE_BACKEND_HOST}`
  : `http://web:8000`;

export const WEBUI_API_BASE_URL = `${WEBUI_BASE_URL}/api`;

// WebSocket URL - use wss for remote backend
export const WEBSOCKET_BASE_URL = browser 
  ? `wss://${REMOTE_BACKEND_HOST}`
  : `ws://web:8000`;

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
