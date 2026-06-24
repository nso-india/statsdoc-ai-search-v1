import { dev } from '$app/environment';

export const APP_NAME = import.meta.env.VITE_APP_NAME || 'MOSPI';

export const REMOTE_BACKEND_HOST =
	import.meta.env.VITE_REMOTE_BACKEND_HOST ||
	(dev ? import.meta.env.VITE_LOCAL_BACKEND_HOST || 'localhost:8000' : 'statsdoc.ai.mospi.gov.in');
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
export const WEBUI_WS_BASE_URL = resolveWebuiWsUrl();
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
