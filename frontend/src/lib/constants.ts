import { browser, dev } from '$app/environment';

export const APP_NAME = import.meta.env.VITE_APP_NAME || 'MOSPI';

// CONNECT TO REMOTE BACKEND FOR PRODUCTION
export const REMOTE_BACKEND_HOST = import.meta.env.VITE_REMOTE_BACKEND_HOST || 'statsdoc.ai.mospi.gov.in';
// Force use of remote backend
export const WEBUI_HOSTNAME = browser ? REMOTE_BACKEND_HOST : 'web:8000';
export const WEBUI_BASE_URL = browser ? `https://${REMOTE_BACKEND_HOST}` : `http://web:8000`;
export const WEBUI_API_BASE_URL = `${WEBUI_BASE_URL}/api`;

// WebSocket configuration
export const WEBUI_WS_BASE_URL = browser 
	? (dev ? 'ws://localhost:8000' : `wss://${REMOTE_BACKEND_HOST}`)
	: `ws://web:8000`;
export const WEBSOCKET_BASE_URL = WEBUI_WS_BASE_URL;

export const WEBUI_VERSION = import.meta.env.VITE_APP_VERSION || '1.0.0';

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

export const PASTED_TEXT_CHARACTER_LIMIT = 1000;
