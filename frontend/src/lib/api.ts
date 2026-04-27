import type { 
	LoginRequest, 
	LoginResponse, 
	TokenRefreshRequest, 
	TokenRefreshResponse, 
	ApiResponse,
	FileUploadRequest,
	FileUploadResponse,
	MultiFileUploadResponse,
	UploadedFile,
	UserProfile
} from './types';
import { browser } from '$app/environment';
import { WEBUI_API_BASE_URL } from './constants/app';

// API base configuration - use the constant from app config
const API_BASE_URL = WEBUI_API_BASE_URL;

// Create a fetch wrapper with error handling
async function apiRequest<T>(
	endpoint: string,
	options: RequestInit = {}
): Promise<ApiResponse<T>> {
	try {
		const token = localStorage.getItem('access_token');
		
		const config: RequestInit = {
			headers: {
				'Content-Type': 'application/json',
				...(token && { Authorization: `Bearer ${token}` }),
				...options.headers,
			},
			...options,
		};

		const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
		const data = await response.json();

		if (!response.ok) {
			return {
				success: false,
				error: data.detail || data.message || 'An error occurred',
				data: undefined
			};
		}

		return {
			success: true,
			data,
		};
	} catch (error) {
		return {
			success: false,
			error: error instanceof Error ? error.message : 'Network error',
			data: undefined
		};
	}
}

// File upload wrapper for FormData
async function apiUploadRequest<T>(
	endpoint: string,
	formData: FormData
): Promise<ApiResponse<T>> {
	try {
		const token = localStorage.getItem('access_token');
		
		const config: RequestInit = {
			method: 'POST',
			headers: {
				...(token && { Authorization: `Bearer ${token}` }),
			},
			body: formData,
		};

		const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
		const data = await response.json();

		if (!response.ok) {
			return {
				success: false,
				error: data.detail || data.message || 'An error occurred',
				data: null
			};
		}

		return {
			success: true,
			data,
		};
	} catch (error) {
		return {
			success: false,
			error: error instanceof Error ? error.message : 'Network error',
			data: null
		};
	}
}

// Authentication API functions
export const authApi = {
	async login(credentials: LoginRequest): Promise<ApiResponse<LoginResponse>> {
		const response = await apiRequest<LoginResponse>('/token/', {
			method: 'POST',
			body: JSON.stringify(credentials),
		});

		if (response.success && response.data) {
			// Store tokens in localStorage
			localStorage.setItem('access_token', response.data.access);
			localStorage.setItem('refresh_token', response.data.refresh);
			
			// Fetch user role data and merge it with the basic user data
			try {
				const { UsersAPI } = await import('./api/users.js');
				const roleData = await UsersAPI.getCurrentUserRole();
				const enrichedUser = {
					...response.data.user,
					role: roleData.role,
					access_level: roleData.access_level
				};
				localStorage.setItem('user', JSON.stringify(enrichedUser));
			} catch (error) {
				console.error('Failed to fetch user role:', error);
				// Fallback to basic user data
				localStorage.setItem('user', JSON.stringify(response.data.user));
			}
		}

		return response;
	},

	async refreshToken(): Promise<ApiResponse<TokenRefreshResponse>> {
		const refreshToken = localStorage.getItem('refresh_token');
		
		if (!refreshToken) {
			return {
				success: false,
				error: 'No refresh token available',
				data: null
			};
		}

		const response = await apiRequest<TokenRefreshResponse>('/token/refresh/', {
			method: 'POST',
			body: JSON.stringify({ refresh: refreshToken }),
		});

		if (response.success && response.data) {
			localStorage.setItem('access_token', response.data.access);
		}

		return response;
	},

	async verifyToken(): Promise<ApiResponse<any>> {
		const token = localStorage.getItem('access_token');
		
		if (!token) {
			return {
				success: false,
				error: 'No access token available',
				data: null
			};
		}

		return await apiRequest<any>('/token/verify/', {
			method: 'POST',
			body: JSON.stringify({ token }),
		});
	},

	async logout(): Promise<void> {
		localStorage.removeItem('access_token');
		localStorage.removeItem('refresh_token');
		localStorage.removeItem('user');
	},

	getCurrentUser() {
		const userStr = localStorage.getItem('user');
		return userStr ? JSON.parse(userStr) : null;
	},

	isAuthenticated(): boolean {
		return !!localStorage.getItem('access_token');
	}
};

// File API functions
export const fileApi = {
	async uploadFiles(files: File[], otherInfo?: any): Promise<ApiResponse<MultiFileUploadResponse>> {
		const formData = new FormData();
		
		files.forEach(file => {
			formData.append('file', file);
		});
		
		if (otherInfo) {
			formData.append('other_info', JSON.stringify(otherInfo));
		}

		return await apiUploadRequest<MultiFileUploadResponse>('/upload/', formData);
	},

	async uploadSingleFile(file: File, otherInfo?: any): Promise<ApiResponse<FileUploadResponse>> {
		const formData = new FormData();
		formData.append('file', file);
		
		if (otherInfo) {
			formData.append('other_info', JSON.stringify(otherInfo));
		}

		return await apiUploadRequest<FileUploadResponse>('/upload/', formData);
	},

	async getUploadedFiles(): Promise<ApiResponse<UploadedFile[]>> {
		return await apiRequest<UploadedFile[]>('/upload/');
	},

	async getRawFile(fileId: number): Promise<Response> {
		const token = localStorage.getItem('access_token');
		
		return fetch(`${API_BASE_URL}/files/${fileId}/raw/`, {
			headers: {
				...(token && { Authorization: `Bearer ${token}` }),
			},
		});
	},

	async getProcessedFile(fileId: number): Promise<Response> {
		const token = localStorage.getItem('access_token');
		
		return fetch(`${API_BASE_URL}/files/${fileId}/processed/`, {
			headers: {
				...(token && { Authorization: `Bearer ${token}` }),
			},
		});
	},

	async getDoclingJson(fileId: number): Promise<ApiResponse<any>> {
		return await apiRequest<any>(`/files/${fileId}/docling-json/`);
	}
};

// User profile API functions
export const userApi = {
	async getProfile(): Promise<ApiResponse<UserProfile>> {
		return await apiRequest<UserProfile>('/profile/');
	}
};

export { apiRequest, apiUploadRequest };