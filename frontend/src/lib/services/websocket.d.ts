import { WebSocketState } from './websocket';

declare module './websocket' {
  interface SimpleWebSocketService {
    sendMessageWithConfirmation(message: any, timeout?: number): Promise<boolean>;
    on(event: string, listener: (data: any) => void): void;
    off(event: string, listener: (data: any) => void): void;
    isConnected(): boolean;
    getState(): WebSocketState;
    disconnect(code?: number, reason?: string): void;
    destroy(): void;
  }

  export function createSimpleWebSocketService(
    url: string,
    authToken?: string,
    fileId?: string
  ): SimpleWebSocketService;

  export function createDocumentWebSocketService(
    documentId: string,
    authToken?: string,
    fileId?: string
  ): SimpleWebSocketService;
}
