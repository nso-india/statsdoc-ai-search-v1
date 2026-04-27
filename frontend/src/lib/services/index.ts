// WebSocket and collaboration services following Open WebUI pattern
export * from './websocket';
export * from './collaboration';

// Re-export commonly used services
export { getDocumentCollaborationService } from './collaboration';
export { createWebSocketService, createDocumentWebSocketService } from './websocket';