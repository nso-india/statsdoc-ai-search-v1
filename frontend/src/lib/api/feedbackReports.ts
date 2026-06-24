import { WEBUI_API_BASE_URL } from '$lib/constants';
import { tokenManager } from '$lib/auth/tokenManager';

export interface PaginatedResponse<T> {
	count: number;
	page: number;
	page_size: number;
	results: T[];
}

export interface FeedbackAttachment {
	id: string;
	original_filename: string;
	content_type: string;
	file_size: number;
	url: string;
	created_at: string;
}

export interface FormFeedbackItem {
	id: string;
	user: number | null;
	name: string;
	email: string;
	category: string;
	subject: string;
	message: string;
	page_url: string;
	status: string;
	attachments: FeedbackAttachment[];
	created_at: string;
	updated_at: string;
}

export interface ResponseFeedbackItem {
	id: string;
	message_id: number;
	chat_id: number;
	user_email: string;
	user_username: string;
	rating: 'up' | 'down';
	category: string;
	category_label: string;
	details: string;
	user_question: string;
	assistant_response: string;
	created_at: string;
	updated_at: string;
}

export interface FeedbackReportFilters {
	from_date?: string;
	to_date?: string;
	status?: string;
	category?: string;
	rating?: string;
	q?: string;
	page?: number;
	page_size?: number;
}

export interface FeedbackReportMeta {
	form_statuses: Array<{ value: string; label: string }>;
	form_categories: Array<{ value: string; label: string }>;
	response_ratings: Array<{ value: string; label: string }>;
	response_categories: Array<{ value: string; label: string }>;
}

function buildQuery(filters: FeedbackReportFilters): string {
	const params = new URLSearchParams();
	Object.entries(filters).forEach(([key, value]) => {
		if (value !== undefined && value !== null && String(value).trim() !== '') {
			params.set(key, String(value));
		}
	});
	const query = params.toString();
	return query ? `?${query}` : '';
}

async function parseError(response: Response): Promise<string> {
	try {
		const data = await response.json();
		return data.detail || data.message || `Request failed (${response.status})`;
	} catch {
		return `Request failed (${response.status})`;
	}
}

export async function fetchFeedbackReportMeta(): Promise<FeedbackReportMeta> {
	const response = await tokenManager.makeAuthenticatedRequest(
		`${WEBUI_API_BASE_URL}/feedback/reports/meta/`
	);
	if (!response.ok) {
		throw new Error(await parseError(response));
	}
	return response.json();
}

export async function fetchFormFeedbackList(
	filters: FeedbackReportFilters = {}
): Promise<PaginatedResponse<FormFeedbackItem>> {
	const response = await tokenManager.makeAuthenticatedRequest(
		`${WEBUI_API_BASE_URL}/feedback/list${buildQuery(filters)}`
	);
	if (!response.ok) {
		throw new Error(await parseError(response));
	}
	return response.json();
}

export async function fetchResponseFeedbackList(
	filters: FeedbackReportFilters = {}
): Promise<PaginatedResponse<ResponseFeedbackItem>> {
	const response = await tokenManager.makeAuthenticatedRequest(
		`${WEBUI_API_BASE_URL}/feedback/response/list${buildQuery(filters)}`
	);
	if (!response.ok) {
		throw new Error(await parseError(response));
	}
	return response.json();
}

export async function downloadFeedbackReportExcel(
	filters: FeedbackReportFilters = {}
): Promise<void> {
	const response = await tokenManager.makeAuthenticatedRequest(
		`${WEBUI_API_BASE_URL}/feedback/reports/export${buildQuery(filters)}`
	);
	if (!response.ok) {
		throw new Error(await parseError(response));
	}

	const blob = await response.blob();
	const disposition = response.headers.get('Content-Disposition') || '';
	const match = disposition.match(/filename="?([^"]+)"?/);
	const filename = match?.[1] || `feedback_report_${Date.now()}.xlsx`;

	const objectUrl = URL.createObjectURL(blob);
	const link = document.createElement('a');
	link.href = objectUrl;
	link.download = filename;
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
	URL.revokeObjectURL(objectUrl);
}
