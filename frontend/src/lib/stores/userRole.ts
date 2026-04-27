import { writable, derived } from 'svelte/store';
import { user } from './index';
import { WEBUI_API_BASE_URL } from '$lib/constants';

// User role state
export const userRole = writable<any>(null);
export const userRoleLoading = writable(false);

// Load user role function
export const loadUserRole = async () => {
  try {
    userRoleLoading.set(true);
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      throw new Error('No token found');
    }

    const response = await fetch(`${WEBUI_API_BASE_URL}/users/me/role/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      const roleData = await response.json();
      userRole.set(roleData);
      
      // Update user store with role info
      user.update(currentUser => ({
        ...currentUser,
        role: roleData.role,
        is_staff: roleData.role === 'STAFF' || roleData.role === 'SUPERADMIN',
        is_superuser: roleData.role === 'SUPERADMIN'
      }));
    }
  } catch (error) {
    console.error('Failed to load user role:', error);
  } finally {
    userRoleLoading.set(false);
  }
};

// Clear user role
export const clearUserRole = () => {
  userRole.set(null);
  userRoleLoading.set(false);
};
