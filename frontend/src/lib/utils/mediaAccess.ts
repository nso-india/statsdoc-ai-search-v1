/**
 * Utility functions for accessing protected media files
 */

import { WEBUI_BASE_URL } from '$lib/constants';
import { tokenManager } from '$lib/auth/tokenManager';

function resolveProtectedMediaUrl(url: string): string {
	if (url.startsWith('http://') || url.startsWith('https://')) {
		try {
			const parsed = new URL(url);
			return `${WEBUI_BASE_URL}${parsed.pathname}${parsed.search}`;
		} catch {
			return url;
		}
	}

	const normalizedPath = url.startsWith('/') ? url : `/${url}`;
	return `${WEBUI_BASE_URL}${normalizedPath}`;
}

/**
 * Opens a protected media file in a new tab with authentication
 * @param url - The media file URL or API path (e.g. /media/... or /api/files/1/raw/)
 */
export async function openProtectedMedia(url: string | null | undefined): Promise<void> {
	try {
		if (!url) {
			console.error('No URL provided to openProtectedMedia');
			alert('File URL is not available');
			return;
		}

		console.log('Opening protected media:', url);

		const fullUrl = resolveProtectedMediaUrl(url);
		console.log('Full URL:', fullUrl);

		const response = await tokenManager.makeAuthenticatedRequest(fullUrl, {
			method: 'GET'
		});

		console.log('Response status:', response.status, response.statusText);

		if (!response.ok) {
			throw new Error(`Failed to fetch file: ${response.status} ${response.statusText}`);
		}

		// Get content type from response headers
		const contentType = response.headers.get('content-type') || 'application/pdf';
		console.log('Content type:', contentType);

		// Get the blob with the correct MIME type
		const blob = await response.blob();
		const typedBlob = new Blob([blob], { type: contentType });
		const objectUrl = URL.createObjectURL(typedBlob);

		console.log('Created object URL:', objectUrl);

		// Open in new tab
		const newWindow = window.open(objectUrl, '_blank', 'noopener,noreferrer');
		
		// Clean up the object URL after a longer delay to ensure it loads
		if (newWindow) {
			// Revoke the object URL after 10 seconds to allow the file to load
			setTimeout(() => {
				URL.revokeObjectURL(objectUrl);
				console.log('Object URL revoked');
			}, 10000);
		} else {
			// If popup was blocked, try to download instead
			const link = document.createElement('a');
			link.href = objectUrl;
			link.download = url.split('/').pop() || 'download';
			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
			
			setTimeout(() => {
				URL.revokeObjectURL(objectUrl);
			}, 1000);
			
			alert('Popup blocked. File download started instead.');
		}
	} catch (error) {
		console.error('Error opening protected media:', error);
		alert(`Failed to open file: ${error instanceof Error ? error.message : 'Unknown error'}`);
	}
}

/**
 * Gets the authorization header for authenticated requests
 */
export function getAuthHeader(): { Authorization: string } | {} {
	const token = localStorage.getItem('access_token');
	return token ? { Authorization: `Bearer ${token}` } : {};
}
