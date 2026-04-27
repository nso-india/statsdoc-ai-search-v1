import { initializeAuth } from './stores/index.js';

// App initialization function
export async function initializeApp() {
  try {
    // Initialize auth store from localStorage
    initializeAuth();
    
  } catch (error) {
    console.error('App initialization failed:', error);
    throw error;
  }
}

// Export all the organized modules
export * from './constants.js';
export * from './apis/index.js';
export * from './stores/index.js';
export * from './utils/index.js';

// Export components
export * from './components/index.js';