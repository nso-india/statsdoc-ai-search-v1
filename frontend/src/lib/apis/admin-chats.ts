import { WEBUI_API_BASE_URL } from '$lib/constants';

export interface UserChat {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  user: number;
  message_count?: number;
}

export interface UserChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  chat: number;
}

export interface UserChatResponse {
  chats: UserChat[];
  user: {
    id: number;
    username: string;
    email: string;
  };
}

/**
 * Admin Chat API - for managing user chats (admin only)
 */
export class AdminChatAPI {
  
  private static getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  }

  private static async apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${WEBUI_API_BASE_URL}${endpoint}`, {
      headers: this.getAuthHeaders(),
      ...options
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || error.message || 'API request failed');
    }

    return response.json();
  }

  /**
   * Get all chats for a specific user (admin only)
   */
  static async getUserChats(userId: number): Promise<UserChat[]> {
    try {
      // Debug logging
      console.log('AdminChatAPI.getUserChats called with userId:', userId, 'type:', typeof userId);
      
      // Ensure userId is a valid number
      const userIdParam = parseInt(userId.toString(), 10);
      if (isNaN(userIdParam) || userIdParam <= 0) {
        throw new Error(`Invalid user ID provided: ${userId}`);
      }
      
      // Use the proper backend endpoint with user query parameter
      console.log('Fetching chats for user:', userIdParam, 'using backend user parameter');
      const userChats = await this.apiRequest<UserChat[]>(`/chat/chats/?user=${userIdParam}`);
      
      if (!Array.isArray(userChats)) {
        console.warn('API returned non-array for user chats:', userChats);
        return [];
      }
      
      console.log(`Loaded ${userChats.length} chats for user ${userIdParam}`);
      return userChats;
      
    } catch (error) {
      console.error('Error fetching user chats:', error);
      // Fall back to alternative method if the main method fails
      console.log('Falling back to frontend filtering method');
      try {
        const userIdParam = parseInt(userId.toString(), 10);
        return await this.getUserChatsAlternative(userIdParam);
      } catch (fallbackError) {
        console.error('Fallback method also failed:', fallbackError);
        throw error;
      }
    }
  }

  /**
   * Get user chats by filtering all chats (admin only)
   * This method works around backend issues with user parameter
   */
  private static async getUserChatsAlternative(userId: number): Promise<UserChat[]> {
    try {
      // Get all chats and filter on frontend (works as admin)
      console.log('Getting all chats for filtering by user:', userId);
      
      const allChats = await this.apiRequest<UserChat[]>('/chat/chats/');
      
      if (!Array.isArray(allChats)) {
        console.warn('API returned non-array for chats:', allChats);
        return [];
      }
      
      // Filter chats for the specific user
      const userChats = allChats.filter(chat => {
        // Handle both number and string user IDs
        const chatUserId = typeof chat.user === 'string' ? parseInt(chat.user, 10) : chat.user;
        return chatUserId === userId;
      });
      
      console.log(`Filtered ${userChats.length} chats from ${allChats.length} total chats for user ${userId}`);
      return userChats;
    } catch (error) {
      console.error('Frontend filtering method failed:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      throw new Error(`Failed to load chats for user ${userId}. API error: ${errorMessage}`);
    }
  }

  /**
   * Get messages for a specific chat of a user (admin only)
   */
  static async getUserChatMessages(chatId: number, userId: number): Promise<UserChatMessage[]> {
    try {
      // Validate both IDs
      const chatIdParam = parseInt(chatId.toString(), 10);
      const userIdParam = parseInt(userId.toString(), 10);
      
      if (isNaN(chatIdParam) || chatIdParam <= 0) {
        throw new Error('Invalid chat ID provided');
      }
      if (isNaN(userIdParam) || userIdParam <= 0) {
        throw new Error('Invalid user ID provided');
      }
      
      const messages = await this.apiRequest<UserChatMessage[]>(`/chat/chats/${chatIdParam}/messages/?user=${userIdParam}`);
      return messages || [];
    } catch (error) {
      console.error('Error fetching user chat messages:', error);
      throw error;
    }
  }

  /**
   * Get chat messages by chat ID with optional user ID (admin only)
   * Superadmins can access any chat without user parameter
   * Staff users need to provide user parameter
   */
  static async getChatMessages(chatId: number, userId?: number): Promise<UserChatMessage[]> {
    try {
      const chatIdParam = parseInt(chatId.toString(), 10);
      
      if (isNaN(chatIdParam) || chatIdParam <= 0) {
        throw new Error('Invalid chat ID provided');
      }
      
      console.log('Attempting to fetch chat messages for chat ID:', chatIdParam, 'user ID:', userId);
      
      // Try without user parameter first (works for superadmins)
      try {
        const endpoint = `/chat/chats/${chatIdParam}/messages/`;
        console.log('Fetching chat messages from endpoint (superadmin access):', endpoint);
        
        const messages = await this.apiRequest<UserChatMessage[]>(endpoint);
        console.log('Successfully fetched messages via superadmin access');
        return messages || [];
      } catch (error) {
        // If that fails and we have a userId, try with user parameter (for staff users)
        if (userId) {
          const endpoint = `/chat/chats/${chatIdParam}/messages/?user=${userId}`;
          console.log('Fetching chat messages from endpoint (staff access):', endpoint);
          
          const messages = await this.apiRequest<UserChatMessage[]>(endpoint);
          console.log('Successfully fetched messages via staff access');
          return messages || [];
        }
        
        // If no userId provided, re-throw the original error
        throw error;
      }
      
    } catch (error) {
      console.error('Error fetching chat messages:', error);
      throw error;
    }
  }

  /**
   * Delete a user's chat (admin only)
   */
  static async deleteUserChat(chatId: number): Promise<void> {
    try {
      await this.apiRequest(`/chat/chats/${chatId}/delete/`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error('Error deleting user chat:', error);
      throw error;
    }
  }

  /**
   * Get user statistics with basic info
   */
  static async getUserStats() {
    try {
      return await this.apiRequest('/users/stats/');
    } catch (error) {
      console.error('Error fetching user stats:', error);
      throw error;
    }
  }

  /**
   * Debug method to test API connectivity and admin permissions
   */
  static async debugUserChatsAPI(userId: number): Promise<any> {
    console.log('=== DEBUG: Testing User Chats API ===');
    console.log('User ID:', userId, 'Type:', typeof userId);
    
    try {
      // Test 1: Get all chats (should work for admin)
      console.log('Test 1: Getting all chats...');
      const allChats = await this.apiRequest<UserChat[]>('/chat/chats/');
      console.log('All chats count:', allChats?.length || 0);
      console.log('Sample chats:', allChats?.slice(0, 3));
      
      // Test 2: Use our working alternative method
      console.log(`Test 2: Getting chats for user ${userId} using frontend filtering...`);
      const userChats = await this.getUserChatsAlternative(userId);
      console.log('User chats count:', userChats?.length || 0);
      console.log('User chats:', userChats);
      
      return {
        success: true,
        allChatsCount: allChats?.length || 0,
        userChatsCount: userChats?.length || 0,
        userChats: userChats || [],
        allChatsPreview: allChats?.slice(0, 3) || []
      };
    } catch (error) {
      console.error('Debug test failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
}
