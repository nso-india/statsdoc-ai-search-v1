import { browser } from '$app/environment';
import { get } from 'svelte/store';
import { authToken } from '$lib/stores';
import { WEBSOCKET_BASE_URL } from '$lib/constants/app';

// Simple WebSocket connection following Open WebUI pattern
export class WebSocketConnection {
  private ws: WebSocket | null = null;
  private url: string;
  private isConnected = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;
  private reconnectInterval = 3000;

  constructor(url: string) {
    this.url = url;
  }

  connect(onMessage?: (data: any) => void, onError?: (error: any) => void) {
    if (!browser) return;

    const token = get(authToken);
    if (!token) {
      console.error('No auth token for WebSocket');
      return;
    }

    try {
      const wsUrl = `${this.url}?token=${token}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.isConnected = true;
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage?.(data);
        } catch (err) {
          console.error('WebSocket message parse error:', err);
        }
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        this.attemptReconnect(onMessage, onError);
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.(error);
      };

    } catch (error) {
      console.error('WebSocket connection failed:', error);
      onError?.(error);
    }
  }

  private attemptReconnect(onMessage?: (data: any) => void, onError?: (error: any) => void) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      
      setTimeout(() => {
        this.connect(onMessage, onError);
      }, this.reconnectInterval);
    }
  }

  send(data: any) {
    if (this.ws && this.isConnected) {
      this.ws.send(JSON.stringify(data));
      return true;
    }
    return false;
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
  }

  getConnectionStatus() {
    return this.isConnected;
  }
}

// Factory function for document WebSocket
export function createDocumentWebSocket(documentId: string): WebSocketConnection {
  // Use the remote backend WebSocket URL
  const wsUrl = `${WEBSOCKET_BASE_URL}/ws/pdf_update/`;
  return new WebSocketConnection(wsUrl);
}