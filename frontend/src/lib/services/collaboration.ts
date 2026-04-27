import { browser } from '$app/environment';
import { createDocumentWebSocketService, WebSocketState } from './websocket';
import type SimpleWebSocketService from './websocket';
import { toast } from 'svelte-sonner';

// Simple document WebSocket service
class DocumentWebSocketService {
  private wsService: SimpleWebSocketService | null = null;
  private documentId: string | null = null;
  private updateHandlers: ((message: any) => void)[] = [];

  // Initialize WebSocket for a document
  async initializeDocument(documentId: string): Promise<boolean> {
    if (!browser) {
      console.warn('WebSocket not available in SSR context');
      return false;
    }

    // Check if we're already connected to this document
    if (this.documentId === documentId && this.wsService?.isConnected()) {
      return true;
    }

    // Cleanup existing connection if it exists
    if (this.wsService) {
      this.wsService.destroy();
      this.wsService = null;
    }

    this.documentId = documentId;

    try {
      // Create WebSocket service for this document
      this.wsService = createDocumentWebSocketService(documentId);
      
      if (!this.wsService) {
        throw new Error('Failed to create WebSocket service');
      }

      // Setup basic event handlers
      const success = await this.connectToDocument();
      
      if (success) {
        this.handleIncomingMessage({
          type: 'connection_status',
          status: 'connected',
          documentId: documentId
        });
      } else {
        console.warn('WebSocket connection failed for document:', documentId);
      }

      return success;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('Failed to initialize WebSocket:', error);
      this.handleIncomingMessage({
        type: 'error',
        message: errorMessage
      });
      return false;
    }
  }

  // Helper function to get the parent data structure
  private getParentData(document: any, targetRef: string): any {
    if (!document) return null;
    
    // Remove the leading #/ if present
    const path = targetRef.startsWith('#/') ? targetRef.substring(2) : targetRef;
    const parts = path.split('/');
    let current = document;
    
    // Navigate to the parent of the target
    for (let i = 0; i < parts.length - 1; i++) {
      const part = parts[i];
      if (current[part] === undefined) {
        console.warn('Path not found in document:', part);
        return null;
      }
      current = current[part];
    }
    
    return current;
  }

  // Send document update
  sendDocumentUpdate(targetRef: string, newData: any): boolean {
    if (!this.documentId || !this.wsService?.isConnected()) {
      console.warn('Cannot send update: WebSocket not connected or document not initialized');
      return false;
    }

    try {
      // Check if this is a table or text update that needs full data structure
      const isTableOrTextUpdate = targetRef.includes('tables') || targetRef.includes('texts');
      
      // If this is a table or text update, we need to get the full data structure
      if (isTableOrTextUpdate && (window as any).doclingData) {
        const fullDocument = (window as any).doclingData;
        const parentData = this.getParentData(fullDocument, targetRef);
        const lastKey = targetRef.split('/').pop();
        
        if (parentData && lastKey && parentData[lastKey]) {
          // Use the full data structure from the document
          newData = parentData[lastKey];
          console.log('Using full data structure for table/text update:', { 
            targetRef, 
            dataType: Array.isArray(newData) ? 'array' : typeof newData,
            itemCount: Array.isArray(newData) ? newData.length : 1
          });
        }
      }

      // If we have newData, use it
      if (newData !== undefined && newData !== null) {
        const message = {
          type: 'update',
          file_id: this.documentId,
          target_ref: targetRef,
          new_data: newData,
          is_full_update: isTableOrTextUpdate, // Mark as full update for tables/texts
          message: `Document updated: ${targetRef}`,
          timestamp: new Date().toISOString(),
          message_id: `update_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
        };

        console.log('Sending document update:', {
          type: 'update',
          target_ref: targetRef,
          is_full_update: isTableOrTextUpdate,
          has_data: true,
          data_type: typeof newData,
          is_array: Array.isArray(newData),
          data_sample: JSON.stringify(newData).substring(0, 200) + '...'
        });

        return this.wsService.send(message);
      }

      // Fallback to getting data from the document if newData is not provided
      console.warn('No newData provided, falling back to document data');
      const fullDocument = (window as any).doclingData;
      if (!fullDocument) {
        console.error('No document data found in window.doclingData');
        return false;
      }

      const parentData = this.getParentData(fullDocument, targetRef);
      if (!parentData) {
        console.error(`Could not find parent data for targetRef: ${targetRef}`);
        return false;
      }

      const lastKey = targetRef.split('/').pop();
      if (!lastKey || !parentData[lastKey]) {
        console.error(`Could not find data for key: ${lastKey} in parent data`);
        return false;
      }

      const dataToSend = parentData[lastKey];
      const message = {
        type: 'update',
        file_id: this.documentId,
        target_ref: targetRef,
        new_data: dataToSend,
        is_full_update: true,
        message: `Document updated with full data: ${targetRef}`,
        timestamp: new Date().toISOString(),
        message_id: `update_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      };

      console.log('Sending full document update (fallback):', {
        type: 'update',
        target_ref: targetRef,
        is_full_update: true,
        has_data: !!dataToSend,
        data_type: typeof dataToSend,
        is_array: Array.isArray(dataToSend)
      });

      return this.wsService.send(message);
    } catch (error) {
      console.error('Error in sendDocumentUpdate:', error);
      return false;
    }
  }

  // Send table merge request
  sendTableMergeRequest(sourceRef: string, targetRef: string): boolean {
    if (!this.documentId || !this.wsService?.isConnected()) {
      console.warn('Cannot send table merge: WebSocket not connected');
      return false;
    }

    const message = {
      type: 'merge_table',
      file_id: this.documentId,
      source_ref: sourceRef,
      target_ref: targetRef,
      message: `Table merge: ${sourceRef} -> ${targetRef}`
    };

    return this.wsService.send(message);
  }

  // Send comment update with confirmation
  async sendCommentUpdate(comment: string, targetRef?: string): Promise<boolean> {
    if (!this.documentId) {
      console.error('Cannot send comment update: Document not initialized');
      return false;
    }

    // Ensure WebSocket is connected
    if (!this.wsService || !this.wsService.isConnected()) {
      console.warn('WebSocket not connected, attempting to reconnect...');
      try {
        await this.connectToDocument();
        if (!this.wsService?.isConnected()) {
          console.error('Failed to establish WebSocket connection');
          return false;
        }
      } catch (error) {
        console.error('Error reconnecting WebSocket:', error);
        return false;
      }
    }

    try {
      // Parse the comment data
      let commentData;
      try {
        commentData = typeof comment === 'string' ? JSON.parse(comment) : comment;
      } catch (e) {
        console.error('Failed to parse comment data:', e);
        return false;
      }

      // Create a unique message ID for tracking
      const messageId = `comment_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const commentId = commentData.commentId || commentData.id || messageId;
      const action = commentData.action || 'update';
      const targetRefValue = targetRef || commentData.targetRef || commentData.target_ref || '';
      
      // Construct the message in the format expected by the backend
      const message = {
        type: 'comment',
        file_id: this.documentId,
        target_ref: targetRefValue,
        action: action,
        comment_id: commentId,
        comment: commentData.comment || commentData.content || '',
        timestamp: new Date().toISOString(),
        message_id: messageId,
        expects_ack: true,
        version: '1.0',
        // Include the full comment data for reference
        data: {
          ...commentData,
          id: commentId,
          targetRef: targetRefValue,
          action: action
        }
      };

      console.log('Sending comment update:', {
        type: 'comment',
        message_id: messageId,
        target_ref: message.target_ref,
        action: message.action,
        comment_id: message.comment_id,
        full_message: JSON.stringify(message, null, 2)
      });

      // Send with confirmation and handle the response
      const success = await this.wsService.sendMessageWithConfirmation(message, 15000);
      
      if (!success) {
        console.error('Failed to get confirmation for comment update:', messageId);
        // Try one more time before giving up
        console.log('Retrying comment update...');
        const retrySuccess = await this.wsService.sendMessageWithConfirmation(message, 15000);
        
        if (!retrySuccess) {
          console.error('Failed to confirm comment update after retry:', messageId);
          return false;
        }
        console.log('Comment update succeeded on retry:', messageId);
      }

      console.log('Comment update confirmed by server:', messageId);
      return true;
    } catch (error) {
      console.error('Error in sendCommentUpdate:', error);
      // Try to recover by reconnecting
      try {
        await this.connectToDocument();
      } catch (reconnectError) {
        console.error('Failed to reconnect after error:', reconnectError);
      }
      return false;
    }
  }

  // Send raw message
  sendMessage(message: any): boolean {
    if (!this.wsService?.isConnected()) {
      console.warn('Cannot send message: WebSocket not connected');
      return false;
    }
    console.log('Sending WebSocket message:', message);
    return this.wsService.send(message);
  }

  // Send message and wait for confirmation
  async sendMessageWithConfirmation(message: any, timeout = 5000): Promise<boolean> {
    if (!this.wsService || !this.wsService.isConnected()) {
      console.warn('Cannot send message: WebSocket not connected');
      return false;
    }

    return new Promise((resolve) => {
      let responseReceived = false;
      let timeoutId: NodeJS.Timeout | null = null;

      // Set up a handler for the response
      const responseHandler = (response: any) => {
        // PATCH: Accept any {success: true} for comment actions
        if (message.type === 'comment' && response && response.success === true) {
          responseReceived = true;
          if (timeoutId) clearTimeout(timeoutId);
          this.wsService?.off('message', responseHandler);
          console.log('Received confirmation for comment:', message);
          resolve(true);
          return;
        }
        // For other actions, check for _responseTo or message_id as before
        if (response && response.type === 'ack' && response.message_id === message.message_id) {
          responseReceived = true;
          if (timeoutId) clearTimeout(timeoutId);
          this.wsService?.off('message', responseHandler);
          console.log('Received ACK for message:', message);
          resolve(true);
        }
      };

      // Set up timeout
      const wsService = this.wsService; // Capture the service reference
      if (!wsService) {
        console.warn('WebSocket service not available');
        resolve(false);
        return;
      }
      
      timeoutId = setTimeout(() => {
        if (!responseReceived) {
          wsService.off('message', responseHandler);
          console.warn('Timeout waiting for confirmation:', message);
          resolve(false);
        }
      }, timeout);

      // Add the handler
      if (wsService) {
        wsService.on('message', responseHandler);

        // Add a unique message ID if not present
        if (!message.message_id) {
          message.message_id = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        }

        // Mark that we expect an ACK
        message.expects_ack = true;

        // Send the message
        console.log('Sending message with confirmation:', message);
        wsService.send(message);
      } else {
        if (timeoutId) clearTimeout(timeoutId);
        resolve(false);
      }
    });
  }

  // Passthrough for sendMessageWithConfirmation
  sendMessageWithConfirmationPassthrough(message: any, timeout?: number) {
    return this.wsService?.sendMessageWithConfirmation(message, timeout);
  }

  // Subscribe to WebSocket messages
  onMessage(handler: (message: any) => void): () => void {
    this.updateHandlers.push(handler);
    return () => {
      const index = this.updateHandlers.indexOf(handler);
      if (index > -1) {
        this.updateHandlers.splice(index, 1);
      }
    };
  }

  // Alias for onMessage to support onDocumentUpdate
  onDocumentUpdate(handler: (message: any) => void): () => void {
    return this.onMessage(handler);
  }

  // Private methods for connection handling
  private async connectToDocument(): Promise<boolean> {
    return new Promise((resolve) => {
      if (!this.wsService) {
        console.error('WebSocket service not initialized');
        resolve(false);
        return;
      }
      
      let resolved = false;
      let connectionTimeout: NodeJS.Timeout;
      
      connectionTimeout = setTimeout(() => {
        console.error('WebSocket connection timed out');
        resolveOnce(false);
      }, 10000);
      
      const resolveOnce = (result: boolean) => {
        if (!resolved) {
          resolved = true;
          clearTimeout(connectionTimeout);
          resolve(result);
        }
      };

      this.wsService.connect({
        onConnect: () => {
          console.log('WebSocket connected for document updates');
          resolveOnce(true);
        },
        onDisconnect: (code: number, reason: string) => {
          console.log('WebSocket disconnected:', code, reason);
          if (!resolved) {
            resolveOnce(false);
          }
        },
        onError: (error: Event) => {
          console.error('WebSocket error:', error);
          resolveOnce(false);
        }
      });
    });
  }

  // Handle incoming WebSocket messages
  private handleIncomingMessage(message: any) {
    try {
      console.log('Received WebSocket message:', message);
      
      // Send ACK for messages that expect it
      if (message.expects_ack) {
        this.wsService?.send({
          type: 'ack',
          message_id: message.message_id,
          timestamp: new Date().toISOString()
        });
      }
      
      // Update all registered handlers
      this.updateHandlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('Error in message handler:', error);
        }
      });
      
      // Handle specific message types
      if (message.type === 'error') {
        if (message.message && !message.message.includes('heartbeat')) {
          toast.error(message.message);
        }
      } else if (message.type === 'connection_status') {
        if (message.status === 'disconnected') {
          toast('Disconnected');
        }
      } else if (message.type === 'update') {
        console.log('Document update received:', message);
        // Trigger document update handlers
        this.updateHandlers.forEach(handler => handler({
          type: 'document_update',
          target_ref: message.target_ref,
          data: message.data,
          success: true,
          timestamp: new Date().toISOString()
        }));
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
    }
  }

  // Check connection status
  isConnected(): boolean {
    return this.wsService?.isConnected() ?? false;
  }

  getConnectionState(): WebSocketState {
    return this.wsService?.getState() ?? WebSocketState.DISCONNECTED;
  }

  // Cleanup and disconnect
  disconnect() {
    if (this.wsService) {
      this.wsService.disconnect();
      this.wsService = null;
    }
    this.documentId = null;
    console.log('WebSocket disconnected');
  }

  // Complete cleanup
  destroy() {
    this.disconnect();
    this.updateHandlers = [];
  }
}

// Singleton instance
let documentWebSocketService: DocumentWebSocketService | null = null;
let activeDocumentId: string | null = null;

export function getDocumentWebSocketService(documentId?: string): DocumentWebSocketService {
  // If no instance exists or document ID has changed, create a new one
  if (!documentWebSocketService || (documentId && documentId !== activeDocumentId)) {
    if (documentWebSocketService) {
      // Clean up previous instance if document ID changed
      documentWebSocketService.destroy();
    }
    documentWebSocketService = new DocumentWebSocketService();
    activeDocumentId = documentId || null;
    
    if (documentId) {
      // Initialize with the document ID if provided
      documentWebSocketService.initializeDocument(documentId).catch(err => {
        console.error('Failed to initialize WebSocket:', err);
      });
    }
  }
  return documentWebSocketService;
}

// Helper function to get auth token from storage
function getAuthToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('authToken');
  }
  return null;
}

export default DocumentWebSocketService;
