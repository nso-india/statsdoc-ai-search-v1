import { WEBUI_API_BASE_URL } from '../constants';

export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  date_joined: string;
  userprofile: {
    id: number;
    role: string;
    created_by: string;
    created_at: string;
    updated_at: string;
    is_active: boolean;
  };
}

export interface CreateUserData {
  username: string;
  email: string;
  password: string;
}

export interface UserCreationLog {
  id: number;
  created_user: {
    id: number;
    username: string;
    email: string;
  };
  created_by: {
    id: number;
    username: string;
  };
  created_at: string;
  action: string;
  notes: string;
}

/**
 * Fetch all users (admin only)
 */
export async function getUsers(token: string): Promise<User[]> {
  const response = await fetch(`${WEBUI_API_BASE_URL}/user-management/admin/users/`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to fetch users: ${response.status}`);
  }

  return response.json();
}

/**
 * Create a new user (admin only)
 */
export async function createUser(token: string, userData: CreateUserData): Promise<any> {
  const response = await fetch(`${WEBUI_API_BASE_URL}/user-management/admin/users/create/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to create user: ${response.status}`);
  }

  return response.json();
}

/**
 * Toggle user active status (admin only)
 */
export async function toggleUserStatus(token: string, userId: number): Promise<any> {
  const response = await fetch(`${WEBUI_API_BASE_URL}/user-management/admin/users/${userId}/toggle-status/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to toggle user status: ${response.status}`);
  }

  return response.json();
}

/**
 * Get user creation logs (admin only)
 */
export async function getUserCreationLogs(token: string): Promise<UserCreationLog[]> {
  const response = await fetch(`${WEBUI_API_BASE_URL}/user-management/admin/logs/`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to fetch logs: ${response.status}`);
  }

  return response.json();
}

/**
 * Delete a user (admin only)
 */
export async function deleteUser(token: string, userId: number): Promise<any> {
  const response = await fetch(`${WEBUI_API_BASE_URL}/user-management/admin/users/${userId}/`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to delete user: ${response.status}`);
  }

  return response.json();
}
