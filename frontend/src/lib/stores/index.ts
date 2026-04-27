import { APP_NAME, WEBUI_API_BASE_URL } from '$lib/constants';
import { type Writable, writable, derived } from 'svelte/store';
import { userSignIn, refreshToken } from '$lib/apis/auths';
import { getFiles, uploadFiles, type UploadedFile } from '$lib/apis/files';

// TypeScript types following Open WebUI pattern
export type SessionUser = {
  id: string;
  username: string;
  email: string;
  role: string;
  is_superuser: boolean;
  name?: string;
  profile_image_url?: string;
};

export type ToastMessage = {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration: number;
  dismissible: boolean;
};

export type UserProfile = {
  id: string;
  name: string;
  email: string;
  profile_image_url?: string;
  created_at: string;
  updated_at: string;
};

export type UserPreferences = {
  theme: 'light' | 'dark' | 'system';
  notifications: boolean;
  display: {
    pageSize: number;
    showThumbnails: boolean;
  };
};

// Backend
export const WEBUI_NAME = writable(APP_NAME);
export const user: Writable<SessionUser | undefined> = writable(undefined);

// Authentication stores
export const isAuthenticated = writable(false);
export const authToken = writable<string | null>(null);
export const refreshAuthToken = writable<string | null>(null);

// Files stores
export const files: Writable<UploadedFile[]> = writable([]);
export const selectedFiles: Writable<number[]> = writable([]);
export const uploadProgress: Writable<Record<string, number>> = writable({});
export const filesLoading = writable(false);

// UI stores  
export const theme = writable('system');
export const mobile = writable(false);
export const showSidebar = writable(false);
export const showSettings = writable(false);

// Sidebar and navigation
export const sidebarOpen = writable(true);
export const sidebarCollapsed = writable(false);
export const activeSection = writable('chat');

// Modals and overlays
export const modals: Writable<Record<string, boolean>> = writable({});

// Toast notifications
export const toasts: Writable<ToastMessage[]> = writable([]);

// File filters and pagination
export const fileFilters = writable({
  status: '',
  search: '',
  dateRange: { start: undefined as Date | undefined, end: undefined as Date | undefined }
});

export const filePagination = writable({
  page: 1,
  pageSize: 20,
  total: 0
});

// User profile and preferences
export const userProfile: Writable<UserProfile | null> = writable(null);
export const userPreferences: Writable<UserPreferences | null> = writable(null);
export const userLoading = writable(false);

// Loading states
export const loading = writable(false);
export const globalLoading = writable(false);

// Derived stores
export const filteredFiles = derived(
  [files, fileFilters],
  ([$files, $filters]) => {
    let filtered = $files;

    // Apply status filter
    if ($filters.status) {
      filtered = filtered.filter(file => file.upload_status === $filters.status);
    }

    // Apply search filter
    if ($filters.search) {
      const search = $filters.search.toLowerCase();
      filtered = filtered.filter(file => 
        file.file_name.toLowerCase().includes(search) ||
        file.original_name.toLowerCase().includes(search)
      );
    }

    // Apply date range filter
    if ($filters.dateRange.start || $filters.dateRange.end) {
      filtered = filtered.filter(file => {
        const fileDate = new Date(file.created_at);
        const start = $filters.dateRange.start;
        const end = $filters.dateRange.end;
        
        return (!start || fileDate >= start) && (!end || fileDate <= end);
      });
    }

    return filtered;
  }
);

export const selectedFilesData = derived(
  [filteredFiles, selectedFiles],
  ([$filtered, $selected]) => 
    $filtered.filter(file => $selected.includes(file.id))
);

export const currentUser = derived(user, $user => $user);
export const userTheme = derived(userPreferences, $prefs => $prefs?.theme || 'system');

// Store actions following Open WebUI pattern
export const loginUser = async (username: string, password: string) => {
  try {
    const response = await userSignIn(username, password);
    
    if (response && response.access) {
      authToken.set(response.access);
      refreshAuthToken.set(response.refresh);
      isAuthenticated.set(true);
      
      // Store tokens in localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem('access_token', response.access);
        localStorage.setItem('refresh_token', response.refresh);
      }
      
      // Fetch and set user data immediately after login
      try {
        const roleResponse = await fetch(`${WEBUI_API_BASE_URL}/users/me/role/`, {
          headers: { 'Authorization': `Bearer ${response.access}` }
        });
        
        if (roleResponse.ok) {
          const roleData = await roleResponse.json();
          
          // Validate that roleData has the expected structure
          if (roleData && typeof roleData === 'object' && roleData.user_id) {
            const userData = {
              id: roleData.user_id.toString(),
              username: roleData.username || '',
              email: roleData.email || '',
              role: roleData.role || 'USER',
              is_superuser: roleData.role === 'SUPERADMIN',
              is_staff: roleData.role === 'STAFF' || roleData.role === 'SUPERADMIN'
            };
            
            user.set(userData);
            
            // Store user data in localStorage
            if (typeof window !== 'undefined') {
              localStorage.setItem('user', JSON.stringify(userData));
            }
          } else {
            console.error('Invalid user data structure received:', roleData);
          }
        } else {
          console.warn('Failed to fetch user role data after login');
        }
      } catch (userError) {
        console.error('Failed to fetch user data after login:', userError);
        // Don't throw here - login was successful, just user data fetch failed
      }
      
      return response;
    }
    
    // If we reach here, response doesn't have the expected structure
    throw new Error('Invalid response from server - missing access token');
  } catch (error: any) {
    console.error('Login error:', error);
    
    // Enhance error with additional context
    if (error && typeof error === 'object') {
      // Pass through enhanced error object
      throw error;
    }
    
    // Fallback for unknown error types
    throw new Error(error?.message || 'Login failed');
  }
};

export const logoutUser = () => {
  authToken.set(null);
  refreshAuthToken.set(null);
  isAuthenticated.set(false);
  user.set(undefined);
  
  if (typeof window !== 'undefined') {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }
};

export const signupUser = async (signupData: {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  user_type: string;
  organization_name: string;
  password: string;
}) => {
  try {
    const response = await fetch(`${WEBUI_API_BASE_URL}/api/signup/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(signupData)
    });

    const data = await response.json();

    if (!response.ok) {
      throw data;
    }

    return data;
  } catch (error: any) {
    console.error('Signup error:', error);
    throw error;
  }
};

export const loadFiles = async () => {
  try {
    filesLoading.set(true);
    const response = await getFiles();
    if (response.success && response.data) {
      files.set(response.data);
    }
  } catch (error) {
    console.error('Load files error:', error);
    throw error;
  } finally {
    filesLoading.set(false);
  }
};

export const addToast = (toast: Omit<ToastMessage, 'id' | 'dismissible' | 'duration'> & Partial<Pick<ToastMessage, 'dismissible' | 'duration'>>) => {
  const id = `toast-${Date.now()}-${Math.random()}`;
  const newToast: ToastMessage = {
    id,
    dismissible: true,
    duration: 5000,
    ...toast
  };

  toasts.update(current => [...current, newToast]);

  // Auto remove after duration
  if (newToast.duration > 0) {
    setTimeout(() => removeToast(id), newToast.duration);
  }

  return id;
};

export const removeToast = (id: string) => {
  toasts.update(current => current.filter(toast => toast.id !== id));
};

export const showModal = (modalId: string) => {
  modals.update(current => ({ ...current, [modalId]: true }));
};

export const hideModal = (modalId: string) => {
  modals.update(current => ({ ...current, [modalId]: false }));
};

export const initializeAuth = () => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    const refresh = localStorage.getItem('refresh_token');
    const userData = localStorage.getItem('user');
    
    if (token) {
      authToken.set(token);
      refreshAuthToken.set(refresh);
      isAuthenticated.set(true);
      
      if (userData) {
        try {
          user.set(JSON.parse(userData));
        } catch (error) {
          console.error('Failed to parse user data:', error);
        }
      }
    }
  }
};

// Export upload store functions
export * from './upload.js';