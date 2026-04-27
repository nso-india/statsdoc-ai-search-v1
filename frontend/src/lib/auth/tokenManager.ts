import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import { WEBUI_API_BASE_URL } from '$lib/constants';

// API base configuration - use remote backend
const API_BASE_URL = WEBUI_API_BASE_URL;

class TokenManager {
  private static instance: TokenManager;
  private refreshPromise: Promise<string> | null = null;

  static getInstance(): TokenManager {
    if (!TokenManager.instance) {
      TokenManager.instance = new TokenManager();
    }
    return TokenManager.instance;
  }

  getToken(): string | null {
    if (!browser) return null;
    return localStorage.getItem('access_token') || localStorage.getItem('token');
  }

  getRefreshToken(): string | null {
    if (!browser) return null;
    return localStorage.getItem('refresh_token');
  }

  setTokens(accessToken: string, refreshToken?: string): void {
    if (!browser) return;
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('token', accessToken); // For backward compatibility
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
    }
  }

  clearTokens(): void {
    if (!browser) return;
    localStorage.removeItem('access_token');
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }

  async refreshAccessToken(): Promise<string> {
    // Prevent multiple simultaneous refresh attempts
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this._performRefresh();
    
    try {
      const newToken = await this.refreshPromise;
      return newToken;
    } finally {
      this.refreshPromise = null;
    }
  }

  private async _performRefresh(): Promise<string> {
    const refreshToken = this.getRefreshToken();
    
    if (!refreshToken) {
      this.clearTokens();
      goto('/login');
      throw new Error('No refresh token available');
    }

    try {
      const response = await fetch(`${API_BASE_URL}/token/refresh/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh: refreshToken }),
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      this.setTokens(data.access);
      
      return data.access;
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.clearTokens();
      goto('/login');
      throw error;
    }
  }

  async makeAuthenticatedRequest(url: string, options: RequestInit = {}): Promise<Response> {
    let token = this.getToken();
    
    if (!token) {
      goto('/login');
      throw new Error('No access token available');
    }

    // First attempt with current token
    const headers = new Headers(options.headers);
    headers.set('Authorization', `Bearer ${token}`);

    let response = await fetch(url, {
      ...options,
      headers,
    });

    // If unauthorized, try to refresh token and retry
    if (response.status === 401) {
      try {
        token = await this.refreshAccessToken();
        headers.set('Authorization', `Bearer ${token}`);
        
        response = await fetch(url, {
          ...options,
          headers,
        });
      } catch (error) {
        console.error('Token refresh failed, redirecting to login');
        goto('/login');
        throw error;
      }
    }

    return response;
  }
}

export const tokenManager = TokenManager.getInstance();