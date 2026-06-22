import { browser } from '$app/environment';
import { get } from 'svelte/store';
import { authToken } from '$lib/stores';
import { toast } from 'svelte-sonner';
import { WEBSOCKET_BASE_URL } from '$lib/constants/app';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string | {
    content?: string;
    files?: Array<{
      id: number;
      file_name: string;
      file_url: string;
    }>;
    response?: string;
    qdrant_data?: {
      context: string;
    };
  };
  timestamp: string;
  chat_id: string;
  data_response?: any;
}

export interface ChatWebSocketService {
  connect(): void;
  disconnect(): void;
  sendMessage(message: string, chatId?: string, languageId?: string | null): void;
  sendEditMessage(
    message: string,
    editMessageId: string | number,
    chatId?: string,
    languageId?: string | null
  ): void;
  onMessage(callback: (message: ChatMessage) => void): void;
  onLoading(callback: (loading: boolean) => void): void;
  onError(callback: (error: string) => void): void;
  on(event: string, callback: (...args: any[]) => void): void;
  off(event: string, callback: (...args: any[]) => void): void;
  isConnected(): boolean;
  destroy(): void;
}

class ChatWebSocketServiceImpl implements ChatWebSocketService {
  private ws: WebSocket | null = null;
  private chatId: string;
  private messageHandlers: Array<(message: ChatMessage) => void> = [];
  private loadingHandlers: Array<(loading: boolean) => void> = [];
  private errorHandlers: Array<(error: string) => void> = [];
  private eventHandlers: Map<string, Array<(...args: any[]) => void>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 3000;
  private isManuallyDisconnected = false;

  constructor(chatId: string) {
    this.chatId = chatId;
  }

  connect(): void {
    if (!browser) return;

    // Try to get token from store first, then fallback to localStorage
    let token = get(authToken);
    if (!token) {
      token = localStorage.getItem('access_token');
    }
    
    if (!token) {
      this.handleError('No authentication token available');
      return;
    }

    try {
      const wsUrl = `${WEBSOCKET_BASE_URL}/ws/chat/${this.chatId}/?token=${encodeURIComponent(token)}`;
      
      console.log('Connecting to WebSocket:', wsUrl);
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('Chat WebSocket connected successfully');
        this.reconnectAttempts = 0;
        this.isManuallyDisconnected = false;
        this.emitEvent('connected');
      };

      this.ws.onmessage = (event) => {
        try {
          console.log('WebSocket message received:', event.data);
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
          this.handleError('Failed to parse message from server');
        }
      };

      this.ws.onclose = (event) => {
        console.log('Chat WebSocket disconnected:', event.code, event.reason);
        this.ws = null;
        this.emitEvent('disconnected', event.code, event.reason);

        // Attempt reconnection if not manually disconnected and code indicates it should retry
        if (!this.isManuallyDisconnected && 
            this.reconnectAttempts < this.maxReconnectAttempts &&
            event.code !== 1000) { // 1000 = normal closure
          this.reconnectAttempts++;
          console.log(`Attempting to reconnect in ${this.reconnectInterval}ms... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
          setTimeout(() => {
            if (!this.isManuallyDisconnected) {
              this.connect();
            }
          }, this.reconnectInterval);
        }
      };

      this.ws.onerror = (event) => {
        console.error('Chat WebSocket error:', event);
        this.handleError('WebSocket connection error');
        this.emitEvent('error', event);
      };

    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      this.handleError('Failed to create WebSocket connection');
    }
  }

  disconnect(): void {
    this.isManuallyDisconnected = true;
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
  }

  sendMessage(message: string, chatId?: string, languageId?: string | null): void {
    this.sendPayload({
      message,
      chat_id: chatId || this.chatId,
      language_id: languageId || undefined,
    });
  }

  sendEditMessage(
    message: string,
    editMessageId: string | number,
    chatId?: string,
    languageId?: string | null
  ): void {
    this.sendPayload({
      message,
      chat_id: chatId || this.chatId,
      edit_message_id: editMessageId,
      language_id: languageId || undefined,
    });
  }

  private sendPayload(payload: Record<string, unknown>): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.handleError('WebSocket is not connected');
      return;
    }

    try {
      const body: Record<string, unknown> = {
        message: payload.message,
        chat_id: payload.chat_id,
      };

      if (payload.language_id) {
        body.language_id = payload.language_id;
      }

      if (payload.edit_message_id !== undefined) {
        body.edit_message_id = payload.edit_message_id;
      }

      this.ws.send(JSON.stringify(body));
    } catch (error) {
      console.error('Error sending message:', error);
      this.handleError('Failed to send message');
    }
  }

  onMessage(callback: (message: ChatMessage) => void): void {
    this.messageHandlers.push(callback);
  }

  onLoading(callback: (loading: boolean) => void): void {
    this.loadingHandlers.push(callback);
  }

  onError(callback: (error: string) => void): void {
    this.errorHandlers.push(callback);
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  on(event: string, callback: (...args: any[]) => void): void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, []);
    }
    this.eventHandlers.get(event)!.push(callback);
  }

  off(event: string, callback: (...args: any[]) => void): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      const index = handlers.indexOf(callback);
      if (index !== -1) {
        handlers.splice(index, 1);
      }
    }
  }

  destroy(): void {
    this.disconnect();
    this.messageHandlers = [];
    this.loadingHandlers = [];
    this.errorHandlers = [];
    this.eventHandlers.clear();
  }

  private handleMessage(data: any): void {
    try {
      switch (data.type) {
        case 'message':
          if (data.message) {
            this.messageHandlers.forEach(handler => {
              try {
                handler(data.message);
              } catch (error) {
                console.error('Error in message handler:', error);
              }
            });
          }
          break;

        case 'loading':
          this.loadingHandlers.forEach(handler => {
            try {
              handler(data.loading || false);
            } catch (error) {
              console.error('Error in loading handler:', error);
            }
          });
          break;

        case 'error':
          const errorMessage = data.message || data.error || 'Unknown server error';
          
          // Always show error messages to user via toast
          toast.error(errorMessage);
          
          this.handleError(errorMessage);
          break;

        default:
          console.warn('Unknown message type:', data.type);
      }
    } catch (error) {
      console.error('Error handling message:', error);
      this.handleError('Failed to process server message');
    }
  }

  private handleError(error: string): void {
    console.error('Chat WebSocket error:', error);
    this.errorHandlers.forEach(handler => {
      try {
        handler(error);
      } catch (err) {
        console.error('Error in error handler:', err);
      }
    });
  }

  private emitEvent(event: string, ...args: any[]): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(...args);
        } catch (error) {
          console.error(`Error in ${event} event handler:`, error);
        }
      });
    }
  }
}

export function createChatWebSocket(chatId: string): ChatWebSocketService {
  return new ChatWebSocketServiceImpl(chatId);
}
