import { WEBUI_API_BASE_URL } from '$lib/constants';
import { tokenManager } from '$lib/auth/tokenManager';

export interface ApiUser {
	id: number;
	username: string;
	email: string;
	first_name: string;
	last_name: string;
	phone?: string;
	user_type?: 'individual' | 'company';
	organization_name?: string;
	is_active: boolean;
	is_staff: boolean;
	is_superuser: boolean;
	date_joined: string;
	last_login: string | null;
}

export interface CreateUserData {
	username?: string;
	email: string;
	password: string;
	first_name?: string;
	last_name?: string;
	phone?: string;
	user_type?: 'individual' | 'company';
	organization_name?: string;
	is_active?: boolean;
}

export interface UpdateUserData {
	username?: string;
	email?: string;
	first_name?: string;
	last_name?: string;
	phone?: string;
	user_type?: 'individual' | 'company';
	organization_name?: string;
	is_active?: boolean;
}

export interface UserListResponse {
	users: ApiUser[];
	pagination: {
		page: number;
		total_pages: number;
		total_count: number;
		has_next: boolean;
		has_previous: boolean;
	};
}

export interface UserStatsResponse {
	total_users: number;
	active_users: number;
	inactive_users: number;
	staff_users: number;
	superuser_count: number;
}

export interface UserRoleResponse {
	user_id: number;
	username: string;
	role: 'SUPERADMIN' | 'STAFF' | 'USER';
	access_level: number;
	is_active: boolean;
}

export interface PasswordChangeData {
	new_password: string;
}

export interface BulkCreateResponse {
	summary: {
		total_in_file: number;
		validation_passed: number;
		successfully_created: number;
		validation_errors: number;
		creation_errors: number;
	};
	created_users: ApiUser[];
	validation_errors: Array<{ row: number; error: string }>;
	creation_errors: Array<{ username: string; error: any }>;
}

export class UsersAPI {
	static async listUsers(
		search?: string,
		isActive?: boolean,
		page: number = 1,
		pageSize: number = 20
	): Promise<UserListResponse> {
		const params = new URLSearchParams();
		if (search) params.append('search', search);
		if (isActive !== undefined) params.append('is_active', isActive.toString());
		params.append('page', page.toString());
		params.append('page_size', pageSize.toString());

		const response = await tokenManager.makeAuthenticatedRequest(
			`${WEBUI_API_BASE_URL}/users/?${params.toString()}`
		);

		if (!response.ok) {
			const error = await response.text();
			throw new Error(`Failed to fetch users: ${error}`);
		}

		return response.json();
	}

	static async createUser(userData: CreateUserData): Promise<ApiUser> {
		const response = await tokenManager.makeAuthenticatedRequest(
			`${WEBUI_API_BASE_URL}/users/`,
			{
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(userData)
			}
		);

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to create user');
		}

		return response.json();
	}

	static async getUserDetail(userId: number): Promise<ApiUser> {
		const response = await tokenManager.makeAuthenticatedRequest(
			`${WEBUI_API_BASE_URL}/users/${userId}/`
		);

		if (!response.ok) {
			const error = await response.text();
			throw new Error(`Failed to fetch user details: ${error}`);
		}

		return response.json();
	}

	static async updateUser(userId: number, userData: UpdateUserData): Promise<ApiUser> {
		const response = await tokenManager.makeAuthenticatedRequest(
			`${WEBUI_API_BASE_URL}/users/${userId}/`,
			{
				method: 'PUT',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(userData)
			}
		);

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to update user');
		}

		return response.json();
	}

	static async deleteUser(userId: number): Promise<{ message: string }> {
		const response = await tokenManager.makeAuthenticatedRequest(
			`${WEBUI_API_BASE_URL}/users/${userId}/`,
			{
				method: 'DELETE'
			}
		);

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to delete user');
		}

		return response.json();
	}

	static async activateUser(userId: number): Promise<{ message: string; user: ApiUser }> {
		const response = await tokenManager.makeAuthenticatedRequest(
			`${WEBUI_API_BASE_URL}/users/${userId}/activate/`,
			{
				method: 'POST'
			}
		);

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to activate user');
		}

		return response.json();
	}

	static async deactivateUser(userId: number): Promise<{ message: string; user: ApiUser }> {
		const response = await tokenManager.makeAuthenticatedRequest(
			`${WEBUI_API_BASE_URL}/users/${userId}/deactivate/`,
			{
				method: 'POST'
			}
		);

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to deactivate user');
		}

		return response.json();
	}

	static async changePassword(userId: number, passwordData: PasswordChangeData): Promise<{ message: string }> {
		const response = await tokenManager.makeAuthenticatedRequest(
			`${WEBUI_API_BASE_URL}/users/${userId}/change-password/`,
			{
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(passwordData)
			}
		);

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to change password');
		}

		return response.json();
	}

	static async getUserStats(): Promise<UserStatsResponse> {
		const response = await tokenManager.makeAuthenticatedRequest(
			`${WEBUI_API_BASE_URL}/users/stats/`
		);

		if (!response.ok) {
			const error = await response.text();
			throw new Error(`Failed to fetch user stats: ${error}`);
		}

		return response.json();
	}

	static async getCurrentUserRole(): Promise<UserRoleResponse> {
		const response = await tokenManager.makeAuthenticatedRequest(
			`${WEBUI_API_BASE_URL}/users/me/role/`
		);

		if (!response.ok) {
			const error = await response.text();
			throw new Error(`Failed to fetch user role: ${error}`);
		}

		return response.json();
	}

	static async bulkCreateUsers(file: File): Promise<BulkCreateResponse> {
		const formData = new FormData();
		formData.append('file', file);

		const response = await tokenManager.makeAuthenticatedRequest(
			`${WEBUI_API_BASE_URL}/users/bulk-create/`,
			{
				method: 'POST',
				body: formData
			}
		);

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to bulk create users');
		}

		return response.json();
	}

	static async downloadTemplate(): Promise<Blob> {
		const response = await tokenManager.makeAuthenticatedRequest(
			`${WEBUI_API_BASE_URL}/users/template/`
		);

		if (!response.ok) {
			const error = await response.text();
			throw new Error(`Failed to download template: ${error}`);
		}

		return response.blob();
	}

	// Legacy method for compatibility - will use activate/deactivate based on current status
	static async toggleUserStatus(userId: number): Promise<{ message: string; user: ApiUser }> {
		// First get user details to check current status
		const user = await this.getUserDetail(userId);
		
		if (user.is_active) {
			return this.deactivateUser(userId);
		} else {
			return this.activateUser(userId);
		}
	}
}
