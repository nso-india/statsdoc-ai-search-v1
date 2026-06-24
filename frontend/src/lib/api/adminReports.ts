import { WEBUI_API_BASE_URL } from '$lib/constants';
import { tokenManager } from '$lib/auth/tokenManager';

export interface PaginatedResponse<T> {
	count: number;
	page?: number;
	page_size?: number;
	results: T[];
	breakdown?: T[];
	details?: T[];
}

export interface ReportDefinition {
	slug: string;
	name: string;
	phase: number;
	category: string;
	description: string;
}

export interface AdminReportMeta {
	form_statuses: Array<{ value: string; label: string }>;
	form_categories: Array<{ value: string; label: string }>;
	response_ratings: Array<{ value: string; label: string }>;
	response_categories: Array<{ value: string; label: string }>;
	reports: ReportDefinition[];
}

export interface ReportFilters {
	from_date?: string;
	to_date?: string;
	status?: string;
	category?: string;
	rating?: string;
	q?: string;
	page?: number;
	page_size?: number;
}

function buildUrl(path: string, filters: ReportFilters): string {
	const params = new URLSearchParams();
	Object.entries(filters).forEach(([key, value]) => {
		if (value !== undefined && value !== null && String(value).trim() !== '') {
			params.set(key, String(value));
		}
	});
	const query = params.toString();
	return query ? `${path}?${query}` : path;
}

async function parseError(response: Response): Promise<string> {
	try {
		const data = await response.json();
		return data.detail || data.message || `Request failed (${response.status})`;
	} catch {
		return `Request failed (${response.status})`;
	}
}

async function downloadExcel(url: string, fallbackName: string): Promise<void> {
	const response = await tokenManager.makeAuthenticatedRequest(url);
	if (!response.ok) {
		throw new Error(await parseError(response));
	}

	const blob = await response.blob();
	const disposition = response.headers.get('Content-Disposition') || '';
	const match = disposition.match(/filename="?([^"]+)"?/);
	const filename = match?.[1] || fallbackName;

	const objectUrl = URL.createObjectURL(blob);
	const link = document.createElement('a');
	link.href = objectUrl;
	link.download = filename;
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
	URL.revokeObjectURL(objectUrl);
}

export async function fetchAdminReportMeta(): Promise<AdminReportMeta> {
	const response = await tokenManager.makeAuthenticatedRequest(`${WEBUI_API_BASE_URL}/reports/meta/`);
	if (!response.ok) {
		throw new Error(await parseError(response));
	}
	return response.json();
}

export async function fetchReportData<T>(
	slug: string,
	filters: ReportFilters = {}
): Promise<PaginatedResponse<T>> {
	const response = await tokenManager.makeAuthenticatedRequest(
		buildUrl(`${WEBUI_API_BASE_URL}/reports/${slug}/`, filters)
	);
	if (!response.ok) {
		throw new Error(await parseError(response));
	}
	return response.json();
}

export async function downloadReportExcel(
	slug: string | null,
	filters: ReportFilters = {}
): Promise<void> {
	const exportFilters = { ...filters };
	delete exportFilters.page;
	delete exportFilters.page_size;

	const url = slug
		? buildUrl(`${WEBUI_API_BASE_URL}/reports/${slug}/export/`, exportFilters)
		: buildUrl(`${WEBUI_API_BASE_URL}/reports/export/`, exportFilters);

	await downloadExcel(
		url,
		slug ? `${slug}_report_${Date.now()}.xlsx` : `admin_reports_${Date.now()}.xlsx`
	);
}
