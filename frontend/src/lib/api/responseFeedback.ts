import { WEBUI_API_BASE_URL } from '$lib/constants';

export type ResponseFeedbackRating = 'up' | 'down';

export interface ResponseFeedbackCategory {
	value: string;
	label: string;
}

export const RESPONSE_FEEDBACK_CATEGORIES: ResponseFeedbackCategory[] = [
	{ value: 'incorrect_incomplete', label: 'Incorrect or incomplete' },
	{ value: 'not_what_asked', label: 'Not what I asked for' },
	{ value: 'wrong_document', label: 'Wrong document / source' },
	{ value: 'language_issue', label: 'Language or translation issue' },
	{ value: 'slow_buggy', label: 'Slow or buggy' },
	{ value: 'style_tone', label: 'Style or tone' },
	{ value: 'safety_legal', label: 'Safety or legal concern' },
	{ value: 'other', label: 'Other' }
];

export interface ResponseFeedbackSummary {
	message_id: number;
	rating: ResponseFeedbackRating;
	category: string;
	updated_at: string;
}

export interface SubmitResponseFeedbackPayload {
	messageId: number;
	rating: ResponseFeedbackRating;
	category?: string;
	details?: string;
	token?: string | null;
}

function authHeaders(token?: string | null): Record<string, string> {
	const headers: Record<string, string> = {
		'Content-Type': 'application/json'
	};
	if (token) {
		headers.Authorization = `Bearer ${token}`;
	}
	return headers;
}

export async function fetchChatResponseFeedback(
	chatId: string | number,
	token?: string | null
): Promise<ResponseFeedbackSummary[]> {
	const response = await fetch(
		`${WEBUI_API_BASE_URL}/feedback/response/chat/${chatId}/`,
		{
			headers: authHeaders(token)
		}
	);

	if (!response.ok) {
		return [];
	}

	return response.json();
}

export async function submitResponseFeedback(
	payload: SubmitResponseFeedbackPayload
): Promise<ResponseFeedbackSummary> {
	const response = await fetch(`${WEBUI_API_BASE_URL}/feedback/response/`, {
		method: 'POST',
		headers: authHeaders(payload.token),
		body: JSON.stringify({
			message_id: payload.messageId,
			rating: payload.rating,
			category: payload.category || '',
			details: payload.details || ''
		})
	});

	const contentType = response.headers.get('content-type') || '';
	const data = contentType.includes('application/json')
		? await response.json().catch(() => ({}))
		: {};

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
		throw new Error(detail || `Failed to submit feedback (HTTP ${response.status})`);
	}

	return {
		message_id: data.message_id,
		rating: data.rating,
		category: data.category || '',
		updated_at: data.updated_at
	};
}
