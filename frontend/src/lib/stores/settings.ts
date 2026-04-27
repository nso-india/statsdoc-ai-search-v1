import { writable, derived, get } from 'svelte/store';
import { getNamespaceConfig } from '$lib/apis/settings';

// Application settings interface
export interface AppSettings {
  file_size_limit_mb: number;
  questions_per_chat: number;
  chats_per_day: number;
}

// Settings store state
interface SettingsState {
  settings: AppSettings | null;
  loading: boolean;
  error: string | null;
  lastFetched: number | null;
}

// Create the settings store
const createSettingsStore = () => {
  const { subscribe, set, update } = writable<SettingsState>({
    settings: null,
    loading: false,
    error: null,
    lastFetched: null
  });

  // Cache duration (5 minutes)
  const CACHE_DURATION = 5 * 60 * 1000;

  const actions = {
    // Load settings from API
    async loadSettings(token?: string, forceRefresh = false) {
      const currentState = get({ subscribe });
      
      // Check if we need to refresh (force refresh or cache expired)
      const now = Date.now();
      const cacheExpired = !currentState.lastFetched || 
        (now - currentState.lastFetched) > CACHE_DURATION;
      
      if (!forceRefresh && currentState.settings && !cacheExpired) {
        return currentState.settings;
      }

      update((state: SettingsState) => ({ ...state, loading: true, error: null }));

      try {
        if (!token) {
          throw new Error('No authentication token provided');
        }

        const response = await getNamespaceConfig(token, 'chat');
        const settings: AppSettings = {
          file_size_limit_mb: response.data?.file_size_limit_mb || 20,
          questions_per_chat: response.data?.questions_per_chat || 10,
          chats_per_day: response.data?.chats_per_day || 50
        };

        update((state: SettingsState) => ({
          ...state,
          settings,
          loading: false,
          error: null,
          lastFetched: now
        }));

        return settings;
      } catch (error: any) {
        console.error('Failed to load settings:', error);
        
        update((state: SettingsState) => ({
          ...state,
          settings: null,
          loading: false,
          error: error?.detail || error?.message || 'Failed to load settings',
          lastFetched: null
        }));

        throw error;
      }
    },

    // Update settings cache (called after settings are updated via API)
    updateSettings(newSettings: Partial<AppSettings>) {
      update((state: SettingsState) => ({
        ...state,
        settings: state.settings ? { ...state.settings, ...newSettings } : null,
        lastFetched: Date.now()
      }));
    },

    // Clear settings (on logout)
    clearSettings() {
      set({
        settings: null,
        loading: false,
        error: null,
        lastFetched: null
      });
    },

    // Reset to default settings
    resetToDefaults() {
      update((state: SettingsState) => ({
        ...state,
        settings: { 
          file_size_limit_mb: 20,
          questions_per_chat: 10,
          chats_per_day: 50
        },
        lastFetched: Date.now()
      }));
    }
  };

  return {
    subscribe,
    ...actions
  };
};

// Export the settings store
export const settingsStore = createSettingsStore();

// Derived stores for easy access to specific settings
export const fileSizeLimit = derived(
  settingsStore,
  ($settingsStore: SettingsState) => $settingsStore.settings?.file_size_limit_mb || 20
);

export const questionsPerChat = derived(
  settingsStore,
  ($settingsStore: SettingsState) => $settingsStore.settings?.questions_per_chat || 10
);

export const chatsPerDay = derived(
  settingsStore,
  ($settingsStore: SettingsState) => $settingsStore.settings?.chats_per_day || 50
);

// Derived store for file size limit in bytes
export const fileSizeLimitBytes = derived(
  fileSizeLimit,
  ($fileSizeLimit: number) => $fileSizeLimit * 1024 * 1024
);

// Helper function to initialize settings with user token
export const initializeSettings = async () => {
  if (typeof window === 'undefined') return;
  
  try {
    const { authToken } = await import('./index');
    const token = get(authToken);
    
    if (token) {
      await settingsStore.loadSettings(token);
    }
  } catch (error) {
    console.warn('Failed to initialize settings:', error);
  }
};
