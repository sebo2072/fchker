/**
 * WebSocket client service for real-time communication with backend.
 */

export interface WebSocketMessage {
    type: 'thinking_update' | 'verification_result' | 'claims_extracted' | 'error' | 'status';
    data: any;
    timestamp: string;
}

export type MessageHandler = (message: WebSocketMessage) => void;

class WebSocketClient {
    private ws: WebSocket | null = null;
    private sessionId: string | null = null;
    private handlers: MessageHandler[] = [];
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 2000;

    connect(sessionId: string) {
        this.sessionId = sessionId;
        const wsUrl = `ws://localhost:8000/ws/${sessionId}`;

        console.log(`Connecting to WebSocket: ${wsUrl}`);

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
        };

        this.ws.onmessage = (event) => {
            try {
                const message: WebSocketMessage = JSON.parse(event.data);
                console.log('WebSocket message received:', message);
                this.notifyHandlers(message);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.attemptReconnect();
        };
    }

    private attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts && this.sessionId) {
            this.reconnectAttempts++;
            console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);

            setTimeout(() => {
                if (this.sessionId) {
                    this.connect(this.sessionId);
                }
            }, this.reconnectDelay);
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.sessionId = null;
        this.reconnectAttempts = 0;
    }

    addMessageHandler(handler: MessageHandler) {
        this.handlers.push(handler);
    }

    removeMessageHandler(handler: MessageHandler) {
        this.handlers = this.handlers.filter(h => h !== handler);
    }

    private notifyHandlers(message: WebSocketMessage) {
        this.handlers.forEach(handler => {
            try {
                handler(message);
            } catch (error) {
                console.error('Error in message handler:', error);
            }
        });
    }

    isConnected(): boolean {
        return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
    }
}

export const wsClient = new WebSocketClient();
