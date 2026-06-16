import { dev } from '$app/environment';

export interface FeedbackSubmitPayload {
	name: string;
	email: string;
	subject: string;
	message: string;
	pageUrl?: string;
	attachments?: File[];
	token?: string | null;
}

export interface FeedbackSubmitResponse {
	id: string;
	message: string;
	attachments?: Array<{
		id: string;
		original_filename: string;
		url: string;
	}>;
}

function getFeedbackApiUrl(): string {
	const host = import.meta.env.VITE_REMOTE_BACKEND_HOST || 'statsdoc.ai.mospi.gov.in';
	const isLocal = host.includes('localhost') || host.includes('127.0.0.1');
	const protocol = isLocal || dev ? 'http' : 'https';
	return `${protocol}://${host}/api/feedback/`;
}

export async function submitFeedback(
	payload: FeedbackSubmitPayload
): Promise<FeedbackSubmitResponse> {
	const pageUrl = payload.pageUrl || (typeof window !== 'undefined' ? window.location.href : '');
	const hasAttachments = payload.attachments && payload.attachments.length > 0;

	const headers: Record<string, string> = {};
	if (payload.token) {
		headers.Authorization = `Bearer ${payload.token}`;
	}

	let response: Response;

	if (hasAttachments) {
		const formData = new FormData();
		formData.append('name', payload.name);
		formData.append('email', payload.email);
		formData.append('subject', payload.subject);
		formData.append('message', payload.message);
		formData.append('page_url', pageUrl);
		formData.append('website', '');

		for (const file of payload.attachments!) {
			formData.append('attachments', file);
		}

		response = await fetch(getFeedbackApiUrl(), {
			method: 'POST',
			headers,
			body: formData
		});
	} else {
		headers['Content-Type'] = 'application/json';
		response = await fetch(getFeedbackApiUrl(), {
			method: 'POST',
			headers,
			body: JSON.stringify({
				name: payload.name,
				email: payload.email,
				subject: payload.subject,
				message: payload.message,
				page_url: pageUrl,
				website: ''
			})
		});
	}

	const data = await response.json().catch(() => ({}));

	if (!response.ok) {
		const detail =
			typeof data.detail === 'string'
				? data.detail
				: Object.entries(data)
						.map(([key, value]) => {
							if (Array.isArray(value)) return `${key}: ${value.join(', ')}`;
							return `${key}: ${String(value)}`;
						})
						.join('; ');
		throw new Error(detail || 'Failed to submit feedback');
	}

	return data as FeedbackSubmitResponse;
}
