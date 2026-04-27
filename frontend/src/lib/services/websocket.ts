import { browser } from '$app/environment';
import { get } from 'svelte/store';
import { authToken } from '$lib/stores';
import { toast } from 'svelte-sonner';
import { REMOTE_BACKEND_HOST } from '$lib/constants';

// Simple WebSocket states
export enum WebSocketState {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  ERROR = 'error',
  RECONNECTING = 'reconnecting'
}

// Simple WebSocket service configuration
interface WebSocketConfig {
  url: string;
  protocols?: string[];
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  autoReconnect?: boolean;
  authToken?: string;
  fileId?: string;
}

// Simple event handlers
interface WebSocketEventHandlers {
  onConnect?: () => void;
  onDisconnect?: (code: number, reason: string) => void;
  onMessage?: (message: any) => void;
  onError?: (error: Event) => void;
}

class SimpleWebSocketService {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private handlers: WebSocketEventHandlers = {};
  private state: WebSocketState = WebSocketState.DISCONNECTED;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private isManuallyDisconnected = false;
  private authToken: string | null = null;
  private fileId: string | null = null;

  constructor(config: WebSocketConfig) {
    this.config = {
      reconnectInterval: 3000,
      maxReconnectAttempts: 5,
      autoReconnect: true,
      ...config
    };
    // Get token from config or from localStorage if not provided
    this.authToken = config.authToken || (browser ? localStorage.getItem('access_token') : null);
    this.fileId = config.fileId || null;
    
    // Debug logging
    console.log('WebSocketService initialized with config:', {
      url: this.config.url,
      hasToken: !!this.authToken,
      tokenLength: this.authToken?.length,
      tokenStart: this.authToken?.substring(0, 10) + '...',
      fileId: this.fileId
    });
  }

  // Simple connect method
  connect(handlers?: WebSocketEventHandlers): Promise<boolean> {
    if (handlers) {
      this.handlers = { ...this.handlers, ...handlers };
    }

    return new Promise((resolve) => {
      if (this.ws) {
        console.warn('WebSocket already exists, disconnecting first');
        this.ws.close();
      }

      this.state = WebSocketState.CONNECTING;
      
      // Construct the WebSocket URL with token if available
      let wsUrl = this.config.url;
      
      // Add token to URL if available
      if (this.authToken) {
        const separator = wsUrl.includes('?') ? '&' : '?';
        const tokenParam = `token=${encodeURIComponent(this.authToken)}`;
        wsUrl = `${wsUrl}${separator}${tokenParam}`;
        console.log('Added token to WebSocket URL:', {
          originalUrl: this.config.url,
          finalUrl: wsUrl,
          tokenLength: this.authToken.length,
          tokenStart: this.authToken.substring(0, 10) + '...'
        });
      } else {
        console.warn('No authToken available for WebSocket connection');
        // Check if we can get the token from localStorage directly
        if (browser) {
          const tokenFromStorage = localStorage.getItem('access_token');
          console.log('Token from localStorage:', {
            exists: !!tokenFromStorage,
            length: tokenFromStorage?.length,
            start: tokenFromStorage?.substring(0, 10) + '...'
          });
        }
      }
      
      console.log(`Connecting to WebSocket at ${wsUrl}`);

      try {
        // Create WebSocket with token in URL
        this.ws = new WebSocket(wsUrl, this.config.protocols);
        
        // Set up message handler to handle the initial welcome message
        const onMessage = (event: MessageEvent) => {
          try {
            const message = JSON.parse(event.data);
            if (message.message === 'Hello WebSocket!') {
              console.log('Successfully connected to WebSocket');
              this.ws?.removeEventListener('message', onMessage);
              this.state = WebSocketState.CONNECTED;
              this.handlers.onConnect?.();
              resolve(true);
            }
          } catch (e) {
            console.error('Error parsing welcome message:', e);
          }
        };
        
        this.ws.addEventListener('message', onMessage);
        
        // Set up error handler
        this.ws.addEventListener('error', (error) => {
          console.error('WebSocket error:', error);
          this.state = WebSocketState.ERROR;
          this.handlers.onError?.(error);
          this.ws?.removeEventListener('message', onMessage);
          resolve(false);
        });
        
        // Set up close handler
        this.ws.addEventListener('close', (event) => {
          console.log('WebSocket closed:', event.code, event.reason);
          this.state = WebSocketState.DISCONNECTED;
          this.handlers.onDisconnect?.(event.code, event.reason);
          this.ws?.removeEventListener('message', onMessage);
          
          // Attempt to reconnect if not a normal closure
          if (event.code !== 1000) {
            this.attemptReconnect();
          }
        });
        
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        this.state = WebSocketState.ERROR;
        this.handlers.onError?.(error as Event);
        this.attemptReconnect();
        resolve(false);
        return;
      }

      this.setupEventListeners();

      resolve(true);
    });
  }

  // Setup basic event listeners
  private setupEventListeners(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected successfully');
      this.setState(WebSocketState.CONNECTED);
      this.reconnectAttempts = 0;
      this.handlers.onConnect?.();
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('WebSocket message received:', message);
        
        // Emit the raw message for general handling
        this.emit('message', message);
        
        // Also pass to the legacy handler
        this.handlers.onMessage?.(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      this.setState(WebSocketState.DISCONNECTED);
      this.handlers.onDisconnect?.(event.code, event.reason);
      
      // Auto-reconnect if not manually disconnected
      if (!this.isManuallyDisconnected && this.config.autoReconnect) {
        this.attemptReconnect();
      }
    };

    this.ws.onerror = (event) => {
      this.handleError('WebSocket error');
    };
  }

  private handleError(error: string | Event) {
    console.error('WebSocket error:', error);
    
    // Extract error message from Event if it's an Event object
    const errorMessage = typeof error === 'string' 
      ? error 
      : (error instanceof Error ? error.message : 'Unknown WebSocket error');
    
    // Show error toast for connection-related errors
    if (typeof errorMessage === 'string' && 
        (errorMessage.includes('connection') || 
         errorMessage.includes('failed') ||
         errorMessage.includes('token'))) {
      toast.error(`Connection error: ${errorMessage}`);
    }
    
    // Notify error handlers
    if (this.handlers.onError) {
      this.handlers.onError(error instanceof Event ? error : new Event('error'));
    }
  }

  // Event emitter methods
  private eventListeners: Record<string, ((data: any) => void)[]> = {};

  /**
   * Add an event listener
   * @param event Event name
   * @param listener Callback function
   */
  on(event: string, listener: (data: any) => void): void {
    if (!this.eventListeners[event]) {
      this.eventListeners[event] = [];
    }
    this.eventListeners[event].push(listener);
  }

  /**
   * Remove an event listener
   * @param event Event name
   * @param listener Callback function to remove
   */
  off(event: string, listener: (data: any) => void): void {
    if (!this.eventListeners[event]) return;
    
    const index = this.eventListeners[event].indexOf(listener);
    if (index > -1) {
      this.eventListeners[event].splice(index, 1);
    }
  }

  /**
   * Emit an event
   * @param event Event name
   * @param data Data to pass to listeners
   * @private
   */
  private emit(event: string, data: any): void {
    if (!this.eventListeners[event]) return;
    
    for (const listener of this.eventListeners[event]) {
      try {
        listener(data);
      } catch (error) {
        console.error(`Error in event listener for '${event}':`, error);
      }
    }
  }

  // Simple send method
  send(data: any): boolean {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        // Ensure we have a proper message object
        const messageData = typeof data === 'object' ? { ...data } : { message: data };
        
        // Always include file_id in message body
        if (this.fileId && !messageData.file_id) {
          messageData.file_id = this.fileId;
        }
        
        // Ensure we have a message type
        if (!messageData.type) {
          messageData.type = 'update';
        }
        
        // Add a message if not provided
        if (!messageData.message) {
          messageData.message = `WebSocket ${messageData.type} message`;
        }
        
        console.log('Sending WebSocket message:', messageData);
        this.ws.send(JSON.stringify(messageData));
        return true;
      } catch (error) {
        console.error('Error sending WebSocket message:', error);
        return false;
      }
    }
    console.warn('Cannot send message - WebSocket not connected');
    return false;
  }

  // Send document update (matching backend format)
  sendDocumentUpdate(fileId: string, targetRef: string, newData: any): boolean {
    const message = {
      type: 'update',
      file_id: fileId,
      target_ref: targetRef,
      new_data: newData,
      message: `Document updated: ${targetRef}`,
      // Token will be added automatically in the send method
    };
    
    return this.send(message);
  }

  // Send table merge request (matching backend format)
  sendTableMergeRequest(fileId: string, sourceRef: string, targetRef: string): boolean {
    const message = {
      type: 'merge_table',
      file_id: fileId,
      source_ref: sourceRef,
      target_ref: targetRef,
      message: `Table merge: ${sourceRef} -> ${targetRef}`
    };
    
    return this.send(message);
  }

  // Send comment update (matching backend format)
  sendCommentUpdate(fileId: string, comment: { 
    comment: string; 
    comment_type: 'EDIT' | 'REMOVE' | 'TABLE_MERGE';
    target_ref?: string;
    source_ref?: string;
  }): boolean {
    const message = {
      type: 'comment',
      file_id: fileId,
      ...comment
    };
    
    return this.send(message);
  }

  // Enhanced reconnection logic with exponential backoff
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= (this.config.maxReconnectAttempts || 5)) {
      console.error('Max reconnection attempts reached');
      this.setState(WebSocketState.ERROR);
      this.handlers.onError?.(new Event('Max reconnection attempts reached'));
      return;
    }

    this.reconnectAttempts++;
    this.setState(WebSocketState.RECONNECTING);

    // Exponential backoff with jitter
    const baseDelay = this.config.reconnectInterval || 3000;
    const jitter = Math.random() * 1000; // Add up to 1s jitter
    const delay = Math.min(baseDelay * Math.pow(1.5, this.reconnectAttempts - 1) + jitter, 30000); // Cap at 30s

    console.log(`Attempting to reconnect in ${Math.round(delay)}ms (attempt ${this.reconnectAttempts}/${this.config.maxReconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      if (this.state !== WebSocketState.DISCONNECTED && this.state !== WebSocketState.RECONNECTING) {
        console.log('Skipping reconnection - already connected or connecting');
        return;
      }
      console.log('Initiating reconnection...');
      this.connect(this.handlers).catch(error => {
        console.error('Reconnection attempt failed:', error);
        this.attemptReconnect(); // Schedule another reconnection attempt
      });
    }, delay);
  }

  // State management with validation and logging
  private setState(newState: WebSocketState): void {
    if (this.state !== newState) {
      const oldState = this.state;
      this.state = newState;
      console.log(`WebSocket state changed: ${oldState} -> ${newState}`);
      
      // Additional state-specific logic
      if (newState === WebSocketState.CONNECTED) {
        this.reconnectAttempts = 0; // Reset reconnection attempts on successful connection
      } else if (newState === WebSocketState.ERROR) {
        console.error('WebSocket encountered an error');
      }
    }
  }

  /**
   * Sends a message and waits for a confirmation from the server
   * @param message The message to send
   * @param timeout Optional timeout in milliseconds (default: 5000ms)
   * @returns Promise that resolves to true if confirmed, false if timed out or failed
   */
  sendMessageWithConfirmation(message: any, timeout: number = 5000): Promise<boolean> {
    return new Promise((resolve) => {
      if (!this.isConnected()) {
        console.error('Cannot send message - WebSocket not connected');
        resolve(false);
        return;
      }

      // Generate a unique ID for this message
      const messageId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      // Add the ID to the message
      const messageWithId = {
        ...message,
        _messageId: messageId
      };

      // Set up a timeout
      const timeoutId = setTimeout(() => {
        console.warn(`Message ${messageId} timed out waiting for confirmation`);
        this.off('message', handleConfirmation);
        resolve(false);
      }, timeout);

      // Handle the confirmation response
      const handleConfirmation = (response: any) => {
        // Check if this is a confirmation for our message
        if (response?._responseTo === messageId) {
          clearTimeout(timeoutId);
          this.off('message', handleConfirmation);
          resolve(response.success === true);
        }
      };

      // Listen for the confirmation
      this.on('message', handleConfirmation);

      // Send the message
      if (!this.send(messageWithId)) {
        clearTimeout(timeoutId);
        this.off('message', handleConfirmation);
        resolve(false);
      }
    });
  }

  // Utility methods
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  getState(): WebSocketState {
    return this.state;
  }

  /**
   * Cleanly disconnect the WebSocket connection
   * @param code Close status code (default: 1000 - Normal closure)
   * @param reason Optional reason for disconnection
   */
  disconnect(code: number = 1000, reason: string = 'Manual disconnect'): void {
    this.isManuallyDisconnected = true;
    
    // Clear any pending reconnection attempts
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    // Close the WebSocket if it exists and is open/opening
    if (this.ws) {
      try {
        if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
          this.ws.close(code, reason);
        }
      } catch (error) {
        console.error('Error while closing WebSocket:', error);
      } finally {
        this.ws = null;
      }
    }
    
    this.setState(WebSocketState.DISCONNECTED);
  }

  /**
   * Clean up all resources and event listeners
   * Should be called when the WebSocket is no longer needed
   */
  destroy(): void {
    console.log('Destroying WebSocket service');
    
    // Disconnect the WebSocket
    this.disconnect(1000, 'Service destroyed');
    
    // Clear any remaining timers
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    // Clear all handlers and event listeners
    this.handlers = {};
    this.eventListeners = {};
    
    // Reset state
    this.state = WebSocketState.DISCONNECTED;
    this.reconnectAttempts = 0;
    this.isManuallyDisconnected = false;
    
    console.log('WebSocket service destroyed');
  }
}

// Simple factory function
export function createSimpleWebSocketService(url: string, authToken?: string, fileId?: string): SimpleWebSocketService {
  return new SimpleWebSocketService({ url, authToken, fileId });
}

// Document-specific WebSocket service
export function createDocumentWebSocketService(documentId: string, fileId?: string): SimpleWebSocketService {
  if (!browser) {
    throw new Error('WebSocket can only be created in browser environment');
  }

  // Use the API domain for WebSocket connections
  const wsProtocol = 'wss:';
  const apiHostname = REMOTE_BACKEND_HOST;
  
  // Construct WebSocket URL - using the API domain
  const wsUrl = `${wsProtocol}//${apiHostname}/ws/pdf_update/`;
  
  console.log('Creating WebSocket service for document:', documentId);
  
  const service = new SimpleWebSocketService({
    url: wsUrl,
    fileId: fileId || documentId, // Store fileId for message bodies
    autoReconnect: true,
    reconnectInterval: 3000,
    maxReconnectAttempts: 10
  });

  // Log connection state changes
  service.on('state_change', (state: WebSocketState) => {
    console.log(`WebSocket state changed to: ${state}`);
  });

  return service;
}

export default SimpleWebSocketService;
